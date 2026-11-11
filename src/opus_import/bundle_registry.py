"""The bundle registry: every bundle registered for import, its id range and its state.

One table, ``import_bundle``, holds a row per bundle registered for import in the target
schema (`opus_import.steps.do_register` writes them). A bundle's row carries:

- its **number**, ``bundle_number``, given in registration order;
- its **id range**: the ``obs_general`` ids its observations take are ``first_id`` and
  the ``id_capacity - 1`` after it, and the ranges ascend in ``bundle_number`` order, so
  ids depend only on the registration order and the labels, never on which process
  imports a bundle or when;
- its **state**: ``pending`` until an import takes it, ``importing`` while it is deleted
  and loaded, and then ``done``, or ``failed`` when it logged an error.

The states are also the work queue several import processes draw from (`claim_bundle`):
each takes the largest ``pending`` bundle no other process holds.

The registry is what keeps a half-finished import from being finished: finalization and
the schema version step both refuse while any bundle in it is not ``done``
(`unfinished_bundles`). An append into a finalized schema that fails part way leaves its
bundles recorded, and the next import into that schema resumes them.
"""

from __future__ import annotations

import datetime
from collections.abc import Collection, Iterable, Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING

from opus_import import import_util

if TYPE_CHECKING:
    from opus_import.context import ImportContext
    from opus_import.import_processes import ImporterLock
    from opus_import.importdb.super import ImportDBSuper

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

#: How many ids a bundle's range holds for each row its labels declare. The margin is
#: room for a re-imported bundle that has grown, and for an index row that yields
#: several observations.
ID_CAPACITY_FACTOR = 100

#: The largest id ``obs_general.id``, an ``INT UNSIGNED``, can hold.
MAX_OBSERVATION_ID = 4_294_967_295

#: The columns `registered_ranges` reads.
_RANGE_COLUMNS = (
    'bundle_number',
    'bundle_id',
    'size_estimate',
    'first_id',
    'id_capacity',
    'state',
    'started_at',
)


class RegistrationError(Exception):
    """A bundle cannot be registered; the message names it and says why."""


class BundleIdRangeError(ValueError):
    """A bundle needs more observation ids than its range holds."""


@dataclass(frozen=True)
class BundleRange:
    """One bundle's row of the registry.

    Attributes:
        bundle_number: Its place in registration order.
        bundle_id: The bundle.
        size_estimate: The rows its primary index labels declared at registration.
        first_id: The ``obs_general`` id of its first observation.
        id_capacity: How many ids, from `first_id`, it may use.
        state: Its state, one of the ``BUNDLE_`` constants.
        started_at: When its latest import began, or None before the first.
    """

    bundle_number: int
    bundle_id: str
    size_estimate: int
    first_id: int
    id_capacity: int
    state: str
    started_at: datetime.datetime | None = None

    @property
    def end(self) -> int:
        """The first id after the range, where the next bundle's range starts."""
        return self.first_id + self.id_capacity


@dataclass
class BundleIds:
    """The observation ids one import of a bundle hands out, from its registered range.

    Attributes:
        range: The bundle's registry row.
        used: How many ids have been handed out.
        rows_done: How many ``obs_general`` rows the import has committed, which each
            chunk's transaction records in the registry
            (`opus_import.import_processes.BundleGuard`).
    """

    range: BundleRange
    used: int = 0
    rows_done: int = 0

    def take(self, count: int) -> int:
        """Hand out the next `count` ids, and return the first.

        Parameters:
            count: How many ids; at least 1.

        Returns:
            The first id of the block; the block's ids follow it.

        Raises:
            BundleIdRangeError: If the block would pass the end of the range. The
                message names the bundle, its capacity and its row count.
        """
        if self.used + count > self.range.id_capacity:
            raise BundleIdRangeError(
                f'Bundle {self.range.bundle_id} needs more than its {self.range.id_capacity} '
                f'observation ids, {ID_CAPACITY_FACTOR} for each of the {self.range.size_estimate} '
                'rows its labels declared when it was registered; a bundle that has grown '
                'this much needs a full import, which registers it afresh'
            )
        first = self.range.first_id + self.used
        self.used += count
        return first


def plan_ranges(start: int, estimates: Sequence[tuple[str, int]]) -> list[dict[str, str | int]]:
    """Lay out the id ranges of bundles registered together, one after another.

    Parameters:
        start: The first id after every range already registered.
        estimates: Each bundle with its size estimate, in registration order.

    Returns:
        One registry row per bundle, in the same order, with ``bundle_id``,
        ``size_estimate``, ``first_id``, ``id_capacity`` and ``state`` ``pending``.

    Raises:
        RegistrationError: If a range would pass `MAX_OBSERVATION_ID`, naming the
            bundle; nothing is registered then.
    """
    rows: list[dict[str, str | int]] = []
    first_id = start
    for bundle_id, size_estimate in estimates:
        capacity = ID_CAPACITY_FACTOR * size_estimate
        if first_id + capacity - 1 > MAX_OBSERVATION_ID:
            raise RegistrationError(
                f'Bundle {bundle_id} cannot be registered: its range of {capacity} ids from '
                f'{first_id} would pass {MAX_OBSERVATION_ID}, the largest obs_general.id; '
                'nothing is registered'
            )
        rows.append(
            {
                'bundle_id': bundle_id,
                'size_estimate': size_estimate,
                'first_id': first_id,
                'id_capacity': capacity,
                'state': BUNDLE_PENDING,
            }
        )
        first_id += capacity
    return rows


def create_registry(ctx: ImportContext) -> None:
    """Create the registry table if the schema does not have it.

    Parameters:
        ctx: The import run's context, for the open database.
    """
    db = ctx.db
    assert db is not None
    schema = import_util.read_schema_for_table(ctx, BUNDLE_REGISTRY_TABLE)
    # import_bundle.json is packaged with opus_import, so the schema is always found.
    assert schema is not None
    db.create_table(BUNDLE_REGISTRY_TABLE, schema)


def registered_ranges(db: ImportDBSuper) -> list[BundleRange]:
    """Return every bundle the registry holds, in registration order.

    Parameters:
        db: The open database.

    Returns:
        The rows ordered by ``bundle_number``; none when the table is absent.
    """
    if not db.table_exists(BUNDLE_REGISTRY_TABLE):
        return []
    order = f'1=1 ORDER BY {db.quote_identifier("bundle_number")}'
    return [_range(row) for row in db.read_rows(BUNDLE_REGISTRY_TABLE, _RANGE_COLUMNS, order)]


def _range(row: Sequence[object]) -> BundleRange:
    """Return a `BundleRange` from a row of `_RANGE_COLUMNS`."""
    number, bundle_id, size_estimate, first_id, capacity, state, started_at = row
    return BundleRange(
        int(str(number)),
        str(bundle_id),
        int(str(size_estimate)),
        int(str(first_id)),
        int(str(capacity)),
        str(state),
        started_at if isinstance(started_at, datetime.datetime) else None,
    )


def registered_bundles(ctx: ImportContext) -> list[tuple[str, str]]:
    """Return every bundle the registry holds, with its state.

    Parameters:
        ctx: The import run's context, for the open database.

    Returns:
        ``(bundle, state)`` pairs in registration order; none when the table is absent.
    """
    assert ctx.db is not None
    return [(row.bundle_id, row.state) for row in registered_ranges(ctx.db)]


def unfinished_bundles(ctx: ImportContext) -> list[tuple[str, str]]:
    """Return the bundles in the registry that are not ``done``, with their states.

    Parameters:
        ctx: The import run's context, for the open database.

    Returns:
        ``(bundle, state)`` pairs in registration order; none when the table is absent
        or every bundle is ``done``.
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


def bundle_range(ctx: ImportContext, bundle_id: str) -> BundleRange | None:
    """Return one bundle's registry row.

    Parameters:
        ctx: The import run's context, for the open database.
        bundle_id: The bundle.

    Returns:
        Its row, or None when the registry does not hold it or is absent.
    """
    db = ctx.db
    assert db is not None
    if not db.table_exists(BUNDLE_REGISTRY_TABLE):
        return None
    rows = db.read_rows(
        BUNDLE_REGISTRY_TABLE, _RANGE_COLUMNS, f'{db.quote_identifier("bundle_id")}=%s', [bundle_id]
    )
    return _range(rows[0]) if rows else None


def bundle_ids(ctx: ImportContext, bundle_id: str) -> BundleIds | None:
    """Return the counter one import of a bundle hands its observation ids out from.

    Parameters:
        ctx: The import run's context, for the open database.
        bundle_id: The bundle.

    Returns:
        A counter starting at the bundle's first id, or None when the registry does not
        hold the bundle.
    """
    found = bundle_range(ctx, bundle_id)
    return None if found is None else BundleIds(found)


def _now() -> datetime.datetime:
    """Return the time in UTC, to the second, as the registry's columns store it."""
    return datetime.datetime.now(datetime.UTC).replace(tzinfo=None, microsecond=0)


def _state_columns(state: str) -> dict[str, object]:
    """Return what a move to a state writes: the state, and the times and count it resets.

    Parameters:
        state: The new state, one of the ``BUNDLE_`` constants.

    Returns:
        The columns and their values.
    """
    if state == BUNDLE_IMPORTING:
        # A plain import names no importer; a queue importer's claim sets its own.
        return {
            'state': state,
            'started_at': _now(),
            'finished_at': None,
            'rows_done': 0,
            'process_id': None,
        }
    if state == BUNDLE_PENDING:
        return {
            'state': state,
            'started_at': None,
            'finished_at': None,
            'rows_done': 0,
            'process_id': None,
        }
    return {'state': state, 'finished_at': _now()}


@dataclass(frozen=True)
class Claim:
    """One process's hold on a bundle it moved to ``importing``.

    Attributes:
        bundle_id: The bundle.
        started_at: The ``started_at`` the move wrote. A bundle returned to ``pending``
            and taken again has another, so the process that held it first can no longer
            finish it (`finish_bundle`).
    """

    bundle_id: str
    started_at: datetime.datetime


def _in_states(db: ImportDBSuper, states: Sequence[str]) -> str:
    """Return the condition ``state IN (...)``, with one placeholder per state."""
    return f'{db.quote_identifier("state")} IN ({", ".join(["%s"] * len(states))})'


#: The states a bundle an invocation names may be taken from: any but ``importing``,
#: which another process holds. A bundle named twice in one invocation is ``done`` or
#: ``failed`` by its second turn.
_STARTABLE = (BUNDLE_PENDING, BUNDLE_DONE, BUNDLE_FAILED)


def start_bundle(ctx: ImportContext, bundle_id: str) -> Claim | None:
    """Move a bundle an invocation names to ``importing``, unless another process holds it.

    Parameters:
        ctx: The import run's context, for the open database.
        bundle_id: The bundle.

    Returns:
        The hold on the bundle, or None when it was ``importing`` already.
    """
    db = ctx.db
    assert db is not None
    columns = _state_columns(BUNDLE_IMPORTING)
    changed = db.conditional_update(
        BUNDLE_REGISTRY_TABLE,
        columns,
        f'{db.quote_identifier("bundle_id")}=%s AND {_in_states(db, _STARTABLE)}',
        [bundle_id, *_STARTABLE],
    )
    if changed == 0:
        return None
    started_at = columns['started_at']
    assert isinstance(started_at, datetime.datetime)
    return Claim(bundle_id, started_at)


def finish_bundle(ctx: ImportContext, claim: Claim, state: str) -> bool:
    """Move a bundle this process holds from ``importing`` to ``done`` or ``failed``.

    The move happens only while the bundle is still ``importing`` under this hold: a
    bundle ``--requeue`` returned to the queue, perhaps taken since by another process,
    is left as it is.

    Parameters:
        ctx: The import run's context, for the open database.
        claim: The hold `start_bundle` or `claim_bundle` gave.
        state: `BUNDLE_DONE` or `BUNDLE_FAILED`.

    Returns:
        Whether the bundle moved; False when this process no longer held it.
    """
    db = ctx.db
    assert db is not None
    q = db.quote_identifier
    changed = db.conditional_update(
        BUNDLE_REGISTRY_TABLE,
        _state_columns(state),
        f'{q("bundle_id")}=%s AND {_in_states(db, [BUNDLE_IMPORTING])} AND {q("started_at")}=%s',
        [claim.bundle_id, BUNDLE_IMPORTING, claim.started_at],
    )
    return changed != 0


def return_to_pending(
    ctx: ImportContext, bundle_ids: Iterable[str], from_states: Sequence[str]
) -> list[str]:
    """Move registered bundles in the given states back to ``pending``.

    Parameters:
        ctx: The import run's context, for the open database.
        bundle_ids: The bundles; one the registry does not hold is ignored.
        from_states: The states a bundle may be moved from. ``importing`` belongs here
            only for ``--requeue``, which states that the process holding it has stopped.

    Returns:
        The bundles moved, in the order given.
    """
    db = ctx.db
    assert db is not None
    moved = []
    for bundle_id in bundle_ids:
        changed = db.conditional_update(
            BUNDLE_REGISTRY_TABLE,
            _state_columns(BUNDLE_PENDING),
            f'{db.quote_identifier("bundle_id")}=%s AND {_in_states(db, from_states)}',
            [bundle_id, *from_states],
        )
        if changed != 0:
            moved.append(bundle_id)
    return moved


def claim_bundle(
    ctx: ImportContext,
    among: Collection[str] | None = None,
    excluding: Collection[str] = (),
    importer: ImporterLock | None = None,
) -> Claim | None:
    """Take the largest ``pending`` bundle no other process holds, and mark it ``importing``.

    The claim is one transaction: a locking read of one row through the registry's key
    on ``(state, size_estimate, bundle_number)``, scanned from its highest entry, that
    passes over rows another process has locked, then the move to ``importing``, naming
    the importer in ``process_id``. An importer's claim commits only while its lock
    connection holds its lock. It is run again if the server reports a lock conflict
    (`ImportDBSuper.retrying`).

    Parameters:
        ctx: The import run's context, for the open database.
        among: The only bundles that may be claimed, or None for any.
        excluding: Bundles never claimed.
        importer: The importer claiming, or None for a process that holds no lock.

    Returns:
        The hold on the bundle claimed, or None when no bundle is ``pending`` (of
        `among`, and not of `excluding`) that another process has not claimed first.

    Raises:
        opus_import.import_processes.LostImporterError: If the importer's lock is lost;
            nothing is claimed then.
    """
    # Imported here: import_processes reads this module's table and states.
    from opus_import import import_processes

    db = ctx.db
    assert db is not None
    q = db.quote_identifier
    where = f'{q("state")} = %s'
    params: list[object] = [BUNDLE_PENDING]
    if among is not None:
        if not among:
            return None
        where += f' AND {q("bundle_id")} IN ({", ".join(["%s"] * len(among))})'
        params += sorted(among)
    if excluding:
        where += f' AND {q("bundle_id")} NOT IN ({", ".join(["%s"] * len(excluding))})'
        params += sorted(excluding)

    def claim() -> Claim | None:
        """Lock the row, move it to ``importing``, and return the hold."""
        number = db.lock_first_row(
            BUNDLE_REGISTRY_TABLE,
            'bundle_number',
            where,
            params,
            ['size_estimate', 'bundle_number'],
        )
        if number is None:
            return None
        columns = _state_columns(BUNDLE_IMPORTING)
        columns['process_id'] = None if importer is None else importer.process_id
        db.update_row(BUNDLE_REGISTRY_TABLE, columns, f'{q("bundle_number")}=%s', [number])
        if importer is not None and not importer.held():
            raise import_processes.LostImporterError(
                import_processes.lost_lock_message(importer, import_processes.WHILE_CLAIMING)
            )
        rows = db.read_rows(
            BUNDLE_REGISTRY_TABLE, ['bundle_id'], f'{q("bundle_number")}=%s', [number]
        )
        started_at = columns['started_at']
        assert isinstance(started_at, datetime.datetime)
        return Claim(str(rows[0][0]), started_at)

    return db.retrying('Claiming a pending bundle', claim)


def finish_claimed_bundle(ctx: ImportContext, bundle_number: int, importer: ImporterLock) -> None:
    """Mark an importer's bundle ``done``, only while it is ``importing`` under the importer.

    One transaction: the move to ``done``, matching the bundle only in that state and
    under that importer, committed only while the importer's lock connection holds its
    lock.

    Parameters:
        ctx: The import run's context, for the open database.
        bundle_number: The bundle's number.
        importer: The importer holding it.

    Raises:
        opus_import.import_processes.LostImporterError: If the registry no longer names
            the importer, or its lock is lost; the bundle is left as it was.
    """
    from opus_import import import_processes

    db = ctx.db
    assert db is not None
    q = db.quote_identifier
    with db.transaction():
        matched = db.update_row(
            BUNDLE_REGISTRY_TABLE,
            _state_columns(BUNDLE_DONE),
            f'{q("bundle_number")}=%s AND {q("state")}=%s AND {q("process_id")}=%s',
            [bundle_number, BUNDLE_IMPORTING, importer.process_id],
        )
        if matched != 1 or not importer.held():
            raise import_processes.LostImporterError(
                import_processes.lost_lock_message(importer, import_processes.WHILE_FINISHING)
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
