################################################################################
# obs_profile_pds4.py
#
# Defines the ObsProfilePDS4 class, which augments ObsProfile with methods that
# are PDS4-specific.
################################################################################

from obs_base_pds4 import ObsBasePDS4
from obs_profile import ObsProfile

class ObsProfilePDS4(ObsProfile, ObsBasePDS4):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


    ####################################
    ### FIELD METHODS FOR THIS TABLE ###
    ####################################

    ################################
    ### ! Might override these ! ###
    ################################

    def field_obs_profile_occ_type(self):
        return self._create_mult(None)

    def field_obs_profile_occ_dir(self):
        return self._create_mult(None)

    def field_obs_profile_body_occ_flag(self):
        return self._create_mult(None)

    def field_obs_profile_temporal_sampling(self):
        return None

    def field_obs_profile_quality_score(self):
        return self._create_mult(None)

    def field_obs_profile_optical_depth1(self):
        return None

    def field_obs_profile_optical_depth2(self):
        return None

    def field_obs_profile_wl_band(self):
        return self._create_mult(None)

    def field_obs_profile_source(self):
        return self._create_mult(None)

    def field_obs_profile_host(self):
        return self._create_mult(None)
