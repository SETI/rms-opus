"""The bundle registry: the import's record of which bundles it has imported.

Every invocation that imports bundles records each bundle it is about to import in one
table, ``import_bundle``, with a state: ``pending`` until its turn comes, ``importing``
while it is deleted and loaded, and then ``done``, or ``failed`` when it logged an error.
A bundle OPUS deliberately skips (`opus_import.steps.do_import_tables.opus_imports_bundle`)
is never recorded, so no row waits for an import that will never come.

The registry is what keeps a half-finished import from being finished: finalization and
the schema version step both refuse while any bundle in it is not ``done``
(`unfinished_bundles`). An append into a finalized schema that fails part way leaves its
bundles recorded, and the next import into that schema resumes every one that is not
``done``.

The table is created with every key its schema declares, by the first invocation that
needs it, on either write path.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from typing import TYPE_CHECKING

from opus_import import import_util

if TYPE_CHECKING:
    from opus_import.context import ImportContext

#: The table holding the registry.
BUNDLE_REGISTRY_TABLE = 'import_bundle'

#: A bundle recorded for import and not yet started.
BUNDLE_PENDING = 'pending'

#: A bundle being deleted and loaded.
BUNDLE_IMPORTING = 'importing'

#: A bundle whose import finished without logging an error, or under ``--ignore-errors``.
BUNDLE_DONE = 'done'

#: A bundle whose import logged an error, or stopped.
BUNDLE_FAILED = 'failed'


def create_registry(ctx: ImportContext) -> None:
    """Create the registry table if the schema does not have it.

    Parameters:
        ctx: The import run's context, for the open database.
    """
    db = ctx.db
    assert db is not None
    if db.table_exists(BUNDLE_REGISTRY_TABLE):
        return
    schema = import_util.read_schema_for_table(ctx, BUNDLE_REGISTRY_TABLE)
    # import_bundle.json is packaged with opus_import, so the schema is always found.
    assert schema is not None
    db.create_table(BUNDLE_REGISTRY_TABLE, schema, ignore_if_exists=False)


def registered_bundles(ctx: ImportContext) -> list[tuple[str, str]]:
    """Return every bundle the registry holds, with its state.

    Parameters:
        ctx: The import run's context, for the open database.

    Returns:
        ``(bundle, state)`` pairs, ordered by bundle; none when the table is absent.
    """
    db = ctx.db
    assert db is not None
    if not db.table_exists(BUNDLE_REGISTRY_TABLE):
        return []
    rows = db.read_rows(BUNDLE_REGISTRY_TABLE, ['bundle_id', 'state'])
    return sorted((str(bundle_id), str(state)) for bundle_id, state in rows)


def unfinished_bundles(ctx: ImportContext) -> list[tuple[str, str]]:
    """Return the bundles in the registry that are not ``done``, with their states.

    Parameters:
        ctx: The import run's context, for the open database.

    Returns:
        ``(bundle, state)`` pairs, ordered by bundle; none when the table is absent or
        every bundle is ``done``.
    """
    return [(bundle, state) for bundle, state in registered_bundles(ctx) if state != BUNDLE_DONE]


def unfinished_message(unfinished: Sequence[tuple[str, str]]) -> str:
    """Name every unfinished bundle with its state, for a refusal.

    Parameters:
        unfinished: What `unfinished_bundles` returned; not empty.

    Returns:
        The bundles as ``<bundle> (<state>)``, joined by commas.
    """
    return ', '.join(f'{bundle} ({state})' for bundle, state in unfinished)


def register_bundles(ctx: ImportContext, bundle_ids: Iterable[str]) -> None:
    """Record bundles as ``pending``, adding the ones the registry does not hold yet.

    Parameters:
        ctx: The import run's context, for the open database.
        bundle_ids: The bundles about to be imported.
    """
    db = ctx.db
    assert db is not None
    rows = [{'bundle_id': bundle_id, 'state': BUNDLE_PENDING} for bundle_id in bundle_ids]
    if rows:
        db.upsert_rows(BUNDLE_REGISTRY_TABLE, 'bundle_id', rows)


def set_bundle_state(ctx: ImportContext, bundle_id: str, state: str) -> None:
    """Move one registered bundle to a new state.

    Parameters:
        ctx: The import run's context, for the open database.
        bundle_id: The bundle.
        state: Its new state, one of the ``BUNDLE_`` constants.
    """
    db = ctx.db
    assert db is not None
    db.update_row(
        BUNDLE_REGISTRY_TABLE,
        {'state': state},
        f'{db.quote_identifier("bundle_id")}=%s',
        [bundle_id],
    )


def unregister_bundles(ctx: ImportContext, bundle_ids: Iterable[str]) -> None:
    """Remove bundles from the registry, as deleting them from the schema does.

    Parameters:
        ctx: The import run's context, for the open database.
        bundle_ids: The bundles to remove; one the registry does not hold is ignored.
    """
    db = ctx.db
    assert db is not None
    if not db.table_exists(BUNDLE_REGISTRY_TABLE):
        return
    q = db.quote_identifier
    for bundle_id in bundle_ids:
        db.delete_rows(BUNDLE_REGISTRY_TABLE, f'{q("bundle_id")}=%s', [bundle_id])
