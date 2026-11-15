"""Tests that a generation the schema does not serve never reaches a response.

``obs_general`` is a view of the rows of the import generation the schema serves; the
rows of a pending generation, which an incremental update writes, and the rows a switch
retired, which wait for the purge, sit beside them in ``obs_general_rows`` and in the
child tables, which carry no generation. The endpoints that read a child table outside a
search's results join the view while the version row names a pending generation or marks
the switch revertible, and only then.

Each hiding test plants an observation the view does not show, a copy of a served one
with its child rows: once in the next generation, with the version row naming it pending,
as ``--begin-generation`` leaves the schema; and once retired at the served generation,
with the switch revertible, as ``--switch-generation`` leaves it. What the endpoints
answer must be what they answered before the plant. The autocomplete from every
observation is the exception: it suggests every stored value, as the mult choices list
theirs. The statement tests compare the SQL itself: with no other generation's rows, no
statement joins the view, and with them, each joined statement is the plain one with the
join added. The planted rows are deleted, and the view and the version row put back,
afterwards.

These tests require a database the import test sequence built.
"""

from __future__ import annotations

import json
import logging
import re
from importlib.resources import files
from typing import Any
from unittest import TestCase

from django.conf import settings
from django.core.cache import cache
from django.db import connection
from django.test import Client
from django.test.utils import CaptureQueriesContext

from opus_import.generations import (
    ADDED_GENERATION_COLUMN,
    OBS_GENERAL_ROWS,
    OBS_GENERAL_VIEW,
    PENDING_GENERATION_COLUMN,
    PENDING_STATE_COLUMN,
    PENDING_WRITING,
    REMOVED_GENERATION_COLUMN,
    REVERTIBLE_COLUMN,
    SERVED_GENERATION_COLUMN,
    in_generation_condition,
    view_columns,
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

#: How the planted observation is hidden: in a pending generation, or retired by a
#: revertible switch.
_PENDING = 'pending'
_RETIRED = 'retired'

#: The empty search's counts and endpoints of child columns: a list column's junction
#: table, a child's GROUP column, and a child's range, whose two statements join.
_COUNT_PATHS = [
    '/api/meta/mults/target.json',
    '/api/meta/mults/imagetype.json',
    '/api/meta/range/endpoints/wavelength1.json',
]

#: The served observations' files and product types; the OPUS ID is filled in.
_FILE_PATHS = [
    '/api/files/{opus_id}.json',
    '/api/product_types/{opus_id}.json',
    '/api/product_types.json',
]

#: The join to the view, as a statement renders it off a child table or its alias.
_JOIN = re.compile(r' STRAIGHT_JOIN `obs_general` ON `obs_general`\.`id`=`\w+`\.`obs_general_id`')

#: The product types' tie-breaking order, which a statement with the join adds.
_PRODUCT_TYPE_TIES = ''.join(
    f',`obs_files`.`{name}`' for name in ('category', 'short_name', 'full_name', 'version_name')
)


def _set_view(served: int | None) -> None:
    """Re-create the obs_general view as the import does: of every row, or of one generation.

    Parameters:
        served: The generation shown, or None for every row.
    """
    schema = json.loads(
        (files('opus_import') / 'table_schemas' / 'obs_general.json').read_text(encoding='utf-8')
    )
    columns = ', '.join(f'`{name}`' for name in view_columns(schema))
    statement = (
        'CREATE OR REPLACE ALGORITHM=MERGE SQL SECURITY INVOKER VIEW '  # nosec B608
        f'`{OBS_GENERAL_VIEW}` AS SELECT {columns} FROM `{OBS_GENERAL_ROWS}`'
    )
    if served is not None:
        condition = in_generation_condition(lambda name: f'`{name}`', OBS_GENERAL_ROWS)
        statement += ' WHERE ' + condition.replace('%s', str(served))
    with connection.cursor() as cursor:
        cursor.execute(statement)


def _set_version_row(pending: int | None, pending_state: str | None, revertible: int) -> None:
    """Write the version row's pending generation, its state and ``revertible``."""
    with connection.cursor() as cursor:
        cursor.execute(
            f'UPDATE `{SCHEMA_VERSION_TABLE}` '  # nosec B608
            f'SET `{PENDING_GENERATION_COLUMN}` = %s, '
            f'`{PENDING_STATE_COLUMN}` = %s, `{REVERTIBLE_COLUMN}` = %s',
            [pending, pending_state, revertible],
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


def _without_join(statement: str) -> str:
    """Return a statement less the join to the view and the tie-breaking order it adds."""
    return _JOIN.sub('', statement).replace(_PRODUCT_TYPE_TIES, '')


class HiddenGenerationTests(TestCase):
    """The endpoints that read a child table outside a search's results."""

    def setUp(self) -> None:
        """Empty the stored searches and the cache, keep the version row, and find an
        observation to copy."""
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
                f'SELECT `{SERVED_GENERATION_COLUMN}`, '  # nosec B608
                f'`{PENDING_GENERATION_COLUMN}`, '
                f'`{PENDING_STATE_COLUMN}`, `{REVERTIBLE_COLUMN}` FROM `{SCHEMA_VERSION_TABLE}`'
            )
            served, pending, pending_state, revertible = cursor.fetchone()
            self.served = int(served)
            self.saved_version_row = (pending, pending_state, int(revertible))
        self.saved_threshold = settings.STRINGCHOICE_FULL_SEARCH_COUNT_THRESHOLD
        self.host = next((h for h in settings.ALLOWED_HOSTS if h != '*'), 'localhost')
        logging.disable(logging.ERROR)

    def tearDown(self) -> None:
        """Delete the planted rows and restore what setUp changed."""
        self._unplant()
        with connection.cursor() as cursor:
            cursor.execute('DELETE FROM user_searches')
        settings.STRINGCHOICE_FULL_SEARCH_COUNT_THRESHOLD = self.saved_threshold
        cache.clear()
        logging.disable(logging.NOTSET)

    def _unplant(self) -> None:
        """Delete the planted rows, children first, and put the view and the version row
        back as setUp found them."""
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
        _set_view(None)
        _set_version_row(*self.saved_version_row)

    def _hide_another_generation(self, kind: str) -> dict[str, Any]:
        """Leave the view and the version row as an update leaves them, and return what
        the planted observation's ``obs_general`` row carries to be hidden.

        Parameters:
            kind: `_PENDING`, a generation begun and pending; `_RETIRED`, a switch
                revertible, its retired rows waiting for the purge.
        """
        _set_view(self.served)
        if kind == _PENDING:
            _set_version_row(self.served + 1, PENDING_WRITING, 0)
            return {ADDED_GENERATION_COLUMN: self.served + 1}
        _set_version_row(None, None, 1)
        return {ADDED_GENERATION_COLUMN: self.served, REMOVED_GENERATION_COLUMN: self.served}

    def _plant(self, kind: str) -> None:
        """Copy the source observation into rows the view does not show, with its child
        rows, once the view and the version row say so.

        Parameters:
            kind: How the copy is hidden, `_PENDING` or `_RETIRED`.
        """
        generations = self._hide_another_generation(kind)
        hidden = self.hidden_id
        _copy_rows(
            OBS_GENERAL_ROWS,
            'id',
            self.source_id,
            {'id': hidden, 'opus_id': _HIDDEN_OPUS_ID, **generations},
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

    def _file_paths(self) -> list[str]:
        """Return the files and product types URLs, of the source observation."""
        return [path.format(opus_id=self.source_opus_id) for path in _FILE_PATHS]

    def _statements(self, paths: list[str]) -> list[str]:
        """Return every statement the URLs run."""
        with CaptureQueriesContext(connection) as queries:
            for path in paths:
                self._get(path)
        return [str(query['sql']) for query in queries.captured_queries]

    def test_the_view_hides_the_planted_observation(self) -> None:
        """The served rows of obs_general do not include the planted copy, either way."""
        for kind in (_PENDING, _RETIRED):
            with self.subTest(kind=kind):
                self._plant(kind)
                with connection.cursor() as cursor:
                    cursor.execute(
                        'SELECT COUNT(*) FROM obs_general WHERE id = %s', [self.hidden_id]
                    )
                    self.assertEqual(cursor.fetchone()[0], 0)
                    cursor.execute(
                        f'SELECT COUNT(*) FROM `{OBS_GENERAL_ROWS}` WHERE id = %s',  # nosec B608
                        [self.hidden_id],
                    )
                    self.assertEqual(cursor.fetchone()[0], 1)
                self._unplant()

    def test_the_empty_searchs_counts_and_endpoints_are_unchanged(self) -> None:
        """Mult counts of a list column and a child's column, and a child's range."""
        before = self._answers(_COUNT_PATHS)
        for kind in (_PENDING, _RETIRED):
            with self.subTest(kind=kind):
                self._plant(kind)
                self.assertEqual(self._answers(_COUNT_PATHS), before)
                self._unplant()

    def test_the_autocomplete_from_every_observation_suggests_the_planted_value(self) -> None:
        """The branch that reads every stored value, as the mult choices do, not the view's."""
        settings.STRINGCHOICE_FULL_SEARCH_COUNT_THRESHOLD = 0
        path = (
            f'/__api/stringsearchchoices/productid.json?productid={_HIDDEN_PRODUCT_ID[:12]}&reqno=1'
        )
        self._plant(_PENDING)
        # Each choice comes back with the typed text in bold.
        answer = self._get(path).replace('<b>', '').replace('</b>', '')
        self.assertIn(_HIDDEN_PRODUCT_ID, answer)

    def test_files_and_product_types_omit_the_planted_files(self) -> None:
        """The served observation's files, under an OPUS ID the hidden copy shares."""
        paths = self._file_paths()
        before = self._answers(paths)
        for kind in (_PENDING, _RETIRED):
            with self.subTest(kind=kind):
                self._plant(kind)
                after = self._answers(paths)
                self.assertEqual(after, before)
                for answer in after.values():
                    self.assertNotIn(_HIDDEN_SHORT_NAME, answer)
                self._unplant()

    def test_no_statement_joins_the_view_while_every_row_is_served(self) -> None:
        """With no generation pending and no switch revertible, every statement is the one
        the schema would get with no generations at all; the version row is still read."""
        _set_version_row(None, None, 0)
        statements = self._statements(_COUNT_PATHS + self._file_paths())
        self.assertEqual([s for s in statements if 'STRAIGHT_JOIN' in s], [])
        self.assertTrue(any(f'FROM `{SCHEMA_VERSION_TABLE}`' in s for s in statements))

    def test_each_child_statement_joins_the_view_while_another_generation_has_rows(
        self,
    ) -> None:
        """A pending generation or a revertible switch adds the join, and nothing else but
        the product types' tie-breaking order, to each statement reading a child table:
        the counts', both of the range's, the files' and both product types'."""
        paths = _COUNT_PATHS + self._file_paths()
        _set_version_row(None, None, 0)
        plain = {path: self._statements([path]) for path in paths}
        for pending, state, revertible in ((self.served + 1, PENDING_WRITING, 0), (None, None, 1)):
            for path in paths:
                with self.subTest(pending=pending, revertible=revertible, path=path):
                    _set_version_row(pending, state, revertible)
                    joined = [s for s in self._statements([path]) if 'STRAIGHT_JOIN' in s]
                    # The range's endpoints and its NULL count are two statements.
                    expected = 2 if '/range/endpoints/' in path else 1
                    self.assertEqual(len(joined), expected, joined)
                    for statement in joined:
                        self.assertEqual(len(_JOIN.findall(statement)), 1, statement)
                        self.assertIn(_without_join(statement), plain[path])
        _set_version_row(*self.saved_version_row)
