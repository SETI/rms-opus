"""The PDS4 half of the hierarchy, assembled: every table a PDS4 observation fills.

The PDS4 counterpart of `opus_import.obs.obs_common_pds3`, combining the same table
modules with the PDS4 variants of the three that have one.
"""

from opus_import.obs.obs_general_pds4 import ObsGeneralPDS4
from opus_import.obs.obs_pds_pds4 import ObsPdsPDS4
from opus_import.obs.obs_profile_pds4 import ObsProfilePDS4
from opus_import.obs.obs_ring_geometry import ObsRingGeometry
from opus_import.obs.obs_surface_geometry import ObsSurfaceGeometry
from opus_import.obs.obs_surface_geometry_name import ObsSurfaceGeometryName
from opus_import.obs.obs_surface_geometry_target import ObsSurfaceGeometryTarget
from opus_import.obs.obs_type_image import ObsTypeImage
from opus_import.obs.obs_wavelength import ObsWavelength


class ObsCommonPDS4(ObsGeneralPDS4, ObsPdsPDS4, ObsTypeImage, ObsWavelength,
                    ObsProfilePDS4, ObsRingGeometry, ObsSurfaceGeometry,
                    ObsSurfaceGeometryName, ObsSurfaceGeometryTarget):
    """Every table module a PDS4 observation needs, combined in one base class."""
