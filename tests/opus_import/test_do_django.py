"""The reset of the search tables: what it re-creates, the ids it hands out, the flush.

The web application's cache names searches by their ``user_searches`` ids, so what is
worth pinning is that a reset never lets an old id name a new search, and that a flush
that fails fails the step.
"""

from __future__ import annotations

import subprocess  # nosec B404 - only the type of a faked result
from typing import Any

import pytest

from opus_import.steps import do_django

from .conftest import make_context


class _ResettingDB:
    """A stand-in recording what the reset does to the tables."""

    def __init__(self, last_id: int | None, *, exists: bool = True, read_only: bool = False):
        """Hold the old table's highest id, whether it exists, and the run's mode."""
        self.last_id = last_id
        self.exists = exists
        self.read_only = read_only
        self.events: list[tuple[Any, ...]] = []

    def table_exists(self, table_name: str) -> bool:
        """Say whether ``user_searches`` exists before the reset."""
        assert table_name == 'user_searches'
        return self.exists

    def find_column_max(self, table_name: str, column_name: str) -> int | None:
        """Return the old table's highest id."""
        assert (table_name, column_name) == ('user_searches', 'id')
        return self.last_id

    def drop_table(self, table_name: str) -> None:
        """Record a drop."""
        self.events.append(('drop', table_name))

    def create_table(self, table_name: str, schema: Any) -> bool:
        """Record a create."""
        self.events.append(('create', table_name))
        return True

    def set_next_id(self, table_name: str, next_id: int) -> None:
        """Record where the ids start."""
        self.events.append(('next_id', table_name, next_id))


def _flush(monkeypatch: pytest.MonkeyPatch, returncode: int) -> list[Any]:
    """Make the flush subprocess exit with a status, recording each command it runs."""
    commands: list[Any] = []

    def run(command: Any, **kwargs: Any) -> subprocess.CompletedProcess[str]:
        commands.append(command)
        return subprocess.CompletedProcess(command, returncode, '', 'no cache')

    monkeypatch.setattr(subprocess, 'run', run)
    return commands


def test_the_tables_are_recreated_and_ids_continue_above_the_old_ones(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An id a request in flight cached before the reset names no new search."""
    commands = _flush(monkeypatch, 0)
    db = _ResettingDB(last_id=500)
    do_django.reset_search_tables(make_context(db=db))
    assert db.events == [
        ('drop', 'user_searches'),
        ('create', 'user_searches'),
        ('drop', 'search_results'),
        ('create', 'search_results'),
        ('next_id', 'user_searches', 501),
    ]
    assert commands == [do_django.CACHE_FLUSH_COMMAND]


@pytest.mark.parametrize(('last_id', 'exists'), [(None, True), (None, False)])
def test_an_empty_or_absent_table_leaves_the_ids_where_they_start(
    monkeypatch: pytest.MonkeyPatch, last_id: int | None, exists: bool
) -> None:
    """With no old id there is nothing to stay above."""
    _flush(monkeypatch, 0)
    db = _ResettingDB(last_id=last_id, exists=exists)
    do_django.reset_search_tables(make_context(db=db))
    assert not any(event[0] == 'next_id' for event in db.events)


def test_a_failed_flush_fails_the_step(monkeypatch: pytest.MonkeyPatch) -> None:
    """A cache that may still name old searches is an error, not a warning."""
    _flush(monkeypatch, 1)
    with pytest.raises(do_django.CacheFlushError, match='status 1: no cache'):
        do_django.reset_search_tables(make_context(db=_ResettingDB(last_id=None)))


def test_a_simulated_run_flushes_nothing(monkeypatch: pytest.MonkeyPatch) -> None:
    """A read-only run changes nothing outside the database it only pretends to change."""
    commands = _flush(monkeypatch, 1)
    do_django.reset_search_tables(make_context(db=_ResettingDB(last_id=None, read_only=True)))
    assert commands == []
