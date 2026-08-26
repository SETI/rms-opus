"""The obs class for COCIRS_5xxx and COCIRS_6xxx.

Cassini CIRS apodized spectra. The primary file is the spectrum rather than the
observation index's own, and the spectral columns are computed in wavenumbers and
converted.
"""

from typing import cast

from opus_import.obs.field_types import FloatField, IntField, MultFieldRet, StrField
from opus_import.obs.obs_cassini_common_pds3 import ObsCassiniCommonPDS3
from opus_import.obs.obs_wavelength import MICRONS_PER_CM


class ObsVolumeCOCIRS56xxx(ObsCassiniCommonPDS3):
    #############################
    ### OVERRIDE FROM ObsBase ###
    #############################

    """The Cassini CIRS spectra of COCIRS_5xxx and COCIRS_6xxx.

    Its ``field_obs_*`` methods each fill the schema column their name ends in,
    declaring the type `opus_import.obs.field_types` gives that column.
    """

    @property
    def instrument_id(self) -> str | None:
        """The OPUS instrument id, ``COCIRS``."""
        return 'COCIRS'

    @property
    def primary_filespec(self) -> str | None:
        """The path of this spectrum's data file.

        Returns:
            The volume-prefixed path, which for these volumes is the spectrum file rather
            than the observation index's own.
        """
        # Format: "DATA/APODSPEC/SPEC0802010000_FP1.DAT"
        filespec = self._index_col('SPECTRUM_FILE_SPECIFICATION')
        assert self.bundle is not None
        return cast(str | None, self.bundle + '/' + filespec)

    def convert_filespec_from_lbl(self, filespec: str) -> str:
        """Convert a ``.LBL`` file specification to the ``.IMG`` data file.

        Parameters:
            filespec: The path, relative to the holdings root.

        Returns:
            The same path with ``.LBL`` replaced by ``.IMG``, which is the file
            this bundle's observations are identified by.
        """
        return filespec.replace('.LBL', '.IMG')


    ################################
    ### OVERRIDE FROM ObsGeneral ###
    ################################

    def field_obs_general_ring_obs_id(self) -> StrField:
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

    def field_obs_general_planet_id(self) -> MultFieldRet:
        return self._create_mult(self._cassini_planet_id())

    def _target_name(self) -> list[tuple[str | None, str | None]]:
        """The target this observation was aimed at.

        Returns:
            The intended target, as a one-element list.
        """
        return [self._cassini_intended_target_name()]

    def field_obs_general_quantity(self) -> MultFieldRet:
        return self._create_mult('THERMAL')

    def field_obs_general_observation_type(self) -> MultFieldRet:
        return self._create_mult('STS') # Spectral Time Series


    ############################
    ### OVERRIDE FROM ObsPds ###
    ############################

    def field_obs_pds_product_id(self) -> StrField:
        # Format: "DATA/APODSPEC/SPEC0802010000_FP1.DAT"
        return cast(StrField,
                    self._index_col('SPECTRUM_FILE_SPECIFICATION').split('/')[-1])

    def field_obs_pds_product_creation_time(self) -> FloatField:
        return None


    ###################################
    ### OVERRIDE FROM ObsWavelength ###
    ###################################

    def field_obs_wavelength_wavelength1(self) -> FloatField:
        wave_no2 = self._index_col('MAXIMUM_WAVENUMBER')
        if wave_no2 is None:
            return None
        return cast(FloatField, MICRONS_PER_CM / wave_no2)

    def field_obs_wavelength_wavelength2(self) -> FloatField:
        wave_no1 = self._index_col('MINIMUM_WAVENUMBER')
        if wave_no1 is None:
            return None
        return cast(FloatField, MICRONS_PER_CM / wave_no1)

    def field_obs_wavelength_wave_res1(self) -> FloatField:
        wnr = self._index_col('WAVENUMBER_RESOLUTION')
        wn2 = self._index_col('MAXIMUM_WAVENUMBER')
        if wnr is None or wn2 is None:
            return None
        return cast(FloatField, MICRONS_PER_CM*wnr/(wn2*wn2))

    def field_obs_wavelength_wave_res2(self) -> FloatField:
        wnr = self._index_col('WAVENUMBER_RESOLUTION')
        wn1 = self._index_col('MINIMUM_WAVENUMBER')
        if wnr is None or wn1 is None:
            return None
        return cast(FloatField, MICRONS_PER_CM*wnr/(wn1*wn1))

    def field_obs_wavelength_wave_no1(self) -> FloatField:
        return cast(FloatField, self._index_col('MINIMUM_WAVENUMBER'))

    def field_obs_wavelength_wave_no2(self) -> FloatField:
        return cast(FloatField, self._index_col('MAXIMUM_WAVENUMBER'))

    def field_obs_wavelength_wave_no_res1(self) -> FloatField:
        return cast(FloatField, self._index_col('WAVENUMBER_RESOLUTION'))

    def field_obs_wavelength_wave_no_res2(self) -> FloatField:
        return cast(FloatField, self._index_col('WAVENUMBER_RESOLUTION'))

    def field_obs_wavelength_spec_flag(self) -> MultFieldRet:
        return self._create_mult('Y')

    def field_obs_wavelength_spec_size(self) -> IntField:
        return cast(IntField, self._index_col('SPECTRUM_SAMPLES'))


    ##########################################
    ### OVERRIDE FROM ObsCassiniCommonPDS3 ###
    ##########################################

    def field_obs_mission_cassini_spacecraft_clock_count1(self) -> FloatField:
        sc = self._index_col('SPACECRAFT_CLOCK_START_COUNT')
        sc = self._fix_cassini_sclk(sc)
        if sc is None or not sc.startswith('1/') or sc[2] == ' ':
            self._log_nonrepeating_warning(
                f'Badly formatted SPACECRAFT_CLOCK_START_COUNT "{sc}"')
            return None
        return self._parse_cassini_sclk(sc, self._log_nonrepeating_warning)

    def field_obs_mission_cassini_spacecraft_clock_count2(self) -> FloatField:
        sc = self._index_col('SPACECRAFT_CLOCK_STOP_COUNT')
        sc = self._fix_cassini_sclk(sc)
        if sc is None or not sc.startswith('1/') or sc[2] == ' ':
            self._log_nonrepeating_warning(
                f'Badly formatted SPACECRAFT_CLOCK_STOP_COUNT "{sc}"')
            return None
        sc_cvt = self._parse_cassini_sclk(sc, self._log_nonrepeating_warning)
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
        mp = self._cassini_normalize_mission_phase_name()
        return self._create_mult(mp)


    ###############################################
    ### FIELD METHODS FOR obs_instrument_cocirs ###
    ###############################################

    def field_obs_instrument_cocirs_opus_id(self) -> StrField:
        return self.opus_id

    def field_obs_instrument_cocirs_bundle_id(self) -> StrField:
        return self.bundle

    def field_obs_instrument_cocirs_detector_id(self) -> MultFieldRet:
        return self._create_mult(self._index_col('DETECTOR_ID'))

    def field_obs_instrument_cocirs_instrument_mode_blinking_flag(self) -> MultFieldRet:
        blinking_flag = self._index_col('INSTRUMENT_MODE_BLINKING_FLAG')
        return self._create_mult(blinking_flag)

    def field_obs_instrument_cocirs_instrument_mode_even_flag(self) -> MultFieldRet:
        return self._create_mult(self._index_col('INSTRUMENT_MODE_EVEN_FLAG'))

    def field_obs_instrument_cocirs_instrument_mode_odd_flag(self) -> MultFieldRet:
        return self._create_mult(self._index_col('INSTRUMENT_MODE_ODD_FLAG'))

    def field_obs_instrument_cocirs_instrument_mode_centers_flag(self) -> MultFieldRet:
        center_flag = self._index_col('INSTRUMENT_MODE_CENTERS_FLAG')
        return self._create_mult(center_flag)

    def field_obs_instrument_cocirs_instrument_mode_pairs_flag(self) -> MultFieldRet:
        return self._create_mult(self._index_col('INSTRUMENT_MODE_PAIRS_FLAG'))

    def field_obs_instrument_cocirs_instrument_mode_all_flag(self) -> MultFieldRet:
        return self._create_mult(self._index_col('INSTRUMENT_MODE_ALL_FLAG'))
