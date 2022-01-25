################################################################################
# obs_profile.py
#
# Defines the ObsProfile class, which encapsulates fields in the
# obs_profile table.
################################################################################

from functools import cached_property
import json
import os

import pdsfile

import impglobals
import import_util

from obs_base import ObsBase


class ObsProfile(ObsBase):
    def __init__(self, *args, **kwargs):
        super().__init__(args, kwargs)


    ####################################
    ### FIELD METHODS FOR THIS TABLE ###
    ####################################

    # Because the obs_profile table has an entry for all observations,
    # we provide a default for all fields and don't require subclasses to
    # override the methods.

    @property
    def field_occ_type(self):
        return None

    @property
    def field_occ_dir(self):
        return None

    @property
    def field_body_occ_flag(self):
        return None

    @property
    def field_temporal_sampling(self):
        return None

    @property
    def field_quality_score(self):
        return None

    @property
    def field_optical_depth1(self):
        return None

    @property
    def field_optical_depth2(self):
        return None

    @property
    def field_wl_band(self):
        return None

    @property
    def field_source(self):
        return None

    @property
    def field_host(self):
        return None
