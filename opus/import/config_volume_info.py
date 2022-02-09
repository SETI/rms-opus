from obs_instrument_coiss import ObsInstrumentCOISS
from obs_instrument_corss_occ import ObsInstrumentCORSSOcc
from obs_instrument_couvis import ObsInstrumentCOUVIS
from obs_instrument_couvis_occ import ObsInstrumentCOUVISOcc
from obs_instrument_covims_occ import ObsInstrumentCOVIMSOcc
from obs_instrument_ebrocc import ObsInstrumentEBROCC
from obs_instrument_gossi import ObsInstrumentGOSSI
from obs_instrument_nhlorri import ObsInstrumentNHLORRI
from obs_instrument_nhmvic import ObsInstrumentNHMVIC
from obs_instrument_vgiss import ObsInstrumentVGISS
from obs_instrument_vg28xx_vgiss import ObsInstrumentVG28xxVGISS
from obs_instrument_vg28xx_vgpps_vguvs import (ObsInstrumentVG28xxVGPPS,
                                               ObsInstrumentVG28xxVGUVS)
from obs_instrument_vg28xx_vgrss import ObsInstrumentVG28xxVGRSS


# Information about each volume or group of volumes, used to determine
# which instrument class to use, which index files to read, etc.
VOLUME_INFO = [
    (r'EBROCC_0001',
        {'primary_index': '<VOLUME>_profile_index.lbl',
         'instrument_class': ObsInstrumentEBROCC},
    ),
    (r'COISS_[12]\d\d\d',
        {'primary_index': '<VOLUME>_index.lbl',
         'instrument_class': ObsInstrumentCOISS},
    ),
    (r'CORSS_8001',
        {'primary_index': '<VOLUME>_profile_index.lbl',
         'instrument_class': ObsInstrumentCORSSOcc},
    ),
    (r'COUVIS_0\d\d\d',
        {'primary_index': '<VOLUME>_index.lbl',
         'instrument_class': ObsInstrumentCOUVIS},
    ),
    (r'COUVIS_8001',
        {'primary_index': '<VOLUME>_profile_index.lbl',
         'instrument_class': ObsInstrumentCOUVISOcc},
    ),
    (r'COVIMS_8001',
        {'primary_index': '<VOLUME>_profile_index.lbl',
         'instrument_class': ObsInstrumentCOVIMSOcc},
    ),
    (r'GO_00\d\d',
        {'primary_index': '<VOLUME>_index.lbl',
         'instrument_class': ObsInstrumentGOSSI},
    ),
    (r'NH..LO_[12]001',
        {'primary_index': '<VOLUME>_index.lbl',
         'instrument_class': ObsInstrumentNHLORRI},
    ),
    (r'NH..MV_[12]001',
        {'primary_index': '<VOLUME>_index.lbl',
         'instrument_class': ObsInstrumentNHMVIC},
    ),
    (r'VGISS_[5678]\d\d\d',
        {'primary_index': '<VOLUME>_raw_image_index.lbl',
         'instrument_class': ObsInstrumentVGISS},
    ),
    (r'VG_2801',
        {'primary_index': '<VOLUME>_profile_index.lbl',
         'instrument_class': ObsInstrumentVG28xxVGPPS},
    ),
    (r'VG_2802',
        {'primary_index': '<VOLUME>_profile_index.lbl',
         'instrument_class': ObsInstrumentVG28xxVGUVS},
    ),
    (r'VG_2803',
        {'primary_index': '<VOLUME>_profile_index.lbl',
         'instrument_class': ObsInstrumentVG28xxVGRSS},
    ),
    (r'VG_2810',
        {'primary_index': '<VOLUME>_profile_index.lbl',
         'instrument_class': ObsInstrumentVG28xxVGISS},
    ),
]
