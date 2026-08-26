"""The obs class for COVIMS_8001.

Cassini VIMS stellar ring occultation profiles.
"""

from typing import cast

from opus_import.obs.field_types import FloatField, IntField, MultFieldRet, StrField, as_int
from opus_import.obs.obs_volume_couvis_covims_occ_common import ObsVolumeUVISVIMSOccCommon


class ObsVolumeCOVIMS8xxx(ObsVolumeUVISVIMSOccCommon):
    #############################
    ### OVERRIDE FROM ObsBase ###
    #############################

    """The Cassini VIMS ring occultation profiles of COVIMS_8001.

    Its ``field_obs_*`` methods each fill the schema column their name ends in,
    declaring the type `opus_import.obs.field_types` gives that column.
    """

    @property
    def instrument_id(self) -> str | None:
        """The OPUS instrument id, ``COVIMS``."""
        return 'COVIMS'


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
        return cast(FloatField, self._supp_index_col('IR_EXPOSURE') / 1000) # msec -> sec

    def field_obs_profile_wl_band(self) -> MultFieldRet:
        return self._create_mult('IR')


    ##########################################
    ### OVERRIDE FROM ObsCassiniCommonPDS3 ###
    ##########################################

    def field_obs_mission_cassini_spacecraft_clock_count1(self) -> FloatField:
        sc = self._supp_index_col('SPACECRAFT_CLOCK_START_COUNT')
        if sc == 'UNK':
            return None
        # COVIMS_8001 SCLKs are in some weird units where the number to the right
        # of the decimal can be > 255, so we just round down
        if '.' in sc:
            sc = sc.split('.')[0] + '.000'
        return self._parse_cassini_sclk(sc)

    def field_obs_mission_cassini_spacecraft_clock_count2(self) -> FloatField:
        sc = self._supp_index_col('SPACECRAFT_CLOCK_STOP_COUNT')
        if sc == 'UNK':
            return None
        # COVIMS_8001 SCLKs are in some weird units where the number to the right
        # of the decimal can be > 255, so we just round up
        if '.' in sc:
            sc = sc.split('.')[0] + '.000'
        sc_cvt = self._parse_cassini_sclk(sc)
        if sc_cvt is None:
            return None
        sc_cvt += 1 # Round up

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
    ### FIELD METHODS FOR obs_instrument_covims ###
    ###############################################

    def field_obs_instrument_covims_opus_id(self) -> StrField:
        return self.opus_id

    def field_obs_instrument_covims_bundle_id(self) -> StrField:
        return self.bundle

    def field_obs_instrument_covims_instrument_mode_id(self) -> MultFieldRet:
        return self._create_mult(self._supp_index_col('INSTRUMENT_MODE_ID'))

    def field_obs_instrument_covims_spectral_editing(self) -> MultFieldRet:
        return self._create_mult(self._supp_index_col('SPECTRAL_EDITING'))

    def field_obs_instrument_covims_spectral_summing(self) -> MultFieldRet:
        return self._create_mult(self._supp_index_col('SPECTRAL_SUMMING'))

    def field_obs_instrument_covims_star_tracking(self) -> MultFieldRet:
        return self._create_mult(self._supp_index_col('STAR_TRACKING'))

    def field_obs_instrument_covims_swath_width(self) -> IntField:
        return as_int(self._supp_index_col('SWATH_WIDTH'))

    def field_obs_instrument_covims_swath_length(self) -> IntField:
        return as_int(self._supp_index_col('SWATH_LENGTH'))

    def field_obs_instrument_covims_ir_exposure(self) -> FloatField:
        ir_exp = self._supp_index_col('IR_EXPOSURE')
        if ir_exp is None:
            return None
        return cast(FloatField, ir_exp / 1000.)

    def field_obs_instrument_covims_ir_sampling_mode_id(self) -> MultFieldRet:
        return self._create_mult(self._supp_index_col('IR_SAMPLING_MODE_ID'))

    def field_obs_instrument_covims_vis_exposure(self) -> FloatField:
        return None

    def field_obs_instrument_covims_vis_sampling_mode_id(self) -> MultFieldRet:
        return self._create_mult('N/A')

    def field_obs_instrument_covims_channel(self) -> MultFieldRet:
        return self._create_mult('IR')
