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

    ### Don't override these ###

    def field_obs_wavelength_opus_id(self):
        return self.opus_id

    def field_obs_wavelength_volume_id(self):
        return self.volume

    def field_obs_wavelength_instrument_id(self):
        return self.instrument_id


    ################################
    ### ! Might override these ! ###
    ################################

    # Because the obs_wavelength table has an entry for all observations,
    # we provide a default for all fields and don't require subclasses to
    # override the methods.

    def field_obs_wavelength_wavelength1(self):
        return None

    def field_obs_wavelength_wavelength2(self):
        return None

    def field_obs_wavelength_wave_res1(self):
        return None

    def field_obs_wavelength_wave_res2(self):
        return None

    def field_obs_wavelength_wave_no1(self):
        wl2 = self.field_obs_wavelength_wavelength2()
        if wl2 is None:
            return None
        return 10000 / wl2 # cm^-1

    def field_obs_wavelength_wave_no2(self):
        wl1 = self.field_obs_wavelength_wavelength1()
        if wl1 is None:
            return None
        return 10000 / wl1 # cm^-1

    def field_obs_wavelength_wave_no_res1(self):
        return None

    def field_obs_wavelength_wave_no_res2(self):
        return None

    def field_obs_wavelength_spec_flag(self):
        return 'N'

    def field_obs_wavelength_spec_size(self):
        return None

    def field_obs_wavelength_polarization_type(self):
        return 'NONE'