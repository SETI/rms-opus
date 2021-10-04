################################################################################
# populate_obs_instrument_GB_occ.py
#
# Routines to populate fields specific to ground-based instruments.
#
# XXX NOTE THIS ONLY WORKS FOR 28 SGR RIGHT NOW.
# On 1989-07-03, 28 Sgr incidence angle was 64.627 on the south side
# North-based incidence angle was 180-64.627 = 115.373
# The north side of the rings were illuminated by the Sun
# Earth was viewing the north side of the rings
# Emission angle and north-based emission angle = incidence angle
# Observer elevation = 90 - incidence angle
################################################################################

import pdsfile

from config_data import *
import import_util

from populate_obs_mission_groundbased_prof import *
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

def populate_obs_general_GB_opus_id_PROF(**kwargs):
    file_spec = _GB_file_spec_helper(**kwargs)
    pds_file = pdsfile.PdsFile.from_filespec(file_spec, fix_case=True)
    opus_id = pds_file.opus_id
    if not opus_id:
        import_util.log_nonrepeating_error(
            f'Unable to create OPUS_ID for FILE_SPEC "{file_spec}"')
        return file_spec.split('/')[-1]
    return opus_id

def populate_obs_general_GB_ring_obs_id_PROF(**kwargs):
    return None

def populate_obs_general_GB_inst_host_id_PROF(**kwargs):
    return 'GB'

def populate_obs_general_GB_data_type_PROF(**kwargs):
    return 'OCC'

def populate_obs_general_GB_time1_PROF(**kwargs):
    return populate_time1_from_index(**kwargs)

def populate_obs_general_GB_time2_PROF(**kwargs):
    return populate_time2_from_index(**kwargs)

def populate_obs_general_GB_target_name_PROF(**kwargs):
    return helper_groundbased_target_name(**kwargs)

def populate_obs_general_GB_observation_duration_PROF(**kwargs):
    return populate_observation_duration_from_time(**kwargs)

def populate_obs_general_GB_quantity_PROF(**kwargs):
    return 'OPDEPTH'

def populate_obs_general_GB_observation_type_PROF(**kwargs):
    return 'OCC'

def populate_obs_pds_GB_note_PROF(**kwargs):
    return None

def populate_obs_general_GB_primary_file_spec_PROF(**kwargs):
    return _GB_file_spec_helper(**kwargs)

def populate_obs_pds_GB_primary_file_spec_PROF(**kwargs):
    return _GB_file_spec_helper(**kwargs)

def populate_obs_pds_GB_product_creation_time_PROF(**kwargs):
    return populate_product_creation_time_from_index(**kwargs)

# Format: "ESO1M-SR-APPH-4-OCC-V1.0"
def populate_obs_pds_GB_data_set_id_PROF(**kwargs):
    return populate_data_set_id_from_supp_index(**kwargs)

# Format: "ES1_EGRESS"
def populate_obs_pds_GB_product_id_PROF(**kwargs):
    return populate_product_id_from_index(**kwargs)

def populate_obs_general_GB_right_asc1_PROF(**kwargs):
    return populate_occ_ra_dec_helper_index_label(**kwargs)[0]

def populate_obs_general_GB_right_asc2_PROF(**kwargs):
    return populate_occ_ra_dec_helper_index_label(**kwargs)[1]

def populate_obs_general_GB_declination1_PROF(**kwargs):
    return populate_occ_ra_dec_helper_index_label(**kwargs)[2]

def populate_obs_general_GB_declination2_PROF(**kwargs):
    return populate_occ_ra_dec_helper_index_label(**kwargs)[3]


### OBS_TYPE_IMAGE TABLE ###

def populate_obs_type_image_GB_image_type_id_PROF(**kwargs):
    return None

def populate_obs_type_image_GB_duration_PROF(**kwargs):
    return None

def populate_obs_type_image_GB_levels_PROF(**kwargs):
    return None

def populate_obs_type_image_GB_lesser_pixel_size_PROF(**kwargs):
    return None

def populate_obs_type_image_GB_greater_pixel_size_PROF(**kwargs):
    return None


### OBS_WAVELENGTH TABLE ###

def populate_obs_wavelength_GB_wavelength1_PROF(**kwargs):
    metadata = kwargs['metadata']
    supp_index_row = metadata['supp_index_row']
    wl = supp_index_row['WAVELENGTH'] # microns

    return wl

def populate_obs_wavelength_GB_wavelength2_PROF(**kwargs):
    metadata = kwargs['metadata']
    supp_index_row = metadata['supp_index_row']
    wl = supp_index_row['WAVELENGTH'] # microns

    return wl

def populate_obs_wavelength_GB_wave_res1_PROF(**kwargs):
    return None # Not available

def populate_obs_wavelength_GB_wave_res2_PROF(**kwargs):
    return None # Not available

def populate_obs_wavelength_GB_wave_no1_PROF(**kwargs):
    metadata = kwargs['metadata']
    supp_index_row = metadata['supp_index_row']
    wl = supp_index_row['WAVELENGTH'] # microns

    return 10000 / wl # cm^-1

def populate_obs_wavelength_GB_wave_no2_PROF(**kwargs):
    metadata = kwargs['metadata']
    supp_index_row = metadata['supp_index_row']
    wl = supp_index_row['WAVELENGTH'] # microns

    return 10000 / wl # cm^-1

def populate_obs_wavelength_GB_wave_no_res1_PROF(**kwargs):
    return None # Not available

def populate_obs_wavelength_GB_wave_no_res2_PROF(**kwargs):
    return None # Not available

def populate_obs_wavelength_GB_spec_flag_PROF(**kwargs):
    return 'N'

def populate_obs_wavelength_GB_spec_size_PROF(**kwargs):
    return None

def populate_obs_wavelength_GB_polarization_type_PROF(**kwargs):
    return 'NONE'


### OBS_PROFILE TABLE ###

def populate_obs_occultation_GB_occ_type_PROF(**kwargs):
    return 'STE'

def populate_obs_occultation_GB_occ_dir_PROF(**kwargs):
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
        f'Unknown OCCULTATION_DIRECTION "{occ_dir}"')
    return None

def populate_obs_occultation_GB_body_occ_flag_PROF(**kwargs):
    metadata = kwargs['metadata']
    supp_index_row = metadata['supp_index_row']
    body_occ_flag = supp_index_row['PLANETARY_OCCULTATION_FLAG']

    return body_occ_flag

def populate_obs_occultation_GB_optical_depth_min_PROF(**kwargs):
    return None # Not available

def populate_obs_occultation_GB_optical_depth_max_PROF(**kwargs):
    return None # Not available

def populate_obs_occultation_GB_temporal_sampling_PROF(**kwargs):
    return None # Not available

def populate_obs_occultation_GB_quality_score_PROF(**kwargs):
    return ("UNASSIGNED", "Unassigned")

def populate_obs_occultation_GB_wl_band_PROF(**kwargs):
    metadata = kwargs['metadata']
    supp_index_row = metadata['supp_index_row']
    wl = supp_index_row['WAVELENGTH'] # microns

    if wl > 0.7:
        return 'IR'
    if wl > 0.4:
        return 'VIS'
    return 'UV'

def populate_obs_occultation_GB_source_PROF(**kwargs):
    target_name, target_name_info = populate_star_name_helper_index_label(
                                                                    **kwargs)
    if target_name_info is None:
        return None
    return target_name, target_name_info[2]

def populate_obs_occultation_GB_host_PROF(**kwargs):
    metadata = kwargs['metadata']
    supp_index_row = metadata['supp_index_row']
    insthost = supp_index_row['INSTRUMENT_HOST_NAME']

    return (insthost, insthost)


### OBS_RING_GEOMETRY TABLE ###

def populate_obs_ring_geometry_GB_ring_radius1_PROF(**kwargs):
    metadata = kwargs['metadata']
    supp_index_row = metadata['supp_index_row']
    radius1 = import_util.safe_column(supp_index_row, 'MINIMUM_RING_RADIUS')

    return radius1

def populate_obs_ring_geometry_GB_ring_radius2_PROF(**kwargs):
    metadata = kwargs['metadata']
    supp_index_row = metadata['supp_index_row']
    radius2 = import_util.safe_column(supp_index_row, 'MAXIMUM_RING_RADIUS')

    return radius2

def _radial_resolution_helper(**kwargs):
    metadata = kwargs['metadata']
    supp_index_row = metadata['supp_index_row']
    res = import_util.safe_column(supp_index_row, 'RADIAL_RESOLUTION')

    return res

def populate_obs_ring_geometry_GB_resolution1_PROF(**kwargs):
    return _radial_resolution_helper(**kwargs)

def populate_obs_ring_geometry_GB_resolution2_PROF(**kwargs):
    return _radial_resolution_helper(**kwargs)

def populate_obs_ring_geometry_GB_proj_resolution1_PROF(**kwargs):
    return _radial_resolution_helper(**kwargs)

def populate_obs_ring_geometry_GB_proj_resolution2_PROF(**kwargs):
    return _radial_resolution_helper(**kwargs)

### Phase angle

def populate_obs_ring_geometry_GB_phase1_PROF(**kwargs):
    return 180.

def populate_obs_ring_geometry_GB_phase2_PROF(**kwargs):
    return 180.

def populate_obs_ring_geometry_GB_center_phase1_PROF(**kwargs):
    return 180.

def populate_obs_ring_geometry_GB_center_phase2_PROF(**kwargs):
    return 180.

### Incidence angle

def _incidence_helper(**kwargs):
    metadata = kwargs['metadata']
    supp_index_row = metadata['supp_index_row']
    inc = supp_index_row['INCIDENCE_ANGLE']

    return inc

def populate_obs_ring_geometry_GB_incidence1_PROF(**kwargs):
    return _incidence_helper(**kwargs)

def populate_obs_ring_geometry_GB_incidence2_PROF(**kwargs):
    return _incidence_helper(**kwargs)

def populate_obs_ring_geometry_GB_center_incidence1_PROF(**kwargs):
    return _incidence_helper(**kwargs)

def populate_obs_ring_geometry_GB_center_incidence2_PROF(**kwargs):
    return _incidence_helper(**kwargs)

def populate_obs_ring_geometry_GB_north_based_incidence1_PROF(**kwargs):
    # XXX This is only valid for EBROCC 28 Sgr where the star was on the south
    # side of the rings
    return 180.-_incidence_helper(**kwargs)

def populate_obs_ring_geometry_GB_north_based_incidence2_PROF(**kwargs):
    # XXX This is only valid for EBROCC 28 Sgr where the star was on the south
    # side of the rings
    return 180.-_incidence_helper(**kwargs)

def populate_obs_ring_geometry_GB_center_north_based_incidence1_PROF(**kwargs):
    # XXX This is only valid for EBROCC 28 Sgr where the star was on the south
    # side of the rings
    return 180.-_incidence_helper(**kwargs)

def populate_obs_ring_geometry_GB_center_north_based_incidence2_PROF(**kwargs):
    # XXX This is only valid for EBROCC 28 Sgr where the star was on the south
    # side of the rings
    return 180.-_incidence_helper(**kwargs)

### Emission angle

def populate_obs_ring_geometry_GB_emission1_PROF(**kwargs):
    return 180.-_incidence_helper(**kwargs)

def populate_obs_ring_geometry_GB_emission2_PROF(**kwargs):
    return 180.-_incidence_helper(**kwargs)

def populate_obs_ring_geometry_GB_center_emission1_PROF(**kwargs):
    return 180.-_incidence_helper(**kwargs)

def populate_obs_ring_geometry_GB_center_emission2_PROF(**kwargs):
    return 180.-_incidence_helper(**kwargs)

def populate_obs_ring_geometry_GB_north_based_emission1_PROF(**kwargs):
    # XXX This is only valid for EBROCC 28 Sgr where the star was on the south
    # side of the rings
    return _incidence_helper(**kwargs)

def populate_obs_ring_geometry_GB_north_based_emission2_PROF(**kwargs):
    # XXX This is only valid for EBROCC 28 Sgr where the star was on the south
    # side of the rings
    return _incidence_helper(**kwargs)

def populate_obs_ring_geometry_GB_center_north_based_emission1_PROF(**kwargs):
    # XXX This is only valid for EBROCC 28 Sgr where the star was on the south
    # side of the rings
    return _incidence_helper(**kwargs)

def populate_obs_ring_geometry_GB_center_north_based_emission2_PROF(**kwargs):
    # XXX This is only valid for EBROCC 28 Sgr where the star was on the south
    # side of the rings
    return _incidence_helper(**kwargs)

### Observer ring opening angle (positive on north side of rings)
### Observer ring elevation (positive on north side of rings for Saturn)

def populate_obs_ring_geometry_GB_observer_ring_opening_angle1_PROF(**kwargs):
    # XXX This is only valid for EBROCC 28 Sgr where the star was on the south
    # side of the rings
    return 90.-_incidence_helper(**kwargs)

def populate_obs_ring_geometry_GB_observer_ring_opening_angle2_PROF(**kwargs):
    # XXX This is only valid for EBROCC 28 Sgr where the star was on the south
    # side of the rings
    return 90.-_incidence_helper(**kwargs)

def populate_obs_ring_geometry_GB_observer_ring_elevation1_PROF(**kwargs):
    # XXX This is only valid for EBROCC 28 Sgr where the star was on the south
    # side of the rings
    return 90.-_incidence_helper(**kwargs)

def populate_obs_ring_geometry_GB_observer_ring_elevation2_PROF(**kwargs):
    # XXX This is only valid for EBROCC 28 Sgr where the star was on the south
    # side of the rings
    return 90.-_incidence_helper(**kwargs)

### Solar ring opening angle (positive on north side of rings)
### Solar ring elevation (positive on north side of rings for Saturn)

def populate_obs_ring_geometry_GB_solar_ring_opening_angle1_PROF(**kwargs):
    # XXX This is only valid for EBROCC 28 Sgr where the star was on the south
    # side of the rings
    return _incidence_helper(**kwargs)-90.

def populate_obs_ring_geometry_GB_solar_ring_opening_angle2_PROF(**kwargs):
    # XXX This is only valid for EBROCC 28 Sgr where the star was on the south
    # side of the rings
    return _incidence_helper(**kwargs)-90.

def populate_obs_ring_geometry_GB_solar_ring_elevation1_PROF(**kwargs):
    # XXX This is only valid for EBROCC 28 Sgr where the star was on the south
    # side of the rings
    return _incidence_helper(**kwargs)-90.

def populate_obs_ring_geometry_GB_solar_ring_elevation2_PROF(**kwargs):
    # XXX This is only valid for EBROCC 28 Sgr where the star was on the south
    # side of the rings
    return _incidence_helper(**kwargs)-90.

### Time

def populate_obs_ring_geometry_GB_ring_intercept_time1_PROF(**kwargs):
    return populate_time1_from_index(column='RING_EVENT_START', **kwargs)

def populate_obs_ring_geometry_GB_ring_intercept_time2_PROF(**kwargs):
    return populate_time1_from_index(column='RING_EVENT_STOP', **kwargs)


################################################################################
# THESE NEED TO BE IMPLEMENTED FOR EVERY GROUND-BASED INSTRUMENT
################################################################################



################################################################################
# THESE ARE SPECIFIC TO OBS_INSTRUMENT_GB
################################################################################
