"""The ``obs_type_image`` columns: an image's dimensions and its intensity levels.

One module per OPUS table, mixed into every obs class that fills the table. A column
whose value depends on the PDS version or on the instrument is left to a subclass, which
is why most of the methods here can be overridden and a few raise `NotImplementedError`
outright.
"""

from opus_import.obs.field_types import FloatField, IntField, MultFieldRet, StrField
from opus_import.obs.obs_base import ObsBase

# The number of distinct intensity levels a detector of a given bit depth records,
# which is what field_obs_type_image_levels reports.
EIGHT_BIT_IMAGE_LEVELS = 2**8
TWELVE_BIT_IMAGE_LEVELS = 2**12
SIXTEEN_BIT_IMAGE_LEVELS = 2**16


class ObsTypeImage(ObsBase):
    ####################################
    ### FIELD METHODS FOR THIS TABLE ###
    ####################################

    ### Don't override these ###

    """The ``obs_type_image`` columns: an image's size and its levels.

    Its ``field_obs_*`` methods each fill the schema column their name ends in,
    declaring the type `opus_import.obs.field_types` gives that column.
    """

    def field_obs_type_image_opus_id(self) -> StrField:
        return self.opus_id

    def field_obs_type_image_bundle_id(self) -> StrField:
        return self.bundle

    def field_obs_type_image_instrument_id(self) -> StrField:
        return self.instrument_id


    ################################
    ### ! Might override these ! ###
    ################################

    # Because the obs_type_image table has an entry for all observations,
    # we provide a default for all fields and don't require subclasses to
    # override the methods.

    def field_obs_type_image_image_type_id(self) -> MultFieldRet:
        return self._create_mult(None)

    def field_obs_type_image_duration(self) -> FloatField:
        # We don't make this field_obs_general_observation_duration by default because
        # we want it to be None if this observation isn't an image at all.
        return None

    def field_obs_type_image_levels(self) -> IntField:
        return None

    def field_obs_type_image_greater_pixel_size(self) -> IntField:
        return None

    def field_obs_type_image_lesser_pixel_size(self) -> IntField:
        return None
