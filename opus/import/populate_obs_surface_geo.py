################################################################################
# populate_obs_surface_geo.py
#
# Routines to populate fields in the obs_surface_geometry,
# obs_surface_geometry_name, and obs_surface_geometry__<TARGET> tables.
################################################################################

from config_data import *

import impglobals
import import_util



# These are fields in the normal obs_surface_geometry table that have the
# standard one-to-one mapping with OPUS ID
def populate_obs_surface_geo_target_list(**kwargs):
    metadata = kwargs['metadata']
    target_list = metadata['inventory_list']
    if target_list is None:
        return None

    new_target_list = []
    for target_name in target_list:
        if target_name in TARGET_NAME_MAPPING:
            target_name = TARGET_NAME_MAPPING[target_name]
        if target_name not in TARGET_NAME_INFO:
            import_util.announce_unknown_target_name(target_name)
            return None
        new_target_list.append(TARGET_NAME_INFO[target_name][2])
    ret = ','.join(sorted(new_target_list))

    if impglobals.ARGUMENTS.import_report_inventory_mismatch:
        used_targets = metadata['used_surface_geo_targets']
        used_target_list = []
        for target_name in used_targets:
            if target_name in TARGET_NAME_MAPPING:
                target_name = TARGET_NAME_MAPPING[target_name]
            if target_name not in TARGET_NAME_INFO:
                import_util.announce_unknown_target_name(target_name)
                return None
            used_target_list.append(TARGET_NAME_INFO[target_name][2])
        used_str = ','.join(sorted(used_target_list))

        if ret != used_str:
            # It's OK if the surface geo has the central planet but the
            # inventory doesn't
            for planet in ['Jupiter', 'Saturn', 'Uranus', 'Neptune',
                            'Pluto']:
                try:
                    used_target_list.remove(planet)
                except ValueError:
                    pass
            used_str = ','.join(sorted(used_target_list))
            if ret != used_str:
                import_util.log_nonrepeating_warning(
                    f'Inventory and surface geo differ: {ret} vs {used_str}')

    return ret
