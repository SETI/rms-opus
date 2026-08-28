"""The ``obs_ring_geometry`` columns: where the observation fell on a ring plane, and at
what angles.

One module per OPUS table, mixed into every obs class that fills the table. A column
whose value depends on the PDS version or on the instrument is left to a subclass, which
is why most of the methods here can be overridden and a few raise `NotImplementedError`
outright.
"""

from typing import TYPE_CHECKING, Any

from opus_import.obs.field_types import FloatField, MultFieldRet, StrField
from opus_import.obs.obs_base import ObsBase

# The longitude, in degrees, of each planet's ring-plane ascending node measured
# from the J2000 prime meridian. Adding the offset converts a J2000-referenced
# longitude to an ascending-node-referenced one; subtracting it converts back.
# A planet with no entry has no ring-plane longitude system here.
_ASCENDING_NODE_OFFSET_DEG = {
    'JUP': -1.942979,
    'SAT': -130.589560,
    'URA': -167.311270,
    'NEP': 16.853049,
    'PLU': -223.030000,
}


class ObsRingGeometry(ObsBase):
    """The ``obs_ring_geometry`` columns: where a ring plane was crossed.

    Its ``field_obs_*`` methods each fill the schema column their name ends in,
    declaring the type `opus_import.obs.field_types` gives that column.
    """

    if TYPE_CHECKING:
        # Supplied by ObsGeneral, which every class combining this one also inherits.
        def field_obs_general_planet_id(self) -> MultFieldRet: ...

    def _ascending_node_offset(self, planet: str | int | float | None) -> float | None:
        """Return the longitude offset between a planet's ring-plane node and J2000.

        Parameters:
            planet: The OPUS planet id, as a mult column's value gives it, which is
                why it is typed as widely as
                `opus_import.obs.field_types.MultField`'s ``col_val``.

        Returns:
            The offset in degrees, or None for a planet with no ring-plane longitude
            system
            here -- which includes every value that is not one of the planet ids.
        """
        if not isinstance(planet, str):
            return None
        return _ASCENDING_NODE_OFFSET_DEG.get(planet)

    def _j2000_to_ascending(self, long: FloatField) -> FloatField:
        """Convert a J2000-referenced ring longitude to an ascending-node-referenced one.

        Parameters:
            long: The longitude in degrees, or None.

        Returns:
            The converted longitude in ``[0, 360)``, or None if there was none to convert
            or
            this observation's planet has no ring-plane longitude system.
        """
        if long is None:
            return None
        planet_id = self.field_obs_general_planet_id()
        # obs_general.planet_id is a GROUP column, not a MULTIGROUP one, so every
        # implementation of it returns a single value rather than a list.
        assert isinstance(planet_id, dict)
        planet = planet_id['col_val']
        offset = self._ascending_node_offset(planet)
        if offset is None:
            return None
        return (long + offset) % 360.0

    def _ascending_to_j2000(self, long: FloatField) -> FloatField:
        """Convert an ascending-node-referenced ring longitude to a J2000-referenced one.

        The inverse of `_j2000_to_ascending`.

        Parameters:
            long: The longitude in degrees, or None.

        Returns:
            The converted longitude in ``[0, 360)``, or None on the same two conditions.
        """
        if long is None:
            return None
        planet_id = self.field_obs_general_planet_id()
        # obs_general.planet_id is a GROUP column, not a MULTIGROUP one, so every
        # implementation of it returns a single value rather than a list.
        assert isinstance(planet_id, dict)
        planet = planet_id['col_val']
        offset = self._ascending_node_offset(planet)
        if offset is None:
            return None
        return (long - offset) % 360.0

    ####################################
    ### FIELD METHODS FOR THIS TABLE ###
    ####################################

    ### Don't override these ###

    def field_obs_ring_geometry_opus_id(self) -> StrField:
        return self.opus_id

    def field_obs_ring_geometry_bundle_id(self) -> StrField:
        return self.bundle

    def field_obs_ring_geometry_instrument_id(self) -> StrField:
        return self.instrument_id

    ################################
    ### ! Might override these ! ###
    ################################

    # For all of these methods, _ring_geo_index_col will return None if there is no
    # ring geo information for this instrument or this observation.
    # If the ring_geo contents are going to come from another source, the
    # instrument class can subclass these methods.

    # Radius & Longitude

    def field_obs_ring_geometry_ring_radius1(self) -> FloatField:
        return self._ring_geo_index_col('MINIMUM_RING_RADIUS')

    def field_obs_ring_geometry_ring_radius2(self) -> FloatField:
        return self._ring_geo_index_col('MAXIMUM_RING_RADIUS')

    # Ascending node-based longitude (here and below) is not available in the current
    # ring_summary tables, so we compute it here. This is possible because the
    # difference between the First Point of Aries and the Ascending Node is essentially
    # constant over the lifetime of our observations. However, if the original range is
    # 0-360, we make the new range also 0-360, because nothing else would make sense.
    def field_obs_ring_geometry_ascending_longitude1(self) -> FloatField:
        # New ring_geo files have this column, old files have to be be computed from
        # J2000
        long = self._ring_geo_index_col('MINIMUM_RING_LONGITUDE_WRT_NODE', missing_ok=True)
        if long is not None:
            return long
        if (
            self.field_obs_ring_geometry_j2000_longitude1() == 0
            and self.field_obs_ring_geometry_j2000_longitude2() == 360
        ):
            return 0
        return self._j2000_to_ascending(self.field_obs_ring_geometry_j2000_longitude1())

    def field_obs_ring_geometry_ascending_longitude2(self) -> FloatField:
        # New ring_geo files have this column, old files have to be be computed from
        # J2000
        long = self._ring_geo_index_col('MAXIMUM_RING_LONGITUDE_WRT_NODE', missing_ok=True)
        if long is not None:
            return long
        if (
            self.field_obs_ring_geometry_j2000_longitude1() == 0
            and self.field_obs_ring_geometry_j2000_longitude2() == 360
        ):
            return 360
        return self._j2000_to_ascending(self.field_obs_ring_geometry_j2000_longitude2())

    def field_obs_ring_geometry_sub_solar_ring_ascending_long1(self) -> FloatField:
        # New ring_geo files have this column, old files have to be be computed from
        # J2000
        long = self._ring_geo_index_col(
            'MINIMUM_SUB_SOLAR_RING_LONGITUDE_WRT_NODE', missing_ok=True
        )
        if long is not None:
            return long
        if (
            self.field_obs_ring_geometry_sub_solar_ring_j2000_long1() == 0
            and self.field_obs_ring_geometry_sub_solar_ring_j2000_long2() == 360
        ):
            return 0
        return self._j2000_to_ascending(self.field_obs_ring_geometry_sub_solar_ring_j2000_long1())

    def field_obs_ring_geometry_sub_solar_ring_ascending_long2(self) -> FloatField:
        # New ring_geo files have this column, old files have to be be computed from
        # J2000
        long = self._ring_geo_index_col(
            'MAXIMUM_SUB_SOLAR_RING_LONGITUDE_WRT_NODE', missing_ok=True
        )
        if long is not None:
            return long
        if (
            self.field_obs_ring_geometry_sub_solar_ring_j2000_long1() == 0
            and self.field_obs_ring_geometry_sub_solar_ring_j2000_long2() == 360
        ):
            return 360
        return self._j2000_to_ascending(self.field_obs_ring_geometry_sub_solar_ring_j2000_long2())

    def field_obs_ring_geometry_sub_observer_ring_ascending_long1(self) -> FloatField:
        # New ring_geo files have this column, old files have to be be computed from
        # J2000
        long = self._ring_geo_index_col(
            'MINIMUM_SUB_OBSERVER_RING_LONGITUDE_WRT_NODE', missing_ok=True
        )
        if long is not None:
            return long
        if (
            self.field_obs_ring_geometry_sub_observer_ring_j2000_long1() == 0
            and self.field_obs_ring_geometry_sub_observer_ring_j2000_long2() == 360
        ):
            return 0
        return self._j2000_to_ascending(
            self.field_obs_ring_geometry_sub_observer_ring_j2000_long1()
        )

    def field_obs_ring_geometry_sub_observer_ring_ascending_long2(self) -> FloatField:
        # New ring_geo files have this column, old files have to be be computed from
        # J2000
        long = self._ring_geo_index_col(
            'MAXIMUM_SUB_OBSERVER_RING_LONGITUDE_WRT_NODE', missing_ok=True
        )
        if long is not None:
            return long
        if (
            self.field_obs_ring_geometry_sub_observer_ring_j2000_long1() == 0
            and self.field_obs_ring_geometry_sub_observer_ring_j2000_long2() == 360
        ):
            return 360
        return self._j2000_to_ascending(
            self.field_obs_ring_geometry_sub_observer_ring_j2000_long2()
        )

    def field_obs_ring_geometry_j2000_longitude1(self) -> FloatField:
        return self._ring_geo_index_col('MINIMUM_RING_LONGITUDE')

    def field_obs_ring_geometry_j2000_longitude2(self) -> FloatField:
        return self._ring_geo_index_col('MAXIMUM_RING_LONGITUDE')

    def field_obs_ring_geometry_sub_solar_ring_j2000_long1(self) -> FloatField:
        return self._ring_geo_index_col(
            'MINIMUM_SUB_SOLAR_RING_LONGITUDE', 'SUB_SOLAR_RING_LONGITUDE'
        )

    def field_obs_ring_geometry_sub_solar_ring_j2000_long2(self) -> FloatField:
        return self._ring_geo_index_col(
            'MAXIMUM_SUB_SOLAR_RING_LONGITUDE', 'SUB_SOLAR_RING_LONGITUDE'
        )

    def field_obs_ring_geometry_sub_observer_ring_j2000_long1(self) -> FloatField:
        return self._ring_geo_index_col(
            'MINIMUM_SUB_OBSERVER_RING_LONGITUDE', 'SUB_OBSERVER_RING_LONGITUDE'
        )

    def field_obs_ring_geometry_sub_observer_ring_j2000_long2(self) -> FloatField:
        return self._ring_geo_index_col(
            'MAXIMUM_SUB_OBSERVER_RING_LONGITUDE', 'SUB_OBSERVER_RING_LONGITUDE'
        )

    def field_obs_ring_geometry_solar_hour_angle1(self) -> FloatField:
        return self._ring_geo_index_col('MINIMUM_SOLAR_HOUR_ANGLE')

    def field_obs_ring_geometry_solar_hour_angle2(self) -> FloatField:
        return self._ring_geo_index_col('MAXIMUM_SOLAR_HOUR_ANGLE')

    def field_obs_ring_geometry_longitude_wrt_observer1(self) -> FloatField:
        return self._ring_geo_index_col('MINIMUM_RING_LONGITUDE_WRT_OBSERVER')

    def field_obs_ring_geometry_longitude_wrt_observer2(self) -> FloatField:
        return self._ring_geo_index_col('MAXIMUM_RING_LONGITUDE_WRT_OBSERVER')

    def field_obs_ring_geometry_ring_azimuth_wrt_observer1(self) -> FloatField:
        return self._ring_geo_index_col('MINIMUM_RING_AZIMUTH')

    def field_obs_ring_geometry_ring_azimuth_wrt_observer2(self) -> FloatField:
        return self._ring_geo_index_col('MAXIMUM_RING_AZIMUTH')

    # Distance & Resolution

    def field_obs_ring_geometry_range_to_ring_intercept1(self) -> FloatField:
        return self._ring_geo_index_col('MINIMUM_RING_DISTANCE')

    def field_obs_ring_geometry_range_to_ring_intercept2(self) -> FloatField:
        return self._ring_geo_index_col('MAXIMUM_RING_DISTANCE')

    def field_obs_ring_geometry_ring_center_distance1(self) -> FloatField:
        return self._ring_geo_index_col('MINIMUM_RING_CENTER_DISTANCE', 'RING_CENTER_DISTANCE')

    def field_obs_ring_geometry_ring_center_distance2(self) -> FloatField:
        return self._ring_geo_index_col('MAXIMUM_RING_CENTER_DISTANCE', 'RING_CENTER_DISTANCE')

    def field_obs_ring_geometry_resolution1(self) -> FloatField:
        return self._ring_geo_index_col('FINEST_RING_INTERCEPT_RESOLUTION')

    def field_obs_ring_geometry_resolution2(self) -> FloatField:
        return self._ring_geo_index_col('COARSEST_RING_INTERCEPT_RESOLUTION')

    def field_obs_ring_geometry_projected_radial_resolution1(self) -> FloatField:
        return self._ring_geo_index_col('FINEST_RADIAL_RESOLUTION')

    def field_obs_ring_geometry_projected_radial_resolution2(self) -> FloatField:
        return self._ring_geo_index_col('COARSEST_RADIAL_RESOLUTION')

    def field_obs_ring_geometry_projected_long_resolution_angle1(self) -> FloatField:
        return self._ring_geo_index_col('FINEST_LONGITUDINAL_RESOLUTION', missing_ok=True)

    def field_obs_ring_geometry_projected_long_resolution_angle2(self) -> FloatField:
        return self._ring_geo_index_col('COARSEST_LONGITUDINAL_RESOLUTION', missing_ok=True)

    def field_obs_ring_geometry_projected_long_resolution1(self) -> FloatField:
        return self._ring_geo_index_col('FINEST_LONGITUDINAL_RESOLUTION_KM', missing_ok=True)

    def field_obs_ring_geometry_projected_long_resolution2(self) -> FloatField:
        return self._ring_geo_index_col('COARSEST_LONGITUDINAL_RESOLUTION_KM', missing_ok=True)

    # Lighting Geometry - Observed

    def field_obs_ring_geometry_phase1(self) -> FloatField:
        return self._ring_geo_index_col('MINIMUM_RING_PHASE_ANGLE')

    def field_obs_ring_geometry_phase2(self) -> FloatField:
        return self._ring_geo_index_col('MAXIMUM_RING_PHASE_ANGLE')

    def field_obs_ring_geometry_incidence1(self) -> FloatField:
        return self._ring_geo_index_col('MINIMUM_RING_INCIDENCE_ANGLE')

    def field_obs_ring_geometry_incidence2(self) -> FloatField:
        return self._ring_geo_index_col('MAXIMUM_RING_INCIDENCE_ANGLE')

    def field_obs_ring_geometry_emission1(self) -> FloatField:
        return self._ring_geo_index_col('MINIMUM_RING_EMISSION_ANGLE')

    def field_obs_ring_geometry_emission2(self) -> FloatField:
        return self._ring_geo_index_col('MAXIMUM_RING_EMISSION_ANGLE')

    def field_obs_ring_geometry_north_based_incidence1(self) -> FloatField:
        return self._ring_geo_index_col('MINIMUM_NORTH_BASED_INCIDENCE_ANGLE')

    def field_obs_ring_geometry_north_based_incidence2(self) -> FloatField:
        return self._ring_geo_index_col('MAXIMUM_NORTH_BASED_INCIDENCE_ANGLE')

    def field_obs_ring_geometry_north_based_emission1(self) -> FloatField:
        return self._ring_geo_index_col('MINIMUM_NORTH_BASED_EMISSION_ANGLE')

    def field_obs_ring_geometry_north_based_emission2(self) -> FloatField:
        return self._ring_geo_index_col('MAXIMUM_NORTH_BASED_EMISSION_ANGLE')

    def field_obs_ring_geometry_solar_ring_elevation1(self) -> FloatField:
        return self._ring_geo_index_col('MINIMUM_SOLAR_RING_ELEVATION')

    def field_obs_ring_geometry_solar_ring_elevation2(self) -> FloatField:
        return self._ring_geo_index_col('MAXIMUM_SOLAR_RING_ELEVATION')

    def field_obs_ring_geometry_observer_ring_elevation1(self) -> FloatField:
        return self._ring_geo_index_col('MINIMUM_OBSERVER_RING_ELEVATION')

    def field_obs_ring_geometry_observer_ring_elevation2(self) -> FloatField:
        return self._ring_geo_index_col('MAXIMUM_OBSERVER_RING_ELEVATION')

    # Lighting Geometry - Ring Center

    def field_obs_ring_geometry_ring_center_phase1(self) -> FloatField:
        return self._ring_geo_index_col(
            'MINIMUM_RING_CENTER_PHASE_ANGLE', 'RING_CENTER_PHASE_ANGLE'
        )

    def field_obs_ring_geometry_ring_center_phase2(self) -> FloatField:
        return self._ring_geo_index_col(
            'MAXIMUM_RING_CENTER_PHASE_ANGLE', 'RING_CENTER_PHASE_ANGLE'
        )

    def field_obs_ring_geometry_ring_center_incidence1(self) -> FloatField:
        return self._ring_geo_index_col(
            'MINIMUM_RING_CENTER_INCIDENCE_ANGLE', 'RING_CENTER_INCIDENCE_ANGLE'
        )

    def field_obs_ring_geometry_ring_center_incidence2(self) -> FloatField:
        return self._ring_geo_index_col(
            'MAXIMUM_RING_CENTER_INCIDENCE_ANGLE', 'RING_CENTER_INCIDENCE_ANGLE'
        )

    def field_obs_ring_geometry_ring_center_emission1(self) -> FloatField:
        return self._ring_geo_index_col(
            'MINIMUM_RING_CENTER_EMISSION_ANGLE', 'RING_CENTER_EMISSION_ANGLE'
        )

    def field_obs_ring_geometry_ring_center_emission2(self) -> FloatField:
        return self._ring_geo_index_col(
            'MAXIMUM_RING_CENTER_EMISSION_ANGLE', 'RING_CENTER_EMISSION_ANGLE'
        )

    def field_obs_ring_geometry_ring_center_north_based_incidence1(self) -> FloatField:
        return self._ring_geo_index_col(
            'MINIMUM_RING_CENTER_NORTH_BASED_INCIDENCE_ANGLE',
            'MINIMUM_NORTH_BASED_CENTER_INCIDENCE_ANGLE',
            'RING_CENTER_NORTH_BASED_INCIDENCE_ANGLE',
        )

    def field_obs_ring_geometry_ring_center_north_based_incidence2(self) -> FloatField:
        return self._ring_geo_index_col(
            'MAXIMUM_RING_CENTER_NORTH_BASED_INCIDENCE_ANGLE',
            'MAXIMUM_NORTH_BASED_CENTER_INCIDENCE_ANGLE',
            'RING_CENTER_NORTH_BASED_INCIDENCE_ANGLE',
        )

    def field_obs_ring_geometry_ring_center_north_based_emission1(self) -> FloatField:
        return self._ring_geo_index_col(
            'MINIMUM_RING_CENTER_NORTH_BASED_EMISSION_ANGLE',
            'MINIMUM_NORTH_BASED_CENTER_EMISSION_ANGLE',
            'RING_CENTER_NORTH_BASED_EMISSION_ANGLE',
        )

    def field_obs_ring_geometry_ring_center_north_based_emission2(self) -> FloatField:
        return self._ring_geo_index_col(
            'MAXIMUM_RING_CENTER_NORTH_BASED_EMISSION_ANGLE',
            'MAXIMUM_NORTH_BASED_CENTER_EMISSION_ANGLE',
            'RING_CENTER_NORTH_BASED_EMISSION_ANGLE',
        )

    def field_obs_ring_geometry_solar_ring_opening_angle1(self) -> FloatField:
        return self._ring_geo_index_col(
            'MINIMUM_SOLAR_RING_OPENING_ANGLE',
            'MINIMUM_SOLAR_RING_CENTER_OPENING_ANGLE',
            'SOLAR_RING_OPENING_ANGLE',
        )

    def field_obs_ring_geometry_solar_ring_opening_angle2(self) -> FloatField:
        return self._ring_geo_index_col(
            'MAXIMUM_SOLAR_RING_OPENING_ANGLE',
            'MAXIMUM_SOLAR_RING_CENTER_OPENING_ANGLE',
            'SOLAR_RING_OPENING_ANGLE',
        )

    def field_obs_ring_geometry_observer_ring_opening_angle1(self) -> FloatField:
        return self._ring_geo_index_col(
            'MINIMUM_OBSERVER_RING_OPENING_ANGLE',
            'MINIMUM_OBSERVER_RING_CENTER_OPENING_ANGLE',
            'OBSERVER_RING_OPENING_ANGLE',
        )

    def field_obs_ring_geometry_observer_ring_opening_angle2(self) -> FloatField:
        return self._ring_geo_index_col(
            'MAXIMUM_OBSERVER_RING_OPENING_ANGLE',
            'MAXIMUM_OBSERVER_RING_CENTER_OPENING_ANGLE',
            'OBSERVER_RING_OPENING_ANGLE',
        )

    # Edge-On Viewing Geometry

    def field_obs_ring_geometry_edge_on_radius1(self) -> FloatField:
        return self._ring_geo_index_col('MINIMUM_EDGE_ON_RING_RADIUS')

    def field_obs_ring_geometry_edge_on_radius2(self) -> FloatField:
        return self._ring_geo_index_col('MAXIMUM_EDGE_ON_RING_RADIUS')

    def field_obs_ring_geometry_edge_on_ascending_longitude1(self) -> FloatField:
        # New ring_geo files have this column, old files have to be be computed from
        # J2000
        long = self._ring_geo_index_col('MINIMUM_EDGE_ON_RING_LONGITUDE_WRT_NODE', missing_ok=True)
        if long is not None:
            return long
        if (
            self.field_obs_ring_geometry_edge_on_j2000_longitude1() == 0
            and self.field_obs_ring_geometry_edge_on_j2000_longitude2() == 360
        ):
            return 0
        return self._j2000_to_ascending(self.field_obs_ring_geometry_edge_on_j2000_longitude1())

    def field_obs_ring_geometry_edge_on_ascending_longitude2(self) -> FloatField:
        # New ring_geo files have this column, old files have to be be computed from
        # J2000
        long = self._ring_geo_index_col('MAXIMUM_EDGE_ON_RING_LONGITUDE_WRT_NODE', missing_ok=True)
        if long is not None:
            return long
        if (
            self.field_obs_ring_geometry_edge_on_j2000_longitude1() == 0
            and self.field_obs_ring_geometry_edge_on_j2000_longitude2() == 360
        ):
            return 360
        return self._j2000_to_ascending(self.field_obs_ring_geometry_edge_on_j2000_longitude2())

    def field_obs_ring_geometry_edge_on_j2000_longitude1(self) -> FloatField:
        return self._ring_geo_index_col('MINIMUM_EDGE_ON_RING_LONGITUDE')

    def field_obs_ring_geometry_edge_on_j2000_longitude2(self) -> FloatField:
        return self._ring_geo_index_col('MAXIMUM_EDGE_ON_RING_LONGITUDE')

    def field_obs_ring_geometry_edge_on_solar_hour_angle1(self) -> FloatField:
        return self._ring_geo_index_col('MINIMUM_EDGE_ON_SOLAR_HOUR_ANGLE')

    def field_obs_ring_geometry_edge_on_solar_hour_angle2(self) -> FloatField:
        return self._ring_geo_index_col('MAXIMUM_EDGE_ON_SOLAR_HOUR_ANGLE')

    def field_obs_ring_geometry_range_to_edge_on_point1(self) -> FloatField:
        return self._ring_geo_index_col('MINIMUM_EDGE_ON_INTERCEPT_DISTANCE')

    def field_obs_ring_geometry_range_to_edge_on_point2(self) -> FloatField:
        return self._ring_geo_index_col('MAXIMUM_EDGE_ON_INTERCEPT_DISTANCE')

    def field_obs_ring_geometry_edge_on_radial_resolution1(self) -> FloatField:
        return self._ring_geo_index_col('FINEST_EDGE_ON_RADIAL_RESOLUTION')

    def field_obs_ring_geometry_edge_on_radial_resolution2(self) -> FloatField:
        return self._ring_geo_index_col('COARSEST_EDGE_ON_RADIAL_RESOLUTION')

    def field_obs_ring_geometry_edge_on_altitude1(self) -> FloatField:
        return self._ring_geo_index_col('MINIMUM_EDGE_ON_RING_ALTITUDE')

    def field_obs_ring_geometry_edge_on_altitude2(self) -> FloatField:
        return self._ring_geo_index_col('MAXIMUM_EDGE_ON_RING_ALTITUDE')

    # Pole

    def field_obs_ring_geometry_ring_pole_clock_angle(self) -> FloatField:
        return self._ring_geo_index_col('RING_POLE_CLOCK_ANGLE', missing_ok=True)

    def field_obs_ring_geometry_ring_pole_position_angle(self) -> FloatField:
        return self._ring_geo_index_col('RING_POLE_POSITION_ANGLE', missing_ok=True)

    # Image Geometry

    def field_obs_ring_geometry_ring_diameter_pixels(self) -> FloatField:
        return self._ring_geo_index_col('RING_DIAMETER_IN_PIXELS', missing_ok=True)

    def field_obs_ring_geometry_center_x_coordinate(self) -> FloatField:
        return self._ring_geo_index_col('RING_CENTER_X_COORDINATE', missing_ok=True)

    def field_obs_ring_geometry_center_y_coordinate(self) -> FloatField:
        return self._ring_geo_index_col('RING_CENTER_Y_COORDINATE', missing_ok=True)

    # Timing

    def field_obs_ring_geometry_ring_intercept_time1(self) -> FloatField:
        return self._time_helper(
            'ring_geo_row', 'MINIMUM_RING_INTERCEPT_TIME', missing_index_ok=True
        )

    def field_obs_ring_geometry_ring_intercept_time2(self) -> FloatField:
        return self._time2_helper(
            'ring_geo_row',
            self.field_obs_ring_geometry_ring_intercept_time1(),
            'MAXIMUM_RING_INTERCEPT_TIME',
            missing_index_ok=True,
        )

    ########################
    ### Field validation ###
    ########################

    def validate_ring_geo_fields(self, row: dict[str, Any], metadata: dict[str, Any]) -> None:
        """Report a gridless ring geometry value whose minimum and maximum disagree.

        A gridless quantity describes the observation as a whole rather than a point in
        it,
        so its pair should be equal -- unless the observation spans enough time for the
        geometry to have moved, which is what ``temporal_camera`` records.

        Parameters:
            row: The ``obs_ring_geometry`` row this observation produced.
            metadata: What the import has computed for this observation, for the bundle's
                ``temporal_camera`` setting.
        """
        # This runs after all fields have been populated.
        # Compare min/max gridless fields and make sure they are the same
        # for a non-temporal camera.
        if metadata['temporal_camera']:
            # In this case, the minimum/maximum fields can be different
            return

        for gridless_column in (
            'ring_center_distance',
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
            'observer_ring_opening_angle',
        ):
            val1 = row[gridless_column + '1']
            val2 = row[gridless_column + '2']
            if val1 != val2 and not (
                val1 == 0 and val2 == 360 and gridless_column.endswith('_long')
            ):
                self._log_nonrepeating_error(
                    f'RING GEO fields {gridless_column}1 ({val1}) and '
                    f'{gridless_column}2 ({val2}) differ'
                )
