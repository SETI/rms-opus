"""The bundle registry, registration, and the import loops that keep it, without a server.

The loops run against an in-memory stand-in holding the registry and the version table,
with each bundle's size estimate given and each bundle's delete and load replaced by a
recording function, so what is asserted is the order of the work, the ranges, and the
state each bundle ends in.
"""

from __future__ import annotations

import contextlib
import datetime
from collections.abc import Iterator
from typing import Any

import pytest

from opus_import import bundle_registry, cli, import_processes, import_util, importdb
from opus_import.schema_version import (
    SCHEMA_STATE_APPENDING,
    SCHEMA_STATE_READY,
    SCHEMA_VERSION,
    SCHEMA_VERSION_TABLE,
)
from opus_import.steps import (
    do_import,
    do_import_mult,
    do_import_tables,
    do_recover,
    do_register,
)

from .conftest import default_arguments, make_context


class _RegistryDB:
    """A stand-in holding a few small tables as lists of rows, and recording events."""

    def __init__(self, tables: dict[str, list[dict[str, Any]]] | None = None) -> None:
        """Hold the tables.

        Parameters:
            tables: Each table's rows, keyed by table; none for an empty schema.
        """
        self.tables = {} if tables is None else tables
        self.db_schema = 'opus_test'
        self.events: list[str] = []
        self.on_lock: Any = None
        self.read_only = False

    def table_exists(self, table_name: str) -> bool:
        """Say whether a table is held."""
        return table_name in self.tables

    def forget_table_names(self) -> None:
        """Record the table names being read again."""
        self.events.append('reread tables')

    def table_names(self, prefix: Any = None) -> list[str]:
        """Return the tables, which hold no key a fresh import's check looks for."""
        return sorted(self.tables)

    def read_table_keys(self) -> dict[str, list[Any]]:
        """Report no keys."""
        return {}

    def create_table(self, table_name: str, schema: Any, ignore_if_exists: bool = True) -> bool:
        """Create an empty table."""
        self.tables.setdefault(table_name, [])
        return True

    def read_rows(
        self,
        table_name: str,
        columns: list[str],
        where: str | None = None,
        where_params: list[Any] | None = None,
    ) -> list[tuple[Any, ...]]:
        """Return the rows' values in `columns` order, as the registry's reads select them."""
        rows = self.tables[table_name]
        if where is not None and where.startswith('1=1 ORDER BY'):
            rows = sorted(rows, key=lambda row: row['bundle_number'])
        elif where is not None:
            assert where_params is not None
            rows = self._matching(table_name, where, where_params[0])
        return [tuple(row[column] for column in columns) for row in rows]

    def quote_identifier(self, name: str) -> str:
        """Backtick-quote a name."""
        return f'`{name}`'

    def _matching(self, table_name: str, where: str, value: Any) -> list[dict[str, Any]]:
        """Return the rows a ```column`=%s`` clause selects."""
        column = where.split('`')[1]
        return [row for row in self.tables[table_name] if row[column] == value]

    def insert_rows(self, table_name: str, rows: list[dict[str, Any]]) -> None:
        """Append rows, numbering a registry row as its auto-incremented key would."""
        for row in rows:
            added = dict(row)
            if table_name == 'import_bundle':
                numbers = [existing['bundle_number'] for existing in self.tables[table_name]]
                added['bundle_number'] = max(numbers, default=0) + 1
            self.tables[table_name].append(added)

    def update_row(
        self, table_name: str, row: dict[str, Any], where: str, where_params: list[Any]
    ) -> int:
        """Assign `row`'s values to the rows the clause selects, and count them."""
        matched = self._matching(table_name, where, where_params[0])
        for existing in matched:
            existing.update(row)
        return len(matched)

    def conditional_update(
        self, table_name: str, row: dict[str, Any], where: str, where_params: list[Any]
    ) -> int:
        """Assign `row` to the bundle the clause names if its state, its start when
        named, and a NULL ``process_id`` when asked for, are the ones the clause expects;
        return how many rows changed."""
        bundle_id, *rest = where_params
        state_count = where.split(' IN (', 1)[1].split(')', 1)[0].count('%s')
        states, started = rest[:state_count], rest[state_count:]
        unheld = where.endswith('`process_id` IS NULL')
        changed = 0
        for existing in self._matching(table_name, '`bundle_id`=%s', bundle_id):
            if (
                existing['state'] in states
                and (not started or existing.get('started_at') == started[0])
                and (not unheld or existing.get('process_id') is None)
            ):
                existing.update(row)
                changed += 1
        return changed

    def delete_rows(self, table_name: str, where: str, where_params: list[Any]) -> None:
        """Delete the rows the clause selects."""
        doomed = self._matching(table_name, where, where_params[0])
        self.tables[table_name] = [row for row in self.tables[table_name] if row not in doomed]

    @contextlib.contextmanager
    def named_lock(self, name: str) -> Iterator[None]:
        """Record the lock being held, and run `on_lock` while it is."""
        self.events.append(f'lock {name}')
        try:
            if self.on_lock is not None:
                self.on_lock()
            yield
        finally:
            self.events.append('unlock')

    @contextlib.contextmanager
    def transaction(self) -> Iterator[None]:
        """Record the transaction."""
        self.events.append('begin')
        yield
        self.events.append('commit')

    def retrying(self, description: str, body: Any, expected: Any = None) -> Any:
        """Run the body once, as a transaction."""
        with self.transaction():
            return body()

    def lock_first_row(
        self, table_name: str, column: str, where: str, where_params: list[Any], order_by: list[str]
    ) -> Any:
        """Return the first pending row of the ones the claim may take, highest first."""
        state, *names = where_params
        excluded_count = where.split('NOT IN (', 1)[1].count('%s') if 'NOT IN' in where else 0
        among = names[: len(names) - excluded_count]
        excluded = names[len(names) - excluded_count :]
        rows = [
            row
            for row in self.tables[table_name]
            if row['state'] == state
            and (not among or row['bundle_id'] in among)
            and row['bundle_id'] not in excluded
        ]
        rows.sort(key=lambda row: tuple(row[name] for name in order_by), reverse=True)
        return rows[0][column] if rows else None

    @contextlib.contextmanager
    def foreign_keys_unchecked(self) -> Iterator[None]:
        """Record the checks going off and coming back on."""
        self.events.append('checks off')
        try:
            yield
        finally:
            self.events.append('checks on')

    @staticmethod
    def named_lock_holder(name: str) -> int | None:
        """Report every named lock free."""
        return None

    def close(self) -> None:
        """Record the connection closing."""
        self.events.append('close')

    logger = None

    def states(self) -> dict[str, str]:
        """Return each registered bundle's state."""
        return {row['bundle_id']: row['state'] for row in self.tables.get('import_bundle', [])}


class _Importer:
    """An importer that always holds its lock."""

    process_id = 1
    name = 'opus:lock'

    @staticmethod
    def held() -> bool:
        """Say the lock is held."""
        return True

    @staticmethod
    def exit() -> None:
        """Exit, holding nothing."""


#: The size estimate every bundle is given, so each range is a thousand ids.
_SIZE = 10


def _registry(states: dict[str, str]) -> list[dict[str, Any]]:
    """Return registry rows holding `states`, numbered and ranged in the order given."""
    capacity = bundle_registry.ID_CAPACITY_FACTOR * _SIZE
    return [
        {
            'bundle_number': number,
            'bundle_id': bundle,
            'size_estimate': _SIZE,
            'first_id': (number - 1) * capacity,
            'id_capacity': capacity,
            'state': state,
            'started_at': None,
            'finished_at': None,
            'process_id': None,
            'rows_done': 0,
            'losses': 0,
        }
        for number, (bundle, state) in enumerate(states.items(), start=1)
    ]


def _run(
    db: _RegistryDB,
    named: list[str],
    monkeypatch: pytest.MonkeyPatch,
    *,
    logging: tuple[str, ...] = (),
    failing: tuple[str, ...] = (),
    during: dict[str, Any] | None = None,
    **arguments: Any,
) -> tuple[bool, Any]:
    """Run the import loop over `named`, each bundle's work recorded on `db`.

    Parameters:
        db: The stand-in.
        named: The bundles the command line names.
        monkeypatch: Replaces the bundle's delete and load.
        logging: Bundles whose import logs an error and still returns True.
        failing: Bundles whose import returns False.
        during: What to call, with the context, while a bundle imports, by bundle.
        arguments: Options to set, by attribute.

    Returns:
        What `do_import_steps` returned, and the context.
    """
    monkeypatch.setattr(import_util, 'yield_import_bundle_ids', lambda ctx: iter(named))
    monkeypatch.setattr(do_register, 'size_estimate', lambda bundle: _SIZE)
    monkeypatch.setattr(do_import_mult, 'register_pinned_fields', lambda ctx: None)
    monkeypatch.setattr(
        do_import_tables,
        'delete_bundle_from_obs_tables',
        lambda ctx, bundle: db.events.append(f'delete {bundle}'),
    )

    def load(ctx: Any, bundle: str) -> bool:
        db.events.append(f'load {bundle} ({db.states().get(bundle)})')
        if during and bundle in during:
            during[bundle](ctx)
        if bundle in logging:
            import_util.log_error(ctx, f'{bundle} went wrong')
        return bundle not in failing

    monkeypatch.setattr(do_import, 'import_one_bundle', load)
    monkeypatch.setattr(import_processes, 'start_importer', lambda lock_db, log_path: _Importer())
    monkeypatch.setattr(db, 'open_sibling_connection', lambda: db, raising=False)

    def release(ctx: Any, bundle: str, number: int, process_id: int, state: str | None) -> bool:
        do_import_tables.delete_bundle_from_obs_tables(ctx, bundle)
        if state is not None:
            db.update_row('import_bundle', {'state': state}, '`bundle_id`=%s', [bundle])
        return True

    monkeypatch.setattr(do_recover, 'release_bundle', release)
    args = default_arguments()
    args.do_import = not (arguments.get('join') or arguments.get('register_bundles'))
    for name, value in arguments.items():
        setattr(args, name, value)
    ctx = make_context(db=db, args=args)
    return do_import.do_import_steps(ctx), ctx


def test_each_bundle_is_deleted_then_loaded_unchecked_and_ends_done(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A fresh import registers its bundles, and moves each through importing to done."""
    db = _RegistryDB()
    succeeded, _ctx = _run(db, ['B_1', 'B_2'], monkeypatch)
    assert succeeded
    assert db.states() == {'B_1': 'done', 'B_2': 'done'}
    assert [
        event for event in db.events if not event.startswith(('lock', 'unlock', 'begin', 'commit'))
    ] == [
        'delete B_1',
        'checks off',
        'load B_1 (importing)',
        'checks on',
        'delete B_2',
        'checks off',
        'load B_2 (importing)',
        'checks on',
    ]
    assert SCHEMA_VERSION_TABLE not in db.tables


def test_a_bundle_that_logs_an_error_is_failed_and_the_loop_goes_on(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A logged error fails its bundle only; the invocation fails at the end."""
    db = _RegistryDB()
    succeeded, _ctx = _run(db, ['B_1', 'B_2', 'B_3'], monkeypatch, logging=('B_2',))
    assert not succeeded
    assert db.states() == {'B_1': 'done', 'B_2': 'failed', 'B_3': 'done'}


def test_a_bundle_whose_import_fails_stops_the_loop(monkeypatch: pytest.MonkeyPatch) -> None:
    """The bundles after it stay pending."""
    db = _RegistryDB()
    succeeded, _ctx = _run(db, ['B_1', 'B_2', 'B_3'], monkeypatch, failing=('B_2',))
    assert not succeeded
    assert db.states() == {'B_1': 'done', 'B_2': 'failed', 'B_3': 'pending'}


def test_ignore_errors_marks_every_bundle_done_and_goes_on(monkeypatch: pytest.MonkeyPatch) -> None:
    """``--ignore-errors`` is how a debugging run reaches a finished registry."""
    db = _RegistryDB()
    succeeded, _ctx = _run(
        db,
        ['B_1', 'B_2', 'B_3'],
        monkeypatch,
        logging=('B_1',),
        failing=('B_2',),
        ignore_errors=True,
    )
    assert succeeded
    assert db.states() == {'B_1': 'done', 'B_2': 'done', 'B_3': 'done'}


def test_a_bundle_opus_skips_is_never_registered(monkeypatch: pytest.MonkeyPatch) -> None:
    """Its import is still asked for, which logs that it is ignored, but no row waits on it."""
    db = _RegistryDB()
    succeeded, _ctx = _run(db, ['GO_0001', 'COCIRS_0101', 'COISS_2002'], monkeypatch)
    assert succeeded
    assert db.states() == {'COISS_2002': 'done'}
    assert [event for event in db.events if event.startswith('load')] == [
        'load GO_0001 (None)',
        'load COCIRS_0101 (None)',
        'load COISS_2002 (importing)',
    ]


@pytest.mark.parametrize(
    ('bundle', 'imported'),
    [('GO_0001', False), ('COCIRS_0101', False), ('COISS_2002', True), ('NO_SUCH_1', True)],
)
def test_opus_imports_every_bundle_but_the_ones_with_no_instrument_class(
    bundle: str, imported: bool
) -> None:
    """A bundle with no entry is imported, and fails there; one with an empty entry is not."""
    assert do_import_tables.opus_imports_bundle(bundle) is imported


def test_an_append_resumes_the_pending_and_failed_bundles_first(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Every registered bundle pending or failed and not named, in registration order, then
    the named ones; a bundle left importing waits for --requeue."""
    db = _RegistryDB(
        {
            SCHEMA_VERSION_TABLE: [{'version': SCHEMA_VERSION, 'state': SCHEMA_STATE_READY}],
            'import_bundle': _registry(
                {'B_1': 'done', 'B_7': 'pending', 'B_4': 'failed', 'B_6': 'importing'}
            ),
        }
    )
    succeeded, ctx = _run(db, ['B_9', 'B_1'], monkeypatch)
    assert succeeded
    assert ctx.import_path == do_import.IMPORT_PATH_APPEND
    assert [event for event in db.events if event.startswith('delete')] == [
        'delete B_7',
        'delete B_4',
        'delete B_9',
        'delete B_1',
    ]
    assert db.states() == {
        'B_1': 'done',
        'B_4': 'done',
        'B_6': 'importing',
        'B_7': 'done',
        'B_9': 'done',
    }
    assert db.tables[SCHEMA_VERSION_TABLE] == [
        {'version': SCHEMA_VERSION, 'state': SCHEMA_STATE_APPENDING}
    ]


@pytest.mark.parametrize(
    'arguments',
    [{}, {'do_import': False, 'delete_bundles': True}],
    ids=['import', 'delete-bundles'],
)
def test_a_bundle_another_process_holds_is_refused_and_nothing_changes(
    arguments: dict[str, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    """``--import`` and ``--delete-bundles`` name an importing bundle: refused, naming it
    and the requeue, before anything is deleted or moved."""
    states = {'B_1': 'done', 'B_5': 'importing'}
    db = _RegistryDB({'import_bundle': _registry(states)})
    succeeded, ctx = _run(db, ['B_1', 'B_5'], monkeypatch, **arguments)
    assert not succeeded
    assert db.states() == states
    assert not [event for event in db.events if event.startswith(('delete', 'load'))]
    (message,) = ctx.logger.messages_at('fatal')
    assert 'Bundle B_5 is importing in another process' in message
    assert '"opus_import --requeue B_5"' in message


def test_a_bundle_taken_after_registration_is_not_imported_twice(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The move to importing is conditional: a bundle another importer claimed between
    this invocation's registration and its turn is left to that importer."""
    db = _RegistryDB({'import_bundle': _registry({'B_1': 'done'})})
    original = do_register.register_bundles

    def register_then_lose(*args: Any, **kwargs: Any) -> Any:
        registration = original(*args, **kwargs)
        db.tables['import_bundle'][0]['state'] = 'importing'
        return registration

    monkeypatch.setattr(do_register, 'register_bundles', register_then_lose)
    succeeded, _ctx = _run(db, ['B_1'], monkeypatch)
    assert not succeeded
    assert db.states() == {'B_1': 'importing'}
    assert not [event for event in db.events if event.startswith(('delete', 'load'))]


def test_a_stale_holder_neither_finishes_nor_deletes_a_requeued_bundle(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A bundle returned to the queue and taken by another importer while its first ran is
    left to the second: the first's failure deletes nothing and moves nothing."""
    db = _RegistryDB({'import_bundle': _registry({'B_1': 'pending'})})

    def taken_by_another(ctx: Any, bundle: str) -> bool:
        db.events.append(f'load {bundle}')
        db.tables['import_bundle'][0]['process_id'] = 2
        import_util.log_error(ctx, f'{bundle} went wrong')
        return True

    def lock_row(
        table_name: str, columns: list[str], where: str, where_params: list[Any]
    ) -> tuple[Any, ...] | None:
        rows = db._matching(table_name, where, where_params[0])
        return tuple(rows[0][column] for column in columns) if rows else None

    monkeypatch.setattr(import_util, 'yield_import_bundle_ids', lambda ctx: iter([]))
    monkeypatch.setattr(
        do_import_tables,
        'delete_bundle_from_obs_tables',
        lambda ctx, bundle: db.events.append(f'delete {bundle}'),
    )
    monkeypatch.setattr(do_import, 'import_one_bundle', taken_by_another)
    monkeypatch.setattr(import_processes, 'start_importer', lambda lock_db, log_path: _Importer())
    monkeypatch.setattr(db, 'open_sibling_connection', lambda: db, raising=False)
    monkeypatch.setattr(db, 'lock_row', lock_row, raising=False)
    args = default_arguments()
    args.join = True
    ctx = make_context(db=db, args=args)
    assert not do_import.do_import_steps(ctx)
    assert db.states() == {'B_1': 'importing'}
    assert db.tables['import_bundle'][0]['process_id'] == 2
    assert [event for event in db.events if event.startswith(('delete', 'load'))] == [
        'delete B_1',
        'load B_1',
    ]
    assert any(
        import_processes.WHILE_DELETING in message for message in ctx.logger.messages_at('fatal')
    )


def test_a_failed_bundle_is_deleted_under_its_hold_and_only_then_marked_failed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """While the cleanup deletes, the bundle is still importing under the importer, its
    registry row held, so no claim or plain import can take it and load rows the delete
    would take (`do_recover.release_bundle`)."""
    db = _RegistryDB({'import_bundle': _registry({'B_1': 'pending'})})
    deleted_in: list[str | None] = []

    def failing_load(ctx: Any, bundle: str) -> bool:
        import_util.log_error(ctx, f'{bundle} went wrong')
        return True

    def lock_row(
        table_name: str, columns: list[str], where: str, where_params: list[Any]
    ) -> tuple[Any, ...] | None:
        rows = db._matching(table_name, where, where_params[0])
        return tuple(rows[0][column] for column in columns) if rows else None

    monkeypatch.setattr(import_util, 'yield_import_bundle_ids', lambda ctx: iter([]))
    monkeypatch.setattr(
        do_import_tables,
        'delete_bundle_from_obs_tables',
        lambda ctx, bundle: deleted_in.append(db.states().get(bundle)),
    )
    monkeypatch.setattr(do_import, 'import_one_bundle', failing_load)
    monkeypatch.setattr(import_processes, 'start_importer', lambda lock_db, log_path: _Importer())
    monkeypatch.setattr(db, 'open_sibling_connection', lambda: db, raising=False)
    monkeypatch.setattr(db, 'lock_row', lock_row, raising=False)
    args = default_arguments()
    args.join = True
    ctx = make_context(db=db, args=args)

    assert not do_import.do_import_steps(ctx)

    assert deleted_in == ['importing', 'importing']
    assert db.states() == {'B_1': 'failed'}


def test_an_empty_claim_waits_for_a_registration_and_claims_again(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A bundle a registration commits while the first claim found nothing is claimed."""
    db = _RegistryDB({'import_bundle': _registry({'B_1': 'done'})})

    def registration_commits() -> None:
        db.tables['import_bundle'].append({**_registry({'B_2': 'pending'})[0], 'bundle_number': 2})
        db.on_lock = None

    db.on_lock = registration_commits
    succeeded, _ctx = _run(db, [], monkeypatch, join=True)
    assert succeeded
    assert db.states() == {'B_1': 'done', 'B_2': 'done'}
    lock = importdb.lock_name('opus_test', do_register.REGISTRATION_LOCK)
    assert db.events[:3] == ['begin', 'commit', f'lock {lock}']


def test_a_queue_importer_with_no_registry_to_claim_from_is_refused(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Before its first claim it waits for a registration in progress and reads the
    tables again; with still no registry it fails, naming the registration step."""
    db = _RegistryDB()
    succeeded, ctx = _run(db, [], monkeypatch, join=True)
    assert not succeeded
    lock = importdb.lock_name('opus_test', do_register.REGISTRATION_LOCK)
    assert db.events == [f'lock {lock}', 'unlock', 'reread tables']
    (message,) = ctx.logger.messages_at('fatal')
    assert message.startswith('"opus_test" has no bundle registry, so there is nothing to claim')
    assert '"opus_import --register-bundles"' in message


def test_a_queue_importer_claims_from_a_registry_a_registration_in_progress_creates(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A registry created while the importer waited on registration's lock is claimed
    from, though the table names it read first lacked it."""
    db = _RegistryDB()

    def registration_commits() -> None:
        db.tables['import_bundle'] = _registry({'B_1': 'pending'})
        db.on_lock = None

    db.on_lock = registration_commits
    succeeded, _ctx = _run(db, [], monkeypatch, join=True)
    assert succeeded
    assert db.states() == {'B_1': 'done'}


def test_a_queue_importer_honors_exclusions(monkeypatch: pytest.MonkeyPatch) -> None:
    """``--exclude-bundles`` with no bundles named still keeps the importer off them."""
    db = _RegistryDB({'import_bundle': _registry({'B_1': 'pending', 'B_2': 'pending'})})
    succeeded, _ctx = _run(db, [], monkeypatch, join=True, exclude_bundles='B_2')
    assert succeeded
    assert db.states() == {'B_1': 'done', 'B_2': 'pending'}


def test_registration_numbers_new_bundles_in_order_after_the_last_range(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A re-registered bundle keeps its number and range; new ones follow the last range."""
    db = _RegistryDB({'import_bundle': _registry({'B_1': 'done', 'B_2': 'done'})})
    db.tables['import_bundle'][1]['id_capacity'] = 5
    succeeded, _ctx = _run(db, ['B_9', 'B_2', 'B_3'], monkeypatch, register_bundles=True)
    assert succeeded
    ranges = {
        row['bundle_id']: (row['bundle_number'], row['first_id'], row['id_capacity'])
        for row in db.tables['import_bundle']
    }
    capacity = bundle_registry.ID_CAPACITY_FACTOR * _SIZE
    assert ranges == {
        'B_1': (1, 0, capacity),
        'B_2': (2, capacity, 5),
        'B_9': (3, capacity + 5, capacity),
        'B_3': (4, 2 * capacity + 5, capacity),
    }
    # A fresh import's registration leaves registered bundles as they are, so a rerun
    # after an interruption keeps what is done.
    assert db.states() == {'B_1': 'done', 'B_2': 'done', 'B_9': 'pending', 'B_3': 'pending'}
    assert [event for event in db.events if not event.startswith('delete')] == [
        f'lock {importdb.lock_name("opus_test", do_register.REGISTRATION_LOCK)}',
        'begin',
        'commit',
        'unlock',
    ]


def test_registration_leaves_registered_bundles_as_they_are(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """On a finished schema a bundle added becomes pending and the schema appending; the
    registered ones keep their states, importing among them."""
    db = _RegistryDB(
        {
            SCHEMA_VERSION_TABLE: [{'version': SCHEMA_VERSION, 'state': SCHEMA_STATE_READY}],
            'import_bundle': _registry({'B_1': 'done', 'B_2': 'done', 'B_4': 'importing'}),
        }
    )
    succeeded, _ctx = _run(db, ['B_2', 'B_4', 'B_3'], monkeypatch, register_bundles=True)
    assert succeeded
    assert db.states() == {'B_1': 'done', 'B_2': 'done', 'B_4': 'importing', 'B_3': 'pending'}
    assert db.tables[SCHEMA_VERSION_TABLE] == [
        {'version': SCHEMA_VERSION, 'state': SCHEMA_STATE_APPENDING}
    ]
    assert not [event for event in db.events if event.startswith(('delete', 'load'))]


def test_registering_again_changes_nothing_on_a_finished_schema(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A rerun of the registration ``opus_import_all --prepare`` runs adds nothing, moves
    no bundle, and leaves the schema ready."""
    ready = [{'version': SCHEMA_VERSION, 'state': SCHEMA_STATE_READY}]
    db = _RegistryDB(
        {
            SCHEMA_VERSION_TABLE: [dict(row) for row in ready],
            'import_bundle': _registry({'B_1': 'done', 'B_2': 'done'}),
        }
    )
    succeeded, _ctx = _run(db, ['B_1', 'B_2'], monkeypatch, register_bundles=True)
    assert succeeded
    assert db.states() == {'B_1': 'done', 'B_2': 'done'}
    assert db.tables[SCHEMA_VERSION_TABLE] == ready


def test_registration_refused_for_a_label_registers_nothing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A bundle whose labels declare no row count refuses the whole registration."""
    db = _RegistryDB()

    def size(bundle: str) -> int:
        if bundle == 'B_2':
            raise bundle_registry.RegistrationError('B_2 has no row count')
        return _SIZE

    args = default_arguments()
    args.register_bundles = True
    monkeypatch.setattr(import_util, 'yield_import_bundle_ids', lambda ctx: iter(['B_1', 'B_2']))
    monkeypatch.setattr(do_register, 'size_estimate', size)
    ctx = make_context(db=db, args=args)
    assert not do_import.do_import_steps(ctx)
    assert db.states() == {}
    assert ctx.logger.messages_at('fatal') == ['B_2 has no row count']


def test_registration_skips_the_bundles_opus_does_not_import() -> None:
    """GO_0001 and COCIRS_0101 have no instrument class: dropped, logged, order kept."""
    ctx = make_context()
    kept = do_register.registrable_bundles(
        ctx, ['GO_0001', 'COISS_2002', 'COCIRS_0101', 'VGISS_6109']
    )
    assert kept == ['COISS_2002', 'VGISS_6109']
    assert ctx.logger.messages_at('debug') == [
        'Ignoring registration of GO_0001',
        'Ignoring registration of COCIRS_0101',
    ]


def test_a_queue_importer_takes_the_largest_first_and_goes_on_past_a_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Claims run largest first, a failed bundle is deleted and failed, and none is retried."""
    db = _RegistryDB(
        {
            'import_bundle': _registry(
                {'B_1': 'pending', 'B_2': 'pending', 'B_3': 'pending', 'B_4': 'done'}
            )
        }
    )
    for row, size in zip(db.tables['import_bundle'], (50, 30, 30, 99), strict=True):
        row['size_estimate'] = size
    succeeded, _ctx = _run(db, [], monkeypatch, join=True, logging=('B_3',))
    assert not succeeded
    # Equal sizes are claimed highest number first.
    assert [event for event in db.events if event.startswith(('delete', 'load'))] == [
        'delete B_1',
        'load B_1 (importing)',
        'delete B_3',
        'load B_3 (importing)',
        'delete B_3',
        'delete B_2',
        'load B_2 (importing)',
    ]
    assert db.states() == {'B_1': 'done', 'B_2': 'done', 'B_3': 'failed', 'B_4': 'done'}


def test_a_queue_importer_given_bundles_claims_only_those(monkeypatch: pytest.MonkeyPatch) -> None:
    """The bundles named, as ``--sets`` names them, are the only ones claimed."""
    db = _RegistryDB({'import_bundle': _registry({'B_1': 'pending', 'B_2': 'pending'})})
    succeeded, _ctx = _run(db, ['B_2'], monkeypatch, join=True, bundles=['B_2'])
    assert succeeded
    assert db.states() == {'B_1': 'pending', 'B_2': 'done'}
    # The claim names the importer, and the bundle keeps it once done.
    assert [row['process_id'] for row in db.tables['import_bundle']] == [None, 1]


def _two_pending() -> _RegistryDB:
    """Return a registry of B_1, the larger, and B_2, both pending."""
    db = _RegistryDB({'import_bundle': _registry({'B_1': 'pending', 'B_2': 'pending'})})
    db.tables['import_bundle'][0]['size_estimate'] = 50
    return db


def test_an_interrupted_importer_finishes_its_bundle_and_claims_nothing_more(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The first interrupt drains: B_1 is done, B_2 left pending, and the run fails."""
    db = _two_pending()

    def interrupt(ctx: Any) -> None:
        ctx.interrupts = 1

    succeeded, ctx = _run(db, [], monkeypatch, join=True, during={'B_1': interrupt})

    assert not succeeded
    assert db.states() == {'B_1': 'done', 'B_2': 'pending'}
    assert ctx.logger.messages_at('fatal') == [
        'Interrupted: this importer claims nothing more and exits'
    ]


@pytest.mark.parametrize(
    'raised',
    [KeyboardInterrupt(), import_processes.LostImporterError('lost "opus:lock"')],
    ids=['second-interrupt', 'lost-lock'],
)
def test_an_aborted_bundle_goes_back_to_the_queue_on_a_fresh_connection(
    raised: BaseException, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A second interrupt or a lost lock: the connection is closed and replaced, the
    bundle's rows deleted and the bundle pending, nothing more claimed, and the run fails."""
    db = _two_pending()

    def stop(ctx: Any) -> None:
        raise raised

    succeeded, ctx = _run(db, [], monkeypatch, join=True, during={'B_1': stop})

    assert not succeeded
    assert db.states() == {'B_1': 'pending', 'B_2': 'pending'}
    events = [event for event in db.events if event.startswith(('delete', 'load', 'close'))]
    assert events == ['delete B_1', 'load B_1 (importing)', 'close', 'delete B_1']
    (fatal,) = ctx.logger.messages_at('fatal')
    assert fatal in (
        'Interrupted twice: this importer returned B_1 to the queue, and exits',
        'lost "opus:lock"',
    )


@pytest.mark.parametrize('where', ['after-claim', 'failure-path'])
def test_a_second_interrupt_outside_the_import_still_aborts_the_bundle_it_holds(
    where: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Between the claim's commit and the work, or in a failed bundle's own release, the
    bundle the registry has under the importer is aborted, and the log says so."""
    db = _two_pending()
    during: dict[str, Any] = {}
    if where == 'after-claim':

        def interrupted_hold(site: str) -> str | None:
            if site == do_import.HOLD_AFTER_CLAIM_FAULT_SITE:
                raise KeyboardInterrupt
            return None

        monkeypatch.setattr(do_import, 'import_fault_argument', interrupted_hold)
        expected = ['close', 'delete B_1']
    else:

        def interrupt_the_failed_release(ctx: Any) -> None:
            release = do_recover.release_bundle

            def interrupted(*args: Any) -> bool:
                if args[-1] == bundle_registry.BUNDLE_FAILED:
                    raise KeyboardInterrupt
                return release(*args)

            monkeypatch.setattr(do_recover, 'release_bundle', interrupted)

        during['B_1'] = interrupt_the_failed_release
        expected = ['delete B_1', 'close', 'delete B_1']

    succeeded, ctx = _run(db, [], monkeypatch, join=True, failing=('B_1',), during=during)

    assert not succeeded
    assert db.states() == {'B_1': 'pending', 'B_2': 'pending'}
    assert [event for event in db.events if event.startswith(('delete', 'close'))] == expected
    assert ctx.logger.messages_at('fatal') == [
        'Interrupted twice: this importer returned B_1 to the queue, and exits'
    ]


@pytest.mark.parametrize(
    ('named', 'returned'),
    [(['B_3', 'B_4'], True), (['B_3', 'B_1'], False), (['B_9'], False), ([], False)],
    ids=['failed-and-importing', 'done', 'unregistered', 'none'],
)
def test_requeue_returns_only_failed_and_importing_bundles(
    named: list[str], returned: bool, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Any other bundle named refuses the whole requeue, which then changes nothing."""
    states = {'B_1': 'done', 'B_2': 'pending', 'B_3': 'failed', 'B_4': 'importing'}
    db = _RegistryDB({'import_bundle': _registry(states)})
    # Failed under importer 3; B_4 is importing under no queue importer.
    db.tables['import_bundle'][2]['process_id'] = 3
    succeeded, _ctx = _run(db, named, monkeypatch, do_import=False, requeue=True)
    assert succeeded is returned
    if returned:
        assert db.events == ['delete B_3', 'delete B_4']
        assert db.states() == {**states, 'B_3': 'pending', 'B_4': 'pending'}
        assert all(row['process_id'] is None for row in db.tables['import_bundle'])
    else:
        assert db.events == []
        assert db.states() == states


@pytest.mark.parametrize('taken_to', ['done', 'pending'], ids=['imported', 'requeued'])
def test_requeue_deletes_nothing_of_a_bundle_another_process_took_after_the_check(
    taken_to: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The requeue holds a bundle before deleting its rows: one that left ``failed``
    after the states were read keeps its rows and its state."""
    states = {'B_3': 'failed'}
    db = _RegistryDB({'import_bundle': _registry(states)})
    original = bundle_registry.registered_bundles

    def read_then_taken(ctx: Any) -> list[tuple[str, str]]:
        found = original(ctx)
        db.tables['import_bundle'][0]['state'] = taken_to
        return found

    monkeypatch.setattr(bundle_registry, 'registered_bundles', read_then_taken)
    succeeded, ctx = _run(db, ['B_3'], monkeypatch, do_import=False, requeue=True)
    assert not succeeded
    assert db.events == []
    assert db.states() == {'B_3': taken_to}
    (error,) = ctx.logger.messages_at('error')
    assert error == 'B_3 changed state before it was requeued; nothing was deleted'


def test_requeue_returns_a_bundle_only_while_its_own_hold_stands(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A bundle taken from the requeue's hold while its rows were deleted is left as the
    other process has it."""
    db = _RegistryDB({'import_bundle': _registry({'B_4': 'importing'})})

    def delete_then_lose(ctx: Any, bundle: str) -> None:
        db.events.append(f'delete {bundle}')
        db.tables['import_bundle'][0]['started_at'] = datetime.datetime(2000, 1, 1)

    monkeypatch.setattr(do_import_tables, 'delete_bundle_from_obs_tables', delete_then_lose)
    ctx = make_context(db=db)

    assert not do_import.requeue_bundles(ctx, ['B_4'])

    assert db.events == ['delete B_4']
    assert db.states() == {'B_4': 'importing'}
    (error,) = ctx.logger.messages_at('error')
    assert error == 'B_4 changed state while it was requeued'


def test_a_read_only_run_imports_a_new_bundle_from_the_range_it_planned(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Registration writes nothing, and the bundle's ids come from the range it would
    have registered, after the last one the registry holds."""
    db = _RegistryDB({'import_bundle': _registry({'B_1': 'done'})})
    db.read_only = True
    monkeypatch.setattr(db, 'insert_rows', lambda table_name, rows: None)
    monkeypatch.setattr(do_register, 'size_estimate', lambda bundle: _SIZE)
    monkeypatch.setattr(do_import_mult, 'register_pinned_fields', lambda ctx: None)
    ctx = make_context(db=db)

    do_register.register_bundles(ctx, ['B_1', 'B_2'], make_pending=False)

    assert db.states() == {'B_1': 'done'}
    ids = bundle_registry.bundle_ids(ctx, 'B_2')
    assert ids is not None
    capacity = bundle_registry.ID_CAPACITY_FACTOR * _SIZE
    assert (ids.range.bundle_number, ids.range.first_id, ids.range.id_capacity) == (
        2,
        capacity,
        capacity,
    )


@pytest.mark.parametrize('named', [[], ['GO_0001']], ids=['nothing-named', 'only-skipped'])
def test_an_append_with_nothing_to_import_leaves_the_schema_ready(
    named: list[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Nothing unfinished and nothing OPUS imports named: no bundle, and still ``ready``."""
    ready = [{'version': SCHEMA_VERSION, 'state': SCHEMA_STATE_READY}]
    db = _RegistryDB({SCHEMA_VERSION_TABLE: [dict(row) for row in ready], 'import_bundle': []})
    succeeded, _ctx = _run(db, named, monkeypatch)
    assert succeeded
    assert db.tables[SCHEMA_VERSION_TABLE] == ready
    assert db.states() == {}


def test_a_fresh_import_does_not_resume(monkeypatch: pytest.MonkeyPatch) -> None:
    """Without a version row the named bundles are imported, and only they."""
    db = _RegistryDB({'import_bundle': _registry({'B_4': 'failed'})})
    _run(db, ['B_9'], monkeypatch)
    assert [event for event in db.events if event.startswith('delete')] == ['delete B_9']
    assert db.states() == {'B_4': 'failed', 'B_9': 'done'}


def test_deleting_bundles_removes_their_registry_rows(monkeypatch: pytest.MonkeyPatch) -> None:
    """A failed bundle the operator drops no longer holds up the schema."""
    db = _RegistryDB({'import_bundle': _registry({'B_4': 'failed', 'B_5': 'done'})})
    succeeded, _ctx = _run(db, ['B_4'], monkeypatch, do_import=False, delete_bundles=True)
    assert succeeded
    assert db.events == ['delete B_4']
    assert db.states() == {'B_5': 'done'}


@pytest.mark.parametrize(
    ('state', 'after'),
    [
        (SCHEMA_STATE_READY, SCHEMA_STATE_APPENDING),
        (SCHEMA_STATE_APPENDING, SCHEMA_STATE_APPENDING),
    ],
    ids=['ready', 'appending'],
)
def test_deleting_bundles_from_a_finished_schema_unfinishes_it(
    state: str, after: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The deletion changes a served schema, so it is ``appending`` until stamped again."""
    db = _RegistryDB(
        {
            SCHEMA_VERSION_TABLE: [{'version': SCHEMA_VERSION, 'state': state}],
            'import_bundle': _registry({'B_4': 'done'}),
        }
    )
    succeeded, _ctx = _run(db, ['B_4'], monkeypatch, do_import=False, delete_bundles=True)
    assert succeeded
    assert db.tables[SCHEMA_VERSION_TABLE] == [{'version': SCHEMA_VERSION, 'state': after}]


def test_deleting_nothing_leaves_a_finished_schema_ready(monkeypatch: pytest.MonkeyPatch) -> None:
    """With no bundle named there is nothing to delete, so nothing changes."""
    ready = [{'version': SCHEMA_VERSION, 'state': SCHEMA_STATE_READY}]
    db = _RegistryDB({SCHEMA_VERSION_TABLE: [dict(row) for row in ready]})
    succeeded, _ctx = _run(db, [], monkeypatch, do_import=False, delete_bundles=True)
    assert succeeded
    assert db.tables[SCHEMA_VERSION_TABLE] == ready


@pytest.mark.parametrize(
    ('tables', 'finished'),
    [
        ({}, True),
        ({'import_bundle': _registry({'B_1': 'done'})}, True),
        ({'import_bundle': _registry({'B_1': 'done', 'B_3': 'failed', 'B_2': 'pending'})}, False),
    ],
    ids=['no-registry', 'all-done', 'unfinished'],
)
def test_finalization_and_the_version_step_refuse_an_unfinished_registry(
    tables: dict[str, list[dict[str, Any]]], finished: bool
) -> None:
    """The refusal names every bundle that is not done, with its state."""
    ctx = make_context(db=_RegistryDB(tables))
    assert cli._registry_finished(ctx, '--finalize') is finished
    if finished:
        assert ctx.logger.messages_at('fatal') == []
    else:
        assert ctx.logger.messages_at('fatal') == [
            '--finalize refuses to run while bundles in the bundle registry are not done: '
            'B_3 (failed), B_2 (pending). Import them again, or remove them with '
            '--delete-bundles'
        ]


def test_the_registry_reads_nothing_when_it_has_no_table() -> None:
    """An import that never registered anything leaves nothing unfinished."""
    ctx = make_context(db=_RegistryDB())
    assert bundle_registry.unfinished_bundles(ctx) == []
    bundle_registry.unregister_bundles(ctx, ['B_1'])


def test_ranges_ascend_and_one_past_the_largest_id_is_refused() -> None:
    """Each range starts where the last ended; one ending past INT UNSIGNED's maximum fails."""
    rows = bundle_registry.plan_ranges(7, [('A', 2), ('B', 3)])
    assert [(row['bundle_id'], row['first_id'], row['id_capacity']) for row in rows] == [
        ('A', 7, 200),
        ('B', 207, 300),
    ]
    last = bundle_registry.MAX_OBSERVATION_ID + 1
    assert bundle_registry.plan_ranges(last - 100, [('C', 1)])[0]['first_id'] == last - 100
    with pytest.raises(bundle_registry.RegistrationError, match='Bundle D'):
        bundle_registry.plan_ranges(last - 99, [('D', 1)])


def test_a_bundle_that_outgrows_its_range_is_refused_naming_it() -> None:
    """The refusal names the bundle, its capacity and the rows it declared."""
    ids = bundle_registry.BundleIds(bundle_registry.BundleRange(3, 'B_3', 2, 500, 200, 'importing'))
    assert ids.take(150) == 500
    assert ids.take(50) == 650
    with pytest.raises(bundle_registry.BundleIdRangeError) as raised:
        ids.take(1)
    assert 'B_3' in str(raised.value)
    assert 'its 200 observation ids' in str(raised.value)
    assert 'the 2 rows' in str(raised.value)


def test_a_lock_name_fits_mysqls_limit_and_belongs_to_its_schema() -> None:
    """Any schema name gives a name of at most 64 characters, distinct per schema and parts."""
    long_schema = 'x' * 200
    name = importdb.lock_name(long_schema, 'register')
    assert name.startswith(importdb.LOCK_NAME_PREFIX)
    assert len(name) <= 64
    assert name != importdb.lock_name('other', 'register')
    assert name != importdb.lock_name(long_schema, 'importer', 1)
    assert importdb.lock_name('s', 'importer', 1) == importdb.lock_name('s', 'importer', '1')


@pytest.mark.parametrize('lock_holder', [77, None], ids=['alive', 'lock-free'])
def test_requeue_refuses_a_bundle_a_queue_importer_holds(
    lock_holder: int | None, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A queue importer's bundle is left to recovery, whether its importer is alive or
    not, and nothing named is returned."""
    states = {'B_3': 'failed', 'B_4': 'importing'}
    db = _RegistryDB({'import_bundle': _registry(states)})
    db.tables['import_bundle'][1]['process_id'] = 5
    monkeypatch.setattr(db, 'named_lock_holder', lambda name: lock_holder)
    succeeded, ctx = _run(db, ['B_3', 'B_4'], monkeypatch, do_import=False, requeue=True)
    assert not succeeded
    assert db.events == []
    assert db.states() == states
    (fatal,) = ctx.logger.messages_at('fatal')
    assert 'B_4 (importing under importer 5, whose bundle recovery returns' in fatal


def test_requeue_deletes_nothing_of_a_bundle_a_queue_importer_took_after_the_check(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A bundle read ``importing`` under no importer, then returned and claimed by a
    queue importer before the hold, is left to that importer with its rows."""
    db = _RegistryDB({'import_bundle': _registry({'B_4': 'importing'})})
    original = do_import._queue_holders

    def checked_then_claimed(ctx: Any, bundle_ids: list[str]) -> list[tuple[str, int]]:
        found = original(ctx, bundle_ids)
        db.tables['import_bundle'][0]['process_id'] = 9
        return found

    monkeypatch.setattr(do_import, '_queue_holders', checked_then_claimed)
    succeeded, ctx = _run(db, ['B_4'], monkeypatch, do_import=False, requeue=True)
    assert not succeeded
    assert db.events == []
    assert db.tables['import_bundle'][0]['process_id'] == 9
    (error,) = ctx.logger.messages_at('error')
    assert error == 'B_4 changed state before it was requeued; nothing was deleted'
