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

The ``obs_surface_geometry__<TARGET>`` tables are the exception throughout: there is one
per target an observation mentions, so which of them exist is not known until the
observations have been read, and they are created from a single template schema as the
targets turn up.

These are the table-preparation internals of `opus_import.steps.do_import`, not a step of
their own.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from opus_import import (
    bundle_registry,
    config_bundle_info,
    config_data,
    import_util,
    mult_fields,
    schema_version,
    table_keys,
)
from opus_import.mult_fields import MULT_TABLE

if TYPE_CHECKING:
    from collections.abc import Iterator

    from opus_import.config_bundle_info import BundleInfo
    from opus_import.context import ImportContext
    from opus_import.import_util import TableSchema
    from opus_import.importdb.super import ImportDBSuper

#: The prefixes of the tables the import creates in any number or under a ``mult_`` name
#: -- the observation tables, and ``mult_field`` and ``mult_group``.
OPUS_TABLE_PREFIXES = ('obs_', 'mult_')

#: The other tables the import creates, by exact name, including the tables a rebuild
#: that stopped part way leaves beside the live ones (`opus_import.table_swap`).
OPUS_TABLE_NAMES = (
    schema_version.SCHEMA_VERSION_TABLE,
    MULT_TABLE,
    'cart',
    bundle_registry.BUNDLE_REGISTRY_TABLE,
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
)

#: The ``definitions`` tables, which reference ``contexts`` and so are dropped before
#: every other exact name.
_DEFINITIONS_TABLES = ('definitions', 'definitions__new', 'definitions__old')


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

    The tables are the ones `OPUS_TABLE_PREFIXES` and `OPUS_TABLE_NAMES` name, dropped
    in an order the foreign keys allow: ``schema_version`` first, so an erase that stops
    part way leaves a schema nothing serves or deploys onto; then every ``obs_`` table
    but ``obs_general``; ``cart``; ``obs_general``; the ``definitions`` tables, which
    reference ``contexts``; every other exact name but ``mult``; and ``mult`` and every
    ``mult_`` table, ``mult_field`` and ``mult_group`` among them, last.

    Parameters:
        ctx: The import run's context, for the open database.
    """
    db = ctx.db
    assert db is not None
    present = set(db.table_names())
    prefixed = sorted(name for name in present if name.startswith(OPUS_TABLE_PREFIXES))

    order = [schema_version.SCHEMA_VERSION_TABLE]
    order += [name for name in prefixed if name.startswith('obs_') and name != 'obs_general']
    order += ['cart', 'obs_general', *_DEFINITIONS_TABLES]
    order += [
        name
        for name in OPUS_TABLE_NAMES
        if name
        not in (schema_version.SCHEMA_VERSION_TABLE, 'cart', MULT_TABLE, *_DEFINITIONS_TABLES)
    ]
    order += [MULT_TABLE, *(name for name in prefixed if name.startswith('mult_'))]
    for name in order:
        if name in present:
            db.drop_table(name)


def delete_bundle_from_obs_tables(ctx: ImportContext, bundle_id: str) -> None:
    """Delete one bundle's rows from every ``obs_`` table.

    Every other table goes before ``obs_general``, in chunks, each chunk one statement and
    its own transaction, so no single statement holds a whole large bundle's undo:

    * The tables `opus_import.table_keys.BUNDLE_KEYED_TABLE_PREFIXES` names hold
      ``bundle_id``, and are created with its key: their rows of the bundle are deleted
      by ``bundle_id`` and a range of the table's own ``id``,
      `ImportDBSuper.transaction_rows` rows at a time, read through that key.
    * Every other table's rows above ``obs_general``'s highest ``id`` are deleted. They
      are rows of observations whose ``obs_general`` rows were never loaded: a table is
      loaded once a transaction's worth of its rows wait, so a run that stopped partway
      through an index can leave a child's rows behind with no ``obs_general`` row to
      join, and the bundle's ids, handed out again from ``obs_general``'s highest, would
      collide with them.
    * Then the bundle's ``obs_general`` ids are read `ImportDBSuper.transaction_rows` at
      a time through ``obs_general``'s ``bundle_id`` key. For each chunk, every other
      table's rows of those observations are deleted by joining ``obs_general`` on
      ``obs_general_id``, which leads each such table's primary key -- for ``obs_files``
      every file of each observation -- and then the chunk's ``obs_general`` rows.

    Every statement selects by ``bundle_id`` and a range of ids, or by a range of the
    primary key, so none reads rows outside its range: a table a fresh import is still
    loading has no other key to find a bundle's rows by. The connection checks foreign
    keys while it deletes, so ``cart``'s cascade removes the cart rows that name the
    bundle's observations.

    Parameters:
        ctx: The import run's context, for the open database and the logger.
        bundle_id: The bundle whose rows go.
    """
    import_util.log_info(ctx, f'Deleting bundle "{bundle_id}"')

    db = ctx.db
    assert db is not None
    table_names = sorted(db.table_names(prefix=['obs_']))
    children = [name for name in table_names if name != 'obs_general']
    keyed = [name for name in children if table_keys.is_bundle_keyed_table(name)]
    joined = [name for name in children if name not in keyed]

    for table_name in keyed:
        for first_id, last_id in _bundle_id_ranges(db, table_name, bundle_id):
            _delete_id_range(db, table_name, bundle_id, first_id, last_id)
    if 'obs_general' not in table_names:
        return
    q = db.quote_identifier
    highest = db.find_column_max('obs_general', 'id') or 0
    for table_name in joined:
        db.delete_rows(table_name, f'{q("obs_general_id")} > %s', [highest])
    parent = q(db.JOINED_PARENT_ALIAS)
    in_chunk = f'{parent}.{q("bundle_id")} = %s AND {parent}.{q("id")} BETWEEN %s AND %s'
    for first_id, last_id in _bundle_id_ranges(db, 'obs_general', bundle_id):
        for table_name in joined:
            db.delete_joined_rows(
                table_name,
                'obs_general_id',
                'obs_general',
                'id',
                in_chunk,
                [bundle_id, first_id, last_id],
            )
        _delete_id_range(db, 'obs_general', bundle_id, first_id, last_id)


def _bundle_id_ranges(
    db: ImportDBSuper, table_name: str, bundle_id: str
) -> Iterator[tuple[int, int]]:
    """Yield the ranges of a table's ``id`` its rows of a bundle cover, a chunk at a time.

    Each range covers at most `ImportDBSuper.transaction_rows` of the bundle's rows, read
    through the table's ``bundle_id`` key, so a large bundle's ids are never all held at
    once. The caller deletes each range's rows before the next is read.

    Parameters:
        db: The open database.
        table_name: A table holding ``bundle_id`` and an ``id`` of its own.
        bundle_id: The bundle.

    Yields:
        The first and last id of each chunk.
    """
    q = db.quote_identifier
    in_bundle = f'{q("bundle_id")}=%s'
    after: int | None = None
    while True:
        if after is None:
            where, params = in_bundle, [bundle_id, db.transaction_rows]
        else:
            where = f'{in_bundle} AND {q("id")} > %s'
            params = [bundle_id, after, db.transaction_rows]
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
    columns in.

    The ``obs_surface_geometry__<TARGET>`` tables are deliberately **not** created: the
    target names are not known until the observations have been read. Its template
    schema is still returned, because the import needs the column names.

    Parameters:
        ctx: The import run's context, for the open database and the caches.
        bundle_id: The bundle whose tables to create.

    Returns:
        The schema of each table, keyed by table name, and the table names in the order
        the import should populate them.
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

        if table_name.startswith('obs_surface_geometry__'):
            # Note that we aren't replacing <TARGET> here because we don't know
            # the target name! We're only using this schema to get field names,
            # data source, source order, etc. The real use of the schema will be
            # later when we finally create and insert into the correct table for
            # each target.
            table_schema = import_util.read_schema_for_table(ctx, 'obs_surface_geometry_target')
        else:
            table_schema = import_util.read_schema_for_table(ctx, table_name)
        if table_schema is None:
            continue

        table_schemas[table_name] = table_schema
        table_names_in_order.append(table_name)

        if table_name.startswith('obs_surface_geometry__'):
            # Skip surface geo tables until they are needed
            continue

        db.create_table(table_name, table_schema)

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
