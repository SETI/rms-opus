################################################################################
# validate.py
#
# Perform various validations on the database.
################################################################################

import os

import pdsfile

from secrets import *
import impglobals
import import_util


def validate_param_info(namespace):
    # Every column in every obs_ table should have an entry in the param_info
    # table except for id and obs_general_id.

    db = impglobals.DATABASE
    logger = impglobals.LOGGER

    logger.log('debug', 'Validating param_info table')

    obs_table_names = sorted(list(db.table_names(namespace, prefix='obs_')))

    pi_table_name = db.convert_raw_to_namespace(namespace, 'param_info')

    for obs_table_name in obs_table_names:
        column_list = db.table_info(namespace, obs_table_name)
        field_names = [x['field_name'] for x in column_list]
        for column in column_list:
            field_name = column['field_name']
            if (field_name == 'id' or
                field_name == 'timestamp' or
                field_name == 'obs_general_id' or
                field_name.startswith('d_') or
                'd_'+field_name in field_names or
                (field_name == 'opus_id' and
                 obs_table_name != 'obs_general') or
                (field_name.startswith('mult_'))):
                continue
            cmd = f"""
COUNT(*) FROM {pi_table_name} WHERE CATEGORY_NAME='{obs_table_name}' AND
NAME='{field_name}'"""
            res = db.general_select(cmd)
            count = res[0][0]
            if count == 0:
                logger.log('warning',
       f'OBS field "{obs_table_name}.{field_name}" missing param_info entry')

    # Every param_info entry should have a unique disp_order
    # This is a hideous query that looks for duplicate disp_order fields
    # within a given category as long as the field is displayed
    cmd = f"""
category_name, name FROM {pi_table_name} pi1 WHERE EXISTS
    (SELECT 1 FROM {pi_table_name} pi2 WHERE
        pi1.category_name=pi2.category_name AND
        pi1.disp_order=pi2.disp_order AND
        (pi1.display=1 OR pi1.display_results=1) AND
        (pi2.display=1 OR pi2.display_results=1)
        LIMIT 1,1)"""
    res = db.general_select(cmd)
    for cat_name, field_name in res:
        logger.log('warning',
    f'PARAM_INFO field "{cat_name}.{field_name}" has duplicate disp_order')

    # Every param_info entry should have a unique slug. Period.
    cmd = f"""
category_name, name FROM {pi_table_name} pi1 WHERE EXISTS
    (SELECT 1 FROM {pi_table_name} pi2 WHERE
        pi1.slug=pi2.slug
        LIMIT 1,1)"""
    res = db.general_select(cmd)
    for cat_name, field_name in res:
        logger.log('error',
    f'PARAM_INFO field "{cat_name}.{field_name}" has duplicate slug')


def validate_nulls(namespace):
    # Look for columns in OBS tables that don't contain nulls and yet the
    # column is marked as NULLS-OK and suggest the column type be changed.
    db = impglobals.DATABASE
    logger = impglobals.LOGGER

    logger.log('debug', 'Validating non-NULL columns')

    obs_table_names = sorted(list(db.table_names(namespace, prefix='obs_')))

    for obs_table_name in obs_table_names:
        column_list = db.table_info(namespace, obs_table_name)
        for column in column_list:
            field_name = column['field_name']
            notnull = column['field_notnull']
            if notnull:
                continue
            # OK the column allows nulls...are there any?
            full_obs_table_name = db.convert_raw_to_namespace(namespace,
                                                              obs_table_name)
            cmd = f"""
count(*) FROM {full_obs_table_name} WHERE {field_name} is NULL"""
            res = db.general_select(cmd)
            count = res[0][0]
            if count == 0:
                logger.log('info',
    f'Column "{full_obs_table_name}.{field_name}" allows NULLs but none found '+
    '- suggest changing column attributes')


def do_validate(namespace='perm'):
    impglobals.LOGGER.open(
            f'Performing database validation', limits={'info': -1, 'debug': -1})

    validate_param_info(namespace)
    validate_nulls(namespace)

    impglobals.LOGGER.close()
