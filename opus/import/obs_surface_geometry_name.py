################################################################################
# obs_surface_geometry_name.py
#
# Defines the ObsSurfaceGeometryName class, which encapsulates fields in the
# obs_surface_geometry_name table.
################################################################################

from obs_base import ObsBase


class ObsSurfaceGeometryName(ObsBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


    ####################################
    ### FIELD METHODS FOR THIS TABLE ###
    ####################################

    @property
    def field_obs_surface_geometry_name_opus_id(self):
        return self.opus_id

    @property
    def field_obs_surface_geometry_name_volume_id(self):
        return self.volume

    @property
    def field_obs_surface_geometry_name_instrument_id(self):
        return self.instrument_id

    @property
    def field_obs_surface_geometry_name_target_name(self):
        assert NonImplementedError
