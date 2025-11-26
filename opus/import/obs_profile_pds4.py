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
        occ_type = self._index_col('rings:occultation_type')
        if occ_type == 'stellar':
            return self._create_mult('STE')
        self._log_nonrepeating_error(
            f'Unknown rings:occultation:type "{occ_type}"')

    def field_obs_profile_occ_dir(self):
        occ_dir = self._index_col('rings:ring_profile_direction')
        if occ_dir is None:
            occ_dir = self._index_col('rings:time_series_direction')
        if occ_dir is None:
            self._log_nonrepeating_error(
                'rings:ring_profile_direction and rings:time_series_direction" '
                'missing')
            return None
        occ_dir = occ_dir.upper()
        if occ_dir in ('INGRESS', 'EGRESS', 'BOTH'):
            return self._create_mult(occ_dir[0])
        self._log_nonrepeating_error(f'Unknown profile direction "{occ_dir}"')
        return self._create_mult(None)

    def field_obs_profile_body_occ_flag(self):
        return self._create_mult(self._index_col('rings:planetary_occultation_flag'))

    def field_obs_profile_quality_score(self):
        return self._create_mult(self._index_col('rings:data_quality_score'))

    def field_obs_profile_temporal_sampling(self):
        return None

    # Assume BeckerJarmak optical depth parameter can be interpreted the same as the Uranus Occs opacity parameter.
    # Can fix later.
    def field_obs_profile_optical_depth1(self):
        ret = self._index_col('rings:lowest_detectable_opacity') # Uranus Occs
        if ret is None:
            ret = self._index_col('rings:lowest_detectable_normal_optical_depth') # BeckerJarmak. Note co-uvis-occ-2016-269-sun-i has -999.
        return ret

    def field_obs_profile_optical_depth2(self):
        ret = self._index_col('rings:highest_detectable_opacity') # Uranus Occs
        if ret is None:
            ret = self._index_col('rings:highest_detectable_normal_optical_depth') # BeckerJarmak. Note co-uvis-occ-2016-269-sun-i has -999.
        return ret

    def field_obs_profile_wl_band(self):
        wl_range = self._index_col('pds:wavelength_range')
        if wl_range.upper() == 'INFRARED':
            return self._create_mult('IR')
        if wl_range.upper() == 'VISIBLE':
            return self._create_mult('VI')
        self._log_nonrepeating_error(f'Unknown pds:wavelength_range "{wl_range}"')
        return None
