################################################################################
# do_import.py
#
# This is the actual top-level import process.
################################################################################

import csv
import json
import os
import re
import traceback

import pdsfile

import opus_support

import config_bundle_info
import config_data
import do_cart
import do_django
import impglobals
import import_util


################################################################################
# TABLE PREPARATION
################################################################################

def _lookup_vol_info(bundle_id):
    for vol_info in config_bundle_info.BUNDLE_INFO:
        if re.fullmatch(vol_info[0], bundle_id) is not None:
            return vol_info[1]
    return None


def delete_all_obs_mult_tables(namespace):
    """Delete ALL import or permanent obs_ and mult_ tables."""

    table_names = impglobals.DATABASE.table_names(namespace,
                                                  prefix=['obs_', 'mult_', 'cart'])
    table_names = sorted(table_names)
    # This has to happen in four phases to handle foreign key contraints:
    # 1. All obs_ tables except obs_general
    for table_name in table_names:
        if (table_name.startswith('obs_') and table_name != 'obs_general'):
            impglobals.DATABASE.drop_table(namespace, table_name)

    # 2. cart
    if 'cart' in table_names:
        impglobals.DATABASE.drop_table(namespace, 'cart')

    # 3. obs_general
    if 'obs_general' in table_names:
        impglobals.DATABASE.drop_table(namespace, 'obs_general')

    # 4. All mult_YYY tables
    for table_name in table_names:
        if table_name.startswith('mult_'):
            impglobals.DATABASE.drop_table(namespace, table_name)


def delete_bundle_from_obs_tables(bundle_id, namespace):
    """Delete a single bundle from all import or permanent obs tables."""

    import_util.log_info(f'Deleting bundle "{bundle_id}" from {namespace} tables')

    table_names = impglobals.DATABASE.table_names(namespace, prefix=['obs_', 'mult_'])
    table_names = sorted(table_names)
    q = impglobals.DATABASE.quote_identifier
    where = f'{q("bundle_id")}="{bundle_id}"'

    # This has to happen in two phases to handle foreign key contraints:
    # 1. All tables except obs_general
    for table_name in table_names:
        if (table_name.startswith('obs_') and table_name != 'obs_general'):
            impglobals.DATABASE.delete_rows(namespace, table_name, where)

    # 2. obs_general
    if 'obs_general' in table_names:
        impglobals.DATABASE.delete_rows(namespace, 'obs_general', where)


def find_duplicate_opus_ids():
    """Find opus_ids that exist in both import and permanent tables.
       This can only happen in real life if the same opus_id appears in
       two different bundles, since normally we delete and entire bundle
       before getting here. Sadly this really happens with GOSSI."""

    if (not impglobals.DATABASE.table_exists('import', 'obs_general') or
        not impglobals.DATABASE.table_exists('perm', 'obs_general')):
        return []

    imp_obs_general_table_name = impglobals.DATABASE.convert_raw_to_namespace(
                                                            'import', 'obs_general')
    perm_obs_general_table_name = impglobals.DATABASE.convert_raw_to_namespace(
                                                            'perm', 'obs_general')

    q = impglobals.DATABASE.quote_identifier
    cmd = f"""
        og.{q('opus_id')} FROM
        {q(perm_obs_general_table_name)} og,
        {q(imp_obs_general_table_name)} iog WHERE
        og.{q('opus_id')} = iog.{q('opus_id')}"""
    res = impglobals.DATABASE.general_select(cmd)
    return [x[0] for x in res]


def delete_opus_id_from_obs_tables(opus_id, namespace):
    """Delete a single opus_id from all import or permanent obs tables."""

    import_util.log_info(f'Deleting opus_id "{opus_id}" from {namespace} tables')

    table_names = impglobals.DATABASE.table_names(namespace, prefix=['obs_', 'mult_'])
    table_names = sorted(table_names)
    q = impglobals.DATABASE.quote_identifier
    where = f'{q("opus_id")}="{opus_id}"'

    # This has to happen in two phases to handle foreign key contraints:
    # 1. All tables except obs_general
    for table_name in table_names:
        if (table_name.startswith('obs_') and table_name != 'obs_general'):
            impglobals.DATABASE.delete_rows(namespace, table_name, where)

    # 2. obs_general
    if 'obs_general' in table_names:
        impglobals.DATABASE.delete_rows(namespace, 'obs_general', where)


def delete_duplicate_opus_id_from_perm_tables():
    """Find duplicate opus_ids and delete them from the permanent obs tables."""
    opus_ids = find_duplicate_opus_ids()
    for opus_id in opus_ids:
        delete_opus_id_from_obs_tables(opus_id, 'perm')


def create_tables_for_import(bundle_id, namespace):
    """Create the import or permanent obs_ tables and all the mult tables they
       reference. This does NOT create the target-specific obs_surface_geometry
       tables because we don't yet know what target names we have."""

    vol_info = _lookup_vol_info(bundle_id)
    instrument_obj = vol_info['instrument_class'](bundle=bundle_id)
    mission_id = instrument_obj.mission_id
    instrument_id = instrument_obj.instrument_id
    mission_name = config_data.MISSION_ID_TO_MISSION_TABLE_SFX[mission_id]

    mult_table_schema = import_util.read_schema_for_table('mult_template')

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
                                                'obs_surface_geometry_target')
        else:
            table_schema = import_util.read_schema_for_table(table_name)
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
                if (impglobals.DATABASE.create_table(namespace, mult_name, schema) and
                    namespace == 'import'):
                    _CREATED_IMP_MULT_TABLES.add(mult_name)

        impglobals.DATABASE.create_table(namespace, table_name, table_schema)

    return table_schemas, table_names_in_order


def copy_bundle_from_import_to_permanent(bundle_id):
    """Copy a single bundle from all import obs tables to the corresponding
       permanent tables. Create the permanent obs tables if they don't already
       exist. As usual, we have to treat the obs_surface_geometry__<T> tables
       specially."""

    import_util.log_info(f'Copying bundle "{bundle_id}" from import to permanent')

    q = impglobals.DATABASE.quote_identifier

    table_schemas, table_names_in_order = create_tables_for_import(bundle_id,
                                                                   namespace='perm')
    for table_name in table_names_in_order:
        if table_name.startswith('obs_surface_geometry__'):
            continue
        import_util.log_debug(f'Copying table "{table_name}"')
        where = f'{q("bundle_id")}="{bundle_id}"'
        impglobals.DATABASE.copy_rows_between_namespaces('import', 'perm',
                                                         table_name,
                                                         where=where)

    # For obs_surface_geometry__<T> we don't even know the target names at
    # this point, so we actually have to look at the table names in the database
    # to see what to copy! Also the tables may not have been created yet.

    surface_geo_table_names = impglobals.DATABASE.table_names(
                                            'import',
                                            prefix='obs_surface_geometry__')
    for table_name in sorted(surface_geo_table_names):
        target_name = table_name.replace('obs_surface_geometry__', '')
        if not impglobals.DATABASE.table_exists('perm', table_name):
            table_schema = import_util.read_schema_for_table(
                                            'obs_surface_geometry_target',
                                            replace=[
               ('<TARGET>', import_util.table_name_for_sfc_target(target_name)),
               ('<SLUGTARGET>', import_util.slug_name_for_sfc_target(target_name))])
            impglobals.DATABASE.create_table('perm', table_name, table_schema)
        import_util.log_debug(f'Copying table "{table_name}"')
        where = f'{q("bundle_id")}="{bundle_id}"'
        impglobals.DATABASE.copy_rows_between_namespaces('import', 'perm',
                                                         table_name,
                                                         where=where)

def read_existing_import_opus_id():
    """Return a list of all opus_id used in the import tables. Used to check
       for duplicates during import."""
    import_util.log_debug('Collecting previous import opus_ids')

    imp_obs_general_table_name = impglobals.DATABASE.convert_raw_to_namespace(
                                                        'import', 'obs_general')
    if (not impglobals.DATABASE.table_exists('import', 'obs_general') and
        impglobals.ARGUMENTS.read_only):
        # It's OK if we don't have this table in read-only mode, because perhaps
        # nobody ever created it before.
        return []

    q = impglobals.DATABASE.quote_identifier
    rows = impglobals.DATABASE.general_select(
        f'{q("opus_id")} FROM {q(imp_obs_general_table_name)}')

    return [x[0] for x in rows]


def analyze_all_tables(namespace):
    """Analyze ALL import or permanent (as specified by namespace)
    obs_ and mult_ tables."""

    table_names = impglobals.DATABASE.table_names(namespace, prefix=['obs_', 'mult_'])
    table_names = sorted(table_names)
    for table_name in table_names:
        impglobals.DATABASE.analyze_table(namespace, table_name)


################################################################################
# MULT TABLE HANDLING
################################################################################

# We cache the contents of mult_ tables we've touched so we don't have to keep
# reading them from the database.
# We initialize them to {} here because do_partables needs these to have values
# and they are normally only set during a bundle import.
_MULT_TABLE_CACHE = {}
_CREATED_IMP_MULT_TABLES = {}
_MODIFIED_MULT_TABLES = {}

def _mult_table_column_names(table_name):
    """Return a list of the columns found in a mult tables. This isn't
       constant because various *_target_name tables have an extra
       column used for target name grouping."""

    column_list = ['id', 'value', 'label','disp_order', 'display',
                   'grouping', 'group_disp_order', 'aliases']
    return column_list

def _convert_sql_response_to_mult_table(mult_table_name, rows):
    """Given a set of rows from an SQL query of a mult table, convert it into
       our internal dictionary representation."""
    mult_rows = []
    for row in rows:
        if len(row) == 8:
            (id_num, value, label, disp_order,
             display, grouping, group_disp_order, aliases) = row
        else:
            # preprogrammed mult options list doesn't have aliases field
            (id_num, value, label, disp_order,
             display, grouping, group_disp_order) = row
            aliases = None

        row_dict = {
            'id': id_num,
            'value': value,
            'label': str(label),
            'aliases': aliases,
            'disp_order': disp_order,
            'display': display,
            'grouping': grouping,
            'group_disp_order': group_disp_order
        }
        mult_rows.append(row_dict)
    return mult_rows

def read_or_create_mult_table(mult_table_name, table_column):
    """Given a mult table name, either read the table from the database or
       return the cached version if we previously read it."""

    if mult_table_name in _MULT_TABLE_CACHE:
        return _MULT_TABLE_CACHE[mult_table_name]

    if 'mult_options' in table_column:
        if not impglobals.ARGUMENTS.import_suppress_mult_messages:
            import_util.log_debug(f'Using preprogrammed mult table "{mult_table_name}"')
        mult_rows = _convert_sql_response_to_mult_table(mult_table_name,
                                                        table_column['mult_options'])
        _MULT_TABLE_CACHE[mult_table_name] = mult_rows
        _MODIFIED_MULT_TABLES[mult_table_name] = table_column
        return mult_rows

    # If there is already an import version of the table, it means this is a
    # second run of the import pipeline without copying over to the new
    # database, so read the contents of the import version. But it's also
    # possible we just created the mult table during the initalization phase
    # and it's empty. In that case ignore the import one.
    # Otherwise, if there is already a non-import version, read that one.
    # And if there's no table to be found anyway, create a new one.
    use_namespace = None

    if (mult_table_name not in _CREATED_IMP_MULT_TABLES and
        impglobals.DATABASE.table_exists('import', mult_table_name)):
        # Previous import table available
        use_namespace = 'import'

    elif impglobals.DATABASE.table_exists('perm', mult_table_name):
        use_namespace = 'perm'
        # If we just created an import version but are reading the permanent
        # version, we have to write out the import version before doing
        # anything else too
        if mult_table_name in _CREATED_IMP_MULT_TABLES:
            _MODIFIED_MULT_TABLES[mult_table_name] = table_column

    if use_namespace is not None:
        ns_mult_table_name = (
            impglobals.DATABASE.convert_raw_to_namespace(use_namespace, mult_table_name))
        if not impglobals.ARGUMENTS.import_suppress_mult_messages:
            import_util.log_debug(f'Reading from mult table "{ns_mult_table_name}"')
        rows = impglobals.DATABASE.read_rows(use_namespace,
                                             mult_table_name,
                                             _mult_table_column_names(mult_table_name))
        mult_rows = _convert_sql_response_to_mult_table(mult_table_name, rows)
        _MULT_TABLE_CACHE[mult_table_name] = mult_rows
        return mult_rows

    rows = []
    _MULT_TABLE_CACHE[mult_table_name] = rows
    return rows


def mult_table_lookup_id(table_name, field_name, table_column, val):
    """Lookup the id for a single value in the cached version of a mult table."""
    mult_table_name = import_util.table_name_mult(table_name, field_name)
    mult_table = read_or_create_mult_table(mult_table_name, table_column)
    if val is not None:
        val = str(val)
    for entry in mult_table:
        if entry['value'] == val:
            # The value is already in the mult table, so we're done here
            return entry['id']
    return None


def update_mult_table(table_name, field_name, table_column, val, label, aliases=None,
                      disp='Y', disp_order=None, grouping=None, group_disp_order=None):
    """Update a single value in the cached version of a mult table."""

    mult_table_name = import_util.table_name_mult(table_name, field_name)
    mult_table = read_or_create_mult_table(mult_table_name, table_column)
    if val is not None:
        val = str(val)
    for entry in mult_table:
        if entry['value'] == val:
            # The value is already in the mult table, so we're done here
            return entry['id']

    if 'mult_options' in table_column:
        import_util.log_nonrepeating_error(
            f'Unable to add value "{val}" to preprogrammed mult table '
            f'"{mult_table_name}"')
        return 0

    label = str(label)

    if disp_order is None:
        # No disp_order specified, so make one up
        # Update the display_order
        (form_type, form_type_format,
         form_type_unit_id) = opus_support.parse_form_type(table_column['pi_form_type'])
        parse_func = opus_support.get_single_parse_function(form_type_unit_id)

        # See if all values in the mult table are numeric
        all_numeric = True
        for row in mult_table:
            if (row['label'] is None or
                str(row['label']).upper() == 'NONE' or
                str(row['label']).upper() == 'NULL'):
                continue
            try:
                float(row['label'])
            except ValueError:
                all_numeric = False
                break
        try:
            float(label)
        except ValueError:
            all_numeric = False

        # Null always comes last. N/A always comes before that.
        # None always comes before that.
        # Yes comes before No. On comes before Off.
        if label in [None, 'NULL', 'Null']:
            if parse_func is not None:
                disp_order = label
            else:
                disp_order = 'zzz' + str(label)
        elif label == 'N/A':
            if parse_func is not None:
                disp_order = label
            else:
                disp_order = 'zzy' + str(label)
        elif label in ['NONE', 'None']:
            if parse_func is not None:
                disp_order = label
            else:
                disp_order = 'zzx' + str(label)
        elif parse_func:
            try:
                disp_order = '%030.9f' % parse_func(str(val))
            except Exception as e:
                import_util.log_nonrepeating_error(
f'Unable to parse "{label}" for type "range_func_name": {e}')
                disp_order = label
        elif all_numeric:
            disp_order = '%20.9f' % float(label)
        elif label in ('Yes', 'On'):
            disp_order = 'zzAYes'
        elif label in ('No', 'Off'):
            disp_order = 'zzBNo'
        else:
            disp_order = label

    if isinstance(disp_order, (int, float)):
        disp_order = '%030.9f' % disp_order
    if len(mult_table) == 0:
        next_id = 0
    else:
        next_id = max([x['id'] for x in mult_table])+1
    if label is None:
        label = 'N/A'

    # If we didn't specify the group_disp_order, we will order groups
    # alphabetically
    if grouping is not None and group_disp_order is None:
        group_disp_order = grouping

    new_entry = {
        'id': next_id,
        'value': val,
        'label': label,
        'aliases': aliases,
        'disp_order': disp_order,
        'display': disp, # default display: 'Y'
        'grouping': grouping,
        'group_disp_order': group_disp_order
    }
    mult_table.append(new_entry)

    _MODIFIED_MULT_TABLES[mult_table_name] = table_column
    if not impglobals.ARGUMENTS.import_suppress_mult_messages:
        import_util.log_info(f'Added new value "{val}" ("{label}") to mult table '+
                             f'"{mult_table_name}"')

    return next_id


def dump_import_mult_tables():
    """Dump all of the cached import mult tables into the database."""

    for mult_table_name in sorted(_MODIFIED_MULT_TABLES):
        rows = _MULT_TABLE_CACHE[mult_table_name]
        # Insert or update all the rows
        imp_mult_table_name = impglobals.DATABASE.convert_raw_to_namespace(
                                                        'import', mult_table_name)
        import_util.log_debug(f'Writing mult table "{imp_mult_table_name}"')
        impglobals.DATABASE.upsert_rows('import', mult_table_name, 'id', rows)
        # If we wrote out a mult table, that means we didn't just create it
        # empty anymore, so remove it from _CREATED_IMP_MULT_TABLES.
        if mult_table_name in _CREATED_IMP_MULT_TABLES:
            _CREATED_IMP_MULT_TABLES.remove(mult_table_name)


def copy_mult_from_import_to_permanent():
    """Copy ALL mult tables from import to permament. We have to do all tables,
       not just the ones that have changed, because tables might have changed
       during previous import runs or previous bundles and we don't have a
       record of that."""

    table_names = impglobals.DATABASE.table_names('import', prefix='mult_')
    for table_name in table_names:
        imp_mult_table_name = impglobals.DATABASE.convert_raw_to_namespace(
                                                            'import', table_name)
        import_util.log_debug(f'Copying mult table "{imp_mult_table_name}"')
        # Read the import mult table
        column_list = _mult_table_column_names(table_name)
        rows = impglobals.DATABASE.read_rows('import', table_name, column_list)
        mult_rows = _convert_sql_response_to_mult_table(table_name, rows)
        # Write the permanent table
        impglobals.DATABASE.upsert_rows('perm', table_name, 'id', mult_rows)


################################################################################
# TOP-LEVEL IMPORT ROUTINES
################################################################################

def import_one_bundle(bundle_id):
    """Read the PDS data and perform all import functions for one bundle.
       The results are left in the import namespace."""
    impglobals.LOGGER.open(f'Importing {bundle_id}',
                           limits={'info': impglobals.ARGUMENTS.log_info_limit,
                                   'debug': impglobals.ARGUMENTS.log_debug_limit})

    # Start fresh
    global _MULT_TABLE_CACHE, _MODIFIED_MULT_TABLES
    _MULT_TABLE_CACHE = {}
    _MODIFIED_MULT_TABLES = {}
    impglobals.ANNOUNCED_IMPORT_WARNINGS = []
    impglobals.ANNOUNCED_IMPORT_ERRORS = []
    impglobals.MAX_TABLE_ID_CACHE = {}
    impglobals.CURRENT_BUNDLE_ID = bundle_id
    impglobals.CURRENT_INDEX_ROW_NUMBER = None
    impglobals.CURRENT_PRIMARY_FILESPEC = None

    vol_info = _lookup_vol_info(bundle_id)
    if vol_info is None:
        import_util.log_error(f'No BUNDLE_INFO entry for {bundle_id}!')
        impglobals.LOGGER.close()
        impglobals.CURRENT_BUNDLE_ID = None
        return False
    if vol_info['instrument_class'] is None:
        import_util.log_debug(f'Ignoring import of {bundle_id}')
        impglobals.LOGGER.close()
        impglobals.CURRENT_BUNDLE_ID = None
        return True

    if vol_info['pds_version'] == 3:
        bundle_pdsfile = pdsfile.pds3file.Pds3File.from_path(bundle_id)
    elif vol_info['pds_version'] == 4:
        bundle_pdsfile = pdsfile.pds4file.Pds4File.from_path(bundle_id)
    else:
        import_util.log_error(f'BUNDLE_INFO has illegal PDS version for {bundle_id}!')
        return False

    if not bundle_pdsfile.is_bundle:
        import_util.log_error(f'{bundle_id} is not a bundle!')
        impglobals.LOGGER.close()
        impglobals.CURRENT_BUNDLE_ID = None
        return False


    ##################################
    ### FIND PRIMARY INDEX FILE(s) ###
    ##################################

    primary_index_names = [
        x.replace('<BUNDLE>', bundle_id) for x in vol_info['primary_index']]

    # These are the metadata directories
    index_paths = bundle_pdsfile.associated_abspaths('metadata', must_exist=True)
    if vol_info['pds_version'] == 3:
        # These are the plain <volume>/index directories for PDS3 volumes that
        # don't have a separate metadata directory
        index_paths.append(import_util.safe_join(bundle_pdsfile.abspath, 'INDEX'))
        index_paths.append(import_util.safe_join(bundle_pdsfile.abspath, 'index'))
    found_in_this_dir = False
    for path in index_paths:
        if not os.path.exists(path):
            continue
        basenames = os.listdir(path)
        ret = True
        for basename in basenames:
            if basename in primary_index_names:
                bundle_label_path = import_util.safe_join(path, basename)
                import_util.log_debug(f'Using index: {bundle_label_path}')
                found_in_this_dir = True
                ret = ret and import_one_index(bundle_id,
                                               vol_info,
                                               index_paths,
                                               bundle_label_path)
        if found_in_this_dir:
            impglobals.LOGGER.close()
            impglobals.CURRENT_BUNDLE_ID = None
            impglobals.CURRENT_INDEX_ROW_NUMBER = None
            impglobals.CURRENT_PRIMARY_FILESPEC = None
            return ret

    import_util.log_error(f'No index label file found: "{bundle_id}" - searched in:')
    for path in index_paths:
        import_util.log_error(f'    {path}')
    impglobals.LOGGER.close()
    impglobals.CURRENT_BUNDLE_ID = None

    return False


def import_one_index(bundle_id, vol_info, index_paths, bundle_label_path):
    """Import the observations given a single primary index file."""
    instrument_class = vol_info['instrument_class']
    pds_version = vol_info['pds_version']

    obs_rows, obs_label_dict = import_util.safe_pdstable_read(bundle_label_path,
                                                              pds_version)
    if not obs_rows:
        import_util.log_error(f'Read failed: "{bundle_label_path}"')
        return False

    import_util.log_info(f'OBSERVATIONS: {len(obs_rows)} in {bundle_label_path}')

    metadata = {'phase_name': None,
                'temporal_camera': vol_info['temporal_camera']}

    # Instantiate the appropriate class that knows how to import this instrument
    instrument_obj = instrument_class(
        bundle=bundle_id,
        metadata=metadata
    )

    # We need to validate index rows for bundles where there can be more than one
    # row in the index file for a single opus_id. We first compute the opus_id for
    # each row (which is a fast operation), looking for duplicates. When we find
    # duplicates, we collect them into a dictionary. Then we go through the duplicates,
    # if any, and do the reverse mapping opus_id -> filespec, seeing if the result
    # is the same. If it is, that's the row we want to use.
    # We do this complicated process because from_opus_id is a slow operation so we
    # don't want to do it unless absolutely necessary.
    valid_rows = None
    if vol_info['validate_index_rows']:
        opus_ids = {}
        valid_rows = [True] * len(obs_rows)
        for row_no, row in enumerate(obs_rows):
            opus_id = instrument_obj.opus_id_from_index_row(row)
            if opus_id is None:
                # Error already reported
                valid_rows[row_no] = False
                continue
            if opus_id not in opus_ids:
                opus_ids[opus_id] = []
            opus_ids[opus_id].append(row_no)
        for opus_id, row_nos in opus_ids.items():
            if len(row_nos) == 1: # Only one row means not ambiguous
                continue
            # Mark them all invalid to start
            for row_no in row_nos:
                valid_rows[row_no] = False
            good_row = None
            deriv_filespec = None
            try:
                deriv_filespec = pdsfile.pds3file.Pds3File.from_opus_id(opus_id).abspath
            except ValueError:
                try:
                    deriv_filespec = pdsfile.pds4file.Pds4File.from_opus_id(opus_id).abspath
                except ValueError:
                    impglobals.CURRENT_INDEX_ROW_NUMBER = row_no+1
                    import_util.log_nonrepeating_warning(
                        f'Unable to convert OPUS ID "{opus_id}" to filespec')
            if deriv_filespec is not None:
                for row_no in row_nos:
                    orig_filespec = instrument_obj.primary_filespec_from_index_row(
                                            obs_rows[row_no], convert_lbl=True)
                    orig_filespec = instrument_obj.convert_filespec_from_lbl(
                                                                        orig_filespec)
                    if orig_filespec in deriv_filespec:
                        # Found it!
                        if good_row is not None:
                            import_util.log_nonrepeating_error(
                                f'Found multiple rows that map from the same opus_id '
                                f'{opus_id}: {good_row} and {row_no}')
                        good_row = row_no
            if good_row is None:
                impglobals.CURRENT_INDEX_ROW_NUMBER = row_nos[0]+1
                # This isn't always an error because sometimes we actually do have
                # an opud_id that can't be properly reverse-mapped, like
                # vg-pps-2-u-occ-1986-024-betper-lambda-i
                import_util.log_nonrepeating_warning(
                    f'No row found that reverse matches opus_id {opus_id}')
            else:
                valid_rows[good_row] = True
                import_util.log_info('Resolving OPUS ID ambiguity:')
                for row_no in row_nos:
                    orig_filespec = instrument_obj.primary_filespec_from_index_row(
                                                    obs_rows[row_no], convert_lbl=True)
                    sfx = ' (chosen)' if row_no == good_row else ''
                    import_util.log_info('  '+orig_filespec+sfx)

        old_obs_rows = obs_rows
        obs_rows = []
        for row_no, row in enumerate(old_obs_rows):
            if valid_rows[row_no]:
                obs_rows.append(row)
            else:
                impglobals.CURRENT_INDEX_ROW_NUMBER = row_no+1
                import_util.log_info('Dropping index row '+
                                     instrument_obj.primary_filespec_from_index_row(row))

    metadata['index'] = obs_rows
    metadata['index_label'] = obs_label_dict


    ######################################
    ### FIND ASSOCIATED METADATA FILES ###
    ######################################

    # Look for all the "associated" metadata files and read them in
    # Metadata filenames include:
    #   <vol>_ring_summary.lbl
    #   <vol>_moon_summary.lbl
    #   <vol>_<planet>_summary.lbl
    #   <vol>_body_summary.lbl
    #   <vol>_sky_summary.lbl
    #   <vol>_supplemental_index.lbl
    # All of these files are cross-indexed with the primary index file based on
    # the primary filespec.

    if index_paths:
        for index_path in index_paths:
            if vol_info['pds_version'] == 3:
                assoc_pdsfile = pdsfile.pds3file.Pds3File.from_abspath(index_path)
            else:
                assoc_pdsfile = pdsfile.pds4file.Pds4File.from_abspath(index_path)
            try:
                basenames = assoc_pdsfile.childnames
            except KeyError:
                continue
            for basename in basenames:
                if basename.find('999') != -1:
                    # These are cumulative geo files
                    continue
                if not basename.startswith(bundle_id):
                    continue
                basename_upper = basename.upper()
                if (not basename_upper.endswith('SUMMARY.LBL') and
                    not basename_upper.endswith('SUPPLEMENTAL_INDEX.LBL') and
                    not basename_upper.endswith('INVENTORY.LBL')):
                    continue
                assoc_label_path = import_util.safe_join(index_path, basename)
                if basename_upper.endswith('INVENTORY.LBL'):
                    # The inventory files are in CSV format, but the pdstable
                    # module can't read non-fixed-length records so we fake it up
                    # ourselves here.
                    table_filename = (assoc_label_path.replace('.LBL', '.CSV')
                                      .replace('.lbl', '.csv'))
                    assoc_rows = []
                    assoc_label_dict = {} # Not used
                    with open(table_filename, 'r') as table_file:
                        csvreader = csv.reader(table_file)
                        for row in csvreader:
                            if len(row) > 2 and row[2].count('-') > 1:
                                # Old format with OPUS ID column
                                (csv_bundle, csv_filespec, csv_ringobsid,
                                 *csv_targets) = row
                            else:
                                # New format without OPUS ID column
                                csv_ringobsid = None
                                (csv_bundle, csv_filespec, *csv_targets) = row
                            row_dict = {'BUNDLE_ID': csv_bundle.strip(),
                                        'FILE_SPECIFICATION_NAME': csv_filespec.strip(),
                                        'TARGET_LIST': csv_targets}
                            if csv_ringobsid:
                                row_dict['OPUS_ID'] = csv_ringobsid.strip()

                            assoc_rows.append(row_dict)
                else:
                    (assoc_rows,
                     assoc_label_dict) = import_util.safe_pdstable_read(assoc_label_path,
                                                                        pds_version)

                if assoc_rows is None:
                    # No need to report an error here because safe_pdstable_read
                    # will have already done so
                    return False

                if 'RING_SUMMARY' in basename_upper:
                    assoc_type = 'ring_geo'
                elif 'SKY_SUMMARY' in basename_upper:
                    assoc_type = 'sky_geo'
                elif 'SUPPLEMENTAL_INDEX' in basename_upper:
                    assoc_type = 'supp_index'
                elif 'INVENTORY' in basename_upper:
                    assoc_type = 'inventory'
                else:
                    assoc_type = 'surface_geo'

                # Now that we have the data from the associated file, we need to go
                # through and cross-reference it with the primary index based on the
                # primary filespec.
                import_util.log_info(
                        f'{assoc_type.upper()}: {len(assoc_rows)} in {assoc_label_path}')
                assoc_dict = metadata.get(assoc_type, {})
                if assoc_type in ('ring_geo', 'surface_geo', 'sky_geo', 'inventory'):
                    for row in assoc_rows:
                        # We use add_phase_from_row=True here because in COVIMS_0xxx
                        # there are both _IR and _VIS versions of each geo row and we
                        # need a way to distinguish between them. It does nothing
                        # for other cases.
                        key = instrument_obj.primary_filespec_from_index_row(
                                                                row, convert_lbl=True,
                                                                add_phase_from_row=True)
                        if key is None:
                            # Error will already be logged
                            continue
                        key = key.upper()

                        if assoc_type in ('ring_geo', 'sky_geo', 'inventory'):
                            # RING_GEO, SKY_GEO, and INVENTORY are easy - there is at most
                            # a single entry per observation, so we just create
                            # a dictionary keyed by opus_id.
                            assoc_dict[key] = row

                        elif assoc_type == 'surface_geo':
                            # SURFACE_GEO is more complicated, because there can
                            # be more than one entry per observation, since
                            # there is one for each target. We create a
                            # dictionary keyed by opus_id containing a
                            # dictionary keyed by target name so we can collect
                            # all the target entries in one place.
                            key2 = row.get('TARGET_NAME', None)
                            if key2 is None:
                                import_util.log_nonrepeating_error(
                                    f'{assoc_label_path} is missing TARGET_NAME field')
                                break
                            if key not in assoc_dict:
                                assoc_dict[key] = {}
                            assoc_dict[key][key2] = row

                else:
                    assert assoc_type == 'supp_index'
                    for row in assoc_rows:
                        key = instrument_obj.primary_filespec_from_index_row(
                                                                row, convert_lbl=True)
                        if key is not None:
                            # Error will already be logged if key is None
                            key = key.upper()
                            assoc_dict[key] = row

                # We need to be able to look things up in both the main tab file and
                # also the associate label, because different instruments store
                # useful data in both places.
                metadata[assoc_type] = assoc_dict
                metadata[assoc_type+'_label'] = assoc_label_dict

    table_schemas, table_names_in_order = create_tables_for_import(bundle_id,
                                                                   'import')

    # It's time to actually compute the values that will go in the database!
    # Start with the obs_general table, because other tables reference
    # it with foreign keys. Then do general, mission, and instrument in that
    # order. Later come things like type_id, wavelength, and ring_geo. Finally
    # take care of surface geometry, which has to be done once for each target
    # in the image, so is handled separately.
    table_rows = {}
    for table_name in table_names_in_order:
        table_rows[table_name] = []

    # Also look for duplicates in the existing import tables
    if impglobals.ARGUMENTS.import_check_duplicate_id:
        used_opus_id_prev_vol = read_existing_import_opus_id()
    else:
        used_opus_id_prev_vol = set()

    used_targets = set()

    ##############################################
    ### MASTER LOOP - IMPORT ONE ROW AT A TIME ###
    ##############################################

    for index_row_num, index_row in enumerate(obs_rows):
        metadata['index_row'] = index_row
        metadata['index_row_num'] = index_row_num+1
        metadata['phase_name'] = None
        obs_general_row = None
        obs_pds_row = None
        impglobals.CURRENT_INDEX_ROW_NUMBER = index_row_num+1

        # Sometimes the primary_filespec is taken from the supplemental index, which we
        # don't have yet, so we can't look it up until later.
        impglobals.CURRENT_PRIMARY_FILESPEC = None

        # For supplemental_index and logging
        # Note we don't use primary_filespec_from_index_row here because that doesn't
        # currently work with CIRS, which makes the logging not give full
        # row information.
        primary_filespec = instrument_obj.primary_filespec
        primary_filespec = instrument_obj.convert_filespec_from_lbl(primary_filespec)
        impglobals.CURRENT_PRIMARY_FILESPEC = primary_filespec
        primary_filespec = primary_filespec.upper()
        if 'supp_index' in metadata:
            supp_index = metadata['supp_index']
            if primary_filespec in supp_index:
                metadata['supp_index_row'] = supp_index[primary_filespec]
            else:
                import_util.log_nonrepeating_warning(
                    f'FILESPEC "{primary_filespec}" is missing supplemental data')
                metadata['supp_index_row'] = None

        # Sometimes a single row in the index turns into multiple opus_id
        # in the database. This happens with COVIMS because each observation
        # might include both VIS and IR entries. Build up a list of such entries
        # here and then process the row as many times as necessary.
        phase_names = instrument_obj.phase_names
        for phase_name in phase_names:
            metadata['phase_name'] = phase_name

            # For the geo indexes - we have to add in the phase because COVIMS_0xxx has
            # separate rows for IR and VIS
            primary_filespec_phase = instrument_obj.primary_filespec_from_index_row(
                                                            index_row, convert_lbl=True,
                                                            add_phase_from_inst=True)
            primary_filespec_phase = primary_filespec_phase.upper()
            if 'ring_geo' in metadata:
                ring_geo = metadata['ring_geo'].get(primary_filespec_phase, None)
                metadata['ring_geo_row'] = ring_geo
                if (ring_geo is None and
                    impglobals.ARGUMENTS.import_report_missing_ring_geo):
                    import_util.log_warning(
                        f'RING GEO metadata missing for "{primary_filespec_phase}"')
            if 'sky_geo' in metadata:
                sky_geo = metadata['sky_geo'].get(primary_filespec_phase, None)
                metadata['sky_geo_row'] = sky_geo
                if (sky_geo is None and
                    impglobals.ARGUMENTS.import_report_missing_sky_geo):
                    import_util.log_warning(
                        f'SKY GEO metadata missing for "{primary_filespec_phase}"')
            if 'surface_geo' in metadata:
                body_geo = metadata['surface_geo'].get(primary_filespec_phase)
                metadata['surface_geo_row'] = body_geo

            # Handle everything except surface_geo

            for table_name in table_names_in_order:
                if table_name.startswith('obs_surface_geometry'):
                    # Deal with surface geometry a little later
                    continue
                if table_name == 'obs_files':
                    # obs_files is done separately below because it has multiple
                    # rows per observation
                    continue
                if table_name not in table_schemas:
                    # Table not relevant for this product
                    continue
                row = import_observation_table(instrument_obj,
                                               table_name,
                                               table_schemas[table_name],
                                               metadata)
                if table_name == 'obs_pds':
                    obs_pds_row = row
                if table_name == 'obs_general':
                    obs_general_row = row
                    opus_id = row['opus_id']
                    if opus_id in used_opus_id_prev_vol:
                        # Some of the GO_xxxx and COUVIS_xxxx bundles have
                        # duplicate observations across bundles. In these cases
                        # we have to use the NEW one and delete the old one
                        # from the database itself. Note this will only be
                        # triggered if we have already loaded the previous
                        # bundle into the import tables but not clear them out.
                        # In the case where we copied them to the perm tables
                        # and cleared them out, a future check during the copy
                        # process will catch the duplicates.
                        delete_opus_id_from_obs_tables(opus_id, 'import')
                table_rows[table_name].append(row)
                metadata[table_name+'_row'] = row

            assert obs_general_row is not None

            # Handle obs_surface_geometry_name and
            # obs_surface_geometry__<TARGET>

            target_dict = {}
            if 'surface_geo' in metadata:
                surface_geo_dict = metadata['surface_geo']
                for table_name in table_names_in_order:
                    if not table_name.startswith('obs_surface_geometry_'):
                        # Deal with obs_surface_geometry_name and
                        # obs_surface_geometry__<TARGET> only
                        continue
                    # Here we are handling both obs_surface_geometry_name and
                    # obs_surface_geometry as well as all of the
                    # obs_surface_geometry__<TARGET> tables

                    # Retrieve the opus_id from obs_general to find the
                    # surface_geo
                    target_dict = surface_geo_dict.get(primary_filespec_phase, {})
                    for target_name in sorted(target_dict.keys()):
                        used_targets.add(target_name)
                        # Note the following only affects
                        # obs_surface_geometry__<T> not the generalized
                        # obs_surface_geometry. This is fine because we want the
                        # generalized obs_surface_geometry to include all the
                        # targets.
                        new_target_name = import_util.table_name_for_sfc_target(
                                                                target_name)
                        new_table_name = table_name.replace('<TARGET>',
                                                            new_target_name)
                        metadata['surface_geo_row'] = target_dict[
                                                                target_name]
                        metadata['surface_geo_target_name'] = target_name

                        row = import_observation_table(instrument_obj,
                                                       new_table_name,
                                                       table_schemas[table_name],
                                                       metadata)
                        if new_table_name not in table_rows:
                            table_rows[new_table_name] = []
                            import_util.log_debug(
                              f'Creating surface geo table for new target {target_name}')
                        table_rows[new_table_name].append(row)

            if instrument_obj.surface_geo_target_list():
                # The are some cases (like COCIRS_[01]xxx) where the index files
                # contain the surface geo information instead of a separate
                # summary file. In these cases we ask the instrument for the list of
                # targets and process them directly.
                for table_name in table_names_in_order:
                    if not table_name.startswith('obs_surface_geometry_'):
                        # Deal with obs_surface_geometry_name and
                        # obs_surface_geometry__<TARGET> only
                        continue
                    # Here we are handling both obs_surface_geometry_name and
                    # obs_surface_geometry as well as all of the
                    # obs_surface_geometry__<TARGET> tables

                    for target_name in instrument_obj.surface_geo_target_list():
                        used_targets.add(target_name)
                        # Note the following only affects
                        # obs_surface_geometry__<T> not the generalized
                        # obs_surface_geometry. This is fine because we want the
                        # generalized obs_surface_geometry to include all the
                        # targets.
                        new_target_name = import_util.table_name_for_sfc_target(
                                                                target_name)
                        new_table_name = table_name.replace('<TARGET>',
                                                            new_target_name)
                        metadata['surface_geo_row'] = None
                        metadata['surface_geo_target_name'] = target_name

                        row = import_observation_table(instrument_obj,
                                                       new_table_name,
                                                       table_schemas[table_name],
                                                       metadata)
                        if new_table_name not in table_rows:
                            table_rows[new_table_name] = []
                            import_util.log_debug(
                              f'Creating surface geo table for new target {target_name}')
                        table_rows[new_table_name].append(row)


            # Handle obs_surface_geometry
            # We have to do this later than the other obs_ tables because only
            # now do we know what all the available targets are

            surface_target_list = None
            if 'inventory' in metadata:
                inventory = metadata['inventory']
                if primary_filespec_phase in inventory:
                    surface_target_list = inventory[primary_filespec_phase]['TARGET_LIST']
            metadata['inventory_list'] = surface_target_list
            metadata['used_surface_geo_targets'] = list(target_dict.keys())

            for table_name in table_names_in_order:
                if table_name != 'obs_surface_geometry':
                    # Deal with obs_surface_geometry only
                    continue
                # This is used to populate the surface geo target_list
                # field

                row = import_observation_table(instrument_obj,
                                               table_name,
                                               table_schemas[table_name],
                                               metadata)
                if table_name not in table_rows:
                    table_rows[new_table_name] = []
                table_rows[table_name].append(row)

            # Handle obs_files

            if 'obs_files' not in table_rows:
                table_rows['obs_files'] = []
            for table_name in table_names_in_order:
                if table_name != 'obs_files':
                    # Deal with obs_files only
                    continue
                rows = get_opus_products_rows_for_filespec(
                                vol_info['pds_version'],
                                obs_pds_row['primary_filespec'],
                                obs_general_row['id'],
                                obs_general_row['opus_id'],
                                obs_general_row['bundle_id'],
                                obs_general_row['instrument_id'])
                table_rows[table_name].extend(rows)


    #################################################################
    ### DONE COMPUTING ROW CONTENTS - CREATE MULTS AND DUMP TO DB ###
    #################################################################

    impglobals.CURRENT_INDEX_ROW_NUMBER = None
    impglobals.CURRENT_PRIMARY_FILESPEC = None

    # Now that we have all the values, we have to dump out the mult tables
    # because they are referenced as foreign keys
    dump_import_mult_tables()

    # Now dump out the obs tables, in order, because at least obs_general
    # is referenced by foreign keys.
    for table_name in table_names_in_order:
        if table_name.find('<TARGET>') == -1:
            imp_name = impglobals.DATABASE.convert_raw_to_namespace('import', table_name)
            import_util.log_debug(f'Inserting into obs table "{imp_name}"')
            impglobals.DATABASE.insert_rows('import', table_name, table_rows[table_name])
        else:
            for target_name in sorted(used_targets):
                new_table_name = table_name.replace(
                            '<TARGET>',
                            import_util.table_name_for_sfc_target(target_name))
                imp_name = impglobals.DATABASE.convert_raw_to_namespace('import',
                                                                        new_table_name)
                import_util.log_debug(f'Inserting into obs table "{imp_name}"')
                surface_geo_schema = import_util.read_schema_for_table(
                                            'obs_surface_geometry_target',
                                            replace=[
                    ('<TARGET>', import_util.table_name_for_sfc_target(target_name)),
                    ('<SLUGTARGET>', import_util.slug_name_for_sfc_target(target_name))])
                # We can finally get around to creating the
                # obs_surface_geometry_<T> tables now that we know what targets
                # we have
                impglobals.DATABASE.create_table('import', new_table_name,
                                                 surface_geo_schema)
                impglobals.DATABASE.insert_rows('import', new_table_name,
                                                table_rows[new_table_name])

    return True # SUCCESS!


def import_observation_table(instrument_obj,
                             table_name,
                             table_schema,
                             metadata):
    "Import the data from a row from a PDS file into a single table."
    new_row = {}

    metadata[table_name+'_row'] = new_row

    # Run through all the based columns and compute their values.
    # Always skip "id" for tables other than obs_general, because this is just
    # an AUTO_INCREMENT field used by Django and has no other purpose.
    # Always skip "timestamp" fields because these are automatically filled in
    # by SQL because we mark them as ON CREATE and ON UPDATE.
    # Skip "mult_" tables because they are handled separately when the search
    # type is a GROUP-type.

    for table_column in table_schema:
        if (table_column.get('put_mults_here', False) or
            table_column.get('pi_referred_slug', False)):
            continue
        field_name = table_column['field_name']
        field_type = table_column['field_type']

        metadata['table_name'] = table_name
        metadata['field_name'] = field_name

        if field_name == 'timestamp':
            continue

        data_source = table_column.get('data_source', None)
        if not data_source:
            import_util.log_nonrepeating_warning(
                f'No data source for column "{field_name}" in table '+
                f'"{table_name}"')
            column_val_list = []
        else:
            ### COMPUTE THE NEW COLUMN VALUE ###

            column_val_list = None
            mult_label_list = None
            aliases_list = None
            disp_list = None
            disp_order_list = None # Might be set with mult_label but not otherwise
            grouping_list = None
            group_disp_order_list = None

            if data_source == 'OBS_GENERAL_ID':
                obs_general_row = metadata['obs_general_row']
                column_val_list = [import_util.safe_column(obs_general_row, 'id')]

            elif data_source == 'COMPUTE':
                ok, ret = import_run_field_function(instrument_obj,
                                                    table_name,
                                                    table_schema,
                                                    metadata,
                                                    field_name)
                if ok:
                    # For a mult_list field, it's OK to return a single value, just to
                    # make the populate_ code simpler. In that case we turn it into a
                    # single-element list.
                    # Note that if one return value is a dict (full-spec mult field) then
                    # they all have to be.
                    if not isinstance(ret, (list, tuple)):
                        ret = [ret]
                    if isinstance(ret[0], dict):
                        column_val_list = [x['col_val'] for x in ret]
                        mult_label_list = [x['disp_name'] for x in ret]
                        aliases_list = [x['aliases'] for x in ret]
                        disp_list = [x['disp'] for x in ret]
                        disp_order_list = [x['disp_order'] for x in ret]
                        grouping_list = [x['grouping'] for x in ret]
                        group_disp_order_list = [x['group_disp_order'] for x in ret]
                    else:
                        column_val_list = ret
                else:
                    # Error will already be logged by import_run_field_function
                    column_val_list = [None]

            elif data_source == 'LONGITUDE_FIELD':
                column_val_list = [instrument_obj.compute_longitude_field()]

            elif data_source == 'D_LONGITUDE_FIELD':
                column_val_list = [instrument_obj.compute_d_longitude_field()]

            elif data_source == 'MAX_ID':
                if table_name not in impglobals.MAX_TABLE_ID_CACHE:
                    impglobals.MAX_TABLE_ID_CACHE[table_name] = (
                        import_util.find_max_table_id(table_name))
                impglobals.MAX_TABLE_ID_CACHE[table_name] = (
                    impglobals.MAX_TABLE_ID_CACHE[table_name]+1)
                column_val_list = [impglobals.MAX_TABLE_ID_CACHE[table_name]]

            else:
                import_util.log_nonrepeating_error(
                    f'Unknown data_source type "{data_source}" for '+
                    f'"{field_name}" in table "{table_name}"')

        ### VALIDATE THE COLUMN VALUE ###

        # For a mult_list field, the column_val_list contains a list of column_vals.
        # Otherwise it contains a list with a single entry for the single value.
        assert field_type == 'mult_list' or len(column_val_list) == 1

        row_val = []

        for column_val_num, column_val in enumerate(column_val_list):
            if column_val is None:
                notnull = table_column.get('field_notnull', False)
                if notnull:
                    import_util.log_nonrepeating_error(
                        f'Column "{field_name}" in table "{table_name}" '+
                        'has NULL value but NOT NULL is set')
            else:
                if field_type.startswith('flag'):
                    if column_val in [0, 'n', 'N', 'no', 'No', 'NO', 'off', 'OFF']:
                        if field_type == 'flag_onoff':
                            column_val = 'Off'
                        else:
                            column_val = 'No'
                    elif column_val in [1, 'y', 'Y', 'yes', 'Yes', 'YES', 'on', 'ON']:
                        if field_type == 'flag_onoff':
                            column_val = 'On'
                        else:
                            column_val = 'Yes'
                    elif column_val in ['N/A', 'UNK', 'NULL']:
                        column_val = None
                    else:
                        import_util.log_nonrepeating_error(
                            f'Column "{field_name}" in table "{table_name}" '+
                            f'has FLAG type but value "{column_val}" is not '+
                            'a valid flag value')
                        column_val = None
                if field_type.startswith('char'):
                    field_size = int(field_type[4:])
                    if not isinstance(column_val, str):
                        import_util.log_nonrepeating_error(
                            f'Column "{field_name}" in table "{table_name}" '+
                            f'has CHAR type but value "{column_val}" is of '+
                            f'type "{type(column_val)}"')
                        column_val = ''
                    elif len(column_val) > field_size:
                        import_util.log_nonrepeating_error(
                            f'Column "{field_name}" in table "{table_name}" '+
                            f'has CHAR size {field_size} but value '+
                            f'"{column_val}" is too long')
                        column_val = column_val[:field_size]
                elif (field_type.startswith('real') or
                      field_type.startswith('int') or
                      field_type.startswith('uint')):
                    the_val = None
                    if field_type.startswith('real'):
                        try:
                            the_val = float(column_val)
                        except ValueError:
                            import_util.log_nonrepeating_error(
                                f'Column "{field_name}" in table '+
                                f'"{table_name}" has REAL type but '+
                                f'"{column_val}" is not a float')
                            column_val = None
                    else:
                        try:
                            the_val = int(column_val)
                        except ValueError:
                            import_util.log_nonrepeating_error(
                                f'Column "{field_name}" in table '+
                                f'"{table_name}" has INT type but '+
                                f'"{column_val}" is not an int')
                            column_val = None
                    if column_val is not None and the_val is not None:
                        val_sentinel = table_column.get('val_sentinel', None)
                        if not isinstance(val_sentinel, list):
                            val_sentinel = [val_sentinel]
                        if the_val in val_sentinel:
                            column_val = None
                            import_util.log_nonrepeating_error(
                                f'Caught sentinel value {the_val} for column '+
                                f'"{field_name}" that was missed'+
                                ' by the PDS label!')
                    if column_val is not None and the_val is not None:
                        val_min = table_column.get('val_min', None)
                        val_max = table_column.get('val_max', None)
                        val_use_null = table_column.get('val_set_invalid_to_null',
                                                        False)
                        if val_min is not None and the_val < val_min:
                            if val_use_null:
                                msg = (f'Column "{field_name}" in table '+
                                       f'"{table_name}" has minimum value '+
                                       f'{val_min} but {column_val} is too small -'+
                                       ' substituting NULL')
                                import_util.log_debug(msg)
                            else:
                                msg = (f'Column "{field_name}" in table '+
                                       f'"{table_name}" has minimum value '+
                                       f'{val_min} but {column_val} is too small')
                                import_util.log_nonrepeating_error(msg)
                            column_val = None
                        if val_max is not None and the_val > val_max:
                            if val_use_null:
                                msg = (f'Column "{field_name}" in table '+
                                       f'"{table_name}" has maximum value {val_max}'+
                                       f' but {column_val} is too large - '+
                                       'substituting NULL')
                                import_util.log_debug(msg)
                            else:
                                msg = (f'Column "{field_name}" in table '+
                                       f'"{table_name}" has maximum value '+
                                       f'{val_max} but {column_val} is too large')
                                import_util.log_nonrepeating_error(msg)
                            column_val = None

            ### CHECK TO SEE IF THERE IS AN ASSOCIATED MULT_ TABLE ###

            form_type = table_column.get('pi_form_type', None)
            if form_type is not None and form_type.find(':') != -1:
                form_type = form_type[:form_type.find(':')]
            if form_type in config_data.GROUP_FORM_TYPES:
                # Handle the case when display value is not set. This stays here because
                # mult_label gets updated based on column_val after column_val is validated.
                # (ex: flag)
                mult_label = None
                if mult_label_list is None:
                    import_util.log_nonrepeating_error(
                        f'Fatal error processing column "{field_name}" in '
                        f'table "{table_name}" - bad data type returned for mult'
                    )
                    return None
                mult_label = mult_label_list[column_val_num]
                if mult_label is None:
                    if column_val is None:
                        mult_label = 'N/A'
                    else:
                        mult_label = str(column_val)
                        if (not mult_label[0].isdigit() or
                            not mult_label[-1].isdigit()):
                            # This catches things like 2014 MU69 and leaves them
                            # in all caps
                            mult_label = mult_label.title()

                column_val = update_mult_table(
                              table_name, field_name, table_column,
                              column_val, mult_label,
                              aliases_list[column_val_num],
                              disp_list[column_val_num],
                              disp_order_list[column_val_num],
                              grouping_list[column_val_num],
                              group_disp_order_list[column_val_num])

            if field_type != 'mult_list' or column_val is not None:
                # When making a list for a mult_list field, don't include None
                # results because then we end up with a weird list like
                # ['SATURN', None, 'S RINGS'] which doesn't convert to JSON
                # propertly.
                row_val.append(column_val)

        if field_type == 'mult_list':
            # An empty list corresponds to a NULL database field
            if len(row_val) == 0:
                new_row[field_name] = None
            else:
                new_row[field_name] = json.dumps(row_val)
        else:
            new_row[field_name] = row_val[0] # Only a single value

    if not impglobals.ARGUMENTS.import_ignore_geo_mismatch:
        if table_name == 'obs_ring_geometry':
            instrument_obj.validate_ring_geo_fields(new_row, metadata)
        elif table_name.startswith('obs_surface_geometry__'):
            instrument_obj.validate_surface_geo_fields(new_row, metadata, table_name)

    return new_row

def import_run_field_function(instrument_obj,
                              table_name, table_schema, metadata,
                              field_name):
    """Call the Python function used to populate a single field in a table."""
    if table_name.startswith('obs_surface_geometry__'):
        table_name = 'obs_surface_geometry_target'
    func_name = 'field_'+table_name+'_'+field_name
    if (not hasattr(instrument_obj, func_name) or
        not callable(func := getattr(instrument_obj, func_name))):
        class_name = type(instrument_obj).__name__
        import_util.log_nonrepeating_error(
            f'Unknown table field func "{class_name}::{func_name}"')
        return (False, None)
    try:
        res = func()
    except Exception:
        tb = traceback.format_exc()
        class_name = type(instrument_obj).__name__
        import_util.log_nonrepeating_error(
            f'Execution of field function {class_name}::{func_name} failed with '
            f'exception:\n{tb}')
        return False, None
    return (True, res)

def get_opus_products_rows_for_filespec(pds_version, filespec, obs_general_id,
                                        opus_id, bundle_id, instrument_id):
    rows = []

    try:
        if pds_version == 3:
            pdsf = pdsfile.pds3file.Pds3File.from_filespec(filespec, fix_case=True)
        else:
            pdsf = pdsfile.pds4file.Pds4File.from_filespec(filespec, fix_case=True)
    except ValueError:
        import_util.log_nonrepeating_error(f'Failed to convert filespec "{filespec}"')
        return

    products = pdsf.opus_products()
    if '' in products:
        file_list_str = '  '.join([x.abspath for x in products[''][0]])
        if impglobals.ARGUMENTS.import_report_empty_products:
            import_util.log_nonrepeating_warning(
                f'Empty opus_product key for files: {file_list_str}')
        del products['']
    # Keep a running list of all products by type, sorted by version
    for product_type in products:
        (category, sort_order_num, short_name,
         full_name, default_checked) = product_type

        if category == 'standard':
            pref = 'ZZZZZ1'
        elif category == 'metadata':
            pref = 'ZZZZZ2'
        elif category == 'browse':
            pref = 'ZZZZZ3'
        elif category == 'diagram':
            pref = 'ZZZZZ4'
        else:
            pref_list = category.split(' ')
            pref = pref_list[0][:3]
            if len(pref_list) == 1:
                pref += pref_list[0][-3:]
            else:
                pref += pref_list[-1][:3]
            pref = pref.upper()
        sort_order = pref + ('%03d' % sort_order_num)
        list_of_sublists = products[product_type]

        skip_current_product_type = False

        # rows for current product type
        # Since the opus products output is sorted in alphebatical order, for the opus
        # type of index files, we will visit label file first before visiting the index
        # file. In the case like this, we don't want to include the lable file in the row
        # when the current index product type is skip.
        current_rows = []
        for sublist in list_of_sublists:
            if (not impglobals.ARGUMENTS.import_dont_use_row_files and
                skip_current_product_type):
                current_rows = []
                break
            for file_num, file in enumerate(sublist):
                version_number = sublist[0].version_rank
                version_name = sublist[0].version_id
                if version_name == '':
                    version_name = 'Current'
                # Make sure versions other than "Current" are not checked by default
                if version_name != 'Current':
                    default_checked = False
                logical_path = file.logical_path

                # For an index file, we check to see if this observation is
                # present. If not, we don't include the index file in the
                # results.
                # TODO: for PDS4, find_selected_row_key will raise an OSError complaining
                # about missing pickle files in _indexshelf-metadata, so for now we will
                # assume the selection is always in the index file and create a row for
                # it in db. Will fix this when pickle files in indexshelf is ready.
                if (not impglobals.ARGUMENTS.import_dont_use_row_files and
                    file.is_index and pds_version == 3):
                    basename = filespec.split('/')[-1]
                    selection = basename.split('.')[0]
                    try:
                        file.find_selected_row_key(selection, '=',
                                                   exact_match=True)
                    except KeyError:
                        # can't find the row, we skip this product_type
                        skip_current_product_type = True
                        break
                    except OSError as e:
                        # selection is partially matched, we skip this
                        # product_type
                        import_util.log_warning(
                            f'{e} - {selection} is partially matched and ' +
                            'does not exist in the table.')
                        skip_current_product_type = True
                        break
                elif ('_summary.tab' in logical_path or
                      '_index.tab' in logical_path or
                      '_hstfiles.tab' in logical_path):
                    # if an index file has no files in shelves/index
                    import_util.log_nonrepeating_warning(
                        f'Volume "{bundle_id}" is missing row files under '+
                        f'shelves/index for {logical_path}')

                # If the pdsfile is expecting the shelf file, check if corresponding
                # shelves/info files exist, if not, we skip the file.
                if pds_version == 3 and file.shelf_exists_if_expected() is False:
                    # TODOPDS4 ^^^
                    import_util.log_nonrepeating_warning(
                        'Missing corresponding ' +
                        f'shelves/info for {file.abspath}')
                    continue

                # The following info are obtained from _info (from shelves/info)
                url = file.url.strip('/')
                checksum = file.checksum
                size = file.size_bytes
                width = file.width or None
                height = file.height or None

                if 'obs_files' not in impglobals.MAX_TABLE_ID_CACHE:
                    impglobals.MAX_TABLE_ID_CACHE['obs_files'] = (
                        import_util.find_max_table_id('obs_files'))
                impglobals.MAX_TABLE_ID_CACHE['obs_files'] = (
                    impglobals.MAX_TABLE_ID_CACHE['obs_files']+1)
                id = impglobals.MAX_TABLE_ID_CACHE['obs_files']

                row = {'id': id,
                       'obs_general_id': obs_general_id,
                       'opus_id': opus_id,
                       'bundle_id': bundle_id,
                       'instrument_id': instrument_id,
                       'version_number': version_number,
                       'version_name': version_name,
                       'category': category,
                       'sort_order': sort_order,
                       'product_order': file_num,
                       'short_name': short_name,
                       'full_name': full_name,
                       'logical_path': logical_path,
                       'url': url,
                       'checksum': checksum,
                       'size': size,
                       'width': width,
                       'height': height,
                       'pds_version': pds_version,
                       'default_checked': default_checked,
                       }
                current_rows.append(row)
                if size == 0:
                    import_util.log_nonrepeating_warning(
                        f'File has zero size: {opus_id} {logical_path}')

            if skip_current_product_type:
                current_rows = []

        rows += current_rows

    return rows

def remove_opus_id_from_tables(table_rows, opus_id):
    for table_name in table_rows:
        rows = table_rows[table_name]
        i = 0
        while i < len(rows):
            if ('opus_id' in rows[i] and
                rows[i]['opus_id'] == opus_id):
                import_util.log_debug(f'Removing "{opus_id}" from unwritten table '
                                      f'"{table_name}"')
                del rows[i]
                continue # There might be more than one in obs_surface_geometry
            i += 1


################################################################################
# THE MAIN IMPORT LOOP
################################################################################

def do_import_steps():
    "Do all of the steps requested by the user for an import."
    impglobals.IMPORT_HAS_BAD_DATA = False
    impglobals.MAX_TABLE_ID_CACHE = {}
    global _CREATED_IMP_MULT_TABLES
    _CREATED_IMP_MULT_TABLES = set()

    bundle_id_list = []
    for bundle_id in import_util.yield_import_bundle_ids(impglobals.ARGUMENTS):
        bundle_id_list.append(bundle_id)

    # Delete the old import tables if
    #   --drop-old-import-tables but not
    #   --leave-old-import-tables
    # is given.
    old_imp_tables_dropped = False
    if (impglobals.ARGUMENTS.drop_old_import_tables and
        not impglobals.ARGUMENTS.leave_old_import_tables):
        import_util.log_info('Deleting all old import tables')
        delete_all_obs_mult_tables('import')
        old_imp_tables_dropped = True

    # If --drop-permanent-tables AND --scorched-earth is given, delete
    # the permanent tables entirely. We have to do this before starting the
    # real import so that there are no vestigial mult tables and the ids
    # can be reset to 0.
    old_perm_tables_dropped = False
    if (impglobals.ARGUMENTS.drop_permanent_tables and
        impglobals.ARGUMENTS.scorched_earth):
        import_util.log_warning('** DELETING ALL PERMANENT TABLES **')
        delete_all_obs_mult_tables('perm')
        old_perm_tables_dropped = True

        # This must be done after the permanent tables were deleted, since
        # that process also deleted these tables. In this case, we didn't do
        # this step earlier.
        if (impglobals.ARGUMENTS.drop_cache_tables or
            impglobals.ARGUMENTS.create_cart):
            impglobals.LOGGER.open(
                'Cleaning up OPUS/Django tables',
                limits={'info': impglobals.ARGUMENTS.log_info_limit,
                        'debug': impglobals.ARGUMENTS.log_debug_limit})

            if impglobals.ARGUMENTS.create_cart:
                do_cart.create_cart()
            if impglobals.ARGUMENTS.drop_cache_tables:
                do_django.drop_cache_tables()

            impglobals.LOGGER.close()

    # If --import is given, first delete the bundles from the import tables,
    # then do the new import
    if (impglobals.ARGUMENTS.do_import or
        impglobals.ARGUMENTS.delete_import_bundles):
        if not old_imp_tables_dropped:
            import_util.log_warning('Importing on top of previous import tables!')
            for bundle_id in import_util.yield_import_bundle_ids(
                                                    impglobals.ARGUMENTS):
                delete_bundle_from_obs_tables(bundle_id, 'import')

    if impglobals.ARGUMENTS.do_import:
        for bundle_id in bundle_id_list:
            if not import_one_bundle(bundle_id):
                impglobals.LOGGER.log('fatal',
                        f'Import of bundle {bundle_id} failed - Aborting')
                impglobals.IMPORT_HAS_BAD_DATA = True
                if not impglobals.ARGUMENTS.import_ignore_errors:
                    break

        if (impglobals.IMPORT_HAS_BAD_DATA and
            not impglobals.ARGUMENTS.import_ignore_errors):
            impglobals.LOGGER.log('fatal',
                                  'ERRORs found during import - aborting early')
            return False

    # If --copy-import-to-permanent-tables or --delete-permanent-import-bundles
    # are given, delete all bundles that exist in the import tables from the
    # permanent tables.
    import_bundle_ids = []
    if ((impglobals.ARGUMENTS.copy_import_to_permanent_tables or
         impglobals.ARGUMENTS.delete_permanent_import_bundles) and
        impglobals.DATABASE.table_exists('import', 'obs_general')):
        imp_obs_general_table_name = (
            impglobals.DATABASE.convert_raw_to_namespace('import',
                                                         'obs_general'))
        q = impglobals.DATABASE.quote_identifier
        import_bundle_ids = [x[0] for x in
                      impglobals.DATABASE.general_select(
    f'DISTINCT {q("bundle_id")} FROM {q(imp_obs_general_table_name)} ORDER BY {q("bundle_id")}')
                     ]
        if not old_perm_tables_dropped:
            # Don't bother if there's nothing there!
            if not impglobals.ARGUMENTS.create_cart:
                import_util.log_warning(
                        'Deleting bundles from perm tables but cart table not wiped')
            for bundle_id in import_bundle_ids:
                delete_bundle_from_obs_tables(bundle_id, 'perm')

    # If --delete-permanent-bundles is given, delete the given set of bundles
    # from the permanent tables.
    if impglobals.ARGUMENTS.delete_permanent_bundles:
        for bundle_id in bundle_id_list:
            delete_bundle_from_obs_tables(bundle_id, 'perm')

    # If --copy-import-to-permanent-tables is given, create obs and mult tables
    # as necessary, then copy the import tables to the permanent tables.
    if impglobals.ARGUMENTS.copy_import_to_permanent_tables:
        for bundle_id in import_bundle_ids:
            create_tables_for_import(bundle_id, 'perm')

        import_util.log_info('Deleting duplicate opus_ids')
        delete_duplicate_opus_id_from_perm_tables()

        import_util.log_info('Copying import mult tables to permanent')
        copy_mult_from_import_to_permanent()

        for bundle_id in import_bundle_ids:
            copy_bundle_from_import_to_permanent(bundle_id)

    # If --drop-new-import-tables is given, delete the new import tables
    if impglobals.ARGUMENTS.drop_new_import_tables:
        import_util.log_info('Deleting all new import tables')
        delete_all_obs_mult_tables('import')

    # If --analyze-permanent-tables is given, analyze the permanent tables
    if impglobals.ARGUMENTS.analyze_permanent_tables:
        import_util.log_info('Analyzing all permanent tables')
        analyze_all_tables('perm')

    return True
