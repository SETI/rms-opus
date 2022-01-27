################################################################################
# obs_ring_geometry.py
#
# Defines the ObsRingGeometry class, which encapsulates fields in the
# obs_ring_geometry table.
################################################################################

from obs_base import ObsBase


class ObsRingGeometry(ObsBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


    ####################################
    ### FIELD METHODS FOR THIS TABLE ###
    ####################################

    @property
    def field_obs_ring_geometry_opus_id(self):
        return self.opus_id

    @property
    def field_obs_ring_geometry_volume_id(self):
        return self.volume

    @property
    def field_obs_ring_geometry_instrument_id(self):
        return self.instrument_id

    # For all of these methods, _ring_geo_index_col will return None if there is no
    # ring geo information for this instrument or this observation.
    # If the ring_geo contents are going to come from another source, the
    # instrument class can subclass these methods.

    @property
    def field_obs_ring_geometry_ring_radius1(self):
        return self._ring_geo_index_col('MINIMUM_RING_RADIUS')

    @property
    def field_obs_ring_geometry_ring_radius2(self):
        return self._ring_geo_index_col('MAXIMUM_RING_RADIUS')

    @property
    def field_obs_ring_geometry_resolution1(self):
        return self._ring_geo_index_col('FINEST_RING_INTERCEPT_RESOLUTION')

    @property
    def field_obs_ring_geometry_resolution2(self):
        return self._ring_geo_index_col('COARSEST_RING_INTERCEPT_RESOLUTION')

    @property
    def field_obs_ring_geometry_projected_radial_resolution1(self):
        return self._ring_geo_index_col('FINEST_RADIAL_RESOLUTION')

    @property
    def field_obs_ring_geometry_projected_radial_resolution2(self):
        return self._ring_geo_index_col('COARSEST_RADIAL_RESOLUTION')

    @property
    def field_obs_ring_geometry_range_to_ring_intercept1(self):
        return self._ring_geo_index_col('MINIMUM_RING_DISTANCE')

    @property
    def field_obs_ring_geometry_range_to_ring_intercept2(self):
        return self._ring_geo_index_col('MAXIMUM_RING_DISTANCE')

    @property
    def field_obs_ring_geometry_ring_center_distance1(self):
        return self._ring_geo_index_col('RING_CENTER_DISTANCE')

    @property
    def field_obs_ring_geometry_ring_center_distance2(self):
        return self._ring_geo_index_col('RING_CENTER_DISTANCE')

    @property
    def field_obs_ring_geometry_j2000_longitude1(self):
        return self._ring_geo_index_col('MINIMUM_RING_LONGITUDE')

    @property
    def field_obs_ring_geometry_j2000_longitude2(self):
        return self._ring_geo_index_col('MAXIMUM_RING_LONGITUDE')

    @property
    def field_obs_ring_geometry_solar_hour_angle1(self):
        return self._ring_geo_index_col('MINIMUM_SOLAR_HOUR_ANGLE')

    @property
    def field_obs_ring_geometry_solar_hour_angle2(self):
        return self._ring_geo_index_col('MAXIMUM_SOLAR_HOUR_ANGLE')

    @property
    def field_obs_ring_geometry_longitude_wrt_observer1(self):
        return self._ring_geo_index_col('MINIMUM_RING_LONGITUDE_WRT_OBSERVER')

    @property
    def field_obs_ring_geometry_longitude_wrt_observer2(self):
        return self._ring_geo_index_col('MAXIMUM_RING_LONGITUDE_WRT_OBSERVER')

    @property
    def field_obs_ring_geometry_ring_azimuth_wrt_observer1(self):
        return self._ring_geo_index_col('MINIMUM_RING_AZIMUTH')

    @property
    def field_obs_ring_geometry_ring_azimuth_wrt_observer2(self):
        return self._ring_geo_index_col('MAXIMUM_RING_AZIMUTH')

    @property
    def field_obs_ring_geometry_sub_solar_ring_long1(self):
        return self._ring_geo_index_col('SUB_SOLAR_RING_LONGITUDE')

    @property
    def field_obs_ring_geometry_sub_solar_ring_long2(self):
        return self._ring_geo_index_col('SUB_SOLAR_RING_LONGITUDE')

    @property
    def field_obs_ring_geometry_sub_observer_ring_long1(self):
        return self._ring_geo_index_col('SUB_OBSERVER_RING_LONGITUDE')

    @property
    def field_obs_ring_geometry_sub_observer_ring_long2(self):
        return self._ring_geo_index_col('SUB_OBSERVER_RING_LONGITUDE')

    @property
    def field_obs_ring_geometry_solar_ring_elev1(self):
        return self._ring_geo_index_col('MINIMUM_SOLAR_RING_ELEVATION')

    @property
    def field_obs_ring_geometry_solar_ring_elev2(self):
        return self._ring_geo_index_col('MAXIMUM_SOLAR_RING_ELEVATION')

    @property
    def field_obs_ring_geometry_observer_ring_elevation1(self):
        return self._ring_geo_index_col('MINIMUM_OBSERVER_RING_ELEVATION')

    @property
    def field_obs_ring_geometry_observer_ring_elevation2(self):
        return self._ring_geo_index_col('MAXIMUM_OBSERVER_RING_ELEVATION')

    @property
    def field_obs_ring_geometry_phase1(self):
        return self._ring_geo_index_col('MINIMUM_RING_PHASE_ANGLE')

    @property
    def field_obs_ring_geometry_phase2(self):
        return self._ring_geo_index_col('MAXIMUM_RING_PHASE_ANGLE')

    @property
    def field_obs_ring_geometry_incidence1(self):
        return self._ring_geo_index_col('MINIMUM_RING_INCIDENCE_ANGLE')

    @property
    def field_obs_ring_geometry_incidence2(self):
        return self._ring_geo_index_col('MAXIMUM_RING_INCIDENCE_ANGLE')

    @property
    def field_obs_ring_geometry_emission1(self):
        return self._ring_geo_index_col('MINIMUM_RING_EMISSION_ANGLE')

    @property
    def field_obs_ring_geometry_emission2(self):
        return self._ring_geo_index_col('MAXIMUM_RING_EMISSION_ANGLE')

    @property
    def field_obs_ring_geometry_north_based_incidence1(self):
        return self._ring_geo_index_col('MINIMUM_NORTH_BASED_INCIDENCE_ANGLE')

    @property
    def field_obs_ring_geometry_north_based_incidence2(self):
        return self._ring_geo_index_col('MAXIMUM_NORTH_BASED_INCIDENCE_ANGLE')

    @property
    def field_obs_ring_geometry_north_based_emission1(self):
        return self._ring_geo_index_col('MINIMUM_NORTH_BASED_EMISSION_ANGLE')

    @property
    def field_obs_ring_geometry_north_based_emission2(self):
        return self._ring_geo_index_col('MAXIMUM_NORTH_BASED_EMISSION_ANGLE')

    @property
    def field_obs_ring_geometry_ring_center_phase1(self):
        return self._ring_geo_index_col('RING_CENTER_PHASE_ANGLE')

    @property
    def field_obs_ring_geometry_ring_center_phase2(self):
        return self._ring_geo_index_col('RING_CENTER_PHASE_ANGLE')

    @property
    def field_obs_ring_geometry_ring_center_incidence1(self):
        return self._ring_geo_index_col('RING_CENTER_INCIDENCE_ANGLE')

    @property
    def field_obs_ring_geometry_ring_center_incidence2(self):
        return self._ring_geo_index_col('RING_CENTER_INCIDENCE_ANGLE')

    @property
    def field_obs_ring_geometry_ring_center_emission1(self):
        return self._ring_geo_index_col('RING_CENTER_EMISSION_ANGLE')

    @property
    def field_obs_ring_geometry_ring_center_emission2(self):
        return self._ring_geo_index_col('RING_CENTER_EMISSION_ANGLE')

    @property
    def field_obs_ring_geometry_ring_center_north_based_incidence1(self):
        return self._ring_geo_index_col('RING_CENTER_NORTH_BASED_INCIDENCE_ANGLE')

    @property
    def field_obs_ring_geometry_ring_center_north_based_incidence2(self):
        return self._ring_geo_index_col('RING_CENTER_NORTH_BASED_INCIDENCE_ANGLE')

    @property
    def field_obs_ring_geometry_ring_center_north_based_emission1(self):
        return self._ring_geo_index_col('RING_CENTER_NORTH_BASED_EMISSION_ANGLE')

    @property
    def field_obs_ring_geometry_ring_center_north_based_emission2(self):
        return self._ring_geo_index_col('RING_CENTER_NORTH_BASED_EMISSION_ANGLE')

    @property
    def field_obs_ring_geometry_solar_ring_opening_angle1(self):
        return self._ring_geo_index_col('SOLAR_RING_OPENING_ANGLE')

    @property
    def field_obs_ring_geometry_solar_ring_opening_angle2(self):
        return self._ring_geo_index_col('SOLAR_RING_OPENING_ANGLE')

    @property
    def field_obs_ring_geometry_observer_ring_opening_angle1(self):
        return self._ring_geo_index_col('OBSERVER_RING_OPENING_ANGLE')

    @property
    def field_obs_ring_geometry_observer_ring_opening_angle2(self):
        return self._ring_geo_index_col('OBSERVER_RING_OPENING_ANGLE')

    @property
    def field_obs_ring_geometry_edge_on_radius1(self):
        return self._ring_geo_index_col('MINIMUM_EDGE_ON_RING_RADIUS')

    @property
    def field_obs_ring_geometry_edge_on_radius2(self):
        return self._ring_geo_index_col('MAXIMUM_EDGE_ON_RING_RADIUS')

    @property
    def field_obs_ring_geometry_edge_on_altitude1(self):
        return self._ring_geo_index_col('MINIMUM_EDGE_ON_RING_ALTITUDE')

    @property
    def field_obs_ring_geometry_edge_on_altitude2(self):
        return self._ring_geo_index_col('MAXIMUM_EDGE_ON_RING_ALTITUDE')

    @property
    def field_obs_ring_geometry_edge_on_radial_resolution1(self):
        return self._ring_geo_index_col('FINEST_EDGE_ON_RADIAL_RESOLUTION')

    @property
    def field_obs_ring_geometry_edge_on_radial_resolution2(self):
        return self._ring_geo_index_col('COARSEST_EDGE_ON_RADIAL_RESOLUTION')

    @property
    def field_obs_ring_geometry_range_to_edge_on_point1(self):
        return self._ring_geo_index_col('MINIMUM_EDGE_ON_INTERCEPT_DISTANCE')

    @property
    def field_obs_ring_geometry_range_to_edge_on_point2(self):
        return self._ring_geo_index_col('MAXIMUM_EDGE_ON_INTERCEPT_DISTANCE')

    @property
    def field_obs_ring_geometry_edge_on_j2000_longitude1(self):
        return self._ring_geo_index_col('MINIMUM_EDGE_ON_RING_LONGITUDE')

    @property
    def field_obs_ring_geometry_edge_on_j2000_longitude2(self):
        return self._ring_geo_index_col('MAXIMUM_EDGE_ON_RING_LONGITUDE')

    @property
    def field_obs_ring_geometry_edge_on_solar_hour_angle1(self):
        return self._ring_geo_index_col('MINIMUM_EDGE_ON_SOLAR_HOUR_ANGLE')

    @property
    def field_obs_ring_geometry_edge_on_solar_hour_angle2(self):
        return self._ring_geo_index_col('MAXIMUM_EDGE_ON_SOLAR_HOUR_ANGLE')

    @property
    def field_obs_ring_geometry_ring_intercept_time1(self):
        # This is not in the ring geometry file but only provided by certain instruments
        return None

    @property
    def field_obs_ring_geometry_ring_intercept_time2(self):
        # This is not in the ring geometry file but only provided by certain instruments
        return None
