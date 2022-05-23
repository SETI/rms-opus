################################################################################
# obs_mission_hubble.py
#
# Defines the ObsMissionHubble class, which encapsulates fields in the
# common and obs_mission_hubble tables. Note HST does not have separate tables
# for each instrument but combines them all together.
################################################################################

from obs_common import ObsCommon


class ObsMissionHubble(ObsCommon):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


    def _decode_filters(self):
        filter_name = self._index_col('FILTER_NAME')
        if filter_name.find('+') == -1:
            return filter_name, None
        return filter_name.split('+')

    def _is_image(self):
        obs_type = self._observation_type()
        assert obs_type in ('IMG', 'SPE', 'SPI')
        return obs_type == 'IMG' or obs_type == 'SPI'


    #############################
    ### OVERRIDE FROM ObsBase ###
    #############################

    @property
    def inst_host_id(self):
        return 'HST'

    @property
    def mission_id(self):
        return 'HST'

    @property
    def primary_filespec(self):
        # Note it's very important that this can be calculated using ONLY
        # the primary index, not the supplemental index!
        # This is because this (and the subsequent creation of opus_id) is used
        # to actually find the matching row in the supplemental index dictionary.
        # Format: "DATA/VISIT_05/O43B05C1Q.LBL"
        filespec = self._index_col('FILE_SPECIFICATION_NAME')
        return self.volume + '/' + filespec


    ################################
    ### OVERRIDE FROM ObsGeneral ###
    ################################

    def field_obs_general_observation_duration(self):
        return self._index_col('EXPOSURE_DURATION')

    def field_obs_general_ring_obs_id(self):
        instrument_id = self._index_col('INSTRUMENT_ID')
        image_date = self._index_col('START_TIME')[:10]
        filename = self._index_col('PRODUCT_ID')
        planet = self._planet_id()
        if planet == 'OTH':
            pl_str = ''
        else:
            pl_str = planet[0]
        return f'{pl_str}_IMG_HST_{instrument_id}_{image_date}_{filename}'

    def _planet_id(self):
        planet_name = self._index_col('PLANET_NAME')
        if planet_name not in ['VENUS', 'EARTH', 'MARS', 'JUPITER', 'SATURN',
                               'URANUS', 'NEPTUNE', 'PLUTO']:
            return 'OTH'
        return planet_name[:3]

    def field_obs_general_planet_id(self):
        return self._create_mult(self._planet_id())

    def field_obs_general_quantity(self):
        wl1 = self._index_col('MINIMUM_WAVELENGTH')
        wl2 = self._index_col('MAXIMUM_WAVELENGTH')

        if wl1 is None or wl2 is None:
            return self._create_mult('REFLECT')

        # We call it "EMISSION" if at least 3/4 of the passband is below 350 nm
        # and the high end of the passband is below 400 nm.
        if wl2 < 0.4 and (3*wl1+wl2)/4 < 0.35:
            return self._create_mult('EMISSION')
        return self._create_mult('REFLECT')


    ##################################
    ### OVERRIDE FROM ObsTypeImage ###
    ##################################

    def field_obs_type_image_image_type_id(self):
        if not self._is_image():
            return self._create_mult(None)
        return self._create_mult('FRAM')

    def field_obs_type_image_duration(self):
        if not self._is_image():
            return None
        return self.field_obs_general_observation_duration()

    def field_obs_type_image_greater_pixel_size(self):
        if not self._is_image():
            return None
        lines = self._index_col('LINES')
        samples = self._index_col('LINE_SAMPLES')
        if lines is None or samples is None:
            return None
        return max(lines, samples)

    def field_obs_type_image_lesser_pixel_size(self):
        if not self._is_image():
            return None
        lines = self._index_col('LINES')
        samples = self._index_col('LINE_SAMPLES')
        if lines is None or samples is None:
            return None
        return min(lines, samples)


    ###################################
    ### OVERRIDE FROM ObsWavelength ###
    ###################################

    def field_obs_wavelength_wavelength1(self):
        wl1 = self._index_col('MINIMUM_WAVELENGTH')
        wl2 = self._index_col('MAXIMUM_WAVELENGTH')
        if wl1 is None or wl2 is None:
            return None
        # This is necessary because in some cases these are backwards in the table!
        if wl1 > wl2:
            self._log_nonrepeating_warning(
                        'MAXIMUM_WAVELENGTH < MINIMUM_WAVELENGTH; swapping')
            return wl2
        return wl1

    def field_obs_wavelength_wavelength2(self):
        wl1 = self._index_col('MINIMUM_WAVELENGTH')
        wl2 = self._index_col('MAXIMUM_WAVELENGTH')
        if wl1 is None or wl2 is None:
            return None
        # This is necessary because in some cases these are backwards in the table!
        if wl1 > wl2:
            self._log_nonrepeating_warning(
                        'MAXIMUM_WAVELENGTH < MINIMUM_WAVELENGTH; swapping')
            return wl1
        return wl2

    def field_obs_wavelength_wave_res1(self):
        return self._index_col('WAVELENGTH_RESOLUTION')

    def field_obs_wavelength_wave_res2(self):
        return self._index_col('WAVELENGTH_RESOLUTION')

    def field_obs_wavelength_wave_no_res1(self):
        return self._wave_no_res_from_full_bandwidth()

    def field_obs_wavelength_wave_no_res2(self):
        return self.field_obs_wavelength_wave_no_res1()


    ####################################
    ### FIELD METHODS FOR THIS TABLE ###
    ####################################

    def field_obs_mission_hubble_opus_id(self):
        return self.opus_id

    def field_obs_mission_hubble_volume_id(self):
        return self.volume

    def field_obs_mission_hubble_instrument_id(self):
        return self.instrument_id

    def field_obs_mission_hubble_stsci_group_id(self):
        return self._index_col('STSCI_GROUP_ID')

    def field_obs_mission_hubble_hst_proposal_id(self):
        return self._index_col('HST_PROPOSAL_ID')

    def field_obs_mission_hubble_hst_pi_name(self):
        return self._index_col('HST_PI_NAME')

    def field_obs_mission_hubble_detector_id(self):
        detector_id = self._index_col('DETECTOR_ID')
        if detector_id == '':
            return self._create_mult('UNKNOWN')
        ret = self.instrument_id[3:] + '-' + detector_id
        return self._create_mult_keep_case(ret)

    def field_obs_mission_hubble_publication_date(self):
        return self._time_from_index(column='PUBLICATION_DATE')

    def field_obs_mission_hubble_hst_target_name(self):
        return self._index_col('HST_TARGET_NAME')

    def field_obs_mission_hubble_fine_guidance_system_lock_type(self):
        lock_type = self._index_col('FINE_GUIDANCE_SYSTEM_LOCK_TYPE')
        return self._create_mult(lock_type)

    def field_obs_mission_hubble_filter_name(self):
        instrument = self.instrument_id
        filter_name = self._index_col('FILTER_NAME')
        if filter_name.startswith('ND'): # For STIS ND_3 => ND3
            filter_name = filter_name.replace('_', '')
        else:
            filter_name = filter_name.replace('_', ' ')
        ret = instrument[3:] + '-' + filter_name
        return self._create_mult_keep_case(ret)

    def field_obs_mission_hubble_filter_type(self):
        raise NotImplementedError # Required

    def field_obs_mission_hubble_aperture_type(self):
        instrument = self.instrument_id
        aperture = self._index_col('APERTURE_TYPE')
        ret = instrument[3:] + '-' + aperture
        return self._create_mult_keep_case(ret)

    def field_obs_mission_hubble_proposed_aperture_type(self):
        return self._create_mult(None)

    def field_obs_mission_hubble_exposure_type(self):
        return self._create_mult(self._index_col('EXPOSURE_TYPE'))

    def field_obs_mission_hubble_gain_mode_id(self):
        return self._create_mult(self._index_col('GAIN_MODE_ID'))

    def field_obs_mission_hubble_instrument_mode_id(self):
        return self._create_mult(self._index_col('INSTRUMENT_MODE_ID'))

    def field_obs_mission_hubble_pc1_flag(self):
        return self._create_mult(None)

    def field_obs_mission_hubble_wf2_flag(self):
        return self._create_mult(None)

    def field_obs_mission_hubble_wf3_flag(self):
        return self._create_mult(None)

    def field_obs_mission_hubble_wf4_flag(self):
        return self._create_mult(None)

    def field_obs_mission_hubble_targeted_detector_id(self):
        return self._create_mult(None)

    def field_obs_mission_hubble_optical_element(self):
        return self._create_mult(None)
