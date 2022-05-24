################################################################################
# obs_instrument_cocirs_cube.py
#
# Defines the ObsInstrumentCOCIRSCube class, which encapsulates fields in the
# common, obs_mission_cassini, and obs_instrument_cocirs tables for volumes
# COCIRS_[01]xxx.
################################################################################

import julian

import opus_support

from obs_mission_cassini import ObsMissionCassini

_EQUINOX_DATE = julian.tai_from_iso('2009-08-11T01:40:08.914')


class ObsInstrumentCOCIRSCube(ObsMissionCassini):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _get_cube_map_projection(self):
        return self._index_col('PRODUCT_ID')[-1].lower()

    def _is_ring_map_projection(self):
        return self._get_cube_map_projection() == 'r'

    def _is_equi_map_projection(self):
        return self._get_cube_map_projection() == 'e'

    # Equinox: 2009-08-11T01:40:08.914
    # Before this time, north side of the ring is lit.
    # After this time, south side of the ring is lit.
    def _is_ring_north_side_lit(self):
        return self.field_obs_general_time1() < _EQUINOX_DATE

    # Use north based emission angle to determine if observer is at the north of the
    # ring.
    def _is_cassini_at_north(self):
        ea = self.field_obs_ring_geometry_north_based_emission1()
        return 0 <= ea <= 90


    #############################
    ### OVERRIDE FROM ObsBase ###
    #############################

    @property
    def instrument_id(self):
        return 'COCIRS'

    def surface_geo_target_list(self):
        # If the surface_geo info exists somewhere other than in separate summary
        # files, we can give a list of targets this observation supports here.
        # This instrument's surface geo field methods will then be called on
        # each target.
        if not self._is_equi_map_projection():
            return None
        return (self._index_col('TARGET_NAME'), )

    def convert_filespec_from_lbl(self, filespec):
        return filespec.replace('.LBL', '.tar.gz')


    ################################
    ### OVERRIDE FROM ObsGeneral ###
    ################################

    def field_obs_general_ring_obs_id(self):
        return None

    def field_obs_general_planet_id(self):
        return self._create_mult('SAT')

    def _target_name(self):
        return self._cassini_intended_target_name()

    def field_obs_general_target_name(self):
        col_val, disp_name = self._target_name()
        return self._create_mult(col_val=col_val, disp_name=disp_name)

    def field_obs_general_quantity(self):
        return self._create_mult('THERMAL')

    def field_obs_general_observation_type(self):
        return self._create_mult('SCU') # Spectral Cube


    ############################
    ### OVERRIDE FROM ObsPds ###
    ############################

    def field_obs_pds_product_id(self):
        # Format: "DATA/APODSPEC/SPEC0802010000_FP1.DAT"
        return self._index_col('FILE_SPECIFICATION_NAME').split('/')[-1]

    def field_obs_pds_product_creation_time(self):
        return None


    ###################################
    ### OVERRIDE FROM ObsWavelength ###
    ###################################

    def field_obs_wavelength_wavelength1(self):
        wave_no2 = self._supp_index_col('MAXIMUM_WAVENUMBER')
        if wave_no2 is None:
            return None
        return 10000. / wave_no2

    def field_obs_wavelength_wavelength2(self):
        wave_no1 = self._supp_index_col('MINIMUM_WAVENUMBER')
        if wave_no1 is None:
            return None
        return 10000. / wave_no1

    def field_obs_wavelength_wave_res1(self):
        wnr = self._supp_index_col('BAND_BIN_WIDTH')
        wn2 = self._supp_index_col('MAXIMUM_WAVENUMBER')
        if wnr is None or wn2 is None:
            return None
        return 10000.*wnr/(wn2*wn2)

    def field_obs_wavelength_wave_res2(self):
        wnr = self._supp_index_col('BAND_BIN_WIDTH')
        wn1 = self._supp_index_col('MINIMUM_WAVENUMBER')
        if wnr is None or wn1 is None:
            return None
        return 10000.*wnr/(wn1*wn1)

    def field_obs_wavelength_wave_no1(self):
        return self._supp_index_col('MINIMUM_WAVENUMBER')

    def field_obs_wavelength_wave_no2(self):
        return self._supp_index_col('MAXIMUM_WAVENUMBER')

    def field_obs_wavelength_wave_no_res1(self):
        return self._supp_index_col('BAND_BIN_WIDTH')

    def field_obs_wavelength_wave_no_res2(self):
        return self._supp_index_col('BAND_BIN_WIDTH')

    def field_obs_wavelength_spec_flag(self):
        return self._create_mult('Y')

    def field_obs_wavelength_spec_size(self):
        return self._supp_index_col('BANDS')


    #####################################
    ### OVERRIDE FROM ObsRingGeometry ###
    #####################################

    def field_obs_ring_geometry_ring_radius1(self):
        if not self._is_ring_map_projection():
            return None
        return self._index_col('CSS:MEAN_RING_BORESIGHT_RADIUS_ZPD')

    def field_obs_ring_geometry_ring_radius2(self):
        if not self._is_ring_map_projection():
            return None
        return self._index_col('CSS:MEAN_RING_BORESIGHT_RADIUS_ZPD')

    def field_obs_ring_geometry_j2000_longitude1(self):
        if not self._is_ring_map_projection():
            return None
        return self._index_col('CSS:PRIMARY_SUB_SOLAR_LONGITUDE_BEGINNING')

    def field_obs_ring_geometry_j2000_longitude2(self):
        if not self._is_ring_map_projection():
            return None
        return self._index_col('CSS:PRIMARY_SUB_SOLAR_LONGITUDE_END')

    def field_obs_ring_geometry_observer_ring_elevation1(self):
        return self.field_obs_ring_geometry_observer_ring_opening_angle1()

    def field_obs_ring_geometry_observer_ring_elevation2(self):
        return self.field_obs_ring_geometry_observer_ring_opening_angle1()

    def field_obs_ring_geometry_phase1(self):
        if not self._is_ring_map_projection():
            return None
        return self._index_col('CSS:MEAN_RING_BORESIGHT_SOLAR_PHASE')

    def field_obs_ring_geometry_phase2(self):
        if not self._is_ring_map_projection():
            return None
        return self._index_col('CSS:MEAN_RING_BORESIGHT_SOLAR_PHASE')

    def field_obs_ring_geometry_emission1(self):
        if not self._is_ring_map_projection():
            return None
        return self._index_col('CSS:MEAN_RING_BORESIGHT_EMISSION_ANGLE')

    def field_obs_ring_geometry_emission2(self):
        if not self._is_ring_map_projection():
            return None
        return self._index_col('CSS:MEAN_RING_BORESIGHT_EMISSION_ANGLE')

    def field_obs_ring_geometry_north_based_emission1(self):
        if not self._is_ring_map_projection():
            return None
        ea = self._index_col('CSS:MEAN_RING_BORESIGHT_EMISSION_ANGLE')
        if self._is_ring_north_side_lit():
            return ea
        return 180. - ea

    def field_obs_ring_geometry_north_based_emission2(self):
        return self.field_obs_ring_geometry_north_based_emission1()

    def field_obs_ring_geometry_ring_center_phase1(self):
        return self.field_obs_ring_geometry_phase1()

    def field_obs_ring_geometry_ring_center_phase2(self):
        return self.field_obs_ring_geometry_phase2()

    def field_obs_ring_geometry_ring_center_emission1(self):
        return self.field_obs_ring_geometry_emission1()

    def field_obs_ring_geometry_ring_center_emission2(self):
        return self.field_obs_ring_geometry_emission2()

    def field_obs_ring_geometry_ring_center_north_based_emission1(self):
        return self.field_obs_ring_geometry_north_based_emission1()

    def field_obs_ring_geometry_ring_center_north_based_emission2(self):
        return self.field_obs_ring_geometry_north_based_emission2()

    def field_obs_ring_geometry_observer_ring_opening_angle1(self):
        if not self._is_ring_map_projection():
            return None
        ea = self._index_col('CSS:MEAN_RING_BORESIGHT_EMISSION_ANGLE')
        if self._is_cassini_at_north():
            return abs(90. - ea)
        return -abs(90. - ea)

    def field_obs_ring_geometry_observer_ring_opening_angle2(self):
        return self.field_obs_ring_geometry_observer_ring_opening_angle1()


    ##############################################
    ### OVERRIDE FROM ObsSurfaceGeometryTarget ###
    ##############################################

    def field_obs_surface_geometry_target_planetocentric_latitude1(self):
        if not self._is_equi_map_projection():
            return None
        return self._index_col('CSS:MEAN_BORESIGHT_LATITUDE_ZPD_PC')

    def field_obs_surface_geometry_target_planetocentric_latitude2(self):
        return self.field_obs_surface_geometry_target_planetocentric_latitude1()

    def field_obs_surface_geometry_target_planetographic_latitude1(self):
        if not self._is_equi_map_projection():
            return None
        return self._index_col('CSS:MEAN_BORESIGHT_LATITUDE_ZPD')

    def field_obs_surface_geometry_target_planetographic_latitude2(self):
        return self.field_obs_surface_geometry_target_planetographic_latitude1()

    def field_obs_surface_geometry_target_iau_west_longitude1(self):
        if not self._is_equi_map_projection():
            return None
        return self._index_col('CSS:MEAN_BORESIGHT_LONGITUDE_ZPD')

    def field_obs_surface_geometry_target_iau_west_longitude2(self):
        return self.field_obs_surface_geometry_target_iau_west_longitude1()

    def field_obs_surface_geometry_target_phase1(self):
        if not self._is_equi_map_projection():
            return None
        return self._index_col('CSS:MEAN_BODY_PHASE_ANGLE')

    def field_obs_surface_geometry_target_phase2(self):
        return self.field_obs_surface_geometry_target_phase1()

    def field_obs_surface_geometry_target_emission1(self):
        if not self._is_equi_map_projection():
            return None
        return self._index_col('CSS:MEAN_EMISSION_ANGLE_FOV_AVERAGE')

    def field_obs_surface_geometry_target_emission2(self):
        return self.field_obs_surface_geometry_target_emission1()

    def field_obs_surface_geometry_target_sub_solar_planetocentric_latitude(self):
        if not self._is_equi_map_projection():
            return None
        return self._index_col('CSS:BODY_SUB_SOLAR_LATITUDE_PC_MIDDLE')

    def field_obs_surface_geometry_target_sub_solar_planetographic_latitude(self):
        if not self._is_equi_map_projection():
            return None
        return self._index_col('CSS:BODY_SUB_SOLAR_LATITUDE_MIDDLE')

    def field_obs_surface_geometry_target_sub_observer_planetocentric_latitude(self):
        if not self._is_equi_map_projection():
            return None
        return self._index_col('CSS:BODY_SUB_SPACECRAFT_LATITUDE_PC_MIDDLE')

    def field_obs_surface_geometry_target_sub_observer_planetographic_latitude(self):
        if not self._is_equi_map_projection():
            return None
        return self._index_col('CSS:BODY_SUB_SPACECRAFT_LATITUDE_MIDDLE')

    def field_obs_surface_geometry_target_sub_solar_iau_west_longitude(self):
        if not self._is_equi_map_projection():
            return None
        return self._index_col('CSS:BODY_SUB_SOLAR_LONGITUDE_MIDDLE')

    def field_obs_surface_geometry_target_sub_observer_iau_west_longitude(self):
        if not self._is_equi_map_projection():
            return None
        return self._index_col('CSS:BODY_SUB_SPACECRAFT_LONGITUDE_MIDDLE')

    def field_obs_surface_geometry_target_center_distance(self):
        if not self._is_equi_map_projection():
            return None
        return self._index_col('CSS:BODY_SPACECRAFT_RANGE_MIDDLE')


    #######################################
    ### OVERRIDE FROM ObsMissionCassini ###
    #######################################

    # Warning: Both the equi/point/ring index files and the supplemental index files
    # have an OBSERVATION_ID field and they're different! The index file version looks
    # like "127EN_ICYPLU001____UV____699_F1_039E" and the supplemental index version
    # looks like "CIRS_127EN_ICYPLU001_UVIS", which is obviously correct. We rely
    # on the default behavior for obs_mission_cassini_obs_name(), which looks first
    # in the supplemental index. If we end up with the plain index version for some
    # reason, many derived Cassini mission fields will be incorrect.

    def field_obs_mission_cassini_spacecraft_clock_count1(self):
        sc = self._index_col('SPACECRAFT_CLOCK_START_COUNT')
        sc = self._fix_cassini_sclk(sc)
        if not sc.startswith('1/'):
            self._log_nonrepeating_error(
                f'Badly formatted SPACECRAFT_CLOCK_START_COUNT "{sc}"')
            return None
        try:
            sc_cvt = opus_support.parse_cassini_sclk(sc)
        except Exception as e:
            self._log_nonrepeating_error(f'Unable to parse Cassini SCLK "{sc}": {e}')
            return None
        return sc_cvt

    def field_obs_mission_cassini_spacecraft_clock_count2(self):
        sc = self._index_col('SPACECRAFT_CLOCK_STOP_COUNT')
        sc = self._fix_cassini_sclk(sc)
        if not sc.startswith('1/'):
            self._log_nonrepeating_error(
                f'Badly formatted SPACECRAFT_CLOCK_START_COUNT "{sc}"')
            return None
        try:
            sc_cvt = opus_support.parse_cassini_sclk(sc)
        except Exception as e:
            self._log_nonrepeating_error(f'Unable to parse Cassini SCLK "{sc}": {e}')
            return None
        return sc_cvt

        sc1 = self.field_obs_mission_cassini_spacecraft_clock_count1()
        if sc1 is not None and sc_cvt < sc1:
            self._log_nonrepeating_warning(
                f'spacecraft_clock_count1 ({sc1}) and spacecraft_clock_count2 '+
                f'({sc_cvt}) are in the wrong order - setting to count1')
            sc_cvt = sc1

        return sc_cvt

    def field_obs_mission_cassini_mission_phase_name(self):
        mp = self._supp_index_col('MISSION_PHASE_NAME')
        if mp.upper() == 'NULL':
            return self._create_mult(None)
        return self._create_mult(mp.replace('_', ' '))


    ###############################################
    ### FIELD METHODS FOR obs_instrument_cocirs ###
    ###############################################

    def field_obs_instrument_cocirs_opus_id(self):
        return self.opus_id

    def field_obs_instrument_cocirs_volume_id(self):
        return self.volume

    def field_obs_instrument_cocirs_instrument_id(self):
        return self.instrument_id

    def field_obs_instrument_cocirs_detector_id(self):
        return self._create_mult(self._supp_index_col('DETECTOR_ID'))

    def field_obs_instrument_cocirs_instrument_mode_blinking_flag(self):
        return self._create_mult(None)

    def field_obs_instrument_cocirs_instrument_mode_even_flag(self):
        return self._create_mult(None)

    def field_obs_instrument_cocirs_instrument_mode_odd_flag(self):
        return self._create_mult(None)

    def field_obs_instrument_cocirs_instrument_mode_centers_flag(self):
        return self._create_mult(None)

    def field_obs_instrument_cocirs_instrument_mode_pairs_flag(self):
        return self._create_mult(None)

    def field_obs_instrument_cocirs_instrument_mode_all_flag(self):
        return self._create_mult(None)
