"""Tests for the WSGI entry point's schema version check."""

from __future__ import annotations

import threading
from typing import Any

import pytest
from django.db import OperationalError

from opus_app import schema_guard
from opus_import.schema_version import (
    SCHEMA_STATE_APPENDING,
    SCHEMA_STATE_READY,
    SCHEMA_VERSION,
    SCHEMA_VERSION_TABLE,
)

#: What the stand-in application answers.
_SERVED = [b'served']


def _application(environ: dict[str, Any], start_response: Any) -> list[bytes]:
    """Stand in for Django's application."""
    start_response('200 OK', [])
    return _SERVED


def _call(application: Any) -> tuple[str, bytes]:
    """Make one request.

    Parameters:
        application: What the web server would call.

    Returns:
        The status and the body.
    """
    statuses: list[str] = []
    body = b''.join(application({}, lambda status, headers: statuses.append(status)))
    return statuses[0], body


def _reader(rows: list[tuple[Any, ...]]) -> Any:
    """Return a row reader answering `rows`."""
    return lambda: rows


def test_a_matching_ready_row_serves_the_application() -> None:
    """The one row this release accepts."""
    guarded = schema_guard.guard_schema_version(
        _application, _reader([(SCHEMA_VERSION, SCHEMA_STATE_READY)])
    )
    assert guarded is _application
    assert _call(guarded) == ('200 OK', b'served')


@pytest.mark.parametrize(
    'rows',
    [
        [],
        [(SCHEMA_VERSION + 1, SCHEMA_STATE_READY)],
        [(SCHEMA_VERSION, SCHEMA_STATE_APPENDING)],
    ],
    ids=['missing-row', 'other-version', 'appending'],
)
def test_any_other_row_serves_a_503_naming_the_remedy(rows: list[tuple[Any, ...]]) -> None:
    """A missing row, a mismatch and an unfinished schema are each refused."""
    guarded = schema_guard.guard_schema_version(_application, _reader(rows))
    assert guarded is not _application
    status, body = _call(guarded)
    assert status == schema_guard.SCHEMA_REFUSED_STATUS
    assert status.startswith('503')
    assert b'opus_import --write-schema-version' in body


def test_the_stub_answers_every_request_without_raising() -> None:
    """mod_wsgi would reload the module on each request after one that raised."""
    stub = schema_guard.schema_refused_application('the schema has no schema_version row')
    for _ in range(3):
        status, body = _call(stub)
        assert status == schema_guard.SCHEMA_REFUSED_STATUS
        assert body == b'OPUS is unavailable: the schema has no schema_version row.\n'


def test_an_unreachable_database_is_checked_again_on_each_request() -> None:
    """A database down while the application loads is not refused for good."""
    answers: list[Any] = [
        OperationalError('down'),
        OperationalError('still down'),
        [(SCHEMA_VERSION, SCHEMA_STATE_READY)],
    ]
    calls: list[int] = []

    def read() -> list[tuple[Any, ...]]:
        calls.append(1)
        answer = answers.pop(0)
        if isinstance(answer, Exception):
            raise answer
        return answer  # type: ignore[no-any-return]

    guarded = schema_guard.guard_schema_version(_application, read)
    status, body = _call(guarded)
    assert status == schema_guard.SCHEMA_REFUSED_STATUS
    assert b'down' not in body
    assert _call(guarded) == ('200 OK', b'served')
    assert _call(guarded) == ('200 OK', b'served')
    assert len(calls) == 3


def test_a_refused_schema_is_served_once_it_is_finished() -> None:
    """A worker that loaded before the version step serves the schema without a reload."""
    answers: list[list[tuple[Any, ...]]] = [
        [],
        [(SCHEMA_VERSION, SCHEMA_STATE_APPENDING)],
        [(SCHEMA_VERSION, SCHEMA_STATE_READY)],
    ]
    calls: list[int] = []

    def read() -> list[tuple[Any, ...]]:
        calls.append(1)
        return answers.pop(0)

    guarded = schema_guard.guard_schema_version(_application, read)
    status, body = _call(guarded)
    assert status == schema_guard.SCHEMA_REFUSED_STATUS
    assert b"'appending'" in body
    assert _call(guarded) == ('200 OK', b'served')
    assert _call(guarded) == ('200 OK', b'served')
    assert len(calls) == 3


def test_a_refused_schema_is_refused_on_every_request_until_then() -> None:
    """Each refused request checks again, and says what is wrong now."""
    guarded = schema_guard.guard_schema_version(
        _application, _reader([(SCHEMA_VERSION + 1, SCHEMA_STATE_READY)])
    )
    for _ in range(3):
        status, body = _call(guarded)
        assert status == schema_guard.SCHEMA_REFUSED_STATUS
        assert f'version {SCHEMA_VERSION + 1}'.encode() in body


class _FakeCursor:
    """A cursor answering the version query."""

    def __init__(self, connection: _FakeConnection) -> None:
        self._connection = connection

    def __enter__(self) -> _FakeCursor:
        return self

    def __exit__(self, *exc: object) -> None:
        return None

    def execute(self, statement: str) -> None:
        if self._connection.fail:
            raise OperationalError('lost')
        self._connection.statements.append(statement)

    def fetchall(self) -> list[tuple[Any, ...]]:
        return [(SCHEMA_VERSION, SCHEMA_STATE_READY)]


class _FakeConnection:
    """Django's connection, as `schema_guard.read_schema_version_rows` uses it."""

    def __init__(self, *, has_table: bool, fail: bool = False) -> None:
        self.fail = fail
        self.closed = 0
        self.statements: list[str] = []
        tables = ['schema_version'] if has_table else ['obs_general']
        self.introspection = type('Introspection', (), {'table_names': lambda _, c: tables})()

    def cursor(self) -> _FakeCursor:
        return _FakeCursor(self)

    def close(self) -> None:
        self.closed += 1


@pytest.mark.parametrize(
    ('has_table', 'fail', 'expected'),
    [
        (True, False, [(SCHEMA_VERSION, SCHEMA_STATE_READY)]),
        (False, False, []),
        (True, True, None),
    ],
    ids=['row', 'no-table', 'database-error'],
)
def test_read_rows_closes_the_connection_however_it_ends(
    monkeypatch: pytest.MonkeyPatch, has_table: bool, fail: bool, expected: Any
) -> None:
    """The connection was opened while loading, in a thread no request runs on."""
    fake = _FakeConnection(has_table=has_table, fail=fail)
    monkeypatch.setattr(schema_guard, 'connection', fake)
    if expected is None:
        with pytest.raises(OperationalError):
            schema_guard.read_schema_version_rows()
    else:
        assert schema_guard.read_schema_version_rows() == expected
    assert fake.closed == 1


def test_a_request_during_a_stalled_check_is_refused_without_waiting() -> None:
    """One stuck read holds one thread; the others are answered 503 at once."""
    reading = threading.Event()
    release = threading.Event()
    answers: list[list[tuple[Any, ...]]] = [[], [(SCHEMA_VERSION, SCHEMA_STATE_READY)]]

    def read() -> list[tuple[Any, ...]]:
        rows = answers.pop(0)
        if len(answers) == 0:
            reading.set()
            assert release.wait(5)
        return rows

    guarded = schema_guard.guard_schema_version(_application, read)
    stalled: list[tuple[str, bytes]] = []
    thread = threading.Thread(target=lambda: stalled.append(_call(guarded)))
    thread.start()
    assert reading.wait(5)

    status, body = _call(guarded)
    assert status == schema_guard.SCHEMA_REFUSED_STATUS
    assert f'no {SCHEMA_VERSION_TABLE} row'.encode() in body

    release.set()
    thread.join(5)
    assert stalled == [('200 OK', b'served')]
    assert _call(guarded) == ('200 OK', b'served')
