################################################################################
# obs_type_image.py
#
# Defines the ObsTypeImage class, which encapsulates fields in the
# obs_type_image table.
################################################################################

from obs_base import ObsBase


class ObsTypeImage(ObsBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


    ####################################
    ### FIELD METHODS FOR THIS TABLE ###
    ####################################

    @property
    def field_obs_type_image_opus_id(self):
        return self.opus_id

    @property
    def field_obs_type_image_volume_id(self):
        return self.volume

    @property
    def field_obs_type_image_instrument_id(self):
        return self.instrument_id


    # Because the obs_type_image table has an entry for all observations,
    # we provide a default for all fields and don't require subclasses to
    # override the methods.

    @property
    def field_type_image_image_type_id(self):
        return None

    @property
    def field_type_image_duration(self):
        return None

    @property
    def field_type_image_levels(self):
        return None

    @property
    def field_type_image_greater_pixel_size(self):
        return None

    @property
    def field_type_image_lesser_pixel_size(self):
        return None
