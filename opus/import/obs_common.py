################################################################################
# obs_common.py
#
# Defines the ObsCommon class, which is a simple class that inherits from all
# of the classes that are common to all observations.
################################################################################

from functools import cached_property
import json
import os

import pdsfile

import impglobals
import import_util

from obs_general import ObsGeneral
from obs_pds import ObsPds
from obs_type_image import ObsTypeImage
from obs_wavelength import ObsWavelength
from obs_profile import ObsProfile


class ObsCommon(ObsGeneral, ObsPds, ObsTypeImage, ObsWavelength, ObsProfile):
    def __init__(self, *args, **kwargs):
        super().__init__(args, kwargs)
