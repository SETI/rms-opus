################################################################################
# populate_obs_mission_cassini.py
#
# Routines to populate fields specific to Cassini. It may change fields in
# obs_general or obs_mission_cassini.
################################################################################

import re

import julian

import opus_support

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

# These date ranges are used to deduce the MISSION_PHASE_NAME for COUVIS and
# COVIMS because those instruments don't include it in their metadata. These
# were derived from COISS and adjusted so that there is complete date range
# coverage. When there was a gap, the earlier phase was extended to the
# beginning of the later one, for lack of anything better to do.
_CASSINI_PHASE_NAME_MAPPING = (
    # Short encounters that interrupt longer ones; these take priority so
    # are listed first
    ('Phoebe Encounter',          julian.tai_from_iso('2004-163T04:30:06.353'), julian.tai_from_iso('2004-163T20:52:47.180')),
    ('Saturn Orbit Insertion',    julian.tai_from_iso('2004-183T03:11:40.288'), julian.tai_from_iso('2004-183T05:15:46.245')),
    ('Titan A Encounter',         julian.tai_from_iso('2004-300T00:30:21.455'), julian.tai_from_iso('2004-300T21:15:32.979')),
    ('Titan B Encounter',         julian.tai_from_iso('2004-348T00:18:13.469'), julian.tai_from_iso('2004-348T22:03:45.065')),
    # Full length encounters that completely cover the mission timeline
    ('Science Cruise',            julian.tai_from_iso('1997-001T00:00:00.000'), julian.tai_from_iso('2000-262T00:32:38.930')), # '2000-209T02:40:23.416'
    ('Earth-Jupiter Cruise',      julian.tai_from_iso('2000-262T00:32:38.930'), julian.tai_from_iso('2001-014T23:02:09.804')), # '2001-013T22:47:48.047'
    ('Jupiter Encounter',         julian.tai_from_iso('2001-014T23:02:09.804'), julian.tai_from_iso('2001-071T12:28:05.413')), # '2001-071T00:58:38.838'
    ('Cruise Science',            julian.tai_from_iso('2001-071T12:28:05.413'), julian.tai_from_iso('2003-138T02:16:18.383')), # '2003-115T07:45:08.222'
    ('Space Science',             julian.tai_from_iso('2003-138T02:16:18.383'), julian.tai_from_iso('2004-037T02:07:06.418')), # '2003-359T10:29:18.711'
    ('Approach Science',          julian.tai_from_iso('2004-037T02:07:06.418'), julian.tai_from_iso('2004-164T02:33:41.000')), # '2004-162T14:47:05.854'
    ('Tour Pre-Huygens',          julian.tai_from_iso('2004-164T02:33:41.000'), julian.tai_from_iso('2004-359T12:53:08.998')), # '2004-358T13:47:22.548'),
    ('Huygens Probe Separation',  julian.tai_from_iso('2004-359T12:53:08.998'), julian.tai_from_iso('2004-360T13:30:10.410')), # '2004-359T13:47:22.981'),
    # The descent actually happened on Jan 14
    ('Huygens Descent',           julian.tai_from_iso('2004-360T13:30:10.410'), julian.tai_from_iso('2005-015T18:28:29.451')), # '2005-001T14:28:54.449'),
    ('Tour',                      julian.tai_from_iso('2005-015T18:28:29.451'), julian.tai_from_iso('2008-183T21:04:08.998')), # '2008-183T09:17:06.323'),
    ('Extended Mission',          julian.tai_from_iso('2008-183T21:04:08.998'), julian.tai_from_iso('2010-285T05:22:24.745')), # '2010-283T14:14:20.741'),
    ('Extended-Extended Mission', julian.tai_from_iso('2010-285T05:22:24.745'), julian.tai_from_iso('2020-001T00:00:00.000'))
)

# These mappings are for the TARGET_DESC field to clean them up
COISS_TARGET_DESC_MAPPING = {
    'DIONE, RHEA, MIMAS(?), RINGS': 'ICY SATELLITES',
    'GENERIC-SATELLITE': 'ICY SATELLITES',
    'SATELLITE SEARCH': 'ICY SATELLITES',
    'TETHYS, RHEA, RINGS': 'ICY SATELLITES',
    'ENCELADUS, RINGS': 'ENCELADUS',
    'IAPETUS FP1': 'IAPETUS',
    'METHON': 'METHONE',
    'ROCK': 'ROCKS',
    'STAR -- CW LEO': 'STAR',
    'STAR -- ETA CAR': 'STAR',
    '--': 'UNKNOWN',
    'UNK': 'UNKNOWN',
    'F RING': 'SATURN-FRING'
}

################################################################################
# HELPER FUNCTIONS USED BY CASSINI INSTRUMENTS
################################################################################

def helper_cassini_obs_name(**kwargs):
    "Look up the obs_id in the main or supplemental index."
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    obs_id = index_row.get('OBSERVATION_ID', None)
    if obs_id is None:
        supp_index_row = metadata.get('supp_index_row', None) # COUVIS & CORSS
        if supp_index_row is not None:
            obs_id = supp_index_row.get('OBSERVATION_ID', None)
    if obs_id is None:
        import_util.log_nonrepeating_error('No OBSERVATION_ID found')
    if obs_id == '':
        obs_id = 'N/A'

    return obs_id

def helper_cassini_valid_obs_name(obs_name):
    r"""Check a Cassini observation name to see if it is parsable. Such a
    name will have four parts separated by _:

    <PRIME> _ <REVNO> <TARGETCODE> _ <ACTIVITYNAME> <ACTIVITYNUMBER> _ <INST>

    or, in the case of VIMS (sometimes):

    <PRIME> _ <REVNO> <TARGETCODE> _ <ACTIVITYNAME> <ACTIVITYNUMBER>

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

    If <INST> is missing but everything else is OK, we assume it's PRIME
    """

    if obs_name is None:
        return False

    ret = re.fullmatch(
r'([A-Z]{2,5}|22NAV)_([0-2]\d\d|00[A-C]|C\d\d)[A-Z]{2}_[0-9A-Z]+\d\d\d_[A-Z]{2,7}',
        obs_name)
    if ret:
        return True

    # Try without _INST
    ret = re.fullmatch(
r'([A-Z]{2,5}|22NAV)_([0-2]\d\d|00[A-C]|C\d\d)[A-Z]{2}_[0-9A-Z]+\d\d\d',
        obs_name)
    if ret:
        return True
    return False

_JUPITER_TAI = julian.tai_from_iso('2000-262T00:32:38.930')
_SATURN_TAI = julian.tai_from_iso('2003-138T02:16:18.383')

def helper_cassini_planet_id(**kwargs):
    """Find the planet associated with an observation. This is based on the
    mission phase (as encoded in the observation time so it works with all
    instruments)."""

    metadata = kwargs['metadata']
    obs_general_row = metadata['obs_general_row']

    time_sec2 = obs_general_row['time2']

    if time_sec2 is None or time_sec2 < _JUPITER_TAI:
        return None
    if time_sec2 < _SATURN_TAI:
        return 'JUP'
    return 'SAT'

def helper_cassini_intended_target_name(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']

    target_name = index_row['TARGET_NAME'].upper()
    if target_name in TARGET_NAME_MAPPING:
        target_name = TARGET_NAME_MAPPING[target_name]

    target_desc = None
    if 'TARGET_DESC' in index_row:
        # Only for COISS
        target_desc = index_row['TARGET_DESC'].upper()
        if target_desc in COISS_TARGET_DESC_MAPPING:
            target_desc = COISS_TARGET_DESC_MAPPING[target_desc]
        if target_desc in TARGET_NAME_MAPPING:
            target_desc = TARGET_NAME_MAPPING[target_desc]

    target_code = None
    obs_name = helper_cassini_obs_name(**kwargs)
    if helper_cassini_valid_obs_name(obs_name):
        obs_parts = obs_name.split('_')
        target_code = obs_parts[1][-2:]

    # 1: TARGET_NAME of SATURN or SKY and TARGET_CODE is one of the rings
    if ((target_name == 'SATURN' or target_name == 'SKY') and
        target_code in ('RA','RB','RC','RD','RE','RF','RG','RI')):
        return ('S RINGS', 'Saturn Rings')

    # 2: TARGET_NAME of SATURN or SKY and TARGET_DESC contains "RING"
    # (leave TARGET_CODE of "Star" alone)
    if ((target_name == 'SATURN' or target_name == 'SKY') and
        target_desc is not None and target_desc.find('RING') != -1 and
        target_code != 'ST'):
        return ('S RINGS', 'Saturn Rings')

    # 3: TARGET_NAME of SKY and TARGET_CODE of Skeleton, let TARGET_DESC
    # override TARGET_NAME
    if (target_name == 'SKY' and target_code == 'SK' and
        target_desc is not None and target_desc in TARGET_NAME_INFO):
        target_name_info = TARGET_NAME_INFO[target_desc]
        return target_desc, target_name_info[2]

    if target_name not in TARGET_NAME_INFO:
        import_util.announce_unknown_target_name(target_name)
        if impglobals.ARGUMENTS.import_ignore_errors:
            return 'None'
        return None
    target_name_info = TARGET_NAME_INFO[target_name]
    return target_name, target_name_info[2]

# This is used for COUVIS and COVIMS because they don't include the
# MISSION_PHASE_NAME in the label files. We deduce it from the observation
# time based on what we found in COISS.
def helper_cassini_mission_phase_name(**kwargs):
    metadata = kwargs['metadata']
    obs_general_row = metadata['obs_general_row']
    time1 = obs_general_row['time1']
    for phase, start_time, stop_time in _CASSINI_PHASE_NAME_MAPPING:
        start_time_sec = start_time
        stop_time_sec = stop_time
        if start_time_sec <= time1 < stop_time_sec:
            return phase.upper()
    return None

def helper_fix_cassini_sclk(count):
    if count is None:
        return None

    ### CIRS
    if count.find('.') == -1:
        count += '.000'

    ### UVIS
    # See pds-opus issue #336
    # count = count.replace('.320', '.032')
    # count = count.replace('.640', '.064')
    # count = count.replace('.960', '.096')
    # if count.endswith('.32'):
    #     count = count.replace('.32', '.032')
    # if count.endswith('.64'):
    #     count = count.replace('.64', '.064')
    # if count.endswith('.96'):
    #     count = count.replace('.96', '.096')
    # # See pds-opus issue #443
    # if count.endswith('.324'):
    #     count = count.replace('.324', '.000')

    ### VIMS
    # See pds-opus issue #444
    if count.endswith('.971'):
        count = count.replace('.971', '.000')
    if count.endswith('.973'):
        count = count.replace('.973', '.000')

    return count


################################################################################
# THESE NEED TO BE IMPLEMENTED FOR EVERY MISSION
################################################################################

def populate_obs_general_CO_planet_id_OBS(**kwargs):
    planet_id = helper_cassini_planet_id(**kwargs)
    if planet_id is None:
        return 'OTH'
    return planet_id

def populate_obs_general_CO_planet_id_PROF(**kwargs):
    return 'SAT'

################################################################################
# THESE ARE SPECIFIC TO OBS_MISSION_CASSINI
################################################################################

def populate_obs_mission_cassini_obs_name(**kwargs):
    return helper_cassini_obs_name(**kwargs)

def populate_obs_mission_cassini_prime_inst_id(**kwargs):
    obs_name = helper_cassini_obs_name(**kwargs)
    if obs_name is None:
        return 'UNK'

    if not helper_cassini_valid_obs_name(obs_name):
        return 'UNK'

    obs_parts = obs_name.split('_')
    first = obs_parts[0]
    if len(obs_parts) == 3:
        # This happens for some VIMS observations
        last = 'PRIME'
    else:
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

    if prime_inst_id not in ['CIRS', 'ISS', 'RSS', 'UVIS', 'VIMS']:
        prime_inst_id = 'OTHER'

    return prime_inst_id

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

def populate_obs_mission_cassini_cassini_target_name(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']

    if 'TARGET_NAME' not in index_row: # RSS
        return None

    target_name = index_row['TARGET_NAME'].title()

    return (target_name, target_name)

def populate_obs_mission_cassini_activity_name(**kwargs):
    obs_name = helper_cassini_obs_name(**kwargs)
    if not helper_cassini_valid_obs_name(obs_name):
        return None

    obs_parts = obs_name.split('_')
    return obs_parts[2][:-3]

def populate_obs_mission_cassini_rev_no(**kwargs):
    obs_name = helper_cassini_obs_name(**kwargs)
    if not helper_cassini_valid_obs_name(obs_name):
        return None
    obs_parts = obs_name.split('_')
    rev_no = obs_parts[1][:3]
    if rev_no[0] == 'C':
        return None
    return (rev_no, rev_no)

def populate_obs_mission_cassini_rev_no_cvt(**kwargs):
    metadata = kwargs['metadata']
    cassini_row = metadata['obs_mission_cassini_row']
    rev_no = cassini_row['rev_no']
    if rev_no is None:
        return None
    try:
        rev_no_cvt = opus_support.parse_cassini_orbit(rev_no)
    except Exception as e:
        import_util.log_nonrepeating_warning(
            f'Unable to parse Cassini orbit "{rev_no}": {e}')
        return None
    return rev_no_cvt
