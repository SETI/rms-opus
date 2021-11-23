################################################################################
# populate_obs_instrument_COVIMS_occ.py
#
# Routines to populate fields specific to COVIMS.
################################################################################

import pdsfile

from config_data import *
import import_util

from populate_obs_mission_cassini import *
from populate_util import *


################################################################################
# THESE NEED TO BE IMPLEMENTED FOR EVERY INSTRUMENT
################################################################################

### OBS_GENERAL TABLE ###

def _COVIMS_file_spec_helper(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    # Format: "DATA/VIMS_2005_144_OMICET_E_TAU_01KM.LBL"
    file_spec = index_row['FILE_SPECIFICATION_NAME']
    volume_id = kwargs['volume_id']
    return volume_id + '/' + file_spec

def populate_obs_general_COVIMS_opus_id_PROF(**kwargs):
    file_spec = _COVIMS_file_spec_helper(**kwargs)
    pds_file = pdsfile.PdsFile.from_filespec(file_spec, fix_case=True)
    opus_id = pds_file.opus_id
    if not opus_id:
        import_util.log_nonrepeating_error(
            f'Unable to create OPUS_ID for FILE_SPEC "{file_spec}"')
        return file_spec.split('/')[-1]

    return opus_id

def populate_obs_general_COVIMS_ring_obs_id_PROF(**kwargs):
    return None

def populate_obs_general_COVIMS_inst_host_id_PROF(**kwargs):
    return 'CO'

# COVIMS time span is the duration of the observation at the spacecraft
def populate_obs_general_COVIMS_time1_PROF(**kwargs):
    return populate_time1_from_supp_index(**kwargs)

def populate_obs_general_COVIMS_time2_PROF(**kwargs):
    return populate_time2_from_supp_index(**kwargs)

def populate_obs_general_COVIMS_target_name_PROF(**kwargs):
    target_name = 'S RINGS'
    target_name_info = TARGET_NAME_INFO[target_name]
    return target_name, target_name_info[2]

def populate_obs_general_COVIMS_observation_duration_PROF(**kwargs):
    return populate_observation_duration_from_time(**kwargs)

def populate_obs_general_COVIMS_quantity_PROF(**kwargs):
    return 'OPDEPTH'

def populate_obs_general_COVIMS_observation_type_PROF(**kwargs):
    return 'OCC'

def populate_obs_pds_COVIMS_note_PROF(**kwargs):
    metadata = kwargs['metadata']
    supp_index_row = metadata['supp_index_row']
    dq_score = supp_index_row['DATA_QUALITY_SCORE']
    return 'Data quality ' + dq_score.lower()

def populate_obs_general_COVIMS_primary_file_spec_PROF(**kwargs):
    return _COVIMS_file_spec_helper(**kwargs)

def populate_obs_pds_COVIMS_primary_file_spec_PROF(**kwargs):
    return _COVIMS_file_spec_helper(**kwargs)

def populate_obs_pds_COVIMS_product_creation_time_PROF(**kwargs):
    return populate_product_creation_time_from_supp_index(**kwargs)

# Format: "CO-SR-VIMS-HSP-2/4-OCC-V2.0"
def populate_obs_pds_COVIMS_data_set_id_PROF(**kwargs):
    return populate_data_set_id_from_index_label(**kwargs)

# Format: "VIMS_HSP_2004_280_XI2CET_E_TAU01KM.TAB"
def populate_obs_pds_COVIMS_product_id_PROF(**kwargs):
    return populate_product_id_from_index(**kwargs)

def populate_obs_general_COVIMS_right_asc1_PROF(**kwargs):
    return populate_occ_ra_dec_helper_index(**kwargs)[0]

def populate_obs_general_COVIMS_right_asc2_PROF(**kwargs):
    return populate_occ_ra_dec_helper_index(**kwargs)[1]

def populate_obs_general_COVIMS_declination1_PROF(**kwargs):
    return populate_occ_ra_dec_helper_index(**kwargs)[2]

def populate_obs_general_COVIMS_declination2_PROF(**kwargs):
    return populate_occ_ra_dec_helper_index(**kwargs)[3]


### OBS_TYPE_IMAGE TABLE ###

def populate_obs_type_image_COVIMS_image_type_id_PROF(**kwargs):
    return None

def populate_obs_type_image_COVIMS_duration_PROF(**kwargs):
    return None

def populate_obs_type_image_COVIMS_levels_PROF(**kwargs):
    return None

def populate_obs_type_image_COVIMS_lesser_pixel_size_PROF(**kwargs):
    return None

def populate_obs_type_image_COVIMS_greater_pixel_size_PROF(**kwargs):
    return None


### OBS_WAVELENGTH TABLE ###

def populate_obs_wavelength_COVIMS_wavelength1_PROF(**kwargs):
    return 0.8842

def populate_obs_wavelength_COVIMS_wavelength2_PROF(**kwargs):
    return 5.1225

def _wave_res_helper(**kwargs):
    metadata = kwargs['metadata']
    wl_row = metadata['obs_wavelength_row']
    wl1 = wl_row['wavelength1']
    wl2 = wl_row['wavelength2']
    if wl1 is None or wl2 is None:
        return None
    return wl2 - wl1

def populate_obs_wavelength_COVIMS_wave_res1_PROF(**kwargs):
    return 0.01662

def populate_obs_wavelength_COVIMS_wave_res2_PROF(**kwargs):
    return 0.01662

def populate_obs_wavelength_COVIMS_wave_no1_PROF(**kwargs):
    metadata = kwargs['metadata']
    wavelength_row = metadata['obs_wavelength_row']
    return 10000 / wavelength_row['wavelength2'] # cm^-1

def populate_obs_wavelength_COVIMS_wave_no2_PROF(**kwargs):
    metadata = kwargs['metadata']
    wavelength_row = metadata['obs_wavelength_row']
    return 10000 / wavelength_row['wavelength1'] # cm^-1

def populate_obs_wavelength_COVIMS_wave_no_res1_PROF(**kwargs):
    metadata = kwargs['metadata']
    wl_row = metadata['obs_wavelength_row']
    wave_res2 = wl_row['wave_res2']
    wl2 = wl_row['wavelength2']

    if wave_res2 is None or wl2 is None:
        return None

    return wave_res2 * 10000. / (wl2*wl2)

def populate_obs_wavelength_COVIMS_wave_no_res2_PROF(**kwargs):
    metadata = kwargs['metadata']
    wl_row = metadata['obs_wavelength_row']
    wave_res1 = wl_row['wave_res1']
    wl1 = wl_row['wavelength1']

    if wave_res1 is None or wl1 is None:
        return None

    return wave_res1 * 10000. / (wl1*wl1)

def populate_obs_wavelength_COVIMS_spec_flag_PROF(**kwargs):
    return 'Y'

def populate_obs_wavelength_COVIMS_spec_size_PROF(**kwargs):
    return 256

def populate_obs_wavelength_COVIMS_polarization_type_PROF(**kwargs):
    return 'NONE'


### populate_obs_occultation TABLE ###

def populate_obs_occultation_COVIMS_occ_type_PROF(**kwargs):
    return 'STE' # There are no SUN occultations

def populate_obs_occultation_COVIMS_occ_dir_PROF(**kwargs):
    filespec = _COVIMS_file_spec_helper(**kwargs)

    # We don't allow "Both" as a direction since these are always split into
    # separate files.
    if '_I_' in filespec:
        return 'I'
    if '_E_' in filespec:
        return 'E'
    import_util.log_nonrepeating_error(
        f'Unknown ring occultation direction in filespec "{filespec}"')
    return None

def populate_obs_occultation_COVIMS_body_occ_flag_PROF(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    body_occ_flag = index_row['PLANETARY_OCCULTATION_FLAG']

    return body_occ_flag

def populate_obs_occultation_COVIMS_optical_depth_min_PROF(**kwargs):
    metadata = kwargs['metadata']
    supp_index_row = metadata['supp_index_row']
    opac = import_util.safe_column(supp_index_row, 'LOWEST_DETECTABLE_OPACITY')

    return opac

def populate_obs_occultation_COVIMS_optical_depth_max_PROF(**kwargs):
    metadata = kwargs['metadata']
    supp_index_row = metadata['supp_index_row']
    opac = import_util.safe_column(supp_index_row, 'HIGHEST_DETECTABLE_OPACITY')

    return opac

def _integration_duration_helper(**kwargs):
    metadata = kwargs['metadata']
    supp_index_row = metadata['supp_index_row']
    dur = supp_index_row['IR_EXPOSURE']

    return dur/1000

def populate_obs_occultation_COVIMS_temporal_sampling_PROF(**kwargs):
    return _integration_duration_helper(**kwargs)

def populate_obs_occultation_COVIMS_quality_score_PROF(**kwargs):
    metadata = kwargs['metadata']
    supp_index_row = metadata['supp_index_row']
    dq_score = supp_index_row['DATA_QUALITY_SCORE']

    return dq_score

def populate_obs_occultation_COVIMS_wl_band_PROF(**kwargs):
    return 'IR'

def populate_obs_occultation_COVIMS_source_PROF(**kwargs):
    target_name, target_name_info = populate_star_name_helper_index(**kwargs)
    if target_name_info is None:
        return None
    return target_name, target_name_info[2]

def populate_obs_occultation_COVIMS_host_PROF(**kwargs):
    return 'Cassini'


### OBS_RING_GEOMETRY TABLE ###

def populate_obs_ring_geometry_COVIMS_ring_radius1_PROF(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    radius1 = import_util.safe_column(index_row, 'MINIMUM_RING_RADIUS')

    return radius1

def populate_obs_ring_geometry_COVIMS_ring_radius2_PROF(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    radius2 = import_util.safe_column(index_row, 'MAXIMUM_RING_RADIUS')

    return radius2

def populate_obs_ring_geometry_COVIMS_resolution1_PROF(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    res = import_util.safe_column(index_row, 'RADIAL_RESOLUTION')

    return res

def populate_obs_ring_geometry_COVIMS_resolution2_PROF(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    res = import_util.safe_column(index_row, 'RADIAL_RESOLUTION')

    return res

def populate_obs_ring_geometry_COVIMS_proj_resolution1_PROF(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    res = import_util.safe_column(index_row, 'RADIAL_RESOLUTION')

    return res

def populate_obs_ring_geometry_COVIMS_proj_resolution2_PROF(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    res = import_util.safe_column(index_row, 'RADIAL_RESOLUTION')

    return res

def populate_obs_ring_geometry_COVIMS_j2000_longitude1_PROF(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    long1 = import_util.safe_column(index_row, 'MINIMUM_RING_LONGITUDE')

    return long1

def populate_obs_ring_geometry_COVIMS_j2000_longitude2_PROF(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    long2 = import_util.safe_column(index_row, 'MAXIMUM_RING_LONGITUDE')

    return long2

def populate_obs_ring_geometry_COVIMS_ring_azimuth_wrt_observer1_PROF(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    az1 = import_util.safe_column(index_row, 'MINIMUM_OBSERVED_RING_AZIMUTH')

    return az1

def populate_obs_ring_geometry_COVIMS_ring_azimuth_wrt_observer2_PROF(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    az2 = import_util.safe_column(index_row, 'MAXIMUM_OBSERVED_RING_AZIMUTH')

    return az2

def populate_obs_ring_geometry_COVIMS_phase1_PROF(**kwargs):
    return 180.

def populate_obs_ring_geometry_COVIMS_phase2_PROF(**kwargs):
    return 180.

def populate_obs_ring_geometry_COVIMS_incidence1_PROF(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    el = index_row['OBSERVED_RING_ELEVATION']

    return 90. - abs(el)

def populate_obs_ring_geometry_COVIMS_incidence2_PROF(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    el = index_row['OBSERVED_RING_ELEVATION']

    return 90. - abs(el)

def populate_obs_ring_geometry_COVIMS_north_based_incidence1_PROF(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    el = index_row['OBSERVED_RING_ELEVATION']

    return 90. + el

def populate_obs_ring_geometry_COVIMS_north_based_incidence2_PROF(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    el = index_row['OBSERVED_RING_ELEVATION']

    return 90. + el

def populate_obs_ring_geometry_COVIMS_emission1_PROF(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    el = index_row['OBSERVED_RING_ELEVATION']

    return 90. + abs(el)

def populate_obs_ring_geometry_COVIMS_emission2_PROF(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    el = index_row['OBSERVED_RING_ELEVATION']

    return 90. + abs(el)

def populate_obs_ring_geometry_COVIMS_north_based_emission1_PROF(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    el = index_row['OBSERVED_RING_ELEVATION']

    return 90. - el

def populate_obs_ring_geometry_COVIMS_north_based_emission2_PROF(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    el = index_row['OBSERVED_RING_ELEVATION']

    return 90. - el

# We set the center versions to be the same as the normal versions
populate_obs_ring_geometry_COVIMS_center_phase1_PROF = \
    populate_obs_ring_geometry_COVIMS_phase1_PROF
populate_obs_ring_geometry_COVIMS_center_phase2_PROF = \
    populate_obs_ring_geometry_COVIMS_phase2_PROF
populate_obs_ring_geometry_COVIMS_center_incidence1_PROF = \
    populate_obs_ring_geometry_COVIMS_incidence1_PROF
populate_obs_ring_geometry_COVIMS_center_incidence2_PROF = \
    populate_obs_ring_geometry_COVIMS_incidence2_PROF
populate_obs_ring_geometry_COVIMS_center_emission1_PROF = \
    populate_obs_ring_geometry_COVIMS_emission1_PROF
populate_obs_ring_geometry_COVIMS_center_emission2_PROF = \
    populate_obs_ring_geometry_COVIMS_emission2_PROF
populate_obs_ring_geometry_COVIMS_center_north_based_incidence1_PROF = \
    populate_obs_ring_geometry_COVIMS_north_based_incidence1_PROF
populate_obs_ring_geometry_COVIMS_center_north_based_incidence2_PROF = \
    populate_obs_ring_geometry_COVIMS_north_based_incidence2_PROF
populate_obs_ring_geometry_COVIMS_center_north_based_emission1_PROF = \
    populate_obs_ring_geometry_COVIMS_north_based_emission1_PROF
populate_obs_ring_geometry_COVIMS_center_north_based_emission2_PROF = \
    populate_obs_ring_geometry_COVIMS_north_based_emission2_PROF

def populate_obs_ring_geometry_COVIMS_observer_ring_opening_angle1_PROF(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    el = index_row['OBSERVED_RING_ELEVATION']

    return el

def populate_obs_ring_geometry_COVIMS_observer_ring_opening_angle2_PROF(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    el = index_row['OBSERVED_RING_ELEVATION']

    return el

def populate_obs_ring_geometry_COVIMS_observer_ring_elevation1_PROF(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    el = index_row['OBSERVED_RING_ELEVATION']

    return el

def populate_obs_ring_geometry_COVIMS_observer_ring_elevation2_PROF(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    el = index_row['OBSERVED_RING_ELEVATION']

    return el

def populate_obs_ring_geometry_COVIMS_solar_ring_opening_angle1_PROF(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    el = index_row['OBSERVED_RING_ELEVATION']

    return -el

def populate_obs_ring_geometry_COVIMS_solar_ring_opening_angle2_PROF(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    el = index_row['OBSERVED_RING_ELEVATION']

    return -el

def populate_obs_ring_geometry_COVIMS_solar_ring_elevation1_PROF(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    el = index_row['OBSERVED_RING_ELEVATION']

    return -el

def populate_obs_ring_geometry_COVIMS_solar_ring_elevation2_PROF(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    el = index_row['OBSERVED_RING_ELEVATION']

    return -el

def populate_obs_ring_geometry_COVIMS_ring_intercept_time1_PROF(**kwargs):
    return populate_time1_from_index(column='RING_EVENT_START_TIME', **kwargs)

def populate_obs_ring_geometry_COVIMS_ring_intercept_time2_PROF(**kwargs):
    return populate_time1_from_index(column='RING_EVENT_STOP_TIME', **kwargs)


################################################################################
# THESE NEED TO BE IMPLEMENTED FOR EVERY CASSINI INSTRUMENT
################################################################################

def populate_obs_mission_cassini_COVIMS_ert1_PROF(**kwargs):
    return None

def populate_obs_mission_cassini_COVIMS_ert2_PROF(**kwargs):
    return None

def populate_obs_mission_cassini_COVIMS_spacecraft_clock_count1_PROF(**kwargs):
    metadata = kwargs['metadata']
    supp_index_row = metadata['supp_index_row']
    sc = supp_index_row['SPACECRAFT_CLOCK_START_COUNT']
    if sc == 'UNK':
        return None

    # COVIMS_8001 SCLKs are in some weird units where the number to the right
    # of the decimal can be > 255, so we just round down
    if '.' in sc:
        sc = sc.split('.')[0] + '.000'
    try:
        sc_cvt = opus_support.parse_cassini_sclk(sc)
    except Exception as e:
        import_util.log_nonrepeating_warning(
            f'Unable to parse Cassini SCLK "{sc}": {e}')
        return None
    return sc_cvt

def populate_obs_mission_cassini_COVIMS_spacecraft_clock_count2_PROF(**kwargs):
    metadata = kwargs['metadata']
    supp_index_row = metadata['supp_index_row']
    sc = supp_index_row['SPACECRAFT_CLOCK_STOP_COUNT']
    if sc == 'UNK':
        return None

    # COVIMS_8001 SCLKs are in some weird units where the number to the right
    # of the decimal can be > 255, so we just round up
    if '.' in sc:
        sc = sc.split('.')[0] + '.000'
    try:
        sc_cvt = opus_support.parse_cassini_sclk(sc)+1 # Round up
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

def populate_obs_mission_cassini_COVIMS_mission_phase_name_PROF(**kwargs):
    return helper_cassini_mission_phase_name(**kwargs)

def populate_obs_mission_cassini_COVIMS_sequence_id_PROF(**kwargs):
    metadata = kwargs['metadata']
    supp_index_row = metadata['supp_index_row']
    id = supp_index_row['SEQUENCE_ID']

    return id


################################################################################
# THESE ARE SPECIFIC TO OBS_INSTRUMENT_COVIMS
################################################################################

def populate_obs_instrument_covims_channel_PROF(**kwargs):
    return 'IR'

def populate_obs_instrument_covims_ir_exposure_PROF(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['supp_index_row']
    ir_exp = import_util.safe_column(index_row, 'IR_EXPOSURE')

    if ir_exp is None:
        return None

    return ir_exp / 1000.
