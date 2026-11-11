"""The queue importer's loop (``opus_import --join``), without a server.

It runs against the in-memory registry stand-in (`conftest.RegistryDB`), with each
bundle's delete and load replaced by a recording function: which bundles it claims and in
what order, what it does when an import fails, when the registry no longer names it, and
when it is interrupted.
"""

from __future__ import annotations

import signal
from typing import Any

import pytest

from opus_import import bundle_registry, cli, import_processes, import_util, importdb
from opus_import.steps import do_import, do_import_tables, do_recover, do_register

from .conftest import (
    HeldImporter,
    RegistryDB,
    default_arguments,
    make_context,
    registry_rows,
    run_import_loop,
)


def _join_one_bundle(
    db: RegistryDB,
    load: Any,
    delete: Any,
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[bool, Any]:
    """Run a queue importer over `db` with each bundle's load and delete replaced, through
    the real release of its bundle (`do_recover.release_bundle`).

    Parameters:
        db: The stand-in.
        load: Replaces `do_import.import_one_bundle`.
        delete: Replaces `do_import_tables.delete_bundle_from_obs_tables`.
        monkeypatch: Makes the replacements.

    Returns:
        What `do_import.do_import_steps` returned, and the context.
    """
    monkeypatch.setattr(import_util, 'yield_import_bundle_ids', lambda ctx: iter([]))
    monkeypatch.setattr(do_import_tables, 'delete_bundle_from_obs_tables', delete)
    monkeypatch.setattr(do_import, 'import_one_bundle', load)
    monkeypatch.setattr(
        import_processes, 'start_importer', lambda lock_db, log_path: HeldImporter()
    )
    args = default_arguments()
    args.join = True
    ctx = make_context(db=db, args=args)
    return do_import.do_import_steps(ctx), ctx


def _record_delete(db: RegistryDB) -> Any:
    """Return a bundle delete that records itself on `db`."""
    return lambda ctx, bundle: db.events.append(f'delete {bundle}')


def test_a_stale_holder_neither_finishes_nor_deletes_a_requeued_bundle(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A bundle returned to the queue and taken by another importer while its first ran is
    left to the second: the first's failure deletes nothing and moves nothing."""
    db = RegistryDB({'import_bundle': registry_rows({'B_1': 'pending'})})

    def taken_by_another(ctx: Any, bundle: str) -> bool:
        db.events.append(f'load {bundle}')
        db.tables['import_bundle'][0]['process_id'] = 2
        import_util.log_error(ctx, f'{bundle} went wrong')
        return True

    succeeded, ctx = _join_one_bundle(db, taken_by_another, _record_delete(db), monkeypatch)
    assert not succeeded
    assert db.states() == {'B_1': 'importing'}
    assert db.tables['import_bundle'][0]['process_id'] == 2
    assert [event for event in db.events if event.startswith(('delete', 'load'))] == [
        'delete B_1',
        'load B_1',
    ]
    assert any(
        import_processes.WHILE_DELETING in message for message in ctx.logger.messages_at('fatal')
    )


def test_an_importer_whose_bundle_was_given_to_another_does_not_mark_it_done(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A bundle recovered and claimed by importer 2 while importer 1 loaded it: importer
    1's load succeeds, but its move to ``done`` matches no row, so it stops as a lost
    importer, leaving the bundle and its rows to importer 2 and logging no import error."""
    db = RegistryDB({'import_bundle': registry_rows({'B_1': 'pending'})})

    def taken_by_another(ctx: Any, bundle: str) -> bool:
        db.events.append(f'load {bundle}')
        db.tables['import_bundle'][0]['process_id'] = 2
        return True

    succeeded, ctx = _join_one_bundle(db, taken_by_another, _record_delete(db), monkeypatch)

    assert not succeeded
    assert db.states() == {'B_1': 'importing'}
    assert db.tables['import_bundle'][0]['process_id'] == 2
    assert [event for event in db.events if event.startswith(('delete', 'load'))] == [
        'delete B_1',
        'load B_1',
    ]
    assert ctx.logger.messages_at('error') == []
    assert any(
        import_processes.WHILE_FINISHING in message for message in ctx.logger.messages_at('fatal')
    )


def test_a_failed_bundle_is_deleted_under_its_hold_and_only_then_marked_failed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """While the cleanup deletes, the bundle is still importing under the importer, its
    registry row held, so no claim or plain import can take it and load rows the delete
    would take (`do_recover.release_bundle`)."""
    db = RegistryDB({'import_bundle': registry_rows({'B_1': 'pending'})})
    deleted_in: list[str | None] = []

    def failing_load(ctx: Any, bundle: str) -> bool:
        import_util.log_error(ctx, f'{bundle} went wrong')
        return True

    def delete(ctx: Any, bundle: str) -> None:
        deleted_in.append(db.states().get(bundle))

    succeeded, _ctx = _join_one_bundle(db, failing_load, delete, monkeypatch)

    assert not succeeded
    assert deleted_in == ['importing', 'importing']
    assert db.states() == {'B_1': 'failed'}


def test_an_empty_claim_waits_for_a_registration_and_claims_again(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A bundle a registration commits while the first claim found nothing is claimed."""
    db = RegistryDB({'import_bundle': registry_rows({'B_1': 'done'})})

    def registration_commits() -> None:
        db.tables['import_bundle'].append(
            {**registry_rows({'B_2': 'pending'})[0], 'bundle_number': 2}
        )
        db.on_lock = None

    db.on_lock = registration_commits
    succeeded, _ctx = run_import_loop(db, [], monkeypatch, join=True)
    assert succeeded
    assert db.states() == {'B_1': 'done', 'B_2': 'done'}
    lock = importdb.lock_name('opus_test', do_register.REGISTRATION_LOCK)
    assert db.events[:3] == ['begin', 'commit', f'lock {lock}']


def test_a_queue_importer_with_no_registry_to_claim_from_is_refused(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Before its first claim it waits for a registration in progress and reads the
    tables again; with still no registry it fails, naming the registration step."""
    db = RegistryDB()
    succeeded, ctx = run_import_loop(db, [], monkeypatch, join=True)
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
    db = RegistryDB()

    def registration_commits() -> None:
        db.tables['import_bundle'] = registry_rows({'B_1': 'pending'})
        db.on_lock = None

    db.on_lock = registration_commits
    succeeded, _ctx = run_import_loop(db, [], monkeypatch, join=True)
    assert succeeded
    assert db.states() == {'B_1': 'done'}


def test_a_queue_importer_honors_exclusions(monkeypatch: pytest.MonkeyPatch) -> None:
    """``--exclude-bundles`` with no bundles named still keeps the importer off them."""
    db = RegistryDB({'import_bundle': registry_rows({'B_1': 'pending', 'B_2': 'pending'})})
    succeeded, _ctx = run_import_loop(db, [], monkeypatch, join=True, exclude_bundles='B_2')
    assert succeeded
    assert db.states() == {'B_1': 'done', 'B_2': 'pending'}


def test_a_queue_importer_takes_the_largest_first_and_goes_on_past_a_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Claims run largest first, a failed bundle is deleted and failed, and none is retried."""
    db = RegistryDB(
        {
            'import_bundle': registry_rows(
                {'B_1': 'pending', 'B_2': 'pending', 'B_3': 'pending', 'B_4': 'done'}
            )
        }
    )
    for row, size in zip(db.tables['import_bundle'], (50, 30, 30, 99), strict=True):
        row['size_estimate'] = size
    succeeded, _ctx = run_import_loop(db, [], monkeypatch, join=True, logging=('B_3',))
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
    db = RegistryDB({'import_bundle': registry_rows({'B_1': 'pending', 'B_2': 'pending'})})
    succeeded, _ctx = run_import_loop(db, ['B_2'], monkeypatch, join=True, bundles=['B_2'])
    assert succeeded
    assert db.states() == {'B_1': 'pending', 'B_2': 'done'}
    # The claim names the importer, and the bundle keeps it once done.
    assert [row['process_id'] for row in db.tables['import_bundle']] == [None, 1]


def _two_pending() -> RegistryDB:
    """Return a registry of B_1, the larger, and B_2, both pending."""
    db = RegistryDB({'import_bundle': registry_rows({'B_1': 'pending', 'B_2': 'pending'})})
    db.tables['import_bundle'][0]['size_estimate'] = 50
    return db


def test_an_interrupted_importer_finishes_its_bundle_and_claims_nothing_more(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The first interrupt drains: B_1 is done, B_2 left pending, and the run fails."""
    db = _two_pending()

    def interrupt(ctx: Any) -> None:
        ctx.interrupts = 1

    succeeded, ctx = run_import_loop(db, [], monkeypatch, join=True, during={'B_1': interrupt})

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

    succeeded, ctx = run_import_loop(db, [], monkeypatch, join=True, during={'B_1': stop})

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

    succeeded, ctx = run_import_loop(
        db, [], monkeypatch, join=True, failing=('B_1',), during=during
    )

    assert not succeeded
    assert db.states() == {'B_1': 'pending', 'B_2': 'pending'}
    assert [event for event in db.events if event.startswith(('delete', 'close'))] == expected
    assert ctx.logger.messages_at('fatal') == [
        'Interrupted twice: this importer returned B_1 to the queue, and exits'
    ]


def test_a_second_interrupt_once_the_importer_records_itself_stops_it_before_a_claim(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """From the start of its record in ``import_process`` the second interrupt is only
    counted, so it cannot leave a half-made record; the loop's first check stops it."""
    db = RegistryDB({'import_bundle': registry_rows({'B_1': 'pending'})})
    ctx = make_context(db=db)
    handler = cli._interrupt_handler(ctx)

    def interrupted_twice(db: Any) -> None:
        handler(signal.SIGINT, None)
        handler(signal.SIGINT, None)

    monkeypatch.setattr(import_processes, 'create_process_table', interrupted_twice)
    monkeypatch.setattr(
        import_processes, 'start_importer', lambda lock_db, log_path: HeldImporter()
    )
    try:
        succeeded = do_import.import_from_queue(ctx, None)
    except KeyboardInterrupt:
        pytest.fail('the second interrupt raised while the importer recorded itself')

    assert not succeeded
    assert db.states() == {'B_1': 'pending'}
    assert ctx.logger.messages_at('fatal') == [
        'Interrupted: this importer claims nothing more and exits'
    ]
