################################################################################
# obs_type_image.py
#
# Defines the ObsTypeImage class, which encapsulates fields in the
# obs_type_image table.
################################################################################

from functools import cached_property
import json
import os

import pdsfile

import impglobals
import import_util

from obs_base import ObsBase


class ObsTypeImage(ObsBase):
    def __init__(self, *args, **kwargs):
        super().__init__(args, kwargs)


    ####################################
    ### FIELD METHODS FOR THIS TABLE ###
    ####################################

    # Because the obs_type_image table has an entry for all observations,
    # we provide a default for all fields and don't require subclasses to
    # override the methods.

    @property
    def field_image_type_id(self):
        return None

    @property
    def field_duration(self):
        return None

    @property
    def field_levels(self):
        return None

    @property
    def field_greater_pixel_size(self):
        return None

    @property
    def field_lesser_pixel_size(self):
        return None
