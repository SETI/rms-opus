"""Add the secondary keys a fresh import left out: the step behind ``--create-indexes``.

A fresh import creates each observation and mult table with only the keys a load needs
(`opus_import.table_keys.create_time_keys`), so each bundle's rows are written into as
few indexes as possible. This step, the first of finalization, adds the rest once, in
three phases:

1. **The plain keys**, grouped per table into ``ALTER TABLE ... ADD KEY ..., ADD KEY
   ...`` statements, run for different tables at once over ``[import] index_workers``
   connections (`ImportDBSuper.build_indexes`). Each statement's sort memory is sized to
   the estimated sort of its largest key, within a share of a quarter of the server's
   buffer pool, and its sorts go to ``[import] server_tmpdir`` when that is set. When the free space there can be read, the
   statements running at once must fit it together: a table's keys are split into as
   many statements as that takes, and a key whose own estimate exceeds the whole of it
   is refused. Otherwise each table's keys go in one statement, and the estimate is
   logged.
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
from opus_import.table_keys import KEY_FILTERED_TABLE_PREFIXES, TableKey, add_secondary_indexes

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
    sized = [(key, db.key_space_bytes('perm', table_name, schema, key)) for key in keys]
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
            sql=db.add_keys_statement('perm', table_name, [key for key, _ in group]),
            label=_key_label([key for key, _ in group]),
            space_bytes=sum(space for _, space in group),
            sort_bytes=max(space for _, space in group),
        )
        for group in groups
    ]


def create_indexes(ctx: ImportContext) -> bool:
    """Add every secondary key the schema files declare and an observation or mult table lacks.

    Parameters:
        ctx: The import run's context, for the configuration, the open database and the
            logger.

    Returns:
        True when every key is in place; False when a build failed or a key's space
        estimate exceeds the budget, which is logged.
    """
    db = ctx.db
    assert db is not None
    config = get_config().import_
    existing = db.read_table_keys('perm')
    space_budget = db.index_space_budget(config.server_tmpdir)
    if space_budget is None:
        import_util.log_info(ctx, 'Building keys with no space budget')
    else:
        import_util.log_info(ctx, f'Building keys within a space budget of {space_budget} bytes')

    plain: dict[str, list[IndexStatement]] = {}
    foreign: list[IndexStatement] = []
    foreign_tables: set[str] = set()
    total_estimate = 0
    for table_name in sorted(db.table_names('perm', prefix=list(KEY_FILTERED_TABLE_PREFIXES))):
        schema = import_util.read_schema_for_existing_table(ctx, table_name)
        if schema is None:
            continue
        have = existing.get(table_name, [])
        missing = [key for key in add_secondary_indexes(table_name, schema) if key not in have]
        plain_keys = [key for key in missing if key.kind != 'foreign']
        if plain_keys:
            plain[table_name] = _group_keys(db, table_name, schema, plain_keys, space_budget)
            total_estimate += sum(statement.space_bytes for statement in plain[table_name])
        for key in missing:
            if key.kind == 'foreign':
                foreign.append(
                    IndexStatement(
                        sql=db.add_foreign_key_statement('perm', table_name, key),
                        label=f'{table_name}:{key.describe()}',
                        space_bytes=0,
                        sort_bytes=0,
                    )
                )
                foreign_tables.add(table_name)
    if not plain and not foreign:
        import_util.log_info(ctx, 'Every table has every key its schema declares')
        return True
    import_util.log_info(
        ctx,
        f'Adding keys to {len(plain)} tables over {config.index_workers} connections, '
        f'an estimated {total_estimate} bytes of temporary space in all',
    )

    try:
        with ctx.timed('create_indexes:keys'):
            built = db.build_indexes(
                plain,
                workers=config.index_workers,
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
        ctx.import_has_bad_data = True
        return False
    for table_name, timed in built.items():
        ctx.step_timings[f'create_indexes:{table_name}'] = sum(seconds for _, seconds in timed)
        for label, seconds in timed:
            ctx.step_timings[f'create_indexes:{table_name}:{label}'] = seconds
    for label, seconds in foreign_timed:
        ctx.step_timings[f'create_indexes:{label}'] = seconds

    with ctx.timed('create_indexes:analyze'):
        for table_name in sorted(set(plain) | foreign_tables):
            db.analyze_table('perm', table_name)
    return True
