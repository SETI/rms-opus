"""Add the secondary keys a fresh import left out: the step behind ``--create-indexes``.

A fresh import creates each observation and mult table with only the keys a load needs
(`opus_import.table_keys.create_time_keys`), so each bundle's rows are written into as
few indexes as possible. This step, the first of finalization, adds the rest once, in
three phases:

1. **The ``FULLTEXT`` keys and the plain keys**. Each ``FULLTEXT`` key is a statement of
   its own, since the server builds one per statement, and comes first among its table's
   statements: the first ``FULLTEXT`` key on a table rebuilds the table, which would
   build again every key added before it. The ``FULLTEXT`` keys are built with the ngram
   parser, so the step refuses, before it builds anything, when the server's
   ``ngram_token_size`` is not `opus_import.table_keys.NGRAM_TOKEN_SIZE`; every import
   session turns the stopword list off (`opus_import.importdb.mysql.ImportDBMySQL`). The
   plain keys are grouped per table into ``ALTER TABLE ... ADD KEY ..., ADD KEY ...``
   statements. Different tables' statements run at once over ``[import] index_workers``
   connections (`ImportDBSuper.build_indexes`), each table analyzed first so that its
   keys' estimates count the rows its loads wrote. Each statement's sort memory is sized
   to the estimated sort of its largest key, within a share of a quarter of the server's
   buffer pool divided among the indexes it builds at once, and its sorts go to
   ``[import] server_tmpdir`` when that is set. When the free space there can be read,
   the statements running at once must fit it together: a table's plain keys are split
   into as many statements as that takes, and a key whose own estimate exceeds the whole
   of it is refused. Otherwise each table's plain keys go in one statement, and the
   estimate is logged.
2. **The foreign keys**, one at a time with ``foreign_key_checks`` off, after every plain
   key, since each takes an exclusive lock on the table it references.
3. **ANALYZE** of every table that gained a key.

It is idempotent: the keys a table already has, compared by kind and ordered columns
rather than by name, are skipped, so a rerun after an interruption adds only what is
missing, and on a schema with every key it does nothing. Each statement's and each
table's wall-clock goes into ``--timing-json``, as ``create_indexes:<table>:<keys>`` and
``create_indexes:<table>``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from opus_config import get_config
from opus_import import import_util
from opus_import.importdb.super import ImportDBError, IndexStatement
from opus_import.table_keys import (
    KEY_FILTERED_TABLE_PREFIXES,
    NGRAM_TOKEN_SIZE,
    TableKey,
    add_secondary_indexes,
)

if TYPE_CHECKING:
    from collections.abc import Sequence

    from opus_import.context import ImportContext
    from opus_import.importdb.super import ImportDBSuper, SchemaColumn


def _key_label(keys: Sequence[TableKey]) -> str:
    """Return what a statement adds, as the timings name it.

    Parameters:
        keys: The keys the statement adds.

    Returns:
        The keys' descriptions, joined by ``+``.
    """
    return '+'.join(key.describe() for key in keys)


def _group_keys(
    db: ImportDBSuper,
    table_name: str,
    schema: Sequence[SchemaColumn],
    keys: Sequence[TableKey],
    space_budget: int | None,
) -> list[IndexStatement]:
    """Group one table's plain keys into the statements that add them.

    Parameters:
        db: The open database.
        table_name: The table.
        schema: Its schema.
        keys: The keys to add, none of them a foreign key.
        space_budget: The temporary space the statements running at once may hold
            together, or None for none.

    Returns:
        One statement for all the keys without a budget; with one, as many as keep each
        statement's estimate within it, keys in order. A key whose own estimate exceeds
        the budget is a statement of its own, which `ImportDBSuper.build_indexes` refuses.
    """
    sized = [(key, db.key_space_bytes(table_name, schema, key)) for key in keys]
    groups: list[list[tuple[TableKey, int]]] = []
    for key, space in sized:
        if (
            groups
            and space_budget is not None
            and sum(s for _, s in groups[-1]) + space > space_budget
        ):
            groups.append([])
        if not groups:
            groups.append([])
        groups[-1].append((key, space))
    return [
        IndexStatement(
            sql=db.add_keys_statement(table_name, [key for key, _ in group]),
            label=_key_label([key for key, _ in group]),
            space_bytes=sum(space for _, space in group),
            sort_bytes=max(space for _, space in group),
            key_count=len(group),
        )
        for group in groups
    ]


def _fulltext_statements(
    db: ImportDBSuper,
    table_name: str,
    schema: Sequence[SchemaColumn],
    keys: Sequence[TableKey],
    have: Sequence[TableKey],
) -> list[IndexStatement]:
    """Return one statement for each ``FULLTEXT`` key of a table.

    The first ``FULLTEXT`` key on a table rebuilds it, which copies its rows and sorts
    each secondary key it already has again. So when the table has none yet, the first
    statement's estimate is its own sort, the table's data bytes and the sorts of the keys
    it has, and its sort memory is sized for the largest of those keys, shared among
    them, as a statement building them would be; every later statement sorts only its
    tokens, with the sort memory at the server's setting.

    Parameters:
        db: The open database.
        table_name: The table.
        schema: Its schema.
        keys: The ``FULLTEXT`` keys to add.
        have: The keys the table has, as the server reports them.

    Returns:
        The statements, in the keys' order.
    """
    statements = [
        IndexStatement(
            sql=db.add_fulltext_key_statement(table_name, key),
            label=_key_label([key]),
            space_bytes=db.key_space_bytes(table_name, schema, key),
            sort_bytes=0,
            key_count=1,
        )
        for key in keys
    ]
    if statements and not any(key.kind == 'fulltext' for key in have):
        rebuilt = [
            db.key_space_bytes(table_name, schema, key)
            for key in have
            if key.kind in ('unique', 'key')
        ]
        first = statements[0]
        statements[0] = IndexStatement(
            sql=first.sql,
            label=first.label,
            space_bytes=first.space_bytes + db.table_data_bytes(table_name) + sum(rebuilt),
            sort_bytes=max(rebuilt, default=0),
            key_count=max(1, len(rebuilt)),
        )
    return statements


def _ngram_token_size_problem(db: ImportDBSuper) -> str | None:
    """Say why the server cannot build the ``FULLTEXT`` keys, if it cannot.

    Parameters:
        db: The open database.

    Returns:
        The error to log when the server's ``ngram_token_size`` is not
        `opus_import.table_keys.NGRAM_TOKEN_SIZE`, or None when it is.
    """
    token_size = db.read_ngram_token_size()
    if token_size == NGRAM_TOKEN_SIZE:
        return None
    return (
        f"The server's ngram_token_size is {token_size}, and the FULLTEXT keys need "
        f'{NGRAM_TOKEN_SIZE}: ngram_token_size is read only when the server starts, so set '
        f"it to {NGRAM_TOKEN_SIZE} in the server's configuration and restart it"
    )


def create_indexes(ctx: ImportContext) -> bool:
    """Add every secondary key the schema files declare and an observation or mult table lacks.

    Parameters:
        ctx: The import run's context, for the configuration, the open database and the
            logger.

    Returns:
        True when every key is in place; False when a build failed, a key's space
        estimate exceeds the budget, or a ``FULLTEXT`` key is missing and the server's
        ``ngram_token_size`` is not `opus_import.table_keys.NGRAM_TOKEN_SIZE`, each of
        which is logged. The last refuses before any key is built.
    """
    db = ctx.db
    assert db is not None
    config = get_config().import_
    existing = db.read_table_keys()
    space_budget = db.index_space_budget(config.server_tmpdir)
    if space_budget is None:
        import_util.log_info(ctx, 'Building keys with no space budget')
    else:
        import_util.log_info(ctx, f'Building keys within a space budget of {space_budget} bytes')

    key_statements: dict[str, list[IndexStatement]] = {}
    foreign: list[IndexStatement] = []
    foreign_tables: set[str] = set()
    total_estimate = 0
    token_size_checked = False
    for table_name in sorted(db.table_names(prefix=list(KEY_FILTERED_TABLE_PREFIXES))):
        schema = import_util.read_schema_for_existing_table(ctx, table_name)
        if schema is None:
            continue
        have = existing.get(table_name, [])
        missing = [key for key in add_secondary_indexes(table_name, schema) if key not in have]
        fulltext_keys = [key for key in missing if key.kind == 'fulltext']
        plain_keys = [key for key in missing if key.kind not in ('foreign', 'fulltext')]
        if fulltext_keys and not token_size_checked:
            problem = _ngram_token_size_problem(db)
            if problem is not None:
                import_util.log_error(ctx, problem)
                return False
            token_size_checked = True
        if fulltext_keys or plain_keys:
            # The estimates read the server's row count, which can predate the loads
            # until the table is analyzed.
            db.analyze_table(table_name)
            key_statements[table_name] = _fulltext_statements(
                db, table_name, schema, fulltext_keys, have
            )
            if plain_keys:
                key_statements[table_name] += _group_keys(
                    db, table_name, schema, plain_keys, space_budget
                )
            total_estimate += sum(statement.space_bytes for statement in key_statements[table_name])
        for key in missing:
            if key.kind == 'foreign':
                foreign.append(
                    IndexStatement(
                        sql=db.add_foreign_key_statement(table_name, key),
                        label=f'{table_name}:{key.describe()}',
                        space_bytes=0,
                        sort_bytes=0,
                        key_count=0,
                    )
                )
                foreign_tables.add(table_name)
    if not key_statements and not foreign:
        import_util.log_info(ctx, 'Every table has every key its schema declares')
        return True
    import_util.log_info(
        ctx,
        f'Adding keys to {len(key_statements)} tables over {ctx.index_workers} connections, '
        f'an estimated {total_estimate} bytes of temporary space in all',
    )

    try:
        with ctx.timed('create_indexes:keys'):
            built = db.build_indexes(
                key_statements,
                workers=ctx.index_workers,
                server_tmpdir=config.server_tmpdir,
                space_budget=space_budget,
            )
        with ctx.timed('create_indexes:foreign_keys'):
            foreign_timed = db.add_foreign_keys(foreign)
    except ValueError as e:
        import_util.log_error(ctx, str(e))
        return False
    except ImportDBError:
        # build_indexes and add_foreign_keys have logged every failure.
        ctx.mark_bad_data()
        return False
    for table_name, timed in built.items():
        ctx.step_timings[f'create_indexes:{table_name}'] = sum(seconds for _, seconds in timed)
        for label, seconds in timed:
            ctx.step_timings[f'create_indexes:{table_name}:{label}'] = seconds
    for label, seconds in foreign_timed:
        ctx.step_timings[f'create_indexes:{label}'] = seconds

    with ctx.timed('create_indexes:analyze'):
        for table_name in sorted(set(key_statements) | foreign_tables):
            db.analyze_table(table_name)
    return True
