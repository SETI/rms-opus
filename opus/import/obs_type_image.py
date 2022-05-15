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

    ### Don't override these ###

    def field_obs_type_image_opus_id(self):
        return self.opus_id

    def field_obs_type_image_volume_id(self):
        return self.volume

    def field_obs_type_image_instrument_id(self):
        return self.instrument_id


    ################################
    ### ! Might override these ! ###
    ################################

    # Because the obs_type_image table has an entry for all observations,
    # we provide a default for all fields and don't require subclasses to
    # override the methods.

    def field_obs_type_image_image_type_id(self):
        return self._create_mult(None)

    def field_obs_type_image_duration(self):
        # We don't make this field_obs_general_observation_duration by default because
        # we want it to be None if this observation isn't an image at all.
        return None

    def field_obs_type_image_levels(self):
        return None

    def field_obs_type_image_greater_pixel_size(self):
        return None

    def field_obs_type_image_lesser_pixel_size(self):
        return None
