################################################################################
# do_import_tables.py
#
# Create, delete, and copy the obs_ tables an import writes into. These are the
# table-preparation internals of do_import, not a step of their own.
################################################################################

import re

from opus_import import config_bundle_info, config_data, import_util


def lookup_vol_info(bundle_id):
    for vol_info in config_bundle_info.BUNDLE_INFO:
        if re.fullmatch(vol_info[0], bundle_id) is not None:
            return vol_info[1]
    return None


def delete_all_obs_mult_tables(ctx, namespace):
    """Delete ALL import or permanent obs_ and mult_ tables."""

    table_names = ctx.db.table_names(namespace,
                                     prefix=['obs_', 'mult_', 'cart'])
    table_names = sorted(table_names)
    # This has to happen in four phases to handle foreign key contraints:
    # 1. All obs_ tables except obs_general
    for table_name in table_names:
        if (table_name.startswith('obs_') and table_name != 'obs_general'):
            ctx.db.drop_table(namespace, table_name)

    # 2. cart
    if 'cart' in table_names:
        ctx.db.drop_table(namespace, 'cart')

    # 3. obs_general
    if 'obs_general' in table_names:
        ctx.db.drop_table(namespace, 'obs_general')

    # 4. All mult_YYY tables
    for table_name in table_names:
        if table_name.startswith('mult_'):
            ctx.db.drop_table(namespace, table_name)


def delete_bundle_from_obs_tables(ctx, bundle_id, namespace):
    """Delete a single bundle from all import or permanent obs tables."""

    import_util.log_info(ctx, f'Deleting bundle "{bundle_id}" from {namespace} tables')

    table_names = ctx.db.table_names(namespace, prefix=['obs_'])
    table_names = sorted(table_names)
    q = ctx.db.quote_identifier
    where = f'{q("bundle_id")}="{bundle_id}"'

    # This has to happen in two phases to handle foreign key contraints:
    # 1. All tables except obs_general
    for table_name in table_names:
        if (table_name.startswith('obs_') and table_name != 'obs_general'):
            ctx.db.delete_rows(namespace, table_name, where)

    # 2. obs_general
    if 'obs_general' in table_names:
        ctx.db.delete_rows(namespace, 'obs_general', where)


def find_duplicate_opus_ids(ctx):
    """Find opus_ids that exist in both import and permanent tables.
       This can only happen in real life if the same opus_id appears in
       two different bundles, since normally we delete and entire bundle
       before getting here. Sadly this really happens with GOSSI."""

    if (not ctx.db.table_exists('import', 'obs_general') or
        not ctx.db.table_exists('perm', 'obs_general')):
        return []

    imp_obs_general_table_name = ctx.db.convert_raw_to_namespace('import',
                                                                 'obs_general')
    perm_obs_general_table_name = ctx.db.convert_raw_to_namespace('perm',
                                                                  'obs_general')

    q = ctx.db.quote_identifier
    cmd = f"""
        og.{q('opus_id')} FROM
        {q(perm_obs_general_table_name)} og,
        {q(imp_obs_general_table_name)} iog WHERE
        og.{q('opus_id')} = iog.{q('opus_id')}"""
    res = ctx.db.general_select(cmd)
    return [x[0] for x in res]


def delete_opus_id_from_obs_tables(ctx, opus_id, namespace):
    """Delete a single opus_id from all import or permanent obs tables."""

    import_util.log_info(ctx, f'Deleting opus_id "{opus_id}" from {namespace} tables')

    table_names = ctx.db.table_names(namespace, prefix=['obs_'])
    table_names = sorted(table_names)
    q = ctx.db.quote_identifier
    where = f'{q("opus_id")}="{opus_id}"'

    # This has to happen in two phases to handle foreign key contraints:
    # 1. All tables except obs_general
    for table_name in table_names:
        if (table_name.startswith('obs_') and table_name != 'obs_general'):
            ctx.db.delete_rows(namespace, table_name, where)

    # 2. obs_general
    if 'obs_general' in table_names:
        ctx.db.delete_rows(namespace, 'obs_general', where)


def delete_duplicate_opus_id_from_perm_tables(ctx):
    """Find duplicate opus_ids and delete them from the permanent obs tables."""
    opus_ids = find_duplicate_opus_ids(ctx)
    for opus_id in opus_ids:
        delete_opus_id_from_obs_tables(ctx, opus_id, 'perm')


def create_tables_for_import(ctx, bundle_id, namespace):
    """Create the import or permanent obs_ tables and all the mult tables they
       reference. This does NOT create the target-specific obs_surface_geometry
       tables because we don't yet know what target names we have."""

    vol_info = lookup_vol_info(bundle_id)
    instrument_obj = vol_info['instrument_class'](ctx, bundle=bundle_id)
    mission_id = instrument_obj.mission_id
    instrument_id = instrument_obj.instrument_id
    mission_name = config_data.MISSION_ID_TO_MISSION_TABLE_SFX[mission_id]

    mult_table_schema = import_util.read_schema_for_table(ctx, 'mult_template')

    table_schemas = {}
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
                if (ctx.db.create_table(namespace, mult_name, schema) and
                    namespace == 'import'):
                    ctx.created_import_mult_tables.add(mult_name)

        ctx.db.create_table(namespace, table_name, table_schema)

    return table_schemas, table_names_in_order


def copy_bundle_from_import_to_permanent(ctx, bundle_id):
    """Copy a single bundle from all import obs tables to the corresponding
       permanent tables. Create the permanent obs tables if they don't already
       exist. As usual, we have to treat the obs_surface_geometry__<T> tables
       specially."""

    import_util.log_info(ctx, f'Copying bundle "{bundle_id}" from import to permanent')

    q = ctx.db.quote_identifier

    _table_schemas, table_names_in_order = create_tables_for_import(
                                                    ctx, bundle_id, namespace='perm')
    for table_name in table_names_in_order:
        if table_name.startswith('obs_surface_geometry__'):
            continue
        import_util.log_debug(ctx, f'Copying table "{table_name}"')
        where = f'{q("bundle_id")}="{bundle_id}"'
        ctx.db.copy_rows_between_namespaces('import', 'perm', table_name,
                                            where=where)

    # For obs_surface_geometry__<T> we don't even know the target names at
    # this point, so we actually have to look at the table names in the database
    # to see what to copy! Also the tables may not have been created yet.

    surface_geo_table_names = ctx.db.table_names(
                                    'import', prefix='obs_surface_geometry__')
    for table_name in sorted(surface_geo_table_names):
        target_name = table_name.replace('obs_surface_geometry__', '')
        if not ctx.db.table_exists('perm', table_name):
            table_schema = import_util.read_schema_for_table(
                                            ctx, 'obs_surface_geometry_target',
                                            replace=[
               ('<TARGET>', import_util.table_name_for_sfc_target(target_name)),
               ('<SLUGTARGET>', import_util.slug_name_for_sfc_target(target_name))])
            ctx.db.create_table('perm', table_name, table_schema)
        import_util.log_debug(ctx, f'Copying table "{table_name}"')
        where = f'{q("bundle_id")}="{bundle_id}"'
        ctx.db.copy_rows_between_namespaces('import', 'perm', table_name,
                                            where=where)

def read_existing_import_opus_id(ctx):
    """Return a list of all opus_id used in the import tables. Used to check
       for duplicates during import."""
    import_util.log_debug(ctx, 'Collecting previous import opus_ids')

    imp_obs_general_table_name = ctx.db.convert_raw_to_namespace('import',
                                                                 'obs_general')
    if (not ctx.db.table_exists('import', 'obs_general') and
        ctx.args.read_only):
        # It's OK if we don't have this table in read-only mode, because perhaps
        # nobody ever created it before.
        return []

    q = ctx.db.quote_identifier
    rows = ctx.db.general_select(
        f'{q("opus_id")} FROM {q(imp_obs_general_table_name)}')

    return [x[0] for x in rows]


def analyze_all_tables(ctx, namespace):
    """Analyze ALL import or permanent (as specified by namespace)
    obs_ and mult_ tables."""

    table_names = ctx.db.table_names(namespace, prefix=['obs_', 'mult_'])
    table_names = sorted(table_names)
    for table_name in table_names:
        ctx.db.analyze_table(namespace, table_name)
