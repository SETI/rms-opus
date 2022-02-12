################################################################################
# obs_instrument_covims_occ.py
#
# Defines the ObsInstrumentCOVIMSOcc class, which encapsulates fields in the
# obs_instrument_covims table for COVIMS_8001 occultations.
################################################################################

import opus_support

from obs_instrument_couvis_covims_occ import ObsInstrumentUVISVIMSOcc


class ObsInstrumentCOVIMSOcc(ObsInstrumentUVISVIMSOcc):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


    #############################
    ### OVERRIDE FROM ObsBase ###
    #############################

    @property
    def instrument_id(self):
        return 'COVIMS'


    ###################################
    ### OVERRIDE FROM ObsWavelength ###
    ###################################

    def field_obs_wavelength_wavelength1(self):
        return 0.8842

    def field_obs_wavelength_wavelength2(self):
        return 5.1225

    def field_obs_wavelength_wave_res1(self):
        return 0.01662

    def field_obs_wavelength_wave_res2(self):
        return 0.01662

    def field_obs_wavelength_wave_no_res1(self):
        return self._wave_no_res1_from_wave_res()

    def field_obs_wavelength_wave_no_res2(self):
        return self._wave_no_res2_from_wave_res()

    def field_obs_wavelength_spec_flag(self):
        return 'Y'

    def field_obs_wavelength_spec_size(self):
        return 256


    ################################
    ### OVERRIDE FROM ObsProfile ###
    ################################

    def field_obs_profile_temporal_sampling(self):
        return self._supp_index_col('IR_EXPOSURE') / 1000 # msec -> sec

    def field_obs_profile_wl_band(self):
        return 'IR'


    #######################################
    ### OVERRIDE FROM ObsMissionCassini ###
    #######################################

    def field_obs_mission_cassini_spacecraft_clock_count1(self):
        sc = self._supp_index_col('SPACECRAFT_CLOCK_START_COUNT')
        if sc == 'UNK':
            return None
        # COVIMS_8001 SCLKs are in some weird units where the number to the right
        # of the decimal can be > 255, so we just round down
        if '.' in sc:
            sc = sc.split('.')[0] + '.000'
        try:
            sc_cvt = opus_support.parse_cassini_sclk(sc)
        except Exception as e:
            self._log_nonrepeating_warning(f'Unable to parse Cassini SCLK "{sc}": {e}')
            return None
        return sc_cvt

    def field_obs_mission_cassini_spacecraft_clock_count2(self):
        sc = self._supp_index_col('SPACECRAFT_CLOCK_STOP_COUNT')
        if sc == 'UNK':
            return None
        # COVIMS_8001 SCLKs are in some weird units where the number to the right
        # of the decimal can be > 255, so we just round up
        if '.' in sc:
            sc = sc.split('.')[0] + '.000'
        try:
            sc_cvt = opus_support.parse_cassini_sclk(sc)+1 # Round up
        except Exception as e:
            self._log_nonrepeating_warning(f'Unable to parse Cassini SCLK "{sc}": {e}')
            return None

        sc1 = self.field_obs_mission_cassini_spacecraft_clock_count1()
        if sc1 is not None and sc_cvt < sc1:
            import_util.log_warning(
                f'spacecraft_clock_count1 ({sc1}) and spacecraft_clock_count2 ({sc_cvt}) '
                 +'are in the wrong order - setting to count1')
            sc_cvt = sc1

        return sc_cvt

    def field_obs_mission_cassini_mission_phase_name(self):
        return self._cassini_mission_phase_name()


    ####################################
    ### FIELD METHODS FOR THIS TABLE ###
    ####################################

    def field_obs_instrument_covims_opus_id(self):
        return self.opus_id

    def field_obs_instrument_covims_volume_id(self):
        return self.volume

    def field_obs_instrument_covims_instrument_id(self):
        return self.instrument_id

    def field_obs_instrument_covims_instrument_mode_id(self):
        return self._supp_index_col('INSTRUMENT_MODE_ID')

    def field_obs_instrument_covims_spectral_editing(self):
        return self._supp_index_col('SPECTRAL_EDITING')

    def field_obs_instrument_covims_spectral_summing(self):
        return self._supp_index_col('SPECTRAL_SUMMING')

    def field_obs_instrument_covims_star_tracking(self):
        return self._supp_index_col('STAR_TRACKING')

    def field_obs_instrument_covims_swath_width(self):
        return self._supp_index_col('SWATH_WIDTH')

    def field_obs_instrument_covims_swath_length(self):
        return self._supp_index_col('SWATH_LENGTH')

    def field_obs_instrument_covims_ir_exposure(self):
        ir_exp = self._supp_index_col('IR_EXPOSURE')
        if ir_exp is None:
            return None
        return ir_exp / 1000.

    def field_obs_instrument_covims_ir_sampling_mode_id(self):
        return self._supp_index_col('IR_SAMPLING_MODE_ID')

    def field_obs_instrument_covims_vis_exposure(self):
        return None

    def field_obs_instrument_covims_vis_sampling_mode_id(self):
        return 'N/A'

    def field_obs_instrument_covims_channel(self):
        return 'IR'
