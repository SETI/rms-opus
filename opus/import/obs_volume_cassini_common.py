################################################################################
# obs_volume_cassini_common.py
#
# Defines the ObsVolumeCassiniCommon class, which encapsulates fields in the
# common and obs_mission_cassini tables.
################################################################################

import re

import opus_support

import config_targets
from import_util import cached_tai_from_iso
from obs_common_pds3 import ObsCommonPDS3


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
    ('Phoebe Encounter',          cached_tai_from_iso('2004-163T04:30:06.353'), cached_tai_from_iso('2004-163T20:52:47.180')),
    ('Saturn Orbit Insertion',    cached_tai_from_iso('2004-183T03:11:40.288'), cached_tai_from_iso('2004-183T05:15:46.245')),
    ('Titan A Encounter',         cached_tai_from_iso('2004-300T00:30:21.455'), cached_tai_from_iso('2004-300T21:15:32.979')),
    ('Titan B Encounter',         cached_tai_from_iso('2004-348T00:18:13.469'), cached_tai_from_iso('2004-348T22:03:45.065')),
    # Full length encounters that completely cover the mission timeline
    ('Science Cruise',            cached_tai_from_iso('1997-001T00:00:00.000'), cached_tai_from_iso('2000-262T00:32:38.930')), # '2000-209T02:40:23.416'
    ('Earth-Jupiter Cruise',      cached_tai_from_iso('2000-262T00:32:38.930'), cached_tai_from_iso('2001-014T23:02:09.804')), # '2001-013T22:47:48.047'
    ('Jupiter Encounter',         cached_tai_from_iso('2001-014T23:02:09.804'), cached_tai_from_iso('2001-071T12:28:05.413')), # '2001-071T00:58:38.838'
    ('Cruise Science',            cached_tai_from_iso('2001-071T12:28:05.413'), cached_tai_from_iso('2003-138T02:16:18.383')), # '2003-115T07:45:08.222'
    ('Space Science',             cached_tai_from_iso('2003-138T02:16:18.383'), cached_tai_from_iso('2004-037T02:07:06.418')), # '2003-359T10:29:18.711'
    ('Approach Science',          cached_tai_from_iso('2004-037T02:07:06.418'), cached_tai_from_iso('2004-164T02:33:41.000')), # '2004-162T14:47:05.854'
    ('Tour Pre-Huygens',          cached_tai_from_iso('2004-164T02:33:41.000'), cached_tai_from_iso('2004-359T12:53:08.998')), # '2004-358T13:47:22.548'),
    ('Huygens Probe Separation',  cached_tai_from_iso('2004-359T12:53:08.998'), cached_tai_from_iso('2004-360T13:30:10.410')), # '2004-359T13:47:22.981'),
    # The descent actually happened on Jan 14
    ('Huygens Descent',           cached_tai_from_iso('2004-360T13:30:10.410'), cached_tai_from_iso('2005-015T18:28:29.451')), # '2005-001T14:28:54.449'),
    ('Tour',                      cached_tai_from_iso('2005-015T18:28:29.451'), cached_tai_from_iso('2008-183T21:04:08.998')), # '2008-183T09:17:06.323'),
    ('Equinox Mission',           cached_tai_from_iso('2008-183T21:04:08.998'), cached_tai_from_iso('2010-285T05:22:24.745')), # '2010-283T14:14:20.741'),
    ('Solstice Mission',          cached_tai_from_iso('2010-285T05:22:24.745'), cached_tai_from_iso('2020-001T00:00:00.000'))
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


class ObsVolumeCassiniCommon(ObsCommonPDS3):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


    ################################################################################
    # HELPER FUNCTIONS USED BY CASSINI INSTRUMENTS
    ################################################################################

    def _cassini_valid_obs_name(self, obs_name):
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

    # Break points for each planet
    _JUPITER_TAI = cached_tai_from_iso('2000-262T00:32:38.930')
    _SATURN_TAI = cached_tai_from_iso('2003-138T02:16:18.383')

    def _cassini_planet_id(self):
        """Find the planet associated with an observation. This is based on the
        mission phase (as encoded in the observation time so it works with all
        instruments)."""
        time_sec2 = self.field_obs_general_time2()
        if time_sec2 is None or time_sec2 < self._JUPITER_TAI:
            return 'OTH'
        if time_sec2 < self._SATURN_TAI:
            return 'JUP'
        return 'SAT'

    def _cassini_intended_target_name(self):
        target_name = self._index_col('TARGET_NAME').upper()
        # Note this mapping takes care of the "ATLAS:" case from COUVIS_0053
        if target_name in config_targets.TARGET_NAME_MAPPING:
            target_name = config_targets.TARGET_NAME_MAPPING[target_name]

        target_desc = None
        if 'TARGET_DESC' in self._metadata['index_row']:
            # Only for COISS
            target_desc = self._index_col('TARGET_DESC').upper()
            if target_desc in COISS_TARGET_DESC_MAPPING:
                target_desc = COISS_TARGET_DESC_MAPPING[target_desc]
            if target_desc in config_targets.TARGET_NAME_MAPPING:
                target_desc = config_targets.TARGET_NAME_MAPPING[target_desc]

        target_code = None
        obs_name = self._some_index_col('OBSERVATION_ID')
        if self._cassini_valid_obs_name(obs_name):
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
            target_desc is not None and target_desc in config_targets.TARGET_NAME_INFO):
            target_name_info = config_targets.TARGET_NAME_INFO[target_desc]
            return target_desc, target_name_info[2]

        if target_name not in config_targets.TARGET_NAME_INFO:
            self._announce_unknown_target_name(target_name)
            if self._ignore_errors:
                return 'None'
            return None, None
        target_info = config_targets.TARGET_NAME_INFO[target_name]
        return target_name, target_info[2]

    def _cassini_normalize_mission_phase_name(self, phase):
        # These mission phase names are interchangeable, so we standardize on
        # one version
        phase = phase.upper().replace('_', ' ')
        if phase == 'EXTENDED MISSION':
            phase = 'EQUINOX MISSION'
        elif phase == 'EXTENDED-EXTENDED MISSION':
            phase = 'SOLSTICE MISSION'
        return phase

    def _cassini_mission_phase_name_from_time(self):
        # This is used for COUVIS and COVIMS because they don't include the
        # MISSION_PHASE_NAME in the label files. We deduce it from the observation
        # time based on what we found in COISS.
        time1 = self.field_obs_general_time1()
        for phase, start_time, stop_time in _CASSINI_PHASE_NAME_MAPPING:
            start_time_sec = start_time
            stop_time_sec = stop_time
            if start_time_sec <= time1 < stop_time_sec:
                return phase.upper()
        return None

    def _fix_cassini_sclk(self, count):
        if count is None:
            return None

        ### CIRS
        if count.find('.') == -1:
            count += '.000'

        ### VIMS
        # See rms-opus issue #444
        if count.endswith('.971'):
            count = count.replace('.971', '.000')
        if count.endswith('.973'):
            count = count.replace('.973', '.000')

        ### UVIS
        # See rms-opus issue #443
        if count.endswith('.324'):
            count = count.replace('.324', '.000')

        return count


    #############################
    ### OVERRIDE FROM ObsBase ###
    #############################

    @property
    def inst_host_id(self):
        return 'CO'

    @property
    def mission_id(self):
        return 'CO'

    @property
    def primary_filespec(self):
        # Note it's very important that this can be calculated using ONLY
        # the primary index, not the supplemental index!
        # This is because this (and the subsequent creation of opus_id) is used
        # to actually find the matching row in the supplemental index dictionary.
        # Format: "data/1294561143_1295221348/W1294561143_1.IMG"
        filespec = self._index_col('FILE_SPECIFICATION_NAME')
        return self.bundle + '/' + filespec


    #############################################
    ### FIELD METHODS FOR obs_mission_cassini ###
    #############################################

    def field_obs_mission_cassini_opus_id(self):
        return self.opus_id

    def field_obs_mission_cassini_bundle_id(self):
        return self.bundle

    def field_obs_mission_cassini_instrument_id(self):
        return self.instrument_id

    def field_obs_mission_cassini_obs_name(self):
        return self._some_index_col('OBSERVATION_ID')

    def _rev_no(self):
        obs_name = self._some_index_col('OBSERVATION_ID')
        if not self._cassini_valid_obs_name(obs_name):
            return None
        obs_parts = obs_name.split('_')
        rev_no = obs_parts[1][:3]
        if rev_no[0] == 'C':
            return None
        return rev_no

    def field_obs_mission_cassini_rev_no(self):
        return self._create_mult_keep_case(self._rev_no())

    def field_obs_mission_cassini_rev_no_int(self):
        rev_no = self._rev_no()
        if rev_no is None:
            return None
        try:
            rev_no_cvt = opus_support.parse_cassini_orbit(rev_no)
        except Exception as e:
            self._log_nonrepeating_error(
                f'Unable to parse Cassini orbit "{rev_no}": {e}')
            return None
        return rev_no_cvt

    def field_obs_mission_cassini_is_prime(self):
        prime_inst = self._prime_inst_id()
        inst_id = self.instrument_id

        # Change COISS to ISS, etc.
        inst_id = inst_id.replace('CO', '')
        if prime_inst == inst_id:
            return self._create_mult('Yes')
        return self._create_mult('No')

    def _prime_inst_id(self):
        obs_name = self._some_index_col('OBSERVATION_ID')
        if obs_name is None:
            return 'UNK'

        if not self._cassini_valid_obs_name(obs_name):
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
        # PIE is equivalent to PRIME. These were “pre-integrated elements” that
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

        if prime_inst_id not in ('CIRS', 'ISS', 'RSS', 'UVIS', 'VIMS'):
            prime_inst_id = 'OTHER'

        return prime_inst_id

    def field_obs_mission_cassini_prime_inst_id(self):
        return self._create_mult(self._prime_inst_id())

    def field_obs_mission_cassini_spacecraft_clock_count1(self):
        return None

    def field_obs_mission_cassini_spacecraft_clock_count2(self):
        return None

    def field_obs_mission_cassini_ert1(self):
        return None

    def field_obs_mission_cassini_ert2(self):
        return None

    def field_obs_mission_cassini_cassini_target_code(self):
        obs_name = self._some_index_col('OBSERVATION_ID')
        if obs_name is None:
            return self._create_mult(None)
        if not self._cassini_valid_obs_name(obs_name):
            return self._create_mult(None)
        obs_parts = obs_name.split('_')
        target_code = obs_parts[1][-2:]
        if target_code in _CASSINI_TARGET_CODE_MAPPING:
            return self._create_mult(col_val=target_code,
                                     disp_name=_CASSINI_TARGET_CODE_MAPPING[target_code])

        return self._create_mult(None)

    def field_obs_mission_cassini_cassini_target_name(self):
        if 'TARGET_NAME' not in self._metadata['index_row']: # RSS
            return self._create_mult(None)
        target_name = self._index_col('TARGET_NAME').title()
        target_name = target_name.replace(':', '') # Bug in COUVIS_0053 index
        if target_name == 'N/A':
            return self._create_mult(None)
        return self._create_mult_keep_case(target_name)

    def field_obs_mission_cassini_activity_name(self):
        obs_name = self._some_index_col('OBSERVATION_ID')
        if not self._cassini_valid_obs_name(obs_name):
            return None
        obs_parts = obs_name.split('_')
        return obs_parts[2][:-3]

    def field_obs_mission_cassini_mission_phase_name(self):
        raise NotImplementedError

    def field_obs_mission_cassini_sequence_id(self):
        return None
