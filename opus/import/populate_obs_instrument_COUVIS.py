################################################################################
# populate_obs_instrument_COUVIS.py
#
# Routines to populate fields specific to COUVIS.
################################################################################

# Ordering:
#   time1/2 must come before observation_duration
#   planet_id must come before opus_id

import os

import pdsfile

from config_data import *
import import_util

from populate_obs_mission_cassini import *
from populate_util import *


################################################################################
# THESE NEED TO BE IMPLEMENTED FOR EVERY INSTRUMENT
################################################################################

### OBS_GENERAL TABLE ###

def _COUVIS_file_spec_helper(**kwargs):
    metadata = kwargs['metadata']
    supp_index_row = metadata.get('supp_index_row', None)
    if supp_index_row is None:
        return None
    # Format: "/DATA/D2015_001/EUV2015_001_17_57.LBL"
    file_spec = supp_index_row['FILE_SPECIFICATION_NAME']
    volume_id = kwargs['volume_id']
    return volume_id + '/' + file_spec

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

def populate_obs_general_COUVIS_opus_id_OBS(**kwargs):
    file_spec = _COUVIS_file_spec_helper(**kwargs)
    pds_file = pdsfile.PdsFile.from_filespec(file_spec, fix_case=True)
    opus_id = pds_file.opus_id
    if not opus_id:
        import_util.log_nonrepeating_error(
            f'Unable to create OPUS_ID for FILE_SPEC "{file_spec}"')
        return file_spec.split('/')[-1]
    return opus_id

def populate_obs_general_COUVIS_ring_obs_id_OBS(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    filename = index_row['FILE_NAME'].split('/')[-1]
    if filename.startswith('HDAC'):
        image_camera = filename[:4]
        image_time = filename[4:18]
    else:
        image_camera = filename[:3]
        image_time = filename[3:17]
    image_time_str = (image_time[:4] + '-' + image_time[5:8] + 'T' +
                      image_time[9:11] + '-' + image_time[12:14])
    planet = helper_cassini_planet_id(**kwargs)
    if planet is None:
        pl_str = ''
    else:
        pl_str = planet[0]

    return pl_str + '_CO_UVIS_' + image_time_str + '_' + image_camera

def populate_obs_general_COUVIS_inst_host_id_OBS(**kwargs):
    return 'CO'

def populate_obs_general_COUVIS_quantity_OBS(**kwargs):
    # This is the NEW logic
    metadata = kwargs['metadata']
    supp_index_row = metadata['supp_index_row']
    if supp_index_row is None:
        return None
    description = supp_index_row['DESCRIPTION'].upper()
    if (description.find('OCCULTATION') != -1 and
        description.find('CALIBRATION') == -1):
        return 'OPDEPTH'
    return 'EMISSION'

    # This is the OLD logic
    # channel, image_time = _COUVIS_channel_time_helper(**kwargs)
    # metadata = kwargs['metadata']
    # index_row = metadata['index_row']
    # slit_state = index_row['SLIT_STATE']
    #
    # if channel == 'HSP':
    #     return 'OPTICAL'
    # if (channel == 'EUV' or channel == 'FUV') and slit_state == 'OCCULTATION':
    #     return 'OPTICAL'
    # # HDAC is measuring EMISSION, along with EUV/FUV normal slits
    # return 'EMISSION'

def populate_obs_general_COUVIS_observation_type_OBS(**kwargs):
    channel, image_time = _COUVIS_channel_time_helper(**kwargs)
    if channel == 'HSP' or channel == 'HDAC':
        return 'TS' # Time Series
    assert channel == 'EUV' or channel == 'FUV'
    return 'SCU' # Spectral Cube

def populate_obs_general_COUVIS_time1_OBS(**kwargs):
    return populate_time1_from_index(**kwargs)

def populate_obs_general_COUVIS_time2_OBS(**kwargs):
    channel, image_time = _COUVIS_channel_time_helper(**kwargs)
    if channel != 'HSP':
        return populate_time2_from_index(**kwargs)

    # The HSP stop times are wrong by a factor of the integration duration.
    # So we use the normal start time but then compute the stop time by taking
    # the start time and adding the number of samples * integration duration.
    metadata = kwargs['metadata']
    general_row = metadata['obs_general_row']
    start_time_sec = general_row['time1']

    if start_time_sec is None:
        return None

    supp_index_row = metadata['supp_index_row']
    samples = import_util.safe_column(supp_index_row, 'LINE_SAMPLES')
    integration_duration = _integration_duration_helper(**kwargs)

    if samples is None or integration_duration is None:
        return None

    return start_time_sec + samples*integration_duration

def populate_obs_general_COUVIS_target_name_OBS(**kwargs):
    return helper_cassini_intended_target_name(**kwargs)

def populate_obs_general_COUVIS_observation_duration_OBS(**kwargs):
    return populate_observation_duration_from_time(**kwargs)

def populate_obs_pds_COUVIS_note_OBS(**kwargs):
    metadata = kwargs['metadata']
    supp_index_row = metadata['supp_index_row']
    if supp_index_row is None:
        return None
    description = supp_index_row['DESCRIPTION']
    description = description.replace('The purpose of this observation is ',
                                      '')
    return description

def populate_obs_general_COUVIS_primary_file_spec_OBS(**kwargs):
    return _COUVIS_file_spec_helper(**kwargs)

def populate_obs_pds_COUVIS_primary_file_spec_OBS(**kwargs):
    return _COUVIS_file_spec_helper(**kwargs)

def populate_obs_pds_COUVIS_product_creation_time_OBS(**kwargs):
    return populate_product_creation_time_from_supp_index(**kwargs)

# Format: "CO-S-UVIS-2-SSB-V1.4"
def populate_obs_pds_COUVIS_data_set_id_OBS(**kwargs):
    return populate_data_set_id_from_index(**kwargs)

# Format: "EUV2015_001_17_57"
def populate_obs_pds_COUVIS_product_id_OBS(**kwargs):
    return populate_product_id_from_supp_index(**kwargs)

# We occasionally don't bother to generate ring_geo data for COUVIS, like during
# cruise, so just use the given RA/DEC from the label if needed. We don't make
# any effort to figure out the min/max values.
def populate_obs_general_COUVIS_right_asc1_OBS(**kwargs):
    metadata = kwargs['metadata']
    ring_geo_row = metadata.get('ring_geo_row', None)
    if ring_geo_row is not None:
        return import_util.safe_column(ring_geo_row, 'MINIMUM_RIGHT_ASCENSION')

    index_row = metadata['index_row']
    ra = import_util.safe_column(index_row, 'RIGHT_ASCENSION')
    return ra

def populate_obs_general_COUVIS_right_asc2_OBS(**kwargs):
    metadata = kwargs['metadata']
    ring_geo_row = metadata.get('ring_geo_row', None)
    if ring_geo_row is not None:
        return import_util.safe_column(ring_geo_row, 'MAXIMUM_RIGHT_ASCENSION')

    index_row = metadata['index_row']
    ra = import_util.safe_column(index_row, 'RIGHT_ASCENSION')
    return ra

def populate_obs_general_COUVIS_declination1_OBS(**kwargs):
    metadata = kwargs['metadata']
    ring_geo_row = metadata.get('ring_geo_row', None)
    if ring_geo_row is not None:
        return import_util.safe_column(ring_geo_row, 'MINIMUM_DECLINATION')

    index_row = metadata['index_row']
    dec = import_util.safe_column(index_row, 'DECLINATION')
    return dec

def populate_obs_general_COUVIS_declination2_OBS(**kwargs):
    metadata = kwargs['metadata']
    ring_geo_row = metadata.get('ring_geo_row', None)
    if ring_geo_row is not None:
        return import_util.safe_column(ring_geo_row, 'MAXIMUM_DECLINATION')

    index_row = metadata['index_row']
    dec = import_util.safe_column(index_row, 'DECLINATION')
    return dec


### OBS_TYPE_IMAGE TABLE ###

def _COUVIS_is_image(**kwargs):
    channel, image_time = _COUVIS_channel_time_helper(**kwargs)
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    slit_state = index_row['SLIT_STATE']

    if channel == 'HSP' or channel == 'HDAC':
        return False
    assert channel == 'EUV' or channel == 'FUV'
    if slit_state == 'OCCULTATION':
        return False

    supp_index_row = metadata['supp_index_row']
    if supp_index_row is None:
        import_util.log_nonrepeating_warning(
            '_COUVIS_is_image has channel EUV or FUV but no '+
            'DATA_OBJECT_TYPE available')
        return False

    object_type = supp_index_row['DATA_OBJECT_TYPE']
    if object_type == 'SPECTRUM':
        return False

    return True

def populate_obs_type_image_COUVIS_image_type_id_OBS(**kwargs):
    if _COUVIS_is_image(**kwargs):
        return 'PUSH'
    return None

def _integration_duration_helper(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    dur = import_util.safe_column(index_row, 'INTEGRATION_DURATION')

    if dur is None:
        return None

    channel, image_time = _COUVIS_channel_time_helper(**kwargs)
    if channel == 'HSP':
        # HSP integration_duration is in milliseconds!
        return dur/1000
    # EUV and FUV are in seconds! What were they thinking?
    return dur

def populate_obs_type_image_COUVIS_duration_OBS(**kwargs):
    if not _COUVIS_is_image(**kwargs):
        return None

    return _integration_duration_helper(**kwargs)

def populate_obs_type_image_COUVIS_levels_OBS(**kwargs):
    if not _COUVIS_is_image(**kwargs):
        return None

    return 65536

def populate_obs_type_image_COUVIS_lesser_pixel_size_OBS(**kwargs):
    if not _COUVIS_is_image(**kwargs):
        return None

    metadata = kwargs['metadata']
    supp_index_row = metadata.get('supp_index_row', None)
    if supp_index_row is None:
        return None
    line1 = import_util.safe_column(supp_index_row,
                                    'WINDOW_MINIMUM_LINE_NUMBER')
    line2 = import_util.safe_column(supp_index_row,
                                    'WINDOW_MAXIMUM_LINE_NUMBER')
    line_bin = import_util.safe_column(supp_index_row,
                                       'LINE_BINNING_FACTOR')
    samples = import_util.safe_column(supp_index_row, 'LINE_SAMPLES')
    if line1 is None or line2 is None or line_bin is None or samples is None:
        return None
    pixels = min(samples, (line2-line1+1)//line_bin)
    if pixels < 0:
        return None
    return pixels

def populate_obs_type_image_COUVIS_greater_pixel_size_OBS(**kwargs):
    if not _COUVIS_is_image(**kwargs):
        return None

    metadata = kwargs['metadata']
    supp_index_row = metadata.get('supp_index_row', None)
    if supp_index_row is None:
        return None
    line1 = import_util.safe_column(supp_index_row,
                                    'WINDOW_MINIMUM_LINE_NUMBER')
    line2 = import_util.safe_column(supp_index_row,
                                    'WINDOW_MAXIMUM_LINE_NUMBER')
    line_bin = import_util.safe_column(supp_index_row,
                                       'LINE_BINNING_FACTOR')
    samples = import_util.safe_column(supp_index_row, 'LINE_SAMPLES')
    if line1 is None or line2 is None or line_bin is None or samples is None:
        return None
    pixels = max(samples, (line2-line1+1)//line_bin)
    if pixels < 0:
        return None
    return pixels


### OBS_WAVELENGTH TABLE ###

def populate_obs_wavelength_COUVIS_wavelength1_OBS(**kwargs):
    channel, image_time = _COUVIS_channel_time_helper(**kwargs)
    if channel == 'HSP':
        return 0.11
    if channel == 'HDAC':
        return 0.115

    metadata = kwargs['metadata']
    supp_index_row = metadata.get('supp_index_row', None)
    if supp_index_row is None:
        return None
    band1 = import_util.safe_column(supp_index_row, 'MINIMUM_BAND_NUMBER')
    if band1 is None:
        return None

    if channel == 'EUV':
        return 0.0558 + band1 * 0.0000607422
    if channel == 'FUV':
        return 0.11 + band1 * 0.000078125

    import_util.log_nonrepeating_warning(
        'obs_wavelength_COUVIS_wavelength1 has unknown channel type '+
        f' {channel}')
    return None

def populate_obs_wavelength_COUVIS_wavelength2_OBS(**kwargs):
    channel, image_time = _COUVIS_channel_time_helper(**kwargs)
    if channel == 'HSP':
        return 0.19
    if channel == 'HDAC':
        return 0.180

    metadata = kwargs['metadata']
    supp_index_row = metadata.get('supp_index_row', None)
    if supp_index_row is None:
        return None
    band2 = import_util.safe_column(supp_index_row, 'MINIMUM_BAND_NUMBER')
    if band2 is None:
        return None

    if channel == 'EUV':
        return 0.0558 + (band2 + 1) * 0.0000607422
    if channel == 'FUV':
        return 0.11 + (band2 + 1) * 0.000078125

    import_util.log_nonrepeating_warning(
        'obs_wavelength_COUVIS_wavelength1 has unknown channel type '+
        f' {channel}')
    return None

def _COUVIS_wave_res_helper(**kwargs):
    metadata = kwargs['metadata']
    supp_index_row = metadata.get('supp_index_row', None)
    if supp_index_row is None:
        return None
    channel, image_time = _COUVIS_channel_time_helper(**kwargs)
    band_bin = import_util.safe_column(supp_index_row, 'BAND_BINNING_FACTOR')

    if channel == 'EUV':
        return band_bin * 0.0000607422
    if channel == 'FUV':
        return band_bin * 0.000078125

    wl_row = metadata['obs_wavelength_row']
    wl1 = wl_row['wavelength1']
    wl2 = wl_row['wavelength2']
    if wl1 is None or wl2 is None:
        return None
    return wl2 - wl1

def populate_obs_wavelength_COUVIS_wave_res1_OBS(**kwargs):
    return _COUVIS_wave_res_helper(**kwargs)

def populate_obs_wavelength_COUVIS_wave_res2_OBS(**kwargs):
    return _COUVIS_wave_res_helper(**kwargs)

def populate_obs_wavelength_COUVIS_wave_no1_OBS(**kwargs):
    metadata = kwargs['metadata']
    wl_row = metadata['obs_wavelength_row']
    wl2 = wl_row['wavelength2']

    if wl2 is None:
        return None

    return 10000. / wl2

def populate_obs_wavelength_COUVIS_wave_no2_OBS(**kwargs):
    metadata = kwargs['metadata']
    wl_row = metadata['obs_wavelength_row']
    wl1 = wl_row['wavelength1']

    if wl1 is None:
        return None

    return 10000. / wl1

def populate_obs_wavelength_COUVIS_wave_no_res1_OBS(**kwargs):
    channel, image_time = _COUVIS_channel_time_helper(**kwargs)
    metadata = kwargs['metadata']
    wl_row = metadata['obs_wavelength_row']

    if channel == 'HSP' or channel == 'HDAC':
        wno1 = wl_row['wave_no1']
        wno2 = wl_row['wave_no2']
        if wno1 is None or wno2 is None:
            return None
        return wno2 - wno1

    wave_res2 = wl_row['wave_res2']
    wl2 = wl_row['wavelength2']

    if wave_res2 is None or wl2 is None:
        return None

    return wave_res2 * 10000. / (wl2*wl2)

def populate_obs_wavelength_COUVIS_wave_no_res2_OBS(**kwargs):
    channel, image_time = _COUVIS_channel_time_helper(**kwargs)
    metadata = kwargs['metadata']
    wl_row = metadata['obs_wavelength_row']

    if channel == 'HSP' or channel == 'HDAC':
        wno1 = wl_row['wave_no1']
        wno2 = wl_row['wave_no2']
        if wno1 is None or wno2 is None:
            return None
        return wno2 - wno1

    wave_res1 = wl_row['wave_res1']
    wl1 = wl_row['wavelength1']

    if wave_res1 is None or wl1 is None:
        return None

    return wave_res1 * 10000. / (wl1*wl1)

def _spec_size_helper(**kwargs):
    channel, image_time = _COUVIS_channel_time_helper(**kwargs)
    metadata = kwargs['metadata']

    if channel == 'HSP' or channel == 'HDAC':
        return None

    supp_index_row = metadata.get('supp_index_row', None)
    if supp_index_row is None:
        return None
    band1 = import_util.safe_column(supp_index_row, 'MINIMUM_BAND_NUMBER')
    band2 = import_util.safe_column(supp_index_row, 'MAXIMUM_BAND_NUMBER')
    band_bin = import_util.safe_column(supp_index_row, 'BAND_BINNING_FACTOR')
    if band1 is None or band2 is None or band_bin is None:
        return None

    return (band2 - band1 + 1) // band_bin

def populate_obs_wavelength_COUVIS_spec_flag_OBS(**kwargs):
    spec_size = _spec_size_helper(**kwargs)
    if spec_size is None or spec_size < 1:
        return 'N'
    return 'Y'

def populate_obs_wavelength_COUVIS_spec_size_OBS(**kwargs):
    return _spec_size_helper(**kwargs)

def populate_obs_wavelength_COUVIS_polarization_type_OBS(**kwargs):
    return 'NONE'


### populate_obs_occultation TABLE ###

def populate_obs_occultation_COUVIS_occ_type_OBS(**kwargs):
    return None

def populate_obs_occultation_COUVIS_occ_dir_OBS(**kwargs):
    return None

def populate_obs_occultation_COUVIS_body_occ_flag_OBS(**kwargs):
    return None

def populate_obs_occultation_COUVIS_optical_depth_min_OBS(**kwargs):
    return None

def populate_obs_occultation_COUVIS_optical_depth_max_OBS(**kwargs):
    return None

def populate_obs_occultation_COUVIS_temporal_sampling_OBS(**kwargs):
    return None

def populate_obs_occultation_COUVIS_quality_score_OBS(**kwargs):
    return None

def populate_obs_occultation_COUVIS_wl_band_OBS(**kwargs):
    return None

def populate_obs_occultation_COUVIS_source_OBS(**kwargs):
    return None

def populate_obs_occultation_COUVIS_host_OBS(**kwargs):
    return None


################################################################################
# THESE NEED TO BE IMPLEMENTED FOR EVERY CASSINI INSTRUMENT
################################################################################

def populate_obs_mission_cassini_COUVIS_ert1_OBS(**kwargs):
    return None

def populate_obs_mission_cassini_COUVIS_ert2_OBS(**kwargs):
    return None

def populate_obs_mission_cassini_COUVIS_spacecraft_clock_count1_OBS(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    sc = index_row['SPACECRAFT_CLOCK_START_COUNT']
    sc = helper_fix_cassini_sclk(sc)
    if not sc.startswith('1/'):
        import_util.log_nonrepeating_warning(
            f'Badly formatted SPACECRAFT_CLOCK_START_COUNT "{sc}"')
        return None
    try:
        sc_cvt = opus_support.parse_cassini_sclk(sc)
    except Exception as e:
        import_util.log_nonrepeating_warning(
            f'Unable to parse Cassini SCLK "{sc}": {e}')
        return None
    return sc_cvt

# There is no SPACECRAFT_CLOCK_STOP_COUNT for COUVIS so we have to compute it.
# This works because Cassini SCLK is in units of seconds.
def populate_obs_mission_cassini_COUVIS_spacecraft_clock_count2_OBS(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    count = index_row['SPACECRAFT_CLOCK_START_COUNT']
    count = helper_fix_cassini_sclk(count)
    general_row = metadata['obs_general_row']
    time1 = general_row['time1']
    time2 = general_row['time2']
    try:
        count_sec = opus_support.parse_cassini_sclk(count)
    except Exception as e:
        import_util.log_nonrepeating_warning(
            f'Unable to parse Cassini SCLK "{count}": {e}')
        return None
    new_count_sec = count_sec + (time2-time1)
    return new_count_sec

def populate_obs_mission_cassini_COUVIS_mission_phase_name_OBS(**kwargs):
    return helper_cassini_mission_phase_name(**kwargs)

def populate_obs_mission_cassini_COUVIS_sequence_id_OBS(**kwargs):
    return None


################################################################################
# THESE ARE SPECIFIC TO OBS_INSTRUMENT_COUVIS
################################################################################

def populate_obs_instrument_couvis_channel_OBS(**kwargs):
    channel, image_time = _COUVIS_channel_time_helper(**kwargs)
    return (channel, channel)

def populate_obs_instrument_couvis_observation_type_OBS(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    obstype = index_row['OBSERVATION_TYPE']
    if obstype == '' or obstype == 'NULL':
        obstype = 'NONE'
    return obstype.upper()

def populate_obs_instrument_couvis_occultation_port_state_OBS(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    occ_state = index_row['OCCULTATION_PORT_STATE']
    if occ_state == 'NULL':
        occ_state = 'N/A'
    return occ_state.upper()

def populate_obs_instrument_couvis_integration_duration_OBS(**kwargs):
    return _integration_duration_helper(**kwargs)
