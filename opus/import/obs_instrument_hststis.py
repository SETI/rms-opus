################################################################################
# obs_instrument_hststis.py
#
# Defines the ObsInstrumentHSTSTIS class, which encapsulates fields in the
# common and obs_mission_hubble tables for the HST STIS instrument for
# HSTOx_xxxx. Note HST does not have separate tables for each instrument but
# combines them all together.
################################################################################

from obs_mission_hubble import ObsMissionHubble


class ObsInstrumentHSTSTIS(ObsMissionHubble):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


    def _stis_spec_flag(self):
        obs_type = self.field_obs_general_observation_type()['col_val']
        return obs_type == 'SPE'


    #############################
    ### OVERRIDE FROM ObsBase ###
    #############################

    @property
    def instrument_id(self):
        return 'HSTSTIS'


    ################################
    ### OVERRIDE FROM ObsGeneral ###
    ################################

    def field_obs_general_observation_type(self):
        obs_type = self._index_col('OBSERVATION_TYPE')
        if obs_type not in ('IMAGE', 'IMAGING', 'SPECTRUM', 'SPECTROSCOPIC'):
            self._log_nonrepeating_error(f'Unknown HST OBSERVATION_TYPE "{obs_type}"')
            return self._create_mult(None)
        if obs_type.startswith('SPEC'): # SPECTRUM or SPECTROSCOPIC
            return self._create_mult('SPE') # Spectrum (1-D with spectral information)
        return self._create_mult('IMG') # Image


    ##################################
    ### OVERRIDE FROM ObsTypeImage ###
    ##################################

    def field_obs_type_image_levels(self):
        if not self._is_image():
            return None
        return 65536 # STIS Inst Handbook, Sec 7.5.1


    ###################################
    ### OVERRIDE FROM ObsWavelength ###
    ###################################


    def field_obs_wavelength_wave_res1(self):
        wr1 = self._index_col('MAXIMUM_WAVELENGTH_RESOLUTION')
        wr2 = self._index_col('MINIMUM_WAVELENGTH_RESOLUTION')
        # This is necessary because in some cases these are backwards in the table!
        if wr1 > wr2:
            self._log_warning(
                'MAXIMUM_WAVELENGTH_RESOLUTION < MINIMUM_WAVELENGTH_RESOLUTION; '
                +'swapping')
            return wr2
        return wr1

    def field_obs_wavelength_wave_res2(self):
        wr1 = self._index_col('MAXIMUM_WAVELENGTH_RESOLUTION')
        wr2 = self._index_col('MINIMUM_WAVELENGTH_RESOLUTION')
        # This is necessary because in some cases these are backwards in the table!
        if wr1 > wr2:
            return wr1
        return wr2

    def field_obs_wavelength_wave_no_res1(self):
        return self._wave_no_res1_from_wave_res()

    def field_obs_wavelength_wave_no_res2(self):
        return self._wave_no_res2_from_wave_res()

    def field_obs_wavelength_spec_flag(self):
        if self._stis_spec_flag():
            return self._create_mult('Y')
        return self._create_mult('N')

    def field_obs_wavelength_spec_size(self):
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
        return max(lines, samples, x1d_size)

    def field_obs_wavelength_polarization_type(self):
        return self._create_mult('NONE')


    ######################################
    ### OVERRIDE FROM ObsMissionHubble ###
    ######################################

    def field_obs_mission_hubble_filter_type(self):
        filter1, filter2 = self._decode_filters()

        # STIS doesn't do filter stacking
        if filter2 is not None:
            self._log_nonrepeating_error('filter2 not None')
            return self._create_mult(None)

        if filter1 in ('CLEAR', 'CRYSTAL QUARTZ', 'LONG_PASS',
                       'STRONTIUM_FLUORIDE', 'ND_3'):
            return self._create_mult('LP')
        if filter1 == 'LYMAN_ALPHA':
            return self._create_mult('N')

        self._log_nonrepeating_error(f'Unknown filter "{filter1}"')
        return self._create_mult(None)

    def field_obs_mission_hubble_proposed_aperture_type(self):
        aperture = self._index_col('PROPOSED_APERTURE_TYPE').upper()
        return self._create_mult_keep_case(aperture)

    def field_obs_mission_hubble_optical_element(self):
        element = self._index_col('OPTICAL_ELEMENT_NAME').upper()
        return self._create_mult_keep_case(element)
