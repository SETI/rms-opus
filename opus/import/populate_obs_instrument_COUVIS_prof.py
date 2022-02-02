
def populate_obs_general_CO_planet_id_PROF(**kwargs):
    return 'SAT'

################################################################################
# populate_obs_instrument_COUVIS_occ.py
#
# Routines to populate fields specific to COUVIS.
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

def _COUVIS_filespec_helper(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    # Format: "DATA/UVIS_HSP_2004_280_XI2CET_E_TAU01KM.LBL"
    filespec = index_row['FILE_SPECIFICATION_NAME']
    volume_id = kwargs['volume_id']
    return volume_id + '/' + filespec

def populate_obs_general_COUVIS_opus_id_PROF(**kwargs):
    filespec = _COUVIS_filespec_helper(**kwargs)
    pds_file = pdsfile.PdsFile.from_filespec(filespec, fix_case=True)
    opus_id = pds_file.opus_id
    if not opus_id:
        import_util.log_nonrepeating_error(
            f'Unable to create OPUS_ID for FILE_SPEC "{filespec}"')
        return filespec.split('/')[-1]

    # We do this because the filenames are wrong in the archive
    if opus_id == 'co-uvis-occ-2005-139-psicen-e':
        opus_id = 'co-uvis-occ-2007-038-psicen-e'
    elif opus_id == 'co-uvis-occ-2005-139-thehya-e':
        opus_id = 'co-uvis-occ-2009-062-thehya-e'
    elif opus_id == 'co-uvis-occ-2007-038-sao205839-i':
        opus_id = 'co-uvis-occ-2008-026-sao205839-i'

    return opus_id

def populate_obs_general_COUVIS_ring_obs_id_PROF(**kwargs):
    return None

def populate_obs_general_COUVIS_inst_host_id_PROF(**kwargs):
    return 'CO'

# COUVIS time span is the duration of the observation at the spacecraft
def populate_obs_general_COUVIS_time1_PROF(**kwargs):
    return populate_time1_from_supp_index(**kwargs)

def populate_obs_general_COUVIS_time2_PROF(**kwargs):
    return populate_time2_from_supp_index(**kwargs)

def populate_obs_general_COUVIS_target_name_PROF(**kwargs):
    target_name = 'S RINGS'
    target_name_info = TARGET_NAME_INFO[target_name]
    return target_name, target_name_info[2]

def populate_obs_general_COUVIS_observation_duration_PROF(**kwargs):
    return populate_observation_duration_from_time(**kwargs)

def populate_obs_general_COUVIS_quantity_PROF(**kwargs):
    return 'OPDEPTH'

def populate_obs_general_COUVIS_observation_type_PROF(**kwargs):
    return 'OCC'

def populate_obs_pds_COUVIS_note_PROF(**kwargs):
    metadata = kwargs['metadata']
    supp_index_row = metadata['supp_index_row']
    dq_score = supp_index_row['DATA_QUALITY_SCORE']
    return 'Data quality ' + dq_score.lower()

def populate_obs_general_COUVIS_primary_filespec_PROF(**kwargs):
    return _COUVIS_filespec_helper(**kwargs)

def populate_obs_pds_COUVIS_primary_filespec_PROF(**kwargs):
    return _COUVIS_filespec_helper(**kwargs)

def populate_obs_pds_COUVIS_product_creation_time_PROF(**kwargs):
    return populate_product_creation_time_from_supp_index(**kwargs)

# Format: "CO-SR-UVIS-HSP-2/4-OCC-V2.0"
def populate_obs_pds_COUVIS_data_set_id_PROF(**kwargs):
    return populate_data_set_id_from_index_label(**kwargs)

# Format: "UVIS_HSP_2004_280_XI2CET_E_TAU01KM.TAB"
def populate_obs_pds_COUVIS_product_id_PROF(**kwargs):
    return populate_product_id_from_index(**kwargs)

def populate_obs_general_COUVIS_right_asc1_PROF(**kwargs):
    return populate_occ_ra_dec_helper_index(**kwargs)[0]

def populate_obs_general_COUVIS_right_asc2_PROF(**kwargs):
    return populate_occ_ra_dec_helper_index(**kwargs)[1]

def populate_obs_general_COUVIS_declination1_PROF(**kwargs):
    return populate_occ_ra_dec_helper_index(**kwargs)[2]

def populate_obs_general_COUVIS_declination2_PROF(**kwargs):
    return populate_occ_ra_dec_helper_index(**kwargs)[3]


### OBS_TYPE_IMAGE TABLE ###

def populate_obs_type_image_COUVIS_image_type_id_PROF(**kwargs):
    return None

def populate_obs_type_image_COUVIS_duration_PROF(**kwargs):
    return None

def populate_obs_type_image_COUVIS_levels_PROF(**kwargs):
    return None

def populate_obs_type_image_COUVIS_lesser_pixel_size_PROF(**kwargs):
    return None

def populate_obs_type_image_COUVIS_greater_pixel_size_PROF(**kwargs):
    return None


### OBS_WAVELENGTH TABLE ###

def populate_obs_wavelength_COUVIS_wavelength1_PROF(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    wl1 = index_row['MINIMUM_WAVELENGTH']
    return wl1

def populate_obs_wavelength_COUVIS_wavelength2_PROF(**kwargs):
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

def populate_obs_wavelength_COUVIS_wave_res1_PROF(**kwargs):
    return _wave_res_helper(**kwargs)

def populate_obs_wavelength_COUVIS_wave_res2_PROF(**kwargs):
    return _wave_res_helper(**kwargs)

def populate_obs_wavelength_COUVIS_wave_no1_PROF(**kwargs):
    metadata = kwargs['metadata']
    wavelength_row = metadata['obs_wavelength_row']
    wl2 = wavelength_row['wavelength2']
    if wl2 is None:
        return None
    return 10000 / wl2 # cm^-1

def populate_obs_wavelength_COUVIS_wave_no2_PROF(**kwargs):
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

def populate_obs_wavelength_COUVIS_wave_no_res1_PROF(**kwargs):
    return _wave_no_res_helper(**kwargs)

def populate_obs_wavelength_COUVIS_wave_no_res2_PROF(**kwargs):
    return _wave_no_res_helper(**kwargs)

def populate_obs_wavelength_COUVIS_spec_flag_PROF(**kwargs):
    return 'N'

def populate_obs_wavelength_COUVIS_spec_size_PROF(**kwargs):
    return None

def populate_obs_wavelength_COUVIS_polarization_type_PROF(**kwargs):
    return 'NONE'


### populate_obs_occultation TABLE ###

def populate_obs_occultation_COUVIS_occ_type_PROF(**kwargs):
    return 'STE' # There are no SUN occultations

def populate_obs_occultation_COUVIS_occ_dir_PROF(**kwargs):
    filespec = _COUVIS_filespec_helper(**kwargs)

    # We don't allow "Both" as a direction since these are always split into
    # separate files.
    if '_I_' in filespec:
        return 'I'
    if '_E_' in filespec:
        return 'E'
    import_util.log_nonrepeating_error(
        f'Unknown ring occultation direction in filespec "{filespec}"')
    return None

def populate_obs_occultation_COUVIS_body_occ_flag_PROF(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    body_occ_flag = index_row['PLANETARY_OCCULTATION_FLAG']

    return body_occ_flag

def populate_obs_occultation_COUVIS_optical_depth_min_PROF(**kwargs):
    metadata = kwargs['metadata']
    supp_index_row = metadata['supp_index_row']
    opac = import_util.safe_column(supp_index_row, 'LOWEST_DETECTABLE_OPACITY')

    return opac

def populate_obs_occultation_COUVIS_optical_depth_max_PROF(**kwargs):
    metadata = kwargs['metadata']
    supp_index_row = metadata['supp_index_row']
    opac = import_util.safe_column(supp_index_row, 'HIGHEST_DETECTABLE_OPACITY')

    return opac

def _integration_duration_helper(**kwargs):
    metadata = kwargs['metadata']
    supp_index_row = metadata['supp_index_row']
    dur = supp_index_row['INTEGRATION_DURATION']

    # HSP integration_duration is in milliseconds!
    return dur/1000

def populate_obs_occultation_COUVIS_temporal_sampling_PROF(**kwargs):
    return _integration_duration_helper(**kwargs)

def populate_obs_occultation_COUVIS_quality_score_PROF(**kwargs):
    metadata = kwargs['metadata']
    supp_index_row = metadata['supp_index_row']
    dq_score = supp_index_row['DATA_QUALITY_SCORE']

    return dq_score

def populate_obs_occultation_COUVIS_wl_band_PROF(**kwargs):
    return 'UV'

def populate_obs_occultation_COUVIS_source_PROF(**kwargs):
    target_name, target_name_info = populate_star_name_helper_index(**kwargs)
    if target_name_info is None:
        return None
    return target_name, target_name_info[2]

def populate_obs_occultation_COUVIS_host_PROF(**kwargs):
    return 'Cassini'


### OBS_RING_GEOMETRY TABLE ###

def populate_obs_ring_geometry_COUVIS_ring_radius1_PROF(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    radius1 = import_util.safe_column(index_row, 'MINIMUM_RING_RADIUS')

    return radius1

def populate_obs_ring_geometry_COUVIS_ring_radius2_PROF(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    radius2 = import_util.safe_column(index_row, 'MAXIMUM_RING_RADIUS')

    return radius2

def populate_obs_ring_geometry_COUVIS_resolution1_PROF(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    res = import_util.safe_column(index_row, 'RADIAL_RESOLUTION')

    return res

def populate_obs_ring_geometry_COUVIS_resolution2_PROF(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    res = import_util.safe_column(index_row, 'RADIAL_RESOLUTION')

    return res

def populate_obs_ring_geometry_COUVIS_proj_resolution1_PROF(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    res = import_util.safe_column(index_row, 'RADIAL_RESOLUTION')

    return res

def populate_obs_ring_geometry_COUVIS_proj_resolution2_PROF(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    res = import_util.safe_column(index_row, 'RADIAL_RESOLUTION')

    return res

def populate_obs_ring_geometry_COUVIS_j2000_longitude1_PROF(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    long1 = import_util.safe_column(index_row, 'MINIMUM_RING_LONGITUDE')

    return long1

def populate_obs_ring_geometry_COUVIS_j2000_longitude2_PROF(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    long2 = import_util.safe_column(index_row, 'MAXIMUM_RING_LONGITUDE')

    return long2

def populate_obs_ring_geometry_COUVIS_ring_azimuth_wrt_observer1_PROF(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    az1 = import_util.safe_column(index_row, 'MINIMUM_OBSERVED_RING_AZIMUTH')

    return az1

def populate_obs_ring_geometry_COUVIS_ring_azimuth_wrt_observer2_PROF(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    az2 = import_util.safe_column(index_row, 'MAXIMUM_OBSERVED_RING_AZIMUTH')

    return az2

def populate_obs_ring_geometry_COUVIS_phase1_PROF(**kwargs):
    return 180.

def populate_obs_ring_geometry_COUVIS_phase2_PROF(**kwargs):
    return 180.

def populate_obs_ring_geometry_COUVIS_incidence1_PROF(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    el = index_row['OBSERVED_RING_ELEVATION']

    return 90. - abs(el)

def populate_obs_ring_geometry_COUVIS_incidence2_PROF(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    el = index_row['OBSERVED_RING_ELEVATION']

    return 90. - abs(el)

def populate_obs_ring_geometry_COUVIS_north_based_incidence1_PROF(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    el = index_row['OBSERVED_RING_ELEVATION']

    return 90. + el

def populate_obs_ring_geometry_COUVIS_north_based_incidence2_PROF(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    el = index_row['OBSERVED_RING_ELEVATION']

    return 90. + el

def populate_obs_ring_geometry_COUVIS_emission1_PROF(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    el = index_row['OBSERVED_RING_ELEVATION']

    return 90. + abs(el)

def populate_obs_ring_geometry_COUVIS_emission2_PROF(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    el = index_row['OBSERVED_RING_ELEVATION']

    return 90. + abs(el)

def populate_obs_ring_geometry_COUVIS_north_based_emission1_PROF(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    el = index_row['OBSERVED_RING_ELEVATION']

    return 90. - el

def populate_obs_ring_geometry_COUVIS_north_based_emission2_PROF(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    el = index_row['OBSERVED_RING_ELEVATION']

    return 90. - el

# We set the center versions to be the same as the normal versions
populate_obs_ring_geometry_COUVIS_center_phase1_PROF = \
    populate_obs_ring_geometry_COUVIS_phase1_PROF
populate_obs_ring_geometry_COUVIS_center_phase2_PROF = \
    populate_obs_ring_geometry_COUVIS_phase2_PROF
populate_obs_ring_geometry_COUVIS_center_incidence1_PROF = \
    populate_obs_ring_geometry_COUVIS_incidence1_PROF
populate_obs_ring_geometry_COUVIS_center_incidence2_PROF = \
    populate_obs_ring_geometry_COUVIS_incidence2_PROF
populate_obs_ring_geometry_COUVIS_center_emission1_PROF = \
    populate_obs_ring_geometry_COUVIS_emission1_PROF
populate_obs_ring_geometry_COUVIS_center_emission2_PROF = \
    populate_obs_ring_geometry_COUVIS_emission2_PROF
populate_obs_ring_geometry_COUVIS_center_north_based_incidence1_PROF = \
    populate_obs_ring_geometry_COUVIS_north_based_incidence1_PROF
populate_obs_ring_geometry_COUVIS_center_north_based_incidence2_PROF = \
    populate_obs_ring_geometry_COUVIS_north_based_incidence2_PROF
populate_obs_ring_geometry_COUVIS_center_north_based_emission1_PROF = \
    populate_obs_ring_geometry_COUVIS_north_based_emission1_PROF
populate_obs_ring_geometry_COUVIS_center_north_based_emission2_PROF = \
    populate_obs_ring_geometry_COUVIS_north_based_emission2_PROF

def populate_obs_ring_geometry_COUVIS_observer_ring_opening_angle1_PROF(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    el = index_row['OBSERVED_RING_ELEVATION']

    return el

def populate_obs_ring_geometry_COUVIS_observer_ring_opening_angle2_PROF(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    el = index_row['OBSERVED_RING_ELEVATION']

    return el

def populate_obs_ring_geometry_COUVIS_observer_ring_elevation1_PROF(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    el = index_row['OBSERVED_RING_ELEVATION']

    return el

def populate_obs_ring_geometry_COUVIS_observer_ring_elevation2_PROF(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    el = index_row['OBSERVED_RING_ELEVATION']

    return el

def populate_obs_ring_geometry_COUVIS_solar_ring_opening_angle1_PROF(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    el = index_row['OBSERVED_RING_ELEVATION']

    return -el

def populate_obs_ring_geometry_COUVIS_solar_ring_opening_angle2_PROF(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    el = index_row['OBSERVED_RING_ELEVATION']

    return -el

def populate_obs_ring_geometry_COUVIS_solar_ring_elevation1_PROF(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    el = index_row['OBSERVED_RING_ELEVATION']

    return -el

def populate_obs_ring_geometry_COUVIS_solar_ring_elevation2_PROF(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    el = index_row['OBSERVED_RING_ELEVATION']

    return -el

def populate_obs_ring_geometry_COUVIS_ring_intercept_time1_PROF(**kwargs):
    return populate_time1_from_index(column='RING_EVENT_START_TIME', **kwargs)

def populate_obs_ring_geometry_COUVIS_ring_intercept_time2_PROF(**kwargs):
    return populate_time1_from_index(column='RING_EVENT_STOP_TIME', **kwargs)


################################################################################
# THESE NEED TO BE IMPLEMENTED FOR EVERY CASSINI INSTRUMENT
################################################################################

def populate_obs_mission_cassini_COUVIS_ert1_PROF(**kwargs):
    return None

def populate_obs_mission_cassini_COUVIS_ert2_PROF(**kwargs):
    return None

def populate_obs_mission_cassini_COUVIS_spacecraft_clock_count1_PROF(**kwargs):
    metadata = kwargs['metadata']
    supp_index_row = metadata['supp_index_row']
    sc = supp_index_row['SPACECRAFT_CLOCK_START_COUNT']
    if sc == 'UNK':
        return None

    try:
        sc_cvt = opus_support.parse_cassini_sclk(sc)
    except Exception as e:
        import_util.log_nonrepeating_warning(
            f'Unable to parse Cassini SCLK "{sc}": {e}')
        return None
    return sc_cvt

def populate_obs_mission_cassini_COUVIS_spacecraft_clock_count2_PROF(**kwargs):
    metadata = kwargs['metadata']
    supp_index_row = metadata['supp_index_row']
    sc = supp_index_row['SPACECRAFT_CLOCK_STOP_COUNT']
    if sc == 'UNK':
        return None

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

def populate_obs_mission_cassini_COUVIS_mission_phase_name_PROF(**kwargs):
    return helper_cassini_mission_phase_name(**kwargs)

def populate_obs_mission_cassini_COUVIS_sequence_id_PROF(**kwargs):
    metadata = kwargs['metadata']
    supp_index_row = metadata['supp_index_row']
    id = supp_index_row['SEQUENCE_ID']

    return id


################################################################################
# THESE ARE SPECIFIC TO OBS_INSTRUMENT_COUVIS
################################################################################

def populate_obs_instrument_couvis_channel_PROF(**kwargs):
    return ('HSP', 'HSP')

def populate_obs_instrument_couvis_observation_type_PROF(**kwargs):
    return 'NONE'

def populate_obs_instrument_couvis_occultation_port_state_PROF(**kwargs):
    return 'N/A'

def populate_obs_instrument_couvis_integration_duration_PROF(**kwargs):
    return _integration_duration_helper(**kwargs)

def populate_obs_instrument_couvis_compression_type_PROF(**kwargs):
    metadata = kwargs['metadata']
    supp_index_row = metadata['supp_index_row']
    comp = supp_index_row['COMPRESSION_TYPE']

    return (comp, comp)

def populate_obs_instrument_couvis_slit_state_PROF(**kwargs):
    return 'NULL'

def populate_obs_instrument_couvis_test_pulse_state_PROF(**kwargs):
    return None

def populate_obs_instrument_couvis_dwell_time_PROF(**kwargs):
    return None

def populate_obs_instrument_couvis_band1_PROF(**kwargs):
    return None

def populate_obs_instrument_couvis_band2_PROF(**kwargs):
    return None

def populate_obs_instrument_couvis_band_bin_PROF(**kwargs):
    return None

def populate_obs_instrument_couvis_line1_PROF(**kwargs):
    return None

def populate_obs_instrument_couvis_line2_PROF(**kwargs):
    return None

def populate_obs_instrument_couvis_line_bin_PROF(**kwargs):
    return None

def populate_obs_instrument_couvis_samples_PROF(**kwargs):
    return None
