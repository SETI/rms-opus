"""The PDS4 variant of the ``obs_pds`` table module.

A PDS4 product is identified by its logical identifier rather than by a data set id, and
both are stored so that a search can use either.
"""

from typing import cast

from opus_import.obs.field_types import FloatField, StrField
from opus_import.obs.obs_base_pds4 import ObsBasePDS4
from opus_import.obs.obs_pds import ObsPds


class ObsPdsPDS4(ObsPds, ObsBasePDS4):
    """The ``obs_pds`` columns for a PDS4 product.

    Its ``field_obs_*`` methods each fill the schema column their name ends in,
    declaring the type `opus_import.obs.field_types` gives that column.
    """

    ####################################
    ### FIELD METHODS FOR THIS TABLE ###
    ####################################

    ################################
    ### ! Might override these ! ###
    ################################


    def field_obs_pds_data_set_id(self) -> StrField:
        return None  # Field not used for PDS4

    def field_obs_pds_product_id(self) -> StrField:
        return None  # Field not used for PDS4

    def field_obs_pds_product_creation_time(self) -> FloatField:
        return self._time_from_index(column='pds:creation_date_time')

    def field_obs_pds_primary_lid(self) -> StrField:
        return cast(StrField, self._index_col('pds:logical_identifier'))
