################################################################################
# obs_bundle_occ_common.py
#
# Defines the ObsBundleOccCommon class, which encapsulate fields that are common
# to the PDS4 occultation classes.
################################################################################

from typing import cast

from opus_import.obs.field_types import FloatField, MultFieldRet
from opus_import.obs.obs_common_pds4 import ObsCommonPDS4


class ObsBundleOccCommon(ObsCommonPDS4):
    #############################
    ### OVERRIDE FROM ObsBase ###
    #############################

    @property
    def primary_filespec(self) -> str | None:
        return cast(str | None, self._index_col('filepath'))


    ################################
    ### OVERRIDE FROM ObsGeneral ###
    ################################

    def field_obs_general_quantity(self) -> MultFieldRet:
        return self._create_mult('OPDEPTH')

    def field_obs_general_observation_type(self) -> MultFieldRet:
        return self._create_mult('OCC')


    ###################################
    ### OVERRIDE FROM ObsWavelength ###
    ###################################

    def field_obs_wavelength_wavelength1(self) -> FloatField:
        wl = self._index_col('rings:minimum_wavelength')
        if wl is not None:
            wl = wl / 1000.  # nm->microns
        return cast(FloatField, wl)

    def field_obs_wavelength_wavelength2(self) -> FloatField:
        wl = self._index_col('rings:maximum_wavelength')
        if wl is not None:
            wl = wl / 1000.  # nm->microns
        return cast(FloatField, wl)


    #####################################
    ### OVERRIDE FROM ObsRingGeometry ###
    #####################################

    def field_obs_ring_geometry_ring_radius1(self) -> FloatField:
        return cast(FloatField, self._index_col('rings:minimum_ring_radius'))

    def field_obs_ring_geometry_ring_radius2(self) -> FloatField:
        return cast(FloatField, self._index_col('rings:maximum_ring_radius'))

    def field_obs_ring_geometry_j2000_longitude1(self) -> FloatField:
        if (self.field_obs_ring_geometry_ascending_longitude1() == 0 and
            self.field_obs_ring_geometry_ascending_longitude2() == 360):
            return 0
        return self._ascending_to_j2000(
            self.field_obs_ring_geometry_ascending_longitude1())

    def field_obs_ring_geometry_j2000_longitude2(self) -> FloatField:
        if (self.field_obs_ring_geometry_ascending_longitude1() == 0 and
            self.field_obs_ring_geometry_ascending_longitude2() == 360):
            return 360
        return self._ascending_to_j2000(
            self.field_obs_ring_geometry_ascending_longitude2())

    def field_obs_ring_geometry_ascending_longitude1(self) -> FloatField:
        return cast(FloatField, self._index_col('rings:minimum_ring_longitude'))

    def field_obs_ring_geometry_ascending_longitude2(self) -> FloatField:
        return cast(FloatField, self._index_col('rings:maximum_ring_longitude'))

    def field_obs_ring_geometry_ring_azimuth_wrt_observer1(self) -> FloatField:
        return cast(FloatField, self._index_col('rings:minimum_observed_ring_azimuth'))

    def field_obs_ring_geometry_ring_azimuth_wrt_observer2(self) -> FloatField:
        return cast(FloatField, self._index_col('rings:maximum_observed_ring_azimuth'))

    def field_obs_ring_geometry_solar_ring_elevation1(self) -> FloatField:
        inc = self._index_col('rings:light_source_incidence_angle')
        if inc is not None:
            inc = inc - 90.
        return cast(FloatField, inc)

    def field_obs_ring_geometry_solar_ring_elevation2(self) -> FloatField:
        return self.field_obs_ring_geometry_solar_ring_elevation1()

    def field_obs_ring_geometry_observer_ring_elevation1(self) -> FloatField:
        inc = self._index_col('rings:light_source_incidence_angle')
        if inc is not None:
            inc = 90. - inc
        return cast(FloatField, inc)

    def field_obs_ring_geometry_observer_ring_elevation2(self) -> FloatField:
        return self.field_obs_ring_geometry_observer_ring_elevation1()

    def field_obs_ring_geometry_phase1(self) -> FloatField:
        return 180.

    def field_obs_ring_geometry_phase2(self) -> FloatField:
        return 180.

    def field_obs_ring_geometry_incidence1(self) -> FloatField:
        return cast(FloatField, self._index_col('rings:light_source_incidence_angle'))

    def field_obs_ring_geometry_incidence2(self) -> FloatField:
        return self.field_obs_ring_geometry_incidence1()

    def field_obs_ring_geometry_emission1(self) -> FloatField:
        em = self._index_col('rings:light_source_incidence_angle')
        if em is not None:
            em = 180. - em
        return cast(FloatField, em)

    def field_obs_ring_geometry_emission2(self) -> FloatField:
        return self.field_obs_ring_geometry_emission1()

    def field_obs_ring_geometry_ring_center_phase1(self) -> FloatField:
        return self.field_obs_ring_geometry_phase1()

    def field_obs_ring_geometry_ring_center_phase2(self) -> FloatField:
        return self.field_obs_ring_geometry_phase2()

    def field_obs_ring_geometry_ring_center_incidence1(self) -> FloatField:
        return self.field_obs_ring_geometry_incidence1()

    def field_obs_ring_geometry_ring_center_incidence2(self) -> FloatField:
        return self.field_obs_ring_geometry_incidence2()

    def field_obs_ring_geometry_ring_center_emission1(self) -> FloatField:
        return self.field_obs_ring_geometry_emission1()

    def field_obs_ring_geometry_ring_center_emission2(self) -> FloatField:
        return self.field_obs_ring_geometry_emission2()

    def field_obs_ring_geometry_ring_center_north_based_incidence1(self) -> FloatField:
        return self.field_obs_ring_geometry_north_based_incidence1()

    def field_obs_ring_geometry_ring_center_north_based_incidence2(self) -> FloatField:
        return self.field_obs_ring_geometry_north_based_incidence2()

    def field_obs_ring_geometry_ring_center_north_based_emission1(self) -> FloatField:
        return self.field_obs_ring_geometry_north_based_emission1()

    def field_obs_ring_geometry_ring_center_north_based_emission2(self) -> FloatField:
        return self.field_obs_ring_geometry_north_based_emission2()

    def field_obs_ring_geometry_ring_intercept_time1(self) -> FloatField:
        return cast(FloatField, self._index_col('rings:ring_event_start_tdb'))

    def field_obs_ring_geometry_ring_intercept_time2(self) -> FloatField:
        return cast(FloatField, self._index_col('rings:ring_event_stop_tdb'))
