"""The obs class for COUVIS_8001.

Cassini UVIS stellar ring occultation profiles.
"""

from typing import cast

from opus_import.obs.field_types import FloatField, IntField, MultFieldRet, StrField
from opus_import.obs.obs_volume_couvis_covims_occ_common import ObsVolumeUVISVIMSOccCommon


class ObsVolumeCOUVIS8xxx(ObsVolumeUVISVIMSOccCommon):
    """The Cassini UVIS ring occultation profiles of COUVIS_8001.

    Its ``field_obs_*`` methods each fill the schema column their name ends in,
    declaring the type `opus_import.obs.field_types` gives that column.
    """

    #############################
    ### OVERRIDE FROM ObsBase ###
    #############################


    @property
    def instrument_id(self) -> str | None:
        """The OPUS instrument id, ``COUVIS``."""
        return 'COUVIS'


    ###################################
    ### OVERRIDE FROM ObsWavelength ###
    ###################################

    def field_obs_wavelength_wavelength1(self) -> FloatField:
        return cast(FloatField,
                    self._index_col('MINIMUM_WAVELENGTH') / 1000.) # nm -> micron

    def field_obs_wavelength_wavelength2(self) -> FloatField:
        return cast(FloatField,
                    self._index_col('MAXIMUM_WAVELENGTH') / 1000.) # nm -> micron

    def field_obs_wavelength_wave_res1(self) -> FloatField:
        return self._wave_res_from_full_bandwidth()

    def field_obs_wavelength_wave_res2(self) -> FloatField:
        return self.field_obs_wavelength_wave_res1()

    def field_obs_wavelength_wave_no_res1(self) -> FloatField:
        return self._wave_no_res_from_full_bandwidth()

    def field_obs_wavelength_wave_no_res2(self) -> FloatField:
        return self.field_obs_wavelength_wave_no_res1()


    ################################
    ### OVERRIDE FROM ObsProfile ###
    ################################

    def field_obs_profile_temporal_sampling(self) -> FloatField:
        return cast(FloatField,
                    self._supp_index_col('INTEGRATION_DURATION') / 1000) # msec -> sec

    def field_obs_profile_wl_band(self) -> MultFieldRet:
        return self._create_mult('UV')


    ##########################################
    ### OVERRIDE FROM ObsCassiniCommonPDS3 ###
    ##########################################

    def field_obs_mission_cassini_spacecraft_clock_count1(self) -> FloatField:
        sc = self._supp_index_col('SPACECRAFT_CLOCK_START_COUNT')
        if sc == 'UNK':
            return None
        return self._parse_cassini_sclk(sc)

    def field_obs_mission_cassini_spacecraft_clock_count2(self) -> FloatField:
        sc = self._supp_index_col('SPACECRAFT_CLOCK_STOP_COUNT')
        if sc == 'UNK':
            return None
        sc_cvt = self._parse_cassini_sclk(sc)
        if sc_cvt is None:
            return None

        sc1 = self.field_obs_mission_cassini_spacecraft_clock_count1()
        if sc1 is not None and sc_cvt < sc1:
            self._log_nonrepeating_warning(
                f'spacecraft_clock_count1 ({sc1}) and spacecraft_clock_count2 '+
                f'({sc_cvt}) are in the wrong order - setting to count1')
            sc_cvt = sc1

        return sc_cvt

    def field_obs_mission_cassini_mission_phase_name(self) -> MultFieldRet:
        return self._create_mult(self._cassini_normalize_mission_phase_name())


    ###############################################
    ### FIELD METHODS FOR obs_instrument_couvis ###
    ###############################################

    def field_obs_instrument_couvis_opus_id(self) -> StrField:
        return self.opus_id

    def field_obs_instrument_couvis_bundle_id(self) -> StrField:
        return self.bundle

    def field_obs_instrument_couvis_observation_type(self) -> MultFieldRet:
        return self._create_mult('NONE')

    def field_obs_instrument_couvis_integration_duration(self) -> FloatField:
        return self.field_obs_profile_temporal_sampling()

    def field_obs_instrument_couvis_compression_type(self) -> MultFieldRet:
        comp = self._supp_index_col('COMPRESSION_TYPE')
        return self._create_mult_keep_case(comp)

    def field_obs_instrument_couvis_occultation_port_state(self) -> MultFieldRet:
        return self._create_mult('N/A')

    def field_obs_instrument_couvis_slit_state(self) -> MultFieldRet:
        return self._create_mult('NULL')

    def field_obs_instrument_couvis_test_pulse_state(self) -> MultFieldRet:
        return self._create_mult(None)

    def field_obs_instrument_couvis_dwell_time(self) -> MultFieldRet:
        return self._create_mult(None)

    def field_obs_instrument_couvis_channel(self) -> MultFieldRet:
        return self._create_mult_keep_case('HSP')

    def field_obs_instrument_couvis_band1(self) -> IntField:
        return None

    def field_obs_instrument_couvis_band2(self) -> IntField:
        return None

    def field_obs_instrument_couvis_band_bin(self) -> IntField:
        return None

    def field_obs_instrument_couvis_line1(self) -> IntField:
        return None

    def field_obs_instrument_couvis_line2(self) -> IntField:
        return None

    def field_obs_instrument_couvis_line_bin(self) -> IntField:
        return None

    def field_obs_instrument_couvis_samples(self) -> IntField:
        return None
