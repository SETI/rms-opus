################################################################################
# populate_obs_instrument_COUVIS.py
#
# Routines to populate fields specific to COUVIS. It may change fields in
# obs_general, obs_mission_cassini, or obs_instrument_COUVIS.
################################################################################

# Ordering:
#   time_sec1/2 must come before observation_duration
#   planet_id must come before rms_obs_id

import os

from config_data import *
import impglobals

from populate_obs_mission_cassini import *


################################################################################
# THESE NEED TO BE IMPLEMENTED FOR EVERY INSTRUMENT
################################################################################

### OBS_GENERAL TABLE ###

def _COUVIS_channel_time_helper(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    file_name = index_row['FILE_NAME']
    last_part = os.path.basename(file_name)
    last_part = last_part.replace('.LBL', '')

    if last_part.startswith('HDAC'):
        channel = 'HDAC'
        image_time = last_part[4:]
    else:
        channel = last_part[:3]
        image_time = last_part[3:]

    return channel, image_time

def populate_obs_general_COUVIS_rms_obs_id(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    planet_id = helper_cassini_planet_id(**kwargs)

    planet_ltr = 'X'
    if planet_id is not None:
        planet_ltr = planet_id[0]

    channel, image_time = _COUVIS_channel_time_helper(**kwargs)

    time_split = image_time.split('_')
    image_time = (f'{time_split[0]}-{time_split[1]}T{time_split[2]}-'+
                  f'{time_split[3]}')
    if len(time_split) > 4:
        image_time += '-' + time_split[4]

    rms_obs_id = f'{planet_ltr}/CO/UVIS/{image_time}/{channel}'

    return rms_obs_id

def populate_obs_general_COUVIS_inst_host_id(**kwargs):
    return 'CO'

# XXX
def populate_obs_general_COUVIS_data_type(**kwargs):
    channel, image_time = _COUVIS_channel_time_helper(**kwargs)

    if channel == 'HSP':
        return 'PROFILE'
    if channel == 'HDAC':
        return 'POINT'

    metadata = kwargs['metadata']
    index_row_num = metadata['index_row_num']
    index_row = metadata['index_row']
    slit_state = index_row['SLIT_STATE'];

    if channel == 'EUV' and slit_state == 'OCCULTATION':
        return 'PROFILE'

    supp_index_row = metadata['supp_index_row']
    object_type = None
    if supp_index_row is not None:
        object_type = supp_index_row['DATA_OBJECT_TYPE']

    if channel != 'EUV' and channel != 'FUV':
        import_util.announce_nonrepeating_error(
            f'COUVIS_data_type has unknown channel type {channel}',
            index_row_num)
        return None

    if object_type is None:
        import_util.announce_nonrepeating_error(
            f'COUVIS_data_type has channel EUV or FUV but no '+
            f'DATA_OBJECT_TYPE available', index_row_num)
        return None

    if object_type == 'SPECTRUM':
        return 'PROFILE'

    return 'CUBE'

def populate_obs_general_COUVIS_time1(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    start_time = index_row['START_TIME']
    return start_time

def populate_obs_general_COUVIS_time2(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    stop_time = index_row['STOP_TIME']
    return stop_time

def populate_obs_general_COUVIS_time_sec1(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    start_time = index_row['START_TIME']
    return julian.tai_from_iso(start_time)

def populate_obs_general_COUVIS_time_sec2(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    stop_time = index_row['STOP_TIME']
    obs_general_row = metadata['obs_general_row']

    time2 = julian.tai_from_iso(stop_time)

    time1 = obs_general_row['time_sec1']
    if time2 < time1:
        start_time = index_row['START_TIME']
        index_row_num = metadata['index_row_num']
        impglobals.LOGGER.log('warning',
            f'time_sec1 ({start_time}) and time_sec2 ({stop_time}) are '+
            f'in the wrong order - setting equal [line {index_row_num}]')
        time2 = time1

    return time2

# XXX
def populate_obs_general_COUVIS_target_name(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    target_name = index_row['TARGET_NAME'].upper()
    if target_name in TARGET_NAME_MAPPING:
        target_name = TARGET_NAME_MAPPING[target_name]

    return target_name

def populate_obs_general_COUVIS_observation_duration(**kwargs):
    metadata = kwargs['metadata']
    obs_general_row = metadata['obs_general_row']
    time_sec1 = obs_general_row['time_sec1']
    time_sec2 = obs_general_row['time_sec2']
    return time_sec2 - time_sec1

# XXX
def populate_obs_general_COUVIS_quantity(**kwargs):
    channel, image_time = _COUVIS_channel_time_helper(**kwargs)

    if channel == 'HSP':
        return 'OPTICAL'
    return 'EMISSION'

def populate_obs_general_COUVIS_note(**kwargs):
    metadata = kwargs['metadata']
    supp_index_row = metadata['supp_index_row']
    if supp_index_row is None:
        return None
    description = supp_index_row['DESCRIPTION']
    description = description.replace('The purpose of this observation is ',
                                      '')
    return description

def populate_obs_general_COUVIS_primary_file_spec(**kwargs):
    metadata = kwargs['metadata']
    supp_index_row = metadata.get('supp_index_row', None)
    if supp_index_row is None:
        return None
    return supp_index_row['FILE_SPECIFICATION_NAME']

def populate_obs_general_COUVIS_data_set_id(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    dsi = index_row['DATA_SET_ID']
    return (dsi, dsi)

def populate_obs_general_COUVIS_right_asc1(**kwargs):
    metadata = kwargs['metadata']
    ring_geo_row = metadata.get('ring_geo_row', None)
    if ring_geo_row is not None:
        return ring_geo_row['MINIMUM_RIGHT_ASCENSION']

    index_row = metadata['index_row']
    ra = index_row['RIGHT_ASCENSION']
    return ra

def populate_obs_general_COUVIS_right_asc2(**kwargs):
    metadata = kwargs['metadata']
    ring_geo_row = metadata.get('ring_geo_row', None)
    if ring_geo_row is not None:
        return ring_geo_row['MAXIMUM_RIGHT_ASCENSION']

    index_row = metadata['index_row']
    ra = index_row['RIGHT_ASCENSION']
    return ra

def populate_obs_general_COUVIS_declination1(**kwargs):
    metadata = kwargs['metadata']
    ring_geo_row = metadata.get('ring_geo_row', None)
    if ring_geo_row is not None:
        return ring_geo_row['MINIMUM_DECLINATION']

    index_row = metadata['index_row']
    dec = index_row['DECLINATION']
    if dec == 'NULL': # XXX
        dec = None
    return dec

def populate_obs_general_COUVIS_declination2(**kwargs):
    metadata = kwargs['metadata']
    ring_geo_row = metadata.get('ring_geo_row', None)
    if ring_geo_row is not None:
        return ring_geo_row['MAXIMUM_DECLINATION']

    index_row = metadata['index_row']
    dec = index_row['DECLINATION']
    if dec == 'NULL': # XXX
        dec = None
    return dec

def populate_obs_mission_cassini_COUVIS_mission_phase_name(**kwargs):
    return None


### OBS_TYPE_IMAGE TABLE ###

def populate_obs_type_image_COUVIS_image_type_id(**kwargs):
    metadata = kwargs['metadata']
    obs_general_row = metadata['obs_general_row']
    type_id = obs_general_row['data_type']
    if type_id != 'CUBE':
        return 'PUSH'
    return 'CUBE'

def populate_obs_type_image_COUVIS_duration(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    integration_duration = index_row['INTEGRATION_DURATION']

    return integration_duration

def populate_obs_type_image_COUVIS_levels(**kwargs):
    return 65535

def populate_obs_type_image_COUVIS_lesser_pixel_size(**kwargs):
    metadata = kwargs['metadata']
    supp_index_row = metadata.get('supp_index_row', None)
    if supp_index_row is None:
        return None
    line1 = supp_index_row['WINDOW_MINIMUM_LINE_NUMBER']
    line2 = supp_index_row['WINDOW_MAXIMUM_LINE_NUMBER']
    line_bin = supp_index_row['LINE_BINNING_FACTOR']
    samples = supp_index_row['LINE_SAMPLES']
    if line1 is None or line2 is None or line_bin is None or samples is None:
        return None
    pixels = min(samples, (line2-line1+1)//line_bin)
    if pixels < 0:
        return None
    return pixels

def populate_obs_type_image_COUVIS_greater_pixel_size(**kwargs):
    metadata = kwargs['metadata']
    supp_index_row = metadata.get('supp_index_row', None)
    if supp_index_row is None:
        return None
    line1 = supp_index_row['WINDOW_MINIMUM_LINE_NUMBER']
    line2 = supp_index_row['WINDOW_MAXIMUM_LINE_NUMBER']
    line_bin = supp_index_row['LINE_BINNING_FACTOR']
    samples = supp_index_row['LINE_SAMPLES']
    if line1 is None or line2 is None or line_bin is None or samples is None:
        return None
    pixels = max(samples, (line2-line1+1)//line_bin)
    if pixels < 0:
        return None
    return pixels


### OBS_WAVELENGTH TABLE ###

# This is the effective wavelength (convolved with the solar spectrum)
# Meaningless for a spectrometer
def populate_obs_wavelength_COUVIS_effective_wavelength(**kwargs):
    return None

def populate_obs_wavelength_COUVIS_wavelength1(**kwargs):
    channel, image_time = _COUVIS_channel_time_helper(**kwargs)
    if channel == 'HSP':
        return 0.11
    if channel == 'HDAC':
        return 0.115

    metadata = kwargs['metadata']
    index_row_num = metadata['index_row_num']
    supp_index_row = metadata.get('supp_index_row', None)
    if supp_index_row is None:
        return None
    band1 = supp_index_row['MINIMUM_BAND_NUMBER']
    if band1 is None:
        return None

    if channel == 'EUV':
        return  0.0558 + band1 * 0.0000607422
    if channel == 'FUV':
        return 0.11 + band1 * 0.000078125

    import_util.announce_nonrepeating_error(
        f'obs_wavelength_COUVIS_wavelength1 has unknown channel type '+
        f' {channel}', index_row_num)
    return None


def populate_obs_wavelength_COUVIS_wavelength2(**kwargs):
    channel, image_time = _COUVIS_channel_time_helper(**kwargs)
    if channel == 'HSP':
        return 0.19
    if channel == 'HDAC':
        return 0.180

    metadata = kwargs['metadata']
    index_row_num = metadata['index_row_num']
    supp_index_row = metadata.get('supp_index_row', None)
    if supp_index_row is None:
        return None
    band2 = supp_index_row['MINIMUM_BAND_NUMBER']
    if band2 is None:
        return None

    if channel == 'EUV':
        return  0.0558 + (band2 + 1) * 0.0000607422
    if channel == 'FUV':
        return 0.11 + (band2 + 1) * 0.000078125

    import_util.announce_nonrepeating_error(
        f'obs_wavelength_COUVIS_wavelength1 has unknown channel type '+
        f' {channel}', index_row_num)
    return None

def _COUVIS_wave_res_helper(**kwargs):
    metadata = kwargs['metadata']
    supp_index_row = metadata.get('supp_index_row', None)
    if supp_index_row is None:
        return None
    channel, image_time = _COUVIS_channel_time_helper(**kwargs)
    band_bin = supp_index_row['BAND_BINNING_FACTOR']

    if channel == 'EUV':
        return band_bin * 0.0000607422
    if channel == 'FUV':
        return band_bin * 0.000078125
    return None

def populate_obs_wavelength_COUVIS_wave_res1(**kwargs):
    return _COUVIS_wave_res_helper(**kwargs)

def populate_obs_wavelength_COUVIS_wave_res2(**kwargs):
    return _COUVIS_wave_res_helper(**kwargs)

def populate_obs_wavelength_COUVIS_wave_no1(**kwargs):
    metadata = kwargs['metadata']
    wl_row = metadata['obs_wavelength_row']
    wl2 = wl_row['wavelength2']

    if wl2 is None:
        return None

    return 10000. / wl2

def populate_obs_wavelength_COUVIS_wave_no2(**kwargs):
    metadata = kwargs['metadata']
    wl_row = metadata['obs_wavelength_row']
    wl1 = wl_row['wavelength2']

    if wl1 is None:
        return None

    return 10000. / wl1

def populate_obs_wavelength_COUVIS_wave_no_res1(**kwargs):
    metadata = kwargs['metadata']
    wl_row = metadata['obs_wavelength_row']
    wave_res1 = wl_row['wave_res1']
    wl2 = wl_row['wavelength2']

    if wave_res1 is None or wl2 is None:
        return None

    return wave_res1 * 100. / (wl2*wl2)

def populate_obs_wavelength_COUVIS_wave_no_res2(**kwargs):
    metadata = kwargs['metadata']
    wl_row = metadata['obs_wavelength_row']
    wave_res1 = wl_row['wave_res1'] # XXX?
    wl1 = wl_row['wavelength1']

    if wave_res1 is None or wl1 is None:
        return None

    return wave_res1 * 100. / (wl1*wl1)

def populate_obs_wavelength_COUVIS_spec_flag(**kwargs):
    channel, image_time = _COUVIS_channel_time_helper(**kwargs)

    if channel == 'HDAC' or channel == 'HSP':
        return 'N'
    return 'Y'

def populate_obs_wavelength_COUVIS_spec_size(**kwargs):
    metadata = kwargs['metadata']
    supp_index_row = metadata.get('supp_index_row', None)
    if supp_index_row is None:
        return None
    channel, image_time = _COUVIS_channel_time_helper(**kwargs)
    band1 = supp_index_row['MINIMUM_BAND_NUMBER']
    band2 = supp_index_row['MAXIMUM_BAND_NUMBER']
    band_bin = supp_index_row['BAND_BINNING_FACTOR']
    if band1 is None or band2 is None or band_bin is None:
        return None

    if channel == 'EUV' or channel == 'FUV':
        return (band2 - band1 + 1) / band_bin

    return None

def populate_obs_wavelength_COUVIS_polarization_type(**kwargs):
    return 'NONE'


################################################################################
# THESE NEED TO BE IMPLEMENTED FOR EVERY CASSINI INSTRUMENT
################################################################################

def populate_obs_mission_cassini_COUVIS_ert1(**kwargs):
    return None

def populate_obs_mission_cassini_COUVIS_ert2(**kwargs):
    return None

def populate_obs_mission_cassini_COUVIS_spacecraft_clock_count1(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    count = index_row['SPACECRAFT_CLOCK_START_COUNT']
    if not count.startswith('1/'):
        index_row_num = metadata['index_row_num']
        import_util.announce_nonrepeating_error(
            f'Badly formatted SPACE_CLOCK_START_COUNT "{count}"',
            index_row_num)
        return None
    return float(count[2:])

# NOTE: STOP COUNT is always unknown for UVIS
def populate_obs_mission_cassini_COUVIS_spacecraft_clock_count2(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    count = index_row['SPACECRAFT_CLOCK_START_COUNT']
    if not count.startswith('1/'):
        index_row_num = metadata['index_row_num']
        import_util.announce_nonrepeating_error(
            f'Badly formatted SPACE_CLOCK_START_COUNT "{count}"',
            index_row_num)
        return None
    return float(count[2:])


################################################################################
# THESE ARE SPECIFIC TO OBS_INSTRUMENT_COUVIS
################################################################################

def populate_obs_instrument_COUVIS_channel(**kwargs):
    channel, image_time = _COUVIS_channel_time_helper(**kwargs)
    return (channel, channel)

def populate_obs_instrument_COUVIS_observation_type(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    obstype = index_row['OBSERVATION_TYPE']
    if obstype == '' or obstype == 'NULL':
        obstype = 'NONE'
    return obstype.upper()

def populate_obs_instrument_COUVIS_occultation_port_state(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    occ_state = index_row['OCCULTATION_PORT_STATE']
    if occ_state == 'NULL':
        occ_state = 'N/A'
    return occ_state.upper()
