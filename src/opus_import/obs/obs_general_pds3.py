"""The PDS3 variant of the ``obs_general`` table module.

All it adds is where the target comes from: a PDS3 label records it in ``TARGET_NAME``,
in whichever index carries that column.
"""

from opus_import.obs.obs_base_pds3 import ObsBasePDS3
from opus_import.obs.obs_general import ObsGeneral


class ObsGeneralPDS3(ObsGeneral, ObsBasePDS3):
    """The ``obs_general`` columns for a PDS3 observation."""

    def _target_name(self) -> list[tuple[str | None, str | None]]:
        """Return the target this observation is of, from ``TARGET_NAME``.

        Returns:
            The corrected name and the name shown for it, as a one-element list, or
            ``[(None, None)]`` if the name is one this pipeline does not describe.
        """
        target_name = self._some_index_or_label_col('TARGET_NAME')
        target_name, target_info = self._get_target_info(target_name)
        if target_info is None:
            return [(None, None)]
        return [(target_name, target_info[2])]
