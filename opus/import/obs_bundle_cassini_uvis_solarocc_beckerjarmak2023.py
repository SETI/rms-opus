################################################################################
# obs_bundle_cassini_uvis_solarocc_beckerjarmak2023.py
#
# Defines the ObsBundleCassiniUvisSolarOccBeckerJarmak class, which encapsulates
# fields in the common, common occultation, obs_mission_cassini, and
# obs_instrument_couvis tables for COUVIS solar occultations. This class
# supports derived data from UVIS EUV archived in the
# cassini_uvis_solarocc_beckerjarmak2023 bundle.
################################################################################

from import_util import cached_tai_from_iso
from obs_bundle_occ_common import ObsBundleOccCommon
from obs_cassini_common_pds4 import ObsCassiniCommonPDS4

SATURN_EQUINOX_TAI = cached_tai_from_iso("2009-08-11T00:00:00.000")

class ObsBundleCassiniUvisSolarOccBeckerJarmak(ObsBundleOccCommon, ObsCassiniCommonPDS4):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


    #############################
    ### OVERRIDE FROM ObsBase ###
    #############################

    @property
    def instrument_id(self):
        return 'COUVIS'


    ################################
    ### OVERRIDE FROM ObsGeneral ###
    ################################

    # Note the RA and Dec are returned as None. Although they could be computed, doing so
    # would require spacecraft attitude and ephemeris, and is further complicated by the
    # Sun being an extended source that moves relative to the spacecraft. More importantly,
    # RA and Dec are not useful for occultations anyway, which rely on planet-centric
    # geometry instead.

    def field_obs_general_planet_id(self):
        return self._create_mult('SAT')

    def _target_name(self):
        return [('S RINGS', 'Saturn Rings')]


    ################################
    ### OVERRIDE FROM ObsProfile ###
    ################################

    def field_obs_profile_occ_type(self):
        return self._create_mult('SOL')

    def field_obs_profile_source(self):
        return self._create_mult('Sun')

    def field_obs_profile_host(self):
        return self._create_mult('cassini')

    def field_obs_profile_temporal_sampling(self):
        return self._index_col('rings:temporal_sampling') # sec

    def field_obs_profile_wl_band(self):
        return self._create_mult('UV')


    #####################################
    ### OVERRIDE FROM ObsRingGeometry ###
    #####################################

    # The solar ring elevation, observer ring elevation, phase, incidence angle, and
    # emission angles for Becker/Jarmak are calculated in obs_bundle_occ_common.py.
    # However, the north-based fields are specific to planet and geometry:

    def _north_based_angle_helper(self):
        # Work out north-based incidence angles based on date of Saturnian equinox
        # (when the sun was illuminating the north side of the rings).

        inc = self.field_obs_ring_geometry_incidence1()
        em  = self.field_obs_ring_geometry_emission1()

        # Observation ET time (float seconds)
        time1 = self.field_obs_general_time1() # pds:start_date_time converted to ET
        if time1 is None:
            return (None, None)

        # Before equinox ==> south side lit ==> flip to north-based
        if time1 < SATURN_EQUINOX_TAI:
            north_inc = 180.0 - inc if inc is not None else None
            north_em  = 180.0 - em if em is not None else None
        else:
            # On/after equinox ==> north side lit (no change)
            north_inc = inc
            north_em  = em

        return (north_inc, north_em)

    def field_obs_ring_geometry_north_based_incidence1(self):
        return self._north_based_angle_helper()[0]

    def field_obs_ring_geometry_north_based_incidence2(self):
        return self.field_obs_ring_geometry_north_based_incidence1()

    def field_obs_ring_geometry_north_based_emission1(self):
        return self._north_based_angle_helper()[1]

    def field_obs_ring_geometry_north_based_emission2(self):
        return self.field_obs_ring_geometry_north_based_emission1()

    # TODO: investigate the following. Would be -rings:observed_ring_elevation, but that should
    # become negative after 2009 and doesn't, so there may be errors in the Becker/Jarmak labels
    # for rings:observed_ring_elevation
    # def field_obs_ring_geometry_solar_ring_opening_angle1(self):
    #     return (90.0 - self.field_obs_ring_geometry_north_based_incidence1())
    # def field_obs_ring_geometry_observer_ring_opening_angle1(self):
    #     return (90.0 + self.field_obs_ring_geometry_north_based_incidence1())
    # This crashes so using same method as Uranus Occs for now (below).

    def field_obs_ring_geometry_solar_ring_opening_angle1(self):
        oa = self._index_col('rings:observed_ring_elevation')
        if oa is not None:
            oa = -oa
        return oa

    def field_obs_ring_geometry_solar_ring_opening_angle2(self):
        return self.field_obs_ring_geometry_solar_ring_opening_angle1()

    def field_obs_ring_geometry_observer_ring_opening_angle1(self):
        return self._index_col('rings:observed_ring_elevation')

    def field_obs_ring_geometry_observer_ring_opening_angle2(self):
        return self.field_obs_ring_geometry_observer_ring_opening_angle1()


    ######################################
    ### OVERRIDE FROM ObsCassiniCommon ###
    ######################################

    def field_obs_mission_cassini_mission_phase_name(self):
        return self._create_mult(self._cassini_normalize_mission_phase_name())


    ###############################################
    ### FIELD METHODS FOR obs_instrument_couvis ###
    ###############################################

    def field_obs_instrument_couvis_opus_id(self):
        return self.opus_id

    def field_obs_instrument_couvis_bundle_id(self):
        return self.bundle

    def field_obs_instrument_couvis_instrument_id(self):
        return self.instrument_id

    def field_obs_instrument_couvis_observation_type(self):
        return self._create_mult('NONE')

    def field_obs_instrument_couvis_integration_duration(self):
        return self.field_obs_profile_temporal_sampling()

    def field_obs_instrument_couvis_compression_type(self):
        comp_type = "SQRT_9" # All BeckerJarmak observations use this compression type.
        return self._create_mult_keep_case(comp_type)

    def field_obs_instrument_couvis_occultation_port_state(self):
        return self._create_mult('OPEN')

    def field_obs_instrument_couvis_slit_state(self):
        return self._create_mult('OCCULTATION')

    def field_obs_instrument_couvis_test_pulse_state(self):
        return self._create_mult('OFF')

    def field_obs_instrument_couvis_dwell_time(self):
        return self._create_mult(None)

    def field_obs_instrument_couvis_channel(self):
        return self._create_mult_keep_case('EUV')

    def field_obs_instrument_couvis_band1(self):
        return None

    def field_obs_instrument_couvis_band2(self):
        return None

    def field_obs_instrument_couvis_band_bin(self):
        return None

    def field_obs_instrument_couvis_line1(self):
        return None

    def field_obs_instrument_couvis_line2(self):
        return None

    def field_obs_instrument_couvis_line_bin(self):
        return None

    def field_obs_instrument_couvis_samples(self):
        return None
