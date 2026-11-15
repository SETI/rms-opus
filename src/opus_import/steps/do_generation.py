"""The incremental update of a served schema: its pending generation, switched in whole.

An update writes only the bundles it changes, into the served schema, as a **pending
generation** P one above the served generation G (`opus_import.generations`). Nothing a
request reads changes until P is switched in, and the served rows stay whole until the
purge, so a switch can be reverted until then. The commands, each an ``opus_import``
option run on its own:

- ``--begin-generation`` (`begin_generation`) starts P on a ``ready`` schema of this
  release's version. The version row stays ``ready``, so every web worker goes on serving
  G and a worker started meanwhile passes the version check.
- ``--import``, ``--delete-bundles``, ``--finalize``, ``--validate`` and
  ``--write-schema-version`` then write P, each changed by its own module when P is
  pending; ``schema_version.pending_state`` records how far P has got, and only
  ``--write-schema-version`` makes it ``ready``.
- ``--switch-generation`` (`switch_generation`), run while the web service is stopped,
  swaps P's auxiliary tables in, points the cart at P, resets the search tables and
  flushes the cache, and last serves P. Each step finds out whether it has run, so an
  interrupted switch is completed by running it again.
- ``--purge-generations`` (`purge_generations`), run while the site serves, first makes
  the switch irreversible, then deletes the rows no served generation shows.
- ``--abandon-generation`` (`abandon_generation`) throws away an unswitched P, and
  ``--revert-generation`` (`revert_generation`) runs a switch backward until the purge.

The five commands hold a server-wide named lock on the schema for their whole run and
are refused while another holds it; every invocation that writes P registers itself in
``import_process`` with its liveness lock while briefly holding that lock
(`register_writer`), and a command is refused while any registered invocation is alive.
"""

from __future__ import annotations

import contextlib
from typing import TYPE_CHECKING

from opus_import import bundle_registry, import_processes, import_util, importdb, table_swap
from opus_import.generations import (
    ADDED_GENERATION_COLUMN,
    FIRST_GENERATION,
    GENERATION_LOCK,
    PENDING_GENERATION_COLUMN,
    PENDING_READY,
    PENDING_STATE_COLUMN,
    PENDING_WRITING,
    REMOVED_GENERATION_COLUMN,
    REVERTIBLE_COLUMN,
    SERVED_GENERATION_COLUMN,
    STATE_COLUMNS,
    GenerationState,
)
from opus_import.import_fault import InjectedImportFaultError, import_fault_argument
from opus_import.schema_version import (
    SCHEMA_STATE_READY,
    SCHEMA_VERSION,
    SCHEMA_VERSION_TABLE,
)
from opus_import.steps import do_django, do_finalize_mult, do_import_tables

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator

    from opus_import.context import ImportContext
    from opus_import.importdb.super import ImportDBSuper

#: The auxiliary tables a pending generation builds beside the live ones and the switch
#: swaps in together.
AUX_TABLES = ('param_info', 'partables', 'table_names')

#: The `opus_import.import_fault` site inside ``--switch-generation``. Its argument is a
#: step's number, `SWITCH_STEPS` counting from 1; the switch raises after that step.
SWITCH_FAULT_SITE = 'switch_generation'

#: The steps of ``--switch-generation``, in order, as the log and the fault site name them.
SWITCH_STEPS = ('swap the auxiliary tables', 'point the cart', 'reset the search tables')


class GenerationRefusedError(Exception):
    """A generation command or a write to the pending generation is refused; the message
    says why."""


def read_generation_state(db: ImportDBSuper) -> GenerationState | None:
    """Return the schema's one version row, or None when it has none or several.

    Parameters:
        db: The open database.
    """
    db.forget_table_names()
    if not db.table_exists(SCHEMA_VERSION_TABLE):
        return None
    rows = db.read_rows(SCHEMA_VERSION_TABLE, list(STATE_COLUMNS))
    if len(rows) != 1:
        return None
    return GenerationState.from_row(rows[0])


def load_generation_state(ctx: ImportContext) -> None:
    """Read the version row into the context, and the generation the run writes.

    Parameters:
        ctx: The import run's context, whose `ImportContext.generation_state` and
            `ImportContext.import_generation` are set.
    """
    assert ctx.db is not None
    state = read_generation_state(ctx.db)
    ctx.generation_state = state
    ctx.import_generation = FIRST_GENERATION if state is None else state.working_generation


def _require_state(ctx: ImportContext) -> GenerationState:
    """Return the schema's version row, read again, refusing a schema without one.

    Raises:
        GenerationRefusedError: If the schema has no single version row.
    """
    assert ctx.db is not None
    state = read_generation_state(ctx.db)
    if state is None:
        raise GenerationRefusedError(
            f'"{ctx.db.db_schema}" has no single {SCHEMA_VERSION_TABLE} row, so it has no '
            'generation: an incremental update writes a finished schema'
        )
    return state


def set_pending_state(ctx: ImportContext, pending_state: str) -> None:
    """Record how far the pending generation has got.

    Parameters:
        ctx: The import run's context, for the open database and the pending generation.
        pending_state: One of the ``generations.PENDING_`` constants.
    """
    db = ctx.db
    pending = ctx.pending_generation
    assert db is not None
    assert pending is not None
    db.update_row(
        SCHEMA_VERSION_TABLE,
        {PENDING_STATE_COLUMN: pending_state},
        f'{db.quote_identifier(PENDING_GENERATION_COLUMN)}=%s',
        [pending],
    )
    import_util.log_info(ctx, f'Generation {pending} is {pending_state}')


def read_pending_state(ctx: ImportContext) -> str | None:
    """Return how far the pending generation has got, read from the version row."""
    assert ctx.db is not None
    state = read_generation_state(ctx.db)
    return None if state is None else state.pending_state


def _generation_lock(db: ImportDBSuper) -> str:
    """Return the name of the schema's generation lock."""
    return importdb.lock_name(db.db_schema, GENERATION_LOCK)


def _alive_writers(db: ImportDBSuper) -> list[int]:
    """Return the ``import_process`` rows whose invocations are alive."""
    snapshot = import_processes.read_snapshot(db)
    return [process.process_id for process in snapshot.processes if process.alive]


@contextlib.contextmanager
def generation_command(ctx: ImportContext, option: str) -> Iterator[None]:
    """Hold the schema's generation lock for a generation command's whole run.

    Parameters:
        ctx: The import run's context, for the open database.
        option: The command, as refusals name it.

    Yields:
        Nothing; the body runs holding the lock.

    Raises:
        GenerationRefusedError: If another command holds the lock, or an invocation
            writing the pending generation is alive.
    """
    db = ctx.db
    assert db is not None
    name = _generation_lock(db)
    if not db.try_named_lock(name):
        raise GenerationRefusedError(
            f'{option} refused: another generation command holds "{db.db_schema}"\'s '
            'generation lock'
        )
    try:
        alive = _alive_writers(db)
        if alive:
            raise GenerationRefusedError(
                f'{option} refused: import_process '
                f'{", ".join(str(process) for process in alive)} still running against '
                f'"{db.db_schema}"; wait for them to finish'
            )
        yield
    finally:
        with contextlib.suppress(importdb.ImportDBError):
            db.release_named_lock(name)


def register_writer(ctx: ImportContext) -> import_processes.ImporterLock:
    """Record an invocation that writes the pending generation in ``import_process``.

    The row and its liveness lock are taken on a connection of their own while briefly
    holding the generation lock, so no generation command starts between this
    invocation's check and its registration.

    Parameters:
        ctx: The import run's context, for the open database and the log's path.

    Returns:
        The invocation's row and lock, which it frees when it ends
        (`opus_import.import_processes.ImporterLock.exit`).

    Raises:
        GenerationRefusedError: If a generation command holds the generation lock.
    """
    db = ctx.db
    assert db is not None
    name = _generation_lock(db)
    if not db.try_named_lock(name):
        raise GenerationRefusedError(
            f'A generation command holds "{db.db_schema}"\'s generation lock, so nothing '
            'writes its pending generation until it ends'
        )
    try:
        import_processes.create_process_table(db)
        lock_db = db.open_sibling_connection()
        return import_processes.start_importer(lock_db, ctx.log_path or '')
    finally:
        db.release_named_lock(name)


def _update_version_row(
    ctx: ImportContext, values: dict[str, object], column: str, value: object
) -> int:
    """Update the version row where one of its columns holds a value.

    Parameters:
        ctx: The import run's context, for the open database.
        values: The columns to write.
        column: The column the update is conditional on.
        value: The value it must hold, or None for NULL.

    Returns:
        How many rows matched.
    """
    db = ctx.db
    assert db is not None
    q = db.quote_identifier
    if value is None:
        return db.update_row(SCHEMA_VERSION_TABLE, values, f'{q(column)} IS NULL')
    return db.update_row(SCHEMA_VERSION_TABLE, values, f'{q(column)}=%s', [value])


def begin_generation(ctx: ImportContext) -> bool:
    """Start a pending generation, one above the served one: ``--begin-generation``.

    Refused unless the schema's one version row holds this release's version, ``ready``,
    with no pending generation and no switch still revertible.

    Parameters:
        ctx: The import run's context.

    Returns:
        True if it started one; False, logged as fatal, if refused.
    """
    try:
        with generation_command(ctx, '--begin-generation'):
            state = _require_state(ctx)
            problem = None
            if state.version != SCHEMA_VERSION:
                problem = f'is version {state.version} and this release is version {SCHEMA_VERSION}'
            elif state.state != SCHEMA_STATE_READY:
                problem = f'is {state.state}, not {SCHEMA_STATE_READY}'
            elif state.pending is not None:
                problem = (
                    f'already has the pending generation {state.pending} '
                    f'({state.pending_state}); "opus_import --abandon-generation" throws it away'
                )
            elif state.revertible:
                problem = (
                    f'can still revert to generation {state.generation - 1}; '
                    '"opus_import --purge-generations" ends that, or "--revert-generation" '
                    'then "--abandon-generation" undoes the switch'
                )
            if problem is not None:
                raise GenerationRefusedError(f'--begin-generation refused: the schema {problem}')
            pending = state.generation + 1
            _update_version_row(
                ctx,
                {PENDING_GENERATION_COLUMN: pending, PENDING_STATE_COLUMN: PENDING_WRITING},
                PENDING_GENERATION_COLUMN,
                None,
            )
            import_util.log_info(
                ctx, f'Generation {pending} begun; generation {state.generation} is served'
            )
    except GenerationRefusedError as e:
        ctx.logger.log('fatal', str(e))
        return False
    load_generation_state(ctx)
    return True


def switch_generation(ctx: ImportContext) -> bool:
    """Serve the pending generation: ``--switch-generation``, run while the web service is
    stopped.

    Refused unless the pending generation is ``ready``. The steps, each finding out
    whether it has run: the auxiliary tables' ``__new`` tables are swapped in, the live
    ones kept as ``__prev`` (`opus_import.table_swap.swap_in_keeping_previous`); every
    cart row naming an observation the pending generation does not show is pointed at
    its row with the same OPUS id, or deleted; the search tables are reset and the cache
    flushed; and last, one statement serves the pending generation, clears it and marks
    the switch revertible. With no pending generation and a revertible switch, the
    switch has already run, which it reports and succeeds.

    Parameters:
        ctx: The import run's context.

    Returns:
        True when the pending generation is served; False, logged, if refused.
    """
    try:
        with generation_command(ctx, '--switch-generation'):
            state = _require_state(ctx)
            if state.pending is None and state.revertible:
                import_util.log_info(ctx, f'Generation {state.generation} is already switched in')
                return True
            if state.pending is None or state.pending_state != PENDING_READY:
                raise GenerationRefusedError(
                    '--switch-generation refused: no pending generation is ready '
                    f'(pending {state.pending}, {state.pending_state}); '
                    '"--write-schema-version" marks one ready once it is validated'
                )
            pending = state.pending
            _switch_step(ctx, 1, lambda: table_swap.swap_in_keeping_previous(ctx, AUX_TABLES))
            _switch_step(ctx, 2, lambda: _point_cart(ctx, pending))
            _switch_step(ctx, 3, lambda: do_django.reset_search_tables(ctx))
            _update_version_row(
                ctx,
                {
                    SERVED_GENERATION_COLUMN: pending,
                    PENDING_GENERATION_COLUMN: None,
                    PENDING_STATE_COLUMN: None,
                    REVERTIBLE_COLUMN: 1,
                },
                PENDING_GENERATION_COLUMN,
                pending,
            )
            import_util.log_info(
                ctx,
                f'Generation {pending} is served; "opus_import --purge-generations" deletes '
                f"generation {state.generation}'s retired rows once it has been checked",
            )
    except GenerationRefusedError as e:
        ctx.logger.log('fatal', str(e))
        return False
    load_generation_state(ctx)
    return True


def _switch_step(ctx: ImportContext, number: int, step: Callable[[], object]) -> None:
    """Run one step of the switch, then raise there if a test names it.

    Parameters:
        ctx: The import run's context, for the log.
        number: The step's number, from 1.
        step: The step, a callable taking nothing.

    Raises:
        InjectedImportFaultError: If `SWITCH_FAULT_SITE` names this step.
    """
    import_util.log_info(ctx, f'Switch step {number}: {SWITCH_STEPS[number - 1]}')
    step()
    if import_fault_argument(SWITCH_FAULT_SITE) == str(number):
        raise InjectedImportFaultError(f'{SWITCH_FAULT_SITE}:{number}')


def _point_cart(ctx: ImportContext, generation: int) -> None:
    """Point the cart at a generation's observations, logging what moved and what went.

    Parameters:
        ctx: The import run's context.
        generation: The generation.
    """
    db = ctx.db
    assert db is not None
    if not db.table_exists('cart'):
        return
    pointed, deleted = db.repoint_cart(generation)
    import_util.log_info(
        ctx,
        f'Cart: {pointed} rows pointed at generation {generation}, {deleted} rows deleted '
        'whose observations it does not have',
    )


def revert_generation(ctx: ImportContext) -> bool:
    """Run the last switch backward: ``--revert-generation``, while the web service is
    stopped.

    Refused unless the switch is still revertible. The ``__prev`` auxiliary tables are
    swapped back in and the reverted-from ones kept as ``__new``; the cart is pointed at
    the previous generation; the search tables are reset; and last, the previous
    generation is served again with the reverted-from one pending and ``ready``, no
    longer revertible, so it can be abandoned or switched again. Each step finds out
    whether it has run, as the switch's do.

    Parameters:
        ctx: The import run's context.

    Returns:
        True when the previous generation is served; False, logged, if refused.
    """
    try:
        with generation_command(ctx, '--revert-generation'):
            state = _require_state(ctx)
            if not state.revertible:
                raise GenerationRefusedError(
                    '--revert-generation refused: no switch is revertible (a purge has '
                    'started since, or no generation was switched in)'
                )
            reverted = state.generation
            previous = reverted - 1
            table_swap.swap_back_previous(ctx, AUX_TABLES)
            _point_cart(ctx, previous)
            do_django.reset_search_tables(ctx)
            _update_version_row(
                ctx,
                {
                    SERVED_GENERATION_COLUMN: previous,
                    PENDING_GENERATION_COLUMN: reverted,
                    PENDING_STATE_COLUMN: PENDING_READY,
                    REVERTIBLE_COLUMN: 0,
                },
                REVERTIBLE_COLUMN,
                1,
            )
            import_util.log_info(
                ctx,
                f'Generation {previous} is served again; generation {reverted} is pending and '
                'ready: "--abandon-generation" throws it away, "--switch-generation" serves it',
            )
    except GenerationRefusedError as e:
        ctx.logger.log('fatal', str(e))
        return False
    load_generation_state(ctx)
    return True


def _observation_ids(ctx: ImportContext, where: str, params: list[object]) -> list[int]:
    """Return the ``obs_general`` ids a condition on its base table selects, in order."""
    db = ctx.db
    assert db is not None
    q = db.quote_identifier
    rows = db.general_select(
        f'{q("id")} FROM {q("obs_general")} WHERE {where} ORDER BY {q("id")}',  # nosec B608
        params,
    )
    return [int(row[0]) for row in rows]


def purge_generations(ctx: ImportContext) -> bool:
    """Delete the rows no served generation shows: ``--purge-generations``.

    Run after a switch, while the site serves. Refused while a generation is pending. Its
    first statement, committed on its own, ends the switch's revertibility, so a revert
    is refused from before the first row goes. It then deletes every observation retired
    at or before the served generation from every observation table, children first,
    with foreign keys checked; deletes the registry rows of the copies retired by then;
    drops the auxiliary ``__prev`` tables; and runs finalization's mult step and
    ``ANALYZE``. The rows it deletes are in no served generation, so no request reads
    them.

    Parameters:
        ctx: The import run's context.

    Returns:
        True if it ran; False, logged, if refused or its mult step failed.
    """
    try:
        with generation_command(ctx, '--purge-generations'):
            state = _require_state(ctx)
            if state.pending is not None:
                raise GenerationRefusedError(
                    f'--purge-generations refused: generation {state.pending} is pending; '
                    'switch it in or abandon it first'
                )
            db = ctx.db
            assert db is not None
            q = db.quote_identifier
            _update_version_row(
                ctx, {REVERTIBLE_COLUMN: 0}, SERVED_GENERATION_COLUMN, state.generation
            )
            served = state.generation
            removed = q(REMOVED_GENERATION_COLUMN)
            ids = _observation_ids(ctx, f'{removed} IS NOT NULL AND {removed} <= %s', [served])
            import_util.log_info(ctx, f'Purging {len(ids)} retired observations')
            do_import_tables.delete_observations(ctx, ids)
            bundle_registry.purge_retired_copies(ctx, served)
            for table in reversed(AUX_TABLES):
                db.drop_table(table_swap.swap_prev_name(table))
            mult_done = do_finalize_mult.finalize_mult(ctx)
            do_import_tables.analyze_all_tables(ctx)
    except GenerationRefusedError as e:
        ctx.logger.log('fatal', str(e))
        return False
    load_generation_state(ctx)
    return mult_done


def abandon_generation(ctx: ImportContext) -> bool:
    """Throw away an unswitched pending generation: ``--abandon-generation``.

    The rows the pending generation added are deleted from every observation table; the
    rows it retired are restored; its registry rows are deleted and the copies it retired
    made live again; its auxiliary ``__new`` tables are dropped; and last the version
    row's pending generation is cleared. Running it again after an interruption finishes
    the work.

    Parameters:
        ctx: The import run's context.

    Returns:
        True if it ran; False, logged, if refused.
    """
    try:
        with generation_command(ctx, '--abandon-generation'):
            state = _require_state(ctx)
            if state.pending is None:
                raise GenerationRefusedError(
                    '--abandon-generation refused: no generation is pending'
                )
            pending = state.pending
            db = ctx.db
            assert db is not None
            q = db.quote_identifier
            ids = _observation_ids(ctx, f'{q(ADDED_GENERATION_COLUMN)}=%s', [pending])
            import_util.log_info(
                ctx, f'Abandoning generation {pending}: deleting {len(ids)} observations'
            )
            do_import_tables.delete_observations(ctx, ids)
            while True:
                matched = db.update_row(
                    'obs_general',
                    {REMOVED_GENERATION_COLUMN: None},
                    f'{q(REMOVED_GENERATION_COLUMN)}=%s LIMIT %s',
                    [pending, db.transaction_rows],
                )
                if matched < db.transaction_rows:
                    break
            bundle_registry.delete_generation_copies(ctx, pending)
            bundle_registry.restore_retired_copies(ctx, pending)
            table_swap.drop_swap_leftovers(ctx, AUX_TABLES)
            _update_version_row(
                ctx,
                {PENDING_GENERATION_COLUMN: None, PENDING_STATE_COLUMN: None},
                PENDING_GENERATION_COLUMN,
                pending,
            )
            import_util.log_info(
                ctx, f'Generation {pending} abandoned; generation {state.generation} is served'
            )
    except GenerationRefusedError as e:
        ctx.logger.log('fatal', str(e))
        return False
    load_generation_state(ctx)
    return True
