################################################################################
# obs_instrument_cocirs.py
#
# Defines the ObsInstrumentCOCIRS class, which encapsulates fields in the
# common, obs_mission_cassini, and obs_instrument_cocirs tables for volumes
# COCIRS_[56]xxx.
################################################################################

import opus_support

from obs_mission_cassini import ObsMissionCassini


class ObsInstrumentCOCIRS(ObsMissionCassini):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


    #############################
    ### OVERRIDE FROM ObsBase ###
    #############################

    @property
    def instrument_id(self):
        return 'COCIRS'

    @property
    def primary_filespec(self):
        # Format: "DATA/APODSPEC/SPEC0802010000_FP1.DAT"
        filespec = self._index_col('SPECTRUM_FILE_SPECIFICATION')
        return self.volume + '/' + filespec

    def convert_filespec_from_lbl(self, filespec):
        return filespec.replace('.LBL', '.IMG')


    ################################
    ### OVERRIDE FROM ObsGeneral ###
    ################################

    def field_obs_general_ring_obs_id(self):
        instrument_id = self._index_col('DETECTOR_ID')
        filename = self._index_col('SPECTRUM_FILE_SPECIFICATION').split('/')[-1]
        if not filename.startswith('SPEC') or not filename.endswith('.DAT'):
            self._log_nonrepeating_error(
                f'Bad format SPECTRUM_FILE_SPECIFICATION "{filename}"')
            return None
        image_num = filename[4:14]
        planet = self._cassini_planet_id()
        if planet == 'OTH':
            pl_str = ''
        else:
            pl_str = planet[0]

        return f'{pl_str}_SPEC_CO_CIRS_{image_num}_{instrument_id}'

    def field_obs_general_planet_id(self):
        planet_id = self._cassini_planet_id()
        return self._create_mult(planet_id)

    def field_obs_general_target_name(self):
        col_val, disp_name = self._cassini_intended_target_name()
        return self._create_mult(col_val=col_val, disp_name=disp_name)

    def field_obs_general_quantity(self):
        return self._create_mult('THERMAL')

    def field_obs_general_observation_type(self):
        return self._create_mult('STS') # Spectral Time Series


    ############################
    ### OVERRIDE FROM ObsPds ###
    ############################

    def field_obs_pds_product_id(self):
        # Format: "DATA/APODSPEC/SPEC0802010000_FP1.DAT"
        return self._index_col('SPECTRUM_FILE_SPECIFICATION').split('/')[-1]

    def field_obs_pds_product_creation_time(self):
        return None


    ###################################
    ### OVERRIDE FROM ObsWavelength ###
    ###################################

    def field_obs_wavelength_wavelength1(self):
        wave_no2 = self._index_col('MAXIMUM_WAVENUMBER')
        if wave_no2 is None:
            return None
        return 10000. / wave_no2

    def field_obs_wavelength_wavelength2(self):
        wave_no1 = self._index_col('MINIMUM_WAVENUMBER')
        if wave_no1 is None:
            return None
        return 10000. / wave_no1

    def field_obs_wavelength_wave_res1(self):
        wnr = self._index_col('WAVENUMBER_RESOLUTION')
        wn2 = self._index_col('MAXIMUM_WAVENUMBER')
        if wnr is None or wn2 is None:
            return None
        return 10000.*wnr/(wn2*wn2)

    def field_obs_wavelength_wave_res2(self):
        wnr = self._index_col('WAVENUMBER_RESOLUTION')
        wn1 = self._index_col('MINIMUM_WAVENUMBER')
        if wnr is None or wn1 is None:
            return None
        return 10000.*wnr/(wn1*wn1)

    def field_obs_wavelength_wave_no1(self):
        return self._index_col('MINIMUM_WAVENUMBER')

    def field_obs_wavelength_wave_no2(self):
        return self._index_col('MAXIMUM_WAVENUMBER')

    def field_obs_wavelength_wave_no_res1(self):
        return self._index_col('WAVENUMBER_RESOLUTION')

    def field_obs_wavelength_wave_no_res2(self):
        return self._index_col('WAVENUMBER_RESOLUTION')

    def field_obs_wavelength_spec_flag(self):
        return 'Y'

    def field_obs_wavelength_spec_size(self):
        return self._index_col('SPECTRUM_SAMPLES')


    #######################################
    ### OVERRIDE FROM ObsMissionCassini ###
    #######################################

    def field_obs_mission_cassini_spacecraft_clock_count1(self):
        sc = self._index_col('SPACECRAFT_CLOCK_START_COUNT')
        sc = self._fix_cassini_sclk(sc)
        if not sc.startswith('1/') or sc[2] == ' ':
            self._log_nonrepeating_warning(
                f'Badly formatted SPACECRAFT_CLOCK_START_COUNT "{sc}"')
            return None
        try:
            sc_cvt = opus_support.parse_cassini_sclk(sc)
        except Exception as e:
            self._log_nonrepeating_warning(f'Unable to parse Cassini SCLK "{sc}": {e}')
            return None
        return sc_cvt

    def field_obs_mission_cassini_spacecraft_clock_count2(self):
        sc = self._index_col('SPACECRAFT_CLOCK_STOP_COUNT')
        sc = self._fix_cassini_sclk(sc)
        if not sc.startswith('1/') or sc[2] == ' ':
            self._log_nonrepeating_warning(
                f'Badly formatted SPACECRAFT_CLOCK_START_COUNT "{sc}"')
            return None
        try:
            sc_cvt = opus_support.parse_cassini_sclk(sc)
        except Exception as e:
            self._log_nonrepeating_warning(f'Unable to parse Cassini SCLK "{sc}": {e}')
            return None

        sc1 = self.field_obs_mission_cassini_spacecraft_clock_count1()
        if sc1 is not None and sc_cvt < sc1:
            self._log_nonrepeating_warning(
                f'spacecraft_clock_count1 ({sc1}) and spacecraft_clock_count2 '+
                f'({sc_cvt}) are in the wrong order - setting to count1')
            sc_cvt = sc1

        return sc_cvt

    def field_obs_mission_cassini_mission_phase_name(self):
        mp = self._index_col('MISSION_PHASE_NAME')
        if mp.upper() == 'NULL':
            return None
        return mp.replace('_', ' ')


    ###############################################
    ### FIELD METHODS FOR obs_instrument_cocirs ###
    ###############################################

    def field_obs_instrument_cocirs_opus_id(self):
        return self.opus_id

    def field_obs_instrument_cocirs_volume_id(self):
        return self.volume

    def field_obs_instrument_cocirs_instrument_id(self):
        return self.instrument_id

    def field_obs_instrument_cocirs_detector_id(self):
        return self._index_col('DETECTOR_ID')

    def field_obs_instrument_cocirs_instrument_mode_blinking_flag(self):
        return self._index_col('INSTRUMENT_MODE_BLINKING_FLAG')

    def field_obs_instrument_cocirs_instrument_mode_even_flag(self):
        return self._index_col('INSTRUMENT_MODE_EVEN_FLAG')

    def field_obs_instrument_cocirs_instrument_mode_odd_flag(self):
        return self._index_col('INSTRUMENT_MODE_ODD_FLAG')

    def field_obs_instrument_cocirs_instrument_mode_centers_flag(self):
        return self._index_col('INSTRUMENT_MODE_CENTERS_FLAG')

    def field_obs_instrument_cocirs_instrument_mode_pairs_flag(self):
        return self._index_col('INSTRUMENT_MODE_PAIRS_FLAG')

    def field_obs_instrument_cocirs_instrument_mode_all_flag(self):
        return self._index_col('INSTRUMENT_MODE_ALL_FLAG')
