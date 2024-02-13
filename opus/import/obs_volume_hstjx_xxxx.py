################################################################################
# obs_volume_hstjx_xxxx.py
#
# Defines the ObsVolumeHSTJxxxxx class, which encapsulates fields in the
# common and obs_mission_hubble tables for the HST ACS instrument for
# HSTJx_xxxx. Note HST does not have separate tables for each instrument but
# combines them all together.
################################################################################

from obs_volume_hubble_common import ObsVolumeHubbleCommon


class ObsVolumeHSTJxxxxx(ObsVolumeHubbleCommon):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


    def _acs_spec_flag(self):
        filter1, filter2 = self._decode_filters()
        return (filter1.startswith('G') or filter1.startswith('PR'),
                filter1, filter2)


    #############################
    ### OVERRIDE FROM ObsBase ###
    #############################

    @property
    def instrument_id(self):
        return 'HSTACS'


    ################################
    ### OVERRIDE FROM ObsGeneral ###
    ################################

    def _observation_type(self):
        if self._acs_spec_flag()[0]:
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
        return 65536 # ACS Inst Handbook 25, Sec 3.4.3


    ###################################
    ### OVERRIDE FROM ObsWavelength ###
    ###################################

    def field_obs_wavelength_spec_flag(self):
        if self._acs_spec_flag()[0]:
            return self._create_mult('Y')
        return self._create_mult('N')

    def field_obs_wavelength_spec_size(self):
        spec_flag, filter1, filter2 = self._acs_spec_flag()
        if not spec_flag:
            return None

        # We can't use WAVELENGTH_RESOLUTION because it's too aggressive.
        # Instead we use the Resolving Power (lambda / d-lambda) from ACS Inst
        # Handbook Table 3.5

        if filter1 == 'G800L':
            # G800L's resolving power depends on the channel and order, which we
            # don't know
            self._log_nonrepeating_warning(
                'G800L filter used, but not enough information available to '+
                'compute spec_size')
            wr = 8000. / 140 * .0001
            bw = (10500-5500) * .0001
        elif filter1 == 'PR200L':
            wr = 2500. / 59 * .0001
            bw = (3900-1700) * .0001
        elif filter1 == 'PR110L':
            wr = 1500. / 79 * .0001
            bw = (1800-1150) * .0001
        elif filter1 == 'PR130L':
            wr = 1500. / 96 * .0001
            bw = (1800-1250) * .0001
        else:
            self._log_nonrepeating_error(f'Unknown filter {filter1}')

        spec_size = bw // wr

        lines = self._index_col('LINES')
        samples = self._index_col('LINE_SAMPLES')
        if lines is None or samples is None:
            return spec_size

        return min(max(lines, samples), spec_size)

    def field_obs_wavelength_polarization_type(self):
        filter1, filter2 = self._decode_filters()
        if filter2 is not None and filter2.startswith('POL'):
            return self._create_mult('LINEAR')
        return self._create_mult('NONE')


    ###########################################
    ### OVERRIDE FROM ObsVolumeHubbleCommon ###
    ###########################################

    def field_obs_mission_hubble_filter_type(self):
        filter1, filter2 = self._decode_filters()
        # We only care about filter1 since the second is (almost) always a
        # polarizer
        if filter2 is not None and not filter2.startswith('POL'):
            self._log_nonrepeating_warning(
                f'Filter combination {filter1}+{filter2} does not have a'
                +' polarizer as the second filter - filter_type may be wrong')

        # From ACS Inst handbook Table 3.3
        if filter1 in ('F475W', 'F625W', 'F775W', 'F850LP', 'F435W', 'F555W',
                       'F550M', 'F606W', 'F814W', 'F220W', 'F250W', 'F330W',
                       'CLEAR'):
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

        self._log_nonrepeating_error(
            f'Unknown filter {filter1} while determining filter type')
        return self._create_mult(None)
