################################################################################
# populate_obs_instrument_GOSSI.py
#
# Routines to populate fields specific to GOSSI. It may change fields in
# obs_general, obs_mission_galileo, or obs_instrument_GOSSI.
################################################################################

import julian

import import_util

from populate_obs_mission_galileo import *

# Data from:
#   Title: The Galileo Solid-State Imaging experiment
#   Authors: Belton, M. J. S., Klaasen, K. P., Clary, M. C., Anderson, J. L.,
#            Anger, C. D., Carr, M. H., ,
#   Journal: Space Science Reviews (ISSN 0038-6308), vol. 60, no. 1-4, May 1992,
#            p. 413-455.
#   Bibliographic Code: 1992SSRv...60..413B
# WL MIN/MAX are taken by eye-balling Fig. 3 of the above paper

# (WL MIN, WL MAX, EFFECTIVE WL)
_GOSSI_FILTER_WAVELENGTHS = {
    'CLEAR':   (360, 1050, 611),
    'VIOLET':  (360, 440, 404),
    'GREEN':   (510, 610, 559),
    'RED':     (620, 730, 671),
    'IR-7270': (725, 750, 734),
    'IR-7560': (750, 790, 756),
    'IR-8890': (870, 900, 887),
    'IR-9680': (940, 1050, 986),
}


################################################################################
# THESE NEED TO BE IMPLEMENTED FOR EVERY INSTRUMENT
################################################################################

### OBS_GENERAL TABLE ###

def populate_obs_general_GOSSI_rms_obs_id(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    spacecraft_clock_count = index_row['SPACECRAFT_CLOCK_START_COUNT']
    planet_id = helper_galileo_planet_id(**kwargs)
    if planet_id is not None:
        ret = planet_id[0]
    else:
        ret = ''
    return ret+'_IMG_GO_SSI_'+spacecraft_clock_count.replace('.','')

def populate_obs_general_GOSSI_inst_host_id(**kwargs):
    return 'GO'

def populate_obs_general_GOSSI_data_type(**kwargs):
    return ('IMG', 'Image')

def populate_obs_general_GOSSI_time1(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    start_time = index_row['IMAGE_TIME']
    return start_time[:23]

def populate_obs_general_GOSSI_time2(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    start_time = index_row['IMAGE_TIME']
    exposure = index_row['EXPOSURE_DURATION']

    stop_time = julian.tai_from_iso(start_time)+exposure/1000
    return julian.iso_from_tai(stop_time, digits=3)

def populate_obs_general_GOSSI_time_sec1(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    start_time = index_row['IMAGE_TIME']
    return julian.tai_from_iso(start_time)

def populate_obs_general_GOSSI_time_sec2(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    start_time = index_row['IMAGE_TIME']
    exposure = index_row['EXPOSURE_DURATION']

    return julian.tai_from_iso(start_time)+exposure/1000

def populate_obs_general_GOSSI_target_name(**kwargs):
    target_name = helper_galileo_target_name(**kwargs)
    if target_name is None:
        target_name = 'NONE'
    return target_name

def populate_obs_general_GOSSI_observation_duration(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    exposure = index_row['EXPOSURE_DURATION']
    return exposure / 1000

def populate_obs_general_GOSSI_quantity(**kwargs):
    return 'REFLECT'

def populate_obs_general_GOSSI_note(**kwargs):
    return None

def populate_obs_general_GOSSI_primary_file_spec(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    return index_row['FILE_SPECIFICATION_NAME']

def populate_obs_general_GOSSI_data_set_id(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    return index_row['DATA_SET_ID']


# ### OBS_TYPE_IMAGE TABLE ###

def populate_obs_type_image_GOSSI_image_type_id(**kwargs):
    return 'FRAM'

def populate_obs_type_image_GOSSI_duration(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    exposure = index_row['EXPOSURE_DURATION']
    return exposure / 1000

def populate_obs_type_image_GOSSI_levels(**kwargs):
    return 256

def populate_obs_type_image_GOSSI_lesser_pixel_size(**kwargs):
    return 800

def populate_obs_type_image_GOSSI_greater_pixel_size(**kwargs):
    return 800


### OBS_WAVELENGTH TABLE ###

def _wavelength_helper(**kwargs):
    metadata = kwargs['metadata']
    index_row_num = metadata['index_row_num']
    index_row = metadata['index_row']
    instrument_id = index_row['INSTRUMENT_ID']
    filter_name = index_row['FILTER_NAME']

    if filter_name not in _GOSSI_FILTER_WAVELENGTHS:
        import_util.announce_nonrepeating_error(
            f'Unknown GOSSI filter name "{filter_name}" [line {index_row_num}]')
        return 0

    return _GOSSI_FILTER_WAVELENGTHS[filter_name]

def populate_obs_wavelength_GOSSI_effective_wavelength(**kwargs):
    return _wavelength_helper(**kwargs)[2]

def populate_obs_wavelength_GOSSI_wavelength1(**kwargs):
    return _wavelength_helper(**kwargs)[0]

def populate_obs_wavelength_GOSSI_wavelength2(**kwargs):
    return _wavelength_helper(**kwargs)[1]

def populate_obs_wavelength_GOSSI_wave_res1(**kwargs):
    return None

def populate_obs_wavelength_GOSSI_wave_res2(**kwargs):
    return None

def populate_obs_wavelength_GOSSI_wave_no1(**kwargs):
    return None

def populate_obs_wavelength_GOSSI_wave_no2(**kwargs):
    return None

def populate_obs_wavelength_GOSSI_wave_no_res1(**kwargs):
    return None

def populate_obs_wavelength_GOSSI_wave_no_res2(**kwargs):
    return None

def populate_obs_wavelength_GOSSI_spec_flag(**kwargs):
    return 'N'

def populate_obs_wavelength_GOSSI_spec_size(**kwargs):
    return None

def populate_obs_wavelength_GOSSI_polarization_type(**kwargs):
    return 'NONE'


################################################################################
# THESE NEED TO BE IMPLEMENTED FOR EVERY GALILEO INSTRUMENT
################################################################################



################################################################################
# THESE ARE SPECIFIC TO OBS_INSTRUMENT_GOSSI
################################################################################
