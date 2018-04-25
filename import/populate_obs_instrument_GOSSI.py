################################################################################
# populate_obs_instrument_GOSSI.py
#
# Routines to populate fields specific to GOSSI. It may change fields in
# obs_general, obs_mission_galileo, or obs_instrument_GOSSI.
################################################################################

import numpy as np

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

# We actually have no idea what IMAGE_TIME represents - start, mid, stop?
# We assume it means stop time like it does for Voyager, and because Mark
# has done some ring analysis with this assumption and it seemed to work OK.
def populate_obs_general_GOSSI_time1(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    stop_time = index_row['IMAGE_TIME']
    exposure = index_row['EXPOSURE_DURATION']

    return julian.iso_from_tai(julian.tai_from_iso(stop_time)-exposure/1000,
                               digits=3)

def populate_obs_general_GOSSI_time2(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    stop_time = index_row['IMAGE_TIME']

    return julian.iso_from_tai(julian.tai_from_iso(stop_time), digits=3)

def populate_obs_general_GOSSI_time_sec1(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    stop_time = index_row['IMAGE_TIME']
    exposure = index_row['EXPOSURE_DURATION']

    return julian.tai_from_iso(stop_time)-exposure/1000

def populate_obs_general_GOSSI_time_sec2(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    stop_time = index_row['IMAGE_TIME']

    return julian.tai_from_iso(stop_time)

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
    dsi = index_row['DATA_SET_ID']
    return (dsi, dsi)

# GOSSI is 10.16 microRad / pixel and 800x800
_GOSSI_FOV_RAD = 10.16e-6 * 800
_GOSSI_FOV_RAD_DIAG = _GOSSI_FOV_RAD * np.sqrt(2)

# We only have the center point for RA,DEC so derive the edges by using the
# FOV
def _GOSSI_ra_helper(**kwargs):
    metadata = kwargs['metadata']
    ring_geo_row = metadata.get('ring_geo_row', None)
    if ring_geo_row is not None:
        return ring_geo_row['MINIMUM_RIGHT_ASCENSION']

    index_row = metadata['index_row']
    ra = index_row['RIGHT_ASCENSION']
    dec = index_row['DECLINATION']
    if not isinstance(ra, float) or not isinstance(dec, float):
        return None, None
    delta = np.rad2deg(_GOSSI_FOV_RAD_DIAG/2 / np.cos(np.deg2rad(dec)))
    ra1 = (ra-delta) % 360
    ra2 = (ra+delta) % 360
    if ra2 < ra1:
        ra1, ra2 = ra2, ra1
    return ra1, ra2

def populate_obs_general_GOSSI_right_asc1(**kwargs):
    ra1, ra2 = _GOSSI_ra_helper(**kwargs)
    return ra1

def populate_obs_general_GOSSI_right_asc2(**kwargs):
    ra1, ra2 = _GOSSI_ra_helper(**kwargs)
    return ra2

def populate_obs_general_GOSSI_declination1(**kwargs):
    metadata = kwargs['metadata']
    ring_geo_row = metadata.get('ring_geo_row', None)
    if ring_geo_row is not None:
        return ring_geo_row['MINIMUM_DECLINATION']

    index_row = metadata['index_row']
    dec = index_row['DECLINATION']
    if not isinstance(dec, float):
        return None
    return dec - np.rad2deg(_GOSSI_FOV_RAD_DIAG/2)

def populate_obs_general_GOSSI_declination2(**kwargs):
    metadata = kwargs['metadata']
    ring_geo_row = metadata.get('ring_geo_row', None)
    if ring_geo_row is not None:
        return ring_geo_row['MAXIMUM_DECLINATION']

    index_row = metadata['index_row']
    dec = index_row['DECLINATION']
    if not isinstance(dec, float):
        return None
    return dec + np.rad2deg(_GOSSI_FOV_RAD_DIAG/2)


### OBS_TYPE_IMAGE TABLE ###

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
    return _wavelength_helper(**kwargs)[2] / 1000 # microns

def populate_obs_wavelength_GOSSI_wavelength1(**kwargs):
    return _wavelength_helper(**kwargs)[0] / 1000 # microns

def populate_obs_wavelength_GOSSI_wavelength2(**kwargs):
    return _wavelength_helper(**kwargs)[1] / 1000 # microns

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
