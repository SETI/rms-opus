################################################################################
# obs_cassini_common_pds4.py
#
# Defines the ObsCassiniCommonPDS4 class, which augments ObsCassiniCommon with
# methods that are PDS4-specific.
# Currently, none of the Cassini PDS4 migrations have been imported into OPUS
# yet (and so this PDS4 class simply inherits from the shared Cassini Common,
# using the attributes deduced from the OBSERVATION_ID).
################################################################################

from obs_common_pds4 import ObsCommonPDS4
from obs_cassini_common import ObsCassiniCommon


class ObsCassiniCommonPDS4(ObsCommonPDS4, ObsCassiniCommon):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
