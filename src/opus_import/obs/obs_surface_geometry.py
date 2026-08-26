"""The ``obs_surface_geometry`` columns: which bodies the observation covered.

One module per OPUS table, mixed into every obs class that fills the table. A column
whose value depends on the PDS version or on the instrument is left to a subclass, which
is why most of the methods here can be overridden and a few raise `NotImplementedError`
outright.
"""

from opus_import.obs.field_types import StrField
from opus_import.obs.obs_base import ObsBase


class ObsSurfaceGeometry(ObsBase):
    ####################################
    ### FIELD METHODS FOR THIS TABLE ###
    ####################################

    ### Don't override these ###

    """The ``obs_surface_geometry`` columns: which bodies the observation covered.

    Its ``field_obs_*`` methods each fill the schema column their name ends in,
    declaring the type `opus_import.obs.field_types` gives that column.
    """

    def field_obs_surface_geometry_opus_id(self) -> StrField:
        return self.opus_id

    def field_obs_surface_geometry_bundle_id(self) -> StrField:
        return self.bundle

    def field_obs_surface_geometry_instrument_id(self) -> StrField:
        return self.instrument_id

    def field_obs_surface_geometry_target_list(self) -> StrField:
        # This is the "Multiple Target List" field
        assert self._metadata is not None
        target_list = self._metadata['inventory_list']
        if target_list is None:
            return None

        new_target_list = []
        for target_name in target_list:
            if target_name == '':
                continue
            _, target_info = self._get_target_info(target_name)
            if target_info is None:
                return None
            new_target_list.append(target_info[2])
        ret = ','.join(sorted(new_target_list))

        if self._ctx.args.import_report_inventory_mismatch:
            used_targets = self._metadata['used_surface_geo_targets']
            used_target_list = []
            for target_name in used_targets:
                _, target_info = self._get_target_info(target_name)
                if target_info is None:
                    return None
                used_target_list.append(target_info[2])
            used_str = ','.join(sorted(used_target_list))

            if ret != used_str:
                # It's OK if the surface geo has the central planet but the
                # inventory doesn't
                for planet in ['Jupiter', 'Saturn', 'Uranus', 'Neptune',
                               'Pluto']:
                    if planet in used_target_list:
                        used_target_list.remove(planet)
                used_str = ','.join(sorted(used_target_list))
                if ret != used_str:
                    self._log_nonrepeating_warning(
                        f'Inventory and surface geo differ: {ret} vs {used_str}')

        return ret
