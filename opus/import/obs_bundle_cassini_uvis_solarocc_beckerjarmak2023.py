################################################################################
# obs_bundle_cassini_uvis_solarocc_beckerjarmak2023.py
#
# Defines the ObsBundleCassiniUvisSolarOccBeckerJarmak class, which encapsulates
# fields in the common, common occultation, obs_mission_cassini, and obs_instrument_couvis
# tables for COUVIS solar occultations. This class supports derived data from UVIS EUV
# archived in cassini_uvis_solarocc_beckerjarmak2023.
################################################################################

from datetime import datetime, date
from obs_bundle_occ_common import ObsBundleOccCommon
# MJTM: since there is no PDS4 Cassini Class, use PDS3 one for the moment
from obs_volume_cassini_common import ObsVolumeCassiniCommon

class ObsBundleCassiniUvisSolarOccBeckerJarmak(ObsBundleOccCommon, ObsVolumeCassiniCommon):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _inst_name(self):
        return 'Cassini UVIS'


    #############################
    ### OVERRIDE FROM ObsBase ###
    #############################

    @property
    def instrument_id(self):
        return 'COUVIS'


    ################################
    ### OVERRIDE FROM ObsGeneral ###
    ################################

    # Since the RA and dec of th Sun (not a point source) moves relative to the spacecraft (unlike distant stars),
    # use None, i.e. don't override obs_profile.py's _prof_ra_dec_helper()

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

    def field_obs_ring_geometry_projected_radial_resolution1(self):
        return None

    def field_obs_ring_geometry_projected_radial_resolution2(self):
        return None

    # The solar ring elevation, observer ring elevation, phase, incidence angle, and
    # emission angles for Becker/Jarmak are calculated in obs_bundle_occ_common.py.
    # However, the north-based fields are specific to planet and geometry:

    def _north_based_angle_helper(self):
        # Work out north-based incidence angles based on date of Saturnian equinox
        # (when the sun was illuminating the north side of the rings).

        inc = self.field_obs_ring_geometry_incidence1() # from index table
        em = self.field_obs_ring_geometry_emission1()

        # Get the ISO timestamp string from the index
        iso = self._index_col('pds:start_date_time')
        if iso is None:
            return (None, None)

        # Convert to datetime - fromisoformat() doesn’t accept 'Z' for UTC.
        obs_dt = datetime.fromisoformat(iso.replace('Z', '+00:00')) 
        obs_date = obs_dt.date() # Don't need HH:MM:SS

        saturn_equinox = date(2009, 8, 11)

        if obs_date < saturn_equinox:
            # Before equinox ==> south side lit, so flip for north-based
            return (180.0 - inc, 180.0 - em)
        else:
            # On/after equinox ==> north side lit (no change)
            return (inc, em)

    def field_obs_ring_geometry_north_based_incidence1(self):
        return self._north_based_angle_helper()[0]

    def field_obs_ring_geometry_north_based_incidence2(self):
        return self.field_obs_ring_geometry_north_based_incidence1()

    def field_obs_ring_geometry_north_based_emission1(self):
        return self._north_based_angle_helper()[1]

    def field_obs_ring_geometry_north_based_emission2(self):
        return self.field_obs_ring_geometry_north_based_emission1()

    # Would be -rings:observed_ring_elevation, but that should become negative after 2009
    # and doesn't, so there may be errors in the Becker/Jarmak labels for
    # rings:observed_ring_elevation
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


    #############################################
    ### OVERRIDE FROM ObsVolumeCassiniCommon
    ### (analogous to obs_volume_couvis_8xxx) ###
    #############################################

    # Haven't yet converted the SCLK methods from PDS3 to PDS4.
    # The Becker/Jarmak index file is currently missing SCLK counts.

    # def field_obs_mission_cassini_spacecraft_clock_count1(self):
    #     sc = self._supp_index_col('SPACECRAFT_CLOCK_START_COUNT')
    #     if sc == 'UNK':
    #         return None
    #     try:
    #         sc_cvt = opus_support.parse_cassini_sclk(sc)
    #     except Exception as e:
    #         self._log_nonrepeating_error(f'Unable to parse Cassini SCLK "{sc}": {e}')
    #         return None
    #     return sc_cvt

    # def field_obs_mission_cassini_spacecraft_clock_count2(self):
    #     sc = self._supp_index_col('SPACECRAFT_CLOCK_STOP_COUNT')
    #     if sc == 'UNK':
    #         return None
    #     try:
    #         sc_cvt = opus_support.parse_cassini_sclk(sc)
    #     except Exception as e:
    #         self._log_nonrepeating_error(f'Unable to parse Cassini SCLK "{sc}": {e}')
    #         return None

    #     sc1 = self.field_obs_mission_cassini_spacecraft_clock_count1()
    #     if sc1 is not None and sc_cvt < sc1:
    #         self._log_nonrepeating_warning(
    #             f'spacecraft_clock_count1 ({sc1}) and spacecraft_clock_count2 '+
    #             f'({sc_cvt}) are in the wrong order - setting to count1')
    #         sc_cvt = sc1

    #     return sc_cvt

    def field_obs_mission_cassini_mission_phase_name(self):
        return self._create_mult(self._cassini_normalize_mission_phase_name())


    ##################################################
    ### COPY FIELD METHODS FROM obs_volume_couvis_8xxx 
    ### AND ADAPT FOR BeckerJarmak ###
    ##################################################

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

    # Leaving UVIS band, line, and sample parameters as None:
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
