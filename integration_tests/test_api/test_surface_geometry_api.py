"""The surface geometry selector and body fields, as the public API answers them.

Every body's surface geometry is a row of one table, so an observation can have several
of the selector's rows. What is worth pinning, and why:

* **The selector never multiplies rows.** As a results column or a sort order it is one
  value per observation, the alphabetically first label of its bodies -- of the bodies
  the search selects when the search constrains the field -- so a page has one row per
  observation and a search's stored results can be numbered.
* **A body's field reads the body's rows.** The string-search choices of a body's field,
  and its range endpoints, come from the body's rows of the shared table.

The expected answers are computed from the database rather than recorded, since they
are a property of whatever was imported. That database is the local one, so against a
remote server (``OPUS_TEST_GO_LIVE``) every test whose answer is computed from it is
skipped.
"""

import json
import logging
from typing import Any
from unittest import TestCase

import requests
from django.conf import settings
from django.core.cache import cache
from django.db import connection
from django.db.models import Count, Max, Min
from rest_framework.test import RequestsClient

from opus_app.apps.search.models import ObsGeneral, ObsSurfaceGeometryTarget, TableNames
from opus_app.apps.tools.app_utils import http400_search_params_invalid
from opus_app.apps.tools.import_constants import mult_table
from opus_support import collation_key

from .api_test_helper import ApiTestHelper, go_live_target

#: The selector's mult field.
_SELECTOR_FIELD = 'obs_surface_geometry_name.target_name'


def _labels() -> dict[int, str]:
    """Return each body's label, keyed by its id.

    Returns:
        Every row of the selector's mult field in the local database, as a mapping from
        the row's id, which is what ``obs_surface_geometry_target.target_name`` holds, to
        its label.
    """
    return {row_id: row.label for row_id, row in mult_table(_SELECTOR_FIELD).rows.items()}


def _bodies_of(opus_ids: list[str], target_ids: list[int] | None = None) -> dict[str, set[int]]:
    """Return the bodies each observation has, among `target_ids` when given.

    Parameters:
        opus_ids: The observations.
        target_ids: The bodies to keep to, as ids in the selector's mult field, or None
            for every body.

    Returns:
        A mapping from each of `opus_ids` to the ids of the bodies its rows of
        ``obs_surface_geometry_target`` in the local database are for, among
        `target_ids` when given; an empty set for an observation with no such rows.
    """
    rows = ObsSurfaceGeometryTarget.objects.filter(obs_general__opus_id__in=opus_ids)
    if target_ids is not None:
        rows = rows.filter(target_name__in=target_ids)
    bodies: dict[str, set[int]] = {opus_id: set() for opus_id in opus_ids}
    for opus_id, target_id in rows.values_list('obs_general__opus_id', 'target_name'):
        bodies[opus_id].add(target_id)
    return bodies


class ApiSurfaceGeometryTests(ApiTestHelper, TestCase):
    """The selector as a column and a sort, and a body field's string choices."""

    def setUp(self) -> None:
        """Turn off fault injection and error logging, and choose the client.

        Every stored search is removed, so each search here is built by the code under
        test rather than read back from an earlier build.
        """
        with connection.cursor() as cursor:
            cursor.execute('DELETE FROM search_results')
            cursor.execute('DELETE FROM user_searches')
        self.maxDiff = None
        settings.OPUS_FAKE_API_DELAYS = 0
        settings.OPUS_FAKE_SERVER_ERROR404_PROBABILITY = 0
        settings.OPUS_FAKE_SERVER_ERROR500_PROBABILITY = 0
        settings.CACHE_KEY_PREFIX = 'opustest:' + settings.DB_SCHEMA_NAME
        logging.disable(logging.ERROR)
        if go_live_target():  # pragma: no cover - remote server
            self.client = requests.Session()
        else:
            self.client = RequestsClient()
        cache.clear()

    def tearDown(self) -> None:
        """Restore logging after one test."""
        logging.disable(logging.NOTSET)

    def _require_local_database(self) -> None:
        """Skip a test whose expected answer is computed from the local database.

        A remote server serves a database of its own, which the local one does not
        describe.
        """
        if go_live_target():  # pragma: no cover - remote server
            self.skipTest('the expected answer is computed from the local database')

    def _page(self, url: str) -> dict[str, Any]:
        """Return a data request's decoded answer, after checking it succeeded."""
        response = self._get_response(url)
        self.assertEqual(response.status_code, 200)
        page: dict[str, Any] = json.loads(response.content)
        return page

    def _assert_one_label_each(
        self, page: list[list[Any]], target_ids: list[int] | None, label_column: int
    ) -> None:
        """Assert each row is its own observation, labeled with its first body."""
        opus_ids = [row[0] for row in page]
        self.assertEqual(len(opus_ids), len(set(opus_ids)))
        labels = _labels()
        bodies = _bodies_of(opus_ids, target_ids)
        for row in page:
            names = sorted((labels[target_id] for target_id in bodies[row[0]]), key=collation_key)
            self.assertEqual(row[label_column], names[0] if names else 'N/A')

    def test__api_data_selector_sort_with_its_constraint_is_one_row_each(self) -> None:
        "[test_surface_geometry_api.py] /api/data: sorting by the constrained selector"
        self._require_local_database()
        url = (
            '/api/data.json?surfacegeometrytargetname=Saturn&cols=opusid'
            '&order=surfacegeometrytargetname,opusid&limit=50'
        )
        page = self._page(url)
        saturn = TableNames.objects.get(table_name='obs_surface_geometry__saturn').target_name
        assert saturn is not None
        expected = list(
            ObsGeneral.objects.filter(
                id__in=ObsSurfaceGeometryTarget.objects.filter(target_name=saturn).values(
                    'obs_general_id'
                )
            )
            .order_by('opus_id')
            .values_list('opus_id', flat=True)[:50]
        )
        self.assertEqual([row[0] for row in page['page']], expected)

    def test__api_data_selector_column_is_one_value_per_observation(self) -> None:
        "[test_surface_geometry_api.py] /api/data: the selector as a results column"
        url = (
            '/api/data.json?surfacegeometrytargetname=Saturn'
            '&cols=opusid,surfacegeometrytargetname&limit=50'
        )
        page = self._page(url)
        self.assertEqual(len(page['page']), 50)
        self.assertEqual({row[1] for row in page['page']}, {'Saturn'})
        self.assertEqual(len({row[0] for row in page['page']}), 50)

    def test__api_data_selector_sort_over_two_bodies_is_one_row_each(self) -> None:
        "[test_surface_geometry_api.py] /api/data: sorting by the selector over two bodies"
        self._require_local_database()
        both = (
            ObsSurfaceGeometryTarget.objects.values('obs_general_id')
            .annotate(bodies=Count('target_name'))
            .filter(bodies__gte=2)
            .order_by('obs_general_id')
            .first()
        )
        assert both is not None
        target_ids = sorted(
            ObsSurfaceGeometryTarget.objects.filter(
                obs_general_id=both['obs_general_id']
            ).values_list('target_name', flat=True)
        )[:2]
        labels = _labels()
        names = ','.join(labels[target_id] for target_id in target_ids)
        url = (
            f'/api/data.json?surfacegeometrytargetname={names}'
            '&cols=opusid,surfacegeometrytargetname'
            '&order=surfacegeometrytargetname,opusid&limit=100'
        )
        page = self._page(url)
        expected = (
            ObsSurfaceGeometryTarget.objects.filter(target_name__in=target_ids)
            .values('obs_general_id')
            .distinct()
            .count()
        )
        self.assertEqual(page['available'], expected)
        self.assertEqual(len(page['page']), min(100, expected))
        self._assert_one_label_each(page['page'], target_ids, 1)
        shown = [row[1] for row in page['page']]
        self.assertEqual(shown, sorted(shown, key=collation_key))

    def test__api_data_selector_sort_without_a_constraint_is_one_row_each(self) -> None:
        "[test_surface_geometry_api.py] /api/data: sorting by the unconstrained selector"
        self._require_local_database()
        url = (
            '/api/data.json?cols=opusid,surfacegeometrytargetname'
            '&order=-surfacegeometrytargetname,opusid&limit=100'
        )
        page = self._page(url)
        self.assertEqual(page['available'], ObsGeneral.objects.count())
        self.assertEqual(len(page['page']), 100)
        self._assert_one_label_each(page['page'], None, 1)
        shown = [row[1] for row in page['page']]
        self.assertEqual(shown, sorted(shown, key=collation_key, reverse=True))

    def test__api_data_selector_sort_with_a_body_no_row_names_is_refused(self) -> None:
        "[test_surface_geometry_api.py] /api/data: sorting by a selector naming no body"
        url = (
            '/api/data.json?surfacegeometrytargetname=NotABody'
            '&cols=opusid,surfacegeometrytargetname&order=surfacegeometrytargetname'
        )
        self._run_status_equal(url, 400, http400_search_params_invalid('/api/data.json'))

    def test__api_stringsearchchoices_of_a_body_field_reads_the_bodys_rows(self) -> None:
        "[test_surface_geometry_api.py] /__api/stringsearchchoices: a body's field"
        self._require_local_database()
        url = '/__api/stringsearchchoices/SURFACEGEOsaturn_phase1.json?reqno=1&limit=10'
        response = self._get_response(url)
        self.assertEqual(response.status_code, 200)
        choices = json.loads(response.content)['choices']
        saturn = TableNames.objects.get(table_name='obs_surface_geometry__saturn').target_name
        assert saturn is not None
        values = (
            ObsSurfaceGeometryTarget.objects.filter(target_name=saturn)
            .order_by('phase1')
            .values_list('phase1', flat=True)
            .distinct()[:10]
        )
        self.assertEqual(choices, list(values))

    def test__api_range_endpoints_of_a_body_field_reads_the_bodys_rows(self) -> None:
        "[test_surface_geometry_api.py] /api/meta/range/endpoints: a body's field, no search"
        self._require_local_database()
        url = '/api/meta/range/endpoints/SURFACEGEOjupiter_planetographiclatitude.json'
        response = self._get_response(url)
        self.assertEqual(response.status_code, 200)
        endpoints = json.loads(response.content)
        jupiter = TableNames.objects.get(table_name='obs_surface_geometry__jupiter').target_name
        assert jupiter is not None
        rows = ObsSurfaceGeometryTarget.objects.filter(target_name=jupiter)
        expected = rows.aggregate(
            min=Min('planetographic_latitude1'), max=Max('planetographic_latitude2')
        )
        nulls = rows.filter(
            planetographic_latitude1__isnull=True, planetographic_latitude2__isnull=True
        ).count()
        self.assertEqual(float(endpoints['min']), expected['min'])
        self.assertEqual(float(endpoints['max']), expected['max'])
        self.assertEqual(endpoints['nulls'], nulls)
        self.assertEqual(endpoints['units'], 'degrees')
