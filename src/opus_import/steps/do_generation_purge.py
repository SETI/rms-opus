"""The generation commands that delete rows: the purge and the abandon.

``--purge-generations`` (`purge_generations`) deletes the rows a switch retired, once the
switched generation has been checked, while the site serves; ``--abandon-generation``
(`abandon_generation`) throws away a pending generation that was never switched in, or
was reverted. Each is a generation command (`opus_import.steps.do_generation`): it holds
the schema's generation lock for its whole run, is refused while a writer is alive, and
raises `opus_import.steps.do_generation.GenerationRefusedError` before it changes anything
when refused.

Both leave every row of ``obs_general_rows`` in the served generation, and the version
row says so only once they have: the purge clears ``revertible`` after its last delete,
and the abandon clears the pending generation after its last. The web application reads
those columns to decide whether a statement reading a child table joins the served
observations (`opus_app.apps.tools.db_utils.unserved_observations_exist`).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from opus_import import bundle_registry, import_util, table_swap
from opus_import.generations import (
    ADDED_GENERATION_COLUMN,
    PENDING_GENERATION_COLUMN,
    PENDING_STATE_COLUMN,
    PENDING_WRITING,
    REMOVED_GENERATION_COLUMN,
    REVERTIBLE_COLUMN,
    SERVED_GENERATION_COLUMN,
)
from opus_import.steps import do_finalize_mult, do_generation, do_import_tables

if TYPE_CHECKING:
    from collections.abc import Callable

    from opus_import.context import ImportContext

#: The `opus_import.import_fault` site inside ``--purge-generations``. Its argument is a
#: step's number, `PURGE_STEPS` counting from 1; the purge raises after that step.
PURGE_FAULT_SITE = 'purge_generations'

#: The steps of ``--purge-generations``, in order, as the log and the fault site name them.
PURGE_STEPS = (
    'drop the auxiliary tables a revert swaps back',
    'delete the retired observations',
    'delete the retired registry rows',
    'show every row in the view',
    "end the switch's revertibility",
)


def _purge_step(ctx: ImportContext, number: int, step: Callable[[], object]) -> None:
    """Run one step of the purge, then raise there if a test names it.

    Parameters:
        ctx: The import run's context, for the log.
        number: The step's number, from 1.
        step: The step, a callable taking nothing.

    Raises:
        InjectedImportFaultError: If `PURGE_FAULT_SITE` names this step.
    """
    do_generation.command_step(ctx, 'Purge', PURGE_FAULT_SITE, PURGE_STEPS, number, step)


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


def _drop_revert_tables(ctx: ImportContext) -> None:
    """Drop the auxiliary tables a revert would swap back, the purge's first step.

    A rebuild's leftover ``__new`` and ``__old`` tables go before the ``__prev`` tables, so
    a purge that stops part way never leaves ``__new`` tables with no ``__prev`` beside
    them, the shape of a revert that stopped part way
    (`opus_import.steps.do_generation.unfinished_switch_problem`).

    Parameters:
        ctx: The import run's context, for the open database.
    """
    db = ctx.db
    assert db is not None
    table_swap.drop_swap_leftovers(ctx, do_generation.AUX_TABLES)
    for table in reversed(do_generation.AUX_TABLES):
        db.drop_table(table_swap.swap_prev_name(table))


def _delete_retired_observations(ctx: ImportContext, served: int) -> None:
    """Delete every observation retired at or before the served generation.

    Parameters:
        ctx: The import run's context, for the open database.
        served: The served generation.
    """
    db = ctx.db
    assert db is not None
    removed = db.quote_identifier(REMOVED_GENERATION_COLUMN)
    ids = _observation_ids(ctx, f'{removed} IS NOT NULL AND {removed} <= %s', [served])
    import_util.log_info(ctx, f'Purging {len(ids)} retired observations')
    do_import_tables.delete_observations(ctx, ids)


def purge_generations(ctx: ImportContext) -> bool:
    """Delete the rows no served generation shows: ``--purge-generations``.

    Run after a switch, while the site serves. Refused while a generation is pending, and
    while a revert has stopped part way
    (`opus_import.steps.do_generation.unfinished_switch_problem`). Its steps, in order
    (`PURGE_STEPS`):

    #. the auxiliary ``__new`` and ``__old`` tables a rebuild left are dropped, then the
       ``__prev`` tables, so a revert is refused from before the first row goes
       (`opus_import.steps.do_generation.unfinished_purge_problem`);
    #. every observation retired at or before the served generation is deleted from every
       observation table, children first, with foreign keys checked;
    #. the registry rows of the copies retired by then are deleted;
    #. the view is re-created with no condition, every row left being in the served
       generation;
    #. last, ``revertible`` is cleared.

    Then it runs finalization's mult step and ``ANALYZE``. ``revertible`` stays set for
    as long as retired rows remain, which is what tells the web application to keep a
    child table's rows to the served observations, and what refuses a begin until the
    purge is finished. The rows it deletes are in no served generation, so no request
    reads them. Every step can run again harmlessly, so an interrupted purge is finished
    by running it again; a test makes it fail after a step through `PURGE_FAULT_SITE`.

    Parameters:
        ctx: The import run's context.

    Returns:
        True if it ran; False, logged, if its mult step failed.

    Raises:
        do_generation.GenerationRefusedError: If refused.
    """
    with do_generation.generation_command(ctx, '--purge-generations'):
        state = do_generation.require_state(ctx)
        if state.pending is not None:
            raise do_generation.GenerationRefusedError(
                f'--purge-generations refused: generation {state.pending} is pending; '
                'switch it in or abandon it first'
            )
        db = ctx.db
        assert db is not None
        # The purge deletes the retired rows a part-way revert has pointed the cart at.
        unfinished = do_generation.unfinished_switch_problem(db, state)
        if unfinished is not None:
            raise do_generation.GenerationRefusedError(f'--purge-generations refused: {unfinished}')
        served = state.generation
        _purge_step(ctx, 1, lambda: _drop_revert_tables(ctx))
        _purge_step(ctx, 2, lambda: _delete_retired_observations(ctx, served))
        _purge_step(ctx, 3, lambda: bundle_registry.purge_retired_copies(ctx, served))
        # Every row left is in the served generation.
        _purge_step(ctx, 4, lambda: do_generation.refresh_view(ctx, None))
        _purge_step(
            ctx,
            5,
            lambda: do_generation.update_version_row(
                ctx, {REVERTIBLE_COLUMN: 0}, SERVED_GENERATION_COLUMN, served
            ),
        )
        mult_done = do_finalize_mult.finalize_mult(ctx)
        do_import_tables.analyze_all_tables(ctx)
    do_generation.load_generation_state(ctx)
    return mult_done


def abandon_generation(ctx: ImportContext) -> None:
    """Throw away an unswitched pending generation: ``--abandon-generation``.

    First the pending generation is marked ``writing``, so a switch refuses it from before
    the first row goes. The rows it added are then deleted from every observation table,
    and with them every other observation table's rows in the id ranges it registered,
    which a killed import can leave with no ``obs_general`` row; the rows it retired are
    restored; its registry rows are deleted and the copies it retired made live again;
    its auxiliary ``__new`` tables are dropped; the view is re-created with no condition,
    since the generation was begun with no row retired
    (`opus_import.steps.do_generation.begin_generation`), so every retired row was retired
    by it and has been restored; and last the version row's pending generation is cleared.
    Running it again after an interruption finishes the work. Refused while a switch of
    the pending generation, or a revert of it, has stopped part way
    (`opus_import.steps.do_generation.unfinished_switch_problem`).

    Parameters:
        ctx: The import run's context.

    Raises:
        do_generation.GenerationRefusedError: If refused.
    """
    with do_generation.generation_command(ctx, '--abandon-generation'):
        state = do_generation.require_state(ctx)
        if state.pending is None:
            raise do_generation.GenerationRefusedError(
                '--abandon-generation refused: no generation is pending'
            )
        pending = state.pending
        db = ctx.db
        assert db is not None
        # Abandoning deletes the rows a part-way switch has pointed the cart at, and would
        # serve the pending generation's auxiliary tables against the served rows.
        unfinished = do_generation.unfinished_switch_problem(db, state)
        if unfinished is not None:
            raise do_generation.GenerationRefusedError(
                f'--abandon-generation refused: {unfinished}'
            )
        # A ready generation would otherwise stay switchable after an interruption that
        # left it part deleted.
        do_generation.update_version_row(
            ctx, {PENDING_STATE_COLUMN: PENDING_WRITING}, PENDING_GENERATION_COLUMN, pending
        )
        added, retired = _abandoned_ids(ctx, pending)
        import_util.log_info(
            ctx,
            f'Abandoning generation {pending}: deleting {len(added)} observations and '
            f'restoring {len(retired)}',
        )
        do_import_tables.delete_observations(ctx, added)
        do_import_tables.delete_rows_in_id_ranges(
            ctx,
            [
                (registered.first_id, registered.end - 1)
                for registered in bundle_registry.registered_ranges(db, include_retired=True)
                if registered.generation == pending
            ],
        )
        do_import_tables.restore_retired_rows(ctx, retired, pending)
        bundle_registry.delete_generation_copies(ctx, pending)
        bundle_registry.restore_retired_copies(ctx, pending)
        table_swap.drop_swap_leftovers(ctx, do_generation.AUX_TABLES)
        # Every row left is in the served generation: the generation was begun with no
        # row retired, so every retired row was retired by it and is restored above.
        do_generation.refresh_view(ctx, None)
        do_generation.update_version_row(
            ctx,
            {PENDING_GENERATION_COLUMN: None, PENDING_STATE_COLUMN: None},
            PENDING_GENERATION_COLUMN,
            pending,
        )
        import_util.log_info(
            ctx, f'Generation {pending} abandoned; generation {state.generation} is served'
        )
    do_generation.load_generation_state(ctx)
