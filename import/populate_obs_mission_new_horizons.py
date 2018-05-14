################################################################################
# populate_obs_mission_new_horizons.py
#
# Routines to populate fields specific to new_horizons. It may change fields in
# obs_general or obs_mission_new_horizons.
################################################################################

import julian

from config_data import *
import impglobals
import import_util


################################################################################
# THESE NEED TO BE IMPLEMENTED FOR EVERY MISSION
################################################################################

def helper_new_horizons_target_name(**kwargs):
    metadata = kwargs['metadata']
    supp_index_row = metadata['supp_index_row']

    target_name = supp_index_row['TARGET_NAME'].upper()
    if target_name in TARGET_NAME_MAPPING:
        target_name = TARGET_NAME_MAPPING[target_name]

    return (target_name, target_name.title())

def helper_new_horizons_planet_id(**kwargs):
    metadata = kwargs['metadata']
    supp_index_row = metadata['supp_index_row']
    index_row_num = metadata['index_row_num']
    target_name = supp_index_row['TARGET_NAME'].upper()
    if target_name in TARGET_NAME_MAPPING:
        target_name = TARGET_NAME_MAPPING[target_name]
    if target_name not in TARGET_NAME_INFO:
        import_util.announce_unknown_target_name(target_name, index_row_num)
        pl = None
    else:
        pl, _ = TARGET_NAME_INFO[target_name]

    return pl

def populate_obs_general_NH_planet_id(**kwargs):
    pl = helper_new_horizons_planet_id(**kwargs)
    if pl is None:
        return 'OTH'
    return pl


################################################################################
# THESE ARE SPECIFIC TO OBS_MISSION_NEW_HORIZONS
################################################################################

def populate_obs_mission_new_horizons_spacecraft_clock_count1(**kwargs):
    metadata = kwargs['metadata']
    supp_index_row = metadata['supp_index_row']
    if supp_index_row is None:
        return None
    partition = import_util.safe_column(supp_index_row,
                                        'SPACECRAFT_CLOCK_COUNT_PARTITION')
    start_time = supp_index_row['SPACECRAFT_CLOCK_START_COUNT']

    return str(partition) + '/' + start_time

def populate_obs_mission_new_horizons_spacecraft_clock_count2(**kwargs):
    metadata = kwargs['metadata']
    supp_index_row = metadata['supp_index_row']
    if supp_index_row is None:
        return None
    partition = import_util.safe_column(supp_index_row,
                                        'SPACECRAFT_CLOCK_COUNT_PARTITION')
    stop_time = supp_index_row['SPACECRAFT_CLOCK_STOP_COUNT']

    return str(partition) + '/' + stop_time
