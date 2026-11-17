"""Tests for `opus_app.apps.tools.db_utils.unserved_observations_exist`.

The web application joins a child table's rows to the served observations only while the
version row says the schema holds another generation's rows. These tests read the row
through a stand-in for Django's connection, so they need no database; the statements that
hang the join are checked against a database by
``integration_tests/apps_db_tests/test_generations.py``.
"""

from __future__ import annotations

from typing import Any

import pytest
from django.db import OperationalError, ProgrammingError

from opus_app.apps.tools import db_utils


class _Cursor:
    """A cursor answering the version row's query from its connection."""

    def __init__(self, connection: _Connection) -> None:
        self._connection = connection

    def __enter__(self) -> _Cursor:
        return self

    def __exit__(self, *exc: object) -> None:
        return None

    def execute(self, statement: str, params: list[Any]) -> None:
        self._connection.statements.append((statement, params))
        if self._connection.error is not None:
            raise self._connection.error

    def fetchall(self) -> list[tuple[Any, ...]]:
        return list(self._connection.rows)


class _Connection:
    """Django's connection, as `unserved_observations_exist` uses it."""

    def __init__(
        self, rows: list[tuple[Any, ...]] | None = None, error: Exception | None = None
    ) -> None:
        self.rows = rows or []
        self.error = error
        self.statements: list[tuple[str, list[Any]]] = []

    def cursor(self) -> _Cursor:
        return _Cursor(self)


@pytest.mark.parametrize(
    ('rows', 'expected'),
    [
        ([(None, 0)], False),
        ([(3, 0)], True),
        ([(None, 1)], True),
        ([(3, 1)], True),
        ([], False),
    ],
    ids=['one-generation', 'pending', 'revertible', 'both', 'no-row'],
)
def test_the_version_row_says_whether_another_generation_has_rows(
    monkeypatch: pytest.MonkeyPatch, rows: list[tuple[Any, ...]], expected: bool
) -> None:
    """A pending generation or a revertible switch; neither, or no row, is one generation."""
    connection = _Connection(rows)
    monkeypatch.setattr(db_utils, 'connection', connection)
    assert db_utils.unserved_observations_exist() is expected
    assert connection.statements == [
        ('SELECT `pending_generation`,`revertible` FROM `schema_version`', [])
    ]


def test_a_schema_without_a_version_table_has_one_generation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """MySQL's error 1146, a table that does not exist, joins nothing."""
    error = ProgrammingError(
        db_utils.MYSQL_TABLE_NOT_EXISTS, "Table 'schema_version' doesn't exist"
    )
    monkeypatch.setattr(db_utils, 'connection', _Connection(error=error))
    assert db_utils.unserved_observations_exist() is False


def test_any_other_database_error_is_raised(monkeypatch: pytest.MonkeyPatch) -> None:
    """A version table that cannot be read is not taken to mean one generation."""
    monkeypatch.setattr(db_utils, 'connection', _Connection(error=OperationalError(2013, 'lost')))
    with pytest.raises(OperationalError):
        db_utils.unserved_observations_exist()


def test_the_row_is_read_again_on_every_call(monkeypatch: pytest.MonkeyPatch) -> None:
    """A begin runs while the site serves, so no answer is kept between requests."""
    connection = _Connection([(None, 0)])
    monkeypatch.setattr(db_utils, 'connection', connection)
    assert db_utils.unserved_observations_exist() is False
    connection.rows = [(2, 0)]
    assert db_utils.unserved_observations_exist() is True
    connection.rows = [(None, 1)]
    assert db_utils.unserved_observations_exist() is True
    connection.rows = [(None, 0)]
    assert db_utils.unserved_observations_exist() is False
    assert len(connection.statements) == 4
