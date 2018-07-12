################################################################################
# do_update_mult_info.py
#
# Update the details of preprogrammed mult tables.
################################################################################

import os

from secrets import *
import impglobals
import import_util


def update_mult_info():
    db = impglobals.DATABASE
    logger = impglobals.LOGGER

    # Find all the permament mult_ tables
    table_names = db.table_names('perm', prefix='mult_')

    for table_name in table_names:
        # Try to figure out what the table name is
        splits = table_name.split('_')
        table_schema = None
        for n_splits in range(3, 6):
            # Covers mult_obs_general to mult_obs_mission_new_horizons
            trial_name = '_'.join(splits[1:n_splits])
            table_schema = import_util.read_schema_for_table(trial_name)
            if table_schema is not None:
                break
        if table_schema is None:
            logger.log('error',
                f'Unable to find table schema for mult "{table_name}"')
            continue
        mult_field_name = '_'.join(splits[n_splits:])
        for column in table_schema:
            field_name = column['field_name']
            if field_name == mult_field_name:
                break
        else:
            logger.log('error',
        f'Unable to find field "{mult_field_name}" in table "{table_name}"')
            continue

        mult_options = column.get('mult_options', False)
        if not mult_options:
            continue

        for mult_info in mult_options:
            id_num, value, label, disp_order, display, definition = mult_info

            row_dict = {
                'label': str(label),
                'disp_order': disp_order,
                'display': display
            }

            db.update_row('perm', table_name, row_dict,
                          'id='+str(id_num))
