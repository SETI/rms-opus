################################################################################
# obs_volume_galileo_common.py
#
# Defines the ObsVolumeGalileoCommon class, which encapsulates fields in the
# common and obs_mission_galileo tables.
################################################################################

import opus_support
from opus_import.obs.field_types import FloatField, MultFieldRet, StrField
from opus_import.obs.obs_common_pds3 import ObsCommonPDS3


class ObsVolumeGalileoCommon(ObsCommonPDS3):
    def _parse_galileo_sclk(self, sclk: str) -> FloatField:
        """Parse a Galileo SCLK, reporting a bad one instead of raising.

        Returns the converted SCLK, or None if it could not be parsed.
        """
        return self._parse_sclk(opus_support.parse_galileo_sclk, sclk, 'Galileo')


    #############################################
    ### FIELD METHODS FOR obs_mission_galileo ###
    #############################################

    def field_obs_mission_galileo_opus_id(self) -> StrField:
        return self.opus_id

    def field_obs_mission_galileo_bundle_id(self) -> StrField:
        return self.bundle

    def field_obs_mission_galileo_orbit_number(self) -> MultFieldRet:
        raise NotImplementedError

    def field_obs_mission_galileo_spacecraft_clock_count1(self) -> FloatField:
        raise NotImplementedError

    def field_obs_mission_galileo_spacecraft_clock_count2(self) -> FloatField:
        raise NotImplementedError
