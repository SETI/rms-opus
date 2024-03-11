################################################################################
# obs_profile_pds3.py
#
# Defines the ObsProfilePDS3 class, which augments ObsProfile with methods that
# are PDS3-specific.
################################################################################

from obs_base_pds3 import ObsBasePDS3
from obs_profile import ObsProfile


class ObsProfilePDS3(ObsProfile, ObsBasePDS3):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    ####################################
    ### FIELD METHODS FOR THIS TABLE ###
    ####################################

    ################################
    ### ! Might override these ! ###
    ################################

    # Because the obs_profile table has an entry for all observations,
    # we provide a default for all fields and don't require subclasses to
    # override the methods.

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
