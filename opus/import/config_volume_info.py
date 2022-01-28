from obs_instrument_gossi import ObsInstrumentGOSSI

# Information about each volume or group of volumes, used to determine
# which instrument class to use, which index files to read, etc.
VOLUME_INFO = [
    (r'GO_00\d\d',
        {'mission_id': 'GO',
         'instrument_id': 'GOSSI',
         'primary_index': '<VOLUME>_index.lbl',
         'instrument_class': ObsInstrumentGOSSI},
    )
]
