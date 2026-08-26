"""The PDS3 variant of the ``obs_profile`` table module.

Everything here is empty by default: only an occultation volume fills these columns, and
each one supplies its own values.
"""

from opus_import.obs.field_types import FloatField, MultFieldRet
from opus_import.obs.obs_base_pds3 import ObsBasePDS3
from opus_import.obs.obs_profile import ObsProfile


class ObsProfilePDS3(ObsProfile, ObsBasePDS3):
    ####################################
    ### FIELD METHODS FOR THIS TABLE ###
    ####################################

    ################################
    ### ! Might override these ! ###
    ################################

    # Because the obs_profile table has an entry for all observations,
    # we provide a default for all fields and don't require subclasses to
    # override the methods.

    """The ``obs_profile`` columns for a PDS3 observation.

    Its ``field_obs_*`` methods each fill the schema column their name ends in,
    declaring the type `opus_import.obs.field_types` gives that column.
    """

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
