################################################################################
# config_bundle_info.py
#
# Defines the BUNDLE_INFO structure, which gives information about how to
# import each bundle/volume.
################################################################################

# flake8: noqa

from obs_volume_cocirs_56xxx       import ObsVolumeCOCIRS56xxx
from obs_volume_cocirs_01xxx       import ObsVolumeCOCIRS01xxx
from obs_volume_coiss_12xxx        import ObsVolumeCOISS12xxx
from obs_volume_corss_8xxx         import ObsVolumeCORSS8xxx
from obs_volume_couvis_0xxx        import ObsVolumeCOUVIS0xxx
from obs_volume_couvis_8xxx        import ObsVolumeCOUVIS8xxx
from obs_volume_covims_0xxx        import ObsVolumeCOVIMS0xxx
from obs_volume_covims_8xxx        import ObsVolumeCOVIMS8xxx
from obs_volume_ebrocc_xxxx        import ObsVolumeEBROCCxxxx
from obs_volume_go_0xxx            import ObsVolumeGO0xxx
from obs_volume_hstjx_xxxx         import ObsVolumeHSTJxxxxx
from obs_volume_hstnx_xxxx         import ObsVolumeHSTNxxxxx
from obs_volume_hstox_xxxx         import ObsVolumeHSTOxxxxx
from obs_volume_hstix_xxxx         import ObsVolumeHSTIxxxxx
from obs_volume_hstux_xxxx         import ObsVolumeHSTUxxxxx
from obs_volume_nhxxlo_xxxx        import ObsVolumeNHxxLOXxxx
from obs_volume_nhxxmv_xxxx        import ObsVolumeNHxxMVXxxx
from obs_volume_vgiss_5678xxx      import ObsVolumeVGISS5678xxx
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
#   - temporal_camera: True if the observation can span multiple time steps. This
#       is used to determine whether the gridless ring and surface geo fields
#       should have identical min/max, or whether it's OK for them to be different.
#       When True, we assume that the observation happens over such a long time
#       period that things like ring center distance can vary.
#   - instrument_class: The Python class, imported above, that will handle the
#       import.

BUNDLE_INFO = [
    (r'COCIRS_0[0123]\d\d|COCIRS_0401',     # We ignore these volumes from early
        {'primary_index': None,             # in the cruise without metadata
         'validate_index_rows': False,
         'temporal_camera': True,
         'instrument_class': None},
    ),
    (r'COCIRS_040[2-9]|COCIRS_041\d|COCIRS_0[5-9]\d\d|COCIRS_1\d\d\d', # COCIRS_0402->
        {'primary_index': ('<BUNDLE>_cube_equi_index.lbl',
                           '<BUNDLE>_cube_point_index.lbl',
                           '<BUNDLE>_cube_ring_index.lbl'),
         'validate_index_rows': False,
         'temporal_camera': True,
         'instrument_class': ObsVolumeCOCIRS01xxx},
    ),
    (r'COCIRS_[56]\d\d\d',
        {'primary_index': ('OBSINDEX.LBL',),
         'validate_index_rows': False,
         'temporal_camera': True,
         'instrument_class': ObsVolumeCOCIRS56xxx},
    ),
    (r'COISS_[12]\d\d\d',
        {'primary_index': ('<BUNDLE>_index.lbl',),
         'validate_index_rows': False,
         'temporal_camera': False,
         'instrument_class': ObsVolumeCOISS12xxx},
    ),
    (r'CORSS_8001',
        {'primary_index': ('<BUNDLE>_index.lbl',),
         'validate_index_rows': True,
         'temporal_camera': True,
         'instrument_class': ObsVolumeCORSS8xxx},
    ),
    (r'COUVIS_0\d\d\d',
        {'primary_index': ('<BUNDLE>_index.lbl',),
         'validate_index_rows': False,
         'temporal_camera': True,
         'instrument_class': ObsVolumeCOUVIS0xxx},
    ),
    (r'COUVIS_8001',
        {'primary_index': ('<BUNDLE>_index.lbl',),
         'validate_index_rows': True,
         'temporal_camera': True,
         'instrument_class': ObsVolumeCOUVIS8xxx},
    ),
    (r'COVIMS_0\d\d\d',
        {'primary_index': ('<BUNDLE>_index.lbl',),
         'validate_index_rows': False,
         'temporal_camera': True,
         'instrument_class': ObsVolumeCOVIMS0xxx},
    ),
    (r'COVIMS_8001',
        {'primary_index': ('<BUNDLE>_index.lbl',),
         'validate_index_rows': True,
         'temporal_camera': True,
         'instrument_class': ObsVolumeCOVIMS8xxx},
    ),
    (r'EBROCC_0001',
        {'primary_index': ('<BUNDLE>_index.lbl',),
         'validate_index_rows': True,
         'temporal_camera': True,
         'instrument_class': ObsVolumeEBROCCxxxx},
    ),
    (r'GO_0001',
        {'primary_index': None,
         'validate_index_rows': False,
         'temporal_camera': False,
         'instrument_class': None},
    ),
    (r'GO_000[2-9]|GO_001\d|GO_002\d',
        {'primary_index': ('<BUNDLE>_index.lbl', '<BUNDLE>_sl9_index.lbl'),
         'validate_index_rows': True,
         'temporal_camera': False,
         'instrument_class': ObsVolumeGO0xxx},
    ),
    (r'HSTI\d_\d\d\d\d',
        {'primary_index': ('<BUNDLE>_index.lbl',),
         'validate_index_rows': False,
         'temporal_camera': False,
         'instrument_class': ObsVolumeHSTIxxxxx},
    ),
    (r'HSTJ\d_\d\d\d\d',
        {'primary_index': ('<BUNDLE>_index.lbl',),
         'validate_index_rows': False,
         'temporal_camera': False,
         'instrument_class': ObsVolumeHSTJxxxxx},
    ),
    (r'HSTN\d_\d\d\d\d',
        {'primary_index': ('<BUNDLE>_index.lbl',),
         'validate_index_rows': False,
         'temporal_camera': False,
         'instrument_class': ObsVolumeHSTNxxxxx},
    ),
    (r'HSTO\d_\d\d\d\d',
        {'primary_index': ('<BUNDLE>_index.lbl',),
         'validate_index_rows': False,
         'temporal_camera': False,
         'instrument_class': ObsVolumeHSTOxxxxx},
    ),
    (r'HSTU\d_\d\d\d\d',
        {'primary_index': ('<BUNDLE>_index.lbl',),
         'validate_index_rows': False,
         'temporal_camera': False,
         'instrument_class': ObsVolumeHSTUxxxxx},
    ),
    (r'NH..LO_1001',
        {'primary_index': ('<BUNDLE>_index.lbl',),
         'validate_index_rows': True,
         'temporal_camera': False,
         'instrument_class': ObsVolumeNHxxLOXxxx},
    ),
    (r'NH..MV_1001',
        {'primary_index': ('<BUNDLE>_index.lbl',),
         'validate_index_rows': True,
         'temporal_camera': True,
         'instrument_class': ObsVolumeNHxxMVXxxx},
    ),
    (r'NH...._2\d\d\d',  # Ignore these volumes - we only import 1001
        {'primary_index': None,
         'validate_index_rows': False,
         'temporal_camera': False,
         'instrument_class': None},
    ),
    (r'VGISS_[5678]\d\d\d',
        {'primary_index': ('<BUNDLE>_raw_image_index.lbl',),
         'validate_index_rows': False,
         'temporal_camera': False,
         'instrument_class': ObsVolumeVGISS5678xxx},
    ),
    (r'VG_2801',
        {'primary_index': ('<BUNDLE>_index.lbl',),
         'validate_index_rows': True,
         'temporal_camera': True,
         'instrument_class': ObsVolumeVG28xxVGPPS},
    ),
    (r'VG_2802',
        {'primary_index': ('<BUNDLE>_index.lbl',),
         'validate_index_rows': True,
         'temporal_camera': True,
         'instrument_class': ObsInstrumentVG28xxVGUVS},
         'instrument_class': ObsVolumeVG28xxVGUVS},
    ),
    (r'VG_2803',
        {'primary_index': ('<BUNDLE>_index.lbl',),
         'validate_index_rows': True,
         'temporal_camera': True,
         'instrument_class': ObsVolumeVG28xxVGRSS},
    ),
    (r'VG_2810',
        {'primary_index': ('<BUNDLE>_index.lbl',),
         'validate_index_rows': True,
         'temporal_camera': True,
         'instrument_class': ObsVolumeVG28xxVGISS},
    ),
]
