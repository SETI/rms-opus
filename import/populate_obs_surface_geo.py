################################################################################
# populate_obs_surface_geo.py
#
# Routines to populate fields in the obs_surface_geometry__<T> tables.
################################################################################

from config_data import *

def populate_obs_surface_geo_target_name(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    surface_geo_row = metadata['body_surface_geo_row']
    index_row_num = metadata['index_row_num']

    target_name = surface_geo_row['TARGET_NAME'].upper()
    if target_name in TARGET_NAME_MAPPING:
        target_name = TARGET_NAME_MAPPING[target_name]
    if target_name not in TARGET_NAME_INFO:
        import_util.announce_unknown_target_name(target_name, index_row_num)
        return None
    return (target_name, target_name.title())
