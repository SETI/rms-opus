"""The ``obs_wavelength`` columns: the observation's spectral coverage and resolution, in
both wavelength and wavenumber.

One module per OPUS table, mixed into every obs class that fills the table. A column
whose value depends on the PDS version or on the instrument is left to a subclass, which
is why most of the methods here can be overridden and a few raise `NotImplementedError`
outright.
"""

from opus_import.obs.field_types import FloatField, IntField, MultFieldRet, StrField
from opus_import.obs.obs_base import ObsBase

# Wavelengths are stored in microns and wavenumbers in cm^-1, so converting between
# them is wavelength = MICRONS_PER_CM / wavenumber, and a resolution converts as
# MICRONS_PER_CM * resolution / wavenumber**2.
MICRONS_PER_CM = 10000.0


class ObsWavelength(ObsBase):
    """The ``obs_wavelength`` columns: the observation's spectral coverage.

    Its ``field_obs_*`` methods each fill the schema column their name ends in,
    declaring the type `opus_import.obs.field_types` gives that column.
    """

    # Helpers for wavelength

    def _wave_res_from_full_bandwidth(self) -> FloatField:
        """Return the spectral resolution of an instrument that has only one band.

        Returns:
            The whole bandwidth in microns, or None if either endpoint is missing. An
            instrument with a single band resolves nothing finer than that band, so its
            resolution and its bandwidth are the same number.
        """
        wl1 = self.field_obs_wavelength_wavelength1()
        wl2 = self.field_obs_wavelength_wavelength2()
        if wl1 is None or wl2 is None:
            return None
        return wl2 - wl1

    def _wave_no_res_from_full_bandwidth(self) -> FloatField:
        """Return the wavenumber resolution of an instrument that has only one band.

        Returns:
            The whole bandwidth in cm^-1, or None if either endpoint is missing. The
            wavenumber counterpart of `_wave_res_from_full_bandwidth`.
        """
        wno1 = self.field_obs_wavelength_wave_no1()
        wno2 = self.field_obs_wavelength_wave_no2()
        if wno1 is None or wno2 is None:
            return None
        return wno2 - wno1

    def _wave_no_res1_from_wave_res(self) -> FloatField:
        """Convert the coarser wavelength resolution into the finer wavenumber one.

        Returns:
            The resolution in cm^-1, or None if the wavelength resolution or the
            wavelength it applies at is missing. The two are reciprocal, so the longer
            wavelength gives the smaller wavenumber resolution.
        """
        wave_res2 = self.field_obs_wavelength_wave_res2()
        wl2 = self.field_obs_wavelength_wavelength2()
        if wave_res2 is None or wl2 is None:
            return None
        return wave_res2 * MICRONS_PER_CM / (wl2 * wl2)

    def _wave_no_res2_from_wave_res(self) -> FloatField:
        """Convert the finer wavelength resolution into the coarser wavenumber one.

        Returns:
            The resolution in cm^-1, or None if the wavelength resolution or the
            wavelength it applies at is missing. The companion of
            `_wave_no_res1_from_wave_res`.
        """
        wave_res1 = self.field_obs_wavelength_wave_res1()
        wl1 = self.field_obs_wavelength_wavelength1()
        if wave_res1 is None or wl1 is None:
            return None
        return wave_res1 * MICRONS_PER_CM / (wl1 * wl1)

    ####################################
    ### FIELD METHODS FOR THIS TABLE ###
    ####################################

    ### Don't override these ###

    def field_obs_wavelength_opus_id(self) -> StrField:
        return self.opus_id

    def field_obs_wavelength_bundle_id(self) -> StrField:
        return self.bundle

    def field_obs_wavelength_instrument_id(self) -> StrField:
        return self.instrument_id

    ################################
    ### ! Might override these ! ###
    ################################

    # Because the obs_wavelength table has an entry for all observations,
    # we provide a default for all fields and don't require subclasses to
    # override the methods.

    def field_obs_wavelength_wavelength1(self) -> FloatField:
        return None

    def field_obs_wavelength_wavelength2(self) -> FloatField:
        return None

    def field_obs_wavelength_wave_res1(self) -> FloatField:
        return None

    def field_obs_wavelength_wave_res2(self) -> FloatField:
        return None

    def field_obs_wavelength_wave_no1(self) -> FloatField:
        wl2 = self.field_obs_wavelength_wavelength2()
        if wl2 is None:
            return None
        return MICRONS_PER_CM / wl2  # cm^-1

    def field_obs_wavelength_wave_no2(self) -> FloatField:
        wl1 = self.field_obs_wavelength_wavelength1()
        if wl1 is None:
            return None
        return MICRONS_PER_CM / wl1  # cm^-1

    def field_obs_wavelength_wave_no_res1(self) -> FloatField:
        return None

    def field_obs_wavelength_wave_no_res2(self) -> FloatField:
        return None

    def field_obs_wavelength_spec_flag(self) -> MultFieldRet:
        return self._create_mult('N')

    def field_obs_wavelength_spec_size(self) -> IntField:
        return None

    def field_obs_wavelength_polarization_type(self) -> MultFieldRet:
        return self._create_mult('NONE')
