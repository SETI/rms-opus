from obs_instrument_gossi import ObsInstrumentGOSSI
from obs_instrument_nhlorri import ObsInstrumentNHLORRI

# Information about each volume or group of volumes, used to determine
# which instrument class to use, which index files to read, etc.
VOLUME_INFO = [
    (r'GO_00\d\d',
        {'mission_id': 'GO',
         'instrument_id': 'GOSSI',
         'primary_index': '<VOLUME>_index.lbl',
         'instrument_class': ObsInstrumentGOSSI},
    ),
    (r'NH..LO_[12]001',
        {'mission_id': 'NH',
         'instrument_id': 'NHLORRI',
         'primary_index': '<VOLUME>_index.lbl',
         'instrument_class': ObsInstrumentNHLORRI},
    )
]
