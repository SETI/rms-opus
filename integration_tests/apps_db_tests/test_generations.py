"""Tests that a generation the schema does not serve never reaches a response.

``obs_general`` is a view of the rows of the import generation the schema serves; the
rows of a pending generation, which an incremental update writes, sit beside them in
``obs_general_rows`` and in the child tables, which carry no generation. Each test plants
an observation in the next generation, a copy of a served one with its child rows, and
asks the endpoints that read a child table outside a search's results: what they answer
must be what they answered before the plant. The planted rows are deleted afterwards.

These tests require a database the import test sequence built.
"""

from __future__ import annotations

import logging
from typing import Any
from unittest import TestCase

from django.conf import settings
from django.core.cache import cache
from django.db import connection
from django.test import Client

from opus_import.generations import (
    ADDED_GENERATION_COLUMN,
    OBS_GENERAL_ROWS,
    SERVED_GENERATION_COLUMN,
)
from opus_import.schema_version import SCHEMA_VERSION_TABLE

#: The OPUS ID the planted observation carries, which no import writes.
_HIDDEN_OPUS_ID = 'hidden-generation-copy'

#: A product id only the planted observation's ``obs_pds`` row holds.
_HIDDEN_PRODUCT_ID = 'HIDDENGENERATIONPRODUCT'

#: A product type only the planted observation's files carry.
_HIDDEN_SHORT_NAME = 'hiddengeneration'

#: A URL only the planted observation's files carry.
_HIDDEN_URL = 'https://hidden.generation/file'

#: How far above every served id the planted observation's id lies.
_ID_OFFSET = 10_000_000

#: The child tables the planted observation gets a copy of its source's rows in.
_CHILD_TABLES = (
    'obs_pds',
    'obs_type_image',
    'obs_wavelength',
    'obs_files',
    'obs_general_target_name',
)


def _stored_columns(table: str) -> list[str]:
    """Return a table's columns that take a value, in order (a generated one does not)."""
    with connection.cursor() as cursor:
        cursor.execute(
            'SELECT COLUMN_NAME FROM information_schema.COLUMNS WHERE TABLE_SCHEMA = DATABASE() '
            "AND TABLE_NAME = %s AND EXTRA NOT LIKE '%%GENERATED%%' ORDER BY ORDINAL_POSITION",
            [table],
        )
        return [str(row[0]) for row in cursor.fetchall()]


def _copy_rows(table: str, key: str, source: int, values: dict[str, Any]) -> None:
    """Copy a table's rows of one observation, the given columns written anew.

    Parameters:
        table: The table.
        key: Its column naming the observation (``id`` or ``obs_general_id``).
        source: The observation copied.
        values: The columns given new values, by column, the key's among them.
    """
    columns = _stored_columns(table)
    selected = ', '.join('%s' if name in values else f'`{name}`' for name in columns)
    listed = ', '.join(f'`{name}`' for name in columns)
    params = [values[name] for name in columns if name in values]
    with connection.cursor() as cursor:
        cursor.execute(
            f'INSERT INTO `{table}` ({listed}) SELECT {selected} FROM `{table}` '  # nosec B608
            f'WHERE `{key}` = %s',
            [*params, source],
        )


class HiddenGenerationTests(TestCase):
    """The endpoints that read a child table outside a search's results."""

    def setUp(self) -> None:
        """Empty the stored searches and the cache, and find an observation to copy."""
        with connection.cursor() as cursor:
            cursor.execute('DELETE FROM search_results')
            cursor.execute('DELETE FROM user_searches')
            cursor.execute(
                'SELECT g.id, g.opus_id FROM obs_general g '
                'JOIN obs_pds p ON p.obs_general_id = g.id '
                'JOIN obs_type_image t ON t.obs_general_id = g.id '
                'JOIN obs_wavelength w ON w.obs_general_id = g.id '
                'WHERE EXISTS (SELECT 1 FROM obs_files f WHERE f.obs_general_id = g.id) '
                'AND EXISTS (SELECT 1 FROM obs_general_target_name n '
                'WHERE n.obs_general_id = g.id) ORDER BY g.id LIMIT 1'
            )
            self.source_id, self.source_opus_id = cursor.fetchone()
            cursor.execute(f'SELECT MAX(id) FROM `{OBS_GENERAL_ROWS}`')  # nosec B608
            self.hidden_id = int(cursor.fetchone()[0]) + _ID_OFFSET
            cursor.execute(
                f'SELECT `{SERVED_GENERATION_COLUMN}` FROM `{SCHEMA_VERSION_TABLE}`'  # nosec B608
            )
            self.next_generation = int(cursor.fetchone()[0]) + 1
        self.saved_threshold = settings.STRINGCHOICE_FULL_SEARCH_COUNT_THRESHOLD
        self.host = next((h for h in settings.ALLOWED_HOSTS if h != '*'), 'localhost')
        logging.disable(logging.ERROR)

    def tearDown(self) -> None:
        """Delete the planted rows, children first, and restore what setUp changed."""
        with connection.cursor() as cursor:
            for table in _CHILD_TABLES:
                cursor.execute(
                    f'DELETE FROM `{table}` WHERE obs_general_id = %s',  # nosec B608
                    [self.hidden_id],
                )
            cursor.execute(
                f'DELETE FROM `{OBS_GENERAL_ROWS}` WHERE id = %s',  # nosec B608
                [self.hidden_id],
            )
            cursor.execute('DELETE FROM search_results')
            cursor.execute('DELETE FROM user_searches')
        settings.STRINGCHOICE_FULL_SEARCH_COUNT_THRESHOLD = self.saved_threshold
        cache.clear()
        logging.disable(logging.NOTSET)

    def _plant(self) -> None:
        """Copy the source observation into the next generation, with its child rows."""
        hidden = self.hidden_id
        _copy_rows(
            OBS_GENERAL_ROWS,
            'id',
            self.source_id,
            {
                'id': hidden,
                'opus_id': _HIDDEN_OPUS_ID,
                ADDED_GENERATION_COLUMN: self.next_generation,
            },
        )
        _copy_rows(
            'obs_pds',
            'obs_general_id',
            self.source_id,
            {
                'obs_general_id': hidden,
                'opus_id': _HIDDEN_OPUS_ID,
                'product_id': _HIDDEN_PRODUCT_ID,
            },
        )
        _copy_rows('obs_type_image', 'obs_general_id', self.source_id, {'obs_general_id': hidden})
        # A smaller wavelength than any served one, so a leak moves the minimum.
        _copy_rows(
            'obs_wavelength',
            'obs_general_id',
            self.source_id,
            {'obs_general_id': hidden, 'wavelength1': 1e-12},
        )
        # Files under the served observation's own OPUS ID, as a re-imported bundle's are.
        _copy_rows(
            'obs_files',
            'obs_general_id',
            self.source_id,
            {'obs_general_id': hidden, 'short_name': _HIDDEN_SHORT_NAME, 'url': _HIDDEN_URL},
        )
        _copy_rows(
            'obs_general_target_name', 'obs_general_id', self.source_id, {'obs_general_id': hidden}
        )

    def _get(self, path: str) -> str:
        """Return what one URL answers, its cache emptied first."""
        cache.clear()
        response = Client().get(path, HTTP_HOST=self.host)
        self.assertEqual(response.status_code, 200, path)
        return response.content.decode('utf-8')

    def _answers(self, paths: list[str]) -> dict[str, str]:
        """Return what each URL answers."""
        return {path: self._get(path) for path in paths}

    def test_the_view_hides_the_planted_observation(self) -> None:
        """The served rows of obs_general do not include the next generation's."""
        self._plant()
        with connection.cursor() as cursor:
            cursor.execute('SELECT COUNT(*) FROM obs_general WHERE id = %s', [self.hidden_id])
            self.assertEqual(cursor.fetchone()[0], 0)
            cursor.execute(
                f'SELECT COUNT(*) FROM `{OBS_GENERAL_ROWS}` WHERE id = %s',  # nosec B608
                [self.hidden_id],
            )
            self.assertEqual(cursor.fetchone()[0], 1)

    def test_the_empty_searchs_counts_and_endpoints_are_unchanged(self) -> None:
        """Mult counts of a list column and a child's column, and a child's range."""
        paths = [
            '/api/meta/mults/target.json',
            '/api/meta/mults/imagetype.json',
            '/api/meta/range/endpoints/wavelength1.json',
        ]
        before = self._answers(paths)
        self._plant()
        self.assertEqual(self._answers(paths), before)

    def test_the_autocomplete_from_every_observation_omits_the_planted_value(self) -> None:
        """The branch that reads every observation's values, not the search's."""
        settings.STRINGCHOICE_FULL_SEARCH_COUNT_THRESHOLD = 0
        path = f'/__api/stringsearchchoices/productid.json?productid={_HIDDEN_PRODUCT_ID[:12]}'
        self._plant()
        self.assertNotIn(_HIDDEN_PRODUCT_ID, self._get(path))

    def test_files_and_product_types_omit_the_planted_files(self) -> None:
        """The served observation's files, under an OPUS ID the next generation shares."""
        paths = [
            f'/api/files/{self.source_opus_id}.json',
            f'/api/product_types/{self.source_opus_id}.json',
            '/api/product_types.json',
        ]
        before = self._answers(paths)
        self._plant()
        after = self._answers(paths)
        self.assertEqual(after, before)
        for answer in after.values():
            self.assertNotIn(_HIDDEN_SHORT_NAME, answer)
