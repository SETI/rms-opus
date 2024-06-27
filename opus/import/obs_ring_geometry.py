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

    def _ascending_node_offset(self, planet):
        if planet == 'JUP':
            return -1.942979
        if planet == 'SAT':
            return -130.589560
        if planet == 'URA':
            return -167.311270
        if planet == 'NEP':
            return 16.853049
        if planet == 'PLU':
            return -223.030000
        return None

    def _j2000_to_ascending(self, long):
        if long is None:
            return None
        planet = self.field_obs_general_planet_id()['col_val']
        offset = self._ascending_node_offset(planet)
        if offset is None:
            return None
        return (long + offset) % 360.

    def _ascending_to_j2000(self, long):
        if long is None:
            return None
        planet = self.field_obs_general_planet_id()['col_val']
        offset = self._ascending_node_offset(planet)
        if offset is None:
            return None
        return (long - offset) % 360.


    ####################################
    ### FIELD METHODS FOR THIS TABLE ###
    ####################################

    ### Don't override these ###

    def field_obs_ring_geometry_opus_id(self):
        return self.opus_id

    def field_obs_ring_geometry_bundle_id(self):
        return self.bundle

    def field_obs_ring_geometry_instrument_id(self):
        return self.instrument_id


    ################################
    ### ! Might override these ! ###
    ################################

    # For all of these methods, _ring_geo_index_col will return None if there is no
    # ring geo information for this instrument or this observation.
    # If the ring_geo contents are going to come from another source, the
    # instrument class can subclass these methods.

    def field_obs_ring_geometry_ring_radius1(self):
        return self._ring_geo_index_col('MINIMUM_RING_RADIUS')

    def field_obs_ring_geometry_ring_radius2(self):
        return self._ring_geo_index_col('MAXIMUM_RING_RADIUS')

    def field_obs_ring_geometry_resolution1(self):
        return self._ring_geo_index_col('FINEST_RING_INTERCEPT_RESOLUTION')

    def field_obs_ring_geometry_resolution2(self):
        return self._ring_geo_index_col('COARSEST_RING_INTERCEPT_RESOLUTION')

    def field_obs_ring_geometry_projected_radial_resolution1(self):
        return self._ring_geo_index_col('FINEST_RADIAL_RESOLUTION')

    def field_obs_ring_geometry_projected_radial_resolution2(self):
        return self._ring_geo_index_col('COARSEST_RADIAL_RESOLUTION')

    def field_obs_ring_geometry_range_to_ring_intercept1(self):
        return self._ring_geo_index_col('MINIMUM_RING_DISTANCE')

    def field_obs_ring_geometry_range_to_ring_intercept2(self):
        return self._ring_geo_index_col('MAXIMUM_RING_DISTANCE')

    def field_obs_ring_geometry_ring_center_distance1(self):
        return self._ring_geo_index_col('MINIMUM_RING_CENTER_DISTANCE',
                                        'RING_CENTER_DISTANCE')

    def field_obs_ring_geometry_ring_center_distance2(self):
        return self._ring_geo_index_col('MAXIMUM_RING_CENTER_DISTANCE',
                                        'RING_CENTER_DISTANCE')

    def field_obs_ring_geometry_j2000_longitude1(self):
        return self._ring_geo_index_col('MINIMUM_RING_LONGITUDE')

    def field_obs_ring_geometry_j2000_longitude2(self):
        return self._ring_geo_index_col('MAXIMUM_RING_LONGITUDE')

    # Ascending node-based longitude (here and below) is not available in the current
    # ring_summary tables, so we compute it here. This is possible because the
    # difference between the First Point of Aries and the Ascending Node is essentially
    # constant over the lifetime of our observations. However, if the original range is
    # 0-360, we make the new range also 0-360, because nothing else would make sense.
    def field_obs_ring_geometry_ascending_longitude1(self):
        if (self.field_obs_ring_geometry_j2000_longitude1() == 0 and
            self.field_obs_ring_geometry_j2000_longitude2() == 360):
            return 0
        return self._j2000_to_ascending(self.field_obs_ring_geometry_j2000_longitude1())

    def field_obs_ring_geometry_ascending_longitude2(self):
        if (self.field_obs_ring_geometry_j2000_longitude1() == 0 and
            self.field_obs_ring_geometry_j2000_longitude2() == 360):
            return 360
        return self._j2000_to_ascending(self.field_obs_ring_geometry_j2000_longitude2())

    def field_obs_ring_geometry_solar_hour_angle1(self):
        return self._ring_geo_index_col('MINIMUM_SOLAR_HOUR_ANGLE')

    def field_obs_ring_geometry_solar_hour_angle2(self):
        return self._ring_geo_index_col('MAXIMUM_SOLAR_HOUR_ANGLE')

    def field_obs_ring_geometry_longitude_wrt_observer1(self):
        return self._ring_geo_index_col('MINIMUM_RING_LONGITUDE_WRT_OBSERVER')

    def field_obs_ring_geometry_longitude_wrt_observer2(self):
        return self._ring_geo_index_col('MAXIMUM_RING_LONGITUDE_WRT_OBSERVER')

    def field_obs_ring_geometry_ring_azimuth_wrt_observer1(self):
        return self._ring_geo_index_col('MINIMUM_RING_AZIMUTH')

    def field_obs_ring_geometry_ring_azimuth_wrt_observer2(self):
        return self._ring_geo_index_col('MAXIMUM_RING_AZIMUTH')

    def field_obs_ring_geometry_sub_solar_ring_j2000_long1(self):
        return self._ring_geo_index_col('MINIMUM_SUB_SOLAR_RING_LONGITUDE',
                                        'SUB_SOLAR_RING_LONGITUDE')

    def field_obs_ring_geometry_sub_solar_ring_j2000_long2(self):
        return self._ring_geo_index_col('MAXIMUM_SUB_SOLAR_RING_LONGITUDE',
                                        'SUB_SOLAR_RING_LONGITUDE')

    def field_obs_ring_geometry_sub_solar_ring_ascending_long1(self):
        if (self.field_obs_ring_geometry_sub_solar_ring_j2000_long1() == 0 and
            self.field_obs_ring_geometry_sub_solar_ring_j2000_long2() == 360):
            return 0
        return self._j2000_to_ascending(
            self.field_obs_ring_geometry_sub_solar_ring_j2000_long1())

    def field_obs_ring_geometry_sub_solar_ring_ascending_long2(self):
        if (self.field_obs_ring_geometry_sub_solar_ring_j2000_long1() == 0 and
            self.field_obs_ring_geometry_sub_solar_ring_j2000_long2() == 360):
            return 360
        return self._j2000_to_ascending(
            self.field_obs_ring_geometry_sub_solar_ring_j2000_long2())

    def field_obs_ring_geometry_sub_observer_ring_j2000_long1(self):
        return self._ring_geo_index_col('MINIMUM_SUB_OBSERVER_RING_LONGITUDE',
                                        'SUB_OBSERVER_RING_LONGITUDE')

    def field_obs_ring_geometry_sub_observer_ring_j2000_long2(self):
        return self._ring_geo_index_col('MAXIMUM_SUB_OBSERVER_RING_LONGITUDE',
                                        'SUB_OBSERVER_RING_LONGITUDE')

    def field_obs_ring_geometry_sub_observer_ring_ascending_long1(self):
        if (self.field_obs_ring_geometry_sub_observer_ring_j2000_long1() == 0 and
            self.field_obs_ring_geometry_sub_observer_ring_j2000_long2() == 360):
            return 0
        return self._j2000_to_ascending(
            self.field_obs_ring_geometry_sub_observer_ring_j2000_long1())

    def field_obs_ring_geometry_sub_observer_ring_ascending_long2(self):
        if (self.field_obs_ring_geometry_sub_observer_ring_j2000_long1() == 0 and
            self.field_obs_ring_geometry_sub_observer_ring_j2000_long2() == 360):
            return 360
        return self._j2000_to_ascending(
            self.field_obs_ring_geometry_sub_observer_ring_j2000_long2())

    def field_obs_ring_geometry_solar_ring_elevation1(self):
        return self._ring_geo_index_col('MINIMUM_SOLAR_RING_ELEVATION')

    def field_obs_ring_geometry_solar_ring_elevation2(self):
        return self._ring_geo_index_col('MAXIMUM_SOLAR_RING_ELEVATION')

    def field_obs_ring_geometry_observer_ring_elevation1(self):
        return self._ring_geo_index_col('MINIMUM_OBSERVER_RING_ELEVATION')

    def field_obs_ring_geometry_observer_ring_elevation2(self):
        return self._ring_geo_index_col('MAXIMUM_OBSERVER_RING_ELEVATION')

    def field_obs_ring_geometry_phase1(self):
        return self._ring_geo_index_col('MINIMUM_RING_PHASE_ANGLE')

    def field_obs_ring_geometry_phase2(self):
        return self._ring_geo_index_col('MAXIMUM_RING_PHASE_ANGLE')

    def field_obs_ring_geometry_incidence1(self):
        return self._ring_geo_index_col('MINIMUM_RING_INCIDENCE_ANGLE')

    def field_obs_ring_geometry_incidence2(self):
        return self._ring_geo_index_col('MAXIMUM_RING_INCIDENCE_ANGLE')

    def field_obs_ring_geometry_emission1(self):
        return self._ring_geo_index_col('MINIMUM_RING_EMISSION_ANGLE')

    def field_obs_ring_geometry_emission2(self):
        return self._ring_geo_index_col('MAXIMUM_RING_EMISSION_ANGLE')

    def field_obs_ring_geometry_north_based_incidence1(self):
        return self._ring_geo_index_col('MINIMUM_NORTH_BASED_INCIDENCE_ANGLE')

    def field_obs_ring_geometry_north_based_incidence2(self):
        return self._ring_geo_index_col('MAXIMUM_NORTH_BASED_INCIDENCE_ANGLE')

    def field_obs_ring_geometry_north_based_emission1(self):
        return self._ring_geo_index_col('MINIMUM_NORTH_BASED_EMISSION_ANGLE')

    def field_obs_ring_geometry_north_based_emission2(self):
        return self._ring_geo_index_col('MAXIMUM_NORTH_BASED_EMISSION_ANGLE')

    def field_obs_ring_geometry_ring_center_phase1(self):
        return self._ring_geo_index_col('MINIMUM_RING_CENTER_PHASE_ANGLE',
                                        'RING_CENTER_PHASE_ANGLE')

    def field_obs_ring_geometry_ring_center_phase2(self):
        return self._ring_geo_index_col('MAXIMUM_RING_CENTER_PHASE_ANGLE',
                                        'RING_CENTER_PHASE_ANGLE')

    def field_obs_ring_geometry_ring_center_incidence1(self):
        return self._ring_geo_index_col('MINIMUM_RING_CENTER_INCIDENCE_ANGLE',
                                        'RING_CENTER_INCIDENCE_ANGLE')

    def field_obs_ring_geometry_ring_center_incidence2(self):
        return self._ring_geo_index_col('MAXIMUM_RING_CENTER_INCIDENCE_ANGLE',
                                        'RING_CENTER_INCIDENCE_ANGLE')

    def field_obs_ring_geometry_ring_center_emission1(self):
        return self._ring_geo_index_col('MINIMUM_RING_CENTER_EMISSION_ANGLE',
                                        'RING_CENTER_EMISSION_ANGLE')

    def field_obs_ring_geometry_ring_center_emission2(self):
        return self._ring_geo_index_col('MAXIMUM_RING_CENTER_EMISSION_ANGLE',
                                        'RING_CENTER_EMISSION_ANGLE')

    def field_obs_ring_geometry_ring_center_north_based_incidence1(self):
        return self._ring_geo_index_col('MINIMUM_RING_CENTER_NORTH_BASED_INCIDENCE_ANGLE',
                                        'RING_CENTER_NORTH_BASED_INCIDENCE_ANGLE')

    def field_obs_ring_geometry_ring_center_north_based_incidence2(self):
        return self._ring_geo_index_col('MAXIMUM_RING_CENTER_NORTH_BASED_INCIDENCE_ANGLE',
                                        'RING_CENTER_NORTH_BASED_INCIDENCE_ANGLE')

    def field_obs_ring_geometry_ring_center_north_based_emission1(self):
        return self._ring_geo_index_col('MINIMUM_RING_CENTER_NORTH_BASED_EMISSION_ANGLE',
                                        'RING_CENTER_NORTH_BASED_EMISSION_ANGLE')

    def field_obs_ring_geometry_ring_center_north_based_emission2(self):
        return self._ring_geo_index_col('MAXIMUM_RING_CENTER_NORTH_BASED_EMISSION_ANGLE',
                                        'RING_CENTER_NORTH_BASED_EMISSION_ANGLE')

    def field_obs_ring_geometry_solar_ring_opening_angle1(self):
        return self._ring_geo_index_col('MINIMUM_SOLAR_RING_OPENING_ANGLE',
                                        'SOLAR_RING_OPENING_ANGLE')

    def field_obs_ring_geometry_solar_ring_opening_angle2(self):
        return self._ring_geo_index_col('MAXIMUM_SOLAR_RING_OPENING_ANGLE',
                                        'SOLAR_RING_OPENING_ANGLE')

    def field_obs_ring_geometry_observer_ring_opening_angle1(self):
        return self._ring_geo_index_col('MINIMUM_OBSERVER_RING_OPENING_ANGLE',
                                        'OBSERVER_RING_OPENING_ANGLE')

    def field_obs_ring_geometry_observer_ring_opening_angle2(self):
        return self._ring_geo_index_col('MAXIMUM_OBSERVER_RING_OPENING_ANGLE',
                                        'OBSERVER_RING_OPENING_ANGLE')

    def field_obs_ring_geometry_edge_on_radius1(self):
        return self._ring_geo_index_col('MINIMUM_EDGE_ON_RING_RADIUS')

    def field_obs_ring_geometry_edge_on_radius2(self):
        return self._ring_geo_index_col('MAXIMUM_EDGE_ON_RING_RADIUS')

    def field_obs_ring_geometry_edge_on_altitude1(self):
        return self._ring_geo_index_col('MINIMUM_EDGE_ON_RING_ALTITUDE')

    def field_obs_ring_geometry_edge_on_altitude2(self):
        return self._ring_geo_index_col('MAXIMUM_EDGE_ON_RING_ALTITUDE')

    def field_obs_ring_geometry_edge_on_radial_resolution1(self):
        return self._ring_geo_index_col('FINEST_EDGE_ON_RADIAL_RESOLUTION')

    def field_obs_ring_geometry_edge_on_radial_resolution2(self):
        return self._ring_geo_index_col('COARSEST_EDGE_ON_RADIAL_RESOLUTION')

    def field_obs_ring_geometry_range_to_edge_on_point1(self):
        return self._ring_geo_index_col('MINIMUM_EDGE_ON_INTERCEPT_DISTANCE')

    def field_obs_ring_geometry_range_to_edge_on_point2(self):
        return self._ring_geo_index_col('MAXIMUM_EDGE_ON_INTERCEPT_DISTANCE')

    def field_obs_ring_geometry_edge_on_j2000_longitude1(self):
        return self._ring_geo_index_col('MINIMUM_EDGE_ON_RING_LONGITUDE')

    def field_obs_ring_geometry_edge_on_j2000_longitude2(self):
        return self._ring_geo_index_col('MAXIMUM_EDGE_ON_RING_LONGITUDE')

    def field_obs_ring_geometry_edge_on_ascending_longitude1(self):
        if (self.field_obs_ring_geometry_edge_on_j2000_longitude1() == 0 and
            self.field_obs_ring_geometry_edge_on_j2000_longitude2() == 360):
            return 0
        return self._j2000_to_ascending(
            self.field_obs_ring_geometry_edge_on_j2000_longitude1())

    def field_obs_ring_geometry_edge_on_ascending_longitude2(self):
        if (self.field_obs_ring_geometry_edge_on_j2000_longitude1() == 0 and
            self.field_obs_ring_geometry_edge_on_j2000_longitude2() == 360):
            return 360
        return self._j2000_to_ascending(
            self.field_obs_ring_geometry_edge_on_j2000_longitude2())

    def field_obs_ring_geometry_edge_on_solar_hour_angle1(self):
        return self._ring_geo_index_col('MINIMUM_EDGE_ON_SOLAR_HOUR_ANGLE')

    def field_obs_ring_geometry_edge_on_solar_hour_angle2(self):
        return self._ring_geo_index_col('MAXIMUM_EDGE_ON_SOLAR_HOUR_ANGLE')

    def field_obs_ring_geometry_ring_intercept_time1(self):
        # This is not in the ring geometry file but only provided by certain instruments
        return None

    def field_obs_ring_geometry_ring_intercept_time2(self):
        # This is not in the ring geometry file but only provided by certain instruments
        return None


    ########################
    ### Field validation ###
    ########################

    def validate_ring_geo_fields(self, row, metadata):
        # This runs after all fields have been populated.
        # Compare min/max gridless fields and make sure they are the same
        # for a non-temporal camera.
        if metadata['temporal_camera']:
            # In this case, the minimum/maximum fields can be different
            return

        for gridless_column in ('ring_center_distance',
                                'sub_solar_ring_j2000_long',
                                'sub_solar_ring_ascending_long',
                                'sub_observer_ring_j2000_long',
                                'sub_observer_ring_ascending_long',
                                'ring_center_phase',
                                'ring_center_incidence',
                                'ring_center_emission',
                                'ring_center_north_based_incidence',
                                'ring_center_north_based_emission',
                                'solar_ring_opening_angle',
                                'observer_ring_opening_angle'):
            val1 = row[gridless_column+'1']
            val2 = row[gridless_column+'2']
            if (val1 != val2 and
                not (val1 == 0 and val2 == 360 and gridless_column.endswith('_long'))):
                self._log_nonrepeating_error(
                    f'RING GEO fields {gridless_column}1 ({val1}) and '
                    f'{gridless_column}2 ({val2}) differ')
