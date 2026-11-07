"""Tests for the WSGI entry point's schema version check."""

from __future__ import annotations

from typing import Any

import pytest
from django.db import OperationalError

from opus_app import schema_guard
from opus_import.schema_version import SCHEMA_VERSION, STATE_APPENDING, STATE_READY

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
    guarded = schema_guard.guard(_application, _reader([(SCHEMA_VERSION, STATE_READY)]))
    assert guarded is _application
    assert _call(guarded) == ('200 OK', b'served')


@pytest.mark.parametrize(
    'rows',
    [
        [],
        [(SCHEMA_VERSION + 1, STATE_READY)],
        [(SCHEMA_VERSION, STATE_APPENDING)],
    ],
    ids=['missing-row', 'other-version', 'appending'],
)
def test_any_other_row_serves_a_503_naming_the_remedy(rows: list[tuple[Any, ...]]) -> None:
    """A missing row, a mismatch and an unfinished schema are each refused."""
    guarded = schema_guard.guard(_application, _reader(rows))
    assert guarded is not _application
    status, body = _call(guarded)
    assert status == schema_guard.UNAVAILABLE_STATUS
    assert status.startswith('503')
    assert b'opus_import --write-schema-version' in body


def test_the_stub_answers_every_request_without_raising() -> None:
    """mod_wsgi would reload the module on each request after one that raised."""
    stub = schema_guard.unavailable('the schema has no schema_version row')
    for _ in range(3):
        status, body = _call(stub)
        assert status == schema_guard.UNAVAILABLE_STATUS
        assert body == b'OPUS is unavailable: the schema has no schema_version row.\n'


def test_an_unreachable_database_is_checked_again_on_each_request() -> None:
    """A database down while the application loads is not refused for good."""
    answers: list[Any] = [
        OperationalError('down'),
        OperationalError('still down'),
        [(SCHEMA_VERSION, STATE_READY)],
    ]
    calls: list[int] = []

    def read() -> list[tuple[Any, ...]]:
        calls.append(1)
        answer = answers.pop(0)
        if isinstance(answer, Exception):
            raise answer
        return answer  # type: ignore[no-any-return]

    guarded = schema_guard.guard(_application, read)
    status, body = _call(guarded)
    assert status == schema_guard.UNAVAILABLE_STATUS
    assert b'down' not in body
    assert _call(guarded) == ('200 OK', b'served')
    assert _call(guarded) == ('200 OK', b'served')
    assert len(calls) == 3


def test_once_reached_a_refusing_database_stays_refused() -> None:
    """The check that finally answers decides every later request too."""
    answers: list[Any] = [OperationalError('down'), [(SCHEMA_VERSION + 1, STATE_READY)]]

    def read() -> list[tuple[Any, ...]]:
        answer = answers.pop(0)
        if isinstance(answer, Exception):
            raise answer
        return answer  # type: ignore[no-any-return]

    guarded = schema_guard.guard(_application, read)
    for _ in range(3):
        status, body = _call(guarded)
        assert status == schema_guard.UNAVAILABLE_STATUS
    assert b'version' in body
