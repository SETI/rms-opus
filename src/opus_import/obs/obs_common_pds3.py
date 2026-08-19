################################################################################
# obs_common_pds3.py
#
# Defines the ObsCommonPDS3 class, which is a simple class that inherits from
# all of the classes that are common to all observations.
################################################################################

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
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
