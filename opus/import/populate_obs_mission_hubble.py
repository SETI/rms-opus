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

def populate_obs_general_HST_planet_id(**kwargs):
    planet = _helper_hubble_planet_id(**kwargs)
    if planet is None:
        return 'OTH'
    return planet


################################################################################
# THESE NEED TO BE IMPLEMENTED FOR EVERY INSTRUMENT
################################################################################

### OBS_GENERAL TABLE ###

def _HST_file_spec_helper(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    # Format: "data/1999010T054026_1999010T060958"
    file_spec = index_row['FILE_SPECIFICATION_NAME']
    volume_id = kwargs['volume_id']

    return volume_id + '/' + file_spec

def populate_obs_general_HSTx_opus_id(**kwargs):
    file_spec = _HST_file_spec_helper(**kwargs)
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

populate_obs_general_HSTACS_opus_id = populate_obs_general_HSTx_opus_id
populate_obs_general_HSTNICMOS_opus_id = populate_obs_general_HSTx_opus_id
populate_obs_general_HSTSTIS_opus_id = populate_obs_general_HSTx_opus_id
populate_obs_general_HSTWFC3_opus_id = populate_obs_general_HSTx_opus_id
populate_obs_general_HSTWFPC2_opus_id = populate_obs_general_HSTx_opus_id

def populate_obs_general_HSTx_ring_obs_id(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    instrument_id = index_row['INSTRUMENT_ID']
    image_date = index_row['START_TIME'][:10]
    filename = index_row['PRODUCT_ID']
    image_num = filename[1:11]
    planet = _helper_hubble_planet_id(**kwargs)
    if planet is None:
        pl_str = ''
    else:
        pl_str = planet[0]

    return (pl_str + '_IMG_HST_' + instrument_id + '_' + image_date + '_'
            + filename)

populate_obs_general_HSTACS_ring_obs_id = populate_obs_general_HSTx_ring_obs_id
populate_obs_general_HSTNICMOS_ring_obs_id = populate_obs_general_HSTx_ring_obs_id
populate_obs_general_HSTSTIS_ring_obs_id = populate_obs_general_HSTx_ring_obs_id
populate_obs_general_HSTWFC3_ring_obs_id = populate_obs_general_HSTx_ring_obs_id
populate_obs_general_HSTWFPC2_ring_obs_id = populate_obs_general_HSTx_ring_obs_id

def populate_obs_general_HSTx_inst_host_id(**kwargs):
    return 'HST'

populate_obs_general_HSTACS_inst_host_id = populate_obs_general_HSTx_inst_host_id
populate_obs_general_HSTNICMOS_inst_host_id = populate_obs_general_HSTx_inst_host_id
populate_obs_general_HSTSTIS_inst_host_id = populate_obs_general_HSTx_inst_host_id
populate_obs_general_HSTWFC3_inst_host_id = populate_obs_general_HSTx_inst_host_id
populate_obs_general_HSTWFPC2_inst_host_id = populate_obs_general_HSTx_inst_host_id

def populate_obs_general_HSTx_quantity(**kwargs):
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

populate_obs_general_HSTACS_quantity = populate_obs_general_HSTx_quantity
populate_obs_general_HSTNICMOS_quantity = populate_obs_general_HSTx_quantity
populate_obs_general_HSTSTIS_quantity = populate_obs_general_HSTx_quantity
populate_obs_general_HSTWFC3_quantity = populate_obs_general_HSTx_quantity
populate_obs_general_HSTWFPC2_quantity = populate_obs_general_HSTx_quantity

def populate_obs_general_HSTx_spatial_sampling(**kwargs):
    return '2D'

populate_obs_general_HSTACS_spatial_sampling = populate_obs_general_HSTx_spatial_sampling
populate_obs_general_HSTNICMOS_spatial_sampling = populate_obs_general_HSTx_spatial_sampling
populate_obs_general_HSTSTIS_spatial_sampling = populate_obs_general_HSTx_spatial_sampling
populate_obs_general_HSTWFC3_spatial_sampling = populate_obs_general_HSTx_spatial_sampling
populate_obs_general_HSTWFPC2_spatial_sampling = populate_obs_general_HSTx_spatial_sampling

def populate_obs_general_HSTx_wavelength_sampling(**kwargs):
    filter1, filter2 = _decode_filters(**kwargs)
    if ((filter1 is not None and (filter1.startswith('G') or filter1.startswith('PR'))) or
        (filter2 is not None and (filter2.startswith('G') or filter2.startswith('PR')))):
        return 'Y'
    return 'N'

populate_obs_general_HSTACS_wavelength_sampling = populate_obs_general_HSTx_wavelength_sampling
populate_obs_general_HSTNICMOS_wavelength_sampling = populate_obs_general_HSTx_wavelength_sampling
populate_obs_general_HSTSTIS_wavelength_sampling = populate_obs_general_HSTx_wavelength_sampling
populate_obs_general_HSTWFC3_wavelength_sampling = populate_obs_general_HSTx_wavelength_sampling
populate_obs_general_HSTWFPC2_wavelength_sampling = populate_obs_general_HSTx_wavelength_sampling

def populate_obs_general_HSTx_time_sampling(**kwargs):
    return 'N'

populate_obs_general_HSTACS_time_sampling = populate_obs_general_HSTx_time_sampling
populate_obs_general_HSTNICMOS_time_sampling = populate_obs_general_HSTx_time_sampling
populate_obs_general_HSTSTIS_time_sampling = populate_obs_general_HSTx_time_sampling
populate_obs_general_HSTWFC3_time_sampling = populate_obs_general_HSTx_time_sampling
populate_obs_general_HSTWFPC2_time_sampling = populate_obs_general_HSTx_time_sampling

def populate_obs_general_HSTx_time1(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    start_time = import_util.safe_column(index_row, 'START_TIME')
    return start_time

populate_obs_general_HSTACS_time1 = populate_obs_general_HSTx_time1
populate_obs_general_HSTNICMOS_time1 = populate_obs_general_HSTx_time1
populate_obs_general_HSTSTIS_time1 = populate_obs_general_HSTx_time1
populate_obs_general_HSTWFC3_time1 = populate_obs_general_HSTx_time1
populate_obs_general_HSTWFPC2_time1 = populate_obs_general_HSTx_time1

def populate_obs_general_HSTx_time2(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    stop_time = import_util.safe_column(index_row, 'STOP_TIME')
    return stop_time

populate_obs_general_HSTACS_time2 = populate_obs_general_HSTx_time2
populate_obs_general_HSTNICMOS_time2 = populate_obs_general_HSTx_time2
populate_obs_general_HSTSTIS_time2 = populate_obs_general_HSTx_time2
populate_obs_general_HSTWFC3_time2 = populate_obs_general_HSTx_time2
populate_obs_general_HSTWFPC2_time2 = populate_obs_general_HSTx_time2

def populate_obs_general_HSTx_target_name(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']

    target_name = index_row['TARGET_NAME'].upper()
    if target_name in TARGET_NAME_MAPPING:
        target_name = TARGET_NAME_MAPPING[target_name]

    return (target_name, target_name.title())

populate_obs_general_HSTACS_target_name = populate_obs_general_HSTx_target_name
populate_obs_general_HSTNICMOS_target_name = populate_obs_general_HSTx_target_name
populate_obs_general_HSTSTIS_target_name = populate_obs_general_HSTx_target_name
populate_obs_general_HSTWFC3_target_name = populate_obs_general_HSTx_target_name
populate_obs_general_HSTWFPC2_target_name = populate_obs_general_HSTx_target_name

def populate_obs_general_HSTx_observation_duration(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    exposure = import_util.safe_column(index_row, 'EXPOSURE_DURATION')

    if exposure is None:
        return None

    return exposure / 1000

populate_obs_general_HSTACS_observation_duration = populate_obs_general_HSTx_observation_duration
populate_obs_general_HSTNICMOS_observation_duration = populate_obs_general_HSTx_observation_duration
populate_obs_general_HSTSTIS_observation_duration = populate_obs_general_HSTx_observation_duration
populate_obs_general_HSTWFC3_observation_duration = populate_obs_general_HSTx_observation_duration
populate_obs_general_HSTWFPC2_observation_duration = populate_obs_general_HSTx_observation_duration

def populate_obs_general_HSTx_note(**kwargs):
    return None

populate_obs_general_HSTACS_note = populate_obs_general_HSTx_note
populate_obs_general_HSTNICMOS_note = populate_obs_general_HSTx_note
populate_obs_general_HSTSTIS_note = populate_obs_general_HSTx_note
populate_obs_general_HSTWFC3_note = populate_obs_general_HSTx_note
populate_obs_general_HSTWFPC2_note = populate_obs_general_HSTx_note

def populate_obs_general_HSTx_primary_file_spec(**kwargs):
    file_spec = _HST_file_spec_helper(**kwargs)
    return file_spec

populate_obs_general_HSTACS_primary_file_spec = populate_obs_general_HSTx_primary_file_spec
populate_obs_general_HSTNICMOS_primary_file_spec = populate_obs_general_HSTx_primary_file_spec
populate_obs_general_HSTSTIS_primary_file_spec = populate_obs_general_HSTx_primary_file_spec
populate_obs_general_HSTWFC3_primary_file_spec = populate_obs_general_HSTx_primary_file_spec
populate_obs_general_HSTWFPC2_primary_file_spec = populate_obs_general_HSTx_primary_file_spec

def populate_obs_general_HSTx_product_creation_time(**kwargs):
    metadata = kwargs['metadata']
    index_label = metadata['index_label']
    pct = index_label['PRODUCT_CREATION_TIME']
    return pct

populate_obs_general_HSTACS_product_creation_time = populate_obs_general_HSTx_product_creation_time
populate_obs_general_HSTNICMOS_product_creation_time = populate_obs_general_HSTx_product_creation_time
populate_obs_general_HSTSTIS_product_creation_time = populate_obs_general_HSTx_product_creation_time
populate_obs_general_HSTWFC3_product_creation_time = populate_obs_general_HSTx_product_creation_time
populate_obs_general_HSTWFPC2_product_creation_time = populate_obs_general_HSTx_product_creation_time

def populate_obs_general_HSTx_data_set_id(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    dsi = index_row['DATA_SET_ID']
    return (dsi, dsi)

populate_obs_general_HSTACS_data_set_id = populate_obs_general_HSTx_data_set_id
populate_obs_general_HSTNICMOS_data_set_id = populate_obs_general_HSTx_data_set_id
populate_obs_general_HSTSTIS_data_set_id = populate_obs_general_HSTx_data_set_id
populate_obs_general_HSTWFC3_data_set_id = populate_obs_general_HSTx_data_set_id
populate_obs_general_HSTWFPC2_data_set_id = populate_obs_general_HSTx_data_set_id

def populate_obs_general_HSTx_product_id(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    product_id = index_row['PRODUCT_ID']

    return product_id

populate_obs_general_HSTACS_product_id = populate_obs_general_HSTx_product_id
populate_obs_general_HSTNICMOS_product_id = populate_obs_general_HSTx_product_id
populate_obs_general_HSTSTIS_product_id = populate_obs_general_HSTx_product_id
populate_obs_general_HSTWFC3_product_id = populate_obs_general_HSTx_product_id
populate_obs_general_HSTWFPC2_product_id = populate_obs_general_HSTx_product_id

def populate_obs_general_HSTx_right_asc1(**kwargs):
    return None

populate_obs_general_HSTACS_right_asc1 = populate_obs_general_HSTx_right_asc1
populate_obs_general_HSTNICMOS_right_asc1 = populate_obs_general_HSTx_right_asc1
populate_obs_general_HSTSTIS_right_asc1 = populate_obs_general_HSTx_right_asc1
populate_obs_general_HSTWFC3_right_asc1 = populate_obs_general_HSTx_right_asc1
populate_obs_general_HSTWFPC2_right_asc1 = populate_obs_general_HSTx_right_asc1

def populate_obs_general_HSTx_right_asc2(**kwargs):
    return None

populate_obs_general_HSTACS_right_asc2 = populate_obs_general_HSTx_right_asc2
populate_obs_general_HSTNICMOS_right_asc2 = populate_obs_general_HSTx_right_asc2
populate_obs_general_HSTSTIS_right_asc2 = populate_obs_general_HSTx_right_asc2
populate_obs_general_HSTWFC3_right_asc2 = populate_obs_general_HSTx_right_asc2
populate_obs_general_HSTWFPC2_right_asc2 = populate_obs_general_HSTx_right_asc2

def populate_obs_general_HSTx_declination1(**kwargs):
    return None

populate_obs_general_HSTACS_declination1 = populate_obs_general_HSTx_declination1
populate_obs_general_HSTNICMOS_declination1 = populate_obs_general_HSTx_declination1
populate_obs_general_HSTSTIS_declination1 = populate_obs_general_HSTx_declination1
populate_obs_general_HSTWFC3_declination1 = populate_obs_general_HSTx_declination1
populate_obs_general_HSTWFPC2_declination1 = populate_obs_general_HSTx_declination1

def populate_obs_general_HSTx_declination2(**kwargs):
    return None

populate_obs_general_HSTACS_declination2 = populate_obs_general_HSTx_declination2
populate_obs_general_HSTNICMOS_declination2 = populate_obs_general_HSTx_declination2
populate_obs_general_HSTSTIS_declination2 = populate_obs_general_HSTx_declination2
populate_obs_general_HSTWFC3_declination2 = populate_obs_general_HSTx_declination2
populate_obs_general_HSTWFPC2_declination2 = populate_obs_general_HSTx_declination2


### OBS_TYPE_IMAGE TABLE ###

# XXX
def populate_obs_type_image_HSTx_image_type_id(**kwargs):
    return 'FRAM'

populate_obs_type_image_HSTACS_image_type_id = populate_obs_type_image_HSTx_image_type_id
populate_obs_type_image_HSTNICMOS_image_type_id = populate_obs_type_image_HSTx_image_type_id
populate_obs_type_image_HSTSTIS_image_type_id = populate_obs_type_image_HSTx_image_type_id
populate_obs_type_image_HSTWFC3_image_type_id = populate_obs_type_image_HSTx_image_type_id
populate_obs_type_image_HSTWFPC2_image_type_id = populate_obs_type_image_HSTx_image_type_id

def populate_obs_type_image_HSTx_duration(**kwargs):
    metadata = kwargs['metadata']
    obs_general_row = metadata['obs_general_row']
    return obs_general_row['observation_duration']

populate_obs_type_image_HSTACS_duration = populate_obs_type_image_HSTx_duration
populate_obs_type_image_HSTNICMOS_duration = populate_obs_type_image_HSTx_duration
populate_obs_type_image_HSTSTIS_duration = populate_obs_type_image_HSTx_duration
populate_obs_type_image_HSTWFC3_duration = populate_obs_type_image_HSTx_duration
populate_obs_type_image_HSTWFPC2_duration = populate_obs_type_image_HSTx_duration

def populate_obs_type_image_HSTACS_levels(**kwargs):
    return 65536 # ACS Inst Handbook 25, Sec 3.4.3

def populate_obs_type_image_HSTNICMOS_levels(**kwargs):
    return 65536 # NICMOS Inst Handbook, Sec 7.2.1

def populate_obs_type_image_HSTSTIS_levels(**kwargs):
    return 65536 # STIS Inst Handbook, Sec 7.5.1

def populate_obs_type_image_HSTWFC3_levels(**kwargs):
    return 65536 # WFC3 Inst Handbook, Sec 2.2.3

def populate_obs_type_image_HSTWFPC2_levels(**kwargs):
    return 4096 # WFPC2 Inst Handbook, Sec 2.8

def populate_obs_type_image_HSTx_lesser_pixel_size(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    lines = import_util.safe_column(index_row, 'LINES')
    samples = import_util.safe_column(index_row, 'LINE_SAMPLES')
    if lines is None or samples is None:
        return None
    return min(lines, samples)

populate_obs_type_image_HSTACS_lesser_pixel_size = populate_obs_type_image_HSTx_lesser_pixel_size
populate_obs_type_image_HSTNICMOS_lesser_pixel_size = populate_obs_type_image_HSTx_lesser_pixel_size
populate_obs_type_image_HSTSTIS_lesser_pixel_size = populate_obs_type_image_HSTx_lesser_pixel_size
populate_obs_type_image_HSTWFC3_lesser_pixel_size = populate_obs_type_image_HSTx_lesser_pixel_size
populate_obs_type_image_HSTWFPC2_lesser_pixel_size = populate_obs_type_image_HSTx_lesser_pixel_size

def populate_obs_type_image_HSTx_greater_pixel_size(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    lines = import_util.safe_column(index_row, 'LINES')
    samples = import_util.safe_column(index_row, 'LINE_SAMPLES')
    if lines is None or samples is None:
        return None
    return max(lines, samples)

populate_obs_type_image_HSTACS_greater_pixel_size = populate_obs_type_image_HSTx_greater_pixel_size
populate_obs_type_image_HSTNICMOS_greater_pixel_size = populate_obs_type_image_HSTx_greater_pixel_size
populate_obs_type_image_HSTSTIS_greater_pixel_size = populate_obs_type_image_HSTx_greater_pixel_size
populate_obs_type_image_HSTWFC3_greater_pixel_size = populate_obs_type_image_HSTx_greater_pixel_size
populate_obs_type_image_HSTWFPC2_greater_pixel_size = populate_obs_type_image_HSTx_greater_pixel_size


### OBS_WAVELENGTH TABLE ###

def populate_obs_wavelength_HSTx_wavelength1(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    wl1 = import_util.safe_column(index_row, 'MINIMUM_WAVELENGTH')

    return wl1

populate_obs_wavelength_HSTACS_wavelength1 = populate_obs_wavelength_HSTx_wavelength1
populate_obs_wavelength_HSTNICMOS_wavelength1 = populate_obs_wavelength_HSTx_wavelength1
populate_obs_wavelength_HSTSTIS_wavelength1 = populate_obs_wavelength_HSTx_wavelength1
populate_obs_wavelength_HSTWFC3_wavelength1 = populate_obs_wavelength_HSTx_wavelength1
populate_obs_wavelength_HSTWFPC2_wavelength1 = populate_obs_wavelength_HSTx_wavelength1

def populate_obs_wavelength_HSTx_wavelength2(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    wl2 = import_util.safe_column(index_row, 'MAXIMUM_WAVELENGTH')

    return wl2

populate_obs_wavelength_HSTACS_wavelength2 = populate_obs_wavelength_HSTx_wavelength2
populate_obs_wavelength_HSTNICMOS_wavelength2 = populate_obs_wavelength_HSTx_wavelength2
populate_obs_wavelength_HSTSTIS_wavelength2 = populate_obs_wavelength_HSTx_wavelength2
populate_obs_wavelength_HSTWFC3_wavelength2 = populate_obs_wavelength_HSTx_wavelength2
populate_obs_wavelength_HSTWFPC2_wavelength2 = populate_obs_wavelength_HSTx_wavelength2

def populate_obs_wavelength_HSTx_wave_res1(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    wr = import_util.safe_column(index_row, 'WAVELENGTH_RESOLUTION')

    return wr

populate_obs_wavelength_HSTACS_wave_res1 = populate_obs_wavelength_HSTx_wave_res1
populate_obs_wavelength_HSTNICMOS_wave_res1 = populate_obs_wavelength_HSTx_wave_res1
populate_obs_wavelength_HSTWFC3_wave_res1 = populate_obs_wavelength_HSTx_wave_res1
populate_obs_wavelength_HSTWFPC2_wave_res1 = populate_obs_wavelength_HSTx_wave_res1

def populate_obs_wavelength_HSTx_wave_res2(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    wr = import_util.safe_column(index_row, 'WAVELENGTH_RESOLUTION')

    return wr

populate_obs_wavelength_HSTACS_wave_res2 = populate_obs_wavelength_HSTx_wave_res2
populate_obs_wavelength_HSTNICMOS_wave_res2 = populate_obs_wavelength_HSTx_wave_res2
populate_obs_wavelength_HSTWFC3_wave_res2 = populate_obs_wavelength_HSTx_wave_res2
populate_obs_wavelength_HSTWFPC2_wave_res2 = populate_obs_wavelength_HSTx_wave_res2

def populate_obs_wavelength_HSTSTIS_wave_res1(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    wr1 = import_util.safe_column(index_row, 'MINIMUM_WAVELENGTH_RESOLUTION')

    return wr1

def populate_obs_wavelength_HSTSTIS_wave_res2(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    wr2 = import_util.safe_column(index_row, 'MAXIMUM_WAVELENGTH_RESOLUTION')

    return wr2

def populate_obs_wavelength_HSTx_wave_no1(**kwargs):
    metadata = kwargs['metadata']
    wavelength_row = metadata['obs_wavelength_row']
    wl2 = wavelength_row['wavelength2']
    if wl2 is None:
        return None
    return 10000 / wl2 # cm^-1

populate_obs_wavelength_HSTACS_wave_no1 = populate_obs_wavelength_HSTx_wave_no1
populate_obs_wavelength_HSTNICMOS_wave_no1 = populate_obs_wavelength_HSTx_wave_no1
populate_obs_wavelength_HSTSTIS_wave_no1 = populate_obs_wavelength_HSTx_wave_no1
populate_obs_wavelength_HSTWFC3_wave_no1 = populate_obs_wavelength_HSTx_wave_no1
populate_obs_wavelength_HSTWFPC2_wave_no1 = populate_obs_wavelength_HSTx_wave_no1

def populate_obs_wavelength_HSTx_wave_no2(**kwargs):
    metadata = kwargs['metadata']
    wavelength_row = metadata['obs_wavelength_row']
    wl1 = wavelength_row['wavelength1']
    if wl1 is None:
        return None
    return 10000 / wl1 # cm^-1

populate_obs_wavelength_HSTACS_wave_no2 = populate_obs_wavelength_HSTx_wave_no2
populate_obs_wavelength_HSTNICMOS_wave_no2 = populate_obs_wavelength_HSTx_wave_no2
populate_obs_wavelength_HSTSTIS_wave_no2 = populate_obs_wavelength_HSTx_wave_no2
populate_obs_wavelength_HSTWFC3_wave_no2 = populate_obs_wavelength_HSTx_wave_no2
populate_obs_wavelength_HSTWFPC2_wave_no2 = populate_obs_wavelength_HSTx_wave_no2

def populate_obs_wavelength_HSTx_wave_no_res1(**kwargs):
    metadata = kwargs['metadata']
    wl_row = metadata['obs_wavelength_row']
    wno1 = wl_row['wave_no1']
    wno2 = wl_row['wave_no2']
    if wno1 is None or wno2 is None:
        return None
    return wno2 - wno1

populate_obs_wavelength_HSTACS_wave_no_res1 = populate_obs_wavelength_HSTx_wave_no_res1
populate_obs_wavelength_HSTNICMOS_wave_no_res1 = populate_obs_wavelength_HSTx_wave_no_res1
populate_obs_wavelength_HSTWFC3_wave_no_res1 = populate_obs_wavelength_HSTx_wave_no_res1
populate_obs_wavelength_HSTWFPC2_wave_no_res1 = populate_obs_wavelength_HSTx_wave_no_res1

def populate_obs_wavelength_HSTx_wave_no_res2(**kwargs):
    metadata = kwargs['metadata']
    wl_row = metadata['obs_wavelength_row']
    wno1 = wl_row['wave_no1']
    wno2 = wl_row['wave_no2']
    if wno1 is None or wno2 is None:
        return None
    return wno2 - wno1

populate_obs_wavelength_HSTACS_wave_no_res2 = populate_obs_wavelength_HSTx_wave_no_res2
populate_obs_wavelength_HSTNICMOS_wave_no_res2 = populate_obs_wavelength_HSTx_wave_no_res2
populate_obs_wavelength_HSTWFC3_wave_no_res2 = populate_obs_wavelength_HSTx_wave_no_res2
populate_obs_wavelength_HSTWFPC2_wave_no_res2 = populate_obs_wavelength_HSTx_wave_no_res2

def populate_obs_wavelength_HSTSTIS_wave_no_res1(**kwargs):
    metadata = kwargs['metadata']
    wl_row = metadata['obs_wavelength_row']
    wave_res2 = wl_row['wave_res2']
    wl2 = wl_row['wavelength2']

    if wave_res2 is None or wl2 is None:
        return None

    return wave_res2 * 10000. / (wl2*wl2)

def populate_obs_wavelength_HSTSTIS_wave_no_res2(**kwargs):
    metadata = kwargs['metadata']
    wl_row = metadata['obs_wavelength_row']
    wave_res1 = wl_row['wave_res1']
    wl1 = wl_row['wavelength1']

    if wave_res1 is None or wl1 is None:
        return None

    return wave_res1 * 10000. / (wl1*wl1)


### ACS ###

def populate_obs_wavelength_HSTACS_spec_flag(**kwargs):
    filter1, filter2 = _decode_filters(**kwargs)
    if filter1.startswith('G') or filter1.startswith('PR'):
        return 'Y'
    return 'N'

def populate_obs_wavelength_HSTACS_spec_size(**kwargs):
    filter1, filter2 = _decode_filters(**kwargs)
    if not filter1.startswith('G') and not filter1.startswith('PR'):
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
        wr = 8000. / 120 * .0001 # Average 100 and 140
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

    return bw // wr

def populate_obs_wavelength_HSTACS_polarization_type(**kwargs):
    filter1, filter2 = _decode_filters(**kwargs)
    if filter2 is not None and filter2.startswith('POL'):
        return 'LINEAR'
    return 'NONE'

def populate_obs_mission_hubble_HSTACS_filter_type(**kwargs):
    filter1, filter2 = _decode_filters(**kwargs)
    # We only care about filter1 since the second is always a polarizer
    assert filter2 is None or filter2.startswith('POL')

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

def populate_obs_wavelength_HSTNICMOS_spec_flag(**kwargs):
    filter1, filter2 = _decode_filters(**kwargs)
    if filter1.startswith('G'):
        return 'Y'
    return 'N'

def populate_obs_wavelength_HSTNICMOS_spec_size(**kwargs):
    filter1, filter2 = _decode_filters(**kwargs)
    assert filter2 is None
    if not filter1.startswith('G'):
        return None

    # We can't use WAVELENGTH_RESOLUTION because it's too aggressive.
    # Instead we use the Resolving Power (lambda / d-lambda) from NICMOS Inst
    # Handbook Tables 5.3 and 5.5

    if filter1 == 'G096':
        wr = 0.00536
        bw = 1.2-0.8
    elif filter1 == 'G141':
        wr = 0.007992
        bw = 1.9-1.1
    elif filter1 == 'G206':
        wr = 0.01152
        bw = 2.5-1.4
    else:
        assert False, filter1

    return bw // wr

def populate_obs_wavelength_HSTNICMOS_polarization_type(**kwargs):
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

def populate_obs_wavelength_HSTSTIS_spec_flag(**kwargs):
    return 'N'

def populate_obs_wavelength_HSTSTIS_spec_size(**kwargs):
    return None

def populate_obs_wavelength_HSTSTIS_polarization_type(**kwargs):
    return 'NONE'

def populate_obs_mission_hubble_HSTSTIS_filter_type(**kwargs):
    filter1, filter2 = _decode_filters(**kwargs)
    assert filter2 is None

    if filter1 in ['CLEAR', 'CRYSTAL QUARTZ', 'LONG_PASS', 'STRONTIUM_FLUORIDE']:
        return 'LP'
    if filter1 == 'LYMAN_ALPHA':
        return 'N'

    import_util.log_nonrepeating_error(f'Unknown filter "{filter1}"')
    return None


### WFC3 ###

def populate_obs_wavelength_HSTWFC3_spec_flag(**kwargs):
    filter1, filter2 = _decode_filters(**kwargs)
    assert filter2 is None
    if filter1.startswith('G'):
        return 'Y'
    return 'N'

def populate_obs_wavelength_HSTWFC3_spec_size(**kwargs):
    filter1, filter2 = _decode_filters(**kwargs)
    assert filter2 is None
    if not filter1.startswith('G'):
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

    return bw // wr

def populate_obs_wavelength_HSTWFC3_polarization_type(**kwargs):
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

def populate_obs_wavelength_HSTWFPC2_spec_flag(**kwargs):
    # No prism or grism filters
    return 'N'

def populate_obs_wavelength_HSTWFPC2_spec_size(**kwargs):
    # No prism or grism filters
    return None

def populate_obs_wavelength_HSTWFPC2_polarization_type(**kwargs):
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
        return None
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
        return 'NONE'
    return targeted_detector_id

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

def populate_obs_mission_hubble_publication_date_sec(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    pub_date = index_row['PUBLICATION_DATE']

    if pub_date is None:
        return None

    return julian.tai_from_iso(pub_date)
