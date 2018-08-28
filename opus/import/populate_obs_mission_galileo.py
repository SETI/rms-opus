################################################################################
# populate_obs_mission_galileo.py
#
# Routines to populate fields specific to Galileo. It may change fields in
# obs_general or obs_mission_galileo.
################################################################################

import opus_support

from config_data import *
import impglobals
import import_util

_GOSSI_TARGET_MAPPING = {
    'J': 'JUPITER',
    'A': 'AMALTHEA',
    'I': 'IO',
    'E': 'EUROPA',
    'G': 'GANYMEDE',
    'C': 'CALLISTO',
    'S': 'J MINOR SAT',
    'R': 'J RINGS',
    'H': 'STAR',
    'L': 'MOON',
    'W': 'EARTH',
    'V': 'VENUS',
    'U': 'IDA',
    'P': 'GASPRA',
    'N': 'NONE'
}


################################################################################
# THESE NEED TO BE IMPLEMENTED FOR EVERY MISSION
################################################################################

def helper_galileo_target_name(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    image_id = index_row['IMAGE_ID']

    target_id = image_id[2]
    if target_id not in _GOSSI_TARGET_MAPPING:
        import_util.log_nonrepeating_error(
            f'Unknown GOSSI target ID "{target_id}" in IMAGE_ID "{image_id}"')
        return None

    target_name = _GOSSI_TARGET_MAPPING[target_id]

    if target_name in TARGET_NAME_MAPPING:
        target_name = TARGET_NAME_MAPPING[target_name]
    if target_name is None:
        return None
    if target_name not in TARGET_NAME_INFO:
        import_util.announce_unknown_target_name(target_name)
        return None

    return target_name

def helper_galileo_planet_id(**kwargs):
    # WARNING: This will need to be changed if we ever get additional volumes
    # for Galileo. Right now we set everything to Jupiter rather than basing
    # it on the target name because we only have volumes for the time Galileo
    # was in Jupiter orbit (GO_0017 to GO_0023).
    return 'JUP'
    # metadata = kwargs['metadata']
    # obs_general_row = metadata['obs_general_row']
    # target_name = helper_galileo_target_name(**kwargs)
    # if target_name is None:
    #     return None
    # planet_id, _ = TARGET_NAME_INFO[target_name]
    # return planet_id

def populate_obs_general_GO_planet_id(**kwargs):
    return helper_galileo_planet_id(**kwargs)


################################################################################
# THESE ARE SPECIFIC TO OBS_MISSION_GALILEO
################################################################################

def populate_obs_mission_galileo_rev_no(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    orbit_number = index_row['ORBIT_NUMBER']

    return orbit_number

def populate_obs_mission_galileo_spacecraft_clock_count_cvt1(**kwargs):
    metadata = kwargs['metadata']
    galileo_row = metadata['obs_mission_galileo_row']
    sc = galileo_row['spacecraft_clock_count1']
    try:
        sc_cvt = opus_support.parse_galileo_sclk(sc)
    except Exception as e:
        import_util.log_nonrepeating_error(
            f'Unable to parse Galileo SCLK "{sc}": {e}')
        return None
    return sc_cvt

def populate_obs_mission_galileo_spacecraft_clock_count_cvt2(**kwargs):
    metadata = kwargs['metadata']
    galileo_row = metadata['obs_mission_galileo_row']
    sc = galileo_row['spacecraft_clock_count2']
    try:
        sc_cvt = opus_support.parse_galileo_sclk(sc)
    except Exception as e:
        import_util.log_nonrepeating_error(
            f'Unable to parse Galileo SCLK "{sc}": {e}')
        return None
    return sc_cvt
