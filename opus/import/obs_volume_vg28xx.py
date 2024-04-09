################################################################################
# obs_volume_vg28xx.py
#
# Defines the ObsVolumeVG28xx class, the parent for the
# ObsVolumeVG2810VGISS, ObsVolumeVG2801VGPPS, ObsVolumeVG2803VGRSS,
# and ObsVolumeVG2802VGUVS classes, which encapsulate
# fields in the common, obs_mission_voyager, and (sometimes)
# obs_instrument_vgiss tables for the VG_28XX volumes.
################################################################################

import julian

from obs_volume_voyager_common import ObsVolumeVoyagerCommon


_VG_TARGET_TO_MISSION_PHASE_MAPPING = {
    'S RINGS': 'SATURN ENCOUNTER',
    'U RINGS': 'URANUS ENCOUNTER',
    'N RINGS': 'NEPTUNE ENCOUNTER'
}

# Note: threshold values are determined by observing the results from OPUS.
# Voyager location:
# North
# 1980-11-12T05:15:45.520
# South
# 1980-11-13T04:19:30.640
# North
# 1981-08-26T04:18:21.080
# South
# 1985-11-06T17:22:30.040
# North
# 1986-01-24T17:10:13.320
# South
# We don't cache these dates because they're only computed once, and calling
# julian.tai_from_iso directly allows us to do an easy vectorization of a list
# of dates.
THRESHOLD_START_TIME_VG_AT_NORTH = julian.tai_from_iso(
    [
        '1980-11-12T05:15:45.520',
        '1980-11-13T04:19:30.640',
        '1981-08-26T04:16:45.080',
        '1985-11-06T17:22:30.040',
        '1986-01-24T17:10:13.320'
    ]
)

# This class handles everything that the instruments VGISS, VGPPS, VGRSS,
# and VGUVS have in common in the VG_28xx reflection/occultation profile
# volumes.

class ObsVolumeVG28xx(ObsVolumeVoyagerCommon):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


    #############################
    ### OVERRIDE FROM ObsBase ###
    #############################

    @property
    def mission_id(self):
        return 'VG'

    def convert_filespec_from_lbl(self, filespec):
        return filespec.replace('.LBL', '.TAB')


    ############################
    ### OVERRIDE FROM ObsPds ###
    ############################

    def field_obs_pds_product_creation_time(self):
        return self._product_creation_time_from_supp_index()


    ###################################
    ### OVERRIDE FROM ObsWavelength ###
    ###################################

    def field_obs_wavelength_wavelength1(self):
        return self._supp_index_col('MINIMUM_WAVELENGTH')

    def field_obs_wavelength_wavelength2(self):
        return self._supp_index_col('MAXIMUM_WAVELENGTH')

    def field_obs_wavelength_wave_res1(self):
        return self._wave_res_from_full_bandwidth()

    def field_obs_wavelength_wave_res2(self):
        return self.field_obs_wavelength_wave_res1()

    def field_obs_wavelength_wave_no_res1(self):
        return self._wave_no_res_from_full_bandwidth()

    def field_obs_wavelength_wave_no_res2(self):
        return self.field_obs_wavelength_wave_no_res1()


    ################################
    ### OVERRIDE FROM ObsProfile ###
    ################################

    def field_obs_profile_wl_band(self):
        wl_band1 = self._supp_index_col('WAVELENGTH_BAND_1')
        wl_band2 = self._supp_index_col('WAVELENGTH_BAND_2')

        if wl_band2 is not None and wl_band2 != 'N/A':
            if wl_band1 != wl_band2:
                self._log_nonrepeating_error(
                    f'Mismatched WAVELENGTH_BAND_1 "{wl_band1}" and '+
                    f'WAVELENGTH_BAND_2 "{wl_band2}"')
                return self._create_mult(None)
        if '-BAND' in wl_band1:
            wl_band1 = wl_band1[0]
        if 'VISUAL' in wl_band1:
            wl_band1 = 'VI'

        return self._create_mult(wl_band1)

    def field_obs_profile_source(self):
        src_name1 = self._supp_index_col('SIGNAL_SOURCE_NAME_1')
        src_name2 = self._supp_index_col('SIGNAL_SOURCE_NAME_2')

        if src_name2 is not None and src_name1 != src_name2:
            self._log_nonrepeating_error(
                f'Mismatched SIGNAL_SOURCE_NAME_1 "{src_name1}" and '+
                f'SIGNAL_SOURCE_NAME_2 "{src_name2}"')

        if src_name1.upper().startswith('VOYAGER'):
            return self._create_mult(src_name1)
        return self._create_mult(col_val=src_name1, grouping='Stars')


    #####################################
    ### OVERRIDE FROM ObsRingGeometry ###
    #####################################

    def field_obs_ring_geometry_ring_radius1(self):
        return self._supp_index_col('MINIMUM_RING_RADIUS')

    def field_obs_ring_geometry_ring_radius2(self):
        return self._supp_index_col('MAXIMUM_RING_RADIUS')

    def field_obs_ring_geometry_projected_radial_resolution1(self):
        return self._supp_index_col('MINIMUM_RADIAL_RESOLUTION')

    def field_obs_ring_geometry_projected_radial_resolution2(self):
        return self._supp_index_col('MAXIMUM_RADIAL_RESOLUTION')

    def field_obs_ring_geometry_ring_center_phase1(self):
        return self.field_obs_ring_geometry_phase1()

    def field_obs_ring_geometry_ring_center_phase2(self):
        return self.field_obs_ring_geometry_phase2()

    def field_obs_ring_geometry_ring_center_incidence1(self):
        return self.field_obs_ring_geometry_incidence1()

    def field_obs_ring_geometry_ring_center_incidence2(self):
        return self.field_obs_ring_geometry_incidence2()

    def field_obs_ring_geometry_ring_center_emission1(self):
        return self.field_obs_ring_geometry_emission1()

    def field_obs_ring_geometry_ring_center_emission2(self):
        return self.field_obs_ring_geometry_emission2()

    def field_obs_ring_geometry_ring_center_north_based_incidence1(self):
        return self.field_obs_ring_geometry_north_based_incidence1()

    def field_obs_ring_geometry_ring_center_north_based_incidence2(self):
        return self.field_obs_ring_geometry_north_based_incidence2()

    def field_obs_ring_geometry_ring_center_north_based_emission1(self):
        return self.field_obs_ring_geometry_north_based_emission1()

    def field_obs_ring_geometry_ring_center_north_based_emission2(self):
        return self.field_obs_ring_geometry_north_based_emission2()

    def field_obs_ring_geometry_ring_intercept_time1(self):
        return self._time_from_supp_index(column='RING_EVENT_START_TIME')

    def field_obs_ring_geometry_ring_intercept_time2(self):
        return self._time2_from_supp_index(self.field_obs_ring_geometry_ring_intercept_time1(),
                                      column='RING_EVENT_STOP_TIME')


    ############################################
    ### OVERRIDE FROM ObsVolumeVoyagerCommon ###
    ############################################

    def _mission_phase_name(self):
        target_name = self._index_col('TARGET_NAME').upper()
        mission_phase = _VG_TARGET_TO_MISSION_PHASE_MAPPING[target_name]
        return mission_phase

    def field_obs_mission_voyager_mission_phase_name(self):
        return self._create_mult(self._mission_phase_name())
