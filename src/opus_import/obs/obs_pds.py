"""The ``obs_pds`` columns: what the PDS archive says about the product: its data set, its
product id, and when it was made.

One module per OPUS table, mixed into every obs class that fills the table. A column
whose value depends on the PDS version or on the instrument is left to a subclass, which
is why most of the methods here can be overridden and a few raise `NotImplementedError`
outright.
"""

from opus_import.obs.field_types import FloatField, StrField
from opus_import.obs.obs_base import ObsBase


class ObsPds(ObsBase):

    ####################################
    ### FIELD METHODS FOR THIS TABLE ###
    ####################################

    ### Don't override these ###

    """The ``obs_pds`` columns: what the PDS archive says about the product.

    Its ``field_obs_*`` methods each fill the schema column their name ends in,
    declaring the type `opus_import.obs.field_types` gives that column.
    """

    def field_obs_pds_opus_id(self) -> StrField:
        return self.opus_id

    def field_obs_pds_bundle_id(self) -> StrField:
        return self.bundle

    def field_obs_pds_instrument_id(self) -> StrField:
        return self.instrument_id

    def field_obs_pds_primary_filespec(self) -> StrField:
        return self.primary_filespec


    ################################
    ### ! Might override these ! ###
    ################################

    def field_obs_pds_data_set_id(self) -> StrField:
        raise NotImplementedError

    def field_obs_pds_product_id(self) -> StrField:
        raise NotImplementedError

    def field_obs_pds_product_creation_time(self) -> FloatField:
        raise NotImplementedError

    def field_obs_pds_primary_lid(self) -> StrField:
        raise NotImplementedError

    def field_obs_pds_note(self) -> StrField:
        return None


    ###################################
    ### !!! Must override these !!! ###
    ###################################
