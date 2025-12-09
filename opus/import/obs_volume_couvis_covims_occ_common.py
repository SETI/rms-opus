################################################################################
# obs_volume_couvis_covims_occ_common.py
#
# Defines the ObsVolumeUVISVIMSOccCommon class, which encapsulate fields that
# are common to the ObsVolumeCOUVIS8xxx and ObsVolumeCOVIMS8xxx classes.
################################################################################

from obs_volume_cassini_occ_common import ObsVolumeCassiniOccCommon


class ObsVolumeUVISVIMSOccCommon(ObsVolumeCassiniOccCommon):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


    ################################
    ### OVERRIDE FROM ObsGeneral ###
    ################################

    def field_obs_general_time1(self):
        return self._time_from_supp_index()

    def field_obs_general_time2(self):
        return self._time2_from_supp_index(self.field_obs_general_time1())

    def field_obs_general_right_asc1(self):
        return self._prof_ra_dec_helper('index_row', 'STAR_NAME')[0]

    def field_obs_general_right_asc2(self):
        return self._prof_ra_dec_helper('index_row', 'STAR_NAME')[1]

    def field_obs_general_declination1(self):
        return self._prof_ra_dec_helper('index_row', 'STAR_NAME')[2]

    def field_obs_general_declination2(self):
        return self._prof_ra_dec_helper('index_row', 'STAR_NAME')[3]


    ############################
    ### OVERRIDE FROM ObsPds ###
    ############################

    def field_obs_pds_note(self):
        return 'Data quality ' + self._supp_index_col('DATA_QUALITY_SCORE').lower()


    ################################
    ### OVERRIDE FROM ObsProfile ###
    ################################

    def field_obs_profile_occ_type(self):
        return self._create_mult('STE')

    def field_obs_profile_quality_score(self):
        return self._create_mult(self._supp_index_col('DATA_QUALITY_SCORE'))

    def field_obs_profile_source(self):
        target_name, target_name_info = self._star_name_helper('index_row', 'STAR_NAME')
        if target_name_info is None:
            return self._create_mult(None)
        if target_name.upper().startswith('CASSINI'):
            return self._create_mult(col_val=target_name, disp_name=target_name_info[2])
        return self._create_mult(col_val=target_name, disp_name=target_name_info[2],
                                 grouping='Stars')

    def field_obs_profile_host(self):
        return self._create_mult('cassini')


    #####################################
    ### OVERRIDE FROM ObsRingGeometry ###
    #####################################

    def field_obs_ring_geometry_solar_ring_elevation1(self):
        return -self._index_col('OBSERVED_RING_ELEVATION')

    def field_obs_ring_geometry_solar_ring_elevation2(self):
        return -self._index_col('OBSERVED_RING_ELEVATION')

    def field_obs_ring_geometry_observer_ring_elevation1(self):
        return self._index_col('OBSERVED_RING_ELEVATION')

    def field_obs_ring_geometry_observer_ring_elevation2(self):
        return self._index_col('OBSERVED_RING_ELEVATION')

    def field_obs_ring_geometry_incidence1(self):
        return 90. - abs(self._index_col('OBSERVED_RING_ELEVATION'))

    def field_obs_ring_geometry_incidence2(self):
        return 90. - abs(self._index_col('OBSERVED_RING_ELEVATION'))

    def field_obs_ring_geometry_emission1(self):
        return 90. + abs(self._index_col('OBSERVED_RING_ELEVATION'))

    def field_obs_ring_geometry_emission2(self):
        return 90. + abs(self._index_col('OBSERVED_RING_ELEVATION'))

    def field_obs_ring_geometry_north_based_incidence1(self):
        return 90. + self._index_col('OBSERVED_RING_ELEVATION')

    def field_obs_ring_geometry_north_based_incidence2(self):
        return 90. + self._index_col('OBSERVED_RING_ELEVATION')

    def field_obs_ring_geometry_north_based_emission1(self):
        return 90. - self._index_col('OBSERVED_RING_ELEVATION')

    def field_obs_ring_geometry_north_based_emission2(self):
        return 90. - self._index_col('OBSERVED_RING_ELEVATION')

    def field_obs_ring_geometry_solar_ring_opening_angle1(self):
        return -self._index_col('OBSERVED_RING_ELEVATION')

    def field_obs_ring_geometry_solar_ring_opening_angle2(self):
        return -self._index_col('OBSERVED_RING_ELEVATION')

    def field_obs_ring_geometry_observer_ring_opening_angle1(self):
        return self._index_col('OBSERVED_RING_ELEVATION')

    def field_obs_ring_geometry_observer_ring_opening_angle2(self):
        return self._index_col('OBSERVED_RING_ELEVATION')


    ##########################################
    ### OVERRIDE FROM ObsCassiniCommonPDS3 ###
    ##########################################

    def field_obs_mission_cassini_sequence_id(self):
        return self._supp_index_col('SEQUENCE_ID')
