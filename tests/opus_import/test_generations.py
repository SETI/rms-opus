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

from opus_import import generations, importdb, table_swap
from opus_import.cli import (
    _create_argument_parser,
    _generation_conflicts,
    _rebuilds_pending,
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
from opus_import.importdb.super import ImportDBSuper
from opus_import.schema_version import SCHEMA_STATE_READY, SCHEMA_VERSION
from opus_import.steps import (
    do_django,
    do_duplicate_ids,
    do_generation,
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

    def _execute(
        self, cmd: str, param_list: Any = None, cur: Any = None, mutates: bool = False
    ) -> None:
        self.executed.append((cmd, param_list))


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


def test_dropping_obs_general_drops_the_view_before_the_table() -> None:
    """DROP TABLE refuses a view, and the view reads the table."""
    db = _RecordingDB({'obs_general'})
    db.drop_table('obs_general')
    assert [cmd for cmd, _ in db.executed] == [
        'DROP VIEW IF EXISTS `obs_general`',
        'DROP TABLE `obs_general_rows`',
    ]


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


def test_a_bundle_is_retired_a_chunk_at_a_time_through_its_key() -> None:
    """Only rows an earlier generation added and none retired, transaction_rows at a time."""
    updates: list[tuple[str, Any, str, list[Any]]] = []

    class _DB:
        transaction_rows = 2
        read_only = False

        @staticmethod
        def quote_identifier(name: str) -> str:
            return f'`{name}`'

        @staticmethod
        def retrying(description: str, body: Any) -> Any:
            return body()

        def update_row(self, table: str, row: Any, where: str, params: list[Any]) -> int:
            updates.append((table, row, where, params))
            return 2 if len(updates) == 1 else 1

    retired = do_import_tables.retire_bundle_rows(make_context(db=_DB()), 'B_1', 5)
    assert retired == 3
    table, row, where, params = updates[0]
    assert (table, row) == ('obs_general', {'removed_generation': 5})
    assert where == (
        '`bundle_id`=%s AND `added_generation` < %s AND `removed_generation` IS NULL LIMIT %s'
    )
    assert params == ['B_1', 5, 2]
    assert len(updates) == 2


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
    ) -> None:
        self.row = (
            None if state is None else dict(zip(generations.STATE_COLUMNS, state, strict=True))
        )
        self.lock_free = lock_free
        self.tables = set(tables)
        self.events: list[str] = []

    def forget_table_names(self) -> None:
        """Read nothing."""

    def table_exists(self, table: str) -> bool:
        """Hold the version table, when there is a row, and the tables given."""
        return (table == 'schema_version' and self.row is not None) or table in self.tables

    def read_rows(self, table: str, columns: list[str], *args: Any) -> list[tuple[Any, ...]]:
        """Return the version row's columns."""
        assert self.row is not None
        return [tuple(self.row[column] for column in columns)]

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
        """Record a drop."""
        self.events.append(f'drop {table}')


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
    # A stale __prev table, which only an interrupted purge leaves, goes first.
    assert 'drop param_info__prev' in db.events


@pytest.mark.usefixtures('no_writers')
@pytest.mark.parametrize(
    ('row', 'reason'),
    [
        (_ready(pending_generation=2, pending_state=PENDING_WRITING), 'already has the pending'),
        (_ready(state='appending'), 'is appending, not ready'),
        (_ready(version=SCHEMA_VERSION - 1), 'and this release is version'),
        (_ready(generation=2, revertible=1), 'can still revert to generation 1'),
    ],
    ids=['pending', 'appending', 'version', 'revertible'],
)
def test_begin_is_refused_on_a_schema_it_cannot_start_one_in(
    row: tuple[Any, ...], reason: str
) -> None:
    """Nothing is written, and the refusal says why."""
    db = _StateDB(row)
    with pytest.raises(do_generation.GenerationRefusedError, match=reason):
        do_generation.begin_generation(_context(db))
    assert not any(event.startswith('update') for event in db.events)


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

    monkeypatch.setattr(do_generation.import_processes, 'create_process_table', lambda db: None)
    monkeypatch.setattr(do_generation.import_processes, 'start_importer', start_importer)
    monkeypatch.setattr(db, 'open_sibling_connection', open_sibling_connection, raising=False)
    assert do_generation.register_writer(ctx) is importer
    assert opened == [db]
    assert ctx.generation_state is not None
    assert ctx.generation_state.pending_state == PENDING_FINALIZED
    assert db.events == ['lock', 'unlock']


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
    """With nothing pending and the switch revertible, the steps run again for it."""
    db = _StateDB(_ready(generation=2, revertible=1))
    do_generation.switch_generation(_context(db))
    assert switch_steps == ['swap', 'cart 2', 'reset', 'view 2']
    assert not any(event.startswith('update') for event in db.events)


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
    db = _StateDB(_ready(generation=2, revertible=1))
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


def test_a_revert_after_the_purge_has_started_is_refused(switch_steps: list[str]) -> None:
    """The purge's first statement ends revertibility."""
    db = _StateDB(_ready(generation=2))
    with pytest.raises(do_generation.GenerationRefusedError, match='no switch is revertible'):
        do_generation.revert_generation(_context(db))
    assert switch_steps == []


@pytest.mark.usefixtures('no_writers')
def test_the_purge_ends_revertibility_first_and_is_refused_with_a_pending_generation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A pending generation must be switched or abandoned before the purge."""
    db = _StateDB(_ready(generation=2, pending_generation=3, pending_state=PENDING_WRITING))
    with pytest.raises(do_generation.GenerationRefusedError, match='generation 3 is pending'):
        do_generation.purge_generations(_context(db))
    assert not any(event.startswith('update') for event in db.events)


#: The auxiliary tables' names after a switch's swap and after a revert's.
_PREV = tuple(table_swap.swap_prev_name(table) for table in do_generation.AUX_TABLES)
_NEW = tuple(table_swap.swap_new_name(table) for table in do_generation.AUX_TABLES)


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


@pytest.mark.usefixtures('no_writers')
def test_abandon_is_refused_while_a_switch_has_stopped_part_way() -> None:
    """It would delete the rows the cart was pointed at, and drop nothing."""
    db = _StateDB(_ready(pending_generation=2, pending_state=PENDING_READY), tables=_PREV)
    with pytest.raises(do_generation.GenerationRefusedError, match='stopped part way'):
        do_generation.abandon_generation(_context(db))
    assert [event for event in db.events if event not in ('lock', 'unlock')] == []


@pytest.mark.usefixtures('no_writers')
def test_the_purge_is_refused_while_a_revert_has_stopped_part_way() -> None:
    """It would delete the retired rows the cart was pointed back at; revertibility stays."""
    db = _StateDB(_ready(generation=2, revertible=1), tables=_NEW)
    with pytest.raises(do_generation.GenerationRefusedError, match='a revert of generation 2'):
        do_generation.purge_generations(_context(db))
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
        do_generation.abandon_generation(_context(db))


class _ReadOnlyStateDB(_StateDB):
    """A read-only stand-in the deploy chain's pre-check opens, naming who holds a lock."""

    def __init__(self, state: tuple[Any, ...] | None, *, lock_holder: int | None) -> None:
        super().__init__(state)
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
    opened: list[dict[str, Any]] = []

    def get_db(*args: Any, **kwargs: Any) -> _ReadOnlyStateDB:
        opened.append(kwargs)
        return db

    monkeypatch.setattr(importdb, 'get_db', get_db)
    monkeypatch.setattr(do_generation, '_alive_writers', lambda db: alive)
    found = do_generation.generation_command_problem(f'{option}-generation')
    if problem is None:
        assert found is None
    else:
        assert found is not None
        assert problem in found
    assert opened == [{'read_only': True}]
    assert db.closed
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
