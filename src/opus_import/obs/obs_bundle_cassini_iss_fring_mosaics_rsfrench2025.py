"""The obs class for the Cassini ISS F ring mosaics bundle.

PDS4 mosaics of Saturn's F ring assembled from Cassini ISS images. Each mosaic covers a
range of longitudes rather than a pointing, so its resolution columns are computed from
the F ring's own circumference.
"""

import math
from typing import cast

from opus_import.import_util import IndexRow
from opus_import.obs.field_types import FloatField, IntField, MultFieldRet, StrField
from opus_import.obs.obs_cassini_common_pds4 import ObsCassiniCommonPDS4

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
    """The Cassini ISS mosaics of Saturn's F ring.

    Its ``field_obs_*`` methods each fill the schema column their name ends in,
    declaring the type `opus_import.obs.field_types` gives that column.
    """

    #######################
    ### HELPER FUNCTIONS ###
    #######################


    def _camera(self) -> str:
        """Return which ISS camera took the images a mosaic was built from.

        Returns:
            ``'N'`` for the narrow-angle camera or ``'W'`` for the wide-angle one, read
            from
            the last letter of the first image's name.
        """
        return cast(str, self._index_col('min_image_name')[-1].upper())


    #############################
    ### OVERRIDE FROM ObsBase ###
    #############################

    @property
    def instrument_id(self) -> str | None:
        """The OPUS instrument id, ``COISS``."""
        return 'COISS'

    @property
    def primary_filespec(self) -> str | None:
        """The path of this mosaic's data file.

        Returns:
            The bundle-prefixed path, or None for an index row that names no file.
        """
        rel = self._index_col('file_spec')
        if rel is None:
            return None
        assert self.bundle is not None
        return cast(str | None, self.bundle + '/' + rel.strip())

    def primary_filespec_from_index_row(self, row: IndexRow,
                                        convert_lbl: bool = False,
                                        add_phase_from_row: bool = False,
                                        add_phase_from_inst: bool = False
                                        ) -> str | None:
        """Build a file specification from a row of this bundle's index.

        Parameters:
            row: The index row to read.
            convert_lbl: Ignored; the path already names the data file.
            add_phase_from_row: Ignored; this bundle has one observation per row.
            add_phase_from_inst: Ignored, for the same reason.

        Returns:
            The bundle-prefixed path, or None if the row names no file.
        """
        rel = row.get('file_spec')
        if rel is None:
            return None
        assert self.bundle is not None
        return self.bundle + '/' + str(rel).strip()

    def field_obs_pds_product_creation_time(self) -> FloatField:
        return self._time_from_index(column='product_creation_date')


    ################################
    ### OVERRIDE FROM ObsGeneral ###
    ################################

    def field_obs_general_planet_id(self) -> MultFieldRet:
        return self._create_mult('SAT')

    def _target_name(self) -> list[tuple[str | None, str | None]]:
        """The target of every observation in this bundle.

        Returns:
            Saturn's rings, which is what a F ring mosaic is of by construction.
        """
        return [('S RINGS', 'Saturn Rings')]

    def field_obs_general_quantity(self) -> MultFieldRet:
        return self._create_mult('REFLECT')

    def field_obs_general_observation_type(self) -> MultFieldRet:
        return self._create_mult('MOS')


    ################################
    ### OVERRIDE FROM ObsPdsPDS4 ###
    ################################

    def field_obs_pds_note(self) -> StrField:
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

    def field_obs_ring_geometry_ring_radius1(self) -> FloatField:
        return cast(FloatField, self._index_col('rings:minimum_ring_radius'))

    def field_obs_ring_geometry_ring_radius2(self) -> FloatField:
        return cast(FloatField, self._index_col('rings:maximum_ring_radius'))

    def field_obs_ring_geometry_j2000_longitude1(self) -> FloatField:
        if (self.field_obs_ring_geometry_ascending_longitude1() == 0 and
            self.field_obs_ring_geometry_ascending_longitude2() == 360):
            return 0
        return self._ascending_to_j2000(
            self.field_obs_ring_geometry_ascending_longitude1())

    def field_obs_ring_geometry_j2000_longitude2(self) -> FloatField:
        if (self.field_obs_ring_geometry_ascending_longitude1() == 0 and
            self.field_obs_ring_geometry_ascending_longitude2() == 360):
            return 360
        return self._ascending_to_j2000(
            self.field_obs_ring_geometry_ascending_longitude2())

    def field_obs_ring_geometry_ascending_longitude1(self) -> FloatField:
        return cast(FloatField, self._index_col('rings:minimum_inertial_ring_longitude'))

    def field_obs_ring_geometry_ascending_longitude2(self) -> FloatField:
        return cast(FloatField, self._index_col('rings:maximum_inertial_ring_longitude'))

    def field_obs_ring_geometry_phase1(self) -> FloatField:
        return cast(FloatField, self._index_col('rings:minimum_phase_angle'))

    def field_obs_ring_geometry_phase2(self) -> FloatField:
        return cast(FloatField, self._index_col('rings:maximum_phase_angle'))

    def field_obs_ring_geometry_incidence1(self) -> FloatField:
        return cast(FloatField, self._index_col('rings:mean_incidence_angle'))

    def field_obs_ring_geometry_incidence2(self) -> FloatField:
        return self.field_obs_ring_geometry_incidence1()

    def field_obs_ring_geometry_north_based_incidence1(self) -> FloatField:
        inc = self.field_obs_ring_geometry_incidence1()
        is_ring_north_side_lit = self._is_ring_north_side_lit()
        if is_ring_north_side_lit is None:
            return None
        elif is_ring_north_side_lit:
            return inc
        else:
            assert inc is not None
            return 180. - inc

    def field_obs_ring_geometry_north_based_incidence2(self) -> FloatField:
        return self.field_obs_ring_geometry_north_based_incidence1()

    def field_obs_ring_geometry_emission1(self) -> FloatField:
        return cast(FloatField, self._index_col('rings:minimum_emission_angle'))

    def field_obs_ring_geometry_emission2(self) -> FloatField:
        return cast(FloatField, self._index_col('rings:maximum_emission_angle'))

    def field_obs_ring_geometry_north_based_emission1(self) -> FloatField:
        ea1 = self.field_obs_ring_geometry_emission1()
        ea2 = self.field_obs_ring_geometry_emission2()
        is_ring_north_side_lit = self._is_ring_north_side_lit()
        if is_ring_north_side_lit is None:
            return None
        elif is_ring_north_side_lit:
            return ea1
        else:
            assert ea2 is not None
            return 180. - ea2

    def field_obs_ring_geometry_north_based_emission2(self) -> FloatField:
        ea1 = self.field_obs_ring_geometry_emission1()
        ea2 = self.field_obs_ring_geometry_emission2()
        is_ring_north_side_lit = self._is_ring_north_side_lit()
        if is_ring_north_side_lit is None:
            return None
        elif is_ring_north_side_lit:
            return ea2
        else:
            assert ea1 is not None
            return 180. - ea1

    def field_obs_ring_geometry_solar_ring_elevation1(self) -> FloatField:
        north_based_inc = self.field_obs_ring_geometry_north_based_incidence1()
        assert north_based_inc is not None
        return 90. - north_based_inc

    def field_obs_ring_geometry_solar_ring_elevation2(self) -> FloatField:
        north_based_inc = self.field_obs_ring_geometry_north_based_incidence2()
        assert north_based_inc is not None
        return 90. - north_based_inc

    def field_obs_ring_geometry_observer_ring_elevation1(self) -> FloatField:
        north_based_ea = self.field_obs_ring_geometry_north_based_emission2()
        assert north_based_ea is not None
        return 90. - north_based_ea

    def field_obs_ring_geometry_observer_ring_elevation2(self) -> FloatField:
        north_based_ea = self.field_obs_ring_geometry_north_based_emission1()
        assert north_based_ea is not None
        return 90. - north_based_ea

    def field_obs_ring_geometry_projected_radial_resolution1(self) -> FloatField:
        return cast(FloatField, self._index_col('rings:minimum_radial_resolution'))

    def field_obs_ring_geometry_projected_radial_resolution2(self) -> FloatField:
        return cast(FloatField, self._index_col('rings:maximum_radial_resolution'))

    def field_obs_ring_geometry_projected_long_resolution_angle1(self) -> FloatField:
        return cast(FloatField, self._index_col('rings:minimum_longitudinal_resolution'))

    def field_obs_ring_geometry_projected_long_resolution_angle2(self) -> FloatField:
        return cast(FloatField, self._index_col('rings:maximum_longitudinal_resolution'))

    # circumference * projected_long_resolution_angle / 360.
    def field_obs_ring_geometry_projected_long_resolution1(self) -> FloatField:
        angular_resolution1 = \
            self.field_obs_ring_geometry_projected_long_resolution_angle1()
        assert angular_resolution1 is not None
        return _F_RING_CIRCUMFERENCE * angular_resolution1 / 360.

    def field_obs_ring_geometry_projected_long_resolution2(self) -> FloatField:
        angular_resolution2 = \
            self.field_obs_ring_geometry_projected_long_resolution_angle2()
        assert angular_resolution2 is not None
        return _F_RING_CIRCUMFERENCE * angular_resolution2 / 360.


    ######################################
    ### OVERRIDE FROM ObsCassiniCommon ###
    ######################################

    def field_obs_mission_cassini_mission_phase_name(self) -> MultFieldRet:
        return self._create_mult(self._cassini_normalize_mission_phase_name())


    ##################################
    ### OVERRIDE FROM ObsTypeImage ###
    ##################################

    def field_obs_type_image_image_type_id(self) -> MultFieldRet:
        return self._create_mult('MOSAIC')

    def field_obs_type_image_duration(self) -> FloatField:
        return self.field_obs_general_observation_duration()

    def field_obs_type_image_levels(self) -> IntField:
        return None

    def field_obs_type_image_greater_pixel_size(self) -> IntField:
        return 18000

    def field_obs_type_image_lesser_pixel_size(self) -> IntField:
        return 401


    ###################################
    ### OVERRIDE FROM ObsWavelength ###
    ###################################

    def field_obs_wavelength_wavelength1(self) -> FloatField:
        filter1, filter2 = 'CL1', 'CL2'
        central_wl, fwhm, _ = self._coiss_wavelength_helper(self._camera(),
                                                            filter1, filter2)
        # _coiss_wavelength_helper reports a filter combination it does not describe
        # and returns Nones, which is a documented outcome rather than an invariant.
        if central_wl is None or fwhm is None:
            return None
        return (central_wl - fwhm / 2) / 1000.

    def field_obs_wavelength_wavelength2(self) -> FloatField:
        filter1, filter2 = 'CL1', 'CL2'
        central_wl, fwhm, _ = self._coiss_wavelength_helper(self._camera(),
                                                            filter1, filter2)
        # _coiss_wavelength_helper reports a filter combination it does not describe
        # and returns Nones, which is a documented outcome rather than an invariant.
        if central_wl is None or fwhm is None:
            return None
        return (central_wl + fwhm / 2) / 1000.

    def field_obs_wavelength_wave_res1(self) -> FloatField:
        return self._wave_res_from_full_bandwidth()

    def field_obs_wavelength_wave_res2(self) -> FloatField:
        return self.field_obs_wavelength_wave_res1()

    def field_obs_wavelength_wave_no_res1(self) -> FloatField:
        return self._wave_no_res_from_full_bandwidth()

    def field_obs_wavelength_wave_no_res2(self) -> FloatField:
        return self.field_obs_wavelength_wave_no_res1()


    #################################################################################
    ### OVERRIDE FIELD METHODS FOR obs_instrument_coiss FROM ObsCassiniCommonPDS4 ###
    #################################################################################

    def field_obs_instrument_coiss_combined_filter(self) -> MultFieldRet:
        return self._create_mult_keep_case('CLEAR')

    def field_obs_instrument_coiss_camera(self) -> MultFieldRet:
        return self._create_mult(self._camera())
