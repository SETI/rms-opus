################################################################################
# obs_instrument_hstwfpc2.py
#
# Defines the ObsInstrumentHSTWFPC2 class, which encapsulates fields in the
# common and obs_mission_hubble tables for the HST WFPC2 instrument for
# HSTUx_xxxx. Note HST does not have separate tables for each instrument but
# combines them all together.
################################################################################

from obs_mission_hubble import ObsMissionHubble


class ObsInstrumentHSTWFPC2(ObsMissionHubble):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


    #############################
    ### OVERRIDE FROM ObsBase ###
    #############################

    @property
    def instrument_id(self):
        return 'HSTWFPC2'


    ################################
    ### OVERRIDE FROM ObsGeneral ###
    ################################

    def field_obs_general_observation_type(self):
        return 'IMG'


    ##################################
    ### OVERRIDE FROM ObsTypeImage ###
    ##################################

    def field_obs_type_image_levels(self):
        if not self._is_image():
            return None
        return 4096 # WFPC2 Inst Handbook, Sec 2.8


    ###################################
    ### OVERRIDE FROM ObsWavelength ###
    ###################################

    def field_obs_wavelength_spec_flag(self):
        return 'N'

    def field_obs_wavelength_spec_size(self):
        return None

    def field_obs_wavelength_polarization_type(self):
        filter_name = self._index_col('FILTER_NAME')
        if filter_name.find('POL') == -1:
            return 'NONE'
        return 'LINEAR'


    ######################################
    ### OVERRIDE FROM ObsMissionHubble ###
    ######################################

    def field_obs_mission_hubble_filter_type(self):
        filter1, filter2 = self._decode_filters()

        if filter2 is None:
            filter2 = ''

        if filter1.startswith('FR') or filter2.startswith('FR'):
            return 'FR' # Ramp overrides everything

        if filter1.startswith('FQ') or filter1 == 'F160BN15':
            filter1 = 'N'
        if filter2.startswith('FQ') or filter2 == 'F160BN15':
            filter2 = 'N'

        # Start from narrowest band - paired filters take the type of the smallest
        # bandpass
        if filter1.endswith('N') or filter2.endswith('N'):
            return 'N'
        if filter1.endswith('M') or filter2.endswith('M'):
            return 'M'
        if filter1.endswith('W') or filter2.endswith('W'):
            return 'W'
        if filter1.endswith('LP') or filter2.endswith('LP'):
            return 'LP'

        self._log_nonrepeating_error(f'Unknown filter combination "{filter1}+{filter2}"')
        return None

    def field_obs_mission_hubble_pc1_flag(self):
        return self._index_col('PC1_FLAG')

    def field_obs_mission_hubble_wf2_flag(self):
        return self._index_col('WF2_FLAG')

    def field_obs_mission_hubble_wf3_flag(self):
        return self._index_col('WF3_FLAG')

    def field_obs_mission_hubble_wf4_flag(self):
        return self._index_col('WF4_FLAG')

    def field_obs_mission_hubble_targeted_detector_id(self):
        targeted_detector_id = self._index_col('TARGETED_DETECTOR_ID')
        if targeted_detector_id == '':
            self._log_nonrepeating_error('Empty targeted detector ID')
        return targeted_detector_id
