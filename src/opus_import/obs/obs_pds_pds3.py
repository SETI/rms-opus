################################################################################
# obs_pds_pds3.py
#
# Defines the ObsPdsPDS3 class, which augments ObsPds with methods that are
# PDS3-specific.
################################################################################

from typing import cast

from opus_import.obs.field_types import FloatField, StrField
from opus_import.obs.obs_base_pds3 import ObsBasePDS3
from opus_import.obs.obs_pds import ObsPds


class ObsPdsPDS3(ObsPds, ObsBasePDS3):
    # Product creation time helpers

    def _product_creation_time_from_index(self) -> FloatField:
        return self._time_from_index(column='PRODUCT_CREATION_TIME')

    def _product_creation_time_from_supp_index(self) -> FloatField:
        return self._time_from_supp_index(column='PRODUCT_CREATION_TIME')

    def _product_creation_time_from_some_index(self) -> FloatField:
        return self._time_from_some_index(column='PRODUCT_CREATION_TIME')


    ####################################
    ### FIELD METHODS FOR THIS TABLE ###
    ####################################

    ################################
    ### ! Might override these ! ###
    ################################

    def field_obs_pds_data_set_id(self) -> StrField:
        return cast(StrField, self._some_index_or_label_col('DATA_SET_ID'))

    def field_obs_pds_product_id(self) -> StrField:
        return cast(StrField, self._some_index_or_label_col('PRODUCT_ID'))

    def field_obs_pds_product_creation_time(self) -> FloatField:
        return self._product_creation_time_from_some_index()

    def field_obs_pds_primary_lid(self) -> StrField:
        return None  # Field not used for PDS3
