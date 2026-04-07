################################################################################
# obs_bundle_cassini_iss_fring_mosaics_rsfrench2025.py
#
# Defines the ObsBundleCassiniISSFRingMosaicsRSFrench2025 class, which encapsulates
# fields in the common, obs_mission_cassini, and obs_instrument_coiss tables for
# the PDS4 bundleset "cassini_iss_fring_mosaics_rsfrench2025". This class
# supports derived data from the cassini_iss_fring_mosaics_rsfrench2025 bundle.
################################################################################

import import_util
import opus_support

from obs_cassini_common_pds4 import ObsCassiniCommonPDS4
from obs_volume_coiss_12xxx import _COISS_FILTER_WAVELENGTHS


class ObsBundleCassiniISSFRingMosaicsRSFrench2025(ObsCassiniCommonPDS4):
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

    @property
    def camera(self):
        return self._index_col('min_image_name')[-1].upper()

    def primary_filespec_from_index_row(self, row, convert_lbl=False,
                                        add_phase_from_inst=False):
        rel = row.get('file_spec')
        if rel is None:
            return None
        return self.bundle + '/' + str(rel).strip()


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
        return self._time_from_index()

    def field_obs_general_time2(self):
        return self._time2_from_index()


    ################################
    ### OVERRIDE FROM ObsPdsPDS4 ###
    ################################

    def field_obs_pds_note(self):
        return self._index_col('notes')


    #####################################
    ### OVERRIDE FROM ObsRingGeometry ###
    #####################################

    def field_obs_ring_geometry_ring_radius1(self):
        return self._index_col('rings:minimum_ring_radius')

    def field_obs_ring_geometry_ring_radius2(self):
        return self._index_col('rings:maximum_ring_radius')

    def field_obs_ring_geometry_j2000_longitude1(self):
        return self._index_col('rings:minimum_inertial_ring_longitude')

    def field_obs_ring_geometry_j2000_longitude2(self):
        return self._index_col('rings:maximum_inertial_ring_longitude')

    def field_obs_ring_geometry_ascending_longitude1(self):
        return self._index_col('rings:minimum_inertial_ring_longitude')

    def field_obs_ring_geometry_ascending_longitude2(self):
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

    def field_obs_ring_geometry_projected_long_resolution_angle1(self):
        return self._index_col('rings:minimum_longitudinal_resolution')

    def field_obs_ring_geometry_projected_long_resolution_angle2(self):
        return self._index_col('rings:maximum_longitudinal_resolution')


    ######################################
    ### OVERRIDE FROM ObsCassiniCommon ###
    ######################################

    def field_obs_mission_cassini_mission_phase_name(self):
        return self._create_mult(self._cassini_normalize_mission_phase_name())


    ###################################
    ### OVERRIDE FROM ObsTypeImage ###
    ###################################

    def field_obs_type_image_image_type_id(self):
        return self._create_mult('FRAM')

    def field_obs_type_image_duration(self):
        return self.field_obs_general_observation_duration()

    def field_obs_type_image_levels(self):
        return None

    def field_obs_type_image_greater_pixel_size(self):
        return 18000.

    def field_obs_type_image_lesser_pixel_size(self):
        return 401.


    ###################################
    ### OVERRIDE FROM ObsWavelength ###
    ###################################

    def field_obs_wavelength_wavelength1(self):
        filter1, filter2 = 'CL1', 'CL2'
        central_wl, fwhm, _effective = _COISS_FILTER_WAVELENGTHS[(self.camera, filter1, filter2)]
        return (central_wl - fwhm / 2) / 1000.

    def field_obs_wavelength_wavelength2(self):
        filter1, filter2 = 'CL1', 'CL2'
        central_wl, fwhm, _effective = _COISS_FILTER_WAVELENGTHS[(self.camera, filter1, filter2)]
        return (central_wl + fwhm / 2) / 1000.

    def field_obs_wavelength_wave_res1(self):
        return self._wave_res_from_full_bandwidth()

    def field_obs_wavelength_wave_res2(self):
        return self.field_obs_wavelength_wave_res1()

    def field_obs_wavelength_wave_no_res1(self):
        return self._wave_no_res_from_full_bandwidth()

    def field_obs_wavelength_wave_no_res2(self):
        return self.field_obs_wavelength_wave_no_res1()


    ##############################################
    ### FIELD METHODS FOR obs_instrument_coiss ###
    ##############################################

    def field_obs_instrument_coiss_opus_id(self):
        return self.opus_id

    def field_obs_instrument_coiss_bundle_id(self):
        return self.bundle

    def field_obs_instrument_coiss_instrument_id(self):
        return self.instrument_id

    def field_obs_instrument_coiss_data_conversion_type(self):
        return None

    def field_obs_instrument_coiss_compression_type(self):
        return None

    def field_obs_instrument_coiss_gain_mode_id(self):
        return None

    def field_obs_instrument_coiss_image_observation_type(self):
        return self._create_mult('SCIENCE')

    def field_obs_instrument_coiss_missing_lines(self):
        return None

    def field_obs_instrument_coiss_shutter_mode_id(self):
        return None

    def field_obs_instrument_coiss_shutter_state_id(self):
        return self._create_mult('Enabled')

    def field_obs_instrument_coiss_image_number(self):
        return None

    def field_obs_instrument_coiss_instrument_mode_id(self):
        return self._create_mult('FULL')

    def field_obs_instrument_coiss_target_desc(self):
        return None

    def field_obs_instrument_coiss_combined_filter(self):
        return self._create_mult_keep_case('CLEAR')

    def field_obs_instrument_coiss_camera(self):
        return self._create_mult(self.camera)
