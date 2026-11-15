"""Create the ``obs_`` and mult tables an import writes into, and delete from them.

A bundle is replaced by deleting its rows from every ``obs_`` table and loading them
again; its ``mult`` rows stay, and finalization deletes the values no observation
references (`opus_import.steps.do_finalize_mult`). What fixes the order of a deletion is
that the other ``obs_`` tables and ``cart`` carry foreign keys onto ``obs_general``, so a
teardown goes other tables, then ``cart``, then ``obs_general``, then the mult tables,
and a build goes the other way. The mult tables (``mult``, ``mult_field`` and
``mult_group``) come last on teardown and first on build by the same convention the
import follows -- an ``obs_`` row holds a ``mult`` row's id -- but no database constraint
enforces that one.

Scorched earth (`delete_all_opus_tables`) drops every table the import creates, which is
every table in the schema but Django's own: the ones `OPUS_TABLE_PREFIXES` and
`OPUS_TABLE_NAMES` name.

These are the table-preparation internals of `opus_import.steps.do_import`, not a step of
their own.
"""

from __future__ import annotations

import functools
import re
from typing import TYPE_CHECKING

from opus_import import (
    bundle_registry,
    config_bundle_info,
    config_data,
    generations,
    import_processes,
    import_util,
    list_junctions,
    mult_fields,
    schema_version,
    table_keys,
)
from opus_import.mult_fields import MULT_TABLE

if TYPE_CHECKING:
    from collections.abc import Iterator, Sequence

    from opus_import.config_bundle_info import BundleInfo
    from opus_import.context import ImportContext
    from opus_import.import_util import TableSchema
    from opus_import.importdb.super import ImportDBSuper

#: The prefixes of the tables the import creates in any number or under a ``mult_`` name
#: -- the observation tables, and ``mult_field`` and ``mult_group``.
OPUS_TABLE_PREFIXES = ('obs_', 'mult_')

#: The other tables the import creates, by exact name, including the tables a rebuild
#: that stopped part way leaves beside the live ones, and those a generation's switch
#: keeps until the purge (`opus_import.table_swap`).
OPUS_TABLE_NAMES = (
    schema_version.SCHEMA_VERSION_TABLE,
    MULT_TABLE,
    'cart',
    bundle_registry.BUNDLE_REGISTRY_TABLE,
    import_processes.IMPORT_PROCESS_TABLE,
    'param_info',
    'partables',
    'table_names',
    'contexts',
    'definitions',
    'user_searches',
    'search_results',
    'param_info__new',
    'param_info__old',
    'partables__new',
    'partables__old',
    'table_names__new',
    'table_names__old',
    'contexts__new',
    'contexts__old',
    'definitions__new',
    'definitions__old',
    'param_info__prev',
    'partables__prev',
    'table_names__prev',
)

#: The ``definitions`` tables, which reference ``contexts`` and so are dropped before
#: every other exact name.
_DEFINITIONS_TABLES = ('definitions', 'definitions__new', 'definitions__old')

#: The exact names dropped after every other one, beside the ``mult_`` tables: an
#: observation row holds a ``mult`` row's id.
_DROPPED_LAST = (MULT_TABLE,)


def lookup_vol_info(bundle_id: str) -> BundleInfo | None:
    """Return what `opus_import.config_bundle_info` says about a bundle.

    Parameters:
        bundle_id: The bundle to look up.

    Returns:
        The first entry whose pattern matches the whole bundle id, or None if no entry
        does, which means OPUS does not know how to import that bundle.
    """
    for vol_info in config_bundle_info.BUNDLE_INFO:
        if re.fullmatch(vol_info[0], bundle_id) is not None:
            return vol_info[1]
    return None


def opus_imports_bundle(bundle_id: str) -> bool:
    """Return whether OPUS imports a bundle, rather than deliberately skipping it.

    Parameters:
        bundle_id: The bundle.

    Returns:
        False exactly when `opus_import.config_bundle_info` has an entry for the bundle
        with no instrument class; True otherwise, including for a bundle with no entry,
        whose import then fails.
    """
    vol_info = lookup_vol_info(bundle_id)
    return vol_info is None or vol_info['instrument_class'] is not None


def delete_all_opus_tables(ctx: ImportContext) -> None:
    """Drop every table the import creates, leaving Django's own.

    The ``obs_general`` view goes first, with ``DROP VIEW``, since ``DROP TABLE`` refuses
    a view. The tables are the ones `OPUS_TABLE_PREFIXES` and `OPUS_TABLE_NAMES` name,
    dropped in an order the foreign keys allow: ``schema_version`` first, so an erase that stops
    part way leaves a schema nothing serves or deploys onto; then every ``obs_`` table
    but ``obs_general``; ``cart``; ``obs_general``; the ``definitions`` tables, which
    reference ``contexts``; every other exact name but ``mult``; and ``mult`` and every
    ``mult_`` table, ``mult_field`` and ``mult_group`` among them, last.

    Parameters:
        ctx: The import run's context, for the open database.
    """
    db = ctx.db
    assert db is not None
    db.drop_obs_general_view()
    present = set(db.table_names())
    prefixed = sorted(name for name in present if name.startswith(OPUS_TABLE_PREFIXES))

    order = [schema_version.SCHEMA_VERSION_TABLE]
    order += [name for name in prefixed if name.startswith('obs_') and name != 'obs_general']
    order += ['cart', 'obs_general', *_DEFINITIONS_TABLES]
    first = (schema_version.SCHEMA_VERSION_TABLE, 'cart', *_DEFINITIONS_TABLES)
    order += [name for name in OPUS_TABLE_NAMES if name not in (*first, *_DROPPED_LAST)]
    order += [name for name in OPUS_TABLE_NAMES if name in _DROPPED_LAST]
    order += [name for name in prefixed if name.startswith('mult_')]
    for name in order:
        if name in present:
            db.drop_table(name)


def delete_bundle_from_obs_tables(ctx: ImportContext, bundle_id: str) -> None:
    """Delete one bundle's rows from every ``obs_`` table.

    The tables are read from the server first, not taken from what the connection has
    seen: another process importing into the schema may have created one since, and a
    table left out would keep the bundle's rows.

    Every other table goes before ``obs_general``, in chunks, each chunk one statement and
    its own transaction, so no single statement holds a whole large bundle's undo:

    * Every other table's rows in the bundle's registered id range above the highest
      ``obs_general`` id in that range are deleted. They are rows of observations whose
      ``obs_general`` rows were never loaded: a table is loaded once a transaction's worth
      of its rows wait, so a run that stopped partway through an index can leave a
      child's rows behind with no ``obs_general`` row to join, and the bundle's ids,
      handed out again from the start of its range, would collide with them. No other
      bundle's rows lie in the range, so another process importing into the schema at the
      same time loses nothing. A bundle the registry does not hold has no range, and this
      part is skipped.
    * Then the bundle's ``obs_general`` ids are read `ImportDBSuper.transaction_rows` at
      a time through ``obs_general``'s ``bundle_id`` key. For each chunk, every other
      table's rows of those observations are deleted by joining ``obs_general`` on
      ``obs_general_id``, which leads each such table's primary key -- for ``obs_files``
      every file of each observation -- or a key of its own on that column, which
      ``obs_surface_geometry_target`` has because its primary key starts with
      ``target_name``; and then the chunk's ``obs_general`` rows.

    Every statement selects by ``bundle_id`` and a range of ids, or by a range of
    ``obs_general_id``, through a key a table is created with, so none reads rows outside
    its range. Each is run again when the server reports a deadlock or a lock wait
    timeout (`ImportDBSuper.retrying`). The connection checks foreign keys while it
    deletes, so ``cart``'s cascade removes the cart rows that name the bundle's
    observations.

    With a pending generation (`opus_import.generations`) the bundle's rows of earlier
    generations are not deleted but retired (`retire_bundle_rows`), since the served
    generation still shows them; only the rows the pending generation added, which lie
    in the range its registration gave the bundle, are deleted as above.

    Parameters:
        ctx: The import run's context, for the open database and the logger.
        bundle_id: The bundle whose rows go.
    """
    import_util.log_info(ctx, f'Deleting bundle "{bundle_id}"')

    db = ctx.db
    assert db is not None
    db.forget_table_names()
    table_names = sorted(db.table_names(prefix=['obs_']))
    joined = [name for name in table_names if not table_keys.is_bundle_keyed_table(name)]

    if 'obs_general' not in table_names:
        return
    q = db.quote_identifier
    description = f'Deleting bundle "{bundle_id}"'
    registered = bundle_registry.bundle_range(ctx, bundle_id)
    pending = ctx.pending_generation
    within: tuple[int, int] | None = None
    if pending is not None:
        retire_bundle_rows(ctx, bundle_id, pending)
        if registered is None or registered.generation != pending:
            # The pending generation added none of the bundle's rows.
            return
        within = (registered.first_id, registered.end - 1)
    if registered is not None:
        last = registered.end - 1
        in_range = f'{q("id")} BETWEEN %s AND %s'
        highest = db.general_select(
            f'MAX({q("id")}) FROM {q("obs_general")} WHERE {in_range}',  # nosec B608
            [registered.first_id, last],
        )[0][0]
        above = registered.first_id if highest is None else int(highest) + 1
        in_orphans = f'{q("obs_general_id")} BETWEEN %s AND %s'
        for table_name in joined:
            db.retrying(
                description,
                functools.partial(db.delete_rows, table_name, in_orphans, [above, last]),
            )
    parent = q(db.JOINED_PARENT_ALIAS)
    in_chunk = f'{parent}.{q("bundle_id")} = %s AND {parent}.{q("id")} BETWEEN %s AND %s'
    for first_id, last_id in _bundle_id_ranges(db, 'obs_general', bundle_id, within):
        for table_name in joined:
            db.retrying(
                description,
                functools.partial(
                    db.delete_joined_rows,
                    table_name,
                    'obs_general_id',
                    'obs_general',
                    'id',
                    in_chunk,
                    [bundle_id, first_id, last_id],
                ),
            )
        db.retrying(
            description,
            functools.partial(_delete_id_range, db, 'obs_general', bundle_id, first_id, last_id),
        )


def retire_bundle_rows(ctx: ImportContext, bundle_id: str, generation: int) -> int:
    """Retire a bundle's observations at a pending generation, which hides them from it.

    Every ``obs_general`` row of the bundle that an earlier generation added and none has
    retired gets ``removed_generation`` set to the pending generation. The bundle's rows
    are walked through the ``bundle_id`` key a range of ids at a time, each range holding
    at most `ImportDBSuper.transaction_rows` of them (`_bundle_id_ranges`), and each
    statement reads only its range, so no row is read twice. The rows stay until the
    purge; the served generation goes on showing them.

    Parameters:
        ctx: The import run's context, for the open database.
        bundle_id: The bundle.
        generation: The pending generation.

    Returns:
        How many rows were retired.
    """
    db = ctx.db
    assert db is not None
    q = db.quote_identifier
    where = (
        f'{q("bundle_id")}=%s AND {q("id")} BETWEEN %s AND %s AND '
        f'{q(generations.ADDED_GENERATION_COLUMN)} < %s AND '
        f'{q(generations.REMOVED_GENERATION_COLUMN)} IS NULL'
    )
    retired = 0
    for first_id, last_id in _bundle_id_ranges(db, 'obs_general', bundle_id):
        retired += db.retrying(
            f'Retiring bundle "{bundle_id}"',
            functools.partial(
                db.update_row,
                'obs_general',
                {generations.REMOVED_GENERATION_COLUMN: generation},
                where,
                [bundle_id, first_id, last_id, generation],
            ),
        )
    return retired


def restore_retired_rows(
    ctx: ImportContext, obs_general_ids: Sequence[int], generation: int
) -> None:
    """Show again observations a pending generation retired, as abandoning it does.

    `ImportDBSuper.transaction_rows` observations to a statement, each found by its
    primary key, so a statement reads and locks only the rows it changes.

    Parameters:
        ctx: The import run's context, for the open database.
        obs_general_ids: The observations, read from a scan for ``removed_generation``.
        generation: The pending generation; a row another generation retired is left.
    """
    db = ctx.db
    assert db is not None
    q = db.quote_identifier
    for start in range(0, len(obs_general_ids), db.transaction_rows):
        chunk = list(obs_general_ids[start : start + db.transaction_rows])
        placeholders = ','.join(['%s'] * len(chunk))
        db.retrying(
            f'Restoring the rows generation {generation} retired',
            functools.partial(
                db.update_row,
                'obs_general',
                {generations.REMOVED_GENERATION_COLUMN: None},
                f'{q("id")} IN ({placeholders}) AND {q(generations.REMOVED_GENERATION_COLUMN)}=%s',
                [*chunk, generation],
            ),
        )


def delete_observations(ctx: ImportContext, obs_general_ids: Sequence[int]) -> None:
    """Delete observations by ``obs_general`` id from every observation table.

    `ImportDBSuper.transaction_rows` observations to a statement: every other ``obs_``
    table's rows of a chunk first, by ``obs_general_id``, then the chunk's ``obs_general``
    rows. The connection checks foreign keys, so a row that still references a deleted
    observation is refused rather than orphaned, and ``cart``'s cascade removes the cart
    rows that name one.

    Parameters:
        ctx: The import run's context, for the open database.
        obs_general_ids: The observations.
    """
    db = ctx.db
    assert db is not None
    q = db.quote_identifier
    db.forget_table_names()
    other_tables = [name for name in sorted(db.table_names(prefix='obs_')) if name != 'obs_general']
    for start in range(0, len(obs_general_ids), db.transaction_rows):
        chunk = list(obs_general_ids[start : start + db.transaction_rows])
        placeholders = ','.join(['%s'] * len(chunk))
        for table_name in other_tables:
            db.delete_rows(
                table_name, f'{q("obs_general_id")} IN ({placeholders})', where_params=chunk
            )
        db.delete_rows('obs_general', f'{q("id")} IN ({placeholders})', where_params=chunk)


def _bundle_id_ranges(
    db: ImportDBSuper, table_name: str, bundle_id: str, within: tuple[int, int] | None = None
) -> Iterator[tuple[int, int]]:
    """Yield the ranges of a table's ``id`` its rows of a bundle cover, a chunk at a time.

    Each range covers at most `ImportDBSuper.transaction_rows` of the bundle's rows, read
    through the table's ``bundle_id`` key, so a large bundle's ids are never all held at
    once. The caller deletes each range's rows before the next is read.

    Parameters:
        db: The open database.
        table_name: A table holding ``bundle_id`` and an ``id`` of its own.
        bundle_id: The bundle.
        within: The first and last id of the only rows to cover, or None for all.

    Yields:
        The first and last id of each chunk.
    """
    q = db.quote_identifier
    in_bundle = f'{q("bundle_id")}=%s'
    bundle_params: list[object] = [bundle_id]
    if within is not None:
        in_bundle += f' AND {q("id")} BETWEEN %s AND %s'
        bundle_params += list(within)
    after: int | None = None
    while True:
        if after is None:
            where, params = in_bundle, [*bundle_params, db.transaction_rows]
        else:
            where = f'{in_bundle} AND {q("id")} > %s'
            params = [*bundle_params, after, db.transaction_rows]
        ids = [
            row[0]
            for row in db.general_select(
                f'{q("id")} FROM {q(table_name)} WHERE {where} ORDER BY {q("id")} LIMIT %s',
                params,
            )
        ]
        if not ids:
            return
        yield ids[0], ids[-1]
        if len(ids) < db.transaction_rows:
            return
        after = ids[-1]


def _delete_id_range(
    db: ImportDBSuper, table_name: str, bundle_id: str, first_id: int, last_id: int
) -> None:
    """Delete a table's rows of a bundle whose ``id`` lies in a range.

    Parameters:
        db: The open database.
        table_name: A table holding ``bundle_id`` and an ``id`` of its own.
        bundle_id: The bundle.
        first_id: The range's first id.
        last_id: Its last.
    """
    q = db.quote_identifier
    db.delete_rows(
        table_name,
        f'{q("bundle_id")}=%s AND {q("id")} BETWEEN %s AND %s',
        where_params=[bundle_id, first_id, last_id],
    )


def create_tables_for_import(
    ctx: ImportContext, bundle_id: str
) -> tuple[dict[str, TableSchema], list[str]]:
    """Create the tables one bundle needs, and return the schemas that describe them.

    The mult tables are created first if the schema lacks them, and then each table
    `opus_import.config_data` lists is created if a packaged schema defines it, with the
    mission and instrument placeholders filled in for this bundle. A table with no schema
    is skipped, which is how a bundle ends up with only the tables its instrument has
    columns in. Each ``mult_list`` column's junction table
    (`opus_import.list_junctions`) is created after the table holding the column.

    Parameters:
        ctx: The import run's context, for the open database and the caches.
        bundle_id: The bundle whose tables to create.

    Returns:
        The schema of each table, keyed by table name, and the table names in the order
        the import should populate them; neither names a junction table, whose rows the
        import derives from its observation table's (`opus_import.list_junctions`).
    """
    db = ctx.db
    assert db is not None
    vol_info = lookup_vol_info(bundle_id)
    # The import has already established that OPUS knows this bundle. Without an entry
    # there is no instrument class and no table to create.
    assert vol_info is not None
    # An entry with no instrument class is one OPUS ignores, and the import skips a
    # bundle of that kind before it reaches this function.
    instrument_class = vol_info['instrument_class']
    assert instrument_class is not None
    instrument_obj = instrument_class(ctx, bundle=bundle_id)
    mission_id = instrument_obj.mission_id
    instrument_id = instrument_obj.instrument_id
    mission_name = config_data.MISSION_ID_TO_MISSION_TABLE_SFX[mission_id]

    mult_fields.create_mult_tables(ctx)

    table_schemas: dict[str, TableSchema] = {}
    table_names_in_order = []
    for table_name in config_data.TABLES_TO_POPULATE:
        if instrument_id is not None:
            table_name = table_name.replace('<INST>', instrument_id.lower())
        table_name = table_name.replace('<MISSION>', mission_name.lower())

        table_schema = import_util.read_schema_for_table(ctx, table_name)
        if table_schema is None:
            continue

        table_schemas[table_name] = table_schema
        table_names_in_order.append(table_name)
        db.create_table(table_name, table_schema)
        for column in list_junctions.list_columns(table_schema):
            junction = list_junctions.junction_table(table_name, column)
            junction_schema = import_util.read_schema_for_table(ctx, junction)
            # Every mult_list column has a packaged junction schema
            # (tests/opus_import/test_table_schemas.py).
            assert junction_schema is not None
            db.create_table(junction, junction_schema)

    return table_schemas, table_names_in_order


def analyze_all_tables(ctx: ImportContext) -> None:
    """Recompute the key distribution statistics of every ``obs_`` and mult table.

    Parameters:
        ctx: The import run's context, for the open database.
    """
    db = ctx.db
    assert db is not None
    table_names = sorted(db.table_names(prefix=['obs_', *mult_fields.MULT_TABLES]))
    for table_name in table_names:
        db.analyze_table(table_name)
