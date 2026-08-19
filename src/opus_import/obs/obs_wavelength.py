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

    # Helpers for wavelength

    def _wave_res_from_full_bandwidth(self):
        wl1 = self.field_obs_wavelength_wavelength1()
        wl2 = self.field_obs_wavelength_wavelength2()
        if wl1 is None or wl2 is None:
            return None
        return wl2 - wl1

    def _wave_no_res_from_full_bandwidth(self):
        wno1 = self.field_obs_wavelength_wave_no1()
        wno2 = self.field_obs_wavelength_wave_no2()
        if wno1 is None or wno2 is None:
            return None
        return wno2 - wno1

    def _wave_no_res1_from_wave_res(self):
        wave_res2 = self.field_obs_wavelength_wave_res2()
        wl2 = self.field_obs_wavelength_wavelength2()
        if wave_res2 is None or wl2 is None:
            return None
        return wave_res2 * 10000. / (wl2*wl2)

    def _wave_no_res2_from_wave_res(self):
        wave_res1 = self.field_obs_wavelength_wave_res1()
        wl1 = self.field_obs_wavelength_wavelength1()
        if wave_res1 is None or wl1 is None:
            return None
        return wave_res1 * 10000. / (wl1*wl1)


    ####################################
    ### FIELD METHODS FOR THIS TABLE ###
    ####################################

    ### Don't override these ###

    def field_obs_wavelength_opus_id(self):
        return self.opus_id

    def field_obs_wavelength_bundle_id(self):
        return self.bundle

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
        return self._create_mult('N')

    def field_obs_wavelength_spec_size(self):
        return None

    def field_obs_wavelength_polarization_type(self):
        return self._create_mult('NONE')
