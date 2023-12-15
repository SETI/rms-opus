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

    ### Don't override these ###

    def field_obs_surface_geometry_target_opus_id(self):
        return self.opus_id

    def field_obs_surface_geometry_target_bundle_id(self):
        return self.bundle

    def field_obs_surface_geometry_target_instrument_id(self):
        return self.instrument_id

    def field_obs_surface_geometry_target_iau_east_longitude1(self):
        long = self.field_obs_surface_geometry_target_iau_west_longitude2()
        if long is None:
            return None
        return 360. - long

    def field_obs_surface_geometry_target_iau_east_longitude2(self):
        long = self.field_obs_surface_geometry_target_iau_west_longitude1()
        if long is None:
            return None
        return 360. - long

    def field_obs_surface_geometry_target_sub_solar_iau_east_longitude1(self):
        long = self.field_obs_surface_geometry_target_sub_solar_iau_west_longitude2()
        if long is None:
            return None
        return 360. - long

    def field_obs_surface_geometry_target_sub_solar_iau_east_longitude2(self):
        long = self.field_obs_surface_geometry_target_sub_solar_iau_west_longitude1()
        if long is None:
            return None
        return 360. - long

    def field_obs_surface_geometry_target_sub_observer_iau_east_longitude1(self):
        long = self.field_obs_surface_geometry_target_sub_observer_iau_west_longitude2()
        if long is None:
            return None
        return 360. - long

    def field_obs_surface_geometry_target_sub_observer_iau_east_longitude2(self):
        long = self.field_obs_surface_geometry_target_sub_observer_iau_west_longitude1()
        if long is None:
            return None
        return 360. - long

    def field_obs_surface_geometry_target_observer_east_longitude1(self):
        long = self.field_obs_surface_geometry_target_observer_west_longitude2()
        if long is None:
            return None
        return -long

    def field_obs_surface_geometry_target_observer_east_longitude2(self):
        long = self.field_obs_surface_geometry_target_observer_west_longitude1()
        if long is None:
            return None
        return -long


    ################################
    ### ! Might override these ! ###
    ################################

    # For all of these methods, _surface_geo_index_col will return None if there is no
    # surface geo information for this instrument or this observation.
    # If the surface_geo contents are going to come from another source, the
    # instrument class can subclass these methods.

    def field_obs_surface_geometry_target_planetocentric_latitude1(self):
        return self._surface_geo_index_col('MINIMUM_PLANETOCENTRIC_LATITUDE')

    def field_obs_surface_geometry_target_planetocentric_latitude2(self):
        return self._surface_geo_index_col('MAXIMUM_PLANETOCENTRIC_LATITUDE')

    def field_obs_surface_geometry_target_planetographic_latitude1(self):
        return self._surface_geo_index_col('MINIMUM_PLANETOGRAPHIC_LATITUDE')

    def field_obs_surface_geometry_target_planetographic_latitude2(self):
        return self._surface_geo_index_col('MAXIMUM_PLANETOGRAPHIC_LATITUDE')

    def field_obs_surface_geometry_target_iau_west_longitude1(self):
        return self._surface_geo_index_col('MINIMUM_IAU_LONGITUDE')

    def field_obs_surface_geometry_target_iau_west_longitude2(self):
        return self._surface_geo_index_col('MAXIMUM_IAU_LONGITUDE')

    def field_obs_surface_geometry_target_solar_hour_angle1(self):
        return self._surface_geo_index_col('MINIMUM_LOCAL_HOUR_ANGLE')

    def field_obs_surface_geometry_target_solar_hour_angle2(self):
        return self._surface_geo_index_col('MAXIMUM_LOCAL_HOUR_ANGLE')

    def field_obs_surface_geometry_target_observer_west_longitude1(self):
        return self._surface_geo_index_col('MINIMUM_LONGITUDE_WRT_OBSERVER')

    def field_obs_surface_geometry_target_observer_west_longitude2(self):
        return self._surface_geo_index_col('MAXIMUM_LONGITUDE_WRT_OBSERVER')

    def field_obs_surface_geometry_target_finest_resolution1(self):
        return self._surface_geo_index_col('MINIMUM_FINEST_SURFACE_RESOLUTION')

    def field_obs_surface_geometry_target_finest_resolution2(self):
        return self._surface_geo_index_col('MAXIMUM_FINEST_SURFACE_RESOLUTION')

    def field_obs_surface_geometry_target_coarsest_resolution1(self):
        return self._surface_geo_index_col('MINIMUM_COARSEST_SURFACE_RESOLUTION')

    def field_obs_surface_geometry_target_coarsest_resolution2(self):
        return self._surface_geo_index_col('MAXIMUM_COARSEST_SURFACE_RESOLUTION')

    def field_obs_surface_geometry_target_range_to_body1(self):
        return self._surface_geo_index_col('MINIMUM_SURFACE_DISTANCE')

    def field_obs_surface_geometry_target_range_to_body2(self):
        return self._surface_geo_index_col('MAXIMUM_SURFACE_DISTANCE')

    def field_obs_surface_geometry_target_phase1(self):
        return self._surface_geo_index_col('MINIMUM_PHASE_ANGLE')

    def field_obs_surface_geometry_target_phase2(self):
        return self._surface_geo_index_col('MAXIMUM_PHASE_ANGLE')

    def field_obs_surface_geometry_target_incidence1(self):
        return self._surface_geo_index_col('MINIMUM_INCIDENCE_ANGLE')

    def field_obs_surface_geometry_target_incidence2(self):
        return self._surface_geo_index_col('MAXIMUM_INCIDENCE_ANGLE')

    def field_obs_surface_geometry_target_emission1(self):
        return self._surface_geo_index_col('MINIMUM_EMISSION_ANGLE')

    def field_obs_surface_geometry_target_emission2(self):
        return self._surface_geo_index_col('MAXIMUM_EMISSION_ANGLE')

    def field_obs_surface_geometry_target_sub_solar_planetocentric_latitude1(self):
        return self._surface_geo_index_col('MINIMUM_SUB_SOLAR_PLANETOCENTRIC_LATITUDE',
                                           'SUB_SOLAR_PLANETOCENTRIC_LATITUDE')

    def field_obs_surface_geometry_target_sub_solar_planetocentric_latitude2(self):
        return self._surface_geo_index_col('MAXIMUM_SUB_SOLAR_PLANETOCENTRIC_LATITUDE',
                                           'SUB_SOLAR_PLANETOCENTRIC_LATITUDE')

    def field_obs_surface_geometry_target_sub_solar_planetographic_latitude1(self):
        return self._surface_geo_index_col('MINIMUM_SUB_SOLAR_PLANETOGRAPHIC_LATITUDE',
                                           'SUB_SOLAR_PLANETOGRAPHIC_LATITUDE')

    def field_obs_surface_geometry_target_sub_solar_planetographic_latitude2(self):
        return self._surface_geo_index_col('MAXIMUM_SUB_SOLAR_PLANETOGRAPHIC_LATITUDE',
                                           'SUB_SOLAR_PLANETOGRAPHIC_LATITUDE')

    def field_obs_surface_geometry_target_sub_observer_planetocentric_latitude1(self):
        return self._surface_geo_index_col('MINIMUM_SUB_OBSERVER_PLANETOCENTRIC_LATITUDE',
                                           'SUB_OBSERVER_PLANETOCENTRIC_LATITUDE')

    def field_obs_surface_geometry_target_sub_observer_planetocentric_latitude2(self):
        return self._surface_geo_index_col('MAXIMUM_SUB_OBSERVER_PLANETOCENTRIC_LATITUDE',
                                           'SUB_OBSERVER_PLANETOCENTRIC_LATITUDE')

    def field_obs_surface_geometry_target_sub_observer_planetographic_latitude1(self):
        return self._surface_geo_index_col('MINIMUM_SUB_OBSERVER_PLANETOGRAPHIC_LATITUDE',
                                           'SUB_OBSERVER_PLANETOGRAPHIC_LATITUDE')

    def field_obs_surface_geometry_target_sub_observer_planetographic_latitude2(self):
        return self._surface_geo_index_col('MINIMUM_SUB_OBSERVER_PLANETOGRAPHIC_LATITUDE',
                                           'SUB_OBSERVER_PLANETOGRAPHIC_LATITUDE')

    def field_obs_surface_geometry_target_sub_solar_iau_west_longitude1(self):
        return self._surface_geo_index_col('MINIMUM_SUB_SOLAR_IAU_LONGITUDE',
                                           'SUB_SOLAR_IAU_LONGITUDE')

    def field_obs_surface_geometry_target_sub_solar_iau_west_longitude2(self):
        return self._surface_geo_index_col('MAXIMUM_SUB_SOLAR_IAU_LONGITUDE',
                                           'SUB_SOLAR_IAU_LONGITUDE')

    def field_obs_surface_geometry_target_sub_observer_iau_west_longitude1(self):
        return self._surface_geo_index_col('MINIMUM_SUB_OBSERVER_IAU_LONGITUDE',
                                           'SUB_OBSERVER_IAU_LONGITUDE')

    def field_obs_surface_geometry_target_sub_observer_iau_west_longitude2(self):
        return self._surface_geo_index_col('MINIMUM_SUB_OBSERVER_IAU_LONGITUDE',
                                           'SUB_OBSERVER_IAU_LONGITUDE')

    def field_obs_surface_geometry_target_center_resolution1(self):
        return self._surface_geo_index_col('MINIMUM_CENTER_RESOLUTION',
                                           'CENTER_RESOLUTION')

    def field_obs_surface_geometry_target_center_resolution2(self):
        return self._surface_geo_index_col('MAXIMUM_CENTER_RESOLUTION',
                                           'CENTER_RESOLUTION')

    def field_obs_surface_geometry_target_center_distance1(self):
        return self._surface_geo_index_col('MINIMUM_CENTER_DISTANCE',
                                           'CENTER_DISTANCE')

    def field_obs_surface_geometry_target_center_distance2(self):
        return self._surface_geo_index_col('MAXIMUM_CENTER_DISTANCE',
                                           'CENTER_DISTANCE')

    def field_obs_surface_geometry_target_center_phase_angle1(self):
        ret = self._surface_geo_index_col('MINIMUM_CENTER_PHASE_ANGLE',
                                          'CENTER_PHASE_ANGLE')

    def field_obs_surface_geometry_target_center_phase_angle2(self):
        ret = self._surface_geo_index_col('MAXIMUM_CENTER_PHASE_ANGLE',
                                          'CENTER_PHASE_ANGLE')


    ########################
    ### Field validation ###
    ########################

    def validate_surface_geo_fields(self, row, metadata, table_name):
        # This runs after all fields have been populated.
        # Compare min/max gridless fields and make sure they are the same
        # for a non-temporal camera.
        if metadata['temporal_camera']:
            # In this case, the minimum/maximum fields can be different
            return

        for gridless_column in ('sub_solar_planetocentric_latitude',
                                'sub_solar_planetographic_latitude',
                                'sub_observer_planetocentric_latitude',
                                'sub_observer_planetographic_latitude',
                                'sub_solar_iau_west_longitude',
                                'sub_observer_iau_west_longitude',
                                'center_resolution',
                                'center_distance',
                                'center_phase_angle'):
            val1 = row[gridless_column+'1']
            val2 = row[gridless_column+'2']
            if val1 != val2:
                target = table_name.replace('obs_surface_geometry__', '').upper()
                self._log_nonrepeating_error(
                    f'SURFACE GEO {target} fields {gridless_column}1 ({val1}) and '
                    f'{gridless_column}2 ({val2}) differ')
