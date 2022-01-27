################################################################################
# populate_obs_instrument_NHLORRI.py
#
# Routines to populate fields specific to NHLORRI.
################################################################################

import pdsfile

import import_util

from populate_obs_mission_new_horizons import *
from populate_util import *


################################################################################
# THESE NEED TO BE IMPLEMENTED FOR EVERY INSTRUMENT
################################################################################

### OBS_GENERAL TABLE ###

def _NHLORRI_filespec_helper(**kwargs):
    metadata = kwargs['metadata']
    supp_index_row = metadata['supp_index_row']
    # Format: "data/20070108_003059/lor_0030598439_0x630_eng.lbl"
    filespec = supp_index_row['FILE_SPECIFICATION_NAME']
    volume_id = kwargs['volume_id']
    return volume_id + '/' + filespec

def populate_obs_general_NHLORRI_opus_id_OBS(**kwargs):
    filespec = _NHLORRI_filespec_helper(**kwargs)
    pds_file = pdsfile.PdsFile.from_filespec(filespec, fix_case=True)
    opus_id = pds_file.opus_id
    if not opus_id:
        import_util.log_nonrepeating_error(
            f'Unable to create OPUS_ID for FILE_SPEC "{filespec}"')
        return filespec.split('/')[-1]
    return opus_id

def populate_obs_general_NHLORRI_ring_obs_id_OBS(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    image_num = index_row['FILE_NAME'][4:14]
    start_time = index_row['START_TIME']
    # This is really dumb, but it's what the old OPUS did so we do it for
    # backwards compatability
    start_time = index_row['START_TIME']
    if start_time > '2007-09-01':
        pl_str = 'P'
    else:
        pl_str = 'J'

    return pl_str + '_IMG_NH_LORRI_' + image_num

def populate_obs_general_NHLORRI_inst_host_id_OBS(**kwargs):
    return 'NH'

def populate_obs_general_NHLORRI_time1_OBS(**kwargs):
    return populate_time1_from_index(**kwargs)

def populate_obs_general_NHLORRI_time2_OBS(**kwargs):
    return populate_time2_from_index(**kwargs)

def populate_obs_general_NHLORRI_target_name_OBS(**kwargs):
    target_name = helper_new_horizons_target_name(**kwargs)
    if target_name is None:
        target_name = 'NONE'
    return target_name

def populate_obs_general_NHLORRI_observation_duration_OBS(**kwargs):
    metadata = kwargs['metadata']
    supp_index_row = metadata['supp_index_row']
    exposure = import_util.safe_column(supp_index_row, 'EXPOSURE_DURATION')

    if exposure is None:
        return None

    return exposure

def populate_obs_general_NHLORRI_quantity_OBS(**kwargs):
    return 'REFLECT'

def populate_obs_general_NHLORRI_observation_type_OBS(**kwargs):
    return 'IMG' # Image

def populate_obs_pds_NHLORRI_note_OBS(**kwargs):
    metadata = kwargs['metadata']
    supp_index_row = metadata['supp_index_row']
    note = supp_index_row['OBSERVATION_DESC']
    if note == 'NULL':
        note = None
    return note

def populate_obs_general_NHLORRI_primary_filespec_OBS(**kwargs):
    return _NHLORRI_filespec_helper(**kwargs)

def populate_obs_pds_NHLORRI_primary_filespec_OBS(**kwargs):
    return _NHLORRI_filespec_helper(**kwargs)

def populate_obs_pds_NHLORRI_product_creation_time_OBS(**kwargs):
    return populate_product_creation_time_from_supp_index(**kwargs)

# Format: "NH-J-LORRI-2-JUPITER-V3.0"
def populate_obs_pds_NHLORRI_data_set_id_OBS(**kwargs):
    return populate_data_set_id_from_supp_index(**kwargs)

# Format: "LOR_0030598439_0X630_ENG"
def populate_obs_pds_NHLORRI_product_id_OBS(**kwargs):
    return populate_product_id_from_supp_index(**kwargs)

# We occasionally don't bother to generate ring_geo data for NHLORRI, like during
# cruise, so just use the given RA/DEC from the label if needed. We don't make
# any effort to figure out the min/max values.
def populate_obs_general_NHLORRI_right_asc1_OBS(**kwargs):
    metadata = kwargs['metadata']
    ring_geo_row = metadata.get('ring_geo_row', None)
    if ring_geo_row is not None:
        return import_util.safe_column(ring_geo_row, 'MINIMUM_RIGHT_ASCENSION')

    supp_index_row = metadata['supp_index_row']
    ra = import_util.safe_column(supp_index_row, 'RIGHT_ASCENSION')
    return ra

def populate_obs_general_NHLORRI_right_asc2_OBS(**kwargs):
    metadata = kwargs['metadata']
    ring_geo_row = metadata.get('ring_geo_row', None)
    if ring_geo_row is not None:
        return import_util.safe_column(ring_geo_row, 'MAXIMUM_RIGHT_ASCENSION')

    supp_index_row = metadata['supp_index_row']
    ra = import_util.safe_column(supp_index_row, 'RIGHT_ASCENSION')
    return ra

def populate_obs_general_NHLORRI_declination1_OBS(**kwargs):
    metadata = kwargs['metadata']
    ring_geo_row = metadata.get('ring_geo_row', None)
    if ring_geo_row is not None:
        return import_util.safe_column(ring_geo_row, 'MINIMUM_DECLINATION')

    supp_index_row = metadata['supp_index_row']
    dec = import_util.safe_column(supp_index_row, 'DECLINATION')
    return dec

def populate_obs_general_NHLORRI_declination2_OBS(**kwargs):
    metadata = kwargs['metadata']
    ring_geo_row = metadata.get('ring_geo_row', None)
    if ring_geo_row is not None:
        return import_util.safe_column(ring_geo_row, 'MAXIMUM_DECLINATION')

    supp_index_row = metadata['supp_index_row']
    dec = import_util.safe_column(supp_index_row, 'DECLINATION')
    return dec


### OBS_TYPE_IMAGE TABLE ###

def populate_obs_type_image_NHLORRI_image_type_id_OBS(**kwargs):
    return 'FRAM'

def populate_obs_type_image_NHLORRI_duration_OBS(**kwargs):
    metadata = kwargs['metadata']
    obs_general_row = metadata['obs_general_row']
    return obs_general_row['observation_duration']

def populate_obs_type_image_NHLORRI_levels_OBS(**kwargs):
    return 4096

def populate_obs_type_image_NHLORRI_lesser_pixel_size_OBS(**kwargs):
    return 1024

def populate_obs_type_image_NHLORRI_greater_pixel_size_OBS(**kwargs):
    return 1024


### OBS_WAVELENGTH TABLE ###

def populate_obs_wavelength_NHLORRI_wavelength1_OBS(**kwargs):
    return 0.35

def populate_obs_wavelength_NHLORRI_wavelength2_OBS(**kwargs):
    return 0.85

def populate_obs_wavelength_NHLORRI_wave_res1_OBS(**kwargs):
    return 0.5

def populate_obs_wavelength_NHLORRI_wave_res2_OBS(**kwargs):
    return 0.5

def populate_obs_wavelength_NHLORRI_wave_no1_OBS(**kwargs):
    metadata = kwargs['metadata']
    wavelength_row = metadata['obs_wavelength_row']
    return 10000 / wavelength_row['wavelength2'] # cm^-1

def populate_obs_wavelength_NHLORRI_wave_no2_OBS(**kwargs):
    metadata = kwargs['metadata']
    wavelength_row = metadata['obs_wavelength_row']
    return 10000 / wavelength_row['wavelength1'] # cm^-1

def populate_obs_wavelength_NHLORRI_wave_no_res1_OBS(**kwargs):
    metadata = kwargs['metadata']
    wl_row = metadata['obs_wavelength_row']
    wno1 = wl_row['wave_no1']
    wno2 = wl_row['wave_no2']
    if wno1 is None or wno2 is None:
        return None
    return wno2 - wno1

def populate_obs_wavelength_NHLORRI_wave_no_res2_OBS(**kwargs):
    metadata = kwargs['metadata']
    wl_row = metadata['obs_wavelength_row']
    wno1 = wl_row['wave_no1']
    wno2 = wl_row['wave_no2']
    if wno1 is None or wno2 is None:
        return None
    return wno2 - wno1

def populate_obs_wavelength_NHLORRI_spec_flag_OBS(**kwargs):
    return 'N'

def populate_obs_wavelength_NHLORRI_spec_size_OBS(**kwargs):
    return None

def populate_obs_wavelength_NHLORRI_polarization_type_OBS(**kwargs):
    return 'NONE'


### populate_obs_occultation TABLE ###

def populate_obs_occultation_NHLORRI_occ_type_OBS(**kwargs):
    return None

def populate_obs_occultation_NHLORRI_occ_dir_OBS(**kwargs):
    return None

def populate_obs_occultation_NHLORRI_body_occ_flag_OBS(**kwargs):
    return None

def populate_obs_occultation_NHLORRI_optical_depth_min_OBS(**kwargs):
    return None

def populate_obs_occultation_NHLORRI_optical_depth_max_OBS(**kwargs):
    return None

def populate_obs_occultation_NHLORRI_temporal_sampling_OBS(**kwargs):
    return None

def populate_obs_occultation_NHLORRI_quality_score_OBS(**kwargs):
    return None

def populate_obs_occultation_NHLORRI_wl_band_OBS(**kwargs):
    return None

def populate_obs_occultation_NHLORRI_source_OBS(**kwargs):
    return None

def populate_obs_occultation_NHLORRI_host_OBS(**kwargs):
    return None


################################################################################
# THESE NEED TO BE IMPLEMENTED FOR EVERY NEW HORIZONS INSTRUMENT
################################################################################



################################################################################
# THESE ARE SPECIFIC TO OBS_INSTRUMENT_NHLORRI
################################################################################
