################################################################################
# populate_obs_instrument_CORSS_occ.py
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
from populate_util import *


################################################################################
# THESE NEED TO BE IMPLEMENTED FOR EVERY INSTRUMENT
################################################################################

### OBS_GENERAL TABLE ###

def _CORSS_file_spec_helper(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    # Format: "data/Rev007/Rev007E/Rev007E_RSS_2005_123_K34_E/RSS_2005_123_K34_E_TAU_01KM.LBL"
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
    return None

def populate_obs_general_CORSS_inst_host_id_OCC(**kwargs):
    return 'CO'

def populate_obs_general_CORSS_time1_OCC(**kwargs):
    return populate_time1_from_index(**kwargs)

def populate_obs_general_CORSS_time2_OCC(**kwargs):
    return populate_time2_from_index(**kwargs)

def populate_obs_general_CORSS_target_name_OCC(**kwargs):
    target_name = 'S RINGS'
    target_name_info = TARGET_NAME_INFO[target_name]
    if len(target_name_info) == 3:
        return target_name, target_name_info[2]

    return (target_name, import_util.cleanup_target_name(target_name))

def populate_obs_general_CORSS_observation_duration_OCC(**kwargs):
    return populate_observation_duration_from_time(**kwargs)

def populate_obs_general_CORSS_quantity_OCC(**kwargs):
    return 'OPDEPTH'

def populate_obs_general_CORSS_observation_type_OCC(**kwargs):
    return 'OCC'

def populate_obs_pds_CORSS_note_OCC(**kwargs):
    return None

def populate_obs_general_CORSS_primary_file_spec_OCC(**kwargs):
    return _CORSS_file_spec_helper(**kwargs)

def populate_obs_pds_CORSS_primary_file_spec_OCC(**kwargs):
    return _CORSS_file_spec_helper(**kwargs)

def populate_obs_pds_CORSS_product_creation_time_OCC(**kwargs):
    return populate_product_creation_time_from_index(**kwargs)

# Format: "CO-SR-RSS-4/5-OCC-V2.0"
def populate_obs_pds_CORSS_data_set_id_OCC(**kwargs):
    return populate_data_set_id_from_index_label(**kwargs)

# Format: "RSS_2005_123_X43_E_TAU_01KM.LBL"
def populate_obs_pds_CORSS_product_id_OCC(**kwargs):
    return populate_product_id_from_index(**kwargs)

# There's no easy way to figure out RA/DEC for CORSS since the Spacecraft
# itself is the signal source.
def populate_obs_general_CORSS_right_asc1_OCC(**kwargs):
    return None

def populate_obs_general_CORSS_right_asc2_OCC(**kwargs):
    return None

def populate_obs_general_CORSS_declination1_OCC(**kwargs):
    return None

def populate_obs_general_CORSS_declination2_OCC(**kwargs):
    return None


### OBS_TYPE_IMAGE TABLE ###

def populate_obs_type_image_CORSS_image_type_id_OCC(**kwargs):
    return None

def populate_obs_type_image_CORSS_duration_OCC(**kwargs):
    return None

def populate_obs_type_image_CORSS_levels_OCC(**kwargs):
    return None

def _pixel_size_helper(**kwargs):
    return None

def populate_obs_type_image_CORSS_lesser_pixel_size_OCC(**kwargs):
    return None

def populate_obs_type_image_CORSS_greater_pixel_size_OCC(**kwargs):
    return None


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
    wl = index_row['WAVELENGTH']

    return wl

def populate_obs_wavelength_CORSS_wavelength2_OCC(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    wl = index_row['WAVELENGTH']

    return wl

def populate_obs_wavelength_CORSS_wave_res1_OCC(**kwargs):
    return None

def populate_obs_wavelength_CORSS_wave_res2_OCC(**kwargs):
    return None

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

def populate_obs_wavelength_CORSS_wave_no_res1_OCC(**kwargs):
    return None

def populate_obs_wavelength_CORSS_wave_no_res2_OCC(**kwargs):
    return None

def populate_obs_wavelength_CORSS_spec_flag_OCC(**kwargs):
    return 'N'

def populate_obs_wavelength_CORSS_spec_size_OCC(**kwargs):
    return None

def populate_obs_wavelength_CORSS_polarization_type_OCC(**kwargs):
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

def populate_obs_mission_cassini_CORSS_ert1(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['supp_index_row']

    # START_TIME isn't available for COUVIS
    start_time = index_row.get('EARTH_RECEIVED_START_TIME', None)
    if start_time is None or start_time == 'UNK':
        return None

    try:
        ert_sec = julian.tai_from_iso(start_time)
    except Exception as e:
        import_util.log_nonrepeating_warning(
            f'Bad earth received start time format "{start_time}": {e}')
        return None

    return ert_sec

def populate_obs_mission_cassini_CORSS_ert2(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['supp_index_row']

    # STOP_TIME isn't available for COUVIS
    stop_time = index_row.get('EARTH_RECEIVED_STOP_TIME', None)
    if stop_time is None or stop_time == 'UNK':
        return None

    try:
        ert_sec = julian.tai_from_iso(stop_time)
    except Exception as e:
        import_util.log_nonrepeating_warning(
            f'Bad earth received stop time format "{stop_time}": {e}')
        return None

    cassini_row = metadata['obs_mission_cassini_row']
    start_time_sec = cassini_row['ert1']

    if start_time_sec is not None and ert_sec < start_time_sec:
        import_util.log_warning(
            f'cassini_ert1 ({start_time_sec}) and cassini_ert2 ({ert_sec}) '
            +f'are in the wrong order - setting to ert1')
        ert_sec = start_time_sec

    return ert_sec

def populate_obs_mission_cassini_CORSS_spacecraft_clock_count1_OCC(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['supp_index_row']
    count = index_row['SPACECRAFT_CLOCK_START_COUNT']
    sc = '1/' + str(count)
    try:
        sc_cvt = opus_support.parse_cassini_sclk(sc)
    except Exception as e:
        import_util.log_nonrepeating_warning(
            f'Unable to parse Cassini SCLK "{sc}": {e}')
        return None
    return sc_cvt

def populate_obs_mission_cassini_CORSS_spacecraft_clock_count2_OCC(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['supp_index_row']
    count = index_row['SPACECRAFT_CLOCK_STOP_COUNT']
    sc = '1/' + str(count)
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

    return sc_cvt

def populate_obs_mission_cassini_CORSS_mission_phase_name_OCC(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['supp_index_row']
    mp = index_row['MISSION_PHASE_NAME']
    if mp.upper() == 'NULL':
        return None
    return mp.replace('_', ' ')

def populate_obs_mission_cassini_CORSS_sequence_id_OCC(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['supp_index_row']
    seqid = index_row['SEQUENCE_ID']
    return seqid


################################################################################
# THESE ARE SPECIFIC TO OBS_INSTRUMENT_CORSS
################################################################################
