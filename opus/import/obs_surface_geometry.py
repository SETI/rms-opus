################################################################################
# obs_surface_geometry.py
#
# Defines the ObsSurfaceGeometry class, which encapsulates fields in the
# obs_surface_geometry table.
################################################################################

import impglobals

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
        # This is the "Multiple Target List" field
        target_list = self._metadata['inventory_list']
        if target_list is None:
            return None

        new_target_list = []
        for target_name in target_list:
            target_info = self._get_target_info(target_name)
            if target_info is None:
                return None
            new_target_list.append(target_info[2])
        ret = ','.join(sorted(new_target_list))

        if impglobals.ARGUMENTS.import_report_inventory_mismatch:
            used_targets = self._metadata['used_surface_geo_targets']
            used_target_list = []
            for target_name in used_targets:
                target_info = self._get_target_info(target_name)
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
                    import_util.log_nonrepeating_warning(
                        f'Inventory and surface geo differ: {ret} vs {used_str}')

        return ret
