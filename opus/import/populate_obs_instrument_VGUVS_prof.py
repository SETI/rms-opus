################################################################################
# populate_obs_instrument_VGUVS_occ.py
#
# Routines to populate fields specific to VGUVS.
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

def _VGUVS_file_spec_helper(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']

    file_spec = index_row['FILE_SPECIFICATION_NAME']
    volume_id = kwargs['volume_id']
    return volume_id + '/' + file_spec

def populate_obs_general_VGUVS_opus_id_PROF(**kwargs):
    file_spec = _VGUVS_file_spec_helper(**kwargs)
    pds_file = pdsfile.PdsFile.from_filespec(file_spec, fix_case=True)
    opus_id = pds_file.opus_id
    if not opus_id:
        import_util.log_nonrepeating_error(
            f'Unable to create OPUS_ID for FILE_SPEC "{file_spec}"')
        return file_spec.split('/')[-1]

    return opus_id

def populate_obs_general_VGUVS_ring_obs_id_PROF(**kwargs):
    return None

def populate_obs_general_VGUVS_inst_host_id_PROF(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    inst_host = index_row['INSTRUMENT_HOST_NAME']

    assert inst_host in ['VOYAGER 1', 'VOYAGER 2']

    return 'VG'+inst_host[-1]
    # return 'VG'

# VGUVS time span is the duration of the observation at the spacecraft
def populate_obs_general_VGUVS_time1_PROF(**kwargs):
    return populate_time1_from_index(**kwargs)

def populate_obs_general_VGUVS_time2_PROF(**kwargs):
    return populate_time2_from_index(**kwargs)

def populate_obs_general_VGUVS_target_name_PROF(**kwargs):
    # Get target name from index table
    target_name = populate_target_name_from_index(**kwargs)
    target_name_info = TARGET_NAME_INFO[target_name]
    return target_name, target_name_info[2]

def populate_obs_general_VGUVS_observation_duration_PROF(**kwargs):
    return populate_observation_duration_from_time(**kwargs)

def populate_obs_general_VGUVS_quantity_PROF(**kwargs):
    return 'OPDEPTH'

def populate_obs_general_VGUVS_observation_type_PROF(**kwargs):
    return 'OCC'

def populate_obs_pds_VGUVS_note_PROF(**kwargs):
    return None

def populate_obs_general_VGUVS_primary_file_spec_PROF(**kwargs):
    return _VGUVS_file_spec_helper(**kwargs)

def populate_obs_pds_VGUVS_primary_file_spec_PROF(**kwargs):
    return _VGUVS_file_spec_helper(**kwargs)

def populate_obs_pds_VGUVS_product_creation_time_PROF(**kwargs):
    return populate_product_creation_time_from_supp_index(**kwargs)

# Format: "VG2-SR/UR/NR-UVS-2/4-OCC-V1.0"
def populate_obs_pds_VGUVS_data_set_id_PROF(**kwargs):
    return populate_data_set_id_from_index_label(**kwargs)

# Format: "KM001/UU1P01DE.TAB"
def populate_obs_pds_VGUVS_product_id_PROF(**kwargs):
    return populate_product_id_from_index(**kwargs)

def populate_obs_general_VGUVS_right_asc1_PROF(**kwargs):
    return populate_occ_ra_dec_helper_index(**kwargs)[0]

def populate_obs_general_VGUVS_right_asc2_PROF(**kwargs):
    return populate_occ_ra_dec_helper_index(**kwargs)[1]

def populate_obs_general_VGUVS_declination1_PROF(**kwargs):
    return populate_occ_ra_dec_helper_index(**kwargs)[2]

def populate_obs_general_VGUVS_declination2_PROF(**kwargs):
    return populate_occ_ra_dec_helper_index(**kwargs)[3]


### OBS_TYPE_IMAGE TABLE ###

def populate_obs_type_image_VGUVS_image_type_id_PROF(**kwargs):
    return None

def populate_obs_type_image_VGUVS_duration_PROF(**kwargs):
    return None

def populate_obs_type_image_VGUVS_levels_PROF(**kwargs):
    return None

def populate_obs_type_image_VGUVS_lesser_pixel_size_PROF(**kwargs):
    return None

def populate_obs_type_image_VGUVS_greater_pixel_size_PROF(**kwargs):
    return None


### OBS_WAVELENGTH TABLE ###

def populate_obs_wavelength_VGUVS_wavelength1_PROF(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    wl1 = index_row['MINIMUM_WAVELENGTH']
    return wl1

def populate_obs_wavelength_VGUVS_wavelength2_PROF(**kwargs):
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

def populate_obs_wavelength_VGUVS_wave_res1_PROF(**kwargs):
    return _wave_res_helper(**kwargs)

def populate_obs_wavelength_VGUVS_wave_res2_PROF(**kwargs):
    return _wave_res_helper(**kwargs)

def populate_obs_wavelength_VGUVS_wave_no1_PROF(**kwargs):
    metadata = kwargs['metadata']
    wavelength_row = metadata['obs_wavelength_row']
    wl2 = wavelength_row['wavelength2']
    if wl2 is None:
        return None
    return 10000 / wl2 # cm^-1

def populate_obs_wavelength_VGUVS_wave_no2_PROF(**kwargs):
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

def populate_obs_wavelength_VGUVS_wave_no_res1_PROF(**kwargs):
    return _wave_no_res_helper(**kwargs)

def populate_obs_wavelength_VGUVS_wave_no_res2_PROF(**kwargs):
    return _wave_no_res_helper(**kwargs)

def populate_obs_wavelength_VGUVS_spec_flag_PROF(**kwargs):
    return 'N'

def populate_obs_wavelength_VGUVS_spec_size_PROF(**kwargs):
    return 1

def populate_obs_wavelength_VGUVS_polarization_type_PROF(**kwargs):
    return 'NONE'


### populate_obs_occultation TABLE ###

def populate_obs_occultation_VGUVS_occ_type_PROF(**kwargs):
    return 'STE' # There are no SUN occultations

def populate_obs_occultation_VGUVS_occ_dir_PROF(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    occ_direction = index_row['RING_OCCULTATION_DIRECTION'][0]

    return occ_direction

def populate_obs_occultation_VGUVS_body_occ_flag_PROF(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    body_occ_flag = index_row['PLANETARY_OCCULTATION_FLAG']

    return body_occ_flag

def populate_obs_occultation_VGUVS_optical_depth_min_PROF(**kwargs):
    return None

def populate_obs_occultation_VGUVS_optical_depth_max_PROF(**kwargs):
    return None

def _integration_duration_helper(**kwargs):
    metadata = kwargs['metadata']
    supp_index_row = metadata['supp_index_row']
    dur = supp_index_row['INTEGRATION_DURATION']

    # HSP integration_duration is in milliseconds!
    return dur/1000

def populate_obs_occultation_VGUVS_temporal_sampling_PROF(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    tmp_sampling_interval = index_row['TEMPORAL_SAMPLING_INTERVAL']

    return tmp_sampling_interval

def populate_obs_occultation_VGUVS_quality_score_PROF(**kwargs):
    return None

def populate_obs_occultation_VGUVS_wl_band_PROF(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    wl_band1 = index_row['WAVELENGTH_BAND_1']
    wl_band2 = index_row['WAVELENGTH_BAND_2']
    wl_band = [wl_band1, wl_band2]

    for idx, band in enumerate(wl_band):
        if '-BAND' in band:
            wl_band[idx] = band[0]

    if wl_band2 == 'N/A':
        wl_band = wl_band[0]

    return wl_band

def populate_obs_occultation_VGUVS_source_PROF(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    src_name1 = index_row['SIGNAL_SOURCE_NAME_1']
    src_name2 = index_row['SIGNAL_SOURCE_NAME_2']

    if src_name2 == 'N/A':
        src_name = src_name1
    else:
        src_name = [src_name1, src_name2]

    return src_name

def populate_obs_occultation_VGUVS_host_PROF(**kwargs):
    return 'voyager'


### OBS_RING_GEOMETRY TABLE ###

def populate_obs_ring_geometry_VGUVS_ring_radius1_PROF(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    radius1 = import_util.safe_column(index_row, 'MINIMUM_RING_RADIUS')

    return radius1

def populate_obs_ring_geometry_VGUVS_ring_radius2_PROF(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    radius2 = import_util.safe_column(index_row, 'MAXIMUM_RING_RADIUS')

    return radius2

def populate_obs_ring_geometry_VGUVS_resolution1_PROF(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    res = import_util.safe_column(index_row, 'MINIMUM_RADIAL_RESOLUTION')

    return res

def populate_obs_ring_geometry_VGUVS_resolution2_PROF(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    res = import_util.safe_column(index_row, 'MAXIMUM_RADIAL_RESOLUTION')

    return res

def populate_obs_ring_geometry_VGUVS_proj_resolution1_PROF(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    res = import_util.safe_column(index_row, 'MINIMUM_RADIAL_RESOLUTION')

    return res

def populate_obs_ring_geometry_VGUVS_proj_resolution2_PROF(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    res = import_util.safe_column(index_row, 'MAXIMUM_RADIAL_RESOLUTION')

    return res

def populate_obs_ring_geometry_VGUVS_j2000_longitude1_PROF(**kwargs):
    return None

def populate_obs_ring_geometry_VGUVS_j2000_longitude2_PROF(**kwargs):
    return None

def populate_obs_ring_geometry_VGUVS_ring_azimuth_wrt_observer1_PROF(**kwargs):
    return None

def populate_obs_ring_geometry_VGUVS_ring_azimuth_wrt_observer2_PROF(**kwargs):
    return None

def populate_obs_ring_geometry_VGUVS_phase1_PROF(**kwargs):
    return 180.

def populate_obs_ring_geometry_VGUVS_phase2_PROF(**kwargs):
    return 180.

# Source is star, observer is voyager
# Voyager location: N -> S -> N => Saturn
# Do the same to figure out voyager location for Neptune and Uranus
# Incidence angle: the angle between the point where incoming source photons
# hit the ring, to the north pole of the earth (normal vector
# on the surface of LIT side of the ring, same as source side), always between
# 0 (parallel to north pole) to 90 (parallel to ring)
# We would like to use emission angle to get both min/max of incidence angle.
# Emission angle is 90-180 (dark side), so incidence angle is 180 - emission
# angle.
def populate_obs_ring_geometry_VGUVS_incidence1_PROF(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    el = index_row['INCIDENCE_ANGLE']

    return el

def populate_obs_ring_geometry_VGUVS_incidence2_PROF(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    el = index_row['INCIDENCE_ANGLE']

    return el

# North based ia: the angle between the point where incoming source photons hit
# the ring to the normal vector on the NORTH side of the ring. 0-90 when north
# side of the ring is lit, and 90-180 when south side is lit.
def populate_obs_ring_geometry_VGUVS_north_based_incidence1_PROF(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    el = index_row['INCIDENCE_ANGLE']

    return el

def populate_obs_ring_geometry_VGUVS_north_based_incidence2_PROF(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    el = index_row['INCIDENCE_ANGLE']

    return el

# Emission angle: the angle between the normal vector on the LIT side, to the
# direction where outgoing photons to the observer. 0-90 when observer is at the
# lit side of the ring, and 90-180 when it's at the dark side.
# Since observer is at the dark side, ea is between 90-180
def populate_obs_ring_geometry_VGUVS_emission1_PROF(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    el = index_row['MAXIMUM_EMISSION_ANGLE']

    return el

def populate_obs_ring_geometry_VGUVS_emission2_PROF(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    el = index_row['MAXIMUM_EMISSION_ANGLE']

    return el

# North based ea: the angle between the normal vector on the NORTH side of the
# ring, to the direction where outgoing photons to the observer. 0-90 when
# observer is at the north side of the ring, and 90-180 when it's at the south
# side.
def populate_obs_ring_geometry_VGUVS_north_based_emission1_PROF(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    el = index_row['MAXIMUM_EMISSION_ANGLE']

    return el

def populate_obs_ring_geometry_VGUVS_north_based_emission2_PROF(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    el = index_row['MAXIMUM_EMISSION_ANGLE']

    return el

# We set the center versions to be the same as the normal versions
populate_obs_ring_geometry_VGUVS_center_phase1_PROF = \
    populate_obs_ring_geometry_VGUVS_phase1_PROF
populate_obs_ring_geometry_VGUVS_center_phase2_PROF = \
    populate_obs_ring_geometry_VGUVS_phase2_PROF
populate_obs_ring_geometry_VGUVS_center_incidence1_PROF = \
    populate_obs_ring_geometry_VGUVS_incidence1_PROF
populate_obs_ring_geometry_VGUVS_center_incidence2_PROF = \
    populate_obs_ring_geometry_VGUVS_incidence2_PROF
populate_obs_ring_geometry_VGUVS_center_emission1_PROF = \
    populate_obs_ring_geometry_VGUVS_emission1_PROF
populate_obs_ring_geometry_VGUVS_center_emission2_PROF = \
    populate_obs_ring_geometry_VGUVS_emission2_PROF
populate_obs_ring_geometry_VGUVS_center_north_based_incidence1_PROF = \
    populate_obs_ring_geometry_VGUVS_north_based_incidence1_PROF
populate_obs_ring_geometry_VGUVS_center_north_based_incidence2_PROF = \
    populate_obs_ring_geometry_VGUVS_north_based_incidence2_PROF
populate_obs_ring_geometry_VGUVS_center_north_based_emission1_PROF = \
    populate_obs_ring_geometry_VGUVS_north_based_emission1_PROF
populate_obs_ring_geometry_VGUVS_center_north_based_emission2_PROF = \
    populate_obs_ring_geometry_VGUVS_north_based_emission2_PROF


# Opening angle to observer: the angle between the ring surface to the direction
# where outgoing photons to the observer. Positive if observer is at the north
# side of the ring , negative if it's at the south side. In this case, observer
# is at the north side, so it's 90 - ea. For reference, if observer is at the
# south side, then oa is 90 - 180 - ea.
def populate_obs_ring_geometry_VGUVS_observer_ring_opening_angle1_PROF(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    el = index_row['INCIDENCE_ANGLE']

    return el

def populate_obs_ring_geometry_VGUVS_observer_ring_opening_angle2_PROF(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    el = index_row['INCIDENCE_ANGLE']

    return el

# Ring elevation to observer, same to opening angle except, it's positive if
# observer is at north side of Jupiter, Saturn, and Neptune, and south side of
# Uranus. Negative if observer is at south side of Jupiter, Saturn, and Neptune,
# and north side of Uranus.
def populate_obs_ring_geometry_VGUVS_observer_ring_elevation1_PROF(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    el = index_row['INCIDENCE_ANGLE']

    return el

def populate_obs_ring_geometry_VGUVS_observer_ring_elevation2_PROF(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    el = index_row['INCIDENCE_ANGLE']

    return el

# Opening angle to solar: the angle between the ring surface to the direction
# where incoming photons from the source. Positive if source is at the north
# side of the ring , negative if it's at the south side. In this case, source
# is at the north side, so it's 90 - inc. For reference, if source is at the
# south side, then oa is - (90 - inc).
def populate_obs_ring_geometry_VGUVS_solar_ring_opening_angle1_PROF(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    el = index_row['INCIDENCE_ANGLE']

    return -el

def populate_obs_ring_geometry_VGUVS_solar_ring_opening_angle2_PROF(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    el = index_row['INCIDENCE_ANGLE']

    return -el

# Ring elevation to solar, same to opening angle except, it's positive if
# source is at north side of Jupiter, Saturn, and Neptune, and south side of
# Uranus. Negative if source is at south side of Jupiter, Saturn, and Neptune,
# and north side of Uranus.
def populate_obs_ring_geometry_VGUVS_solar_ring_elevation1_PROF(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    el = index_row['INCIDENCE_ANGLE']

    return -el

def populate_obs_ring_geometry_VGUVS_solar_ring_elevation2_PROF(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    el = index_row['INCIDENCE_ANGLE']

    return -el

def populate_obs_ring_geometry_VGUVS_ring_intercept_time1_PROF(**kwargs):
    return populate_time1_from_index(column='RING_EVENT_START_TIME', **kwargs)

def populate_obs_ring_geometry_VGUVS_ring_intercept_time2_PROF(**kwargs):
    return populate_time1_from_index(column='RING_EVENT_STOP_TIME', **kwargs)


################################################################################
# THESE NEED TO BE IMPLEMENTED FOR EVERY voyager INSTRUMENT
################################################################################

def populate_obs_mission_voyager_VGUVS_mission_phase_name_PROF(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    target_name = index_row['TARGET_NAME'].upper()
    mp = VG_TARGET_TO_MISSION_PHASE_MAPPING[target_name]

    return mp


################################################################################
# THESE ARE SPECIFIC TO OBS_INSTRUMENT_VGUVS
################################################################################

def populate_obs_instrument_VGUVS_observation_type_PROF(**kwargs):
    return 'Occultation Profile'
