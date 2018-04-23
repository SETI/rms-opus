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

    'mult_obs_general_inst_host_id': [
        (   0,  'CO',      'Cassini',   10, 'Y'),
        (   1,  'GO',      'Galileo',   20, 'Y'),
        (   2, 'HST',       'Hubble',   30, 'Y'),
        (   3,  'NH', 'New Horizons',   40, 'Y'),
        (   4, 'VG1',    'Voyager 1',   50, 'Y'),
        (   5, 'VG2',    'Voyager 2',   60, 'Y'),
    ],
    'mult_obs_general_instrument_id': [
        (   0,    'COCIRS',       'Cassini CIRS (Infrared Spectrometer)',   10, 'Y'),
        (   1,     'COISS',        'Cassini ISS (Imaging Subsystem)',   20, 'Y'),
        (   2,    'COUVIS',       'Cassini UVIS (Ultraviolet Spectrometer)',   30, 'Y'),
        (   3,    'COVIMS',       'Cassini VIMS (Visual/Infrared Spectrometer)',   40, 'Y'),
        (   4,     'GOSSI',        'Galileo SSI (Imaging)',   50, 'Y'),
        (   5,     'VGISS',        'Voyager ISS (Imaging Subsystem)',   60, 'Y'),
        (   6,    'HSTACS',         'Hubble ACS (Advanced Camera for Surveys)',   70, 'Y'),
        (   7,   'HSTWFC3',        'Hubble WFC3 (Wide Field Camera 3)',   80, 'Y'),
        (   8,  'HSTWFPC2',       'Hubble WFPC2 (Wide Field Planetary Camera 2)',   90, 'Y'),
        (   9, 'HSTNICMOS',      'Hubble NICMOS (Near Infrared Camera/Spectrometer)',  100, 'Y'),
        (  10,   'HSTSTIS',    'Hubble NICMOS (Imaging Spectrograph)',  110, 'Y'),
        (  11,     'LORRI', 'New Horizons LORRI (Long Range Reconnaissance Imager)',  120, 'Y'),
        (  12,      'MVIC',  'New Horizons MVIC (Multispectral Visible Imaging Camera)',  130, 'Y'),
    ],
    'mult_obs_general_mission_id': [
        (   0,  'CO',      'Cassini',   10, 'Y'),
        (   1,  'GO',      'Galileo',   20, 'Y'),
        (   2, 'HST',       'Hubble',   30, 'Y'),
        (   3,  'NH', 'New Horizons',   40, 'Y'),
        (   4,  'VG',      'Voyager',   50, 'Y'),
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
        (   8,  None,   'Other',   90, 'Y'),
    ],
    'mult_obs_general_quantity': [
        (   0,  'REFLECT',     'Reflectivity',   10, 'Y'),
        (   1,  'THERMAL', 'Thermal Emission',   20, 'Y'),
        (   2,  'OPTICAL',    'Optical Depth',   30, 'Y'),
        (   3, 'EMISSION',         'Emission',   40, 'Y'),
        (   4,       None,             'None',   50, 'Y'),
    ],
    'mult_obs_general_target_class': [
        (   0,        'RING',        'Ring',   10, 'Y'),
        (   1,      'PLANET',      'Planet',   20, 'Y'),
        (   2,        'MOON',        'Moon',   30, 'Y'),
        (   3,    'ASTEROID',    'Asteroid',   40, 'Y'),
        (   4,         'SUN',         'Sun',   50, 'Y'),
        (   5,        'STAR',        'Star',   60, 'Y'),
        (   6,         'SKY',         'Sky',   70, 'Y'),
        (   7, 'CALIBRATION', 'Calibration',   80, 'Y'),
        (   8,       'OTHER',       'Other',   90, 'Y'),
    ],

    ### OBS_INSTRUMENT_COISS ###

    'mult_obs_instrument_COISS_camera': [
        (   0, 'N', 'Narrow Angle Camera',   10, 'Y'),
        (   1, 'W',   'Wide Angle Camera',   20, 'Y'),
    ],

    'mult_obs_instrument_COISS_SHUTTER_MODE_ID': [
        (   0, 'NACONLY', 'Narrow Angle Camera Only',   10, 'Y'),
        (   1, 'WACONLY',   'Wide Angle Camera Only',   20, 'Y'),
        (   2,  'BOTSIM',      'Both Simultaneously',   30, 'Y'),
    ],

    'mult_obs_instrument_COISS_DATA_CONVERSION_TYPE': [
        (   0, '12BIT',                 'No conversion',   10, 'Y'),
        (   1,  '8LSB', 'Keep 8 Least Significant Bits',   20, 'Y'),
        (   2, 'TABLE',      'Table Lookup',               30, 'Y'),
    ],

    'mult_obs_instrument_COISS_GAIN_MODE_ID': [
        (   0,  '12 ELECTRONS PER DN',  '12 Electrons per DN',   10, 'Y'),
        (   1,  '29 ELECTRONS PER DN',  '29 Electrons per DN',   20, 'Y'),
        (   2,  '95 ELECTRONS PER DN',  '95 Electrons per DN',   30, 'Y'),
        (   3, '215 ELECTRONS PER DN', '215 Electrons per DN',   40, 'Y'),
    ],


    ### OBS_MISSION_VOYAGER ###

    'mult_obs_mission_voyager_spacecraft_name': [
        (   0, 'VG1', 'Voyager 1',   10, 'Y'),
        (   1, 'VG2', 'Voyager 2',   20, 'Y'),
    ],

    ### OBS_INSTRUMENT_VGISS ###

    'mult_obs_instrument_VGISS_camera': [
        (   0, 'N', 'Narrow Angle',   10, 'Y'),
        (   1, 'W',   'Wide Angle',   20, 'Y'),
    ],

    ### OBS_MISSION_HUBBLE ###

    'mult_obs_mission_hubble_DETECTOR_ID': [
        (   0,   'HRC',   'ACS-HRC',   10, 'Y'),
        (   1,   'SBC',   'ACS-SBC',   20, 'Y'),
        (   2,   'WFC',  'ACS-WFC3',   30, 'Y'),
        (   3,    'IR',   'WFC3-IR',   40, 'Y'),
        (   4,  'UVIS', 'WFC3-UVIS',   50, 'Y'),
        (   5, 'WFPC2',     'WFPC2',   60, 'Y'),
    ],

    ### OBS_TYPE_IMAGE ###

    'mult_obs_type_image_image_data_type': [
        (   0, 'FRAM',       'Frame',   10, 'Y'),
        (   1, 'PUSH',   'Pushbroom',   20, 'Y'),
        (   2, 'RAST', 'Raster Scan',   30, 'Y'),
        (   3, 'CUBE',        'Cube',   40, 'Y'),
        (   4,  'IMG',       'Image',   50, 'Y'),
    ],

    ### OBS_WAVELENGTH ###

    'mult_obs_wavelength_polarization_type': [
        (   0,   'LINEAR',   'Linear',   10, 'Y'),
        (   1,     'NONE',     'None',   20, 'Y'),
    ],
}
