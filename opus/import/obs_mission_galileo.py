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

    @property
    def field_obs_mission_galileo_opus_id(self):
        return self.opus_id

    @property
    def field_obs_mission_galileo_volume_id(self):
        return self.volume

    @property
    def field_obs_mission_galileo_instrument_id(self):
        return self.instrument_id

    @property
    def field_obs_mission_galileo_orbit_number(self):
        raise NotImplementedError

    @property
    def field_obs_mission_galileo_spacecraft_clock_count1(self):
        raise NotImplementedError

    @property
    def field_obs_mission_galileo_spacecraft_clock_count2(self):
        raise NotImplementedError
