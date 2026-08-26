"""The obs class for COVIMS_0xxx.

Cassini VIMS cubes. One index row describes both an infrared and a visible observation,
so each row is expanded into two and the OPUS id carries the channel.
"""

from typing import cast

from opus_import.obs.field_types import FloatField, IntField, MultFieldRet, StrField, as_int
from opus_import.obs.obs_cassini_common_pds3 import ObsCassiniCommonPDS3
from opus_import.obs.obs_type_image import TWELVE_BIT_IMAGE_LEVELS


class ObsVolumeCOVIMS0xxx(ObsCassiniCommonPDS3):
    """The Cassini VIMS cubes of COVIMS_0xxx.

    Its ``field_obs_*`` methods each fill the schema column their name ends in,
    declaring the type `opus_import.obs.field_types` gives that column.
    """

    def _is_image(self) -> bool:
        """Whether this observation is a spectral image rather than a single spectrum."""
        return cast(bool, self._index_col('INSTRUMENT_MODE_ID') == 'IMAGE')


    #############################
    ### OVERRIDE FROM ObsBase ###
    #############################

    @property
    def instrument_id(self) -> str | None:
        """The OPUS instrument id, ``COVIMS``."""
        return 'COVIMS'

    @property
    def primary_filespec(self) -> str | None:
        """The path of this observation's data file.

        Computed from the primary index alone, for the reason
        `opus_import.obs.obs_cassini_common.ObsCassiniCommon.primary_filespec` gives.

        Returns:
            The volume-prefixed path, built from the index's separate path and file
            columns.
        """
        # Note it's very important that this can be calculated using ONLY
        # the primary index, not the supplemental index!
        # This is because this (and the subsequent creation of opus_id) is used
        # to actually find the matching row in the supplemental index dictionary.
        path_name = self._index_col('PATH_NAME')
        file_name = self._index_col('FILE_NAME')
        return f'{self.bundle}{path_name}/{file_name}'

    def convert_filespec_from_lbl(self, filespec: str) -> str:
        """Convert a ``.lbl`` file specification to the ``.qub`` data file.

        Parameters:
            filespec: The path, relative to the holdings root.

        Returns:
            The same path with ``.lbl`` replaced by ``.qub``, which is the file
            this bundle's observations are identified by.
        """
        return filespec.replace('.lbl', '.qub')

    @property
    def opus_id(self) -> str | None:
        """The OPUS id of the current observation, with its channel appended.

        One COVIMS index row describes both an infrared and a visible observation, so the
        id
        the file specification alone yields is not unique.

        Returns:
            The id with ``_ir`` or ``_vis`` appended, or the plain id while the indexes
            are
            being scanned, before either channel has been selected.
        """
        if self.phase_name is None:
            # This happens during scanning the index/supp_index/geo files because
            # we don't have separate phases at that time.
            return super().opus_id
        base_opus_id = super().opus_id
        assert base_opus_id is not None
        return cast(str | None, base_opus_id + '_' + self.phase_name.lower())

    @property
    def phase_names(self) -> list[str]:
        """The channels this index row is expanded into.

        Returns:
            ``'VIS'``, ``'IR'``, or both, according to which sampling modes the row
            records
            as used. Every field method is called once per channel.
        """
        phase_names = []
        if self._index_col('VIS_SAMPLING_MODE_ID') != 'N/A':
            phase_names.append('VIS')
        if self._index_col('IR_SAMPLING_MODE_ID') != 'N/A':
            phase_names.append('IR')
        return phase_names


    ################################
    ### OVERRIDE FROM ObsGeneral ###
    ################################

    def _target_name(self) -> list[tuple[str | None, str | None]]:
        """The target this observation was aimed at.

        Returns:
            The intended target, as a one-element list.
        """
        return [self._cassini_intended_target_name()]

    # We occasionally don't bother to generate ring_geo data for COVIMS, like during
    # cruise, so just use the given RA/DEC from the index if needed. We don't make
    # any effort to figure out the min/max values.
    def field_obs_general_right_asc1(self) -> FloatField:
        ra = self._ring_geo_index_col('MINIMUM_RIGHT_ASCENSION')
        if ra is not None:
            return ra
        return cast(FloatField, self._index_col('RIGHT_ASCENSION'))

    def field_obs_general_right_asc2(self) -> FloatField:
        ra = self._ring_geo_index_col('MAXIMUM_RIGHT_ASCENSION')
        if ra is not None:
            return ra
        return cast(FloatField, self._index_col('RIGHT_ASCENSION'))

    def field_obs_general_declination1(self) -> FloatField:
        ra = self._ring_geo_index_col('MINIMUM_DECLINATION')
        if ra is not None:
            return ra
        return cast(FloatField, self._index_col('DECLINATION'))

    def field_obs_general_declination2(self) -> FloatField:
        ra = self._ring_geo_index_col('MAXIMUM_DECLINATION')
        if ra is not None:
            return ra
        return cast(FloatField, self._index_col('DECLINATION'))

    def field_obs_general_ring_obs_id(self) -> StrField:
        filename = self._index_col('FILE_NAME')
        image_num = filename[1:11]
        phase_name = self.phase_name
        planet = self._cassini_planet_id()
        if planet == 'OTH':
            pl_str = ''
        else:
            pl_str = planet[0]

        return f'{pl_str}_CUBE_CO_VIMS_{image_num}_{phase_name}'

    def field_obs_general_planet_id(self) -> MultFieldRet:
        return self._create_mult(self._cassini_planet_id())

    def field_obs_general_quantity(self) -> MultFieldRet:
        inst_mod = self._index_col('INSTRUMENT_MODE_ID')
        if inst_mod == 'OCCULTATION':
            return self._create_mult('OPDEPTH')
        return self._create_mult('REFLECT')

    def field_obs_general_observation_type(self) -> MultFieldRet:
        inst_mod = self._index_col('INSTRUMENT_MODE_ID')
        if inst_mod == 'OCCULTATION':
            return self._create_mult('TS') # Time Series
        return self._create_mult('SCU') # Spectral Cube


    ############################
    ### OVERRIDE FROM ObsPds ###
    ############################

    def field_obs_pds_note(self) -> StrField:
        return None


    ##################################
    ### OVERRIDE FROM ObsTypeImage ###
    ##################################

    def field_obs_type_image_image_type_id(self) -> MultFieldRet:
        inst_mod = self._index_col('INSTRUMENT_MODE_ID')
        if inst_mod != 'IMAGE':
            return self._create_mult(None)
        if self.phase_name == 'VIS':
            return self._create_mult('PUSH')
        return self._create_mult('RAST')

    def field_obs_type_image_duration(self) -> FloatField:
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
            return cast(FloatField, ir_exp/1000)
        if vis_exp is None:
            return None
        if vis_exp < 0:
            self._log_nonrepeating_warning(f'VIS Exposure {vis_exp} is < 0')
            return None
        return cast(FloatField, vis_exp/1000)

    def field_obs_type_image_levels(self) -> IntField:
        if not self._is_image():
            return None
        return TWELVE_BIT_IMAGE_LEVELS

    def field_obs_type_image_greater_pixel_size(self) -> IntField:
        if not self._is_image():
            return None
        return as_int(max(self._index_col('SWATH_WIDTH'), self._index_col('SWATH_LENGTH')))

    def field_obs_type_image_lesser_pixel_size(self) -> IntField:
        if not self._is_image():
            return None
        return as_int(min(self._index_col('SWATH_WIDTH'), self._index_col('SWATH_LENGTH')))


    ###################################
    ### OVERRIDE FROM ObsWavelength ###
    ###################################

    def field_obs_wavelength_wavelength1(self) -> FloatField:
        if self.phase_name == 'IR':
            return 0.8842
        return 0.35054

    def field_obs_wavelength_wavelength2(self) -> FloatField:
        if self.phase_name == 'IR':
            return 5.1225
        return 1.04598

    def field_obs_wavelength_wave_res1(self) -> FloatField:
        if self.phase_name == 'IR':
            return 0.01662
        return 0.0073204

    def field_obs_wavelength_wave_res2(self) -> FloatField:
        if self.phase_name == 'IR':
            return 0.01662
        return 0.0073204

    def field_obs_wavelength_wave_no_res1(self) -> FloatField:
        return self._wave_no_res1_from_wave_res()

    def field_obs_wavelength_wave_no_res2(self) -> FloatField:
        return self._wave_no_res2_from_wave_res()

    def field_obs_wavelength_spec_flag(self) -> MultFieldRet:
        return self._create_mult('Y')

    def field_obs_wavelength_spec_size(self) -> IntField:
        if self.phase_name == 'IR':
            return 256
        return 96


    ##########################################
    ### OVERRIDE FROM ObsCassiniCommonPDS3 ###
    ##########################################

    def field_obs_mission_cassini_spacecraft_clock_count1(self) -> FloatField:
        """The start clock count, with the partition VIMS omits.

        Returns:
            The count as a number, or None if the index has none. The raw column is
            checked before the partition prefix is added: prefixing None raises
            `TypeError` and aborts the bundle, and `_fix_cassini_sclk` returns None
            only for a None input, so a check placed after the concatenation cannot
            see the missing-count case it names.
        """
        count = self._index_col('SPACECRAFT_CLOCK_START_COUNT')
        if count is None:
            self._log_nonrepeating_error('Missing SPACECRAFT_CLOCK_START_COUNT')
            return None
        sc = self._fix_cassini_sclk('1/' + count)
        # Not None: `_fix_cassini_sclk` returns None only for a None input, and `count`
        # was checked above. Asserting rather than re-checking keeps the dead branch
        # this method used to carry from coming back.
        assert sc is not None
        return self._parse_cassini_sclk(sc)

    def field_obs_mission_cassini_spacecraft_clock_count2(self) -> FloatField:
        """The stop clock count, never earlier than the start count.

        Returns:
            The count as a number, or None if the index has none. The raw column is
            checked before the partition prefix is added, for the reason
            `field_obs_mission_cassini_spacecraft_clock_count1` gives.
        """
        count = self._index_col('SPACECRAFT_CLOCK_STOP_COUNT')
        if count is None:
            self._log_nonrepeating_error('Missing SPACECRAFT_CLOCK_STOP_COUNT')
            return None
        sc = self._fix_cassini_sclk('1/' + count)
        assert sc is not None  # for the reason count1 gives
        sc_cvt = self._parse_cassini_sclk(sc)
        if sc_cvt is None:
            return None

        sc1 = self.field_obs_mission_cassini_spacecraft_clock_count1()
        if sc1 is not None and sc_cvt < sc1:
            self._log_warning(
                f'spacecraft_clock_count1 ({sc1}) and spacecraft_clock_count2 '+
                f'({sc_cvt}) are in the wrong order - setting to count1')
            sc_cvt = sc1

        return sc_cvt

    def field_obs_mission_cassini_mission_phase_name(self) -> MultFieldRet:
        return self._create_mult(self._cassini_normalize_mission_phase_name())

    def field_obs_mission_cassini_sequence_id(self) -> StrField:
        return cast(StrField, self._index_col('SEQ_ID'))


    ###############################################
    ### FIELD METHODS FOR obs_instrument_covims ###
    ###############################################

    def field_obs_instrument_covims_opus_id(self) -> StrField:
        return self.opus_id

    def field_obs_instrument_covims_bundle_id(self) -> StrField:
        return self.bundle

    def field_obs_instrument_covims_instrument_mode_id(self) -> MultFieldRet:
        return self._create_mult(self._index_col('INSTRUMENT_MODE_ID'))

    def field_obs_instrument_covims_spectral_editing(self) -> MultFieldRet:
        return self._create_mult(self._index_col('SPECTRAL_EDITING'))

    def field_obs_instrument_covims_spectral_summing(self) -> MultFieldRet:
        return self._create_mult(self._index_col('SPECTRAL_SUMMING'))

    def field_obs_instrument_covims_star_tracking(self) -> MultFieldRet:
        return self._create_mult(self._index_col('STAR_TRACKING'))

    def field_obs_instrument_covims_swath_width(self) -> IntField:
        return as_int(self._index_col('SWATH_WIDTH'))

    def field_obs_instrument_covims_swath_length(self) -> IntField:
        return as_int(self._index_col('SWATH_LENGTH'))

    def field_obs_instrument_covims_ir_exposure(self) -> FloatField:
        ir_exp = self._index_col('IR_EXPOSURE')
        if ir_exp is None:
            return None
        return cast(FloatField, ir_exp / 1000.)

    def field_obs_instrument_covims_ir_sampling_mode_id(self) -> MultFieldRet:
        return self._create_mult(self._index_col('IR_SAMPLING_MODE_ID'))

    def field_obs_instrument_covims_vis_exposure(self) -> FloatField:
        vis_exp = self._index_col('VIS_EXPOSURE')
        if vis_exp is None:
            return None
        return cast(FloatField, vis_exp / 1000.)

    def field_obs_instrument_covims_vis_sampling_mode_id(self) -> MultFieldRet:
        return self._create_mult(self._index_col('VIS_SAMPLING_MODE_ID'))

    def field_obs_instrument_covims_channel(self) -> MultFieldRet:
        return self._create_mult_keep_case(self.phase_name)
