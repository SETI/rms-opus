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

    return (target_name, target_name.title())


################################################################################
# THESE NEED TO BE IMPLEMENTED FOR EVERY MISSION
################################################################################

def populate_obs_general_VG_planet_id(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    # MISSION_PHASE_NAME exists for both VGISS and VGIRIS
    mp = index_row['MISSION_PHASE_NAME']
    pl = mp.upper()[:3]

    assert pl in ['JUP', 'SAT', 'URA', 'NEP']

    return pl


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

    return ert_time

def populate_obs_mission_voyager_ert_sec(**kwargs):
    metadata = kwargs['metadata']
    voyager_row = metadata['obs_mission_voyager_row']
    ert_time = voyager_row['ert']

    if ert_time is None or ert_time.startswith('UNK'):
        return None

    try:
        ert = julian.tai_from_iso(ert_time)
    except Exception as e:
        import_util.log_nonrepeating_error(
            f'"{ert_time}" is not a valid date-time format in '+
            f'populate_obs_mission_voyager_ert_sec: {e}')
        ert = None
    return ert

def populate_obs_mission_voyager_spacecraft_clock_count1(**kwargs):
    metadata = kwargs['metadata']
    supp_index_row = metadata['supp_index_row']
    if supp_index_row is None:
        return None
    partition = import_util.safe_column(supp_index_row,
                                        'SPACECRAFT_CLOCK_PARTITION_NUMBER')
    start_time = supp_index_row['SPACECRAFT_CLOCK_START_COUNT']

    return str(partition) + '/' + start_time

def populate_obs_mission_voyager_spacecraft_clock_count2(**kwargs):
    metadata = kwargs['metadata']
    supp_index_row = metadata['supp_index_row']
    if supp_index_row is None:
        return None
    partition = import_util.safe_column(supp_index_row,
                                        'SPACECRAFT_CLOCK_PARTITION_NUMBER')
    stop_time = supp_index_row['SPACECRAFT_CLOCK_STOP_COUNT']

    return str(partition) + '/' + stop_time

def populate_obs_mission_voyager_spacecraft_clock_count_cvt1(**kwargs):
    metadata = kwargs['metadata']
    voyager_row = metadata['obs_mission_voyager_row']
    sc = voyager_row['spacecraft_clock_count1']
    try:
        sc_cvt = opus_support.parse_voyager_sclk(sc)
    except Exception as e:
        import_util.log_nonrepeating_error(
            f'Unable to parse Voyager SCLK "{sc}": {e}')
        return None
    return sc_cvt

def populate_obs_mission_voyager_spacecraft_clock_count_cvt2(**kwargs):
    metadata = kwargs['metadata']
    voyager_row = metadata['obs_mission_voyager_row']
    sc = voyager_row['spacecraft_clock_count2']
    try:
        sc_cvt = opus_support.parse_voyager_sclk(sc)
    except Exception as e:
        import_util.log_nonrepeating_error(
            f'Unable to parse Voyager SCLK "{sc}": {e}')
        return None
    return sc_cvt
