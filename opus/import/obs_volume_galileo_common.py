################################################################################
# obs_volume_galileo_common.py
#
# Defines the ObsVolumeGalileoCommon class, which encapsulates fields in the
# common and obs_mission_galileo tables.
################################################################################

from obs_common_pds3 import ObsCommonPDS3


class ObsVolumeGalileoCommon(ObsCommonPDS3):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


    #############################################
    ### FIELD METHODS FOR obs_mission_galileo ###
    #############################################

    def field_obs_mission_galileo_opus_id(self):
        return self.opus_id

    def field_obs_mission_galileo_bundle_id(self):
        return self.bundle

    def field_obs_mission_galileo_instrument_id(self):
        return self.instrument_id

    def field_obs_mission_galileo_orbit_number(self):
        raise NotImplementedError

    def field_obs_mission_galileo_spacecraft_clock_count1(self):
        raise NotImplementedError

    def field_obs_mission_galileo_spacecraft_clock_count2(self):
        raise NotImplementedError
