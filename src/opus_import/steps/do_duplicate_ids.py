"""Keep one copy of each OPUS id: finalization's duplicate step.

Two bundles can produce the same OPUS id -- Galileo SSI does, and a calibrated bundle and
its raw counterpart can -- and ``obs_general.opus_id`` carries a plain key rather than a
unique one, so both copies load side by side and nothing looks for them while bundles
load. This step, run in finalization after the keys are built, keeps the copy with the
highest ``obs_general.id`` and deletes the others' rows from every observation table.
Ids are handed out in import order, so the copy kept is the one imported last; a bundle
imported again gets ids above every existing one, so its new copy replaces the old.

Each deleted copy is logged at info level when it came from another bundle than the copy
kept, and as a warning when it came from the same bundle, which is a fault in that
bundle's data. The step runs on the import's own connection, whose foreign-key checks
are on (only `ImportDBSuper.add_foreign_keys` turns them off, and it turns them back on),
so a row that references a deleted copy is refused rather than orphaned.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from opus_import import import_util

if TYPE_CHECKING:
    from collections.abc import Sequence

    from opus_import.context import ImportContext


def _duplicated_rows(ctx: ImportContext) -> Sequence[tuple[int, str, str]]:
    """Return every ``obs_general`` row whose OPUS id another row shares.

    Parameters:
        ctx: The import run's context, for the open database.

    Returns:
        ``(id, opus_id, bundle_id)`` rows, ordered by OPUS id and then id. The OPUS id is
        the one the server grouped by, so two that differ only in case under the
        column's collation come back as one.
    """
    db = ctx.db
    assert db is not None
    q = db.quote_identifier
    obs_general = q('obs_general')
    # Every interpolation is an identifier produced by quote_identifier
    # (^[A-Za-z0-9_]+$); the statement carries no values at all.
    rows = db.general_select(
        f'{q("g")}.{q("id")}, {q("d")}.{q("opus_id")}, {q("g")}.{q("bundle_id")} '  # nosec B608
        f'FROM {obs_general} {q("g")} JOIN (SELECT {q("opus_id")} FROM {obs_general} '
        f'GROUP BY {q("opus_id")} HAVING COUNT(*) > 1) {q("d")} '
        f'ON {q("d")}.{q("opus_id")} = {q("g")}.{q("opus_id")} '
        f'ORDER BY {q("d")}.{q("opus_id")}, {q("g")}.{q("id")}'
    )
    return [(int(row[0]), str(row[1]), str(row[2])) for row in rows]


def delete_duplicate_opus_ids(ctx: ImportContext) -> bool:
    """Delete every copy of a shared OPUS id but the one with the highest id.

    The deleted copies' rows go from every other observation table first, by
    ``obs_general_id``, then from ``obs_general``, `ImportDBSuper.transaction_rows` copies
    to a statement. The step ends by checking that no OPUS id has two rows.

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
    groups: dict[str, list[tuple[int, str]]] = {}
    for obs_general_id, opus_id, bundle_id in rows:
        groups.setdefault(opus_id, []).append((obs_general_id, bundle_id))

    deleted: list[int] = []
    for opus_id, copies in groups.items():
        kept_id, kept_bundle = copies[-1]
        for obs_general_id, bundle_id in copies[:-1]:
            message = (
                f'Duplicate OPUS ID "{opus_id}": keeping obs_general id {kept_id} from '
                f'{kept_bundle}, deleting id {obs_general_id} from {bundle_id}'
            )
            if bundle_id == kept_bundle:
                import_util.log_warning(ctx, message)
            else:
                import_util.log_info(ctx, message)
            deleted.append(obs_general_id)
    if deleted:
        import_util.log_info(
            ctx, f'Deleting {len(deleted)} duplicate copies of {len(groups)} OPUS IDs'
        )

    q = db.quote_identifier
    other_tables = [name for name in sorted(db.table_names(prefix='obs_')) if name != 'obs_general']
    for start in range(0, len(deleted), db.transaction_rows):
        chunk = deleted[start : start + db.transaction_rows]
        placeholders = ','.join(['%s'] * len(chunk))
        for table_name in other_tables:
            db.delete_rows(
                table_name,
                f'{q("obs_general_id")} IN ({placeholders})',
                where_params=chunk,
            )
        db.delete_rows('obs_general', f'{q("id")} IN ({placeholders})', where_params=chunk)

    if not db.read_only and _duplicated_rows(ctx):
        import_util.log_error(ctx, 'An OPUS ID still has more than one obs_general row')
        return False
    return True
