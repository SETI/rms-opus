from obs_instrument_coiss import ObsInstrumentCOISS
from obs_instrument_ebrocc import ObsInstrumentEBROCC
from obs_instrument_gossi import ObsInstrumentGOSSI
from obs_instrument_nhlorri import ObsInstrumentNHLORRI
from obs_instrument_nhmvic import ObsInstrumentNHMVIC
from obs_instrument_vgiss import ObsInstrumentVGISS
from obs_instrument_vg28xx import (ObsInstrumentVG28xxVGISS,
                                   ObsInstrumentVG28xxVGPPS)
                                   # ObsInstrumentVG28xxVGRSS,
                                   # ObsInstrumentVG28xxVGUVS)


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
    # (r'VG_2802',
    #     {'primary_index': '<VOLUME>_profile_index.lbl',
    #      'instrument_class': ObsInstrumentVG28xxVGUVS},
    # ),
    # (r'VG_2803',
    #     {'primary_index': '<VOLUME>_profile_index.lbl',
    #      'instrument_class': ObsInstrumentVG28xxVGRSS},
    # ),
    (r'VG_2810',
        {'primary_index': '<VOLUME>_profile_index.lbl',
         'instrument_class': ObsInstrumentVG28xxVGISS},
    ),
]
