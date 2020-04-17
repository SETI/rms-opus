################################################################################
# populate_obs_instrument_GB_occ.py
#
# Routines to populate fields specific to ground-based instruments.
################################################################################

import numpy as np

import julian
import pdsfile

from config_data import *
import import_util

from populate_obs_mission_groundbased_occ import *
from populate_util import *


################################################################################
# THESE NEED TO BE IMPLEMENTED FOR EVERY INSTRUMENT
################################################################################

### OBS_GENERAL TABLE ###

def _GB_file_spec_helper(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata.get('index_row', None)
    if index_row is None:
        return None
    # Format: "/DATA/ESO1M/ES1_EPD.LBL"
    file_spec = index_row['FILE_SPECIFICATION_NAME']
    volume_id = kwargs['volume_id']
    return volume_id + file_spec

def populate_obs_general_GB_opus_id_OCC(**kwargs):
    file_spec = _GB_file_spec_helper(**kwargs)
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

def populate_obs_general_GB_ring_obs_id_OCC(**kwargs):
    return None

def populate_obs_general_GB_inst_host_id_OCC(**kwargs):
    return 'GB'

def populate_obs_general_GB_data_type_OCC(**kwargs):
    return 'OCC'

def populate_obs_general_GB_time1_OCC(**kwargs):
    return populate_time1_from_index(**kwargs)

def populate_obs_general_GB_time2_OCC(**kwargs):
    return populate_time2_from_index(**kwargs)

def populate_obs_general_GB_target_name_OCC(**kwargs):
    return helper_earthbased_target_name(**kwargs)

def populate_obs_general_GB_observation_duration_OCC(**kwargs):
    return populate_observation_duration_from_time(**kwargs)

def populate_obs_general_GB_quantity_OCC(**kwargs):
    return 'OPDEPTH'

def populate_obs_general_GB_observation_type_OCC(**kwargs):
    return 'OCC'

def populate_obs_pds_GB_note_OCC(**kwargs):
    return None

def populate_obs_general_GB_primary_file_spec_OCC(**kwargs):
    return _GB_file_spec_helper(**kwargs)

def populate_obs_pds_GB_primary_file_spec_OCC(**kwargs):
    return _GB_file_spec_helper(**kwargs)

def populate_obs_pds_GB_product_creation_time_OCC(**kwargs):
    return populate_product_creation_time_from_index(**kwargs)

# Format: "ESO1M-SR-APPH-4-OCC-V1.0"
def populate_obs_pds_GB_data_set_id_OCC(**kwargs):
    return populate_data_set_id_from_index_label(**kwargs)

# Format: "ES1_EGRESS"
def populate_obs_pds_GB_product_id_OCC(**kwargs):
    return populate_product_id_from_index(**kwargs)

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

def populate_obs_general_GB_right_asc1_OCC(**kwargs):
    return _ra_dec_helper(**kwargs)[0]

def populate_obs_general_GB_right_asc2_OCC(**kwargs):
    return _ra_dec_helper(**kwargs)[0]

def populate_obs_general_GB_declination1_OCC(**kwargs):
    return _ra_dec_helper(**kwargs)[1]

def populate_obs_general_GB_declination2_OCC(**kwargs):
    return _ra_dec_helper(**kwargs)[1]


### OBS_TYPE_IMAGE TABLE ###

def populate_obs_type_image_GB_image_type_id_OCC(**kwargs):
    return None

def populate_obs_type_image_GB_duration_OCC(**kwargs):
    return None

def populate_obs_type_image_GB_levels_OCC(**kwargs):
    return None

def populate_obs_type_image_GB_lesser_pixel_size_OCC(**kwargs):
    return None

def populate_obs_type_image_GB_greater_pixel_size_OCC(**kwargs):
    return None


### OBS_WAVELENGTH TABLE ###

def populate_obs_wavelength_GB_wavelength1_OCC(**kwargs):
    metadata = kwargs['metadata']
    index_label = metadata['index_label']
    wl = index_label['WAVELENGTH'] # microns

    return wl

def populate_obs_wavelength_GB_wavelength2_OCC(**kwargs):
    metadata = kwargs['metadata']
    index_label = metadata['index_label']
    wl = index_label['WAVELENGTH'] # microns

    return wl

def populate_obs_wavelength_GB_wave_res1_OCC(**kwargs):
    return None # Not available

def populate_obs_wavelength_GB_wave_res2_OCC(**kwargs):
    return None # Not available

def populate_obs_wavelength_GB_wave_no1_OCC(**kwargs):
    metadata = kwargs['metadata']
    index_label = metadata['index_label']
    wl = index_label['WAVELENGTH'] # microns

    return 10000 / wl # cm^-1

def populate_obs_wavelength_GB_wave_no2_OCC(**kwargs):
    metadata = kwargs['metadata']
    index_label = metadata['index_label']
    wl = index_label['WAVELENGTH'] # microns

    return 10000 / wl # cm^-1

def populate_obs_wavelength_GB_wave_no_res1_OCC(**kwargs):
    return None # Not available

def populate_obs_wavelength_GB_wave_no_res2_OCC(**kwargs):
    return None # Not available

def populate_obs_wavelength_GB_spec_flag_OCC(**kwargs):
    return 'N'

def populate_obs_wavelength_GB_spec_size_OCC(**kwargs):
    return None

def populate_obs_wavelength_GB_polarization_type_OCC(**kwargs):
    return 'NONE'


### OBS_OCCULTATION TABLE ###

def populate_obs_occultation_GB_occ_type_OCC(**kwargs):
    metadata = kwargs['metadata']
    index_label = metadata['index_label']
    star_name = index_label['STAR_NAME']

    if star_name == 'SUN':
        return 'SOL'
    return 'STE'

def populate_obs_occultation_GB_occ_dir_OCC(**kwargs):
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

def populate_obs_occultation_GB_body_occ_flag_OCC(**kwargs):
    metadata = kwargs['metadata']
    supp_index_row = metadata['supp_index_row']
    body_occ_flag = supp_index_row['PLANETARY_OCCULTATION_FLAG']

    return body_occ_flag

def populate_obs_occultation_GB_optical_depth_min_OCC(**kwargs):
    return None # Not available

def populate_obs_occultation_GB_optical_depth_max_OCC(**kwargs):
    return None # Not available

def populate_obs_occultation_GB_temporal_sampling_OCC(**kwargs):
    return None # Not available

def populate_obs_occultation_GB_quality_score_OCC(**kwargs):
    return ("UNASSIGNED", "Unassigned")

def populate_obs_occultation_GB_wl_band_OCC(**kwargs):
    metadata = kwargs['metadata']
    index_label = metadata['index_label']
    wl = index_label['WAVELENGTH'] # microns

    if wl > 0.7:
        return 'IR'
    if wl > 0.4:
        return 'VIS'
    return 'UV'

def populate_obs_occultation_GB_source_OCC(**kwargs):
    metadata = kwargs['metadata']
    index_label = metadata['index_label']
    star_name = index_label['STAR_NAME']

    return star_name

def populate_obs_occultation_GB_host_OCC(**kwargs):
    metadata = kwargs['metadata']
    supp_index_row = metadata['supp_index_label']
    insthost = supp_index_row['INSTRUMENT_HOST_NAME']

    return (insthost, insthost)


### OBS_RING_GEOMETRY TABLE ###

def populate_obs_ring_geometry_GB_ring_radius1_OCC(**kwargs):
    metadata = kwargs['metadata']
    supp_index_row = metadata['supp_index_row']
    radius1 = import_util.safe_column(supp_index_row, 'MINIMUM_RING_RADIUS')

    return radius1

def populate_obs_ring_geometry_GB_ring_radius2_OCC(**kwargs):
    metadata = kwargs['metadata']
    supp_index_row = metadata['supp_index_row']
    radius2 = import_util.safe_column(supp_index_row, 'MAXIMUM_RING_RADIUS')

    return radius2

def populate_obs_ring_geometry_GB_resolution1_OCC(**kwargs):
    metadata = kwargs['metadata']
    supp_index_row = metadata['supp_index_row']
    res = import_util.safe_column(supp_index_row, 'RADIAL_RESOLUTION')

    return res

def populate_obs_ring_geometry_GB_resolution2_OCC(**kwargs):
    metadata = kwargs['metadata']
    supp_index_row = metadata['supp_index_row']
    res = import_util.safe_column(supp_index_row, 'RADIAL_RESOLUTION')

    return res

def populate_obs_ring_geometry_GB_proj_resolution1_OCC(**kwargs):
    metadata = kwargs['metadata']
    supp_index_row = metadata['supp_index_row']
    res = import_util.safe_column(supp_index_row, 'RADIAL_RESOLUTION')

    return res

def populate_obs_ring_geometry_GB_proj_resolution2_OCC(**kwargs):
    metadata = kwargs['metadata']
    supp_index_row = metadata['supp_index_row']
    res = import_util.safe_column(supp_index_row, 'RADIAL_RESOLUTION')

    return res

def populate_obs_ring_geometry_GB_phase1_OCC(**kwargs):
    return 180.

def populate_obs_ring_geometry_GB_phase2_OCC(**kwargs):
    return 180.

def populate_obs_ring_geometry_GB_incidence1_OCC(**kwargs):
    metadata = kwargs['metadata']
    supp_index_row = metadata['supp_index_row']
    inc = import_util.safe_column(supp_index_row, 'INCIDENCE_ANGLE')

    return inc

def populate_obs_ring_geometry_GB_incidence2_OCC(**kwargs):
    metadata = kwargs['metadata']
    supp_index_row = metadata['supp_index_row']
    inc = import_util.safe_column(supp_index_row, 'INCIDENCE_ANGLE')

    return inc

def populate_obs_ring_geometry_GB_center_phase_OCC(**kwargs):
    return 180.

def populate_obs_ring_geometry_GB_center_incidence_OCC(**kwargs):
    metadata = kwargs['metadata']
    supp_index_row = metadata['supp_index_row']
    inc = import_util.safe_column(supp_index_row, 'INCIDENCE_ANGLE')

    return inc


################################################################################
# THESE NEED TO BE IMPLEMENTED FOR EVERY GROUND-BASED INSTRUMENT
################################################################################



################################################################################
# THESE ARE SPECIFIC TO OBS_INSTRUMENT_EB
################################################################################
