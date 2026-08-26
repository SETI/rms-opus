"""The PDS3 half of the hierarchy, assembled: every table a PDS3 observation fills.

`ObsCommonPDS3` introduces no behavior of its own. It exists so that a PDS3 mission
class names one base instead of nine, and so the order those nine are combined in is
written down once: a table module earlier in the list wins when two of them define the
same method.
"""

from opus_import.obs.obs_general_pds3 import ObsGeneralPDS3
from opus_import.obs.obs_pds_pds3 import ObsPdsPDS3
from opus_import.obs.obs_profile_pds3 import ObsProfilePDS3
from opus_import.obs.obs_ring_geometry import ObsRingGeometry
from opus_import.obs.obs_surface_geometry import ObsSurfaceGeometry
from opus_import.obs.obs_surface_geometry_name import ObsSurfaceGeometryName
from opus_import.obs.obs_surface_geometry_target import ObsSurfaceGeometryTarget
from opus_import.obs.obs_type_image import ObsTypeImage
from opus_import.obs.obs_wavelength import ObsWavelength


class ObsCommonPDS3(ObsGeneralPDS3, ObsPdsPDS3, ObsTypeImage, ObsWavelength,
                    ObsProfilePDS3, ObsRingGeometry, ObsSurfaceGeometry,
                    ObsSurfaceGeometryName, ObsSurfaceGeometryTarget):
    """Every table module a PDS3 observation needs, combined in one base class."""
