################################################################################
# obs_volume_corss_occ.py
#
# Defines the ObsVolumeCORSSOcc class, which encapsulates fields for
# common and obs_mission_cassini for CORSS_8001 (there is no RSS instrument
# table).
################################################################################

import opus_support

from config_data import DSN_NAMES
from obs_volume_cassini_occ_helper import ObsVolumeCassiniOccHelper


class ObsVolumeCORSSOcc(ObsVolumeCassiniOccHelper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


    #############################
    ### OVERRIDE FROM ObsBase ###
    #############################

    @property
    def instrument_id(self):
        return 'CORSS'


    ################################
    ### OVERRIDE FROM ObsGeneral ###
    ################################

    def field_obs_general_time1(self):
        return self._time_from_supp_index(column='SPACECRAFT_EVENT_START_TIME')

    def field_obs_general_time2(self):
        return self._time2_from_supp_index(self.field_obs_general_time1(),
                                           column='EARTH_RECEIVED_STOP_TIME')


    ###################################
    ### OVERRIDE FROM ObsWavelength ###
    ###################################

    def field_obs_wavelength_wavelength1(self):
        return self._index_col('WAVELENGTH') * 10000 # cm -> micron

    def field_obs_wavelength_wavelength2(self):
        return self._index_col('WAVELENGTH') * 10000 # cm -> micron


    ################################
    ### OVERRIDE FROM ObsProfile ###
    ################################

    def field_obs_profile_occ_type(self):
        return self._create_mult('RAD')

    def field_obs_profile_quality_score(self):
        return self._create_mult('UNASSIGNED')

    def field_obs_profile_wl_band(self):
        band = self._index_col('BAND_NAME')
        if band == 'K':
            band = 'KA'
        return self._create_mult(band)

    def field_obs_profile_source(self):
        # disp_order '!Cassini' is to force Cassini to be before all stars
        return self._create_mult(col_val='CASSINI', disp_name='Cassini',
                                 disp_order='!Cassini')

    def field_obs_profile_host(self):
        dsn = self._supp_index_col('DSN_STATION_NUMBER')
        ret = f'DSN {dsn} ({DSN_NAMES[dsn]})'
        return self._create_mult_keep_case(col_val=ret, grouping='DSNs')


    #####################################
    ### OVERRIDE FROM ObsRingGeometry ###
    #####################################

    def field_obs_ring_geometry_solar_ring_elevation1(self):
        return -self._index_col('MAXIMUM_OBSERVED_RING_ELEVATION')

    def field_obs_ring_geometry_solar_ring_elevation2(self):
        return -self._index_col('MINIMUM_OBSERVED_RING_ELEVATION')

    def field_obs_ring_geometry_observer_ring_elevation1(self):
        return self._index_col('MINIMUM_OBSERVED_RING_ELEVATION')

    def field_obs_ring_geometry_observer_ring_elevation2(self):
        return self._index_col('MAXIMUM_OBSERVED_RING_ELEVATION')

    def field_obs_ring_geometry_incidence1(self):
        return self._index_col('MINIMUM_LIGHT_SOURCE_INCIDENCE_ANGLE')

    def field_obs_ring_geometry_incidence2(self):
        return self._index_col('MAXIMUM_LIGHT_SOURCE_INCIDENCE_ANGLE')

    def field_obs_ring_geometry_emission1(self):
        return 180. - self._index_col('MAXIMUM_LIGHT_SOURCE_INCIDENCE_ANGLE')

    def field_obs_ring_geometry_emission2(self):
        return 180. - self._index_col('MINIMUM_LIGHT_SOURCE_INCIDENCE_ANGLE')

    def field_obs_ring_geometry_north_based_incidence1(self):
        return 90. + self._index_col('MINIMUM_OBSERVED_RING_ELEVATION')

    def field_obs_ring_geometry_north_based_incidence2(self):
        return 90. + self._index_col('MAXIMUM_OBSERVED_RING_ELEVATION')

    def field_obs_ring_geometry_north_based_emission1(self):
        return 90. - self._index_col('MAXIMUM_OBSERVED_RING_ELEVATION')

    def field_obs_ring_geometry_north_based_emission2(self):
        return 90. - self._index_col('MINIMUM_OBSERVED_RING_ELEVATION')

    def field_obs_ring_geometry_solar_ring_opening_angle1(self):
        return -self._index_col('MAXIMUM_OBSERVED_RING_ELEVATION')

    def field_obs_ring_geometry_solar_ring_opening_angle2(self):
        return -self._index_col('MINIMUM_OBSERVED_RING_ELEVATION')

    def field_obs_ring_geometry_observer_ring_opening_angle1(self):
        return self._index_col('MINIMUM_OBSERVED_RING_ELEVATION')

    def field_obs_ring_geometry_observer_ring_opening_angle2(self):
        return self._index_col('MAXIMUM_OBSERVED_RING_ELEVATION')


    #######################################
    ### OVERRIDE FROM ObsVolumeCassiniHelper ###
    #######################################

    def field_obs_mission_cassini_spacecraft_clock_count1(self):
        count = self._supp_index_col('SPACECRAFT_CLOCK_START_COUNT')
        if count == 'UNK':
            return None
        sc = '1/' + str(count)
        try:
            sc_cvt = opus_support.parse_cassini_sclk(sc)
        except Exception as e:
            self._log_nonrepeating_error(f'Unable to parse Cassini SCLK "{sc}": {e}')
            return None
        return sc_cvt

    def field_obs_mission_cassini_spacecraft_clock_count2(self):
        count = self._supp_index_col('SPACECRAFT_CLOCK_STOP_COUNT')
        if count == 'UNK':
            return None
        sc = '1/' + str(count)
        try:
            sc_cvt = opus_support.parse_cassini_sclk(sc)
        except Exception as e:
            self._log_nonrepeating_error(f'Unable to parse Cassini SCLK "{sc}": {e}')
            return None

        sc1 = self.field_obs_mission_cassini_spacecraft_clock_count1()
        if sc1 is not None and sc_cvt < sc1:
            self._log_warning(
                f'spacecraft_clock_count1 ({sc1}) and spacecraft_clock_count2 '+
                f'({sc_cvt}) are in the wrong order - setting to count1')
            sc_cvt = sc1

        return sc_cvt

    def field_obs_mission_cassini_ert1(self):
        return self._time_from_supp_index(column='EARTH_RECEIVED_START_TIME')

    def field_obs_mission_cassini_ert2(self):
        return self._time2_from_supp_index(self.field_obs_mission_cassini_ert1(),
                                          column='EARTH_RECEIVED_STOP_TIME')

    def field_obs_mission_cassini_mission_phase_name(self):
        mp = self._supp_index_col('MISSION_PHASE_NAME')
        if mp.upper() == 'NULL':
            return self._create_mult(None)
        return self._create_mult(mp.replace('_', ' '))
