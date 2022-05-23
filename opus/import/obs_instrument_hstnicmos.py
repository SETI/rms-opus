################################################################################
# obs_instrument_hstnicmos.py
#
# Defines the ObsInstrumentHSTNICMOS class, which encapsulates fields in the
# common and obs_mission_hubble tables for the HST NICMOS instrument for
# HSTNx_xxxx. Note HST does not have separate tables for each instrument but
# combines them all together.
################################################################################

from obs_mission_hubble import ObsMissionHubble


class ObsInstrumentHSTNICMOS(ObsMissionHubble):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


    def _nicmos_spec_flag(self):
        filter1, filter2 = self._decode_filters()
        return filter1.startswith('G'), filter1, filter2


    #############################
    ### OVERRIDE FROM ObsBase ###
    #############################

    @property
    def instrument_id(self):
        return 'HSTNICMOS'


    ################################
    ### OVERRIDE FROM ObsGeneral ###
    ################################

    def _observation_type(self):
        if self._nicmos_spec_flag()[0]:
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
        return 65536 # NICMOS Inst Handbook, Sec 7.2.1


    ###################################
    ### OVERRIDE FROM ObsWavelength ###
    ###################################

    def field_obs_wavelength_spec_flag(self):
        if self._nicmos_spec_flag()[0]:
            return self._create_mult('Y')
        return self._create_mult('N')

    def field_obs_wavelength_spec_size(self):
        spec_flag, filter1, filter2 = self._nicmos_spec_flag()
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
            return samples
        if samples is None:
            return lines
        return max(lines, samples)

    def field_obs_wavelength_polarization_type(self):
        filter_name = self._index_col('FILTER_NAME')
        if filter_name.find('POL') == -1:
            return self._create_mult('NONE')
        return self._create_mult('LINEAR')


    ######################################
    ### OVERRIDE FROM ObsMissionHubble ###
    ######################################

    def field_obs_mission_hubble_filter_type(self):
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
