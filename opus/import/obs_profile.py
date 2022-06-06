################################################################################
# obs_profile.py
#
# Defines the ObsProfile class, which encapsulates fields in the
# obs_profile table.
################################################################################

from config_targets import STAR_RA_DEC
from obs_base import ObsBase


class ObsProfile(ObsBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


    ### Utility functions useful for subclasses ###

    def _star_name_helper(self, index, col):
        target_name = self._metadata[index][col]
        target_name = target_name.replace(' ', '').upper()
        return self._get_target_info(target_name)

    _STAR_RA_DEC_SLOP = 0. # Decided at meeting 2020/05/14 to have stars as fixed pts

    def _prof_ra_dec_helper(self, index, col):
        target_name, target_info = self._star_name_helper(index, col)
        if target_name is None:
            return None, None, None, None
        if target_name not in STAR_RA_DEC:
            self._log_nonrepeating_error(
                f'Star "{target_name}" missing RA and DEC information'
            )
            return None, None, None, None

        return (STAR_RA_DEC[target_name][0]-self._STAR_RA_DEC_SLOP,
                STAR_RA_DEC[target_name][0]+self._STAR_RA_DEC_SLOP,
                STAR_RA_DEC[target_name][1]-self._STAR_RA_DEC_SLOP,
                STAR_RA_DEC[target_name][1]+self._STAR_RA_DEC_SLOP)


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
