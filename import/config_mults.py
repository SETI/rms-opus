################################################################################
# mult_config.py
#
# mult_obs_<table>_<field> tables are used to store the possible values for
# each field in a table that has form type "GROUP". For most such tables,
# the mult_ tables are created and updated dynamically as new values are found.
# In this case, the mult_ value (from the field) and the display label are the
# same, and they are sorted in alphabetical order.
#
# However, some tables rarely change and have labels that differ from the
# raw database field value (for example display "Yes" instead of "Y").
# These tables are defined by hand here, and if a value ever needs to be added,
# this file has to be edited by hand before import can proceed.
################################################################################

# Anything ending in FLAG should be set up like:
#     'mult_obs_instrument_COCIRS_INSTRUMENT_MODE_ALL_FLAG': [
#         (   0, '0',  'On',   10, 'Y'),
#         (   1, '1', 'Off',   20, 'Y'),
#     ],
# OR:
#    'mult_obs_wavelength_spec_flag': [
#         (   0, None,  None,   10, 'Y'),
#         (   1,  'Y', 'Yes',   10, 'Y'),
#         (   2,  'N',  'No',   20, 'Y'),
#     ],


# Fields are:
#   Unique id (used by Django)
#   Data value as found in the obs_ table field
#   Label to display in the OPUS GUI
#   Display order
#   Whether to display or not

PREPROGRAMMED_MULT_TABLE_CONTENTS = {

    ### OBS_GENERAL ###

    'mult_obs_general_instrument_id': [
        (   0,    'COCIRS',       'Cassini CIRS',   10, 'Y'),
        (   1,     'COISS',        'Cassini ISS',   20, 'Y'),
        (   2,    'COUVIS',       'Cassini UVIS',   30, 'Y'),
        (   3,    'COVIMS',       'Cassini VIMS',   40, 'Y'),
        (   4,     'GOSSI',        'Galileo SSI',   50, 'Y'),
        (   5,     'VGISS',        'Voyager ISS',   60, 'Y'),
        (   6,    'HSTACS',         'Hubble ACS',   70, 'Y'),
        (   7, 'HSTNICMOS',      'Hubble NICMOS',   80, 'Y'),
        (   8,   'HSTSTIS',        'Hubble STIS',   90, 'Y'),
        (   9,   'HSTWFC3',        'Hubble WFC3',  100, 'Y'),
        (  10,  'HSTWFPC2',       'Hubble WFPC2',  110, 'Y'),
        (  11,     'LORRI', 'New Horizons LORRI',  120, 'Y'),
        (  12,      'MVIC',  'New Horizons MVIC',  130, 'Y'),
    ],
    'mult_obs_general_mission_id': [
        (   0,  'CO',      'Cassini',   10, 'Y'),
        (   1,  'GO',      'Galileo',   20, 'Y'),
        (   2, 'HST',       'Hubble',   30, 'Y'),
        (   3,  'NH', 'New Horizons',   40, 'Y'),
        (   4,  'VG',      'Voyager',   50, 'Y'),
    ],
    'mult_obs_general_inst_host_id': [
        (   0,  'CO',      'Cassini',   10, 'Y'),
        (   1,  'GO',      'Galileo',   20, 'Y'),
        (   2, 'HST',       'Hubble',   30, 'Y'),
        (   3,  'NH', 'New Horizons',   40, 'Y'),
        (   4, 'VG1',    'Voyager 1',   50, 'Y'),
        (   5, 'VG2',    'Voyager 2',   60, 'Y'),
    ],
    'mult_obs_general_data_type': [
        (   0,    'CUBE',    'Cube',   10, 'Y'),
        (   1,     'IMG',   'Image',   20, 'Y'),
        (   2,    'LINE',    'Line',   30, 'Y'),
        (   3, 'PROFILE', 'Profile',   40, 'Y'),
        (   4,   'POINT',   'Point',   50, 'Y'),
    ],
    'mult_obs_general_planet_id': [
        (   0, 'VEN',   'Venus',   10, 'Y'),
        (   1, 'EAR',   'Earth',   20, 'Y'),
        (   2, 'MAR',    'Mars',   30, 'Y'),
        (   3, 'JUP', 'Jupiter',   40, 'Y'),
        (   4, 'SAT',  'Saturn',   50, 'Y'),
        (   5, 'URA',  'Uranus',   60, 'Y'),
        (   6, 'NEP', 'Neptune',   70, 'Y'),
        (   7, 'PLU',   'Pluto',   80, 'Y'),
        (   8, 'OTH',   'Other',   90, 'Y'),
    ],
    'mult_obs_general_target_class': [
        (   0,      'PLANET',      'Planet',   10, 'Y'),
        (   1,        'MOON',        'Moon',   20, 'Y'),
        (   2,        'RING',        'Ring',   30, 'Y'),
        (   3,    'ASTEROID',    'Asteroid',   40, 'Y'),
        (   4,         'SUN',         'Sun',   50, 'Y'),
        (   5,        'STAR',        'Star',   60, 'Y'),
        (   6,         'SKY',         'Sky',   70, 'Y'),
        (   7, 'CALIBRATION', 'Calibration',   80, 'Y'),
        (   8,       'OTHER',       'Other',   90, 'Y'),
    ],
    'mult_obs_general_quantity': [
        (   0,  'REFLECT',     'Reflectivity',   10, 'Y'),
        (   1,  'THERMAL', 'Thermal Emission',   20, 'Y'),
        (   2,  'OPTICAL',    'Optical Depth',   30, 'Y'),
        (   3, 'EMISSION',         'Emission',   40, 'Y'),
    ],

    ### OBS_TYPE_IMAGE ###

    'mult_obs_type_image_image_type_id': [
        (   0, 'CUBE',        'Cube',   10, 'Y'),
        (   1,  'IMG',       'Image',   20, 'Y'),
        (   2, 'FRAM',       'Frame',   30, 'Y'),
        (   3, 'RAST', 'Raster Scan',   40, 'Y'),
        (   4, 'PUSH',   'Pushbroom',   50, 'Y'),
    ],

    ### OBS_WAVELENGTH ###

    'mult_obs_wavelength_polarization_type': [
        (   0,   'LINEAR',   'Linear',   10, 'Y'),
        (   1,     'NONE',     'None',   20, 'Y'),
    ],

    ### OBS_MISSION_CASSINI ###

    'mult_obs_mission_cassini_prime_inst_id': [
        (   0,  'CIRS',  'CIRS',   10, 'Y'),
        (   1,   'ISS',   'ISS',   20, 'Y'),
        (   2,  'UVIS',  'UVIS',   30, 'Y'),
        (   3,  'VIMS',  'VIMS',   40, 'Y'),
        (   4, 'OTHER', 'Other',   50, 'Y'),
        (   5,    None,  'Null',   60, 'Y'),
    ],

    ### OBS_INSTRUMENT_COISS ###

    'mult_obs_instrument_coiss_data_conversion_type': [
        (   0, '12BIT', '12BIT',  10, 'Y'),
        (   1,  '8LSB',  '8LSB',  20, 'Y'),
        (   2, 'TABLE', 'TABLE',  30, 'Y'),
    ],
    'mult_obs_instrument_coiss_gain_mode_id': [
        (   0,  '12 ELECTRONS PER DN',  '12 Electrons per DN',   10, 'Y'),
        (   1,  '29 ELECTRONS PER DN',  '29 Electrons per DN',   20, 'Y'),
        (   2,  '95 ELECTRONS PER DN',  '95 Electrons per DN',   30, 'Y'),
        (   3, '215 ELECTRONS PER DN', '215 Electrons per DN',   40, 'Y'),
    ],
    'mult_obs_instrument_image_observation_type': [
        (   0, 'SCIENCE',             'Science',             10, 'Y'),
        (   1, 'SCIENCE,OPNAV',       'Science,OpNav',       20, 'Y'),
        (   2, 'SCIENCE,CALIBRATION', 'Science,Calibration', 30, 'Y'),
        (   3, 'SCIENCE,SUPPORT',     'Science,Support',     40, 'Y'),
        (   4, 'OPNAV',               'OpNav',               50, 'Y'),
        (   5, 'OPNAV,SUPPORT',       'Opnav,Support',       60, 'Y'),
        (   6, 'CALIBRATION',         'Calibration',         70, 'Y'),
        (   7, 'SUPPORT',             'Support',             80, 'Y'),
        (   8, 'UNKNOWN',             'Unknown',             90, 'Y'),
    ],
    'mult_obs_instrument_coiss_shutter_mode_id': [
        (   0, 'NACONLY', 'NACONLY',   10, 'Y'),
        (   1, 'WACONLY', 'WACONLY',   20, 'Y'),
        (   2, 'BOTSIM',  'BOTSIM',    30, 'Y'),
    ],
    'mult_obs_instrument_coiss_shutter_state_id': [
        (   0, 'DISABLED', 'Disabled',  10, 'Y'),
        (   1, 'ENABLED',  'Enabled',   20, 'Y'),
    ],
    'mult_obs_instrument_coiss_instrument_mode_id': [
        (   0, 'FULL', 'FULL',  10, 'Y'),
        (   1, 'SUM2', 'SUM2',  20, 'Y'),
        (   2, 'SUM4', 'SUM4',  30, 'Y'),
    ],
    'mult_obs_instrument_coiss_camera': [
        (   0, 'N', 'Narrow Angle Camera',   10, 'Y'),
        (   1, 'W',   'Wide Angle Camera',   20, 'Y'),
    ],

    ### OBS_INSTRUMENT_COUVIS ###

    'mult_obs_instrument_couvis_observation_type': [
        (   0, 'CALIB',   'CALIB',    10, 'Y'),
        (   1, 'UCSTAR',  'UCSTAR',   20, 'Y'),
        (   2, 'UFPSCAN', 'UFPSCAN',  30, 'Y'),
        (   3, 'UHDAC',   'UHDAC',    40, 'Y'),
        (   4, 'UHIGHSN', 'UHIGHSN',  50, 'Y'),
        (   5, 'UMAP',    'UMAP',     60, 'Y'),
        (   6, 'USCAN',   'USCAN',    70, 'Y'),
        (   7, 'USTARE',  'USTARE',   80, 'Y'),
        (   8, 'NONE',    'None',     90, 'Y'),
    ],
    'mult_obs_instrument_couvis_compression_type': [
        (   0,  '8_BIT',  '8_BIT',   10, 'Y'),
        (   1, 'SQRT_8', 'SQRT_8',   20, 'Y'),
        (   2, 'SQRT_9', 'SQRT_9',   30, 'Y'),
        (   3,   'NONE',   'None',   40, 'Y'),
    ],
    'mult_obs_instrument_couvis_occultation_port_state': [
        (   0,   'OPEN',   'Open',   10, 'Y'),
        (   1, 'CLOSED', 'Closed',   20, 'Y'),
        (   2,    'N/A',    'N/A',   30, 'Y'),
    ],
    'mult_obs_instrument_couvis_slit_state': [
        (   0, 'HIGH_RESOLUTION', 'High Resolution',   10, 'Y'),
        (   1,  'LOW_RESOLUTION',  'Low Resolution',   20, 'Y'),
        (   2,     'OCCULTATION',     'Occultation',   30, 'Y'),
        (   3,            'NULL',             'N/A',   40, 'Y'),
    ],
    'mult_obs_instrument_couvis_channel': [
        (   0, 'EUV',   'EUV',   10, 'Y'),
        (   1, 'FUV',   'FUV',   20, 'Y'),
        (   2, 'HDAC', 'HDAC',   30, 'Y'),
        (   3, 'HSP',   'HSP',   40, 'Y'),
    ],

    ### OBS_INSTRUMENT_COVIMS ###

    'mult_obs_instrument_covims_instrument_mode_id': [
        (   0, 'IMAGE',          'IMAGE',           10, 'Y'),
        (   1, 'LINE',           'LINE',            20, 'Y'),
        (   2, 'OCCULTATION',    'OCCULTATION',     30, 'Y'),
        (   3, 'POINT',          'POINT',           40, 'Y'),
        (   4, 'CAL_BACKGROUND', 'CAL_BACKGROUND',  50, 'Y'),
        (   5, 'CAL_SOLAR',      'CAL_SOLAR',       60, 'Y'),
        (   6, 'CAL_SPECTRAL',   'CAL_SPECTRAL',    70, 'Y'),
    ],
    'mult_obs_instrument_covims_ir_sampling_mode_id': [
        (   0, 'HI-RES', 'Hi-Res',  10, 'Y'),
        (   1, 'NORMAL', 'Normal',  20, 'Y'),
        (   2, 'UNDER',  'Under',   30, 'Y'),
    ],
    'mult_obs_instrument_covims_vis_sampling_mode_id': [
        (   0, 'HI-RES', 'Hi-Res',  10, 'Y'),
        (   1, 'NORMAL', 'Normal',  20, 'Y'),
        (   2, 'N/A',    'N/A',     30, 'Y'),
        (   3, 'UNK',    'Unknown', 40, 'Y'),
    ],
    'mult_obs_instrument_covims_channel': [
        (   0, 'IR',  'IR',   10, 'Y'),
        (   1, 'VIS', 'VIS',  20, 'Y'),
    ],

    ### OBS_INSTRUMENT_GOSSI ###

    'mult_obs_instrument_gossi_filter_name': [
        (   0,    'CLEAR',           'Clear',   10, 'Y'),
        (   1,   'VIOLET',          'Violet',   20, 'Y'),
        (   2,    'GREEN',           'Green',   30, 'Y'),
        (   3,      'RED',             'Red',   40, 'Y'),
        (   4,   'IR-7270', 'Methane (7270)',   50, 'Y'),
        (   5,   'IR-7560',      'Continuum',   60, 'Y'),
        (   6,   'IR-8890', 'Methane (8890)',   70, 'Y'),
        (   7,   'IR-9680',       'Infrared',   80, 'Y'),
    ],
    'mult_obs_instrument_gossi_gain_mode_id': [
        (   0,  '10K',  '10K',   10, 'Y'),
        (   1,  '40K',  '40K',   20, 'Y'),
        (   2, '100K', '100K',   30, 'Y'),
        (   3, '400K', '400K',   40, 'Y'),
    ],
    'mult_obs_instrument_gossi_obstruction_id': [
        (   0, 'POSSIBLE',          'Possible',           10, 'Y'),
        (   1, 'NOT POSSIBLE',      'Not Possible',       20, 'Y'),
        (   2, 'PRESENCE VERIFIED', 'Presence Verified',  30, 'Y'),
    ],
    'mult_obs_instrument_gossi_compression_type': [
        (   0,        'BARC RATE CONTROL',        'BARC Rate Control', 10, 'Y'),
        (   1,                  'HUFFMAN',                  'Huffman', 20, 'Y'),
        (   2, 'INTEGER COSINE TRANSFORM', 'Integer Cosine Transform', 30, 'Y'),
        (   3,                     'NONE',                     'None', 40, 'Y'),
    ],

    ### OBS_MISSION_HUBBLE ###

    'mult_obs_mission_hubble_detector_id': [
        (   0,   'HRC',   'ACS-HRC',   10, 'Y'),
        (   1,   'SBC',   'ACS-SBC',   20, 'Y'),
        (   2,   'WFC',  'ACS-WFC3',   30, 'Y'),
        (   3,    'IR',   'WFC3-IR',   40, 'Y'),
        (   4,  'UVIS', 'WFC3-UVIS',   50, 'Y'),
        (   5, 'WFPC2',     'WFPC2',   60, 'Y'),
    ],

    ### OBS_MISSION_VOYAGER ###

    'mult_obs_mission_voyager_spacecraft_name': [
        (   0, 'VG1', 'Voyager 1',   10, 'Y'),
        (   1, 'VG2', 'Voyager 2',   20, 'Y'),
    ],

    ### OBS_INSTRUMENT_VGISS ###

    'mult_obs_instrument_vgiss_camera': [
        (   0, 'N', 'Narrow Angle',   10, 'Y'),
        (   1, 'W',   'Wide Angle',   20, 'Y'),
    ],
}
