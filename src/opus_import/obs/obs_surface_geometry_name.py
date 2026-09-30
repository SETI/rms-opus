"""The ``obs_surface_geometry_name`` columns: the one body a per-target geometry row
belongs to.

One module per OPUS table, mixed into every obs class that fills the table. A column
whose value depends on the PDS version or on the instrument is left to a subclass, which
is why most of the methods here can be overridden and a few raise `NotImplementedError`
outright.
"""

from opus_import.obs.field_types import MultFieldRet, StrField
from opus_import.obs.obs_base import ObsBase


class ObsSurfaceGeometryName(ObsBase):
    """The ``obs_surface_geometry_name`` columns: the body one geometry row is for.

    Its ``field_obs_*`` methods each fill the schema column their name ends in,
    declaring the type `opus_import.obs.field_types` gives that column.
    """

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
        return self._create_mult(
            col_val=target_name,
            disp_name=target_info[2],
            grouping=group_info['label'],
            group_disp_order=group_info['disp_order'],
        )
