"""The obs class for HSTOx_xxxx.

HST STIS observations.
"""

from typing import cast

from opus_import.obs.field_types import FloatField, IntField, MultFieldRet, as_int
from opus_import.obs.obs_type_image import SIXTEEN_BIT_IMAGE_LEVELS
from opus_import.obs.obs_volume_hubble_common import ObsVolumeHubbleCommon


class ObsVolumeHSTOxxxxx(ObsVolumeHubbleCommon):
    """The HST STIS observations of HSTOx_xxxx.

    Its ``field_obs_*`` methods each fill the schema column their name ends in,
    declaring the type `opus_import.obs.field_types` gives that column.
    """

    def _stis_spec_flag(self) -> bool:
        """Whether this STIS observation is a spectrum rather than an image."""
        return self._observation_type() == 'SPE'

    #############################
    ### OVERRIDE FROM ObsBase ###
    #############################

    @property
    def instrument_id(self) -> str | None:
        """The OPUS instrument id, ``HSTSTIS``."""
        return 'HSTSTIS'

    ################################
    ### OVERRIDE FROM ObsGeneral ###
    ################################

    def _observation_type(self) -> str | None:
        """Whether this observation is an image or a spectrum.

        Unlike the other HST instruments STIS records the distinction directly, so it is
        read rather than derived from the filter.

        Returns:
            ``'SPE'`` or ``'IMG'``, or None for a value this pipeline does not describe,
            which is logged as an error.
        """
        obs_type = self._index_col('OBSERVATION_TYPE')
        if obs_type not in ('IMAGE', 'IMAGING', 'SPECTRUM', 'SPECTROSCOPIC'):
            self._log_nonrepeating_error(f'Unknown HST OBSERVATION_TYPE "{obs_type}"')
            return None
        if obs_type.startswith('SPEC'):  # SPECTRUM or SPECTROSCOPIC
            return 'SPE'  # Spectrum (1-D with spectral information)
        return 'IMG'  # Image

    def field_obs_general_observation_type(self) -> MultFieldRet:
        return self._create_mult(self._observation_type())

    ##################################
    ### OVERRIDE FROM ObsTypeImage ###
    ##################################

    def field_obs_type_image_levels(self) -> IntField:
        if not self._is_image():
            return None
        return SIXTEEN_BIT_IMAGE_LEVELS  # STIS Inst Handbook, Sec 7.5.1

    ###################################
    ### OVERRIDE FROM ObsWavelength ###
    ###################################

    def field_obs_wavelength_wave_res1(self) -> FloatField:
        wr1 = self._index_col('MAXIMUM_WAVELENGTH_RESOLUTION')
        wr2 = self._index_col('MINIMUM_WAVELENGTH_RESOLUTION')
        # This is necessary because in some cases these are backwards in the table!
        if wr1 is not None and wr2 is not None and wr1 > wr2:
            self._log_warning(
                'MAXIMUM_WAVELENGTH_RESOLUTION < MINIMUM_WAVELENGTH_RESOLUTION; ' + 'swapping'
            )
            return cast(FloatField, wr2)
        return cast(FloatField, wr1)

    def field_obs_wavelength_wave_res2(self) -> FloatField:
        wr1 = self._index_col('MAXIMUM_WAVELENGTH_RESOLUTION')
        wr2 = self._index_col('MINIMUM_WAVELENGTH_RESOLUTION')
        # This is necessary because in some cases these are backwards in the table!
        if wr1 is not None and wr2 is not None and wr1 > wr2:
            return cast(FloatField, wr1)
        return cast(FloatField, wr2)

    def field_obs_wavelength_wave_no_res1(self) -> FloatField:
        return self._wave_no_res1_from_wave_res()

    def field_obs_wavelength_wave_no_res2(self) -> FloatField:
        return self._wave_no_res2_from_wave_res()

    def field_obs_wavelength_spec_flag(self) -> MultFieldRet:
        if self._stis_spec_flag():
            return self._create_mult('Y')
        return self._create_mult('N')

    def field_obs_wavelength_spec_size(self) -> IntField:
        if not self._stis_spec_flag():
            return None
        lines = self._index_col('LINES')
        samples = self._index_col('LINE_SAMPLES')
        x1d_size = self._index_col('X1D_SPECTRUM_SIZE')
        if lines is None:
            lines = 0
        if samples is None:
            samples = 0
        if x1d_size is None:
            x1d_size = 0
        return as_int(max(lines, samples, x1d_size))

    def field_obs_wavelength_polarization_type(self) -> MultFieldRet:
        return self._create_mult('NONE')

    ###########################################
    ### OVERRIDE FROM ObsVolumeHubbleCommon ###
    ###########################################

    def field_obs_mission_hubble_filter_type(self) -> MultFieldRet:
        filter1, filter2 = self._decode_filters()

        # STIS doesn't do filter stacking
        if filter2 is not None:
            self._log_nonrepeating_error('filter2 not None')
            return self._create_mult(None)

        if filter1 in ('CLEAR', 'CRYSTAL QUARTZ', 'LONG_PASS', 'STRONTIUM_FLUORIDE', 'ND_3'):
            return self._create_mult('LP')
        if filter1 == 'LYMAN_ALPHA':
            return self._create_mult('N')

        self._log_nonrepeating_error(f'Unknown filter "{filter1}"')
        return self._create_mult(None)

    def field_obs_mission_hubble_proposed_aperture_type(self) -> MultFieldRet:
        aperture = self._index_col('PROPOSED_APERTURE_TYPE').upper()
        return self._create_mult_keep_case(aperture)

    def field_obs_mission_hubble_optical_element(self) -> MultFieldRet:
        element = self._index_col('OPTICAL_ELEMENT_NAME').upper()
        return self._create_mult_keep_case(element)
