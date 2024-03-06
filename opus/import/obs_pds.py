################################################################################
# obs_pds.py
#
# Defines the ObsPds class, which encapsulates fields in the
# obs_pds table.
################################################################################

from obs_base import ObsBase


class ObsPds(ObsBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


    ####################################
    ### FIELD METHODS FOR THIS TABLE ###
    ####################################

    ### Don't override these ###

    def field_obs_pds_opus_id(self):
        return self.opus_id

    def field_obs_pds_bundle_id(self):
        return self.bundle

    def field_obs_pds_instrument_id(self):
        return self.instrument_id

    def field_obs_pds_primary_filespec(self):
        return self.primary_filespec


    ################################
    ### ! Might override these ! ###
    ################################

    def field_obs_pds_data_set_id(self):
        raise NotImplementedError

    def field_obs_pds_product_id(self):
        raise NotImplementedError

    def field_obs_pds_product_creation_time(self):
        raise NotImplementedError

    def field_obs_pds_primary_lid(self):
        raise NotImplementedError

    def field_obs_pds_note(self):
        return None


    ###################################
    ### !!! Must override these !!! ###
    ###################################
