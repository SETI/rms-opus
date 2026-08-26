"""The obs class for HSTUx_xxxx.

HST WFPC2 observations.
"""

from opus_import.obs.field_types import IntField, MultFieldRet
from opus_import.obs.obs_type_image import TWELVE_BIT_IMAGE_LEVELS
from opus_import.obs.obs_volume_hubble_common import ObsVolumeHubbleCommon


class ObsVolumeHSTUxxxxx(ObsVolumeHubbleCommon):
    #############################
    ### OVERRIDE FROM ObsBase ###
    #############################

    """The HST WFPC2 observations of HSTUx_xxxx.

    Its ``field_obs_*`` methods each fill the schema column their name ends in,
    declaring the type `opus_import.obs.field_types` gives that column.
    """

    @property
    def instrument_id(self) -> str | None:
        """The OPUS instrument id, ``HSTWFPC2``."""
        return 'HSTWFPC2'


    ################################
    ### OVERRIDE FROM ObsGeneral ###
    ################################

    def _observation_type(self) -> str | None:
        """Whether this observation is an image or a spectrum.

        Returns:
            Always ``'IMG'``: WFPC2 has no spectroscopic mode.
        """
        return 'IMG'

    def field_obs_general_observation_type(self) -> MultFieldRet:
        return self._create_mult(self._observation_type())


    ##################################
    ### OVERRIDE FROM ObsTypeImage ###
    ##################################

    def field_obs_type_image_levels(self) -> IntField:
        if not self._is_image():
            return None
        return TWELVE_BIT_IMAGE_LEVELS # WFPC2 Inst Handbook, Sec 2.8


    ###################################
    ### OVERRIDE FROM ObsWavelength ###
    ###################################

    def field_obs_wavelength_spec_flag(self) -> MultFieldRet:
        return self._create_mult('N')

    def field_obs_wavelength_spec_size(self) -> IntField:
        return None

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

        if filter2 is None:
            filter2 = ''

        if filter1.startswith('FR') or filter2.startswith('FR'):
            return self._create_mult('FR') # Ramp overrides everything

        if filter1.startswith('FQ') or filter1 == 'F160BN15':
            filter1 = 'N'
        if filter2.startswith('FQ') or filter2 == 'F160BN15':
            filter2 = 'N'

        # Start from narrowest band - paired filters take the type of the smallest
        # bandpass
        if filter1.endswith('N') or filter2.endswith('N'):
            return self._create_mult('N')
        if filter1.endswith('M') or filter2.endswith('M'):
            return self._create_mult('M')
        if filter1.endswith('W') or filter2.endswith('W'):
            return self._create_mult('W')
        if filter1.endswith('LP') or filter2.endswith('LP'):
            return self._create_mult('LP')

        self._log_nonrepeating_error(f'Unknown filter combination "{filter1}+{filter2}"')
        return self._create_mult(None)

    def field_obs_mission_hubble_pc1_flag(self) -> MultFieldRet:
        return self._create_mult(self._index_col('PC1_FLAG'))

    def field_obs_mission_hubble_wf2_flag(self) -> MultFieldRet:
        return self._create_mult(self._index_col('WF2_FLAG'))

    def field_obs_mission_hubble_wf3_flag(self) -> MultFieldRet:
        return self._create_mult(self._index_col('WF3_FLAG'))

    def field_obs_mission_hubble_wf4_flag(self) -> MultFieldRet:
        return self._create_mult(self._index_col('WF4_FLAG'))

    def field_obs_mission_hubble_targeted_detector_id(self) -> MultFieldRet:
        targeted_detector_id = self._index_col('TARGETED_DETECTOR_ID')
        if targeted_detector_id == '':
            self._log_nonrepeating_error('Empty targeted detector ID')
        return self._create_mult(targeted_detector_id)
