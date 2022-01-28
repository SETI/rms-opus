################################################################################
# populate_util.py
#
# General routines that are common to many instruments.
################################################################################

import julian

from config_data import *
import import_util


def populate_observation_duration_from_time(**kwargs):
    metadata = kwargs['metadata']
    general_row = metadata['obs_general_row']
    start_time_sec = general_row['time1']
    stop_time_sec = general_row['time2']

    if start_time_sec is None or stop_time_sec is None:
        return None

    return max(stop_time_sec - start_time_sec, 0)

def _product_creation_time_helper(index, **kwargs):
    metadata = kwargs['metadata']
    index_row = metadata[index]
    pct = index_row['PRODUCT_CREATION_TIME']

    try:
        pct_sec = julian.tai_from_iso(pct)
    except Exception as e:
        import_util.log_nonrepeating_error(
            f'Bad product creation time format "{pct}": {e}')
        return None

    return pct_sec

def populate_product_creation_time_from_index(**kwargs):
    return _product_creation_time_helper('index_row', **kwargs)

def populate_product_creation_time_from_index_label(**kwargs):
    return _product_creation_time_helper('index_label', **kwargs)

def populate_product_creation_time_from_supp_index(**kwargs):
    return _product_creation_time_helper('supp_index_row', **kwargs)

def _data_set_id_helper(index, **kwargs):
    metadata = kwargs['metadata']
    index_label = metadata[index]
    dsi = index_label['DATA_SET_ID']
    return (dsi, dsi)

def populate_data_set_id_from_index(**kwargs):
    return _data_set_id_helper('index_row', **kwargs)

def populate_data_set_id_from_index_label(**kwargs):
    return _data_set_id_helper('index_label', **kwargs)

def populate_data_set_id_from_supp_index(**kwargs):
    return _data_set_id_helper('supp_index_row', **kwargs)

def populate_product_id_from_index(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    product_id = index_row['PRODUCT_ID']

    return product_id

def populate_product_id_from_supp_index(**kwargs):
    metadata = kwargs['metadata']
    supp_index_row = metadata.get('supp_index_row', None)
    if supp_index_row is None: # Needed for UVIS?
        return None
    product_id = supp_index_row['PRODUCT_ID']

    return product_id

def populate_target_name_from_index(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    target_name = index_row['TARGET_NAME'].strip()

    return target_name

def _star_name_helper(index, **kwargs):
    metadata = kwargs['metadata']
    index_label = metadata[index]
    try:
        target_name = index_label['STAR_NAME'].replace(' ', '').upper()
    except KeyError:
        # For VG_28xx
        target_name = index_label['SIGNAL_SOURCE_NAME_1'].upper()

    if target_name in TARGET_NAME_MAPPING:
        target_name = TARGET_NAME_MAPPING[target_name]

    if target_name not in TARGET_NAME_INFO:
        import_util.announce_unknown_target_name(target_name)
        if impglobals.ARGUMENTS.import_ignore_errors:
            return 'None'
        return None, None

    target_name_info = TARGET_NAME_INFO[target_name]
    return target_name, target_name_info

def populate_star_name_helper_index(**kwargs):
    return _star_name_helper('index_row', **kwargs)

def populate_star_name_helper_index_label(**kwargs):
    return _star_name_helper('index_label', **kwargs)

_OCC_RA_DEC_SLOP = 0. # Decided at meeting 2020/05/14 to have stars as fixed pts

def _occ_ra_dec_helper(index, **kwargs):
    target_name, target_name_info = _star_name_helper(index, **kwargs)
    if target_name is None:
        return None, None, None, None
    if target_name not in import_util.STAR_RA_DEC:
        import_util.log_nonrepeating_warning(
            f'Star "{target_name}" missing RA and DEC information'
        )
        return None, None, None, None

    return (STAR_RA_DEC[target_name][0]-_OCC_RA_DEC_SLOP,
            STAR_RA_DEC[target_name][0]+_OCC_RA_DEC_SLOP,
            STAR_RA_DEC[target_name][1]-_OCC_RA_DEC_SLOP,
            STAR_RA_DEC[target_name][1]+_OCC_RA_DEC_SLOP)

def populate_occ_ra_dec_helper_index(**kwargs):
    return _occ_ra_dec_helper('index_row', **kwargs)

def populate_occ_ra_dec_helper_index_label(**kwargs):
    return _occ_ra_dec_helper('index_label', **kwargs)
