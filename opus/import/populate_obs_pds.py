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

    return julian.tai_from_iso(product_time)
