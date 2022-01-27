################################################################################
# populate_obs_instrument_COCIRS_obs.py
#
# Routines to populate fields specific to COCIRS.
################################################################################

# Ordering:
#   time1/2 must come before planet_id
#   planet_id must come before opus_id

import pdsfile

from config_data import *
import import_util

from populate_obs_mission_cassini import *
from populate_util import *


################################################################################
# THESE NEED TO BE IMPLEMENTED FOR EVERY INSTRUMENT
################################################################################

### OBS_GENERAL TABLE ###

def _COCIRS_filespec_helper(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    # Format: "DATA/APODSPEC/SPEC0802010000_FP1.DAT"
    filespec = index_row['SPECTRUM_FILE_SPECIFICATION']
    volume_id = kwargs['volume_id']
    return volume_id + '/' + filespec

def populate_obs_general_COCIRS_opus_id_OBS(**kwargs):
    filespec = _COCIRS_filespec_helper(**kwargs)
    pds_file = pdsfile.PdsFile.from_filespec(filespec, fix_case=True)
    opus_id = pds_file.opus_id
    if not opus_id:
        import_util.log_nonrepeating_error(
            f'Unable to create OPUS_ID for FILE_SPEC "{filespec}"')
        return filespec.split('/')[-1]
    return opus_id

def populate_obs_general_COCIRS_ring_obs_id_OBS(**kwargs):
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

def populate_obs_general_COCIRS_inst_host_id_OBS(**kwargs):
    return 'CO'

def populate_obs_general_COCIRS_time1_OBS(**kwargs):
    return populate_time1_from_index(**kwargs)

def populate_obs_general_COCIRS_time2_OBS(**kwargs):
    return populate_time2_from_index(**kwargs)

def populate_obs_general_COCIRS_target_name_OBS(**kwargs):
    return helper_cassini_intended_target_name(**kwargs)

def populate_obs_general_COCIRS_observation_duration_OBS(**kwargs):
    return populate_observation_duration_from_time(**kwargs)

def populate_obs_general_COCIRS_quantity_OBS(**kwargs):
    return 'THERMAL'

def populate_obs_general_COCIRS_observation_type_OBS(**kwargs):
    return 'STS' # Spectral Time Series

def populate_obs_pds_COCIRS_note_OBS(**kwargs):
    return None

def populate_obs_general_COCIRS_primary_filespec_OBS(**kwargs):
    return _COCIRS_filespec_helper(**kwargs)

def populate_obs_pds_COCIRS_primary_filespec_OBS(**kwargs):
    return _COCIRS_filespec_helper(**kwargs)

def populate_obs_pds_COCIRS_product_creation_time_OBS(**kwargs):
    return None # Until the proper data is available in the supplemental index

# Format: "CO-S-CIRS-2/3/4-REFORMATTED-V1.0"
def populate_obs_pds_COCIRS_data_set_id_OBS(**kwargs):
    return populate_data_set_id_from_index_label(**kwargs)

def populate_obs_pds_COCIRS_product_id_OBS(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    # Format: "DATA/APODSPEC/SPEC0802010000_FP1.DAT"
    filename = index_row['SPECTRUM_FILE_SPECIFICATION'].split('/')[-1]
    return filename

# We don't have ring geometry or other such info for CIRS
def populate_obs_general_COCIRS_right_asc1_OBS(**kwargs):
    return None

def populate_obs_general_COCIRS_right_asc2_OBS(**kwargs):
    return None

def populate_obs_general_COCIRS_declination1_OBS(**kwargs):
    return None

def populate_obs_general_COCIRS_declination2_OBS(**kwargs):
    return None


### OBS_TYPE_IMAGE TABLE ###

def populate_obs_type_image_COCIRS_image_type_id_OBS(**kwargs):
    return None

def populate_obs_type_image_COCIRS_duration_OBS(**kwargs):
    return None

def populate_obs_type_image_COCIRS_levels_OBS(**kwargs):
    return None

def populate_obs_type_image_COCIRS_lesser_pixel_size_OBS(**kwargs):
    return None

def populate_obs_type_image_COCIRS_greater_pixel_size_OBS(**kwargs):
    return None


### OBS_WAVELENGTH TABLE ###

def populate_obs_wavelength_COCIRS_wavelength1_OBS(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    wave_no2 = index_row['MAXIMUM_WAVENUMBER']

    if wave_no2 is None:
        return None

    return 10000. / wave_no2

def populate_obs_wavelength_COCIRS_wavelength2_OBS(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    wave_no1 = index_row['MINIMUM_WAVENUMBER']

    if wave_no1 is None:
        return None

    return 10000. / wave_no1

def populate_obs_wavelength_COCIRS_wave_res1_OBS(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    wave_no_res2 = index_row['WAVENUMBER_RESOLUTION']
    wave_no2 = index_row['MAXIMUM_WAVENUMBER']

    if wave_no_res2 is None or wave_no2 is None:
        return None

    return 10000.*wave_no_res2/(wave_no2 * wave_no2)

def populate_obs_wavelength_COCIRS_wave_res2_OBS(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    wave_no_res1 = index_row['WAVENUMBER_RESOLUTION']
    wave_no1 = index_row['MINIMUM_WAVENUMBER']

    if wave_no_res1 is None or wave_no1 is None:
        return None

    return 10000.*wave_no_res1/(wave_no1 * wave_no1)

def populate_obs_wavelength_COCIRS_wave_no1_OBS(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    wave_no2 = index_row['MINIMUM_WAVENUMBER']
    return wave_no2

def populate_obs_wavelength_COCIRS_wave_no2_OBS(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    wave_no2 = index_row['MAXIMUM_WAVENUMBER']
    return wave_no2

def populate_obs_wavelength_COCIRS_wave_no_res1_OBS(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    wave_no_res1 = index_row['WAVENUMBER_RESOLUTION']
    return wave_no_res1

def populate_obs_wavelength_COCIRS_wave_no_res2_OBS(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    wave_no_res2 = index_row['WAVENUMBER_RESOLUTION']
    return wave_no_res2

def populate_obs_wavelength_COCIRS_spec_flag_OBS(**kwargs):
    return 'Y'

def populate_obs_wavelength_COCIRS_spec_size_OBS(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    wave_no_res1 = index_row['SPECTRUM_SAMPLES']
    return wave_no_res1

def populate_obs_wavelength_COCIRS_polarization_type_OBS(**kwargs):
    return 'NONE'


### populate_obs_occultation TABLE ###

def populate_obs_occultation_COCIRS_occ_type_OBS(**kwargs):
    return None

def populate_obs_occultation_COCIRS_occ_dir_OBS(**kwargs):
    return None

def populate_obs_occultation_COCIRS_body_occ_flag_OBS(**kwargs):
    return None

def populate_obs_occultation_COCIRS_optical_depth_min_OBS(**kwargs):
    return None

def populate_obs_occultation_COCIRS_optical_depth_max_OBS(**kwargs):
    return None

def populate_obs_occultation_COCIRS_temporal_sampling_OBS(**kwargs):
    return None

def populate_obs_occultation_COCIRS_quality_score_OBS(**kwargs):
    return None

def populate_obs_occultation_COCIRS_wl_band_OBS(**kwargs):
    return None

def populate_obs_occultation_COCIRS_source_OBS(**kwargs):
    return None

def populate_obs_occultation_COCIRS_host_OBS(**kwargs):
    return None


################################################################################
# THESE NEED TO BE IMPLEMENTED FOR EVERY CASSINI INSTRUMENT
################################################################################

def populate_obs_mission_cassini_COCIRS_ert1_OBS(**kwargs):
    return None

def populate_obs_mission_cassini_COCIRS_ert2_OBS(**kwargs):
    return None

def populate_obs_mission_cassini_COCIRS_spacecraft_clock_count1_OBS(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    sc = index_row['SPACECRAFT_CLOCK_START_COUNT']
    sc = helper_fix_cassini_sclk(sc)
    if not sc.startswith('1/') or sc[2] == ' ':
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

def populate_obs_mission_cassini_COCIRS_spacecraft_clock_count2_OBS(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    sc = index_row['SPACECRAFT_CLOCK_STOP_COUNT']
    sc = helper_fix_cassini_sclk(sc)
    cassini_row = metadata['obs_mission_cassini_row']

    # For CIRS only, there are some badly formatted clock counts
    sc1 = cassini_row['spacecraft_clock_count1']
    if not sc.startswith('1/') or sc[2] == ' ':
        import_util.log_nonrepeating_warning(
            f'Badly formatted SPACECRAFT_CLOCK_STOP_COUNT "{sc}"')
        return sc1
    try:
        sc_cvt = opus_support.parse_cassini_sclk(sc)
    except Exception as e:
        import_util.log_nonrepeating_warning(
            f'Unable to parse Cassini SCLK "{sc}": {e}')
        return sc1

    if sc1 is not None and sc_cvt < sc1:
        import_util.log_warning(
    f'spacecraft_clock_count1 ({sc1}) and spacecraft_clock_count2 ({sc_cvt}) '
    +'are in the wrong order - setting to count1')
        sc_cvt = sc1

    return sc_cvt

# Format: "SCIENCE_CRUISE"
def populate_obs_mission_cassini_COCIRS_mission_phase_name_OBS(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    mp = index_row['MISSION_PHASE_NAME']
    if mp.upper() == 'NULL':
        return None
    return mp.replace('_', ' ')

def populate_obs_mission_cassini_COCIRS_sequence_id_OBS(**kwargs):
    return None


################################################################################
# THESE ARE SPECIFIC TO OBS_INSTRUMENT_COCIRS
################################################################################
