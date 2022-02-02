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

    def field_obs_pds_volume_id(self):
        return self.volume

    def field_obs_pds_instrument_id(self):
        return self.instrument_id

    def field_obs_pds_primary_filespec(self):
        return self.primary_filespec


    ################################
    ### ! Might override these ! ###
    ################################

    def field_obs_pds_data_set_id(self):
        return self._some_index_or_label_col('DATA_SET_ID')

    def field_obs_pds_product_id(self):
        return self._some_index_or_label_col('PRODUCT_ID')

    def field_obs_pds_product_creation_time(self):
        return self._product_creation_time_from_some_index()

    def field_obs_pds_note(self):
        return None


    ###################################
    ### !!! Must override these !!! ###
    ###################################
