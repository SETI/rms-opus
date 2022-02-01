################################################################################
# obs_mission_galileo.py
#
# Defines the ObsMissionGalileo class, which encapsulates fields in the
# obs_mission_galileo table.
################################################################################

from obs_common import ObsCommon


class ObsMissionGalileo(ObsCommon):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


    ####################################
    ### FIELD METHODS FOR THIS TABLE ###
    ####################################

    def field_obs_mission_galileo_opus_id(self):
        return self.opus_id

    def field_obs_mission_galileo_volume_id(self):
        return self.volume

    def field_obs_mission_galileo_instrument_id(self):
        return self.instrument_id

    def field_obs_mission_galileo_orbit_number(self):
        raise NotImplementedError

    def field_obs_mission_galileo_spacecraft_clock_count1(self):
        raise NotImplementedError

    def field_obs_mission_galileo_spacecraft_clock_count2(self):
        raise NotImplementedError
