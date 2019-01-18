################################################################################
# populate_obs_mission_new_horizons.py
#
# Routines to populate fields specific to new_horizons. It may change fields in
# obs_general or obs_mission_new_horizons.
################################################################################

import julian

import opus_support

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

    if target_name not in TARGET_NAME_INFO:
        import_util.announce_unknown_target_name(target_name)
        if impglobals.ARGUMENTS.import_ignore_errors:
            return 'None'
        return None
    target_name_info = TARGET_NAME_INFO[target_name]
    if len(target_name_info) == 3:
        return target_name, target_name_info[2]

    return (target_name, target_name.title())

def helper_new_horizons_planet_id(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['supp_index_row']
    # Values are:
    #   Jupiter Encounter
    #   Pluto Cruise
    #   Pluto Encounter
    #   Post-Launch Checkout
    mp = index_row['MISSION_PHASE_NAME'].upper()
    if mp == 'JUPITER ENCOUNTER':
        return 'JUP'
    if (mp == 'PLUTO CRUISE' or
        mp == 'PLUTO ENCOUNTER'):
        return 'PLU'
    if mp == 'POST-LAUNCH CHECKOUT':
        return 'OTH'

    import_util.log_nonrepeating_error(
        f'Unknown MISSION_PHASE_NAME "{mp}"')
    return None

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

    sc = str(partition) + '/' + start_time

    try:
        sc_cvt = opus_support.parse_new_horizons_sclk(sc)
    except Exception as e:
        import_util.log_nonrepeating_error(
            f'Unable to parse New Horizons SCLK "{sc}": {e}')
        return None

    return sc_cvt

def populate_obs_mission_new_horizons_spacecraft_clock_count2(**kwargs):
    metadata = kwargs['metadata']
    supp_index_row = metadata['supp_index_row']
    if supp_index_row is None:
        return None
    partition = import_util.safe_column(supp_index_row,
                                        'SPACECRAFT_CLOCK_COUNT_PARTITION')
    stop_time = supp_index_row['SPACECRAFT_CLOCK_STOP_COUNT']

    sc = str(partition) + '/' + stop_time

    try:
        sc_cvt = opus_support.parse_new_horizons_sclk(sc)
    except Exception as e:
        import_util.log_nonrepeating_error(
            f'Unable to parse New Horizons SCLK "{sc}": {e}')
        return None

    nh_row = metadata['obs_mission_new_horizons_row']
    sc1 = nh_row['spacecraft_clock_count1']
    if sc1 is not None and sc_cvt < sc1:
        import_util.log_warning(
    f'spacecraft_clock_count1 ({sc1}) and spacecraft_clock_count2 ({sc_cvt}) '
    +f'are in the wrong order - setting to count1')
        sc_cvt = sc1

    return sc_cvt
