################################################################################
# obs_profile_pds4.py
#
# Defines the ObsProfilePDS4 class, which augments ObsProfile with methods that
# are PDS4-specific.
################################################################################

from opus_import.obs.field_types import FloatField, MultFieldRet
from opus_import.obs.obs_base_pds4 import ObsBasePDS4
from opus_import.obs.obs_profile import ObsProfile


class ObsProfilePDS4(ObsProfile, ObsBasePDS4):
    ####################################
    ### FIELD METHODS FOR THIS TABLE ###
    ####################################

    ################################
    ### ! Might override these ! ###
    ################################

    def field_obs_profile_occ_type(self) -> MultFieldRet:
        return self._create_mult(None)

    def field_obs_profile_occ_dir(self) -> MultFieldRet:
        return self._create_mult(None)

    def field_obs_profile_body_occ_flag(self) -> MultFieldRet:
        return self._create_mult(None)

    def field_obs_profile_temporal_sampling(self) -> FloatField:
        return None

    def field_obs_profile_quality_score(self) -> MultFieldRet:
        return self._create_mult(None)

    def field_obs_profile_optical_depth1(self) -> FloatField:
        return None

    def field_obs_profile_optical_depth2(self) -> FloatField:
        return None

    def field_obs_profile_wl_band(self) -> MultFieldRet:
        return self._create_mult(None)

    def field_obs_profile_source(self) -> MultFieldRet:
        return self._create_mult(None)

    def field_obs_profile_host(self) -> MultFieldRet:
        return self._create_mult(None)
