################################################################################
# config_bundle_info.py
#
# Defines the BUNDLE_INFO structure, which gives information about how to
# import each bundle/volume.
################################################################################

# flake8: noqa

from obs_volume_cocirs             import ObsVolumeCOCIRS
from obs_volume_cocirs_cube        import ObsVolumeCOCIRSCube
from obs_volume_coiss              import ObsVolumeCOISS
from obs_volume_corss_occ          import ObsVolumeCORSSOcc
from obs_volume_couvis             import ObsVolumeCOUVIS
from obs_volume_couvis_occ         import ObsVolumeCOUVISOcc
from obs_volume_covims             import ObsVolumeCOVIMS
from obs_volume_covims_occ         import ObsVolumeCOVIMSOcc
from obs_volume_ebrocc             import ObsVolumeEBROCC
from obs_volume_gossi              import ObsVolumeGOSSI
from obs_volume_hstacs             import ObsVolumeHSTACS
from obs_volume_hstnicmos          import ObsVolumeHSTNICMOS
from obs_volume_hststis            import ObsVolumeHSTSTIS
from obs_volume_hstwfc3            import ObsVolumeHSTWFC3
from obs_volume_hstwfpc2           import ObsVolumeHSTWFPC2
from obs_volume_nhlorri            import ObsVolumeNHLORRI
from obs_volume_nhmvic             import ObsVolumeNHMVIC
from obs_volume_vgiss              import ObsVolumeVGISS
from obs_volume_vg28xx_vgiss       import ObsVolumeVG28xxVGISS
from obs_volume_vg28xx_vgpps_vguvs import (ObsVolumeVG28xxVGPPS,
                                               ObsVolumeVG28xxVGUVS)
from obs_volume_vg28xx_vgrss       import ObsVolumeVG28xxVGRSS


# The BUNDLE_INFO structure is used to determine the details of importing
# each distinct type of bundle/volume.
# - The first element of each tuple is a regular expression to match the bundle_id.
# - The second element of each tuple is a dictionary with these keys:
#   - primary_index: The name of the primary index file. <BUNDLE> will be
#       substituted with the current bundle/volume ID. This is used to distinguish
#       between plain index files and other special index files like
#       raw_image_index for VGISS.
#   - validate_index_rows: True if we should check the filespec for each row in
#       the primary index to see if filespec -> opus_id -> filespec is
#       idempotent. If it's not, we ignore this row. This is used to handle
#       index files that include multiple versions of each opus_id or information
#       on other support files. Basically this guarantees that only a single row
#       will be used for each opus_id.
#   - instrument_class: The Python class, imported above, that will handle the
#       import.

BUNDLE_INFO = [
    (r'COCIRS_0[0123]\d\d|COCIRS_0401',     # We ignore these volumes from early
        {'primary_index': None,             # in the cruise without metadata
         'validate_index_rows': False,
         'instrument_class': None},
    ),
    (r'COCIRS_040[2-9]|COCIRS_041\d|COCIRS_0[5-9]\d\d|COCIRS_1\d\d\d', # COCIRS_0402->
        {'primary_index': ('<BUNDLE>_cube_equi_index.lbl',
                           '<BUNDLE>_cube_point_index.lbl',
                           '<BUNDLE>_cube_ring_index.lbl'),
         'validate_index_rows': False,
         'instrument_class': ObsVolumeCOCIRSCube},
    ),
    (r'COCIRS_[56]\d\d\d',
        {'primary_index': ('OBSINDEX.LBL',),
         'validate_index_rows': False,
         'instrument_class': ObsVolumeCOCIRS},
    ),
    (r'COISS_[12]\d\d\d',
        {'primary_index': ('<BUNDLE>_index.lbl',),
         'validate_index_rows': False,
         'instrument_class': ObsVolumeCOISS},
    ),
    (r'CORSS_8001',
        {'primary_index': ('<BUNDLE>_index.lbl',),
         'validate_index_rows': True,
         'instrument_class': ObsVolumeCORSSOcc},
    ),
    (r'COUVIS_0\d\d\d',
        {'primary_index': ('<BUNDLE>_index.lbl',),
         'validate_index_rows': False,
         'instrument_class': ObsVolumeCOUVIS},
    ),
    (r'COUVIS_8001',
        {'primary_index': ('<BUNDLE>_index.lbl',),
         'validate_index_rows': True,
         'instrument_class': ObsVolumeCOUVISOcc},
    ),
    (r'COVIMS_0\d\d\d',
        {'primary_index': ('<BUNDLE>_index.lbl',),
         'validate_index_rows': False,
         'instrument_class': ObsVolumeCOVIMS},
    ),
    (r'COVIMS_8001',
        {'primary_index': ('<BUNDLE>_index.lbl',),
         'validate_index_rows': True,
         'instrument_class': ObsVolumeCOVIMSOcc},
    ),
    (r'EBROCC_0001',
        {'primary_index': ('<BUNDLE>_index.lbl',),
         'validate_index_rows': True,
         'instrument_class': ObsVolumeEBROCC},
    ),
    (r'GO_0001',
        {'primary_index': None,
         'validate_index_rows': False,
         'instrument_class': None},
    ),
    (r'GO_000[2-9]|GO_001\d|GO_002\d',
        {'primary_index': ('<BUNDLE>_index.lbl', '<BUNDLE>_sl9_index.lbl'),
         'validate_index_rows': True,
         'instrument_class': ObsVolumeGOSSI},
    ),
    (r'HSTI\d_\d\d\d\d',
        {'primary_index': ('<BUNDLE>_index.lbl',),
         'validate_index_rows': False,
         'instrument_class': ObsVolumeHSTWFC3},
    ),
    (r'HSTJ\d_\d\d\d\d',
        {'primary_index': ('<BUNDLE>_index.lbl',),
         'validate_index_rows': False,
         'instrument_class': ObsVolumeHSTACS},
    ),
    (r'HSTN\d_\d\d\d\d',
        {'primary_index': ('<BUNDLE>_index.lbl',),
         'validate_index_rows': False,
         'instrument_class': ObsVolumeHSTNICMOS},
    ),
    (r'HSTO\d_\d\d\d\d',
        {'primary_index': ('<BUNDLE>_index.lbl',),
         'validate_index_rows': False,
         'instrument_class': ObsVolumeHSTSTIS},
    ),
    (r'HSTU\d_\d\d\d\d',
        {'primary_index': ('<BUNDLE>_index.lbl',),
         'validate_index_rows': False,
         'instrument_class': ObsVolumeHSTWFPC2},
    ),
    (r'NH..LO_1001',
        {'primary_index': ('<BUNDLE>_index.lbl',),
         'validate_index_rows': True,
         'instrument_class': ObsVolumeNHLORRI},
    ),
    (r'NH..MV_1001',
        {'primary_index': ('<BUNDLE>_index.lbl',),
         'validate_index_rows': True,
         'instrument_class': ObsVolumeNHMVIC},
    ),
    (r'NH...._2\d\d\d',  # Ignore these volumes - we only import 1001
        {'primary_index': None,
         'validate_index_rows': False,
         'instrument_class': None},
    ),
    (r'VGISS_[5678]\d\d\d',
        {'primary_index': ('<BUNDLE>_raw_image_index.lbl',),
         'validate_index_rows': False,
         'instrument_class': ObsVolumeVGISS},
    ),
    (r'VG_2801',
        {'primary_index': ('<BUNDLE>_index.lbl',),
         'validate_index_rows': True,
         'instrument_class': ObsVolumeVG28xxVGPPS},
    ),
    (r'VG_2802',
        {'primary_index': ('<BUNDLE>_index.lbl',),
         'validate_index_rows': True,
         'instrument_class': ObsVolumeVG28xxVGUVS},
    ),
    (r'VG_2803',
        {'primary_index': ('<BUNDLE>_index.lbl',),
         'validate_index_rows': True,
         'instrument_class': ObsVolumeVG28xxVGRSS},
    ),
    (r'VG_2810',
        {'primary_index': ('<BUNDLE>_index.lbl',),
         'validate_index_rows': True,
         'instrument_class': ObsVolumeVG28xxVGISS},
    ),
]
