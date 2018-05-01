################################################################################
# populate_obs_mission_hubble.py
#
# Routines to populate fields specific to HST. It may change fields in
# obs_general or obs_mission_hubble.
################################################################################

import julian

from config_data import *
import impglobals
import import_util


################################################################################
# THESE NEED TO BE IMPLEMENTED FOR EVERY MISSION
################################################################################



def helper_galileo_target_name(**kwargs):
    metadata = kwargs['metadata']
    index_row_num = metadata['index_row_num']
    index_row = metadata['index_row']
    image_id = index_row['IMAGE_ID']

    target_id = image_id[2]
    if target_id not in _GOSSI_TARGET_MAPPING:
        import_util.announce_nonrepeating_error(
            f'Unknown GOSSI target ID "{target_id}" in IMAGE_ID "{image_id}"'+
            f' [line {index_row_num}]')
        return None

    target_name = _GOSSI_TARGET_MAPPING[target_id]

    if target_name in TARGET_NAME_MAPPING:
        target_name = TARGET_NAME_MAPPING[target_name]
    if target_name is None:
        return None
    if target_name not in TARGET_NAME_INFO:
        import_util.announce_unknown_target_name(target_name, index_row_num)
        return None

    return target_name

def helper_galileo_planet_id(**kwargs):
    # WARNING: This will need to be changed if we ever get additional volumes
    # for Galileo. Right now we set everything to Jupiter rather than basing
    # it on the target name because we only have volumes for the time Galileo
    # was in Jupiter orbit (GO_0017 to GO_0023).
    return 'JUP'
    # metadata = kwargs['metadata']
    # index_row_num = metadata['index_row_num']
    # obs_general_row = metadata['obs_general_row']
    # target_name = helper_galileo_target_name(**kwargs)
    # if target_name is None:
    #     return None
    # planet_id, _ = TARGET_NAME_INFO[target_name]
    # return planet_id

def populate_obs_general_GO_planet_id(**kwargs):
    return helper_galileo_planet_id(**kwargs)


################################################################################
# THESE NEED TO BE IMPLEMENTED FOR EVERY INSTRUMENT
################################################################################

### OBS_GENERAL TABLE ###

def populate_obs_general_COISS_rms_obs_id(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    image_number = index_row['IMAGE_NUMBER']
    instrument_id = index_row['INSTRUMENT_ID']
    planet_id = helper_cassini_planet_id(**kwargs)
    assert instrument_id[3] in ('N', 'W')
    assert len(image_number) == 10
    ret = 'X'
    if planet_id is not None:
        ret = planet_id[0]
    return ret+'_IMG_CO_ISS_'+image_number+'_'+instrument_id[3]

def populate_obs_general_HST_inst_host_id(**kwargs):
    return 'HST'

populate_obs_general_HSTACS_inst_host_id = populate_obs_general_HST_inst_host_id
populate_obs_general_HSTNICMOS_inst_host_id = populate_obs_general_HST_inst_host_id
populate_obs_general_HSTSTIS_inst_host_id = populate_obs_general_HST_inst_host_id
populate_obs_general_HSTWFC3_inst_host_id = populate_obs_general_HST_inst_host_id
populate_obs_general_HSTWFPC2_inst_host_id = populate_obs_general_HST_inst_host_id

def populate_obs_general_HST_data_type(**kwargs):
    return 'IMG'

populate_obs_general_HSTACS_data_type = populate_obs_general_HST_data_type
populate_obs_general_HSTNICMOS_data_type = populate_obs_general_HST_data_type
populate_obs_general_HSTSTIS_data_type = populate_obs_general_HST_data_type
populate_obs_general_HSTWFC3_data_type = populate_obs_general_HST_data_type
populate_obs_general_HSTWFPC2_data_type = populate_obs_general_HST_data_type

def populate_obs_general_HST_time1(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    start_time = index_row['START_TIME']
    return start_time

populate_obs_general_HSTACS_time1 = populate_obs_general_HST_time1
populate_obs_general_HSTNICMOS_time1 = populate_obs_general_HST_time1
populate_obs_general_HSTSTIS_time1 = populate_obs_general_HST_time1
populate_obs_general_HSTWFC3_time1 = populate_obs_general_HST_time1
populate_obs_general_HSTWFPC2_time1 = populate_obs_general_HST_time1

def populate_obs_general_HST_time2(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    stop_time = index_row['STOP_TIME']
    return stop_time

populate_obs_general_HSTACS_time2 = populate_obs_general_HST_time2
populate_obs_general_HSTNICMOS_time2 = populate_obs_general_HST_time2
populate_obs_general_HSTSTIS_time2 = populate_obs_general_HST_time2
populate_obs_general_HSTWFC3_time2 = populate_obs_general_HST_time2
populate_obs_general_HSTWFPC2_time2 = populate_obs_general_HST_time2

def populate_obs_general_HST_time_sec1(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    start_time = index_row['START_TIME']
    return julian.tai_from_iso(start_time)

def populate_obs_general_HST_time_sec2(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    stop_time = index_row['STOP_TIME']
    obs_general_row = metadata['obs_general_row']

    time2 = julian.tai_from_iso(stop_time)

    if time2 < obs_general_row['time_sec1']:
        start_time = index_row['START_TIME']
        index_row_num = metadata['index_row_num']
        impglobals.LOGGER.log('error',
            f'time_sec1 ({start_time}) and time_sec2 ({stop_time}) are '+
            f'in the wrong order [line {index_row_num}]')
        impglobals.IMPORT_HAS_BAD_DATA = True

    return time2

def populate_obs_general_HST_target_name(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']

    target_name = index_row['TARGET_NAME'].upper()
    if target_name in TARGET_NAME_MAPPING:
        target_name = TARGET_NAME_MAPPING[target_name]

    target_desc = index_row['TARGET_DESC'].upper()
    if target_desc in TARGET_NAME_MAPPING:
        target_desc = TARGET_NAME_MAPPING[target_desc]

    target_code = None
    obs_name = helper_cassini_obs_name(**kwargs)
    if helper_cassini_valid_obs_name(obs_name):
        obs_parts = obs_name.split('_')
        target_code = obs_parts[1][-2:]

    # Examine targets that are Saturn - are they really rings?
    if ((target_name == 'SATURN' or target_name == 'SKY') and
        target_code in ('RA','RB','RC','RD','RE','RF','RG','RI')):
        return ('S RINGS', 'S Rings')
    # Examine targets that are SKY - are they really rings?
    if target_name == 'SKY' and target_code == 'SK':
        if target_desc.find('RING') != -1:
            return ('S RINGS', 'S Rings')
        if target_desc in TARGET_NAME_INFO:
            return (target_desc.upper(), target_desc.title())

    return (target_name, target_name.title())

def populate_obs_general_COISS_observation_duration(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    exposure = index_row['EXPOSURE_DURATION']
    return exposure / 1000

def populate_obs_general_COISS_quantity(**kwargs):
    return 'REFLECT'

def populate_obs_general_COISS_note(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    return index_row['DESCRIPTION']

def populate_obs_general_COISS_primary_file_spec(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    return index_row['FILE_SPECIFICATION_NAME']

def populate_obs_general_COISS_data_set_id(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    dsi = index_row['DATA_SET_ID']
    return (dsi, dsi)

def populate_obs_general_COISS_right_asc1(**kwargs):
    metadata = kwargs['metadata']
    ring_geo_row = metadata.get('ring_geo_row', None)
    if ring_geo_row is None:
        return None
    return ring_geo_row['MINIMUM_RIGHT_ASCENSION']

def populate_obs_general_COISS_right_asc2(**kwargs):
    metadata = kwargs['metadata']
    ring_geo_row = metadata.get('ring_geo_row', None)
    if ring_geo_row is None:
        return None
    return ring_geo_row['MAXIMUM_RIGHT_ASCENSION']

def populate_obs_general_COISS_declination1(**kwargs):
    metadata = kwargs['metadata']
    ring_geo_row = metadata.get('ring_geo_row', None)
    if ring_geo_row is None:
        return None
    return ring_geo_row['MINIMUM_DECLINATION']

def populate_obs_general_COISS_declination2(**kwargs):
    metadata = kwargs['metadata']
    ring_geo_row = metadata.get('ring_geo_row', None)
    if ring_geo_row is None:
        return None
    return ring_geo_row['MAXIMUM_DECLINATION']

def populate_obs_mission_cassini_COISS_mission_phase_name(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    mp = index_row['MISSION_PHASE_NAME']
    return mp.replace('_', ' ')


### OBS_TYPE_IMAGE TABLE ###

def populate_obs_type_image_COISS_image_type_id(**kwargs):
    return 'FRAM'

def populate_obs_type_image_COISS_duration(**kwargs):
    metadata = kwargs['metadata']
    obs_general_row = metadata['obs_general_row']
    return obs_general_row['observation_duration']

def populate_obs_type_image_COISS_levels(**kwargs):
    return 4096

def _pixel_size_helper(**kwargs):
    # For COISS, this is both greater and lesser pixel size
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    exposure = index_row['INSTRUMENT_MODE_ID']
    if exposure == 'FULL':
        return 1024
    if exposure == 'SUM2':
        return 512
    if exposure == 'SUM4':
        return 256
    index_row_num = metadata['index_row_num']
    import_util.announce_nonrepeating_error(
        f'Unknown INSTRUMENT_MODE_ID "{exposure}"', index_row_num)
    return None

def populate_obs_type_image_COISS_lesser_pixel_size(**kwargs):
    return _pixel_size_helper(**kwargs)

def populate_obs_type_image_COISS_greater_pixel_size(**kwargs):
    return _pixel_size_helper(**kwargs)


### OBS_WAVELENGTH TABLE ###

# For COISS, effective wavelength is the center wavelength of the filter
# combination when convolved with the solar spectrum. Where possible, this
# is taken from the pre-computed CISSCAL values. When that isn't available,
# the filters are treated like boxcars with the FWHM of the non-convolved
# filter! If that doesn't overlap, then the average is used.

def _COISS_wavelength_helper(inst, filter1, filter2):
    key = (inst, filter1, filter2)
    if key in _COISS_FILTER_WAVELENGTHS:
        return _COISS_FILTER_WAVELENGTHS[key]

    import_util.announce_nonrepeating_warning(
        'Making up wavelength info for unknown COISS filter combination '+
        f'{key[0]}/{key[1]}/{key[2]}')

    # If we don't have the exact key combination, try to set polarization equal
    # to CLEAR for lack of anything better to do.
    nfilter1 = filter1 if filter1.find('P') == -1 else 'CL1'
    nfilter2 = filter2 if filter2.find('P') == -1 else 'CL2'
    key2 = (inst, nfilter1, nfilter2)
    if key2 in _COISS_FILTER_WAVELENGTHS:
        return _COISS_FILTER_WAVELENGTHS[key2]

    return None, None, None

# This is the effective wavelength (convolved with the solar spectrum)
def populate_obs_wavelength_COISS_effective_wavelength(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    instrument_id = index_row['INSTRUMENT_ID'][3]
    filter1, filter2 = index_row['FILTER_NAME']

    central_wl, fwhm, effective_wl = _COISS_wavelength_helper(
            instrument_id, filter1, filter2)
    if effective_wl is None:
        return None
    return effective_wl / 1000 # microns

# These are the center wavelength +/- FWHM/2
def populate_obs_wavelength_COISS_wavelength1(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    instrument_id = index_row['INSTRUMENT_ID'][3]
    filter1, filter2 = index_row['FILTER_NAME']

    central_wl, fwhm, effective_wl = _COISS_wavelength_helper(
            instrument_id, filter1, filter2)
    if central_wl is None or fwhm is None:
        return None
    return (central_wl - fwhm/2) / 1000 # microns

def populate_obs_wavelength_COISS_wavelength2(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    instrument_id = index_row['INSTRUMENT_ID'][3]
    filter1, filter2 = index_row['FILTER_NAME']

    central_wl, fwhm, effective_wl = _COISS_wavelength_helper(
            instrument_id, filter1, filter2)
    if central_wl is None or fwhm is None:
        return None
    return (central_wl + fwhm/2) / 1000 # microns

def populate_obs_wavelength_COISS_wave_res1(**kwargs):
    return None

def populate_obs_wavelength_COISS_wave_res2(**kwargs):
    return None

def populate_obs_wavelength_COISS_wave_no1(**kwargs):
    metadata = kwargs['metadata']
    wavelength_row = metadata['obs_wavelength_row']
    wl2 = wavelength_row['wavelength2']
    if wl2 is None:
        return None
    return 10000 / wl2 # cm^-1

def populate_obs_wavelength_COISS_wave_no2(**kwargs):
    metadata = kwargs['metadata']
    wavelength_row = metadata['obs_wavelength_row']
    wl1 = wavelength_row['wavelength1']
    if wl1 is None:
        return None
    return 10000 / wl1 # cm^-1

def populate_obs_wavelength_COISS_wave_no_res1(**kwargs):
    return None

def populate_obs_wavelength_COISS_wave_no_res2(**kwargs):
    return None

def populate_obs_wavelength_COISS_spec_flag(**kwargs):
    return 'No'

def populate_obs_wavelength_COISS_spec_size(**kwargs):
    return None

def populate_obs_wavelength_COISS_polarization_type(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['obs_instrument_coiss_row']
    the_filter = index_row['combined_filter']
    if the_filter.find('POL') != -1:
        return 'LINEAR'
    return 'NONE'



################################################################################
# THESE ARE SPECIFIC TO OBS_MISSION_HUBBLE
################################################################################

# populate_obs_general_HSTACS_data_type
# populate_obs_general_HSTACS_target_name
#
# populate_obs_general_HSTACS_time1
# populate_obs_general_HSTACS_time2
# populate_obs_general_HSTACS_quantity
# populate_obs_general_HSTACS_note
# populate_obs_general_HSTACS_primary_file_spec
# populate_obs_general_HSTACS_data_set_id
