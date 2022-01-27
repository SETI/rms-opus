################################################################################
# obs_mission_galileo.py
#
# Defines the ObsMissionGalileo class, which encapsulates fields in the
# obs_mission_galileo table.
################################################################################

import opus_support

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
        sc = self._index_col('SPACECRAFT_CLOCK_START_COUNT')
        try:
            sc_cvt = opus_support.parse_galileo_sclk(sc)
        except Exception as e:
            self._log_nonrepeating_error(
                f'Unable to parse Galileo SCLK "{sc}": {e}')
            return None
        return sc_cvt

    @property
    def field_obs_mission_galileo_spacecraft_clock_count2(self):
        # There is no SPACECRAFT_CLOCK_STOP_COUNT for Galileo
        return self.field_obs_mission_galileo_spacecraft_clock_count1
