def populate_obs_general_CO_planet_id_CUBE(**kwargs):
    return 'SAT'


################################################################################
# populate_obs_instrument_COCIRS_cube.py
#
# Routines to populate fields specific to COCIRS.
################################################################################

# Ordering:
#   time1/2 must come before planet_id
#   planet_id must come before opus_id

import julian
import pdsfile

from config_data import *
import import_util

from populate_obs_mission_cassini import *
from populate_util import *


################################################################################
# THESE NEED TO BE IMPLEMENTED FOR EVERY INSTRUMENT
################################################################################

### OBS_GENERAL TABLE ###
def _COCIRS_filespec_helper(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    filespec = index_row['FILE_SPECIFICATION_NAME']
    volume_id = kwargs['volume_id']
    return volume_id + '/' + filespec

def populate_obs_general_COCIRS_opus_id_CUBE(**kwargs):
    filespec = _COCIRS_filespec_helper(**kwargs)
    pds_file = pdsfile.PdsFile.from_filespec(filespec, fix_case=True)
    opus_id = pds_file.opus_id
    if not opus_id:
        import_util.log_nonrepeating_error(
            f'Unable to create OPUS_ID for FILE_SPEC "{filespec}"')
        return filespec.split('/')[-1]
    return opus_id

def populate_obs_general_COCIRS_ring_obs_id_CUBE(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['supp_index_row']
    instrument_id = index_row['DETECTOR_ID']

    filename = index_row['FILE_SPECIFICATION_NAME'].split('/')[-1]
    image_num = filename[4:14]
    planet = helper_cassini_planet_id(**kwargs)
    if planet is None:
        pl_str = ''
    else:
        pl_str = planet[0]

    return pl_str + '_SPEC_CO_CIRS_' + image_num + '_' + instrument_id

def populate_obs_general_COCIRS_inst_host_id_CUBE(**kwargs):
    return 'CO'

def populate_obs_general_COCIRS_time1_CUBE(**kwargs):
    return populate_time1_from_index(**kwargs)

def populate_obs_general_COCIRS_time2_CUBE(**kwargs):
    return populate_time2_from_index(**kwargs)

def populate_obs_general_COCIRS_target_name_CUBE(**kwargs):
    return helper_cassini_intended_target_name(**kwargs)

def populate_obs_general_COCIRS_observation_duration_CUBE(**kwargs):
    return populate_observation_duration_from_time(**kwargs)

def populate_obs_general_COCIRS_quantity_CUBE(**kwargs):
    return 'THERMAL'

def populate_obs_general_COCIRS_observation_type_CUBE(**kwargs):
    return 'SCU'

def populate_obs_pds_COCIRS_note_CUBE(**kwargs):
    return None

def populate_obs_general_COCIRS_primary_filespec_CUBE(**kwargs):
    return _COCIRS_filespec_helper(**kwargs)

def populate_obs_pds_COCIRS_primary_filespec_CUBE(**kwargs):
    return _COCIRS_filespec_helper(**kwargs)

def populate_obs_pds_COCIRS_product_creation_time_CUBE(**kwargs):
    return None # Until the proper data is available in the supplemental index

# Format: "CO-S-CIRS-2/3/4-REFORMATTED-V1.0"
def populate_obs_pds_COCIRS_data_set_id_CUBE(**kwargs):
    return populate_data_set_id_from_index_label(**kwargs)

def populate_obs_pds_COCIRS_product_id_CUBE(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    filespec = index_row['FILE_SPECIFICATION_NAME']
    filename = filespec.split('/')[-1]
    return filename

# We don't have ring geometry or other such info for CIRS
def populate_obs_general_COCIRS_right_asc1_CUBE(**kwargs):
    return None

def populate_obs_general_COCIRS_right_asc2_CUBE(**kwargs):
    return None

def populate_obs_general_COCIRS_declination1_CUBE(**kwargs):
    return None

def populate_obs_general_COCIRS_declination2_CUBE(**kwargs):
    return None

# RING GEOMETRY FOR COCIRS_0xxx/1xxx, only apply to ring maps (RING_POLAR)
def populate_obs_ring_geometry_COCIRS_ring_radius1_CUBE(**kwargs):
    if not _is_ring_map_projections(**kwargs):
        return None
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    radius = import_util.safe_column(index_row,
                'CSS:MEAN_RING_BORESIGHT_RADIUS_ZPD')

    return radius

def populate_obs_ring_geometry_COCIRS_ring_radius2_CUBE(**kwargs):
    if not _is_ring_map_projections(**kwargs):
        return None
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    radius = import_util.safe_column(index_row,
                'CSS:MEAN_RING_BORESIGHT_RADIUS_ZPD')

    return radius

def populate_obs_ring_geometry_COCIRS_j2000_longitude1_CUBE(**kwargs):
    if not _is_ring_map_projections(**kwargs):
        return None
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    longitude = import_util.safe_column(index_row,
                'CSS:PRIMARY_SUB_SOLAR_LONGITUDE_BEGINNING')

    return longitude

def populate_obs_ring_geometry_COCIRS_j2000_longitude2_CUBE(**kwargs):
    if not _is_ring_map_projections(**kwargs):
        return None
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    longitude = import_util.safe_column(index_row,
                'CSS:PRIMARY_SUB_SOLAR_LONGITUDE_END')

    return longitude

def populate_obs_ring_geometry_COCIRS_ring_azimuth_wrt_observer1_CUBE(**kwargs):
    return None

def populate_obs_ring_geometry_COCIRS_ring_azimuth_wrt_observer2_CUBE(**kwargs):
    return None

# Phase angle: The angle between the point where incoming source photons
# hit the ring , to the direction where outgoing photons to the observer
def populate_obs_ring_geometry_COCIRS_phase1_CUBE(**kwargs):
    if not _is_ring_map_projections(**kwargs):
        return None
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    phase_angle = import_util.safe_column(index_row,
                'CSS:MEAN_RING_BORESIGHT_SOLAR_PHASE')

    return phase_angle

def populate_obs_ring_geometry_COCIRS_phase2_CUBE(**kwargs):
    if not _is_ring_map_projections(**kwargs):
        return None
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    phase_angle = import_util.safe_column(index_row,
                'CSS:MEAN_RING_BORESIGHT_SOLAR_PHASE')

    return phase_angle

# Source: star, observer: COCIRS
# Incidence angle: the angle between the point where incoming source photons
# hit the ring, to the north pole of the planet we're looking at (normal vector
# on the surface of LIT side of the ring, same as source side), always between
# 0 (parallel to north pole) to 90 (parallel to ring)
# Note: we don't have enough info to get the incidence angle.
def populate_obs_ring_geometry_COCIRS_incidence1_CUBE(**kwargs):
    return None

def populate_obs_ring_geometry_COCIRS_incidence2_CUBE(**kwargs):
    return None

# North based inc: the angle between the point where incoming source photons hit
# the ring to the normal vector on the NORTH side of the ring. 0-90 when north
# side of the ring is lit, and 90-180 when south side is lit.
# Note: we don't have enough info to get the incidence angle.
def populate_obs_ring_geometry_COCIRS_north_based_incidence1_CUBE(**kwargs):
    return None

def populate_obs_ring_geometry_COCIRS_north_based_incidence2_CUBE(**kwargs):
    return None

# Emission angle: the angle between the normal vector on the LIT side, to the
# direction where outgoing photons to the observer. 0-90 when observer is at the
# lit side of the ring, and 90-180 when it's at the dark side.
# Since observer is at the dark side, ea is between 90-180
def populate_obs_ring_geometry_COCIRS_emission1_CUBE(**kwargs):
    if not _is_ring_map_projections(**kwargs):
        return None
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    ea = index_row['CSS:MEAN_RING_BORESIGHT_EMISSION_ANGLE']

    return ea

def populate_obs_ring_geometry_COCIRS_emission2_CUBE(**kwargs):
    if not _is_ring_map_projections(**kwargs):
        return None
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    ea = index_row['CSS:MEAN_RING_BORESIGHT_EMISSION_ANGLE']

    return ea

# North based ea: the angle between the normal vector on the NORTH side of the
# ring, to the direction where outgoing photons to the observer. 0-90 when
# observer is at the north side of the ring, and 90-180 when it's at the south
# side.
# If north side of the ring is lit, then north based emission angle is the same
# as the emission angle. If south side of the ring is lit, north based emission
# angle will be 180 - the emission angle.
def populate_obs_ring_geometry_COCIRS_north_based_emission1_CUBE(**kwargs):
    ea = populate_obs_ring_geometry_COCIRS_emission1_CUBE(**kwargs)
    if ea is None:
        return ea # not ring map projections

    if _is_ring_north_side_lit(**kwargs):
        return ea
    else:
        # min/max ea are the same
        return 180. - ea

def populate_obs_ring_geometry_COCIRS_north_based_emission2_CUBE(**kwargs):
    ea = populate_obs_ring_geometry_COCIRS_emission2_CUBE(**kwargs)
    if ea is None:
        return ea # not ring map projections

    if _is_ring_north_side_lit(**kwargs):
        return ea
    else:
        # min/max ea are the same
        return 180. - ea

# We set the center versions to be the same as the normal versions
populate_obs_ring_geometry_COCIRS_center_phase1_CUBE = \
    populate_obs_ring_geometry_COCIRS_phase1_CUBE
populate_obs_ring_geometry_COCIRS_center_phase2_CUBE = \
    populate_obs_ring_geometry_COCIRS_phase2_CUBE
populate_obs_ring_geometry_COCIRS_center_incidence1_CUBE = \
    populate_obs_ring_geometry_COCIRS_incidence1_CUBE
populate_obs_ring_geometry_COCIRS_center_incidence2_CUBE = \
    populate_obs_ring_geometry_COCIRS_incidence2_CUBE
populate_obs_ring_geometry_COCIRS_center_emission1_CUBE = \
    populate_obs_ring_geometry_COCIRS_emission1_CUBE
populate_obs_ring_geometry_COCIRS_center_emission2_CUBE = \
    populate_obs_ring_geometry_COCIRS_emission2_CUBE
populate_obs_ring_geometry_COCIRS_center_north_based_incidence1_CUBE = \
    populate_obs_ring_geometry_COCIRS_north_based_incidence1_CUBE
populate_obs_ring_geometry_COCIRS_center_north_based_incidence2_CUBE = \
    populate_obs_ring_geometry_COCIRS_north_based_incidence2_CUBE
populate_obs_ring_geometry_COCIRS_center_north_based_emission1_CUBE = \
    populate_obs_ring_geometry_COCIRS_north_based_emission1_CUBE
populate_obs_ring_geometry_COCIRS_center_north_based_emission2_CUBE = \
    populate_obs_ring_geometry_COCIRS_north_based_emission2_CUBE

# Opening angle to observer: the angle between the ring surface to the direction
# where outgoing photons to the observer. Positive if observer is at the north
# side of the ring, negative if it's at the south side.
def populate_obs_ring_geometry_COCIRS_observer_ring_opening_angle1_CUBE(**kwargs):
    ea = populate_obs_ring_geometry_COCIRS_emission1_CUBE(**kwargs)
    if ea is None:
        return ea # not ring map projections

    if _is_cassini_at_north(**kwargs):
        return abs(90. - ea)
    else:
        return - abs(90. - ea)

def populate_obs_ring_geometry_COCIRS_observer_ring_opening_angle2_CUBE(**kwargs):
    ea = populate_obs_ring_geometry_COCIRS_emission2_CUBE(**kwargs)
    if ea is None:
        return ea # not ring map projections

    if _is_cassini_at_north(**kwargs):
        return abs(90. - ea)
    else:
        return - abs(90. - ea)

# Ring elevation to observer, same to opening angle. It's positive if observer
# is at north side Saturn (COCIRS is targeting Saturn). Negative if observer is
# at south side of Saturn.
def populate_obs_ring_geometry_COCIRS_observer_ring_elevation1_CUBE(**kwargs):
    return (populate_obs_ring_geometry_COCIRS_observer_ring_opening_angle1_CUBE(
            **kwargs))

def populate_obs_ring_geometry_COCIRS_observer_ring_elevation2_CUBE(**kwargs):
    return (populate_obs_ring_geometry_COCIRS_observer_ring_opening_angle2_CUBE(
            **kwargs))

# Opening angle to solar: the angle between the ring surface to the direction
# where incoming photons from the source. Positive if source is at the north
# side of the ring , negative if it's at the south side.
# Note: we don't have enough info to get the incidence angle.
def populate_obs_ring_geometry_COCIRS_solar_ring_opening_angle1_CUBE(**kwargs):
    return None

def populate_obs_ring_geometry_COCIRS_solar_ring_opening_angle2_CUBE(**kwargs):
    return None

# Ring elevation to solar, same to opening angle except, it's positive if
# source is at north side of Jupiter, Saturn, and Neptune, and south side of
# Uranus. Negative if source is at south side of Jupiter, Saturn, and Neptune,
# and north side of Uranus.
# Note: we don't have enough info to get the incidence angle.
def populate_obs_ring_geometry_COCIRS_solar_ring_elevation1_CUBE(**kwargs):
    return None

def populate_obs_ring_geometry_COCIRS_solar_ring_elevation2_CUBE(**kwargs):
    return None

def populate_obs_ring_geometry_COCIRS_ring_intercept_time1_CUBE(**kwargs):
    return None

def populate_obs_ring_geometry_COCIRS_ring_intercept_time2_CUBE(**kwargs):
    return None

### SURFACE GEOMETRY ###
def populate_obs_surface_geo_COCIRS_planetocentric_latitude1_CUBE(**kwargs):
    if not _is_equi_map_projections(**kwargs):
        return None
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    pc_latitude = index_row['CSS:MEAN_BORESIGHT_LATITUDE_ZPD_PC']

    return pc_latitude

def populate_obs_surface_geo_COCIRS_planetocentric_latitude2_CUBE(**kwargs):
    if not _is_equi_map_projections(**kwargs):
        return None
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    pc_latitude = index_row['CSS:MEAN_BORESIGHT_LATITUDE_ZPD_PC']

    return pc_latitude

def populate_obs_surface_geo_COCIRS_planetographic_latitude1_CUBE(**kwargs):
    if not _is_equi_map_projections(**kwargs):
        return None
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    latitude = index_row['CSS:MEAN_BORESIGHT_LATITUDE_ZPD']

    return latitude

def populate_obs_surface_geo_COCIRS_planetographic_latitude2_CUBE(**kwargs):
    if not _is_equi_map_projections(**kwargs):
        return None
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    latitude = index_row['CSS:MEAN_BORESIGHT_LATITUDE_ZPD']

    return latitude

def populate_obs_surface_geo_COCIRS_iau_west_longitude1_CUBE(**kwargs):
    if not _is_equi_map_projections(**kwargs):
        return None
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    longitude = index_row['CSS:MEAN_BORESIGHT_LONGITUDE_ZPD']

    return longitude

def populate_obs_surface_geo_COCIRS_iau_west_longitude2_CUBE(**kwargs):
    if not _is_equi_map_projections(**kwargs):
        return None
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    longitude = index_row['CSS:MEAN_BORESIGHT_LONGITUDE_ZPD']

    return longitude

def populate_obs_surface_geo_COCIRS_solar_hour_angle1_CUBE(**kwargs):
    return None

def populate_obs_surface_geo_COCIRS_solar_hour_angle2_CUBE(**kwargs):
    return None

def populate_obs_surface_geo_COCIRS_observer_longitude1_CUBE(**kwargs):
    return None

def populate_obs_surface_geo_COCIRS_observer_longitude2_CUBE(**kwargs):
    return None

def populate_obs_surface_geo_COCIRS_finest_resolution1_CUBE(**kwargs):
    return None

def populate_obs_surface_geo_COCIRS_finest_resolution2_CUBE(**kwargs):
    return None

def populate_obs_surface_geo_COCIRS_coarsest_resolution1_CUBE(**kwargs):
    return None

def populate_obs_surface_geo_COCIRS_coarsest_resolution2_CUBE(**kwargs):
    return None

def populate_obs_surface_geo_COCIRS_range_to_body1_CUBE(**kwargs):
    return None

def populate_obs_surface_geo_COCIRS_range_to_body2_CUBE(**kwargs):
    return None

def populate_obs_surface_geo_COCIRS_phase1_CUBE(**kwargs):
    if not _is_equi_map_projections(**kwargs):
        return None
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    phase_angle = index_row['CSS:MEAN_BODY_PHASE_ANGLE']

    return phase_angle

def populate_obs_surface_geo_COCIRS_phase2_CUBE(**kwargs):
    if not _is_equi_map_projections(**kwargs):
        return None
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    phase_angle = index_row['CSS:MEAN_BODY_PHASE_ANGLE']

    return phase_angle

def populate_obs_surface_geo_COCIRS_incidence1_CUBE(**kwargs):
    return None

def populate_obs_surface_geo_COCIRS_incidence2_CUBE(**kwargs):
    return None

def populate_obs_surface_geo_COCIRS_emission1_CUBE(**kwargs):
    if not _is_equi_map_projections(**kwargs):
        return None
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    ea = index_row['CSS:MEAN_EMISSION_ANGLE_FOV_AVERAGE']

    return ea

def populate_obs_surface_geo_COCIRS_emission2_CUBE(**kwargs):
    if not _is_equi_map_projections(**kwargs):
        return None
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    ea = index_row['CSS:MEAN_EMISSION_ANGLE_FOV_AVERAGE']

    return ea

def populate_obs_surface_geo_COCIRS_sub_solar_planetocentric_latitude_CUBE(
    **kwargs
):
    if not _is_equi_map_projections(**kwargs):
        return None
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    pc_latitude = index_row['CSS:BODY_SUB_SOLAR_LATITUDE_PC_MIDDLE']

    return pc_latitude

def populate_obs_surface_geo_COCIRS_sub_solar_planetographic_latitude_CUBE(
    **kwargs
):
    if not _is_equi_map_projections(**kwargs):
        return None
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    latitude = index_row['CSS:BODY_SUB_SOLAR_LATITUDE_MIDDLE']

    return latitude

def populate_obs_surface_geo_COCIRS_sub_observer_planetocentric_latitude_CUBE(
    **kwargs
):
    if not _is_equi_map_projections(**kwargs):
        return None
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    latitude = index_row['CSS:BODY_SUB_SPACECRAFT_LATITUDE_PC_MIDDLE']

    return latitude

def populate_obs_surface_geo_COCIRS_sub_observer_planetographic_latitude_CUBE(
    **kwargs
):
    if not _is_equi_map_projections(**kwargs):
        return None
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    latitude = index_row['CSS:BODY_SUB_SPACECRAFT_LATITUDE_MIDDLE']

    return latitude

def populate_obs_surface_geo_COCIRS_sub_solar_iau_longitude_CUBE(**kwargs):
    if not _is_equi_map_projections(**kwargs):
        return None
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    longitude = index_row['CSS:BODY_SUB_SOLAR_LONGITUDE_MIDDLE']

    return longitude

def populate_obs_surface_geo_COCIRS_sub_observer_iau_longitude_CUBE(**kwargs):
    if not _is_equi_map_projections(**kwargs):
        return None
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    longitude = index_row['CSS:BODY_SUB_SPACECRAFT_LONGITUDE_MIDDLE']

    return longitude

def populate_obs_surface_geo_COCIRS_center_resolution_CUBE(**kwargs):
    return None

def populate_obs_surface_geo_COCIRS_center_distance_CUBE(**kwargs):
    if not _is_equi_map_projections(**kwargs):
        return None
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    center_distance = index_row['CSS:BODY_SPACECRAFT_RANGE_MIDDLE']

    return center_distance

def populate_obs_surface_geo_COCIRS_center_phase_angle_CUBE(**kwargs):
    return None


### OBS_TYPE_IMAGE TABLE ###

def populate_obs_type_image_COCIRS_image_type_id_CUBE(**kwargs):
    return None

def populate_obs_type_image_COCIRS_duration_CUBE(**kwargs):
    return None

def populate_obs_type_image_COCIRS_levels_CUBE(**kwargs):
    return None

def populate_obs_type_image_COCIRS_lesser_pixel_size_CUBE(**kwargs):
    return None

def populate_obs_type_image_COCIRS_greater_pixel_size_CUBE(**kwargs):
    return None


### OBS_WAVELENGTH TABLE ###

def populate_obs_wavelength_COCIRS_wavelength1_CUBE(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['supp_index_row']
    wave_no2 = index_row['MAXIMUM_WAVENUMBER']

    if wave_no2 is None:
        return None

    return 10000. / wave_no2

def populate_obs_wavelength_COCIRS_wavelength2_CUBE(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['supp_index_row']
    wave_no1 = index_row['MINIMUM_WAVENUMBER']

    if wave_no1 is None:
        return None

    return 10000. / wave_no1

def populate_obs_wavelength_COCIRS_wave_res1_CUBE(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['supp_index_row']
    wave_no_res2 = index_row['BAND_BIN_WIDTH']
    wave_no2 = index_row['MAXIMUM_WAVENUMBER']

    if wave_no_res2 is None or wave_no2 is None:
        return None

    return 10000.*wave_no_res2/(wave_no2 * wave_no2)

def populate_obs_wavelength_COCIRS_wave_res2_CUBE(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    index_row = metadata['supp_index_row']
    wave_no_res1 = index_row['BAND_BIN_WIDTH']
    wave_no1 = index_row['MINIMUM_WAVENUMBER']

    if wave_no_res1 is None or wave_no1 is None:
        return None

    return 10000.*wave_no_res1/(wave_no1 * wave_no1)

def populate_obs_wavelength_COCIRS_wave_no1_CUBE(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['supp_index_row']
    wave_no1 = index_row['MINIMUM_WAVENUMBER']
    return wave_no1

def populate_obs_wavelength_COCIRS_wave_no2_CUBE(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['supp_index_row']
    wave_no2 = index_row['MAXIMUM_WAVENUMBER']
    return wave_no2

def populate_obs_wavelength_COCIRS_wave_no_res1_CUBE(**kwargs):
    return None

def populate_obs_wavelength_COCIRS_wave_no_res2_CUBE(**kwargs):
    return None

def populate_obs_wavelength_COCIRS_spec_flag_CUBE(**kwargs):
    return 'Y'

def populate_obs_wavelength_COCIRS_spec_size_CUBE(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['supp_index_row']
    spec_size = index_row['BANDS']

    return spec_size

def populate_obs_wavelength_COCIRS_polarization_type_CUBE(**kwargs):
    return 'NONE'


### populate_obs_occultation TABLE ###

def populate_obs_occultation_COCIRS_occ_type_CUBE(**kwargs):
    return None

def populate_obs_occultation_COCIRS_occ_dir_CUBE(**kwargs):
    return None

def populate_obs_occultation_COCIRS_body_occ_flag_CUBE(**kwargs):
    return None

def populate_obs_occultation_COCIRS_optical_depth_min_CUBE(**kwargs):
    return None

def populate_obs_occultation_COCIRS_optical_depth_max_CUBE(**kwargs):
    return None

def populate_obs_occultation_COCIRS_temporal_sampling_CUBE(**kwargs):
    return None

def populate_obs_occultation_COCIRS_quality_score_CUBE(**kwargs):
    return None

def populate_obs_occultation_COCIRS_wl_band_CUBE(**kwargs):
    return None

def populate_obs_occultation_COCIRS_source_CUBE(**kwargs):
    return None

def populate_obs_occultation_COCIRS_host_CUBE(**kwargs):
    return None


################################################################################
# THESE NEED TO BE IMPLEMENTED FOR EVERY CASSINI INSTRUMENT
################################################################################

def populate_obs_mission_cassini_COCIRS_ert1_CUBE(**kwargs):
    return None

def populate_obs_mission_cassini_COCIRS_ert2_CUBE(**kwargs):
    return None

def populate_obs_mission_cassini_COCIRS_spacecraft_clock_count1_CUBE(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    sc = index_row['SPACECRAFT_CLOCK_START_COUNT']
    sc = helper_fix_cassini_sclk(sc)
    if not sc.startswith('1/') or sc[2] == ' ':
        import_util.log_nonrepeating_warning(
            f'Badly formatted SPACECRAFT_CLOCK_START_COUNT "{sc}"')
        return None
    try:
        sc_cvt = opus_support.parse_cassini_sclk(sc)
    except Exception as e:
        import_util.log_nonrepeating_warning(
            f'Unable to parse Cassini SCLK "{sc}": {e}')
        return None
    return sc_cvt

def populate_obs_mission_cassini_COCIRS_spacecraft_clock_count2_CUBE(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    sc = index_row['SPACECRAFT_CLOCK_STOP_COUNT']
    sc = helper_fix_cassini_sclk(sc)
    cassini_row = metadata['obs_mission_cassini_row']

    # For CIRS only, there are some badly formatted clock counts
    sc1 = cassini_row['spacecraft_clock_count1']
    if not sc.startswith('1/') or sc[2] == ' ':
        import_util.log_nonrepeating_warning(
            f'Badly formatted SPACECRAFT_CLOCK_STOP_COUNT "{sc}"')
        return sc1
    try:
        sc_cvt = opus_support.parse_cassini_sclk(sc)
    except Exception as e:
        import_util.log_nonrepeating_warning(
            f'Unable to parse Cassini SCLK "{sc}": {e}')
        return sc1

    if sc1 is not None and sc_cvt < sc1:
        import_util.log_warning(
    f'spacecraft_clock_count1 ({sc1}) and spacecraft_clock_count2 ({sc_cvt}) '
    +'are in the wrong order - setting to count1')
        sc_cvt = sc1

    return sc_cvt

# Format: "SCIENCE_CRUISE"
def populate_obs_mission_cassini_COCIRS_mission_phase_name_CUBE(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    index_row = metadata['supp_index_row']
    mp = index_row['MISSION_PHASE_NAME']

    if mp.upper() == 'NULL':
        return None
    return mp.replace('_', ' ')

def populate_obs_mission_cassini_COCIRS_sequence_id_CUBE(**kwargs):
    return None


################################################################################
# THESE ARE SPECIFIC TO OBS_INSTRUMENT_COCIRS
################################################################################
def populate_obs_instrument_cocirs_detector_id_CUBE(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['supp_index_row']
    return index_row['DETECTOR_ID']

# For COCIRS_0xxx and COCIRS_1xxx, we don't have these info in the index files
# TODO: Should we put None for all of them, check with Mark/Rob later. All these
# can't be null in the table previously
def populate_obs_instrument_cocirs_blinking_flag_CUBE(**kwargs):
    return None
def populate_obs_instrument_cocirs_even_flag_CUBE(**kwargs):
    return None
def populate_obs_instrument_cocirs_odd_flag_CUBE(**kwargs):
    return None
def populate_obs_instrument_cocirs_centers_flag_CUBE(**kwargs):
    return None
def populate_obs_instrument_cocirs_pairs_flag_CUBE(**kwargs):
    return None
def populate_obs_instrument_cocirs_all_flag_CUBE(**kwargs):
    return None

################################################################################
# Helper functions
################################################################################
def _get_COCIRS_cube_map_projections(metadata):
    index_row = metadata['index_row']
    vol_id = index_row['VOLUME_ID']
    if (vol_id.startswith('COCIRS_0') or vol_id.startswith('COCIRS_1')):
        return index_row['PRODUCT_ID'][-1].lower()
    else:
        return None

def _is_ring_map_projections(**kwargs):
    metadata = kwargs['metadata']
    return _get_COCIRS_cube_map_projections(metadata) == 'r'

def _is_equi_map_projections(**kwargs):
    metadata = kwargs['metadata']
    return _get_COCIRS_cube_map_projections(metadata) == 'e'

# Equinox: 2009-08-11T01:40:08.914
# Before this time, north side of the ring is lit.
# After this time, south side of the ring is lit.
def _is_ring_north_side_lit(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    start_time = julian.tai_from_iso(index_row['START_TIME'])
    equinox_time = julian.tai_from_iso('2009-08-11T01:40:08.914')
    return start_time < equinox_time

# Use north based emission angle to determine if observer is at the north of the
# ring.
def _is_cassini_at_north(**kwargs):
    ea = populate_obs_ring_geometry_COCIRS_north_based_emission1_CUBE(**kwargs)
    return ea >= 0 and ea <= 90
