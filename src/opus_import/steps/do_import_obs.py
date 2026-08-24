################################################################################
# do_import_obs.py
#
# Compute a single row of a single observation table by calling the obs class
# field functions. These are the per-observation internals of do_import, not a
# step of their own.
################################################################################

import json
import traceback

from opus_import import config_data, impglobals, import_util
from opus_import.steps import do_import_mult


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

                column_val = do_import_mult.update_mult_table(
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
