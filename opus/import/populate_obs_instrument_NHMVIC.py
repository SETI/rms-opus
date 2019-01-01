################################################################################
# populate_obs_instrument_NHMVIC.py
#
# Routines to populate fields specific to NHMVIC.
################################################################################

import numpy as np

import pdsfile

import import_util

from populate_obs_mission_new_horizons import *


################################################################################
# THESE NEED TO BE IMPLEMENTED FOR EVERY INSTRUMENT
################################################################################

### OBS_GENERAL TABLE ###

def _NHMVIC_file_spec_helper(**kwargs):
    metadata = kwargs['metadata']
    supp_index_row = metadata['supp_index_row']
    # Format: "data/20070108_003059/mc0_0030598439_0x630_eng_1.lbl"
    file_spec = supp_index_row['FILE_SPECIFICATION_NAME']
    volume_id = kwargs['volume_id']
    return volume_id + '/' + file_spec

def populate_obs_general_NHMVIC_opus_id(**kwargs):
    file_spec = _NHMVIC_file_spec_helper(**kwargs)
    pds_file = pdsfile.PdsFile.from_filespec(file_spec)
    try:
        opus_id = pds_file.opus_id.replace('.', '-')
    except:
        opus_id = None
    if not opus_id:
        metadata = kwargs['metadata']
        index_row = metadata['index_row']
        import_util.log_nonrepeating_error(
            f'Unable to create OPUS_ID for FILE_SPEC "{file_spec}"')
        return file_spec.split('/')[-1]
    return opus_id

def populate_obs_general_NHMVIC_ring_obs_id(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    image_num = index_row['FILE_NAME'][4:14]
    camera = index_row['FILE_NAME'][:3].upper()
    # This is really dumb, but it's what the old OPUS did so we do it for
    # backwards compatability
    start_time = index_row['START_TIME']
    if start_time > '2007-09-01':
        pl_str = 'P'
    else:
        pl_str = 'J'

    return pl_str + '_IMG_NH_MVIC_' + image_num + '_' + camera

def populate_obs_general_NHMVIC_inst_host_id(**kwargs):
    return 'NH'

def populate_obs_general_NHMVIC_time1(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    start_time = import_util.safe_column(index_row, 'START_TIME')

    if start_time is None:
        return None

    try:
        start_time_sec = julian.tai_from_iso(start_time)
    except Exception as e:
        import_util.log_nonrepeating_error(
            f'Bad start time format "{start_time}": {e}')
        return None

    return start_time_sec

def populate_obs_general_NHMVIC_time2(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    stop_time = import_util.safe_column(index_row, 'STOP_TIME')

    if stop_time is None:
        return None

    try:
        stop_time_sec = julian.tai_from_iso(stop_time)
    except Exception as e:
        import_util.log_nonrepeating_error(
            f'Bad stop time format "{stop_time}": {e}')
        return None

    general_row = metadata['obs_general_row']
    start_time_sec = general_row['time1']

    if start_time_sec is not None and stop_time_sec < start_time_sec:
        start_time = import_util.safe_column(index_row, 'START_TIME')
        import_util.log_warning(f'time1 ({start_time}) and time2 ({stop_time}) '
                                f'are in the wrong order - setting to time1')
        stop_time_sec = start_time_sec

    return stop_time_sec

def populate_obs_general_NHMVIC_target_name(**kwargs):
    target_name = helper_new_horizons_target_name(**kwargs)
    if target_name is None:
        target_name = 'NONE'
    return target_name

def populate_obs_general_NHMVIC_observation_duration(**kwargs):
    metadata = kwargs['metadata']
    supp_index_row = metadata['supp_index_row']
    exposure = import_util.safe_column(supp_index_row, 'EXPOSURE_DURATION')

    if exposure is None:
        return None

    return exposure

def populate_obs_general_NHMVIC_quantity(**kwargs):
    return 'REFLECT'

def populate_obs_general_NHMVIC_observation_type(**kwargs):
    return 'IMG' # Image

def populate_obs_pds_NHMVIC_note(**kwargs):
    metadata = kwargs['metadata']
    supp_index_row = metadata['supp_index_row']
    return supp_index_row['OBSERVATION_DESC']

def populate_obs_general_NHMVIC_primary_file_spec(**kwargs):
    return _NHMVIC_file_spec_helper(**kwargs)

def populate_obs_pds_NHMVIC_primary_file_spec(**kwargs):
    return _NHMVIC_file_spec_helper(**kwargs)

def populate_obs_pds_NHMVIC_product_creation_time(**kwargs):
    metadata = kwargs['metadata']
    supp_index_row = metadata['supp_index_row']
    if supp_index_row is None:
        return None
    pct = supp_index_row['PRODUCT_CREATION_TIME']

    try:
        pct_sec = julian.tai_from_iso(pct)
    except Exception as e:
        import_util.log_nonrepeating_error(
            f'Bad product creation time format "{pct}": {e}')
        return None

    return pct_sec

# Format: "NH-J-MVIC-2-JUPITER-V2.0"
def populate_obs_pds_NHMVIC_data_set_id(**kwargs):
    metadata = kwargs['metadata']
    supp_index_row = metadata['supp_index_row']
    return supp_index_row['DATA_SET_ID']

# Format: "MC0_0032528036_0X536_ENG_1"
def populate_obs_pds_NHMVIC_product_id(**kwargs):
    metadata = kwargs['metadata']
    supp_index_row = metadata['supp_index_row']
    return supp_index_row['PRODUCT_ID']

# We occasionally don't bother to generate ring_geo data for NHMVIC, like during
# cruise, so just use the given RA/DEC from the label if needed. We don't make
# any effort to figure out the min/max values.
def populate_obs_general_NHMVIC_right_asc1(**kwargs):
    metadata = kwargs['metadata']
    ring_geo_row = metadata.get('ring_geo_row', None)
    if ring_geo_row is not None:
        return import_util.safe_column(ring_geo_row, 'MINIMUM_RIGHT_ASCENSION')

    supp_index_row = metadata['supp_index_row']
    ra = import_util.safe_column(supp_index_row, 'RIGHT_ASCENSION')
    return ra

def populate_obs_general_NHMVIC_right_asc2(**kwargs):
    metadata = kwargs['metadata']
    ring_geo_row = metadata.get('ring_geo_row', None)
    if ring_geo_row is not None:
        return import_util.safe_column(ring_geo_row, 'MAXIMUM_RIGHT_ASCENSION')

    supp_index_row = metadata['supp_index_row']
    ra = import_util.safe_column(supp_index_row, 'RIGHT_ASCENSION')
    return ra

def populate_obs_general_NHMVIC_declination1(**kwargs):
    metadata = kwargs['metadata']
    ring_geo_row = metadata.get('ring_geo_row', None)
    if ring_geo_row is not None:
        return import_util.safe_column(ring_geo_row, 'MINIMUM_DECLINATION')

    supp_index_row = metadata['supp_index_row']
    dec = import_util.safe_column(supp_index_row, 'DECLINATION')
    return dec

def populate_obs_general_NHMVIC_declination2(**kwargs):
    metadata = kwargs['metadata']
    ring_geo_row = metadata.get('ring_geo_row', None)
    if ring_geo_row is not None:
        return import_util.safe_column(ring_geo_row, 'MAXIMUM_DECLINATION')

    supp_index_row = metadata['supp_index_row']
    dec = import_util.safe_column(supp_index_row, 'DECLINATION')
    return dec


### OBS_TYPE_IMAGE TABLE ###

def populate_obs_type_image_NHMVIC_image_type_id(**kwargs):
    return 'PUSH'

def populate_obs_type_image_NHMVIC_duration(**kwargs):
    metadata = kwargs['metadata']
    obs_general_row = metadata['obs_general_row']
    return obs_general_row['observation_duration']

def populate_obs_type_image_NHMVIC_levels(**kwargs):
    return 4096

def populate_obs_type_image_NHMVIC_lesser_pixel_size(**kwargs):
    return 128

def populate_obs_type_image_NHMVIC_greater_pixel_size(**kwargs):
    return 5024


### OBS_WAVELENGTH TABLE ###

def populate_obs_wavelength_NHMVIC_wavelength1(**kwargs):
    return 0.4

def populate_obs_wavelength_NHMVIC_wavelength2(**kwargs):
    return 0.975

def populate_obs_wavelength_NHMVIC_wave_res1(**kwargs):
    return 0.575

def populate_obs_wavelength_NHMVIC_wave_res2(**kwargs):
    return 0.575

def populate_obs_wavelength_NHMVIC_wave_no1(**kwargs):
    metadata = kwargs['metadata']
    wavelength_row = metadata['obs_wavelength_row']
    return 10000 / wavelength_row['wavelength2'] # cm^-1

def populate_obs_wavelength_NHMVIC_wave_no2(**kwargs):
    metadata = kwargs['metadata']
    wavelength_row = metadata['obs_wavelength_row']
    return 10000 / wavelength_row['wavelength1'] # cm^-1

def populate_obs_wavelength_NHMVIC_wave_no_res1(**kwargs):
    metadata = kwargs['metadata']
    wl_row = metadata['obs_wavelength_row']
    wno1 = wl_row['wave_no1']
    wno2 = wl_row['wave_no2']
    if wno1 is None or wno2 is None:
        return None
    return wno2 - wno1

def populate_obs_wavelength_NHMVIC_wave_no_res2(**kwargs):
    metadata = kwargs['metadata']
    wl_row = metadata['obs_wavelength_row']
    wno1 = wl_row['wave_no1']
    wno2 = wl_row['wave_no2']
    if wno1 is None or wno2 is None:
        return None
    return wno2 - wno1

def populate_obs_wavelength_NHMVIC_spec_flag(**kwargs):
    return 'N'

def populate_obs_wavelength_NHMVIC_spec_size(**kwargs):
    return None

def populate_obs_wavelength_NHMVIC_polarization_type(**kwargs):
    return 'NONE'


################################################################################
# THESE NEED TO BE IMPLEMENTED FOR EVERY NEW HORIZONS INSTRUMENT
################################################################################



################################################################################
# THESE ARE SPECIFIC TO OBS_INSTRUMENT_NHMVIC
################################################################################
