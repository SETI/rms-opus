################################################################################
# obs_bundle_cassini_iss_fring_mosaics_rsfrench2025.py
#
# Defines the ObsBundleCassiniISSFRingMosaicsRSFrench2025 class, which encapsulates
# fields in the common, obs_mission_cassini, and obs_instrument_coiss tables for
# the PDS4 bundleset "cassini_iss_fring_mosaics_rsfrench2025". This class
# supports derived data from the cassini_iss_fring_mosaics_rsfrench2025 bundle.
################################################################################

from import_util import cached_tai_from_iso

from obs_cassini_common_pds4 import ObsCassiniCommonPDS4
from obs_volume_coiss_12xxx import _COISS_FILTER_WAVELENGTHS

NOTE_MAPPING = {
    'B': 'Background-subtracted mosaic is missing data due to insufficient radial extent.',
    'C': 'Some source images have corrupted or missing data.',
    'E': 'Some areas may be overexposed.',
    'M1': 'Multiple contiguous observations of the same inertial longitude range.',
    'M2': 'One of a pair of observations taken at inertial longitudes roughly 180 degrees apart.',
    'M3': 'Multiple observations of the same co-rotating longitude range but different inertial.',
    'M4': 'Observations of different co-rotating and different inertial longitudes.',
    'N': 'Non-inertial.',
    'O': 'Occultation.',
    'R': 'Follows one co-rotating longitude range with different inertial longitudes.',
}

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
        raw = self._index_col('notes')
        if raw is None: return ''

        raw_list = raw.split(';')
        note_list = [NOTE_MAPPING[note] for note in raw_list]
        return ' '.join(note_list)


    #####################################
    ### OVERRIDE FROM ObsRingGeometry ###
    #####################################

    def field_obs_ring_geometry_ring_radius1(self):
        return self._index_col('rings:minimum_ring_radius')

    def field_obs_ring_geometry_ring_radius2(self):
        return self._index_col('rings:maximum_ring_radius')

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
        return self._index_col('rings:minimum_inertial_ring_longitude')

    def field_obs_ring_geometry_ascending_longitude2(self):
        return self._index_col('rings:maximum_inertial_ring_longitude')

    # Phase angle: The angle between the point where incoming source photons
    # hit the ring , to the direction where outgoing photons to the observer
    def field_obs_ring_geometry_phase1(self):
        return self._index_col('rings:minimum_phase_angle')

    def field_obs_ring_geometry_phase2(self):
        return self._index_col('rings:maximum_phase_angle')

    # Source: star, observer: COISS
    # Incidence angle: the angle between the point where incoming source photons
    # hit the ring, to the north pole of the planet we're looking at (normal vector
    # on the surface of LIT side of the ring, same as source side), always between
    # 0 (parallel to north pole) to 90 (parallel to ring)
    def field_obs_ring_geometry_incidence1(self):
        return self._index_col('rings:mean_incidence_angle')

    def field_obs_ring_geometry_incidence2(self):
        return self.field_obs_ring_geometry_incidence1()

    # North based inc: the angle between the point where incoming source photons hit
    # the ring to the normal vector on the NORTH side of the ring. 0-90 when north
    # side of the ring is lit, and 90-180 when south side is lit.
    def field_obs_ring_geometry_north_based_incidence1(self):
        inc = self.field_obs_ring_geometry_incidence1()
        if self._is_ring_north_side_lit():
            return inc
        else:
            return 180. - inc

    def field_obs_ring_geometry_north_based_incidence2(self):
        return self.field_obs_ring_geometry_north_based_incidence1()

    # Emission angle: the angle between the normal vector on the LIT side, to the
    # direction where outgoing photons to the observer. 0-90 when observer is at the
    # lit side of the ring, and 90-180 when it's at the dark side.
    def field_obs_ring_geometry_emission1(self):
        return self._index_col('rings:minimum_emission_angle')

    def field_obs_ring_geometry_emission2(self):
        return self._index_col('rings:maximum_emission_angle')

    # North based ea: the angle between the normal vector on the NORTH side of the
    # ring, to the direction where outgoing photons to the observer. 0-90 when
    # observer is at the north side of the ring, and 90-180 when it's at the south
    # side.
    # If north side of the ring is lit, then north based emission angle is the same
    # as the emission angle. If south side of the ring is lit, north based emission
    # angle will be 180 - the emission angle.
    def field_obs_ring_geometry_north_based_emission1(self):
        ea = self.field_obs_ring_geometry_emission1()
        if self._is_ring_north_side_lit():
            return ea
        else:
            return 180. - ea

    def field_obs_ring_geometry_north_based_emission2(self):
        ea = self.field_obs_ring_geometry_emission2()
        if self._is_ring_north_side_lit():
            return ea
        else:
            return 180. - ea

    # Opening angle to solar: the angle between the ring surface to the direction
    # where incoming photons from the source. Positive if source is at the north
    # side of the ring , negative if it's at the south side.
    def field_obs_ring_geometry_solar_ring_opening_angle1(self):
        north_based_inc = self.field_obs_ring_geometry_north_based_incidence1()
        return 90. - north_based_inc

    def field_obs_ring_geometry_solar_ring_opening_angle2(self):
        north_based_inc = self.field_obs_ring_geometry_north_based_incidence2()
        return 90. - north_based_inc

    # Opening angle to observer: the angle between the ring surface to the direction
    # where outgoing photons to the observer. Positive if observer is at the north
    # side of the ring, negative if it's at the south side. (+/-)(90-emission_angle)
    def field_obs_ring_geometry_observer_ring_opening_angle1(self):
        north_based_ea = self.field_obs_ring_geometry_north_based_emission1()
        return 90. - north_based_ea

    def field_obs_ring_geometry_observer_ring_opening_angle2(self):
        north_based_ea = self.field_obs_ring_geometry_north_based_emission2()
        return 90. - north_based_ea

    def field_obs_ring_geometry_projected_radial_resolution1(self):
        return self._index_col('rings:minimum_radial_resolution')

    def field_obs_ring_geometry_projected_radial_resolution2(self):
        return self._index_col('rings:maximum_radial_resolution')

    def field_obs_ring_geometry_projected_long_resolution_angle1(self):
        return self._index_col('rings:minimum_longitudinal_resolution')

    def field_obs_ring_geometry_projected_long_resolution_angle2(self):
        return self._index_col('rings:maximum_longitudinal_resolution')

    # Equinox: 2009-08-11T01:40:08.914
    # After this time, north side of the ring is lit.
    # Before this time, south side of the ring is lit.
    def _is_ring_north_side_lit(self):
        start_time = cached_tai_from_iso(self.field_obs_general_time1())
        equinox_time = cached_tai_from_iso('2009-08-11T01:40:08.914')
        return start_time > equinox_time


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


    #################################################################################
    ### OVERRIDE FIELD METHODS FOR obs_instrument_coiss FROM ObsCassiniCommonPDS4 ###
    #################################################################################

    def field_obs_instrument_coiss_combined_filter(self):
        return self._create_mult_keep_case('CLEAR')

    def field_obs_instrument_coiss_camera(self):
        return self._create_mult(self.camera)
