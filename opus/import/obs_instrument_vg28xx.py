################################################################################
# obs_instrument_vg28xx.py
#
# Defines the ObsInstrumentVGISSProf, ObsInstrumentVGPPSOcc,
# ObsInstrumentVGRSSOcc, and ObsInstrument VGUVSOcc classes, which encapsulate
# fields in the obs_instrument_vgiss/pps/rss/uvs tables for the VG_28XX volume.
################################################################################

import julian

from obs_mission_voyager import ObsMissionVoyager


_VG_TARGET_TO_MISSION_PHASE_MAPPING = {
    'S RINGS': 'SATURN ENCOUNTER',
    'U RINGS': 'URANUS ENCOUNTER',
    'N RINGS': 'NEPTUNE ENCOUNTER'
}

# Note: threshold values are determined by observing the results from OPUS.
# Voyager location:
# North
# 1980-11-12T05:15:45.520
# South
# 1980-11-13T04:19:30.640
# North
# 1981-08-26T04:18:21.080
# South
# 1985-11-06T17:22:30.040
# North
# 1986-01-24T17:10:13.320
# South
_THRESHOLD_START_TIME_VG_AT_NORTH = [
    '1980-11-12T05:15:45.520',
    '1980-11-13T04:19:30.640',
    '1981-08-26T04:16:45.080',
    '1985-11-06T17:22:30.040',
    '1986-01-24T17:10:13.320'
]

# This class handles everything that the instruments VGISS, VGPPS, VGRSS,
# and VGUVS have in common in the VG_28xx reflection/occultation profile
# volumes.

class ObsInstrumentVG28xx(ObsMissionVoyager):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


    #############################
    ### OVERRIDE FROM ObsBase ###
    #############################

    @property
    def mission_id(self):
        return 'VG'


    ################################
    ### OVERRIDE FROM ObsGeneral ###
    ################################

    def field_obs_general_right_asc1(self):
        return self._prof_ra_dec_helper('index_row', 'SIGNAL_SOURCE_NAME_1')[0]

    def field_obs_general_right_asc2(self):
        return self._prof_ra_dec_helper('index_row', 'SIGNAL_SOURCE_NAME_1')[1]

    def field_obs_general_declination1(self):
        return self._prof_ra_dec_helper('index_row', 'SIGNAL_SOURCE_NAME_1')[2]

    def field_obs_general_declination2(self):
        return self._prof_ra_dec_helper('index_row', 'SIGNAL_SOURCE_NAME_1')[3]


    ############################
    ### OVERRIDE FROM ObsPds ###
    ############################

    def field_obs_pds_product_creation_time(self):
        return self._product_creation_time_helper('index_row')


    ###################################
    ### OVERRIDE FROM ObsWavelength ###
    ###################################

    def field_obs_wavelength_wavelength1(self):
        return self._index_col('MINIMUM_WAVELENGTH')

    def field_obs_wavelength_wavelength2(self):
        return self._index_col('MAXIMUM_WAVELENGTH')

    def field_obs_wavelength_wave_res1(self):
        wl1 = self.field_obs_wavelength_wavelength1()
        wl2 = self.field_obs_wavelength_wavelength2()
        if wl1 is None or wl2 is None:
            return None
        return wl2 - wl1

    def field_obs_wavelength_wave_res2(self):
        return self.field_obs_wavelength_wave_res1()

    def field_obs_wavelength_wave_no_res1(self):
        wno1 = self.field_obs_wavelength_wave_no1()
        wno2 = self.field_obs_wavelength_wave_no2()
        if wno1 is None or wno2 is None:
            return None
        return wno2 - wno1

    def field_obs_wavelength_wave_no_res2(self):
        return self.field_obs_wavelength_wave_no_res1()


    ################################
    ### OVERRIDE FROM ObsProfile ###
    ################################

    def field_obs_profile_wl_band(self):
        wl_band1 = self._index_col('WAVELENGTH_BAND_1')
        wl_band2 = self._index_col('WAVELENGTH_BAND_2')

        if wl_band2 is not None and wl_band2 != 'N/A':
            if wl_band1 != wl_band2:
                self._log_nonrepeating_error(
                    f'Mismatched WAVELENGTH_BAND_1 "{wl_band1}" and '+
                    f'WAVELENGTH_BAND_2 "{wl_band2}"')
                return None
        if '-BAND' in wl_band1:
            wl_band1 = wl_band1[0]
        if 'VISUAL' in wl_band1:
            wl_band1 = 'VI'

        return wl_band1

    def field_obs_profile_source(self):
        src_name1 = self._index_col('SIGNAL_SOURCE_NAME_1')
        src_name2 = self._index_col('SIGNAL_SOURCE_NAME_2')

        if src_name2 is not None and src_name1 != src_name2:
            self._log_nonrepeating_error(
                f'Mismatched SIGNAL_SOURCE_NAME_1 "{src_name1}" and '+
                f'SIGNAL_SOURCE_NAME_2 "{src_name2}"')

        return src_name1


    #####################################
    ### OVERRIDE FROM ObsRingGeometry ###
    #####################################

    def field_obs_ring_geometry_ring_radius1(self):
        return self._index_col('MINIMUM_RING_RADIUS')

    def field_obs_ring_geometry_ring_radius2(self):
        return self._index_col('MAXIMUM_RING_RADIUS')

    def field_obs_ring_geometry_resolution1(self):
        return self._index_col('MINIMUM_RADIAL_RESOLUTION')

    def field_obs_ring_geometry_resolution2(self):
        return self._index_col('MAXIMUM_RADIAL_RESOLUTION')

    def field_obs_ring_geometry_projected_radial_resolution1(self):
        return self._index_col('MINIMUM_RADIAL_RESOLUTION')

    def field_obs_ring_geometry_projected_radial_resolution2(self):
        return self._index_col('MAXIMUM_RADIAL_RESOLUTION')

    def field_obs_ring_geometry_ring_center_phase1(self):
        return self.field_obs_ring_geometry_phase1()

    def field_obs_ring_geometry_ring_center_phase2(self):
        return self.field_obs_ring_geometry_phase2()

    def field_obs_ring_geometry_ring_center_incidence1(self):
        return self.field_obs_ring_geometry_incidence1()

    def field_obs_ring_geometry_ring_center_incidence2(self):
        return self.field_obs_ring_geometry_incidence2()

    def field_obs_ring_geometry_ring_center_emission1(self):
        return self.field_obs_ring_geometry_emission1()

    def field_obs_ring_geometry_ring_center_emission2(self):
        return self.field_obs_ring_geometry_emission2()

    def field_obs_ring_geometry_ring_center_north_based_incidence1(self):
        return self.field_obs_ring_geometry_north_based_incidence1()

    def field_obs_ring_geometry_ring_center_north_based_incidence2(self):
        return self.field_obs_ring_geometry_north_based_incidence2()

    def field_obs_ring_geometry_ring_center_north_based_emission1(self):
        return self.field_obs_ring_geometry_north_based_emission1()

    def field_obs_ring_geometry_ring_center_north_based_emission2(self):
        return self.field_obs_ring_geometry_north_based_emission2()

    def field_obs_ring_geometry_ring_intercept_time1(self):
        return self._time1_from_index(column='RING_EVENT_START_TIME')

    def field_obs_ring_geometry_ring_intercept_time2(self):
        return self._time2_from_index(self.field_obs_ring_geometry_ring_intercept_time1(),
                                      column='RING_EVENT_STOP_TIME')


    #######################################
    ### OVERRIDE FROM ObsMissionVoyager ###
    #######################################

    def field_obs_mission_voyager_mission_phase_name(self):
        target_name = self._index_col('TARGET_NAME').upper()
        return _VG_TARGET_TO_MISSION_PHASE_MAPPING[target_name]


################################################################################
################################################################################

# This subclass handles the volume VG_2810

class ObsInstrumentVG28xxVGISS(ObsInstrumentVG28xx):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


    #############################
    ### OVERRIDE FROM ObsBase ###
    #############################

    @property
    def instrument_id(self):
        return 'VGISS'


    ################################
    ### OVERRIDE FROM ObsGeneral ###
    ################################

    def field_obs_general_quantity(self):
        return 'REFLECT'

    def field_obs_general_observation_type(self):
        return 'REF'

    def field_obs_general_right_asc1(self):
        return None

    def field_obs_general_right_asc2(self):
        return None

    def field_obs_general_declination1(self):
        return None

    def field_obs_general_declination2(self):
        return None


    ##################################
    ### OVERRIDE FROM ObsTypeImage ###
    ##################################

    def field_obs_type_image_image_type_id(self):
        return 'FRAM'

    def field_obs_type_image_duration(self):
        return 0.72

    def field_obs_type_image_levels(self):
        return 256

    def field_obs_type_image_greater_pixel_size(self):
        return 800

    def field_obs_type_image_lesser_pixel_size(self):
        return 800


    ################################
    ### OVERRIDE FROM ObsProfile ###
    ################################

    def field_obs_profile_occ_type(self):
        return 'REF'

    def field_obs_profile_occ_dir(self):
        return None

    def field_obs_profile_body_occ_flag(self):
        return None

    def field_obs_profile_temporal_sampling(self):
        return None

    def field_obs_profile_quality_score(self):
        return 'GOOD'

    def field_obs_profile_optical_depth1(self):
        return None

    def field_obs_profile_optical_depth2(self):
        return None

    def field_obs_profile_source(self):
        return None

    def field_obs_profile_host(self):
        return self._index_col('RECEIVER_HOST_NAME')


    #####################################
    ### OVERRIDE FROM ObsRingGeometry ###
    #####################################

    # Source: Sun, observer: Voyager. For both of the reflectance profiles,
    # the Sun was illuminating the north side of the rings and Voyager was
    # observing the rings from the south side. Thus the incidence/emission
    # angles and the north-based incidence/emission angles will
    # be the same.

    # Ring elevation to Sun, same to opening angle except, it's positive if
    # source is at north side of Jupiter, Saturn, and Neptune, and south side of
    # Uranus. Negative if source is at south side of Jupiter, Saturn, and Neptune,
    # and north side of Uranus. In this volume, source is at north of Saturn,
    # so ring elevation will be the same as opening angle.
    def field_obs_ring_geometry_solar_ring_elev1(self):
        return 90. - self._index_col('INCIDENCE_ANGLE')

    def field_obs_ring_geometry_solar_ring_elev2(self):
        return 90. - self._index_col('INCIDENCE_ANGLE')

    # Ring elevation to observer, same to opening angle except, it's positive if
    # observer is at north side of Jupiter, Saturn, and Neptune, and south side of
    # Uranus. Negative if observer is at south side of Jupiter, Saturn, and Neptune,
    # and north side of Uranus. In this volume, observer is at the south of Saturn,
    # so ring elevation will be the same as opening angle.
    def field_obs_ring_geometry_observer_ring_elevation1(self):
        return 90. - self._index_col('MAXIMUM_EMISSION_ANGLE')

    def field_obs_ring_geometry_observer_ring_elevation2(self):
        return 90. - self._index_col('MINIMUM_EMISSION_ANGLE')

    def field_obs_ring_geometry_phase1(self):
        return self._index_col('MINIMUM_PHASE_ANGLE')

    def field_obs_ring_geometry_phase2(self):
        return self._index_col('MAXIMUM_PHASE_ANGLE')

    def field_obs_ring_geometry_incidence1(self):
        return self._index_col('INCIDENCE_ANGLE')

    def field_obs_ring_geometry_incidence2(self):
        return self._index_col('INCIDENCE_ANGLE')

    # Emission angle: the angle between the normal vector on the LIT side, to the
    # direction where outgoing photons to the observer. 0-90 when observer is at the
    # lit side of the ring, and 90-180 when it's at the dark side.
    def field_obs_ring_geometry_emission1(self):
        return self._index_col('MINIMUM_EMISSION_ANGLE')

    def field_obs_ring_geometry_emission2(self):
        return self._index_col('MAXIMUM_EMISSION_ANGLE')

    def field_obs_ring_geometry_north_based_incidence1(self):
        return self._index_col('INCIDENCE_ANGLE')

    def field_obs_ring_geometry_north_based_incidence2(self):
        return self._index_col('INCIDENCE_ANGLE')

    def field_obs_ring_geometry_north_based_emission1(self):
        return self._index_col('MINIMUM_EMISSION_ANGLE')

    def field_obs_ring_geometry_north_based_emission2(self):
        return self._index_col('MAXIMUM_EMISSION_ANGLE')

    # Opening angle to Sun: the angle between the ring surface to the direction
    # where incoming photons from the source. Positive if source is at the north
    # side of the ring, negative if it's at the south side. In this case, source
    # is at the north side, so it's 90 - inc. For reference, if source is at the
    # south side, then oa is - (90 - inc).
    def field_obs_ring_geometry_solar_ring_opening_angle1(self):
        return 90. - self._index_col('INCIDENCE_ANGLE')

    def field_obs_ring_geometry_solar_ring_opening_angle2(self):
        return 90. - self._index_col('INCIDENCE_ANGLE')

    def field_obs_ring_geometry_observer_ring_opening_angle1(self):
        return 90. - self._index_col('MAXIMUM_EMISSION_ANGLE')

    def field_obs_ring_geometry_observer_ring_opening_angle2(self):
        return 90. - self._index_col('MINIMUM_EMISSION_ANGLE')


    ####################################
    ### FIELD METHODS FOR THIS TABLE ###
    ####################################

    def field_obs_instrument_vgiss_opus_id(self):
        return self.opus_id

    def field_obs_instrument_vgiss_volume_id(self):
        return self.volume

    def field_obs_instrument_vgiss_instrument_id(self):
        return self.instrument_id

    def field_obs_instrument_vgiss_image_id(self):
        return self._index_col('IMAGE_ID')

    def field_obs_instrument_vgiss_scan_mode(self):
        return self._index_col('SCAN_MODE')

    def field_obs_instrument_vgiss_shutter_mode(self):
        return self._index_col('SHUTTER_MODE')

    def field_obs_instrument_vgiss_gain_mode(self):
        return self._index_col('GAIN_MODE')

    def field_obs_instrument_vgiss_edit_mode(self):
        return self._index_col('EDIT_MODE')

    def field_obs_instrument_vgiss_filter_name(self):
        return self._index_col('FILTER_NAME')

    def field_obs_instrument_vgiss_filter_number(self):
        return self._index_col('FILTER_NUMBER')

    def field_obs_instrument_vgiss_camera(self):
        # Narrow angle camera
        return 'N'

    def field_obs_instrument_vgiss_usable_lines(self):
        return 800

    def field_obs_instrument_vgiss_usable_samples(self):
        return 800


################################################################################
################################################################################

# This subclass handles the volume VG_2801

class ObsInstrumentVG28xxVGPPS(ObsInstrumentVG28xx):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


    #############################
    ### OVERRIDE FROM ObsBase ###
    #############################

    @property
    def instrument_id(self):
        return 'VGPPS'


    ################################
    ### OVERRIDE FROM ObsGeneral ###
    ################################

    def field_obs_general_quantity(self):
        return 'OPDEPTH'

    def field_obs_general_observation_type(self):
        return 'OCC'


    ################################
    ### OVERRIDE FROM ObsProfile ###
    ################################

    def field_obs_profile_occ_type(self):
        return 'STE'

    def field_obs_profile_occ_dir(self):
        return self._index_col('RING_OCCULTATION_DIRECTION')[0]

    def field_obs_profile_body_occ_flag(self):
        return self._index_col('PLANETARY_OCCULTATION_FLAG')

    def field_obs_profile_temporal_sampling(self):
        return self._index_col('TEMPORAL_SAMPLING_INTERVAL')

    def field_obs_profile_quality_score(self):
        return 'GOOD'

    def field_obs_profile_optical_depth1(self):
        return None

    def field_obs_profile_optical_depth2(self):
        return None

    def field_obs_profile_host(self):
        return self._index_col('RECEIVER_HOST_NAME')


    #####################################
    ### OVERRIDE FROM ObsRingGeometry ###
    #####################################

    # In this volume,
    # Voyager is at north when:
    #     - Source is DELTA SCO (Target S RINGS)
    #     - Source is SIGMA SGR (Target U RINGS)
    # Voyager is south when:
    #     - Source is SIGMA SGR (Target N RINGS)
    #     - Source is BETA PER (Target U RINGS)
    def _is_voyager_at_north(self):
        src_name = self._index_col('SIGNAL_SOURCE_NAME_1')
        target_name = self._index_col('TARGET_NAME').upper().strip()

        start_time = julian.tai_from_iso(self._index_col('START_TIME'))
        threshold = julian.tai_from_iso(_THRESHOLD_START_TIME_VG_AT_NORTH)

        is_at_north = (src_name == 'DELTA SCO' or
                       (src_name == 'SIGMA SGR' and target_name == 'U RINGS'))
        # Check if the start time matches the Voyager location
        if is_at_north:
            if (start_time > threshold[4] or
                threshold[1] > start_time > threshold[0] or
                threshold[3] > start_time > threshold[2]):
                self._log_nonrepeating_error(
                    'Start time and Voyager N/S location do not match.')
        else:
            if (start_time <= threshold[0] or
                threshold[1] <= start_time <= threshold[2] or
                threshold[3] <= start_time <= threshold[4]):
                self._log_nonrepeating_error(
                    'Start time and Voyager N/S location do not match.')
        return is_at_north

    def _is_voyager_at_north_except_uranus(self):
        src_name = self._index_col('SIGNAL_SOURCE_NAME_1')
        target_name = self._index_col('TARGET_NAME').upper().strip()

        start_time = julian.tai_from_iso(self._index_col('START_TIME'))
        threshold = julian.tai_from_iso(_THRESHOLD_START_TIME_VG_AT_NORTH)

        is_at_north = (src_name == 'DELTA SCO')
        # Check if the start time matches the Voyager location.
        if is_at_north or (src_name == 'SIGMA SGR' and target_name == 'U RINGS'):
            if (start_time > threshold[4] or
                threshold[1] > start_time > threshold[0] or
                threshold[3] > start_time > threshold[2]):
                self._log_nonrepeating_error(
                    'Start time and Voyager N/S location do not match.')
        else:
            if (start_time <= threshold[0] or
                threshold[1] <= start_time <= threshold[2] or
                threshold[3] <= start_time <= threshold[4]):
                self._log_nonrepeating_error(
                    'Start time and Voyager N/S location do not match.')
        return is_at_north


    # Source is star, observer is Voyager
    # Source DELTA SCO is at south, observer Voyager is at north. Target: S ring.
    # Source SIGMA SGR is at south, observer Voyager is at north. Target: U ring.
    # Source SIGMA SGR is at north, observer Voyager is at south. Target: N ring.
    # Source BETA PER is at north, observer Voyager is at south. Target: U ring.

    # Ring elevation to Sun, same to opening angle except, it's positive if
    # source is at north side of Jupiter, Saturn, and Neptune, and south side of
    # Uranus. Negative if source is at south side of Jupiter, Saturn, and Neptune,
    # and north side of Uranus.
    def field_obs_ring_geometry_solar_ring_elev1(self):
        if self._is_voyager_at_north_except_uranus():
            return self.field_obs_ring_geometry_incidence1() - 90.
        return 90. - self.field_obs_ring_geometry_incidence2()

    def field_obs_ring_geometry_solar_ring_elev2(self):
        if self._is_voyager_at_north_except_uranus():
            return self.field_obs_ring_geometry_incidence2() - 90.
        return 90. - self.field_obs_ring_geometry_incidence1()

    # Ring elevation to observer, same to opening angle except, it's positive if
    # observer is at north side of Jupiter, Saturn, and Neptune, and south side of
    # Uranus. Negative if observer is at south side of Jupiter, Saturn, and Neptune,
    # and north side of Uranus.
    def field_obs_ring_geometry_observer_ring_elevation1(self):
        if self._is_voyager_at_north_except_uranus():
            return self.field_obs_ring_geometry_emission1() - 90.
        return 90. - self.field_obs_ring_geometry_emission2()

    def field_obs_ring_geometry_observer_ring_elevation2(self):
        if self._is_voyager_at_north_except_uranus():
            return self.field_obs_ring_geometry_emission1() - 90.
        return 90. - self.field_obs_ring_geometry_emission2()

    def field_obs_ring_geometry_phase1(self):
        return 180.

    def field_obs_ring_geometry_phase2(self):
        return 180.

    # Incidence angle: The angle between the point where the incoming source
    # photos hit the ring and the normal to the ring plane on the LIT side of
    # the ring. This is always between 0 (parallel to the normal vector) and 90
    # (parallel to the ring plane)
    # We would like to use emission angle to get both min/max of incidence angle.
    # Emission angle is 90-180 (dark side), so incidence angle is 180 - emission
    # angle.
    def field_obs_ring_geometry_incidence1(self):
        inc = self._index_col('INCIDENCE_ANGLE')
        max_ea = self._index_col('MAXIMUM_EMISSION_ANGLE')
        cal_inc = 180 - max_ea
        if abs(cal_inc - inc) >= 0.005:
            self._log_nonrepeating_error(
                'The difference between incidence angle and 180-emission is > 0.005')
        return cal_inc

    def field_obs_ring_geometry_incidence2(self):
        inc = self._index_col('INCIDENCE_ANGLE')
        max_ea = self._index_col('MINIMUM_EMISSION_ANGLE')
        cal_inc = 180 - max_ea
        if abs(cal_inc - inc) >= 0.005:
            self._log_nonrepeating_error(
                'The difference between incidence angle and 180-emission is > 0.005')
        return cal_inc

    # Emission angle: the angle between the normal vector on the LIT side, to the
    # direction where outgoing photons to the observer. 0-90 when observer is at the
    # lit side of the ring, and 90-180 when it's at the dark side.
    # Since observer is on the dark side, ea is between 90-180
    def field_obs_ring_geometry_emission1(self):
        return self._index_col('MINIMUM_EMISSION_ANGLE')

    def field_obs_ring_geometry_emission2(self):
        return self._index_col('MAXIMUM_EMISSION_ANGLE')

    # North based inc: the angle between the point where incoming source photons hit
    # the ring to the normal vector on the NORTH side of the ring. 0-90 when north
    # side of the ring is lit, and 90-180 when south side is lit.
    def field_obs_ring_geometry_north_based_incidence1(self):
        if self._is_voyager_at_north():
            return 180. - self.field_obs_ring_geometry_incidence2()
        return self.field_obs_ring_geometry_incidence1()

    def field_obs_ring_geometry_north_based_incidence2(self):
        if self._is_voyager_at_north():
            return 180. - self.field_obs_ring_geometry_incidence1()
        return self.field_obs_ring_geometry_incidence2()

    def field_obs_ring_geometry_north_based_emission1(self):
        if self._is_voyager_at_north():
            return 180. - self.field_obs_ring_geometry_emission2()
        return self.field_obs_ring_geometry_emission1()

    def field_obs_ring_geometry_north_based_emission2(self):
        if self._is_voyager_at_north():
            return 180. - self.field_obs_ring_geometry_emission1()
        return self.field_obs_ring_geometry_emission2()

    # Opening angle to Sun: the angle between the ring surface to the direction
    # where incoming photons from the source. Positive if source is at the north
    # side of the ring, negative if it's at the south side. In this case, source
    # is at the north side, so it's 90 - inc. For reference, if source is at the
    # south side, then oa is - (90 - inc).
    def field_obs_ring_geometry_solar_ring_opening_angle1(self):
        if self._is_voyager_at_north():
            return self.field_obs_ring_geometry_incidence1() - 90.
        return 90. - self.field_obs_ring_geometry_incidence2()

    def field_obs_ring_geometry_solar_ring_opening_angle2(self):
        if self._is_voyager_at_north():
            return self.field_obs_ring_geometry_incidence2() - 90.
        return 90. - self.field_obs_ring_geometry_incidence1()

    # Opening angle to observer: the angle between the ring surface to the direction
    # where outgoing photons to the observer. Positive if observer is at the north
    # side of the ring, negative if it's at the south side. If observer is at the
    # north side, it's ea - 90 (or 90 - inc). If observer is at the south side,
    # then oa is 90 - ea.
    def field_obs_ring_geometry_observer_ring_opening_angle1(self):
        if self._is_voyager_at_north():
            return self.field_obs_ring_geometry_emission1() - 90.
        return 90. - self.field_obs_ring_geometry_emission2()

    def field_obs_ring_geometry_observer_ring_opening_angle2(self):
        if self._is_voyager_at_north():
            return self.field_obs_ring_geometry_emission2() - 90.
        return 90. - self.field_obs_ring_geometry_emission1()


    ####################################
    ### FIELD METHODS FOR THIS TABLE ###
    ####################################

    def field_obs_instrument_vgiss_opus_id(self):
        return self.opus_id

    def field_obs_instrument_vgiss_volume_id(self):
        return self.volume

    def field_obs_instrument_vgiss_instrument_id(self):
        return self.instrument_id
