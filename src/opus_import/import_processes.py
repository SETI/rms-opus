"""The importers drawing bundles from the queue: their table, their locks and their status.

An **importer** is one ``opus_import --join`` process. Each records itself as a row of
``import_process``, beside the bundle registry, and names that row in the
``import_bundle.process_id`` of the bundle it holds. Whether an importer is alive is
never guessed from a timestamp: it holds a server-wide named lock, `importer_lock_name`,
on a connection of its own for its whole life, the **lock connection**, and the server
frees the lock when that connection closes, however the process ends. Any computer can
ask the server whether the lock is held (`ImportDBSuper.named_lock_holder`).

An importer commits a chunk of rows only while it holds its lock and the registry still
names it as importing the chunk's bundle (`BundleGuard`), so once its lock is free it can
commit nothing more, and its bundle can be returned to the queue
(`opus_import.steps.do_recover`).

A plain ``opus_import`` takes no lock and has no row: its bundles keep ``process_id``
NULL.
"""

from __future__ import annotations

import datetime
import json
import os
import socket
import time
from dataclasses import dataclass
from typing import TYPE_CHECKING

from opus_import import bundle_registry, importdb
from opus_import.import_fault import import_fault_argument
from opus_import.import_util import TABLE_SCHEMA_DIR

if TYPE_CHECKING:
    from opus_import.bundle_registry import BundleIds
    from opus_import.importdb.super import ImportDBSuper

#: The table recording every importer.
IMPORT_PROCESS_TABLE = 'import_process'

#: An importer that has started and not exited.
PROCESS_RUNNING = 'running'

#: An importer that exited, releasing its lock.
PROCESS_EXITED = 'exited'

#: An importer whose lock was found free while its row said it was running.
PROCESS_LOST = 'lost'

#: What `opus_import.importdb.lock_name` is given, after the schema, for an importer's
#: lock; the importer's ``process_id`` follows.
IMPORTER_LOCK = 'importer'

#: The lock connection's ``wait_timeout``: a year, the largest the server accepts on
#: Linux, so the server never closes the idle connection while its importer is alive.
LOCK_CONNECTION_IDLE_SECONDS = 31_536_000

#: The `opus_import.import_fault` site between an importer's ``import_process`` insert
#: and its ``GET_LOCK``. Its argument is the seconds the importer sleeps there.
HOLD_BEFORE_LOCK_FAULT_SITE = 'hold_before_lock'

#: The `opus_import.import_fault` site after a bundle's first chunk commits. Its
#: argument is the seconds the importer sleeps there.
HOLD_AFTER_CHUNK_FAULT_SITE = 'hold_after_chunk'


class LostImporterError(Exception):
    """The importer lost its lock or its bundle, so it may commit nothing more."""


def importer_lock_name(schema: str, process_id: int) -> str:
    """Return the name of the lock an importer holds for its life.

    Parameters:
        schema: The schema the importer writes.
        process_id: The importer's ``import_process`` row.

    Returns:
        The lock's name.
    """
    return importdb.lock_name(schema, IMPORTER_LOCK, process_id)


def now() -> datetime.datetime:
    """Return the time in UTC, to the second, as the tables' ``DATETIME`` columns hold it."""
    return datetime.datetime.now(datetime.UTC).replace(tzinfo=None, microsecond=0)


def create_process_table(db: ImportDBSuper) -> None:
    """Create ``import_process`` if the schema does not have it.

    Parameters:
        db: The open database.
    """
    schema = json.loads((TABLE_SCHEMA_DIR / f'{IMPORT_PROCESS_TABLE}.json').read_text('utf-8'))
    db.create_table(IMPORT_PROCESS_TABLE, schema)


@dataclass
class ImporterLock:
    """One importer's row and the lock it holds on its own connection.

    Attributes:
        db: The lock connection, opened for this alone and never reconnected.
        process_id: The importer's ``import_process`` row.
        name: The lock's name.
    """

    db: ImportDBSuper
    process_id: int
    name: str

    def held(self) -> bool:
        """Return whether the lock connection still holds the lock.

        Returns:
            True if it does; False if the lock is free or another connection holds it,
            or the query failed, as it does once the connection is gone.
        """
        try:
            return self.db.holds_named_lock(self.name)
        except importdb.ImportDBError:
            return False

    def exit(self) -> None:
        """Record the importer as exited, if it still holds its lock, and free the lock.

        The row is written before the lock connection closes, so no reader sees a free
        lock with the row still ``running`` and takes the importer for lost.
        """
        try:
            if self.held():
                with self.db.transaction():
                    self.db.update_row(
                        IMPORT_PROCESS_TABLE,
                        {'state': PROCESS_EXITED},
                        f'{self.db.quote_identifier("process_id")}=%s AND '
                        f'{self.db.quote_identifier("state")}=%s',
                        [self.process_id, PROCESS_RUNNING],
                    )
        finally:
            self.db.close()


def start_importer(lock_db: ImportDBSuper, log_path: str) -> ImporterLock:
    """Record an importer in ``import_process`` and take its lock, on its lock connection.

    In this order: the connection's idle timeout is raised to
    `LOCK_CONNECTION_IDLE_SECONDS`; the ``running`` row is inserted; its
    ``process_id`` is read back; the lock is taken without waiting; and only then is the
    row committed. A reader therefore never sees a committed ``running`` row whose lock
    is not yet held, and a process that dies before the commit leaves neither.

    Parameters:
        lock_db: A connection opened for the lock alone, on which ``import_process``
            exists.
        log_path: The importer's information log.

    Returns:
        The importer's row and lock.

    Raises:
        opus_import.importdb.super.ImportDBError: If the server refuses a statement or
            does not grant the lock; nothing is committed then.
    """
    lock_db.set_idle_timeout(LOCK_CONNECTION_IDLE_SECONDS)
    started = now()
    with lock_db.transaction():
        lock_db.insert_row(
            IMPORT_PROCESS_TABLE,
            {
                'host': socket.gethostname(),
                'pid': os.getpid(),
                'log_path': log_path,
                'started_at': started,
                'progress_at': started,
                'state': PROCESS_RUNNING,
            },
        )
        process_id = lock_db.last_insert_id()
        hold = import_fault_argument(HOLD_BEFORE_LOCK_FAULT_SITE)
        if hold is not None:
            time.sleep(float(hold))
        name = importer_lock_name(lock_db.db_schema, process_id)
        if not lock_db.try_named_lock(name):
            raise importdb.ImportDBError(f'The server did not grant the importer lock "{name}"')
    return ImporterLock(lock_db, process_id, name)


#: What `lost_lock_message` says the importer was doing, for each check that can fail.
WHILE_COMMITTING_A_CHUNK = 'committing a chunk'
WHILE_CLAIMING = 'claiming a bundle'
WHILE_FINISHING = 'marking its bundle done'
WHILE_DELETING = 'deleting its bundle'


def lost_lock_message(importer: ImporterLock, doing: str) -> str:
    """Return the fatal message of an importer that lost its lock or its bundle.

    Parameters:
        importer: The importer.
        doing: What it was doing when a check failed, one of the ``WHILE_`` constants.

    Returns:
        The message, naming the lock.
    """
    return (
        f'This importer (import_process {importer.process_id}) lost its lock "{importer.name}" '
        f'or its bundle while {doing}, so it commits nothing more'
    )


@dataclass
class BundleGuard:
    """What each chunk of one bundle's rows runs in its transaction (a `LoadGuard`).

    The transaction's first statement advances the bundle's ``rows_done`` in the
    registry, matching the bundle only while it is ``importing`` under this importer, so
    the chunk holds the bundle's registry row until it ends; the importer's
    ``progress_at`` advances in the same transaction. Before the commit, the lock
    connection is asked whether it still holds the lock. A chunk commits only if both
    hold; otherwise `LostImporterError` rolls it back.

    For a plain ``opus_import`` (no importer) only an ``obs_general`` chunk carries the
    ``rows_done`` update, matching the bundle with ``process_id`` NULL, and nothing is
    checked.

    Attributes:
        ids: The bundle's id counter, which holds its committed ``rows_done``.
        importer: The importer, or None for a plain ``opus_import``.
        chunks: How many chunks have committed.
    """

    ids: BundleIds
    importer: ImporterLock | None
    chunks: int = 0
    _pending_rows: int = 0

    def begin(self, db: ImportDBSuper, table_name: str, row_count: int) -> None:
        """Run the chunk's registry and progress updates, first in its transaction.

        Parameters:
            db: The import connection, inside the chunk's transaction.
            table_name: The table the chunk goes into.
            row_count: The chunk's rows.

        Raises:
            LostImporterError: If the registry no longer names this importer as
                importing the bundle.
        """
        q = db.quote_identifier
        observations = row_count if table_name == 'obs_general' else 0
        self._pending_rows = self.ids.rows_done + observations
        number = self.ids.range.bundle_number
        if self.importer is None:
            if observations:
                db.update_row(
                    bundle_registry.BUNDLE_REGISTRY_TABLE,
                    {'rows_done': self._pending_rows},
                    f'{q("bundle_number")}=%s AND {q("process_id")} IS NULL',
                    [number],
                )
            return
        matched = db.update_row(
            bundle_registry.BUNDLE_REGISTRY_TABLE,
            {'rows_done': self._pending_rows},
            f'{q("bundle_number")}=%s AND {q("state")}=%s AND {q("process_id")}=%s',
            [number, bundle_registry.BUNDLE_IMPORTING, self.importer.process_id],
        )
        if matched != 1:
            raise LostImporterError(lost_lock_message(self.importer, WHILE_COMMITTING_A_CHUNK))
        db.update_row(
            IMPORT_PROCESS_TABLE,
            {'progress_at': now()},
            f'{q("process_id")}=%s',
            [self.importer.process_id],
        )

    def confirm(self, db: ImportDBSuper) -> None:
        """Check, last before the commit, that the lock connection holds the lock.

        Parameters:
            db: The import connection; the check runs on the lock connection.

        Raises:
            LostImporterError: If it does not, or the lock connection is gone.
        """
        if self.importer is not None and not self.importer.held():
            raise LostImporterError(lost_lock_message(self.importer, WHILE_COMMITTING_A_CHUNK))

    def committed(self) -> None:
        """Keep the committed ``rows_done``, and hold after the first chunk if a test asks."""
        self.ids.rows_done = self._pending_rows
        self.chunks += 1
        if self.chunks == 1:
            hold = import_fault_argument(HOLD_AFTER_CHUNK_FAULT_SITE)
            if hold is not None:
                time.sleep(float(hold))


@dataclass(frozen=True)
class ProcessStatus:
    """One importer's row, and whether its lock is held.

    Attributes:
        process_id: The row.
        host: Its computer.
        pid: Its process id there.
        log_path: Its information log, on its computer.
        started_at: When it started, in UTC.
        progress_at: When it last committed a chunk, in UTC.
        state: Its row's state.
        alive: Whether its lock is held.
    """

    process_id: int
    host: str
    pid: int
    log_path: str
    started_at: datetime.datetime
    progress_at: datetime.datetime
    state: str
    alive: bool


@dataclass(frozen=True)
class BundleStatus:
    """One bundle's registry row, as the tracking reads it.

    Attributes:
        bundle_number: Its number.
        bundle_id: The bundle.
        state: Its state.
        size_estimate: The rows its labels declared.
        rows_done: The ``obs_general`` rows its latest import committed.
        process_id: The importer holding it or that last failed it, or None.
        started_at: When its latest import began, or None.
        finished_at: When its latest import ended, or None.
    """

    bundle_number: int
    bundle_id: str
    state: str
    size_estimate: int
    rows_done: int
    process_id: int | None
    started_at: datetime.datetime | None
    finished_at: datetime.datetime | None


@dataclass(frozen=True)
class Snapshot:
    """The registry and the importers, read at one moment.

    Attributes:
        bundles: Every registered bundle, in registration order.
        processes: Every importer, in ``process_id`` order.
    """

    bundles: tuple[BundleStatus, ...]
    processes: tuple[ProcessStatus, ...]

    def count(self, state: str) -> int:
        """Return how many bundles are in a state.

        Parameters:
            state: One of the ``bundle_registry.BUNDLE_`` constants.
        """
        return sum(1 for bundle in self.bundles if bundle.state == state)

    def process(self, process_id: int | None) -> ProcessStatus | None:
        """Return an importer's row, or None.

        Parameters:
            process_id: The row's id, or None.
        """
        for process in self.processes:
            if process.process_id == process_id:
                return process
        return None


_BUNDLE_COLUMNS = (
    'bundle_number',
    'bundle_id',
    'state',
    'size_estimate',
    'rows_done',
    'process_id',
    'started_at',
    'finished_at',
)
_PROCESS_COLUMNS = (
    'process_id',
    'host',
    'pid',
    'log_path',
    'started_at',
    'progress_at',
    'state',
)


def read_snapshot(db: ImportDBSuper) -> Snapshot:
    """Read every registry row and every importer's row, and ask whether each running
    importer's lock is held.

    Parameters:
        db: The open database. Absent tables read as empty.

    Returns:
        The snapshot.
    """
    q = db.quote_identifier
    bundles: list[BundleStatus] = []
    if db.table_exists(bundle_registry.BUNDLE_REGISTRY_TABLE):
        for row in db.read_rows(
            bundle_registry.BUNDLE_REGISTRY_TABLE,
            _BUNDLE_COLUMNS,
            f'1=1 ORDER BY {q("bundle_number")}',
        ):
            number, bundle_id, state, size, done, process_id, started, finished = row
            bundles.append(
                BundleStatus(
                    int(number),
                    str(bundle_id),
                    str(state),
                    int(size),
                    int(done),
                    None if process_id is None else int(process_id),
                    started,
                    finished,
                )
            )
    processes: list[ProcessStatus] = []
    if db.table_exists(IMPORT_PROCESS_TABLE):
        for row in db.read_rows(
            IMPORT_PROCESS_TABLE, _PROCESS_COLUMNS, f'1=1 ORDER BY {q("process_id")}'
        ):
            process_id, host, pid, log_path, started, progress, state = row
            alive = (
                str(state) == PROCESS_RUNNING
                and db.named_lock_holder(importer_lock_name(db.db_schema, int(process_id)))
                is not None
            )
            processes.append(
                ProcessStatus(
                    int(process_id),
                    str(host),
                    int(pid),
                    str(log_path),
                    started,
                    progress,
                    str(state),
                    alive,
                )
            )
    return Snapshot(tuple(bundles), tuple(processes))
