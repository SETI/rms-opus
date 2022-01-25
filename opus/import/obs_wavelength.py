################################################################################
# obs_wavelength.py
#
# Defines the ObsWavelength class, which encapsulates fields in the
# obs_wavelength table.
################################################################################

from functools import cached_property
import json
import os

import pdsfile

import impglobals
import import_util

from obs_base import ObsBase


class ObsWavelength(ObsBase):
    def __init__(self, *args, **kwargs):
        super().__init__(args, kwargs)


    ####################################
    ### FIELD METHODS FOR THIS TABLE ###
    ####################################

    # Because the obs_wavelength table has an entry for all observations,
    # we provide a default for all fields and don't require subclasses to
    # override the methods.

    @property
    def field_wavelength1(self):
        return None

    @property
    def field_wavelength2(self):
        return None

    @property
    def field_waveres1(self):
        return None

    @property
    def field_waveres2(self):
        return None

    @property
    def field_wave_no1(self):
        return None

    @property
    def field_wave_no2(self):
        return None

    @property
    def field_wave_no_res1(self):
        return None

    @property
    def field_wave_no_res2(self):
        return None

    @property
    def field_spec_flag(self):
        return 'N'

    @property
    def field_spec_size(self):
        return None

    @property
    def field_polarization_type(self):
        return 'NONE'
