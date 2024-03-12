################################################################################
# obs_general_pds4.py
#
# Defines the ObsGeneralPDS4 class, which augments ObsGeneral with methods
# that are PDS4-specific.
################################################################################

from obs_base_pds4 import ObsBasePDS4
from obs_general import ObsGeneral


class ObsGeneralPDS4(ObsGeneral, ObsBasePDS4):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
