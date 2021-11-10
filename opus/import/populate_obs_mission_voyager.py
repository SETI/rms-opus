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
    return target_name, target_name_info[2]

def helper_voyager_planet_id(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    # MISSION_PHASE_NAME exists for both VGISS and VGIRIS
    # Values are:
    #   Jupiter Encounter
    #   Neptune Encounter
    #   Saturn Encounter
    #   Uranus Encounter

    index_label = metadata['index_label']
    # For a profile, we derive the mission phase from the target name
    if 'VG_28' in index_label['VOLUME_ID']:
        target_name = index_row['TARGET_NAME'].upper()
        mp = VG_TARGET_TO_MISSION_PHASE_MAPPING[target_name]
    else:
        mp = index_row['MISSION_PHASE_NAME']

    pl = mp.upper()[:3]

    assert pl in ['JUP', 'SAT', 'URA', 'NEP']

    return pl

################################################################################
# THESE NEED TO BE IMPLEMENTED FOR EVERY MISSION
################################################################################

def populate_obs_general_VG_planet_id_OBS(**kwargs):
    return helper_voyager_planet_id(**kwargs)

def populate_obs_general_VG_planet_id_PROF(**kwargs):
    return helper_voyager_planet_id(**kwargs)


################################################################################
# THESE ARE SPECIFIC TO OBS_MISSION_VOYAGER
################################################################################

# These are verified to also exist in the Voyager IRIS PDS label so they should
# be kept at the mission level.

def populate_obs_mission_voyager_ert(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    # For PPS & UVS, we don't have EARTH_RECEIVED_TIME in the label.
    ert_time = index_row.get('EARTH_RECEIVED_TIME', 'UNK')

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
    index_row = metadata['supp_index_row']
    if index_row is None:
        return None

    index_label = metadata['index_label']
    # For occulation, we will fetch data from profile index
    if 'VG_28' in index_label['VOLUME_ID']:
        index_row = metadata['index_row']

    start_time = index_row['SPACECRAFT_CLOCK_START_COUNT']
    # VG_28xx doesn't have SPACECRAFT_CLOCK_PARTITION_NUMBER
    try:
        partition = import_util.safe_column(index_row,
                                            'SPACECRAFT_CLOCK_PARTITION_NUMBER')
        sc = str(partition) + '/' + start_time
    except KeyError:
        sc = start_time

    try:
        sc_cvt = opus_support.parse_voyager_sclk(sc)
    except Exception as e:
        import_util.log_nonrepeating_error(
            f'Unable to parse Voyager SCLK "{sc}": {e}')
        return None
    return sc_cvt

def populate_obs_mission_voyager_spacecraft_clock_count2(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['supp_index_row']
    if index_row is None:
        return None

    index_label = metadata['index_label']
    # For occulation, we will fetch data from profile index
    if 'VG_28' in index_label['VOLUME_ID']:
        index_row = metadata['index_row']

    stop_time = index_row['SPACECRAFT_CLOCK_STOP_COUNT']
    # VG_28xx doesn't have SPACECRAFT_CLOCK_PARTITION_NUMBER
    try:
        partition = import_util.safe_column(index_row,
                                            'SPACECRAFT_CLOCK_PARTITION_NUMBER')
        sc = str(partition) + '/' + stop_time
    except KeyError:
        sc = stop_time

    try:
        sc_cvt = opus_support.parse_voyager_sclk(sc)
    except Exception as e:
        import_util.log_nonrepeating_error(
            f'Unable to parse Voyager SCLK "{sc}": {e}')
        return None

    voyager_row = metadata['obs_mission_voyager_row']
    sc1 = voyager_row['spacecraft_clock_count1']
    if sc1 is not None and sc_cvt < sc1:
        import_util.log_warning(
    f'spacecraft_clock_count1 ({sc1}) and spacecraft_clock_count2 ({sc_cvt}) '
    +'are in the wrong order - setting to count1')
        sc_cvt = sc1

    return sc_cvt
