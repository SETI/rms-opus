"""The obs class for HSTNx_xxxx.

HST NICMOS observations.
"""


from opus_import.obs.field_types import IntField, MultFieldRet, as_int
from opus_import.obs.obs_type_image import SIXTEEN_BIT_IMAGE_LEVELS
from opus_import.obs.obs_volume_hubble_common import ObsVolumeHubbleCommon


class ObsVolumeHSTNxxxxx(ObsVolumeHubbleCommon):
    """The HST NICMOS observations of HSTNx_xxxx.

    Its ``field_obs_*`` methods each fill the schema column their name ends in,
    declaring the type `opus_import.obs.field_types` gives that column.
    """

    def _nicmos_spec_flag(self) -> tuple[bool, str, str | None]:
        """Decide whether this NICMOS observation is spectroscopic, from its filter.

        Returns:
            Whether the filter is a grism, followed by the two filter names.
        """
        filter1, filter2 = self._decode_filters()
        return filter1.startswith('G'), filter1, filter2


    #############################
    ### OVERRIDE FROM ObsBase ###
    #############################

    @property
    def instrument_id(self) -> str | None:
        """The OPUS instrument id, ``HSTNICMOS``."""
        return 'HSTNICMOS'


    ################################
    ### OVERRIDE FROM ObsGeneral ###
    ################################

    def _observation_type(self) -> str | None:
        """Whether this observation is an image or a spectral image.

        Returns:
            ``'SPI'`` through a grism and ``'IMG'`` otherwise.
        """
        if self._nicmos_spec_flag()[0]:
            return 'SPI'
        return 'IMG'


    def field_obs_general_observation_type(self) -> MultFieldRet:
        return self._create_mult(self._observation_type())


    ##################################
    ### OVERRIDE FROM ObsTypeImage ###
    ##################################

    def field_obs_type_image_levels(self) -> IntField:
        if not self._is_image():
            return None
        return SIXTEEN_BIT_IMAGE_LEVELS # NICMOS Inst Handbook, Sec 7.2.1


    ###################################
    ### OVERRIDE FROM ObsWavelength ###
    ###################################

    def field_obs_wavelength_spec_flag(self) -> MultFieldRet:
        if self._nicmos_spec_flag()[0]:
            return self._create_mult('Y')
        return self._create_mult('N')

    def field_obs_wavelength_spec_size(self) -> IntField:
        spec_flag, _filter1, filter2 = self._nicmos_spec_flag()
        if filter2 is not None:
            self._log_nonrepeating_error('filter2 not None')
            return None
        if not spec_flag:
            return None
        # For NICMOS, the entire detector is used for the spectrum, but we don't
        # know which direction it goes in, so just be generous and give the maximum
        # dimension of the image.
        lines = self._index_col('LINES')
        samples = self._index_col('LINE_SAMPLES')
        if lines is None and samples is None:
            return None
        if lines is None:
            return as_int(samples)
        if samples is None:
            return as_int(lines)
        return as_int(max(lines, samples))

    def field_obs_wavelength_polarization_type(self) -> MultFieldRet:
        filter_name = self._index_col('FILTER_NAME')
        if filter_name.find('POL') == -1:
            return self._create_mult('NONE')
        return self._create_mult('LINEAR')


    ###########################################
    ### OVERRIDE FROM ObsVolumeHubbleCommon ###
    ###########################################

    def field_obs_mission_hubble_filter_type(self) -> MultFieldRet:
        filter1, filter2 = self._decode_filters()

        # NICMOS doesn't do filter stacking
        if filter2 is not None:
            self._log_nonrepeating_error('filter2 not None')
            return self._create_mult(None)

        if filter1.startswith('G'):
            return self._create_mult('SP')
        if filter1.endswith('N'):
            return self._create_mult('N')
        if filter1.endswith('M'):
            return self._create_mult('M')
        if filter1.endswith('W'):
            return self._create_mult('W')

        if filter1.startswith('POL'):
            if filter1.endswith('S'):
                # POLxS is 0.8-1.3, about the same as wide filters
                return self._create_mult('W')
            elif filter1.endswith('L'):
                # POLxL is 1.89-2.1, about the same as medium filters
                return self._create_mult('M')

        if filter1 == 'BLANK': # Opaque
            return self._create_mult('OT')

        self._log_nonrepeating_error(f'Unknown filter "{filter1}"')
        return self._create_mult(None)
