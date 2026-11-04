"""Measure the schema an import built: sizes, indexes, plans, and index usage.

It first empties the search tables with the side's own reset option, because the
per-search tables an earlier web run left are not part of what the import built. Then
it runs ``ANALYZE TABLE`` on every table and sets
``information_schema_stats_expiry = 0`` on its connection, so nothing it reads comes
from stale statistics. Then it records, per table and for the schema: data and index
bytes and the exact row count, the index count, and ``MAX(id)`` of every ``mult_``
table; the schema's index bytes including InnoDB's ``FULLTEXT`` auxiliary tablespaces,
which ``information_schema.TABLES`` leaves out; the schema's total beside
``innodb_buffer_pool_size``; the size of ``obs_general.preview_images``; and the
index-usage snapshot.

``--dump-queries`` captures the statements each web scenario's requests issue against
this side's own schema (`benchmarks.query_capture`) into the session's scratch
directory, and replays them at once, planning each one. ``--commit-capture`` also
copies the capture to ``scenarios/queries.sql``, the committed copy for a reader.

``--ascii-columns`` counts, for every column whose form type is ``STRING``, the values
that do not survive conversion to ASCII.

Example::

    python -m benchmarks.bench_db --scale test --side before --pr PR-nn --session a \\
        --python venv-head/bin/python --repo-root . --dump-queries --ascii-columns
"""

from __future__ import annotations

import argparse
import contextlib
import shutil
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any

from benchmarks import query_capture
from benchmarks.app_servers import MemcachedServer
from benchmarks.bench_server import (
    MysqlServer,
    load_server_config,
    query,
    quote_identifier,
    reexec_with_socket,
    server_environment,
    write_opus_config,
)
from benchmarks.bench_web import (
    Client,
    RequestTiming,
    WebBench,
    reset_search_tables,
    run_sequence,
    side_schema,
)
from benchmarks.results import (
    REPO_ROOT,
    SCALES,
    SCENARIOS_DIR,
    SIDES,
    Label,
    append_runs,
    host_environment,
    make_label,
    new_run,
    scenario_hash,
)
from benchmarks.sides import Side, Spelling
from benchmarks.web_scenarios import Request, Scenario, load_web_config
from import_tests.tools import build_run

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

#: The committed copy of the newest capture, for a reader; nothing replays it.
COMMITTED_CAPTURE = SCENARIOS_DIR / 'queries.sql'


def table_statistics(connection: Any, schema: str) -> dict[str, dict[str, int]]:
    """Return each table's sizes, exact row count and index count.

    Parameters:
        connection: The harness's connection, with fresh statistics.
        schema: The schema.

    Returns:
        Per table: ``data_bytes``, ``index_bytes``, ``rows``, ``index_count``, and for a
        ``mult_`` table ``max_id``.
    """
    sizes = query(
        connection,
        'SELECT TABLE_NAME, DATA_LENGTH, INDEX_LENGTH FROM information_schema.TABLES '
        "WHERE TABLE_SCHEMA = %s AND TABLE_TYPE = 'BASE TABLE' ORDER BY TABLE_NAME",
        [schema],
    )
    index_counts = dict(
        query(
            connection,
            'SELECT TABLE_NAME, COUNT(DISTINCT INDEX_NAME) FROM information_schema.STATISTICS '
            'WHERE TABLE_SCHEMA = %s GROUP BY TABLE_NAME',
            [schema],
        )
    )
    tables: dict[str, dict[str, int]] = {}
    for name, data, index in sizes:
        table = f'{quote_identifier(schema)}.{quote_identifier(str(name))}'
        entry = {
            'data_bytes': int(data),
            'index_bytes': int(index),
            'rows': int(query(connection, f'SELECT COUNT(*) FROM {table}')[0][0]),  # nosec B608 - quoted identifiers
            'index_count': int(index_counts.get(name, 0)),
        }
        if str(name).startswith('mult_'):
            maximum = query(connection, f'SELECT MAX(id) FROM {table}')[0][0]  # nosec B608 - quoted identifiers
            entry['max_id'] = 0 if maximum is None else int(maximum)
        tables[str(name)] = entry
    return tables


def fulltext_bytes(connection: Any, schema: str) -> int:
    """Return the allocated size of the schema's ``FULLTEXT`` auxiliary tablespaces.

    Parameters:
        connection: The harness's connection.
        schema: The schema.

    Returns:
        The bytes, zero when the schema has no ``FULLTEXT`` index.
    """
    rows = query(
        connection,
        'SELECT COALESCE(SUM(ALLOCATED_SIZE), 0) FROM information_schema.INNODB_TABLESPACES '
        'WHERE NAME LIKE %s',
        [f'{schema}/fts\\_%'],
    )
    return int(rows[0][0])


def preview_images(connection: Any, schema: str, obs_general_data_bytes: int) -> dict[str, float]:
    """Return the size of ``obs_general.preview_images`` beside ``obs_general``'s data.

    Both ``DATA_LENGTH`` and ``JSON_STORAGE_SIZE`` count a large value's off-page pages,
    which a scan of the other columns never reads, so the ratio overstates what moving
    the column would save a scan.

    Parameters:
        connection: The harness's connection.
        schema: The schema.
        obs_general_data_bytes: ``obs_general``'s data length.

    Returns:
        The average and total storage size, and the total's ratio to the data length.
    """
    average, total = query(
        connection,
        'SELECT COALESCE(AVG(JSON_STORAGE_SIZE(preview_images)), 0), '
        'COALESCE(SUM(JSON_STORAGE_SIZE(preview_images)), 0) '
        f'FROM {quote_identifier(schema)}.obs_general',  # nosec B608 - quoted identifier
    )[0]
    return {
        'average_bytes': float(average),
        'total_bytes': float(total),
        'ratio_to_obs_general_data': float(total) / obs_general_data_bytes
        if obs_general_data_bytes > 0
        else 0.0,
    }


def index_usage(connection: Any, schema: str) -> dict[str, Any]:
    """Return the index-usage snapshot for the schema.

    Parameters:
        connection: The harness's connection.
        schema: The schema.

    Returns:
        ``sys.schema_unused_indexes`` and the per-index I/O counters of
        ``performance_schema``, both limited to the schema. They count from the
        server's last start.
    """
    unused = query(
        connection,
        'SELECT object_name, index_name FROM sys.schema_unused_indexes WHERE object_schema = %s',
        [schema],
    )
    usage = query(
        connection,
        'SELECT OBJECT_NAME, INDEX_NAME, COUNT_STAR, COUNT_READ, COUNT_WRITE FROM '
        'performance_schema.table_io_waits_summary_by_index_usage WHERE OBJECT_SCHEMA = %s',
        [schema],
    )
    return {
        'unused_indexes': [[str(table), str(index)] for table, index in unused],
        'index_io': [
            [str(table), None if index is None else str(index), int(star), int(read), int(write)]
            for table, index, star, read, write in usage
        ],
    }


def ascii_columns(connection: Any, schema: str) -> dict[str, int]:
    """Count, per ``STRING`` column, the values that change when converted to ASCII.

    Parameters:
        connection: The harness's connection.
        schema: The schema, whose ``param_info`` names the columns.

    Returns:
        ``<table>.<column>`` to the count, for every column ``param_info`` gives the form
        type ``STRING`` and the schema has.
    """
    columns = query(
        connection,
        f'SELECT DISTINCT p.category_name, p.name FROM {quote_identifier(schema)}.param_info p '  # nosec B608 - quoted identifier
        'JOIN information_schema.COLUMNS c ON c.TABLE_SCHEMA = %s '
        'AND c.TABLE_NAME = p.category_name AND c.COLUMN_NAME = p.name '
        "WHERE p.form_type = 'STRING' ORDER BY p.category_name, p.name",
        [schema],
    )
    counts = {}
    for table, column in columns:
        qualified = f'{quote_identifier(schema)}.{quote_identifier(str(table))}'
        name = quote_identifier(str(column))
        count = query(
            connection,
            f'SELECT COUNT(*) FROM {qualified} WHERE {name} <> CONVERT({name} USING ascii)',  # nosec B608 - quoted identifiers
        )[0][0]
        counts[f'{table}.{column}'] = int(count)
    return counts


def dump_queries(bench: WebBench, capture: Path) -> list[query_capture.Block]:
    """Run each scenario's requests once with the general log on, and write the capture.

    The search tables are reset once, before the first request; nothing is reset
    between scenarios, so every per-search table a statement names still exists when
    the capture is replayed.

    Parameters:
        bench: A web bench for this side, whose servers are started here.
        capture: The file to write.

    Returns:
        The captured blocks.
    """
    bench.reset('app-cold')
    connection = bench.connection
    blocks: list[query_capture.Block] = []
    query_capture.start_capture(connection)
    try:
        for scenario in bench.config.scenarios:

            def around(
                request: Request,
                url: str,
                issue: Callable[[], RequestTiming],
                scenario: Scenario = scenario,
            ) -> RequestTiming:
                """Capture the statements one request issues, as one block."""
                responses: list[RequestTiming] = []
                blocks.append(
                    query_capture.capture_block(
                        connection,
                        f'{scenario.name}/{request.name}',
                        url,
                        lambda: responses.append(issue()),
                    )
                )
                return responses[0]

            run_sequence(Client(bench.gunicorn.base_url), scenario, around=around)
    finally:
        query_capture.stop_capture(connection)
    query_capture.write_capture(capture, blocks)
    return blocks


def _parse_arguments(argv: Sequence[str] | None) -> argparse.Namespace:
    """Read the command line.

    Parameters:
        argv: The arguments, or None for the command line's.

    Returns:
        The parsed arguments.
    """
    parser = argparse.ArgumentParser(
        prog='python -m benchmarks.bench_db',
        description="Measure the schema one side's import built.",
    )
    parser.add_argument('--scale', choices=SCALES, required=True)
    parser.add_argument('--side', choices=SIDES, required=True)
    parser.add_argument('--pr', required=True)
    parser.add_argument('--session', required=True)
    parser.add_argument('--date', default=None)
    parser.add_argument('--python', type=Path, required=True)
    parser.add_argument('--repo-root', type=Path, required=True)
    parser.add_argument(
        '--schema', default=None, help="measure this schema instead of the import's"
    )
    parser.add_argument(
        '--dump-queries', action='store_true', help="capture and replay the scenarios' SQL"
    )
    parser.add_argument(
        '--commit-capture',
        action='store_true',
        help='also copy the capture to scenarios/queries.sql; only for the side whose '
        "checkout this harness runs from, and as the session's last command, since it "
        'changes that checkout',
    )
    parser.add_argument(
        '--ascii-columns', action='store_true', help='count non-ASCII STRING values'
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    """Measure the schema and record one ``db`` run.

    Parameters:
        argv: The arguments, or None for the command line's.
    """
    args = _parse_arguments(argv)
    if args.commit_capture and args.repo_root.resolve() != REPO_ROOT:
        # The committed capture is this checkout's own SQL; another side's would be
        # committed under this commit's name.
        raise SystemExit(
            f'--commit-capture copies only a capture of this checkout ({REPO_ROOT}), not of '
            f'{args.repo_root.resolve()}'
        )
    server_config, memcached_binary = load_server_config()
    reexec_with_socket(server_config, 'benchmarks.bench_db', sys.argv[1:] if argv is None else argv)
    server = MysqlServer(server_config)
    side = Side(python=args.python.absolute(), repo_root=args.repo_root.resolve())
    label = make_label(
        pr=args.pr, side=args.side, scale=args.scale, session=args.session, date=args.date
    )
    schema, holdings = side_schema(label, args.schema)
    run = new_run('db')
    metrics, details = run['metrics'], run['details']
    environment: dict[str, Any] = {**host_environment(), **side.environment()}
    with server.running():
        environment.update(server_environment(server))
        # The per-search tables an earlier web run left behind are not part of what
        # the import built, so they are emptied before anything is measured.
        reset_config = write_opus_config(
            label.scratch_dir / 'db' / 'opus.toml',
            schema=schema,
            pds3_holdings=holdings[0],
            pds4_holdings=holdings[1],
            run_dir=label.scratch_dir / 'db',
            cache_location=load_web_config().server.memcached_location,
        )
        reset_search_tables(
            side,
            Spelling.from_help(side.import_help()),
            server.client_environment(reset_config),
            label.scratch_dir / 'db' / 'logs' / build_run.ERRORS_LOG,
        )
        with contextlib.closing(server.connect()) as connection:
            tables = [
                str(row[0])
                for row in query(
                    connection,
                    'SELECT TABLE_NAME FROM information_schema.TABLES '
                    "WHERE TABLE_SCHEMA = %s AND TABLE_TYPE = 'BASE TABLE'",
                    [schema],
                )
            ]
            for table in tables:
                query(
                    connection,
                    f'ANALYZE TABLE {quote_identifier(schema)}.{quote_identifier(table)}',
                )
            query(connection, 'SET SESSION information_schema_stats_expiry = 0')
            statistics = table_statistics(connection, schema)
            pool = int(query(connection, 'SELECT @@innodb_buffer_pool_size')[0][0])
            fts = fulltext_bytes(connection, schema)
            data = sum(entry['data_bytes'] for entry in statistics.values())
            index = sum(entry['index_bytes'] for entry in statistics.values()) + fts
            metrics['db.schema.data_bytes'] = data
            metrics['db.schema.index_bytes'] = index
            metrics['db.schema.fulltext_bytes'] = fts
            metrics['db.schema.table_count'] = len(statistics)
            metrics['db.schema.total_to_buffer_pool'] = (data + index) / pool
            for name, entry in statistics.items():
                for key, value in entry.items():
                    metrics[f'db.table.{name}.{key}'] = value
            if 'obs_general' in statistics:
                details['preview_images'] = preview_images(
                    connection, schema, statistics['obs_general']['data_bytes']
                )
            details['index_usage'] = index_usage(connection, schema)
            if args.ascii_columns:
                details['ascii_columns'] = ascii_columns(connection, schema)
        details['schema'] = schema
        details['buffer_pool_bytes'] = pool
        environment['schema_bytes_beside_buffer_pool'] = {
            'schema_bytes': data + index,
            'innodb_buffer_pool_size': pool,
        }
        if args.dump_queries:
            _dump_and_replay(
                server=server,
                side=side,
                label=label,
                schema=schema,
                holdings=holdings,
                memcached_binary=memcached_binary,
                run=run,
                commit_capture=args.commit_capture,
            )
    path = append_runs(label, environment, [run])
    sys.stdout.write(f'recorded in {path}\n')


def _dump_and_replay(
    *,
    server: MysqlServer,
    side: Side,
    label: Label,
    schema: str,
    holdings: tuple[Path, Path],
    memcached_binary: str,
    run: dict[str, Any],
    commit_capture: bool,
) -> None:
    """Capture this side's scenario SQL and replay it at once, into the run's details.

    Parameters:
        server: The owned server.
        side: The side.
        label: The result label.
        schema: The side's schema.
        holdings: The holdings roots the application is given.
        memcached_binary: The memcached program.
        run: The run to record the plans in.
        commit_capture: Whether to copy the capture to `COMMITTED_CAPTURE` as well.
    """
    config = load_web_config(scale=label.scale)
    memcached = MemcachedServer(
        memcached_binary, config.server.memcached_port, config.server.memcached_mb
    )
    bench = WebBench(
        server=server,
        memcached=memcached,
        side=side,
        spelling=Spelling.from_help(side.import_help()),
        label=label,
        config=config,
        schema=schema,
        holdings=holdings,
    )
    capture = label.scratch_dir / f'queries_{label.side}.sql'
    memcached.start()
    try:
        bench.application_settings()
        blocks = dump_queries(bench, capture)
    finally:
        bench.gunicorn.stop()
        memcached.stop()
    with contextlib.closing(server.connect(schema)) as connection:
        entries = query_capture.replay(connection, blocks)
    run['details']['plans'] = entries
    run['details']['capture'] = str(capture)
    run['details']['web_scenario_hash'] = scenario_hash([config.path])
    # A block is compared with the other side's by its tag, never by statement: the
    # two sides may issue different statements for the same request.
    metrics = run['metrics']
    for entry in entries:
        plan = entry.get('plan')
        if plan is not None:
            name = f'db.plan.{entry["tag"]}'
            metrics[f'{name}.median_s'] = metrics.get(f'{name}.median_s', 0.0) + plan['median_s']
            metrics[f'{name}.rows_examined'] = (
                metrics.get(f'{name}.rows_examined', 0.0) + plan['rows_examined']
            )
    if commit_capture:
        shutil.copyfile(capture, COMMITTED_CAPTURE)


if __name__ == '__main__':
    main()
