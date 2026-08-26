################################################################################
# obs_pds.py
#
# Defines the ObsPds class, which encapsulates fields in the
# obs_pds table.
################################################################################


from opus_import.obs.field_types import FloatField, StrField
from opus_import.obs.obs_base import ObsBase


class ObsPds(ObsBase):

    ####################################
    ### FIELD METHODS FOR THIS TABLE ###
    ####################################

    ### Don't override these ###

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
