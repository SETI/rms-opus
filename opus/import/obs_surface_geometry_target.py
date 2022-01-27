################################################################################
# obs_surface_geometry_target.py
#
# Defines the ObsSurfaceGeometryTarget class, which encapsulates fields in the
# obs_surface_geometry_<TARGET> tables.
################################################################################

from obs_base import ObsBase


class ObsSurfaceGeometryTarget(ObsBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


    ####################################
    ### FIELD METHODS FOR THIS TABLE ###
    ####################################

    @property
    def field_obs_surface_geometry_target_opus_id(self):
        return self.opus_id

    @property
    def field_obs_surface_geometry_target_volume_id(self):
        return self.volume

    @property
    def field_obs_surface_geometry_target_instrument_id(self):
        return self.instrument_id

    # For all of these methods, _surface_geo_index_col will return None if there is no
    # ring geo information for this instrument or this observation.
    # If the surface_geo contents are going to come from another source, the
    # instrument class can subclass these methods.

    @property
    def field_obs_surface_geometry_target_planetocentric_latitude1(self):
        return self._surface_geo_index_col('MINIMUM_PLANETOCENTRIC_LATITUDE')

    @property
    def field_obs_surface_geometry_target_planetocentric_latitude2(self):
        return self._surface_geo_index_col('MAXIMUM_PLANETOCENTRIC_LATITUDE')

    @property
    def field_obs_surface_geometry_target_planetographic_latitude1(self):
        return self._surface_geo_index_col('MINIMUM_PLANETOGRAPHIC_LATITUDE')

    @property
    def field_obs_surface_geometry_target_planetographic_latitude2(self):
        return self._surface_geo_index_col('MAXIMUM_PLANETOGRAPHIC_LATITUDE')

    @property
    def field_obs_surface_geometry_target_iau_west_longitude1(self):
        return self._surface_geo_index_col('MINIMUM_IAU_LONGITUDE')

    @property
    def field_obs_surface_geometry_target_iau_west_longitude2(self):
        return self._surface_geo_index_col('MAXIMUM_IAU_LONGITUDE')

    @property
    def field_obs_surface_geometry_target_solar_hour_angle1(self):
        return self._surface_geo_index_col('MINIMUM_LOCAL_HOUR_ANGLE')

    @property
    def field_obs_surface_geometry_target_solar_hour_angle2(self):
        return self._surface_geo_index_col('MAXIMUM_LOCAL_HOUR_ANGLE')

    @property
    def field_obs_surface_geometry_target_observer_longitude1(self):
        return self._surface_geo_index_col('MINIMUM_LONGITUDE_WRT_OBSERVER')

    @property
    def field_obs_surface_geometry_target_observer_longitude2(self):
        return self._surface_geo_index_col('MAXIMUM_LONGITUDE_WRT_OBSERVER')

    @property
    def field_obs_surface_geometry_target_finest_resolution1(self):
        return self._surface_geo_index_col('MINIMUM_FINEST_SURFACE_RESOLUTION')

    @property
    def field_obs_surface_geometry_target_finest_resolution2(self):
        return self._surface_geo_index_col('MAXIMUM_FINEST_SURFACE_RESOLUTION')

    @property
    def field_obs_surface_geometry_target_coarsest_resolution1(self):
        return self._surface_geo_index_col('MINIMUM_COARSEST_SURFACE_RESOLUTION')

    @property
    def field_obs_surface_geometry_target_coarsest_resolution2(self):
        return self._surface_geo_index_col('MAXIMUM_COARSEST_SURFACE_RESOLUTION')

    @property
    def field_obs_surface_geometry_target_range_to_body1(self):
        return self._surface_geo_index_col('MINIMUM_SURFACE_DISTANCE')

    @property
    def field_obs_surface_geometry_target_range_to_body2(self):
        return self._surface_geo_index_col('MAXIMUM_SURFACE_DISTANCE')

    @property
    def field_obs_surface_geometry_target_phase1(self):
        return self._surface_geo_index_col('MINIMUM_PHASE_ANGLE')

    @property
    def field_obs_surface_geometry_target_phase2(self):
        return self._surface_geo_index_col('MAXIMUM_PHASE_ANGLE')

    @property
    def field_obs_surface_geometry_target_incidence1(self):
        return self._surface_geo_index_col('MINIMUM_INCIDENCE_ANGLE')

    @property
    def field_obs_surface_geometry_target_incidence2(self):
        return self._surface_geo_index_col('MAXIMUM_INCIDENCE_ANGLE')

    @property
    def field_obs_surface_geometry_target_emission1(self):
        return self._surface_geo_index_col('MINIMUM_EMISSION_ANGLE')

    @property
    def field_obs_surface_geometry_target_emission2(self):
        return self._surface_geo_index_col('MAXIMUM_EMISSION_ANGLE')

    @property
    def field_obs_surface_geometry_target_sub_solar_planetocentric_latitude(self):
        return self._surface_geo_index_col('SUB_SOLAR_PLANETOCENTRIC_LATITUDE')

    @property
    def field_obs_surface_geometry_target_sub_solar_planetographic_latitude(self):
        return self._surface_geo_index_col('SUB_SOLAR_PLANETOGRAPHIC_LATITUDE')

    @property
    def field_obs_surface_geometry_target_sub_observer_planetocentric_latitude(self):
        return self._surface_geo_index_col('SUB_OBSERVER_PLANETOCENTRIC_LATITUDE')

    @property
    def field_obs_surface_geometry_target_sub_observer_planetographic_latitude(self):
        return self._surface_geo_index_col('SUB_OBSERVER_PLANETOGRAPHIC_LATITUDE')

    @property
    def field_obs_surface_geometry_target_sub_solar_iau_longitude(self):
        return self._surface_geo_index_col('SUB_SOLAR_IAU_LONGITUDE')

    @property
    def field_obs_surface_geometry_target_sub_observer_iau_longitude(self):
        return self._surface_geo_index_col('SUB_OBSERVER_IAU_LONGITUDE')

    @property
    def field_obs_surface_geometry_target_center_resolution(self):
        return self._surface_geo_index_col('CENTER_RESOLUTION')

    @property
    def field_obs_surface_geometry_target_center_distance(self):
        return self._surface_geo_index_col('CENTER_DISTANCE')

    @property
    def field_obs_surface_geometry_target_center_phase_angle(self):
        return self._surface_geo_index_col('CENTER_PHASE_ANGLE')
