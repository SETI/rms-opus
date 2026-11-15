"""The incremental update of a served schema: its pending generation, switched in whole.

An update writes only the bundles it changes, into the served schema, as a **pending
generation** P one above the served generation G (`opus_import.generations`). Nothing a
request reads changes until P is switched in, and the served rows stay whole until the
purge, so a switch can be reverted until then. The commands, each an ``opus_import``
option run on its own:

- ``--begin-generation`` (`begin_generation`) starts P on a ``ready`` schema of this
  release's version, first re-creating the ``obs_general`` view to show only G. The
  version row stays ``ready``, so every web worker goes on serving G and a worker started
  meanwhile passes the version check.
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

A switch or a revert that stopped part way leaves the auxiliary tables in a shape no
finished one leaves (`unfinished_switch_problem`), and until it is completed or undone,
the abandon, the purge and every write to P are refused: each would delete rows the cart
was pointed at, or drop auxiliary tables the way back needs.

Each command holds a server-wide named lock on the schema for its whole run and is
refused while another holds it; every invocation that writes P registers itself in
``import_process`` with its liveness lock while briefly holding that lock
(`register_writer`), and a command is refused while any registered invocation is alive.
A refused command raises `GenerationRefusedError` before it changes anything, and
``opus_import`` then exits with `GENERATION_REFUSED_EXIT_STATUS`, so the deploy chain can
tell a refusal from a command that stopped part way.
"""

from __future__ import annotations

import contextlib
from typing import TYPE_CHECKING

from opus_config import get_config
from opus_import import bundle_registry, import_processes, import_util, importdb, table_swap
from opus_import.generations import (
    ADDED_GENERATION_COLUMN,
    FIRST_GENERATION,
    GENERATION_LOCK,
    OBS_GENERAL_VIEW,
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
SWITCH_STEPS = (
    'swap the auxiliary tables',
    'point the cart',
    'reset the search tables',
    'show the generation in the view',
)


#: The status ``opus_import`` exits with when a generation command is refused, having
#: changed nothing. ``promote_generation.sh`` reads it.
GENERATION_REFUSED_EXIT_STATUS = 3


class GenerationRefusedError(Exception):
    """A generation command or a write to the pending generation is refused, before it
    changes anything; the message says why."""


class GenerationLostError(Exception):
    """The pending generation an invocation was writing stopped being pending under it;
    the message names it."""


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

    Raises:
        GenerationLostError: If the generation is no longer pending, so there is no row
            to record it in.
    """
    db = ctx.db
    pending = ctx.pending_generation
    assert db is not None
    assert pending is not None
    matched = db.update_row(
        SCHEMA_VERSION_TABLE,
        {PENDING_STATE_COLUMN: pending_state},
        f'{db.quote_identifier(PENDING_GENERATION_COLUMN)}=%s',
        [pending],
    )
    # A read-only run executes nothing and matches no row.
    if matched == 0 and not db.read_only:
        raise GenerationLostError(
            f'Generation {pending} is no longer pending, so it cannot be marked '
            f'{pending_state}: a generation command switched it in or abandoned it while '
            'this invocation ran'
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
        raise GenerationRefusedError(f'{option} refused: {_lock_held_message(db)}')
    try:
        writers = _writers_message(db)
        if writers is not None:
            raise GenerationRefusedError(f'{option} refused: {writers}')
        yield
    finally:
        with contextlib.suppress(importdb.ImportDBError):
            db.release_named_lock(name)


def _lock_held_message(db: ImportDBSuper) -> str:
    """Return why a generation command is refused while another holds the lock."""
    return f'another generation command holds "{db.db_schema}"\'s generation lock'


def _writers_message(db: ImportDBSuper) -> str | None:
    """Return why a generation command is refused while writers are alive, or None."""
    alive = _alive_writers(db)
    if not alive:
        return None
    return (
        f'import_process {", ".join(str(process) for process in alive)} still running '
        f'against "{db.db_schema}"; wait for them to finish'
    )


def register_writer(ctx: ImportContext) -> import_processes.ImporterLock:
    """Record an invocation that writes the pending generation in ``import_process``.

    The row and its liveness lock are taken on a connection of their own while briefly
    holding the generation lock, so no generation command starts between this
    invocation's check and its registration. The version row is read again under the
    lock: the invocation chose its path by the row it read as it started, and a switch or
    an abandon may have run since.

    Parameters:
        ctx: The import run's context, for the open database and the log's path, and the
            version row it read as it started (`ImportContext.generation_state`), which
            is replaced by the one read under the lock.

    Returns:
        The invocation's row and lock, which it frees when it ends
        (`opus_import.import_processes.ImporterLock.exit`).

    Raises:
        GenerationRefusedError: If a generation command holds the generation lock, the
            generation the invocation started to write is no longer the pending one, or
            a switch of it stopped part way.
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
        started = ctx.generation_state
        state = _require_state(ctx)
        if started is None or (state.generation, state.pending) != (
            started.generation,
            started.pending,
        ):
            now = 'none' if state.pending is None else f'generation {state.pending}'
            raise GenerationRefusedError(
                f'Generation {ctx.pending_generation} is no longer pending: generation '
                f'{state.generation} is served and {now} is pending, since a generation '
                'command ran while this invocation started; run it again'
            )
        ctx.generation_state = state
        unfinished = unfinished_switch_problem(db, state)
        if unfinished is not None:
            raise GenerationRefusedError(
                f'Nothing writes generation {state.pending} now: {unfinished}'
            )
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


def _existing_tables(db: ImportDBSuper, name_for: Callable[[str], str]) -> list[str]:
    """Return the auxiliary tables that exist under one kind of swap name."""
    db.forget_table_names()
    return [name_for(table) for table in AUX_TABLES if db.table_exists(name_for(table))]


def unfinished_switch_problem(db: ImportDBSuper, state: GenerationState) -> str | None:
    """Say whether a switch or a revert stopped part way, and how to finish it.

    While a generation is pending, only a switch leaves ``__prev`` tables: from its first
    step, which swaps the pending generation's auxiliary tables in, until it serves the
    generation, and a revert of it swaps them back last. While no generation is pending
    and the switch is revertible, a revert swaps the ``__prev`` tables back first and
    keeps the tables it replaces as ``__new``, so ``__new`` tables with no ``__prev``
    table beside them mark a revert that stopped before serving the previous generation.
    In either shape the cart, the search tables and the view may belong to either
    generation.

    Parameters:
        db: The open database.
        state: The schema's version row.

    Returns:
        None when no switch or revert is unfinished; otherwise what is unfinished and the
        commands that finish it.
    """
    if state.pending is not None:
        kept = _existing_tables(db, table_swap.swap_prev_name)
        if not kept:
            return None
        return (
            f'a switch of generation {state.pending}, or a revert of it, stopped part way '
            f"({', '.join(kept)} hold generation {state.generation}'s auxiliary tables); "
            'with the web service stopped, "opus_import --switch-generation" completes the '
            'switch and "opus_import --revert-generation" undoes it (promote_generation.sh, '
            'or promote_generation.sh --revert)'
        )
    if not state.revertible or _existing_tables(db, table_swap.swap_prev_name):
        return None
    built = _existing_tables(db, table_swap.swap_new_name)
    if not built:
        return None
    return (
        f'a revert of generation {state.generation} stopped part way ({", ".join(built)} '
        f'hold its auxiliary tables); with the web service stopped, "opus_import '
        '--revert-generation" completes the revert and "opus_import --switch-generation" '
        'serves the generation again (promote_generation.sh --revert, or '
        'promote_generation.sh)'
    )


def begin_generation(ctx: ImportContext) -> None:
    """Start a pending generation, one above the served one: ``--begin-generation``.

    Refused unless the schema's one version row holds this release's version, ``ready``,
    with no pending generation and no switch still revertible. The ``obs_general`` view
    is re-created to show the served generation alone before the pending one is recorded
    (`refresh_view`).

    Parameters:
        ctx: The import run's context.

    Raises:
        GenerationRefusedError: If refused.
    """
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
        # A purge that stopped before dropping them leaves __prev tables no revert can
        # use; while a generation is pending, only a switch that stopped part way
        # leaves any.
        db = ctx.db
        assert db is not None
        for table in reversed(AUX_TABLES):
            db.drop_table(table_swap.swap_prev_name(table))
        # Before the generation is recorded, so no row of it is ever written while
        # the view shows every row.
        refresh_view(ctx, state.generation)
        _update_version_row(
            ctx,
            {PENDING_GENERATION_COLUMN: pending, PENDING_STATE_COLUMN: PENDING_WRITING},
            PENDING_GENERATION_COLUMN,
            None,
        )
        import_util.log_info(
            ctx, f'Generation {pending} begun; generation {state.generation} is served'
        )
    load_generation_state(ctx)


def _switch_refusal(state: GenerationState) -> str | None:
    """Return why ``--switch-generation`` is refused on a version row, or None.

    It runs with a pending generation that is ``ready``, and with none pending while the
    last switch is revertible, which it completes.
    """
    if state.pending is None and state.revertible:
        return None
    if state.pending is not None and state.pending_state == PENDING_READY:
        return None
    return (
        f'no pending generation is ready (pending {state.pending}, {state.pending_state}); '
        '"opus_import --write-schema-version" marks one ready once it is validated'
    )


def _revert_refusal(state: GenerationState) -> str | None:
    """Return why ``--revert-generation`` is refused on a version row, or None.

    It runs while the last switch is revertible, and with a pending generation that is
    ``ready``, whose switch may have stopped part way.
    """
    if state.revertible or (state.pending is not None and state.pending_state == PENDING_READY):
        return None
    return (
        'no switch is revertible (a purge has started since, or no generation was '
        'switched in) and no pending generation is ready'
    )


def switch_generation(ctx: ImportContext) -> None:
    """Serve the pending generation: ``--switch-generation``, run while the web service is
    stopped.

    Refused unless the pending generation is ``ready``. The steps, each finding out
    whether it has run: the auxiliary tables' ``__new`` tables are swapped in, the live
    ones kept as ``__prev`` (`opus_import.table_swap.swap_in_keeping_previous`); every
    cart row naming an observation the pending generation does not show is pointed at
    its row with the same OPUS id, or deleted; the search tables are reset and the cache
    flushed; the ``obs_general`` view is re-created to show the pending generation
    (`refresh_view`); and last, one statement serves the pending generation, clears it
    and marks the switch revertible. With no pending generation and a revertible switch,
    the last statement has already run: the other steps run again for the served
    generation, which finds nothing to do after a whole switch and completes a revert
    that stopped part way.

    Parameters:
        ctx: The import run's context.

    Raises:
        GenerationRefusedError: If refused.
    """
    with generation_command(ctx, '--switch-generation'):
        state = _require_state(ctx)
        refusal = _switch_refusal(state)
        if refusal is not None:
            raise GenerationRefusedError(f'--switch-generation refused: {refusal}')
        if state.pending is None:
            import_util.log_info(
                ctx, f'Generation {state.generation} is already served; completing its switch'
            )
            _switch_steps(ctx, state.generation)
            return
        pending = state.pending
        _switch_steps(ctx, pending)
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
    load_generation_state(ctx)


def _switch_steps(ctx: ImportContext, generation: int) -> None:
    """Run the switch's steps before its last statement, for the generation it serves.

    Parameters:
        ctx: The import run's context.
        generation: The generation being switched in.
    """
    _switch_step(ctx, 1, lambda: table_swap.swap_in_keeping_previous(ctx, AUX_TABLES))
    _switch_step(ctx, 2, lambda: _point_cart(ctx, generation))
    _switch_step(ctx, 3, lambda: do_django.reset_search_tables(ctx))
    _switch_step(ctx, 4, lambda: refresh_view(ctx, generation))


def _revert_steps(ctx: ImportContext, generation: int, *, swap_first: bool) -> None:
    """Run the switch's steps backward, for the generation served again.

    The order decides which auxiliary tables a revert that stops part way leaves, which is
    how `unfinished_switch_problem` finds one: the swap back comes first after a whole
    switch, leaving ``__new`` tables from the start, and last after a switch that stopped
    part way, keeping its ``__prev`` tables to the end.

    Parameters:
        ctx: The import run's context.
        generation: The generation served again.
        swap_first: Whether the ``__prev`` tables are swapped back before the other steps
            rather than after them.
    """
    if swap_first:
        table_swap.swap_back_previous(ctx, AUX_TABLES)
        _point_cart(ctx, generation)
        do_django.reset_search_tables(ctx)
        refresh_view(ctx, generation)
    else:
        refresh_view(ctx, generation)
        do_django.reset_search_tables(ctx)
        _point_cart(ctx, generation)
        table_swap.swap_back_previous(ctx, AUX_TABLES)


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


def refresh_view(ctx: ImportContext, served: int | None) -> None:
    """Re-create the ``obs_general`` view for the rows it is to show.

    The site may be serving the view, so each attempt waits only as long as an auxiliary
    table swap's rename does for the transactions reading it, and a view still held after
    every attempt fails the command at that step, which running the command again
    finishes.

    Parameters:
        ctx: The import run's context, for the open database.
        served: The generation the view is to show, while other generations' rows are in
            the table; None once every row is in the served generation, for a view of
            every row with no condition.
    """
    db = ctx.db
    assert db is not None
    schema = import_util.read_schema_for_table(ctx, OBS_GENERAL_VIEW)
    # obs_general.json is packaged with opus_import, so the schema is always found.
    assert schema is not None
    db.create_obs_general_view(
        schema,
        served,
        lock_wait_timeout_s=table_swap.SWAP_LOCK_WAIT_TIMEOUT_S,
        attempts=table_swap.SWAP_RENAME_ATTEMPTS,
    )
    shown = 'every row' if served is None else f'generation {served}'
    import_util.log_info(ctx, f'The obs_general view shows {shown}')


def _has_retired_rows(ctx: ImportContext) -> bool:
    """Return whether any row of ``obs_general_rows`` has been retired."""
    db = ctx.db
    assert db is not None
    q = db.quote_identifier
    removed = q(REMOVED_GENERATION_COLUMN)
    rows = db.general_select(
        f'1 FROM {q(OBS_GENERAL_VIEW)} WHERE {removed} IS NOT NULL LIMIT 1'  # nosec B608
    )
    return len(rows) > 0


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


def revert_generation(ctx: ImportContext) -> None:
    """Run the last switch backward: ``--revert-generation``, while the web service is
    stopped.

    The ``__prev`` auxiliary tables are swapped back in and the reverted-from ones kept as
    ``__new``; the cart is pointed at the previous generation; the search tables are
    reset; the view is re-created to show the previous generation; and last, the
    previous generation is served again with the reverted-from one pending and
    ``ready``, and the switch is not revertible any more, so the reverted-from generation
    can be abandoned or switched again. Each step finds out whether it has run, as the
    switch's do. A switch that stopped before its last statement left its generation
    pending and ``ready``, and the same steps, in the opposite order, undo whatever of it
    ran, the served generation unchanged (`_revert_steps`). Refused otherwise: once the
    purge has started, or with nothing switched.

    Parameters:
        ctx: The import run's context.

    Raises:
        GenerationRefusedError: If refused.
    """
    with generation_command(ctx, '--revert-generation'):
        state = _require_state(ctx)
        refusal = _revert_refusal(state)
        if refusal is not None:
            raise GenerationRefusedError(f'--revert-generation refused: {refusal}')
        if state.pending is not None and state.pending_state == PENDING_READY:
            _revert_steps(ctx, state.generation, swap_first=False)
            import_util.log_info(
                ctx,
                f'Generation {state.generation} is served, and generation '
                f'{state.pending} is pending and ready, as before the switch began',
            )
            return
        reverted = state.generation
        previous = reverted - 1
        _revert_steps(ctx, previous, swap_first=True)
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
    load_generation_state(ctx)


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


def _abandoned_ids(ctx: ImportContext, pending: int) -> tuple[list[int], list[int]]:
    """Return the observations a pending generation added and those it retired, in order.

    Neither generation column has a key, so both are found in one scan of the base table,
    which reads without locking; the rows are then changed by their primary key.

    Parameters:
        ctx: The import run's context, for the open database.
        pending: The pending generation.
    """
    db = ctx.db
    assert db is not None
    q = db.quote_identifier
    added_column, removed_column = q(ADDED_GENERATION_COLUMN), q(REMOVED_GENERATION_COLUMN)
    rows = db.general_select(
        f'{q("id")}, {added_column} FROM {q("obs_general")} '  # nosec B608
        f'WHERE {added_column}=%s OR {removed_column}=%s ORDER BY {q("id")}',
        [pending, pending],
    )
    added = [int(obs_id) for obs_id, added_in in rows if int(added_in) == pending]
    retired = [int(obs_id) for obs_id, added_in in rows if int(added_in) != pending]
    return added, retired


def purge_generations(ctx: ImportContext) -> bool:
    """Delete the rows no served generation shows: ``--purge-generations``.

    Run after a switch, while the site serves. Refused while a generation is pending, and
    while a revert has stopped part way (`unfinished_switch_problem`). Its first
    statement, committed on its own, ends the switch's revertibility, so a revert is
    refused from before the first row goes. It then drops the auxiliary ``__prev``
    tables; deletes every observation retired at or before the served generation from
    every observation table, children first, with foreign keys checked; deletes the
    registry rows of the copies retired by then; re-creates the view with no condition,
    every row left being in the served generation; and runs finalization's mult step and
    ``ANALYZE``. The rows it deletes are in no served generation, so no request reads
    them.

    Parameters:
        ctx: The import run's context.

    Returns:
        True if it ran; False, logged, if its mult step failed.

    Raises:
        GenerationRefusedError: If refused.
    """
    with generation_command(ctx, '--purge-generations'):
        state = _require_state(ctx)
        if state.pending is not None:
            raise GenerationRefusedError(
                f'--purge-generations refused: generation {state.pending} is pending; '
                'switch it in or abandon it first'
            )
        db = ctx.db
        assert db is not None
        # The purge deletes the retired rows a part-way revert has pointed the cart at.
        unfinished = unfinished_switch_problem(db, state)
        if unfinished is not None:
            raise GenerationRefusedError(f'--purge-generations refused: {unfinished}')
        q = db.quote_identifier
        _update_version_row(ctx, {REVERTIBLE_COLUMN: 0}, SERVED_GENERATION_COLUMN, state.generation)
        # Next, so no __prev table outlives the revert it served (begin_generation drops
        # any an interrupted purge leaves, too).
        for table in reversed(AUX_TABLES):
            db.drop_table(table_swap.swap_prev_name(table))
        served = state.generation
        removed = q(REMOVED_GENERATION_COLUMN)
        ids = _observation_ids(ctx, f'{removed} IS NOT NULL AND {removed} <= %s', [served])
        import_util.log_info(ctx, f'Purging {len(ids)} retired observations')
        do_import_tables.delete_observations(ctx, ids)
        bundle_registry.purge_retired_copies(ctx, served)
        # Every row left is in the served generation.
        refresh_view(ctx, None)
        mult_done = do_finalize_mult.finalize_mult(ctx)
        do_import_tables.analyze_all_tables(ctx)
    load_generation_state(ctx)
    return mult_done


def abandon_generation(ctx: ImportContext) -> None:
    """Throw away an unswitched pending generation: ``--abandon-generation``.

    The rows the pending generation added are deleted from every observation table; the
    rows it retired are restored; its registry rows are deleted and the copies it retired
    made live again; its auxiliary ``__new`` tables are dropped; the view is re-created,
    with no condition unless retired rows remain; and last the version row's pending
    generation is cleared. Running it again after an interruption finishes the work.
    Refused while a switch of the pending generation, or a revert of it, has stopped part
    way (`unfinished_switch_problem`).

    Parameters:
        ctx: The import run's context.

    Raises:
        GenerationRefusedError: If refused.
    """
    with generation_command(ctx, '--abandon-generation'):
        state = _require_state(ctx)
        if state.pending is None:
            raise GenerationRefusedError('--abandon-generation refused: no generation is pending')
        pending = state.pending
        db = ctx.db
        assert db is not None
        # Abandoning deletes the rows a part-way switch has pointed the cart at, and would
        # serve the pending generation's auxiliary tables against the served rows.
        unfinished = unfinished_switch_problem(db, state)
        if unfinished is not None:
            raise GenerationRefusedError(f'--abandon-generation refused: {unfinished}')
        added, retired = _abandoned_ids(ctx, pending)
        import_util.log_info(
            ctx,
            f'Abandoning generation {pending}: deleting {len(added)} observations and '
            f'restoring {len(retired)}',
        )
        do_import_tables.delete_observations(ctx, added)
        do_import_tables.restore_retired_rows(ctx, retired, pending)
        bundle_registry.delete_generation_copies(ctx, pending)
        bundle_registry.restore_retired_copies(ctx, pending)
        table_swap.drop_swap_leftovers(ctx, AUX_TABLES)
        # Rows a purge that stopped part way left keep the view's condition.
        refresh_view(ctx, state.generation if _has_retired_rows(ctx) else None)
        _update_version_row(
            ctx,
            {PENDING_GENERATION_COLUMN: None, PENDING_STATE_COLUMN: None},
            PENDING_GENERATION_COLUMN,
            pending,
        )
        import_util.log_info(
            ctx, f'Generation {pending} abandoned; generation {state.generation} is served'
        )
    load_generation_state(ctx)


def generation_command_problem(option: str) -> str | None:
    """Say why a switch or a revert of the schema ``OPUS_CONFIG`` names would be refused.

    The deploy chain asks before it stops the web service, so a command that would change
    nothing leaves the site up. It asks what the command itself checks before it changes
    anything: the version row, the generation lock, and the invocations writing the
    pending generation. The connection is the import's own, opened read-only.

    Parameters:
        option: ``--switch-generation`` or ``--revert-generation``.

    Returns:
        None when the command would run; otherwise the reason it would be refused.

    Raises:
        ImportDBError: If the database cannot be read.
    """
    database = get_config().database
    db = importdb.get_db(
        database.brand,
        database.host,
        database.database,
        database.schema,
        database.user,
        database.password,
        read_only=True,
    )
    try:
        state = read_generation_state(db)
        if state is None:
            return f'"{database.schema}" has no single {SCHEMA_VERSION_TABLE} row'
        if db.named_lock_holder(_generation_lock(db)) is not None:
            return _lock_held_message(db)
        writers = _writers_message(db)
        if writers is not None:
            return writers
    finally:
        db.close()
    if option == '--revert-generation':
        return _revert_refusal(state)
    return _switch_refusal(state)
