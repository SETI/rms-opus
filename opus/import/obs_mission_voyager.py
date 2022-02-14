################################################################################
# obs_mission_voyager.py
#
# Defines the ObsMissionVoyager class, which encapsulates fields in the
# common and obs_mission_voyager tables.
################################################################################

import opus_support

from obs_common import ObsCommon


class ObsMissionVoyager(ObsCommon):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


    #############################
    ### OVERRIDE FROM ObsBase ###
    #############################

    @property
    def mission_id(self):
        return 'VG'

    @property
    def inst_host_id(self):
        inst_host = self._index_col('INSTRUMENT_HOST_NAME')
        assert inst_host in ['VOYAGER 1', 'VOYAGER 2']
        return 'VG'+inst_host[-1]

    @property
    def primary_filespec(self):
        # Note it's very important that this can be calculated using ONLY
        # the primary index, not the supplemental index!
        # This is because this (and the subsequent creation of opus_id) is used
        # to actually find the matching row in the supplemental index dictionary.
        # Format: "DATA/C13854XX/C1385455_CALIB.LBL"
        filespec = self._index_col('FILE_SPECIFICATION_NAME')
        return self.volume + '/' + filespec


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
        return self._time_from_index(column='EARTH_RECEIVED_TIME')

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
            self._log_nonrepeating_warning(
                    f'spacecraft_clock_count1 ({sc1}) and '+
                    f'spacecraft_clock_count2 ({sc_cvt}) '+
                    'are in the wrong order - setting to count1')
            sc_cvt = sc1

        return sc_cvt
