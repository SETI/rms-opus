"""The obs class for HSTIx_xxxx.

HST WFC3 observations.
"""

from opus_import.obs.field_types import IntField, MultFieldRet, as_int
from opus_import.obs.obs_type_image import SIXTEEN_BIT_IMAGE_LEVELS
from opus_import.obs.obs_volume_hubble_common import ObsVolumeHubbleCommon


class ObsVolumeHSTIxxxxx(ObsVolumeHubbleCommon):
    """The HST WFC3 observations of HSTIx_xxxx.

    Its ``field_obs_*`` methods each fill the schema column their name ends in,
    declaring the type `opus_import.obs.field_types` gives that column.
    """

    def _wfc3_spec_flag(self) -> tuple[bool, str, str | None] | None:
        """Decide whether this WFC3 observation is spectroscopic, from its filter.

        Returns:
            Whether the filter is a grism, followed by the two filter names, or None if
            the
            label carries a second filter -- which WFC3 has no wheel for, and which is
            logged as an error.
        """
        filter1, filter2 = self._decode_filters()
        if filter2 is not None:
            self._log_nonrepeating_error('filter2 not None')
            return None
        return filter1.startswith('G'), filter1, filter2

    #############################
    ### OVERRIDE FROM ObsBase ###
    #############################

    @property
    def instrument_id(self) -> str | None:
        """The OPUS instrument id, ``HSTWFC3``."""
        return 'HSTWFC3'

    ################################
    ### OVERRIDE FROM ObsGeneral ###
    ################################

    def _observation_type(self) -> str | None:
        """Whether this observation is an image or a spectral image.

        Returns:
            ``'SPI'`` through a grism and ``'IMG'`` otherwise, or None if the filter could
            not be decoded.
        """
        spec_flag = self._wfc3_spec_flag()
        if spec_flag is None:
            return None
        if spec_flag[0]:
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
        return SIXTEEN_BIT_IMAGE_LEVELS  # WFC3 Inst Handbook, Sec 2.2.3

    ###################################
    ### OVERRIDE FROM ObsWavelength ###
    ###################################

    def field_obs_wavelength_spec_flag(self) -> MultFieldRet:
        spec_flag = self._wfc3_spec_flag()
        if spec_flag is None:
            return self._create_mult(None)
        if spec_flag[0]:
            return self._create_mult('Y')
        return self._create_mult('N')

    def field_obs_wavelength_spec_size(self) -> IntField:
        wfc3_spec_flag = self._wfc3_spec_flag()
        if wfc3_spec_flag is None:
            return None
        spec_flag, filter1, _filter2 = wfc3_spec_flag
        if not spec_flag:
            return None

        # We can't use WAVELENGTH_RESOLUTION because it's too aggressive.
        # Instead we use the Resolving Power (lambda / d-lambda) from WFC3 Inst
        # Handbook Table 8.1

        if filter1 == 'G280':
            wr = 300.0 / 70 * 0.001
            bw = (450 - 190) * 0.001
        elif filter1 == 'G102':
            wr = 1000.0 / 210 * 0.001
            bw = (1150 - 800) * 0.001
        elif filter1 == 'G141':
            wr = 1400.0 / 130 * 0.001
            bw = (1700 - 1075) * 0.001
        else:
            raise NotImplementedError(filter1)

        spec_size = int(bw // wr)

        lines = self._index_col('LINES')
        samples = self._index_col('LINE_SAMPLES')
        if lines is None or samples is None:
            return spec_size

        return as_int(min(max(lines, samples), spec_size))

    def field_obs_wavelength_polarization_type(self) -> MultFieldRet:
        return self._create_mult('NONE')

    ###########################################
    ### OVERRIDE FROM ObsVolumeHubbleCommon ###
    ###########################################

    def field_obs_mission_hubble_filter_type(self) -> MultFieldRet:
        filter1, filter2 = self._decode_filters()

        # WFC3 doesn't do filter stacking
        if filter2 is not None:
            self._log_nonrepeating_error('filter2 not None')
            return self._create_mult(None)

        if filter1.startswith('FR'):
            return self._create_mult('FR')
        if filter1.startswith('G'):
            return self._create_mult('SP')
        if filter1.endswith('N'):
            return self._create_mult('N')
        if filter1.endswith('M'):
            return self._create_mult('M')
        if filter1.endswith('W'):
            return self._create_mult('W')
        if filter1.endswith('LP'):
            return self._create_mult('LP')
        if filter1.endswith('X'):
            return self._create_mult('X')

        self._log_nonrepeating_error(f'Unknown filter "{filter1}"')
        return self._create_mult(None)
