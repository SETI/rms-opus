################################################################################
# obs_volume_vg2803_vgrss.py
#
# Defines the ObsVolumeVG2803RSS class, which encapsulates fields for the
# common and obs_mission_voyager tables for VGRSS occultations in VG_2803.
################################################################################

from obs_volume_vg28xx import ObsVolumeVG28xx


# TODOPDS4 Verify that these are correct
_DSN_NUM_TO_PDS4_INST = {
    43: 'canberra.dss43_70m',
    63: 'madrid.dss63_70m'
}


class ObsVolumeVG2803VGRSS(ObsVolumeVG28xx):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


    #############################
    ### OVERRIDE FROM ObsBase ###
    #############################

    @property
    def instrument_id(self):
        return 'VGRSS'


    ################################
    ### OVERRIDE FROM ObsGeneral ###
    ################################

    def field_obs_general_quantity(self):
        return self._create_mult('OPDEPTH')

    def field_obs_general_observation_type(self):
        return self._create_mult('OCC')


    ################################
    ### OVERRIDE FROM ObsProfile ###
    ################################

    def field_obs_profile_occ_type(self):
        return self._create_mult('RAD')

    def field_obs_profile_occ_dir(self):
        return self._create_mult(self._index_col('RING_OCCULTATION_DIRECTION')[0])

    def field_obs_profile_body_occ_flag(self):
        return self._create_mult(self._supp_index_col('PLANETARY_OCCULTATION_FLAG'))

    def field_obs_profile_quality_score(self):
        return self._create_mult('GOOD')

    def field_obs_profile_host(self):
        receiver_host = self._supp_index_col('RECEIVER_HOST_NAME')
        dsn = int(receiver_host[-2:])
        return self._create_mult(_DSN_NUM_TO_PDS4_INST[dsn], grouping='DSS')


    #####################################
    ### OVERRIDE FROM ObsRingGeometry ###
    #####################################


    def _is_voyager_at_uranus(self):
        target_name, target_disp_name = self._target_name()[0]
        return target_name == 'U RINGS'

    # Source: Voyager RSS is at south, observer: earth is at north.
    # Note: we searched VGISS start_time in OPUS and looked at north based emssion
    # angle to determine the location of Voyager. If the north based emission
    # angle is more than 90, it means the observer is at the south side of the
    # ring. Otherwise, the observer is at the north side of the ring.

    # Ring elevation to Sun, same to opening angle except, it's positive if
    # source is at north side of Jupiter, Saturn, and Neptune, and south side of
    # Uranus. Negative if source is at south side of Jupiter, Saturn, and Neptune,
    # and north side of Uranus.
    def field_obs_ring_geometry_solar_ring_elevation1(self):
        if self._is_voyager_at_uranus():
            return 90. - self.field_obs_ring_geometry_incidence2()
        return self.field_obs_ring_geometry_incidence1() - 90.

    def field_obs_ring_geometry_solar_ring_elevation2(self):
        if self._is_voyager_at_uranus():
            return 90. - self.field_obs_ring_geometry_incidence1()
        return self.field_obs_ring_geometry_incidence2() - 90.

    # Ring elevation to observer, same to opening angle except, it's positive if
    # observer is at north side of Jupiter, Saturn, and Neptune, and south side of
    # Uranus. Negative if observer is at south side of Jupiter, Saturn, and Neptune,
    # and north side of Uranus.
    def field_obs_ring_geometry_observer_ring_elevation1(self):
        return self.field_obs_ring_geometry_incidence1() - 90.

    def field_obs_ring_geometry_observer_ring_elevation2(self):
        return self.field_obs_ring_geometry_incidence2() - 90.

    def field_obs_ring_geometry_phase1(self):
        return 180.

    def field_obs_ring_geometry_phase2(self):
        return 180.

    # Incidence angle: The angle between the point where the incoming source
    # photos hit the ring and the normal to the ring plane on the LIT side of
    # the ring. This is always between 0 (parallel to the normal vector) and 90
    # (parallel to the ring plane)
    # We would like to use emission angle to get both min/max of incidence angle.
    # Emission angle is 90-180 (dark side), so incidence angle is 180 - emission
    # angle.
    def field_obs_ring_geometry_incidence1(self):
        inc = self._supp_index_col('INCIDENCE_ANGLE')
        max_ea = self._supp_index_col('MAXIMUM_EMISSION_ANGLE')
        cal_inc = 180 - max_ea
        if abs(cal_inc - inc) >= 0.005:
            self._log_nonrepeating_error(
                'The difference between incidence angle and 180-emission is > 0.005')
        return cal_inc

    def field_obs_ring_geometry_incidence2(self):
        inc = self._supp_index_col('INCIDENCE_ANGLE')
        max_ea = self._supp_index_col('MINIMUM_EMISSION_ANGLE')
        cal_inc = 180 - max_ea
        if abs(cal_inc - inc) >= 0.005:
            self._log_nonrepeating_error(
                'The difference between incidence angle and 180-emission is > 0.005')
        return cal_inc

    # Emission angle: the angle between the normal vector on the LIT side, to the
    # direction where outgoing photons to the observer. 0-90 when observer is at the
    # lit side of the ring, and 90-180 when it's at the dark side.
    # Since observer is on the dark side, ea is between 90-180
    def field_obs_ring_geometry_emission1(self):
        return self._supp_index_col('MINIMUM_EMISSION_ANGLE')

    def field_obs_ring_geometry_emission2(self):
        return self._supp_index_col('MAXIMUM_EMISSION_ANGLE')

    # North based inc: the angle between the point where incoming source photons hit
    # the ring to the normal vector on the NORTH side of the ring. 0-90 when north
    # side of the ring is lit, and 90-180 when south side is lit.
    # Since south side is lit, north based incidence angle is between 90-180.
    # It's 180 - inc, which will be the same as emission angle.
    def field_obs_ring_geometry_north_based_incidence1(self):
        return self._supp_index_col('MINIMUM_EMISSION_ANGLE')

    def field_obs_ring_geometry_north_based_incidence2(self):
        return self._supp_index_col('MAXIMUM_EMISSION_ANGLE')

    def field_obs_ring_geometry_north_based_emission1(self):
        return 180. - self.field_obs_ring_geometry_emission2()

    def field_obs_ring_geometry_north_based_emission2(self):
        return 180. - self.field_obs_ring_geometry_emission1()

    # Opening angle to Sun: the angle between the ring surface to the direction
    # where incoming photons from the source. Positive if source is at the north
    # side of the ring, negative if it's at the south side. In this case, source
    # is at the north side, so it's 90 - inc. For reference, if source is at the
    # south side, then oa is - (90 - inc).
    def field_obs_ring_geometry_solar_ring_opening_angle1(self):
        return self.field_obs_ring_geometry_incidence1() - 90.

    def field_obs_ring_geometry_solar_ring_opening_angle2(self):
        return self.field_obs_ring_geometry_incidence2() - 90.

    # Opening angle to observer: the angle between the ring surface to the direction
    # where outgoing photons to the observer. Positive if observer is at the north
    # side of the ring, negative if it's at the south side. If observer is at the
    # north side, it's ea - 90 (or 90 - inc). If observer is at the south side,
    # then oa is 90 - ea.
    def field_obs_ring_geometry_observer_ring_opening_angle1(self):
        return self.field_obs_ring_geometry_emission1() - 90.

    def field_obs_ring_geometry_observer_ring_opening_angle2(self):
        return self.field_obs_ring_geometry_emission2() - 90.
