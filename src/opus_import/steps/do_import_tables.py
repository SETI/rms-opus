"""Create the ``obs_`` and ``mult_`` tables an import writes into, and delete from them.

A bundle is replaced by deleting its rows from every ``obs_`` table and loading them
again. What fixes the order of a deletion is that the other ``obs_`` tables and ``cart``
carry foreign keys onto ``obs_general``, so a teardown goes other tables, then ``cart``,
then ``obs_general``, then the ``mult_`` tables, and a build goes the other way. The
``mult_`` tables come last on teardown and first on build by the same convention the
import follows -- an ``obs_`` row holds a ``mult_`` row id -- but no database constraint
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
    schema_version,
)

if TYPE_CHECKING:
    from opus_import.config_bundle_info import BundleInfo
    from opus_import.context import ImportContext
    from opus_import.import_util import TableSchema

#: The prefixes of the tables the import creates in any number -- the observation tables
#: and the mult tables.
OPUS_TABLE_PREFIXES = ('obs_', 'mult_')

#: The other tables the import creates, by exact name, including the tables a rebuild
#: that stopped part way leaves beside the live ones (`opus_import.table_swap`).
OPUS_TABLE_NAMES = (
    schema_version.SCHEMA_VERSION_TABLE,
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
    reference ``contexts``; every other exact name; and the ``mult_`` tables last.

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
        if name not in (schema_version.SCHEMA_VERSION_TABLE, 'cart', *_DEFINITIONS_TABLES)
    ]
    order += [name for name in prefixed if name.startswith('mult_')]
    for name in order:
        if name in present:
            db.drop_table(name)


def delete_bundle_from_obs_tables(ctx: ImportContext, bundle_id: str) -> None:
    """Delete one bundle's rows from every ``obs_`` table.

    Every other table goes before ``obs_general``. Each table's rows of the bundle are
    deleted in chunks of `ImportDBSuper.transaction_rows`: their ids are read a chunk at a
    time through the ``bundle_id`` key, which each of these tables is created with, so a
    large bundle's ids are never all held at once, and each chunk is one
    statement selecting by ``bundle_id`` and a range of the table's own ``id``, its own
    transaction, so no single statement holds a whole large bundle's undo and none reads
    rows outside its range -- a table a fresh import is still loading has no other key
    to find a bundle's rows by.

    The connection checks foreign keys while it deletes, so ``cart``'s cascade removes
    the cart rows that name the bundle's observations.

    Parameters:
        ctx: The import run's context, for the open database and the logger.
        bundle_id: The bundle whose rows go.
    """
    import_util.log_info(ctx, f'Deleting bundle "{bundle_id}"')

    db = ctx.db
    assert db is not None
    table_names = sorted(db.table_names(prefix=['obs_']))
    ordered = [name for name in table_names if name != 'obs_general']
    if 'obs_general' in table_names:
        ordered.append('obs_general')
    q = db.quote_identifier
    in_bundle = f'{q("bundle_id")}=%s'

    for table_name in ordered:
        after: int | None = None
        while True:
            # One page of the bundle's ids at a time, read through the bundle_id key,
            # so a large bundle's ids are never all held at once.
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
                break
            db.delete_rows(
                table_name,
                f'{in_bundle} AND {q("id")} BETWEEN %s AND %s',
                where_params=[bundle_id, ids[0], ids[-1]],
            )
            if len(ids) < db.transaction_rows:
                break
            after = ids[-1]


def create_tables_for_import(
    ctx: ImportContext, bundle_id: str
) -> tuple[dict[str, TableSchema], list[str]]:
    """Create the tables one bundle needs, and return the schemas that describe them.

    Each table `opus_import.config_data` lists is created if a packaged schema defines
    it, with the mission and instrument placeholders filled in for this bundle, along
    with the ``mult_`` tables the columns of those tables reference. A table with no
    schema is skipped, which is how a bundle ends up with only the tables its instrument
    has columns in.

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

    mult_table_schema = import_util.read_schema_for_table(ctx, 'mult_template')
    # mult_template.json is packaged with opus_import, so the schema is always found.
    assert mult_table_schema is not None

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

        # Create the referenced mult_ tables
        for table_column in table_schema:
            if table_column.get('put_mults_here', False) or table_column.get(
                'pi_referred_slug', False
            ):
                continue
            field_name = table_column['field_name']
            pi_form_type = table_column.get('pi_form_type', None)
            if pi_form_type is not None and pi_form_type.find(':') != -1:
                pi_form_type = pi_form_type[: pi_form_type.find(':')]
            if pi_form_type in config_data.GROUP_FORM_TYPES:
                mult_name = import_util.table_name_mult(table_name, field_name)
                schema = mult_table_schema
                db.create_table(mult_name, schema)

        db.create_table(table_name, table_schema)

    return table_schemas, table_names_in_order


def analyze_all_tables(ctx: ImportContext) -> None:
    """Recompute the key distribution statistics of every ``obs_`` and ``mult_`` table.

    Parameters:
        ctx: The import run's context, for the open database.
    """
    db = ctx.db
    assert db is not None
    table_names = sorted(db.table_names(prefix=['obs_', 'mult_']))
    for table_name in table_names:
        db.analyze_table(table_name)
