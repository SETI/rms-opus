################################################################################
# populate_obs_pds.py
#
# Routines to populate fields in the obs_pds table.
################################################################################

import julian

from config_data import *
import impglobals
import import_util


################################################################################
# THESE ARE SPECIFIC TO OBS_PDS
################################################################################

def populate_obs_pds_product_creation_time_sec(**kwargs):
    metadata = kwargs['metadata']
    general_row = metadata['obs_pds_row']
    product_time = general_row['product_creation_time']

    if product_time is None:
        return None

    try:
        product_time_sec = julian.tai_from_iso(product_time)
    except Exception as e:
        import_util.log_nonrepeating_error(
            f'Bad product creation time format "{product_time}": {e}')
        return None

    return product_time_sec
