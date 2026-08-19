################################################################################
# obs_general_pds3.py
#
# Defines the ObsGeneralPDS3 class, which augments ObsGeneral with methods
# that are PDS3-specific.
################################################################################

from obs_base_pds3 import ObsBasePDS3
from obs_general import ObsGeneral


class ObsGeneralPDS3(ObsGeneral, ObsBasePDS3):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _target_name(self):
        target_name = self._some_index_or_label_col('TARGET_NAME')
        target_name, target_info = self._get_target_info(target_name)
        if target_info is None:
            return [(None, None)]
        return [(target_name, target_info[2])]
