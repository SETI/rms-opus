################################################################################
# obs_common.py
#
# Defines the ObsCommon class, which is a simple class that inherits from all
# of the classes that are common to all observations.
################################################################################

from obs_general import ObsGeneral
from obs_pds import ObsPds
from obs_type_image import ObsTypeImage
from obs_wavelength import ObsWavelength
from obs_profile import ObsProfile
from obs_ring_geometry import ObsRingGeometry
from obs_surface_geometry import ObsSurfaceGeometry
from obs_surface_geometry_name import ObsSurfaceGeometryName
from obs_surface_geometry_target import ObsSurfaceGeometryTarget

class ObsCommon(ObsGeneral, ObsPds, ObsTypeImage, ObsWavelength, ObsProfile,
                ObsRingGeometry,
                ObsSurfaceGeometry, ObsSurfaceGeometryName, ObsSurfaceGeometryTarget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
