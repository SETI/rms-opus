################################################################################
# populate_obs_instrument_VGISS_prof.py
#
# Routines to populate fields specific to VGISS.
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

def _VGISS_file_spec_helper(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']

    file_spec = index_row['FILE_SPECIFICATION_NAME']
    volume_id = kwargs['volume_id']
    return volume_id + '/' + file_spec

def populate_obs_general_VGISS_opus_id_PROF(**kwargs):
    file_spec = _VGISS_file_spec_helper(**kwargs)
    pds_file = pdsfile.PdsFile.from_filespec(file_spec, fix_case=True)
    opus_id = pds_file.opus_id
    if not opus_id:
        import_util.log_nonrepeating_error(
            f'Unable to create OPUS_ID for FILE_SPEC "{file_spec}"')
        return file_spec.split('/')[-1]

    return opus_id

def populate_obs_general_VGISS_ring_obs_id_PROF(**kwargs):
    return None

def populate_obs_general_VGISS_inst_host_id_PROF(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    inst_host = index_row['INSTRUMENT_HOST_NAME']

    assert inst_host in ['VOYAGER 1', 'VOYAGER 2']

    return 'VG'+inst_host[-1]

# VGISS time span is the duration of the observation at the spacecraft
def populate_obs_general_VGISS_time1_PROF(**kwargs):
    return populate_time1_from_index(**kwargs)

def populate_obs_general_VGISS_time2_PROF(**kwargs):
    return populate_time2_from_index(**kwargs)

def populate_obs_general_VGISS_target_name_PROF(**kwargs):
    # Get target name from index table
    target_name = populate_target_name_from_index(**kwargs)
    target_name_info = TARGET_NAME_INFO[target_name]
    return target_name, target_name_info[2]

def populate_obs_general_VGISS_observation_duration_PROF(**kwargs):
    return populate_observation_duration_from_time(**kwargs)

def populate_obs_general_VGISS_quantity_PROF(**kwargs):
    return 'REFLECT'

def populate_obs_general_VGISS_observation_type_PROF(**kwargs):
    # Reflectance
    return 'REF'

def populate_obs_pds_VGISS_note_PROF(**kwargs):
    return None

def populate_obs_general_VGISS_primary_file_spec_PROF(**kwargs):
    return _VGISS_file_spec_helper(**kwargs)

def populate_obs_pds_VGISS_primary_file_spec_PROF(**kwargs):
    return _VGISS_file_spec_helper(**kwargs)

def populate_obs_pds_VGISS_product_creation_time_PROF(**kwargs):
    return populate_product_creation_time_from_supp_index(**kwargs)

# Format: "VG2-SR/UR/NR-ISS-2/4-OCC-V1.0"
def populate_obs_pds_VGISS_data_set_id_PROF(**kwargs):
    return populate_data_set_id_from_index_label(**kwargs)

# Format: "KM001/UU1P01DE.TAB"
def populate_obs_pds_VGISS_product_id_PROF(**kwargs):
    return populate_product_id_from_index(**kwargs)

def populate_obs_general_VGISS_right_asc1_PROF(**kwargs):
    return None

def populate_obs_general_VGISS_right_asc2_PROF(**kwargs):
    return None

def populate_obs_general_VGISS_declination1_PROF(**kwargs):
    return None

def populate_obs_general_VGISS_declination2_PROF(**kwargs):
    return None


### OBS_TYPE_IMAGE TABLE ###

def populate_obs_type_image_VGISS_image_type_id_PROF(**kwargs):
    return 'Frame'

def populate_obs_type_image_VGISS_duration_PROF(**kwargs):
    return 0.72

def populate_obs_type_image_VGISS_levels_PROF(**kwargs):
    return 255

def populate_obs_type_image_VGISS_lesser_pixel_size_PROF(**kwargs):
    return 800

def populate_obs_type_image_VGISS_greater_pixel_size_PROF(**kwargs):
    return 800


### OBS_WAVELENGTH TABLE ###

def populate_obs_wavelength_VGISS_wavelength1_PROF(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    wl1 = index_row['MINIMUM_WAVELENGTH']
    return wl1

def populate_obs_wavelength_VGISS_wavelength2_PROF(**kwargs):
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

def populate_obs_wavelength_VGISS_wave_res1_PROF(**kwargs):
    return _wave_res_helper(**kwargs)

def populate_obs_wavelength_VGISS_wave_res2_PROF(**kwargs):
    return _wave_res_helper(**kwargs)

def populate_obs_wavelength_VGISS_wave_no1_PROF(**kwargs):
    metadata = kwargs['metadata']
    wavelength_row = metadata['obs_wavelength_row']
    wl2 = wavelength_row['wavelength2']
    if wl2 is None:
        return None
    return 10000 / wl2 # cm^-1

def populate_obs_wavelength_VGISS_wave_no2_PROF(**kwargs):
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

def populate_obs_wavelength_VGISS_wave_no_res1_PROF(**kwargs):
    return _wave_no_res_helper(**kwargs)

def populate_obs_wavelength_VGISS_wave_no_res2_PROF(**kwargs):
    return _wave_no_res_helper(**kwargs)

def populate_obs_wavelength_VGISS_spec_flag_PROF(**kwargs):
    return 'N'

def populate_obs_wavelength_VGISS_spec_size_PROF(**kwargs):
    return 1

def populate_obs_wavelength_VGISS_polarization_type_PROF(**kwargs):
    return 'NONE'


### OBS_PROFILE TABLE ###

def populate_obs_occultation_VGISS_occ_type_PROF(**kwargs):
    # Reflectance
    return 'REF'

def populate_obs_occultation_VGISS_occ_dir_PROF(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']

    occ_direction = index_row['RING_OCCULTATION_DIRECTION']
    if 'N/A' in occ_direction:
        return None
    return occ_direction[0]

def populate_obs_occultation_VGISS_body_occ_flag_PROF(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    body_occ_flag = index_row['PLANETARY_OCCULTATION_FLAG']

    return body_occ_flag

def populate_obs_occultation_VGISS_optical_depth_min_PROF(**kwargs):
    return None

def populate_obs_occultation_VGISS_optical_depth_max_PROF(**kwargs):
    return None

def populate_obs_occultation_VGISS_temporal_sampling_PROF(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    tmp_sampling_interval = index_row['TEMPORAL_SAMPLING_INTERVAL']

    return tmp_sampling_interval

def populate_obs_occultation_VGISS_quality_score_PROF(**kwargs):
    return 'GOOD'

def populate_obs_occultation_VGISS_wl_band_PROF(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    wl_band1 = index_row['WAVELENGTH_BAND_1']
    wl_band2 = index_row['WAVELENGTH_BAND_2']

    if wl_band2 != 'N/A':
        assert wl1_band1 == wl2_band2, 'Mismatched wl_band1 and wl_band2.'
    if '-BAND' in wl_band1:
        wl_band1 = wl_band1[0]
    if 'VISUAL' in wl_band1:
        wl_band1 = 'VI'

    return wl_band1

def populate_obs_occultation_VGISS_source_PROF(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    src_name1 = index_row['SIGNAL_SOURCE_NAME_1']
    src_name2 = index_row['SIGNAL_SOURCE_NAME_2']

    if src_name2 != 'N/A':
        assert src_name1 == src_name2, 'Mismatched src_name1 and src_name2.'

    return src_name1

def populate_obs_occultation_VGISS_host_PROF(**kwargs):
    return 'voyager'


### OBS_RING_GEOMETRY TABLE ###

def populate_obs_ring_geometry_VGISS_ring_radius1_PROF(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    radius1 = import_util.safe_column(index_row, 'MINIMUM_RING_RADIUS')

    return radius1

def populate_obs_ring_geometry_VGISS_ring_radius2_PROF(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    radius2 = import_util.safe_column(index_row, 'MAXIMUM_RING_RADIUS')

    return radius2

def populate_obs_ring_geometry_VGISS_resolution1_PROF(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    res = import_util.safe_column(index_row, 'MINIMUM_RADIAL_RESOLUTION')

    return res

def populate_obs_ring_geometry_VGISS_resolution2_PROF(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    res = import_util.safe_column(index_row, 'MAXIMUM_RADIAL_RESOLUTION')

    return res

def populate_obs_ring_geometry_VGISS_proj_resolution1_PROF(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    res = import_util.safe_column(index_row, 'MINIMUM_RADIAL_RESOLUTION')

    return res

def populate_obs_ring_geometry_VGISS_proj_resolution2_PROF(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    res = import_util.safe_column(index_row, 'MAXIMUM_RADIAL_RESOLUTION')

    return res

def populate_obs_ring_geometry_VGISS_j2000_longitude1_PROF(**kwargs):
    return None

def populate_obs_ring_geometry_VGISS_j2000_longitude2_PROF(**kwargs):
    return None

def populate_obs_ring_geometry_VGISS_ring_azimuth_wrt_observer1_PROF(**kwargs):
    return None

def populate_obs_ring_geometry_VGISS_ring_azimuth_wrt_observer2_PROF(**kwargs):
    return None

def populate_obs_ring_geometry_VGISS_phase1_PROF(**kwargs):
    return 180.

def populate_obs_ring_geometry_VGISS_phase2_PROF(**kwargs):
    return 180.

# Source: Sun, observer: earth, both of them are at the north side.
# Incidence angle: the angle between the point where incoming source photons
# hit the ring, to the north pole of the planet we're looking at (normal vector
# on the surface of LIT side of the ring, same as source side), always between
# 0 (parallel to north pole) to 90 (parallel to ring)
def populate_obs_ring_geometry_VGISS_incidence1_PROF(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    inc = index_row['INCIDENCE_ANGLE']

    return inc

def populate_obs_ring_geometry_VGISS_incidence2_PROF(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    inc = index_row['INCIDENCE_ANGLE']

    return inc

# North based inc: the angle between the point where incoming source photons hit
# the ring to the normal vector on the NORTH side of the ring. 0-90 when north
# side of the ring is lit, and 90-180 when south side is lit.
def populate_obs_ring_geometry_VGISS_north_based_incidence1_PROF(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    inc = index_row['INCIDENCE_ANGLE']

    return inc

def populate_obs_ring_geometry_VGISS_north_based_incidence2_PROF(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    inc = index_row['INCIDENCE_ANGLE']

    return inc

# Emission angle: the angle between the normal vector on the LIT side, to the
# direction where outgoing photons to the observer. 0-90 when observer is at the
# lit side of the ring, and 90-180 when it's at the dark side.
def populate_obs_ring_geometry_VGISS_emission1_PROF(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    ea = index_row['MINIMUM_EMISSION_ANGLE']

    return ea

def populate_obs_ring_geometry_VGISS_emission2_PROF(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    ea = index_row['MAXIMUM_EMISSION_ANGLE']

    return ea

# North based ea: the angle between the normal vector on the NORTH side of the
# ring, to the direction where outgoing photons to the observer. 0-90 when
# observer is at the north side of the ring, and 90-180 when it's at the south
# side.
def populate_obs_ring_geometry_VGISS_north_based_emission1_PROF(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    ea = index_row['MINIMUM_EMISSION_ANGLE']

    return ea

def populate_obs_ring_geometry_VGISS_north_based_emission2_PROF(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    ea = index_row['MAXIMUM_EMISSION_ANGLE']

    return ea

# We set the center versions to be the same as the normal versions
populate_obs_ring_geometry_VGISS_center_phase1_PROF = \
    populate_obs_ring_geometry_VGISS_phase1_PROF
populate_obs_ring_geometry_VGISS_center_phase2_PROF = \
    populate_obs_ring_geometry_VGISS_phase2_PROF
populate_obs_ring_geometry_VGISS_center_incidence1_PROF = \
    populate_obs_ring_geometry_VGISS_incidence1_PROF
populate_obs_ring_geometry_VGISS_center_incidence2_PROF = \
    populate_obs_ring_geometry_VGISS_incidence2_PROF
populate_obs_ring_geometry_VGISS_center_emission1_PROF = \
    populate_obs_ring_geometry_VGISS_emission1_PROF
populate_obs_ring_geometry_VGISS_center_emission2_PROF = \
    populate_obs_ring_geometry_VGISS_emission2_PROF
populate_obs_ring_geometry_VGISS_center_north_based_incidence1_PROF = \
    populate_obs_ring_geometry_VGISS_north_based_incidence1_PROF
populate_obs_ring_geometry_VGISS_center_north_based_incidence2_PROF = \
    populate_obs_ring_geometry_VGISS_north_based_incidence2_PROF
populate_obs_ring_geometry_VGISS_center_north_based_emission1_PROF = \
    populate_obs_ring_geometry_VGISS_north_based_emission1_PROF
populate_obs_ring_geometry_VGISS_center_north_based_emission2_PROF = \
    populate_obs_ring_geometry_VGISS_north_based_emission2_PROF

# Opening angle to observer: the angle between the ring surface to the direction
# where outgoing photons to the observer. Positive if observer is at the north
# side of the ring , negative if it's at the south side. In this case, observer
# is at the north side, so it's 90 - ea. For reference, if observer is at the
# south side, then oa is 90 - 180 - ea.
def populate_obs_ring_geometry_VGISS_observer_ring_opening_angle1_PROF(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    max_ea = index_row['MAXIMUM_EMISSION_ANGLE']

    return 90. - max_ea

def populate_obs_ring_geometry_VGISS_observer_ring_opening_angle2_PROF(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    min_ea = index_row['MINIMUM_EMISSION_ANGLE']

    return 90. - min_ea

# Ring elevation to observer, same to opening angle except, it's positive if
# observer is at north side of Jupiter, Saturn, and Neptune, and south side of
# Uranus. Negative if observer is at south side of Jupiter, Saturn, and Neptune,
# and north side of Uranus. In this volume, observer is at the north of Saturn,
# so ring elevation will be the same as opening angle.
def populate_obs_ring_geometry_VGISS_observer_ring_elevation1_PROF(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    max_ea = index_row['MAXIMUM_EMISSION_ANGLE']

    return 90. - max_ea

def populate_obs_ring_geometry_VGISS_observer_ring_elevation2_PROF(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    min_ea = index_row['MINIMUM_EMISSION_ANGLE']

    return 90. - min_ea


# Opening angle to solar: the angle between the ring surface to the direction
# where incoming photons from the source. Positive if source is at the north
# side of the ring, negative if it's at the south side. In this case, source
# is at the north side, so it's 90 - inc. For reference, if source is at the
# south side, then oa is - (90 - inc).
def populate_obs_ring_geometry_VGISS_solar_ring_opening_angle1_PROF(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    inc = index_row['INCIDENCE_ANGLE']

    return 90. - inc

def populate_obs_ring_geometry_VGISS_solar_ring_opening_angle2_PROF(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    inc = index_row['INCIDENCE_ANGLE']

    return 90. - inc

# Ring elevation to solar, same to opening angle except, it's positive if
# source is at north side of Jupiter, Saturn, and Neptune, and south side of
# Uranus. Negative if source is at south side of Jupiter, Saturn, and Neptune,
# and north side of Uranus. In this volume, source is at north of Saturn,
# so ring elevation will be the same as opening angle.
def populate_obs_ring_geometry_VGISS_solar_ring_elevation1_PROF(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    inc = index_row['INCIDENCE_ANGLE']

    return 90. - inc

def populate_obs_ring_geometry_VGISS_solar_ring_elevation2_PROF(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    inc = index_row['INCIDENCE_ANGLE']

    return 90. - inc

def populate_obs_ring_geometry_VGISS_ring_intercept_time1_PROF(**kwargs):
    return populate_time1_from_index(column='RING_EVENT_START_TIME', **kwargs)

def populate_obs_ring_geometry_VGISS_ring_intercept_time2_PROF(**kwargs):
    return populate_time1_from_index(column='RING_EVENT_STOP_TIME', **kwargs)


################################################################################
# THESE NEED TO BE IMPLEMENTED FOR EVERY VOYAGER INSTRUMENT
################################################################################

def populate_obs_mission_voyager_VGISS_mission_phase_name_PROF(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    target_name = index_row['TARGET_NAME'].upper().strip()
    mp = VG_TARGET_TO_MISSION_PHASE_MAPPING[target_name]

    return mp


################################################################################
# THESE ARE SPECIFIC TO OBS_INSTRUMENT_VGISS
################################################################################

def populate_obs_instrument_vgiss_camera_PROF(**kwargs):
    # Narrow angle camera
    return 'N'

def populate_obs_instrument_vgiss_usable_lines_PROF(**kwargs):
    return 800

def populate_obs_instrument_vgiss_usable_samples_PROF(**kwargs):
    return 800

def populate_obs_instrument_vgiss_filter_name_PROF(**kwargs):
    return 'CLEAR'

def populate_obs_instrument_vgiss_filter_number_PROF(**kwargs):
    return 0

def populate_obs_instrument_vgiss_shutter_mode_PROF(**kwargs):
    return 'NAONLY'

def populate_obs_instrument_vgiss_edit_mode_PROF(**kwargs):
    return '1:1'

def populate_obs_instrument_vgiss_scan_mode_PROF(**kwargs):
    return '1:1'

def populate_obs_instrument_vgiss_gain_mode_PROF(**kwargs):
    return 'LOW'

def populate_obs_instrument_vgiss_image_id_PROF(**kwargs):
    return 'LOW'
