################################################################################
# populate_obs_instrument_EB.py
#
# Routines to populate fields specific to Earth-based instruments.
################################################################################

import numpy as np

import julian
import pdsfile

from config_data import *
import import_util

from populate_obs_mission_earthbased_occ import *


################################################################################
# THESE NEED TO BE IMPLEMENTED FOR EVERY INSTRUMENT
################################################################################

### OBS_GENERAL TABLE ###

def _EB_file_spec_helper(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata.get('index_row', None)
    if index_row is None:
        return None
    # Format: "/DATA/ESO1M/ES1_EPD.LBL"
    file_spec = index_row['FILE_SPECIFICATION_NAME']
    volume_id = kwargs['volume_id']
    return volume_id + file_spec

def populate_obs_general_EB_opus_id_OCC(**kwargs):
    file_spec = _EB_file_spec_helper(**kwargs)
    pds_file = pdsfile.PdsFile.from_filespec(file_spec)
    try:
        opus_id = pds_file.opus_id
    except:
        opus_id = None
    if not opus_id:
        metadata = kwargs['metadata']
        index_row = metadata['index_row']
        import_util.log_nonrepeating_error(
            f'Unable to create OPUS_ID for FILE_SPEC "{file_spec}"')
        return file_spec.split('/')[-1]
    return opus_id

def populate_obs_general_EB_ring_obs_id_OCC(**kwargs):
    return None

def populate_obs_general_EB_inst_host_id_OCC(**kwargs):
    return 'EB'

def populate_obs_general_EB_data_type_OCC(**kwargs):
    return 'OCC'

def populate_obs_general_EB_time1_OCC(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    start_time = index_row['START_TIME']

    if start_time is None or start_time == 'UNK':
        return None

    try:
        start_time_sec = julian.tai_from_iso(start_time)
    except Exception as e:
        import_util.log_nonrepeating_error(
            f'Bad start time format "{start_time}": {e}')
        return None

    return start_time_sec

def populate_obs_general_EB_time2_OCC(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    stop_time = import_util.safe_column(index_row, 'STOP_TIME')

    if stop_time is None or stop_time == 'UNK':
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

def populate_obs_general_EB_target_name_OCC(**kwargs):
    return helper_earthbased_target_name(**kwargs)

def populate_obs_general_EB_observation_duration_OCC(**kwargs):
    metadata = kwargs['metadata']
    general_row = metadata['obs_general_row']
    start_time_sec = general_row['time1']
    stop_time_sec = general_row['time2']

    if start_time_sec is None or stop_time_sec is None:
        return None

    return stop_time_sec - start_time_sec

def populate_obs_general_EB_quantity_OCC(**kwargs):
    return 'OPDEPTH'

def populate_obs_general_EB_observation_type_OCC(**kwargs):
    return 'OCC'

def populate_obs_pds_EB_note_OCC(**kwargs):
    return None

def populate_obs_general_EB_primary_file_spec_OCC(**kwargs):
    return _EB_file_spec_helper(**kwargs)

def populate_obs_pds_EB_primary_file_spec_OCC(**kwargs):
    return _EB_file_spec_helper(**kwargs)

def populate_obs_pds_EB_product_creation_time_OCC(**kwargs):
    # For EB the PRODUCT_CREATION_TIME is provided in the volume label file,
    # not the individual observation rows
    metadata = kwargs['metadata']
    index_label = metadata['index_row']
    pct = index_label['PRODUCT_CREATION_TIME']

    try:
        pct_sec = julian.tai_from_iso(pct)
    except Exception as e:
        import_util.log_nonrepeating_error(
            f'Bad product creation time format "{pct}": {e}')
        return None

    return pct_sec

def populate_obs_pds_EB_data_set_id_OCC(**kwargs):
    metadata = kwargs['metadata']
    index_label = metadata['index_label']
    dsi = index_label['DATA_SET_ID']
    return dsi

def populate_obs_pds_EB_product_id_OCC(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    product_id = index_row['PRODUCT_ID']

    return product_id

def _ra_dec_helper(**kwargs):
    metadata = kwargs['metadata']
    index_label = metadata['index_label']
    star_name = index_label['STAR_NAME']
    if star_name not in import_util.STAR_RA_DEC:
        import_util.log_nonrepeating_error(
            f'Star "{star_name}" missing RA and DEC information'
        )
        return None, None

    return STAR_RA_DEC[star_name]

def populate_obs_general_EB_right_asc1_OCC(**kwargs):
    return _ra_dec_helper(**kwargs)[0]

def populate_obs_general_EB_right_asc2_OCC(**kwargs):
    return _ra_dec_helper(**kwargs)[0]

def populate_obs_general_EB_declination1_OCC(**kwargs):
    return _ra_dec_helper(**kwargs)[1]

def populate_obs_general_EB_declination2_OCC(**kwargs):
    return _ra_dec_helper(**kwargs)[1]


### OBS_TYPE_IMAGE TABLE ###

def populate_obs_type_image_EB_image_type_id_OCC(**kwargs):
    return None

def populate_obs_type_image_EB_duration_OCC(**kwargs):
    return None

def populate_obs_type_image_EB_levels_OCC(**kwargs):
    return None

def populate_obs_type_image_EB_lesser_pixel_size_OCC(**kwargs):
    return None

def populate_obs_type_image_EB_greater_pixel_size_OCC(**kwargs):
    return None


### OBS_WAVELENGTH TABLE ###

# For EB, effective wavelengths are taken from the published table.
# Other wavelengths are taken by eyeballing the filter graphs.

def populate_obs_wavelength_EB_wavelength1_OCC(**kwargs):
    metadata = kwargs['metadata']
    index_label = metadata['index_label']
    wl = index_label['WAVELENGTH'] # microns

    return wl

def populate_obs_wavelength_EB_wavelength2_OCC(**kwargs):
    metadata = kwargs['metadata']
    index_label = metadata['index_label']
    wl = index_label['WAVELENGTH'] # microns

    return wl

def populate_obs_wavelength_EB_wave_res1_OCC(**kwargs):
    return None # Not available

def populate_obs_wavelength_EB_wave_res2_OCC(**kwargs):
    return None # Not available

def populate_obs_wavelength_EB_wave_no1_OCC(**kwargs):
    metadata = kwargs['metadata']
    index_label = metadata['index_label']
    wl = index_label['WAVELENGTH'] # microns

    return 10000 / wl # cm^-1

def populate_obs_wavelength_EB_wave_no2_OCC(**kwargs):
    metadata = kwargs['metadata']
    index_label = metadata['index_label']
    wl = index_label['WAVELENGTH'] # microns

    return 10000 / wl # cm^-1

def populate_obs_wavelength_EB_wave_no_res1_OCC(**kwargs):
    return None # Not available

def populate_obs_wavelength_EB_wave_no_res2_OCC(**kwargs):
    return None # Not available

def populate_obs_wavelength_EB_spec_flag_OCC(**kwargs):
    return 'N'

def populate_obs_wavelength_EB_spec_size_OCC(**kwargs):
    return None

def populate_obs_wavelength_EB_polarization_type_OCC(**kwargs):
    return 'NONE'


### populate_obs_occultation TABLE ###

def populate_obs_occultation_EB_occ_type_OCC(**kwargs):
    metadata = kwargs['metadata']
    index_label = metadata['index_label']
    star_name = index_label['STAR_NAME']

    if star_name == 'SUN':
        return 'SOL'
    return 'STE'

def populate_obs_occultation_EB_occ_dir_OCC(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    occ_dir = index_row['OCCULTATION_DIRECTION']

    if occ_dir == 'INGRESS':
        return 'I'
    if occ_dir == 'EGRESS':
        return 'E'
    if occ_dir == 'BOTH':
        return 'B'

    import_util.log_nonrepeating_error(
        f'Unknown OCCULTATION_DIRECTIN "{occ_dir}"')
    return None

def populate_obs_occultation_EB_body_occ_flag_OCC(**kwargs):
    return None # XXX FROM LABEL

def populate_obs_occultation_EB_optical_depth_min_OCC(**kwargs):
    return None # Not available

def populate_obs_occultation_EB_optical_depth_max_OCC(**kwargs):
    return None # Not available

def populate_obs_occultation_EB_temporal_sampling_OCC(**kwargs):
    return None # Not available

def populate_obs_occultation_EB_quality_score_OCC(**kwargs):
    return ("UNASSIGNED", "Unassigned")

def populate_obs_occultation_EB_wl_band_OCC(**kwargs):
    metadata = kwargs['metadata']
    index_label = metadata['index_label']
    wl = index_label['WAVELENGTH'] # microns

    if wl > 0.7:
        return 'IR'
    if wl > 0.4:
        return 'VIS'
    return 'UV'

def populate_obs_occultation_EB_source_OCC(**kwargs):
    metadata = kwargs['metadata']
    index_label = metadata['index_label']
    star_name = index_label['STAR_NAME']

    return star_name

def populate_obs_occultation_EB_host_OCC(**kwargs):
    return None # XXX FROM LABEL


################################################################################
# THESE NEED TO BE IMPLEMENTED FOR EVERY EARTH-BASED INSTRUMENT
################################################################################



################################################################################
# THESE ARE SPECIFIC TO OBS_INSTRUMENT_EB
################################################################################
