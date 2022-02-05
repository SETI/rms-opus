
def populate_obs_general_VGPPS_quantity_PROF(**kwargs):
    return 'OPDEPTH'

def populate_obs_general_VGPPS_observation_type_PROF(**kwargs):
    return 'OCC'

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
    Voyager is at north when:
        - Source is DELTA SCO (Target S RINGS)
        - Source is SIGMA SGR (Target U RINGS)
    Voyager is south when:
        - Source is SIGMA SGR (Target N RINGS)
        - Source is BETA PER (Target U RINGS)
    """
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    src_name = index_row['SIGNAL_SOURCE_NAME_1']
    target_name = index_row['TARGET_NAME'].upper().strip()

    start_time = julian.tai_from_iso(index_row['START_TIME'])
    threshold = julian.tai_from_iso(THRESHOLD_START_TIME_VG_AT_NORTH)
    msg = (f"{index_row['FILE_SPECIFICATION_NAME']} start time" +
           f"{index_row['START_TIME']} and Voyager location do not match.")

    is_at_north = (src_name == 'DELTA SCO'
                 or (src_name == 'SIGMA SGR' and target_name == 'U RINGS'))
    # Check if the start time match the Voyager location.
    if is_at_north:
        assert (start_time <= threshold[0]
                or (start_time <= threshold[2] and start_time >= threshold[1])
                or (start_time <= threshold[4] and start_time >= threshold[3])
                ), msg
    else:
        assert (start_time > threshold[4]
                or (start_time > threshold[0] and start_time < threshold[1])
                or (start_time > threshold[2] and start_time < threshold[3])
                ), msg
    return is_at_north

def _is_voyager_at_north_except_uranus(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    src_name = index_row['SIGNAL_SOURCE_NAME_1']
    target_name = index_row['TARGET_NAME'].upper().strip()

    start_time = julian.tai_from_iso(index_row['START_TIME'])
    threshold = julian.tai_from_iso(THRESHOLD_START_TIME_VG_AT_NORTH)
    msg = (f"{index_row['FILE_SPECIFICATION_NAME']} start time" +
           f"{index_row['START_TIME']} and Voyager location do not match.")

    is_at_north = (src_name == 'DELTA SCO')
    # Check if the start time match the Voyager location.
    if is_at_north or (src_name == 'SIGMA SGR' and target_name == 'U RINGS'):
        assert (start_time <= threshold[0]
                or (start_time <= threshold[2] and start_time >= threshold[1])
                or (start_time <= threshold[4] and start_time >= threshold[3])
                ), msg
    else:
        assert (start_time > threshold[4]
                or (start_time > threshold[0] and start_time < threshold[1])
                or (start_time > threshold[2] and start_time < threshold[3])
                ), msg
    return is_at_north


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
