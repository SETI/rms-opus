"""The bundle registry, registration, and the plain import loop that keeps it, without a
server.

The loop runs against an in-memory stand-in holding the registry and the version table
(`conftest.RegistryDB`), with each bundle's size estimate given and each bundle's delete
and load replaced by a recording function, so what is asserted is the order of the work,
the ranges, and the state each bundle ends in. The queue importer's loop is in
``test_queue_importer.py``.
"""

from __future__ import annotations

import datetime
from typing import Any

import pytest

from opus_import import bundle_registry, cli, import_util, importdb
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
    do_register,
)

from .conftest import (
    BUNDLE_SIZE,
    RegistryDB,
    default_arguments,
    make_context,
    registry_rows,
    run_import_loop,
)


def test_each_bundle_is_deleted_then_loaded_unchecked_and_ends_done(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A fresh import registers its bundles, and moves each through importing to done."""
    db = RegistryDB()
    succeeded, _ctx = run_import_loop(db, ['B_1', 'B_2'], monkeypatch)
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
    db = RegistryDB()
    succeeded, _ctx = run_import_loop(db, ['B_1', 'B_2', 'B_3'], monkeypatch, logging=('B_2',))
    assert not succeeded
    assert db.states() == {'B_1': 'done', 'B_2': 'failed', 'B_3': 'done'}


def test_a_bundle_whose_import_fails_stops_the_loop(monkeypatch: pytest.MonkeyPatch) -> None:
    """The bundles after it stay pending."""
    db = RegistryDB()
    succeeded, _ctx = run_import_loop(db, ['B_1', 'B_2', 'B_3'], monkeypatch, failing=('B_2',))
    assert not succeeded
    assert db.states() == {'B_1': 'done', 'B_2': 'failed', 'B_3': 'pending'}


def test_ignore_errors_marks_every_bundle_done_and_goes_on(monkeypatch: pytest.MonkeyPatch) -> None:
    """``--ignore-errors`` is how a debugging run reaches a finished registry."""
    db = RegistryDB()
    succeeded, _ctx = run_import_loop(
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
    db = RegistryDB()
    succeeded, _ctx = run_import_loop(db, ['GO_0001', 'COCIRS_0101', 'COISS_2002'], monkeypatch)
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
    db = RegistryDB(
        {
            SCHEMA_VERSION_TABLE: [{'version': SCHEMA_VERSION, 'state': SCHEMA_STATE_READY}],
            'import_bundle': registry_rows(
                {'B_1': 'done', 'B_7': 'pending', 'B_4': 'failed', 'B_6': 'importing'}
            ),
        }
    )
    succeeded, ctx = run_import_loop(db, ['B_9', 'B_1'], monkeypatch)
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
    db = RegistryDB({'import_bundle': registry_rows(states)})
    succeeded, ctx = run_import_loop(db, ['B_1', 'B_5'], monkeypatch, **arguments)
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
    db = RegistryDB({'import_bundle': registry_rows({'B_1': 'done'})})
    original = do_register.register_bundles

    def register_then_lose(*args: Any, **kwargs: Any) -> Any:
        registration = original(*args, **kwargs)
        db.tables['import_bundle'][0]['state'] = 'importing'
        return registration

    monkeypatch.setattr(do_register, 'register_bundles', register_then_lose)
    succeeded, _ctx = run_import_loop(db, ['B_1'], monkeypatch)
    assert not succeeded
    assert db.states() == {'B_1': 'importing'}
    assert not [event for event in db.events if event.startswith(('delete', 'load'))]


def test_registration_numbers_new_bundles_in_order_after_the_last_range(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A re-registered bundle keeps its number and range; new ones follow the last range."""
    db = RegistryDB({'import_bundle': registry_rows({'B_1': 'done', 'B_2': 'done'})})
    db.tables['import_bundle'][1]['id_capacity'] = 5
    succeeded, _ctx = run_import_loop(db, ['B_9', 'B_2', 'B_3'], monkeypatch, register_bundles=True)
    assert succeeded
    ranges = {
        row['bundle_id']: (row['bundle_number'], row['first_id'], row['id_capacity'])
        for row in db.tables['import_bundle']
    }
    capacity = bundle_registry.ID_CAPACITY_FACTOR * BUNDLE_SIZE
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
    db = RegistryDB(
        {
            SCHEMA_VERSION_TABLE: [{'version': SCHEMA_VERSION, 'state': SCHEMA_STATE_READY}],
            'import_bundle': registry_rows({'B_1': 'done', 'B_2': 'done', 'B_4': 'importing'}),
        }
    )
    succeeded, _ctx = run_import_loop(db, ['B_2', 'B_4', 'B_3'], monkeypatch, register_bundles=True)
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
    db = RegistryDB(
        {
            SCHEMA_VERSION_TABLE: [dict(row) for row in ready],
            'import_bundle': registry_rows({'B_1': 'done', 'B_2': 'done'}),
        }
    )
    succeeded, _ctx = run_import_loop(db, ['B_1', 'B_2'], monkeypatch, register_bundles=True)
    assert succeeded
    assert db.states() == {'B_1': 'done', 'B_2': 'done'}
    assert db.tables[SCHEMA_VERSION_TABLE] == ready


def test_registration_refused_for_a_label_registers_nothing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A bundle whose labels declare no row count refuses the whole registration."""
    db = RegistryDB()

    def size(bundle: str) -> int:
        if bundle == 'B_2':
            raise bundle_registry.RegistrationError('B_2 has no row count')
        return BUNDLE_SIZE

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
    db = RegistryDB({'import_bundle': registry_rows(states)})
    # Failed under importer 3; B_4 is importing under no queue importer.
    db.tables['import_bundle'][2]['process_id'] = 3
    succeeded, _ctx = run_import_loop(db, named, monkeypatch, do_import=False, requeue=True)
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
    db = RegistryDB({'import_bundle': registry_rows(states)})
    original = bundle_registry.registered_bundles

    def read_then_taken(ctx: Any) -> list[tuple[str, str]]:
        found = original(ctx)
        db.tables['import_bundle'][0]['state'] = taken_to
        return found

    monkeypatch.setattr(bundle_registry, 'registered_bundles', read_then_taken)
    succeeded, ctx = run_import_loop(db, ['B_3'], monkeypatch, do_import=False, requeue=True)
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
    db = RegistryDB({'import_bundle': registry_rows({'B_4': 'importing'})})

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
    db = RegistryDB({'import_bundle': registry_rows({'B_1': 'done'})})
    db.read_only = True
    monkeypatch.setattr(db, 'insert_rows', lambda table_name, rows: None)
    monkeypatch.setattr(do_register, 'size_estimate', lambda bundle: BUNDLE_SIZE)
    monkeypatch.setattr(do_import_mult, 'register_pinned_fields', lambda ctx: None)
    ctx = make_context(db=db)

    do_register.register_bundles(ctx, ['B_1', 'B_2'], make_pending=False)

    assert db.states() == {'B_1': 'done'}
    ids = bundle_registry.bundle_ids(ctx, 'B_2')
    assert ids is not None
    capacity = bundle_registry.ID_CAPACITY_FACTOR * BUNDLE_SIZE
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
    db = RegistryDB({SCHEMA_VERSION_TABLE: [dict(row) for row in ready], 'import_bundle': []})
    succeeded, _ctx = run_import_loop(db, named, monkeypatch)
    assert succeeded
    assert db.tables[SCHEMA_VERSION_TABLE] == ready
    assert db.states() == {}


def test_a_fresh_import_does_not_resume(monkeypatch: pytest.MonkeyPatch) -> None:
    """Without a version row the named bundles are imported, and only they."""
    db = RegistryDB({'import_bundle': registry_rows({'B_4': 'failed'})})
    run_import_loop(db, ['B_9'], monkeypatch)
    assert [event for event in db.events if event.startswith('delete')] == ['delete B_9']
    assert db.states() == {'B_4': 'failed', 'B_9': 'done'}


def test_deleting_bundles_removes_their_registry_rows(monkeypatch: pytest.MonkeyPatch) -> None:
    """A failed bundle the operator drops no longer holds up the schema."""
    db = RegistryDB({'import_bundle': registry_rows({'B_4': 'failed', 'B_5': 'done'})})
    succeeded, _ctx = run_import_loop(
        db, ['B_4'], monkeypatch, do_import=False, delete_bundles=True
    )
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
    db = RegistryDB(
        {
            SCHEMA_VERSION_TABLE: [{'version': SCHEMA_VERSION, 'state': state}],
            'import_bundle': registry_rows({'B_4': 'done'}),
        }
    )
    succeeded, _ctx = run_import_loop(
        db, ['B_4'], monkeypatch, do_import=False, delete_bundles=True
    )
    assert succeeded
    assert db.tables[SCHEMA_VERSION_TABLE] == [{'version': SCHEMA_VERSION, 'state': after}]


def test_deleting_nothing_leaves_a_finished_schema_ready(monkeypatch: pytest.MonkeyPatch) -> None:
    """With no bundle named there is nothing to delete, so nothing changes."""
    ready = [{'version': SCHEMA_VERSION, 'state': SCHEMA_STATE_READY}]
    db = RegistryDB({SCHEMA_VERSION_TABLE: [dict(row) for row in ready]})
    succeeded, _ctx = run_import_loop(db, [], monkeypatch, do_import=False, delete_bundles=True)
    assert succeeded
    assert db.tables[SCHEMA_VERSION_TABLE] == ready


@pytest.mark.parametrize(
    ('tables', 'finished'),
    [
        ({}, True),
        ({'import_bundle': registry_rows({'B_1': 'done'})}, True),
        (
            {'import_bundle': registry_rows({'B_1': 'done', 'B_3': 'failed', 'B_2': 'pending'})},
            False,
        ),
    ],
    ids=['no-registry', 'all-done', 'unfinished'],
)
def test_finalization_and_the_version_step_refuse_an_unfinishedregistry_rows(
    tables: dict[str, list[dict[str, Any]]], finished: bool
) -> None:
    """The refusal names every bundle that is not done, with its state."""
    ctx = make_context(db=RegistryDB(tables))
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
    ctx = make_context(db=RegistryDB())
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
    db = RegistryDB({'import_bundle': registry_rows(states)})
    db.tables['import_bundle'][1]['process_id'] = 5
    monkeypatch.setattr(db, 'named_lock_holder', lambda name: lock_holder)
    succeeded, ctx = run_import_loop(db, ['B_3', 'B_4'], monkeypatch, do_import=False, requeue=True)
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
    db = RegistryDB({'import_bundle': registry_rows({'B_4': 'importing'})})
    original = do_import._queue_holders

    def checked_then_claimed(ctx: Any, bundle_ids: list[str]) -> list[tuple[str, int]]:
        found = original(ctx, bundle_ids)
        db.tables['import_bundle'][0]['process_id'] = 9
        return found

    monkeypatch.setattr(do_import, '_queue_holders', checked_then_claimed)
    succeeded, ctx = run_import_loop(db, ['B_4'], monkeypatch, do_import=False, requeue=True)
    assert not succeeded
    assert db.events == []
    assert db.tables['import_bundle'][0]['process_id'] == 9
    (error,) = ctx.logger.messages_at('error')
    assert error == 'B_4 changed state before it was requeued; nothing was deleted'
