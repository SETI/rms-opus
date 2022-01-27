################################################################################
# populate_obs_mission_hubble_hubble.py
#
# Routines to populate fields specific to HST. It may change fields in
# obs_general or obs_mission_hubble_hubble.
################################################################################

import julian
import pdsfile

from config_data import *
import impglobals
import import_util

from populate_util import *


def _decode_filters(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    filter_name = index_row['FILTER_NAME']

    if filter_name.find('+') == -1:
        return filter_name, None
    return filter_name.split('+')


################################################################################
# THESE NEED TO BE IMPLEMENTED FOR EVERY MISSION
################################################################################

def _helper_hubble_planet_id(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    planet_name = index_row['PLANET_NAME']

    if planet_name not in ['VENUS', 'EARTH', 'MARS', 'JUPITER', 'SATURN',
                           'URANUS', 'NEPTUNE', 'PLUTO']:
        return None
    return planet_name[:3]

def populate_obs_general_HST_planet_id_OBS(**kwargs):
    planet = _helper_hubble_planet_id(**kwargs)
    if planet is None:
        return 'OTH'
    return planet


################################################################################
# THESE NEED TO BE IMPLEMENTED FOR EVERY INSTRUMENT
################################################################################

### OBS_GENERAL TABLE ###

def _HST_filespec_helper(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    # Format: "DATA/VISIT_05/O43B05C1Q.LBL"
    filespec = index_row['FILE_SPECIFICATION_NAME']
    volume_id = kwargs['volume_id']

    return volume_id + '/' + filespec

def populate_obs_general_HSTx_opus_id_OBS(**kwargs):
    filespec = _HST_filespec_helper(**kwargs)
    pds_file = pdsfile.PdsFile.from_filespec(filespec, fix_case=True)
    opus_id = pds_file.opus_id
    if not opus_id:
        import_util.log_nonrepeating_error(
            f'Unable to create OPUS_ID for FILE_SPEC "{filespec}"')
        return filespec.split('/')[-1]

    return opus_id.replace('.', '-')

populate_obs_general_HSTACS_opus_id_OBS = populate_obs_general_HSTx_opus_id_OBS
populate_obs_general_HSTNICMOS_opus_id_OBS = populate_obs_general_HSTx_opus_id_OBS
populate_obs_general_HSTSTIS_opus_id_OBS = populate_obs_general_HSTx_opus_id_OBS
populate_obs_general_HSTWFC3_opus_id_OBS = populate_obs_general_HSTx_opus_id_OBS
populate_obs_general_HSTWFPC2_opus_id_OBS = populate_obs_general_HSTx_opus_id_OBS

def populate_obs_general_HSTx_ring_obs_id_OBS(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    instrument_id = index_row['INSTRUMENT_ID']
    image_date = index_row['START_TIME'][:10]
    filename = index_row['PRODUCT_ID']
    planet = _helper_hubble_planet_id(**kwargs)
    if planet is None:
        pl_str = ''
    else:
        pl_str = planet[0]

    return (pl_str + '_IMG_HST_' + instrument_id + '_' + image_date + '_'
            + filename)

populate_obs_general_HSTACS_ring_obs_id_OBS = populate_obs_general_HSTx_ring_obs_id_OBS
populate_obs_general_HSTNICMOS_ring_obs_id_OBS = populate_obs_general_HSTx_ring_obs_id_OBS
populate_obs_general_HSTSTIS_ring_obs_id_OBS = populate_obs_general_HSTx_ring_obs_id_OBS
populate_obs_general_HSTWFC3_ring_obs_id_OBS = populate_obs_general_HSTx_ring_obs_id_OBS
populate_obs_general_HSTWFPC2_ring_obs_id_OBS = populate_obs_general_HSTx_ring_obs_id_OBS

def populate_obs_general_HSTx_inst_host_id_OBS(**kwargs):
    return 'HST'

populate_obs_general_HSTACS_inst_host_id_OBS = populate_obs_general_HSTx_inst_host_id_OBS
populate_obs_general_HSTNICMOS_inst_host_id_OBS = populate_obs_general_HSTx_inst_host_id_OBS
populate_obs_general_HSTSTIS_inst_host_id_OBS = populate_obs_general_HSTx_inst_host_id_OBS
populate_obs_general_HSTWFC3_inst_host_id_OBS = populate_obs_general_HSTx_inst_host_id_OBS
populate_obs_general_HSTWFPC2_inst_host_id_OBS = populate_obs_general_HSTx_inst_host_id_OBS

def populate_obs_general_HSTx_quantity_OBS(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    wl1 = import_util.safe_column(index_row, 'MINIMUM_WAVELENGTH')
    wl2 = import_util.safe_column(index_row, 'MAXIMUM_WAVELENGTH')

    if wl1 is None or wl2 is None:
        return 'REFLECT'

    # We call it "EMISSION" if at least 3/4 of the passband is below 350 nm
    # and the high end of the passband is below 400 nm.
    if wl2 < 0.4 and (3*wl1+wl2)/4 < 0.35:
        return 'EMISSION'
    return 'REFLECT'

populate_obs_general_HSTACS_quantity_OBS = populate_obs_general_HSTx_quantity_OBS
populate_obs_general_HSTNICMOS_quantity_OBS = populate_obs_general_HSTx_quantity_OBS
populate_obs_general_HSTSTIS_quantity_OBS = populate_obs_general_HSTx_quantity_OBS
populate_obs_general_HSTWFC3_quantity_OBS = populate_obs_general_HSTx_quantity_OBS
populate_obs_general_HSTWFPC2_quantity_OBS = populate_obs_general_HSTx_quantity_OBS

def populate_obs_general_HSTACS_observation_type_OBS(**kwargs):
    if _acs_spec_flag(**kwargs)[0]:
        return 'SPI'
    return 'IMG'

def populate_obs_general_HSTNICMOS_observation_type_OBS(**kwargs):
    if _nicmos_spec_flag(**kwargs)[0]:
        return 'SPI'
    return 'IMG'

def populate_obs_general_HSTWFC3_observation_type_OBS(**kwargs):
    if _wfc3_spec_flag(**kwargs)[0]:
        return 'SPI'
    return 'IMG'

def populate_obs_general_HSTWFPC2_observation_type_OBS(**kwargs):
    return 'IMG'

def populate_obs_general_HSTSTIS_observation_type_OBS(**kwargs):
    # STIS uses a prism/grism WITH a slit, so a spectrum/spectroscopic
    # observation is a 1-D spatial array of type SPECTRUM that has NO
    # image attributes.
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    obs_type = index_row['OBSERVATION_TYPE']
    if obs_type not in ('IMAGE', 'IMAGING', 'SPECTRUM', 'SPECTROSCOPIC'):
        import_util.log_nonrepeating_error(
            f'Unknown HST OBSERVATION_TYPE "{obs_type}"')
        return None
    if obs_type.startswith('SPEC'): # SPECTRUM or SPECTROSCOPIC
        return 'SPE' # Spectrum (1-D with spectral information)
    return 'IMG' # Image

def populate_obs_general_HSTx_time1_OBS(**kwargs):
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

populate_obs_general_HSTACS_time1_OBS = populate_obs_general_HSTx_time1_OBS
populate_obs_general_HSTNICMOS_time1_OBS = populate_obs_general_HSTx_time1_OBS
populate_obs_general_HSTSTIS_time1_OBS = populate_obs_general_HSTx_time1_OBS
populate_obs_general_HSTWFC3_time1_OBS = populate_obs_general_HSTx_time1_OBS
populate_obs_general_HSTWFPC2_time1_OBS = populate_obs_general_HSTx_time1_OBS

def populate_obs_general_HSTx_time2_OBS(**kwargs):
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

populate_obs_general_HSTACS_time2_OBS = populate_obs_general_HSTx_time2_OBS
populate_obs_general_HSTNICMOS_time2_OBS = populate_obs_general_HSTx_time2_OBS
populate_obs_general_HSTSTIS_time2_OBS = populate_obs_general_HSTx_time2_OBS
populate_obs_general_HSTWFC3_time2_OBS = populate_obs_general_HSTx_time2_OBS
populate_obs_general_HSTWFPC2_time2_OBS = populate_obs_general_HSTx_time2_OBS

def populate_obs_general_HSTx_target_name_OBS(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']

    target_name = index_row['TARGET_NAME'].upper()
    if target_name in TARGET_NAME_MAPPING:
        target_name = TARGET_NAME_MAPPING[target_name]

    if target_name not in TARGET_NAME_INFO:
        import_util.announce_unknown_target_name(target_name)
        if impglobals.ARGUMENTS.import_ignore_errors:
            return 'None'
        return None
    target_name_info = TARGET_NAME_INFO[target_name]
    return target_name, target_name_info[2]

populate_obs_general_HSTACS_target_name_OBS = populate_obs_general_HSTx_target_name_OBS
populate_obs_general_HSTNICMOS_target_name_OBS = populate_obs_general_HSTx_target_name_OBS
populate_obs_general_HSTSTIS_target_name_OBS = populate_obs_general_HSTx_target_name_OBS
populate_obs_general_HSTWFC3_target_name_OBS = populate_obs_general_HSTx_target_name_OBS
populate_obs_general_HSTWFPC2_target_name_OBS = populate_obs_general_HSTx_target_name_OBS

def populate_obs_general_HSTx_observation_duration_OBS(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    exposure = import_util.safe_column(index_row, 'EXPOSURE_DURATION')

    if exposure is None:
        return None

    return exposure

populate_obs_general_HSTACS_observation_duration_OBS = populate_obs_general_HSTx_observation_duration_OBS
populate_obs_general_HSTNICMOS_observation_duration_OBS = populate_obs_general_HSTx_observation_duration_OBS
populate_obs_general_HSTSTIS_observation_duration_OBS = populate_obs_general_HSTx_observation_duration_OBS
populate_obs_general_HSTWFC3_observation_duration_OBS = populate_obs_general_HSTx_observation_duration_OBS
populate_obs_general_HSTWFPC2_observation_duration_OBS = populate_obs_general_HSTx_observation_duration_OBS

def populate_obs_pds_HSTx_note_OBS(**kwargs):
    return None

populate_obs_pds_HSTACS_note_OBS = populate_obs_pds_HSTx_note_OBS
populate_obs_pds_HSTNICMOS_note_OBS = populate_obs_pds_HSTx_note_OBS
populate_obs_pds_HSTSTIS_note_OBS = populate_obs_pds_HSTx_note_OBS
populate_obs_pds_HSTWFC3_note_OBS = populate_obs_pds_HSTx_note_OBS
populate_obs_pds_HSTWFPC2_note_OBS = populate_obs_pds_HSTx_note_OBS

def populate_obs_general_HSTx_primary_filespec_OBS(**kwargs):
    filespec = _HST_filespec_helper(**kwargs)
    return filespec

populate_obs_general_HSTACS_primary_filespec_OBS = populate_obs_general_HSTx_primary_filespec_OBS
populate_obs_general_HSTNICMOS_primary_filespec_OBS = populate_obs_general_HSTx_primary_filespec_OBS
populate_obs_general_HSTSTIS_primary_filespec_OBS = populate_obs_general_HSTx_primary_filespec_OBS
populate_obs_general_HSTWFC3_primary_filespec_OBS = populate_obs_general_HSTx_primary_filespec_OBS
populate_obs_general_HSTWFPC2_primary_filespec_OBS = populate_obs_general_HSTx_primary_filespec_OBS

def populate_obs_pds_HSTx_primary_filespec_OBS(**kwargs):
    filespec = _HST_filespec_helper(**kwargs)
    return filespec

populate_obs_pds_HSTACS_primary_filespec_OBS = populate_obs_pds_HSTx_primary_filespec_OBS
populate_obs_pds_HSTNICMOS_primary_filespec_OBS = populate_obs_pds_HSTx_primary_filespec_OBS
populate_obs_pds_HSTSTIS_primary_filespec_OBS = populate_obs_pds_HSTx_primary_filespec_OBS
populate_obs_pds_HSTWFC3_primary_filespec_OBS = populate_obs_pds_HSTx_primary_filespec_OBS
populate_obs_pds_HSTWFPC2_primary_filespec_OBS = populate_obs_pds_HSTx_primary_filespec_OBS

def populate_obs_pds_HSTx_product_creation_time_OBS(**kwargs):
    return populate_product_creation_time_from_index(**kwargs)

populate_obs_pds_HSTACS_product_creation_time_OBS = populate_obs_pds_HSTx_product_creation_time_OBS
populate_obs_pds_HSTNICMOS_product_creation_time_OBS = populate_obs_pds_HSTx_product_creation_time_OBS
populate_obs_pds_HSTSTIS_product_creation_time_OBS = populate_obs_pds_HSTx_product_creation_time_OBS
populate_obs_pds_HSTWFC3_product_creation_time_OBS = populate_obs_pds_HSTx_product_creation_time_OBS
populate_obs_pds_HSTWFPC2_product_creation_time_OBS = populate_obs_pds_HSTx_product_creation_time_OBS

def populate_obs_pds_HSTx_data_set_id_OBS(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    dsi = index_row['DATA_SET_ID']
    return (dsi, dsi)

populate_obs_pds_HSTACS_data_set_id_OBS = populate_obs_pds_HSTx_data_set_id_OBS
populate_obs_pds_HSTNICMOS_data_set_id_OBS = populate_obs_pds_HSTx_data_set_id_OBS
populate_obs_pds_HSTSTIS_data_set_id_OBS = populate_obs_pds_HSTx_data_set_id_OBS
populate_obs_pds_HSTWFC3_data_set_id_OBS = populate_obs_pds_HSTx_data_set_id_OBS
populate_obs_pds_HSTWFPC2_data_set_id_OBS = populate_obs_pds_HSTx_data_set_id_OBS

def populate_obs_pds_HSTx_product_id_OBS(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    product_id = index_row['PRODUCT_ID']

    return product_id

populate_obs_pds_HSTACS_product_id_OBS = populate_obs_pds_HSTx_product_id_OBS
populate_obs_pds_HSTNICMOS_product_id_OBS = populate_obs_pds_HSTx_product_id_OBS
populate_obs_pds_HSTSTIS_product_id_OBS = populate_obs_pds_HSTx_product_id_OBS
populate_obs_pds_HSTWFC3_product_id_OBS = populate_obs_pds_HSTx_product_id_OBS
populate_obs_pds_HSTWFPC2_product_id_OBS = populate_obs_pds_HSTx_product_id_OBS

def populate_obs_general_HSTx_right_asc1_OBS(**kwargs):
    return None

populate_obs_general_HSTACS_right_asc1_OBS = populate_obs_general_HSTx_right_asc1_OBS
populate_obs_general_HSTNICMOS_right_asc1_OBS = populate_obs_general_HSTx_right_asc1_OBS
populate_obs_general_HSTSTIS_right_asc1_OBS = populate_obs_general_HSTx_right_asc1_OBS
populate_obs_general_HSTWFC3_right_asc1_OBS = populate_obs_general_HSTx_right_asc1_OBS
populate_obs_general_HSTWFPC2_right_asc1_OBS = populate_obs_general_HSTx_right_asc1_OBS

def populate_obs_general_HSTx_right_asc2_OBS(**kwargs):
    return None

populate_obs_general_HSTACS_right_asc2_OBS = populate_obs_general_HSTx_right_asc2_OBS
populate_obs_general_HSTNICMOS_right_asc2_OBS = populate_obs_general_HSTx_right_asc2_OBS
populate_obs_general_HSTSTIS_right_asc2_OBS = populate_obs_general_HSTx_right_asc2_OBS
populate_obs_general_HSTWFC3_right_asc2_OBS = populate_obs_general_HSTx_right_asc2_OBS
populate_obs_general_HSTWFPC2_right_asc2_OBS = populate_obs_general_HSTx_right_asc2_OBS

def populate_obs_general_HSTx_declination1_OBS(**kwargs):
    return None

populate_obs_general_HSTACS_declination1_OBS = populate_obs_general_HSTx_declination1_OBS
populate_obs_general_HSTNICMOS_declination1_OBS = populate_obs_general_HSTx_declination1_OBS
populate_obs_general_HSTSTIS_declination1_OBS = populate_obs_general_HSTx_declination1_OBS
populate_obs_general_HSTWFC3_declination1_OBS = populate_obs_general_HSTx_declination1_OBS
populate_obs_general_HSTWFPC2_declination1_OBS = populate_obs_general_HSTx_declination1_OBS

def populate_obs_general_HSTx_declination2_OBS(**kwargs):
    return None

populate_obs_general_HSTACS_declination2_OBS = populate_obs_general_HSTx_declination2_OBS
populate_obs_general_HSTNICMOS_declination2_OBS = populate_obs_general_HSTx_declination2_OBS
populate_obs_general_HSTSTIS_declination2_OBS = populate_obs_general_HSTx_declination2_OBS
populate_obs_general_HSTWFC3_declination2_OBS = populate_obs_general_HSTx_declination2_OBS
populate_obs_general_HSTWFPC2_declination2_OBS = populate_obs_general_HSTx_declination2_OBS


### OBS_TYPE_IMAGE TABLE ###

def _is_image(**kwargs):
    metadata = kwargs['metadata']
    general_row = metadata['obs_general_row']
    obs_type = general_row['observation_type']

    assert obs_type in ('IMG', 'SPE', 'SPI')
    return obs_type == 'IMG' or obs_type == 'SPI'

def populate_obs_type_image_HSTx_image_type_id_OBS(**kwargs):
    if not _is_image(**kwargs):
        return None

    return 'FRAM'

populate_obs_type_image_HSTACS_image_type_id_OBS = populate_obs_type_image_HSTx_image_type_id_OBS
populate_obs_type_image_HSTNICMOS_image_type_id_OBS = populate_obs_type_image_HSTx_image_type_id_OBS
populate_obs_type_image_HSTSTIS_image_type_id_OBS = populate_obs_type_image_HSTx_image_type_id_OBS
populate_obs_type_image_HSTWFC3_image_type_id_OBS = populate_obs_type_image_HSTx_image_type_id_OBS
populate_obs_type_image_HSTWFPC2_image_type_id_OBS = populate_obs_type_image_HSTx_image_type_id_OBS

def populate_obs_type_image_HSTx_duration_OBS(**kwargs):
    if not _is_image(**kwargs):
        return None

    metadata = kwargs['metadata']
    obs_general_row = metadata['obs_general_row']
    return obs_general_row['observation_duration']

populate_obs_type_image_HSTACS_duration_OBS = populate_obs_type_image_HSTx_duration_OBS
populate_obs_type_image_HSTNICMOS_duration_OBS = populate_obs_type_image_HSTx_duration_OBS
populate_obs_type_image_HSTSTIS_duration_OBS = populate_obs_type_image_HSTx_duration_OBS
populate_obs_type_image_HSTWFC3_duration_OBS = populate_obs_type_image_HSTx_duration_OBS
populate_obs_type_image_HSTWFPC2_duration_OBS = populate_obs_type_image_HSTx_duration_OBS

def populate_obs_type_image_HSTACS_levels_OBS(**kwargs):
    if not _is_image(**kwargs):
        return None

    return 65536 # ACS Inst Handbook 25, Sec 3.4.3

def populate_obs_type_image_HSTNICMOS_levels_OBS(**kwargs):
    if not _is_image(**kwargs):
        return None

    return 65536 # NICMOS Inst Handbook, Sec 7.2.1

def populate_obs_type_image_HSTSTIS_levels_OBS(**kwargs):
    if not _is_image(**kwargs):
        return None

    return 65536 # STIS Inst Handbook, Sec 7.5.1

def populate_obs_type_image_HSTWFC3_levels_OBS(**kwargs):
    if not _is_image(**kwargs):
        return None

    return 65536 # WFC3 Inst Handbook, Sec 2.2.3

def populate_obs_type_image_HSTWFPC2_levels_OBS(**kwargs):
    if not _is_image(**kwargs):
        return None

    return 4096 # WFPC2 Inst Handbook, Sec 2.8

def populate_obs_type_image_HSTx_lesser_pixel_size_OBS(**kwargs):
    if not _is_image(**kwargs):
        return None

    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    lines = import_util.safe_column(index_row, 'LINES')
    samples = import_util.safe_column(index_row, 'LINE_SAMPLES')
    if lines is None or samples is None:
        return None
    return min(lines, samples)

populate_obs_type_image_HSTACS_lesser_pixel_size_OBS = populate_obs_type_image_HSTx_lesser_pixel_size_OBS
populate_obs_type_image_HSTNICMOS_lesser_pixel_size_OBS = populate_obs_type_image_HSTx_lesser_pixel_size_OBS
populate_obs_type_image_HSTSTIS_lesser_pixel_size_OBS = populate_obs_type_image_HSTx_lesser_pixel_size_OBS
populate_obs_type_image_HSTWFC3_lesser_pixel_size_OBS = populate_obs_type_image_HSTx_lesser_pixel_size_OBS
populate_obs_type_image_HSTWFPC2_lesser_pixel_size_OBS = populate_obs_type_image_HSTx_lesser_pixel_size_OBS

def populate_obs_type_image_HSTx_greater_pixel_size_OBS(**kwargs):
    if not _is_image(**kwargs):
        return None

    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    lines = import_util.safe_column(index_row, 'LINES')
    samples = import_util.safe_column(index_row, 'LINE_SAMPLES')
    if lines is None or samples is None:
        return None
    return max(lines, samples)

populate_obs_type_image_HSTACS_greater_pixel_size_OBS = populate_obs_type_image_HSTx_greater_pixel_size_OBS
populate_obs_type_image_HSTNICMOS_greater_pixel_size_OBS = populate_obs_type_image_HSTx_greater_pixel_size_OBS
populate_obs_type_image_HSTSTIS_greater_pixel_size_OBS = populate_obs_type_image_HSTx_greater_pixel_size_OBS
populate_obs_type_image_HSTWFC3_greater_pixel_size_OBS = populate_obs_type_image_HSTx_greater_pixel_size_OBS
populate_obs_type_image_HSTWFPC2_greater_pixel_size_OBS = populate_obs_type_image_HSTx_greater_pixel_size_OBS


### OBS_WAVELENGTH TABLE ###

def populate_obs_wavelength_HSTx_wavelength1_OBS(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    wl1 = import_util.safe_column(index_row, 'MINIMUM_WAVELENGTH')
    wl2 = import_util.safe_column(index_row, 'MAXIMUM_WAVELENGTH')

    if wl1 is None or wl2 is None:
        return None

    # This is necessary because in some cases these are backwards in the table!
    if wl1 > wl2:
        import_util.log_warning(
            'MAXIMUM_WAVELENGTH < MINIMUM_WAVELENGTH; swapping')
        return wl2
    return wl1

populate_obs_wavelength_HSTACS_wavelength1_OBS = populate_obs_wavelength_HSTx_wavelength1_OBS
populate_obs_wavelength_HSTNICMOS_wavelength1_OBS = populate_obs_wavelength_HSTx_wavelength1_OBS
populate_obs_wavelength_HSTSTIS_wavelength1_OBS = populate_obs_wavelength_HSTx_wavelength1_OBS
populate_obs_wavelength_HSTWFC3_wavelength1_OBS = populate_obs_wavelength_HSTx_wavelength1_OBS
populate_obs_wavelength_HSTWFPC2_wavelength1_OBS = populate_obs_wavelength_HSTx_wavelength1_OBS

def populate_obs_wavelength_HSTx_wavelength2_OBS(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    wl1 = import_util.safe_column(index_row, 'MINIMUM_WAVELENGTH')
    wl2 = import_util.safe_column(index_row, 'MAXIMUM_WAVELENGTH')

    if wl1 is None or wl2 is None:
        return None

    # This is necessary because in some cases these are backwards in the table!
    if wl1 > wl2:
        return wl1
    return wl2

populate_obs_wavelength_HSTACS_wavelength2_OBS = populate_obs_wavelength_HSTx_wavelength2_OBS
populate_obs_wavelength_HSTNICMOS_wavelength2_OBS = populate_obs_wavelength_HSTx_wavelength2_OBS
populate_obs_wavelength_HSTSTIS_wavelength2_OBS = populate_obs_wavelength_HSTx_wavelength2_OBS
populate_obs_wavelength_HSTWFC3_wavelength2_OBS = populate_obs_wavelength_HSTx_wavelength2_OBS
populate_obs_wavelength_HSTWFPC2_wavelength2_OBS = populate_obs_wavelength_HSTx_wavelength2_OBS

def populate_obs_wavelength_HSTx_wave_res1_OBS(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    wr = import_util.safe_column(index_row, 'WAVELENGTH_RESOLUTION')

    return wr

populate_obs_wavelength_HSTACS_wave_res1_OBS = populate_obs_wavelength_HSTx_wave_res1_OBS
populate_obs_wavelength_HSTNICMOS_wave_res1_OBS = populate_obs_wavelength_HSTx_wave_res1_OBS
populate_obs_wavelength_HSTWFC3_wave_res1_OBS = populate_obs_wavelength_HSTx_wave_res1_OBS
populate_obs_wavelength_HSTWFPC2_wave_res1_OBS = populate_obs_wavelength_HSTx_wave_res1_OBS

def populate_obs_wavelength_HSTx_wave_res2_OBS(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    wr = import_util.safe_column(index_row, 'WAVELENGTH_RESOLUTION')

    return wr

populate_obs_wavelength_HSTACS_wave_res2_OBS = populate_obs_wavelength_HSTx_wave_res2_OBS
populate_obs_wavelength_HSTNICMOS_wave_res2_OBS = populate_obs_wavelength_HSTx_wave_res2_OBS
populate_obs_wavelength_HSTWFC3_wave_res2_OBS = populate_obs_wavelength_HSTx_wave_res2_OBS
populate_obs_wavelength_HSTWFPC2_wave_res2_OBS = populate_obs_wavelength_HSTx_wave_res2_OBS

def populate_obs_wavelength_HSTSTIS_wave_res1_OBS(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    wr1 = import_util.safe_column(index_row, 'MAXIMUM_WAVELENGTH_RESOLUTION')
    wr2 = import_util.safe_column(index_row, 'MINIMUM_WAVELENGTH_RESOLUTION')

    # This is necessary because in some cases these are backwards in the table!
    if wr1 > wr2:
        import_util.log_warning(
            'MAXIMUM_WAVELENGTH_RESOLUTION < MINIMUM_WAVELENGTH_RESOLUTION; '
            +'swapping')
        return wr2
    return wr1

def populate_obs_wavelength_HSTSTIS_wave_res2_OBS(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    wr1 = import_util.safe_column(index_row, 'MAXIMUM_WAVELENGTH_RESOLUTION')
    wr2 = import_util.safe_column(index_row, 'MINIMUM_WAVELENGTH_RESOLUTION')

    # This is necessary because in some cases these are backwards in the table!
    if wr1 > wr2:
        return wr1
    return wr2

def populate_obs_wavelength_HSTx_wave_no1_OBS(**kwargs):
    metadata = kwargs['metadata']
    wavelength_row = metadata['obs_wavelength_row']
    wl2 = wavelength_row['wavelength2']
    if wl2 is None:
        return None
    return 10000 / wl2 # cm^-1

populate_obs_wavelength_HSTACS_wave_no1_OBS = populate_obs_wavelength_HSTx_wave_no1_OBS
populate_obs_wavelength_HSTNICMOS_wave_no1_OBS = populate_obs_wavelength_HSTx_wave_no1_OBS
populate_obs_wavelength_HSTSTIS_wave_no1_OBS = populate_obs_wavelength_HSTx_wave_no1_OBS
populate_obs_wavelength_HSTWFC3_wave_no1_OBS = populate_obs_wavelength_HSTx_wave_no1_OBS
populate_obs_wavelength_HSTWFPC2_wave_no1_OBS = populate_obs_wavelength_HSTx_wave_no1_OBS

def populate_obs_wavelength_HSTx_wave_no2_OBS(**kwargs):
    metadata = kwargs['metadata']
    wavelength_row = metadata['obs_wavelength_row']
    wl1 = wavelength_row['wavelength1']
    if wl1 is None:
        return None
    return 10000 / wl1 # cm^-1

populate_obs_wavelength_HSTACS_wave_no2_OBS = populate_obs_wavelength_HSTx_wave_no2_OBS
populate_obs_wavelength_HSTNICMOS_wave_no2_OBS = populate_obs_wavelength_HSTx_wave_no2_OBS
populate_obs_wavelength_HSTSTIS_wave_no2_OBS = populate_obs_wavelength_HSTx_wave_no2_OBS
populate_obs_wavelength_HSTWFC3_wave_no2_OBS = populate_obs_wavelength_HSTx_wave_no2_OBS
populate_obs_wavelength_HSTWFPC2_wave_no2_OBS = populate_obs_wavelength_HSTx_wave_no2_OBS

def populate_obs_wavelength_HSTx_wave_no_res1_OBS(**kwargs):
    metadata = kwargs['metadata']
    wl_row = metadata['obs_wavelength_row']
    wno1 = wl_row['wave_no1']
    wno2 = wl_row['wave_no2']
    if wno1 is None or wno2 is None:
        return None
    return wno2 - wno1

populate_obs_wavelength_HSTACS_wave_no_res1_OBS = populate_obs_wavelength_HSTx_wave_no_res1_OBS
populate_obs_wavelength_HSTNICMOS_wave_no_res1_OBS = populate_obs_wavelength_HSTx_wave_no_res1_OBS
populate_obs_wavelength_HSTWFC3_wave_no_res1_OBS = populate_obs_wavelength_HSTx_wave_no_res1_OBS
populate_obs_wavelength_HSTWFPC2_wave_no_res1_OBS = populate_obs_wavelength_HSTx_wave_no_res1_OBS

def populate_obs_wavelength_HSTx_wave_no_res2_OBS(**kwargs):
    metadata = kwargs['metadata']
    wl_row = metadata['obs_wavelength_row']
    wno1 = wl_row['wave_no1']
    wno2 = wl_row['wave_no2']
    if wno1 is None or wno2 is None:
        return None
    return wno2 - wno1

populate_obs_wavelength_HSTACS_wave_no_res2_OBS = populate_obs_wavelength_HSTx_wave_no_res2_OBS
populate_obs_wavelength_HSTNICMOS_wave_no_res2_OBS = populate_obs_wavelength_HSTx_wave_no_res2_OBS
populate_obs_wavelength_HSTWFC3_wave_no_res2_OBS = populate_obs_wavelength_HSTx_wave_no_res2_OBS
populate_obs_wavelength_HSTWFPC2_wave_no_res2_OBS = populate_obs_wavelength_HSTx_wave_no_res2_OBS

def populate_obs_wavelength_HSTSTIS_wave_no_res1_OBS(**kwargs):
    metadata = kwargs['metadata']
    wl_row = metadata['obs_wavelength_row']
    wave_res2 = wl_row['wave_res2']
    wl2 = wl_row['wavelength2']

    if wave_res2 is None or wl2 is None:
        return None

    return wave_res2 * 10000. / (wl2*wl2)

def populate_obs_wavelength_HSTSTIS_wave_no_res2_OBS(**kwargs):
    metadata = kwargs['metadata']
    wl_row = metadata['obs_wavelength_row']
    wave_res1 = wl_row['wave_res1']
    wl1 = wl_row['wavelength1']

    if wave_res1 is None or wl1 is None:
        return None

    return wave_res1 * 10000. / (wl1*wl1)


### populate_obs_occultation TABLE ###

def populate_obs_occultation_HSTx_occ_type_OBS(**kwargs):
    return None

populate_obs_occultation_HSTACS_occ_type_OBS = populate_obs_occultation_HSTx_occ_type_OBS
populate_obs_occultation_HSTNICMOS_occ_type_OBS = populate_obs_occultation_HSTx_occ_type_OBS
populate_obs_occultation_HSTSTIS_occ_type_OBS = populate_obs_occultation_HSTx_occ_type_OBS
populate_obs_occultation_HSTWFC3_occ_type_OBS = populate_obs_occultation_HSTx_occ_type_OBS
populate_obs_occultation_HSTWFPC2_occ_type_OBS = populate_obs_occultation_HSTx_occ_type_OBS

def populate_obs_occultation_HSTx_occ_dir_OBS(**kwargs):
    return None

populate_obs_occultation_HSTACS_occ_dir_OBS = populate_obs_occultation_HSTx_occ_dir_OBS
populate_obs_occultation_HSTNICMOS_occ_dir_OBS = populate_obs_occultation_HSTx_occ_dir_OBS
populate_obs_occultation_HSTSTIS_occ_dir_OBS = populate_obs_occultation_HSTx_occ_dir_OBS
populate_obs_occultation_HSTWFC3_occ_dir_OBS = populate_obs_occultation_HSTx_occ_dir_OBS
populate_obs_occultation_HSTWFPC2_occ_dir_OBS = populate_obs_occultation_HSTx_occ_dir_OBS

def populate_obs_occultation_HSTx_body_occ_flag_OBS(**kwargs):
    return None

populate_obs_occultation_HSTACS_body_occ_flag_OBS = populate_obs_occultation_HSTx_body_occ_flag_OBS
populate_obs_occultation_HSTNICMOS_body_occ_flag_OBS = populate_obs_occultation_HSTx_body_occ_flag_OBS
populate_obs_occultation_HSTSTIS_body_occ_flag_OBS = populate_obs_occultation_HSTx_body_occ_flag_OBS
populate_obs_occultation_HSTWFC3_body_occ_flag_OBS = populate_obs_occultation_HSTx_body_occ_flag_OBS
populate_obs_occultation_HSTWFPC2_body_occ_flag_OBS = populate_obs_occultation_HSTx_body_occ_flag_OBS

def populate_obs_occultation_HSTx_optical_depth_min_OBS(**kwargs):
    return None

populate_obs_occultation_HSTACS_optical_depth_min_OBS = populate_obs_occultation_HSTx_optical_depth_min_OBS
populate_obs_occultation_HSTNICMOS_optical_depth_min_OBS = populate_obs_occultation_HSTx_optical_depth_min_OBS
populate_obs_occultation_HSTSTIS_optical_depth_min_OBS = populate_obs_occultation_HSTx_optical_depth_min_OBS
populate_obs_occultation_HSTWFC3_optical_depth_min_OBS = populate_obs_occultation_HSTx_optical_depth_min_OBS
populate_obs_occultation_HSTWFPC2_optical_depth_min_OBS = populate_obs_occultation_HSTx_optical_depth_min_OBS

def populate_obs_occultation_HSTx_optical_depth_max_OBS(**kwargs):
    return None

populate_obs_occultation_HSTACS_optical_depth_max_OBS = populate_obs_occultation_HSTx_optical_depth_max_OBS
populate_obs_occultation_HSTNICMOS_optical_depth_max_OBS = populate_obs_occultation_HSTx_optical_depth_max_OBS
populate_obs_occultation_HSTSTIS_optical_depth_max_OBS = populate_obs_occultation_HSTx_optical_depth_max_OBS
populate_obs_occultation_HSTWFC3_optical_depth_max_OBS = populate_obs_occultation_HSTx_optical_depth_max_OBS
populate_obs_occultation_HSTWFPC2_optical_depth_max_OBS = populate_obs_occultation_HSTx_optical_depth_max_OBS

def populate_obs_occultation_HSTx_temporal_sampling_OBS(**kwargs):
    return None

populate_obs_occultation_HSTACS_temporal_sampling_OBS = populate_obs_occultation_HSTx_temporal_sampling_OBS
populate_obs_occultation_HSTNICMOS_temporal_sampling_OBS = populate_obs_occultation_HSTx_temporal_sampling_OBS
populate_obs_occultation_HSTSTIS_temporal_sampling_OBS = populate_obs_occultation_HSTx_temporal_sampling_OBS
populate_obs_occultation_HSTWFC3_temporal_sampling_OBS = populate_obs_occultation_HSTx_temporal_sampling_OBS
populate_obs_occultation_HSTWFPC2_temporal_sampling_OBS = populate_obs_occultation_HSTx_temporal_sampling_OBS

def populate_obs_occultation_HSTx_quality_score_OBS(**kwargs):
    return None

populate_obs_occultation_HSTACS_quality_score_OBS = populate_obs_occultation_HSTx_quality_score_OBS
populate_obs_occultation_HSTNICMOS_quality_score_OBS = populate_obs_occultation_HSTx_quality_score_OBS
populate_obs_occultation_HSTSTIS_quality_score_OBS = populate_obs_occultation_HSTx_quality_score_OBS
populate_obs_occultation_HSTWFC3_quality_score_OBS = populate_obs_occultation_HSTx_quality_score_OBS
populate_obs_occultation_HSTWFPC2_quality_score_OBS = populate_obs_occultation_HSTx_quality_score_OBS

def populate_obs_occultation_HSTx_wl_band_OBS(**kwargs):
    return None

populate_obs_occultation_HSTACS_wl_band_OBS = populate_obs_occultation_HSTx_wl_band_OBS
populate_obs_occultation_HSTNICMOS_wl_band_OBS = populate_obs_occultation_HSTx_wl_band_OBS
populate_obs_occultation_HSTSTIS_wl_band_OBS = populate_obs_occultation_HSTx_wl_band_OBS
populate_obs_occultation_HSTWFC3_wl_band_OBS = populate_obs_occultation_HSTx_wl_band_OBS
populate_obs_occultation_HSTWFPC2_wl_band_OBS = populate_obs_occultation_HSTx_wl_band_OBS

def populate_obs_occultation_HSTx_source_OBS(**kwargs):
    return None

populate_obs_occultation_HSTACS_source_OBS = populate_obs_occultation_HSTx_source_OBS
populate_obs_occultation_HSTNICMOS_source_OBS = populate_obs_occultation_HSTx_source_OBS
populate_obs_occultation_HSTSTIS_source_OBS = populate_obs_occultation_HSTx_source_OBS
populate_obs_occultation_HSTWFC3_source_OBS = populate_obs_occultation_HSTx_source_OBS
populate_obs_occultation_HSTWFPC2_source_OBS = populate_obs_occultation_HSTx_source_OBS

def populate_obs_occultation_HSTx_host_OBS(**kwargs):
    return None

populate_obs_occultation_HSTACS_host_OBS = populate_obs_occultation_HSTx_host_OBS
populate_obs_occultation_HSTNICMOS_host_OBS = populate_obs_occultation_HSTx_host_OBS
populate_obs_occultation_HSTSTIS_host_OBS = populate_obs_occultation_HSTx_host_OBS
populate_obs_occultation_HSTWFC3_host_OBS = populate_obs_occultation_HSTx_host_OBS
populate_obs_occultation_HSTWFPC2_host_OBS = populate_obs_occultation_HSTx_host_OBS


### ACS ###

def _acs_spec_flag(**kwargs):
    filter1, filter2 = _decode_filters(**kwargs)
    return (filter1.startswith('G') or filter1.startswith('PR'),
            filter1, filter2)

def populate_obs_wavelength_HSTACS_spec_flag_OBS(**kwargs):
    if _acs_spec_flag(**kwargs)[0]:
        return 'Y'
    return 'N'

def populate_obs_wavelength_HSTACS_spec_size_OBS(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']

    spec_flag, filter1, filter2 = _acs_spec_flag(**kwargs)
    if not spec_flag:
        return None

    # We can't use WAVELENGTH_RESOLUTION because it's too aggressive.
    # Instead we use the Resolving Power (lambda / d-lambda) from ACS Inst
    # Handbook Table 3.5

    if filter1 == 'G800L':
        # G800L's resolving power depends on the channel and order, which we
        # don't know
        import_util.log_nonrepeating_warning(
            'G800L filter used, but not enough information available to '+
            'compute spec_size')
        wr = 8000. / 140 * .0001
        bw = (10500-5500) * .0001
    elif filter1 == 'PR200L':
        wr = 2500. / 59 * .0001
        bw = (3900-1700) * .0001
    elif filter1 == 'PR110L':
        wr = 1500. / 79 * .0001
        bw = (1800-1150) * .0001
    elif filter1 == 'PR130L':
        wr = 1500. / 96 * .0001
        bw = (1800-1250) * .0001
    else:
        assert False, filter1

    spec_size = bw // wr

    lines = import_util.safe_column(index_row, 'LINES')
    samples = import_util.safe_column(index_row, 'LINE_SAMPLES')
    if lines is None or samples is None:
        return spec_size

    return min(max(lines, samples), spec_size)

def populate_obs_wavelength_HSTACS_polarization_type_OBS(**kwargs):
    filter1, filter2 = _decode_filters(**kwargs)
    if filter2 is not None and filter2.startswith('POL'):
        return 'LINEAR'
    return 'NONE'

def populate_obs_mission_hubble_HSTACS_filter_type(**kwargs):
    filter1, filter2 = _decode_filters(**kwargs)
    # We only care about filter1 since the second is (almost) always a
    # polarizer
    if filter2 is not None and not filter2.startswith('POL'):
        import_util.log_nonrepeating_warning(
            f'Filter combination {filter1}+{filter2} does not have a'
            +' polarizer as the second filter - filter_type may be wrong')

    # From ACS Inst handbook Table 3.3
    if filter1 in ['F475W', 'F625W', 'F775W', 'F850LP', 'F435W', 'F555W',
                   'F550M', 'F606W', 'F814W', 'F220W', 'F250W', 'F330W',
                   'CLEAR']:
        return 'W'

    if filter1 in ['F658N', 'F502N', 'F660N', 'F344N', 'F892N']:
        return 'N'

    if filter1.startswith('FR'):
        return 'FR'

    if filter1 in ['G800L', 'PR200L', 'PR110L', 'PR130L']:
        return 'SP'

    if filter1 in ['F122M']:
        return 'M'

    if filter1 in ['F115LP', 'F125LP', 'F140LP', 'F150LP', 'F165LP']:
        return 'LP'

    # ACS doesn't have any CH4 filters

    import_util.log_nonrepeating_error(
        f'Unknown filter {filter1} while determining filter type')
    return None


### NICMOS ###

def _nicmos_spec_flag(**kwargs):
    filter1, filter2 = _decode_filters(**kwargs)
    return filter1.startswith('G'), filter1, filter2

def populate_obs_wavelength_HSTNICMOS_spec_flag_OBS(**kwargs):
    if _nicmos_spec_flag(**kwargs)[0]:
        return 'Y'
    return 'N'

def populate_obs_wavelength_HSTNICMOS_spec_size_OBS(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']

    spec_flag, filter1, filter2 = _nicmos_spec_flag(**kwargs)
    assert filter2 is None
    if not spec_flag:
        return None

    # We can't use WAVELENGTH_RESOLUTION because it's too aggressive.
    # Instead we use the Resolving Power (lambda / d-lambda) from NICMOS Inst
    # Handbook Tables 5.3 and 5.5

    # if filter1 == 'G096':
    #     wr = 1.0 / 200
    #     bw = 1.2-0.8
    # elif filter1 == 'G141':
    #     wr = 1.5 / 200
    #     bw = 1.9-1.1
    # elif filter1 == 'G206':
    #     wr = 1.95 / 200
    #     bw = 2.5-1.4
    # else:
    #     assert False, filter1
    #
    # spec_size = bw // wr

    # For NICMOS, the entire detector is used for the spectrum, but we don't
    # know which direction it goes in, so just be generous and give the maximum
    # dimension of the image.
    lines = import_util.safe_column(index_row, 'LINES')
    samples = import_util.safe_column(index_row, 'LINE_SAMPLES')
    if lines is None and samples is None:
        return None
    if lines is None:
        return samples
    if samples is None:
        return lines
    return max(lines, samples)

def populate_obs_wavelength_HSTNICMOS_polarization_type_OBS(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    filter_name = index_row['FILTER_NAME']

    if filter_name.find('POL') == -1:
        return 'NONE'
    return 'LINEAR'

def populate_obs_mission_hubble_HSTNICMOS_filter_type(**kwargs):
    filter1, filter2 = _decode_filters(**kwargs)

    # NICMOS doesn't do filter stacking
    assert filter2 is None

    if filter1.startswith('G'):
        return 'SP'
    if filter1.endswith('N'):
        return 'N'
    if filter1.endswith('M'):
        return 'M'
    if filter1.endswith('W'):
        return 'W'

    if filter1.startswith('POL'):
        if filter1.endswith('S'):
            return 'W' # POLxS is 0.8-1.3, about the same as wide filters
        elif filter1.endswith('L'):
            return 'M' # POLxL is 1.89-2.1, about the same as medium filters

    if filter1 == 'BLANK': # Opaque
        return 'OT'

    import_util.log_nonrepeating_error(f'Unknown filter "{filter1}"')
    return None


### STIS ###

def _stis_spec_flag(**kwargs):
    metadata = kwargs['metadata']
    general_row = metadata['obs_general_row']
    obs_type = general_row['observation_type']

    assert obs_type in ('IMG', 'SPE')
    return obs_type == 'SPE'

def populate_obs_wavelength_HSTSTIS_spec_flag_OBS(**kwargs):
    if _stis_spec_flag(**kwargs):
        return 'Y'
    return 'N'

def populate_obs_wavelength_HSTSTIS_spec_size_OBS(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']

    if not _stis_spec_flag(**kwargs):
        return None

    lines = import_util.safe_column(index_row, 'LINES')
    samples = import_util.safe_column(index_row, 'LINE_SAMPLES')
    x1d_size = import_util.safe_column(index_row, 'X1D_SPECTRUM_SIZE')
    if lines is None:
        lines = 0
    if samples is None:
        samples = 0
    if x1d_size is None:
        x1d_size = 0

    return max(lines, samples, x1d_size)

def populate_obs_wavelength_HSTSTIS_polarization_type_OBS(**kwargs):
    return 'NONE'

def populate_obs_mission_hubble_HSTSTIS_filter_type(**kwargs):
    filter1, filter2 = _decode_filters(**kwargs)
    assert filter2 is None

    if filter1 in ['CLEAR', 'CRYSTAL QUARTZ', 'LONG_PASS',
                   'STRONTIUM_FLUORIDE', 'ND_3']:
        return 'LP'
    if filter1 == 'LYMAN_ALPHA':
        return 'N'

    import_util.log_nonrepeating_error(f'Unknown filter "{filter1}"')
    return None


### WFC3 ###

def _wfc3_spec_flag(**kwargs):
    filter1, filter2 = _decode_filters(**kwargs)
    assert filter2 is None
    return filter1.startswith('G'), filter1, filter2

def populate_obs_wavelength_HSTWFC3_spec_flag_OBS(**kwargs):
    if _wfc3_spec_flag(**kwargs)[0]:
        return 'Y'
    return 'N'

def populate_obs_wavelength_HSTWFC3_spec_size_OBS(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']

    spec_flag, filter1, filter2 = _wfc3_spec_flag(**kwargs)
    if not spec_flag:
        return None

    # We can't use WAVELENGTH_RESOLUTION because it's too aggressive.
    # Instead we use the Resolving Power (lambda / d-lambda) from WFC3 Inst
    # Handbook Table 8.1

    if filter1 == 'G280':
        wr = 300. / 70 * .001
        bw = (450-190) * .001
    elif filter1 == 'G102':
        wr = 1000. / 210 * .001
        bw = (1150-800) * .001
    elif filter1 == 'G141':
        wr = 1400. / 130 * .001
        bw = (1700-1075) * .001
    else:
        assert False, filter1

    spec_size = bw // wr

    lines = import_util.safe_column(index_row, 'LINES')
    samples = import_util.safe_column(index_row, 'LINE_SAMPLES')
    if lines is None or samples is None:
        return spec_size

    return min(max(lines, samples), spec_size)

def populate_obs_wavelength_HSTWFC3_polarization_type_OBS(**kwargs):
    return 'NONE'

def populate_obs_mission_hubble_HSTWFC3_filter_type(**kwargs):
    filter1, filter2 = _decode_filters(**kwargs)

    # WFC3 doesn't do filter stacking
    assert filter2 is None

    if filter1.startswith('FR'):
        return 'FR'
    if filter1.startswith('G'):
        return 'SP'
    if filter1.endswith('N'):
        return 'N'
    if filter1.endswith('M'):
        return 'M'
    if filter1.endswith('W'):
        return 'W'
    if filter1.endswith('LP'):
        return 'LP'
    if filter1.endswith('X'):
        return 'X'

    import_util.log_nonrepeating_error(f'Unknown filter "{filter1}"')
    return None


### WFPC2 ###

def populate_obs_wavelength_HSTWFPC2_spec_flag_OBS(**kwargs):
    # No prism or grism filters
    return 'N'

def populate_obs_wavelength_HSTWFPC2_spec_size_OBS(**kwargs):
    # No prism or grism filters
    return None

def populate_obs_wavelength_HSTWFPC2_polarization_type_OBS(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    filter_name = index_row['FILTER_NAME']

    if filter_name.find('POL') == -1:
        return 'NONE'
    return 'LINEAR'

def populate_obs_mission_hubble_HSTWFPC2_filter_type(**kwargs):
    filter1, filter2 = _decode_filters(**kwargs)

    if filter2 is None:
        filter2 = ''

    if filter1.startswith('FR') or filter2.startswith('FR'):
        return 'FR' # Ramp overrides everything

    if filter1.startswith('FQ') or filter1 == 'F160BN15':
        filter1 = 'N'
    if filter2.startswith('FQ') or filter2 == 'F160BN15':
        filter2 = 'N'

    # Start from narrowest band - paired filters take the type of the smallest
    # bandpass
    if filter1.endswith('N') or filter2.endswith('N'):
        return 'N'
    if filter1.endswith('M') or filter2.endswith('M'):
        return 'M'
    if filter1.endswith('W') or filter2.endswith('W'):
        return 'W'
    if filter1.endswith('LP') or filter2.endswith('LP'):
        return 'LP'

    import_util.log_nonrepeating_error(
        f'Unknown filter combination "{filter1}+{filter2}"')
    return None


################################################################################
# THESE ARE SPECIFIC TO OBS_MISSION_HUBBLE
################################################################################

def populate_obs_mission_hubble_detector_id(**kwargs):
    metadata = kwargs['metadata']
    instrument = kwargs['instrument_name']
    index_row = metadata['index_row']
    detector_id = index_row['DETECTOR_ID']
    if detector_id == '':
        return 'UNKNOWN'
    ret = instrument[3:] + '-' + detector_id
    return (ret, ret)

def populate_obs_mission_hubble_instrument_mode_id(**kwargs):
    metadata = kwargs['metadata']
    instrument = kwargs['instrument_name']
    index_row = metadata['index_row']
    instrument_mode_id = index_row['INSTRUMENT_MODE_ID']
    ret = instrument[3:] + '-' + instrument_mode_id
    return (ret, ret)

def populate_obs_mission_hubble_filter_name(**kwargs):
    metadata = kwargs['metadata']
    instrument = kwargs['instrument_name']
    index_row = metadata['index_row']
    filter_name = index_row['FILTER_NAME']
    if filter_name.startswith('ND'): # For STIS ND_3 => ND3
        filter_name = filter_name.replace('_', '')
    else:
        filter_name = filter_name.replace('_', ' ')
    ret = instrument[3:] + '-' + filter_name
    return (ret, ret)

def populate_obs_mission_hubble_aperture_type(**kwargs):
    metadata = kwargs['metadata']
    instrument = kwargs['instrument_name']
    index_row = metadata['index_row']
    aperture = index_row['APERTURE_TYPE']
    ret = instrument[3:] + '-' + aperture
    return (ret, ret)

def populate_obs_mission_hubble_HSTx_proposed_aperture_type(**kwargs):
    return None

populate_obs_mission_hubble_HSTACS_proposed_aperture_type = populate_obs_mission_hubble_HSTx_proposed_aperture_type
populate_obs_mission_hubble_HSTNICMOS_proposed_aperture_type = populate_obs_mission_hubble_HSTx_proposed_aperture_type
populate_obs_mission_hubble_HSTWFC3_proposed_aperture_type = populate_obs_mission_hubble_HSTx_proposed_aperture_type
populate_obs_mission_hubble_HSTWFPC2_proposed_aperture_type = populate_obs_mission_hubble_HSTx_proposed_aperture_type

def populate_obs_mission_hubble_HSTSTIS_proposed_aperture_type(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    aperture = index_row['PROPOSED_APERTURE_TYPE'].upper()
    return (aperture, aperture)

def populate_obs_mission_hubble_HSTACS_targeted_detector_id(**kwargs):
    return None

def populate_obs_mission_hubble_HSTNICMOS_targeted_detector_id(**kwargs):
    return None

def populate_obs_mission_hubble_HSTSTIS_targeted_detector_id(**kwargs):
    return None

def populate_obs_mission_hubble_HSTWFC3_targeted_detector_id(**kwargs):
    return None

def populate_obs_mission_hubble_HSTWFPC2_targeted_detector_id(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    targeted_detector_id = index_row['TARGETED_DETECTOR_ID']
    if targeted_detector_id == '':
        import_util.log_nonrepeating_error(
            'Empty targeted detector ID')
    return targeted_detector_id

def populate_obs_mission_hubble_HSTx_optical_element(**kwargs):
    return None

populate_obs_mission_hubble_HSTACS_optical_element = populate_obs_mission_hubble_HSTx_optical_element
populate_obs_mission_hubble_HSTNICMOS_optical_element = populate_obs_mission_hubble_HSTx_optical_element
populate_obs_mission_hubble_HSTWFC3_optical_element = populate_obs_mission_hubble_HSTx_optical_element
populate_obs_mission_hubble_HSTWFPC2_optical_element = populate_obs_mission_hubble_HSTx_optical_element

def populate_obs_mission_hubble_HSTSTIS_optical_element(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    element = index_row['OPTICAL_ELEMENT_NAME'].upper()
    return (element, element)

def populate_obs_mission_hubble_HSTACS_pc1_flag(**kwargs):
    return None

def populate_obs_mission_hubble_HSTNICMOS_pc1_flag(**kwargs):
    return None

def populate_obs_mission_hubble_HSTSTIS_pc1_flag(**kwargs):
    return None

def populate_obs_mission_hubble_HSTWFC3_pc1_flag(**kwargs):
    return None

def populate_obs_mission_hubble_HSTWFPC2_pc1_flag(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    pc1_flag = index_row['PC1_FLAG']
    return pc1_flag

def populate_obs_mission_hubble_HSTACS_wf2_flag(**kwargs):
    return None

def populate_obs_mission_hubble_HSTNICMOS_wf2_flag(**kwargs):
    return None

def populate_obs_mission_hubble_HSTSTIS_wf2_flag(**kwargs):
    return None

def populate_obs_mission_hubble_HSTWFC3_wf2_flag(**kwargs):
    return None

def populate_obs_mission_hubble_HSTWFPC2_wf2_flag(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    wf2_flag = index_row['WF2_FLAG']
    return wf2_flag

def populate_obs_mission_hubble_HSTACS_wf3_flag(**kwargs):
    return None

def populate_obs_mission_hubble_HSTNICMOS_wf3_flag(**kwargs):
    return None

def populate_obs_mission_hubble_HSTSTIS_wf3_flag(**kwargs):
    return None

def populate_obs_mission_hubble_HSTWFC3_wf3_flag(**kwargs):
    return None

def populate_obs_mission_hubble_HSTWFPC2_wf3_flag(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    wf3_flag = index_row['WF3_FLAG']
    return wf3_flag

def populate_obs_mission_hubble_HSTACS_wf4_flag(**kwargs):
    return None

def populate_obs_mission_hubble_HSTNICMOS_wf4_flag(**kwargs):
    return None

def populate_obs_mission_hubble_HSTSTIS_wf4_flag(**kwargs):
    return None

def populate_obs_mission_hubble_HSTWFC3_wf4_flag(**kwargs):
    return None

def populate_obs_mission_hubble_HSTWFPC2_wf4_flag(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    wf4_flag = index_row['WF4_FLAG']
    return wf4_flag

def populate_obs_mission_hubble_publication_date(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    pub_date = index_row['PUBLICATION_DATE']

    if pub_date is None:
        return None

    try:
        pub_date_sec = julian.tai_from_iso(pub_date)
    except Exception as e:
        import_util.log_nonrepeating_error(
            f'Bad publication date format "{pub_date}": {e}')
        return None

    return pub_date_sec
