"""Checks that the imported tables agree with each other."""

from typing import Any
from unittest import TestCase

from django.db import connection
from django.db.models import Count, QuerySet

from opus_app.apps.paraminfo.models import ParamInfo
from opus_app.apps.search.models import (
    Mult,
    ObsGeneral,
    ObsInstrumentCocirs,
    ObsInstrumentCoiss,
    ObsInstrumentCouvis,
    ObsInstrumentCovims,
    ObsInstrumentGossi,
    ObsInstrumentNhlorri,
    ObsInstrumentNhmvic,
    ObsInstrumentVgiss,
    ObsMissionCassini,
    ObsMissionGalileo,
    ObsMissionHubble,
    ObsMissionNewHorizons,
    ObsMissionVoyager,
    ObsPds,
    ObsProfile,
    ObsSurfaceGeometryTarget,
    ObsTypeImage,
    ObsWavelength,
    Partables,
    TableNames,
)
from opus_app.apps.tools.db_utils import MYSQL_TABLE_NOT_EXISTS
from opus_app.apps.tools.import_constants import mult_field_id


def _mult_rows(param_qualified_name: str) -> QuerySet[Mult]:
    """Return one mult field's ``mult`` rows.

    Parameters:
        param_qualified_name: The field's ``<table>.<column>`` name.

    Returns:
        The rows, as a queryset to filter further.
    """
    return Mult.objects.filter(field_id=mult_field_id(param_qualified_name))


class DBIntegrityTest(TestCase):
    #############################################
    ######### DATABASE INTEGRITY CHECKS #########
    #############################################
    """Cross-checks between the tables the import pipeline wrote."""

    def test__pds_image_wl_bundle_counts_match_obs_general(self) -> None:
        """DB Integrity: bundles in obs_general = obs_pds, obs_type_image, obs_wavelength, obs_profile
        Test that the observation count per bundle is the same in
        obs_general, obs_pds, obs_type_image, and obs_wavelength, since
        these tables should all include the exact same set of observations.
        """
        self.maxDiff = None
        obs = (
            ObsGeneral.objects.values_list('bundle_id')
            .annotate(Count('bundle_id'))
            .order_by('bundle_id')
        )
        pds = (
            ObsPds.objects.values_list('bundle_id')
            .annotate(Count('bundle_id'))
            .order_by('bundle_id')
        )
        self.assertEqual(list(obs), list(pds))
        img = (
            ObsTypeImage.objects.values_list('obs_general__bundle_id')
            .annotate(Count('obs_general__bundle_id'))
            .order_by('obs_general__bundle_id')
        )
        self.assertEqual(list(obs), list(img))
        wl: Any = (
            ObsWavelength.objects.values_list('obs_general__bundle_id')
            .annotate(Count('obs_general__bundle_id'))
            .order_by('obs_general__bundle_id')
        )
        self.assertEqual(list(obs), list(wl))
        wl = (
            ObsProfile.objects.values_list('obs_general__bundle_id')
            .annotate(Count('obs_general__bundle_id'))
            .order_by('obs_general__bundle_id')
        )
        self.assertEqual(list(obs), list(wl))

    def test__cassini_counts_match_obs_general(self) -> None:
        """DB Integrity: bundles in obs_general = obs_mission_cassini
        Test that the observation count per bundle is the same in
        obs_general for mission_id='CO' and obs_mission_cassini.
        """
        mission_id = (_mult_rows('obs_general.mission_id').values_list('id').filter(value='CO'))[0][
            0
        ]
        obs = (
            ObsGeneral.objects.values_list('bundle_id')
            .filter(mission_id=mission_id)
            .annotate(Count('bundle_id'))
            .order_by('bundle_id')
        )
        ref = (
            ObsMissionCassini.objects.values_list('obs_general__bundle_id')
            .annotate(Count('obs_general__bundle_id'))
            .order_by('obs_general__bundle_id')
        )
        try:
            self.assertEqual(list(obs), list(ref))
        except Exception as e:  # pragma: no cover
            if e.args[0] != MYSQL_TABLE_NOT_EXISTS:
                raise

    def test__galileo_counts_match_obs_general(self) -> None:
        """DB Integrity: bundles in obs_general = obs_mission_galileo
        Test that the observation count per bundle is the same in
        obs_general for mission_id='GO' and obs_mission_galileo.
        """
        mission_id = (_mult_rows('obs_general.mission_id').values_list('id').filter(value='GO'))[0][
            0
        ]
        obs = (
            ObsGeneral.objects.values_list('bundle_id')
            .filter(mission_id=mission_id)
            .annotate(Count('bundle_id'))
            .order_by('bundle_id')
        )
        ref = (
            ObsMissionGalileo.objects.values_list('obs_general__bundle_id')
            .annotate(Count('obs_general__bundle_id'))
            .order_by('obs_general__bundle_id')
        )
        try:
            self.assertEqual(list(obs), list(ref))
        except Exception as e:  # pragma: no cover
            if e.args[0] != MYSQL_TABLE_NOT_EXISTS:
                raise

    def test__hubble_counts_match_obs_general(self) -> None:
        """DB Integrity: bundles in obs_general = obs_mission_hubble
        Test that the observation count per bundle is the same in
        obs_general for mission_id='HST' and obs_mission_hubble.
        """
        mission_id = (_mult_rows('obs_general.mission_id').values_list('id').filter(value='HST'))[
            0
        ][0]
        obs = (
            ObsGeneral.objects.values_list('bundle_id')
            .filter(mission_id=mission_id)
            .annotate(Count('bundle_id'))
            .order_by('bundle_id')
        )
        ref = (
            ObsMissionHubble.objects.values_list('obs_general__bundle_id')
            .annotate(Count('obs_general__bundle_id'))
            .order_by('obs_general__bundle_id')
        )
        try:
            self.assertEqual(list(obs), list(ref))
        except Exception as e:  # pragma: no cover
            if e.args[0] != MYSQL_TABLE_NOT_EXISTS:
                raise

    def test__nh_counts_match_obs_general(self) -> None:
        """DB Integrity: bundles in obs_general = obs_mission_new_horizons
        Test that the observation count per bundle is the same in
        obs_general for mission_id='NH' and obs_mission_newhorizons.
        """
        mission_id = (_mult_rows('obs_general.mission_id').values_list('id').filter(value='NH'))[0][
            0
        ]
        obs = (
            ObsGeneral.objects.values_list('bundle_id')
            .filter(mission_id=mission_id)
            .annotate(Count('bundle_id'))
            .order_by('bundle_id')
        )
        ref = (
            ObsMissionNewHorizons.objects.values_list('obs_general__bundle_id')
            .annotate(Count('obs_general__bundle_id'))
            .order_by('obs_general__bundle_id')
        )
        try:
            self.assertEqual(list(obs), list(ref))
        except Exception as e:  # pragma: no cover
            if e.args[0] != MYSQL_TABLE_NOT_EXISTS:
                raise

    def test__voyager_counts_match_obs_general(self) -> None:
        """DB Integrity: bundles in obs_general = obs_mission_voyager
        Test that the observation count per bundle is the same in
        obs_general for mission_id='VG' and obs_mission_voyager.
        """
        mission_id = (_mult_rows('obs_general.mission_id').values_list('id').filter(value='VG'))[0][
            0
        ]
        obs = (
            ObsGeneral.objects.values_list('bundle_id')
            .filter(mission_id=mission_id)
            .annotate(Count('bundle_id'))
            .order_by('bundle_id')
        )
        ref = (
            ObsMissionVoyager.objects.values_list('obs_general__bundle_id')
            .annotate(Count('obs_general__bundle_id'))
            .order_by('obs_general__bundle_id')
        )
        try:
            self.assertEqual(list(obs), list(ref))
        except Exception as e:  # pragma: no cover
            if e.args[0] != MYSQL_TABLE_NOT_EXISTS:
                raise

    def test__cocirs_counts_match_obs_general(self) -> None:
        """DB Integrity: bundles in obs_general = obs_instrument_cocirs
        Test that the observation count per bundle is the same in
        obs_general for instrument_id='COCIRS' and obs_instrument_cocirs.
        """
        instrument_id = (
            _mult_rows('obs_general.instrument_id').values_list('id').filter(value='COCIRS')
        )[0][0]
        obs = (
            ObsGeneral.objects.values_list('bundle_id')
            .filter(instrument_id=instrument_id)
            .annotate(Count('bundle_id'))
            .order_by('bundle_id')
        )
        ref = (
            ObsInstrumentCocirs.objects.values_list('obs_general__bundle_id')
            .annotate(Count('obs_general__bundle_id'))
            .order_by('obs_general__bundle_id')
        )
        try:
            self.assertEqual(list(obs), list(ref))
        except Exception as e:  # pragma: no cover
            if e.args[0] != MYSQL_TABLE_NOT_EXISTS:
                raise

    def test__coiss_counts_match_obs_general(self) -> None:
        """DB Integrity: bundles in obs_general = obs_instrument_coiss
        Test that the observation count per bundle is the same in
        obs_general for instrument_id='COISS' and obs_instrument_coiss.
        """
        instrument_id = (
            _mult_rows('obs_general.instrument_id').values_list('id').filter(value='COISS')
        )[0][0]
        obs = (
            ObsGeneral.objects.values_list('bundle_id')
            .filter(instrument_id=instrument_id)
            .annotate(Count('bundle_id'))
            .order_by('bundle_id')
        )
        ref = (
            ObsInstrumentCoiss.objects.values_list('obs_general__bundle_id')
            .annotate(Count('obs_general__bundle_id'))
            .order_by('obs_general__bundle_id')
        )
        try:
            self.assertEqual(list(obs), list(ref))
        except Exception as e:  # pragma: no cover
            if e.args[0] != MYSQL_TABLE_NOT_EXISTS:
                raise

    def test__couvis_counts_match_obs_general(self) -> None:
        """DB Integrity: bundles in obs_general = obs_instrument_couvis
        Test that the observation count per bundle is the same in
        obs_general for instrument_id='COUVIS' and obs_instrument_couvis.
        """
        instrument_id = (
            _mult_rows('obs_general.instrument_id').values_list('id').filter(value='COUVIS')
        )[0][0]
        print(instrument_id)
        obs = (
            ObsGeneral.objects.values_list('bundle_id')
            .filter(instrument_id=instrument_id)
            .annotate(Count('bundle_id'))
            .order_by('bundle_id')
        )
        ref = (
            ObsInstrumentCouvis.objects.values_list('obs_general__bundle_id')
            .annotate(Count('obs_general__bundle_id'))
            .order_by('obs_general__bundle_id')
        )
        try:
            self.assertEqual(list(obs), list(ref))
        except Exception as e:  # pragma: no cover
            if e.args[0] != MYSQL_TABLE_NOT_EXISTS:
                raise

    def test__covims_counts_match_obs_general(self) -> None:
        """DB Integrity: bundles in obs_general = obs_instrument_covims
        Test that the observation count per bundle is the same in
        obs_general for instrument_id='COVIMS' and obs_instrument_covims.
        """
        instrument_id = (
            _mult_rows('obs_general.instrument_id').values_list('id').filter(value='COVIMS')
        )[0][0]
        obs = (
            ObsGeneral.objects.values_list('bundle_id')
            .filter(instrument_id=instrument_id)
            .annotate(Count('bundle_id'))
            .order_by('bundle_id')
        )
        ref = (
            ObsInstrumentCovims.objects.values_list('obs_general__bundle_id')
            .annotate(Count('obs_general__bundle_id'))
            .order_by('obs_general__bundle_id')
        )
        try:
            self.assertEqual(list(obs), list(ref))
        except Exception as e:  # pragma: no cover
            if e.args[0] != MYSQL_TABLE_NOT_EXISTS:
                raise

    def test__gossi_counts_match_obs_general(self) -> None:
        """DB Integrity: bundles in obs_general = obs_instrument_gossi
        Test that the observation count per bundle is the same in
        obs_general for instrument_id='GOSSI' and obs_instrument_gossi.
        """
        instrument_id = (
            _mult_rows('obs_general.instrument_id').values_list('id').filter(value='GOSSI')
        )[0][0]
        obs = (
            ObsGeneral.objects.values_list('bundle_id')
            .filter(instrument_id=instrument_id)
            .annotate(Count('bundle_id'))
            .order_by('bundle_id')
        )
        ref = (
            ObsInstrumentGossi.objects.values_list('obs_general__bundle_id')
            .annotate(Count('obs_general__bundle_id'))
            .order_by('obs_general__bundle_id')
        )
        try:
            self.assertEqual(list(obs), list(ref))
        except Exception as e:  # pragma: no cover
            if e.args[0] != MYSQL_TABLE_NOT_EXISTS:
                raise

    def test__nhlorri_counts_match_obs_general(self) -> None:
        """DB Integrity: bundles in obs_general = obs_instrument_nhlorri
        Test that the observation count per bundle is the same in
        obs_general for instrument_id='NHLORRI' and obs_instrument_nhlorri.
        """
        instrument_id = (
            _mult_rows('obs_general.instrument_id').values_list('id').filter(value='NHLORRI')
        )[0][0]
        obs = (
            ObsGeneral.objects.values_list('bundle_id')
            .filter(instrument_id=instrument_id)
            .annotate(Count('bundle_id'))
            .order_by('bundle_id')
        )
        ref = (
            ObsInstrumentNhlorri.objects.values_list('obs_general__bundle_id')
            .annotate(Count('obs_general__bundle_id'))
            .order_by('obs_general__bundle_id')
        )
        try:
            self.assertEqual(list(obs), list(ref))
        except Exception as e:  # pragma: no cover
            if e.args[0] != MYSQL_TABLE_NOT_EXISTS:
                raise

    def test__nhmvic_counts_match_obs_general(self) -> None:
        """DB Integrity: bundles in obs_general = obs_instrument_nhmvic
        Test that the observation count per bundle is the same in
        obs_general for instrument_id='NHMVIC' and obs_instrument_nhmvic.
        """
        instrument_id = (
            _mult_rows('obs_general.instrument_id').values_list('id').filter(value='NHMVIC')
        )[0][0]
        obs = (
            ObsGeneral.objects.values_list('bundle_id')
            .filter(instrument_id=instrument_id)
            .annotate(Count('bundle_id'))
            .order_by('bundle_id')
        )
        ref = (
            ObsInstrumentNhmvic.objects.values_list('obs_general__bundle_id')
            .annotate(Count('obs_general__bundle_id'))
            .order_by('obs_general__bundle_id')
        )
        try:
            self.assertEqual(list(obs), list(ref))
        except Exception as e:  # pragma: no cover
            if e.args[0] != MYSQL_TABLE_NOT_EXISTS:
                raise

    def test__vgiss_counts_match_obs_general(self) -> None:
        """DB Integrity: bundles in obs_general = obs_instrument_vgiss
        Test that the observation count per bundle is the same in
        obs_general for instrument_id='VGISS' and obs_instrument_vgiss.
        """
        instrument_id = (
            _mult_rows('obs_general.instrument_id').values_list('id').filter(value='VGISS')
        )[0][0]
        obs = (
            ObsGeneral.objects.values_list('bundle_id')
            .filter(instrument_id=instrument_id)
            .annotate(Count('bundle_id'))
            .order_by('bundle_id')
        )
        ref = (
            ObsInstrumentVgiss.objects.values_list('obs_general__bundle_id')
            .annotate(Count('obs_general__bundle_id'))
            .order_by('obs_general__bundle_id')
        )
        try:
            self.assertEqual(list(obs), list(ref))
        except Exception as e:  # pragma: no cover
            if e.args[0] != MYSQL_TABLE_NOT_EXISTS:
                raise

    def test__mult_field_matches_id_fields_in_mult_tables(self) -> None:
        """DB Integrity: instrument mults exist
        Check the obs_general instrument_id mult to make sure there are no
        references to an id in the mult table that don't have entries.
        """
        cursor = connection.cursor()
        q = """SELECT COUNT(*) FROM obs_general
               WHERE instrument_id NOT IN
                   (SELECT id FROM mult WHERE field_id = %s)"""
        cursor.execute(q, [mult_field_id('obs_general.instrument_id')])
        result = cursor.fetchone()
        cursor.close()
        self.assertEqual(result[0], 0)

    def test__every_surface_geometry_body_has_its_category_rows(self) -> None:
        """DB Integrity: each body ``obs_surface_geometry_target`` holds has its category rows
        Every distinct target_name of obs_surface_geometry_target has a table_names row
        naming the table and the body, a partables row revealing that category, and the
        template's param_info rows under it, as many as every other body's.
        """
        targets = set(ObsSurfaceGeometryTarget.objects.values_list('target_name', flat=True))
        categories = {
            row.target_name: row.table_name
            for row in TableNames.objects.filter(physical_table='obs_surface_geometry_target')
            if row.target_name is not None
        }
        self.assertEqual(set(categories), targets)
        partables = set(
            Partables.objects.filter(trigger_tab='obs_surface_geometry_name').values_list(
                'partable', flat=True
            )
        )
        self.assertEqual(partables, set(categories.values()))
        field_counts = {
            row['category_name']: row['fields']
            for row in ParamInfo.objects.filter(category_name__in=categories.values())
            .values('category_name')
            .annotate(fields=Count('id'))
        }
        self.assertEqual(set(field_counts), set(categories.values()))
        self.assertEqual(len(set(field_counts.values())), 1)

    def test__the_selector_category_reads_every_row_of_the_surface_geometry_table(self) -> None:
        """DB Integrity: the selector category names the table and no body"""
        row = TableNames.objects.get(table_name='obs_surface_geometry_name')
        self.assertEqual(
            (row.physical_table, row.target_name), ('obs_surface_geometry_target', None)
        )
        self.assertEqual(
            list(
                ParamInfo.objects.filter(category_name='obs_surface_geometry_name').values_list(
                    'name', 'slug'
                )
            ),
            [('target_name', 'surfacegeometrytargetname')],
        )

    def test__planets_properly_ordered(self) -> None:
        "DB Integrity: planets are properly ordered by their rank"
        the_planets = [
            planet['label']
            for planet in _mult_rows('obs_general.planet_id')
            .filter(display='Y')
            .order_by('disp_rank')
            .values('label')
        ]
        print(
            'SELECT label FROM mult WHERE field_id = <planet_id> AND display = "Y" '
            'ORDER BY disp_rank;'
        )
        expect = [
            'Venus',
            'Earth',
            'Mars',
            'Jupiter',
            'Saturn',
            'Uranus',
            'Neptune',
            'Pluto',
            'Other',
        ]
        self.assertEqual(expect, the_planets)

    def test__surface_geometry_table_label_is_correct(self) -> None:
        "DB Integrity: label of the obs_surface_geometry table in table_names"
        label = TableNames.objects.get(table_name='obs_surface_geometry').label
        self.assertEqual(label, 'Surface Geometry Constraints')
