################################################################################
# do_param_info.py
#
# Generate and maintain the param_info table.
################################################################################

import os

from secrets import *
import impglobals
import import_util


def create_import_param_info_table():
    db = impglobals.DATABASE
    logger = impglobals.LOGGER

    logger.log('info', 'Creating new import param_info table')
    pi_schema = import_util.read_schema_for_table('param_info')
    # Start from scratch
    db.drop_table('import', 'param_info')
    db.create_table('import', 'param_info', pi_schema, ignore_if_exists=False)

    # We use the permanent tables to determine what goes into param_info
    table_names = db.table_names('perm', prefix='obs_')

    rows = []
    for table_name in table_names:
        table_schema = import_util.read_schema_for_table(table_name)
        if table_schema is None:
            logger.log('error',
                       f'Unable to read table schema for "{table_name}"')
            return False
        for column in table_schema:
            category_name = column.get('pi_category_name', None)
            if category_name is None:
                continue
            new_row = {
                'category_name': category_name,
                'dict_context': column['pi_dict_context'],
                'dict_name': column['pi_dict_name'],
                'disp_order': column['pi_disp_order'],
                'display': column['pi_display'],
                'display_results': column['pi_display_results'],
                'form_type': column['pi_form_type'],
                'intro': column['pi_intro'],
                'label': column['pi_label'],
                'label_results': column['pi_label_results'],
                'name': column['field_name'],
                'slug': column['pi_slug'],
                'sub_heading': column['pi_sub_heading'],
                'tooltip': column['pi_tooltip'],
                'units': column['pi_units']
            }
            rows.append(new_row)
    db.insert_rows('import', 'param_info', rows)

    return True

def copy_param_info_from_import_to_permanent():
    db = impglobals.DATABASE
    logger = impglobals.LOGGER

    logger.log('info', 'Copying param_info table from import to permanent')
    # Start from scratch
    pi_schema = import_util.read_schema_for_table('param_info')
    # Start from scratch
    db.drop_table('perm', 'param_info')
    db.create_table('perm', 'param_info', pi_schema, ignore_if_exists=False)

    db.copy_rows_between_namespaces('import', 'perm', 'param_info')


def do_param_info():
    if create_import_param_info_table():
        copy_param_info_from_import_to_permanent()
    impglobals.DATABASE.drop_table('import', 'param_info')
