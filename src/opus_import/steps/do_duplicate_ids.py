"""Keep one copy of each OPUS id: finalization's duplicate step.

Two bundles can produce the same OPUS id -- Galileo SSI does, and a calibrated bundle and
its raw counterpart can -- and ``obs_general.opus_id`` carries a plain key rather than a
unique one, so both copies load side by side and nothing looks for them while bundles
load. This step, run in finalization after the keys are built, keeps the copy with the
highest ``obs_general.id`` and deletes the others' rows from every observation table.
A bundle's ids come from its registered range, and the ranges ascend in registration
order (`opus_import.bundle_registry`), so the copy kept is the one from the bundle
registered later, which on a full import is the later bundle in import order. A bundle
imported again keeps its number and its range, so importing it again does not change
which copy that is.

Only the rows of the generation the run works on are compared
(`ImportContext.import_generation`, `opus_import.generations`). With a pending generation,
a losing copy the pending generation added is deleted, and one an earlier generation
added, which the served generation still shows, is retired at the pending generation
instead (`opus_import.steps.do_import_tables.retire_bundle_rows` retires the same way).

Each deleted copy is logged at info level when it came from another bundle than the copy
kept, and as a warning when it came from the same bundle, which is a fault in that
bundle's data. The step runs on the import's own connection, whose foreign-key checks
are on (`ImportDBSuper.foreign_keys_unchecked`, which turns them off while foreign keys
are added and while a bundle loads, turns them back on), so a row that references a
deleted copy is refused rather than orphaned.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from opus_import import generations, import_util
from opus_import.steps import do_import_tables

if TYPE_CHECKING:
    from collections.abc import Sequence

    from opus_import.context import ImportContext


def _duplicated_rows(ctx: ImportContext) -> Sequence[tuple[int, str, str, int]]:
    """Return every ``obs_general`` row of the run's generation whose OPUS id another row
    of it shares.

    Parameters:
        ctx: The import run's context, for the open database and the generation.

    Returns:
        ``(id, opus_id, bundle_id, added_generation)`` rows, ordered by OPUS id and then
        id. The OPUS id is the one the server grouped by, so two that differ only in case
        under the column's collation come back as one.
    """
    db = ctx.db
    assert db is not None
    q = db.quote_identifier
    obs_general = q('obs_general')
    generation = ctx.import_generation
    # Every interpolation is an identifier produced by quote_identifier
    # (^[A-Za-z0-9_]+$); the generation is a parameter.
    rows = db.general_select(
        f'{q("g")}.{q("id")}, {q("d")}.{q("opus_id")}, {q("g")}.{q("bundle_id")}, '  # nosec B608
        f'{q("g")}.{q(generations.ADDED_GENERATION_COLUMN)} '
        f'FROM {obs_general} {q("g")} JOIN (SELECT {q("opus_id")} FROM {obs_general} {q("i")} '
        f'WHERE {generations.in_generation_condition(q, "i")} '
        f'GROUP BY {q("opus_id")} HAVING COUNT(*) > 1) {q("d")} '
        f'ON {q("d")}.{q("opus_id")} = {q("g")}.{q("opus_id")} '
        f'WHERE {generations.in_generation_condition(q, "g")} '
        f'ORDER BY {q("d")}.{q("opus_id")}, {q("g")}.{q("id")}',
        [generation] * 4,
    )
    return [(int(row[0]), str(row[1]), str(row[2]), int(row[3])) for row in rows]


def delete_duplicate_opus_ids(ctx: ImportContext) -> bool:
    """Delete every copy of a shared OPUS id but the one with the highest id.

    The deleted copies' rows go from every other observation table first, by
    ``obs_general_id``, then from ``obs_general``, `ImportDBSuper.transaction_rows` copies
    to a statement (`opus_import.steps.do_import_tables.delete_observations`); with a
    pending generation, a copy an earlier generation added is retired instead. The step
    ends by checking that no OPUS id has two rows in the generation.

    Parameters:
        ctx: The import run's context, for the open database and the logger.

    Returns:
        True when every OPUS id is left with one row; False, logged, when one is not.
    """
    db = ctx.db
    assert db is not None
    if not db.table_exists('obs_general'):
        return True
    rows = _duplicated_rows(ctx)
    groups: dict[str, list[tuple[int, str, int]]] = {}
    for obs_general_id, opus_id, bundle_id, added in rows:
        groups.setdefault(opus_id, []).append((obs_general_id, bundle_id, added))

    pending = ctx.pending_generation
    deleted: list[int] = []
    retired: list[int] = []
    for opus_id, copies in groups.items():
        kept_id, kept_bundle, _kept_added = copies[-1]
        for obs_general_id, bundle_id, added in copies[:-1]:
            message = (
                f'Duplicate OPUS ID "{opus_id}": keeping obs_general id {kept_id} from '
                f'{kept_bundle}, deleting id {obs_general_id} from {bundle_id}'
            )
            if bundle_id == kept_bundle:
                import_util.log_warning(ctx, message)
            else:
                import_util.log_info(ctx, message)
            if pending is not None and added != pending:
                retired.append(obs_general_id)
            else:
                deleted.append(obs_general_id)
    if deleted:
        import_util.log_info(
            ctx, f'Deleting {len(deleted)} duplicate copies of {len(groups)} OPUS IDs'
        )

    do_import_tables.delete_observations(ctx, deleted)
    if pending is not None and retired:
        import_util.log_info(
            ctx, f'Retiring {len(retired)} copies the served generation shows at {pending}'
        )
        q = db.quote_identifier
        for start in range(0, len(retired), db.transaction_rows):
            chunk = retired[start : start + db.transaction_rows]
            placeholders = ','.join(['%s'] * len(chunk))
            db.update_row(
                'obs_general',
                {generations.REMOVED_GENERATION_COLUMN: pending},
                f'{q("id")} IN ({placeholders})',
                chunk,
            )

    if not db.read_only and _duplicated_rows(ctx):
        import_util.log_error(ctx, 'An OPUS ID still has more than one obs_general row')
        return False
    return True
