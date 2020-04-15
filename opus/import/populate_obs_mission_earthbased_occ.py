################################################################################
# populate_obs_mission_earthbased.py
#
# Routines to populate fields specific to Earth-based instruments.
# It may change fields in obs_general or obs_mission_earthbased.
################################################################################

import opus_support

from config_data import *
import impglobals
import import_util


################################################################################
# THESE NEED TO BE IMPLEMENTED FOR EVERY MISSION
################################################################################

def helper_earthbased_target_name(**kwargs):
    metadata = kwargs['metadata']
    index_label = metadata['index_label']
    target_name = index_label['TARGET_NAME']

    if target_name in TARGET_NAME_MAPPING:
        target_name = TARGET_NAME_MAPPING[target_name]
    if target_name is None:
        return None
    if target_name not in TARGET_NAME_INFO:
        import_util.announce_unknown_target_name(target_name)
        return None

    target_name_info = TARGET_NAME_INFO[target_name]
    if len(target_name_info) == 3:
        return target_name, target_name_info[2]

    return (target_name, import_util.cleanup_target_name(target_name))

def helper_earthbased_planet_id(**kwargs):
    return 'SAT'

def populate_obs_general_EB_planet_id_OCC(**kwargs):
    return helper_earthbased_planet_id(**kwargs)


################################################################################
# THESE ARE SPECIFIC TO OBS_MISSION_GALILEO
################################################################################

def populate_obs_mission_earthbased_spacecraft_clock_count1(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    sc = index_row['SPACECRAFT_CLOCK_START_COUNT']
    try:
        sc_cvt = opus_support.parse_earthbased_sclk(sc)
    except Exception as e:
        import_util.log_nonrepeating_error(
            f'Unable to parse Galileo SCLK "{sc}": {e}')
        return None
    return sc_cvt

# There is no SPACECRAFT_CLOCK_STOP_COUNT for Galileo
def populate_obs_mission_earthbased_spacecraft_clock_count2(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    sc = index_row['SPACECRAFT_CLOCK_START_COUNT']
    try:
        sc_cvt = opus_support.parse_earthbased_sclk(sc)
    except Exception as e:
        import_util.log_nonrepeating_error(
            f'Unable to parse Galileo SCLK "{sc}": {e}')
        return None
    return sc_cvt
