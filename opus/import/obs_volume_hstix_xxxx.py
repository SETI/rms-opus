################################################################################
# obs_volume_hstix_xxxx.py
#
# Defines the ObsVolumeHSTIxxxxx class, which encapsulates fields in the
# common and obs_mission_hubble tables for the HST WFC3 instrument for
# HSTIx_xxxx. Note HST does not have separate tables for each instrument but
# combines them all together.
################################################################################

from obs_volume_hubble_common import ObsVolumeHubbleCommon


class ObsVolumeHSTIxxxxx(ObsVolumeHubbleCommon):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


    def _wfc3_spec_flag(self):
        filter1, filter2 = self._decode_filters()
        if filter2 is not None:
            self._log_nonrepeating_error('filter2 not None')
            return None
        return filter1.startswith('G'), filter1, filter2


    #############################
    ### OVERRIDE FROM ObsBase ###
    #############################

    @property
    def instrument_id(self):
        return 'HSTWFC3'


    ################################
    ### OVERRIDE FROM ObsGeneral ###
    ################################

    def _observation_type(self):
        if self._wfc3_spec_flag()[0]:
            return 'SPI'
        return 'IMG'

    def field_obs_general_observation_type(self):
        return self._create_mult(self._observation_type())


    ##################################
    ### OVERRIDE FROM ObsTypeImage ###
    ##################################

    def field_obs_type_image_levels(self):
        if not self._is_image():
            return None
        return 65536 # WFC3 Inst Handbook, Sec 2.2.3


    ###################################
    ### OVERRIDE FROM ObsWavelength ###
    ###################################

    def field_obs_wavelength_spec_flag(self):
        if self._wfc3_spec_flag()[0]:
            return self._create_mult('Y')
        return self._create_mult('N')

    def field_obs_wavelength_spec_size(self):
        spec_flag, filter1, filter2 = self._wfc3_spec_flag()
        if not spec_flag:
            return None

        # We can't use WAVELENGTH_RESOLUTION because it's too aggressive.
        # Instead we use the Resolving Power (lambda / d-lambda) from WFC3 Inst
        # Handbook Table 8.1

        if filter1 == 'G280':
            wr = 300. / 70 * .001
            bw = (450-190) * .001
        elif filter1 == 'G102':
            wr = 1000. / 210 * .001
            bw = (1150-800) * .001
        elif filter1 == 'G141':
            wr = 1400. / 130 * .001
            bw = (1700-1075) * .001
        else:
            assert False, filter1

        spec_size = bw // wr

        lines = self._index_col('LINES')
        samples = self._index_col('LINE_SAMPLES')
        if lines is None or samples is None:
            return spec_size

        return min(max(lines, samples), spec_size)

    def field_obs_wavelength_polarization_type(self):
        return self._create_mult('NONE')


    ###########################################
    ### OVERRIDE FROM ObsVolumeHubbleCommon ###
    ###########################################

    def field_obs_mission_hubble_filter_type(self):
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
