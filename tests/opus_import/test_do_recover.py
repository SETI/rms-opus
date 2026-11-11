"""Returning a dead importer's bundle, and an importer's own release of its bundle.

Driven against a stand-in holding the registry and the importers' table, the locks the
server would report, and the registry rows another session holds; the bundle's delete is
recorded rather than run.
"""

from __future__ import annotations

import contextlib
import re
from collections.abc import Iterator
from typing import Any

import pytest

from opus_import import import_processes
from opus_import.steps import do_import_tables, do_recover

from .conftest import make_context


class _QueueDB:
    """The registry and the importers, the locks held, and the rows another session holds.

    Attributes:
        tables: Each table's rows.
        holders: The connection holding each importer's lock, by ``process_id``.
        locked_elsewhere: The bundle numbers whose registry row another session holds.
        held: The bundle numbers this stand-in's transactions hold, while they run.
        deleted: The bundles deleted, with the bundle rows held at the time.
    """

    db_schema = 'opus_test'

    def __init__(self, bundles: list[dict[str, Any]], processes: list[dict[str, Any]]) -> None:
        self.tables = {'import_bundle': bundles, 'import_process': processes}
        self.holders: dict[int, int | None] = {}
        self.locked_elsewhere: set[int] = set()
        self.held: set[int] = set()
        self.deleted: list[tuple[str, set[int]]] = []

    def table_exists(self, table_name: str) -> bool:
        return table_name in self.tables

    def forget_table_names(self) -> None:
        """Nothing is cached: every table is read where it is held."""

    def quote_identifier(self, name: str) -> str:
        return f'`{name}`'

    @staticmethod
    def _selects(row: dict[str, Any], where: str, params: list[Any]) -> bool:
        """Whether a row meets a conjunction of ```col`=%s`` and ```col` IS [NOT] NULL``."""
        values = iter(params)
        for term in where.split(' AND '):
            column = re.match(r'`(\w+)`', term)
            assert column is not None
            value = row[column[1]]
            if term.endswith('IS NOT NULL'):
                matched = value is not None
            elif term.endswith('IS NULL'):
                matched = value is None
            else:
                matched = value == next(values)
            if not matched:
                return False
        return True

    def read_rows(
        self, table_name: str, columns: list[str], where: str, params: list[Any]
    ) -> list[tuple[Any, ...]]:
        rows = self.tables[table_name]
        return [tuple(r[c] for c in columns) for r in rows if self._selects(r, where, params)]

    def update_row(
        self, table_name: str, row: dict[str, Any], where: str, params: list[Any]
    ) -> int:
        values = list(row.values())
        matched = [r for r in self.tables[table_name] if self._selects(r, where, params)]
        for existing in matched:
            existing.update(zip(row.keys(), values, strict=True))
        return len(matched)

    def lock_row(
        self, table_name: str, columns: list[str], where: str, params: list[Any]
    ) -> tuple[Any, ...] | None:
        if params[0] in self.locked_elsewhere:
            return None
        rows = self.read_rows(table_name, columns, where, params)
        if rows:
            self.held.add(params[0])
        return rows[0] if rows else None

    def named_lock_holder(self, name: str) -> int | None:
        for process_id, holder in self.holders.items():
            if name == import_processes.importer_lock_name(self.db_schema, process_id):
                return holder
        return None

    @contextlib.contextmanager
    def transaction(self) -> Iterator[None]:
        try:
            yield
        finally:
            self.held.clear()

    def open_sibling_connection(self) -> _QueueDB:
        return self

    def close(self) -> None:
        return None

    def bundle(self, bundle_id: str) -> dict[str, Any]:
        """Return a bundle's registry row."""
        (row,) = [r for r in self.tables['import_bundle'] if r['bundle_id'] == bundle_id]
        return row

    def process(self, process_id: int) -> dict[str, Any]:
        """Return an importer's row."""
        (row,) = [r for r in self.tables['import_process'] if r['process_id'] == process_id]
        return row


def _bundle(number: int, state: str, process_id: int | None, losses: int = 0) -> dict[str, Any]:
    return {
        'bundle_number': number,
        'bundle_id': f'B_{number}',
        'state': state,
        'process_id': process_id,
        'losses': losses,
        'rows_done': 7,
        'started_at': 'then',
        'finished_at': None,
    }


def _process(process_id: int, state: str = 'running') -> dict[str, Any]:
    return {'process_id': process_id, 'state': state}


@pytest.fixture
def queue(monkeypatch: pytest.MonkeyPatch) -> _QueueDB:
    """Importer 1, dead, holding bundle 1; importer 2, alive, holding bundle 2."""
    db = _QueueDB(
        [_bundle(1, 'importing', 1), _bundle(2, 'importing', 2), _bundle(3, 'pending', None)],
        [_process(1), _process(2)],
    )
    db.holders = {1: None, 2: 55}
    monkeypatch.setattr(
        do_import_tables,
        'delete_bundle_from_obs_tables',
        lambda ctx, bundle: db.deleted.append((bundle, set(db.held))),
    )
    return db


def test_a_dead_importers_bundle_is_deleted_under_its_row_lock_and_requeued(
    queue: _QueueDB,
) -> None:
    """Its rows go while its registry row is held; it is pending with one loss, and the
    importer is lost. The live importer's bundle is not touched."""
    done = do_recover.recover_lost_importers(make_context(db=queue))

    assert queue.deleted == [('B_1', {1})]
    assert queue.bundle('B_1') == {
        **_bundle(1, 'pending', None, losses=1),
        'rows_done': 0,
        'started_at': None,
    }
    assert queue.bundle('B_2')['state'] == 'importing'
    assert queue.process(1)['state'] == 'lost'
    assert queue.process(2)['state'] == 'running'
    assert done == [
        'B_1 returned to the queue: importer 1 died holding it',
        'importer 1 is lost: its lock is free',
    ]


def test_a_bundle_lost_twice_fails_keeping_its_importer(queue: _QueueDB) -> None:
    """The second loss records it failed, naming the importer whose log says why."""
    queue.bundle('B_1')['losses'] = 1

    do_recover.recover_lost_importers(make_context(db=queue))

    assert queue.bundle('B_1')['state'] == 'failed'
    assert queue.bundle('B_1')['losses'] == 2
    assert queue.bundle('B_1')['process_id'] == 1


def test_a_row_another_session_holds_is_left_for_a_later_pass(queue: _QueueDB) -> None:
    """The importer's own abort, or another coordinator, is acting on it: nothing is
    deleted, and the importer is not yet marked lost."""
    queue.locked_elsewhere = {1}

    assert do_recover.recover_lost_importers(make_context(db=queue)) == []

    assert queue.deleted == []
    assert queue.bundle('B_1')['state'] == 'importing'
    assert queue.process(1)['state'] == 'running'


def test_a_recovery_run_again_changes_nothing(queue: _QueueDB) -> None:
    """Idempotent: the second pass finds no bundle and no running importer to act on."""
    do_recover.recover_lost_importers(make_context(db=queue))
    queue.deleted.clear()

    assert do_recover.recover_lost_importers(make_context(db=queue)) == []
    assert queue.deleted == []


def test_an_exited_importers_stranded_bundle_is_returned_too(queue: _QueueDB) -> None:
    """A bundle still importing under an importer that exited is free to return."""
    queue.process(1)['state'] = 'exited'

    do_recover.recover_lost_importers(make_context(db=queue))

    assert queue.bundle('B_1')['state'] == 'pending'
    assert queue.process(1)['state'] == 'exited'


@pytest.mark.parametrize(
    ('state', 'after'), [('pending', 'pending'), ('failed', 'failed'), (None, 'importing')]
)
def test_an_importer_releases_its_bundle_under_its_row_lock(
    state: str | None, after: str, queue: _QueueDB
) -> None:
    """An abort returns it, a failure fails it (keeping the importer), and the delete
    before an import leaves it importing; each deletes while the row is held."""
    assert do_recover.release_bundle(make_context(db=queue), 'B_2', 2, 2, state)

    assert queue.deleted == [('B_2', {2})]
    assert queue.bundle('B_2')['state'] == after
    assert queue.bundle('B_2')['process_id'] == (None if after == 'pending' else 2)


def test_a_bundle_that_left_the_importer_is_not_released(queue: _QueueDB) -> None:
    """Requeued by a recovery and claimed since, or held by another session: nothing is
    deleted, so another importer's rows are safe."""
    queue.bundle('B_2')['process_id'] = 5
    assert not do_recover.release_bundle(make_context(db=queue), 'B_2', 2, 2, 'pending')
    queue.bundle('B_2')['process_id'] = 2
    queue.locked_elsewhere = {2}
    assert not do_recover.release_bundle(make_context(db=queue), 'B_2', 2, 2, 'pending')
    assert queue.deleted == []
    assert queue.bundle('B_2')['state'] == 'importing'
