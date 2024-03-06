################################################################################
# obs_common_pds4.py
#
# Defines the ObsCommonPDS4 class, which is a simple class that inherits from
# all of the classes that are common to all observations.
################################################################################

from obs_general_pds4 import ObsGeneralPDS4
from obs_pds_pds4 import ObsPdsPDS4
from obs_type_image import ObsTypeImage
from obs_wavelength import ObsWavelength
from obs_profile import ObsProfile
from obs_ring_geometry import ObsRingGeometry
from obs_surface_geometry import ObsSurfaceGeometry
from obs_surface_geometry_name import ObsSurfaceGeometryName
from obs_surface_geometry_target import ObsSurfaceGeometryTarget


class ObsCommonPDS4(ObsGeneralPDS4, ObsPdsPDS4, ObsTypeImage, ObsWavelength,
                    ObsProfile, ObsRingGeometry, ObsSurfaceGeometry,
                    ObsSurfaceGeometryName, ObsSurfaceGeometryTarget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
