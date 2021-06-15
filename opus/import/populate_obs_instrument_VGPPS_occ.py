################################################################################
# populate_obs_instrument_VGPPS_occ.py
#
# Routines to populate fields specific to VGPPS.
################################################################################

import pdsfile

from config_data import *
import import_util

from populate_obs_mission_voyager import *
from populate_util import *

################################################################################
# THESE NEED TO BE IMPLEMENTED FOR EVERY INSTRUMENT
################################################################################

### OBS_GENERAL TABLE ###

def _VGPPS_file_spec_helper(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']

    file_spec = index_row['FILE_SPECIFICATION_NAME']
    volume_id = kwargs['volume_id']
    return volume_id + '/' + file_spec

def populate_obs_general_VGPPS_opus_id_OCC(**kwargs):
    file_spec = _VGPPS_file_spec_helper(**kwargs)
    pds_file = pdsfile.PdsFile.from_filespec(file_spec, fix_case=True)
    opus_id = pds_file.opus_id
    if not opus_id:
        import_util.log_nonrepeating_error(
            f'Unable to create OPUS_ID for FILE_SPEC "{file_spec}"')
        return file_spec.split('/')[-1]

    return opus_id

def populate_obs_general_VGPPS_ring_obs_id_OCC(**kwargs):
    return None

def populate_obs_general_VGPPS_inst_host_id_OCC(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    inst_host = index_row['INSTRUMENT_HOST_NAME']

    assert inst_host in ['VOYAGER 1', 'VOYAGER 2']

    return 'VG'+inst_host[-1]
    # return 'VG'

# VGPPS time span is the duration of the observation at the spacecraft
def populate_obs_general_VGPPS_time1_OCC(**kwargs):
    return populate_time1_from_index(**kwargs)

def populate_obs_general_VGPPS_time2_OCC(**kwargs):
    return populate_time2_from_index(**kwargs)

def populate_obs_general_VGPPS_target_name_OCC(**kwargs):
    # Get target name from index table
    target_name = populate_target_name_from_index(**kwargs)
    target_name_info = TARGET_NAME_INFO[target_name]
    return target_name, target_name_info[2]

def populate_obs_general_VGPPS_observation_duration_OCC(**kwargs):
    return populate_observation_duration_from_time(**kwargs)

def populate_obs_general_VGPPS_quantity_OCC(**kwargs):
    return 'OPDEPTH'

def populate_obs_general_VGPPS_observation_type_OCC(**kwargs):
    return 'OCC'

def populate_obs_pds_VGPPS_note_OCC(**kwargs):
    return None

def populate_obs_general_VGPPS_primary_file_spec_OCC(**kwargs):
    return _VGPPS_file_spec_helper(**kwargs)

def populate_obs_pds_VGPPS_primary_file_spec_OCC(**kwargs):
    return _VGPPS_file_spec_helper(**kwargs)

def populate_obs_pds_VGPPS_product_creation_time_OCC(**kwargs):
    return populate_product_creation_time_from_supp_index(**kwargs)

# Format: "VG2-SR/UR/NR-PPS-2/4-OCC-V1.0"
def populate_obs_pds_VGPPS_data_set_id_OCC(**kwargs):
    return populate_data_set_id_from_index_label(**kwargs)

# Format: "KM001/PU2P016I.TAB"
def populate_obs_pds_VGPPS_product_id_OCC(**kwargs):
    return populate_product_id_from_index(**kwargs)

def populate_obs_general_VGPPS_right_asc1_OCC(**kwargs):
    return populate_occ_ra_dec_helper_index(**kwargs)[0]

def populate_obs_general_VGPPS_right_asc2_OCC(**kwargs):
    return populate_occ_ra_dec_helper_index(**kwargs)[1]

def populate_obs_general_VGPPS_declination1_OCC(**kwargs):
    return populate_occ_ra_dec_helper_index(**kwargs)[2]

def populate_obs_general_VGPPS_declination2_OCC(**kwargs):
    return populate_occ_ra_dec_helper_index(**kwargs)[3]


### OBS_TYPE_IMAGE TABLE ###

def populate_obs_type_image_VGPPS_image_type_id_OCC(**kwargs):
    return None

def populate_obs_type_image_VGPPS_duration_OCC(**kwargs):
    return None

def populate_obs_type_image_VGPPS_levels_OCC(**kwargs):
    return None

def populate_obs_type_image_VGPPS_lesser_pixel_size_OCC(**kwargs):
    return None

def populate_obs_type_image_VGPPS_greater_pixel_size_OCC(**kwargs):
    return None


### OBS_WAVELENGTH TABLE ###

def populate_obs_wavelength_VGPPS_wavelength1_OCC(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    wl1 = index_row['MINIMUM_WAVELENGTH']
    return wl1

def populate_obs_wavelength_VGPPS_wavelength2_OCC(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    wl2 = index_row['MAXIMUM_WAVELENGTH']

    return wl2

def _wave_res_helper(**kwargs):
    metadata = kwargs['metadata']
    wl_row = metadata['obs_wavelength_row']
    wl1 = wl_row['wavelength1']
    wl2 = wl_row['wavelength2']
    if wl1 is None or wl2 is None:
        return None
    return wl2 - wl1

def populate_obs_wavelength_VGPPS_wave_res1_OCC(**kwargs):
    return _wave_res_helper(**kwargs)

def populate_obs_wavelength_VGPPS_wave_res2_OCC(**kwargs):
    return _wave_res_helper(**kwargs)

def populate_obs_wavelength_VGPPS_wave_no1_OCC(**kwargs):
    metadata = kwargs['metadata']
    wavelength_row = metadata['obs_wavelength_row']
    wl2 = wavelength_row['wavelength2']
    if wl2 is None:
        return None
    return 10000 / wl2 # cm^-1

def populate_obs_wavelength_VGPPS_wave_no2_OCC(**kwargs):
    metadata = kwargs['metadata']
    wavelength_row = metadata['obs_wavelength_row']
    wl1 = wavelength_row['wavelength1']
    if wl1 is None:
        return None
    return 10000 / wl1 # cm^-1

# Same logic as wave_res
def _wave_no_res_helper(**kwargs):
    metadata = kwargs['metadata']
    wl_row = metadata['obs_wavelength_row']
    wno1 = wl_row['wave_no1']
    wno2 = wl_row['wave_no2']
    if wno1 is None or wno2 is None:
        return None
    return wno2 - wno1

def populate_obs_wavelength_VGPPS_wave_no_res1_OCC(**kwargs):
    return _wave_no_res_helper(**kwargs)

def populate_obs_wavelength_VGPPS_wave_no_res2_OCC(**kwargs):
    return _wave_no_res_helper(**kwargs)

def populate_obs_wavelength_VGPPS_spec_flag_OCC(**kwargs):
    return 'N'

def populate_obs_wavelength_VGPPS_spec_size_OCC(**kwargs):
    return 1

def populate_obs_wavelength_VGPPS_polarization_type_OCC(**kwargs):
    return 'NONE'


### populate_obs_occultation TABLE ###

def populate_obs_occultation_VGPPS_occ_type_OCC(**kwargs):
    return 'STE' # There are no SUN occultations

def populate_obs_occultation_VGPPS_occ_dir_OCC(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    occ_direction = index_row['RING_OCCULTATION_DIRECTION'][0]

    return occ_direction

def populate_obs_occultation_VGPPS_body_occ_flag_OCC(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    body_occ_flag = index_row['PLANETARY_OCCULTATION_FLAG']

    return body_occ_flag

def populate_obs_occultation_VGPPS_optical_depth_min_OCC(**kwargs):
    return None

def populate_obs_occultation_VGPPS_optical_depth_max_OCC(**kwargs):
    return None

def _integration_duration_helper(**kwargs):
    metadata = kwargs['metadata']
    supp_index_row = metadata['supp_index_row']
    dur = supp_index_row['INTEGRATION_DURATION']

    # HSP integration_duration is in milliseconds!
    return dur/1000

def populate_obs_occultation_VGPPS_temporal_sampling_OCC(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    tmp_sampling_interval = index_row['TEMPORAL_SAMPLING_INTERVAL']

    return tmp_sampling_interval

def populate_obs_occultation_VGPPS_quality_score_OCC(**kwargs):
    return None

def populate_obs_occultation_VGPPS_wl_band_OCC(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    wl_band = index_row['WAVELENGTH_BAND_1']

    return wl_band

def populate_obs_occultation_VGPPS_source_OCC(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    src_name = index_row['SIGNAL_SOURCE_NAME_1']

    return src_name

def populate_obs_occultation_VGPPS_host_OCC(**kwargs):
    return 'voyager'


### OBS_RING_GEOMETRY TABLE ###

def populate_obs_ring_geometry_VGPPS_ring_radius1_OCC(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    radius1 = import_util.safe_column(index_row, 'MINIMUM_RING_RADIUS')

    return radius1

def populate_obs_ring_geometry_VGPPS_ring_radius2_OCC(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    radius2 = import_util.safe_column(index_row, 'MAXIMUM_RING_RADIUS')

    return radius2

def populate_obs_ring_geometry_VGPPS_resolution1_OCC(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    res = import_util.safe_column(index_row, 'MINIMUM_RADIAL_RESOLUTION')

    return res

def populate_obs_ring_geometry_VGPPS_resolution2_OCC(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    res = import_util.safe_column(index_row, 'MAXIMUM_RADIAL_RESOLUTION')

    return res

def populate_obs_ring_geometry_VGPPS_proj_resolution1_OCC(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    res = import_util.safe_column(index_row, 'MINIMUM_RADIAL_RESOLUTION')

    return res

def populate_obs_ring_geometry_VGPPS_proj_resolution2_OCC(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    res = import_util.safe_column(index_row, 'MAXIMUM_RADIAL_RESOLUTION')

    return res

def populate_obs_ring_geometry_VGPPS_j2000_longitude1_OCC(**kwargs):
    return None

def populate_obs_ring_geometry_VGPPS_j2000_longitude2_OCC(**kwargs):
    return None

def populate_obs_ring_geometry_VGPPS_ring_azimuth_wrt_observer1_OCC(**kwargs):
    return None

def populate_obs_ring_geometry_VGPPS_ring_azimuth_wrt_observer2_OCC(**kwargs):
    return None

def populate_obs_ring_geometry_VGPPS_phase1_OCC(**kwargs):
    return 180.

def populate_obs_ring_geometry_VGPPS_phase2_OCC(**kwargs):
    return 180.

###### TODO: Need to figure out the calculations for the followings: ######
def populate_obs_ring_geometry_VGPPS_incidence1_OCC(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    el = index_row['INCIDENCE_ANGLE']

    return el

def populate_obs_ring_geometry_VGPPS_incidence2_OCC(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    el = index_row['INCIDENCE_ANGLE']

    return el

def populate_obs_ring_geometry_VGPPS_north_based_incidence1_OCC(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    el = index_row['INCIDENCE_ANGLE']

    return el

def populate_obs_ring_geometry_VGPPS_north_based_incidence2_OCC(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    el = index_row['INCIDENCE_ANGLE']

    return el

def populate_obs_ring_geometry_VGPPS_emission1_OCC(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    el = index_row['MAXIMUM_EMISSION_ANGLE']

    return el # 180-incidence

def populate_obs_ring_geometry_VGPPS_emission2_OCC(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    el = index_row['MAXIMUM_EMISSION_ANGLE']

    return el # 180-incidence

def populate_obs_ring_geometry_VGPPS_north_based_emission1_OCC(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    el = index_row['MAXIMUM_EMISSION_ANGLE']

    return el # 180-incidence

def populate_obs_ring_geometry_VGPPS_north_based_emission2_OCC(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    el = index_row['MAXIMUM_EMISSION_ANGLE']

    return el # 180-incidence

# We set the center versions to be the same as the normal versions
populate_obs_ring_geometry_VGPPS_center_phase1_OCC = \
    populate_obs_ring_geometry_VGPPS_phase1_OCC
populate_obs_ring_geometry_VGPPS_center_phase2_OCC = \
    populate_obs_ring_geometry_VGPPS_phase2_OCC
populate_obs_ring_geometry_VGPPS_center_incidence1_OCC = \
    populate_obs_ring_geometry_VGPPS_incidence1_OCC
populate_obs_ring_geometry_VGPPS_center_incidence2_OCC = \
    populate_obs_ring_geometry_VGPPS_incidence2_OCC
populate_obs_ring_geometry_VGPPS_center_emission1_OCC = \
    populate_obs_ring_geometry_VGPPS_emission1_OCC
populate_obs_ring_geometry_VGPPS_center_emission2_OCC = \
    populate_obs_ring_geometry_VGPPS_emission2_OCC
populate_obs_ring_geometry_VGPPS_center_north_based_incidence1_OCC = \
    populate_obs_ring_geometry_VGPPS_north_based_incidence1_OCC
populate_obs_ring_geometry_VGPPS_center_north_based_incidence2_OCC = \
    populate_obs_ring_geometry_VGPPS_north_based_incidence2_OCC
populate_obs_ring_geometry_VGPPS_center_north_based_emission1_OCC = \
    populate_obs_ring_geometry_VGPPS_north_based_emission1_OCC
populate_obs_ring_geometry_VGPPS_center_north_based_emission2_OCC = \
    populate_obs_ring_geometry_VGPPS_north_based_emission2_OCC

def populate_obs_ring_geometry_VGPPS_observer_ring_opening_angle1_OCC(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    el = index_row['INCIDENCE_ANGLE']

    return el

def populate_obs_ring_geometry_VGPPS_observer_ring_opening_angle2_OCC(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    el = index_row['INCIDENCE_ANGLE']

    return el

def populate_obs_ring_geometry_VGPPS_observer_ring_elevation1_OCC(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    el = index_row['INCIDENCE_ANGLE']

    return el

def populate_obs_ring_geometry_VGPPS_observer_ring_elevation2_OCC(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    el = index_row['INCIDENCE_ANGLE']

    return el

def populate_obs_ring_geometry_VGPPS_solar_ring_opening_angle1_OCC(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    el = index_row['INCIDENCE_ANGLE']

    return -el

def populate_obs_ring_geometry_VGPPS_solar_ring_opening_angle2_OCC(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    el = index_row['INCIDENCE_ANGLE']

    return -el

def populate_obs_ring_geometry_VGPPS_solar_ring_elevation1_OCC(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    el = index_row['INCIDENCE_ANGLE']

    return -el

def populate_obs_ring_geometry_VGPPS_solar_ring_elevation2_OCC(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    el = index_row['INCIDENCE_ANGLE']

    return -el

def populate_obs_ring_geometry_VGPPS_ring_intercept_time1_OCC(**kwargs):
    return populate_time1_from_index(column='RING_EVENT_START_TIME', **kwargs)

def populate_obs_ring_geometry_VGPPS_ring_intercept_time2_OCC(**kwargs):
    return populate_time1_from_index(column='RING_EVENT_STOP_TIME', **kwargs)


################################################################################
# THESE NEED TO BE IMPLEMENTED FOR EVERY voyager INSTRUMENT
################################################################################

def populate_obs_mission_voyager_VGPPS_ert1_OCC(**kwargs):
    return None

def populate_obs_mission_voyager_VGPPS_ert2_OCC(**kwargs):
    return None

def populate_obs_mission_voyager_VGPPS_spacecraft_clock_count1_OCC(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    sc = index_row['SPACECRAFT_CLOCK_START_COUNT']
    if sc == 'UNK':
        return None

    try:
        sc_cvt = opus_support.parse_voyager_sclk(sc)
    except Exception as e:
        import_util.log_nonrepeating_warning(
            f'Unable to parse voyager SCLK "{sc}": {e}')
        return None
    return sc_cvt

def populate_obs_mission_voyager_VGPPS_spacecraft_clock_count2_OCC(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    sc = index_row['SPACECRAFT_CLOCK_STOP_COUNT']
    if sc == 'UNK':
        return None

    try:
        sc_cvt = opus_support.parse_voyager_sclk(sc)
    except Exception as e:
        import_util.log_nonrepeating_warning(
            f'Unable to parse voyager SCLK "{sc}": {e}')
        return None

    voyager_row = metadata['obs_mission_voyager_row']
    sc1 = voyager_row['spacecraft_clock_count1']
    if sc1 is not None and sc_cvt < sc1:
        import_util.log_warning(
    f'spacecraft_clock_count1 ({sc1}) and spacecraft_clock_count2 ({sc_cvt}) '
    +'are in the wrong order - setting to count1')
        sc_cvt = sc1

    return sc_cvt

def populate_obs_mission_voyager_VGPPS_mission_phase_name_OCC(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    target_name = index_row['TARGET_NAME'].upper()
    mp = VG_TARGET_TO_MISSION_PHASE_MAPPING[target_name]

    return mp

def populate_obs_mission_voyager_VGPPS_sequence_id_OCC(**kwargs):
    metadata = kwargs['metadata']
    supp_index_row = metadata['supp_index_row']
    id = supp_index_row['SEQUENCE_ID']

    return id


################################################################################
# THESE ARE SPECIFIC TO OBS_INSTRUMENT_VGPPS
################################################################################

def populate_obs_instrument_VGPPS_channel_OCC(**kwargs):
    return  None

def populate_obs_instrument_VGPPS_observation_type_OCC(**kwargs):
    return 'Occultation Profile'

def populate_obs_instrument_VGPPS_occultation_port_state_OCC(**kwargs):
    return 'N/A'

def populate_obs_instrument_VGPPS_integration_duration_OCC(**kwargs):
    return None
    # return _integration_duration_helper(**kwargs)

def populate_obs_instrument_VGPPS_compression_type_OCC(**kwargs):
    return None

def populate_obs_instrument_VGPPS_slit_state_OCC(**kwargs):
    return 'NULL'

def populate_obs_instrument_VGPPS_test_pulse_state_OCC(**kwargs):
    return None

def populate_obs_instrument_VGPPS_dwell_time_OCC(**kwargs):
    return None

def populate_obs_instrument_VGPPS_band1_OCC(**kwargs):
    return None

def populate_obs_instrument_VGPPS_band2_OCC(**kwargs):
    return None

def populate_obs_instrument_VGPPS_band_bin_OCC(**kwargs):
    return None

def populate_obs_instrument_VGPPS_line1_OCC(**kwargs):
    return None

def populate_obs_instrument_VGPPS_line2_OCC(**kwargs):
    return None

def populate_obs_instrument_VGPPS_line_bin_OCC(**kwargs):
    return None

def populate_obs_instrument_VGPPS_samples_OCC(**kwargs):
    return None
