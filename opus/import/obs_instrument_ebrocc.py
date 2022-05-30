################################################################################
# obs_instrument_ebrocc.py
#
# Defines the ObsInstrumentEBROCC class, which encapsulates fields for
# the common tables for EBROCC_0001. This class supports multiple instruments
# in a single volume.
################################################################################

from obs_common import ObsCommon

# XXX NOTE THIS ONLY WORKS FOR 28 SGR RIGHT NOW.
# On 1989-07-03:
# * 28 Sgr incidence angle was 64.627 on the south side
# * North-based incidence angle was 180-64.627 = 115.373
# * The north side of the rings were illuminated by the Sun
# * Earth was viewing the north side of the rings
# * Emission angle and north-based emission angle = incidence angle
# * Observer elevation = 90 - incidence angle

class ObsInstrumentEBROCC(ObsCommon):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


    #############################
    ### OVERRIDE FROM ObsBase ###
    #############################

    @property
    def instrument_id(self):
        if self._metadata is None:
            # This happens during the create_tables phase
            return None
        return (self._supp_index_col('INSTRUMENT_HOST_ID') +
                self._supp_index_col('INSTRUMENT_ID'))

    @property
    def inst_host_id(self):
        return 'GB'

    @property
    def mission_id(self):
        return 'GB'

    @property
    def primary_filespec(self):
        # Note it's very important that this can be calculated using ONLY
        # the primary index, not the supplemental index!
        # This is because this (and the subsequent creation of opus_id) is used
        # to actually find the matching row in the supplemental index dictionary.
        # Format: "/DATA/ESO1M/ES1_EPD.LBL"
        filespec = self._index_col('FILE_SPECIFICATION_NAME')
        return self.volume + filespec

    def convert_filespec_from_lbl(self, filespec):
        return filespec.replace('.LBL', '.TAB')


    ################################
    ### OVERRIDE FROM ObsGeneral ###
    ################################

    def field_obs_general_right_asc1(self):
        return self._prof_ra_dec_helper('index_label', 'STAR_NAME')[0]

    def field_obs_general_right_asc2(self):
        return self._prof_ra_dec_helper('index_label', 'STAR_NAME')[1]

    def field_obs_general_declination1(self):
        return self._prof_ra_dec_helper('index_label', 'STAR_NAME')[2]

    def field_obs_general_declination2(self):
        return self._prof_ra_dec_helper('index_label', 'STAR_NAME')[3]

    def field_obs_general_planet_id(self):
        return self._create_mult('SAT')

    def _target_name(self):
        target_name = self._index_label_col('TARGET_NAME')

        if target_name != 'S RINGS':
            self._log_nonrepeating_error(
                f'Ground-based mission targets "{target_name}" instead of "S RINGS"')

        target_name, target_info = self._get_target_info(target_name)
        if target_info is None:
            return None, None

        return target_name, target_info[2]

    def field_obs_general_target_name(self):
        target_name, target_disp_name = self._target_name()
        if target_name is None:
            return self._create_mult(None)
        group_info = self._get_planet_group_info(target_name)
        return self._create_mult(col_val=target_name, disp_name=target_disp_name,
                                 grouping=group_info['label'],
                                 group_disp_order=group_info['disp_order'])

    def field_obs_general_quantity(self):
        return self._create_mult('OPDEPTH')

    def field_obs_general_observation_type(self):
        return self._create_mult('OCC')


    ###################################
    ### OVERRIDE FROM ObsWavelength ###
    ###################################

    def field_obs_wavelength_wavelength1(self):
        return self._supp_index_col('WAVELENGTH')

    def field_obs_wavelength_wavelength2(self):
        return self._supp_index_col('WAVELENGTH')


    ################################
    ### OVERRIDE FROM ObsProfile ###
    ################################

    def field_obs_profile_occ_type(self):
        return self._create_mult('STE')

    def field_obs_profile_occ_dir(self):
        occ_dir = self._index_col('OCCULTATION_DIRECTION')
        if occ_dir in ('INGRESS', 'EGRESS', 'BOTH'):
            return self._create_mult(occ_dir[0])
        self._log_nonrepeating_error(f'Unknown OCCULTATION_DIRECTION "{occ_dir}"')
        return self._create_mult(None)

    def field_obs_profile_body_occ_flag(self):
        return self._create_mult(self._supp_index_col('PLANETARY_OCCULTATION_FLAG'))

    def field_obs_profile_quality_score(self):
        return self._create_mult('UNASSIGNED')

    def field_obs_profile_wl_band(self):
        wl = self._supp_index_col('WAVELENGTH') # microns
        if wl > 0.7:
            return self._create_mult('IR')
        if wl > 0.4:
            return self._create_mult('VIS')
        return self._create_mult('UV')

    def field_obs_profile_source(self):
        target_name, target_info = self._star_name_helper('index_label', 'STAR_NAME')
        if target_info is None:
            return self._create_mult(None)
        return self._create_mult(col_val=target_name, disp_name=target_info[2],
                                 grouping='Stars')

    def field_obs_profile_host(self):
        ret = self._supp_index_col('INSTRUMENT_HOST_NAME')
        return self._create_mult_keep_case(col_val=ret,
                                           grouping='Ground-based Telescopes')


    #####################################
    ### OVERRIDE FROM ObsRingGeometry ###
    #####################################

    def field_obs_ring_geometry_ring_radius1(self):
        return self._supp_index_col('MINIMUM_RING_RADIUS')

    def field_obs_ring_geometry_ring_radius2(self):
        return self._supp_index_col('MAXIMUM_RING_RADIUS')

    def field_obs_ring_geometry_resolution1(self):
        return self._supp_index_col('RADIAL_RESOLUTION')

    def field_obs_ring_geometry_resolution2(self):
        return self._supp_index_col('RADIAL_RESOLUTION')

    def field_obs_ring_geometry_projected_radial_resolution1(self):
        return self._supp_index_col('RADIAL_RESOLUTION')

    def field_obs_ring_geometry_projected_radial_resolution2(self):
        return self._supp_index_col('RADIAL_RESOLUTION')

    def field_obs_ring_geometry_range_to_ring_intercept1(self):
        return self._ring_geo_index_col('MINIMUM_RING_DISTANCE')

    def field_obs_ring_geometry_range_to_ring_intercept2(self):
        return self._ring_geo_index_col('MAXIMUM_RING_DISTANCE')

    def field_obs_ring_geometry_ring_center_distance1(self):
        return self._ring_geo_index_col('RING_CENTER_DISTANCE')

    def field_obs_ring_geometry_ring_center_distance2(self):
        return self._ring_geo_index_col('RING_CENTER_DISTANCE')

    def field_obs_ring_geometry_j2000_longitude1(self):
        return self._ring_geo_index_col('MINIMUM_RING_LONGITUDE')

    def field_obs_ring_geometry_j2000_longitude2(self):
        return self._ring_geo_index_col('MAXIMUM_RING_LONGITUDE')

    def field_obs_ring_geometry_solar_hour_angle1(self):
        return self._ring_geo_index_col('MINIMUM_SOLAR_HOUR_ANGLE')

    def field_obs_ring_geometry_solar_hour_angle2(self):
        return self._ring_geo_index_col('MAXIMUM_SOLAR_HOUR_ANGLE')

    def field_obs_ring_geometry_longitude_wrt_observer1(self):
        return self._ring_geo_index_col('MINIMUM_RING_LONGITUDE_WRT_OBSERVER')

    def field_obs_ring_geometry_longitude_wrt_observer2(self):
        return self._ring_geo_index_col('MAXIMUM_RING_LONGITUDE_WRT_OBSERVER')

    def field_obs_ring_geometry_ring_azimuth_wrt_observer1(self):
        return self._ring_geo_index_col('MINIMUM_RING_AZIMUTH')

    def field_obs_ring_geometry_ring_azimuth_wrt_observer2(self):
        return self._ring_geo_index_col('MAXIMUM_RING_AZIMUTH')

    def field_obs_ring_geometry_sub_solar_ring_long1(self):
        return self._ring_geo_index_col('SUB_SOLAR_RING_LONGITUDE')

    def field_obs_ring_geometry_sub_solar_ring_long2(self):
        return self._ring_geo_index_col('SUB_SOLAR_RING_LONGITUDE')

    def field_obs_ring_geometry_sub_observer_ring_long1(self):
        return self._ring_geo_index_col('SUB_OBSERVER_RING_LONGITUDE')

    def field_obs_ring_geometry_sub_observer_ring_long2(self):
        return self._ring_geo_index_col('SUB_OBSERVER_RING_LONGITUDE')

    def field_obs_ring_geometry_solar_ring_elevation1(self):
        # This is only valid for EBROCC 28 Sgr where the star was on the south
        # side of the rings
        return self._supp_index_col('INCIDENCE_ANGLE')-90.

    def field_obs_ring_geometry_solar_ring_elevation2(self):
        # This is only valid for EBROCC 28 Sgr where the star was on the south
        # side of the rings
        return self._supp_index_col('INCIDENCE_ANGLE')-90.

    def field_obs_ring_geometry_observer_ring_elevation1(self):
        # This is only valid for EBROCC 28 Sgr where the star was on the south
        # side of the rings
        return 90.-self._supp_index_col('INCIDENCE_ANGLE')

    def field_obs_ring_geometry_observer_ring_elevation2(self):
        # This is only valid for EBROCC 28 Sgr where the star was on the south
        # side of the rings
        return 90.-self._supp_index_col('INCIDENCE_ANGLE')

    def field_obs_ring_geometry_phase1(self):
        return 180.

    def field_obs_ring_geometry_phase2(self):
        return 180.

    def field_obs_ring_geometry_incidence1(self):
        return self._supp_index_col('INCIDENCE_ANGLE')

    def field_obs_ring_geometry_incidence2(self):
        return self._supp_index_col('INCIDENCE_ANGLE')

    def field_obs_ring_geometry_emission1(self):
        return 180.-self._supp_index_col('INCIDENCE_ANGLE')

    def field_obs_ring_geometry_emission2(self):
        return 180.-self._supp_index_col('INCIDENCE_ANGLE')

    def field_obs_ring_geometry_north_based_incidence1(self):
        # This is only valid for EBROCC 28 Sgr where the star was on the south
        # side of the rings
        return 180.-self._supp_index_col('INCIDENCE_ANGLE')

    def field_obs_ring_geometry_north_based_incidence2(self):
        # This is only valid for EBROCC 28 Sgr where the star was on the south
        # side of the rings
        return 180.-self._supp_index_col('INCIDENCE_ANGLE')

    def field_obs_ring_geometry_north_based_emission1(self):
        # This is only valid for EBROCC 28 Sgr where the star was on the south
        # side of the rings
        return self._supp_index_col('INCIDENCE_ANGLE')

    def field_obs_ring_geometry_north_based_emission2(self):
        # This is only valid for EBROCC 28 Sgr where the star was on the south
        # side of the rings
        return self._supp_index_col('INCIDENCE_ANGLE')

    def field_obs_ring_geometry_ring_center_phase1(self):
        return 180.

    def field_obs_ring_geometry_ring_center_phase2(self):
        return 180.

    def field_obs_ring_geometry_ring_center_incidence1(self):
        return self._supp_index_col('INCIDENCE_ANGLE')

    def field_obs_ring_geometry_ring_center_incidence2(self):
        return self._supp_index_col('INCIDENCE_ANGLE')

    def field_obs_ring_geometry_ring_center_emission1(self):
        return 180.-self._supp_index_col('INCIDENCE_ANGLE')

    def field_obs_ring_geometry_ring_center_emission2(self):
        return 180.-self._supp_index_col('INCIDENCE_ANGLE')

    def field_obs_ring_geometry_ring_center_north_based_incidence1(self):
        # This is only valid for EBROCC 28 Sgr where the star was on the south
        # side of the rings
        return 180.-self._supp_index_col('INCIDENCE_ANGLE')

    def field_obs_ring_geometry_ring_center_north_based_incidence2(self):
        # This is only valid for EBROCC 28 Sgr where the star was on the south
        # side of the rings
        return 180.-self._supp_index_col('INCIDENCE_ANGLE')

    def field_obs_ring_geometry_ring_center_north_based_emission1(self):
        # This is only valid for EBROCC 28 Sgr where the star was on the south
        # side of the rings
        return self._supp_index_col('INCIDENCE_ANGLE')

    def field_obs_ring_geometry_ring_center_north_based_emission2(self):
        # This is only valid for EBROCC 28 Sgr where the star was on the south
        # side of the rings
        return self._supp_index_col('INCIDENCE_ANGLE')

    def field_obs_ring_geometry_solar_ring_opening_angle1(self):
        # This is only valid for EBROCC 28 Sgr where the star was on the south
        # side of the rings
        return self._supp_index_col('INCIDENCE_ANGLE')-90.

    def field_obs_ring_geometry_solar_ring_opening_angle2(self):
        # This is only valid for EBROCC 28 Sgr where the star was on the south
        # side of the rings
        return self._supp_index_col('INCIDENCE_ANGLE')-90.

    def field_obs_ring_geometry_observer_ring_opening_angle1(self):
        # This is only valid for EBROCC 28 Sgr where the star was on the south
        # side of the rings
        return 90.-self._supp_index_col('INCIDENCE_ANGLE')

    def field_obs_ring_geometry_observer_ring_opening_angle2(self):
        # This is only valid for EBROCC 28 Sgr where the star was on the south
        # side of the rings
        return 90.-self._supp_index_col('INCIDENCE_ANGLE')

    def field_obs_ring_geometry_edge_on_radius1(self):
        return None

    def field_obs_ring_geometry_edge_on_radius2(self):
        return None

    def field_obs_ring_geometry_edge_on_altitude1(self):
        return None

    def field_obs_ring_geometry_edge_on_altitude2(self):
        return None

    def field_obs_ring_geometry_edge_on_radial_resolution1(self):
        return None

    def field_obs_ring_geometry_edge_on_radial_resolution2(self):
        return None

    def field_obs_ring_geometry_range_to_edge_on_point1(self):
        return None

    def field_obs_ring_geometry_range_to_edge_on_point2(self):
        return None

    def field_obs_ring_geometry_edge_on_j2000_longitude1(self):
        return None

    def field_obs_ring_geometry_edge_on_j2000_longitude2(self):
        return None

    def field_obs_ring_geometry_edge_on_solar_hour_angle1(self):
        return None

    def field_obs_ring_geometry_edge_on_solar_hour_angle2(self):
        return None

    def field_obs_ring_geometry_ring_intercept_time1(self):
        return self._time_from_index(column='RING_EVENT_START')

    def field_obs_ring_geometry_ring_intercept_time2(self):
        return self._time2_from_index(self.field_obs_ring_geometry_ring_intercept_time1(),
                                      'RING_EVENT_STOP')
