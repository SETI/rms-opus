"""Create, delete and copy the ``obs_`` tables an import writes into.

The tables are dropped and rebuilt rather than updated, both in the import namespace at
the start of a run and in the permanent one when the run is copied over. Three
constraints fix the order everything here happens in: every other ``obs_`` table has a
foreign key onto ``obs_general``, ``cart`` has one too, and the ``mult_`` tables are
referenced by the ``obs_`` tables. So a teardown goes other tables, then ``cart``, then
``obs_general``, then the ``mult_`` tables, and a build goes the other way.

The ``obs_surface_geometry__<TARGET>`` tables are the exception throughout: there is one
per target an observation mentions, so which of them exist is not known until the
observations have been read, and they are created from a single template schema as the
targets turn up.

These are the table-preparation internals of `opus_import.steps.do_import`, not a step of
their own.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any

from opus_import import config_bundle_info, config_data, import_util

if TYPE_CHECKING:
    from opus_import.context import ImportContext
    from opus_import.import_util import TableSchema
    from opus_import.importdb.super import Namespace


def lookup_vol_info(bundle_id: str) -> dict[str, Any] | None:
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


def delete_all_obs_mult_tables(ctx: ImportContext, namespace: Namespace) -> None:
    """Delete every ``obs_`` and ``mult_`` table in a namespace, and ``cart`` with them.

    Parameters:
        ctx: The import run's context, for the open database.
        namespace: The namespace to empty.
    """
    db = ctx.db
    assert db is not None
    table_names = sorted(db.table_names(namespace,
                                        prefix=['obs_', 'mult_', 'cart']))
    # This has to happen in four phases to handle foreign key contraints:
    # 1. All obs_ tables except obs_general
    for table_name in table_names:
        if (table_name.startswith('obs_') and table_name != 'obs_general'):
            db.drop_table(namespace, table_name)

    # 2. cart
    if 'cart' in table_names:
        db.drop_table(namespace, 'cart')

    # 3. obs_general
    if 'obs_general' in table_names:
        db.drop_table(namespace, 'obs_general')

    # 4. All mult_YYY tables
    for table_name in table_names:
        if table_name.startswith('mult_'):
            db.drop_table(namespace, table_name)


def delete_bundle_from_obs_tables(ctx: ImportContext, bundle_id: str,
                                  namespace: Namespace) -> None:
    """Delete one bundle's rows from every ``obs_`` table in a namespace.

    Parameters:
        ctx: The import run's context, for the open database and the logger.
        bundle_id: The bundle whose rows go.
        namespace: The namespace to delete from.
    """
    import_util.log_info(ctx, f'Deleting bundle "{bundle_id}" from {namespace} tables')

    db = ctx.db
    assert db is not None
    table_names = sorted(db.table_names(namespace, prefix=['obs_']))
    q = db.quote_identifier
    where = f'{q("bundle_id")}=%s'
    where_params = [bundle_id]

    # This has to happen in two phases to handle foreign key contraints:
    # 1. All tables except obs_general
    for table_name in table_names:
        if (table_name.startswith('obs_') and table_name != 'obs_general'):
            db.delete_rows(namespace, table_name, where,
                           where_params=where_params)

    # 2. obs_general
    if 'obs_general' in table_names:
        db.delete_rows(namespace, 'obs_general', where,
                       where_params=where_params)


def find_duplicate_opus_ids(ctx: ImportContext) -> list[str]:
    """Return the opus_ids that are in both the import and the permanent tables.

    A bundle is deleted from a namespace before it is written there, so an id can only
    be in both if two different bundles produced it. That does happen -- Galileo SSI is
    the known case.

    Parameters:
        ctx: The import run's context, for the open database.

    Returns:
        The duplicated ids, or none at all if either ``obs_general`` table is missing.
    """
    db = ctx.db
    assert db is not None
    if (not db.table_exists('import', 'obs_general') or
        not db.table_exists('perm', 'obs_general')):
        return []

    imp_obs_general_table_name = db.convert_raw_to_namespace('import',
                                                             'obs_general')
    perm_obs_general_table_name = db.convert_raw_to_namespace('perm',
                                                              'obs_general')

    q = db.quote_identifier
    cmd = f"""
        og.{q('opus_id')} FROM
        {q(perm_obs_general_table_name)} og,
        {q(imp_obs_general_table_name)} iog WHERE
        og.{q('opus_id')} = iog.{q('opus_id')}"""
    res = db.general_select(cmd)
    return [x[0] for x in res]


def delete_opus_id_from_obs_tables(ctx: ImportContext, opus_id: str,
                                   namespace: Namespace) -> None:
    """Delete one observation's rows from every ``obs_`` table in a namespace.

    Parameters:
        ctx: The import run's context, for the open database and the logger.
        opus_id: The observation whose rows go.
        namespace: The namespace to delete from.
    """
    import_util.log_info(ctx, f'Deleting opus_id "{opus_id}" from {namespace} tables')

    db = ctx.db
    assert db is not None
    table_names = sorted(db.table_names(namespace, prefix=['obs_']))
    q = db.quote_identifier
    where = f'{q("opus_id")}=%s'
    where_params = [opus_id]

    # This has to happen in two phases to handle foreign key contraints:
    # 1. All tables except obs_general
    for table_name in table_names:
        if (table_name.startswith('obs_') and table_name != 'obs_general'):
            db.delete_rows(namespace, table_name, where,
                           where_params=where_params)

    # 2. obs_general
    if 'obs_general' in table_names:
        db.delete_rows(namespace, 'obs_general', where,
                       where_params=where_params)


def delete_duplicate_opus_id_from_perm_tables(ctx: ImportContext) -> None:
    """Delete from the permanent tables every observation the import also produced.

    The import's copy is the one being kept, so the permanent one has to go before it is
    written over.

    Parameters:
        ctx: The import run's context, for the open database and the logger.
    """
    opus_ids = find_duplicate_opus_ids(ctx)
    for opus_id in opus_ids:
        delete_opus_id_from_obs_tables(ctx, opus_id, 'perm')


def create_tables_for_import(ctx: ImportContext, bundle_id: str,
                             namespace: Namespace
                             ) -> tuple[dict[str, TableSchema], list[str]]:
    """Create the tables one bundle needs, and return the schemas that describe them.

    Every table `opus_import.config_data` lists is created, with the mission and
    instrument placeholders filled in for this bundle, along with each ``mult_`` table
    the columns of those tables reference. A table with no packaged schema is skipped,
    which is how a bundle ends up with only the tables its instrument has columns in.

    The ``obs_surface_geometry__<TARGET>`` tables are deliberately **not** created: the
    target names are not known until the observations have been read. Its template
    schema is still returned, because the import needs the column names.

    Parameters:
        ctx: The import run's context, for the open database and the caches.
        bundle_id: The bundle whose tables to create.
        namespace: The namespace to create them in.

    Returns:
        The schema of each table, keyed by table name, and the table names in the order
        the import should populate them.
    """
    db = ctx.db
    assert db is not None
    vol_info = lookup_vol_info(bundle_id)
    # Every caller has already established that OPUS knows this bundle: the import
    # path checks it, and the two copy paths take their ids from rows the import
    # wrote. Without an entry there is no instrument class and no table to create.
    assert vol_info is not None
    instrument_obj = vol_info['instrument_class'](ctx, bundle=bundle_id)
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
            table_schema = import_util.read_schema_for_table(
                                            ctx, 'obs_surface_geometry_target')
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
            if (table_column.get('put_mults_here', False) or
                table_column.get('pi_referred_slug', False)):
                continue
            field_name = table_column['field_name']
            pi_form_type = table_column.get('pi_form_type', None)
            if pi_form_type is not None and pi_form_type.find(':') != -1:
                pi_form_type = pi_form_type[:pi_form_type.find(':')]
            if pi_form_type in config_data.GROUP_FORM_TYPES:
                mult_name = import_util.table_name_mult(table_name, field_name)
                schema = mult_table_schema
                if (db.create_table(namespace, mult_name, schema) and
                    namespace == 'import'):
                    ctx.created_import_mult_tables.add(mult_name)

        db.create_table(namespace, table_name, table_schema)

    return table_schemas, table_names_in_order


def copy_bundle_from_import_to_permanent(ctx: ImportContext, bundle_id: str) -> None:
    """Copy one bundle's rows from the import tables to the permanent ones.

    The permanent tables are created first if they do not exist. The surface geometry
    tables are found by listing the import namespace rather than from a schema, because
    only the import run knows which targets turned up, and each one that has no
    permanent counterpart is created from the template schema with this target's name
    substituted in.

    Parameters:
        ctx: The import run's context, for the open database and the logger.
        bundle_id: The bundle to copy.
    """
    import_util.log_info(ctx, f'Copying bundle "{bundle_id}" from import to permanent')

    db = ctx.db
    assert db is not None
    q = db.quote_identifier

    _table_schemas, table_names_in_order = create_tables_for_import(
                                                    ctx, bundle_id, namespace='perm')
    for table_name in table_names_in_order:
        if table_name.startswith('obs_surface_geometry__'):
            continue
        import_util.log_debug(ctx, f'Copying table "{table_name}"')
        where = f'{q("bundle_id")}=%s'
        db.copy_rows_between_namespaces('import', 'perm', table_name,
                                        where=where,
                                        where_params=[bundle_id])

    # For obs_surface_geometry__<T> we don't even know the target names at
    # this point, so we actually have to look at the table names in the database
    # to see what to copy! Also the tables may not have been created yet.

    surface_geo_table_names = db.table_names(
                                    'import', prefix='obs_surface_geometry__')
    for table_name in sorted(surface_geo_table_names):
        target_name = table_name.replace('obs_surface_geometry__', '')
        if not db.table_exists('perm', table_name):
            table_schema = import_util.read_schema_for_table(
                                            ctx, 'obs_surface_geometry_target',
                                            replace=[
               ('<TARGET>', import_util.table_name_for_sfc_target(target_name)),
               ('<SLUGTARGET>', import_util.slug_name_for_sfc_target(target_name))])
            # obs_surface_geometry_target.json is packaged with opus_import.
            assert table_schema is not None
            db.create_table('perm', table_name, table_schema)
        import_util.log_debug(ctx, f'Copying table "{table_name}"')
        where = f'{q("bundle_id")}=%s'
        db.copy_rows_between_namespaces('import', 'perm', table_name,
                                        where=where,
                                        where_params=[bundle_id])

def read_existing_import_opus_id(ctx: ImportContext) -> list[str]:
    """Return every opus_id the import tables already hold.

    An import that adds to previous import tables has to know which observations are
    already there, so that it can report a duplicate rather than writing one.

    Parameters:
        ctx: The import run's context, for the open database, the arguments and the
            logger.

    Returns:
        The ids, or none at all in a read-only run where the import ``obs_general``
        table has never been created.
    """
    import_util.log_debug(ctx, 'Collecting previous import opus_ids')

    db = ctx.db
    assert db is not None
    imp_obs_general_table_name = db.convert_raw_to_namespace('import',
                                                             'obs_general')
    if (not db.table_exists('import', 'obs_general') and
        ctx.args.read_only):
        # It's OK if we don't have this table in read-only mode, because perhaps
        # nobody ever created it before.
        return []

    q = db.quote_identifier
    rows = db.general_select(
        f'{q("opus_id")} FROM {q(imp_obs_general_table_name)}')

    return [x[0] for x in rows]


def analyze_all_tables(ctx: ImportContext, namespace: Namespace) -> None:
    """Recompute the key distribution statistics of every table in a namespace.

    Parameters:
        ctx: The import run's context, for the open database.
        namespace: The namespace whose ``obs_`` and ``mult_`` tables to analyze.
    """
    db = ctx.db
    assert db is not None
    table_names = sorted(db.table_names(namespace, prefix=['obs_', 'mult_']))
    for table_name in table_names:
        db.analyze_table(namespace, table_name)
