"""The PDS3 variant of the ``obs_pds`` table module.

A PDS3 product has a data set id and a product id, and records when it was created in
one of several indexes -- which is what the helpers here reconcile. It has no logical
identifier, so that column stays empty.
"""

from typing import cast

from opus_import.obs.field_types import FloatField, StrField
from opus_import.obs.obs_base_pds3 import ObsBasePDS3
from opus_import.obs.obs_pds import ObsPds


class ObsPdsPDS3(ObsPds, ObsBasePDS3):
    """The ``obs_pds`` columns for a PDS3 product.

    Its ``field_obs_*`` methods each fill the schema column their name ends in,
    declaring the type `opus_import.obs.field_types` gives that column.
    """

    # Product creation time helpers


    def _product_creation_time_from_index(self) -> FloatField:
        """Read when this product was created, from the primary index row.

        Returns:
            The time in seconds TAI, or None if the column is missing or unparsable.
        """
        return self._time_from_index(column='PRODUCT_CREATION_TIME')

    def _product_creation_time_from_supp_index(self) -> FloatField:
        """Read when this product was created, from the supplemental index row.

        Returns:
            The time in seconds TAI, or None if the column is missing or unparsable.
        """
        return self._time_from_supp_index(column='PRODUCT_CREATION_TIME')

    def _product_creation_time_from_some_index(self) -> FloatField:
        """Read when this product was created, from whichever index row carries it.

        Returns:
            The time in seconds TAI, or None if the column is missing or unparsable.
        """
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
