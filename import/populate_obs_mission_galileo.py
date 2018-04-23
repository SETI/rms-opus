################################################################################
# populate_obs_mission_galileo.py
#
# Routines to populate fields specific to Galileo. It may change fields in
# obs_general or obs_mission_galileo.
################################################################################

import julian

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
    index_row_num = metadata['index_row_num']
    index_row = metadata['index_row']
    image_id = index_row['IMAGE_ID']

    target_id = image_id[2]
    if target_id not in _GOSSI_TARGET_MAPPING:
        import_util.announce_nonrepeating_error(
            f'Unknown GOSSI target ID "{target_id}" in IMAGE_ID "{image_id}"'+
            f' [line {index_row_num}]')
        return None

    target_name = _GOSSI_TARGET_MAPPING[target_id]

    if target_name in TARGET_NAME_MAPPING:
        target_name = TARGET_NAME_MAPPING[target_name]
    if target_name is None:
        return None
    if target_name not in TARGET_NAME_INFO:
        import_util.announce_unknown_target_name(target_name, obs_general_row,
                                                 index_row_num)
        return None

    return target_name

def helper_galileo_planet_id(**kwargs):
    metadata = kwargs['metadata']
    index_row_num = metadata['index_row_num']
    obs_general_row = metadata['obs_general_row']
    target_name = helper_galileo_target_name(**kwargs)
    if target_name is None:
        return None
    planet_id, _ = TARGET_NAME_INFO[target_name]
    return planet_id

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
