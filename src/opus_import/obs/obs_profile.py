################################################################################
# obs_profile.py
#
# Defines the ObsProfile class, which encapsulates fields in the
# obs_profile table.
################################################################################

from opus_import import config_targets
from opus_import.obs.field_types import FloatField, MultFieldRet, StrField
from opus_import.obs.obs_base import ObsBase, TargetInfo


class ObsProfile(ObsBase):

    ### Utility functions useful for subclasses ###

    def _star_name_helper(self, index: str,
                          col: str) -> tuple[str | None, TargetInfo | None]:
        assert self._metadata is not None
        target_name = self._metadata[index][col]
        target_name = target_name.replace(' ', '').upper()
        return self._get_target_info(target_name)

    _STAR_RA_DEC_SLOP = 0. # Decided at meeting 2020/05/14 to have stars as fixed pts

    def _prof_ra_dec_helper(
            self, index: str,
            col: str) -> tuple[FloatField, FloatField, FloatField, FloatField]:
        target_name, _target_info = self._star_name_helper(index, col)
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

    def field_obs_profile_opus_id(self) -> StrField:
        return self.opus_id

    def field_obs_profile_bundle_id(self) -> StrField:
        return self.bundle

    def field_obs_profile_instrument_id(self) -> StrField:
        return self.instrument_id


    ################################
    ### ! Might override these ! ###
    ################################

    def field_obs_profile_occ_type(self) -> MultFieldRet:
        raise NotImplementedError

    def field_obs_profile_occ_dir(self) -> MultFieldRet:
        raise NotImplementedError

    def field_obs_profile_body_occ_flag(self) -> MultFieldRet:
        raise NotImplementedError

    def field_obs_profile_temporal_sampling(self) -> FloatField:
        raise NotImplementedError

    def field_obs_profile_quality_score(self) -> MultFieldRet:
        raise NotImplementedError

    def field_obs_profile_optical_depth1(self) -> FloatField:
        raise NotImplementedError

    def field_obs_profile_optical_depth2(self) -> FloatField:
        raise NotImplementedError

    def field_obs_profile_wl_band(self) -> MultFieldRet:
        raise NotImplementedError

    def field_obs_profile_source(self) -> MultFieldRet:
        raise NotImplementedError

    def field_obs_profile_host(self) -> MultFieldRet:
        raise NotImplementedError
