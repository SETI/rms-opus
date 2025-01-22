################################################################################
# obs_volume_couvis_8xxx.py
#
# Defines the ObsVolumeCOUVIS8xxx class, which encapsulates fields in the
# common, obs_mission_cassini, and obs_instrument_couvis tables for COUVIS_8001
# occultations.
################################################################################

import opus_support

from obs_volume_couvis_covims_occ_common import ObsVolumeUVISVIMSOccCommon


class ObsVolumeCOUVIS8xxx(ObsVolumeUVISVIMSOccCommon):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


    #############################
    ### OVERRIDE FROM ObsBase ###
    #############################

    @property
    def instrument_id(self):
        return 'COUVIS'


    ###################################
    ### OVERRIDE FROM ObsWavelength ###
    ###################################

    def field_obs_wavelength_wavelength1(self):
        return self._index_col('MINIMUM_WAVELENGTH') / 1000. # nm -> micron

    def field_obs_wavelength_wavelength2(self):
        return self._index_col('MAXIMUM_WAVELENGTH') / 1000. # nm -> micron

    def field_obs_wavelength_wave_res1(self):
        return self._wave_res_from_full_bandwidth()

    def field_obs_wavelength_wave_res2(self):
        return self.field_obs_wavelength_wave_res1()

    def field_obs_wavelength_wave_no_res1(self):
        return self._wave_no_res_from_full_bandwidth()

    def field_obs_wavelength_wave_no_res2(self):
        return self.field_obs_wavelength_wave_no_res1()


    ################################
    ### OVERRIDE FROM ObsProfile ###
    ################################

    def field_obs_profile_temporal_sampling(self):
        return self._supp_index_col('INTEGRATION_DURATION') / 1000 # msec -> sec

    def field_obs_profile_wl_band(self):
        return self._create_mult('UV')


    ############################################
    ### OVERRIDE FROM ObsVolumeCassiniCommon ###
    ############################################

    def field_obs_mission_cassini_spacecraft_clock_count1(self):
        sc = self._supp_index_col('SPACECRAFT_CLOCK_START_COUNT')
        if sc == 'UNK':
            return None
        try:
            sc_cvt = opus_support.parse_cassini_sclk(sc)
        except Exception as e:
            self._log_nonrepeating_error(f'Unable to parse Cassini SCLK "{sc}": {e}')
            return None
        return sc_cvt

    def field_obs_mission_cassini_spacecraft_clock_count2(self):
        sc = self._supp_index_col('SPACECRAFT_CLOCK_STOP_COUNT')
        if sc == 'UNK':
            return None
        try:
            sc_cvt = opus_support.parse_cassini_sclk(sc)
        except Exception as e:
            self._log_nonrepeating_error(f'Unable to parse Cassini SCLK "{sc}": {e}')
            return None

        sc1 = self.field_obs_mission_cassini_spacecraft_clock_count1()
        if sc1 is not None and sc_cvt < sc1:
            self._log_nonrepeating_warning(
                f'spacecraft_clock_count1 ({sc1}) and spacecraft_clock_count2 '+
                f'({sc_cvt}) are in the wrong order - setting to count1')
            sc_cvt = sc1

        return sc_cvt

    def field_obs_mission_cassini_mission_phase_name(self):
        return self._create_mult(self._cassini_normalize_mission_phase_name())


    ###############################################
    ### FIELD METHODS FOR obs_instrument_couvis ###
    ###############################################

    def field_obs_instrument_couvis_opus_id(self):
        return self.opus_id

    def field_obs_instrument_couvis_bundle_id(self):
        return self.bundle

    def field_obs_instrument_couvis_instrument_id(self):
        return self.instrument_id

    def field_obs_instrument_couvis_observation_type(self):
        return self._create_mult('NONE')

    def field_obs_instrument_couvis_integration_duration(self):
        return self.field_obs_profile_temporal_sampling()

    def field_obs_instrument_couvis_compression_type(self):
        comp = self._supp_index_col('COMPRESSION_TYPE')
        return self._create_mult_keep_case(comp)

    def field_obs_instrument_couvis_occultation_port_state(self):
        return self._create_mult('N/A')

    def field_obs_instrument_couvis_slit_state(self):
        return self._create_mult('NULL')

    def field_obs_instrument_couvis_test_pulse_state(self):
        return self._create_mult(None)

    def field_obs_instrument_couvis_dwell_time(self):
        return self._create_mult(None)

    def field_obs_instrument_couvis_channel(self):
        return self._create_mult_keep_case('HSP')

    def field_obs_instrument_couvis_band1(self):
        return None

    def field_obs_instrument_couvis_band2(self):
        return None

    def field_obs_instrument_couvis_band_bin(self):
        return None

    def field_obs_instrument_couvis_line1(self):
        return None

    def field_obs_instrument_couvis_line2(self):
        return None

    def field_obs_instrument_couvis_line_bin(self):
        return None

    def field_obs_instrument_couvis_samples(self):
        return None
