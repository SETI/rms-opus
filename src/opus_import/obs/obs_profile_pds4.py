"""The PDS4 variant of the ``obs_profile`` table module.

Empty by default for the same reason as `opus_import.obs.obs_profile_pds3`.
"""

from opus_import.obs.field_types import FloatField, MultFieldRet
from opus_import.obs.obs_base_pds4 import ObsBasePDS4
from opus_import.obs.obs_profile import ObsProfile


class ObsProfilePDS4(ObsProfile, ObsBasePDS4):
    """The ``obs_profile`` columns for a PDS4 observation.

    Its ``field_obs_*`` methods each fill the schema column their name ends in,
    declaring the type `opus_import.obs.field_types` gives that column.
    """

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
