"""What every HST instrument shares: its filters, and what they say about the observation.

An HST label records the filter wheels as one ``+``-joined name, and whether an
observation is an image or a spectrum follows from which filter is in place -- so each
instrument decides that from its own filter vocabulary, and this holds what they have in
common.
"""

from typing import cast

from opus_import.obs.field_types import FloatField, IntField, MultFieldRet, StrField
from opus_import.obs.obs_common_pds3 import ObsCommonPDS3


class ObsVolumeHubbleCommon(ObsCommonPDS3):
    """What every HST instrument shares.

    Its ``field_obs_*`` methods each fill the schema column their name ends in,
    declaring the type `opus_import.obs.field_types` gives that column.
    """

    def _decode_filters(self) -> tuple[str, str | None]:
        """Split the label's filter name into the two filter wheels' positions.

        Returns:
            The first wheel's filter and the second's, or None for the second where the
            label names only one.

        Raises:
            ValueError: If the label names more than two filters, which no HST instrument
                in these volumes has wheels for.
        """
        filter_name = self._index_col('FILTER_NAME')
        if filter_name.find('+') == -1:
            return filter_name, None
        first, second = filter_name.split('+')
        return first, second

    def _observation_type(self) -> str | None:
        """Whether this observation is an image, a spectrum, or a spectral image.

        Returns:
            ``'IMG'``, ``'SPE'`` or ``'SPI'``, or None where the instrument cannot tell.

        Raises:
            NotImplementedError: Always; each HST instrument must override this, because
                each records the distinction differently.
        """
        raise NotImplementedError

    def _is_image(self) -> bool:
        """Whether this observation is spatially resolved.

        Returns:
            True for an image or a spectral image, False for a plain spectrum.
        """
        obs_type = self._observation_type()
        assert obs_type in ('IMG', 'SPE', 'SPI')
        return obs_type == 'IMG' or obs_type == 'SPI'


    #############################
    ### OVERRIDE FROM ObsBase ###
    #############################

    @property
    def inst_host_id(self) -> str:
        """The OPUS instrument host id, ``HST``."""
        return 'HST'

    @property
    def mission_id(self) -> str:
        """The OPUS mission id, ``HST``."""
        return 'HST'

    @property
    def primary_filespec(self) -> str | None:
        """The path of this observation's data file.

        Computed from the primary index alone, for the reason
        `opus_import.obs.obs_cassini_common.ObsCassiniCommon.primary_filespec` gives.

        Returns:
            The volume-prefixed path.
        """
        # Note it's very important that this can be calculated using ONLY
        # the primary index, not the supplemental index!
        # This is because this (and the subsequent creation of opus_id) is used
        # to actually find the matching row in the supplemental index dictionary.
        # Format: "DATA/VISIT_05/O43B05C1Q.LBL"
        filespec = self._index_col('FILE_SPECIFICATION_NAME')
        assert self.bundle is not None
        return cast(str | None, self.bundle + '/' + filespec)


    ################################
    ### OVERRIDE FROM ObsGeneral ###
    ################################

    def field_obs_general_observation_duration(self) -> FloatField:
        return cast(FloatField, self._index_col('EXPOSURE_DURATION'))

    def field_obs_general_ring_obs_id(self) -> StrField:
        instrument_id = self._index_col('INSTRUMENT_ID')
        image_date = self._index_col('START_TIME')[:10]
        filename = self._index_col('PRODUCT_ID')
        planet = self._planet_id()
        if planet == 'OTH':
            pl_str = ''
        else:
            pl_str = planet[0]
        return f'{pl_str}_IMG_HST_{instrument_id}_{image_date}_{filename}'

    def _planet_id(self) -> str:
        """Return which planet this observation was of.

        Returns:
            The first three letters of the planet's name, or ``'OTH'`` for a target that is
            not one of the planets.
        """
        planet_name = self._index_col('PLANET_NAME')
        if planet_name not in ['VENUS', 'EARTH', 'MARS', 'JUPITER', 'SATURN',
                               'URANUS', 'NEPTUNE', 'PLUTO']:
            return 'OTH'
        return cast(str, planet_name[:3])

    def field_obs_general_planet_id(self) -> MultFieldRet:
        return self._create_mult(self._planet_id())

    def field_obs_general_quantity(self) -> MultFieldRet:
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

    def field_obs_type_image_image_type_id(self) -> MultFieldRet:
        if not self._is_image():
            return self._create_mult(None)
        return self._create_mult('FRAM')

    def field_obs_type_image_duration(self) -> FloatField:
        if not self._is_image():
            return None
        return self.field_obs_general_observation_duration()

    def field_obs_type_image_greater_pixel_size(self) -> IntField:
        if not self._is_image():
            return None
        lines = self._index_col('LINES')
        samples = self._index_col('LINE_SAMPLES')
        if lines is None or samples is None:
            return None
        return cast(IntField, max(lines, samples))

    def field_obs_type_image_lesser_pixel_size(self) -> IntField:
        if not self._is_image():
            return None
        lines = self._index_col('LINES')
        samples = self._index_col('LINE_SAMPLES')
        if lines is None or samples is None:
            return None
        return cast(IntField, min(lines, samples))


    ###################################
    ### OVERRIDE FROM ObsWavelength ###
    ###################################

    def field_obs_wavelength_wavelength1(self) -> FloatField:
        wl1 = self._index_col('MINIMUM_WAVELENGTH')
        wl2 = self._index_col('MAXIMUM_WAVELENGTH')
        if wl1 is None or wl2 is None:
            return None
        # This is necessary because in some cases these are backwards in the table!
        if wl1 > wl2:
            self._log_nonrepeating_warning(
                        'MAXIMUM_WAVELENGTH < MINIMUM_WAVELENGTH; swapping')
            return cast(FloatField, wl2)
        return cast(FloatField, wl1)

    def field_obs_wavelength_wavelength2(self) -> FloatField:
        wl1 = self._index_col('MINIMUM_WAVELENGTH')
        wl2 = self._index_col('MAXIMUM_WAVELENGTH')
        if wl1 is None or wl2 is None:
            return None
        # This is necessary because in some cases these are backwards in the table!
        if wl1 > wl2:
            self._log_nonrepeating_warning(
                        'MAXIMUM_WAVELENGTH < MINIMUM_WAVELENGTH; swapping')
            return cast(FloatField, wl1)
        return cast(FloatField, wl2)

    def field_obs_wavelength_wave_res1(self) -> FloatField:
        return cast(FloatField, self._index_col('WAVELENGTH_RESOLUTION'))

    def field_obs_wavelength_wave_res2(self) -> FloatField:
        return cast(FloatField, self._index_col('WAVELENGTH_RESOLUTION'))

    def field_obs_wavelength_wave_no_res1(self) -> FloatField:
        return self._wave_no_res_from_full_bandwidth()

    def field_obs_wavelength_wave_no_res2(self) -> FloatField:
        return self.field_obs_wavelength_wave_no_res1()


    ####################################
    ### FIELD METHODS FOR THIS TABLE ###
    ####################################

    def field_obs_mission_hubble_opus_id(self) -> StrField:
        return self.opus_id

    def field_obs_mission_hubble_bundle_id(self) -> StrField:
        return self.bundle

    def field_obs_mission_hubble_instrument_id(self) -> StrField:
        return self.instrument_id

    def field_obs_mission_hubble_stsci_group_id(self) -> StrField:
        return cast(StrField, self._index_col('STSCI_GROUP_ID'))

    def field_obs_mission_hubble_hst_proposal_id(self) -> IntField:
        return cast(IntField, self._index_col('HST_PROPOSAL_ID'))

    def field_obs_mission_hubble_hst_pi_name(self) -> StrField:
        return cast(StrField, self._index_col('HST_PI_NAME'))

    def field_obs_mission_hubble_detector_id(self) -> MultFieldRet:
        detector_id = self._index_col('DETECTOR_ID')
        if detector_id == '':
            return self._create_mult('UNKNOWN')
        instrument = self.instrument_id
        assert instrument is not None
        assert instrument is not None
        ret = instrument[3:] + '-' + detector_id
        return self._create_mult_keep_case(ret)

    def field_obs_mission_hubble_publication_date(self) -> FloatField:
        return self._time_from_index(column='PUBLICATION_DATE')

    def field_obs_mission_hubble_hst_target_name(self) -> StrField:
        return cast(StrField, self._index_col('HST_TARGET_NAME'))

    def field_obs_mission_hubble_fine_guidance_system_lock_type(self) -> MultFieldRet:
        lock_type = self._index_col('FINE_GUIDANCE_SYSTEM_LOCK_TYPE')
        return self._create_mult(lock_type)

    def field_obs_mission_hubble_filter_name(self) -> MultFieldRet:
        instrument = self.instrument_id
        assert instrument is not None
        filter_name = self._index_col('FILTER_NAME')
        if filter_name.startswith('ND'): # For STIS ND_3 => ND3
            filter_name = filter_name.replace('_', '')
        else:
            filter_name = filter_name.replace('_', ' ')
        ret = instrument[3:] + '-' + filter_name
        return self._create_mult_keep_case(col_val=ret, grouping=instrument[3:])

    def field_obs_mission_hubble_filter_type(self) -> MultFieldRet:
        raise NotImplementedError # Required

    def field_obs_mission_hubble_aperture_type(self) -> MultFieldRet:
        instrument = self.instrument_id
        assert instrument is not None
        aperture = self._index_col('APERTURE_TYPE')
        ret = instrument[3:] + '-' + aperture
        return self._create_mult_keep_case(col_val=ret, grouping=instrument[3:])

    def field_obs_mission_hubble_proposed_aperture_type(self) -> MultFieldRet:
        return self._create_mult(None)

    def field_obs_mission_hubble_exposure_type(self) -> MultFieldRet:
        return self._create_mult(self._index_col('EXPOSURE_TYPE'))

    def field_obs_mission_hubble_gain_mode_id(self) -> MultFieldRet:
        return self._create_mult(self._index_col('GAIN_MODE_ID'))

    def field_obs_mission_hubble_instrument_mode_id(self) -> MultFieldRet:
        return self._create_mult(self._index_col('INSTRUMENT_MODE_ID'))

    def field_obs_mission_hubble_pc1_flag(self) -> MultFieldRet:
        return self._create_mult(None)

    def field_obs_mission_hubble_wf2_flag(self) -> MultFieldRet:
        return self._create_mult(None)

    def field_obs_mission_hubble_wf3_flag(self) -> MultFieldRet:
        return self._create_mult(None)

    def field_obs_mission_hubble_wf4_flag(self) -> MultFieldRet:
        return self._create_mult(None)

    def field_obs_mission_hubble_targeted_detector_id(self) -> MultFieldRet:
        return self._create_mult(None)

    def field_obs_mission_hubble_optical_element(self) -> MultFieldRet:
        return self._create_mult(None)
