################################################################################
# obs_bundle_uranus_occs_earthbased.py
#
# Defines the ObsBundleUranusOccsEarthbased class, which encapsulates fields in
# the common tables for the PDS4 bundle "uranus_occs_earthbase". This class
# supports multiple instruments in a single volume.
################################################################################

import config_targets

from obs_common_pds4 import ObsCommonPDS4


_TELESCOPE_MAPPING = {
    'caha_123cm': 'caha1m23',
    'ctio_150cm': 'ctio1m50',
    'ctio_400cm': 'ctio4m0',
    'eso_104cm': 'esosil1m04',
    'eso_220cm': 'esosil2m2',
    'eso_360cm': 'esosil3m6',
    'hst_fos': 'HSTFOS',
    'irtf_320cm': 'irtf3m2',
    'kao_91cm': 'kao0m91',
    'lco_100cm': 'lascam1m0',
    'lco_250cm': 'lascam2m5',
    'lowell_180cm': 'low1m83',
    'maunakea_380cm': 'mk3m8',
    'mcdonald_270cm': 'mcd2m7',
    'mso_190cm': 'mtstr1m9',
    'opmt_106cm': 'pic1m06',
    'opmt_200cm': 'pic2m0',
    'palomar_508cm': 'pal5m08',
    'saao_188cm': 'saao1m88',
    'sso_230cm': 'sso2m3',
    'sso_390cm': 'sso3m9',
    'teide_155cm': 'tei1m55',
}


class ObsBundleUranusOccsEarthbased(ObsCommonPDS4):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


    def _is_atmos(self):
        lid = self._index_col('pds:logical_identifier')
        return 'atmos' in lid

    def _inst_name(self):
        if self._metadata is None:
            # This happens during the create_tables phase
            return None
        # LID format:
        # urn:nasa:pds:uranus_occ_u13_sso_390cm:data:2200nm_counts-v-time_atmos_ingress
        # urn:nasa:pds:uranus_occ_u137_hst_fos:data:540nm_radius_alpha_egress_100m
        lid = self._index_col('pds:logical_identifier')
        lid = lid.split(':')
        main_lid = lid[3]
        _, _, star, inst1, inst2 = main_lid.split('_')
        return f'{inst1}_{inst2}'

    def _star_id(self):
        star_name = self._index_col('rings:star_name')
        return star_name.upper().replace(' ', '_')

    def _prof_ra_dec_helper(self):
        star_id = self._star_id()
        return (config_targets.STAR_RA_DEC[star_id][0]-self._STAR_RA_DEC_SLOP,
                config_targets.STAR_RA_DEC[star_id][0]+self._STAR_RA_DEC_SLOP,
                config_targets.STAR_RA_DEC[star_id][1]-self._STAR_RA_DEC_SLOP,
                config_targets.STAR_RA_DEC[star_id][1]+self._STAR_RA_DEC_SLOP)


    #############################
    ### OVERRIDE FROM ObsBase ###
    #############################

    # TODOPDS4
    @property
    def instrument_id(self):
        inst = self._inst_name()
        if inst is None:
            return None
        if inst not in _TELESCOPE_MAPPING:
            self._log_nonrepeating_error(f'Unknown telescope in LID "{inst}"')
        return _TELESCOPE_MAPPING[inst]

    @property
    def inst_host_id(self):
        return 'HST' if self._inst_name == 'hst_fos' else 'GB'

    @property
    def mission_id(self):
        return 'HST' if self._inst_name == 'hst_fos' else 'GB'

    # TODOPDS4 Figure out what the primary filespec should really be
    @property
    def primary_filespec(self):
        return self._index_col('filename') # Probably filepath

    # TODOPDS4 This is a hack to make up an OPUS ID until Pds4File works
    def opus_id_from_index_row(self, row):
        filename = row['filename']
        if not '_100m.xml' in filename:
            return None
        opus_id = filename.rstrip('_100m.xml')
        return opus_id

    # TODOPDS4 Should not be needed once Pds4File supports opus_id
    @property
    def opus_id(self):
        filespec = self.primary_filespec
        if filespec == self._opus_id_last_filespec:
            # Creating the OPUS ID can be expensive so we cache it here because
            # it is used for every obs_ table.
            return self._opus_id_cached
        opus_id = filespec.rstrip('_100m.xml')
        if not opus_id:
            self._log_nonrepeating_error(
                        f'Unable to create OPUS_ID using filespec {filespec}')
            return None
        self._opus_id_last_filespec = filespec
        self._opus_id_cached = opus_id
        return opus_id


    ################################
    ### OVERRIDE FROM ObsGeneral ###
    ################################

    def field_obs_general_right_asc1(self):
        return self._prof_ra_dec_helper()[0]

    def field_obs_general_right_asc2(self):
        return self._prof_ra_dec_helper()[1]

    def field_obs_general_declination1(self):
        return self._prof_ra_dec_helper()[2]

    def field_obs_general_declination2(self):
        return self._prof_ra_dec_helper()[3]

    def field_obs_general_planet_id(self):
        return self._create_mult('URA')

    def _target_name(self):
        target_name = 'URANUS' if self._is_atmos() else 'U RINGS'
        target_name, target_info = self._get_target_info(target_name)
        if target_info is None:
            return None, None
        return [(target_name, target_info[2])]

    def field_obs_general_quantity(self):
        return self._create_mult('OPDEPTH')

    def field_obs_general_observation_type(self):
        return self._create_mult('OCC')


    ###################################
    ### OVERRIDE FROM ObsWavelength ###
    ###################################

    def field_obs_wavelength_wavelength1(self):
        return self._index_col('rings:minimum_wavelength') / 1000. # nm->microns

    def field_obs_wavelength_wavelength2(self):
        return self._index_col('rings:maximum_wavelength') / 1000. # nm->microns


    ################################
    ### OVERRIDE FROM ObsProfile ###
    ################################

    def field_obs_profile_source(self):
        star_name = self._index_col('rings:star_name')
        star_name_id = star_name.upper().replace(' ', '_')
        return self._create_mult(star_name_id, disp_name=star_name)

    def field_obs_profile_host(self):
        inst = self._inst_name()
        if inst is None:
            return None
        if inst not in _TELESCOPE_MAPPING:
            self._log_nonrepeating_error(f'Unknown telescope in LID "{inst}"')
        return self._create_mult(_TELESCOPE_MAPPING[inst])


    #####################################
    ### OVERRIDE FROM ObsRingGeometry ###
    #####################################

    def field_obs_ring_geometry_ring_radius1(self):
        return self._index_col('rings:minimum_ring_radius')

    def field_obs_ring_geometry_ring_radius2(self):
        return self._index_col('rings:maximum_ring_radius')

    def field_obs_ring_geometry_resolution1(self):
        return self._index_col('rings:radial_resolution')

    def field_obs_ring_geometry_resolution2(self):
        return self._index_col('rings:radial_resolution')

    def field_obs_ring_geometry_projected_radial_resolution1(self):
        return self._index_col('rings:radial_resolution')

    def field_obs_ring_geometry_projected_radial_resolution2(self):
        return self._index_col('rings:radial_resolution')

    def field_obs_ring_geometry_range_to_ring_intercept1(self):
        return None

    def field_obs_ring_geometry_range_to_ring_intercept2(self):
        return None

    def field_obs_ring_geometry_ring_center_distance1(self):
        return None

    def field_obs_ring_geometry_ring_center_distance2(self):
        return None

    # TODOPDS4 I believe this is incorrect; in fact I expect the other ring
    # occultations volumes are also incorrect. The problem comes from our
    # definition of J2000 longitude vs longitude based on the ascending node.
    # We need to review all of our occultation volumes to see which definition
    # they use, and possible add a new pair of columns to the OPUS database
    # (which we were going to do anyway for the new ring geometry files).
    def field_obs_ring_geometry_j2000_longitude1(self):
        return self._index_col('rings:minimum_ring_longitude')

    def field_obs_ring_geometry_j2000_longitude2(self):
        return self._index_col('rings:maximum_ring_longitude')

    def field_obs_ring_geometry_solar_hour_angle1(self):
        return None

    def field_obs_ring_geometry_solar_hour_angle2(self):
        return None

    def field_obs_ring_geometry_longitude_wrt_observer1(self):
        return None

    def field_obs_ring_geometry_longitude_wrt_observer2(self):
        return None

    def field_obs_ring_geometry_ring_azimuth_wrt_observer1(self):
        return self._index_col('rings:minimum_ring_azimuth')

    def field_obs_ring_geometry_ring_azimuth_wrt_observer2(self):
        return self._index_col('rings:maximum_ring_azimuth')

    def field_obs_ring_geometry_sub_solar_ring_long1(self):
        return None

    def field_obs_ring_geometry_sub_solar_ring_long2(self):
        return None

    def field_obs_ring_geometry_sub_observer_ring_long1(self):
        return None

    def field_obs_ring_geometry_sub_observer_ring_long2(self):
        return None

    # Earth was seeing Uranus' south pole for the entire duration of this data set.
    # Thus the solar elevation was seeing the northern hemisphere and the
    # observer elevation was seeing the southern hemisphere.
    # For Uranus, these values are positive for the southern hemisphere.

    def field_obs_ring_geometry_solar_ring_elevation1(self):
        return self._index_col('rings:light_source_incidence_angle') - 90.

    def field_obs_ring_geometry_solar_ring_elevation2(self):
        return self._index_col('rings:light_source_incidence_angle') - 90.

    def field_obs_ring_geometry_observer_ring_elevation1(self):
        return 90. - self._index_col('rings:light_source_incidence_angle')

    def field_obs_ring_geometry_observer_ring_elevation2(self):
        return 90. - self._index_col('rings:light_source_incidence_angle')

    def field_obs_ring_geometry_phase1(self):
        return 180.

    def field_obs_ring_geometry_phase2(self):
        return 180.

    def field_obs_ring_geometry_incidence1(self):
        return self._index_col('rings:light_source_incidence_angle')

    def field_obs_ring_geometry_incidence2(self):
        return self._index_col('rings:light_source_incidence_angle')

    def field_obs_ring_geometry_emission1(self):
        return 180.-self._index_col('rings:light_source_incidence_angle')

    def field_obs_ring_geometry_emission2(self):
        return 180.-self._index_col('rings:light_source_incidence_angle')

    # Earth was seeing Uranus' south pole for the entire duration of this data set.
    # Thus the star was illuminating the north side of the rings, and the
    # north-based values are the same as the plain values.

    def field_obs_ring_geometry_north_based_incidence1(self):
        return self._index_col('rings:light_source_incidence_angle')

    def field_obs_ring_geometry_north_based_incidence2(self):
        return self._index_col('rings:light_source_incidence_angle')

    def field_obs_ring_geometry_north_based_emission1(self):
        return 180.-self._index_col('rings:light_source_incidence_angle')

    def field_obs_ring_geometry_north_based_emission2(self):
        return 180.-self._index_col('rings:light_source_incidence_angle')

    def field_obs_ring_geometry_ring_center_phase1(self):
        return 180.

    def field_obs_ring_geometry_ring_center_phase2(self):
        return 180.

    def field_obs_ring_geometry_ring_center_incidence1(self):
        return self._index_col('rings:light_source_incidence_angle')

    def field_obs_ring_geometry_ring_center_incidence2(self):
        return self._index_col('rings:light_source_incidence_angle')

    def field_obs_ring_geometry_ring_center_emission1(self):
        return 180.-self._index_col('rings:light_source_incidence_angle')

    def field_obs_ring_geometry_ring_center_emission2(self):
        return 180.-self._index_col('rings:light_source_incidence_angle')

    def field_obs_ring_geometry_ring_center_north_based_incidence1(self):
        return self._index_col('rings:light_source_incidence_angle')

    def field_obs_ring_geometry_ring_center_north_based_incidence2(self):
        return self._index_col('rings:light_source_incidence_angle')

    def field_obs_ring_geometry_ring_center_north_based_emission1(self):
        return 180.-self._index_col('rings:light_source_incidence_angle')

    def field_obs_ring_geometry_ring_center_north_based_emission2(self):
        return 180.-self._index_col('rings:light_source_incidence_angle')

    def field_obs_ring_geometry_solar_ring_opening_angle1(self):
        return -self._index_col('rings:observed_ring_elevation')

    def field_obs_ring_geometry_solar_ring_opening_angle2(self):
        return -self._index_col('rings:observed_ring_elevation')

    def field_obs_ring_geometry_observer_ring_opening_angle1(self):
        return self._index_col('rings:observed_ring_elevation')

    def field_obs_ring_geometry_observer_ring_opening_angle2(self):
        return self._index_col('rings:observed_ring_elevation')

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
        return self._index_col('rings:ring_event_start_tdb')

    def field_obs_ring_geometry_ring_intercept_time2(self):
        return self._index_col('rings:ring_event_stop_tdb')

    # TODOPDS4 Note: For atmos this is not really a "ring event time",
    # it's a "planet event time", but we don't have a field for that.
    # Should we instead add something under surface geometry?
