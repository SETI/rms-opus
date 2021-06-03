################################################################################
# populate_obs_instrument_GOSSI.py
#
# Routines to populate fields specific to GOSSI.
################################################################################

import numpy as np

import julian
import pdsfile

import import_util

from populate_obs_mission_galileo import *
from populate_util import *


# Data from:
#   Title: The Galileo Solid-State Imaging experiment
#   Authors: Belton, M. J. S., Klaasen, K. P., Clary, M. C., Anderson, J. L.,
#            Anger, C. D., Carr, M. H., ,
#   Journal: Space Science Reviews (ISSN 0038-6308), vol. 60, no. 1-4, May 1992,
#            p. 413-455.
#   Bibliographic Code: 1992SSRv...60..413B
# WL MIN/MAX are taken by eye-balling Fig. 3 of the above paper
# Note that min/max are the FULL bandwidth, not just the FWHM
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

def _GOSSI_file_spec_helper(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    # Format: GO_0017/J0/OPNAV/C0347569700R.IMG
    file_spec = index_row['FILE_SPECIFICATION_NAME']
    return file_spec

def populate_obs_general_GOSSI_opus_id_OBS(**kwargs):
    file_spec = _GOSSI_file_spec_helper(**kwargs)
    pds_file = pdsfile.PdsFile.from_filespec(file_spec, fix_case=True)
    opus_id = pds_file.opus_id
    if not opus_id:
        import_util.log_nonrepeating_error(
            f'Unable to create OPUS_ID for FILE_SPEC "{file_spec}"')
        return file_spec.split('/')[-1]
    return opus_id

def populate_obs_general_GOSSI_ring_obs_id_OBS(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    image_num = index_row['SPACECRAFT_CLOCK_START_COUNT'].replace('.', '')
    planet = helper_galileo_planet_id(**kwargs)
    if planet is None:
        pl_str = ''
    else:
        pl_str = planet[0]

    return pl_str + '_IMG_GO_SSI_' + image_num

def populate_obs_general_GOSSI_inst_host_id_OBS(**kwargs):
    return 'GO'

def populate_obs_general_GOSSI_data_type_OBS(**kwargs):
    return 'IMG'

# We actually have no idea what IMAGE_TIME represents - start, mid, stop?
# We assume it means stop time like it does for Voyager, and because Mark
# has done some ring analysis with this assumption and it seemed to work OK.
# So we compute start time by taking IMAGE_TIME and subtracting exposure.
# If we don't have exposure, we just set them equal so we can still search
# cleanly.
def populate_obs_general_GOSSI_time1_OBS(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    stop_time = import_util.safe_column(index_row, 'IMAGE_TIME')
    exposure = import_util.safe_column(index_row, 'EXPOSURE_DURATION')

    if exposure is None or stop_time is None:
        exposure = 0

    try:
        stop_time_sec = julian.tai_from_iso(stop_time)
    except Exception as e:
        import_util.log_nonrepeating_error(
            f'Bad image time format "{stop_time}": {e}')
        return None

    return stop_time_sec-exposure/1000

def populate_obs_general_GOSSI_time2_OBS(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    stop_time = import_util.safe_column(index_row, 'IMAGE_TIME')

    if stop_time is None:
        return None

    try:
        stop_time_sec = julian.tai_from_iso(stop_time)
    except Exception as e:
        import_util.log_nonrepeating_error(
            f'Bad image time format "{stop_time}": {e}')
        return None

    general_row = metadata['obs_general_row']
    start_time_sec = general_row['time1']

    if start_time_sec is not None and stop_time_sec < start_time_sec:
        start_time = import_util.safe_column(index_row, 'START_TIME')
        import_util.log_warning(f'time1 ({start_time}) and time2 ({stop_time}) '
                                f'are in the wrong order - setting to time1')
        stop_time_sec = start_time_sec

    return stop_time_sec

def populate_obs_general_GOSSI_target_name_OBS(**kwargs):
    target_name = helper_galileo_target_name(**kwargs)
    if target_name is None:
        target_name = 'NONE'
    return target_name

def populate_obs_general_GOSSI_observation_duration_OBS(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    exposure = import_util.safe_column(index_row, 'EXPOSURE_DURATION')

    if exposure is None:
        return None

    return exposure / 1000

def populate_obs_general_GOSSI_quantity_OBS(**kwargs):
    return 'REFLECT'

def populate_obs_general_GOSSI_observation_type_OBS(**kwargs):
    return 'IMG' # Image

def populate_obs_pds_GOSSI_note_OBS(**kwargs):
    return None

def populate_obs_general_GOSSI_primary_file_spec_OBS(**kwargs):
    return _GOSSI_file_spec_helper(**kwargs)

def populate_obs_pds_GOSSI_primary_file_spec_OBS(**kwargs):
    return _GOSSI_file_spec_helper(**kwargs)

def populate_obs_pds_GOSSI_product_creation_time_OBS(**kwargs):
    return None # Until the proper data is available in the supplemental index

def populate_obs_pds_GOSSI_data_set_id_OBS(**kwargs):
    return populate_data_set_id_from_index(**kwargs)

def populate_obs_pds_GOSSI_product_id_OBS(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    file_spec = index_row['FILE_SPECIFICATION_NAME']

    # The file_spec looks like GO_0017:[J0.OPNAV.C034640]5900R.IMG
    # We want to extract C0346405900R
    idx = file_spec.find('.')
    file_spec = file_spec[idx+1:]
    idx = file_spec.find('.')
    file_spec = file_spec[idx+1:].replace(']', '').replace('.IMG', '')

    return file_spec

# GOSSI is 10.16 microRad / pixel and 800x800
_GOSSI_FOV_RAD = 10.16e-6 * 800
_GOSSI_FOV_RAD_DIAG = _GOSSI_FOV_RAD * np.sqrt(2)

# We only have the center point for RA,DEC so derive the edges by using the
# FOV
def _GOSSI_ra_helper(**kwargs):
    metadata = kwargs['metadata']
    ring_geo_row = metadata.get('ring_geo_row', None)
    if ring_geo_row is not None:
        return import_util.safe_column(ring_geo_row, 'MINIMUM_RIGHT_ASCENSION')

    index_row = metadata['index_row']
    ra = import_util.safe_column(index_row, 'RIGHT_ASCENSION')
    dec = import_util.safe_column(index_row, 'DECLINATION')
    if ra is None or dec is None:
        return None, None
    delta = np.rad2deg(_GOSSI_FOV_RAD_DIAG/2 / np.cos(np.deg2rad(dec)))
    ra1 = (ra-delta) % 360
    ra2 = (ra+delta) % 360
    if ra2 < ra1:
        ra1, ra2 = ra2, ra1
    return ra1, ra2

def populate_obs_general_GOSSI_right_asc1_OBS(**kwargs):
    ra1, ra2 = _GOSSI_ra_helper(**kwargs)
    return ra1

def populate_obs_general_GOSSI_right_asc2_OBS(**kwargs):
    ra1, ra2 = _GOSSI_ra_helper(**kwargs)
    return ra2

def populate_obs_general_GOSSI_declination1_OBS(**kwargs):
    metadata = kwargs['metadata']
    ring_geo_row = metadata.get('ring_geo_row', None)
    if ring_geo_row is not None:
        return import_util.safe_column(ring_geo_row, 'MINIMUM_DECLINATION')

    index_row = metadata['index_row']
    dec = import_util.safe_column(index_row, 'DECLINATION')
    if dec is None:
        return None
    return dec - np.rad2deg(_GOSSI_FOV_RAD_DIAG/2)

def populate_obs_general_GOSSI_declination2_OBS(**kwargs):
    metadata = kwargs['metadata']
    ring_geo_row = metadata.get('ring_geo_row', None)
    if ring_geo_row is not None:
        return import_util.safe_column(ring_geo_row, 'MAXIMUM_DECLINATION')

    index_row = metadata['index_row']
    dec = import_util.safe_column(index_row, 'DECLINATION')
    if dec is None:
        return None
    return dec + np.rad2deg(_GOSSI_FOV_RAD_DIAG/2)


### OBS_TYPE_IMAGE TABLE ###

def populate_obs_type_image_GOSSI_image_type_id_OBS(**kwargs):
    return 'FRAM'

def populate_obs_type_image_GOSSI_duration_OBS(**kwargs):
    metadata = kwargs['metadata']
    obs_general_row = metadata['obs_general_row']
    return obs_general_row['observation_duration']

def populate_obs_type_image_GOSSI_levels_OBS(**kwargs):
    return 256

def populate_obs_type_image_GOSSI_lesser_pixel_size_OBS(**kwargs):
    return 800

def populate_obs_type_image_GOSSI_greater_pixel_size_OBS(**kwargs):
    return 800


### OBS_WAVELENGTH TABLE ###

# For GOSSI, effective wavelengths are taken from the published table.
# Other wavelengths are taken by eyeballing the filter graphs.

def _wavelength_helper(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    filter_name = index_row['FILTER_NAME']

    if filter_name not in _GOSSI_FILTER_WAVELENGTHS:
        import_util.log_nonrepeating_error(
            f'Unknown GOSSI filter name "{filter_name}"')
        return 0

    return _GOSSI_FILTER_WAVELENGTHS[filter_name]

def populate_obs_wavelength_GOSSI_wavelength1_OBS(**kwargs):
    return _wavelength_helper(**kwargs)[0] / 1000 # microns

def populate_obs_wavelength_GOSSI_wavelength2_OBS(**kwargs):
    return _wavelength_helper(**kwargs)[1] / 1000 # microns

def populate_obs_wavelength_GOSSI_wave_res1_OBS(**kwargs):
    metadata = kwargs['metadata']
    wl_row = metadata['obs_wavelength_row']
    wl1 = wl_row['wavelength1']
    wl2 = wl_row['wavelength2']
    if wl1 is None or wl2 is None:
        return None
    return wl2 - wl1

def populate_obs_wavelength_GOSSI_wave_res2_OBS(**kwargs):
    metadata = kwargs['metadata']
    wl_row = metadata['obs_wavelength_row']
    wl1 = wl_row['wavelength1']
    wl2 = wl_row['wavelength2']
    if wl1 is None or wl2 is None:
        return None
    return wl2 - wl1

def populate_obs_wavelength_GOSSI_wave_no1_OBS(**kwargs):
    metadata = kwargs['metadata']
    wavelength_row = metadata['obs_wavelength_row']
    return 10000 / wavelength_row['wavelength2'] # cm^-1

def populate_obs_wavelength_GOSSI_wave_no2_OBS(**kwargs):
    metadata = kwargs['metadata']
    wavelength_row = metadata['obs_wavelength_row']
    return 10000 / wavelength_row['wavelength1'] # cm^-1

def populate_obs_wavelength_GOSSI_wave_no_res1_OBS(**kwargs):
    metadata = kwargs['metadata']
    wl_row = metadata['obs_wavelength_row']
    wno1 = wl_row['wave_no1']
    wno2 = wl_row['wave_no2']
    if wno1 is None or wno2 is None:
        return None
    return wno2 - wno1

def populate_obs_wavelength_GOSSI_wave_no_res2_OBS(**kwargs):
    metadata = kwargs['metadata']
    wl_row = metadata['obs_wavelength_row']
    wno1 = wl_row['wave_no1']
    wno2 = wl_row['wave_no2']
    if wno1 is None or wno2 is None:
        return None
    return wno2 - wno1

def populate_obs_wavelength_GOSSI_spec_flag_OBS(**kwargs):
    return 'N'

def populate_obs_wavelength_GOSSI_spec_size_OBS(**kwargs):
    return None

def populate_obs_wavelength_GOSSI_polarization_type_OBS(**kwargs):
    return 'NONE'


### populate_obs_occultation TABLE ###

def populate_obs_occultation_GOSSI_occ_type_OBS(**kwargs):
    return None

def populate_obs_occultation_GOSSI_occ_dir_OBS(**kwargs):
    return None

def populate_obs_occultation_GOSSI_body_occ_flag_OBS(**kwargs):
    return None

def populate_obs_occultation_GOSSI_optical_depth_min_OBS(**kwargs):
    return None

def populate_obs_occultation_GOSSI_optical_depth_max_OBS(**kwargs):
    return None

def populate_obs_occultation_GOSSI_temporal_sampling_OBS(**kwargs):
    return None

def populate_obs_occultation_GOSSI_quality_score_OBS(**kwargs):
    return None

def populate_obs_occultation_GOSSI_wl_band_OBS(**kwargs):
    return None

def populate_obs_occultation_GOSSI_source_OBS(**kwargs):
    return None

def populate_obs_occultation_GOSSI_host_OBS(**kwargs):
    return None


################################################################################
# THESE NEED TO BE IMPLEMENTED FOR EVERY GALILEO INSTRUMENT
################################################################################

def populate_obs_mission_galileo_GOSSI_orbit_number(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    orbit_number = index_row['ORBIT_NUMBER']
    return str(orbit_number)


################################################################################
# THESE ARE SPECIFIC TO OBS_INSTRUMENT_GOSSI
################################################################################
