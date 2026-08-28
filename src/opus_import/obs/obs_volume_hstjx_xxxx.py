"""The obs class for HSTJx_xxxx.

HST ACS observations.
"""

from opus_import.obs.field_types import IntField, MultFieldRet, as_int
from opus_import.obs.obs_type_image import SIXTEEN_BIT_IMAGE_LEVELS
from opus_import.obs.obs_volume_hubble_common import ObsVolumeHubbleCommon


class ObsVolumeHSTJxxxxx(ObsVolumeHubbleCommon):
    """The HST ACS observations of HSTJx_xxxx.

    Its ``field_obs_*`` methods each fill the schema column their name ends in,
    declaring the type `opus_import.obs.field_types` gives that column.
    """

    def _acs_spec_flag(self) -> tuple[bool, str, str | None]:
        """Decide whether this ACS observation is spectroscopic, from its filter.

        Returns:
            Whether the filter is a grism or a prism, followed by the two filter names.
        """
        filter1, filter2 = self._decode_filters()
        return (filter1.startswith('G') or filter1.startswith('PR'), filter1, filter2)

    #############################
    ### OVERRIDE FROM ObsBase ###
    #############################

    @property
    def instrument_id(self) -> str | None:
        """The OPUS instrument id, ``HSTACS``."""
        return 'HSTACS'

    ################################
    ### OVERRIDE FROM ObsGeneral ###
    ################################

    def _observation_type(self) -> str | None:
        """Whether this observation is an image or a spectral image.

        Returns:
            ``'SPI'`` through a grism or prism and ``'IMG'`` otherwise.
        """
        if self._acs_spec_flag()[0]:
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
        return SIXTEEN_BIT_IMAGE_LEVELS  # ACS Inst Handbook 25, Sec 3.4.3

    ###################################
    ### OVERRIDE FROM ObsWavelength ###
    ###################################

    def field_obs_wavelength_spec_flag(self) -> MultFieldRet:
        if self._acs_spec_flag()[0]:
            return self._create_mult('Y')
        return self._create_mult('N')

    def field_obs_wavelength_spec_size(self) -> IntField:
        spec_flag, filter1, _filter2 = self._acs_spec_flag()
        if not spec_flag:
            return None

        # We can't use WAVELENGTH_RESOLUTION because it's too aggressive.
        # Instead we use the Resolving Power (lambda / d-lambda) from ACS Inst
        # Handbook Table 3.5

        if filter1 == 'G800L':
            # G800L's resolving power depends on the channel and order, which we
            # don't know
            self._log_nonrepeating_warning(
                'G800L filter used, but not enough information available to ' + 'compute spec_size'
            )
            wr = 8000.0 / 140 * 0.0001
            bw = (10500 - 5500) * 0.0001
        elif filter1 == 'PR200L':
            wr = 2500.0 / 59 * 0.0001
            bw = (3900 - 1700) * 0.0001
        elif filter1 == 'PR110L':
            wr = 1500.0 / 79 * 0.0001
            bw = (1800 - 1150) * 0.0001
        elif filter1 == 'PR130L':
            wr = 1500.0 / 96 * 0.0001
            bw = (1800 - 1250) * 0.0001
        else:
            self._log_nonrepeating_error(f'Unknown filter {filter1}')
            return None

        spec_size = int(bw // wr)

        lines = self._index_col('LINES')
        samples = self._index_col('LINE_SAMPLES')
        if lines is None or samples is None:
            return spec_size

        return as_int(min(max(lines, samples), spec_size))

    def field_obs_wavelength_polarization_type(self) -> MultFieldRet:
        _filter1, filter2 = self._decode_filters()
        if filter2 is not None and filter2.startswith('POL'):
            return self._create_mult('LINEAR')
        return self._create_mult('NONE')

    ###########################################
    ### OVERRIDE FROM ObsVolumeHubbleCommon ###
    ###########################################

    def field_obs_mission_hubble_filter_type(self) -> MultFieldRet:
        filter1, filter2 = self._decode_filters()
        # We only care about filter1 since the second is (almost) always a
        # polarizer
        if filter2 is not None and not filter2.startswith('POL'):
            self._log_nonrepeating_warning(
                f'Filter combination {filter1}+{filter2} does not have a'
                + ' polarizer as the second filter - filter_type may be wrong'
            )

        # From ACS Inst handbook Table 3.3
        if filter1 in (
            'F475W',
            'F625W',
            'F775W',
            'F850LP',
            'F435W',
            'F555W',
            'F550M',
            'F606W',
            'F814W',
            'F220W',
            'F250W',
            'F330W',
            'CLEAR',
        ):
            return self._create_mult('W')

        if filter1 in ('F658N', 'F502N', 'F660N', 'F344N', 'F892N'):
            return self._create_mult('N')

        if filter1.startswith('FR'):
            return self._create_mult('FR')

        if filter1 in ('G800L', 'PR200L', 'PR110L', 'PR130L'):
            return self._create_mult('SP')

        if filter1 == 'F122M':
            return self._create_mult('M')

        if filter1 in ('F115LP', 'F125LP', 'F140LP', 'F150LP', 'F165LP'):
            return self._create_mult('LP')

        # ACS doesn't have any CH4 filters

        self._log_nonrepeating_error(f'Unknown filter {filter1} while determining filter type')
        return self._create_mult(None)
