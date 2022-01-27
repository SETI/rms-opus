################################################################################
# obs_wavelength.py
#
# Defines the ObsWavelength class, which encapsulates fields in the
# obs_wavelength table.
################################################################################

from obs_base import ObsBase


class ObsWavelength(ObsBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


    ####################################
    ### FIELD METHODS FOR THIS TABLE ###
    ####################################

    @property
    def field_obs_wavelength_opus_id(self):
        return self.opus_id

    @property
    def field_obs_wavelength_volume_id(self):
        return self.volume

    @property
    def field_obs_wavelength_instrument_id(self):
        return self.instrument_id


    # Because the obs_wavelength table has an entry for all observations,
    # we provide a default for all fields and don't require subclasses to
    # override the methods.

    @property
    def field_obs_wavelength_wavelength1(self):
        return None

    @property
    def field_obs_wavelength_wavelength2(self):
        return None

    @property
    def field_obs_wavelength_wave_res1(self):
        return None

    @property
    def field_obs_wavelength_wave_res2(self):
        return None

    @property
    def field_obs_wavelength_wave_no1(self):
        return None

    @property
    def field_obs_wavelength_wave_no2(self):
        return None

    @property
    def field_obs_wavelength_wave_no_res1(self):
        return None

    @property
    def field_obs_wavelength_wave_no_res2(self):
        return None

    @property
    def field_obs_wavelength_spec_flag(self):
        return 'N'

    @property
    def field_obs_wavelength_spec_size(self):
        return None

    @property
    def field_obs_wavelength_polarization_type(self):
        return 'NONE'
