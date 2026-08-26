################################################################################
# obs_bundle_uranus_occs_earthbased.py
#
# Defines the ObsBundleUranusOccsEarthbased class, which encapsulates fields in
# the common and common occultation tables for the PDS4 bundleset
# "uranus_occs_earthbased". This class supports multiple instruments in a single
# bundleset.
################################################################################

r"""
PDS4TODO Temporary comment

To create the index files:

for i in `(cd /mnt/rms-holdings/pds4-holdings/bundles/uranus_occs_earthbased; ls -d *_u[0-9]*)`
do
echo Processing $i
mkdir -p /data/new-pds4-holdings/metadata/uranus_occs_earthbased/$i
python pds4_create_xml_index.py \
    /mnt/rms-holdings/pds4-holdings/bundles/uranus_occs_earthbased \
    "${i}/data/rings/*_*00m.xml" \
    --extra-file-info filename filepath --sort-by filepath --output-file \
    /data/new-pds4-holdings/metadata/uranus_occs_earthbased/${i}/${i}_rings_index.csv
python pds4_create_xml_index.py \
    /mnt/rms-holdings/pds4-holdings/bundles/uranus_occs_earthbased \
    "${i}/data/global/*_*00m.xml" \
    --extra-file-info filename filepath --sort-by filepath --output-file \
    /data/new-pds4-holdings/metadata/uranus_occs_earthbased/${i}/${i}_global_index.csv
python pds4_create_xml_index.py \
    /mnt/rms-holdings/pds4-holdings/bundles/uranus_occs_earthbased \
    "${i}/data/atmosphere/*_atmos_*.xml" \
    --extra-file-info filename filepath --sort-by filepath --output-file \
    /data/new-pds4-holdings/metadata/uranus_occs_earthbased/${i}/${i}_atmosphere_index.csv
done
"""

from typing import cast

from opus_import import config_targets
from opus_import.obs.field_types import FloatField, MultFieldRet
from opus_import.obs.obs_bundle_occ_common import ObsBundleOccCommon

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

class ObsBundleUranusOccsEarthbased(ObsBundleOccCommon):
    def _is_atmos(self) -> bool:
        lid = self._index_col('pds:logical_identifier')
        return 'atmos' in lid

    def _inst_name(self) -> str | None:
        if self._metadata is None:
            # This happens during the create_tables phase
            return None
        # LID format:
        # urn:nasa:pds:uranus_occ_u13_sso_390cm:data:2200nm_counts-v-time_atmos_ingress
        # urn:nasa:pds:uranus_occ_u137_hst_fos:data:540nm_radius_alpha_egress_100m
        lid = self._index_col('pds:logical_identifier')
        lid = lid.split(':')
        main_lid = lid[3]
        _, _, _star, inst1, inst2 = main_lid.split('_')
        return _LID_TO_INST[f'{inst1}_{inst2}']

    def _star_id(self) -> str:
        star_name = self._index_col('rings:star_name')
        return cast(str, star_name.upper().replace(' ', '_'))

    def _star_ra_dec_range(self) -> tuple[float, float, float, float]:
        star_id = self._star_id()
        return (config_targets.STAR_RA_DEC[star_id][0]-self._STAR_RA_DEC_SLOP,
                config_targets.STAR_RA_DEC[star_id][0]+self._STAR_RA_DEC_SLOP,
                config_targets.STAR_RA_DEC[star_id][1]-self._STAR_RA_DEC_SLOP,
                config_targets.STAR_RA_DEC[star_id][1]+self._STAR_RA_DEC_SLOP)


    #############################
    ### OVERRIDE FROM ObsBase ###
    #############################

    @property
    def instrument_id(self) -> str | None:
        return self._inst_name()


    @property
    def inst_host_id(self) -> str:
        return 'HST' if self._inst_name() == 'hst.fos' else 'GB'

    @property
    def mission_id(self) -> str:
        return 'HST' if self._inst_name() == 'hst.fos' else 'GB'

    ################################
    ### OVERRIDE FROM ObsGeneral ###
    ################################

    def field_obs_general_right_asc1(self) -> FloatField:
        return self._star_ra_dec_range()[0]

    def field_obs_general_right_asc2(self) -> FloatField:
        return self._star_ra_dec_range()[1]

    def field_obs_general_declination1(self) -> FloatField:
        return self._star_ra_dec_range()[2]

    def field_obs_general_declination2(self) -> FloatField:
        return self._star_ra_dec_range()[3]

    def field_obs_general_planet_id(self) -> MultFieldRet:
        return self._create_mult('URA')

    def _target_name(self) -> list[tuple[str | None, str | None]]:
        lookup_name = 'URANUS' if self._is_atmos() else 'U RINGS'
        target_name, target_info = self._get_target_info(lookup_name)
        if target_info is None:
            return [(None, None)]
        return [(target_name, target_info[2])]


    ################################
    ### OVERRIDE FROM ObsProfile ###
    ################################

    def field_obs_profile_occ_type(self) -> MultFieldRet:
        occ_type = self._index_col('rings:occultation_type')
        if occ_type == 'stellar':
            return self._create_mult('STE')
        self._log_nonrepeating_error(
            f'Unknown rings:occultation:type "{occ_type}"')
        return self._create_mult(None)

    def field_obs_profile_occ_dir(self) -> MultFieldRet:
        occ_dir = self._index_col('rings:ring_profile_direction')
        if occ_dir is None:
            occ_dir = self._index_col('rings:time_series_direction')
        if occ_dir is None:
            self._log_nonrepeating_error(
                'rings:ring_profile_direction and rings:time_series_direction missing')
            return self._create_mult(None)
        occ_dir = occ_dir.upper()
        if occ_dir in ('INGRESS', 'EGRESS', 'BOTH'):
            return self._create_mult(occ_dir[0])
        self._log_nonrepeating_error(f'Unknown profile direction "{occ_dir}"')
        return self._create_mult(None)

    def field_obs_profile_body_occ_flag(self) -> MultFieldRet:
        return self._create_mult(self._index_col('rings:planetary_occultation_flag'))

    def field_obs_profile_quality_score(self) -> MultFieldRet:
        return self._create_mult(self._index_col('rings:data_quality_score'))

    def field_obs_profile_optical_depth1(self) -> FloatField:
        ret = self._index_col('rings:lowest_detectable_opacity')
        return cast(FloatField, ret)

    def field_obs_profile_optical_depth2(self) -> FloatField:
        ret = self._index_col('rings:highest_detectable_opacity')
        return cast(FloatField, ret)

    def field_obs_profile_wl_band(self) -> MultFieldRet:
        wl_range = self._index_col('pds:wavelength_range')
        if not wl_range:
            self._log_nonrepeating_error('pds:wavelength_range missing')
            return self._create_mult(None)
        wl_upper = wl_range.upper()
        if wl_upper == 'INFRARED':
            return self._create_mult('IR')
        if wl_upper == 'VISIBLE':
            return self._create_mult('VI')
        self._log_nonrepeating_error(f'Unknown pds:wavelength_range "{wl_range}"')
        return self._create_mult(None)

    def field_obs_profile_source(self) -> MultFieldRet:
        star_name = self._index_col('rings:star_name')
        star_name_id = star_name.upper().replace(' ', '_')
        return self._create_mult(star_name_id, disp_name=star_name,
                                 grouping='Stars')

    def field_obs_profile_host(self) -> MultFieldRet:
        return self._create_mult(self._inst_name())


    #####################################
    ### OVERRIDE FROM ObsRingGeometry ###
    #####################################

    # Note - A lot of the ring-specific fields are missing from atmos labels so
    # they will just turn out to be None.

    def field_obs_ring_geometry_projected_radial_resolution1(self) -> FloatField:
        return cast(FloatField, self._index_col('rings:radial_resolution'))

    def field_obs_ring_geometry_projected_radial_resolution2(self) -> FloatField:
        return self.field_obs_ring_geometry_projected_radial_resolution1()

    # Earth was seeing Uranus' south pole for the entire duration of this data set.
    # Thus the solar elevation was seeing the northern hemisphere and the
    # observer elevation was seeing the southern hemisphere.
    # For Uranus, these values are positive for the southern hemisphere.
    # The solar ring elevation, observer ring elevation, phase, incidence angle, and
    # emission angle methods are in obs_bundle_occ_common.py

    # The north-based fields are specific to planet and geometry.
    # Earth was seeing Uranus' south pole for the entire duration of this data set.
    # Thus the star was illuminating the north side of the rings, and the
    # north-based values are the same as the plain values.

    def field_obs_ring_geometry_north_based_incidence1(self) -> FloatField:
        return self.field_obs_ring_geometry_incidence1()

    def field_obs_ring_geometry_north_based_incidence2(self) -> FloatField:
        return self.field_obs_ring_geometry_incidence2()

    def field_obs_ring_geometry_north_based_emission1(self) -> FloatField:
        return self.field_obs_ring_geometry_emission1()

    def field_obs_ring_geometry_north_based_emission2(self) -> FloatField:
        return self.field_obs_ring_geometry_emission2()

    # The solar ring opening angle depends on planet and geometry.
    def field_obs_ring_geometry_solar_ring_opening_angle1(self) -> FloatField:
        oa = self._index_col('rings:observed_ring_elevation')
        if oa is not None:
            oa = -oa
        return cast(FloatField, oa)

    def field_obs_ring_geometry_solar_ring_opening_angle2(self) -> FloatField:
        return self.field_obs_ring_geometry_solar_ring_opening_angle1()

    def field_obs_ring_geometry_observer_ring_opening_angle1(self) -> FloatField:
        return cast(FloatField, self._index_col('rings:observed_ring_elevation'))

    def field_obs_ring_geometry_observer_ring_opening_angle2(self) -> FloatField:
        return self.field_obs_ring_geometry_observer_ring_opening_angle1()
