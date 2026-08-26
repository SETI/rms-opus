"""What the UVIS and VIMS ring-occultation volumes share.

Both record a stellar occultation of Saturn's rings, and both name the star the same
way, so the star and the profile columns are computed once here.
"""

from typing import cast

from opus_import.obs.field_types import FloatField, MultFieldRet, StrField
from opus_import.obs.obs_volume_cassini_occ_common import ObsVolumeCassiniOccCommon


class ObsVolumeUVISVIMSOccCommon(ObsVolumeCassiniOccCommon):
    """What the UVIS and VIMS ring-occultation volumes share.

    Its ``field_obs_*`` methods each fill the schema column their name ends in,
    declaring the type `opus_import.obs.field_types` gives that column.
    """

    ################################
    ### OVERRIDE FROM ObsGeneral ###
    ################################


    def field_obs_general_time1(self) -> FloatField:
        return self._time_from_supp_index()

    def field_obs_general_time2(self) -> FloatField:
        return self._time2_from_supp_index(self.field_obs_general_time1())

    def field_obs_general_right_asc1(self) -> FloatField:
        return self._prof_ra_dec_helper('index_row', 'STAR_NAME')[0]

    def field_obs_general_right_asc2(self) -> FloatField:
        return self._prof_ra_dec_helper('index_row', 'STAR_NAME')[1]

    def field_obs_general_declination1(self) -> FloatField:
        return self._prof_ra_dec_helper('index_row', 'STAR_NAME')[2]

    def field_obs_general_declination2(self) -> FloatField:
        return self._prof_ra_dec_helper('index_row', 'STAR_NAME')[3]


    ############################
    ### OVERRIDE FROM ObsPds ###
    ############################

    def field_obs_pds_note(self) -> StrField:
        return cast(StrField,
                    'Data quality ' + self._supp_index_col('DATA_QUALITY_SCORE').lower())


    ################################
    ### OVERRIDE FROM ObsProfile ###
    ################################

    def field_obs_profile_occ_type(self) -> MultFieldRet:
        return self._create_mult('STE')

    def field_obs_profile_quality_score(self) -> MultFieldRet:
        return self._create_mult(self._supp_index_col('DATA_QUALITY_SCORE'))

    def field_obs_profile_source(self) -> MultFieldRet:
        target_name, target_name_info = self._star_name_helper('index_row', 'STAR_NAME')
        if target_name_info is None:
            return self._create_mult(None)
        assert target_name is not None
        if target_name.upper().startswith('CASSINI'):
            return self._create_mult(col_val=target_name, disp_name=target_name_info[2])
        return self._create_mult(col_val=target_name, disp_name=target_name_info[2],
                                 grouping='Stars')

    def field_obs_profile_host(self) -> MultFieldRet:
        return self._create_mult('cassini')


    #####################################
    ### OVERRIDE FROM ObsRingGeometry ###
    #####################################

    def field_obs_ring_geometry_solar_ring_elevation1(self) -> FloatField:
        return cast(FloatField, -self._index_col('OBSERVED_RING_ELEVATION'))

    def field_obs_ring_geometry_solar_ring_elevation2(self) -> FloatField:
        return cast(FloatField, -self._index_col('OBSERVED_RING_ELEVATION'))

    def field_obs_ring_geometry_observer_ring_elevation1(self) -> FloatField:
        return cast(FloatField, self._index_col('OBSERVED_RING_ELEVATION'))

    def field_obs_ring_geometry_observer_ring_elevation2(self) -> FloatField:
        return cast(FloatField, self._index_col('OBSERVED_RING_ELEVATION'))

    def field_obs_ring_geometry_incidence1(self) -> FloatField:
        return cast(FloatField, 90. - abs(self._index_col('OBSERVED_RING_ELEVATION')))

    def field_obs_ring_geometry_incidence2(self) -> FloatField:
        return cast(FloatField, 90. - abs(self._index_col('OBSERVED_RING_ELEVATION')))

    def field_obs_ring_geometry_emission1(self) -> FloatField:
        return cast(FloatField, 90. + abs(self._index_col('OBSERVED_RING_ELEVATION')))

    def field_obs_ring_geometry_emission2(self) -> FloatField:
        return cast(FloatField, 90. + abs(self._index_col('OBSERVED_RING_ELEVATION')))

    def field_obs_ring_geometry_north_based_incidence1(self) -> FloatField:
        return cast(FloatField, 90. + self._index_col('OBSERVED_RING_ELEVATION'))

    def field_obs_ring_geometry_north_based_incidence2(self) -> FloatField:
        return cast(FloatField, 90. + self._index_col('OBSERVED_RING_ELEVATION'))

    def field_obs_ring_geometry_north_based_emission1(self) -> FloatField:
        return cast(FloatField, 90. - self._index_col('OBSERVED_RING_ELEVATION'))

    def field_obs_ring_geometry_north_based_emission2(self) -> FloatField:
        return cast(FloatField, 90. - self._index_col('OBSERVED_RING_ELEVATION'))

    def field_obs_ring_geometry_solar_ring_opening_angle1(self) -> FloatField:
        return cast(FloatField, -self._index_col('OBSERVED_RING_ELEVATION'))

    def field_obs_ring_geometry_solar_ring_opening_angle2(self) -> FloatField:
        return cast(FloatField, -self._index_col('OBSERVED_RING_ELEVATION'))

    def field_obs_ring_geometry_observer_ring_opening_angle1(self) -> FloatField:
        return cast(FloatField, self._index_col('OBSERVED_RING_ELEVATION'))

    def field_obs_ring_geometry_observer_ring_opening_angle2(self) -> FloatField:
        return cast(FloatField, self._index_col('OBSERVED_RING_ELEVATION'))


    ##########################################
    ### OVERRIDE FROM ObsCassiniCommonPDS3 ###
    ##########################################

    def field_obs_mission_cassini_sequence_id(self) -> StrField:
        return cast(StrField, self._supp_index_col('SEQUENCE_ID'))
