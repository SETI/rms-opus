################################################################################
# validate.py
#
# Perform various validations on the database.
################################################################################

import os

import pdsfile

import impglobals
import import_util


def validate_param_info(namespace):
    # Every column in every obs_ table should have an entry in the param_info
    # table except for id and obs_general_id.
    # Exceptions are:
    #   volume_id in tables other than obs_pds
    #   instrument_id in tables other than obs_general

    db = impglobals.DATABASE
    logger = impglobals.LOGGER

    logger.log('debug', 'Validating param_info table')

    obs_table_names = sorted(list(db.table_names(namespace, prefix='obs_')))

    pi_table_name = db.convert_raw_to_namespace(namespace, 'param_info')

    q = db.quote_identifier

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
            if field_name == 'volume_id' and obs_table_name != 'obs_pds':
                continue
            if (field_name == 'instrument_id' and
                obs_table_name != 'obs_general'):
                continue
            cmd = f"""
COUNT(*) FROM {q(pi_table_name)} WHERE CATEGORY_NAME='{obs_table_name}' AND
NAME='{field_name}'"""
            res = db.general_select(cmd)
            count = res[0][0]
            if count == 0:
                logger.log('error',
       f'OBS field "{obs_table_name}.{field_name}" missing param_info entry')

    # Every param_info entry should have a unique disp_order
    # This is a hideous query that looks for duplicate disp_order fields
    # within a given category as long as the field is displayed
    cmd = f"""
{q('category_name')}, {q('name')} FROM {q(pi_table_name)} {q('pi1')} WHERE EXISTS
    (SELECT 1 FROM {q(pi_table_name)} {q('pi2')} WHERE
        {q('pi1')}.{q('category_name')}={q('pi2')}.{q('category_name')} AND
        {q('pi1')}.{q('disp_order')}={q('pi2')}.{q('disp_order')} AND
        ({q('pi1')}.display=1 OR {q('pi1')}.{q('display_results')}=1) AND
        ({q('pi2')}.display=1 OR {q('pi2')}.{q('display_results')}=1)
        LIMIT 1,1)"""
    res = db.general_select(cmd)
    for cat_name, field_name in res:
        logger.log('error',
    f'PARAM_INFO field "{cat_name}.{field_name}" has duplicate disp_order')

    # Every param_info entry should have a unique slug. Period.
    cmd = f"""
{q('category_name')}, {q('name')} FROM {q(pi_table_name)} {q('pi1')} WHERE EXISTS
    (SELECT 1 FROM {q(pi_table_name)} {q('pi2')} WHERE
        {q('pi1')}.{q('slug')}={q('pi2')}.{q('slug')}
        LIMIT 1,1)"""
    res = db.general_select(cmd)
    for cat_name, field_name in res:
        logger.log('error',
    f'PARAM_INFO field "{cat_name}.{field_name}" has duplicate slug')


def validate_nulls(namespace):
    # Look for columns in OBS tables that don't contain nulls and yet the
    # column is marked as NULLS-OK and suggest the column type be changed.
    # We ignore obs_surface_geometry__ tables because they all come from a
    # single template so are harder to analyze.

    db = impglobals.DATABASE
    logger = impglobals.LOGGER

    logger.log('debug', 'Validating non-NULL columns')

    obs_table_names = sorted(list(db.table_names(namespace, prefix='obs_')))
    q = db.quote_identifier

    for obs_table_name in obs_table_names:
        if obs_table_name.startswith('obs_surface_geometry__'):
            continue
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
count(*) FROM {q(full_obs_table_name)} WHERE {q(field_name)} is NULL"""
            res = db.general_select(cmd)
            count = res[0][0]
            if count == 0:
                logger.log('info',
    f'Column "{full_obs_table_name}.{field_name}" allows NULLs but none found '+
    '- suggest changing column attributes')


def validate_min_max_order(namespace):
    # Look for pairs of columns X1/X2 and check to make sure that X1 <= X2 in
    # all non-NULL cases.

    db = impglobals.DATABASE
    logger = impglobals.LOGGER

    logger.log('debug', 'Validating MIN/MAX columns')

    obs_table_names = sorted(list(db.table_names(namespace, prefix='obs_')))

    pi_table_name = db.convert_raw_to_namespace(namespace, 'param_info')

    q = db.quote_identifier

    for obs_table_name in obs_table_names:
        full_obs_table_name = db.convert_raw_to_namespace(namespace,
                                                          obs_table_name)
        column_list = db.table_info(namespace, obs_table_name)
        column_list.sort(key=lambda x:x['field_name'])
        for column in column_list:
            field_name1 = column['field_name']
            if not field_name1.endswith('1'):
                continue
            field_name2 = field_name1[:-1] + '2'
            if field_name2 not in [x['field_name'] for x in column_list]:
                logger.log('error',
    f'Column "{full_obs_table_name}.{field_name1}" present but there is no '
    +f'{field_name2}')
                continue

            # Check param_info to see if this is a longitude field
            cmd = f"""
form_type FROM {q(pi_table_name)} WHERE CATEGORY_NAME='{obs_table_name}' AND
NAME='{field_name1}'"""
            res = db.general_select(cmd)
            if len(res) == 0:
                logger.log('error',
    f'No param_info entry for "{full_obs_table_name}.{field_name1}"')
                continue
            if len(res) > 1:
                logger.log('error',
    f'More than one param_info entry for "{full_obs_table_name}.{field_name1}"')
                continue
            pi_form_type = res[0][0]
            if pi_form_type.startswith('LONG'):
                continue

            cmd = f"""
opus_id FROM {q(full_obs_table_name)} WHERE {q(field_name2)} < {q(field_name1)}"""
            res = db.general_select(cmd)
            if len(res):
                opus_ids = [x[0] for x in res]
                logger.log('error',
    f'Column "{full_obs_table_name}.{field_name1}" has values greater than '+
    f'{field_name2} for some OPUS IDs; first 10: ' + ' '.join(opus_ids[:10]))


def do_validate(namespace='perm'):
    impglobals.LOGGER.open(
            f'Performing database validation', limits={'info': -1, 'debug': -1})

    validate_param_info(namespace)
    validate_nulls(namespace)
    validate_min_max_order(namespace)

    impglobals.LOGGER.close()
