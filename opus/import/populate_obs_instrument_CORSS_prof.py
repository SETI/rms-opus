################################################################################
# populate_obs_instrument_CORSS_occ.py
#
# Routines to populate fields specific to CORSS.
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

def _CORSS_filespec_helper(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    # Format: "data/Rev007/Rev007E/Rev007E_RSS_2005_123_K34_E/RSS_2005_123_K34_E_TAU_01KM.LBL"
    filespec = index_row['FILE_SPECIFICATION_NAME']
    volume_id = kwargs['volume_id']
    return volume_id + '/' + filespec

def populate_obs_general_CORSS_opus_id_PROF(**kwargs):
    filespec = _CORSS_filespec_helper(**kwargs)
    pds_file = pdsfile.PdsFile.from_filespec(filespec, fix_case=True)
    opus_id = pds_file.opus_id
    if not opus_id:
        import_util.log_nonrepeating_error(
            f'Unable to create OPUS_ID for FILE_SPEC "{filespec}"')
        return filespec.split('/')[-1]
    return opus_id

def populate_obs_general_CORSS_ring_obs_id_PROF(**kwargs):
    return None

def populate_obs_general_CORSS_inst_host_id_PROF(**kwargs):
    return 'CO'

# CORSS time span is from when the photon first leaves the spacecraft to when
# it is received on Earth.
def populate_obs_general_CORSS_time1_PROF(**kwargs):
    metadata = kwargs['metadata']
    supp_index_row = metadata['supp_index_row']
    start_time = supp_index_row['SPACECRAFT_EVENT_START_TIME']

    try:
        start_time_sec = julian.tai_from_iso(start_time)
    except Exception as e:
        import_util.log_nonrepeating_error(
            f'Bad start time format "{start_time}": {e}')
        return None

    return start_time_sec

def populate_obs_general_CORSS_time2_PROF(**kwargs):
    metadata = kwargs['metadata']
    supp_index_row = metadata['supp_index_row']
    stop_time = supp_index_row['EARTH_RECEIVED_STOP_TIME']

    try:
        stop_time_sec = julian.tai_from_iso(stop_time)
    except Exception as e:
        import_util.log_nonrepeating_error(
            f'Bad stop time format "{stop_time}": {e}')
        return None

    general_row = metadata['obs_general_row']
    start_time_sec = general_row['time1']

    if start_time_sec is not None and stop_time_sec < start_time_sec:
        start_time = supp_index_row['SPACECRAFT_EVENT_START_TIME']
        import_util.log_warning(f'time1 ({start_time}) and time2 ({stop_time}) '
                                f'are in the wrong order - setting to time1')
        stop_time_sec = start_time_sec

    return stop_time_sec

def populate_obs_general_CORSS_target_name_PROF(**kwargs):
    target_name = 'S RINGS'
    target_name_info = TARGET_NAME_INFO[target_name]
    return target_name, target_name_info[2]

def populate_obs_general_CORSS_observation_duration_PROF(**kwargs):
    return populate_observation_duration_from_time(**kwargs)

def populate_obs_general_CORSS_quantity_PROF(**kwargs):
    return 'OPDEPTH'

def populate_obs_general_CORSS_observation_type_PROF(**kwargs):
    return 'OCC'

def populate_obs_pds_CORSS_note_PROF(**kwargs):
    return None

def populate_obs_general_CORSS_primary_filespec_PROF(**kwargs):
    return _CORSS_filespec_helper(**kwargs)

def populate_obs_pds_CORSS_primary_filespec_PROF(**kwargs):
    return _CORSS_filespec_helper(**kwargs)

def populate_obs_pds_CORSS_product_creation_time_PROF(**kwargs):
    return populate_product_creation_time_from_supp_index(**kwargs)

# Format: "CO-SR-RSS-4/5-OCC-V2.0"
def populate_obs_pds_CORSS_data_set_id_PROF(**kwargs):
    return populate_data_set_id_from_index_label(**kwargs)

# Format: "RSS_2005_123_X43_E_TAU_01KM.LBL"
def populate_obs_pds_CORSS_product_id_PROF(**kwargs):
    return populate_product_id_from_index(**kwargs)

# There's no easy way to figure out RA/DEC for CORSS since the Spacecraft
# itself is the signal source.
def populate_obs_general_CORSS_right_asc1_PROF(**kwargs):
    return None

def populate_obs_general_CORSS_right_asc2_PROF(**kwargs):
    return None

def populate_obs_general_CORSS_declination1_PROF(**kwargs):
    return None

def populate_obs_general_CORSS_declination2_PROF(**kwargs):
    return None


### OBS_TYPE_IMAGE TABLE ###

def populate_obs_type_image_CORSS_image_type_id_PROF(**kwargs):
    return None

def populate_obs_type_image_CORSS_duration_PROF(**kwargs):
    return None

def populate_obs_type_image_CORSS_levels_PROF(**kwargs):
    return None

def populate_obs_type_image_CORSS_lesser_pixel_size_PROF(**kwargs):
    return None

def populate_obs_type_image_CORSS_greater_pixel_size_PROF(**kwargs):
    return None


### OBS_WAVELENGTH TABLE ###

def populate_obs_wavelength_CORSS_wavelength1_PROF(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    wl = index_row['WAVELENGTH']

    return wl * 10000 # cm -> micron

def populate_obs_wavelength_CORSS_wavelength2_PROF(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    wl = index_row['WAVELENGTH']

    return wl * 10000 # cm -> micron

def populate_obs_wavelength_CORSS_wave_res1_PROF(**kwargs):
    return None

def populate_obs_wavelength_CORSS_wave_res2_PROF(**kwargs):
    return None

def populate_obs_wavelength_CORSS_wave_no1_PROF(**kwargs):
    metadata = kwargs['metadata']
    wavelength_row = metadata['obs_wavelength_row']
    wl2 = wavelength_row['wavelength2']
    if wl2 is None:
        return None
    return 10000 / wl2 # cm^-1

def populate_obs_wavelength_CORSS_wave_no2_PROF(**kwargs):
    metadata = kwargs['metadata']
    wavelength_row = metadata['obs_wavelength_row']
    wl1 = wavelength_row['wavelength1']
    if wl1 is None:
        return None
    return 10000 / wl1 # cm^-1

def populate_obs_wavelength_CORSS_wave_no_res1_PROF(**kwargs):
    return None

def populate_obs_wavelength_CORSS_wave_no_res2_PROF(**kwargs):
    return None

def populate_obs_wavelength_CORSS_spec_flag_PROF(**kwargs):
    return 'N'

def populate_obs_wavelength_CORSS_spec_size_PROF(**kwargs):
    return None

def populate_obs_wavelength_CORSS_polarization_type_PROF(**kwargs):
    return 'NONE'


### populate_obs_occultation TABLE ###

def populate_obs_occultation_CORSS_occ_type_PROF(**kwargs):
    return 'RAD'

def populate_obs_occultation_CORSS_occ_dir_PROF(**kwargs):
    filespec = _CORSS_filespec_helper(**kwargs)

    # We don't allow "Both" as a direction since these are always split into
    # separate files.
    if '_I_' in filespec:
        return 'I'
    if '_E_' in filespec:
        return 'E'
    import_util.log_nonrepeating_error(
        f'Unknown ring occultation direction in filespec "{filespec}"')
    return None

def populate_obs_occultation_CORSS_body_occ_flag_PROF(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    body_occ_flag = index_row['PLANETARY_OCCULTATION_FLAG']

    return body_occ_flag

def populate_obs_occultation_CORSS_optical_depth_min_PROF(**kwargs):
    metadata = kwargs['metadata']
    supp_index_row = metadata['supp_index_row']
    opac = supp_index_row['LOWEST_DETECTABLE_OPACITY']

    return opac

def populate_obs_occultation_CORSS_optical_depth_max_PROF(**kwargs):
    metadata = kwargs['metadata']
    supp_index_row = metadata['supp_index_row']
    opac = supp_index_row['HIGHEST_DETECTABLE_OPACITY']

    return opac

def populate_obs_occultation_CORSS_temporal_sampling_PROF(**kwargs):
    return None # Not available

def populate_obs_occultation_CORSS_quality_score_PROF(**kwargs):
    return ("UNASSIGNED", "Unassigned")

def populate_obs_occultation_CORSS_wl_band_PROF(**kwargs):
    metadata = kwargs['metadata']
    index_label = metadata['index_row']
    band = index_label['BAND_NAME'] # microns

    if band == 'K':
        band = 'KA'

    return band

def populate_obs_occultation_CORSS_source_PROF(**kwargs):
    return ('CASSINI', 'Cassini', '!Cassini')

def populate_obs_occultation_CORSS_host_PROF(**kwargs):
    metadata = kwargs['metadata']
    supp_index = metadata['supp_index_row']
    dsn = supp_index['DSN_STATION_NUMBER']

    ret = f'DSN {dsn} ({DSN_NAMES[dsn]})'
    return (ret, ret)


### OBS_RING_GEOMETRY TABLE ###

def populate_obs_ring_geometry_CORSS_ring_radius1_PROF(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    radius1 = import_util.safe_column(index_row, 'MINIMUM_RING_RADIUS')

    return radius1

def populate_obs_ring_geometry_CORSS_ring_radius2_PROF(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    radius2 = import_util.safe_column(index_row, 'MAXIMUM_RING_RADIUS')

    return radius2

def populate_obs_ring_geometry_CORSS_resolution1_PROF(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    res = import_util.safe_column(index_row, 'RADIAL_RESOLUTION')

    return res

def populate_obs_ring_geometry_CORSS_resolution2_PROF(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    res = import_util.safe_column(index_row, 'RADIAL_RESOLUTION')

    return res

def populate_obs_ring_geometry_CORSS_proj_resolution1_PROF(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    res = import_util.safe_column(index_row, 'RADIAL_RESOLUTION')

    return res

def populate_obs_ring_geometry_CORSS_proj_resolution2_PROF(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    res = import_util.safe_column(index_row, 'RADIAL_RESOLUTION')

    return res

def populate_obs_ring_geometry_CORSS_j2000_longitude1_PROF(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    long1 = import_util.safe_column(index_row, 'MINIMUM_RING_LONGITUDE')

    return long1

def populate_obs_ring_geometry_CORSS_j2000_longitude2_PROF(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    long2 = import_util.safe_column(index_row, 'MAXIMUM_RING_LONGITUDE')

    return long2

def populate_obs_ring_geometry_CORSS_ring_azimuth_wrt_observer1_PROF(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    az1 = import_util.safe_column(index_row, 'MINIMUM_OBSERVED_RING_AZIMUTH')

    return az1

def populate_obs_ring_geometry_CORSS_ring_azimuth_wrt_observer2_PROF(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    az2 = import_util.safe_column(index_row, 'MAXIMUM_OBSERVED_RING_AZIMUTH')

    return az2

def populate_obs_ring_geometry_CORSS_phase1_PROF(**kwargs):
    return 180.

def populate_obs_ring_geometry_CORSS_phase2_PROF(**kwargs):
    return 180.

def populate_obs_ring_geometry_CORSS_incidence1_PROF(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    inc = index_row['MINIMUM_LIGHT_SOURCE_INCIDENCE_ANGLE']

    return inc

def populate_obs_ring_geometry_CORSS_incidence2_PROF(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    inc = index_row['MAXIMUM_LIGHT_SOURCE_INCIDENCE_ANGLE']

    return inc

def populate_obs_ring_geometry_CORSS_north_based_incidence1_PROF(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    el = index_row['MINIMUM_OBSERVED_RING_ELEVATION']

    return 90+el

def populate_obs_ring_geometry_CORSS_north_based_incidence2_PROF(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    el = index_row['MAXIMUM_OBSERVED_RING_ELEVATION']

    return 90+el

def populate_obs_ring_geometry_CORSS_emission1_PROF(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    inc = index_row['MAXIMUM_LIGHT_SOURCE_INCIDENCE_ANGLE']

    return 180-inc

def populate_obs_ring_geometry_CORSS_emission2_PROF(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    inc = index_row['MINIMUM_LIGHT_SOURCE_INCIDENCE_ANGLE']

    return 180-inc

def populate_obs_ring_geometry_CORSS_north_based_emission1_PROF(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    el = index_row['MAXIMUM_OBSERVED_RING_ELEVATION']

    return 90-el

def populate_obs_ring_geometry_CORSS_north_based_emission2_PROF(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    el = index_row['MINIMUM_OBSERVED_RING_ELEVATION']

    return 90-el

# We set the center versions to be the same as the normal versions
populate_obs_ring_geometry_CORSS_center_phase1_PROF = \
    populate_obs_ring_geometry_CORSS_phase1_PROF
populate_obs_ring_geometry_CORSS_center_phase2_PROF = \
    populate_obs_ring_geometry_CORSS_phase2_PROF
populate_obs_ring_geometry_CORSS_center_incidence1_PROF = \
    populate_obs_ring_geometry_CORSS_incidence1_PROF
populate_obs_ring_geometry_CORSS_center_incidence2_PROF = \
    populate_obs_ring_geometry_CORSS_incidence2_PROF
populate_obs_ring_geometry_CORSS_center_emission1_PROF = \
    populate_obs_ring_geometry_CORSS_emission1_PROF
populate_obs_ring_geometry_CORSS_center_emission2_PROF = \
    populate_obs_ring_geometry_CORSS_emission2_PROF
populate_obs_ring_geometry_CORSS_center_north_based_incidence1_PROF = \
    populate_obs_ring_geometry_CORSS_north_based_incidence1_PROF
populate_obs_ring_geometry_CORSS_center_north_based_incidence2_PROF = \
    populate_obs_ring_geometry_CORSS_north_based_incidence2_PROF
populate_obs_ring_geometry_CORSS_center_north_based_emission1_PROF = \
    populate_obs_ring_geometry_CORSS_north_based_emission1_PROF
populate_obs_ring_geometry_CORSS_center_north_based_emission2_PROF = \
    populate_obs_ring_geometry_CORSS_north_based_emission2_PROF

def populate_obs_ring_geometry_CORSS_observer_ring_opening_angle1_PROF(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    el = index_row['MINIMUM_OBSERVED_RING_ELEVATION']

    return el

def populate_obs_ring_geometry_CORSS_observer_ring_opening_angle2_PROF(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    el = index_row['MAXIMUM_OBSERVED_RING_ELEVATION']

    return el

def populate_obs_ring_geometry_CORSS_observer_ring_elevation1_PROF(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    el = index_row['MINIMUM_OBSERVED_RING_ELEVATION']

    return el

def populate_obs_ring_geometry_CORSS_observer_ring_elevation2_PROF(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    el = index_row['MAXIMUM_OBSERVED_RING_ELEVATION']

    return el

def populate_obs_ring_geometry_CORSS_solar_ring_opening_angle1_PROF(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    el = index_row['MAXIMUM_OBSERVED_RING_ELEVATION']

    return -el

def populate_obs_ring_geometry_CORSS_solar_ring_opening_angle2_PROF(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    el = index_row['MINIMUM_OBSERVED_RING_ELEVATION']

    return -el

def populate_obs_ring_geometry_CORSS_solar_ring_elevation1_PROF(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    el = index_row['MAXIMUM_OBSERVED_RING_ELEVATION']

    return -el

def populate_obs_ring_geometry_CORSS_solar_ring_elevation2_PROF(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    el = index_row['MINIMUM_OBSERVED_RING_ELEVATION']

    return -el

def populate_obs_ring_geometry_CORSS_ring_intercept_time1_PROF(**kwargs):
    return populate_time1_from_index(column='RING_EVENT_START_TIME', **kwargs)

def populate_obs_ring_geometry_CORSS_ring_intercept_time2_PROF(**kwargs):
    return populate_time1_from_index(column='RING_EVENT_STOP_TIME', **kwargs)


################################################################################
# THESE NEED TO BE IMPLEMENTED FOR EVERY CASSINI INSTRUMENT
################################################################################

def populate_obs_mission_cassini_CORSS_ert1_PROF(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['supp_index_row']

    # START_TIME isn't available for COUVIS
    start_time = index_row.get('EARTH_RECEIVED_START_TIME', None)
    if start_time is None or start_time == 'UNK':
        return None

    try:
        ert_sec = julian.tai_from_iso(start_time)
    except Exception as e:
        import_util.log_nonrepeating_warning(
            f'Bad earth received start time format "{start_time}": {e}')
        return None

    return ert_sec

def populate_obs_mission_cassini_CORSS_ert2_PROF(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['supp_index_row']

    # STOP_TIME isn't available for COUVIS
    stop_time = index_row.get('EARTH_RECEIVED_STOP_TIME', None)
    if stop_time is None or stop_time == 'UNK':
        return None

    try:
        ert_sec = julian.tai_from_iso(stop_time)
    except Exception as e:
        import_util.log_nonrepeating_warning(
            f'Bad earth received stop time format "{stop_time}": {e}')
        return None

    cassini_row = metadata['obs_mission_cassini_row']
    start_time_sec = cassini_row['ert1']

    if start_time_sec is not None and ert_sec < start_time_sec:
        import_util.log_warning(
            f'cassini_ert1 ({start_time_sec}) and cassini_ert2 ({ert_sec}) '
            +'are in the wrong order - setting to ert1')
        ert_sec = start_time_sec

    return ert_sec

def populate_obs_mission_cassini_CORSS_spacecraft_clock_count1_PROF(**kwargs):
    metadata = kwargs['metadata']
    supp_index_row = metadata['supp_index_row']
    count = supp_index_row['SPACECRAFT_CLOCK_START_COUNT']
    if count == 'UNK':
        return None

    sc = '1/' + str(count)
    try:
        sc_cvt = opus_support.parse_cassini_sclk(sc)
    except Exception as e:
        import_util.log_nonrepeating_warning(
            f'Unable to parse Cassini SCLK "{sc}": {e}')
        return None
    return sc_cvt

def populate_obs_mission_cassini_CORSS_spacecraft_clock_count2_PROF(**kwargs):
    metadata = kwargs['metadata']
    supp_index_row = metadata['supp_index_row']
    count = supp_index_row['SPACECRAFT_CLOCK_STOP_COUNT']
    if count == 'UNK':
        return None

    sc = '1/' + str(count)
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

def populate_obs_mission_cassini_CORSS_mission_phase_name_PROF(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['supp_index_row']
    mp = index_row['MISSION_PHASE_NAME']
    if mp.upper() == 'NULL':
        return None
    return mp.replace('_', ' ')

def populate_obs_mission_cassini_CORSS_sequence_id_PROF(**kwargs):
    return None


################################################################################
# THESE ARE SPECIFIC TO OBS_INSTRUMENT_CORSS
################################################################################
