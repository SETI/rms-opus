"""The obs class for EBROCC_xxxx.

ground-based stellar occultations of Saturn's rings from 1989. Six telescopes
contributed, so the instrument is per observation rather than per volume, and the
geometry is fixed for the whole event -- the Sun lit the north face and Earth viewed it,
which is what the module comment works through.
"""

from typing import cast

from opus_import.obs.field_types import FloatField, MultFieldRet
from opus_import.obs.obs_common_pds3 import ObsCommonPDS3

_EBROCC_INST_TO_PDS4_INST = {
    'ESO1MAPPH': 'eso-la_silla.1m04',
    'ESO22MAPPH': 'eso-la_silla.2m2',
    'IRTFURAC': 'irtf-maunakea.3m2',
    # TODOPDS4 "lick1m" is not a valid context product and will need to be
    # added to the PDS4 context products at some point, especially when EBROCC
    # gets ported to PDS4 some day. For now we just fake it.
    'LICK1MCCDC': 'lick.nickel',
    'MCD27MIIRAR': 'mcdonald.harlanjsmith_2m7',
    'PAL200CIRC': 'palomar.hale_5m08'
}


# The EBROCC_0001 volume only uses 28 SGR as a source, and all observations
# were taken on 1989-07-03. On this date:
# * 28 Sgr incidence angle was 64.627 on the south side
# * North-based incidence angle was 180-64.627 = 115.373
# * The north side of the rings were illuminated by the Sun
# * Earth was viewing the north side of the rings
# * Emission angle and north-based emission angle = incidence angle
# * Observer elevation = 90 - incidence angle

class ObsVolumeEBROCCxxxx(ObsCommonPDS3):
    #############################
    ### OVERRIDE FROM ObsBase ###
    #############################

    """The ground-based Saturn ring occultations of EBROCC_xxxx.

    Its ``field_obs_*`` methods each fill the schema column their name ends in,
    declaring the type `opus_import.obs.field_types` gives that column.
    """

    @property
    def instrument_id(self) -> str | None:
        """The OPUS instrument id, which differs per observation in these volumes.

        Returns:
            The telescope and instrument, named the way PDS4 does, or None before any
            observation has been read.
        """
        if self._metadata is None:
            # This happens during the create_tables phase
            return None
        inst = (self._supp_index_col('INSTRUMENT_HOST_ID') +
                self._supp_index_col('INSTRUMENT_ID'))
        return _EBROCC_INST_TO_PDS4_INST[inst]

    @property
    def inst_host_id(self) -> str:
        """The OPUS instrument host id, ``GB``."""
        return 'GB'

    @property
    def mission_id(self) -> str:
        """The OPUS mission id, ``GB``."""
        return 'GB'

    @property
    def primary_filespec(self) -> str | None:
        """The path of this occultation profile's data file.

        Computed from the primary index alone, for the reason
        `opus_import.obs.obs_cassini_common.ObsCassiniCommon.primary_filespec` gives.

        Returns:
            The volume-prefixed path.
        """
        # Note it's very important that this can be calculated using ONLY
        # the primary index, not the supplemental index!
        # This is because this (and the subsequent creation of opus_id) is used
        # to actually find the matching row in the supplemental index dictionary.
        # Format: "/DATA/ESO1M/ES1_EPD.LBL"
        filespec = self._index_col('FILE_SPECIFICATION_NAME')
        assert self.bundle is not None
        return cast(str | None, self.bundle + '/' + filespec)

    def convert_filespec_from_lbl(self, filespec: str) -> str:
        """Convert a ``.LBL`` file specification to the ``.TAB`` data file.

        Parameters:
            filespec: The path, relative to the holdings root.

        Returns:
            The same path with ``.LBL`` replaced by ``.TAB``, which is the file
            this bundle's observations are identified by.
        """
        return filespec.replace('.LBL', '.TAB')


    ################################
    ### OVERRIDE FROM ObsGeneral ###
    ################################

    def field_obs_general_right_asc1(self) -> FloatField:
        return self._prof_ra_dec_helper('index_label', 'STAR_NAME')[0]

    def field_obs_general_right_asc2(self) -> FloatField:
        return self._prof_ra_dec_helper('index_label', 'STAR_NAME')[1]

    def field_obs_general_declination1(self) -> FloatField:
        return self._prof_ra_dec_helper('index_label', 'STAR_NAME')[2]

    def field_obs_general_declination2(self) -> FloatField:
        return self._prof_ra_dec_helper('index_label', 'STAR_NAME')[3]

    def field_obs_general_planet_id(self) -> MultFieldRet:
        return self._create_mult('SAT')

    def _target_name(self) -> list[tuple[str | None, str | None]]:
        """The target of these observations.

        Returns:
            Saturn's rings, as a one-element list, or ``[(None, None)]`` if the label names
            something else -- which is logged as an error, since these volumes hold nothing
            but Saturn ring occultations.
        """
        target_name = self._index_label_col('TARGET_NAME')

        if target_name != 'S RINGS':
            self._log_nonrepeating_error(
                f'Ground-based mission targets "{target_name}" instead of "S RINGS"')

        target_name, target_info = self._get_target_info(target_name)
        if target_info is None:
            return [(None, None)]

        return [(target_name, target_info[2])]

    def field_obs_general_quantity(self) -> MultFieldRet:
        return self._create_mult('OPDEPTH')

    def field_obs_general_observation_type(self) -> MultFieldRet:
        return self._create_mult('OCC')


    ###################################
    ### OVERRIDE FROM ObsWavelength ###
    ###################################

    def field_obs_wavelength_wavelength1(self) -> FloatField:
        return cast(FloatField, self._supp_index_col('WAVELENGTH'))

    def field_obs_wavelength_wavelength2(self) -> FloatField:
        return cast(FloatField, self._supp_index_col('WAVELENGTH'))


    ################################
    ### OVERRIDE FROM ObsProfile ###
    ################################

    def field_obs_profile_occ_type(self) -> MultFieldRet:
        return self._create_mult('STE')

    def field_obs_profile_occ_dir(self) -> MultFieldRet:
        occ_dir = self._index_col('OCCULTATION_DIRECTION')
        if occ_dir in ('INGRESS', 'EGRESS', 'BOTH'):
            return self._create_mult(occ_dir[0])
        self._log_nonrepeating_error(f'Unknown OCCULTATION_DIRECTION "{occ_dir}"')
        return self._create_mult(None)

    def field_obs_profile_body_occ_flag(self) -> MultFieldRet:
        return self._create_mult(self._supp_index_col('PLANETARY_OCCULTATION_FLAG'))

    def field_obs_profile_quality_score(self) -> MultFieldRet:
        return self._create_mult('UNASSIGNED')

    def field_obs_profile_wl_band(self) -> MultFieldRet:
        wl = self._supp_index_col('WAVELENGTH') # microns
        if wl > 0.7:
            return self._create_mult('IR')
        if wl > 0.4:
            return self._create_mult('VIS')
        return self._create_mult('UV')

    def field_obs_profile_source(self) -> MultFieldRet:
        target_name, target_info = self._star_name_helper('index_label', 'STAR_NAME')
        if target_info is None:
            return self._create_mult(None)
        return self._create_mult(col_val=target_name, disp_name=target_info[2],
                                 grouping='Stars')

    def field_obs_profile_host(self) -> MultFieldRet:
        return self._create_mult(self.instrument_id)


    #####################################
    ### OVERRIDE FROM ObsRingGeometry ###
    #####################################

    def field_obs_ring_geometry_ring_radius1(self) -> FloatField:
        return cast(FloatField, self._supp_index_col('MINIMUM_RING_RADIUS'))

    def field_obs_ring_geometry_ring_radius2(self) -> FloatField:
        return cast(FloatField, self._supp_index_col('MAXIMUM_RING_RADIUS'))

    def field_obs_ring_geometry_projected_radial_resolution1(self) -> FloatField:
        return cast(FloatField, self._supp_index_col('RADIAL_RESOLUTION'))

    def field_obs_ring_geometry_projected_radial_resolution2(self) -> FloatField:
        return self.field_obs_ring_geometry_projected_radial_resolution1()

    def field_obs_ring_geometry_solar_ring_elevation1(self) -> FloatField:
        return cast(FloatField, self._supp_index_col('INCIDENCE_ANGLE')-90.)

    def field_obs_ring_geometry_solar_ring_elevation2(self) -> FloatField:
        return self.field_obs_ring_geometry_solar_ring_elevation1()

    def field_obs_ring_geometry_observer_ring_elevation1(self) -> FloatField:
        return cast(FloatField, 90.-self._supp_index_col('INCIDENCE_ANGLE'))

    def field_obs_ring_geometry_observer_ring_elevation2(self) -> FloatField:
        return self.field_obs_ring_geometry_observer_ring_elevation1()

    def field_obs_ring_geometry_phase1(self) -> FloatField:
        return 180.

    def field_obs_ring_geometry_phase2(self) -> FloatField:
        return 180.

    def field_obs_ring_geometry_incidence1(self) -> FloatField:
        return cast(FloatField, self._supp_index_col('INCIDENCE_ANGLE'))

    def field_obs_ring_geometry_incidence2(self) -> FloatField:
        return self.field_obs_ring_geometry_incidence1()

    def field_obs_ring_geometry_emission1(self) -> FloatField:
        return cast(FloatField, 180.-self._supp_index_col('INCIDENCE_ANGLE'))

    def field_obs_ring_geometry_emission2(self) -> FloatField:
        return self.field_obs_ring_geometry_emission1()

    def field_obs_ring_geometry_north_based_incidence1(self) -> FloatField:
        return cast(FloatField, 180.-self._supp_index_col('INCIDENCE_ANGLE'))

    def field_obs_ring_geometry_north_based_incidence2(self) -> FloatField:
        return self.field_obs_ring_geometry_north_based_incidence1()

    def field_obs_ring_geometry_north_based_emission1(self) -> FloatField:
        return cast(FloatField, self._supp_index_col('INCIDENCE_ANGLE'))

    def field_obs_ring_geometry_north_based_emission2(self) -> FloatField:
        return self.field_obs_ring_geometry_north_based_emission1()

    def field_obs_ring_geometry_ring_center_phase1(self) -> FloatField:
        return self.field_obs_ring_geometry_phase1()

    def field_obs_ring_geometry_ring_center_phase2(self) -> FloatField:
        return self.field_obs_ring_geometry_phase2()

    def field_obs_ring_geometry_ring_center_incidence1(self) -> FloatField:
        return self.field_obs_ring_geometry_incidence1()

    def field_obs_ring_geometry_ring_center_incidence2(self) -> FloatField:
        return self.field_obs_ring_geometry_incidence2()

    def field_obs_ring_geometry_ring_center_emission1(self) -> FloatField:
        return self.field_obs_ring_geometry_emission1()

    def field_obs_ring_geometry_ring_center_emission2(self) -> FloatField:
        return self.field_obs_ring_geometry_emission2()

    def field_obs_ring_geometry_ring_center_north_based_incidence1(self) -> FloatField:
        return self.field_obs_ring_geometry_north_based_incidence1()

    def field_obs_ring_geometry_ring_center_north_based_incidence2(self) -> FloatField:
        return self.field_obs_ring_geometry_north_based_incidence2()

    def field_obs_ring_geometry_ring_center_north_based_emission1(self) -> FloatField:
        return self.field_obs_ring_geometry_north_based_emission1()

    def field_obs_ring_geometry_ring_center_north_based_emission2(self) -> FloatField:
        return self.field_obs_ring_geometry_north_based_emission2()

    def field_obs_ring_geometry_solar_ring_opening_angle1(self) -> FloatField:
        return cast(FloatField, self._supp_index_col('INCIDENCE_ANGLE')-90.)

    def field_obs_ring_geometry_solar_ring_opening_angle2(self) -> FloatField:
        return self.field_obs_ring_geometry_solar_ring_opening_angle1()

    def field_obs_ring_geometry_observer_ring_opening_angle1(self) -> FloatField:
        return cast(FloatField, 90.-self._supp_index_col('INCIDENCE_ANGLE'))

    def field_obs_ring_geometry_observer_ring_opening_angle2(self) -> FloatField:
        return self.field_obs_ring_geometry_observer_ring_opening_angle1()

    def field_obs_ring_geometry_ring_intercept_time1(self) -> FloatField:
        return self._time_from_index(column='RING_EVENT_START')

    def field_obs_ring_geometry_ring_intercept_time2(self) -> FloatField:
        return self._time2_from_index(self.field_obs_ring_geometry_ring_intercept_time1(),
                                      'RING_EVENT_STOP')
