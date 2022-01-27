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

    @property
    def field_obs_pds_opus_id(self):
        return self.opus_id

    @property
    def field_obs_pds_volume_id(self):
        return self.volume

    @property
    def field_obs_pds_instrument_id(self):
        return self.instrument_id

    @property
    def field_obs_pds_data_set_id(self):
        raise NotImplementedError

    @property
    def field_obs_pds_product_id(self):
        raise NotImplementedError

    @property
    def field_obs_pds_product_creation_time(self):
        return None

    @property
    def field_obs_pds_note(self):
        return None

    @property
    def field_obs_pds_primary_filespec(self):
        return self.primary_filespec
