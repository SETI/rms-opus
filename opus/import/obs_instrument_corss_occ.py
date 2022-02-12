################################################################################
# obs_instrument_corss_occ.py
#
# Defines the ObsInstrumentCORSSOcc class, which encapsulates fields for
# CORSS_8001.
################################################################################

from config_targets import DSN_NAMES

from import_util import cached_tai_from_iso
from obs_instrument_cassini_occ import ObsInstrumentCassiniOcc


class ObsInstrumentCORSSOcc(ObsInstrumentCassiniOcc):
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
        return 'RAD'

    def field_obs_profile_quality_score(self):
        return ("UNASSIGNED", "Unassigned")

    def field_obs_profile_wl_band(self):
        band = self._index_col('BAND_NAME')
        if band == 'K':
            band = 'KA'
        return band

    def field_obs_profile_source(self):
        return ('CASSINI', 'Cassini', '!Cassini') # XXX

    def field_obs_profile_host(self):
        dsn = self._supp_index_col('DSN_STATION_NUMBER')
        ret = f'DSN {dsn} ({DSN_NAMES[dsn]})'
        return (ret, ret)


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
    ### OVERRIDE FROM ObsMissionCassini ###
    #######################################

    def field_obs_mission_cassini_spacecraft_clock_count1(self):
        count = self._supp_index_col('SPACECRAFT_CLOCK_START_COUNT')
        if count == 'UNK':
            return None
        sc = '1/' + str(count)
        try:
            sc_cvt = opus_support.parse_cassini_sclk(sc)
        except Exception as e:
            self._log_nonrepeating_warning(f'Unable to parse Cassini SCLK "{sc}": {e}')
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
            self._log_nonrepeating_warning(f'Unable to parse Cassini SCLK "{sc}": {e}')
            return None

        sc1 = self.field_obs_mission_cassini_spacecraft_clock_count1()
        if sc1 is not None and sc_cvt < sc1:
            import_util.log_warning(
                f'spacecraft_clock_count1 ({sc1}) and spacecraft_clock_count2 ({sc_cvt}) '
                 +'are in the wrong order - setting to count1')
            sc_cvt = sc1

        return sc_cvt

    def field_obs_mission_cassini_mission_phase_name(self):
        mp = self._supp_index_col('MISSION_PHASE_NAME')
        if mp.upper() == 'NULL':
            return None
        return mp.replace('_', ' ')

    def field_obs_mission_cassini_ert1(self):
        return self._time_from_supp_index(column='EARTH_RECEIVED_START_TIME')

    def field_obs_mission_cassini_ert2(self):
        return self._time2_from_supp_index(self.field_obs_mission_cassini_ert1(),
                                          column='EARTH_RECEIVED_STOP_TIME')

    def field_obs_mission_cassini_mission_phase_name(self):
        mp = self._supp_index_col('MISSION_PHASE_NAME')
        if mp.upper() == 'NULL':
            return None
        return mp.replace('_', ' ')
