################################################################################
# obs_instrument_covims.py
#
# Defines the ObsInstrumentCOVIMS class, which encapsulates fields in the
# common, obs_mission_cassini, and obs_instrument_covims tables for COVIMS_8xxx
# occultations.
################################################################################

import opus_support

from obs_mission_cassini import ObsMissionCassini


class ObsInstrumentCOVIMS(ObsMissionCassini):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _is_image(self):
        return self._index_col('INSTRUMENT_MODE_ID') == 'IMAGE'


    #############################
    ### OVERRIDE FROM ObsBase ###
    #############################

    @property
    def instrument_id(self):
        return 'COVIMS'

    @property
    def primary_filespec(self):
        # Note it's very important that this can be calculated using ONLY
        # the primary index, not the supplemental index!
        # This is because this (and the subsequent creation of opus_id) is used
        # to actually find the matching row in the supplemental index dictionary.
        path_name = self._index_col('PATH_NAME')
        file_name = self._index_col('FILE_NAME')
        return f'{self.bundle}{path_name}/{file_name}'

    def convert_filespec_from_lbl(self, filespec):
        return filespec.replace('.lbl', '.qub')

    @property
    def opus_id(self):
        if self.phase_name is None:
            # This happens during scanning the index/supp_index/geo files because
            # we don't have separate phases at that time.
            return super().opus_id
        return super().opus_id + '_' + self.phase_name.lower()

    @property
    def phase_names(self):
        phase_names = []
        if self._index_col('VIS_SAMPLING_MODE_ID') != 'N/A':
            phase_names.append('VIS')
        if self._index_col('IR_SAMPLING_MODE_ID') != 'N/A':
            phase_names.append('IR')
        return phase_names


    ################################
    ### OVERRIDE FROM ObsGeneral ###
    ################################

    def _target_name(self):
        return [self._cassini_intended_target_name()]

    # We occasionally don't bother to generate ring_geo data for COVIMS, like during
    # cruise, so just use the given RA/DEC from the index if needed. We don't make
    # any effort to figure out the min/max values.
    def field_obs_general_right_asc1(self):
        ra = self._ring_geo_index_col('MINIMUM_RIGHT_ASCENSION')
        if ra is not None:
            return ra
        return self._index_col('RIGHT_ASCENSION')

    def field_obs_general_right_asc2(self):
        ra = self._ring_geo_index_col('MAXIMUM_RIGHT_ASCENSION')
        if ra is not None:
            return ra
        return self._index_col('RIGHT_ASCENSION')

    def field_obs_general_declination1(self):
        ra = self._ring_geo_index_col('MINIMUM_DECLINATION')
        if ra is not None:
            return ra
        return self._index_col('DECLINATION')

    def field_obs_general_declination2(self):
        ra = self._ring_geo_index_col('MAXIMUM_DECLINATION')
        if ra is not None:
            return ra
        return self._index_col('DECLINATION')

    def field_obs_general_ring_obs_id(self):
        filename = self._index_col('FILE_NAME')
        image_num = filename[1:11]
        phase_name = self.phase_name
        planet = self._cassini_planet_id()
        if planet == 'OTH':
            pl_str = ''
        else:
            pl_str = planet[0]

        return f'{pl_str}_CUBE_CO_VIMS_{image_num}_{phase_name}'

        filename = self._index_col('FILE_NAME').split('/')[-1]
        if filename.startswith('HDAC'):
            image_camera = filename[:4]
            image_time = filename[4:18]
        else:
            image_camera = filename[:3]
            image_time = filename[3:17]
        image_time_str = (image_time[:4] + '-' + image_time[5:8] + 'T' +
                          image_time[9:11] + '-' + image_time[12:14])
        planet = self._cassini_planet_id()
        if planet == 'OTH':
            pl_str = ''
        else:
            pl_str = planet[0]

        return f'{pl_str}_CO_UVIS_{image_time_str}_{image_camera}'

    def field_obs_general_planet_id(self):
        return self._create_mult(self._cassini_planet_id())

    def field_obs_general_quantity(self):
        inst_mod = self._index_col('INSTRUMENT_MODE_ID')
        if inst_mod == 'OCCULTATION':
            return self._create_mult('OPDEPTH')
        return self._create_mult('REFLECT')

    def field_obs_general_observation_type(self):
        inst_mod = self._index_col('INSTRUMENT_MODE_ID')
        if inst_mod == 'OCCULTATION':
            return self._create_mult('TS') # Time Series
        return self._create_mult('SCU') # Spectral Cube


    ############################
    ### OVERRIDE FROM ObsPds ###
    ############################

    def field_obs_pds_note(self):
        return None


    ##################################
    ### OVERRIDE FROM ObsTypeImage ###
    ##################################

    def field_obs_type_image_image_type_id(self):
        inst_mod = self._index_col('INSTRUMENT_MODE_ID')
        if inst_mod != 'IMAGE':
            return self._create_mult(None)
        if self.phase_name == 'VIS':
            return self._create_mult('PUSH')
        return self._create_mult('RAST')

    def field_obs_type_image_duration(self):
        if not self._is_image():
            return None

        ir_exp = self._index_col('IR_EXPOSURE')
        vis_exp = self._index_col('VIS_EXPOSURE')
        if self.phase_name == 'IR':
            if ir_exp is None:
                return None
            if ir_exp < 0:
                self._log_nonrepeating_warning(f'IR Exposure {ir_exp} is < 0')
                return None
            return ir_exp/1000
        if vis_exp is None:
            return None
        if vis_exp < 0:
            self._log_nonrepeating_warning(f'VIS Exposure {vis_exp} is < 0')
            return None
        return vis_exp/1000

    def field_obs_type_image_levels(self):
        if not self._is_image():
            return None
        return 4096

    def field_obs_type_image_greater_pixel_size(self):
        if not self._is_image():
            return None
        return max(self._index_col('SWATH_WIDTH'), self._index_col('SWATH_LENGTH'))

    def field_obs_type_image_lesser_pixel_size(self):
        if not self._is_image():
            return None
        return min(self._index_col('SWATH_WIDTH'), self._index_col('SWATH_LENGTH'))


    ###################################
    ### OVERRIDE FROM ObsWavelength ###
    ###################################

    def field_obs_wavelength_wavelength1(self):
        if self.phase_name == 'IR':
            return 0.8842
        return 0.35054

    def field_obs_wavelength_wavelength2(self):
        if self.phase_name == 'IR':
            return 5.1225
        return 1.04598

    def field_obs_wavelength_wave_res1(self):
        if self.phase_name == 'IR':
            return 0.01662
        return 0.0073204

    def field_obs_wavelength_wave_res2(self):
        if self.phase_name == 'IR':
            return 0.01662
        return 0.0073204

    def field_obs_wavelength_wave_no_res1(self):
        return self._wave_no_res1_from_wave_res()

    def field_obs_wavelength_wave_no_res2(self):
        return self._wave_no_res2_from_wave_res()

    def field_obs_wavelength_spec_flag(self):
        return self._create_mult('Y')

    def field_obs_wavelength_spec_size(self):
        if self.phase_name == 'IR':
            return 256
        return 96


    #######################################
    ### OVERRIDE FROM ObsMissionCassini ###
    #######################################

    def field_obs_mission_cassini_spacecraft_clock_count1(self):
        sc = '1/' + self._index_col('SPACECRAFT_CLOCK_START_COUNT')
        sc = self._fix_cassini_sclk(sc)
        try:
            sc_cvt = opus_support.parse_cassini_sclk(sc)
        except Exception as e:
            self._log_nonrepeating_error(f'Unable to parse Cassini SCLK "{sc}": {e}')
            return None
        return sc_cvt

    def field_obs_mission_cassini_spacecraft_clock_count2(self):
        sc = '1/' + self._index_col('SPACECRAFT_CLOCK_STOP_COUNT')
        sc = self._fix_cassini_sclk(sc)
        try:
            sc_cvt = opus_support.parse_cassini_sclk(sc)
        except Exception as e:
            self._log_nonrepeating_error(f'Unable to parse Cassini SCLK "{sc}": {e}')
            return None

        sc1 = self.field_obs_mission_cassini_spacecraft_clock_count1()
        if sc1 is not None and sc_cvt < sc1:
            self._log_warning(
                f'spacecraft_clock_count1 ({sc1}) and spacecraft_clock_count2 '+
                f'({sc_cvt}) are in the wrong order - setting to count1')
            sc_cvt = sc1

        return sc_cvt

    def field_obs_mission_cassini_mission_phase_name(self):
        return self._create_mult(self._cassini_mission_phase_name())

    def field_obs_mission_cassini_sequence_id(self):
        return self._index_col('SEQ_ID')


    ###############################################
    ### FIELD METHODS FOR obs_instrument_covims ###
    ###############################################

    def field_obs_instrument_covims_opus_id(self):
        return self.opus_id

    def field_obs_instrument_covims_bundle_id(self):
        return self.bundle

    def field_obs_instrument_covims_instrument_id(self):
        return self.instrument_id

    def field_obs_instrument_covims_instrument_mode_id(self):
        return self._create_mult(self._index_col('INSTRUMENT_MODE_ID'))

    def field_obs_instrument_covims_spectral_editing(self):
        return self._create_mult(self._index_col('SPECTRAL_EDITING'))

    def field_obs_instrument_covims_spectral_summing(self):
        return self._create_mult(self._index_col('SPECTRAL_SUMMING'))

    def field_obs_instrument_covims_star_tracking(self):
        return self._create_mult(self._index_col('STAR_TRACKING'))

    def field_obs_instrument_covims_swath_width(self):
        return self._index_col('SWATH_WIDTH')

    def field_obs_instrument_covims_swath_length(self):
        return self._index_col('SWATH_LENGTH')

    def field_obs_instrument_covims_ir_exposure(self):
        ir_exp = self._index_col('IR_EXPOSURE')
        if ir_exp is None:
            return None
        return ir_exp / 1000.

    def field_obs_instrument_covims_ir_sampling_mode_id(self):
        return self._create_mult(self._index_col('IR_SAMPLING_MODE_ID'))

    def field_obs_instrument_covims_vis_exposure(self):
        vis_exp = self._index_col('VIS_EXPOSURE')
        if vis_exp is None:
            return None
        return vis_exp / 1000.

    def field_obs_instrument_covims_vis_sampling_mode_id(self):
        return self._create_mult(self._index_col('VIS_SAMPLING_MODE_ID'))

    def field_obs_instrument_covims_channel(self):
        return self._create_mult_keep_case(self.phase_name)
