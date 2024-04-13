################################################################################
# obs_common_pds3.py
#
# Defines the ObsCommonPDS3 class, which is a simple class that inherits from
# all of the classes that are common to all observations.
################################################################################

from obs_general_pds3 import ObsGeneralPDS3
from obs_pds_pds3 import ObsPdsPDS3
from obs_type_image import ObsTypeImage
from obs_wavelength import ObsWavelength
from obs_profile_pds3 import ObsProfilePDS3
from obs_ring_geometry import ObsRingGeometry
from obs_surface_geometry import ObsSurfaceGeometry
from obs_surface_geometry_name import ObsSurfaceGeometryName
from obs_surface_geometry_target import ObsSurfaceGeometryTarget


class ObsCommonPDS3(ObsGeneralPDS3, ObsPdsPDS3, ObsTypeImage, ObsWavelength,
                    ObsProfilePDS3, ObsRingGeometry, ObsSurfaceGeometry,
                    ObsSurfaceGeometryName, ObsSurfaceGeometryTarget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
