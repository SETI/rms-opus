################################################################################
# obs_surface_geometry.py
#
# Defines the ObsSurfaceGeometry class, which encapsulates fields in the
# obs_surface_geometry table.
################################################################################

from obs_base import ObsBase


class ObsSurfaceGeometry(ObsBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


    ####################################
    ### FIELD METHODS FOR THIS TABLE ###
    ####################################

    @property
    def field_obs_surface_geometry_opus_id(self):
        return self.opus_id

    @property
    def field_obs_surface_geometry_volume_id(self):
        return self.volume

    @property
    def field_obs_surface_geometry_instrument_id(self):
        return self.instrument_id

    @property
    def field_obs_surface_geometry_target_list(self):
        assert NotImplementedError
