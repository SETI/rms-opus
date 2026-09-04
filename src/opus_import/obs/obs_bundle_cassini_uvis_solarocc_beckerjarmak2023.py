"""The obs class for the Cassini UVIS solar occultation bundle.

PDS4 profiles of Saturn's rings from solar rather than stellar occultations. The angles
are given relative to the lit face of the rings, which changed sides at Saturn's 2009
equinox, so they are converted to north-based ones.
"""

from typing import cast

from opus_import.obs.field_types import FloatField, IntField, MultFieldRet, StrField
from opus_import.obs.obs_bundle_occ_common import ObsBundleOccCommon
from opus_import.obs.obs_cassini_common_pds4 import ObsCassiniCommonPDS4


class ObsBundleCassiniUvisSolarOccBeckerJarmak(ObsBundleOccCommon, ObsCassiniCommonPDS4):
    """The Cassini UVIS solar occultation profiles of Saturn's rings.

    Its ``field_obs_*`` methods each fill the schema column their name ends in,
    declaring the type `opus_import.obs.field_types` gives that column.
    """

    #############################
    ### OVERRIDE FROM ObsBase ###
    #############################

    @property
    def instrument_id(self) -> str | None:
        """The OPUS instrument id, ``COUVIS``."""
        return 'COUVIS'

    ################################
    ### OVERRIDE FROM ObsGeneral ###
    ################################

    # Note the RA and Dec are returned as None. Although they could be computed, doing so
    # would require spacecraft attitude and ephemeris, and is further complicated by the
    # Sun being an extended source that moves relative to the spacecraft. More importantly,
    # RA and Dec are not useful for occultations anyway, which rely on planet-centric
    # geometry instead.

    def field_obs_general_planet_id(self) -> MultFieldRet:
        return self._create_mult('SAT')

    def _target_name(self) -> list[tuple[str | None, str | None]]:
        """The target of every observation in this bundle.

        Returns:
            Saturn's rings, which is what a ring occultation is of by construction.
        """
        return [('S RINGS', 'Saturn Rings')]

    ################################
    ### OVERRIDE FROM ObsProfile ###
    ################################

    def field_obs_profile_occ_type(self) -> MultFieldRet:
        return self._create_mult('SOL')

    def field_obs_profile_source(self) -> MultFieldRet:
        return self._create_mult('Sun')

    def field_obs_profile_host(self) -> MultFieldRet:
        return self._create_mult('cassini')

    def field_obs_profile_temporal_sampling(self) -> FloatField:
        return cast(FloatField, self._index_col('rings:temporal_sampling'))  # sec

    def field_obs_profile_wl_band(self) -> MultFieldRet:
        return self._create_mult('UV')

    def field_obs_profile_occ_dir(self) -> MultFieldRet:
        occ_dir = self._index_col('rings:ring_profile_direction')
        if occ_dir is None:
            occ_dir = self._index_col('rings:time_series_direction')
        if occ_dir is None:
            self._log_nonrepeating_error(
                '"rings:ring_profile_direction" and "rings:time_series_direction" are missing'
            )
            return self._create_mult(None)
        occ_dir = occ_dir.upper()
        if occ_dir in ('INGRESS', 'EGRESS', 'BOTH'):
            return self._create_mult(occ_dir[0])
        self._log_nonrepeating_error(f'Unknown profile direction "{occ_dir}"')
        return self._create_mult(None)

    def field_obs_profile_body_occ_flag(self) -> MultFieldRet:
        return self._create_mult(self._index_col('rings:planetary_occultation_flag'))

    def field_obs_profile_quality_score(self) -> MultFieldRet:
        return self._create_mult(self._index_col('rings:data_quality_score'))

    # TODO: Investigate further and fix if necessary.
    # co-uvis-occ-2016-269-sun-i has -999, needs to be handled correctly.
    def field_obs_profile_optical_depth1(self) -> FloatField:
        ret = self._index_col('rings:lowest_detectable_normal_optical_depth')
        return cast(FloatField, ret)

    # co-uvis-occ-2016-269-sun-i has -999, needs to be handled correctly.
    def field_obs_profile_optical_depth2(self) -> FloatField:
        ret = self._index_col('rings:highest_detectable_normal_optical_depth')
        return cast(FloatField, ret)

    #####################################
    ### OVERRIDE FROM ObsRingGeometry ###
    #####################################

    # The solar ring elevation, observer ring elevation, phase, incidence angle, and
    # emission angles for Becker/Jarmak are calculated in obs_bundle_occ_common.py.
    # However, the north-based fields are specific to planet and geometry:

    def _north_based_angle_helper(self) -> tuple[FloatField, FloatField]:
        # Work out north-based incidence angles based on date of Saturnian equinox
        # (when the sun was illuminating the north side of the rings).

        """Convert this observation's incidence and emission angles to north-based ones.

        The bundle's own index gives them relative to the lit face of the rings, which
        changed sides at Saturn's 2009 equinox; OPUS stores them relative to north, so an
        observation after the equinox is taken as given and one before it is reflected.

        Returns:
            The north-based incidence and emission angles in degrees, or ``(None, None)``
            if the observation has no start time or either angle is missing.
        """
        inc = self.field_obs_ring_geometry_incidence1()
        em = self.field_obs_ring_geometry_emission1()

        # Observation ET time (float seconds)
        time1 = self.field_obs_general_time1()  # pds:start_date_time converted to ET
        if time1 is None:
            return (None, None)

        # Before equinox ==> south side lit ==> flip to north-based
        if not self._is_ring_north_side_lit():
            north_inc = 180.0 - inc if inc is not None else None
            north_em = 180.0 - em if em is not None else None
        else:
            # On/after equinox ==> north side lit (no change)
            north_inc = inc
            north_em = em

        return (north_inc, north_em)

    def field_obs_ring_geometry_north_based_incidence1(self) -> FloatField:
        return self._north_based_angle_helper()[0]

    def field_obs_ring_geometry_north_based_incidence2(self) -> FloatField:
        return self.field_obs_ring_geometry_north_based_incidence1()

    def field_obs_ring_geometry_north_based_emission1(self) -> FloatField:
        return self._north_based_angle_helper()[1]

    def field_obs_ring_geometry_north_based_emission2(self) -> FloatField:
        return self.field_obs_ring_geometry_north_based_emission1()

    # TODO: investigate the following. Would be -rings:observed_ring_elevation, but that should
    # become negative after 2009 and doesn't, so there may be errors in the Becker/Jarmak labels
    # for rings:observed_ring_elevation
    # def field_obs_ring_geometry_solar_ring_opening_angle1(self):
    #     return (90.0 - self.field_obs_ring_geometry_north_based_incidence1())
    # def field_obs_ring_geometry_observer_ring_opening_angle1(self):
    #     return (90.0 + self.field_obs_ring_geometry_north_based_incidence1())
    # This crashes so using same method as Uranus Occs for now (below).

    def field_obs_ring_geometry_solar_ring_opening_angle1(self) -> FloatField:
        oa = self._index_col('rings:observed_ring_elevation')
        if oa is not None:
            oa = -oa
        return cast(FloatField, oa)

    def field_obs_ring_geometry_solar_ring_opening_angle2(self) -> FloatField:
        return self.field_obs_ring_geometry_solar_ring_opening_angle1()

    def field_obs_ring_geometry_observer_ring_opening_angle1(self) -> FloatField:
        return cast(FloatField, self._index_col('rings:observed_ring_elevation'))

    def field_obs_ring_geometry_observer_ring_opening_angle2(self) -> FloatField:
        return self.field_obs_ring_geometry_observer_ring_opening_angle1()

    ######################################
    ### OVERRIDE FROM ObsCassiniCommon ###
    ######################################

    def field_obs_mission_cassini_obs_name(self) -> StrField:
        return cast(StrField, self._some_index_col('OBSERVATION_ID'))

    def field_obs_mission_cassini_mission_phase_name(self) -> MultFieldRet:
        return self._create_mult(self._cassini_normalize_mission_phase_name())

    ###############################################
    ### FIELD METHODS FOR obs_instrument_couvis ###
    ###############################################

    def field_obs_instrument_couvis_opus_id(self) -> StrField:
        return self.opus_id

    def field_obs_instrument_couvis_bundle_id(self) -> StrField:
        return self.bundle

    def field_obs_instrument_couvis_observation_type(self) -> MultFieldRet:
        return self._create_mult('NONE')

    def field_obs_instrument_couvis_integration_duration(self) -> FloatField:
        return self.field_obs_profile_temporal_sampling()

    def field_obs_instrument_couvis_compression_type(self) -> MultFieldRet:
        comp_type = 'SQRT_9'  # All BeckerJarmak observations use this compression type.
        return self._create_mult_keep_case(comp_type)

    def field_obs_instrument_couvis_occultation_port_state(self) -> MultFieldRet:
        return self._create_mult('OPEN')

    def field_obs_instrument_couvis_slit_state(self) -> MultFieldRet:
        return self._create_mult('OCCULTATION')

    def field_obs_instrument_couvis_test_pulse_state(self) -> MultFieldRet:
        return self._create_mult('OFF')

    def field_obs_instrument_couvis_dwell_time(self) -> MultFieldRet:
        return self._create_mult(None)

    def field_obs_instrument_couvis_channel(self) -> MultFieldRet:
        return self._create_mult_keep_case('EUV')

    def field_obs_instrument_couvis_band1(self) -> IntField:
        return None

    def field_obs_instrument_couvis_band2(self) -> IntField:
        return None

    def field_obs_instrument_couvis_band_bin(self) -> IntField:
        return None

    def field_obs_instrument_couvis_line1(self) -> IntField:
        return None

    def field_obs_instrument_couvis_line2(self) -> IntField:
        return None

    def field_obs_instrument_couvis_line_bin(self) -> IntField:
        return None

    def field_obs_instrument_couvis_samples(self) -> IntField:
        return None
