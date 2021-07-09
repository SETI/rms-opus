################################################################################
# populate_obs_instrument_VGISS_obs.py
#
# Routines to populate fields specific to VGISS.
################################################################################

import pdsfile

import import_util

from populate_obs_mission_voyager import *
from populate_util import *


# Data from: https://pds-rings.seti.org/voyager/iss/inst_cat_wa1.html#inst_info
# (WL MIN, WL MAX)
_VGISS_FILTER_WAVELENGTHS = { # XXX
    'CLEAR':  (280, 640),
    'VIOLET': (350, 450),
    'GREEN':  (530, 640),
    'ORANGE': (590, 640),
    'SODIUM': (588, 590),
    'UV':     (280, 370),
    'BLUE':   (430, 530),
    'CH4_JS': (614, 624),
    'CH4_U':  (536, 546),
}


################################################################################
# THESE NEED TO BE IMPLEMENTED FOR EVERY INSTRUMENT
################################################################################

### OBS_GENERAL TABLE ###

def _VGISS_file_spec_helper(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    # Format: "DATA/C13854XX/C1385455_CALIB.LBL"
    file_spec = index_row['FILE_SPECIFICATION_NAME']
    volume_id = kwargs['volume_id']
    return volume_id + '/' + file_spec

def populate_obs_general_VGISS_opus_id_OBS(**kwargs):
    file_spec = _VGISS_file_spec_helper(**kwargs)
    pds_file = pdsfile.PdsFile.from_filespec(file_spec, fix_case=True)
    opus_id = pds_file.opus_id
    if not opus_id:
        import_util.log_nonrepeating_error(
            f'Unable to create OPUS_ID for FILE_SPEC "{file_spec}"')
        return file_spec.split('/')[-1]
    return opus_id

def populate_obs_general_VGISS_ring_obs_id_OBS(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    filename = index_row['PRODUCT_ID']
    image_num = filename[1:8]
    inst_host_num = index_row['INSTRUMENT_HOST_NAME'][-1]
    camera = index_row['INSTRUMENT_NAME'][0]
    planet = helper_voyager_planet_id(**kwargs)
    if planet is None:
        pl_str = ''
    else:
        pl_str = planet[0]

    return (pl_str + '_IMG_VG' + inst_host_num + '_ISS_' + image_num + '_'
            + camera)

# Format: "VOYAGER 1" or "VOYAGER 2"
def populate_obs_general_VGISS_inst_host_id_OBS(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    inst_host = index_row['INSTRUMENT_HOST_NAME']

    assert inst_host in ['VOYAGER 1', 'VOYAGER 2']

    return 'VG'+inst_host[-1]

def populate_obs_general_VGISS_time1_OBS(**kwargs):
    return populate_time1_from_supp_index(**kwargs)

def populate_obs_general_VGISS_time2_OBS(**kwargs):
    return populate_time2_from_supp_index(**kwargs)

def populate_obs_general_VGISS_target_name_OBS(**kwargs):
    return helper_voyager_target_name(**kwargs)

def populate_obs_general_VGISS_observation_duration_OBS(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    exposure = import_util.safe_column(index_row, 'EXPOSURE_DURATION')

    if exposure is None or exposure < 0:
        # There's one exposure somewhere that has duration -0.09999
        return None

    return exposure

def populate_obs_general_VGISS_quantity_OBS(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    filter_name = index_row['FILTER_NAME']

    if filter_name == 'UV':
        return 'EMISSION'
    return 'REFLECT'

def populate_obs_general_VGISS_observation_type_OBS(**kwargs):
    return 'IMG' # Image

def populate_obs_pds_VGISS_note_OBS(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    return index_row['NOTE']

def populate_obs_general_VGISS_primary_file_spec_OBS(**kwargs):
    return _VGISS_file_spec_helper(**kwargs)

def populate_obs_pds_VGISS_primary_file_spec_OBS(**kwargs):
    return _VGISS_file_spec_helper(**kwargs)

# Format: "VG1/VG2-J-ISS-2/3/4/6-PROCESSED-V1.0"
def populate_obs_pds_VGISS_data_set_id_OBS(**kwargs):
    return populate_data_set_id_from_index_label(**kwargs)

def populate_obs_pds_VGISS_product_creation_time_OBS(**kwargs):
    return populate_product_creation_time_from_supp_index(**kwargs)

# Format: "C1385455_CALIB.IMG"
def populate_obs_pds_VGISS_product_id_OBS(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    product_id = index_row['PRODUCT_ID']

    return product_id

def populate_obs_general_VGISS_right_asc1_OBS(**kwargs):
    metadata = kwargs['metadata']
    ring_geo_row = metadata.get('ring_geo_row', None)
    if ring_geo_row is not None:
        return import_util.safe_column(ring_geo_row, 'MINIMUM_RIGHT_ASCENSION')

    return None

def populate_obs_general_VGISS_right_asc2_OBS(**kwargs):
    metadata = kwargs['metadata']
    ring_geo_row = metadata.get('ring_geo_row', None)
    if ring_geo_row is not None:
        return import_util.safe_column(ring_geo_row, 'MAXIMUM_RIGHT_ASCENSION')

    return None

def populate_obs_general_VGISS_declination1_OBS(**kwargs):
    metadata = kwargs['metadata']
    ring_geo_row = metadata.get('ring_geo_row', None)
    if ring_geo_row is not None:
        return import_util.safe_column(ring_geo_row, 'MINIMUM_DECLINATION')

    return None

def populate_obs_general_VGISS_declination2_OBS(**kwargs):
    metadata = kwargs['metadata']
    ring_geo_row = metadata.get('ring_geo_row', None)
    if ring_geo_row is not None:
        return import_util.safe_column(ring_geo_row, 'MAXIMUM_DECLINATION')

    return None


### OBS_TYPE_IMAGE TABLE ###

def populate_obs_type_image_VGISS_image_type_id_OBS(**kwargs):
    return 'FRAM'

def populate_obs_type_image_VGISS_duration_OBS(**kwargs):
    metadata = kwargs['metadata']
    obs_general_row = metadata['obs_general_row']
    return obs_general_row['observation_duration']

def populate_obs_type_image_VGISS_levels_OBS(**kwargs):
    return 256

def _VGISS_pixel_size_helper(**kwargs):
    metadata = kwargs['metadata']
    supp_index_row = metadata['supp_index_row']
    if supp_index_row is None:
        return None, None
    line1 = supp_index_row['FIRST_LINE']
    line2 = supp_index_row['LAST_LINE']
    sample1 = supp_index_row['FIRST_SAMPLE']
    sample2 = supp_index_row['LAST_SAMPLE']

    return line2-line1+1, sample2-sample1+1

def populate_obs_type_image_VGISS_lesser_pixel_size_OBS(**kwargs):
    pix1, pix2 = _VGISS_pixel_size_helper(**kwargs)
    if pix1 is None or pix2 is None:
        return None
    return min(pix1, pix2)

def populate_obs_type_image_VGISS_greater_pixel_size_OBS(**kwargs):
    pix1, pix2 = _VGISS_pixel_size_helper(**kwargs)
    if pix1 is None or pix2 is None:
        return None
    return max(pix1, pix2)


### OBS_WAVELENGTH TABLE ###

def _wavelength_helper(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    filter_name = index_row['FILTER_NAME']

    if filter_name not in _VGISS_FILTER_WAVELENGTHS:
        import_util.log_nonrepeating_error(
            f'Unknown VGISS filter name "{filter_name}"')
        return 0

    return _VGISS_FILTER_WAVELENGTHS[filter_name]

def populate_obs_wavelength_VGISS_wavelength1_OBS(**kwargs):
    return _wavelength_helper(**kwargs)[0] / 1000 # microns

def populate_obs_wavelength_VGISS_wavelength2_OBS(**kwargs):
    return _wavelength_helper(**kwargs)[1] / 1000 # microns

def populate_obs_wavelength_VGISS_wave_res1_OBS(**kwargs):
    metadata = kwargs['metadata']
    wl_row = metadata['obs_wavelength_row']
    wl1 = wl_row['wavelength1']
    wl2 = wl_row['wavelength2']
    if wl1 is None or wl2 is None:
        return None
    return wl2 - wl1

def populate_obs_wavelength_VGISS_wave_res2_OBS(**kwargs):
    metadata = kwargs['metadata']
    wl_row = metadata['obs_wavelength_row']
    wl1 = wl_row['wavelength1']
    wl2 = wl_row['wavelength2']
    if wl1 is None or wl2 is None:
        return None
    return wl2 - wl1

def populate_obs_wavelength_VGISS_wave_no1_OBS(**kwargs):
    metadata = kwargs['metadata']
    wavelength_row = metadata['obs_wavelength_row']
    return 10000 / wavelength_row['wavelength2'] # cm^-1

def populate_obs_wavelength_VGISS_wave_no2_OBS(**kwargs):
    metadata = kwargs['metadata']
    wavelength_row = metadata['obs_wavelength_row']
    return 10000 / wavelength_row['wavelength1'] # cm^-1

def populate_obs_wavelength_VGISS_wave_no_res1_OBS(**kwargs):
    metadata = kwargs['metadata']
    wl_row = metadata['obs_wavelength_row']
    wno1 = wl_row['wave_no1']
    wno2 = wl_row['wave_no2']
    if wno1 is None or wno2 is None:
        return None
    return wno2 - wno1

def populate_obs_wavelength_VGISS_wave_no_res2_OBS(**kwargs):
    metadata = kwargs['metadata']
    wl_row = metadata['obs_wavelength_row']
    wno1 = wl_row['wave_no1']
    wno2 = wl_row['wave_no2']
    if wno1 is None or wno2 is None:
        return None
    return wno2 - wno1

def populate_obs_wavelength_VGISS_spec_flag_OBS(**kwargs):
    return 'N'

def populate_obs_wavelength_VGISS_spec_size_OBS(**kwargs):
    return None

def populate_obs_wavelength_VGISS_polarization_type_OBS(**kwargs):
    return 'NONE'


### populate_obs_occultation TABLE ###

def populate_obs_occultation_VGISS_occ_type_OBS(**kwargs):
    return None

def populate_obs_occultation_VGISS_occ_dir_OBS(**kwargs):
    return None

def populate_obs_occultation_VGISS_body_occ_flag_OBS(**kwargs):
    return None

def populate_obs_occultation_VGISS_optical_depth_min_OBS(**kwargs):
    return None

def populate_obs_occultation_VGISS_optical_depth_max_OBS(**kwargs):
    return None

def populate_obs_occultation_VGISS_temporal_sampling_OBS(**kwargs):
    return None

def populate_obs_occultation_VGISS_quality_score_OBS(**kwargs):
    return None

def populate_obs_occultation_VGISS_wl_band_OBS(**kwargs):
    return None

def populate_obs_occultation_VGISS_source_OBS(**kwargs):
    return None

def populate_obs_occultation_VGISS_host_OBS(**kwargs):
    return None


################################################################################
# THESE NEED TO BE IMPLEMENTED FOR EVERY VOYAGER INSTRUMENT
################################################################################

def populate_obs_mission_voyager_VGISS_mission_phase_name_OBS(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    mp = index_row['MISSION_PHASE_NAME'].upper()

    return mp


################################################################################
# THESE ARE SPECIFIC TO OBS_INSTRUMENT_VGISS
################################################################################

def populate_obs_instrument_vgiss_camera_OBS(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    camera = index_row['INSTRUMENT_NAME']

    assert camera in ['NARROW ANGLE CAMERA', 'WIDE ANGLE CAMERA']

    return camera[0]

def populate_obs_instrument_vgiss_usable_lines_OBS(**kwargs):
    metadata = kwargs['metadata']
    supp_index_row = metadata['supp_index_row']
    if supp_index_row is None:
        return None
    line1 = supp_index_row['FIRST_LINE']
    line2 = supp_index_row['LAST_LINE']

    return line2-line1+1

def populate_obs_instrument_vgiss_usable_samples_OBS(**kwargs):
    metadata = kwargs['metadata']
    supp_index_row = metadata['supp_index_row']
    if supp_index_row is None:
        return None
    sample1 = supp_index_row['FIRST_SAMPLE']
    sample2 = supp_index_row['LAST_SAMPLE']

    return sample2-sample1+1
