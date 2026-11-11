"""Bundle registration: give each bundle its number and id range, and write the shared rows.

Every invocation that imports bundles registers them before the first one starts, and
``opus_import --register-bundles`` registers a whole list ahead of several import
processes. Registration fixes what every process would otherwise race to decide:

- each new bundle's row of the bundle registry (`opus_import.bundle_registry`), numbered
  in the order the bundles are given, which is the import order, with an id range sized
  from the row count its primary index labels declare (`opus_import.primary_index`);
- the ``mult_field`` row of every field the packaged schemas declare, and the rows and
  groups of every pinned field (`opus_import.steps.do_import_mult.register_pinned_fields`).

Registration is serialized by a server-wide named lock, so two registrations never read
the same last range. Under the lock it first creates the registry and mult tables the
schema lacks, since a table's creation commits on its own, and then reads the last range
and writes every new row in one transaction.

A bundle OPUS deliberately skips is never registered, and a bundle OPUS imports whose
labels cannot be sized is refused, with nothing registered.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from opus_import import bundle_registry, import_util, importdb, mult_fields, primary_index
from opus_import.bundle_registry import BUNDLE_REGISTRY_TABLE, RegistrationError
from opus_import.steps import do_import_mult, do_import_tables

if TYPE_CHECKING:
    from collections.abc import Iterable

    from opus_import.context import ImportContext

#: What `opus_import.importdb.lock_name` is given, after the schema, for registration's
#: lock.
REGISTRATION_LOCK = 'register'


def registrable_bundles(ctx: ImportContext, bundle_ids: Iterable[str]) -> list[str]:
    """Drop the bundles OPUS deliberately skips, keeping the rest in order.

    A bundle whose `opus_import.config_bundle_info` entry has no instrument class is one
    the import skips (`opus_import.steps.do_import_tables.opus_imports_bundle`); it is
    logged at debug level and never registered.

    Parameters:
        ctx: The import run's context, for the log.
        bundle_ids: The bundles, in import order.

    Returns:
        The bundles OPUS imports, in the same order.
    """
    kept = []
    for bundle_id in bundle_ids:
        if do_import_tables.opus_imports_bundle(bundle_id):
            kept.append(bundle_id)
        else:
            import_util.log_debug(ctx, f'Ignoring registration of {bundle_id}')
    return kept


def size_estimate(bundle_id: str) -> int:
    """Return the rows a bundle's primary index labels declare, read from the labels alone.

    Parameters:
        bundle_id: A bundle OPUS imports.

    Returns:
        The sum over the bundle's primary index files (`opus_import.primary_index`).

    Raises:
        RegistrationError: If the bundle has no ``BUNDLE_INFO`` entry, no primary index
            file is found, or one's label declares no row count; the message names the
            bundle and the label.
    """
    vol_info = do_import_tables.lookup_vol_info(bundle_id)
    if vol_info is None:
        raise RegistrationError(f'Bundle {bundle_id} cannot be registered: no BUNDLE_INFO entry')
    try:
        found = primary_index.locate(bundle_id, vol_info)
    except primary_index.PrimaryIndexError as e:
        raise RegistrationError(f'Bundle {bundle_id} cannot be registered: {e}') from e
    if not found.files:
        raise RegistrationError(
            f'Bundle {bundle_id} cannot be registered: no primary index label found in '
            + ', '.join(found.searched)
        )
    total = 0
    for label in found.files:
        rows = primary_index.declared_rows(label)
        if rows is None:
            raise RegistrationError(
                f'Bundle {bundle_id} cannot be registered: its primary index label {label} '
                'declares no row count'
            )
        total += rows
    return total


def create_registration_tables(ctx: ImportContext) -> None:
    """Create the registry and the mult tables where the schema lacks them.

    Parameters:
        ctx: The import run's context, for the open database.
    """
    bundle_registry.create_registry(ctx)
    mult_fields.create_mult_tables(ctx)


def register_bundles(
    ctx: ImportContext, bundle_ids: Iterable[str], *, make_pending: bool
) -> list[str]:
    """Register bundles in the order given, under registration's lock, in one transaction.

    A bundle the registry lacks is added as ``pending`` with the next number and an id
    range that starts where the last registered range ends. A bundle it holds keeps its
    number and range; with `make_pending` it is returned to ``pending`` as well, which is
    how an invocation that names bundles to import again marks them. The same
    transaction numbers any mult field ``mult_field`` lacks and writes the pinned fields'
    rows.

    Parameters:
        ctx: The import run's context, for the open database and the log.
        bundle_ids: The bundles, in import order.
        make_pending: Whether a bundle already registered goes back to ``pending``.

    Returns:
        The bundles OPUS imports among those given (`registrable_bundles`), in order.

    Raises:
        RegistrationError: If a new bundle cannot be sized, or a range would pass the
            largest observation id; nothing is registered then.
    """
    db = ctx.db
    assert db is not None
    bundles = registrable_bundles(ctx, bundle_ids)
    with db.named_lock(importdb.lock_name(db.db_schema, REGISTRATION_LOCK)):
        # Before the transaction: creating a table commits on its own.
        create_registration_tables(ctx)
        registered = {row.bundle_id: row for row in bundle_registry.registered_ranges(db)}
        start = max((row.end for row in registered.values()), default=0)
        estimates = [
            (bundle_id, size_estimate(bundle_id))
            for bundle_id in dict.fromkeys(bundles)
            if bundle_id not in registered
        ]
        new_rows = bundle_registry.plan_ranges(start, estimates)
        with db.transaction():
            if new_rows:
                db.insert_rows(BUNDLE_REGISTRY_TABLE, new_rows)
            if make_pending:
                bundle_registry.set_pending(
                    ctx, [bundle_id for bundle_id in bundles if bundle_id in registered]
                )
            do_import_mult.register_pinned_fields(ctx)
    for row in new_rows:
        import_util.log_debug(
            ctx,
            f'Registered {row["bundle_id"]}: {row["size_estimate"]} rows declared, ids '
            f'{row["first_id"]} to {int(row["first_id"]) + int(row["id_capacity"]) - 1}',
        )
    return bundles
