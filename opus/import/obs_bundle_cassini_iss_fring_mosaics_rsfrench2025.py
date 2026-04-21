################################################################################
# obs_bundle_cassini_iss_fring_mosaics_rsfrench2025.py
#
# Defines the ObsBundleCassiniISSFRingMosaicsRSFrench2025 class, which encapsulates
# fields in the common, obs_mission_cassini, and obs_instrument_coiss tables for
# the PDS4 bundleset "cassini_iss_fring_mosaics_rsfrench2025". This class
# supports derived data from the cassini_iss_fring_mosaics_rsfrench2025 bundle.
################################################################################

import math

from obs_cassini_common_pds4 import ObsCassiniCommonPDS4

_NOTE_MAPPING = {
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

_F_RING_CIRCUMFERENCE = 2 * math.pi * 140221.3

class ObsBundleCassiniISSFRingMosaicsRSFrench2025(ObsCassiniCommonPDS4):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


    #######################
    ### HELPER FUNCTIONS ###
    #######################

    def _camera(self):
        return self._index_col('min_image_name')[-1].upper()


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

    def field_obs_pds_product_creation_time(self):
        return self._time_from_index(column='product_creation_date')


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
        return self._create_mult('MOS')


    ################################
    ### OVERRIDE FROM ObsPdsPDS4 ###
    ################################

    def field_obs_pds_note(self):
        raw = self._index_col('notes')
        if raw is not None:
            raw = raw.strip()

        if not raw:
            return None

        note_list = []
        for note in [n.strip() for n in raw.split(';') if n.strip()]:
            if note not in _NOTE_MAPPING:
                self._log_nonrepeating_error(
                    f'Unknown F Ring note code {note!r} in notes field: {raw!r}')
            else:
                note_list.append(_NOTE_MAPPING[note])
        return ' '.join(note_list) if note_list else None


    #####################################
    ### OVERRIDE FROM ObsRingGeometry ###
    #####################################

    def field_obs_ring_geometry_ring_radius1(self):
        # minimum_core_radius
        return self._index_col('rings:minimum_ring_radius')

    def field_obs_ring_geometry_ring_radius2(self):
        # maximum_core_radius
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
        # minimum_longitude_ascending_node
        return self._index_col('rings:minimum_inertial_ring_longitude')

    def field_obs_ring_geometry_ascending_longitude2(self):
        # maximum_longitude_ascending_node
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
        is_ring_north_side_lit = self._is_ring_north_side_lit()
        if is_ring_north_side_lit is None:
            return None
        elif is_ring_north_side_lit:
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
        ea1 = self.field_obs_ring_geometry_emission1()
        ea2 = self.field_obs_ring_geometry_emission2()
        is_ring_north_side_lit = self._is_ring_north_side_lit()
        if is_ring_north_side_lit is None:
            return None
        elif is_ring_north_side_lit:
            return ea1
        else:
            return 180. - ea2

    def field_obs_ring_geometry_north_based_emission2(self):
        ea1 = self.field_obs_ring_geometry_emission1()
        ea2 = self.field_obs_ring_geometry_emission2()
        is_ring_north_side_lit = self._is_ring_north_side_lit()
        if is_ring_north_side_lit is None:
            return None
        elif is_ring_north_side_lit:
            return ea2
        else:
            return 180. - ea1

    # Ring elevation to solar, the angle between the ring surface (intercept point) and the
    # direction where incoming photons from the source. It's positive if source is at north side
    # of Jupiter, Saturn, and Neptune, and south side of Uranus. Negative if source is at south side
    # of Jupiter, Saturn, and Neptune, and north side of Uranus.
    # In this bundle, we target Saturn.
    def field_obs_ring_geometry_solar_ring_elevation1(self):
        north_based_inc = self.field_obs_ring_geometry_north_based_incidence1()
        return 90. - north_based_inc

    def field_obs_ring_geometry_solar_ring_elevation2(self):
        north_based_inc = self.field_obs_ring_geometry_north_based_incidence2()
        return 90. - north_based_inc

    # Ring elevation to observer, the angle between the ring surface (intercept point) and the
    # direction of outgoing photons to the observer. It's positive if observer is at north side
    # of Saturn. Negative if observer is at south side of Saturn.
    def field_obs_ring_geometry_observer_ring_elevation1(self):
        north_based_ea = self.field_obs_ring_geometry_north_based_emission2()
        return 90. - north_based_ea

    def field_obs_ring_geometry_observer_ring_elevation2(self):
        north_based_ea = self.field_obs_ring_geometry_north_based_emission1()
        return 90. - north_based_ea

    def field_obs_ring_geometry_projected_radial_resolution1(self):
        return self._index_col('rings:minimum_radial_resolution')

    def field_obs_ring_geometry_projected_radial_resolution2(self):
        return self._index_col('rings:maximum_radial_resolution')

    def field_obs_ring_geometry_projected_long_resolution_angle1(self):
        return self._index_col('rings:minimum_longitudinal_resolution')

    def field_obs_ring_geometry_projected_long_resolution_angle2(self):
        return self._index_col('rings:maximum_longitudinal_resolution')

    # circumference * projected_long_resolution_angle / 360.
    def field_obs_ring_geometry_projected_long_resolution1(self):
        angular_resolution1 = self.field_obs_ring_geometry_projected_long_resolution_angle1()
        return _F_RING_CIRCUMFERENCE * angular_resolution1 / 360.

    def field_obs_ring_geometry_projected_long_resolution2(self):
        angular_resolution2 = self.field_obs_ring_geometry_projected_long_resolution_angle2()
        return _F_RING_CIRCUMFERENCE * angular_resolution2 / 360.


    ######################################
    ### OVERRIDE FROM ObsCassiniCommon ###
    ######################################

    def field_obs_mission_cassini_mission_phase_name(self):
        return self._create_mult(self._cassini_normalize_mission_phase_name())


    ##################################
    ### OVERRIDE FROM ObsTypeImage ###
    ##################################

    def field_obs_type_image_image_type_id(self):
        return self._create_mult('MOSAIC')

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
        central_wl, fwhm, _ = self._coiss_wavelength_helper(self._camera(), filter1, filter2)
        return (central_wl - fwhm / 2) / 1000.

    def field_obs_wavelength_wavelength2(self):
        filter1, filter2 = 'CL1', 'CL2'
        central_wl, fwhm, _ = self._coiss_wavelength_helper(self._camera(), filter1, filter2)
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
        return self._create_mult(self._camera())
