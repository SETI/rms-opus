"""The statements a swap sends, for each table set the import rebuilds that way.

No connection is opened: the backend is `ImportDBMySQL` with its statements recorded
instead of run, so these pin the SQL itself -- the ``__new`` tables created, the one
``RENAME TABLE`` that swaps them in, and the drops either side of it.
"""

from __future__ import annotations

from typing import Any

import pytest

from opus_import import import_fault, table_swap
from opus_import.importdb.super import ImportDBError, ImportDBSuper

from .conftest import make_context

MySQLdb = pytest.importorskip('MySQLdb')

from opus_import.importdb.mysql import ImportDBMySQL  # noqa: E402 - follows the skip

#: The lock timeout the recording server reports as the session's own.
_SESSION_LOCK_WAIT_TIMEOUT = 31536000


class _RecordingDB(ImportDBMySQL):
    """An ImportDBMySQL that records statements, over a schema holding `tables`."""

    def __init__(self, tables: set[str], lock_timeouts: int = 0) -> None:
        # Deliberately skips ImportDBMySQL.__init__, which connects to a server.
        ImportDBSuper.__init__(self, 'host', 'db', 'schema', 'user', 'password', logger=None)
        self._table_names = set(tables)
        self._table_info_cache = {}
        self.default_engine = 'INNODB'
        self.executed: list[tuple[str, Any]] = []
        self._lock_timeouts = lock_timeouts

    def _execute(
        self, cmd: str, param_list: Any = None, cur: Any = None, mutates: bool = False
    ) -> None:
        self.executed.append((cmd, param_list))
        if cmd.startswith('RENAME TABLE') and self._lock_timeouts > 0:
            self._lock_timeouts -= 1
            raise MySQLdb.OperationalError(1205, 'Lock wait timeout exceeded')

    def _execute_and_fetchall(
        self, cmd: str, func_name: str, param_list: Any = None
    ) -> list[tuple[Any, ...]]:
        assert cmd == 'SELECT @@SESSION.lock_wait_timeout'
        return [(_SESSION_LOCK_WAIT_TIMEOUT,)]

    def statements(self, prefix: str) -> list[str]:
        """Return the statements that start with `prefix`, each on one line."""
        return [' '.join(cmd.split()) for cmd, _ in self.executed if cmd.startswith(prefix)]


def _swap(db: _RecordingDB, tables: list[str], fill: Any = None) -> bool:
    """Rebuild `tables` by swap against `db`, with a fill that writes nothing."""
    ctx = make_context(db=db)
    return table_swap.rebuild_tables_by_swap(ctx, tables, fill or (lambda: True))


@pytest.mark.parametrize('table', ['param_info', 'partables', 'table_names'])
def test_an_aux_table_is_built_beside_the_live_one_and_swapped_in(table: str) -> None:
    """One ``__new`` table, one rename that moves the live table aside, one drop."""
    db = _RecordingDB({table})

    assert _swap(db, [table]) is True

    assert [cmd.split(' (')[0] for cmd in db.statements('CREATE TABLE')] == [
        f'CREATE TABLE `{table}__new`'
    ]
    assert db.statements('RENAME TABLE') == [
        f'RENAME TABLE `{table}` TO `{table}__old`, `{table}__new` TO `{table}`'
    ]
    assert db.statements('DROP TABLE') == [f'DROP TABLE `{table}__old`']
    assert db.table_exists('perm', table)
    assert not db.table_exists('perm', f'{table}__new')
    assert not db.table_exists('perm', f'{table}__old')


def test_the_dictionary_swaps_both_tables_in_one_rename() -> None:
    """``contexts`` and ``definitions`` change together, and the foreign key follows."""
    db = _RecordingDB({'contexts', 'definitions'})

    assert _swap(db, ['contexts', 'definitions']) is True

    creates = db.statements('CREATE TABLE')
    assert [cmd.split(' (')[0] for cmd in creates] == [
        'CREATE TABLE `contexts__new`',
        'CREATE TABLE `definitions__new`',
    ]
    assert 'REFERENCES `contexts__new`(`name`)' in creates[1]
    assert db.statements('RENAME TABLE') == [
        'RENAME TABLE `contexts` TO `contexts__old`, `contexts__new` TO `contexts`, '
        '`definitions` TO `definitions__old`, `definitions__new` TO `definitions`'
    ]
    # The child first, which the foreign key between the old pair requires.
    assert db.statements('DROP TABLE') == [
        'DROP TABLE `definitions__old`',
        'DROP TABLE `contexts__old`',
    ]


def test_a_table_with_no_live_copy_is_renamed_into_place() -> None:
    """A fresh schema has nothing to move aside, and nothing to drop afterwards."""
    db = _RecordingDB(set())

    assert _swap(db, ['param_info']) is True

    assert db.statements('RENAME TABLE') == ['RENAME TABLE `param_info__new` TO `param_info`']
    assert db.statements('DROP TABLE') == []


def test_leftovers_of_an_interrupted_rebuild_are_dropped_first() -> None:
    """Children before parents, ``__new`` and then ``__old``."""
    db = _RecordingDB(
        {
            'contexts',
            'definitions',
            'contexts__new',
            'definitions__new',
            'contexts__old',
            'definitions__old',
        }
    )

    assert _swap(db, ['contexts', 'definitions']) is True

    assert db.statements('DROP TABLE')[:4] == [
        'DROP TABLE `definitions__new`',
        'DROP TABLE `contexts__new`',
        'DROP TABLE `definitions__old`',
        'DROP TABLE `contexts__old`',
    ]


def test_a_failed_fill_leaves_the_live_table_alone() -> None:
    """The ``__new`` table is dropped again, and nothing is renamed."""
    db = _RecordingDB({'param_info'})

    assert _swap(db, ['param_info'], fill=lambda: False) is False

    assert db.statements('RENAME TABLE') == []
    assert db.statements('DROP TABLE') == ['DROP TABLE `param_info__new`']
    assert db.table_exists('perm', 'param_info')


def test_the_rename_runs_under_a_short_lock_wait_and_restores_it() -> None:
    """The session's own ``lock_wait_timeout`` is put back after the rename."""
    db = _RecordingDB({'partables'})

    _swap(db, ['partables'])

    sets = [(cmd, params) for cmd, params in db.executed if cmd.startswith('SET SESSION')]
    assert sets == [
        ('SET SESSION lock_wait_timeout = %s', [table_swap.SWAP_LOCK_WAIT_TIMEOUT_S]),
        ('SET SESSION lock_wait_timeout = %s', [_SESSION_LOCK_WAIT_TIMEOUT]),
    ]


def test_a_rename_that_waits_out_its_lock_is_tried_again() -> None:
    """A timed-out attempt is not a failure until every attempt has timed out."""
    db = _RecordingDB({'partables'}, lock_timeouts=2)

    assert _swap(db, ['partables']) is True

    assert len(db.statements('RENAME TABLE')) == 3
    assert db.table_exists('perm', 'partables')


def test_a_rename_that_never_gets_its_lock_fails_and_restores_the_timeout() -> None:
    """After the last attempt the wait is an error, and the live table is untouched."""
    db = _RecordingDB({'partables'}, lock_timeouts=table_swap.SWAP_RENAME_ATTEMPTS)

    with pytest.raises(ImportDBError, match='Lock wait timeout'):
        _swap(db, ['partables'])

    assert len(db.statements('RENAME TABLE')) == table_swap.SWAP_RENAME_ATTEMPTS
    assert db.executed[-1] == (
        'SET SESSION lock_wait_timeout = %s',
        [_SESSION_LOCK_WAIT_TIMEOUT],
    )
    assert db.table_exists('perm', 'partables__new')


def test_a_fault_named_for_the_set_stops_before_the_rename(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """``swap_in:definitions`` stops the dictionary's swap, leaving the live pair."""
    monkeypatch.setenv(import_fault.IMPORT_FAULT_ENV_VAR, 'swap_in:definitions')
    db = _RecordingDB({'contexts', 'definitions'})

    with pytest.raises(import_fault.InjectedImportFaultError, match='swap_in:definitions'):
        _swap(db, ['contexts', 'definitions'])

    assert db.statements('RENAME TABLE') == []
    assert db.table_exists('perm', 'definitions__new')


def test_a_fault_named_for_another_set_changes_nothing(monkeypatch: pytest.MonkeyPatch) -> None:
    """The site's argument selects the set; any other set swaps as usual."""
    monkeypatch.setenv(import_fault.IMPORT_FAULT_ENV_VAR, 'swap_in:definitions')
    db = _RecordingDB({'param_info'})

    assert _swap(db, ['param_info']) is True


@pytest.mark.parametrize(
    ('value', 'site', 'argument'),
    [
        (None, 'swap_in', None),
        ('swap_in:param_info', 'swap_in', 'param_info'),
        ('swap_in:param_info', 'log_error', None),
        ('swap_in', 'swap_in', None),
        ('swap_in:', 'swap_in', ''),
    ],
    ids=['unset', 'named', 'another-site', 'no-colon', 'empty-argument'],
)
def test_the_fault_variable_names_a_site_and_an_argument(
    monkeypatch: pytest.MonkeyPatch, value: str | None, site: str, argument: str | None
) -> None:
    """``<site>:<argument>``; a site the variable does not name reads None."""
    if value is None:
        monkeypatch.delenv(import_fault.IMPORT_FAULT_ENV_VAR, raising=False)
    else:
        monkeypatch.setenv(import_fault.IMPORT_FAULT_ENV_VAR, value)
    assert import_fault.import_fault_argument(site) == argument
