################################################################################
# populate_obs_mission_cassini.py
#
# Routines to populate fields specific to Cassini. It may change fields in
# obs_general or obs_mission_cassini.
################################################################################

import re

import julian

from config_data import *
import impglobals
import import_util

# Ordering:
#   prime_inst_id must come before prime
#   instrument_id must come before prime

# These codes show up as the last two characters of the second part of an
# observation name.
_CASSINI_TARGET_CODE_MAPPING = {
    'AG': 'AG (Aegaeon)',
    'AN': 'AN (Anthe)',
    'AT': 'AT (Atlas)',
    'CA': 'CA (Callisto)',
    'CO': 'CO (Co-rotation)',
    'CP': 'CP (Calypso)',
    'DA': 'DA (Daphnis)',
    'DI': 'DI (Dione)',
    'DN': 'DN (Downstream of the wake)',
    'DR': 'DR (Dust RAM direction)',
    'EA': 'EA (Earth)',
    'EN': 'EN (Enceladus)',
    'EP': 'EP (Epimetheus)',
    'EU': 'EU (Europa)',
    'FO': 'FO (Fomalhaut)',
    'FT': 'FT (Flux tube)',
    'GA': 'GA (Ganymede)',
    'HE': 'HR (Helene)',
    'HI': 'HI (Himalia)',
    'HY': 'HY (Hyperion)',
    'IA': 'IA (Iapetus)',
    'IC': 'IC (Instrument calibration)',
    'IO': 'IO (Io)',
    'JA': 'JA (Janus)',
    'JU': 'JU (Jupiter)',
    'ME': 'ME (Methone)',
    'MI': 'MI (Mimas)',
    'NA': 'Not Applicable',
    'OT': 'OT (Other)',
    'PA': 'PA (Pandora)',
    'PH': 'PH (Phoebe)',
    'PL': 'PL (Pallene)',
    'PM': 'PM (Prometheus)',
    'PN': 'PN (Pan)',
    'PO': 'PO (Polydeuces)',
    'PR': 'PR (Plasma RAM direction)',
    'RA': 'RA (Ring A)',
    'RB': 'RB (Ring B)',
    'RC': 'RC (Ring C)',
    'RD': 'RD (Ring D)',
    'RE': 'RE (Ring E)',
    'RF': 'RF (Ring F)',
    'RG': 'RG (Ring G)',
    'RH': 'RH (Rhea)',
    'RI': 'RI (Rings - general)',
    'SA': 'SA (Saturn)',
    'SC': 'SC (Spacecraft activity)',
    'SK': 'SK (Skeleton request)',
    'SR': 'SR (Spacecraft RAM direction)',
    'ST': 'ST (Star)',
    'SU': 'SU (Sun)',
    'SW': 'SE (Solar wind)',
    'TE': 'TE (Tethys)',
    'TI': 'TI (Titan)',
    'TL': 'TL (Telesto)',
    'TO': 'TO (Io torus)',
    'UP': 'UP (Upstream of the wake)'
}


################################################################################
# HELPER FUNCTIONS USED BY CASSINI INSTRUMENTS
################################################################################

def helper_cassini_obs_name(**kwargs):
    "Look up the obs_name in the main or supplemental index."
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    obs_id = index_row.get('OBSERVATION_ID', None)
    if obs_id is None:
        supp_index_row = metadata.get('supp_index_row', None) # COUVIS
        if supp_index_row is not None:
            obs_id = supp_index_row.get('OBSERVATION_ID', None)

    return obs_id

def helper_cassini_valid_obs_name(obs_name):
    """Check a Cassini observation name to see if it is parsable. Such a
    name will have four parts separated by _:

    <PRIME> _ <REVNO> <TARGETCODE> _ <ACTIVITYNAME> <ACTIVITYNUMBER> _ <INST>

    <PRIME> can be: ([A-Z]{2,5}|22NAV)
        - '18ISS', '22NAV', 'CIRS', 'IOSIC', 'IOSIU', 'IOSIV', 'ISS',
          'NAV', 'UVIS', 'VIMS'
        - If <INST> is 'PRIME' or 'PIE' then <PRIME> can only be one of:
          '22NAV', 'CIRS', 'ISS', 'NAV', 'UVIS', 'VIMS'

    <REVNO> can be: ([0-2]\d\d|00[A-C]|C\d\d)
        - 000 to 299
        - 00A to 00C
        - C00 to C99

    <TARGETCODE> can be: [A-Z]{2}
        - See _CASSINI_TARGET_CODE_MAPPING

    <ACTIVITYNAME> can be: [0-9A-Z]+
        - Everything except the final three digits

    <ACTIVITYNUMBER> can be: \d\d\d
        - Last final three digits

    <INST> can be one of: [A-Z]{2,7}
        - 'PRIME', 'PIE' (prime inst is in <PRIME>)
        - 'CAPS', 'CDA', 'CIRS', 'INMS', 'ISS', 'MAG', 'MIMI', 'NAV', 'RADAR',
          'RPWS', 'RSS', 'SI', 'UVIS', 'VIMS'
        - Even though these aren't instruments, it can also be:
          'AACS' (reaction wheel assembly),
          'ENGR' (engineering),
          'IOPS',
          'MP' (mission planning),
          'RIDER', 'SP', 'TRIGGER'
    """

    return re.fullmatch(
'([A-Z]{2,5}|22NAV)_([0-2]\d\d|00[A-C]|C\d\d)[A-Z]{2}_[0-9A-Z]+\d\d\d_[A-Z]{2,7}',
        obs_name) is not None

def helper_cassini_planet_id(**kwargs):
    """Find the planet associated with an observation. This is usually based on
    the TARGET_NAME field, but if the planet is marked as None based on the
    target, we look at the time of the observation to bind it to Jupiter or
    Saturn."""

    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    obs_general_row = metadata['obs_general_row']
    target_name = index_row['TARGET_NAME'].upper()
    if target_name in TARGET_NAME_MAPPING:
        target_name = TARGET_NAME_MAPPING[target_name]
    if target_name not in TARGET_NAME_INFO:
        import_util.announce_unknown_target_name(target_name, obs_general_row)
        pl = None
    else:
        pl, _ = TARGET_NAME_INFO[target_name]
    if pl is not None:
        return pl
    time_sec1 = obs_general_row['time_sec1']
    time_sec2 = obs_general_row['time_sec2']
    if time_sec1 >= 26611232.0 and time_sec2 <= 41904032.0:
        # '2000-11-04' to '2001-04-30'
        return 'JUP'
    if time_sec1 >= 127180832.0:
        # '2004-01-12'
        return 'SAT'
    return None

################################################################################
# THESE NEED TO BE IMPLEMENTED FOR EVERY MISSION
################################################################################

def populate_obs_general_CO_planet_id(**kwargs):
    return helper_cassini_planet_id(**kwargs)


################################################################################
# THESE ARE SPECIFIC TO OBS_MISSION_CASSINI
################################################################################

def populate_obs_mission_cassini_obs_name(**kwargs):
    return helper_cassini_obs_name(**kwargs)

def populate_obs_mission_cassini_prime_inst_id(**kwargs):
    obs_name = helper_cassini_obs_name(**kwargs)
    if obs_name is None:
        return None

    if not helper_cassini_valid_obs_name(obs_name):
        return None

    obs_parts = obs_name.split('_')
    first = obs_parts[0]
    last = obs_parts[-1]

    # If the last part is PRIME, the prime_inst is the first part. Otherwise
    # it's the last part.
    # From Matt Tiscareno:
    # PIE is equivalent to PRIME.  These were “pre-integrated elements” that
    # were considered to be tall tent poles in the process of portioning out
    # observation time.
    if last == 'PRIME' or last == 'PIE':
        if first == 'NAV' or first == '22NAV':
            prime_inst_id = 'ISS'
        else:
            prime_inst_id = first
    else:
        if last == 'NAV' or last == 'SI':
            prime_inst_id = 'ISS'
        else:
            prime_inst_id = last

    if prime_inst_id not in ['CIRS', 'ISS', 'UVIS', 'VIMS']:
        prime_inst_id = 'Other'

    return (prime_inst_id, prime_inst_id)

def populate_obs_mission_cassini_is_prime(**kwargs):
    metadata = kwargs['metadata']
    cassini_row = metadata['obs_mission_cassini_row']
    prime_inst = cassini_row['prime_inst_id']
    inst_id = cassini_row['instrument_id']

    # Change COISS to ISS, etc.
    inst_id = inst_id.replace('CO', '')
    if prime_inst == inst_id:
        return 'Yes'
    return 'No'

def populate_obs_mission_cassini_cassini_target_code(**kwargs):
    obs_name = helper_cassini_obs_name(**kwargs)
    if obs_name is None:
        return None

    if not helper_cassini_valid_obs_name(obs_name):
        return None

    obs_parts = obs_name.split('_')
    target_code = obs_parts[1][-2:]
    if target_code in _CASSINI_TARGET_CODE_MAPPING:
        return (target_code, _CASSINI_TARGET_CODE_MAPPING[target_code])

    return None

def populate_obs_mission_cassini_activity_name(**kwargs):
    obs_name = helper_cassini_obs_name(**kwargs)
    if not helper_cassini_valid_obs_name(obs_name):
        return None

    obs_parts = obs_name.split('_')
    return obs_parts[2][:-3]

def populate_obs_mission_cassini_ert_sec1(**kwargs):
    metadata = kwargs['metadata']
    index_row_num = metadata['index_row_num']
    index_row = metadata['index_row']

    # START_TIME isn't available for COUVIS
    start_time = index_row.get('EARTH_RECEIVED_START_TIME', None)
    if start_time == 'UNK' or start_time is None:
        return None
    try:
        ert = julian.tai_from_iso(start_time)
    except ValueError:
        import_util.announce_nonrepeating_error(
            f'"{start_time}" is not a valid date-time format in '+
            f'mission_cassini_ert_sec1 [line {index_row_num}]')
        ert = None
    return ert

def populate_obs_mission_cassini_ert_sec2(**kwargs):
    metadata = kwargs['metadata']
    index_row_num = metadata['index_row_num']
    index_row = metadata['index_row']

    # STOP_TIME isn't available for COUVIS
    stop_time = index_row.get('EARTH_RECEIVED_STOP_TIME', None)
    if stop_time == 'UNK' or stop_time is None:
        return None
    try:
        ert = julian.tai_from_iso(stop_time)
    except ValueError:
        import_util.announce_nonrepeating_error(
            f'"{stop_time}" is not a valid date-time format in '+
            f'mission_cassini_ert_sec2 [line {index_row_num}]')
        ert = None
    return ert
