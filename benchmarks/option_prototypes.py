"""Build a measured option's prototype on a copy of a schema, and time what it costs.

Two schema options are measured on real data before either is implemented, each by a
prototype built on a scratch copy of a finished schema (`benchmarks.option_probe` times
the statements the application would issue against it). A third, ``none``, is the copy
alone, which the prototypes' copies are compared with:

``none``
    The copy, with nothing added.
``default_rank``
    A rank of every observation in the default sort order, ``(time1, opus_id)``, held in
    a keyed column of the base table holding ``obs_general``'s rows: ``ALTER TABLE ...
    ADD COLUMN default_rank INT UNSIGNED, ADD KEY (default_rank)``, then each row's
    ``ROW_NUMBER() OVER (ORDER BY time1, opus_id)`` written into it. Where ``obs_general``
    is a view of that table, the view is then created again listing the new column, by
    the import's own code (`opus_import.importdb.mysql.ImportDBMySQL.create_obs_general_view`)
    given ``obs_general.json``'s columns and the new one.
``facet``
    A narrow table, ``obs_facet``, holding for each observation the value of every mult
    field kept in a table with one row per observation (`facet_columns`): ``obs_general``
    itself and each table whose primary key is ``obs_general_id``. Its key is
    ``obs_general_id``; each other column is named by its field's qualified name and has
    the type the import gives a mult id. One ``INSERT ... SELECT`` fills it from
    ``obs_general`` joined to each of those tables. A list column, held in a junction
    table, and a table with several rows per observation hold no column of it.

The command copies the source schema into the target with
`benchmarks.schema_copy.clone_schema`, views included, laid out as the import lays out a
schema (``defer_keys``: each table filled in primary-key order, then its secondary keys
built), so every copy compared has the same layout; the source is only read. The source
must serve every row it holds (`require_served_view`): no generation pending, no switch
still revertible, and an ``obs_general`` view without a condition, since a rank or a facet
row of an observation the view hides would measure rows no visitor sees, and the rank's
view, made again, would lose the condition. The build is timed step by step, and its
cost in bytes is read after ``ANALYZE TABLE`` with the statistics cache off: for
``default_rank``, the new key's own size, and the change in the base table's data and
index bytes; for ``facet``, the table's data and index bytes. Last, the server is
restarted once with ``innodb_fast_shutdown = 0``, so InnoDB merges its change buffer and
writes every page before anything is timed on the copy (`settle_server`). The run (kind
``prototype``) goes into the label's result file, whose environment then names the copy
as the label's schema, so ``bench_db`` and ``bench_web`` given the same label measure the
copy.

The prototypes are built with this checkout's import code, so the side given must be
this checkout.

Example, the ``default_rank`` prototype of a complete-scale schema::

    python -m benchmarks.option_prototypes --scale complete --side after --pr PR-nn \\
        --session rank --python venv-head/bin/python --repo-root . \\
        --source bench_complete_before_a_1 --target bench_complete_rank \\
        --option default_rank
"""

from __future__ import annotations

import argparse
import contextlib
import json
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

from benchmarks.bench_server import (
    DB_HOST,
    DB_PASSWORD,
    DB_USER,
    OBS_GENERAL_ROWS_TABLE,
    OBS_GENERAL_TABLE,
    SCHEMA_VERSION_TABLE,
    MysqlServer,
    load_server_config,
    obs_general_table,
    query,
    quote_identifier,
    reexec_with_socket,
    server_environment,
)
from benchmarks.resort_probe import top_level
from benchmarks.results import (
    REPO_ROOT,
    SCALES,
    SIDES,
    append_runs,
    host_environment,
    make_label,
    new_run,
)
from benchmarks.schema_copy import clone_schema
from benchmarks.sides import Side, require_no_pythonpath
from opus_import import generations, import_util, mult_fields, table_keys
from opus_import.importdb.mysql import MYSQL_FIELD_TYPE_SQL, STATS_SAMPLE_PAGES, ImportDBMySQL

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

#: The options a prototype can be built for: ``none`` is the copy with nothing added.
OPTIONS = ('none', 'default_rank', 'facet')

#: The column holding each observation's rank in the default sort order, and its type.
DEFAULT_RANK_COLUMN = 'default_rank'
DEFAULT_RANK_SQL_TYPE = 'INT UNSIGNED'

#: The ``field_type`` the rank column would carry in ``obs_general.json``, which is how
#: the import's view code learns of a column.
DEFAULT_RANK_FIELD_TYPE = 'uint4'

#: The default sort order the rank numbers the observations in.
DEFAULT_ORDER = ('time1', 'opus_id')

#: The facet table, and its key: the observation each row describes.
FACET_TABLE = 'obs_facet'
FACET_KEY_COLUMN = 'obs_general_id'
FACET_KEY_SQL_TYPE = 'INT UNSIGNED'

#: The ``field_type`` values of the mult fields the facet table holds: one mult id each.
FACET_FIELD_TYPES = ('mult_idx', 'flag_yesno', 'flag_onoff')

#: The column of every observation table but ``obs_general`` that names its observation.
OBSERVATION_COLUMN = table_keys.OBSERVATION_DELETE_COLUMN

#: The run kind the command records, which `benchmarks.compare` does not compare.
PROTOTYPE_KIND = 'prototype'

#: The clauses that make an ``obs_general`` view show fewer rows than its base table holds,
#: where they appear outside quotes and parentheses.
_ROW_LIMITING_CLAUSE = r'\b(?:WHERE|LIMIT)\b'

#: The metric names' prefix.
METRIC_PREFIX = 'prototype'


class PrototypeError(Exception):
    """Raised when a prototype cannot be built on the schema given."""


@dataclass(frozen=True)
class FacetColumn:
    """One column of the facet table.

    Attributes:
        name: The mult field's qualified name, which is the column's name.
        table: The observation table holding the field's values.
        column: The column holding them there.
        sql_type: The column's SQL type, the one the import gives the field's values.
    """

    name: str
    table: str
    column: str
    sql_type: str


def _table_schema(table: str) -> list[dict[str, Any]]:
    """Return a packaged table schema.

    Parameters:
        table: The table, whose ``<table>.json`` the import packages.

    Returns:
        The schema's entries.
    """
    path = import_util.TABLE_SCHEMA_DIR / f'{table}.json'
    entries: list[dict[str, Any]] = json.loads(path.read_text(encoding='utf-8'))
    return entries


def is_observation_table(table: str) -> bool:
    """Return whether a table holds at most one row per observation.

    Parameters:
        table: A packaged observation table.

    Returns:
        True for ``obs_general``, and for a table whose schema declares the primary key
        ``(obs_general_id)``.
    """
    if table == OBS_GENERAL_TABLE:
        return True
    primary = table_keys.TableKey('primary', (OBSERVATION_COLUMN,))
    return primary in table_keys.declared_keys(_table_schema(table))


def facet_columns() -> list[FacetColumn]:
    """Return the facet table's columns, from the mult fields the import's schemas declare.

    Returns:
        One column per mult field (`opus_import.mult_fields.packaged_mult_columns`)
        whose ``field_type`` is one of `FACET_FIELD_TYPES` and whose table holds at most
        one row per observation (`is_observation_table`), in order of qualified name.
    """
    return [
        FacetColumn(
            name=name,
            table=found.table_name,
            column=str(found.entry['field_name']),
            sql_type=MYSQL_FIELD_TYPE_SQL[found.entry['field_type']],
        )
        for name, found in mult_fields.packaged_mult_columns().items()
        if found.entry.get('field_type') in FACET_FIELD_TYPES
        and is_observation_table(found.table_name)
    ]


def facet_table_sql(columns: Sequence[FacetColumn]) -> str:
    """Return the statement that creates the facet table.

    Parameters:
        columns: Its columns after the key.

    Returns:
        The ``CREATE TABLE``, with the statistics sample the import gives every table it
        creates (`opus_import.importdb.mysql.STATS_SAMPLE_PAGES`).
    """
    q = quote_identifier
    definitions = [f'{q(FACET_KEY_COLUMN)} {FACET_KEY_SQL_TYPE} NOT NULL PRIMARY KEY']
    definitions += [f'{q(column.name)} {column.sql_type.upper()}' for column in columns]
    return (
        f'CREATE TABLE {q(FACET_TABLE)} ({", ".join(definitions)}) ENGINE=InnoDB '
        f'STATS_SAMPLE_PAGES={STATS_SAMPLE_PAGES}'
    )


def facet_fill_sql(columns: Sequence[FacetColumn]) -> str:
    """Return the one ``INSERT ... SELECT`` that fills the facet table.

    Parameters:
        columns: The facet table's columns after the key.

    Returns:
        The statement: every observation ``obs_general`` shows, with each column's value
        read from ``obs_general`` or from its table, joined on ``obs_general_id`` and
        left joined, so an observation without a row there holds NULL.
    """
    q = quote_identifier
    hub = q(OBS_GENERAL_TABLE)
    names = [q(FACET_KEY_COLUMN)] + [q(column.name) for column in columns]
    values = [f'{hub}.`id`'] + [f'{q(column.table)}.{q(column.column)}' for column in columns]
    children = sorted({column.table for column in columns} - {OBS_GENERAL_TABLE})
    joins = ''.join(
        f' LEFT JOIN {q(table)} ON {q(table)}.{q(OBSERVATION_COLUMN)} = {hub}.`id`'
        for table in children
    )
    return (
        f'INSERT INTO {q(FACET_TABLE)} ({", ".join(names)}) '  # nosec B608 - quoted identifiers
        f'SELECT {", ".join(values)} FROM {hub}{joins}'
    )


def rank_alter_sql(base: str) -> str:
    """Return the statement that adds the rank column and its key.

    Parameters:
        base: The base table holding ``obs_general``'s rows.

    Returns:
        The ``ALTER TABLE``.
    """
    q = quote_identifier
    rank = q(DEFAULT_RANK_COLUMN)
    return (
        f'ALTER TABLE {q(base)} ADD COLUMN {rank} {DEFAULT_RANK_SQL_TYPE}, ADD KEY {rank} ({rank})'
    )


def rank_fill_sql(base: str) -> str:
    """Return the statement that writes every row's rank in the default sort order.

    Parameters:
        base: The base table holding ``obs_general``'s rows.

    Returns:
        An ``UPDATE`` joining the table to its own rows numbered by ``ROW_NUMBER() OVER
        (ORDER BY time1, opus_id)``.
    """
    q = quote_identifier
    order = ', '.join(q(column) for column in DEFAULT_ORDER)
    return (
        f'UPDATE {q(base)} AS `ranked_row` JOIN (SELECT `id`, '  # nosec B608 - quoted identifiers
        f'ROW_NUMBER() OVER (ORDER BY {order}) AS `rank_value` FROM {q(base)}) AS `ranking` '
        f'ON `ranking`.`id` = `ranked_row`.`id` '
        f'SET `ranked_row`.{q(DEFAULT_RANK_COLUMN)} = `ranking`.`rank_value`'
    )


def view_schema_with_rank() -> list[dict[str, Any]]:
    """Return ``obs_general.json``'s entries with the rank column declared after them.

    Returns:
        The schema the import's view code is given, so the view lists the rank column
        as it would list a column ``obs_general.json`` declared.
    """
    return [
        *_table_schema(OBS_GENERAL_TABLE),
        {'field_name': DEFAULT_RANK_COLUMN, 'field_type': DEFAULT_RANK_FIELD_TYPE},
    ]


def recreate_view(schema: str) -> None:
    """Create ``obs_general`` again in a schema, listing the rank column, by the import's code.

    Parameters:
        schema: The copy, whose ``obs_general_rows`` has the rank column.
    """
    db = ImportDBMySQL(DB_HOST, '', schema, DB_USER, DB_PASSWORD, bulk_load=False)
    try:
        db.create_obs_general_view(view_schema_with_rank())
    finally:
        db.close()


def table_bytes(connection: Any, schema: str, table: str) -> tuple[int, int]:
    """Return a table's data and index bytes, after fresh statistics.

    Parameters:
        connection: A connection whose ``information_schema_stats_expiry`` is 0.
        schema: The schema.
        table: The table.

    Returns:
        Its ``DATA_LENGTH`` and ``INDEX_LENGTH`` after ``ANALYZE TABLE``.
    """
    query(connection, f'ANALYZE TABLE {quote_identifier(schema)}.{quote_identifier(table)}')
    data, index = query(
        connection,
        'SELECT DATA_LENGTH, INDEX_LENGTH FROM information_schema.TABLES '
        'WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s',
        [schema, table],
    )[0]
    return int(data), int(index)


def key_bytes(connection: Any, schema: str, table: str, key: str) -> int:
    """Return the size of one key of a table, from InnoDB's persistent statistics.

    Parameters:
        connection: A connection, after ``ANALYZE TABLE`` on the table.
        schema: The schema.
        table: The table.
        key: The key's name.

    Returns:
        Its pages times the page size; 0 when the statistics do not name it.
    """
    rows = query(
        connection,
        'SELECT stat_value * @@innodb_page_size FROM mysql.innodb_index_stats '
        "WHERE database_name = %s AND table_name = %s AND index_name = %s AND stat_name = 'size'",
        [schema, table, key],
    )
    return int(rows[0][0]) if len(rows) > 0 else 0


def require_served_view(connection: Any, schema: str) -> None:
    """Refuse a schema whose ``obs_general`` may hide some of its base table's rows.

    Parameters:
        connection: A connection; the schema is only read.
        schema: The schema.

    Raises:
        PrototypeError: If its ``schema_version`` row records a pending generation or a
            switch that can still be reverted, or its ``obs_general`` is a view whose
            definition has a top-level ``WHERE`` or ``LIMIT``.
    """
    q = quote_identifier
    pending = generations.PENDING_GENERATION_COLUMN
    revertible = generations.REVERTIBLE_COLUMN
    columns = {
        str(row[0])
        for row in query(
            connection,
            'SELECT COLUMN_NAME FROM information_schema.COLUMNS '
            'WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s',
            [schema, SCHEMA_VERSION_TABLE],
        )
    }
    if {pending, revertible} <= columns:
        rows = query(
            connection,
            f'SELECT {q(pending)}, {q(revertible)} FROM {q(schema)}.{q(SCHEMA_VERSION_TABLE)}',  # nosec B608 - quoted identifiers
        )
        for waiting, revert in rows:
            if waiting is not None or bool(revert):
                raise PrototypeError(
                    f'{schema} records a pending generation ({waiting}) or a revertible '
                    f'switch ({bool(revert)}); a prototype is built on a schema that serves '
                    'every row it holds'
                )
    views = query(
        connection,
        'SELECT VIEW_DEFINITION FROM information_schema.VIEWS '
        'WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s',
        [schema, OBS_GENERAL_TABLE],
    )
    if len(views) > 0 and len(top_level(str(views[0][0]), _ROW_LIMITING_CLAUSE)) > 0:
        raise PrototypeError(
            f'{schema}.{OBS_GENERAL_TABLE} is a view with a condition or a row limit; a '
            'prototype is built on a schema that serves every row it holds'
        )


def require_view_columns(connection: Any, schema: str) -> None:
    """Refuse a copy whose ``obs_general`` view lists other columns than the import's.

    The rank prototype makes the view again from ``obs_general.json``, so a view that
    listed anything else would change silently.

    Parameters:
        connection: A connection.
        schema: The copy.

    Raises:
        PrototypeError: If the view's columns, in order, are not those the import's view
            code lists for ``obs_general.json`` (`opus_import.generations.view_columns`).
    """
    listed = [
        str(row[0])
        for row in query(
            connection,
            'SELECT COLUMN_NAME FROM information_schema.COLUMNS '
            'WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s ORDER BY ORDINAL_POSITION',
            [schema, OBS_GENERAL_TABLE],
        )
    ]
    expected = generations.view_columns(_table_schema(OBS_GENERAL_TABLE))
    if listed != expected:
        unlisted = sorted(set(expected) - set(listed))
        extra = sorted(set(listed) - set(expected))
        raise PrototypeError(
            f'{schema}.{OBS_GENERAL_TABLE} lists other columns than obs_general.json gives '
            f'it (missing {unlisted}, extra {extra}, or another order)'
        )


def settle_server(server: MysqlServer) -> float:
    """Restart the server with a slow shutdown, so nothing waits to be merged or written.

    With ``innodb_fast_shutdown = 0`` InnoDB merges its change buffer and purges before it
    stops, so a copy just built has no backlog left for a later cold start to work off.
    The setting is put back afterwards.

    Parameters:
        server: The owned server, running.

    Returns:
        The restart's wall-clock seconds.
    """
    with contextlib.closing(server.connect()) as connection:
        previous = int(query(connection, 'SELECT @@GLOBAL.innodb_fast_shutdown')[0][0])
        query(connection, 'SET GLOBAL innodb_fast_shutdown = 0')
    started = time.perf_counter()
    try:
        server.restart()
    finally:
        with contextlib.closing(server.connect()) as connection:
            query(connection, 'SET GLOBAL innodb_fast_shutdown = %s', [previous])
    return time.perf_counter() - started


def _timed(connection: Any, statement: str) -> float:
    """Run one statement and return its wall-clock seconds."""
    started = time.perf_counter()
    query(connection, statement)
    return time.perf_counter() - started


def build_default_rank(
    connection: Any, schema: str, *, make_view: Callable[[str], None] = recreate_view
) -> tuple[dict[str, float], dict[str, Any]]:
    """Build the rank prototype on a copy, timing each step and reading its cost.

    Parameters:
        connection: A connection to the copy, as its default schema, with
            ``information_schema_stats_expiry`` at 0.
        schema: The copy.
        make_view: What creates ``obs_general`` again listing the rank column, where
            ``obs_general`` is a view.

    Returns:
        The metrics, under ``prototype.default_rank.``: ``alter_s``, ``fill_s`` and
        ``view_s`` (0 where ``obs_general`` is a base table), their sum ``build_s``, the
        rows ranked as ``rows``, the new key's own ``key_bytes``, and the base table's
        change in ``data_bytes`` and ``index_bytes``, each side read after ``ANALYZE
        TABLE``. The details: the base table, both statements, and the table's bytes
        before and after.

    Raises:
        PrototypeError: If the copy already has the column, or its view lists other
            columns than the import's (`require_view_columns`).
    """
    base = obs_general_table(connection, schema)
    present = query(
        connection,
        'SELECT COUNT(*) FROM information_schema.COLUMNS '
        'WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s AND COLUMN_NAME = %s',
        [schema, base, DEFAULT_RANK_COLUMN],
    )[0][0]
    if int(present) > 0:
        raise PrototypeError(f'{schema}.{base} already has the column {DEFAULT_RANK_COLUMN}')
    if base == OBS_GENERAL_ROWS_TABLE:
        require_view_columns(connection, schema)
    before = table_bytes(connection, schema, base)
    statements = {'alter': rank_alter_sql(base), 'fill': rank_fill_sql(base)}
    prefix = f'{METRIC_PREFIX}.default_rank'
    metrics = {f'{prefix}.{step}_s': _timed(connection, text) for step, text in statements.items()}
    view_s = 0.0
    if base == OBS_GENERAL_ROWS_TABLE:
        started = time.perf_counter()
        make_view(schema)
        view_s = time.perf_counter() - started
    metrics[f'{prefix}.view_s'] = view_s
    metrics[f'{prefix}.build_s'] = (
        metrics[f'{prefix}.alter_s'] + metrics[f'{prefix}.fill_s'] + view_s
    )
    after = table_bytes(connection, schema, base)
    metrics[f'{prefix}.data_bytes'] = after[0] - before[0]
    metrics[f'{prefix}.index_bytes'] = after[1] - before[1]
    metrics[f'{prefix}.key_bytes'] = key_bytes(connection, schema, base, DEFAULT_RANK_COLUMN)
    q = quote_identifier
    metrics[f'{prefix}.rows'] = int(
        query(connection, f'SELECT COUNT({q(DEFAULT_RANK_COLUMN)}) FROM {q(base)}')[0][0]  # nosec B608 - quoted identifiers
    )
    details = {
        'base_table': base,
        'statements': statements,
        'bytes_before': {'data': before[0], 'index': before[1]},
        'bytes_after': {'data': after[0], 'index': after[1]},
    }
    return metrics, details


def build_facet(connection: Any, schema: str) -> tuple[dict[str, float], dict[str, Any]]:
    """Build the facet prototype on a copy, timing each step and reading its cost.

    Parameters:
        connection: A connection to the copy, as its default schema, with
            ``information_schema_stats_expiry`` at 0.
        schema: The copy.

    Returns:
        The metrics, under ``prototype.facet.``: ``create_s`` and ``fill_s``, their sum
        ``build_s``, the table's ``rows``, its ``columns`` after the key, and its
        ``data_bytes`` and ``index_bytes``. The details: both statements, the columns
        built (name, table, column), and the columns of tables the copy does not have,
        which are left out.

    Raises:
        PrototypeError: If the copy already has the table.
    """
    tables = {
        str(row[0])
        for row in query(
            connection,
            'SELECT TABLE_NAME FROM information_schema.TABLES WHERE TABLE_SCHEMA = %s',
            [schema],
        )
    }
    if FACET_TABLE in tables:
        raise PrototypeError(f'{schema} already has the table {FACET_TABLE}')
    every = facet_columns()
    columns = [column for column in every if column.table in tables]
    left_out = [column for column in every if column.table not in tables]
    statements = {'create': facet_table_sql(columns), 'fill': facet_fill_sql(columns)}
    prefix = f'{METRIC_PREFIX}.facet'
    metrics = {f'{prefix}.{step}_s': _timed(connection, text) for step, text in statements.items()}
    metrics[f'{prefix}.build_s'] = metrics[f'{prefix}.create_s'] + metrics[f'{prefix}.fill_s']
    data, index = table_bytes(connection, schema, FACET_TABLE)
    metrics[f'{prefix}.data_bytes'] = data
    metrics[f'{prefix}.index_bytes'] = index
    metrics[f'{prefix}.rows'] = int(
        query(connection, f'SELECT COUNT(*) FROM {quote_identifier(FACET_TABLE)}')[0][0]  # nosec B608 - quoted identifier
    )
    metrics[f'{prefix}.columns'] = len(columns)
    details = {
        'statements': statements,
        'columns': [[column.name, column.table, column.column] for column in columns],
        'left_out': [[column.name, column.table, column.column] for column in left_out],
    }
    return metrics, details


def build_prototype(
    server: MysqlServer,
    *,
    source: str,
    target: str,
    option: str,
    version: int | None,
    make_view: Callable[[str], None] = recreate_view,
) -> dict[str, Any]:
    """Copy a schema in the import's layout, build one option on the copy, and settle it.

    Parameters:
        server: The owned server, running.
        source: The schema copied, which is only read.
        target: The copy, dropped first if it exists.
        option: One of `OPTIONS`.
        version: The ``SCHEMA_VERSION`` the copy's version row is restamped to, or None
            to leave it as copied (`benchmarks.schema_copy.clone_schema`).
        make_view: What creates ``obs_general`` again for the rank prototype.

    Returns:
        A ``prototype`` run: the build's metrics (`build_default_rank`, `build_facet`;
        none for ``none``) with the copy's ``clone_s`` and the restart's ``settle_s``
        (`settle_server`), and its details, which name the option, the source and the
        copy.

    Raises:
        PrototypeError: If the option is unknown, the target is the source, the source
            may hide rows (`require_served_view`), or the build refuses the copy.
    """
    if option not in OPTIONS:
        raise PrototypeError(f'unknown option {option!r}, not one of {list(OPTIONS)}')
    if target == source:
        raise PrototypeError(f'the copy cannot be the source schema {source!r}')
    with contextlib.closing(server.connect()) as connection:
        require_served_view(connection, source)
    run = new_run(PROTOTYPE_KIND)
    clone_s = clone_schema(server, source, target, version=version, defer_keys=True)
    metrics: dict[str, float] = {}
    details: dict[str, Any] = {}
    with contextlib.closing(server.connect(target)) as connection:
        query(connection, 'SET SESSION information_schema_stats_expiry = 0')
        if option == 'default_rank':
            metrics, details = build_default_rank(connection, target, make_view=make_view)
        elif option == 'facet':
            metrics, details = build_facet(connection, target)
    run['metrics'].update(metrics)
    run['metrics'][f'{METRIC_PREFIX}.{option}.clone_s'] = clone_s
    run['metrics'][f'{METRIC_PREFIX}.{option}.settle_s'] = settle_server(server)
    run['details'].update(details)
    run['details'].update({'option': option, 'source': source, 'schema': target})
    return run


def _parse_arguments(argv: Sequence[str] | None) -> argparse.Namespace:
    """Read the command line.

    Parameters:
        argv: The arguments, or None for the command line's.

    Returns:
        The parsed arguments.
    """
    parser = argparse.ArgumentParser(
        prog='python -m benchmarks.option_prototypes',
        description="Build one option's prototype on a copy of a schema, and time it.",
    )
    parser.add_argument('--scale', choices=SCALES, required=True)
    parser.add_argument('--side', choices=SIDES, required=True)
    parser.add_argument('--pr', required=True)
    parser.add_argument('--session', required=True)
    parser.add_argument('--date', default=None)
    parser.add_argument('--python', type=Path, required=True)
    parser.add_argument('--repo-root', type=Path, required=True)
    parser.add_argument('--source', required=True, help='the schema copied, which is only read')
    parser.add_argument('--target', required=True, help='the copy the prototype is built on')
    parser.add_argument('--option', choices=OPTIONS, required=True)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    """Build one prototype and record its run.

    Parameters:
        argv: The arguments, or None for the command line's.
    """
    args = _parse_arguments(argv)
    require_no_pythonpath()
    if args.repo_root.resolve() != REPO_ROOT:
        # The prototype is built by this process's import code, so the side recorded must
        # be the checkout that code comes from.
        raise SystemExit(
            f'the prototypes are built with this checkout ({REPO_ROOT}), not '
            f'{args.repo_root.resolve()}'
        )
    server_config, _ = load_server_config()
    reexec_with_socket(
        server_config, 'benchmarks.option_prototypes', sys.argv[1:] if argv is None else argv
    )
    server = MysqlServer(server_config)
    side = Side(python=args.python.absolute(), repo_root=args.repo_root.resolve())
    label = make_label(
        pr=args.pr, side=args.side, scale=args.scale, session=args.session, date=args.date
    )
    environment: dict[str, Any] = {**host_environment(), **side.environment()}
    with server.running():
        environment.update(server_environment(server))
        run = build_prototype(
            server,
            source=args.source,
            target=args.target,
            option=args.option,
            version=side.schema_version(),
        )
    environment['schema'] = args.target
    path = append_runs(label, environment, [run])
    for name, value in sorted(run['metrics'].items()):
        sys.stdout.write(f'{name} = {value}\n')
    sys.stdout.write(f'recorded in {path}\n')


if __name__ == '__main__':
    main()
