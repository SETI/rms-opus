################################################################################
# populate_obs_mission_voyager.py
#
# Routines to populate fields specific to Voyager. It may change fields in
# obs_general or obs_mission_voyager.
################################################################################

import julian

from config_data import *
import impglobals
import import_util


################################################################################
# HELPER FUNCTIONS USED BY VOYAGER INSTRUMENTS
################################################################################

# XXX
def helper_voyager_planet_id(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    obs_general_row = metadata['obs_general_row']
    target_name = index_row['TARGET_NAME'].upper()
    if target_name in TARGET_NAME_MAPPING:
        target_name = TARGET_NAME_MAPPING[target_name]
    if target_name not in TARGET_NAME_INFO:
        import_util.announce_unknown_target_name(target_name)
        pl = None
    else:
        pl, _ = TARGET_NAME_INFO[target_name]
    return pl

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
    mp = index_row['MISSION_PHASE_NAME']
    pl = mp.upper()[:3]

    assert pl in ['JUP', 'SAT', 'URA', 'NEP']

    return pl


################################################################################
# THESE ARE SPECIFIC TO OBS_MISSION_VOYAGER
################################################################################

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
    except (ValueError,TypeError):
        import_util.log_nonrepeating_error(
            f'"{ert_time}" is not a valid date-time format in '+
            f'mission_voyager_ert_sec')
        ert = None
    return ert
