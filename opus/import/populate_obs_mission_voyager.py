################################################################################
# populate_obs_mission_voyager.py
#
# Routines to populate fields specific to Voyager. It may change fields in
# obs_general or obs_mission_voyager.
################################################################################

import julian

import opus_support

from config_data import *
import impglobals
import import_util


################################################################################
# HELPER FUNCTIONS USED BY VOYAGER INSTRUMENTS
################################################################################

def helper_voyager_target_name(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']

    target_name = index_row['TARGET_NAME'].upper()
    if target_name in TARGET_NAME_MAPPING:
        target_name = TARGET_NAME_MAPPING[target_name]

    if target_name not in TARGET_NAME_INFO:
        import_util.announce_unknown_target_name(target_name)
        if impglobals.ARGUMENTS.import_ignore_errors:
            return 'None'
        return None
    target_name_info = TARGET_NAME_INFO[target_name]
    if len(target_name_info) == 3:
        return target_name, target_name_info[2]

    return (target_name, target_name.title())

def helper_voyager_planet_id(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    # MISSION_PHASE_NAME exists for both VGISS and VGIRIS
    # Values are:
    #   Jupiter Encounter
    #   Neptune Encounter
    #   Saturn Encounter
    #   Uranus Encounter
    mp = index_row['MISSION_PHASE_NAME']
    pl = mp.upper()[:3]

    assert pl in ['JUP', 'SAT', 'URA', 'NEP']

    return pl

################################################################################
# THESE NEED TO BE IMPLEMENTED FOR EVERY MISSION
################################################################################

def populate_obs_general_VG_planet_id(**kwargs):
    return helper_voyager_planet_id(**kwargs)


################################################################################
# THESE ARE SPECIFIC TO OBS_MISSION_VOYAGER
################################################################################

# These are verified to also exist in the Voyager IRIS PDS label so they should
# be kept at the mission level.

def populate_obs_mission_voyager_ert(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    ert_time = index_row['EARTH_RECEIVED_TIME']

    if ert_time.startswith('UNK'):
        return None

    try:
        ert_sec = julian.tai_from_iso(ert_time)
    except Exception as e:
        import_util.log_nonrepeating_error(
            f'Bad earth received time format "{ert_time}": {e}')
        return None

    return ert_sec

def populate_obs_mission_voyager_spacecraft_clock_count1(**kwargs):
    metadata = kwargs['metadata']
    supp_index_row = metadata['supp_index_row']
    if supp_index_row is None:
        return None
    partition = import_util.safe_column(supp_index_row,
                                        'SPACECRAFT_CLOCK_PARTITION_NUMBER')
    start_time = supp_index_row['SPACECRAFT_CLOCK_START_COUNT']

    sc = str(partition) + '/' + start_time
    try:
        sc_cvt = opus_support.parse_voyager_sclk(sc)
    except Exception as e:
        import_util.log_nonrepeating_error(
            f'Unable to parse Voyager SCLK "{sc}": {e}')
        return None
    return sc_cvt

def populate_obs_mission_voyager_spacecraft_clock_count2(**kwargs):
    metadata = kwargs['metadata']
    supp_index_row = metadata['supp_index_row']
    if supp_index_row is None:
        return None
    partition = import_util.safe_column(supp_index_row,
                                        'SPACECRAFT_CLOCK_PARTITION_NUMBER')
    stop_time = supp_index_row['SPACECRAFT_CLOCK_STOP_COUNT']

    sc = str(partition) + '/' + stop_time
    try:
        sc_cvt = opus_support.parse_voyager_sclk(sc)
    except Exception as e:
        import_util.log_nonrepeating_error(
            f'Unable to parse Voyager SCLK "{sc}": {e}')
        return None
    return sc_cvt
