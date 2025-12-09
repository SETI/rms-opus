################################################################################
# obs_cassini_common_pds3.py
#
# Defines the ObsCassiniCommonPDS3 class, which augments ObsCassiniCommon, and
# overrides target names and SCLK counts.
################################################################################

from obs_common_pds3 import ObsCommonPDS3
from obs_cassini_common import ObsCassiniCommon


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

class ObsCassiniCommonPDS3(ObsCommonPDS3, ObsCassiniCommon):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


    ################################################################################
    # HELPER FUNCTIONS USED BY CASSINI INSTRUMENTS
    ################################################################################
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
                return 'None', None
            return None, None
        target_info = config_targets.TARGET_NAME_INFO[target_name]
        return target_name, target_info[2]

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
