################################################################################
# obs_instrument_vg28xx_vgiss.py
#
# Defines the ObsInstrumentVG28xxISS class, which encapsulates fields for the
# common, obs_mission_voyager, and obs_instrument_vgiss tables for VG_2810
# radial profiles.
################################################################################

from obs_instrument_vg28xx import ObsInstrumentVG28xx


class ObsInstrumentVG28xxVGISS(ObsInstrumentVG28xx):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


    #############################
    ### OVERRIDE FROM ObsBase ###
    #############################

    @property
    def instrument_id(self):
        return 'VGISS'


    ################################
    ### OVERRIDE FROM ObsGeneral ###
    ################################

    def field_obs_general_quantity(self):
        return 'REFLECT'

    def field_obs_general_observation_type(self):
        return 'REF'


    ##################################
    ### OVERRIDE FROM ObsTypeImage ###
    ##################################

    def field_obs_type_image_image_type_id(self):
        return 'FRAM'

    def field_obs_type_image_duration(self):
        return 0.72

    def field_obs_type_image_levels(self):
        return 256

    def field_obs_type_image_greater_pixel_size(self):
        return 800

    def field_obs_type_image_lesser_pixel_size(self):
        return 800


    ################################
    ### OVERRIDE FROM ObsProfile ###
    ################################

    def field_obs_profile_occ_type(self):
        return 'REF'

    def field_obs_profile_quality_score(self):
        return 'GOOD'

    def field_obs_profile_source(self):
        return None

    def field_obs_profile_host(self):
        return self._index_col('RECEIVER_HOST_NAME')


    #####################################
    ### OVERRIDE FROM ObsRingGeometry ###
    #####################################

    # Source: Sun, observer: Voyager. For both of the reflectance profiles,
    # the Sun was illuminating the north side of the rings and Voyager was
    # observing the rings from the south side. Thus the incidence/emission
    # angles and the north-based incidence/emission angles will
    # be the same.

    # Ring elevation to Sun, same to opening angle except, it's positive if
    # source is at north side of Jupiter, Saturn, and Neptune, and south side of
    # Uranus. Negative if source is at south side of Jupiter, Saturn, and Neptune,
    # and north side of Uranus. In this volume, source is at north of Saturn,
    # so ring elevation will be the same as opening angle.
    def field_obs_ring_geometry_solar_ring_elevation1(self):
        return 90. - self._index_col('INCIDENCE_ANGLE')

    def field_obs_ring_geometry_solar_ring_elevation2(self):
        return 90. - self._index_col('INCIDENCE_ANGLE')

    # Ring elevation to observer, same to opening angle except, it's positive if
    # observer is at north side of Jupiter, Saturn, and Neptune, and south side of
    # Uranus. Negative if observer is at south side of Jupiter, Saturn, and Neptune,
    # and north side of Uranus. In this volume, observer is at the south of Saturn,
    # so ring elevation will be the same as opening angle.
    def field_obs_ring_geometry_observer_ring_elevation1(self):
        return 90. - self._index_col('MAXIMUM_EMISSION_ANGLE')

    def field_obs_ring_geometry_observer_ring_elevation2(self):
        return 90. - self._index_col('MINIMUM_EMISSION_ANGLE')

    def field_obs_ring_geometry_phase1(self):
        return self._index_col('MINIMUM_PHASE_ANGLE')

    def field_obs_ring_geometry_phase2(self):
        return self._index_col('MAXIMUM_PHASE_ANGLE')

    def field_obs_ring_geometry_incidence1(self):
        return self._index_col('INCIDENCE_ANGLE')

    def field_obs_ring_geometry_incidence2(self):
        return self._index_col('INCIDENCE_ANGLE')

    # Emission angle: the angle between the normal vector on the LIT side, to the
    # direction where outgoing photons to the observer. 0-90 when observer is at the
    # lit side of the ring, and 90-180 when it's at the dark side.
    def field_obs_ring_geometry_emission1(self):
        return self._index_col('MINIMUM_EMISSION_ANGLE')

    def field_obs_ring_geometry_emission2(self):
        return self._index_col('MAXIMUM_EMISSION_ANGLE')

    def field_obs_ring_geometry_north_based_incidence1(self):
        return self._index_col('INCIDENCE_ANGLE')

    def field_obs_ring_geometry_north_based_incidence2(self):
        return self._index_col('INCIDENCE_ANGLE')

    def field_obs_ring_geometry_north_based_emission1(self):
        return self._index_col('MINIMUM_EMISSION_ANGLE')

    def field_obs_ring_geometry_north_based_emission2(self):
        return self._index_col('MAXIMUM_EMISSION_ANGLE')

    # Opening angle to Sun: the angle between the ring surface to the direction
    # where incoming photons from the source. Positive if source is at the north
    # side of the ring, negative if it's at the south side. In this case, source
    # is at the north side, so it's 90 - inc. For reference, if source is at the
    # south side, then oa is - (90 - inc).
    def field_obs_ring_geometry_solar_ring_opening_angle1(self):
        return 90. - self._index_col('INCIDENCE_ANGLE')

    def field_obs_ring_geometry_solar_ring_opening_angle2(self):
        return 90. - self._index_col('INCIDENCE_ANGLE')

    def field_obs_ring_geometry_observer_ring_opening_angle1(self):
        return 90. - self._index_col('MAXIMUM_EMISSION_ANGLE')

    def field_obs_ring_geometry_observer_ring_opening_angle2(self):
        return 90. - self._index_col('MINIMUM_EMISSION_ANGLE')


    ##############################################
    ### FIELD METHODS FOR obs_instrument_vgiss ###
    ##############################################

    def field_obs_instrument_vgiss_opus_id(self):
        return self.opus_id

    def field_obs_instrument_vgiss_volume_id(self):
        return self.volume

    def field_obs_instrument_vgiss_instrument_id(self):
        return self.instrument_id

    def field_obs_instrument_vgiss_image_id(self):
        return self._index_col('IMAGE_ID')

    def field_obs_instrument_vgiss_scan_mode(self):
        return self._index_col('SCAN_MODE')

    def field_obs_instrument_vgiss_shutter_mode(self):
        return self._index_col('SHUTTER_MODE')

    def field_obs_instrument_vgiss_gain_mode(self):
        return self._index_col('GAIN_MODE')

    def field_obs_instrument_vgiss_edit_mode(self):
        return self._index_col('EDIT_MODE')

    def field_obs_instrument_vgiss_filter_name(self):
        return self._index_col('FILTER_NAME')

    def field_obs_instrument_vgiss_filter_number(self):
        return self._index_col('FILTER_NUMBER')

    def field_obs_instrument_vgiss_camera(self):
        # Narrow angle camera
        return 'N'

    def field_obs_instrument_vgiss_usable_lines(self):
        return 800

    def field_obs_instrument_vgiss_usable_samples(self):
        return 800
