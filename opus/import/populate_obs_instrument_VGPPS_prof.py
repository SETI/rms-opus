################################################################################
# populate_obs_instrument_VGPPS_prof.py
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

def populate_obs_general_VGPPS_opus_id_PROF(**kwargs):
    file_spec = _VGPPS_file_spec_helper(**kwargs)
    pds_file = pdsfile.PdsFile.from_filespec(file_spec, fix_case=True)
    opus_id = pds_file.opus_id
    if not opus_id:
        import_util.log_nonrepeating_error(
            f'Unable to create OPUS_ID for FILE_SPEC "{file_spec}"')
        return file_spec.split('/')[-1]

    return opus_id

def populate_obs_general_VGPPS_ring_obs_id_PROF(**kwargs):
    return None

def populate_obs_general_VGPPS_inst_host_id_PROF(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    inst_host = index_row['INSTRUMENT_HOST_NAME']

    assert inst_host in ['VOYAGER 1', 'VOYAGER 2']

    return 'VG'+inst_host[-1]

# VGPPS time span is the duration of the observation at the spacecraft
def populate_obs_general_VGPPS_time1_PROF(**kwargs):
    return populate_time1_from_index(**kwargs)

def populate_obs_general_VGPPS_time2_PROF(**kwargs):
    return populate_time2_from_index(**kwargs)

def populate_obs_general_VGPPS_target_name_PROF(**kwargs):
    # Get target name from index table
    target_name = populate_target_name_from_index(**kwargs)
    target_name_info = TARGET_NAME_INFO[target_name]
    return target_name, target_name_info[2]

def populate_obs_general_VGPPS_observation_duration_PROF(**kwargs):
    return populate_observation_duration_from_time(**kwargs)

def populate_obs_general_VGPPS_quantity_PROF(**kwargs):
    return 'OPDEPTH'

def populate_obs_general_VGPPS_observation_type_PROF(**kwargs):
    return 'OCC'

def populate_obs_pds_VGPPS_note_PROF(**kwargs):
    return None

def populate_obs_general_VGPPS_primary_file_spec_PROF(**kwargs):
    return _VGPPS_file_spec_helper(**kwargs)

def populate_obs_pds_VGPPS_primary_file_spec_PROF(**kwargs):
    return _VGPPS_file_spec_helper(**kwargs)

def populate_obs_pds_VGPPS_product_creation_time_PROF(**kwargs):
    return populate_product_creation_time_from_supp_index(**kwargs)

# Format: "VG2-SR/UR/NR-PPS-2/4-OCC-V1.0"
def populate_obs_pds_VGPPS_data_set_id_PROF(**kwargs):
    return populate_data_set_id_from_index_label(**kwargs)

# Format: "KM001/PU2P016I.TAB"
def populate_obs_pds_VGPPS_product_id_PROF(**kwargs):
    return populate_product_id_from_index(**kwargs)

def populate_obs_general_VGPPS_right_asc1_PROF(**kwargs):
    return populate_occ_ra_dec_helper_index(**kwargs)[0]

def populate_obs_general_VGPPS_right_asc2_PROF(**kwargs):
    return populate_occ_ra_dec_helper_index(**kwargs)[1]

def populate_obs_general_VGPPS_declination1_PROF(**kwargs):
    return populate_occ_ra_dec_helper_index(**kwargs)[2]

def populate_obs_general_VGPPS_declination2_PROF(**kwargs):
    return populate_occ_ra_dec_helper_index(**kwargs)[3]


### OBS_TYPE_IMAGE TABLE ###

def populate_obs_type_image_VGPPS_image_type_id_PROF(**kwargs):
    return None

def populate_obs_type_image_VGPPS_duration_PROF(**kwargs):
    return None

def populate_obs_type_image_VGPPS_levels_PROF(**kwargs):
    return None

def populate_obs_type_image_VGPPS_lesser_pixel_size_PROF(**kwargs):
    return None

def populate_obs_type_image_VGPPS_greater_pixel_size_PROF(**kwargs):
    return None


### OBS_WAVELENGTH TABLE ###

def populate_obs_wavelength_VGPPS_wavelength1_PROF(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['supp_index_row']
    wl1 = index_row['MINIMUM_WAVELENGTH']
    return wl1

def populate_obs_wavelength_VGPPS_wavelength2_PROF(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['supp_index_row']
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

def populate_obs_wavelength_VGPPS_wave_res1_PROF(**kwargs):
    return _wave_res_helper(**kwargs)

def populate_obs_wavelength_VGPPS_wave_res2_PROF(**kwargs):
    return _wave_res_helper(**kwargs)

def populate_obs_wavelength_VGPPS_wave_no1_PROF(**kwargs):
    metadata = kwargs['metadata']
    wavelength_row = metadata['obs_wavelength_row']
    wl2 = wavelength_row['wavelength2']
    if wl2 is None:
        return None
    return 10000 / wl2 # cm^-1

def populate_obs_wavelength_VGPPS_wave_no2_PROF(**kwargs):
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

def populate_obs_wavelength_VGPPS_wave_no_res1_PROF(**kwargs):
    return _wave_no_res_helper(**kwargs)

def populate_obs_wavelength_VGPPS_wave_no_res2_PROF(**kwargs):
    return _wave_no_res_helper(**kwargs)

def populate_obs_wavelength_VGPPS_spec_flag_PROF(**kwargs):
    return 'N'

def populate_obs_wavelength_VGPPS_spec_size_PROF(**kwargs):
    return 1

def populate_obs_wavelength_VGPPS_polarization_type_PROF(**kwargs):
    return 'NONE'


### OBS_PROFILE TABLE ###

def populate_obs_occultation_VGPPS_occ_type_PROF(**kwargs):
    return 'STE' # There are no SUN occultations

def populate_obs_occultation_VGPPS_occ_dir_PROF(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    occ_direction = index_row['RING_OCCULTATION_DIRECTION'][0]

    return occ_direction

def populate_obs_occultation_VGPPS_body_occ_flag_PROF(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    body_occ_flag = index_row['PLANETARY_OCCULTATION_FLAG']

    return body_occ_flag

def populate_obs_occultation_VGPPS_optical_depth_min_PROF(**kwargs):
    return None

def populate_obs_occultation_VGPPS_optical_depth_max_PROF(**kwargs):
    return None

def populate_obs_occultation_VGPPS_temporal_sampling_PROF(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['supp_index_row']
    tmp_sampling_interval = index_row['TEMPORAL_SAMPLING_INTERVAL']

    return tmp_sampling_interval

def populate_obs_occultation_VGPPS_quality_score_PROF(**kwargs):
    return 'GOOD'

def populate_obs_occultation_VGPPS_wl_band_PROF(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    wl_band1 = index_row['WAVELENGTH_BAND_1']
    wl_band2 = index_row['WAVELENGTH_BAND_2']

    if wl_band2 != 'N/A':
        assert wl1_band1 == wl2_band2, 'Mismatched wl_band1 and wl_band2.'
    if '-BAND' in wl_band1:
        wl_band1 = wl_band1[0]

    return wl_band1

def populate_obs_occultation_VGPPS_source_PROF(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    src_name1 = index_row['SIGNAL_SOURCE_NAME_1']
    src_name2 = index_row['SIGNAL_SOURCE_NAME_2']

    if src_name2 != 'N/A':
        assert src_name1 == src_name2, 'Mismatched src_name1 and src_name2.'

    return src_name1

def populate_obs_occultation_VGPPS_host_PROF(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    receiver_host = index_row['RECEIVER_HOST_NAME']

    return receiver_host


### OBS_RING_GEOMETRY TABLE ###

def populate_obs_ring_geometry_VGPPS_ring_radius1_PROF(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    radius1 = import_util.safe_column(index_row, 'MINIMUM_RING_RADIUS')

    return radius1

def populate_obs_ring_geometry_VGPPS_ring_radius2_PROF(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    radius2 = import_util.safe_column(index_row, 'MAXIMUM_RING_RADIUS')

    return radius2

def populate_obs_ring_geometry_VGPPS_resolution1_PROF(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    res = import_util.safe_column(index_row, 'MINIMUM_RADIAL_RESOLUTION')

    return res

def populate_obs_ring_geometry_VGPPS_resolution2_PROF(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    res = import_util.safe_column(index_row, 'MAXIMUM_RADIAL_RESOLUTION')

    return res

def populate_obs_ring_geometry_VGPPS_proj_resolution1_PROF(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    res = import_util.safe_column(index_row, 'MINIMUM_RADIAL_RESOLUTION')

    return res

def populate_obs_ring_geometry_VGPPS_proj_resolution2_PROF(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    res = import_util.safe_column(index_row, 'MAXIMUM_RADIAL_RESOLUTION')

    return res

def populate_obs_ring_geometry_VGPPS_j2000_longitude1_PROF(**kwargs):
    return None

def populate_obs_ring_geometry_VGPPS_j2000_longitude2_PROF(**kwargs):
    return None

def populate_obs_ring_geometry_VGPPS_ring_azimuth_wrt_observer1_PROF(**kwargs):
    return None

def populate_obs_ring_geometry_VGPPS_ring_azimuth_wrt_observer2_PROF(**kwargs):
    return None

def populate_obs_ring_geometry_VGPPS_phase1_PROF(**kwargs):
    return 180.

def populate_obs_ring_geometry_VGPPS_phase2_PROF(**kwargs):
    return 180.

# Source is star, observer is Voyager
# Source DELTA SCO is at south, observer Voyager is at north. Target: S ring.
# Source SIGMA SGR is at south, observer Voyager is at north. Target: U ring.
# Source SIGMA SGR is at north, observer Voyager is at south. Target: N ring.
# Source BETA PER is at north, observer Voyager is at south. Target: U ring.

# Incidence angle: The angle between the point where the incoming source
# photos hit the ring and the normal to the ring plane on the LIT side of
# the ring. This is always between 0 (parallel to the normal vector) and 90
# (parallel to the ring plane)
# We would like to use emission angle to get both min/max of incidence angle.
# Emission angle is 90-180 (dark side), so incidence angle is 180 - emission
# angle.
def populate_obs_ring_geometry_VGPPS_incidence1_PROF(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    inc = index_row['INCIDENCE_ANGLE']

    max_ea = index_row['MAXIMUM_EMISSION_ANGLE']
    cal_inc = 180 - max_ea
    msg = ('The difference between incidence angle and 180 - emission is' +
           ' more than 0.005, volume: VG_2801.')
    assert abs(cal_inc - inc) <= 0.005, msg
    return 180. - max_ea

def populate_obs_ring_geometry_VGPPS_incidence2_PROF(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    inc = index_row['INCIDENCE_ANGLE']

    min_ea = index_row['MINIMUM_EMISSION_ANGLE']
    cal_inc = 180 - min_ea
    msg = ('The difference between incidence angle and 180 - emission is' +
           ' more than 0.005, volume: VG_2801.')
    assert abs(cal_inc - inc) <= 0.005, msg
    return 180. - min_ea

def _is_voyager_at_north(**kwargs):
    """In this volume,
    Voyager is at north when: (start time before 1986-01-24T17:10:13.320)
        - Source is DELTA SCO (Target S RINGS)
        - Source is SIGMA SGR (Target U RINGS)
    Voyager is south when: (start time after 1986-01-24T17:10:13.320)
        - Source is SIGMA SGR (Target N RINGS)
        - Source is BETA PER (Target U RINGS)
    Note: threshold value 1986-01-24T17:10:13.320 is obtained and determined by
    observing the results from OPUS.
    """
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    src_name = index_row['SIGNAL_SOURCE_NAME_1']
    target_name = index_row['TARGET_NAME'].upper().strip()

    start_time = julian.tai_from_iso(index_row['START_TIME'])
    threshold = julian.tai_from_iso(THRESHOLD_START_TIME_VG_AT_NORTH)
    msg = "Observation start time and Voyager location don't match."

    isAtNorth = (src_name == 'DELTA SCO'
                 or (src_name == 'SIGMA SGR' and target_name == 'U RINGS'))
    # Check if the start time match the Voyager location.
    if isAtNorth:
        assert start_time <= threshold, msg
    else:
        assert start_time > threshold, msg
    return isAtNorth

def _is_voyager_at_north_except_uranus(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    src_name = index_row['SIGNAL_SOURCE_NAME_1']

    start_time = julian.tai_from_iso(index_row['START_TIME'])
    threshold = julian.tai_from_iso(THRESHOLD_START_TIME_VG_AT_NORTH)
    msg = "Observation start time and Voyager location don't match."

    isAtNorth = (src_name == 'DELTA SCO')
    # Check if the start time match the Voyager location.
    if isAtNorth:
        assert start_time <= threshold, msg
    else:
        assert start_time > threshold, msg
    return isAtNorth


# North based inc: the angle between the point where incoming source photons hit
# the ring to the normal vector on the NORTH side of the ring. 0-90 when north
# side of the ring is lit, and 90-180 when south side is lit.
def populate_obs_ring_geometry_VGPPS_north_based_incidence1_PROF(**kwargs):
    if _is_voyager_at_north(**kwargs):
        inc = populate_obs_ring_geometry_VGPPS_incidence2_PROF(**kwargs)
        return 180. - inc
    else:
        inc = populate_obs_ring_geometry_VGPPS_incidence1_PROF(**kwargs)
        return inc

def populate_obs_ring_geometry_VGPPS_north_based_incidence2_PROF(**kwargs):
    if _is_voyager_at_north(**kwargs):
        inc = populate_obs_ring_geometry_VGPPS_incidence1_PROF(**kwargs)
        return 180. - inc
    else:
        inc = populate_obs_ring_geometry_VGPPS_incidence2_PROF(**kwargs)
        return inc

# Emission angle: the angle between the normal vector on the LIT side, to the
# direction where outgoing photons to the observer. 0-90 when observer is at the
# lit side of the ring, and 90-180 when it's at the dark side.
# Since observer is at the dark side, ea is between 90-180
def populate_obs_ring_geometry_VGPPS_emission1_PROF(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    min_ea = index_row['MINIMUM_EMISSION_ANGLE']

    return min_ea

def populate_obs_ring_geometry_VGPPS_emission2_PROF(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    max_ea = index_row['MAXIMUM_EMISSION_ANGLE']

    return max_ea

# North based ea: the angle between the normal vector on the NORTH side of the
# ring, to the direction where outgoing photons to the observer. 0-90 when
# observer is at the north side of the ring, and 90-180 when it's at the south
# side.
def populate_obs_ring_geometry_VGPPS_north_based_emission1_PROF(**kwargs):
    if _is_voyager_at_north(**kwargs):
        max_ea = populate_obs_ring_geometry_VGPPS_emission2_PROF(**kwargs)
        ea = 180. - max_ea
    else:
        ea = populate_obs_ring_geometry_VGPPS_emission1_PROF(**kwargs)

    return ea

def populate_obs_ring_geometry_VGPPS_north_based_emission2_PROF(**kwargs):
    if _is_voyager_at_north(**kwargs):
        min_ea = populate_obs_ring_geometry_VGPPS_emission1_PROF(**kwargs)
        ea = 180. - min_ea
    else:
        ea = populate_obs_ring_geometry_VGPPS_emission2_PROF(**kwargs)

    return ea

# We set the center versions to be the same as the normal versions
populate_obs_ring_geometry_VGPPS_center_phase1_PROF = \
    populate_obs_ring_geometry_VGPPS_phase1_PROF
populate_obs_ring_geometry_VGPPS_center_phase2_PROF = \
    populate_obs_ring_geometry_VGPPS_phase2_PROF
populate_obs_ring_geometry_VGPPS_center_incidence1_PROF = \
    populate_obs_ring_geometry_VGPPS_incidence1_PROF
populate_obs_ring_geometry_VGPPS_center_incidence2_PROF = \
    populate_obs_ring_geometry_VGPPS_incidence2_PROF
populate_obs_ring_geometry_VGPPS_center_emission1_PROF = \
    populate_obs_ring_geometry_VGPPS_emission1_PROF
populate_obs_ring_geometry_VGPPS_center_emission2_PROF = \
    populate_obs_ring_geometry_VGPPS_emission2_PROF
populate_obs_ring_geometry_VGPPS_center_north_based_incidence1_PROF = \
    populate_obs_ring_geometry_VGPPS_north_based_incidence1_PROF
populate_obs_ring_geometry_VGPPS_center_north_based_incidence2_PROF = \
    populate_obs_ring_geometry_VGPPS_north_based_incidence2_PROF
populate_obs_ring_geometry_VGPPS_center_north_based_emission1_PROF = \
    populate_obs_ring_geometry_VGPPS_north_based_emission1_PROF
populate_obs_ring_geometry_VGPPS_center_north_based_emission2_PROF = \
    populate_obs_ring_geometry_VGPPS_north_based_emission2_PROF

# Opening angle to observer: the angle between the ring surface to the direction
# where outgoing photons to the observer. Positive if observer is at the north
# side of the ring, negative if it's at the south side. If observer is at the
# north side, it's ea - 90 (or 90 - inc). If observer is at the south side,
# then oa is 90 - ea.
def populate_obs_ring_geometry_VGPPS_observer_ring_opening_angle1_PROF(**kwargs):
    if _is_voyager_at_north(**kwargs):
        min_ea = populate_obs_ring_geometry_VGPPS_emission1_PROF(**kwargs)
        return min_ea - 90.
    else:
        max_ea = populate_obs_ring_geometry_VGPPS_emission2_PROF(**kwargs)
        return 90. - max_ea

def populate_obs_ring_geometry_VGPPS_observer_ring_opening_angle2_PROF(**kwargs):
    if _is_voyager_at_north(**kwargs):
        max_ea = populate_obs_ring_geometry_VGPPS_emission2_PROF(**kwargs)
        return max_ea - 90.
    else:
        min_ea = populate_obs_ring_geometry_VGPPS_emission1_PROF(**kwargs)
        return 90. - min_ea

# Ring elevation to observer, same to opening angle except, it's positive if
# observer is at north side of Jupiter, Saturn, and Neptune, and south side of
# Uranus. Negative if observer is at south side of Jupiter, Saturn, and Neptune,
# and north side of Uranus.
def populate_obs_ring_geometry_VGPPS_observer_ring_elevation1_PROF(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    max_ea = index_row['MAXIMUM_EMISSION_ANGLE']
    min_ea = index_row['MINIMUM_EMISSION_ANGLE']
    if _is_voyager_at_north_except_uranus(**kwargs):
        el = min_ea - 90. # positive
    else:
        el = 90. - max_ea # negative

    return el

def populate_obs_ring_geometry_VGPPS_observer_ring_elevation2_PROF(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    max_ea = index_row['MAXIMUM_EMISSION_ANGLE']
    min_ea = index_row['MINIMUM_EMISSION_ANGLE']
    if _is_voyager_at_north_except_uranus(**kwargs):
        el = max_ea - 90. # positive
    else:
        el = 90. - min_ea # negative

    return el

# Opening angle to Sun: the angle between the ring surface to the direction
# where incoming photons from the source. Positive if source is at the north
# side of the ring , negative if it's at the south side. In this case, source
# is at the north side, so it's 90 - inc. For reference, if source is at the
# south side, then oa is - (90 - inc).
def populate_obs_ring_geometry_VGPPS_solar_ring_opening_angle1_PROF(**kwargs):
    if _is_voyager_at_north(**kwargs):
        inc = populate_obs_ring_geometry_VGPPS_incidence1_PROF(**kwargs)
        return inc - 90.
    else:
        inc = populate_obs_ring_geometry_VGPPS_incidence2_PROF(**kwargs)
        return 90. - inc

def populate_obs_ring_geometry_VGPPS_solar_ring_opening_angle2_PROF(**kwargs):
    if _is_voyager_at_north(**kwargs):
        inc = populate_obs_ring_geometry_VGPPS_incidence2_PROF(**kwargs)
        return inc - 90.
    else:
        inc = populate_obs_ring_geometry_VGPPS_incidence1_PROF(**kwargs)
        return 90. - inc

# Ring elevation to Sun, same to opening angle except, it's positive if
# source is at north side of Jupiter, Saturn, and Neptune, and south side of
# Uranus. Negative if source is at south side of Jupiter, Saturn, and Neptune,
# and north side of Uranus.
def populate_obs_ring_geometry_VGPPS_solar_ring_elevation1_PROF(**kwargs):
    if _is_voyager_at_north_except_uranus(**kwargs):
        inc = populate_obs_ring_geometry_VGPPS_incidence1_PROF(**kwargs)
        el = inc - 90. # negative
    else:
        inc = populate_obs_ring_geometry_VGPPS_incidence2_PROF(**kwargs)
        el = 90. - inc # positive

    return el

def populate_obs_ring_geometry_VGPPS_solar_ring_elevation2_PROF(**kwargs):
    if _is_voyager_at_north_except_uranus(**kwargs):
        inc = populate_obs_ring_geometry_VGPPS_incidence2_PROF(**kwargs)
        el = inc - 90. # negative
    else:
        inc = populate_obs_ring_geometry_VGPPS_incidence1_PROF(**kwargs)
        el = 90. - inc # positive

    return el

def populate_obs_ring_geometry_VGPPS_ring_intercept_time1_PROF(**kwargs):
    return populate_time1_from_index(column='RING_EVENT_START_TIME', **kwargs)

def populate_obs_ring_geometry_VGPPS_ring_intercept_time2_PROF(**kwargs):
    return populate_time1_from_index(column='RING_EVENT_STOP_TIME', **kwargs)


################################################################################
# THESE NEED TO BE IMPLEMENTED FOR EVERY VOYAGER INSTRUMENT
################################################################################

def populate_obs_mission_voyager_VGPPS_mission_phase_name_PROF(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    target_name = index_row['TARGET_NAME'].upper().strip()
    mp = VG_TARGET_TO_MISSION_PHASE_MAPPING[target_name]

    return mp


################################################################################
# THESE ARE SPECIFIC TO OBS_INSTRUMENT_VGPPS
################################################################################

def populate_obs_instrument_VGPPS_observation_type_PROF(**kwargs):
    return 'Occultation Profile'
