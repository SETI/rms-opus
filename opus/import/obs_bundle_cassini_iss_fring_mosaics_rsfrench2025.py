################################################################################
# obs_bundle_cassini_iss_fring_mosaics_rsfrench2025.py
#
# Defines the ObsBundleCassiniIssFringMosaicsRSFrench2025 class, which encapsulates
# fields in the common, obs_mission_cassini, and obs_instrument_coiss tables for
# the PDS4 bundleset "cassini_iss_fring_mosaics_rsfrench2025". This class
# supports derived data from the cassini_iss_fring_mosaics_rsfrench2025 bundle.
################################################################################

import import_util
import opus_support

from obs_cassini_common_pds4 import ObsCassiniCommonPDS4
from obs_volume_coiss_12xxx import _COISS_FILTER_WAVELENGTHS


class ObsBundleCassiniIssFringMosaicsRSFrench2025(ObsCassiniCommonPDS4):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


    #############################
    ### OVERRIDE FROM ObsBase ###
    #############################

    @property
    def instrument_id(self):
        return 'COISS'

    @property
    def primary_filespec(self):
        rel = self._index_col('file_spec')
        if rel is None:
            return None
        return self.bundle + '/' + rel.strip()

    def primary_filespec_from_index_row(self, row, convert_lbl=False,
                                        add_phase_from_inst=False):
        rel = row.get('file_spec')
        if rel is None:
            return None
        return self.bundle + '/' + str(rel).strip()

    def _some_index_col(self, col, idx=None):
        if (col == 'OBSERVATION_ID' and self._metadata is not None and
                self._metadata.get('index_row') and
                'cassini:observation_id' in self._metadata['index_row']):
            v = import_util.safe_column(
                self._metadata['index_row'], 'cassini:observation_id', idx=idx)
            if v is not None and isinstance(v, str):
                return v.strip()
            return v
        return super()._some_index_col(col, idx=idx)


    ################################
    ### OVERRIDE FROM ObsProfilePDS4
    ### (non-occultation; match ObsProfilePDS3 pattern)
    ################################

    def field_obs_profile_occ_type(self):
        return self._create_mult(None)

    def field_obs_profile_occ_dir(self):
        return self._create_mult(None)

    def field_obs_profile_body_occ_flag(self):
        return self._create_mult(None)

    def field_obs_profile_temporal_sampling(self):
        return None

    def field_obs_profile_quality_score(self):
        return self._create_mult(None)

    def field_obs_profile_optical_depth1(self):
        return None

    def field_obs_profile_optical_depth2(self):
        return None

    def field_obs_profile_wl_band(self):
        return self._create_mult(None)

    def field_obs_profile_source(self):
        return self._create_mult(None)

    def field_obs_profile_host(self):
        return self._create_mult(None)


    ################################
    ### OVERRIDE FROM ObsGeneral ###
    ################################

    def field_obs_general_planet_id(self):
        return self._create_mult('SAT')

    def _target_name(self):
        return [('S RINGS', 'Saturn Rings')]

    def field_obs_general_quantity(self):
        return self._create_mult('REFLECT')

    def field_obs_general_observation_type(self):
        # Mosaic / bkg_sub tables: MOS; per-frame reprojected images: IMG
        fs = self._index_col('file_spec')
        if fs is not None and 'data_reproj_img' in fs.lower():
            return self._create_mult('IMG')
        return self._create_mult('MOS')

    def field_obs_general_time1(self):
        return self._time_from_index(column='pds:start_date_time')

    def field_obs_general_time2(self):
        return self._time2_from_some_index(self.field_obs_general_time1(),
                                           column='pds:stop_date_time')


    ################################
    ### OVERRIDE FROM ObsPdsPDS4 ###
    ################################

    def field_obs_pds_product_creation_time(self):
        return self._time_from_index(column='product_creation_date')

    def field_obs_pds_note(self):
        return self._index_col('notes')


    #####################################
    ### OVERRIDE FROM ObsRingGeometry ###
    ### (geometry lives in primary index)
    #####################################

    def field_obs_ring_geometry_ring_radius1(self):
        return self._index_col('rings:minimum_ring_radius')

    def field_obs_ring_geometry_ring_radius2(self):
        return self._index_col('rings:maximum_ring_radius')

    def field_obs_ring_geometry_j2000_longitude1(self):
        return self._index_col('rings:minimum_inertial_ring_longitude')

    def field_obs_ring_geometry_j2000_longitude2(self):
        return self._index_col('rings:maximum_inertial_ring_longitude')

    def field_obs_ring_geometry_phase1(self):
        return self._index_col('rings:minimum_phase_angle')

    def field_obs_ring_geometry_phase2(self):
        return self._index_col('rings:maximum_phase_angle')

    def field_obs_ring_geometry_incidence1(self):
        return self._index_col('rings:mean_incidence_angle')

    def field_obs_ring_geometry_incidence2(self):
        return self.field_obs_ring_geometry_incidence1()

    def field_obs_ring_geometry_emission1(self):
        return self._index_col('rings:minimum_emission_angle')

    def field_obs_ring_geometry_emission2(self):
        return self._index_col('rings:maximum_emission_angle')

    def field_obs_ring_geometry_resolution1(self):
        return self._index_col('rings:minimum_radial_resolution')

    def field_obs_ring_geometry_resolution2(self):
        return self._index_col('rings:maximum_radial_resolution')

    def field_obs_ring_geometry_projected_radial_resolution1(self):
        return self.field_obs_ring_geometry_resolution1()

    def field_obs_ring_geometry_projected_radial_resolution2(self):
        return self.field_obs_ring_geometry_resolution2()

    def field_obs_ring_geometry_projected_long_resolution1(self):
        return self._index_col('rings:minimum_longitudinal_resolution')

    def field_obs_ring_geometry_projected_long_resolution2(self):
        return self._index_col('rings:maximum_longitudinal_resolution')


    ######################################
    ### OVERRIDE FROM ObsCassiniCommon ###
    ######################################

    def field_obs_mission_cassini_mission_phase_name(self):
        return self._create_mult(self._cassini_normalize_mission_phase_name())

    def field_obs_mission_cassini_spacecraft_clock_count1(self):
        raw = self._index_col('cassini:spacecraft_clock_start_count')
        if raw is None:
            return None
        try:
            return opus_support.parse_cassini_sclk(str(raw).strip())
        except Exception as e:
            self._log_nonrepeating_error(
                f'Unable to parse Cassini SCLK "{raw}": {e}')
            return None

    def field_obs_mission_cassini_spacecraft_clock_count2(self):
        raw = self._index_col('cassini:spacecraft_clock_stop_count')
        if raw is None:
            return None
        try:
            sc_cvt = opus_support.parse_cassini_sclk(str(raw).strip())
        except Exception as e:
            self._log_nonrepeating_error(
                f'Unable to parse Cassini SCLK "{raw}": {e}')
            return None
        sc1 = self.field_obs_mission_cassini_spacecraft_clock_count1()
        if sc1 is not None and sc_cvt < sc1:
            self._log_nonrepeating_warning(
                'spacecraft_clock_count1 and spacecraft_clock_count2 are in the '
                'wrong order - setting count2 to count1')
            return sc1
        return sc_cvt


    ###################################
    ### OVERRIDE FROM ObsTypeImage ###
    ###################################

    def field_obs_type_image_image_type_id(self):
        return self._create_mult('FRAM')

    def field_obs_type_image_duration(self):
        return self.field_obs_general_observation_duration()

    def field_obs_type_image_levels(self):
        return 4096


    ###################################
    ### OVERRIDE FROM ObsWavelength ###
    ###################################

    def field_obs_wavelength_wavelength1(self):
        camera, filter1, filter2 = 'N', 'CL1', 'CL2'
        central_wl, fwhm, _effective = _COISS_FILTER_WAVELENGTHS[
            (camera, filter1, filter2)]
        return (central_wl - fwhm / 2) / 1000.

    def field_obs_wavelength_wavelength2(self):
        camera, filter1, filter2 = 'N', 'CL1', 'CL2'
        central_wl, fwhm, _effective = _COISS_FILTER_WAVELENGTHS[
            (camera, filter1, filter2)]
        return (central_wl + fwhm / 2) / 1000.

    def field_obs_wavelength_wave_res1(self):
        return self._wave_res_from_full_bandwidth()

    def field_obs_wavelength_wave_res2(self):
        return self.field_obs_wavelength_wave_res1()

    def field_obs_wavelength_wave_no_res1(self):
        return self._wave_no_res_from_full_bandwidth()

    def field_obs_wavelength_wave_no_res2(self):
        return self.field_obs_wavelength_wave_no_res1()

    def field_obs_wavelength_polarization_type(self):
        return self._create_mult('NONE')


    ##############################################
    ### FIELD METHODS FOR obs_instrument_coiss #
    ##############################################

    def field_obs_instrument_coiss_opus_id(self):
        return self.opus_id

    def field_obs_instrument_coiss_bundle_id(self):
        return self.bundle

    def field_obs_instrument_coiss_instrument_id(self):
        return self.instrument_id

    def field_obs_instrument_coiss_data_conversion_type(self):
        return self._create_mult('12BIT')

    def field_obs_instrument_coiss_compression_type(self):
        return self._create_mult('LOSSLESS')

    def field_obs_instrument_coiss_gain_mode_id(self):
        return self._create_mult('12 ELECTRONS PER DN')

    def field_obs_instrument_coiss_image_observation_type(self):
        return self._create_mult('SCIENCE')

    def field_obs_instrument_coiss_missing_lines(self):
        return None

    def field_obs_instrument_coiss_shutter_mode_id(self):
        return self._create_mult('NACONLY')

    def field_obs_instrument_coiss_shutter_state_id(self):
        return self._create_mult('ENABLED')

    def field_obs_instrument_coiss_image_number(self):
        sc = self.field_obs_mission_cassini_spacecraft_clock_count1()
        if sc is None:
            return 0
        return int(sc)

    def field_obs_instrument_coiss_instrument_mode_id(self):
        return self._create_mult('FULL')

    def field_obs_instrument_coiss_target_desc(self):
        return self._create_mult('SATURN-FRING')

    def field_obs_instrument_coiss_combined_filter(self):
        return self._create_mult_keep_case('CLEAR')

    def field_obs_instrument_coiss_camera(self):
        return self._create_mult('N')
