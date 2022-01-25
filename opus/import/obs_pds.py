################################################################################
# obs_pds.py
#
# Defines the ObsPds class, which encapsulates fields in the
# obs_pds table.
################################################################################

from functools import cached_property
import json
import os

import pdsfile

import impglobals
import import_util

from obs_base import ObsBase


class ObsPds(ObsBase):
    def __init__(self, *args, **kwargs):
        super().__init__(args, kwargs)


    ####################################
    ### FIELD METHODS FOR THIS TABLE ###
    ####################################

    @property
    def field_data_set_id(self):
        raise NotImplementedError

    @property
    def field_product_id(self):
        raise NotImplementedError

    @property
    def field_product_creation_time(self):
        raise None

    @property
    def field_note(self):
        raise None
