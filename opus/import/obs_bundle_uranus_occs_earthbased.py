################################################################################
# obs_bundle_uranus_occs_earthbased.py
#
# Defines the ObsBundleUranusOccsEarthbased class, which encapsulates fields in
# the common tables for the PDS4 bundle "uranus_occs_earthbase". This class
# supports multiple instruments in a single volume.
################################################################################

"""
PDS4TODO Temporary comment

To create the index files:

for i in `(cd /data/pds4-holdings/bundles/uranus_occs_earthbased; ls -d *_u[0-9]*)`
do
echo Processing $i
mkdir -p /data/pds4-holdings/metadata/uranus_occs_earthbased/$i
python pds4_create_xml_index.py /data/pds4-holdings/bundles/uranus_occs_earthbased "${i}/data/rings/*_*00m.xml" --extra-file-info filename filepath --sort-by filepath --output-file /data/pds4-holdings/metadata/uranus_occs_earthbased/${i}/${i}_rings_index.csv
python pds4_create_xml_index.py /data/pds4-holdings/bundles/uranus_occs_earthbased "${i}/data/global/*_*00m.xml" --extra-file-info filename filepath --sort-by filepath --output-file /data/pds4-holdings/metadata/uranus_occs_earthbased/${i}/${i}_global_index.csv
python pds4_create_xml_index.py /data/pds4-holdings/bundles/uranus_occs_earthbased "${i}/data/atmosphere/*_atmos_*.xml" --extra-file-info filename filepath --sort-by filepath --output-file /data/pds4-holdings/metadata/uranus_occs_earthbased/${i}/${i}_atmosphere_index.csv
done
"""

import config_targets

from obs_common_pds4 import ObsCommonPDS4


# TODOPDS4 We should be able to get rid of this mapping once
# Observing_System_Component is available in the index file.
_LID_TO_INST = {
    'caha_123cm': 'caha-calar_alto.1m23',
    'ctio_150cm': 'ctio-cerro_tololo.smarts_1m50',
    'ctio_400cm': 'ctio-cerro_tololo.victorblanco_4m0',
    'eso_104cm': 'eso-la_silla.1m04',
    'eso_220cm': 'eso-la_silla.2m2',
    'eso_360cm': 'eso-la_silla.3m6',
    'hst_fos': 'hst.fos',
    'irtf_320cm': 'irtf-maunakea.3m2',
    'kao_91cm': 'kuiper-airborne.0m91',
    'lco_100cm': 'las_campanas.swope_1m0',
    'lco_250cm': 'las_campanas.ireneedupont_2m5',
    'lowell_180cm': 'lowell.perkins_warner1m83',
    'maunakea_380cm': 'maunakea.ukirt_3m8',
    'mcdonald_270cm': 'mcdonald.harlanjsmith_2m7',
    'mso_190cm': 'mount_stromlo.1m9',
    'opmt_106cm': 'pic_du_midi.1m06',
    'opmt_200cm': 'pic_du_midi.bernardlyot_2m0',
    'palomar_508cm': 'palomar.hale_5m08',
    'saao_188cm': 'saao.radcliffe_1m88',
    'sso_230cm': 'siding_spring.anu_2m3',
    'sso_390cm': 'siding_spring.aat_3m9',
    'teide_155cm': 'teide.carlossanchez_1m55',
}


class ObsBundleUranusOccsEarthbased(ObsCommonPDS4):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


    def _is_atmos(self):
        lid = self._index_col('pds:logical_identifier')
        return 'atmos' in lid

    def _inst_name(self):
        if self._metadata is None:
            # This happens during the create_tables phase
            return None
        # LID format:
        # urn:nasa:pds:uranus_occ_u13_sso_390cm:data:2200nm_counts-v-time_atmos_ingress
        # urn:nasa:pds:uranus_occ_u137_hst_fos:data:540nm_radius_alpha_egress_100m
        lid = self._index_col('pds:logical_identifier')
        lid = lid.split(':')
        main_lid = lid[3]
        _, _, star, inst1, inst2 = main_lid.split('_')
        return _LID_TO_INST[f'{inst1}_{inst2}']

    def _star_id(self):
        star_name = self._index_col('rings:star_name')
        return star_name.upper().replace(' ', '_')

    def _prof_ra_dec_helper(self):
        star_id = self._star_id()
        return (config_targets.STAR_RA_DEC[star_id][0]-self._STAR_RA_DEC_SLOP,
                config_targets.STAR_RA_DEC[star_id][0]+self._STAR_RA_DEC_SLOP,
                config_targets.STAR_RA_DEC[star_id][1]-self._STAR_RA_DEC_SLOP,
                config_targets.STAR_RA_DEC[star_id][1]+self._STAR_RA_DEC_SLOP)


    #############################
    ### OVERRIDE FROM ObsBase ###
    #############################

    @property
    def instrument_id(self):
        return self._inst_name()

    @property
    def inst_host_id(self):
        return 'HST' if self._inst_name == 'hst_fos' else 'GB'

    @property
    def mission_id(self):
        return 'HST' if self._inst_name == 'hst_fos' else 'GB'

    @property
    def primary_filespec(self):
        return self._index_col('filepath')


    ################################
    ### OVERRIDE FROM ObsGeneral ###
    ################################

    def field_obs_general_right_asc1(self):
        return self._prof_ra_dec_helper()[0]

    def field_obs_general_right_asc2(self):
        return self._prof_ra_dec_helper()[1]

    def field_obs_general_declination1(self):
        return self._prof_ra_dec_helper()[2]

    def field_obs_general_declination2(self):
        return self._prof_ra_dec_helper()[3]

    def field_obs_general_planet_id(self):
        return self._create_mult('URA')

    def _target_name(self):
        target_name = 'URANUS' if self._is_atmos() else 'U RINGS'
        target_name, target_info = self._get_target_info(target_name)
        if target_info is None:
            return None, None
        return [(target_name, target_info[2])]

    def field_obs_general_quantity(self):
        return self._create_mult('OPDEPTH')

    def field_obs_general_observation_type(self):
        return self._create_mult('OCC')


    ###################################
    ### OVERRIDE FROM ObsWavelength ###
    ###################################

    def field_obs_wavelength_wavelength1(self):
        return self._index_col('rings:minimum_wavelength') / 1000. # nm->microns

    def field_obs_wavelength_wavelength2(self):
        return self._index_col('rings:maximum_wavelength') / 1000. # nm->microns


    ################################
    ### OVERRIDE FROM ObsProfile ###
    ################################

    def field_obs_profile_source(self):
        star_name = self._index_col('rings:star_name')
        star_name_id = star_name.upper().replace(' ', '_')
        return self._create_mult(star_name_id, disp_name=star_name,
                                 grouping='Stars')

    def field_obs_profile_host(self):
        return self._create_mult(self._inst_name())


    #####################################
    ### OVERRIDE FROM ObsRingGeometry ###
    #####################################

    # Note - A lot of the ring-specific fields are missing from atmos labels so
    # they will just turn out to be None.

    def field_obs_ring_geometry_ring_radius1(self):
        return self._index_col('rings:minimum_ring_radius')

    def field_obs_ring_geometry_ring_radius2(self):
        return self._index_col('rings:maximum_ring_radius')

    def field_obs_ring_geometry_projected_radial_resolution1(self):
        return self._index_col('rings:radial_resolution')

    def field_obs_ring_geometry_projected_radial_resolution2(self):
        return self.field_obs_ring_geometry_projected_radial_resolution1()

    def field_obs_ring_geometry_j2000_longitude1(self):
        if (self.field_obs_ring_geometry_ascending_longitude1() == 0 and
            self.field_obs_ring_geometry_ascending_longitude2() == 360):
            return 0
        return self._ascending_to_j2000(
            self.field_obs_ring_geometry_ascending_longitude1())

    def field_obs_ring_geometry_j2000_longitude2(self):
        if (self.field_obs_ring_geometry_ascending_longitude1() == 0 and
            self.field_obs_ring_geometry_ascending_longitude2() == 360):
            return 360
        return self._ascending_to_j2000(
            self.field_obs_ring_geometry_ascending_longitude2())

    def field_obs_ring_geometry_ascending_longitude1(self):
        return self._index_col('rings:minimum_ring_longitude')

    def field_obs_ring_geometry_ascending_longitude2(self):
        return self._index_col('rings:maximum_ring_longitude')

    def field_obs_ring_geometry_ring_azimuth_wrt_observer1(self):
        return self._index_col('rings:minimum_ring_azimuth')

    def field_obs_ring_geometry_ring_azimuth_wrt_observer2(self):
        return self._index_col('rings:maximum_ring_azimuth')

    # Earth was seeing Uranus' south pole for the entire duration of this data set.
    # Thus the solar elevation was seeing the northern hemisphere and the
    # observer elevation was seeing the southern hemisphere.
    # For Uranus, these values are positive for the southern hemisphere.

    def field_obs_ring_geometry_solar_ring_elevation1(self):
        inc = self._index_col('rings:light_source_incidence_angle')
        if inc is not None:
            inc = inc - 90.
        return inc

    def field_obs_ring_geometry_solar_ring_elevation2(self):
        return self.field_obs_ring_geometry_solar_ring_elevation1()

    def field_obs_ring_geometry_observer_ring_elevation1(self):
        inc = self._index_col('rings:light_source_incidence_angle')
        if inc is not None:
            inc = 90. - inc
        return inc

    def field_obs_ring_geometry_observer_ring_elevation2(self):
        return self.field_obs_ring_geometry_observer_ring_elevation1()

    def field_obs_ring_geometry_phase1(self):
        return 180.

    def field_obs_ring_geometry_phase2(self):
        return 180.

    def field_obs_ring_geometry_incidence1(self):
        return self._index_col('rings:light_source_incidence_angle')

    def field_obs_ring_geometry_incidence2(self):
        return self.field_obs_ring_geometry_incidence1()

    def field_obs_ring_geometry_emission1(self):
        em = self._index_col('rings:light_source_incidence_angle')
        if em is not None:
            em = 180. - em
        return em

    def field_obs_ring_geometry_emission2(self):
        return self.field_obs_ring_geometry_emission1()

    # Earth was seeing Uranus' south pole for the entire duration of this data set.
    # Thus the star was illuminating the north side of the rings, and the
    # north-based values are the same as the plain values.

    def field_obs_ring_geometry_north_based_incidence1(self):
        return self.field_obs_ring_geometry_incidence1()

    def field_obs_ring_geometry_north_based_incidence2(self):
        return self.field_obs_ring_geometry_incidence2()

    def field_obs_ring_geometry_north_based_emission1(self):
        return self.field_obs_ring_geometry_emission1()

    def field_obs_ring_geometry_north_based_emission2(self):
        return self.field_obs_ring_geometry_emission2()

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

    def field_obs_ring_geometry_solar_ring_opening_angle1(self):
        oa = self._index_col('rings:observed_ring_elevation')
        if oa is not None:
            oa = -oa
        return oa

    def field_obs_ring_geometry_solar_ring_opening_angle2(self):
        return self.field_obs_ring_geometry_solar_ring_opening_angle1()

    def field_obs_ring_geometry_observer_ring_opening_angle1(self):
        return self._index_col('rings:observed_ring_elevation')

    def field_obs_ring_geometry_observer_ring_opening_angle2(self):
        return self.field_obs_ring_geometry_observer_ring_opening_angle1()

    def field_obs_ring_geometry_ring_intercept_time1(self):
        return self._index_col('rings:ring_event_start_tdb')

    def field_obs_ring_geometry_ring_intercept_time2(self):
        return self._index_col('rings:ring_event_stop_tdb')
