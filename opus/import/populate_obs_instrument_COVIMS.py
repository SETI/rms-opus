# The COVIMS_0xxx index file doesn't use FILE_SPECIFICATION_NAME
# (thanks VIMS team) but that's how we match across (supplemental) index
# files, so it's easier just to fake one here rather than special-case
# all the uses of FILE_SPECIFICATION_NAME later.
# if volset == 'COVIMS_0xxx':
#     vims_filename = index_row['FILE_NAME']
#     vims_path = index_row['PATH_NAME']
#     if vims_path[0] == '/':
#         vims_path = vims_path[1:]
#     filespec = vims_path + '/' + vims_filename.replace('.qub', '.lbl')
#     index_row['FILE_SPECIFICATION_NAME'] = filespec
#

################################################################################
# populate_obs_instrument_COVIMS.py
#
# Routines to populate fields specific to COVIMS.
################################################################################

# Ordering:
#   time_sec1/2 must come before observation_duration
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

def _COVIMS_filespec_helper(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    # Format: "/data/1999010T054026_1999010T060958"
    path_name = index_row['PATH_NAME']
    # Format: "v1294638283_1.qub"
    file_name = index_row['FILE_NAME']
    volume_id = kwargs['volume_id']

    return volume_id + path_name + '/' + file_name

def populate_obs_general_COVIMS_opus_id_OBS(**kwargs):
    metadata = kwargs['metadata']
    phase_name = metadata['phase_name'].lower()
    filespec = _COVIMS_filespec_helper(**kwargs)
    pds_file = pdsfile.PdsFile.from_filespec(filespec, fix_case=True)
    opus_id = pds_file.opus_id
    if not opus_id:
        import_util.log_nonrepeating_error(
            f'Unable to create OPUS_ID for FILE_SPEC "{filespec}"')
        return filespec.split('/')[-1] + '_' + phase_name
    opus_id += '_' + phase_name
    return opus_id

def populate_obs_general_COVIMS_ring_obs_id_OBS(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    filename = index_row['FILE_NAME']
    image_num = filename[1:11]
    phase_name = metadata['phase_name']
    planet = helper_cassini_planet_id(**kwargs)
    if planet is None:
        pl_str = ''
    else:
        pl_str = planet[0]

    return pl_str + '_CUBE_CO_VIMS_' + image_num + '_' + phase_name

def populate_obs_general_COVIMS_inst_host_id_OBS(**kwargs):
    return 'CO'

def populate_obs_general_COVIMS_quantity_OBS(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    inst_mod = index_row['INSTRUMENT_MODE_ID']

    if inst_mod == 'OCCULTATION':
        return 'OPDEPTH'
    return 'REFLECT'
    # XXX CAL?

def populate_obs_general_COVIMS_observation_type_OBS(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    inst_mod = index_row['INSTRUMENT_MODE_ID']

    if inst_mod == 'OCCULTATION':
        return 'TS' # Time Series
    return 'SCU' # Spectral Cube

def populate_obs_general_COVIMS_time1_OBS(**kwargs):
    return populate_time1_from_index(**kwargs)

def populate_obs_general_COVIMS_time2_OBS(**kwargs):
    return populate_time2_from_index(**kwargs)

def populate_obs_general_COVIMS_target_name_OBS(**kwargs):
    return helper_cassini_intended_target_name(**kwargs)

def populate_obs_general_COVIMS_observation_duration_OBS(**kwargs):
    return populate_observation_duration_from_time(**kwargs)

def populate_obs_pds_COVIMS_note_OBS(**kwargs):
    None

def populate_obs_general_COVIMS_primary_filespec_OBS(**kwargs):
    return _COVIMS_filespec_helper(**kwargs)

def populate_obs_pds_COVIMS_primary_filespec_OBS(**kwargs):
    return _COVIMS_filespec_helper(**kwargs)

def populate_obs_pds_COVIMS_product_creation_time_OBS(**kwargs):
    return populate_product_creation_time_from_supp_index(**kwargs)

# Format: "CO-E/V/J/S-VIMS-2-QUBE-V1.0"
def populate_obs_pds_COVIMS_data_set_id_OBS(**kwargs):
    return populate_data_set_id_from_index_label(**kwargs)

# Format: "1/1294638283_1"
def populate_obs_pds_COVIMS_product_id_OBS(**kwargs):
    return populate_product_id_from_index(**kwargs)

def populate_obs_general_COVIMS_right_asc1_OBS(**kwargs):
    metadata = kwargs['metadata']
    ring_geo_row = metadata.get('ring_geo_row', None)
    if ring_geo_row is not None:
        return import_util.safe_column(ring_geo_row, 'MINIMUM_RIGHT_ASCENSION')

    index_row = metadata['index_row']
    ra = import_util.safe_column(index_row, 'RIGHT_ASCENSION')
    return ra

def populate_obs_general_COVIMS_right_asc2_OBS(**kwargs):
    metadata = kwargs['metadata']
    ring_geo_row = metadata.get('ring_geo_row', None)
    if ring_geo_row is not None:
        return import_util.safe_column(ring_geo_row, 'MAXIMUM_RIGHT_ASCENSION')

    index_row = metadata['index_row']
    ra = import_util.safe_column(index_row, 'RIGHT_ASCENSION')
    return ra

def populate_obs_general_COVIMS_declination1_OBS(**kwargs):
    metadata = kwargs['metadata']
    ring_geo_row = metadata.get('ring_geo_row', None)
    if ring_geo_row is not None:
        return import_util.safe_column(ring_geo_row, 'MINIMUM_DECLINATION')

    index_row = metadata['index_row']
    dec = import_util.safe_column(index_row, 'DECLINATION')
    return dec

def populate_obs_general_COVIMS_declination2_OBS(**kwargs):
    metadata = kwargs['metadata']
    ring_geo_row = metadata.get('ring_geo_row', None)
    if ring_geo_row is not None:
        return import_util.safe_column(ring_geo_row, 'MAXIMUM_DECLINATION')

    index_row = metadata['index_row']
    dec = import_util.safe_column(index_row, 'DECLINATION')
    return dec


### OBS_TYPE_IMAGE TABLE ###

def populate_obs_type_image_COVIMS_image_type_id_OBS(**kwargs):
    metadata = kwargs['metadata']
    phase_name = metadata['phase_name']
    index_row = metadata['index_row']
    inst_mod = index_row['INSTRUMENT_MODE_ID']

    if inst_mod != 'IMAGE':
        return None
    if phase_name == 'VIS':
        return 'PUSH'
    return 'RAST'

def populate_obs_type_image_COVIMS_duration_OBS(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    inst_mod = index_row['INSTRUMENT_MODE_ID']

    if inst_mod != 'IMAGE':
        return None

    phase_name = metadata['phase_name']
    ir_exp = import_util.safe_column(index_row, 'IR_EXPOSURE')
    vis_exp = import_util.safe_column(index_row, 'VIS_EXPOSURE')

    if phase_name == 'IR':
        if ir_exp is None:
            return None
        if ir_exp < 0:
            import_util.log_nonrepeating_warning(f'IR Exposure {ir_exp} is < 0')
            return None
        return ir_exp/1000
    if vis_exp is None:
        return None
    if vis_exp < 0:
        import_util.log_nonrepeating_warning(f'VIS Exposure {vis_exp} is < 0')
        return None
    return vis_exp/1000

def populate_obs_type_image_COVIMS_levels_OBS(**kwargs):
    return 4096

def populate_obs_type_image_COVIMS_lesser_pixel_size_OBS(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    inst_mod = index_row['INSTRUMENT_MODE_ID']

    if inst_mod != 'IMAGE':
        return None

    width = import_util.safe_column(index_row, 'SWATH_WIDTH')
    length = import_util.safe_column(index_row, 'SWATH_LENGTH')

    return min(width, length)

def populate_obs_type_image_COVIMS_greater_pixel_size_OBS(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    inst_mod = index_row['INSTRUMENT_MODE_ID']

    if inst_mod != 'IMAGE':
        return None

    width = import_util.safe_column(index_row, 'SWATH_WIDTH')
    length = import_util.safe_column(index_row, 'SWATH_LENGTH')

    return max(width, length)


### OBS_WAVELENGTH TABLE ###

def populate_obs_wavelength_COVIMS_wavelength1_OBS(**kwargs):
    metadata = kwargs['metadata']
    phase_name = metadata['phase_name']

    if phase_name == 'IR':
        return 0.8842
    return 0.35054

def populate_obs_wavelength_COVIMS_wavelength2_OBS(**kwargs):
    metadata = kwargs['metadata']
    phase_name = metadata['phase_name']

    if phase_name == 'IR':
        return 5.1225
    return 1.04598

def populate_obs_wavelength_COVIMS_wave_res1_OBS(**kwargs):
    metadata = kwargs['metadata']
    phase_name = metadata['phase_name']

    if phase_name == 'IR':
        return 0.01662
    return 0.0073204

def populate_obs_wavelength_COVIMS_wave_res2_OBS(**kwargs):
    metadata = kwargs['metadata']
    phase_name = metadata['phase_name']

    if phase_name == 'IR':
        return 0.01662
    return 0.0073204

def populate_obs_wavelength_COVIMS_wave_no1_OBS(**kwargs):
    metadata = kwargs['metadata']
    wavelength_row = metadata['obs_wavelength_row']
    return 10000 / wavelength_row['wavelength2'] # cm^-1

def populate_obs_wavelength_COVIMS_wave_no2_OBS(**kwargs):
    metadata = kwargs['metadata']
    wavelength_row = metadata['obs_wavelength_row']
    return 10000 / wavelength_row['wavelength1'] # cm^-1

def populate_obs_wavelength_COVIMS_wave_no_res1_OBS(**kwargs):
    metadata = kwargs['metadata']
    wl_row = metadata['obs_wavelength_row']
    wave_res2 = wl_row['wave_res2']
    wl2 = wl_row['wavelength2']

    if wave_res2 is None or wl2 is None:
        return None

    return wave_res2 * 10000. / (wl2*wl2)

def populate_obs_wavelength_COVIMS_wave_no_res2_OBS(**kwargs):
    metadata = kwargs['metadata']
    wl_row = metadata['obs_wavelength_row']
    wave_res1 = wl_row['wave_res1']
    wl1 = wl_row['wavelength1']

    if wave_res1 is None or wl1 is None:
        return None

    return wave_res1 * 10000. / (wl1*wl1)

def populate_obs_wavelength_COVIMS_spec_flag_OBS(**kwargs):
    return 'Y'

def populate_obs_wavelength_COVIMS_spec_size_OBS(**kwargs):
    metadata = kwargs['metadata']
    phase_name = metadata['phase_name']

    if phase_name == 'IR':
        return 256
    return 96

def populate_obs_wavelength_COVIMS_polarization_type_OBS(**kwargs):
    return 'NONE'


### populate_obs_occultation TABLE ###

def populate_obs_occultation_COVIMS_occ_type_OBS(**kwargs):
    return None

def populate_obs_occultation_COVIMS_occ_dir_OBS(**kwargs):
    return None

def populate_obs_occultation_COVIMS_body_occ_flag_OBS(**kwargs):
    return None

def populate_obs_occultation_COVIMS_optical_depth_min_OBS(**kwargs):
    return None

def populate_obs_occultation_COVIMS_optical_depth_max_OBS(**kwargs):
    return None

def populate_obs_occultation_COVIMS_temporal_sampling_OBS(**kwargs):
    return None

def populate_obs_occultation_COVIMS_quality_score_OBS(**kwargs):
    return None

def populate_obs_occultation_COVIMS_wl_band_OBS(**kwargs):
    return None

def populate_obs_occultation_COVIMS_source_OBS(**kwargs):
    return None

def populate_obs_occultation_COVIMS_host_OBS(**kwargs):
    return None


################################################################################
# THESE NEED TO BE IMPLEMENTED FOR EVERY CASSINI INSTRUMENT
################################################################################

def populate_obs_mission_cassini_COVIMS_ert1_OBS(**kwargs):
    return None

def populate_obs_mission_cassini_COVIMS_ert2_OBS(**kwargs):
    return None

def populate_obs_mission_cassini_COVIMS_spacecraft_clock_count1_OBS(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    count = index_row['SPACECRAFT_CLOCK_START_COUNT']
    sc = '1/' + count
    sc = helper_fix_cassini_sclk(sc)
    try:
        sc_cvt = opus_support.parse_cassini_sclk(sc)
    except Exception as e:
        import_util.log_nonrepeating_warning(
            f'Unable to parse Cassini SCLK "{sc}": {e}')
        return None
    return sc_cvt

def populate_obs_mission_cassini_COVIMS_spacecraft_clock_count2_OBS(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    count = index_row['SPACECRAFT_CLOCK_STOP_COUNT']
    sc = '1/' + count
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
    +'are in the wrong order - setting to count1')
        sc_cvt = sc1

    return sc_cvt

def populate_obs_mission_cassini_COVIMS_mission_phase_name_OBS(**kwargs):
    return helper_cassini_mission_phase_name(**kwargs)

def populate_obs_mission_cassini_COVIMS_sequence_id_OBS(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    seqid = index_row['SEQ_ID']
    return seqid


################################################################################
# THESE ARE SPECIFIC TO OBS_INSTRUMENT_COVIMS
################################################################################

def populate_obs_instrument_covims_channel_OBS(**kwargs):
    metadata = kwargs['metadata']
    phase_name = metadata['phase_name']

    return (phase_name, phase_name)

def populate_obs_instrument_covims_vis_exposure_OBS(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    vis_exp = import_util.safe_column(index_row, 'VIS_EXPOSURE')

    if vis_exp is None:
        return None

    return vis_exp / 1000.

def populate_obs_instrument_covims_ir_exposure_OBS(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    ir_exp = import_util.safe_column(index_row, 'IR_EXPOSURE')

    if ir_exp is None:
        return None

    return ir_exp / 1000.
