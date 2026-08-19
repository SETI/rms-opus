################################################################################
# obs_common_pds4.py
#
# Defines the ObsCommonPDS4 class, which is a simple class that inherits from
# all of the classes that are common to all observations.
################################################################################

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
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
