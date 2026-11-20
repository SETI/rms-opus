"""Tests for the import generations of a served schema, against stand-ins.

The SQL the MySQL layer renders for the served view, the name translation, the retire,
and the cart's move are read from a recording connection; the generation commands'
refusals, their lock, and the switch's order and resumption run against a stand-in that
holds the version row.
"""

from __future__ import annotations

import contextlib
import re
from typing import TYPE_CHECKING, Any

import pytest

from opus_import import bundle_registry, generations, import_processes, importdb, table_swap
from opus_import.cli import (
    _create_argument_parser,
    _generation_conflicts,
    _rebuilds_pending,
    _rebuilds_served,
    _validate,
    expand_aggregate_options,
)
from opus_import.generations import (
    PENDING_FINALIZED,
    PENDING_READY,
    PENDING_VALIDATED,
    PENDING_WRITING,
    GenerationState,
)
from opus_import.import_fault import IMPORT_FAULT_ENV_VAR, InjectedImportFaultError
from opus_import.importdb.mysql import ImportDBMySQL
from opus_import.importdb.super import ImportDBError, ImportDBSuper
from opus_import.schema_version import SCHEMA_STATE_READY, SCHEMA_VERSION
from opus_import.steps import (
    do_django,
    do_duplicate_ids,
    do_finalize_mult,
    do_generation,
    do_generation_purge,
    do_import_tables,
    do_schema_version,
    do_validate,
)

from .conftest import make_context

if TYPE_CHECKING:
    from opus_import.context import ImportContext


class _Connection:
    """A DB-API connection stand-in whose cursor reports one changed row."""

    def cursor(self) -> Any:
        """Return a cursor that does nothing."""
        return contextlib.nullcontext(_Cursor())

    def commit(self) -> None:
        """Commit nothing."""

    def rollback(self) -> None:
        """Roll back nothing."""


class _Cursor:
    """A cursor that runs nothing and reports one row changed."""

    rowcount = 1

    def execute(self, cmd: str, params: Any = None) -> None:
        """Run nothing."""


class _RecordingDB(ImportDBMySQL):
    """An ImportDBMySQL that records statements instead of running them."""

    def __init__(self, tables: set[str] | None = None) -> None:
        # Deliberately skips ImportDBMySQL.__init__, which connects to a server.
        ImportDBSuper.__init__(self, 'host', 'db', 'schema', 'user', 'password', logger=None)
        self.conn = _Connection()
        self.executed: list[tuple[str, Any]] = []
        self._table_names = set(tables or ())
        self._table_info_cache = {}
        self.default_engine = 'INNODB'

    #: What ``INFORMATION_SCHEMA.TABLES`` says ``obs_general`` is, or None when absent.
    obs_general_type: str | None = 'VIEW'

    def _execute(
        self, cmd: str, param_list: Any = None, cur: Any = None, mutates: bool = False
    ) -> None:
        self.executed.append((cmd, param_list))

    def _execute_and_fetchall(self, cmd: str, func_name: str, param_list: Any = None) -> Any:
        """Answer the one query these tests reach, what ``obs_general`` is."""
        assert func_name == 'obs_general_type', func_name
        return [] if self.obs_general_type is None else [(self.obs_general_type,)]


def _obs_general_schema() -> list[dict[str, Any]]:
    """Return a small schema of ``obs_general`` with the generation columns."""
    return [
        {'field_name': 'id', 'field_type': 'uint4', 'field_key': 'primary', 'field_notnull': True},
        {'field_name': 'opus_id', 'field_type': 'varchar50', 'field_notnull': True},
        {
            'field_name': 'added_generation',
            'field_type': 'uint4',
            'field_notnull': True,
            'data_source': 'GENERATION',
        },
        {'field_name': 'removed_generation', 'field_type': 'uint4', 'data_source': 'GENERATION'},
    ]


# ------------------------------------------------------------------------------------
# The served view and the name translation
# ------------------------------------------------------------------------------------


def test_obs_general_is_created_as_its_base_table_then_a_view_of_every_row() -> None:
    """A fresh import's rows are all in its generation, so the view has no condition."""
    db = _RecordingDB()
    db.create_table('obs_general', _obs_general_schema())
    (table, _), (view, _) = db.executed
    assert table.startswith('CREATE TABLE IF NOT EXISTS `obs_general_rows` (')
    assert view == (
        'CREATE OR REPLACE ALGORITHM=MERGE SQL SECURITY INVOKER VIEW `obs_general` AS '
        'SELECT `id`, `opus_id` FROM `obs_general_rows`'
    )
    assert 'obs_general' in db.table_names()
    assert 'obs_general_rows' not in db.table_names()


def test_a_view_of_one_generation_names_it_as_a_number() -> None:
    """While other generations' rows are in the table, the view shows the served one's."""
    db = _RecordingDB()
    db.create_obs_general_view(_obs_general_schema(), 3)
    ((view, _),) = db.executed
    assert view.endswith(
        'FROM `obs_general_rows` WHERE `obs_general_rows`.`added_generation` <= 3 AND '
        '(`obs_general_rows`.`removed_generation` IS NULL OR '
        '`obs_general_rows`.`removed_generation` > 3)'
    )


class _LockedViewDB(_RecordingDB):
    """A recording database whose first view re-creations wait out their lock."""

    def __init__(self, lock_timeouts: int) -> None:
        super().__init__()
        self.lock_timeouts = lock_timeouts
        # The MySQL layer tells a lock wait by the driver's own error.
        self.driver = pytest.importorskip('MySQLdb')

    def _execute(
        self, cmd: str, param_list: Any = None, cur: Any = None, mutates: bool = False
    ) -> None:
        self.executed.append((cmd, param_list))
        if cmd.startswith('CREATE OR REPLACE') and self.lock_timeouts > 0:
            self.lock_timeouts -= 1
            raise self.driver.OperationalError(1205, 'Lock wait timeout exceeded')

    def _execute_and_fetchall(
        self, cmd: str, func_name: str, param_list: Any = None
    ) -> list[tuple[Any, ...]]:
        """Answer the session's lock wait timeout."""
        assert cmd == 'SELECT @@SESSION.lock_wait_timeout'
        return [(_SESSION_LOCK_WAIT_TIMEOUT,)]


#: The session's own lock wait timeout, which a bounded wait restores.
_SESSION_LOCK_WAIT_TIMEOUT = 50


def test_a_view_re_created_while_served_waits_a_bounded_time_and_tries_again() -> None:
    """A transaction reading the view holds its lock; each attempt waits a short time."""
    db = _LockedViewDB(lock_timeouts=2)
    db.create_obs_general_view(_obs_general_schema(), 3, lock_wait_timeout_s=5, attempts=3)
    statements = [cmd.split(' ALGORITHM')[0] for cmd, _ in db.executed]
    assert statements == [
        'SET SESSION lock_wait_timeout = %s',
        'CREATE OR REPLACE',
        'CREATE OR REPLACE',
        'CREATE OR REPLACE',
        'SET SESSION lock_wait_timeout = %s',
    ]
    assert db.executed[0][1] == [5]
    assert db.executed[-1][1] == [_SESSION_LOCK_WAIT_TIMEOUT]


def test_a_view_that_never_gets_its_lock_fails_and_restores_the_wait() -> None:
    """After the last attempt the wait is an error naming the view."""
    db = _LockedViewDB(lock_timeouts=3)
    with pytest.raises(ImportDBError, match='Lock wait timeout'):
        db.create_obs_general_view(_obs_general_schema(), 3, lock_wait_timeout_s=5, attempts=3)
    assert db.executed[-1] == ('SET SESSION lock_wait_timeout = %s', [_SESSION_LOCK_WAIT_TIMEOUT])


def test_the_commands_re_create_the_view_with_the_swaps_bounded_wait() -> None:
    """The begin, the purge and the abandon run while the site serves the view."""
    created: list[tuple[int | None, dict[str, Any]]] = []

    class _DB:
        @staticmethod
        def create_obs_general_view(schema: Any, served: int | None, **kwargs: Any) -> None:
            created.append((served, kwargs))

    do_generation.refresh_view(make_context(db=_DB()), 2)
    assert created == [
        (
            2,
            {
                'lock_wait_timeout_s': table_swap.SWAP_LOCK_WAIT_TIMEOUT_S,
                'attempts': table_swap.SWAP_RENAME_ATTEMPTS,
            },
        )
    ]


@pytest.mark.parametrize(
    ('obs_general_type', 'created'),
    [(None, True), ('VIEW', False)],
    ids=['view-missing', 'view-there'],
)
def test_an_existing_obs_general_table_gets_its_view_when_it_has_none(
    obs_general_type: str | None, created: bool
) -> None:
    """A table whose view's statement failed after it is given its view the next time
    it is asked for; an existing view, which may name a generation, is left alone."""
    db = _RecordingDB({'obs_general'})
    db.obs_general_type = obs_general_type
    assert db.create_table('obs_general', _obs_general_schema()) is False
    views = [cmd for cmd, _ in db.executed if 'VIEW' in cmd]
    assert views == (
        [
            'CREATE OR REPLACE ALGORITHM=MERGE SQL SECURITY INVOKER VIEW `obs_general` AS '
            'SELECT `id`, `opus_id` FROM `obs_general_rows`'
        ]
        if created
        else []
    )
    assert not any(cmd.startswith('CREATE TABLE') for cmd, _ in db.executed)


def test_dropping_obs_general_drops_the_view_before_the_table() -> None:
    """DROP TABLE refuses a view, and the view reads the table."""
    db = _RecordingDB({'obs_general'})
    db.drop_table('obs_general')
    assert [cmd for cmd, _ in db.executed] == [
        'DROP VIEW `obs_general`',
        'DROP TABLE `obs_general_rows`',
    ]


def test_an_obs_general_base_table_of_an_earlier_version_is_dropped_by_its_name() -> None:
    """A schema of an earlier version has no view to drop, and its base table is
    obs_general itself, which the erase drops in its turn."""
    db = _RecordingDB({'obs_general'})
    db.obs_general_type = 'BASE TABLE'
    db.drop_obs_general_view()
    assert db.executed == []
    db.drop_table('obs_general')
    assert [cmd for cmd, _ in db.executed] == ['DROP TABLE `obs_general`']


def test_a_schema_without_obs_general_drops_no_view() -> None:
    """The erase of a schema that never had obs_general sends no DROP VIEW."""
    db = _RecordingDB()
    db.obs_general_type = None
    db.drop_obs_general_view()
    assert db.executed == []


def test_the_import_names_are_mapped_both_ways() -> None:
    """The base table is reported as obs_general and rendered from it."""
    assert generations.physical_table_name('obs_general') == 'obs_general_rows'
    assert generations.physical_table_name('obs_pds') == 'obs_pds'
    assert generations.logical_table_name('OBS_GENERAL_ROWS') == 'obs_general'
    assert generations.logical_table_name('obs_pds') == 'obs_pds'
    assert generations.view_columns(_obs_general_schema()) == ['id', 'opus_id']


def test_the_cart_is_moved_by_opus_id_then_the_rows_left_behind_deleted() -> None:
    """Rows not in the generation point at its copy, or go."""
    db = _RecordingDB()
    assert db.repoint_cart(4) == (1, 1)
    (update, update_params), (delete, delete_params) = db.executed
    assert update.startswith('UPDATE `cart` AS `c` JOIN `obs_general_rows` AS `o`')
    assert '`n`.`opus_id` = `o`.`opus_id`' in update
    assert 'SET `c`.`obs_general_id` = `n`.`id` WHERE NOT (' in update
    assert update_params == [4, 4, 4, 4]
    assert delete.startswith('DELETE `c` FROM `cart` AS `c` JOIN `obs_general_rows` AS `o`')
    assert delete_params == [4, 4]


def test_a_bundle_is_retired_a_range_of_ids_at_a_time_through_its_key() -> None:
    """Only rows an earlier generation added and none retired, each range read once."""
    selects: list[list[Any]] = []
    updates: list[tuple[str, Any, str, list[Any]]] = []
    bundle_ids = [[10, 11], [12]]

    class _DB:
        transaction_rows = 2
        read_only = False

        @staticmethod
        def quote_identifier(name: str) -> str:
            return f'`{name}`'

        @staticmethod
        def retrying(description: str, body: Any) -> Any:
            return body()

        @staticmethod
        def general_select(cmd: str, params: Any = None) -> list[tuple[Any, ...]]:
            assert cmd.startswith('`id` FROM `obs_general` WHERE `bundle_id`=%s')
            selects.append(list(params))
            return [(obs_id,) for obs_id in bundle_ids.pop(0)] if bundle_ids else []

        def update_row(self, table: str, row: Any, where: str, params: list[Any]) -> int:
            updates.append((table, row, where, params))
            return int(params[2] - params[1] + 1)

    retired = do_import_tables.retire_bundle_rows(make_context(db=_DB()), 'B_1', 5)
    assert retired == 3
    assert selects == [['B_1', 2], ['B_1', 11, 2]]
    assert [params for _table, _row, _where, params in updates] == [
        ['B_1', 10, 11, 5],
        ['B_1', 12, 12, 5],
    ]
    table, row, where, _params = updates[0]
    assert (table, row) == ('obs_general', {'removed_generation': 5})
    assert where == (
        '`bundle_id`=%s AND `id` BETWEEN %s AND %s AND `added_generation` < %s AND '
        '`removed_generation` IS NULL'
    )
    assert 'LIMIT' not in where


def test_an_abandon_finds_its_rows_in_one_scan_and_restores_them_by_key() -> None:
    """The rows it added and the rows it retired, apart; the retired back by primary key."""
    selects: list[tuple[str, Any]] = []
    updates: list[tuple[dict[str, Any], str, list[Any]]] = []

    class _DB:
        transaction_rows = 2

        @staticmethod
        def quote_identifier(name: str) -> str:
            return f'`{name}`'

        @staticmethod
        def retrying(description: str, body: Any) -> Any:
            return body()

        @staticmethod
        def general_select(cmd: str, params: Any = None) -> list[tuple[Any, ...]]:
            selects.append((cmd, params))
            return [(3, 1), (4, 1), (5, 1), (8, 2), (9, 2)]

        @staticmethod
        def update_row(table: str, row: dict[str, Any], where: str, params: list[Any]) -> int:
            assert table == 'obs_general'
            updates.append((row, where, params))
            return len(params) - 1

    ctx = make_context(db=_DB())
    added, retired = do_generation_purge._abandoned_ids(ctx, 2)
    assert (added, retired) == ([8, 9], [3, 4, 5])
    ((cmd, params),) = selects
    assert 'WHERE `added_generation`=%s OR `removed_generation`=%s' in cmd
    assert params == [2, 2]
    do_import_tables.restore_retired_rows(ctx, retired, 2)
    assert updates == [
        ({'removed_generation': None}, '`id` IN (%s,%s) AND `removed_generation`=%s', [3, 4, 2]),
        ({'removed_generation': None}, '`id` IN (%s) AND `removed_generation`=%s', [5, 2]),
    ]


# ------------------------------------------------------------------------------------
# The generation commands, against a stand-in holding the version row
# ------------------------------------------------------------------------------------


class _StateDB:
    """A stand-in holding one version row and the generation lock, recording events."""

    db_schema = 'opus_test'
    read_only = False
    transaction_rows = 100

    def __init__(
        self,
        state: tuple[Any, ...] | None,
        *,
        lock_free: bool = True,
        tables: tuple[str, ...] = (),
        columns: tuple[str, ...] = generations.STATE_COLUMNS,
        sole_writer: int | None = None,
    ) -> None:
        self.row = (
            None if state is None else dict(zip(generations.STATE_COLUMNS, state, strict=True))
        )
        self.lock_free = lock_free
        self.tables = set(tables)
        self.columns = columns
        self.sole_writer = sole_writer
        self.events: list[str] = []

    def forget_table_names(self) -> None:
        """Read nothing."""

    def table_exists(self, table: str) -> bool:
        """Hold the version table, when there is a row, and the tables given."""
        return (table == 'schema_version' and self.row is not None) or table in self.tables

    def table_info(self, table: str) -> list[dict[str, Any]]:
        """Return the version table's columns."""
        assert table == 'schema_version'
        return [{'field_name': column} for column in self.columns]

    def read_rows(self, table: str, columns: list[str], *args: Any) -> list[tuple[Any, ...]]:
        """Return the version row's columns."""
        assert self.row is not None
        assert set(columns) <= set(self.columns)
        return [tuple(self.row[column] for column in columns)]

    def named_lock_holder(self, name: str) -> int | None:
        """Return the sole writer's connection, the only lock these tests ask about."""
        assert name == importdb.lock_name(self.db_schema, generations.GENERATION_SOLE_WRITER_LOCK)
        return self.sole_writer

    def update_row(self, table: str, row: dict[str, Any], where: str, params: Any = None) -> int:
        """Write the version row when it meets a condition on one column, recording the
        columns written, and return how many rows matched."""
        assert self.row is not None
        equal = re.fullmatch(r'`(\w+)`=%s', where)
        null = re.fullmatch(r'`(\w+)` IS NULL', where)
        if equal is not None and self.row[equal.group(1)] != params[0]:
            return 0
        if null is not None and self.row[null.group(1)] is not None:
            return 0
        self.row.update(row)
        self.events.append(f'update {sorted(row)}')
        return 1

    def try_named_lock(self, name: str) -> bool:
        """Grant the lock when it is free."""
        self.events.append('lock')
        return self.lock_free

    def release_named_lock(self, name: str) -> None:
        """Record the release."""
        self.events.append('unlock')

    @staticmethod
    def quote_identifier(name: str) -> str:
        return f'`{name}`'

    def drop_table(self, table: str) -> None:
        """Record a drop, and forget the table."""
        self.events.append(f'drop {table}')
        self.tables.discard(table)


def _ready(**changes: Any) -> tuple[Any, ...]:
    """Return a version row serving generation 1, as a fresh import leaves it, changed."""
    row = dict(
        zip(
            generations.STATE_COLUMNS,
            (SCHEMA_VERSION, SCHEMA_STATE_READY, 1, None, None, 0),
            strict=True,
        )
    )
    row.update(changes)
    return tuple(row[column] for column in generations.STATE_COLUMNS)


#: The auxiliary tables' names after a switch's swap and after a revert's.
_PREV = tuple(table_swap.swap_prev_name(table) for table in do_generation.AUX_TABLES)
_NEW = tuple(table_swap.swap_new_name(table) for table in do_generation.AUX_TABLES)


@pytest.fixture
def no_writers(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    """Report no invocation writing the pending generation, and record the view's
    re-creations instead of running them."""
    views: list[str] = []
    monkeypatch.setattr(do_generation, '_alive_writers', lambda db: [])
    monkeypatch.setattr(
        do_generation, 'refresh_view', lambda ctx, served: views.append(f'view {served}')
    )
    return views


def _context(db: _StateDB) -> ImportContext:
    """Return a context on the stand-in, its version row read."""
    ctx = make_context(db=db)
    do_generation.load_generation_state(ctx)
    return ctx


def test_begin_sets_the_next_generation_pending_and_writing(no_writers: list[str]) -> None:
    """The view shows the served generation alone first; the version row stays ready."""
    assert no_writers == []
    db = _StateDB(_ready())
    ctx = _context(db)
    do_generation.begin_generation(ctx)
    assert db.row is not None
    assert (db.row['generation'], db.row['pending_generation'], db.row['pending_state']) == (
        1,
        2,
        PENDING_WRITING,
    )
    assert db.row['state'] == SCHEMA_STATE_READY
    assert ctx.import_generation == 2
    assert no_writers == ['view 1']
    assert db.events[0] == 'lock'
    assert db.events[-1] == 'unlock'
    # No switch is revertible, so the purge has dropped every __prev table already.
    assert not any(event.startswith('drop') for event in db.events)


@pytest.mark.usefixtures('no_writers')
@pytest.mark.parametrize(
    ('row', 'tables', 'reason'),
    [
        (
            _ready(pending_generation=2, pending_state=PENDING_WRITING),
            (),
            'already has the pending',
        ),
        (_ready(state='appending'), (), 'is appending, not ready'),
        (_ready(version=SCHEMA_VERSION - 1), (), 'and this release is version'),
        (_ready(generation=2, revertible=1), _PREV, 'can still revert to generation 1'),
        (_ready(generation=2, revertible=1), (), 'holds retired rows: the purge of the rows'),
    ],
    ids=['pending', 'appending', 'version', 'revertible', 'purge-started'],
)
def test_begin_is_refused_on_a_schema_it_cannot_start_one_in(
    row: tuple[Any, ...], tables: tuple[str, ...], reason: str
) -> None:
    """Nothing is written or dropped, and the refusal says why."""
    db = _StateDB(row, tables=tables)
    with pytest.raises(do_generation.GenerationRefusedError, match=reason):
        do_generation.begin_generation(_context(db))
    assert [event for event in db.events if event not in ('lock', 'unlock')] == []


def test_a_command_is_refused_while_another_holds_the_lock() -> None:
    """The generation lock is taken without waiting."""
    db = _StateDB(_ready(), lock_free=False)
    with pytest.raises(do_generation.GenerationRefusedError, match='another generation command'):
        do_generation.begin_generation(_context(db))


def test_a_command_is_refused_while_a_writer_is_alive(monkeypatch: pytest.MonkeyPatch) -> None:
    """A registered invocation writing the pending generation holds every command off."""
    monkeypatch.setattr(do_generation, '_alive_writers', lambda db: [7])
    db = _StateDB(_ready(pending_generation=2, pending_state=PENDING_READY))
    with pytest.raises(do_generation.GenerationRefusedError, match='import_process 7 still'):
        do_generation.switch_generation(_context(db))
    assert db.events[-1] == 'unlock'


def test_a_writer_is_refused_while_a_command_holds_the_lock() -> None:
    """Registration takes the generation lock without waiting."""
    db = _StateDB(_ready(pending_generation=2, pending_state=PENDING_WRITING), lock_free=False)
    with pytest.raises(do_generation.GenerationRefusedError, match='holds'):
        do_generation.register_writer(_context(db))


@pytest.mark.parametrize(
    'now',
    [
        _ready(generation=2, revertible=1),
        _ready(),
        _ready(generation=2, pending_generation=3, pending_state=PENDING_WRITING),
    ],
    ids=['switched', 'abandoned', 'switched-and-begun'],
)
def test_a_writer_is_refused_when_its_generation_changed_before_the_lock(
    now: tuple[Any, ...],
) -> None:
    """The row it started by is read again under the lock, and nothing registers."""
    db = _StateDB(_ready(pending_generation=2, pending_state=PENDING_WRITING))
    ctx = _context(db)
    db.row = dict(zip(generations.STATE_COLUMNS, now, strict=True))
    with pytest.raises(do_generation.GenerationRefusedError, match='no longer pending'):
        do_generation.register_writer(ctx)
    assert db.events == ['lock', 'unlock']


def test_a_writer_registers_under_the_lock_with_the_row_read_again(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The row read under the lock replaces the one read as the invocation started."""
    db = _StateDB(_ready(pending_generation=2, pending_state=PENDING_WRITING))
    ctx = _context(db)
    assert db.row is not None
    db.row['pending_state'] = PENDING_FINALIZED
    importer = object()
    opened: list[object] = []

    def start_importer(lock_db: object, log_path: str) -> object:
        """Record the connection the row is taken on."""
        opened.append(lock_db)
        return importer

    def open_sibling_connection() -> _StateDB:
        """Return the stand-in itself."""
        return db

    monkeypatch.setattr(import_processes, 'create_process_table', lambda db: None)
    monkeypatch.setattr(import_processes, 'start_importer', start_importer)
    monkeypatch.setattr(db, 'open_sibling_connection', open_sibling_connection, raising=False)
    assert do_generation.register_writer(ctx) is importer
    assert opened == [db]
    assert ctx.generation_state is not None
    assert ctx.generation_state.pending_state == PENDING_FINALIZED
    assert db.events == ['lock', 'unlock']


class _LockConnection:
    """The sibling connection a writer's row is taken on, recording the locks it takes."""

    def __init__(self, *, grants: bool = True) -> None:
        self.grants = grants
        self.locks: list[str] = []

    def try_named_lock(self, name: str) -> bool:
        """Record the lock, and grant it unless told not to."""
        self.locks.append(name)
        return self.grants


class _Writer:
    """What `import_processes.start_importer` returns, recording its exit."""

    def __init__(self) -> None:
        self.exited = False

    def exit(self) -> None:
        """Record the exit."""
        self.exited = True


@pytest.fixture
def registering(monkeypatch: pytest.MonkeyPatch) -> tuple[_LockConnection, Any]:
    """Take a writer's row on a recording connection, and return both."""
    connection = _LockConnection()
    writer = _Writer()
    monkeypatch.setattr(import_processes, 'create_process_table', lambda db: None)
    monkeypatch.setattr(import_processes, 'start_importer', lambda lock_db, log_path: writer)
    monkeypatch.setattr(_StateDB, 'open_sibling_connection', lambda self: connection, raising=False)
    return connection, writer


def _sole_writer_lock() -> str:
    """Return the sole writer's lock on the stand-in's schema."""
    return importdb.lock_name('opus_test', generations.GENERATION_SOLE_WRITER_LOCK)


def test_a_writer_of_the_served_rows_registers_and_holds_a_begin_off(
    registering: tuple[_LockConnection, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    """With nothing pending the version row is read again under the lock, and the row
    registered then refuses a begin."""
    connection, writer = registering
    db = _StateDB(_ready())
    ctx = _context(db)
    assert do_generation.register_writer(ctx) is writer
    assert connection.locks == []
    assert db.events == ['lock', 'unlock']
    monkeypatch.setattr(do_generation, '_alive_writers', lambda db: [7])
    with pytest.raises(do_generation.GenerationRefusedError, match='import_process 7 still'):
        do_generation.begin_generation(ctx)


def test_a_writer_of_the_served_rows_is_refused_once_a_generation_has_begun(
    registering: tuple[_LockConnection, Any],
) -> None:
    """It chose to write the served rows by the row it read as it started."""
    db = _StateDB(_ready())
    ctx = _context(db)
    db.row = dict(
        zip(
            generations.STATE_COLUMNS,
            _ready(pending_generation=2, pending_state=PENDING_WRITING),
            strict=True,
        )
    )
    with pytest.raises(
        do_generation.GenerationRefusedError,
        match='The schema changed: generation 1 is served and generation 2 is pending',
    ):
        do_generation.register_writer(ctx)
    assert db.events == ['lock', 'unlock']


def test_the_sole_writer_is_refused_beside_another_writer(
    registering: tuple[_LockConnection, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Finalization, validation and the stamp record a state of rows nothing else writes;
    another writer of the pending generation registers beside a writer that is not sole."""
    connection, writer = registering
    monkeypatch.setattr(do_generation, '_alive_writers', lambda db: [7])
    db = _StateDB(_ready(pending_generation=2, pending_state=PENDING_FINALIZED))
    with pytest.raises(do_generation.GenerationRefusedError, match='import_process 7 still'):
        do_generation.register_writer(_context(db), sole=True)
    assert connection.locks == []
    assert do_generation.register_writer(_context(db)) is writer


def test_the_sole_writer_holds_its_lock_on_its_rows_connection(
    registering: tuple[_LockConnection, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    """The lock lasts as long as the row's, and frees with it."""
    connection, writer = registering
    monkeypatch.setattr(do_generation, '_alive_writers', lambda db: [])
    db = _StateDB(_ready(pending_generation=2, pending_state=PENDING_FINALIZED))
    assert do_generation.register_writer(_context(db), sole=True) is writer
    assert connection.locks == [_sole_writer_lock()]
    # Read through the fixture's tuple: the identity check narrows `writer`'s type.
    assert not registering[1].exited
    assert db.events == ['lock', 'unlock']


def test_a_sole_writer_whose_lock_is_not_granted_frees_its_row(
    registering: tuple[_LockConnection, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Nothing is left registered."""
    connection, writer = registering
    connection.grants = False
    monkeypatch.setattr(do_generation, '_alive_writers', lambda db: [])
    db = _StateDB(_ready(pending_generation=2, pending_state=PENDING_FINALIZED))
    with pytest.raises(do_generation.GenerationRefusedError, match='as its sole writer'):
        do_generation.register_writer(_context(db), sole=True)
    assert writer.exited


@pytest.mark.parametrize('sole', [False, True], ids=['writer', 'sole-writer'])
def test_no_writer_registers_while_the_sole_writer_runs(
    registering: tuple[_LockConnection, Any], monkeypatch: pytest.MonkeyPatch, sole: bool
) -> None:
    """While the pending generation is finalized, validated or stamped, nothing else
    writes it."""
    connection, _writer = registering
    monkeypatch.setattr(do_generation, '_alive_writers', lambda db: [])
    db = _StateDB(_ready(pending_generation=2, pending_state=PENDING_FINALIZED), sole_writer=12)
    with pytest.raises(do_generation.GenerationRefusedError, match='which runs alone'):
        do_generation.register_writer(_context(db), sole=sole)
    assert connection.locks == []
    assert db.events == ['lock', 'unlock']


def test_a_version_table_without_the_generation_columns_holds_no_generation() -> None:
    """A schema of an earlier version is read as having none, and its columns are never
    selected, so it reaches the refusals and the erase rather than a failed read."""
    db = _StateDB(_ready(), columns=('version', 'state'))
    assert do_generation.read_generation_state(db) is None  # type: ignore[arg-type]
    with pytest.raises(do_generation.GenerationRefusedError, match='the generation columns'):
        do_generation.begin_generation(_context(db))


def test_a_pending_state_with_no_pending_generation_to_hold_it_fails_loudly() -> None:
    """A generation switched in or abandoned under a writer is not silently re-marked."""
    db = _StateDB(_ready(pending_generation=2, pending_state=PENDING_WRITING))
    ctx = _context(db)
    db.row = dict(zip(generations.STATE_COLUMNS, _ready(generation=2, revertible=1), strict=True))
    with pytest.raises(do_generation.GenerationLostError, match='no longer pending'):
        do_generation.set_pending_state(ctx, PENDING_FINALIZED)
    assert db.row['pending_state'] is None


def test_a_read_only_run_records_no_pending_state_and_does_not_fail() -> None:
    """A read-only run executes nothing, so no row matches."""
    db = _StateDB(_ready(pending_generation=2, pending_state=PENDING_WRITING))
    ctx = _context(db)
    db.read_only = True
    db.row = dict(zip(generations.STATE_COLUMNS, _ready(), strict=True))
    do_generation.set_pending_state(ctx, PENDING_FINALIZED)


@pytest.fixture
def switch_steps(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    """Record the switch's steps instead of running them."""
    steps: list[str] = []
    monkeypatch.setattr(do_generation, '_alive_writers', lambda db: [])
    monkeypatch.setattr(
        table_swap, 'swap_in_keeping_previous', lambda ctx, tables: steps.append('swap')
    )
    monkeypatch.setattr(table_swap, 'swap_back_previous', lambda ctx, tables: steps.append('back'))
    monkeypatch.setattr(
        do_generation, '_point_cart', lambda ctx, generation: steps.append(f'cart {generation}')
    )
    monkeypatch.setattr(do_django, 'reset_search_tables', lambda ctx: steps.append('reset'))
    monkeypatch.setattr(
        do_generation, 'refresh_view', lambda ctx, served: steps.append(f'view {served}')
    )
    return steps


def test_the_switch_runs_its_steps_then_serves_the_generation_last(
    switch_steps: list[str],
) -> None:
    """Swap, cart, reset, then the one statement that serves it."""
    db = _StateDB(_ready(pending_generation=2, pending_state=PENDING_READY))
    do_generation.switch_generation(_context(db))
    assert switch_steps == ['swap', 'cart 2', 'reset', 'view 2']
    assert db.row is not None
    assert (db.row['generation'], db.row['pending_generation'], db.row['revertible']) == (
        2,
        None,
        1,
    )


@pytest.mark.parametrize('step', [1, 2, 3, 4])
def test_an_interrupted_switch_stops_after_its_step_and_serves_nothing(
    switch_steps: list[str], monkeypatch: pytest.MonkeyPatch, step: int
) -> None:
    """The fault raises after the named step; the version row is untouched; a rerun ends it."""
    db = _StateDB(_ready(pending_generation=2, pending_state=PENDING_READY))
    monkeypatch.setenv(IMPORT_FAULT_ENV_VAR, f'{do_generation.SWITCH_FAULT_SITE}:{step}')
    with pytest.raises(InjectedImportFaultError):
        do_generation.switch_generation(_context(db))
    assert switch_steps == ['swap', 'cart 2', 'reset', 'view 2'][:step]
    assert db.row is not None
    assert db.row['pending_generation'] == 2
    assert db.events[-1] == 'unlock'
    monkeypatch.delenv(IMPORT_FAULT_ENV_VAR)
    do_generation.switch_generation(_context(db))
    assert db.row['generation'] == 2


def test_a_switched_generation_is_completed_not_refused(switch_steps: list[str]) -> None:
    """With nothing pending and the switch revertible, its __prev tables whole, the steps
    run again for it."""
    db = _StateDB(_ready(generation=2, revertible=1), tables=_PREV)
    do_generation.switch_generation(_context(db))
    assert switch_steps == ['swap', 'cart 2', 'reset', 'view 2']
    assert not any(event.startswith('update') for event in db.events)


@pytest.mark.parametrize('built', [_NEW, _NEW[:1]], ids=['whole', 'part'])
def test_completing_a_switch_beside_an_unfinished_rebuild_is_refused(
    switch_steps: list[str], built: tuple[str, ...]
) -> None:
    """__new tables beside a whole __prev set, with nothing pending, are a served rebuild
    that stopped part way: the switch would swap them in and drop the __prev set."""
    db = _StateDB(_ready(generation=2, revertible=1), tables=(*_PREV, *built))
    with pytest.raises(do_generation.GenerationRefusedError, match='rebuild of the served'):
        do_generation.switch_generation(_context(db))
    assert switch_steps == []
    ctx = _context(db)
    assert ctx.db is not None
    assert ctx.generation_state is not None
    problem = do_generation.unfinished_rebuild_problem(ctx.db, ctx.generation_state)
    assert problem is not None
    assert "generation 1's __prev tables" in problem


@pytest.mark.parametrize(
    ('row', 'tables'),
    [
        (_ready(generation=2, revertible=1), _NEW),
        (_ready(generation=2, revertible=1), (*_PREV[:1], *_NEW)),
        (_ready(generation=2, revertible=0), (*_PREV, *_NEW)),
        (_ready(generation=2, revertible=1, pending_generation=3), (*_PREV, *_NEW)),
    ],
    ids=['revert-marker', 'purge-started', 'not-revertible', 'pending'],
)
def test_only_new_tables_beside_a_whole_revertible_prev_set_are_an_unfinished_rebuild(
    row: tuple[Any, ...], tables: tuple[str, ...]
) -> None:
    """A part-way revert's __new tables, a purge's, and any shape with a generation
    pending or nothing revertible are other states, which other checks name."""
    ctx = _context(_StateDB(row, tables=tables))
    assert ctx.db is not None
    assert ctx.generation_state is not None
    assert do_generation.unfinished_rebuild_problem(ctx.db, ctx.generation_state) is None


def test_a_switch_of_an_unready_generation_is_refused(switch_steps: list[str]) -> None:
    """Validation must have passed and the stamp been written."""
    db = _StateDB(_ready(pending_generation=2, pending_state=PENDING_VALIDATED))
    with pytest.raises(do_generation.GenerationRefusedError, match='no pending generation is'):
        do_generation.switch_generation(_context(db))
    assert switch_steps == []


def test_a_revert_serves_the_previous_generation_with_the_reverted_one_pending(
    switch_steps: list[str],
) -> None:
    """Swap back, the cart to the previous generation, reset, then the version row."""
    db = _StateDB(_ready(generation=2, revertible=1), tables=_PREV)
    do_generation.revert_generation(_context(db))
    assert switch_steps == ['back', 'cart 1', 'reset', 'view 1']
    assert db.row is not None
    assert (
        db.row['generation'],
        db.row['pending_generation'],
        db.row['pending_state'],
        db.row['revertible'],
    ) == (1, 2, PENDING_READY, 0)


def test_a_revert_undoes_a_switch_that_stopped_part_way(switch_steps: list[str]) -> None:
    """The steps run in the opposite order, so the __prev tables go last; the pending
    generation stays pending and ready, and the served one is untouched."""
    db = _StateDB(_ready(pending_generation=2, pending_state=PENDING_READY))
    do_generation.revert_generation(_context(db))
    assert switch_steps == ['view 1', 'reset', 'cart 1', 'back']
    assert not any(event.startswith('update') for event in db.events)


@pytest.mark.parametrize(
    ('row', 'tables', 'reason'),
    [
        (_ready(generation=2), (), 'no switch is revertible'),
        (_ready(generation=2, revertible=1), (), 'the purge of the rows generation 2 retired'),
        (_ready(generation=2, revertible=1), _PREV[:1], 'the purge of the rows generation 2'),
    ],
    ids=['purged', 'purge-started', 'purge-dropping'],
)
def test_a_revert_after_the_purge_has_started_is_refused(
    switch_steps: list[str], row: tuple[Any, ...], tables: tuple[str, ...], reason: str
) -> None:
    """The purge drops the __prev tables before the first row goes, and ends
    revertibility only once the last has gone; a revert is refused cleanly either way,
    running no step and changing nothing."""
    db = _StateDB(row, tables=tables)
    with pytest.raises(do_generation.GenerationRefusedError, match=reason):
        do_generation.revert_generation(_context(db))
    assert switch_steps == []
    assert [event for event in db.events if event not in ('lock', 'unlock')] == []
    assert db.tables == set(tables)


@pytest.mark.usefixtures('no_writers')
def test_the_purge_is_refused_with_a_pending_generation() -> None:
    """A pending generation must be switched or abandoned before the purge."""
    db = _StateDB(_ready(generation=2, pending_generation=3, pending_state=PENDING_WRITING))
    with pytest.raises(do_generation.GenerationRefusedError, match='generation 3 is pending'):
        do_generation_purge.purge_generations(_context(db))
    assert not any(event.startswith(('update', 'drop')) for event in db.events)


#: A rebuild's leftover ``__new`` table beside the ``__prev`` tables of a switch.
_LEFTOVER = table_swap.swap_new_name(do_generation.AUX_TABLES[0])


class _PurgeDB(_StateDB):
    """A stand-in that also records the condition the purge selects retired rows by."""

    def __init__(self, state: tuple[Any, ...], *, tables: tuple[str, ...]) -> None:
        super().__init__(state, tables=tables)
        self.deleted_where: list[tuple[str, list[Any]]] = []


@pytest.fixture
def purging(monkeypatch: pytest.MonkeyPatch) -> _PurgeDB:
    """Return a switched schema, with a rebuild's leftover beside its __prev tables, whose
    purge records its work in the stand-in's events instead of doing it; each event of
    the purge's own steps carries the ``revertible`` it ran under."""
    db = _PurgeDB(_ready(generation=2, revertible=1), tables=(*_PREV, _LEFTOVER))

    def event(name: str) -> None:
        assert db.row is not None
        db.events.append(f'{name} r={db.row["revertible"]}')

    def observation_ids(ctx: Any, where: str, params: list[Any]) -> list[int]:
        db.deleted_where.append((where, params))
        return [5, 6]

    def finalize_mult(ctx: Any) -> bool:
        event('mult')
        return True

    monkeypatch.setattr(do_generation, '_alive_writers', lambda db: [])
    monkeypatch.setattr(do_generation_purge, '_observation_ids', observation_ids)
    monkeypatch.setattr(
        do_import_tables, 'delete_observations', lambda ctx, ids: event(f'delete {ids}')
    )
    monkeypatch.setattr(
        bundle_registry, 'purge_retired_copies', lambda ctx, served: event(f'registry {served}')
    )
    monkeypatch.setattr(do_generation, 'refresh_view', lambda ctx, served: event(f'view {served}'))
    monkeypatch.setattr(do_finalize_mult, 'finalize_mult', finalize_mult)
    monkeypatch.setattr(do_import_tables, 'analyze_all_tables', lambda ctx: event('analyze'))
    return db


#: The drops of the purge's first step: the leftovers of a rebuild, then the __prev tables.
_PURGE_DROPS = [
    *(
        f'drop {name_for(table)}'
        for name_for in (table_swap.swap_new_name, table_swap.swap_old_name)
        for table in reversed(do_generation.AUX_TABLES)
    ),
    *(f'drop {table}' for table in reversed(_PREV)),
]

#: What each of the purge's steps records, in order.
_PURGE_STEP_EVENTS = [
    _PURGE_DROPS,
    ['delete [5, 6] r=1'],
    ['registry 2 r=1'],
    ['view None r=1'],
    ["update ['revertible']"],
]


def test_the_purge_ends_revertibility_only_after_the_last_retired_row_is_gone(
    purging: _PurgeDB,
) -> None:
    """The __prev tables go first, so no revert runs once a row has gone; the retired
    rows, their registry rows and the view's condition next; revertible last, so the web
    application keeps a child table's rows to the served generation until then."""
    assert do_generation_purge.purge_generations(_context(purging))
    assert purging.events == [
        'lock',
        *(event for step in _PURGE_STEP_EVENTS for event in step),
        'mult r=0',
        'analyze r=0',
        'unlock',
    ]
    assert purging.tables == set()
    assert purging.row is not None
    assert purging.row['revertible'] == 0
    assert purging.deleted_where == [
        ('`removed_generation` IS NOT NULL AND `removed_generation` <= %s', [2])
    ]


@pytest.mark.parametrize('step', range(1, len(do_generation_purge.PURGE_STEPS) + 1))
def test_an_interrupted_purge_refuses_a_revert_and_a_begin_and_finishes_when_run_again(
    purging: _PurgeDB, monkeypatch: pytest.MonkeyPatch, step: int
) -> None:
    """Stopped after any step before the last, the switch stays revertible, so the web
    application keeps joining, but the __prev tables are gone: the revert and the begin
    are refused, naming the purge, and a rerun finishes it."""
    monkeypatch.setenv(IMPORT_FAULT_ENV_VAR, f'{do_generation_purge.PURGE_FAULT_SITE}:{step}')
    with pytest.raises(InjectedImportFaultError):
        do_generation_purge.purge_generations(_context(purging))
    assert purging.events == [
        'lock',
        *(event for events in _PURGE_STEP_EVENTS[:step] for event in events),
        'unlock',
    ]
    monkeypatch.delenv(IMPORT_FAULT_ENV_VAR)
    assert purging.row is not None
    ctx = _context(purging)
    assert ctx.db is not None
    assert ctx.generation_state is not None
    unfinished = do_generation.unfinished_purge_problem(ctx.db, ctx.generation_state)
    last = step == len(do_generation_purge.PURGE_STEPS)
    if last:
        assert purging.row['revertible'] == 0
        assert unfinished is None
    else:
        assert purging.row['revertible'] == 1
        assert unfinished is not None
        assert '--purge-generations' in unfinished
        purging.events.clear()
        with pytest.raises(do_generation.GenerationRefusedError, match='purge of the rows'):
            do_generation.revert_generation(ctx)
        with pytest.raises(do_generation.GenerationRefusedError, match='holds retired rows'):
            do_generation.begin_generation(ctx)
        with pytest.raises(do_generation.GenerationRefusedError, match='purge of the rows'):
            do_generation.switch_generation(ctx)
        assert [event for event in purging.events if event not in ('lock', 'unlock')] == []
    purging.events.clear()
    assert do_generation_purge.purge_generations(_context(purging))
    assert purging.events[-5:] == [
        f'view None r={0 if last else 1}',
        "update ['revertible']",
        'mult r=0',
        'analyze r=0',
        'unlock',
    ]
    assert purging.row['revertible'] == 0
    assert purging.row['generation'] == 2


@pytest.mark.parametrize(
    ('row', 'tables', 'unfinished'),
    [
        (_ready(pending_generation=2, pending_state=PENDING_READY), _NEW, None),
        (_ready(pending_generation=2, pending_state=PENDING_READY), _PREV, 'a switch of'),
        (_ready(pending_generation=2, pending_state=PENDING_WRITING), _PREV, 'a switch of'),
        (_ready(generation=2, revertible=1), _PREV, None),
        (_ready(generation=2, revertible=1), _NEW, 'a revert of generation 2'),
        (_ready(generation=2, revertible=1), _PREV + _NEW, None),
        (_ready(generation=2), _NEW, None),
    ],
    ids=[
        'pending',
        'part-way-switch',
        'written-after-a-part-way-switch',
        'switched',
        'part-way-revert',
        'rebuild-left-over',
        'purged',
    ],
)
def test_an_unfinished_switch_or_revert_is_told_by_its_auxiliary_tables(
    row: tuple[Any, ...], tables: tuple[str, ...], unfinished: str | None
) -> None:
    """__prev beside a pending generation; __new with no __prev beside a revertible one."""
    ctx = _context(_StateDB(row, tables=tables))
    assert ctx.db is not None
    assert ctx.generation_state is not None
    problem = do_generation.unfinished_switch_problem(ctx.db, ctx.generation_state)
    if unfinished is None:
        assert problem is None
    else:
        assert problem is not None
        assert unfinished in problem
        assert '--switch-generation' in problem
        assert '--revert-generation' in problem


@pytest.mark.parametrize(
    ('row', 'tables', 'started'),
    [
        (_ready(pending_generation=2, pending_state=PENDING_READY), (), False),
        (_ready(generation=2), (), False),
        (_ready(generation=2, revertible=1), _PREV, False),
        (_ready(generation=2, revertible=1), (*_PREV, _LEFTOVER), False),
        (_ready(generation=2, revertible=1), _NEW, False),
        (_ready(generation=2, revertible=1), (), True),
        (_ready(generation=2, revertible=1), _PREV[:2], True),
    ],
    ids=[
        'pending',
        'purged',
        'switched',
        'rebuild-left-over',
        'part-way-revert',
        'purge-started',
        'purge-dropping',
    ],
)
def test_an_unfinished_purge_is_a_revertible_switch_without_its_prev_tables(
    row: tuple[Any, ...], tables: tuple[str, ...], started: bool
) -> None:
    """__prev tables not all there and no __new beside them, with the switch revertible;
    __new with no __prev is a part-way revert, which unfinished_switch_problem reports."""
    ctx = _context(_StateDB(row, tables=tables))
    assert ctx.db is not None
    assert ctx.generation_state is not None
    problem = do_generation.unfinished_purge_problem(ctx.db, ctx.generation_state)
    if started:
        assert problem is not None
        assert 'generation 1 cannot be served again' in problem
        assert '--purge-generations' in problem
    else:
        assert problem is None


@pytest.mark.usefixtures('no_writers')
def test_abandon_is_refused_while_a_switch_has_stopped_part_way() -> None:
    """It would delete the rows the cart was pointed at, and drop nothing."""
    db = _StateDB(_ready(pending_generation=2, pending_state=PENDING_READY), tables=_PREV)
    with pytest.raises(do_generation.GenerationRefusedError, match='stopped part way'):
        do_generation_purge.abandon_generation(_context(db))
    assert [event for event in db.events if event not in ('lock', 'unlock')] == []


@pytest.mark.usefixtures('no_writers')
def test_the_purge_is_refused_while_a_revert_has_stopped_part_way() -> None:
    """It would delete the retired rows the cart was pointed back at; revertibility stays."""
    db = _StateDB(_ready(generation=2, revertible=1), tables=_NEW)
    with pytest.raises(do_generation.GenerationRefusedError, match='a revert of generation 2'):
        do_generation_purge.purge_generations(_context(db))
    assert db.row is not None
    assert db.row['revertible'] == 1
    assert [event for event in db.events if event not in ('lock', 'unlock')] == []


def test_a_writer_is_refused_while_a_switch_has_stopped_part_way() -> None:
    """A rebuild would replace the __new tables, and the next switch drop the __prev ones."""
    db = _StateDB(_ready(pending_generation=2, pending_state=PENDING_READY), tables=_PREV)
    with pytest.raises(do_generation.GenerationRefusedError, match='stopped part way'):
        do_generation.register_writer(_context(db))
    assert db.events == ['lock', 'unlock']


@pytest.mark.usefixtures('no_writers')
def test_abandon_is_refused_with_nothing_pending() -> None:
    """There is nothing to throw away."""
    db = _StateDB(_ready())
    with pytest.raises(do_generation.GenerationRefusedError, match='no generation is pending'):
        do_generation_purge.abandon_generation(_context(db))


def test_an_abandon_unreadies_the_generation_first_and_deletes_its_ranges_rows(
    monkeypatch: pytest.MonkeyPatch, no_writers: list[str]
) -> None:
    """A ready generation is marked writing before the first row goes, so an interrupted
    abandon leaves nothing a switch serves; the rows left in the id ranges it registered
    go before its registry rows, and no other generation's range is touched; the view
    loses its condition only once nothing is pending."""
    db = _StateDB(_ready(pending_generation=2, pending_state=PENDING_READY))
    steps: list[Any] = []

    def record(name: str) -> Any:
        """Return a stand-in step that records its name, the state, and its argument."""

        def step(ctx: Any, *args: Any) -> None:
            assert db.row is not None
            steps.append((name, db.row['pending_state'], *args))

        return step

    monkeypatch.setattr(do_generation_purge, '_abandoned_ids', lambda ctx, pending: ([8, 9], [3]))
    for module, name in [
        (do_import_tables, 'delete_observations'),
        (do_import_tables, 'delete_rows_in_id_ranges'),
        (do_import_tables, 'restore_retired_rows'),
        (bundle_registry, 'delete_generation_copies'),
        (bundle_registry, 'restore_retired_copies'),
        (table_swap, 'drop_swap_leftovers'),
    ]:
        monkeypatch.setattr(module, name, record(name))

    def refresh_view(ctx: Any, served: int | None) -> None:
        """Record the view's re-creation and the pending generation at that moment."""
        assert db.row is not None
        steps.append(('refresh_view', db.row['pending_generation'], served))

    monkeypatch.setattr(do_generation, 'refresh_view', refresh_view)
    monkeypatch.setattr(
        bundle_registry,
        'registered_ranges',
        lambda db, include_retired: [
            bundle_registry.BundleRange(1, 'A_1', 4, 1, 10, 'done', None, 1),
            bundle_registry.BundleRange(2, 'B_1', 4, 21, 10, 'importing', None, 2),
            bundle_registry.BundleRange(3, 'C_1', 4, 31, 5, 'done', None, 2),
        ],
    )
    do_generation_purge.abandon_generation(_context(db))
    assert [step[:2] for step in steps] == [
        ('delete_observations', PENDING_WRITING),
        ('delete_rows_in_id_ranges', PENDING_WRITING),
        ('restore_retired_rows', PENDING_WRITING),
        ('delete_generation_copies', PENDING_WRITING),
        ('restore_retired_copies', PENDING_WRITING),
        ('drop_swap_leftovers', PENDING_WRITING),
        ('refresh_view', None),
    ]
    assert steps[1][2] == [(21, 30), (31, 35)]
    assert steps[-1][2] is None
    assert db.row is not None
    assert (db.row['pending_generation'], db.row['pending_state']) == (None, None)


def test_the_rows_in_id_ranges_are_deleted_from_every_child_table() -> None:
    """Each range from every observation table but obs_general, by obs_general_id."""
    deleted: list[tuple[str, str, list[Any]]] = []

    class _DB:
        @staticmethod
        def quote_identifier(name: str) -> str:
            return f'`{name}`'

        @staticmethod
        def forget_table_names() -> None:
            """Read nothing."""

        @staticmethod
        def table_names(prefix: Any = None) -> list[str]:
            assert prefix == ['obs_']
            return ['obs_pds', 'obs_general', 'obs_files']

        @staticmethod
        def retrying(description: str, body: Any) -> Any:
            return body()

        @staticmethod
        def delete_rows(table: str, where: str, params: list[Any]) -> None:
            deleted.append((table, where, params))

    do_import_tables.delete_rows_in_id_ranges(make_context(db=_DB()), [(21, 30), (31, 35)])
    where = '`obs_general_id` BETWEEN %s AND %s'
    assert deleted == [
        ('obs_files', where, [21, 30]),
        ('obs_pds', where, [21, 30]),
        ('obs_files', where, [31, 35]),
        ('obs_pds', where, [31, 35]),
    ]


class _ReadOnlyStateDB(_StateDB):
    """A read-only stand-in the deploy chain's check reads, naming who holds a lock;
    its tables are a switch's __prev tables unless given."""

    def __init__(
        self,
        state: tuple[Any, ...] | None,
        *,
        lock_holder: int | None,
        tables: tuple[str, ...] = _PREV,
    ) -> None:
        super().__init__(state, tables=tables)
        self.lock_holder = lock_holder
        self.closed = False

    def named_lock_holder(self, name: str) -> int | None:
        """Return the generation lock's holder."""
        assert name == importdb.lock_name(self.db_schema, generations.GENERATION_LOCK)
        return self.lock_holder

    def close(self) -> None:
        """Record the close."""
        self.closed = True


@pytest.mark.parametrize(
    ('row', 'lock_holder', 'alive', 'option', 'problem'),
    [
        (_ready(pending_generation=2, pending_state=PENDING_READY), None, [], '--switch', None),
        (_ready(generation=2, revertible=1), None, [], '--switch', None),
        (_ready(generation=2, revertible=1), None, [], '--revert', None),
        (_ready(pending_generation=2, pending_state=PENDING_READY), None, [], '--revert', None),
        (
            _ready(pending_generation=2, pending_state=PENDING_VALIDATED),
            None,
            [],
            '--switch',
            'no pending generation is ready',
        ),
        (_ready(generation=2), None, [], '--revert', 'no switch is revertible'),
        (
            _ready(pending_generation=2, pending_state=PENDING_READY),
            41,
            [],
            '--switch',
            'another generation command holds',
        ),
        (
            _ready(pending_generation=2, pending_state=PENDING_READY),
            None,
            [7],
            '--switch',
            'import_process 7 still running',
        ),
        (None, None, [], '--switch', 'has no single schema_version row'),
    ],
    ids=[
        'ready',
        'completing',
        'revertible',
        'part-way',
        'unready',
        'purged',
        'locked',
        'writer',
        'no-row',
    ],
)
def test_the_deploy_chains_pre_check_names_what_the_command_would_refuse(
    monkeypatch: pytest.MonkeyPatch,
    row: tuple[Any, ...] | None,
    lock_holder: int | None,
    alive: list[int],
    option: str,
    problem: str | None,
) -> None:
    """The version row, the generation lock and the live writers, read without writing."""
    db = _ReadOnlyStateDB(row, lock_holder=lock_holder)
    monkeypatch.setattr(do_generation, '_alive_writers', lambda db: alive)
    found = do_generation.generation_problem(db, option.removeprefix('--'))  # type: ignore[arg-type]
    if problem is None:
        assert found is None
    else:
        assert found is not None
        assert problem in found
    assert db.events == []


@pytest.mark.parametrize(
    ('row', 'lock_holder', 'alive', 'problem'),
    [
        (_ready(pending_generation=2, pending_state=PENDING_WRITING), None, [], None),
        (_ready(pending_generation=2, pending_state=PENDING_READY), None, [], None),
        (_ready(), None, [], 'has no pending generation to continue (generation 1 served)'),
        (
            _ready(pending_generation=2, pending_state=PENDING_WRITING),
            41,
            [],
            'another generation command holds',
        ),
        (
            _ready(pending_generation=2, pending_state=PENDING_WRITING),
            None,
            [7],
            'import_process 7',
        ),
        (None, None, [], 'has no single schema_version row'),
    ],
    ids=['writing', 'ready', 'none-pending', 'locked', 'writer', 'no-row'],
)
def test_an_update_continues_only_a_pending_generation_no_invocation_is_writing(
    monkeypatch: pytest.MonkeyPatch,
    row: tuple[Any, ...] | None,
    lock_holder: int | None,
    alive: list[int],
    problem: str | None,
) -> None:
    """The version row, the generation lock and the live writers, read without writing:
    an update that skips --begin-generation with nothing pending would append to the
    served rows."""
    db = _ReadOnlyStateDB(row, lock_holder=lock_holder)
    monkeypatch.setattr(do_generation, '_alive_writers', lambda db: alive)
    found = do_generation.generation_problem(db, do_generation.CHECK_CONTINUE)  # type: ignore[arg-type]
    if problem is None:
        assert found is None
    else:
        assert found is not None
        assert problem in found
    assert db.events == []


@pytest.mark.parametrize(
    ('row', 'tables', 'lock_holder', 'problem'),
    [
        (_ready(), (), None, None),
        (_ready(generation=2, revertible=1), _PREV, None, None),
        (
            _ready(pending_generation=2, pending_state=PENDING_WRITING),
            (),
            None,
            'generation 2 of "opus_test" is pending',
        ),
        (_ready(), (), 41, 'another generation command holds'),
        (_ready(generation=2, revertible=1), _NEW, None, 'revert'),
        (_ready(generation=2, revertible=1), (), None, 'purge'),
        (None, (), None, 'has no single schema_version row'),
    ],
    ids=[
        'served',
        'revertible',
        'pending',
        'locked',
        'part-way-revert',
        'part-way-purge',
        'no-row',
    ],
)
def test_a_code_only_rebuild_is_refused_while_a_generation_is_pending(
    monkeypatch: pytest.MonkeyPatch,
    row: tuple[Any, ...] | None,
    tables: tuple[str, ...],
    lock_holder: int | None,
    problem: str | None,
) -> None:
    """A rebuild with a generation pending would leave its tables for the switch; one
    beside a switch, a revert or a purge stopped part way is refused as the import refuses
    it. A live writer does not refuse it: an append may run beside a rebuild."""
    db = _ReadOnlyStateDB(row, lock_holder=lock_holder, tables=tables)
    monkeypatch.setattr(do_generation, '_alive_writers', lambda db: [7])
    found = do_generation.generation_problem(db, do_generation.CHECK_REBUILD)  # type: ignore[arg-type]
    if problem is None:
        assert found is None
    else:
        assert found is not None
        assert problem in found
    assert db.events == []


def test_the_deploy_chains_pre_check_refuses_a_switch_or_revert_once_the_purge_has_started(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A revertible switch whose __prev tables are gone is not stopped for: the revert
    and the switch would be refused, and the purge finishes the work while the site
    serves."""
    db = _ReadOnlyStateDB(_ready(generation=2, revertible=1), lock_holder=None, tables=())
    monkeypatch.setattr(do_generation, '_alive_writers', lambda db: [])
    found = do_generation.generation_problem(db, do_generation.CHECK_REVERT)  # type: ignore[arg-type]
    assert found is not None
    assert 'the purge of the rows generation 2 retired has started' in found
    found = do_generation.generation_problem(db, do_generation.CHECK_SWITCH)  # type: ignore[arg-type]
    assert found is not None
    assert 'the purge of the rows generation 2 retired has started' in found
    assert db.events == []


# ------------------------------------------------------------------------------------
# The closing invocations with a pending generation
# ------------------------------------------------------------------------------------


@pytest.mark.parametrize(
    ('pending_state', 'runs'),
    [
        (PENDING_WRITING, False),
        (PENDING_FINALIZED, True),
        (PENDING_VALIDATED, True),
    ],
)
def test_validation_runs_only_on_a_finalized_generation(
    monkeypatch: pytest.MonkeyPatch, pending_state: str, runs: bool
) -> None:
    """Refused before finalization succeeds; marks the generation validated when it passes."""
    ran: list[bool] = []

    def passing(ctx: ImportContext) -> bool:
        """Record the run, and pass."""
        ran.append(True)
        return True

    monkeypatch.setattr(do_validate, 'do_validate', passing)
    db = _StateDB(_ready(pending_generation=2, pending_state=pending_state))
    assert _validate(_context(db)) is runs
    assert bool(ran) is runs
    assert db.row is not None
    assert db.row['pending_state'] == (PENDING_VALIDATED if runs else pending_state)


def test_a_failed_validation_leaves_the_generation_finalized(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A stamp never follows a failed validation."""
    monkeypatch.setattr(do_validate, 'do_validate', lambda ctx: False)
    db = _StateDB(_ready(pending_generation=2, pending_state=PENDING_VALIDATED))
    assert not _validate(_context(db))
    assert db.row is not None
    assert db.row['pending_state'] == PENDING_FINALIZED


@pytest.mark.parametrize(
    ('pending_state', 'stamped'), [(PENDING_VALIDATED, True), (PENDING_FINALIZED, False)]
)
def test_the_stamp_marks_only_a_validated_generation_ready(
    pending_state: str, stamped: bool
) -> None:
    """The version and state stay; only the pending state moves."""
    db = _StateDB(_ready(pending_generation=2, pending_state=pending_state))
    assert do_schema_version.write_schema_version(_context(db)) is stamped
    assert db.row is not None
    assert db.row['pending_state'] == (PENDING_READY if stamped else pending_state)
    assert (db.row['version'], db.row['state']) == (SCHEMA_VERSION, SCHEMA_STATE_READY)


class _ParamInfoDB:
    """A stand-in with one ``obs_general`` range pair, recording the queries it answers."""

    def __init__(self, tables: tuple[str, ...] = ()) -> None:
        self.tables = set(tables)
        self.selects: list[str] = []

    def forget_table_names(self) -> None:
        """Read nothing."""

    def table_exists(self, table: str) -> bool:
        """Hold the tables given."""
        return table in self.tables

    def table_names(self, prefix: str) -> list[str]:
        """Name ``obs_general`` alone."""
        return ['obs_general']

    def table_info(self, table: str) -> list[dict[str, Any]]:
        """Describe an id, the OPUS ID and one range pair."""
        return [{'field_name': name} for name in ('id', 'opus_id', 'time1', 'time2')]

    @staticmethod
    def quote_identifier(name: str) -> str:
        return f'`{name}`'

    def general_select(self, cmd: str, params: Any = None) -> list[tuple[Any, ...]]:
        """Describe every column, as a range, and find no bad row."""
        self.selects.append(cmd)
        if cmd.startswith('MIN('):
            return [(None,)]
        if 'COUNT(*)' in cmd:
            return [(1,)]
        if cmd.lstrip().startswith('`form_type`'):
            return [('RANGE',)]
        return []


def _pending_context(db: Any) -> ImportContext:
    """Return a context writing generation 2, finalized, on a stand-in."""
    ctx = make_context(db=db)
    ctx.generation_state = GenerationState(
        SCHEMA_VERSION, SCHEMA_STATE_READY, 1, 2, PENDING_FINALIZED, False
    )
    ctx.import_generation = 2
    return ctx


def test_a_pending_generation_is_validated_against_its_own_param_info() -> None:
    """The switch puts param_info__new in place; the live table describes the served rows."""
    db = _ParamInfoDB()
    ctx = _pending_context(db)
    assert do_validate.param_info_table(ctx) == 'param_info__new'
    assert do_validate.param_info_table(make_context(db=db)) == 'param_info'
    do_validate.validate_param_info(ctx)
    do_validate.validate_min_max_order(ctx)
    assert ctx.logger.messages_at('error') == []
    described = [cmd for cmd in db.selects if 'param_info' in cmd]
    assert described
    assert all('`param_info__new`' in cmd for cmd in described)


def test_a_pending_generation_with_no_param_info_of_its_own_fails_validation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The checks that read it are skipped, the others run, and the failure names it."""
    ran: list[str] = []
    for name in (
        'validate_param_info',
        'validate_nulls',
        'validate_min_max_order',
        'validate_filter_wavelength_consistency',
        'validate_orphans',
        'validate_pds_bundle_ids',
        'validate_previews',
        'validate_junctions',
        'validate_unique_opus_ids',
    ):
        monkeypatch.setattr(do_validate, name, lambda ctx, name=name: ran.append(name))
    ctx = _pending_context(_ParamInfoDB(tables=('param_info',)))
    monkeypatch.setattr(
        ctx.logger,
        'close',
        lambda *args, **kwargs: (0, len(ctx.logger.messages_at('error')), 0, 0),
    )
    assert not do_validate.do_validate(ctx)
    (error,) = ctx.logger.messages_at('error')
    assert '"param_info__new" does not exist' in error
    assert 'validate_param_info' not in ran
    assert 'validate_min_max_order' not in ran
    assert 'validate_orphans' in ran


def test_the_duplicate_step_retires_a_served_copy_and_deletes_a_pending_one(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Of each OPUS id's copies in the pending generation, the highest id is kept."""
    deleted: list[list[int]] = []
    monkeypatch.setattr(
        do_import_tables, 'delete_observations', lambda ctx, ids: deleted.append(list(ids))
    )
    updates: list[tuple[dict[str, Any], list[Any]]] = []
    answers = [[(3, 'a', 'B_1', 1), (9, 'a', 'B_2', 2), (7, 'b', 'B_2', 2), (8, 'b', 'B_2', 2)], []]

    class _DB:
        read_only = False
        transaction_rows = 100

        @staticmethod
        def quote_identifier(name: str) -> str:
            return f'`{name}`'

        @staticmethod
        def table_exists(name: str) -> bool:
            return True

        @staticmethod
        def general_select(cmd: str, params: Any = None) -> Any:
            assert params == [2, 2, 2, 2]
            return answers.pop(0)

        @staticmethod
        def update_row(table: str, row: dict[str, Any], where: str, params: list[Any]) -> int:
            updates.append((row, params))
            return len(params)

    ctx = make_context(db=_DB())
    ctx.generation_state = GenerationState(
        SCHEMA_VERSION, SCHEMA_STATE_READY, 1, 2, 'writing', False
    )
    ctx.import_generation = 2
    assert do_duplicate_ids.delete_duplicate_opus_ids(ctx)
    assert deleted == [[7]]
    assert updates == [({'removed_generation': 2}, [3])]


@pytest.mark.parametrize(
    ('arguments', 'rebuilds'),
    [
        (['--finalize'], True),
        (['--create-indexes'], True),
        (['--create-param-info'], True),
        (['--create-partables'], True),
        (['--create-table-names'], True),
        (['--validate'], False),
        (['--write-schema-version'], False),
        (['--analyze-tables'], False),
    ],
)
def test_every_rebuild_from_the_pending_generation_marks_it_writing(
    arguments: list[str], rebuilds: bool
) -> None:
    """A generation rebuilt after its stamp must be finalized, validated and stamped again."""
    args = _create_argument_parser().parse_args(arguments)
    expand_aggregate_options(args)
    assert _rebuilds_pending(args) is rebuilds


@pytest.mark.parametrize(
    ('arguments', 'rebuilds'),
    [
        (['--finalize'], True),
        (['--create-param-info'], True),
        (['--create-partables'], True),
        (['--create-table-names'], True),
        (['--create-cart'], True),
        (['--create-indexes'], False),
        (['--validate'], False),
        (['--write-schema-version'], False),
    ],
)
def test_a_rebuild_of_the_served_tables_is_told_from_the_other_steps(
    arguments: list[str], rebuilds: bool
) -> None:
    """The steps an unfinished revert refuses, since they drop the tables that mark it."""
    args = _create_argument_parser().parse_args(arguments)
    expand_aggregate_options(args)
    assert _rebuilds_served(args) is rebuilds


def test_a_generation_command_runs_alone() -> None:
    """Every step and every other command is refused beside it."""
    parser = _create_argument_parser()
    args = parser.parse_args(['--switch-generation', '--finalize', '--purge-generations'])
    assert _generation_conflicts(args) == '--finalize, --purge-generations'
    assert _generation_conflicts(parser.parse_args(['--switch-generation'])) == ''


def test_a_schema_with_no_version_row_writes_the_first_generation() -> None:
    """A fresh import's rows are added in generation 1."""
    ctx = _context(_StateDB(None))
    assert ctx.generation_state is None
    assert ctx.import_generation == generations.FIRST_GENERATION
    assert ctx.pending_generation is None
