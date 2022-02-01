################################################################################
# obs_profile.py
#
# Defines the ObsProfile class, which encapsulates fields in the
# obs_profile table.
################################################################################

from obs_base import ObsBase


class ObsProfile(ObsBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


    ####################################
    ### FIELD METHODS FOR THIS TABLE ###
    ####################################

    ### Don't override these ###

    def field_obs_profile_opus_id(self):
        return self.opus_id

    def field_obs_profile_volume_id(self):
        return self.volume

    def field_obs_profile_instrument_id(self):
        return self.instrument_id


    ################################
    ### ! Might override these ! ###
    ################################

    # Because the obs_profile table has an entry for all observations,
    # we provide a default for all fields and don't require subclasses to
    # override the methods.

    def field_obs_profile_occ_type(self):
        return None

    def field_obs_profile_occ_dir(self):
        return None

    def field_obs_profile_body_occ_flag(self):
        return None

    def field_obs_profile_temporal_sampling(self):
        return None

    def field_obs_profile_quality_score(self):
        return None

    def field_obs_profile_optical_depth1(self):
        return None

    def field_obs_profile_optical_depth2(self):
        return None

    def field_obs_profile_wl_band(self):
        return None

    def field_obs_profile_source(self):
        return None

    def field_obs_profile_host(self):
        return None
