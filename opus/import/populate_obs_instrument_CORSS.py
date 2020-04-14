################################################################################
# populate_obs_instrument_CORSS.py
#
# Routines to populate fields specific to CORSS.
################################################################################

# Ordering:
#   time1/2 must come before planet_id
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

def _CORSS_file_spec_helper(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    # Format: "data/1294561143_1295221348/W1294561143_1.IMG"
    file_spec = index_row['FILE_SPECIFICATION_NAME']
    volume_id = kwargs['volume_id']
    return volume_id + '/' + file_spec

def populate_obs_general_CORSS_opus_id_OCC(**kwargs):
    file_spec = _CORSS_file_spec_helper(**kwargs)
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

def populate_obs_general_CORSS_ring_obs_id_OCC(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    instrument_id = index_row['INSTRUMENT_ID']
    camera = instrument_id[3]
    assert camera in ('N', 'W')
    filename = index_row['FILE_NAME']
    image_num = filename[1:11]
    planet = helper_cassini_planet_id(**kwargs)
    if planet is None:
        pl_str = ''
    else:
        pl_str = planet[0]

    return pl_str + '_IMG_CO_ISS_' + image_num + '_' + camera

def populate_obs_general_CORSS_inst_host_id_OCC(**kwargs):
    return 'CO'

def populate_obs_general_CORSS_time1_OCC(**kwargs):
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

def populate_obs_general_CORSS_time2_OCC(**kwargs):
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

def populate_obs_general_CORSS_target_name_OCC(**kwargs):
    return helper_cassini_intended_target_name(**kwargs)

def populate_obs_general_CORSS_observation_duration_OCC(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    exposure = import_util.safe_column(index_row, 'EXPOSURE_DURATION')
    return exposure / 1000

def populate_obs_general_CORSS_quantity_OCC(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    filter1, filter2 = index_row['FILTER_NAME']

    if filter1.startswith('UV') or filter2.startswith('UV'):
        return 'EMISSION'
    return 'REFLECT'

def populate_obs_general_CORSS_observation_type_OCC(**kwargs):
    return 'IMG' # Image

def populate_obs_pds_CORSS_note_OCC(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    return index_row['DESCRIPTION']

def populate_obs_general_CORSS_primary_file_spec_OCC(**kwargs):
    return _CORSS_file_spec_helper(**kwargs)

def populate_obs_pds_CORSS_primary_file_spec_OCC(**kwargs):
    return _CORSS_file_spec_helper(**kwargs)

def populate_obs_pds_CORSS_product_creation_time_OCC(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    pct = index_row['PRODUCT_CREATION_TIME']

    try:
        pct_sec = julian.tai_from_iso(pct)
    except Exception as e:
        import_util.log_nonrepeating_error(
            f'Bad product creation time format "{pct}": {e}')
        return None

    return pct_sec

# Format: "CO-E/V/J-ISSNA/ISSWA-2-EDR-V1.0"
def populate_obs_pds_CORSS_data_set_id_OCC(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    dsi = index_row['DATA_SET_ID']
    return (dsi, dsi)

# Format: 1_W1294561143.000
def populate_obs_pds_CORSS_product_id_OCC(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    product_id = index_row['PRODUCT_ID']

    return product_id

# We occasionally don't bother to generate ring_geo data for CORSS, like during
# cruise, so just use the given RA/DEC from the label if needed. We don't make
# any effort to figure out the min/max values.
def populate_obs_general_CORSS_right_asc1_OCC(**kwargs):
    metadata = kwargs['metadata']
    ring_geo_row = metadata.get('ring_geo_row', None)
    if ring_geo_row is not None:
        return import_util.safe_column(ring_geo_row, 'MINIMUM_RIGHT_ASCENSION')

    index_row = metadata['index_row']
    ra = import_util.safe_column(index_row, 'RIGHT_ASCENSION')
    return ra

def populate_obs_general_CORSS_right_asc2_OCC(**kwargs):
    metadata = kwargs['metadata']
    ring_geo_row = metadata.get('ring_geo_row', None)
    if ring_geo_row is not None:
        return import_util.safe_column(ring_geo_row, 'MAXIMUM_RIGHT_ASCENSION')

    index_row = metadata['index_row']
    ra = import_util.safe_column(index_row, 'RIGHT_ASCENSION')
    return ra

def populate_obs_general_CORSS_declination1_OCC(**kwargs):
    metadata = kwargs['metadata']
    ring_geo_row = metadata.get('ring_geo_row', None)
    if ring_geo_row is not None:
        return import_util.safe_column(ring_geo_row, 'MINIMUM_DECLINATION')

    index_row = metadata['index_row']
    dec = import_util.safe_column(index_row, 'DECLINATION')
    return dec

def populate_obs_general_CORSS_declination2_OCC(**kwargs):
    metadata = kwargs['metadata']
    ring_geo_row = metadata.get('ring_geo_row', None)
    if ring_geo_row is not None:
        return import_util.safe_column(ring_geo_row, 'MAXIMUM_DECLINATION')

    index_row = metadata['index_row']
    dec = import_util.safe_column(index_row, 'DECLINATION')
    return dec

# Format: "SCIENCE_CRUISE"
def populate_obs_mission_cassini_CORSS_mission_phase_name_OCC(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    mp = index_row['MISSION_PHASE_NAME']
    if mp.upper() == 'NULL':
        return None
    return mp.replace('_', ' ')

def populate_obs_mission_cassini_CORSS_sequence_id_OCC(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    seqid = index_row['SEQUENCE_ID']
    return seqid


### OBS_TYPE_IMAGE TABLE ###

def populate_obs_type_image_CORSS_image_type_id_OCC(**kwargs):
    return 'FRAM'

def populate_obs_type_image_CORSS_duration_OCC(**kwargs):
    metadata = kwargs['metadata']
    obs_general_row = metadata['obs_general_row']
    return obs_general_row['observation_duration']

# CORSS is 12 bits and always has a square FOV

def populate_obs_type_image_CORSS_levels_OCC(**kwargs):
    return 4096

def _pixel_size_helper(**kwargs):
    # For CORSS, this is both greater and lesser pixel size
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    exposure = index_row['INSTRUMENT_MODE_ID']
    if exposure == 'FULL':
        return 1024
    if exposure == 'SUM2':
        return 512
    if exposure == 'SUM4':
        return 256
    import_util.log_nonrepeating_error(
        f'Unknown INSTRUMENT_MODE_ID "{exposure}"')
    return None

def populate_obs_type_image_CORSS_lesser_pixel_size_OCC(**kwargs):
    return _pixel_size_helper(**kwargs)

def populate_obs_type_image_CORSS_greater_pixel_size_OCC(**kwargs):
    return _pixel_size_helper(**kwargs)


### OBS_WAVELENGTH TABLE ###

# See additional notes under _CORSS_FILTER_WAVELENGTHS
def _CORSS_wavelength_helper(inst, filter1, filter2):
    key = (inst, filter1, filter2)
    if key in _CORSS_FILTER_WAVELENGTHS:
        return _CORSS_FILTER_WAVELENGTHS[key]

    # If we don't have the exact key combination, try to set polarization equal
    # to CLEAR for lack of anything better to do.
    nfilter1 = filter1 if filter1.find('P') == -1 else 'CL1'
    nfilter2 = filter2 if filter2.find('P') == -1 else 'CL2'
    key2 = (inst, nfilter1, nfilter2)
    if key2 in _CORSS_FILTER_WAVELENGTHS:
        import_util.log_nonrepeating_warning(
            'Using CLEAR instead of polarized filter for unknown CORSS '+
            f'filter combination {key[0]}/{key[1]}/{key[2]}')
        return _CORSS_FILTER_WAVELENGTHS[key2]

    import_util.log_nonrepeating_warning(
        'Ignoring unknown CORSS filter combination '+
        f'{key[0]}/{key[1]}/{key[2]}')

    return None, None, None

# These are the center wavelength +/- FWHM/2
def populate_obs_wavelength_CORSS_wavelength1_OCC(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    instrument_id = index_row['INSTRUMENT_ID'][3]
    filter1, filter2 = index_row['FILTER_NAME']

    central_wl, fwhm, effective_wl = _CORSS_wavelength_helper(
            instrument_id, filter1, filter2)
    if central_wl is None or fwhm is None:
        return None
    return (central_wl - fwhm/2) / 1000 # microns

def populate_obs_wavelength_CORSS_wavelength2_OCC(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    instrument_id = index_row['INSTRUMENT_ID'][3]
    filter1, filter2 = index_row['FILTER_NAME']

    central_wl, fwhm, effective_wl = _CORSS_wavelength_helper(
            instrument_id, filter1, filter2)
    if central_wl is None or fwhm is None:
        return None
    return (central_wl + fwhm/2) / 1000 # microns

# CORSS is always a single passband - there are no ramps or grisms or prisms
# Thus the wavelength resolution is just the total size of the bandpass
def _wave_res_helper(**kwargs):
    metadata = kwargs['metadata']
    wl_row = metadata['obs_wavelength_row']
    wl1 = wl_row['wavelength1']
    wl2 = wl_row['wavelength2']
    if wl1 is None or wl2 is None:
        return None
    return wl2 - wl1

def populate_obs_wavelength_CORSS_wave_res1_OCC(**kwargs):
    return _wave_res_helper(**kwargs)

def populate_obs_wavelength_CORSS_wave_res2_OCC(**kwargs):
    return _wave_res_helper(**kwargs)

def populate_obs_wavelength_CORSS_wave_no1_OCC(**kwargs):
    metadata = kwargs['metadata']
    wavelength_row = metadata['obs_wavelength_row']
    wl2 = wavelength_row['wavelength2']
    if wl2 is None:
        return None
    return 10000 / wl2 # cm^-1

def populate_obs_wavelength_CORSS_wave_no2_OCC(**kwargs):
    metadata = kwargs['metadata']
    wavelength_row = metadata['obs_wavelength_row']
    wl1 = wavelength_row['wavelength1']
    if wl1 is None:
        return None
    return 10000 / wl1 # cm^-1

# Same logic as wave_res
def _wave_no_res_helper(**kwargs):
    metadata = kwargs['metadata']
    wl_row = metadata['obs_wavelength_row']
    wno1 = wl_row['wave_no1']
    wno2 = wl_row['wave_no2']
    if wno1 is None or wno2 is None:
        return None
    return wno2 - wno1

def populate_obs_wavelength_CORSS_wave_no_res1_OCC(**kwargs):
    return _wave_no_res_helper(**kwargs)

def populate_obs_wavelength_CORSS_wave_no_res2_OCC(**kwargs):
    return _wave_no_res_helper(**kwargs)

def populate_obs_wavelength_CORSS_spec_flag_OCC(**kwargs):
    return 'N'

def populate_obs_wavelength_CORSS_spec_size_OCC(**kwargs):
    return None

def populate_obs_wavelength_CORSS_polarization_type_OCC(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['obs_instrument_CORSS_row']
    the_filter = index_row['combined_filter']
    if the_filter.find('P') != -1:
        return 'LINEAR'
    return 'NONE'


### populate_obs_occultation TABLE ###

def populate_obs_occultation_CORSS_occ_type_OCC(**kwargs):
    return None

def populate_obs_occultation_CORSS_occ_dir_OCC(**kwargs):
    return None

def populate_obs_occultation_CORSS_body_occ_flag_OCC(**kwargs):
    return None

def populate_obs_occultation_CORSS_optical_depth_min_OCC(**kwargs):
    return None

def populate_obs_occultation_CORSS_optical_depth_max_OCC(**kwargs):
    return None

def populate_obs_occultation_CORSS_wl_band_OCC(**kwargs):
    return None

def populate_obs_occultation_CORSS_source_OCC(**kwargs):
    return None

def populate_obs_occultation_CORSS_host_OCC(**kwargs):
    return None


################################################################################
# THESE NEED TO BE IMPLEMENTED FOR EVERY CASSINI INSTRUMENT
################################################################################

def populate_obs_mission_cassini_CORSS_spacecraft_clock_count1_OCC(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    partition = index_row['SPACECRAFT_CLOCK_CNT_PARTITION']
    count = index_row['SPACECRAFT_CLOCK_START_COUNT']
    sc = str(partition) + '/' + str(count)
    sc = helper_fix_cassini_sclk(sc)
    try:
        sc_cvt = opus_support.parse_cassini_sclk(sc)
    except Exception as e:
        import_util.log_nonrepeating_warning(
            f'Unable to parse Cassini SCLK "{sc}": {e}')
        return None
    return sc_cvt

def populate_obs_mission_cassini_CORSS_spacecraft_clock_count2_OCC(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    partition = index_row['SPACECRAFT_CLOCK_CNT_PARTITION']
    count = index_row['SPACECRAFT_CLOCK_STOP_COUNT']
    sc = str(partition) + '/' + str(count)
    sc = helper_fix_cassini_sclk(sc)
    try:
        sc_cvt = opus_support.parse_cassini_sclk(sc)
    except Exception as e:
        import_util.log_nonrepeating_warning(
            f'Unable to parse Cassini SCLK "{sc}": {e}')
        return None

    cassini_row = metadata['obs_mission_cassini_row']
    sc1 = cassini_row['spacecraft_clock_count1']
    if sc1 is not None and sc_cvt < sc1:
        import_util.log_warning(
    f'spacecraft_clock_count1 ({sc1}) and spacecraft_clock_count2 ({sc_cvt}) '
    +f'are in the wrong order - setting to count1')
        sc_cvt = sc1
    else:
        index_row = metadata['index_row']
        image_number = index_row['IMAGE_NUMBER']
        sc2_int = int(sc_cvt)
        if int(image_number) != sc2_int:
            import_util.log_warning(
    f'spacecraft_clock_count2 ({sc_cvt}) and CORSS IMAGE_NUMBER '
    +f'({image_number}) don\'t match')

    return sc_cvt


################################################################################
# THESE ARE SPECIFIC TO OBS_INSTRUMENT_CORSS
################################################################################

def populate_obs_instrument_CORSS_camera(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    instrument_id = index_row['INSTRUMENT_ID']
    assert instrument_id[3] in ('N', 'W')
    return instrument_id[3]

def populate_obs_instrument_CORSS_combined_filter(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    instrument_id = index_row['INSTRUMENT_ID'][3]
    filter1, filter2 = index_row['FILTER_NAME']

    central_wl1, fwhm1, wl1 = _CORSS_wavelength_helper(
            instrument_id, filter1, 'CL2')
    central_wl2, fwhm2, wl2 = _CORSS_wavelength_helper(
            instrument_id, 'CL1', filter2)

    # Collapse the various angles of polarizer into one grand polarizer
    # if filter1[0] == 'P':
    #     filter1 = 'POL'
    # elif filter1[:3] == 'IRP':
    #     filter1 = 'IRPOL'
    #
    # if filter2[0] == 'P':
    #     filter2 = 'POL'
    # elif filter2[:3] == 'IRP':
    #     filter2 = 'IRPOL'

    new_filter = None

    if filter1 == 'CL1' and filter2 == 'CL2':
        new_filter = 'CLEAR'
    elif filter1 == 'CL1':
        new_filter = filter2
    elif filter2 == 'CL2':
        new_filter = filter1
    else:
        # If one of them is a polarizer, put it second
        if filter1.find('P') != -1:
            new_filter = filter2 + '+' + filter1
        elif filter2.find('P') != -1:
            new_filter = filter1 + '+' + filter2
        else:
            if (((wl1 is None or wl2 is None or wl1 == wl2) and
                 filter1 > filter2) or
                wl1 > wl2):
                # Place filters in wavelength order
                # If wavelengths are the same, make it name order
                filter1, filter2 = filter2, filter1
            new_filter = filter1 + '+' + filter2

    return (new_filter, new_filter)

def populate_obs_instrument_CORSS_image_observation_type(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    obs_type = index_row['IMAGE_OBSERVATION_TYPE']

    # Sometimes they have both SCIENCE,OPNAV and OPNAV,SCIENCE so normalize
    # the order
    has_science = obs_type.find('SCIENCE') != -1
    has_opnav = obs_type.find('OPNAV') != -1
    has_calib = obs_type.find('CALIBRATION') != -1
    has_support = obs_type.find('SUPPORT') != -1
    has_unk = obs_type.find('UNK') != -1
    has_eng = obs_type.find('ENGINEERING') != -1

    ret_list = []
    if has_science:
        ret_list.append('SCIENCE')
    if has_opnav:
        ret_list.append('OPNAV')
    if has_calib:
        ret_list.append('CALIBRATION')
    if has_eng:
        ret_list.append('ENGINEERING')
    if has_support:
        ret_list.append('SUPPORT')
    if has_unk:
        ret_list.append('UNKNOWN')

    ret = '/'.join(ret_list)

    # If the result isn't the same length as what we started with, we must've
    # encountered a new type we didn't know about
    if len(ret) != len(obs_type.replace('UNK','UNKNOWN')):
        import_util.log_nonrepeating_error(
            f'Unknown format for CORSS image_observation_type: "{obs_type}"')
        return None

    return ret

def populate_obs_instrument_CORSS_target_desc(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    target_desc = index_row['TARGET_DESC'].upper()

    if target_desc in CORSS_TARGET_DESC_MAPPING:
        target_desc = CORSS_TARGET_DESC_MAPPING[target_desc]

    return target_desc
