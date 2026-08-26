################################################################################
# obs_general_pds3.py
#
# Defines the ObsGeneralPDS3 class, which augments ObsGeneral with methods
# that are PDS3-specific.
################################################################################

from opus_import.obs.obs_base_pds3 import ObsBasePDS3
from opus_import.obs.obs_general import ObsGeneral


class ObsGeneralPDS3(ObsGeneral, ObsBasePDS3):
    def _target_name(self) -> list[tuple[str | None, str | None]]:
        target_name = self._some_index_or_label_col('TARGET_NAME')
        target_name, target_info = self._get_target_info(target_name)
        if target_info is None:
            return [(None, None)]
        return [(target_name, target_info[2])]
