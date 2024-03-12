################################################################################
# obs_profile.py
#
# Defines the ObsProfile class, which encapsulates fields in the
# obs_profile table.
################################################################################

import config_targets


class ObsProfile:

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
        if target_name not in config_targets.STAR_RA_DEC:
            self._log_nonrepeating_error(
                f'Star "{target_name}" missing RA and DEC information'
            )
            return None, None, None, None

        return (config_targets.STAR_RA_DEC[target_name][0]-self._STAR_RA_DEC_SLOP,
                config_targets.STAR_RA_DEC[target_name][0]+self._STAR_RA_DEC_SLOP,
                config_targets.STAR_RA_DEC[target_name][1]-self._STAR_RA_DEC_SLOP,
                config_targets.STAR_RA_DEC[target_name][1]+self._STAR_RA_DEC_SLOP)


    ####################################
    ### FIELD METHODS FOR THIS TABLE ###
    ####################################

    ### Don't override these ###

    def field_obs_profile_opus_id(self):
        return self.opus_id

    def field_obs_profile_bundle_id(self):
        return self.bundle

    def field_obs_profile_instrument_id(self):
        return self.instrument_id


    ################################
    ### ! Might override these ! ###
    ################################

    def field_obs_profile_occ_type(self):
        raise NotImplementedError

    def field_obs_profile_occ_dir(self):
        raise NotImplementedError

    def field_obs_profile_body_occ_flag(self):
        raise NotImplementedError

    def field_obs_profile_temporal_sampling(self):
        raise NotImplementedError

    def field_obs_profile_quality_score(self):
        raise NotImplementedError

    def field_obs_profile_optical_depth1(self):
        raise NotImplementedError

    def field_obs_profile_optical_depth2(self):
        raise NotImplementedError

    def field_obs_profile_wl_band(self):
        raise NotImplementedError

    def field_obs_profile_source(self):
        raise NotImplementedError

    def field_obs_profile_host(self):
        raise NotImplementedError
