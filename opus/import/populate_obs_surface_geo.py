################################################################################
# populate_obs_surface_geo.py
#
# Routines to populate fields in the obs_surface_geometry,
# obs_surface_geometry_name, and obs_surface_geometry__<TARGET> tables.
################################################################################

from config_data import *

import impglobals
import import_util

# This is the target_name field in obs_surface_geometry that has the many-to-one
# mapping of rows to OPUS IDs
def populate_obs_surface_geo_name_target_name(**kwargs):
    metadata = kwargs['metadata']
    surface_geo_row = metadata['body_surface_geo_row']

    target_name = surface_geo_row['TARGET_NAME'].upper()
    if target_name in TARGET_NAME_MAPPING:
        target_name = TARGET_NAME_MAPPING[target_name]
    if target_name not in TARGET_NAME_INFO:
        import_util.announce_unknown_target_name(target_name)
        return None
    target_name_info = TARGET_NAME_INFO[target_name]
    # Check if there is a tooltip specified in TOOLTIPS_FOR_MULT
    table_name = kwargs['table_name']
    field_name = 'combined_filter'
    tooltip = import_util.get_mult_tooltip(table_name, field_name,
                                           target_name_info[2])
    return (target_name, target_name_info[2], tooltip)

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
