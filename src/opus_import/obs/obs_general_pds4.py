"""The PDS4 variant of the ``obs_general`` table module.

`opus_import.obs.obs_general` computes every column that does not depend on the PDS
version. This class supplies nothing further: a PDS4 bundle's target name and times come
from the bundle module or from `opus_import.obs.obs_base_pds4`, so the pairing exists to
put the PDS4 base into the class's own ancestry rather than to add behavior.
"""

from opus_import.obs.obs_base_pds4 import ObsBasePDS4
from opus_import.obs.obs_general import ObsGeneral


class ObsGeneralPDS4(ObsGeneral, ObsBasePDS4):
    """The ``obs_general`` columns for a PDS4 observation."""
