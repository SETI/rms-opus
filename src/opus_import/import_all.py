"""Import every bundle set OPUS holds, dividing the work among several importers.

A full-holdings import is not one command. ``opus_import_all`` runs it from the package,
so that it is available wherever the distribution is installed::

    OPUS_CONFIG=/opt/opus/opus.toml opus_import_all --override-db-schema opus3_new

With no step named it is the **coordinator**:

1. **Prepare.** It registers every bundle the bundle sets expand to (or the ones
   ``--sets`` names), in import order, in the target schema's bundle registry, which
   fixes each bundle's number and the range its observation ids come from. With
   ``--scorched-earth`` it first erases every OPUS table in the schema. Registration
   leaves registered bundles alone, so a rerun after an interruption resumes.
2. **Divide.** ``--workers`` is the total of worker processes on this computer
   (``[import] workers`` when not given), refused above the ceiling every import
   obeys. It starts ``--importers`` importers (``[import] importers`` when not given),
   capped at that total, and divides the total among them as evenly as whole numbers
   allow (`divide`). Each importer is an ``opus_import --join`` process drawing bundles
   from the registry's queue, the largest pending first.
3. **Track.** Every few seconds it reads the registry and the importers' table: on a
   terminal it redraws a table of the running importers under a totals line; otherwise
   it logs a line per finished bundle and the totals every
   ``[import] status_interval_minutes``.
4. **Recover.** An importer whose lock is free while its row says it is running is
   lost; its bundle's rows are deleted and the bundle returns to the queue, or fails at
   its second loss (`opus_import.steps.do_recover`). A lost importer of its own is
   replaced while bundles its importers may claim are pending.
5. **Finish.** When no bundle is pending or importing and no importer anywhere is
   alive, it runs the closing sequence (``--finish``), unless a bundle failed, when it
   names each with its importer's log and leaves the schema unfinalized.

The first interrupt (Ctrl-C) drains: the importers claim nothing new and finish their
bundles, and the coordinator exits without finalizing. A second aborts: each importer
returns its bundle to the queue, and later ones do not interrupt that. Either way a rerun
resumes.

Each step also runs alone when named: ``--prepare``; ``--join``, which starts and tracks
``--importers`` importers on this computer (one by default) and never prepares or
finishes, so another computer naming the same database server, schema and holdings can
join a running import; ``--finish``; ``--requeue``; and ``--status``, which prints the
coordinator's table from any computer.

**Erasing is asked for, never the default.** ``--scorched-earth`` asks for confirmation
first, naming the schema; ``--yes`` answers for a caller that has already asked -- which is
what the Ring-Moon Systems Node's ``scripts/import/import_all.sh`` wrapper does before it
puts the run under ``nohup`` -- and is refused without ``--scorched-earth``.
"""

from __future__ import annotations

import argparse
import contextlib
import datetime
import os
import signal
import socket
import subprocess  # nosec B404
import sys
import time
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from opus_config import MAX_WORKERS

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence
    from types import FrameType

    import pdslogger

    from opus_config import OpusConfig
    from opus_config.config import ImportConfig
    from opus_import.context import ImportContext
    from opus_import.import_processes import Snapshot
    from opus_import.importdb.super import ImportDBSuper

#: The bundle sets, in the order they are imported -- GALILEO and NEWHORIZONS, then the rest
#: roughly in the reverse of how long each takes. Registration numbers the bundles in this
#: order, and a bundle registered later keeps its copy of an OPUS id two bundles share.
BUNDLE_SETS = (
    'GALILEO',
    'NEWHORIZONS',
    'EBROCC',
    'uranus_occs_earthbased',
    'cassini_uvis_solarocc_beckerjarmak2023',
    'COUVIS_8xxx',
    'COVIMS_8xxx',
    'CORSS_8xxx',
    'VOYAGER',
    'HST',
    'COCIRS',
    'COISS',
    'COUVIS_0xxx',
    'COVIMS_0xxx',
)

#: What finishes the database once every bundle is in it. They are the finalization
#: group -- the secondary keys, one copy of each OPUS id, and the auxiliary tables that
#: describe the search form -- the dictionary the tooltips come from, the validation that
#: reads the result back, and the schema version row that lets the web application serve
#: the result, which comes last. None of them names a bundle.
FINALIZATION_OPTIONS = (
    '--finalize',
    '--import-dictionary',
    '--validate',
    '--write-schema-version',
)

#: The erase `--scorched-earth` asks for, run as its own invocation before registration.
#: The run has asked its own confirmation by then.
DROP_OPTIONS = ('--scorched-earth', '--yes')

#: What has to be typed to let the erase proceed. Nothing else is accepted, including
#: ``yes``: the tables it is about to drop are not recoverable.
CONFIRMATION = 'YES'

#: The ``--importers`` value that takes the count from ``[import] importers``.
AUTO_IMPORTERS = 'auto'

#: The seconds between two readings of the registry while importers run.
TRACK_SECONDS = 5.0

#: How many of the latest events a terminal's table shows beneath it.
EVENTS_SHOWN = 8

#: How long every reading of the database may fail in a row before the coordinator stops.
DATABASE_OUTAGE_SECONDS = 300.0

#: How many importers in a row may exit with failure before claiming a bundle before the
#: coordinator starts no more: an importer that cannot start would otherwise be started
#: again for every pending bundle.
FAILED_STARTS_ALLOWED = 3

#: The registry states ``--finish`` refuses to run past, and the ones of those that
#: ``--requeue`` returns to the queue.
_UNFINISHED_STATES = ('pending', 'importing', 'failed')
_REQUEUEABLE_STATES = ('importing', 'failed')

#: What redraws a terminal from its top-left corner.
_CLEAR_SCREEN = '\x1b[H\x1b[2J'


def divide(total: int, importers: int) -> list[int]:
    """Divide a total of workers among importers as evenly as whole numbers allow.

    Parameters:
        total: The workers, at least 1.
        importers: The importers, from 1 to `total`.

    Returns:
        Each importer's workers, in start order. The first ``total mod importers`` take
        one more than the rest, and together they make `total`.
    """
    share, extra = divmod(total, importers)
    return [share + 1 if index < extra else share for index in range(importers)]


@dataclass(frozen=True)
class Division:
    """How this computer's workers are divided among its importers, and why.

    Attributes:
        cores: The cores detected.
        cpu_fraction: The share of them the ceiling allows.
        ceiling: The most workers a request may ask for.
        workers: The total of workers, N.
        importers: The importers, M, at most N.
        per_importer: Each importer's workers, in start order.
    """

    cores: int
    cpu_fraction: float
    ceiling: int
    workers: int
    importers: int
    per_importer: tuple[int, ...]

    def describe(self) -> str:
        """Return the line the coordinator writes first.

        Returns:
            The cores, the fraction, the ceiling, N, M, and each importer's workers.
        """
        return (
            f'Parallelism: {self.cores} cores detected, cpu_fraction {self.cpu_fraction:g}, '
            f'ceiling {self.ceiling}; workers {self.workers} in all, importers '
            f'{self.importers}, workers per importer '
            f'{", ".join(str(count) for count in self.per_importer)}'
        )


def resolve_division(
    config: ImportConfig,
    workers: int | str | None,
    importers: int | str,
    *,
    detected: int | None = None,
) -> Division:
    """Resolve the total of workers against the ceiling, and divide it among importers.

    Parameters:
        config: The ``[import]`` table.
        workers: ``--workers``: a number, `opus_config.MAX_WORKERS` for the ceiling, or
            None for ``[import] workers``.
        importers: ``--importers``: a number, or `AUTO_IMPORTERS` for
            ``[import] importers``.
        detected: The cores to take as detected, or None to count them.

    Returns:
        The division.

    Raises:
        opus_config.config.ConfigError: If the total is above the ceiling, naming it.
    """
    # Imported here, so that --help needs no configuration package state.
    from opus_config import resolve_parallelism

    parallelism = resolve_parallelism(config, workers, detected=detected)
    requested = config.importers if importers == AUTO_IMPORTERS else int(importers)
    count = min(requested, parallelism.workers)
    return Division(
        cores=parallelism.cores,
        cpu_fraction=parallelism.cpu_fraction,
        ceiling=parallelism.ceiling,
        workers=parallelism.workers,
        importers=count,
        per_importer=tuple(divide(parallelism.workers, count)),
    )


def _override(schema: str | None) -> list[str]:
    """Return the schema override every invocation carries, or nothing."""
    return ['--override-db-schema', schema] if schema is not None else []


def prepare_steps(
    schema: str | None, erase: bool, extra_options: Sequence[str], sets: str | None = None
) -> list[list[str]]:
    """Return the ``opus_import`` command lines ``--prepare`` runs, in order.

    Parameters:
        schema: The database schema to import into, or None for the one the
            configuration file names. A schema that does not exist is created by the
            first step that writes to it.
        erase: Whether to erase every OPUS table in the schema first.
        extra_options: Options added to every invocation, from this command's own
            command line.
        sets: Comma-separated bundle descriptors to register in place of `BUNDLE_SETS`,
            or None.

    Returns:
        The erase, when asked for, then one registration of every bundle set, in import
        order.
    """
    override = _override(schema)
    steps = [[*DROP_OPTIONS, *override, *extra_options]] if erase else []
    descriptors = list(BUNDLE_SETS) if sets is None else [sets]
    steps.append(['--register-bundles', *override, *extra_options, *descriptors])
    return steps


def importer_step(
    schema: str | None, workers: int, extra_options: Sequence[str], sets: str | None = None
) -> list[str]:
    """Return one importer's ``opus_import`` command line.

    Parameters:
        schema: The database schema, or None for the configuration's.
        workers: The importer's workers.
        extra_options: Options added to the invocation.
        sets: Comma-separated bundle descriptors the importer may claim, or None for any.

    Returns:
        The command line after ``python -m opus_import``.
    """
    step = ['--join', *_override(schema), '--workers', str(workers), *extra_options]
    if sets is not None:
        step.append(sets)
    return step


def finish_steps(schema: str | None) -> list[list[str]]:
    """Return the ``opus_import`` command lines ``--finish`` runs, in order.

    Parameters:
        schema: The database schema, or None for the configuration's.

    Returns:
        One invocation per `FINALIZATION_OPTIONS` entry. They take neither a bundle nor
        the extra options, because they import nothing.
    """
    return [[option, *_override(schema)] for option in FINALIZATION_OPTIONS]


def requeue_steps(schema: str | None, bundles: Sequence[str]) -> list[list[str]]:
    """Return the ``opus_import`` command line ``--requeue`` runs.

    Parameters:
        schema: The database schema, or None for the configuration's.
        bundles: The bundle ids to return to the queue.

    Returns:
        One command line.
    """
    return [['--requeue', *_override(schema), *bundles]]


def run_step(arguments: list[str]) -> int:
    """Run one ``opus_import`` invocation, in a process of its own.

    Parameters:
        arguments: The command line after ``python -m opus_import``.

    Returns:
        The invocation's exit status. A non-zero status stops the run; a zero one does
        not mean the step was clean, because several steps report failure through
        ``ERRORS.log`` and still exit zero.
    """
    command = [sys.executable, '-m', 'opus_import', *arguments]
    print(f'>>> {" ".join(command)}', flush=True)
    # The command is this module's own constants and the options the caller typed,
    # run without a shell, so there is nothing here for a shell to interpret.
    return subprocess.run(command, check=False).returncode  # nosec B603


def start_importer(arguments: list[str]) -> subprocess.Popen[bytes]:
    """Start one importer, in a process group of its own.

    A terminal's Ctrl-C reaches the coordinator alone, which passes it on to each
    importer itself. The importer's console output duplicates its log, and would break a
    terminal's table, so it is discarded.

    Parameters:
        arguments: The command line after ``python -m opus_import``.

    Returns:
        The running process.
    """
    command = [sys.executable, '-m', 'opus_import', *arguments]
    # As in run_step: this module's constants and the caller's options, with no shell.
    return subprocess.Popen(  # nosec B603
        command, stdout=subprocess.DEVNULL, process_group=0
    )


def confirm(schema: str | None) -> bool:
    """Ask whether to erase the database, and read the answer.

    Parameters:
        schema: The schema the run was pointed at, or None when the configuration file's
            own schema is the one being erased.

    Returns:
        Whether `CONFIRMATION` was typed exactly.
    """
    target = schema if schema is not None else 'the schema named in $OPUS_CONFIG'
    print('*** A full import ERASES every OPUS table in the schema before it starts. ***')
    print(f'*** About to erase and re-import: {target}')
    return input(f'>>> Type {CONFIRMATION} to continue: ') == CONFIRMATION


def _open_db(
    config: OpusConfig,
    schema: str | None,
    *,
    read_only: bool,
    logger: pdslogger.PdsLogger | None = None,
) -> ImportDBSuper:
    """Open the target schema the way the import does, with no bulk load.

    Parameters:
        config: The configuration.
        schema: The schema, or None for the configuration's.
        read_only: Whether to execute no write.
        logger: Where the connection reports, or None.

    Returns:
        The open connection.
    """
    from opus_import import importdb

    return importdb.get_db(
        config.database.brand,
        config.database.host,
        config.database.database,
        schema if schema is not None else config.database.schema,
        config.database.user,
        config.database.password,
        logger=logger,
        read_only=read_only,
        bulk_load=False,
    )


def registry_states(schema: str | None) -> list[tuple[str, str]]:
    """Read every registered bundle's state from the target schema.

    Parameters:
        schema: The database schema, or None for the configuration's.

    Returns:
        ``(bundle, state)`` pairs in registration order; none when the schema has no
        registry.

    Raises:
        opus_import.importdb.super.ImportDBError: If the schema cannot be read, which includes
            a schema that does not exist.
    """
    # Imported here, so that --help needs neither a configuration nor the database driver.
    from opus_config import get_config
    from opus_import import bundle_registry

    db = _open_db(get_config(), schema, read_only=True)
    try:
        return [(row.bundle_id, row.state) for row in bundle_registry.registered_ranges(db)]
    finally:
        db.close()


def unfinished_refusal(states: Sequence[tuple[str, str]]) -> str | None:
    """Return ``--finish``'s refusal for a registry with unfinished bundles, or None.

    Parameters:
        states: What `registry_states` returned.

    Returns:
        The message, naming each bundle that is pending, importing or failed with its
        state, and, for a failed or importing one, the command that returns it to the
        queue; None when every registered bundle is done.
    """
    lines = []
    for bundle, state in states:
        if state not in _UNFINISHED_STATES:
            continue
        line = f'  {bundle} ({state})'
        if state in _REQUEUEABLE_STATES:
            line += f': "opus_import_all --requeue {bundle}" returns it to the queue'
        lines.append(line)
    if not lines:
        return None
    return '--finish refuses to run while registered bundles are not done:\n' + '\n'.join(lines)


################################################################################
# THE COORDINATOR'S TABLE
################################################################################


def format_duration(seconds: float) -> str:
    """Return a duration as ``H:MM:SS``.

    Parameters:
        seconds: The duration; a negative one reads as 0.
    """
    whole = max(0, int(seconds))
    return f'{whole // 3600}:{whole % 3600 // 60:02d}:{whole % 60:02d}'


def _age(now: datetime.datetime, then: datetime.datetime | None) -> str:
    """Return the time since `then`, or ``-``."""
    return '-' if then is None else format_duration((now - then).total_seconds())


def totals_line(snapshot: Snapshot, elapsed: float, remaining: float | None) -> str:
    """Return the coordinator's totals line.

    Parameters:
        snapshot: The registry and importers.
        elapsed: The seconds since tracking began.
        remaining: The estimated seconds left, or None when no rate has been observed.

    Returns:
        The bundles done, importing, pending and failed; the rows done of the estimated
        total; the time elapsed; and the remaining time, labeled as an estimate.
    """
    rows = sum(bundle.rows_done for bundle in snapshot.bundles)
    estimated = sum(bundle.size_estimate for bundle in snapshot.bundles)
    left = 'not yet estimated' if remaining is None else f'about {format_duration(remaining)}'
    return (
        f'Bundles: {snapshot.count("done")} done, {snapshot.count("importing")} importing, '
        f'{snapshot.count("pending")} pending, {snapshot.count("failed")} failed; '
        f'rows {rows:,} of an estimated {estimated:,}; elapsed {format_duration(elapsed)}; '
        f'remaining {left} (an estimate from the observed row rate)'
    )


def importer_lines(snapshot: Snapshot, now: datetime.datetime, stall_minutes: int) -> list[str]:
    """Return one line per importer that is alive, on any computer.

    Parameters:
        snapshot: The registry and importers.
        now: The time, in UTC.
        stall_minutes: How long without progress makes an importer stalled.

    Returns:
        A heading, then each importer's host and pid, bundle, rows done of the bundle's
        estimate, time in the bundle, and time since its last progress, marked
        ``STALLED`` past `stall_minutes`.
    """
    lines = ['host:pid  bundle  rows  in bundle  since progress']
    for process in snapshot.processes:
        if not process.alive:
            continue
        held = [
            bundle
            for bundle in snapshot.bundles
            if bundle.state == 'importing' and bundle.process_id == process.process_id
        ]
        since = (now - process.progress_at).total_seconds()
        stalled = '  STALLED' if since > stall_minutes * 60 else ''
        if held:
            bundle = held[0]
            work = (
                f'{bundle.bundle_id}  {bundle.rows_done:,} of {bundle.size_estimate:,}  '
                f'{_age(now, bundle.started_at)}'
            )
        else:
            work = '-  -  -'
        lines.append(f'{process.host}:{process.pid}  {work}  {format_duration(since)}{stalled}')
    return lines


@dataclass
class RateEstimate:
    """The observed row rate since tracking began, and what it predicts.

    Attributes:
        started: When tracking began, as `time.monotonic` counts.
        first_rows: The rows done at the first reading, or None before it.
    """

    started: float = field(default_factory=time.monotonic)
    first_rows: int | None = None

    def remaining(self, snapshot: Snapshot) -> float | None:
        """Return the estimated seconds left, from the rows done since the first reading.

        Parameters:
            snapshot: The latest reading.

        Returns:
            The rows left over the observed rate, or None before any row has been done
            since the first reading.
        """
        rows = sum(bundle.rows_done for bundle in snapshot.bundles)
        estimated = sum(bundle.size_estimate for bundle in snapshot.bundles)
        if self.first_rows is None:
            self.first_rows = rows
        done = rows - self.first_rows
        elapsed = time.monotonic() - self.started
        if done <= 0 or elapsed <= 0:
            return None
        return max(0, estimated - rows) / (done / elapsed)


def _now() -> datetime.datetime:
    """Return the time in UTC, as the registry's columns hold it."""
    return datetime.datetime.now(datetime.UTC).replace(tzinfo=None, microsecond=0)


def _pending_numbers(snapshot: Snapshot) -> frozenset[int]:
    """Return the numbers of the bundles ``pending`` in a reading."""
    return frozenset(
        bundle.bundle_number for bundle in snapshot.bundles if bundle.state == 'pending'
    )


################################################################################
# THE COORDINATOR
################################################################################


@dataclass
class _Importer:
    """One importer the coordinator started.

    Attributes:
        process: Its process.
        workers: Its workers.
        started_at: When it was started, in UTC, to the second.
        pending_at_start: The bundle numbers ``pending`` in the reading before it started.
        process_id: Its ``import_process`` row, once a reading shows it.
        claimed: Whether a reading has shown it holding a bundle.
        reported: Whether its exit has been dealt with.
    """

    process: subprocess.Popen[bytes]
    workers: int
    started_at: datetime.datetime = field(default_factory=_now)
    pending_at_start: frozenset[int] = frozenset()
    process_id: int | None = None
    claimed: bool = False
    reported: bool = False


class Coordinator:
    """Start importers on this computer, track every importer, recover the lost ones.

    An importer of its own that exits is replaced only while bundles are ``pending``
    that its importers may claim. Which those are is learned from the importers
    themselves: an importer exits cleanly only once it finds nothing it may claim, so a
    bundle that was ``pending`` both when it started and when it exited cleanly is one
    the importers here may not claim (the ``--sets`` of a ``--join``, or an
    ``--exclude-bundles``), and is not started for again. After
    `FAILED_STARTS_ALLOWED` importers in a row exit with failure before claiming a
    bundle, no more are started.

    Attributes:
        interrupts: How many interrupts it has received.
    """

    def __init__(
        self,
        config: OpusConfig,
        schema: str | None,
        division: Division,
        extra_options: Sequence[str],
        *,
        finishing: bool,
        sets: str | None = None,
    ) -> None:
        """Hold what the run needs; nothing is started until `run`.

        Parameters:
            config: The configuration.
            schema: The database schema, or None for the configuration's.
            division: The workers per importer to start.
            extra_options: Options added to every importer's invocation.
            finishing: True for the coordinator, which waits for every importer anywhere
                before it returns; False for ``--join``, which returns once its own have
                exited.
            sets: Comma-separated bundle descriptors the importers may claim, or None.
        """
        self.config = config
        self.schema = schema
        self.division = division
        self.extra_options = list(extra_options)
        self.finishing = finishing
        self.sets = sets
        self.interrupts = 0
        self.terminal = sys.stdout.isatty()
        self.logger: pdslogger.PdsLogger | None = None
        self._host = socket.gethostname()
        self._own: list[_Importer] = []
        self._exited: list[_Importer] = []
        self._starts_left = 0
        self._failed_starts = 0
        self._pending: frozenset[int] = frozenset()
        self._unclaimable: frozenset[int] = frozenset()
        self._leftovers_retried = False
        self._failing_since: float | None = None
        self._events: list[str] = []
        self._shown = 0
        self._seen_states: dict[str, str] = {}
        self._stalls: set[tuple[int, datetime.datetime]] = set()
        self._last_totals = 0.0
        self._own_failures = 0
        self._estimate = RateEstimate()

    def _event(self, line: str, *, level: str | None = 'info') -> None:
        """Report one event: logged, and printed at once without a terminal or under the
        table on one.

        Parameters:
            line: The event.
            level: The level it is logged at, or None for an event already logged.
        """
        stamped = f'{_now():%Y-%m-%d %H:%M:%S} {line}'
        self._events.append(stamped)
        if self.logger is not None and level is not None:
            self.logger.log(level, line)
        if not self.terminal:
            print(stamped, flush=True)
            self._shown = len(self._events)

    def _show_events(self) -> None:
        """Print the events a terminal's table has not shown yet."""
        for line in self._events[self._shown :]:
            print(line, flush=True)
        self._shown = len(self._events)

    def _start(self, workers: int) -> None:
        """Start one importer with the given workers, if the run may start more.

        Parameters:
            workers: Its workers.
        """
        if self._starts_left <= 0:
            return
        self._starts_left -= 1
        arguments = importer_step(self.schema, workers, self.extra_options, self.sets)
        process = start_importer(arguments)
        self._own.append(_Importer(process, workers, pending_at_start=self._pending))
        self._event(f'started importer {process.pid} with {workers} workers')

    def _interrupt(self, signum: int, frame: FrameType | None) -> None:
        """Pass an interrupt on to every running importer of its own.

        Parameters:
            signum: The signal.
            frame: Where the program was. Unused.
        """
        self.interrupts += 1
        for importer in self._running():
            try:
                os.kill(importer.process.pid, signal.SIGINT)
            except ProcessLookupError:
                continue
        if self.interrupts == 1:
            self._event(
                'Interrupted: the importers finish their bundles and claim nothing new; '
                'nothing is finalized, and a rerun resumes',
                level='warning',
            )
        else:
            self._event(
                'Interrupted again: the importers return their bundles to the queue',
                level='warning',
            )

    def _running(self) -> list[_Importer]:
        """Return the importers of its own still running."""
        return [importer for importer in self._own if importer.process.poll() is None]

    def run(self) -> int:
        """Start the importers, then track and recover until the run is over.

        Every event is written to ``opus_import_all.log``, and the events of the run's
        end are printed whether or not standard output is a terminal.

        Returns:
            0 when the coordinator may finish the schema, or when every importer of a
            ``--join`` exited cleanly; 1 otherwise, after saying why.
        """
        from opus_import import import_processes

        ctx = self._context()
        db = ctx.db
        assert db is not None
        try:
            import_processes.create_process_table(db)
            snapshot = import_processes.read_snapshot(db)
            self._pending = _pending_numbers(snapshot)
            # Room to replace every importer once per bundle, which a bundle lost twice
            # bounds; it ends a run whose importers cannot start at all.
            self._starts_left = self.division.importers + len(snapshot.bundles)
            previous = signal.signal(signal.SIGINT, self._interrupt)
            try:
                for workers in self.division.per_importer:
                    self._start(workers)
                while True:
                    status = self._pass(ctx)
                    if status is not None:
                        self._show_events()
                        return status
                    time.sleep(TRACK_SECONDS)
            finally:
                signal.signal(signal.SIGINT, previous)
        finally:
            if ctx.db is not None:
                ctx.db.close()

    def _context(self) -> ImportContext:
        """Open the coordinator's log and connection, and a context for the recovery's
        deletes."""
        import pdslogger

        from opus_import.context import ImportContext

        logger = pdslogger.PdsLogger('opus_import.coordinator')
        log_dir = self.config.paths.import_log_dir
        logger.add_handler(
            pdslogger.file_handler(os.path.join(log_dir, 'opus_import_all.log'), rotation='ymdhms')
        )
        logger.add_handler(pdslogger.error_handler(log_dir, rotation='none'))
        self.logger = logger
        ctx = ImportContext(args=argparse.Namespace(), logger=logger)
        ctx.db = _open_db(self.config, self.schema, read_only=False, logger=logger)
        return ctx

    def _pass(self, ctx: ImportContext) -> int | None:
        """Read, recover, replace and report once.

        A pass whose reading of the database fails is logged and the connection opened
        again on the next; once they have failed for `DATABASE_OUTAGE_SECONDS` in a row,
        the coordinator gives up.

        Parameters:
            ctx: The coordinator's context.

        Returns:
            The run's exit status once it is over, or None while it goes on.
        """
        from opus_import import import_processes, importdb
        from opus_import.steps import do_recover

        for importer in self._own:
            code = importer.process.poll()
            if code is not None and not importer.reported:
                importer.reported = True
                self._exited.append(importer)
                if code != 0:
                    self._own_failures += 1
                self._event(f'importer {importer.process.pid} exited with status {code}')
        try:
            if ctx.db is None:
                ctx.db = _open_db(self.config, self.schema, read_only=False, logger=self.logger)
            recovered = do_recover.recover_lost_importers(ctx)
            snapshot = import_processes.read_snapshot(ctx.db)
        except importdb.ImportDBError as e:
            return self._reading_failed(ctx, e)
        self._failing_since = None
        for line in recovered:
            self._event(line, level=None)
        self._pending = _pending_numbers(snapshot)
        self._track(snapshot)
        if not self.interrupts:
            self._replace(snapshot)
        self._report(snapshot)
        if self._running():
            return None
        if self.interrupts:
            self._event(
                'Interrupted: the schema is not finalized; a rerun resumes', level='warning'
            )
            return 1
        if not self.finishing:
            return 1 if self._own_failures else 0
        return self._settle(snapshot)

    def _reading_failed(self, ctx: ImportContext, error: Exception) -> int | None:
        """Log a pass whose reading failed, and close the connection for the next to open.

        Parameters:
            ctx: The coordinator's context.
            error: What failed.

        Returns:
            1 once readings have failed for `DATABASE_OUTAGE_SECONDS` in a row, or once
            an interrupted run's importers have all exited; None otherwise.
        """
        now = time.monotonic()
        if self._failing_since is None:
            self._failing_since = now
        self._event(f'The database could not be read: {error}', level='warning')
        if ctx.db is not None:
            with contextlib.suppress(Exception):
                ctx.db.close()
            ctx.db = None
        running = self._running()
        if self.interrupts and not running:
            self._event(
                'Interrupted: the schema is not finalized; a rerun resumes', level='warning'
            )
            return 1
        if now - self._failing_since < DATABASE_OUTAGE_SECONDS:
            return None
        pids = ', '.join(str(importer.process.pid) for importer in running) or 'none'
        self._event(
            f'The database has not been readable for {format_duration(now - self._failing_since)}, '
            f'so the coordinator stops; the importers it started that still run ({pids}) are '
            'left running, and a rerun resumes the import and tracks them',
            level='error',
        )
        return 1

    def _track(self, snapshot: Snapshot) -> None:
        """Note each importer of its own's row, whether it has claimed a bundle, and what
        the exits since the last pass say.

        Parameters:
            snapshot: The latest reading.
        """
        holders = {
            bundle.process_id for bundle in snapshot.bundles if bundle.process_id is not None
        }
        for importer in self._own:
            if importer.process_id is None:
                rows = [
                    process.process_id
                    for process in snapshot.processes
                    if process.host == self._host
                    and process.pid == importer.process.pid
                    and process.started_at >= importer.started_at
                ]
                importer.process_id = max(rows, default=None)
            if importer.process_id in holders:
                importer.claimed = True
        for importer in self._exited:
            if importer.claimed:
                self._failed_starts = 0
            if importer.process.poll() == 0:
                # It found nothing it may claim; what was pending all its life it may not.
                self._unclaimable |= importer.pending_at_start & self._pending
            elif not importer.claimed:
                self._failed_starts += 1
                self._stop_failed_starts(snapshot, importer)
        self._exited = []

    def _stop_failed_starts(self, snapshot: Snapshot, importer: _Importer) -> None:
        """Start no more importers once `FAILED_STARTS_ALLOWED` in a row failed unclaimed.

        Parameters:
            snapshot: The latest reading.
            importer: The latest to fail.
        """
        if self._failed_starts < FAILED_STARTS_ALLOWED or self._starts_left <= 0:
            return
        self._starts_left = 0
        process = snapshot.process(importer.process_id)
        where = (
            '' if process is None else f"; the last one's log: {process.host}:{process.log_path}"
        )
        self._event(
            f'{self._failed_starts} importers in a row exited with failure before claiming a '
            f'bundle, so no more are started{where}',
            level='error',
        )

    def _replace(self, snapshot: Snapshot) -> None:
        """Start importers into the free places while bundles its importers may claim are
        pending, beyond the ones its idle importers are about to claim.

        Parameters:
            snapshot: The latest reading.
        """
        claimable = self._pending - self._unclaimable
        if not claimable:
            return
        importing = {
            bundle.process_id for bundle in snapshot.bundles if bundle.state == 'importing'
        }
        running = self._running()
        idle = sum(1 for importer in running if importer.process_id not in importing)
        free = list(self.division.per_importer)
        for importer in running:
            if importer.workers in free:
                free.remove(importer.workers)
        for workers in free[: max(0, len(claimable) - idle)]:
            self._start(workers)

    def _settle(self, snapshot: Snapshot) -> int | None:
        """Decide, once no importer of its own runs, whether the run is over.

        Parameters:
            snapshot: The latest reading.

        Returns:
            None while an importer elsewhere is alive or a lost one's bundle awaits
            recovery, or while bundles are pending that its importers have not yet
            been started for once more; 0 when every bundle is done; otherwise 1,
            naming what is left.
        """
        if any(process.alive for process in snapshot.processes):
            return None
        importing = [bundle for bundle in snapshot.bundles if bundle.state == 'importing']
        if any(bundle.process_id is not None for bundle in importing):
            return None
        if importing:
            names = ', '.join(bundle.bundle_id for bundle in importing)
            self._event(
                f'Bundles importing outside the queue, with no importer: {names}; once the '
                'process importing them has stopped, "opus_import_all --requeue" returns '
                'them and a rerun imports them',
                level='warning',
            )
            return 1
        pending = [bundle.bundle_id for bundle in snapshot.bundles if bundle.state == 'pending']
        if pending:
            if not self._leftovers_retried and self._starts_left > 0:
                # A bundle returned to the queue as an importer exited can be taken for
                # one it may not claim; one more start settles it.
                self._leftovers_retried = True
                self._unclaimable = frozenset()
                return None
            self._event(
                f'Bundles are pending that no importer started here claimed: '
                f'{", ".join(pending)}; once importers that may claim them have imported '
                'them ("opus_import_all --join" on a computer that holds them), a rerun '
                'finishes the schema',
                level='warning',
            )
            return 1
        failed = [bundle for bundle in snapshot.bundles if bundle.state == 'failed']
        if failed:
            lines = []
            for bundle in failed:
                process = snapshot.process(bundle.process_id)
                where = (
                    'no importer recorded'
                    if process is None
                    else f"its importer's log: {process.host}:{process.log_path}"
                )
                lines.append(f'  {bundle.bundle_id} ({where})')
            self._event(
                'Bundles failed, so the schema is not finalized; after the fix, '
                '"opus_import_all --requeue <bundle>" and a rerun import them:\n'
                + '\n'.join(lines),
                level='warning',
            )
            return 1
        return 0

    def _report(self, snapshot: Snapshot) -> None:
        """Redraw the table on a terminal, or log what changed without one.

        Parameters:
            snapshot: The latest reading.
        """
        now = _now()
        stall = self.config.import_.stall_warning_minutes
        remaining = self._estimate.remaining(snapshot)
        elapsed = time.monotonic() - self._estimate.started
        totals = totals_line(snapshot, elapsed, remaining)
        if self.terminal:
            screen = [
                self.division.describe(),
                totals,
                *importer_lines(snapshot, now, stall),
                '',
                *self._events[-EVENTS_SHOWN:],
            ]
            print(_CLEAR_SCREEN + '\n'.join(screen), flush=True)
            self._shown = len(self._events)
            return
        for bundle in snapshot.bundles:
            before = self._seen_states.get(bundle.bundle_id)
            if bundle.state in ('done', 'failed') and before not in (None, bundle.state):
                self._event(f'{bundle.bundle_id} {bundle.state}: {bundle.rows_done:,} rows')
            self._seen_states[bundle.bundle_id] = bundle.state
        for process in snapshot.processes:
            key = (process.process_id, process.progress_at)
            stalled = (now - process.progress_at).total_seconds() > stall * 60
            if process.alive and stalled and key not in self._stalls:
                self._stalls.add(key)
                self._event(
                    f'importer {process.host}:{process.pid} has made no progress for '
                    f'{format_duration((now - process.progress_at).total_seconds())}; it is '
                    'not stopped'
                )
        interval = self.config.import_.status_interval_minutes * 60
        if time.monotonic() - self._last_totals >= interval:
            self._last_totals = time.monotonic()
            print(totals, flush=True)


def show_status(config: OpusConfig, schema: str | None, *, watch: bool, recover: bool) -> int:
    """Print the coordinator's table, from any computer.

    Parameters:
        config: The configuration.
        schema: The database schema, or None for the configuration's.
        watch: Whether to redraw it every few seconds until interrupted. A reading that
            fails, as one does while a rerun drops the tables, is reported on standard
            error and the next is read on a connection opened again.
        recover: Whether to recover lost importers first, which writes; without it the
            connection writes nothing.

    Returns:
        0, or 1 when the schema cannot be read, which without `watch` ends the command.
    """
    import pdslogger

    from opus_import import import_processes, importdb
    from opus_import.context import ImportContext
    from opus_import.steps import do_recover

    db: ImportDBSuper | None = None
    estimate = RateEstimate()
    try:
        while True:
            try:
                if db is None:
                    db = _open_db(config, schema, read_only=not recover)
                    if recover:
                        import_processes.create_process_table(db)
                        ctx = ImportContext(
                            args=argparse.Namespace(), logger=pdslogger.PdsLogger('status')
                        )
                        ctx.db = db
                        for line in do_recover.recover_lost_importers(ctx) or [
                            'No importer is lost'
                        ]:
                            print(line)
                        recover = False
                snapshot = import_processes.read_snapshot(db)
            except importdb.ImportDBError as e:
                print(f'opus_import_all: the schema could not be read: {e}', file=sys.stderr)
                if db is not None:
                    with contextlib.suppress(Exception):
                        db.close()
                    db = None
                if not watch:
                    return 1
            else:
                elapsed = time.monotonic() - estimate.started
                lines = [
                    totals_line(snapshot, elapsed, estimate.remaining(snapshot)),
                    *importer_lines(snapshot, _now(), config.import_.stall_warning_minutes),
                ]
                print((_CLEAR_SCREEN if watch else '') + '\n'.join(lines), flush=True)
                if not watch:
                    return 0
            time.sleep(TRACK_SECONDS)
    except KeyboardInterrupt:
        return 0
    finally:
        if db is not None:
            db.close()


################################################################################
# THE COMMAND LINE
################################################################################


def _count_or(word: str) -> Callable[[str], int | str]:
    """Return an argument type: a whole number of at least 1, or `word`.

    Parameters:
        word: The one word accepted beside a number.
    """

    def parse(text: str) -> int | str:
        """Parse one argument."""
        if text == word:
            return text
        try:
            count = int(text)
        except ValueError:
            count = 0
        if count < 1:
            raise argparse.ArgumentTypeError(
                f'must be a whole number of at least 1 or "{word}", not {text!r}'
            )
        return count

    return parse


def _create_argument_parser() -> argparse.ArgumentParser:
    """Build ``opus_import_all``'s argument parser."""
    parser = argparse.ArgumentParser(
        prog='opus_import_all',
        description='Import every bundle set OPUS holds: register the bundles, import them '
        'with several importers drawing from one queue, and finish the database',
        epilog='Any other option is passed to every opus_import invocation that reads the '
        'holdings.',
    )
    steps = parser.add_mutually_exclusive_group()
    steps.add_argument(
        '--prepare',
        action='store_true',
        help='register every bundle in import order (after the erase, with --scorched-earth)',
    )
    steps.add_argument(
        '--join',
        action='store_true',
        help='start --importers importers on this computer (1 by default) and track them; '
        'they draw from the queue a coordinator elsewhere prepared, and nothing is finished',
    )
    steps.add_argument(
        '--finish',
        action='store_true',
        help='finalize, import the dictionary, validate and mark the schema ready, once '
        'every registered bundle is done',
    )
    steps.add_argument(
        '--requeue',
        nargs='+',
        metavar='BUNDLE',
        help='return failed bundles, or importing ones whose importer is gone, to the '
        'queue, after deleting their rows',
    )
    steps.add_argument(
        '--status',
        action='store_true',
        help="print the coordinator's table of the importers and the totals, from any computer",
    )
    parser.add_argument(
        '--sets',
        metavar='DESC,DESC',
        help='with --join, claim only the bundles these comma-separated descriptors name; '
        'with --prepare or no step, register them in place of every bundle set',
    )
    parser.add_argument(
        '--workers',
        metavar='N',
        type=_count_or(MAX_WORKERS),
        help='the total of worker processes on this computer, divided among the importers, '
        f'or "{MAX_WORKERS}" for the ceiling; [import] workers by default',
    )
    parser.add_argument(
        '--importers',
        metavar='M',
        type=_count_or(AUTO_IMPORTERS),
        help='how many importers to start on this computer, capped at --workers: '
        f'"{AUTO_IMPORTERS}" ([import] importers, the default with no step) or a number '
        '(1 is the default with --join)',
    )
    parser.add_argument(
        '--watch',
        action='store_true',
        help='with --status, redraw the table every few seconds until interrupted',
    )
    parser.add_argument(
        '--recover',
        action='store_true',
        help='with --status, first return the bundles of lost importers to the queue',
    )
    # Named exactly as the pipeline names it, and not passed through: an option this
    # parser did not recognize would reach only the steps that read the holdings and not
    # the ones that finish the database, which would finish a different database from
    # the one just imported.
    parser.add_argument(
        '--override-db-schema',
        metavar='SCHEMA',
        help='the database schema to import into, instead of the one the configuration '
        'file names; it is created if it does not exist',
    )
    parser.add_argument(
        '--scorched-earth',
        action='store_true',
        help='erase every OPUS table in the schema before registering, after asking for '
        'confirmation',
    )
    parser.add_argument(
        '--yes',
        action='store_true',
        help="answer --scorched-earth's confirmation, which running under nohup needs; "
        'refused without --scorched-earth',
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='print the steps these arguments would run, and run none of them',
    )
    return parser


def _division(parser: argparse.ArgumentParser, arguments: argparse.Namespace) -> Division:
    """Resolve the division the arguments ask for, from the configuration.

    Parameters:
        parser: The parser, whose ``error`` reports a refusal.
        arguments: The parsed arguments.

    Returns:
        The division.

    Raises:
        SystemExit: If the total of workers is above the ceiling.
    """
    from opus_config import ConfigError, get_config

    default = 1 if arguments.join else AUTO_IMPORTERS
    importers = arguments.importers if arguments.importers is not None else default
    try:
        return resolve_division(get_config().import_, arguments.workers, importers)
    except ConfigError as e:
        parser.error(str(e))


def _print_plan(
    arguments: argparse.Namespace, extra_options: Sequence[str], division: Division | None
) -> None:
    """Print, for ``--dry-run``, the steps the arguments would run.

    Parameters:
        arguments: The parsed arguments.
        extra_options: The options passed through.
        division: The importers to start, or None when no importer would start.
    """
    schema = arguments.override_db_schema
    run_all = not (
        arguments.prepare
        or arguments.join
        or arguments.finish
        or arguments.requeue
        or arguments.status
    )
    if division is not None:
        print(division.describe())
    if arguments.prepare or run_all:
        registered = BUNDLE_SETS if arguments.sets is None else (arguments.sets,)
        print(
            f'prepare: {"erases" if arguments.scorched_earth else "erases nothing"}; '
            f'registers, in import order: {" ".join(registered)}'
        )
        for step in prepare_steps(schema, arguments.scorched_earth, extra_options, arguments.sets):
            print(' '.join(['opus_import', *step]))
    if division is not None:
        claimed = arguments.sets if arguments.join else None
        print(
            f'import: {division.importers} importers on this computer, tracked every '
            f'{TRACK_SECONDS:g} seconds, a lost one replaced while bundles are pending'
        )
        for workers in division.per_importer:
            print(
                ' '.join(['opus_import', *importer_step(schema, workers, extra_options, claimed)])
            )
    if arguments.finish or run_all:
        print('finish: once every registered bundle is done')
        for step in finish_steps(schema):
            print(' '.join(['opus_import', *step]))
    if arguments.requeue:
        print('requeue:')
        for step in requeue_steps(schema, arguments.requeue):
            print(' '.join(['opus_import', *step]))
    if arguments.status:
        print("status: prints the coordinator's table" + (', watching' if arguments.watch else ''))


def _run(parser: argparse.ArgumentParser, steps: list[list[str]]) -> None:
    """Run invocations in order, stopping at the first that fails.

    Parameters:
        parser: The parser, whose ``exit`` reports a failure.
        steps: The command lines.

    Raises:
        SystemExit: With the failed invocation's status, naming it.
    """
    for step in steps:
        status = run_step(step)
        if status != 0:
            parser.exit(
                status if 0 < status < 256 else 1,
                f'{parser.prog}: stopped -- `opus_import {" ".join(step)}` exited {status}\n',
            )


def _finish(parser: argparse.ArgumentParser, schema: str | None) -> None:
    """Run ``--finish``: refuse while a registered bundle is not done, else finish.

    Parameters:
        parser: The parser, whose ``exit`` reports a refusal or a failure.
        schema: The database schema, or None for the configuration's.

    Raises:
        SystemExit: With status 1 when the registry refuses, or the failed invocation's
            status.
    """
    refusal = unfinished_refusal(registry_states(schema))
    if refusal is not None:
        parser.exit(1, f'{parser.prog}: {refusal}\n')
    _run(parser, finish_steps(schema))


def _check_arguments(parser: argparse.ArgumentParser, arguments: argparse.Namespace) -> None:
    """Refuse the combinations of arguments that mean nothing.

    Parameters:
        parser: The parser, whose ``error`` reports a refusal.
        arguments: The parsed arguments.

    Raises:
        SystemExit: With status 2 for a refused combination.
    """
    if arguments.yes and not arguments.scorched_earth:
        parser.error(
            '--yes answers the confirmation --scorched-earth asks, and is refused without it'
        )
    step_named = (
        arguments.prepare
        or arguments.join
        or arguments.finish
        or arguments.requeue
        or arguments.status
    )
    if arguments.scorched_earth and step_named and not arguments.prepare:
        parser.error(
            '--scorched-earth erases before registering, so it goes with --prepare or no step'
        )
    if (arguments.workers or arguments.importers) and step_named and not arguments.join:
        parser.error(
            '--workers and --importers divide the importers on this computer, so they go '
            'with --join or no step'
        )
    if arguments.sets and step_named and not (arguments.join or arguments.prepare):
        parser.error(
            '--sets names bundles to register or claim, so it goes with --prepare, '
            '--join or no step'
        )
    if (arguments.watch or arguments.recover) and not arguments.status:
        parser.error('--watch and --recover go with --status')


def main() -> None:
    """Run the full-holdings import, or the one step named.

    Raises:
        SystemExit: With a non-zero status if the arguments are refused, the
            confirmation is refused, an invocation fails, naming it, a bundle failed,
            the run was interrupted, or ``--finish`` refuses. A successful run exits
            zero, which says every step ran -- not that every step was clean. Read
            ``ERRORS.log`` for that.
    """
    parser = _create_argument_parser()
    arguments, extra_options = parser.parse_known_args()
    _check_arguments(parser, arguments)
    step_named = (
        arguments.prepare
        or arguments.join
        or arguments.finish
        or arguments.requeue
        or arguments.status
    )
    starts_importers = arguments.join or not step_named
    # Resolved first, so a total above the ceiling stops the run before anything is erased.
    division = _division(parser, arguments) if starts_importers else None

    if arguments.dry_run:
        _print_plan(arguments, extra_options, division)
        return

    schema = arguments.override_db_schema
    if arguments.status:
        from opus_config import get_config

        sys.exit(
            show_status(get_config(), schema, watch=arguments.watch, recover=arguments.recover)
        )
    if arguments.scorched_earth and not arguments.yes and not confirm(schema):
        parser.exit(1, 'Aborting: the confirmation was not given.\n')

    if division is not None:
        print(division.describe(), flush=True)
    if arguments.requeue:
        _run(parser, requeue_steps(schema, arguments.requeue))
        return
    if arguments.prepare or not step_named:
        _run(
            parser,
            prepare_steps(schema, arguments.scorched_earth, extra_options, arguments.sets),
        )
    if division is not None:
        status = coordinate(
            schema,
            division,
            extra_options,
            finishing=not step_named,
            sets=arguments.sets if arguments.join else None,
        )
        if status != 0:
            parser.exit(status, f'{parser.prog}: stopped -- the importers did not finish\n')
    if arguments.finish or not step_named:
        _finish(parser, schema)
    if not step_named:
        print('Import is complete. Read ERRORS.log before trusting it.')


def coordinate(
    schema: str | None,
    division: Division,
    extra_options: Sequence[str],
    *,
    finishing: bool,
    sets: str | None,
) -> int:
    """Start, track and recover importers until the run is over (`Coordinator.run`).

    Parameters:
        schema: The database schema, or None for the configuration's.
        division: The importers to start.
        extra_options: Options added to every importer's invocation.
        finishing: Whether to wait for every importer anywhere, as the coordinator does.
        sets: Comma-separated bundle descriptors the importers may claim, or None.

    Returns:
        The run's exit status.
    """
    from opus_config import get_config

    coordinator = Coordinator(
        get_config(), schema, division, extra_options, finishing=finishing, sets=sets
    )
    return coordinator.run()


if __name__ == '__main__':  # pragma: no cover
    main()
