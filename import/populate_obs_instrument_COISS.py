################################################################################
# populate_obs_instrument_COISS.py
#
# Routines to populate fields specific to COISS. It may change fields in
# obs_general, obs_mission_cassini, or obs_instrument_COISS.
################################################################################

# Ordering:
#   time_sec1/2 must come before planet_id
#   planet_id must come before rms_obs_id

from config_data import *
import impglobals

from populate_obs_mission_cassini import *


# This data is from the ISS Data User's Guide Table A.2
# When missing from there it is from the CISSCAL files na_effwl.tab
# and wa_effwl.tab
# (Camera, Filter1, Filter2): (Central wavelength, FWHM, Effective wavelength)
# Values are in nm and must be converted to microns!
_COISS_FILTER_WAVELENGTHS = {
    ('N', 'CL1', 'CL2'): (610.675, 340.056, 651.057),
    ('N', 'CL1', 'GRN'): (568.134, 113.019, 569.236),
    ('N', 'CL1', 'UV3'): (338.284, 68.0616, 343.136),
    ('N', 'CL1', 'BL2'): (439.923, 29.4692, 440.980),
    ('N', 'CL1', 'MT2'): (727.421, 4.11240, 727.415),
    ('N', 'CL1', 'CB2'): (750.505, 10.0129, 750.495),
    ('N', 'CL1', 'MT3'): (889.194, 10.4720, 889.196),
    ('N', 'CL1', 'CB3'): (937.964, 9.54761, 937.928),
    ('N', 'CL1', 'MT1'): (618.945, 3.68940, 618.949),
    ('N', 'CL1', 'CB1'): (619.381, 9.99526, 619.292),
    ('N', 'CL1', 'CB1A'): (602.908, 9.99526, 602.917),
    ('N', 'CL1', 'CB1B'): (634.531, 11.9658, 634.526),
    ('N', 'CL1', 'IR3'): (929.763, 66.9995, 928.304),
    ('N', 'CL1', 'IR1'): (751.894, 152.929, 750.048),
    ('N', 'RED', 'CL2'): (650.086, 149.998, 648.879),
    ('N', 'RED', 'GRN'): (601.032, 51.9801, 600.959),
    ('N', 'RED', 'MT2'): (726.633, 2.33906, 726.624),
    ('N', 'RED', 'CB2'): (744.255, 4.22393, 743.912),
    ('N', 'RED', 'MT1'): (618.911, 3.69858, 618.922),
    ('N', 'RED', 'CB1'): (619.568, 9.07488, 619.481),
    ('N', 'RED', 'IR3'): (695.435, 2.04887, 695.040),
    ('N', 'RED', 'IR1'): (701.900, 44.9603, 701.692),
    ('N', 'BL1', 'CL2'): (450.851, 102.996, 455.471),
    ('N', 'BL1', 'GRN'): (497.445, 5.00811, 497.435),
    ('N', 'BL1', 'UV3'): (386.571, 14.0295, 389.220),
    ('N', 'BL1', 'BL2'): (440.035, 29.6733, 441.077),
    ('N', 'UV2', 'CL2'): (297.880, 59.9535, 306.477),
    ('N', 'UV2', 'UV3'): (315.623, 28.9282, 317.609),
    ('N', 'UV1', 'CL2'): (258.098, 37.9542, 266.321),
    ('N', 'UV1', 'UV3'): (350.697, 9.07263, 353.878),
    ('N', 'IRPO', 'MT2'): (727.434, 4.11241, 727.424),
    ('N', 'IRPO', 'CB2'): (750.512, 10.0158, 750.501),
    ('N', 'IRPO', 'MT3'): (889.211, 10.4738, 889.208),
    ('N', 'IRPO', 'CB3'): (938.001, 9.54946, 937.961),
    ('N', 'IRPO', 'MT1'): (618.970, 3.69682, 618.967),
    ('N', 'IRPO', 'IR3'): (930.047, 67.9802, 928.583),
    ('N', 'IRPO', 'IR1'): (752.822, 153.994, 750.967),
    ('N', 'P120', 'GRN'): (568.532, 112.946, 569.630),
    ('N', 'P120', 'UV3'): (341.101, 66.0391, 345.492),
    ('N', 'P120', 'BL2'): (440.022, 29.4620, 441.079),
    ('N', 'P120', 'MT2'): (727.430, 4.11216, 727.421),
    ('N', 'P120', 'CB2'): (750.535, 10.0307, 750.524),
    ('N', 'P120', 'MT1'): (618.908, 3.69299, 618.920),
    ('N', 'P120', 'CB1'): (619.961, 9.99561, 619.872),
    ('N', 'P60', 'GRN'): (568.532, 112.946, 569.630),
    ('N', 'P60', 'UV3'): (341.101, 66.0391, 345.492),
    ('N', 'P60', 'BL2'): (440.022, 29.4620, 441.079),
    ('N', 'P60', 'MT2'): (727.430, 4.11216, 727.421),
    ('N', 'P60', 'CB2'): (750.535, 10.0307, 750.524),
    ('N', 'P60', 'MT1'): (618.908, 3.69299, 618.920),
    ('N', 'P60', 'CB1'): (619.961, 9.99561, 619.872),
    ('N', 'P0', 'GRN'): (568.532, 112.946, 569.630),
    ('N', 'P0', 'UV3'): (341.101, 66.0391, 345.492),
    ('N', 'P0', 'BL2'): (440.022, 29.4620, 441.079),
    ('N', 'P0', 'MT2'): (727.430, 4.11216, 727.421),
    ('N', 'P0', 'CB2'): (750.535, 10.0307, 750.524),
    ('N', 'P0', 'MT1'): (618.908, 3.69299, 618.920),
    ('N', 'P0', 'CB1'): (619.961, 9.99561, 619.872),
    ('N', 'HAL', 'CL2'): (655.663, 9.26470, 655.621),
    ('N', 'HAL', 'GRN'): (648.028, 5.58862, 647.808),
    ('N', 'HAL', 'CB1'): (650.567, 2.73589, 650.466),
    ('N', 'HAL', 'IR1'): (663.476, 5.25757, 663.431),
    ('N', 'IR4', 'CL2'): (1002.40, 35.9966, 1001.91),
    ('N', 'IR4', 'IR3'): (996.723, 36.0700, 996.460),
    ('N', 'IR2', 'CL2'): (861.962, 97.0431, 861.066),
    ('N', 'IR2', 'MT3'): (889.176, 10.4655, 889.176),
    ('N', 'IR2', 'CB3'): (933.657, 3.71709, 933.593),
    ('N', 'IR2', 'IR3'): (901.843, 44.0356, 901.630),
    ('N', 'IR2', 'IR1'): (827.438, 28.0430, 827.331),
    ('W', 'CL1', 'CL2'): (634.928, 285.999, 633.817),
    ('W', 'CL1', 'RED'): (648.422, 150.025, 647.239),
    ('W', 'CL1', 'GRN'): (567.126, 123.999, 568.214),
    ('W', 'CL1', 'BL1'): (460.418, 62.2554, 462.865),
    ('W', 'CL1', 'VIO'): (419.684, 18.1825, 419.822),
    ('W', 'CL1', 'HAL'): (656.401, 9.96150, 656.386),
    ('W', 'CL1', 'IR1'): (741.456, 99.9735, 739.826),
    ('W', 'IR3', 'CL2'): (917.841, 45.3074, 916.727),
    ('W', 'IR3', 'RED'): (690.604, 3.04414, 689.959),
    ('W', 'IR3', 'IRP90'): (917.883, 45.3223, 916.770),
    ('W', 'IR3', 'IRP0'): (917.883, 45.3223, 916.770),
    ('W', 'IR3', 'IR1'): (790.007, 3.02556, 783.722),
    ('W', 'IR4', 'CL2'): (1002.36, 25.5330, 1001.88),
    ('W', 'IR4', 'IRP90'): (1002.44, 25.5299, 1001.98),
    ('W', 'IR4', 'IRP0'): (1002.44, 25.5299, 1001.98),
    ('W', 'IR5', 'CL2'): (1034.49, 19.4577, 1033.87),
    ('W', 'IR5', 'IRP90'): (1035.20, 19.4591, 1034.85),
    ('W', 'IR5', 'IRP0'): (1035.20, 19.4591, 1034.85),
    ('W', 'CB3', 'CL2'): (938.532, 9.95298, 938.445),
    ('W', 'CB3', 'IRP90'): (938.668, 9.95308, 938.611),
    ('W', 'CB3', 'IRP0'): (938.668, 9.95308, 938.611),
    ('W', 'MT3', 'CL2'): (890.340, 10.0116, 890.332),
    ('W', 'MT3', 'IRP90'): (890.368, 10.0118, 890.364),
    ('W', 'MT3', 'IRP0'): (890.368, 10.0118, 890.364),
    ('W', 'CB2', 'CL2'): (752.364, 10.0044, 752.354),
    ('W', 'CB2', 'RED'): (747.602, 4.07656, 747.317),
    ('W', 'CB2', 'IRP90'): (752.373, 10.0049, 752.363),
    ('W', 'CB2', 'IRP0'): (752.373, 10.0049, 752.363),
    ('W', 'CB2', 'IR1'): (752.324, 10.0026, 752.314),
    ('W', 'MT2', 'CL2'): (728.452, 4.00903, 728.418),
    ('W', 'MT2', 'RED'): (727.517, 2.05059, 727.507),
    ('W', 'MT2', 'IRP90'): (728.470, 4.00906, 728.435),
    ('W', 'MT2', 'IRP0'): (728.470, 4.00906, 728.435),
    ('W', 'MT2', 'IR1'): (728.293, 4.00906, 728.284),
    ('W', 'IR2', 'CL2'): (853.258, 54.8544, 852.448),
    ('W', 'IR2', 'IRP90'): (853.320, 54.8765, 852.510),
    ('W', 'IR2', 'IRP0'): (853.320, 54.8765, 852.510),
    ('W', 'IR2', 'IR1'): (826.348, 26.0795, 826.255),
}
# The following filter combinations are found in the data but aren't in the
# above table:
# N/HAL/UV3
# N/IR2/UV3
# N/IR4/UV3
# N/IRP0/CB1
# N/IRP0/CB2
# N/IRP0/CB3
# N/IRP0/CL2
# N/IRP0/GRN
# N/IRP0/IR1
# N/IRP0/IR3
# N/IRP0/MT1
# N/IRP0/MT2
# N/IRP0/MT3
# N/P0/CL2
# N/P0/IR1
# N/P0/IR3
# N/P120/CL2
# N/P120/IR1
# N/P60/CL2
# N/P60/IR1
# N/RED/UV3
# N/UV1/BL2
# N/UV1/CB1
# N/UV1/CB2
# N/UV1/GRN
# N/UV1/IR1
# N/UV1/IR3
# N/UV2/BL2
# N/UV2/CB1
# N/UV2/CB2
# N/UV2/GRN
# N/UV2/IR1
# N/UV2/IR3
# N/UV2/MT1
# W/CB3/HAL
# W/CB3/VIO
# W/CL1/IRP0
# W/CL1/IRP90
# W/IR3/BL1
# W/MT3/BL1

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
    if planet_id is not None:
        ret = planet_id[0]
    else:
        ret = ''
    return ret+'_IMG_CO_ISS_'+image_number+'_'+instrument_id[3]

def populate_obs_general_COISS_inst_host_id(**kwargs):
    return 'CO'

def populate_obs_general_COISS_data_type(**kwargs):
    return ('IMG', 'Image')

def populate_obs_general_COISS_time1(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    start_time = index_row['START_TIME']
    return start_time

def populate_obs_general_COISS_time2(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    stop_time = index_row['STOP_TIME']
    return stop_time

def populate_obs_general_COISS_time_sec1(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    start_time = index_row['START_TIME']
    if start_time == 'UNK':
        index_row_num = metadata['index_row_num']
        import_util.announce_nonrepeating_error(
            'Found "UNK" in START_TIME field', index_row_num)
        return 0.
    return julian.tai_from_iso(start_time)

def populate_obs_general_COISS_time_sec2(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    stop_time = index_row['STOP_TIME']
    obs_general_row = metadata['obs_general_row']

    if stop_time == 'UNK':
        index_row_num = metadata['index_row_num']
        import_util.announce_nonrepeating_error(
            'Found "UNK" in STOP_TIME field', index_row_num)
        return 0.

    time2 = julian.tai_from_iso(stop_time)

    if time2 < obs_general_row['time_sec1']:
        start_time = index_row['START_TIME']
        if start_time != 'UNK':
            index_row_num = metadata['index_row_num']
            impglobals.LOGGER.log('error',
                f'time_sec1 ({start_time}) and time_sec2 ({stop_time}) are '+
                f'in the wrong order [line {index_row_num}]')
        impglobals.IMPORT_HAS_BAD_DATA = True

    return time2

def populate_obs_general_COISS_target_name(**kwargs):
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
    return mp


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

def _COISS_wavelength_helper(inst, filter1, filter2):
    key = (inst, filter1, filter2)
    if key in _COISS_FILTER_WAVELENGTHS:
        return _COISS_FILTER_WAVELENGTHS[key]

    import_util.announce_nonrepeating_warning(
        'Making up wavelength info for unknown COISS filter combination '+
        f'{key[0]}/{key[1]}/{key[2]}')

    # If we don't have the exact key combination, try to set polarization equal
    # to clear for lack of anything better to do.
    nfilter1 = filter1 if filter1.find('P') == -1 else 'CL1'
    nfilter2 = filter2 if filter2.find('P') == -1 else 'CL2'
    key2 = (inst, nfilter1, nfilter2)
    if key2 in _COISS_FILTER_WAVELENGTHS:
        return _COISS_FILTER_WAVELENGTHS[key2]

    # If we don't have the exact key combination, try to make one up by using
    # overlapping regions.
    key1 = (inst, filter1, 'CL2')
    key2 = (inst, 'CL1', filter2)
    if (key1 not in _COISS_FILTER_WAVELENGTHS or
        key2 not in _COISS_FILTER_WAVELENGTHS):
        import_util.announce_nonrepeating_error(
            f'Unknown COISS filter {key[0]}/{key[1]}/{key[2]}')
        impglobals.IMPORT_HAS_BAD_DATA = True
        return 0,0,0

    lc1, fw1, le1 = _COISS_FILTER_WAVELENGTHS[key1]
    lc2, fw2, le2 = _COISS_FILTER_WAVELENGTHS[key2]

    if le1 > le2:
        lc1, fw1, le1, lc2, fw2, le2 = lc2, fw2, le2, lc1, fw1, le1
    l1 = le1-fw1/2
    r1 = le1+fw1/2
    l2 = le2-fw2/2
    r2 = le2+fw2/2

    if r1 < l2:
        # No overlap at all! No idea why anyone would ever do this, but we
        # have to make something up...
        return (lc1+lc2)/2, 0, (le1+le2)/2

    # New region is l2 to r1
    return (lc2-fw2/2 + lc1+fw1/2)/2, (r1-l2)/2, (r1+l2)/2

# This is the effective wavelength (convolved with the solar spectrum)
def populate_obs_wavelength_COISS_effective_wavelength(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    instrument_id = index_row['INSTRUMENT_ID'][3]
    filter1, filter2 = index_row['FILTER_NAME']

    central_wl, fwhm, effective_wl = _COISS_wavelength_helper(
            instrument_id, filter1, filter2)
    return effective_wl / 1000 # microns

# These are the center wavelength +/- FWHM/2
def populate_obs_wavelength_COISS_wavelength1(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    instrument_id = index_row['INSTRUMENT_ID'][3]
    filter1, filter2 = index_row['FILTER_NAME']

    central_wl, fwhm, effective_wl = _COISS_wavelength_helper(
            instrument_id, filter1, filter2)
    return (central_wl - fwhm/2) / 1000 # microns

def populate_obs_wavelength_COISS_wavelength2(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    instrument_id = index_row['INSTRUMENT_ID'][3]
    filter1, filter2 = index_row['FILTER_NAME']

    central_wl, fwhm, effective_wl = _COISS_wavelength_helper(
            instrument_id, filter1, filter2)
    return (central_wl + fwhm/2) / 1000 # microns

def populate_obs_wavelength_COISS_wave_res1(**kwargs):
    return None

def populate_obs_wavelength_COISS_wave_res2(**kwargs):
    return None

def populate_obs_wavelength_COISS_wave_no1(**kwargs):
    metadata = kwargs['metadata']
    wavelength_row = metadata['obs_wavelength_row']
    return 10000 / wavelength_row['wavelength2'] # cm^-1

def populate_obs_wavelength_COISS_wave_no2(**kwargs):
    metadata = kwargs['metadata']
    wavelength_row = metadata['obs_wavelength_row']
    return 10000 / wavelength_row['wavelength1'] # cm^-1

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
# THESE NEED TO BE IMPLEMENTED FOR EVERY CASSINI INSTRUMENT
################################################################################

def populate_obs_mission_cassini_COISS_ert1(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    ert = index_row['EARTH_RECEIVED_START_TIME']
    return ert

def populate_obs_mission_cassini_COISS_ert2(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    ert = index_row['EARTH_RECEIVED_STOP_TIME']
    return ert

def populate_obs_mission_cassini_COISS_spacecraft_clock_count1(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    count = index_row['SPACECRAFT_CLOCK_START_COUNT']
    return float(count)

def populate_obs_mission_cassini_COISS_spacecraft_clock_count2(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    count = index_row['SPACECRAFT_CLOCK_STOP_COUNT']
    return float(count)


################################################################################
# THESE ARE SPECIFIC TO OBS_INSTRUMENT_COISS
################################################################################

def populate_obs_instrument_COISS_camera(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    instrument_id = index_row['INSTRUMENT_ID']
    assert instrument_id[3] in ('N', 'W')
    return instrument_id[3]

def populate_obs_instrument_COISS_filter_name(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    filter1, filter2 = index_row['FILTER_NAME']
    return filter1 + ',' + filter2

def populate_obs_instrument_COISS_combined_filter(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    instrument_id = index_row['INSTRUMENT_ID'][3]
    filter1, filter2 = index_row['FILTER_NAME']

    central_wl1, fwhm1, wl1 = _COISS_wavelength_helper(
            instrument_id, filter1, 'CL2')
    central_wl2, fwhm2, wl2 = _COISS_wavelength_helper(
            instrument_id, 'CL1', filter2)

    if filter1[0] == 'P':
        filter1 = 'POL'
    elif filter1[:3] == 'IRP':
        filter1 = 'IRPOL'

    if filter2[0] == 'P':
        filter2 = 'POL'
    elif filter2[:3] == 'IRP':
        filter2 = 'IRPOL'

    new_filter = None

    if filter1 == 'CL1' and filter2 == 'CL2':
        new_filter = 'CLEAR'
    elif filter1 == 'CL1':
        new_filter = filter2
    elif filter2 == 'CL2':
        new_filter = filter1
    else:
        # If one of them is a polarizer, put it second
        if filter1.find('POL') != -1:
            new_filter = filter2 + '+' + filter1
        elif filter2.find('POL') != -1:
            new_filter = filter1 + '+' + filter2
        else:
            if wl1 > wl2 or (wl1 == wl2 and filter1 > filter2):
                # Place filters in wavelength order
                # If wavelengths are the same, make it name order
                filter1, filter2 = filter2, filter1
            new_filter = filter1 + '+' + filter2

    return (new_filter, new_filter)

def populate_obs_instrument_COISS_image_observation_type(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    obs_type = index_row['IMAGE_OBSERVATION_TYPE']

    has_science = obs_type.find('SCIENCE') != -1
    has_opnav = obs_type.find('OPNAV') != -1
    has_calib = obs_type.find('CALIBRATION') != -1
    has_support = obs_type.find('SUPPORT') != -1
    has_unk = obs_type.find('UNK') != -1

    ret_list = []
    if has_science:
        ret_list.append('Science')
    if has_opnav:
        ret_list.append('OpNav')
    if has_calib:
        ret_list.append('Calibration')
    if has_support:
        ret_list.append('Support')
    if has_unk:
        ret_list.append('Unknown')

    return ','.join(ret_list)
