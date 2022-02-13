################################################################################
# config_volume_info.py
#
# Defines the VOLUME_INFO structure, which gives information about how to
# import each volume.
################################################################################

# flake8: noqa

from obs_instrument_coiss              import ObsInstrumentCOISS
from obs_instrument_corss_occ          import ObsInstrumentCORSSOcc
from obs_instrument_couvis             import ObsInstrumentCOUVIS
from obs_instrument_couvis_occ         import ObsInstrumentCOUVISOcc
from obs_instrument_covims             import ObsInstrumentCOVIMS
from obs_instrument_covims_occ         import ObsInstrumentCOVIMSOcc
from obs_instrument_ebrocc             import ObsInstrumentEBROCC
from obs_instrument_gossi              import ObsInstrumentGOSSI
from obs_instrument_hstacs             import ObsInstrumentHSTACS
from obs_instrument_hstnicmos          import ObsInstrumentHSTNICMOS
from obs_instrument_hststis            import ObsInstrumentHSTSTIS
from obs_instrument_hstwfc3            import ObsInstrumentHSTWFC3
from obs_instrument_hstwfpc2           import ObsInstrumentHSTWFPC2
from obs_instrument_nhlorri            import ObsInstrumentNHLORRI
from obs_instrument_nhmvic             import ObsInstrumentNHMVIC
from obs_instrument_vgiss              import ObsInstrumentVGISS
from obs_instrument_vg28xx_vgiss       import ObsInstrumentVG28xxVGISS
from obs_instrument_vg28xx_vgpps_vguvs import (ObsInstrumentVG28xxVGPPS,
                                               ObsInstrumentVG28xxVGUVS)
from obs_instrument_vg28xx_vgrss       import ObsInstrumentVG28xxVGRSS


# The VOLUME_INFO structure is used to determine the details of importing
# each distinct type of volume.
# - The first element of each tuple is a regular expression to match the volume_id.
# - The second element of each tuple is a dictionary with these keys:
#   - primary_index: The name of the primary index file. <VOLUME> will be
#       substituted with the current volume ID. This is used to distinguish between
#       plain index files, profile_index, and other special index files like
#       raw_image_index for VGISS.
#   - validate_index_rows: True if we should check the filespec for each row in
#       the primary index to see if filespec -> opus_id -> filespec is
#       idempotent. If it's not, we ignore this row. This is used to handle
#       index files that include multiple versions of each opus_id or information
#       on other support files. Basically this guarantees that only a single row
#       will be used for each opus_id.
#   - instrument_class: The Python class, imported above, that will handle the
#       import.

VOLUME_INFO = [
    (r'EBROCC_0001',
        # We would like to get rid of this profile_index, but the normal index
        # has "UNK" for the start/stop times for LICK. Once this is fixed we can
        # revisit.
        {'primary_index': '<VOLUME>_profile_index.lbl',
         'validate_index_rows': False,
         'instrument_class': ObsInstrumentEBROCC},
    ),
    (r'COISS_[12]\d\d\d',
        {'primary_index': '<VOLUME>_index.lbl',
         'validate_index_rows': False,
         'instrument_class': ObsInstrumentCOISS},
    ),
    (r'CORSS_8001',
        {'primary_index': '<VOLUME>_index.lbl',
         'validate_index_rows': True,
         'instrument_class': ObsInstrumentCORSSOcc},
    ),
    (r'COUVIS_0\d\d\d',
        {'primary_index': '<VOLUME>_index.lbl',
         'validate_index_rows': False,
         'instrument_class': ObsInstrumentCOUVIS},
    ),
    (r'COUVIS_8001',
        {'primary_index': '<VOLUME>_index.lbl',
         'validate_index_rows': True,
         'instrument_class': ObsInstrumentCOUVISOcc},
    ),
    (r'COVIMS_0\d\d\d',
        {'primary_index': '<VOLUME>_index.lbl',
         'validate_index_rows': False,
         'instrument_class': ObsInstrumentCOVIMS},
    ),
    (r'COVIMS_8001',
        {'primary_index': '<VOLUME>_index.lbl',
         'validate_index_rows': True,
         'instrument_class': ObsInstrumentCOVIMSOcc},
    ),
    (r'GO_00\d\d',
        {'primary_index': '<VOLUME>_index.lbl',
         'validate_index_rows': True,
         'instrument_class': ObsInstrumentGOSSI},
    ),
    (r'HSTI\d_\d\d\d\d',
        {'primary_index': '<VOLUME>_index.lbl',
         'validate_index_rows': False,
         'instrument_class': ObsInstrumentHSTWFC3},
    ),
    (r'HSTJ\d_\d\d\d\d',
        {'primary_index': '<VOLUME>_index.lbl',
         'validate_index_rows': False,
         'instrument_class': ObsInstrumentHSTACS},
    ),
    (r'HSTN\d_\d\d\d\d',
        {'primary_index': '<VOLUME>_index.lbl',
         'validate_index_rows': False,
         'instrument_class': ObsInstrumentHSTNICMOS},
    ),
    (r'HSTO\d_\d\d\d\d',
        {'primary_index': '<VOLUME>_index.lbl',
         'validate_index_rows': False,
         'instrument_class': ObsInstrumentHSTSTIS},
    ),
    (r'HSTU\d_\d\d\d\d',
        {'primary_index': '<VOLUME>_index.lbl',
         'validate_index_rows': False,
         'instrument_class': ObsInstrumentHSTWFPC2},
    ),
    (r'NH..LO_[12]001',
        {'primary_index': '<VOLUME>_index.lbl',
         'validate_index_rows': True,
         'instrument_class': ObsInstrumentNHLORRI},
    ),
    (r'NH..MV_[12]001',
        {'primary_index': '<VOLUME>_index.lbl',
         'validate_index_rows': True,
         'instrument_class': ObsInstrumentNHMVIC},
    ),
    (r'VGISS_[5678]\d\d\d',
        {'primary_index': '<VOLUME>_raw_image_index.lbl',
         'validate_index_rows': False,
         'instrument_class': ObsInstrumentVGISS},
    ),
    (r'VG_2801',
        {'primary_index': '<VOLUME>_profile_index.lbl',
         'validate_index_rows': False,
         'instrument_class': ObsInstrumentVG28xxVGPPS},
    ),
    (r'VG_2802',
        {'primary_index': '<VOLUME>_profile_index.lbl',
         'validate_index_rows': False,
         'instrument_class': ObsInstrumentVG28xxVGUVS},
    ),
    (r'VG_2803',
        {'primary_index': '<VOLUME>_profile_index.lbl',
         'validate_index_rows': False,
         'instrument_class': ObsInstrumentVG28xxVGRSS},
    ),
    (r'VG_2810',
        {'primary_index': '<VOLUME>_profile_index.lbl',
         'validate_index_rows': False,
         'instrument_class': ObsInstrumentVG28xxVGISS},
    ),
]
