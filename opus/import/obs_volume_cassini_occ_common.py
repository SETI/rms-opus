################################################################################
# obs_volume_cassini_occ_common.py
#
# Defines the ObsVolumeCassiniOccCommon class, the parent for the
# ObsVolumeCORSS8xxx, ObsVolumeCOUVIS8xxx, and ObsVolumeCOVIMS8xxx
# classes, which encapsulate fields in the obs_instrument_corss,
# obs_instrument_couvis, and obs_instrument_covims tables for the 8xxx
# occultation volumes
################################################################################

from obs_volume_cassini_common import ObsVolumeCassiniCommon


class ObsVolumeCassiniOccCommon(ObsVolumeCassiniCommon):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


    def convert_filespec_from_lbl(self, filespec):
        return filespec.replace('.LBL', '.TAB')


    ################################
    ### OVERRIDE FROM ObsGeneral ###
    ################################

    def _target_name(self):
        target_name, target_info = self._get_target_info('S RINGS')
        return [(target_name, target_info[2])]
        # MULTXXX2 - Comment out the above line to fake a multi-target results
        target_name2, target_info2 = self._get_target_info('ENCELADUS')
        target_name3, target_info3 = self._get_target_info('TETHYS')
        return [(target_name, target_info[2]),
                (target_name2, target_info2[2]),
                (target_name3, target_info3[2])]

    def field_obs_general_planet_id(self):
        return self._create_mult('SAT')

    def field_obs_general_quantity(self):
        return self._create_mult('OPDEPTH')

    def field_obs_general_observation_type(self):
        return self._create_mult('OCC')


    ################################
    ### OVERRIDE FROM ObsProfile ###
    ################################

    def field_obs_profile_occ_dir(self):
        filespec = self.primary_filespec

        # We don't allow "Both" as a direction since these are always split into
        # separate files.
        if '_I_' in filespec:
            return self._create_mult('I')
        if '_E_' in filespec:
            return self._create_mult('E')
        self._log_nonrepeating_error(
            f'Unknown ring occultation direction in filespec "{filespec}"')
        return self._create_mult(None)

    def field_obs_profile_body_occ_flag(self):
        return self._create_mult(self._index_col('PLANETARY_OCCULTATION_FLAG'))

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

    def field_obs_ring_geometry_projected_radial_resolution1(self):
        return self._index_col('RADIAL_RESOLUTION')

    def field_obs_ring_geometry_projected_radial_resolution2(self):
        return self._index_col('RADIAL_RESOLUTION')

    def field_obs_ring_geometry_j2000_longitude1(self):
        if (self.field_obs_ring_geometry_ascending_longitude1() == 0 and
            self.field_obs_ring_geometry_ascending_longitude2() == 360):
            return 0
        return self._ascending_to_j2000(
            self.field_obs_ring_geometry_ascending_longitude1())

    def field_obs_ring_geometry_j2000_longitude2(self):
        if (self.field_obs_ring_geometry_ascending_longitude1() == 0 and
            self.field_obs_ring_geometry_ascending_longitude2() == 360):
            return 360
        return self._ascending_to_j2000(
            self.field_obs_ring_geometry_ascending_longitude2())

    def field_obs_ring_geometry_ascending_longitude1(self):
        return self._index_col('MINIMUM_RING_LONGITUDE')

    def field_obs_ring_geometry_ascending_longitude2(self):
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
        return self._time_from_index(column='RING_EVENT_START_TIME')

    def field_obs_ring_geometry_ring_intercept_time2(self):
        return self._time2_from_index(self.field_obs_ring_geometry_ring_intercept_time1(),
                                      column='RING_EVENT_STOP_TIME')
