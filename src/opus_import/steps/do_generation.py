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
- ``--purge-generations``, run while the site serves, first drops the auxiliary tables a
  revert would swap back, then deletes the rows no served generation shows, and last ends
  the switch's revertibility.
- ``--abandon-generation`` throws away an unswitched P, and ``--revert-generation``
  (`revert_generation`) runs a switch backward until the purge.

The purge and the abandon, the two commands that delete rows, are in
`opus_import.steps.do_generation_purge`, and are built from this module's lock, version
row and view.

A switch or a revert that stopped part way leaves the auxiliary tables in a shape no
finished one leaves (`unfinished_switch_problem`), and until it is completed or undone,
the abandon, the purge and every write to P are refused: each would delete rows the cart
was pointed at, or drop auxiliary tables the way back needs. A purge that stopped part way
leaves a revertible switch without its ``__prev`` tables (`unfinished_purge_problem`), and
until it is run again the revert, the begin and every rebuild of the served auxiliary
tables are refused.

The version row names a pending generation or marks the switch revertible for exactly as
long as ``obs_general_rows`` holds rows outside the served generation: from the begin,
which records the pending generation before any of its rows is written, until the abandon
has deleted them, or from the switch until the purge has deleted the rows it retired. The
web application reads the row to decide whether a statement reading a child table joins
the served observations (`opus_app.apps.tools.db_utils.unserved_observations_exist`).

Each command holds a server-wide named lock on the schema for its whole run and is
refused while another holds it; every invocation that writes the schema, P or the served
rows, registers itself in ``import_process`` with its liveness lock while briefly holding
that lock (`register_writer`), and a command is refused while any registered invocation is
alive. An invocation that moves P's state forward, ``--finalize``, ``--validate`` or
``--write-schema-version``, registers as P's sole writer, so the state it records
describes rows no other invocation changed meanwhile. A refused command raises
`GenerationRefusedError` before it changes anything, and ``opus_import`` then exits with
`GENERATION_REFUSED_EXIT_STATUS`, so the deploy chain can tell a refusal from a command
that stopped part way.
"""

from __future__ import annotations

import contextlib
from typing import TYPE_CHECKING

from opus_import import import_processes, import_util, importdb, table_swap
from opus_import.generations import (
    FIRST_GENERATION,
    GENERATION_LOCK,
    GENERATION_SOLE_WRITER_LOCK,
    OBS_GENERAL_VIEW,
    PENDING_GENERATION_COLUMN,
    PENDING_READY,
    PENDING_STATE_COLUMN,
    PENDING_WRITING,
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
from opus_import.steps import do_django

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

    A ``schema_version`` table without the generation columns, which a schema of an earlier
    version has, holds no generation either, so such a schema reaches the version check
    that refuses it, or the erase that ends it, rather than a failed read.

    Parameters:
        db: The open database.
    """
    db.forget_table_names()
    if not db.table_exists(SCHEMA_VERSION_TABLE):
        return None
    present = {column['field_name'] for column in db.table_info(SCHEMA_VERSION_TABLE)}
    if not present.issuperset(STATE_COLUMNS):
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


def require_state(ctx: ImportContext) -> GenerationState:
    """Return the schema's version row, read again, refusing a schema without one.

    Raises:
        GenerationRefusedError: If the schema has no single version row.
    """
    assert ctx.db is not None
    state = read_generation_state(ctx.db)
    if state is None:
        raise GenerationRefusedError(
            f'"{ctx.db.db_schema}" has no single {SCHEMA_VERSION_TABLE} row with the '
            'generation columns, so it has no generation: an incremental update writes a '
            f'finished schema of version {SCHEMA_VERSION}'
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


def _sole_writer_lock(db: ImportDBSuper) -> str:
    """Return the name of the lock a sole writer of the pending generation holds."""
    return importdb.lock_name(db.db_schema, GENERATION_SOLE_WRITER_LOCK)


def _generations(state: GenerationState | None) -> tuple[int, int | None] | None:
    """Return the served and pending generations of a version row, None without one."""
    return None if state is None else (state.generation, state.pending)


def _describe_generations(state: GenerationState | None) -> str:
    """Return what a version row serves and holds pending, for a refusal."""
    if state is None:
        return f'the schema has no single {SCHEMA_VERSION_TABLE} row with a generation'
    pending = 'none' if state.pending is None else f'generation {state.pending}'
    return f'generation {state.generation} is served and {pending} is pending'


def register_writer(ctx: ImportContext, *, sole: bool = False) -> import_processes.ImporterLock:
    """Record an invocation that writes the schema in ``import_process``.

    The row and its liveness lock are taken on a connection of their own while briefly
    holding the generation lock, so no generation command starts between this
    invocation's check and its registration, and every generation command is refused
    while the row's lock is held. The version row is read again under the lock: the
    invocation chose its path by the row it read as it started, and a begin, a switch or
    an abandon may have run since.

    A sole writer of the pending generation, one that moves its state forward, is refused
    while any other registered invocation is alive, and holds a lock of its own on the
    same connection until it ends, which refuses every other writer of the pending
    generation meanwhile; so the state it records after reading the generation describes
    rows nothing else wrote while it read them.

    Parameters:
        ctx: The import run's context, for the open database and the log's path, and the
            version row it read as it started (`ImportContext.generation_state`), which
            is replaced by the one read under the lock.
        sole: Whether the invocation writes the pending generation as its sole writer.

    Returns:
        The invocation's row and lock, which it frees when it ends
        (`opus_import.import_processes.ImporterLock.exit`).

    Raises:
        GenerationRefusedError: If a generation command holds the generation lock; the
            served or pending generation is not the one the invocation started by; a
            switch of the pending generation stopped part way; another invocation is
            alive and this one would be the sole writer; or a sole writer is alive.
    """
    db = ctx.db
    assert db is not None
    name = _generation_lock(db)
    if not db.try_named_lock(name):
        raise GenerationRefusedError(
            f'A generation command holds "{db.db_schema}"\'s generation lock, so nothing '
            'writes the schema until it ends'
        )
    try:
        started = ctx.generation_state
        state = read_generation_state(db)
        if _generations(state) != _generations(started):
            lost = (
                'The schema changed'
                if started is None or started.pending is None
                else f'Generation {started.pending} is no longer pending'
            )
            raise GenerationRefusedError(
                f'{lost}: {_describe_generations(state)}, since a generation command ran '
                'while this invocation started; run it again'
            )
        ctx.generation_state = state
        if state is not None and state.pending is not None:
            unfinished = unfinished_switch_problem(db, state)
            if unfinished is not None:
                raise GenerationRefusedError(
                    f'Nothing writes generation {state.pending} now: {unfinished}'
                )
            _refuse_beside_sole_writer(db, state.pending, sole=sole)
        import_processes.create_process_table(db)
        lock_db = db.open_sibling_connection()
        writer = import_processes.start_importer(lock_db, ctx.log_path or '')
        if sole and not lock_db.try_named_lock(_sole_writer_lock(db)):
            writer.exit()
            raise GenerationRefusedError(
                f'Another invocation holds generation {ctx.pending_generation} as its sole '
                'writer; wait for it to finish'
            )
        return writer
    finally:
        db.release_named_lock(name)


def _refuse_beside_sole_writer(db: ImportDBSuper, pending: int, *, sole: bool) -> None:
    """Refuse a writer of the pending generation that would run beside a sole writer.

    Parameters:
        db: The open database, holding the generation lock.
        pending: The pending generation.
        sole: Whether the writer would be the sole writer itself.

    Raises:
        GenerationRefusedError: If a sole writer is alive, or this one would be and
            another registered invocation is alive.
    """
    if db.named_lock_holder(_sole_writer_lock(db)) is not None:
        raise GenerationRefusedError(
            f'Generation {pending} is being finalized, validated or stamped, which runs '
            'alone; wait for it to finish'
        )
    if not sole:
        return
    alive = _alive_writers(db)
    if alive:
        raise GenerationRefusedError(
            f'import_process {", ".join(str(process) for process in alive)} still writing '
            f'"{db.db_schema}"; --finalize, --validate and --write-schema-version run alone '
            f'on generation {pending}, so wait for them to finish'
        )


def update_version_row(
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
    generation. A revertible switch with neither, or with only some ``__prev`` tables, is
    a purge that stopped part way (`unfinished_purge_problem`): the purge drops every
    ``__new`` table before the first ``__prev`` one.

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


def unfinished_purge_problem(db: ImportDBSuper, state: GenerationState) -> str | None:
    """Say whether a purge stopped part way, and how to finish it.

    The purge drops the leftover ``__new`` tables, then the ``__prev`` tables, before it
    deletes the first retired row, and clears ``revertible`` only once the last is gone and
    the view shows every row. So a revertible switch with nothing pending whose ``__prev``
    tables are not all there, and no ``__new`` table beside them (which a revert that
    stopped part way leaves instead, `unfinished_switch_problem`), is one whose purge has
    started: the previous generation may have lost rows, so no revert can serve it again,
    and running the purge again finishes the work.

    Parameters:
        db: The open database.
        state: The schema's version row.

    Returns:
        None when no purge is unfinished; otherwise what is unfinished and the command
        that finishes it.
    """
    if state.pending is not None or not state.revertible:
        return None
    kept = _existing_tables(db, table_swap.swap_prev_name)
    if len(kept) == len(AUX_TABLES) or _existing_tables(db, table_swap.swap_new_name):
        return None
    return (
        f'the purge of the rows generation {state.generation} retired has started, so '
        f'generation {state.generation - 1} cannot be served again; '
        '"opus_import --purge-generations" finishes it'
    )


def unfinished_rebuild_problem(db: ImportDBSuper, state: GenerationState) -> str | None:
    """Say whether a rebuild of the served auxiliary tables stopped part way beside a
    revertible switch, so that completing the switch would swap its tables in.

    With nothing pending and the switch revertible, a whole set of ``__prev`` tables is
    the previous generation's, kept for a revert, and no switch or revert leaves ``__new``
    tables beside it; a rebuild of the served auxiliary tables builds its tables under
    those names before it swaps them in. Completing the switch would drop the ``__prev``
    set and swap in whatever the rebuild left, so it is refused until the rebuild has been
    run again. A revert drops the ``__new`` tables before it swaps the ``__prev`` ones
    back, so it is not refused.

    Parameters:
        db: The open database.
        state: The schema's version row.

    Returns:
        None when no such rebuild is unfinished; otherwise what is unfinished and the
        command that finishes it.
    """
    if state.pending is not None or not state.revertible:
        return None
    if len(_existing_tables(db, table_swap.swap_prev_name)) != len(AUX_TABLES):
        return None
    built = _existing_tables(db, table_swap.swap_new_name)
    if not built:
        return None
    return (
        f'a rebuild of the served auxiliary tables stopped part way ({", ".join(built)} '
        f"beside generation {state.generation - 1}'s __prev tables); running that rebuild "
        'again finishes it'
    )


def begin_generation(ctx: ImportContext) -> None:
    """Start a pending generation, one above the served one: ``--begin-generation``.

    Refused unless the schema's one version row holds this release's version, ``ready``,
    with no pending generation and no switch still revertible, which leaves no retired row
    and no ``__prev`` table: the purge deletes and drops them all before it ends the
    switch's revertibility, and an abandon restores every row it retired. The
    ``obs_general`` view is re-created to show the served generation alone before the
    pending one is recorded (`refresh_view`).

    Parameters:
        ctx: The import run's context.

    Raises:
        GenerationRefusedError: If refused.
    """
    with generation_command(ctx, '--begin-generation'):
        state = require_state(ctx)
        db = ctx.db
        assert db is not None
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
            unfinished = unfinished_purge_problem(db, state)
            problem = (
                f'can still revert to generation {state.generation - 1}; '
                '"opus_import --purge-generations" ends that, or "--revert-generation" '
                'then "--abandon-generation" undoes the switch'
                if unfinished is None
                else f'holds retired rows: {unfinished}'
            )
        if problem is not None:
            raise GenerationRefusedError(f'--begin-generation refused: the schema {problem}')
        pending = state.generation + 1
        # Before the generation is recorded, so no row of it is ever written while
        # the view shows every row.
        refresh_view(ctx, state.generation)
        update_version_row(
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
        'no switch is revertible (a purge has ended it, or no generation was switched in) '
        'and no pending generation is ready'
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
    that stopped part way; that is refused while a purge is unfinished
    (`unfinished_purge_problem`), which a rerun of the purge finishes instead, and while a
    rebuild of the served auxiliary tables is (`unfinished_rebuild_problem`), whose
    tables it would otherwise swap in.

    Parameters:
        ctx: The import run's context.

    Raises:
        GenerationRefusedError: If refused.
    """
    with generation_command(ctx, '--switch-generation'):
        state = require_state(ctx)
        db = ctx.db
        assert db is not None
        refusal = (
            _switch_refusal(state)
            or unfinished_purge_problem(db, state)
            or unfinished_rebuild_problem(db, state)
        )
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
        update_version_row(
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
    command_step(ctx, 'Switch', SWITCH_FAULT_SITE, SWITCH_STEPS, number, step)


def command_step(
    ctx: ImportContext,
    command: str,
    site: str,
    names: tuple[str, ...],
    number: int,
    step: Callable[[], object],
) -> None:
    """Run one numbered step of a generation command, then raise if a test names it.

    Parameters:
        ctx: The import run's context, for the log.
        command: The command, as the log names it.
        site: The command's `opus_import.import_fault` site.
        names: The command's steps, as the log names them.
        number: The step's number, from 1.
        step: The step, a callable taking nothing.

    Raises:
        InjectedImportFaultError: If ``site`` names this step.
    """
    import_util.log_info(ctx, f'{command} step {number}: {names[number - 1]}')
    step()
    if import_fault_argument(site) == str(number):
        raise InjectedImportFaultError(f'{site}:{number}')


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
    ``__new``; the cart is pointed at the previous generation, though a cart row the
    switch deleted, its OPUS ID absent from the switched-in generation, is not restored;
    the search tables are reset; the view is re-created to show the previous generation;
    and last, the previous generation is served again with the reverted-from one pending and
    ``ready``, and the switch is not revertible any more, so the reverted-from generation
    can be abandoned or switched again. Each step finds out whether it has run, as the
    switch's do. A switch that stopped before its last statement left its generation
    pending and ``ready``, and the same steps, in the opposite order, undo whatever of it
    ran, the served generation unchanged (`_revert_steps`). Refused otherwise: once the
    purge has started (`unfinished_purge_problem`), since it drops the ``__prev`` tables
    before the first retired row goes, or with nothing switched.

    Parameters:
        ctx: The import run's context.

    Raises:
        GenerationRefusedError: If refused.
    """
    with generation_command(ctx, '--revert-generation'):
        state = require_state(ctx)
        db = ctx.db
        assert db is not None
        refusal = _revert_refusal(state) or unfinished_purge_problem(db, state)
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
        update_version_row(
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


#: What `generation_problem` answers for: a switch, a revert, an update that writes into
#: the pending generation without beginning one, and a rebuild of the served auxiliary
#: tables in place, as a code-only deploy runs.
CHECK_SWITCH = 'switch'
CHECK_REVERT = 'revert'
CHECK_CONTINUE = 'continue'
CHECK_REBUILD = 'rebuild'


def generation_problem(db: ImportDBSuper, action: str) -> str | None:
    """Say why a generation action on the schema would be refused, reading without writing.

    The deploy chain asks, through ``opus_import --check``, before it acts: before it
    stops the web service for a switch or a revert, so a command that would change nothing
    leaves the site up; before an update that skips ``--begin-generation`` writes
    anything, since without a pending generation its imports would take the append path
    and write the served rows; and before a code-only deploy rebuilds the served
    auxiliary tables, since with a generation pending the rebuild would leave the new
    tables for its switch while the dictionary and the mult labels changed in place. It
    asks what the action itself checks before it changes anything: the version row, the
    generation lock, the invocations writing the pending generation (except for a rebuild,
    which an append may run beside), and whether a switch, a revert or a purge stopped
    part way: for a continuation a switch, which refuses every write to the generation.

    Parameters:
        db: A connection to the schema, which may be read-only.
        action: `CHECK_SWITCH`, `CHECK_REVERT`, `CHECK_CONTINUE` or `CHECK_REBUILD`.

    Returns:
        None when the action would run; otherwise the reason it would be refused.

    Raises:
        ImportDBError: If the database cannot be read.
    """
    state = read_generation_state(db)
    if state is None:
        return f'"{db.db_schema}" has no single {SCHEMA_VERSION_TABLE} row'
    if action == CHECK_CONTINUE and state.pending is None:
        return (
            f'"{db.db_schema}" has no pending generation to continue (generation '
            f'{state.generation} served); an update without --continue begins one'
        )
    if action == CHECK_REBUILD and state.pending is not None:
        return (
            f'generation {state.pending} of "{db.db_schema}" is pending, and a rebuild would '
            'leave the auxiliary tables it builds for its switch; promote or abandon it first'
        )
    if db.named_lock_holder(_generation_lock(db)) is not None:
        return _lock_held_message(db)
    if action == CHECK_REBUILD:
        return unfinished_switch_problem(db, state) or unfinished_purge_problem(db, state)
    writers = _writers_message(db)
    if action == CHECK_CONTINUE:
        # A switch that stopped part way refuses every write to the generation it was
        # switching until it is completed or reverted.
        return writers or unfinished_switch_problem(db, state)
    if writers is not None:
        return writers
    if action == CHECK_REVERT:
        return _revert_refusal(state) or unfinished_purge_problem(db, state)
    return (
        _switch_refusal(state)
        or unfinished_purge_problem(db, state)
        or unfinished_rebuild_problem(db, state)
    )
