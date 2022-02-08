################################################################################
# obs_instrument_cassini_occ.py
#
# Defines the ObsInstrumentCassiniOcc class, the parent for the
# ObsInstrumentCORSSOcc, ObsInstrumentCOUVISOcc, and ObsInstrumentCOVIMSOcc
# classes, which encapsulate fields in the obs_instrument_corss,
# obs_instrument_couvis, and obs_instrument_covims tables for the 8xxx
# occultation volumes
################################################################################

from obs_mission_cassini import ObsMissionCassini


class ObsInstrumentCassiniOcc(ObsMissionCassini):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


    def _convert_filespec_from_lbl(self, filespec):
        return filespec.replace('.LBL', '.TAB')


    ################################
    ### OVERRIDE FROM ObsGeneral ###
    ################################

    def field_obs_general_target_name(self):
        target_name, target_info = self._get_target_info('S RINGS')
        return target_name, target_info[2]

    def field_obs_general_planet_id(self):
        return 'SAT'

    def field_obs_general_quantity(self):
        return 'OPDEPTH'

    def field_obs_general_observation_type(self):
        return 'OCC'


    ################################
    ### OVERRIDE FROM ObsProfile ###
    ################################

    def field_obs_profile_occ_dir(self):
        filespec = self.primary_filespec

        # We don't allow "Both" as a direction since these are always split into
        # separate files.
        if '_I_' in filespec:
            return 'I'
        if '_E_' in filespec:
            return 'E'
        self._log_nonrepeating_error(
            f'Unknown ring occultation direction in filespec "{filespec}"')
        return None

    def field_obs_profile_body_occ_flag(self):
        return self._index_col('PLANETARY_OCCULTATION_FLAG')

    def field_obs_profile_optical_depth1(self):
        return self._supp_index_col('LOWEST_DETECTABLE_OPACITY')

    def field_obs_profile_optical_depth2(self):
        return self._supp_index_col('HIGHEST_DETECTABLE_OPACITY')


    #####################################
    ### OVERRIDE FROM ObsRingGeometry ###
    #####################################

    def field_obs_ring_geometry_ring_radius1(self):
        return self._index_col('MINIMUM_RING_RADIUS')

    def field_obs_ring_geometry_ring_radius2(self):
        return self._index_col('MAXIMUM_RING_RADIUS')

    def field_obs_ring_geometry_resolution1(self):
        return self._index_col('RADIAL_RESOLUTION')

    def field_obs_ring_geometry_resolution2(self):
        return self._index_col('RADIAL_RESOLUTION')

    def field_obs_ring_geometry_projected_radial_resolution1(self):
        return self._index_col('RADIAL_RESOLUTION')

    def field_obs_ring_geometry_projected_radial_resolution2(self):
        return self._index_col('RADIAL_RESOLUTION')

    def field_obs_ring_geometry_j2000_longitude1(self):
        return self._index_col('MINIMUM_RING_LONGITUDE')

    def field_obs_ring_geometry_j2000_longitude2(self):
        return self._index_col('MAXIMUM_RING_LONGITUDE')

    def field_obs_ring_geometry_ring_azimuth_wrt_observer1(self):
        return self._index_col('MINIMUM_OBSERVED_RING_AZIMUTH')

    def field_obs_ring_geometry_ring_azimuth_wrt_observer2(self):
        return self._index_col('MAXIMUM_OBSERVED_RING_AZIMUTH')

    def field_obs_ring_geometry_phase1(self):
        return 180.

    def field_obs_ring_geometry_phase2(self):
        return 180.

    def field_obs_ring_geometry_ring_center_phase1(self):
        return self.field_obs_ring_geometry_phase1()

    def field_obs_ring_geometry_ring_center_phase2(self):
        return self.field_obs_ring_geometry_phase2()

    def field_obs_ring_geometry_ring_center_incidence1(self):
        return self.field_obs_ring_geometry_incidence1()

    def field_obs_ring_geometry_ring_center_incidence2(self):
        return self.field_obs_ring_geometry_incidence2()

    def field_obs_ring_geometry_ring_center_emission1(self):
        return self.field_obs_ring_geometry_emission1()

    def field_obs_ring_geometry_ring_center_emission2(self):
        return self.field_obs_ring_geometry_emission2()

    def field_obs_ring_geometry_ring_center_north_based_incidence1(self):
        return self.field_obs_ring_geometry_north_based_incidence1()

    def field_obs_ring_geometry_ring_center_north_based_incidence2(self):
        return self.field_obs_ring_geometry_north_based_incidence2()

    def field_obs_ring_geometry_ring_center_north_based_emission1(self):
        return self.field_obs_ring_geometry_north_based_emission1()

    def field_obs_ring_geometry_ring_center_north_based_emission2(self):
        return self.field_obs_ring_geometry_north_based_emission2()

    def field_obs_ring_geometry_ring_intercept_time1(self):
        return self._time1_from_index(column='RING_EVENT_START_TIME')

    def field_obs_ring_geometry_ring_intercept_time2(self):
        return self._time2_from_index(self.field_obs_ring_geometry_ring_intercept_time1(),
                                      column='RING_EVENT_STOP_TIME')
