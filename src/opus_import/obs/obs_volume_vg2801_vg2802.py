"""The obs class for VG_2801 and VG_2802.

Voyager PPS and UVS radial ring profiles. These carry no geometry summary, so which face
of the rings the signal source was on is decided from the star and the planet and
checked against the observation's time.
"""

from typing import cast

from opus_import.obs.field_types import FloatField, MultFieldRet
from opus_import.obs.obs_volume_vg28xx import THRESHOLD_START_TIME_VG_AT_NORTH, ObsVolumeVG28xx


class ObsVolumeVG28xxVGPPSUVS(ObsVolumeVG28xx):
    ################################
    ### OVERRIDE FROM ObsGeneral ###
    ################################

    """What the VG_2801 and VG_2802 radial ring profiles share.

    Its ``field_obs_*`` methods each fill the schema column their name ends in,
    declaring the type `opus_import.obs.field_types` gives that column.
    """

    def field_obs_general_quantity(self) -> MultFieldRet:
        return self._create_mult('OPDEPTH')

    def field_obs_general_observation_type(self) -> MultFieldRet:
        return self._create_mult('OCC')

    def field_obs_general_right_asc1(self) -> FloatField:
        return self._prof_ra_dec_helper('supp_index_row', 'SIGNAL_SOURCE_NAME_1')[0]

    def field_obs_general_right_asc2(self) -> FloatField:
        return self._prof_ra_dec_helper('supp_index_row', 'SIGNAL_SOURCE_NAME_1')[1]

    def field_obs_general_declination1(self) -> FloatField:
        return self._prof_ra_dec_helper('supp_index_row', 'SIGNAL_SOURCE_NAME_1')[2]

    def field_obs_general_declination2(self) -> FloatField:
        return self._prof_ra_dec_helper('supp_index_row', 'SIGNAL_SOURCE_NAME_1')[3]


    ################################
    ### OVERRIDE FROM ObsProfile ###
    ################################

    def field_obs_profile_occ_type(self) -> MultFieldRet:
        return self._create_mult('STE')

    def field_obs_profile_occ_dir(self) -> MultFieldRet:
        return self._create_mult(self._index_col('RING_OCCULTATION_DIRECTION')[0])

    def field_obs_profile_body_occ_flag(self) -> MultFieldRet:
        return self._create_mult(self._supp_index_col('PLANETARY_OCCULTATION_FLAG'))

    def field_obs_profile_temporal_sampling(self) -> FloatField:
        return cast(FloatField, self._supp_index_col('TEMPORAL_SAMPLING_INTERVAL'))

    def field_obs_profile_quality_score(self) -> MultFieldRet:
        return self._create_mult('GOOD')

    def field_obs_profile_host(self) -> MultFieldRet:
        return self._create_mult(self._supp_index_col('RECEIVER_HOST_NAME').lower())


    #####################################
    ### OVERRIDE FROM ObsRingGeometry ###
    #####################################

    # In this volume,
    # Voyager is at north when:
    #     - Source is DELTA SCO (Target S RINGS)
    #     - Source is SIGMA SGR (Target U RINGS)
    # Voyager is south when:
    #     - Source is SIGMA SGR (Target N RINGS)
    #     - Source is BETA PER (Target U RINGS)
    def _is_voyager_at_north(self) -> bool:
        """Whether the signal source was on the north face of the rings.

        Which face is decided by the star and the planet rather than by geometry columns,
        because these profiles carry none. The observation's start time is checked against
        the intervals the answer holds over, and a disagreement is logged as an error.

        Returns:
            True if the source was north of the ring plane.
        """
        src_name = self._supp_index_col('SIGNAL_SOURCE_NAME_1')
        target_name = self._index_col('TARGET_NAME').upper().strip()

        start_time = self.field_obs_general_time1()

        is_at_north = (src_name == 'DELTA SCO' or
                       (src_name == 'SIGMA SGR' and target_name == 'U RINGS'))
        # Check if the start time matches the Voyager location
        if is_at_north:
            if (start_time > THRESHOLD_START_TIME_VG_AT_NORTH[4] or
                THRESHOLD_START_TIME_VG_AT_NORTH[1] > start_time >
                    THRESHOLD_START_TIME_VG_AT_NORTH[0] or
                THRESHOLD_START_TIME_VG_AT_NORTH[3] > start_time >
                    THRESHOLD_START_TIME_VG_AT_NORTH[2]):
                self._log_nonrepeating_error(
                    'Start time and Voyager N/S location do not match.')
        else:
            if (start_time <= THRESHOLD_START_TIME_VG_AT_NORTH[0] or
                THRESHOLD_START_TIME_VG_AT_NORTH[1] <= start_time <=
                    THRESHOLD_START_TIME_VG_AT_NORTH[2] or
                THRESHOLD_START_TIME_VG_AT_NORTH[3] <= start_time <=
                    THRESHOLD_START_TIME_VG_AT_NORTH[4]):
                self._log_nonrepeating_error(
                    'Start time and Voyager N/S location do not match.')
        return cast(bool, is_at_north)

    def _is_voyager_at_north_except_uranus(self) -> bool:
        """Whether the signal source was on the north face, counting Uranus's rings as south.

        Uranus's pole is tipped past the ecliptic, so an observation of its rings is
        north-facing by the ring plane's own reckoning and south-facing by the convention
        the other columns use. This is the second reckoning.

        Returns:
            True if the source was north of the ring plane under that convention.
        """
        src_name = self._supp_index_col('SIGNAL_SOURCE_NAME_1')
        target_name = self._index_col('TARGET_NAME').upper().strip()

        start_time = self.field_obs_general_time1()

        is_at_north = (src_name == 'DELTA SCO')
        # Check if the start time matches the Voyager location.
        if is_at_north or (src_name == 'SIGMA SGR' and target_name == 'U RINGS'):
            if (start_time > THRESHOLD_START_TIME_VG_AT_NORTH[4] or
                THRESHOLD_START_TIME_VG_AT_NORTH[1] > start_time >
                    THRESHOLD_START_TIME_VG_AT_NORTH[0] or
                THRESHOLD_START_TIME_VG_AT_NORTH[3] > start_time >
                    THRESHOLD_START_TIME_VG_AT_NORTH[2]):
                self._log_nonrepeating_error(
                    'Start time and Voyager N/S location do not match.')
        else:
            if (start_time <= THRESHOLD_START_TIME_VG_AT_NORTH[0] or
                THRESHOLD_START_TIME_VG_AT_NORTH[1] <= start_time <=
                    THRESHOLD_START_TIME_VG_AT_NORTH[2] or
                THRESHOLD_START_TIME_VG_AT_NORTH[3] <= start_time <=
                    THRESHOLD_START_TIME_VG_AT_NORTH[4]):
                self._log_nonrepeating_error(
                    'Start time and Voyager N/S location do not match.')
        return cast(bool, is_at_north)


    # Source is star, observer is Voyager
    # Source DELTA SCO is at south, observer Voyager is at north. Target: S ring.
    # Source SIGMA SGR is at south, observer Voyager is at north. Target: U ring.
    # Source SIGMA SGR is at north, observer Voyager is at south. Target: N ring.
    # Source BETA PER is at north, observer Voyager is at south. Target: U ring.

    # Ring elevation to Sun, same to opening angle except, it's positive if
    # source is at north side of Jupiter, Saturn, and Neptune, and south side of
    # Uranus. Negative if source is at south side of Jupiter, Saturn, and Neptune,
    # and north side of Uranus.
    def field_obs_ring_geometry_solar_ring_elevation1(self) -> FloatField:
        if self._is_voyager_at_north_except_uranus():
            incidence1 = self.field_obs_ring_geometry_incidence1()
            assert incidence1 is not None
            return incidence1 - 90.
        incidence2 = self.field_obs_ring_geometry_incidence2()
        assert incidence2 is not None
        return 90. - incidence2

    def field_obs_ring_geometry_solar_ring_elevation2(self) -> FloatField:
        if self._is_voyager_at_north_except_uranus():
            incidence2 = self.field_obs_ring_geometry_incidence2()
            assert incidence2 is not None
            return incidence2 - 90.
        incidence1 = self.field_obs_ring_geometry_incidence1()
        assert incidence1 is not None
        return 90. - incidence1

    # Ring elevation to observer, same to opening angle except, it's positive if
    # observer is at north side of Jupiter, Saturn, and Neptune, and south side of
    # Uranus. Negative if observer is at south side of Jupiter, Saturn, and Neptune,
    # and north side of Uranus.
    def field_obs_ring_geometry_observer_ring_elevation1(self) -> FloatField:
        if self._is_voyager_at_north_except_uranus():
            emission1 = self.field_obs_ring_geometry_emission1()
            assert emission1 is not None
            return emission1 - 90.
        emission2 = self.field_obs_ring_geometry_emission2()
        assert emission2 is not None
        return 90. - emission2

    def field_obs_ring_geometry_observer_ring_elevation2(self) -> FloatField:
        if self._is_voyager_at_north_except_uranus():
            emission1 = self.field_obs_ring_geometry_emission1()
            assert emission1 is not None
            return emission1 - 90.
        emission2 = self.field_obs_ring_geometry_emission2()
        assert emission2 is not None
        return 90. - emission2

    def field_obs_ring_geometry_phase1(self) -> FloatField:
        return 180.

    def field_obs_ring_geometry_phase2(self) -> FloatField:
        return 180.

    # Incidence angle: The angle between the point where the incoming source
    # photos hit the ring and the normal to the ring plane on the LIT side of
    # the ring. This is always between 0 (parallel to the normal vector) and 90
    # (parallel to the ring plane)
    # We would like to use emission angle to get both min/max of incidence angle.
    # Emission angle is 90-180 (dark side), so incidence angle is 180 - emission
    # angle.
    def field_obs_ring_geometry_incidence1(self) -> FloatField:
        inc = self._supp_index_col('INCIDENCE_ANGLE')
        max_ea = self._supp_index_col('MAXIMUM_EMISSION_ANGLE')
        cal_inc = 180 - max_ea
        if abs(cal_inc - inc) >= 0.005:
            self._log_nonrepeating_error(
                'The difference between incidence angle and 180-emission is > 0.005')
        return cast(FloatField, cal_inc)

    def field_obs_ring_geometry_incidence2(self) -> FloatField:
        inc = self._supp_index_col('INCIDENCE_ANGLE')
        max_ea = self._supp_index_col('MINIMUM_EMISSION_ANGLE')
        cal_inc = 180 - max_ea
        if abs(cal_inc - inc) >= 0.005:
            self._log_nonrepeating_error(
                'The difference between incidence angle and 180-emission is > 0.005')
        return cast(FloatField, cal_inc)

    # Emission angle: the angle between the normal vector on the LIT side, to the
    # direction where outgoing photons to the observer. 0-90 when observer is at the
    # lit side of the ring, and 90-180 when it's at the dark side.
    # Since observer is on the dark side, ea is between 90-180
    def field_obs_ring_geometry_emission1(self) -> FloatField:
        return cast(FloatField, self._supp_index_col('MINIMUM_EMISSION_ANGLE'))

    def field_obs_ring_geometry_emission2(self) -> FloatField:
        return cast(FloatField, self._supp_index_col('MAXIMUM_EMISSION_ANGLE'))

    # North based inc: the angle between the point where incoming source photons hit
    # the ring to the normal vector on the NORTH side of the ring. 0-90 when north
    # side of the ring is lit, and 90-180 when south side is lit.
    def field_obs_ring_geometry_north_based_incidence1(self) -> FloatField:
        if self._is_voyager_at_north():
            incidence2 = self.field_obs_ring_geometry_incidence2()
            assert incidence2 is not None
            return 180. - incidence2
        return self.field_obs_ring_geometry_incidence1()

    def field_obs_ring_geometry_north_based_incidence2(self) -> FloatField:
        if self._is_voyager_at_north():
            incidence1 = self.field_obs_ring_geometry_incidence1()
            assert incidence1 is not None
            return 180. - incidence1
        return self.field_obs_ring_geometry_incidence2()

    def field_obs_ring_geometry_north_based_emission1(self) -> FloatField:
        if self._is_voyager_at_north():
            emission2 = self.field_obs_ring_geometry_emission2()
            assert emission2 is not None
            return 180. - emission2
        return self.field_obs_ring_geometry_emission1()

    def field_obs_ring_geometry_north_based_emission2(self) -> FloatField:
        if self._is_voyager_at_north():
            emission1 = self.field_obs_ring_geometry_emission1()
            assert emission1 is not None
            return 180. - emission1
        return self.field_obs_ring_geometry_emission2()

    # Opening angle to Sun: the angle between the ring surface to the direction
    # where incoming photons from the source. Positive if source is at the north
    # side of the ring, negative if it's at the south side. In this case, source
    # is at the north side, so it's 90 - inc. For reference, if source is at the
    # south side, then oa is - (90 - inc).
    def field_obs_ring_geometry_solar_ring_opening_angle1(self) -> FloatField:
        if self._is_voyager_at_north():
            incidence1 = self.field_obs_ring_geometry_incidence1()
            assert incidence1 is not None
            return incidence1 - 90.
        incidence2 = self.field_obs_ring_geometry_incidence2()
        assert incidence2 is not None
        return 90. - incidence2

    def field_obs_ring_geometry_solar_ring_opening_angle2(self) -> FloatField:
        if self._is_voyager_at_north():
            incidence2 = self.field_obs_ring_geometry_incidence2()
            assert incidence2 is not None
            return incidence2 - 90.
        incidence1 = self.field_obs_ring_geometry_incidence1()
        assert incidence1 is not None
        return 90. - incidence1

    # Opening angle to observer: the angle between the ring surface to the direction
    # where outgoing photons to the observer. Positive if observer is at the north
    # side of the ring, negative if it's at the south side. If observer is at the
    # north side, it's ea - 90 (or 90 - inc). If observer is at the south side,
    # then oa is 90 - ea.
    def field_obs_ring_geometry_observer_ring_opening_angle1(self) -> FloatField:
        if self._is_voyager_at_north():
            emission1 = self.field_obs_ring_geometry_emission1()
            assert emission1 is not None
            return emission1 - 90.
        emission2 = self.field_obs_ring_geometry_emission2()
        assert emission2 is not None
        return 90. - emission2

    def field_obs_ring_geometry_observer_ring_opening_angle2(self) -> FloatField:
        if self._is_voyager_at_north():
            emission2 = self.field_obs_ring_geometry_emission2()
            assert emission2 is not None
            return emission2 - 90.
        emission1 = self.field_obs_ring_geometry_emission1()
        assert emission1 is not None
        return 90. - emission1


class ObsVolumeVG2801VGPPS(ObsVolumeVG28xxVGPPSUVS):
    #############################
    ### OVERRIDE FROM ObsBase ###
    #############################

    """The Voyager PPS radial ring profiles of VG_2801."""

    @property
    def instrument_id(self) -> str | None:
        """The OPUS instrument id, ``VGPPS``."""
        return 'VGPPS'


class ObsVolumeVG2802VGUVS(ObsVolumeVG28xxVGPPSUVS):
    #############################
    ### OVERRIDE FROM ObsBase ###
    #############################

    """The Voyager UVS radial ring profiles of VG_2802."""

    @property
    def instrument_id(self) -> str | None:
        """The OPUS instrument id, ``VGUVS``."""
        return 'VGUVS'
