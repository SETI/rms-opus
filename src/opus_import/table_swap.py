"""Rebuild tables beside the live ones and swap them in with one atomic rename.

The auxiliary tables (``param_info``, ``partables``, ``table_names``) and the dictionary
(``contexts`` and ``definitions``) are rebuilt on a schema the web application may be
serving. Each is built as ``<table>__new`` and filled there, while the live table goes on
answering, and then one ``RENAME TABLE`` moves every live table aside to ``<table>__old``
and every new one into its place. MySQL applies the whole statement atomically, so a
reader finds each table either as it was or as it now is, never missing and never partly
filled. The ``__old`` tables are dropped afterwards.

Each ``__new`` table is analyzed after it is filled and before it is swapped in. The
server's persistent statistics for a table created empty say it has no rows, a rename
carries them across, and nothing recomputes them soon after a bulk fill, so without
this a rebuilt table goes live with statistics that mislead the optimizer.

A set swapped together is named parents first. A foreign key from one table of the set
to another is pointed at the other's ``__new`` table while the set is built, so after the
rename it references the live table it should; ``definitions`` and ``contexts`` are the
set that needs this.

A run that stops part way leaves ``__new`` or ``__old`` tables behind, and the next
rebuild of the same tables drops them before it starts.

While an incremental update writes a pending generation (`opus_import.generations`), the
auxiliary tables are built from it into their ``__new`` tables and left there, since the
served generation's rows still need the live ones. The switch swaps them in and keeps
the tables they replace as ``<table>__prev`` (`swap_in_keeping_previous`), so a revert can
swap those back (`swap_back_previous`); the purge drops them.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import TYPE_CHECKING, Any

from opus_import import import_util
from opus_import.import_fault import InjectedImportFaultError, import_fault_argument
from opus_import.importdb.super import ImportDBError

if TYPE_CHECKING:
    from opus_import.context import ImportContext

#: What a table is built as before it is swapped in.
SWAP_NEW_SUFFIX = '__new'

#: What a live table is renamed to as the new one takes its place, until it is dropped.
SWAP_OLD_SUFFIX = '__old'

#: What a live table is renamed to as a generation's table is switched in, until the
#: purge drops it.
SWAP_PREV_SUFFIX = '__prev'

#: How long one attempt at the rename waits for a reader's transaction to finish.
SWAP_LOCK_WAIT_TIMEOUT_S = 5

#: How many attempts the rename makes before waiting is a failure.
SWAP_RENAME_ATTEMPTS = 12

#: The `opus_import.import_fault` site between the fill and the rename. Its argument is a
#: table; a swap that includes that table raises there.
SWAP_FAULT_SITE = 'swap_in'


def swap_new_name(table: str) -> str:
    """Return the name a table is built under before it is swapped in.

    Parameters:
        table: The live table's raw name.

    Returns:
        The name with `SWAP_NEW_SUFFIX`.
    """
    return table + SWAP_NEW_SUFFIX


def swap_old_name(table: str) -> str:
    """Return the name a live table is moved to as its replacement is swapped in.

    Parameters:
        table: The live table's raw name.

    Returns:
        The name with `SWAP_OLD_SUFFIX`.
    """
    return table + SWAP_OLD_SUFFIX


def swap_prev_name(table: str) -> str:
    """Return the name a live table keeps after a generation's table is switched in.

    Parameters:
        table: The live table's raw name.

    Returns:
        The name with `SWAP_PREV_SUFFIX`.
    """
    return table + SWAP_PREV_SUFFIX


def swap_in_keeping_previous(ctx: ImportContext, tables: Sequence[str]) -> bool:
    """Swap a set's ``__new`` tables in with one rename, keeping the live ones as ``__prev``.

    Any ``__prev`` table an earlier switch left is dropped first. A set with no ``__new``
    table has already been swapped in, and is left as it is.

    Parameters:
        ctx: The import run's context, for the open database and the logger.
        tables: The set, parents first.

    Returns:
        True if it swapped the set in, False if there was nothing to swap.

    Raises:
        opus_import.importdb.super.ImportDBError: If only some of the ``__new`` tables
            exist, which no rebuild leaves.
    """
    return _rename_set(ctx, tables, swap_new_name, swap_prev_name)


def swap_back_previous(ctx: ImportContext, tables: Sequence[str]) -> bool:
    """Swap a set's ``__prev`` tables back in, keeping the live ones as ``__new``.

    A set with no ``__prev`` table has already been swapped back, and is left as it is.

    Parameters:
        ctx: The import run's context, for the open database and the logger.
        tables: The set, parents first.

    Returns:
        True if it swapped the set back, False if there was nothing to swap.

    Raises:
        opus_import.importdb.super.ImportDBError: If only some of the ``__prev`` tables
            exist.
    """
    return _rename_set(ctx, tables, swap_prev_name, swap_new_name)


def _rename_set(
    ctx: ImportContext,
    tables: Sequence[str],
    incoming: Callable[[str], str],
    outgoing: Callable[[str], str],
) -> bool:
    """Move each live table to its outgoing name and its incoming table into its place.

    Parameters:
        ctx: The import run's context, for the open database and the logger.
        tables: The set, parents first.
        incoming: The name of the table that takes each live table's place.
        outgoing: The name each live table is moved to; a table of that name is dropped
            first.

    Returns:
        True if it renamed, False when no incoming table exists.

    Raises:
        opus_import.importdb.super.ImportDBError: If only some incoming tables exist.
    """
    db = ctx.db
    assert db is not None
    present = [table for table in tables if db.table_exists(incoming(table))]
    if not present:
        return False
    if len(present) != len(tables):
        raise ImportDBError(
            f'Only some of {", ".join(incoming(table) for table in tables)} exist, so none '
            'is swapped in'
        )
    for table in reversed(tables):
        db.drop_table(outgoing(table))
    renames: list[tuple[str, str]] = []
    for table in tables:
        if db.table_exists(table):
            renames.append((table, outgoing(table)))
        renames.append((incoming(table), table))
    import_util.log_info(ctx, f'Swapping in {", ".join(incoming(table) for table in tables)}')
    db.rename_tables_atomically(
        renames, lock_wait_timeout_s=SWAP_LOCK_WAIT_TIMEOUT_S, attempts=SWAP_RENAME_ATTEMPTS
    )
    return True


def drop_swap_leftovers(ctx: ImportContext, tables: Sequence[str]) -> None:
    """Drop every ``__new`` and ``__old`` table of a set, children before parents.

    Parameters:
        ctx: The import run's context, for the open database.
        tables: The set, parents first.
    """
    db = ctx.db
    assert db is not None
    for name_for in (swap_new_name, swap_old_name):
        for table in reversed(tables):
            db.drop_table(name_for(table))


def _point_foreign_keys_at_new_tables(
    schema: Sequence[dict[str, Any]], tables: Sequence[str]
) -> list[dict[str, Any]]:
    """Return a table schema whose foreign keys into the set reference the ``__new`` tables.

    Parameters:
        schema: The table's packaged schema, which is not changed.
        tables: The set being built together.

    Returns:
        A copy of the schema with each ``field_key_foreign`` that names a table of the set
        naming that table's ``__new`` name instead.
    """
    pointed: list[dict[str, Any]] = []
    for entry in schema:
        foreign = entry.get('field_key_foreign')
        if foreign is not None and foreign[0] in tables:
            entry = {**entry, 'field_key_foreign': [swap_new_name(foreign[0]), *foreign[1:]]}
        pointed.append(entry)
    return pointed


def create_swap_tables(ctx: ImportContext, tables: Sequence[str]) -> None:
    """Create each table of a set, empty, under its ``__new`` name, parents first.

    Parameters:
        ctx: The import run's context, for the open database.
        tables: The set, parents first.
    """
    db = ctx.db
    assert db is not None
    for table in tables:
        schema = import_util.read_schema_for_table(ctx, table)
        # Every table swapped in has a schema packaged with opus_import.
        assert schema is not None, table
        db.create_table(
            swap_new_name(table),
            _point_foreign_keys_at_new_tables(schema, tables),
            ignore_if_exists=False,
        )


def swap_in_new_tables(ctx: ImportContext, tables: Sequence[str]) -> None:
    """Swap a filled set of ``__new`` tables in with one rename, then drop the old tables.

    Raises `InjectedImportFaultError` first when `SWAP_FAULT_SITE` names a table of the set.

    Parameters:
        ctx: The import run's context, for the open database and the logger.
        tables: The set, parents first.

    Raises:
        InjectedImportFaultError: If a test named a table of the set at `SWAP_FAULT_SITE`.
    """
    db = ctx.db
    assert db is not None
    faulted = import_fault_argument(SWAP_FAULT_SITE)
    if faulted is not None and faulted in tables:
        raise InjectedImportFaultError(f'{SWAP_FAULT_SITE}:{faulted}')

    renames: list[tuple[str, str]] = []
    for table in tables:
        if db.table_exists(table):
            renames.append((table, swap_old_name(table)))
        renames.append((swap_new_name(table), table))
    import_util.log_info(ctx, f'Swapping in {", ".join(tables)}')
    db.rename_tables_atomically(
        renames,
        lock_wait_timeout_s=SWAP_LOCK_WAIT_TIMEOUT_S,
        attempts=SWAP_RENAME_ATTEMPTS,
    )
    for table in reversed(tables):
        db.drop_table(swap_old_name(table))


def rebuild_tables_by_swap(
    ctx: ImportContext, tables: Sequence[str], fill: Callable[[], bool], *, swap: bool = True
) -> bool:
    """Rebuild a set of tables beside the live ones and swap them in together.

    Drops any leftovers of an earlier rebuild, creates the ``__new`` tables, fills them,
    analyzes them, and swaps them in. A fill that fails drops the ``__new`` tables again
    and leaves the live ones as they were.

    Parameters:
        ctx: The import run's context, for the open database and the logger.
        tables: The set, parents first.
        fill: Writes every row into the ``__new`` tables (`swap_new_name`), returning
            False, having logged why, when the rows cannot be built.
        swap: False to leave the filled ``__new`` tables for a generation's switch to
            swap in (`swap_in_keeping_previous`).

    Returns:
        True if the set was built (and swapped in, with `swap`), False if the fill
        failed.
    """
    drop_swap_leftovers(ctx, tables)
    create_swap_tables(ctx, tables)
    if not fill():
        drop_swap_leftovers(ctx, tables)
        return False
    db = ctx.db
    assert db is not None
    for table in tables:
        db.analyze_table(swap_new_name(table))
    if swap:
        swap_in_new_tables(ctx, tables)
    else:
        import_util.log_info(ctx, f'Built {", ".join(map(swap_new_name, tables))} for the switch')
    return True
