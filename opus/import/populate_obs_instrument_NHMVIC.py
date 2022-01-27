################################################################################
# populate_obs_instrument_NHMVIC.py
#
# Routines to populate fields specific to NHMVIC.
################################################################################

import pdsfile

import import_util

from populate_obs_mission_new_horizons import *
from populate_util import *


################################################################################
# THESE NEED TO BE IMPLEMENTED FOR EVERY INSTRUMENT
################################################################################

### OBS_GENERAL TABLE ###

def _NHMVIC_filespec_helper(**kwargs):
    metadata = kwargs['metadata']
    supp_index_row = metadata['supp_index_row']
    # Format: "data/20070108_003059/mc0_0030598439_0x630_eng_1.lbl"
    filespec = supp_index_row['FILE_SPECIFICATION_NAME']
    volume_id = kwargs['volume_id']
    return volume_id + '/' + filespec

def populate_obs_general_NHMVIC_opus_id_OBS(**kwargs):
    filespec = _NHMVIC_filespec_helper(**kwargs)
    pds_file = pdsfile.PdsFile.from_filespec(filespec, fix_case=True)
    opus_id = pds_file.opus_id
    if not opus_id:
        import_util.log_nonrepeating_error(
            f'Unable to create OPUS_ID for FILE_SPEC "{filespec}"')
        return filespec.split('/')[-1]
    return opus_id

def populate_obs_general_NHMVIC_ring_obs_id_OBS(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    image_num = index_row['FILE_NAME'][4:14]
    camera = index_row['FILE_NAME'][:3].upper()
    # This is really dumb, but it's what the old OPUS did so we do it for
    # backwards compatability
    start_time = index_row['START_TIME']
    if start_time > '2007-09-01':
        pl_str = 'P'
    else:
        pl_str = 'J'

    return pl_str + '_IMG_NH_MVIC_' + image_num + '_' + camera

def populate_obs_general_NHMVIC_inst_host_id_OBS(**kwargs):
    return 'NH'

def populate_obs_general_NHMVIC_time1_OBS(**kwargs):
    return populate_time1_from_index(**kwargs)

def populate_obs_general_NHMVIC_time2_OBS(**kwargs):
    return populate_time2_from_index(**kwargs)

def populate_obs_general_NHMVIC_target_name_OBS(**kwargs):
    target_name = helper_new_horizons_target_name(**kwargs)
    if target_name is None:
        target_name = 'NONE'
    return target_name

def populate_obs_general_NHMVIC_observation_duration_OBS(**kwargs):
    metadata = kwargs['metadata']
    supp_index_row = metadata['supp_index_row']
    exposure = import_util.safe_column(supp_index_row, 'EXPOSURE_DURATION')

    if exposure is None:
        return None

    return exposure

def populate_obs_general_NHMVIC_quantity_OBS(**kwargs):
    return 'REFLECT'

def populate_obs_general_NHMVIC_observation_type_OBS(**kwargs):
    return 'IMG' # Image

def populate_obs_pds_NHMVIC_note_OBS(**kwargs):
    metadata = kwargs['metadata']
    supp_index_row = metadata['supp_index_row']
    note = supp_index_row['OBSERVATION_DESC']
    if note == 'NULL':
        note = None
    return note

def populate_obs_general_NHMVIC_primary_filespec_OBS(**kwargs):
    return _NHMVIC_filespec_helper(**kwargs)

def populate_obs_pds_NHMVIC_primary_filespec_OBS(**kwargs):
    return _NHMVIC_filespec_helper(**kwargs)

def populate_obs_pds_NHMVIC_product_creation_time_OBS(**kwargs):
    return populate_product_creation_time_from_supp_index(**kwargs)

# Format: "NH-J-MVIC-2-JUPITER-V2.0"
def populate_obs_pds_NHMVIC_data_set_id_OBS(**kwargs):
    return populate_data_set_id_from_supp_index(**kwargs)

# Format: "MC0_0032528036_0X536_ENG_1"
def populate_obs_pds_NHMVIC_product_id_OBS(**kwargs):
    return populate_product_id_from_supp_index(**kwargs)

# We occasionally don't bother to generate ring_geo data for NHMVIC, like during
# cruise, so just use the given RA/DEC from the label if needed. We don't make
# any effort to figure out the min/max values.
def populate_obs_general_NHMVIC_right_asc1_OBS(**kwargs):
    metadata = kwargs['metadata']
    ring_geo_row = metadata.get('ring_geo_row', None)
    if ring_geo_row is not None:
        return import_util.safe_column(ring_geo_row, 'MINIMUM_RIGHT_ASCENSION')

    supp_index_row = metadata['supp_index_row']
    ra = import_util.safe_column(supp_index_row, 'RIGHT_ASCENSION')
    return ra

def populate_obs_general_NHMVIC_right_asc2_OBS(**kwargs):
    metadata = kwargs['metadata']
    ring_geo_row = metadata.get('ring_geo_row', None)
    if ring_geo_row is not None:
        return import_util.safe_column(ring_geo_row, 'MAXIMUM_RIGHT_ASCENSION')

    supp_index_row = metadata['supp_index_row']
    ra = import_util.safe_column(supp_index_row, 'RIGHT_ASCENSION')
    return ra

def populate_obs_general_NHMVIC_declination1_OBS(**kwargs):
    metadata = kwargs['metadata']
    ring_geo_row = metadata.get('ring_geo_row', None)
    if ring_geo_row is not None:
        return import_util.safe_column(ring_geo_row, 'MINIMUM_DECLINATION')

    supp_index_row = metadata['supp_index_row']
    dec = import_util.safe_column(supp_index_row, 'DECLINATION')
    return dec

def populate_obs_general_NHMVIC_declination2_OBS(**kwargs):
    metadata = kwargs['metadata']
    ring_geo_row = metadata.get('ring_geo_row', None)
    if ring_geo_row is not None:
        return import_util.safe_column(ring_geo_row, 'MAXIMUM_DECLINATION')

    supp_index_row = metadata['supp_index_row']
    dec = import_util.safe_column(supp_index_row, 'DECLINATION')
    return dec


### OBS_TYPE_IMAGE TABLE ###

def populate_obs_type_image_NHMVIC_image_type_id_OBS(**kwargs):
    return 'PUSH'

def populate_obs_type_image_NHMVIC_duration_OBS(**kwargs):
    metadata = kwargs['metadata']
    obs_general_row = metadata['obs_general_row']
    return obs_general_row['observation_duration']

def populate_obs_type_image_NHMVIC_levels_OBS(**kwargs):
    return 4096

def populate_obs_type_image_NHMVIC_lesser_pixel_size_OBS(**kwargs):
    return 128

def populate_obs_type_image_NHMVIC_greater_pixel_size_OBS(**kwargs):
    return 5024


### OBS_WAVELENGTH TABLE ###

def populate_obs_wavelength_NHMVIC_wavelength1_OBS(**kwargs):
    return 0.4

def populate_obs_wavelength_NHMVIC_wavelength2_OBS(**kwargs):
    return 0.975

def populate_obs_wavelength_NHMVIC_wave_res1_OBS(**kwargs):
    return 0.575

def populate_obs_wavelength_NHMVIC_wave_res2_OBS(**kwargs):
    return 0.575

def populate_obs_wavelength_NHMVIC_wave_no1_OBS(**kwargs):
    metadata = kwargs['metadata']
    wavelength_row = metadata['obs_wavelength_row']
    return 10000 / wavelength_row['wavelength2'] # cm^-1

def populate_obs_wavelength_NHMVIC_wave_no2_OBS(**kwargs):
    metadata = kwargs['metadata']
    wavelength_row = metadata['obs_wavelength_row']
    return 10000 / wavelength_row['wavelength1'] # cm^-1

def populate_obs_wavelength_NHMVIC_wave_no_res1_OBS(**kwargs):
    metadata = kwargs['metadata']
    wl_row = metadata['obs_wavelength_row']
    wno1 = wl_row['wave_no1']
    wno2 = wl_row['wave_no2']
    if wno1 is None or wno2 is None:
        return None
    return wno2 - wno1

def populate_obs_wavelength_NHMVIC_wave_no_res2_OBS(**kwargs):
    metadata = kwargs['metadata']
    wl_row = metadata['obs_wavelength_row']
    wno1 = wl_row['wave_no1']
    wno2 = wl_row['wave_no2']
    if wno1 is None or wno2 is None:
        return None
    return wno2 - wno1

def populate_obs_wavelength_NHMVIC_spec_flag_OBS(**kwargs):
    return 'N'

def populate_obs_wavelength_NHMVIC_spec_size_OBS(**kwargs):
    return None

def populate_obs_wavelength_NHMVIC_polarization_type_OBS(**kwargs):
    return 'NONE'


### populate_obs_occultation TABLE ###

def populate_obs_occultation_NHMVIC_occ_type_OBS(**kwargs):
    return None

def populate_obs_occultation_NHMVIC_occ_dir_OBS(**kwargs):
    return None

def populate_obs_occultation_NHMVIC_body_occ_flag_OBS(**kwargs):
    return None

def populate_obs_occultation_NHMVIC_optical_depth_min_OBS(**kwargs):
    return None

def populate_obs_occultation_NHMVIC_optical_depth_max_OBS(**kwargs):
    return None

def populate_obs_occultation_NHMVIC_temporal_sampling_OBS(**kwargs):
    return None

def populate_obs_occultation_NHMVIC_quality_score_OBS(**kwargs):
    return None

def populate_obs_occultation_NHMVIC_wl_band_OBS(**kwargs):
    return None

def populate_obs_occultation_NHMVIC_source_OBS(**kwargs):
    return None

def populate_obs_occultation_NHMVIC_host_OBS(**kwargs):
    return None


################################################################################
# THESE NEED TO BE IMPLEMENTED FOR EVERY NEW HORIZONS INSTRUMENT
################################################################################



################################################################################
# THESE ARE SPECIFIC TO OBS_INSTRUMENT_NHMVIC
################################################################################
