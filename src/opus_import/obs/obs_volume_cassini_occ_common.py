"""What every Cassini ring-occultation volume shares.

An occultation profile is of Saturn's rings by construction and its direction is encoded
in the file name, which is what makes these columns common across the instruments that
recorded one.
"""

from typing import cast

from opus_import.obs.field_types import FloatField, MultFieldRet
from opus_import.obs.obs_cassini_common_pds3 import ObsCassiniCommonPDS3


class ObsVolumeCassiniOccCommon(ObsCassiniCommonPDS3):
    """What every Cassini ring-occultation volume shares.

    Its ``field_obs_*`` methods each fill the schema column their name ends in,
    declaring the type `opus_import.obs.field_types` gives that column.
    """

    def convert_filespec_from_lbl(self, filespec: str) -> str:
        """Convert a ``.LBL`` file specification to the ``.TAB`` data file.

        Parameters:
            filespec: The path, relative to the holdings root.

        Returns:
            The same path with ``.LBL`` replaced by ``.TAB``, which is the file
            this bundle's observations are identified by.
        """
        return filespec.replace('.LBL', '.TAB')


    ################################
    ### OVERRIDE FROM ObsGeneral ###
    ################################

    def _target_name(self) -> list[tuple[str | None, str | None]]:
        """The target of every observation in these volumes.

        Returns:
            Saturn's rings, which is what a ring occultation is of by construction.
        """
        target_name, target_info = self._get_target_info('S RINGS')
        # 'S RINGS' is in TARGET_NAME_INFO, so the lookup cannot fail.
        assert target_info is not None
        return [(target_name, target_info[2])]

    def field_obs_general_planet_id(self) -> MultFieldRet:
        return self._create_mult('SAT')

    def field_obs_general_quantity(self) -> MultFieldRet:
        return self._create_mult('OPDEPTH')

    def field_obs_general_observation_type(self) -> MultFieldRet:
        return self._create_mult('OCC')


    ################################
    ### OVERRIDE FROM ObsProfile ###
    ################################

    def field_obs_profile_occ_dir(self) -> MultFieldRet:
        filespec = self.primary_filespec
        assert filespec is not None

        # We don't allow "Both" as a direction since these are always split into
        # separate files.
        if '_I_' in filespec:
            return self._create_mult('I')
        if '_E_' in filespec:
            return self._create_mult('E')
        self._log_nonrepeating_error(
            f'Unknown ring occultation direction in filespec "{filespec}"')
        return self._create_mult(None)

    def field_obs_profile_body_occ_flag(self) -> MultFieldRet:
        return self._create_mult(self._index_col('PLANETARY_OCCULTATION_FLAG'))

    def field_obs_profile_optical_depth1(self) -> FloatField:
        return cast(FloatField, self._supp_index_col('LOWEST_DETECTABLE_OPACITY'))

    def field_obs_profile_optical_depth2(self) -> FloatField:
        return cast(FloatField, self._supp_index_col('HIGHEST_DETECTABLE_OPACITY'))


    #####################################
    ### OVERRIDE FROM ObsRingGeometry ###
    #####################################

    def field_obs_ring_geometry_ring_radius1(self) -> FloatField:
        return cast(FloatField, self._index_col('MINIMUM_RING_RADIUS'))

    def field_obs_ring_geometry_ring_radius2(self) -> FloatField:
        return cast(FloatField, self._index_col('MAXIMUM_RING_RADIUS'))

    def field_obs_ring_geometry_projected_radial_resolution1(self) -> FloatField:
        return cast(FloatField, self._index_col('RADIAL_RESOLUTION'))

    def field_obs_ring_geometry_projected_radial_resolution2(self) -> FloatField:
        return cast(FloatField, self._index_col('RADIAL_RESOLUTION'))

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
        return cast(FloatField, self._index_col('MINIMUM_RING_LONGITUDE'))

    def field_obs_ring_geometry_ascending_longitude2(self) -> FloatField:
        return cast(FloatField, self._index_col('MAXIMUM_RING_LONGITUDE'))

    def field_obs_ring_geometry_ring_azimuth_wrt_observer1(self) -> FloatField:
        return cast(FloatField, self._index_col('MINIMUM_OBSERVED_RING_AZIMUTH'))

    def field_obs_ring_geometry_ring_azimuth_wrt_observer2(self) -> FloatField:
        return cast(FloatField, self._index_col('MAXIMUM_OBSERVED_RING_AZIMUTH'))

    def field_obs_ring_geometry_phase1(self) -> FloatField:
        return 180.

    def field_obs_ring_geometry_phase2(self) -> FloatField:
        return 180.

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
        return self._time_from_index(column='RING_EVENT_START_TIME')

    def field_obs_ring_geometry_ring_intercept_time2(self) -> FloatField:
        return self._time2_from_index(self.field_obs_ring_geometry_ring_intercept_time1(),
                                      column='RING_EVENT_STOP_TIME')
