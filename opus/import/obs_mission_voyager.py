################################################################################
# obs_mission_voyager.py
#
# Defines the ObsMissionVoyager class, which encapsulates fields in the
# obs_mission_voyager table.
################################################################################

import julian

import opus_support

from obs_common import ObsCommon



# Note: threshold values are obtained and determined by observing the results
# from OPUS. Voyager location:
# North
# 1980-11-12T05:15:45.520
# South
# 1980-11-13T04:19:30.640
# North
# 1981-08-26T04:18:21.080
# South
# 1985-11-06T17:22:30.040
# North
# 1986-01-24T17:10:13.320
# South
# THRESHOLD_START_TIME_VG_AT_NORTH = [
#     '1980-11-12T05:15:45.520',
#     '1980-11-13T04:19:30.640',
#     '1981-08-26T04:16:45.080',
#     '1985-11-06T17:22:30.040',
#     '1986-01-24T17:10:13.320'
# ]

_VG_TARGET_TO_MISSION_PHASE_MAPPING = {
    'S RINGS': 'SATURN ENCOUNTER',
    'U RINGS': 'URANUS ENCOUNTER',
    'N RINGS': 'NEPTUNE ENCOUNTER'
}


class ObsMissionVoyager(ObsCommon):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


    #############################
    ### OVERRIDE FROM ObsBase ###
    #############################

    @property
    def mission_id(self):
        return 'VG'


    ################################
    ### OVERRIDE FROM ObsGeneral ###
    ################################

    def field_obs_general_planet_id(self):
        mp = self.field_obs_mission_voyager_mission_phase_name()
        pl = mp[:3].upper()

        assert pl in ['JUP', 'SAT', 'URA', 'NEP']

        return pl


    ####################################
    ### FIELD METHODS FOR THIS TABLE ###
    ####################################

    def field_obs_mission_voyager_opus_id(self):
        return self.opus_id

    def field_obs_mission_voyager_volume_id(self):
        return self.volume

    def field_obs_mission_voyager_instrument_id(self):
        return self.instrument_id

    def field_obs_mission_voyager_ert(self):
        if not self._col_in_index('EARTH_RECEIVED_TIME'):
            return None
        ert_time = self._index_col('EARTH_RECEIVED_TIME')
        if ert_time == 'UNKNOWN':
            return None
        try:
            ert_sec = julian.tai_from_iso(ert_time)
        except Exception as e:
            self._log_nonrepeating_error(
                f'Bad earth received time format "{ert_time}": {e}')
            return None
        return ert_sec

    def field_obs_mission_voyager_spacecraft_clock_count1(self):
        sc = self._some_index_or_label_col('SPACECRAFT_CLOCK_START_COUNT')
        if self._col_in_some_index_or_label('SPACECRAFT_CLOCK_PARTITION_NUMBER'):
            partition = self._some_index_or_label_col('SPACECRAFT_CLOCK_PARTITION_NUMBER')
            sc = str(partition) + '/' + sc

        try:
            sc_cvt = opus_support.parse_voyager_sclk(sc)
        except Exception as e:
            self._log_nonrepeating_error(f'Unable to parse Voyager SCLK "{sc}": {e}')
            return None
        return sc_cvt

    def field_obs_mission_voyager_spacecraft_clock_count2(self):
        sc = self._some_index_or_label_col('SPACECRAFT_CLOCK_STOP_COUNT')
        if self._col_in_some_index_or_label('SPACECRAFT_CLOCK_PARTITION_NUMBER'):
            partition = self._some_index_or_label_col('SPACECRAFT_CLOCK_PARTITION_NUMBER')
            sc = str(partition) + '/' + sc
        try:
            sc_cvt = opus_support.parse_voyager_sclk(sc)
        except Exception as e:
            self._log_nonrepeating_error(f'Unable to parse Voyager SCLK "{sc}": {e}')
            return None

        sc1 = self.field_obs_mission_voyager_spacecraft_clock_count1()
        if sc1 is not None and sc_cvt < sc1:
            self._log_warning(
                    f'spacecraft_clock_count1 ({sc1}) and '+
                    f'spacecraft_clock_count2 ({sc_cvt}) '+
                     'are in the wrong order - setting to count1')
            sc_cvt = sc1

        return sc_cvt
