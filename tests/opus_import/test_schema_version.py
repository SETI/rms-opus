"""Tests for the schema version constant's checks and the step that writes the row."""

from __future__ import annotations

import os
import subprocess  # nosec B404
import sys
from collections.abc import Sequence
from typing import Any

import pytest

from opus_config import OPUS_CONFIG_ENV_VAR
from opus_import.schema_version import (
    SCHEMA_STATE_APPENDING,
    SCHEMA_STATE_READY,
    SCHEMA_VERSION,
    SCHEMA_VERSION_REMEDY,
    SCHEMA_VERSION_TABLE,
    schema_version_problem,
)
from opus_import.steps import do_import_tables, do_schema_version
from tests.opus_import.conftest import RecordingLogger, make_context

#: Prints which of the heavier packages importing the module loaded.
_IMPORTED_PACKAGES = (
    'import sys\n'
    'import opus_import.schema_version\n'
    "print(sorted({m.split('.')[0] for m in sys.modules} & "
    "{'django', 'opus_config', 'MySQLdb', 'pdslogger'}))\n"
)


class _VersionDB:
    """An `ImportDBSuper` stand-in holding one schema's ``schema_version`` table."""

    def __init__(self, rows: list[tuple[Any, ...]] | None) -> None:
        """Hold the table's rows, or None for no table.

        Parameters:
            rows: The ``(version, state)`` rows.
        """
        self.rows = None if rows is None else list(rows)
        self.created: list[str] = []
        self.dropped: list[str] = []

    def table_exists(self, table_name: str) -> bool:
        """Answer for the version table only."""
        return table_name == SCHEMA_VERSION_TABLE and self.rows is not None

    def read_rows(self, table_name: str, columns: Sequence[str]) -> list[Any]:
        """Return the rows."""
        assert (table_name, list(columns)) == (
            SCHEMA_VERSION_TABLE,
            ['version', 'state'],
        )
        assert self.rows is not None
        return list(self.rows)

    def create_table(self, table_name: str, schema: Any, *, ignore_if_exists: bool) -> None:
        """Create the empty table from the packaged schema."""
        assert [column['field_name'] for column in schema] == ['version', 'state']
        self.created.append(table_name)
        self.rows = []

    def insert_row(self, table_name: str, row: dict[str, Any]) -> None:
        """Append a row."""
        assert self.rows is not None
        self.rows.append((row['version'], row['state']))

    def update_row(
        self,
        table_name: str,
        row: dict[str, Any],
        where: str,
        where_params: Sequence[Any],
    ) -> None:
        """Set the state of the row whose version matches."""
        assert self.rows is not None
        self.rows = [
            (version, row['state']) if version == where_params[0] else (version, state)
            for version, state in self.rows
        ]

    def quote_identifier(self, name: str) -> str:
        """Quote as MySQL does."""
        return f'`{name}`'

    def drop_table(self, table_name: str) -> None:
        """Record the drop."""
        self.dropped.append(table_name)

    def table_names(self) -> list[str]:
        """Report the tables an erase drops: the version table, while it exists, and others."""
        version = [SCHEMA_VERSION_TABLE] if self.rows is not None else []
        return [*version, 'obs_general', 'obs_pds', 'cart', 'mult_obs_general_planet_id']


def _write(rows: list[tuple[Any, ...]] | None) -> tuple[bool, _VersionDB, RecordingLogger]:
    """Run the step against a table holding `rows`.

    Parameters:
        rows: The table's rows, or None for no table.

    Returns:
        What the step returned, the table afterwards, and what it logged.
    """
    db = _VersionDB(rows)
    logger = RecordingLogger()
    ctx = make_context(db=db, logger=logger)
    return do_schema_version.write_schema_version(ctx), db, logger


@pytest.mark.parametrize(
    ('rows', 'expected'),
    [
        ([(SCHEMA_VERSION, SCHEMA_STATE_READY)], None),
        ([], f'the schema has no {SCHEMA_VERSION_TABLE} row'),
        ([(SCHEMA_VERSION + 1, SCHEMA_STATE_READY)], f'the schema is version {SCHEMA_VERSION + 1}'),
        ([(SCHEMA_VERSION, SCHEMA_STATE_APPENDING)], "the schema's state is 'appending'"),
        (
            [(SCHEMA_VERSION, SCHEMA_STATE_READY), (SCHEMA_VERSION + 1, SCHEMA_STATE_READY)],
            f'the schema has 2 {SCHEMA_VERSION_TABLE} rows',
        ),
    ],
    ids=['match', 'missing', 'other-version', 'appending', 'two-rows'],
)
def test_problem_names_what_keeps_a_schema_from_being_served(
    rows: list[tuple[Any, ...]], expected: str | None
) -> None:
    """Only one row, this version, ``ready``, passes; anything else names the remedy."""
    found = schema_version_problem(rows)
    if expected is None:
        assert found is None
    else:
        assert found is not None
        assert found.startswith(expected)
        assert found.endswith(SCHEMA_VERSION_REMEDY)
        assert '--write-schema-version' in found


def test_with_no_table_the_step_creates_it_and_writes_this_version_ready() -> None:
    """A schema with no version table is one the step finishes."""
    written, db, logger = _write(None)
    assert written
    assert db.created == [SCHEMA_VERSION_TABLE]
    assert db.rows == [(SCHEMA_VERSION, SCHEMA_STATE_READY)]
    assert logger.messages_at('error') == []


def test_an_empty_table_gets_the_row() -> None:
    """An empty table is a missing row, not a refusal."""
    written, db, _ = _write([])
    assert written
    assert db.created == []
    assert db.rows == [(SCHEMA_VERSION, SCHEMA_STATE_READY)]


def test_an_appending_row_of_this_version_becomes_ready_logged_at_info() -> None:
    """The step finishes an append."""
    written, db, logger = _write([(SCHEMA_VERSION, SCHEMA_STATE_APPENDING)])
    assert written
    assert db.rows == [(SCHEMA_VERSION, SCHEMA_STATE_READY)]
    assert any(SCHEMA_STATE_APPENDING in message for message in logger.messages_at('info'))


def test_a_ready_row_of_this_version_is_left_alone_logged_at_debug() -> None:
    """Running the step twice changes nothing."""
    written, db, logger = _write([(SCHEMA_VERSION, SCHEMA_STATE_READY)])
    assert written
    assert db.rows == [(SCHEMA_VERSION, SCHEMA_STATE_READY)]
    assert logger.messages_at('info') == []
    assert any('already' in message for message in logger.messages_at('debug'))


@pytest.mark.parametrize('state', [SCHEMA_STATE_READY, SCHEMA_STATE_APPENDING])
def test_another_version_is_refused_with_an_error_and_left_as_it_is(state: str) -> None:
    """New code never stamps an old schema, whatever its state."""
    other = (SCHEMA_VERSION + 1, state)
    written, db, logger = _write([other])
    assert not written
    assert db.rows == [other]
    errors = logger.messages_at('error')
    assert len(errors) == 1
    assert f'version {SCHEMA_VERSION + 1}' in errors[0]


def test_more_than_one_row_is_refused() -> None:
    """The table holds one row; the step does not choose between several."""
    rows = [(SCHEMA_VERSION, SCHEMA_STATE_READY), (SCHEMA_VERSION + 1, SCHEMA_STATE_READY)]
    written, db, logger = _write(rows)
    assert not written
    assert db.rows == rows
    assert len(logger.messages_at('error')) == 1


def test_the_erase_drops_the_version_table_before_any_other() -> None:
    """An erase that stops part way leaves no version row."""
    db = _VersionDB([(SCHEMA_VERSION, SCHEMA_STATE_READY)])
    do_import_tables.delete_all_opus_tables(make_context(db=db))
    assert db.dropped[0] == SCHEMA_VERSION_TABLE
    assert set(db.dropped[1:]) == {'obs_general', 'obs_pds', 'cart', 'mult_obs_general_planet_id'}


def test_the_module_imports_neither_django_nor_the_configuration() -> None:
    """Both halves and the deploy check import it, with no configuration set."""
    environment = {key: value for key, value in os.environ.items() if key != OPUS_CONFIG_ENV_VAR}
    finished = subprocess.run(  # nosec B603 - this interpreter and a fixed program
        [sys.executable, '-c', _IMPORTED_PACKAGES],
        env=environment,
        capture_output=True,
        text=True,
        check=True,
    )
    assert finished.stdout.strip() == '[]'


def test_a_state_neither_ready_nor_appending_is_refused() -> None:
    """A row the step did not write is not taken for a finished schema."""
    written, db, logger = _write([(SCHEMA_VERSION, '')])
    assert not written
    assert db.rows == [(SCHEMA_VERSION, '')]
    assert len(logger.messages_at('error')) == 1
