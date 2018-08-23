################################################################################
# populate_obs_instrument_COCIRS.py
#
# Routines to populate fields specific to COCIRS.
################################################################################

# Ordering:
#   time_sec1/2 must come before planet_id
#   planet_id must come before opus_id

import pdsfile

from config_data import *
import impglobals
import import_util

from populate_obs_mission_cassini import *


################################################################################
# THESE NEED TO BE IMPLEMENTED FOR EVERY INSTRUMENT
################################################################################

### OBS_GENERAL TABLE ###

def _COCIRS_file_spec_helper(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    # Format: "DATA/APODSPEC/SPEC0802010000_FP1.DAT"
    file_spec = index_row['SPECTRUM_FILE_SPECIFICATION']
    volume_id = kwargs['volume_id']
    return volume_id + '/' + file_spec

def populate_obs_general_COCIRS_opus_id(**kwargs):
    file_spec = _COCIRS_file_spec_helper(**kwargs)
    pds_file = pdsfile.PdsFile.from_filespec(file_spec)
    try:
        opus_id = pds_file.opus_id
    except:
        metadata = kwargs['metadata']
        index_row = metadata['index_row']
        import_util.log_nonrepeating_error(
            f'Unable to create OPUS_ID for FILE_SPEC "{file_spec}"')
        return file_spec
    return opus_id

def populate_obs_general_COCIRS_ring_obs_id(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    instrument_id = index_row['DETECTOR_ID']
    filename = index_row['SPECTRUM_FILE_SPECIFICATION'].split('/')[-1]
    if not filename.startswith('SPEC') or not filename.endswith('.DAT'):
        import_util.log_nonrepeating_error(
            f'Bad format SPECTRUM_FILE_SPECIFICATION "{filename}"')
        return None
    image_num = filename[4:14]
    planet = helper_cassini_planet_id(**kwargs)
    if planet is None:
        pl_str = ''
    else:
        pl_str = planet[0]

    return pl_str + '_SPEC_CO_CIRS_' + image_num + '_' + instrument_id

def populate_obs_general_COCIRS_inst_host_id(**kwargs):
    return 'CO'

def populate_obs_general_COCIRS_time1(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    start_time = import_util.safe_column(index_row, 'START_TIME')

    if start_time is None:
        return None

    try:
        start_time_sec = julian.tai_from_iso(start_time)
    except:
        import_util.log_nonrepeating_error(
            f'Bad start time format "{start_time}"')
        return None

    return julian.iso_from_tai(start_time_sec, digits=3, ymd=True)

def populate_obs_general_COCIRS_time2(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    stop_time = import_util.safe_column(index_row, 'STOP_TIME')

    if stop_time is None:
        return None

    try:
        stop_time_sec = julian.tai_from_iso(stop_time)
    except:
        import_util.log_nonrepeating_error(
            f'Bad stop time format "{stop_time}"')
        return None

    return julian.iso_from_tai(stop_time_sec, digits=3, ymd=True)

def populate_obs_general_COCIRS_target_name(**kwargs):
    return helper_cassini_target_name(**kwargs)

def populate_obs_general_COCIRS_observation_duration(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    # This is the MEAN duration in SECONDS
    exposure = import_util.safe_column(index_row, 'EXPOSURE_DURATION')
    return exposure

def populate_obs_general_COCIRS_quantity(**kwargs):
    return 'THERMAL'

def populate_obs_general_COCIRS_spatial_sampling(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    instrument_id = index_row['DETECTOR_ID']
    if instrument_id == 'FP1':
        return 'POINT'
    return '1D'

def populate_obs_general_COCIRS_wavelength_sampling(**kwargs):
    return 'Y'

def populate_obs_general_COCIRS_time_sampling(**kwargs):
    return 'N'

def populate_obs_general_COCIRS_note(**kwargs):
    return None

def populate_obs_general_COCIRS_primary_file_spec(**kwargs):
    return _COCIRS_file_spec_helper(**kwargs)

def populate_obs_general_COCIRS_product_creation_time(**kwargs):
    metadata = kwargs['metadata']
    index_label = metadata['index_label']
    pct = index_label['PRODUCT_CREATION_TIME']
    return pct

# Format: "CO-S-CIRS-2/3/4-REFORMATTED-V1.0"
def populate_obs_general_COCIRS_data_set_id(**kwargs):
    metadata = kwargs['metadata']
    index_label = metadata['index_label']
    dsi = index_label['DATA_SET_ID']
    return (dsi, dsi)

def populate_obs_general_COCIRS_product_id(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    # Format: "DATA/APODSPEC/SPEC0802010000_FP1.DAT"
    filename = index_row['SPECTRUM_FILE_SPECIFICATION'].split('/')[-1]
    return filename

# We don't have ring geometry or other such info for CIRS
def populate_obs_general_COCIRS_right_asc1(**kwargs):
    return None

def populate_obs_general_COCIRS_right_asc2(**kwargs):
    return None

def populate_obs_general_COCIRS_declination1(**kwargs):
    return None

def populate_obs_general_COCIRS_declination2(**kwargs):
    return None

# Format: "SCIENCE_CRUISE"
def populate_obs_mission_cassini_COCIRS_mission_phase_name(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    mp = index_row['MISSION_PHASE_NAME']
    if mp.upper() == 'NULL':
        return None
    return mp.replace('_', ' ')

def populate_obs_mission_cassini_COCIRS_sequence_id(**kwargs):
    return None


### OBS_TYPE_IMAGE TABLE ###

def populate_obs_type_image_COCIRS_image_type_id(**kwargs):
    return 'FRAM'

def populate_obs_type_image_COCIRS_duration(**kwargs):
    metadata = kwargs['metadata']
    obs_general_row = metadata['obs_general_row']
    return obs_general_row['observation_duration']

def populate_obs_type_image_COCIRS_levels(**kwargs):
    return None

def populate_obs_type_image_COCIRS_lesser_pixel_size(**kwargs):
    return None

def populate_obs_type_image_COCIRS_greater_pixel_size(**kwargs):
    return None


### OBS_WAVELENGTH TABLE ###

def populate_obs_wavelength_COCIRS_wavelength1(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    wave_no2 = index_row['MAXIMUM_WAVENUMBER']

    if wave_no2 is None:
        return None

    return 10000. / wave_no2

def populate_obs_wavelength_COCIRS_wavelength2(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    wave_no1 = index_row['MINIMUM_WAVENUMBER']

    if wave_no1 is None:
        return None

    return 10000. / wave_no1

def populate_obs_wavelength_COCIRS_wave_res1(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    wave_no_res2 = index_row['WAVENUMBER_RESOLUTION']
    wave_no2 = index_row['MAXIMUM_WAVENUMBER']

    if wave_no_res2 is None or wave_no2 is None:
        return None

    return 10000.*wave_no_res2/(wave_no2 * wave_no2)

def populate_obs_wavelength_COCIRS_wave_res2(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    wave_no_res1 = index_row['WAVENUMBER_RESOLUTION']
    wave_no1 = index_row['MINIMUM_WAVENUMBER']

    if wave_no_res1 is None or wave_no1 is None:
        return None

    return 10000.*wave_no_res1/(wave_no1 * wave_no1)

def populate_obs_wavelength_COCIRS_wave_no1(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    wave_no2 = index_row['MINIMUM_WAVENUMBER']
    return wave_no2

def populate_obs_wavelength_COCIRS_wave_no2(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    wave_no2 = index_row['MAXIMUM_WAVENUMBER']
    return wave_no2

def populate_obs_wavelength_COCIRS_wave_no_res1(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    wave_no_res1 = index_row['WAVENUMBER_RESOLUTION']
    return wave_no_res1

def populate_obs_wavelength_COCIRS_wave_no_res2(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    wave_no_res2 = index_row['WAVENUMBER_RESOLUTION']
    return wave_no_res2

def populate_obs_wavelength_COCIRS_spec_flag(**kwargs):
    return 'Y'

def populate_obs_wavelength_COCIRS_spec_size(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    wave_no_res1 = index_row['SPECTRUM_SAMPLES']
    return wave_no_res1

def populate_obs_wavelength_COCIRS_polarization_type(**kwargs):
    return 'NONE'


################################################################################
# THESE NEED TO BE IMPLEMENTED FOR EVERY CASSINI INSTRUMENT
################################################################################

def populate_obs_mission_cassini_COCIRS_spacecraft_clock_count1(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    count = index_row['SPACECRAFT_CLOCK_START_COUNT']
    if not count.startswith('1/'):
        import_util.log_nonrepeating_error(
            f'Badly formatted SPACECRAFT_CLOCK_START_COUNT "{count}"')
        return None
    if count.find('.') == -1:
        count += '.000'
    return count

def populate_obs_mission_cassini_COCIRS_spacecraft_clock_count2(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    count = index_row['SPACECRAFT_CLOCK_STOP_COUNT']
    if not count.startswith('1/'):
        import_util.log_nonrepeating_error(
            f'Badly formatted SPACECRAFT_CLOCK_STOP_COUNT "{count}"')
        return None
    if count.find('.') == -1:
        count += '.000'
    return count


################################################################################
# THESE ARE SPECIFIC TO OBS_INSTRUMENT_COCIRS
################################################################################
