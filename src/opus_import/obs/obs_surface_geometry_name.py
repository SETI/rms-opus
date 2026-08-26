################################################################################
# obs_surface_geometry_name.py
#
# Defines the ObsSurfaceGeometryName class, which encapsulates fields in the
# obs_surface_geometry_name table.
################################################################################

from opus_import.obs.field_types import MultFieldRet, StrField
from opus_import.obs.obs_base import ObsBase


class ObsSurfaceGeometryName(ObsBase):
    ####################################
    ### FIELD METHODS FOR THIS TABLE ###
    ####################################

    ### Don't override these ###

    def field_obs_surface_geometry_name_opus_id(self) -> StrField:
        return self.opus_id

    def field_obs_surface_geometry_name_bundle_id(self) -> StrField:
        return self.bundle

    def field_obs_surface_geometry_name_instrument_id(self) -> StrField:
        return self.instrument_id

    def field_obs_surface_geometry_name_target_name(self) -> MultFieldRet:
        # This is the target_name field in obs_surface_geometry that has the
        # many-to-one mapping of rows to OPUS IDs
        assert self._metadata is not None
        target_name = self._metadata['surface_geo_target_name'].upper()
        target_name, target_info = self._get_target_info(target_name)
        if target_info is None:
            return self._create_mult(None)
        group_info = self._get_planet_group_info(target_name)
        return self._create_mult(col_val=target_name, disp_name=target_info[2],
                                 grouping=group_info['label'],
                                 group_disp_order=group_info['disp_order'])
