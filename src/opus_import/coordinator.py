"""The coordinator: start importers on this computer, track every importer, recover the lost.

`Coordinator` is what ``opus_import_all`` runs once the bundles are registered
(`opus_import.import_all`), and with ``--join``: it starts ``opus_import --join``
importers on this computer (`start_importer`), reads the bundle registry and
``import_process`` every `TRACK_SECONDS`, returns the bundles of lost importers to the
queue (`opus_import.steps.do_recover`), replaces its own importers while bundles they may
claim are pending, and decides when the run is over. `show_status` prints its table from
any computer.
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

import pdslogger

from opus_import import import_all, import_processes, importdb
from opus_import.context import ImportContext
from opus_import.steps import do_recover

if TYPE_CHECKING:
    from collections.abc import Sequence
    from types import FrameType

    from opus_config import OpusConfig
    from opus_import.import_all import Division
    from opus_import.import_processes import Snapshot
    from opus_import.importdb.super import ImportDBSuper

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

#: What redraws a terminal from its top-left corner.
_CLEAR_SCREEN = '\x1b[H\x1b[2J'


################################################################################
# THE TABLE
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
    # The module's own name and the caller's options, run without a shell.
    return subprocess.Popen(  # nosec B603
        command, stdout=subprocess.DEVNULL, process_group=0
    )


def _send_interrupt(process: subprocess.Popen[bytes]) -> None:
    """Send SIGINT to an importer, unless it has already gone."""
    with contextlib.suppress(ProcessLookupError):
        os.kill(process.pid, signal.SIGINT)


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
        """Start one importer with the given workers, if the run may start more and has
        not been interrupted.

        An interrupt that arrives while the importer is being started finds it not yet
        registered, so it is passed on to the importer once it is.

        Parameters:
            workers: Its workers.
        """
        if self._starts_left <= 0 or self.interrupts:
            return
        self._starts_left -= 1
        arguments = import_all.importer_step(self.schema, workers, self.extra_options, self.sets)
        process = start_importer(arguments)
        self._own.append(_Importer(process, workers, pending_at_start=self._pending))
        self._event(f'started importer {process.pid} with {workers} workers')
        if self.interrupts:
            _send_interrupt(process)

    def _interrupt(self, signum: int, frame: FrameType | None) -> None:
        """Pass an interrupt on to every running importer of its own.

        Parameters:
            signum: The signal.
            frame: Where the program was. Unused.
        """
        self.interrupts += 1
        for importer in self._running():
            _send_interrupt(importer.process)
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
        logger = pdslogger.PdsLogger('opus_import.coordinator')
        log_dir = self.config.paths.import_log_dir
        logger.add_handler(
            pdslogger.file_handler(os.path.join(log_dir, 'opus_import_all.log'), rotation='ymdhms')
        )
        logger.add_handler(pdslogger.error_handler(log_dir, rotation='none'))
        self.logger = logger
        ctx = ImportContext(args=argparse.Namespace(), logger=logger)
        ctx.db = import_all.open_target_db(self.config, self.schema, read_only=False, logger=logger)
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
                ctx.db = import_all.open_target_db(
                    self.config, self.schema, read_only=False, logger=self.logger
                )
            snapshot = import_processes.read_snapshot(ctx.db)
            # Before the recovery, which clears a dead importer's hold on its bundle.
            self._track(snapshot)
            recovered = do_recover.recover_lost_importers(ctx)
            if recovered:
                snapshot = import_processes.read_snapshot(ctx.db)
        except importdb.ImportDBError as e:
            return self._reading_failed(ctx, e)
        self._failing_since = None
        for line in recovered:
            self._event(line, level=None)
        self._pending = _pending_numbers(snapshot)
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

        It reads the pass's reading from before the recovery: an importer that claimed a
        bundle and died since the last pass still holds it there, and a bundle the
        recovery is about to return to the queue is not yet among the pending ones an
        importer that exited cleanly may not claim.

        Parameters:
            snapshot: The pass's reading, taken before its recovery.
        """
        pending = _pending_numbers(snapshot)
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
                self._unclaimable |= importer.pending_at_start & pending
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
    db: ImportDBSuper | None = None
    estimate = RateEstimate()
    try:
        while True:
            try:
                if db is None:
                    db = import_all.open_target_db(config, schema, read_only=not recover)
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
