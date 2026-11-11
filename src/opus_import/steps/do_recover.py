"""Deleting a queue importer's bundle safely, and returning a dead importer's bundle.

Two kinds of process act on a bundle an importer holds besides the importer itself: the
importer's own **release** of it, when it deletes the bundle's rows before importing it,
after a failure, or when it aborts (a lost lock, or a second interrupt); and any
coordinator's **recovery** of it, once the importer is found lost
(`recover_lost_importers`).

Both delete the bundle's rows while a second connection holds the bundle's registry row
locked (``SELECT ... FOR UPDATE``), and both first check, under that lock, that the row
still names the importer as ``importing``. The deletes run on the import connection, in
transactions of their own, so the row lock has to be held elsewhere to last through
them. Whichever of the two takes the row first acts; the other finds the row locked or
changed and does nothing. A recovery also checks again, under the row lock, that the
importer's lock is free, and an importer's chunk holds the same row until it commits
(`opus_import.import_processes.BundleGuard`), so a chunk can never commit after the
recovery that deletes its bundle.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from opus_import import bundle_registry, import_processes, import_util
from opus_import.steps import do_import_tables

if TYPE_CHECKING:
    from opus_import.context import ImportContext
    from opus_import.importdb.super import ImportDBSuper

#: How many times an importer may die holding a bundle before the bundle is ``failed``
#: rather than returned to the queue: a bundle that kills its importer twice (memory, a
#: crash in a native library) would loop.
LOSSES_BEFORE_FAILED = 2

_HELD_COLUMNS = ('state', 'process_id', 'losses')


def _held_row(holder: ImportDBSuper, bundle_number: int) -> tuple[object, ...] | None:
    """Lock a bundle's registry row on the holding connection, unless another holds it.

    Parameters:
        holder: The connection, inside its transaction.
        bundle_number: The bundle.

    Returns:
        The row's state, ``process_id`` and losses, or None when another session holds
        the row or it is gone.
    """
    q = holder.quote_identifier
    return holder.lock_row(
        bundle_registry.BUNDLE_REGISTRY_TABLE,
        _HELD_COLUMNS,
        f'{q("bundle_number")}=%s',
        [bundle_number],
    )


def _transition(
    holder: ImportDBSuper, bundle_number: int, process_id: int, columns: dict[str, object]
) -> None:
    """Move a bundle on, matching it only while it is ``importing`` under the importer.

    Parameters:
        holder: The connection holding the row, inside its transaction.
        bundle_number: The bundle.
        process_id: The importer the row has to name.
        columns: What the move writes.
    """
    q = holder.quote_identifier
    holder.update_row(
        bundle_registry.BUNDLE_REGISTRY_TABLE,
        columns,
        f'{q("bundle_number")}=%s AND {q("state")}=%s AND {q("process_id")}=%s',
        [bundle_number, bundle_registry.BUNDLE_IMPORTING, process_id],
    )


def _pending_columns(losses: int) -> dict[str, object]:
    """What a return to the queue writes."""
    return {
        'state': bundle_registry.BUNDLE_PENDING,
        'started_at': None,
        'finished_at': None,
        'rows_done': 0,
        'process_id': None,
        'losses': losses,
    }


def release_bundle(
    ctx: ImportContext,
    bundle_id: str,
    bundle_number: int,
    process_id: int,
    state: str | None,
) -> bool:
    """Delete an importer's bundle's rows, and move it on, while the registry names it.

    Parameters:
        ctx: The import run's context, whose connection runs the deletes.
        bundle_id: The bundle.
        bundle_number: Its number.
        process_id: The importer holding it.
        state: ``pending`` to return the bundle to the queue (an abort), ``failed`` to
            record it failed, keeping ``process_id`` so its importer's log can be named,
            or None to leave it ``importing`` (the delete before an import).

    Returns:
        True if the row named the importer as ``importing`` and the rows were deleted;
        False, deleting nothing, if another session held the row or it names the
        importer no longer.
    """
    db = ctx.db
    assert db is not None
    holder = db.open_sibling_connection()
    try:
        with holder.transaction():
            row = _held_row(holder, bundle_number)
            if row is None or row[0] != bundle_registry.BUNDLE_IMPORTING or row[1] != process_id:
                return False
            do_import_tables.delete_bundle_from_obs_tables(ctx, bundle_id)
            if state == bundle_registry.BUNDLE_PENDING:
                _transition(holder, bundle_number, process_id, _pending_columns(int(str(row[2]))))
            elif state is not None:
                _transition(
                    holder,
                    bundle_number,
                    process_id,
                    {'state': state, 'finished_at': import_processes.now()},
                )
        return True
    finally:
        holder.close()


def _recover_bundle(
    ctx: ImportContext, bundle_id: str, bundle_number: int, process_id: int, lock: str
) -> str | None:
    """Return one lost importer's bundle to the queue, or record it ``failed``.

    Parameters:
        ctx: The context whose connection runs the deletes.
        bundle_id: The bundle.
        bundle_number: Its number.
        process_id: The lost importer.
        lock: The importer's lock name.

    Returns:
        What was done, for the log; None when another session held the row, so a later
        pass tries again.
    """
    db = ctx.db
    assert db is not None
    holder = db.open_sibling_connection()
    try:
        with holder.transaction():
            row = _held_row(holder, bundle_number)
            if row is None:
                return None
            if row[0] != bundle_registry.BUNDLE_IMPORTING or row[1] != process_id:
                return f'{bundle_id} had already left importer {process_id}'
            if holder.named_lock_holder(lock) is not None:
                return f'{bundle_id}: importer {process_id} holds its lock again'
            do_import_tables.delete_bundle_from_obs_tables(ctx, bundle_id)
            losses = int(str(row[2])) + 1
            if losses >= LOSSES_BEFORE_FAILED:
                columns: dict[str, object] = {
                    'state': bundle_registry.BUNDLE_FAILED,
                    'finished_at': import_processes.now(),
                    'losses': losses,
                }
                done = f'{bundle_id} failed: its importer died holding it {losses} times'
            else:
                columns = _pending_columns(losses)
                done = f'{bundle_id} returned to the queue: importer {process_id} died holding it'
            _transition(holder, bundle_number, process_id, columns)
        return done
    finally:
        holder.close()


def recover_lost_importers(ctx: ImportContext) -> list[str]:
    """Return or fail every bundle held by an importer whose lock is free, and mark the
    importers that are lost.

    A bundle ``importing`` under an importer whose lock is free has its rows deleted and
    its losses counted, and goes back to ``pending``, or to ``failed`` at its
    `LOSSES_BEFORE_FAILED`th loss. An importer whose row is ``running`` while its lock is
    free is lost, and once it holds no bundle its row becomes ``lost``. Every move checks
    the state it moves from, so the recovery may run on any computer, any number of
    times, at once.

    Parameters:
        ctx: The context whose connection reads, deletes and writes.

    Returns:
        One line per bundle or importer acted on, which is also logged.
    """
    db = ctx.db
    assert db is not None
    if not db.table_exists(import_processes.IMPORT_PROCESS_TABLE):
        return []
    q = db.quote_identifier
    done: list[str] = []
    free: dict[int, bool] = {}

    def lock_is_free(process_id: int) -> bool:
        """Ask the server, once per pass, whether an importer's lock is free."""
        if process_id not in free:
            lock = import_processes.importer_lock_name(db.db_schema, process_id)
            free[process_id] = db.named_lock_holder(lock) is None
        return free[process_id]

    unsettled: set[int] = set()
    held = db.read_rows(
        bundle_registry.BUNDLE_REGISTRY_TABLE,
        ['bundle_id', 'bundle_number', 'process_id'],
        f'{q("state")}=%s AND {q("process_id")} IS NOT NULL',
        [bundle_registry.BUNDLE_IMPORTING],
    )
    for bundle_id, bundle_number, found in held:
        process_id = int(found)
        if not lock_is_free(process_id):
            continue
        lock = import_processes.importer_lock_name(db.db_schema, process_id)
        outcome = _recover_bundle(ctx, str(bundle_id), int(bundle_number), process_id, lock)
        if outcome is None:
            unsettled.add(process_id)
        else:
            done.append(outcome)
    running = db.read_rows(
        import_processes.IMPORT_PROCESS_TABLE,
        ['process_id'],
        f'{q("state")}=%s',
        [import_processes.PROCESS_RUNNING],
    )
    for (found,) in running:
        process_id = int(found)
        if process_id in unsettled or not lock_is_free(process_id):
            continue
        db.update_row(
            import_processes.IMPORT_PROCESS_TABLE,
            {'state': import_processes.PROCESS_LOST},
            f'{q("process_id")}=%s AND {q("state")}=%s',
            [process_id, import_processes.PROCESS_RUNNING],
        )
        done.append(f'importer {process_id} is lost: its lock is free')
    for line in done:
        import_util.log_warning(ctx, line)
    return done
