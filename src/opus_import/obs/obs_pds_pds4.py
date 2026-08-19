################################################################################
# obs_pds_pds4.py
#
# Defines the ObsPdsPDS4 class, which augments ObsPds with methods that are
# PDS4-specific.
################################################################################

from obs_base_pds4 import ObsBasePDS4
from obs_pds import ObsPds


class ObsPdsPDS4(ObsPds, ObsBasePDS4):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


    ####################################
    ### FIELD METHODS FOR THIS TABLE ###
    ####################################

    ################################
    ### ! Might override these ! ###
    ################################

    def field_obs_pds_data_set_id(self):
        return None  # Field not used for PDS4

    def field_obs_pds_product_id(self):
        return None  # Field not used for PDS4

    def field_obs_pds_product_creation_time(self):
        return self._time_from_index(column='pds:creation_date_time')

    def field_obs_pds_primary_lid(self):
        return self._index_col('pds:logical_identifier')
