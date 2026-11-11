"""The state one import run carries from the command line down to the obs classes.

An import run has a database connection, a logger, the parsed command-line arguments and
a handful of counters and caches that every layer of the pipeline reads. They live in a
single `ImportContext` that `opus_import.cli` builds and passes down: `cli` hands it to
each step, the steps hand it to each other, and the obs classes keep it as ``self._ctx``.
Nothing in the pipeline reaches for pipeline state any other way.

The context's logging is reached through `ImportContext.log`, an `ImportLog` bound to the
context. It is what puts the bundle, index row and filespec being processed in front of
every message, and it is what makes a message that would otherwise repeat hundreds of
thousands of times appear once. The step modules call the same operations through the
`opus_import.import_util` ``log_*`` functions, which take the context as their first
argument.
"""

from __future__ import annotations

import contextlib
import time
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from opus_config.config import DEFAULT_INDEX_WORKERS, DEFAULT_WORKER_ROWS, DEFAULT_WORKERS

if TYPE_CHECKING:
    import argparse
    from collections.abc import Iterator

    import pdslogger

    from opus_import.bundle_registry import BundleIds
    from opus_import.deferred import Capture
    from opus_import.import_processes import BundleGuard, ImporterLock
    from opus_import.importdb.super import ImportDBSuper
    from opus_import.mult_fields import MultFieldInfo
    from opus_import.steps.do_import_mult import MultFieldCache


class ImportLog:
    """The import pipeline's log, bound to one `ImportContext`.

    Every message is prefixed with the bundle, index row and primary filespec the context
    is currently on, so a message read out of a log file names the observation that
    produced it. The ``nonrepeating_`` methods log a given message only once per run,
    which is what keeps a fault shared by every row of an index out of the log a hundred
    thousand times.

    While the context is capturing (`ImportContext.capture`, in a pool worker), every
    method records its call and the position instead, deduplicating nothing and marking
    nothing, and the import's process replays the call where the serial loop would have
    made it.

    Instances are created by `ImportContext`; the pipeline reaches this class only as
    ``ctx.log``.
    """

    def __init__(self, ctx: ImportContext) -> None:
        """Bind a log to a context.

        Parameters:
            ctx: The context whose logger and current position this log reports through.
        """
        self._ctx = ctx

    def _position(self) -> str:
        """Return the bracketed bundle/row/filespec prefix, or an empty string.

        Returns:
            ``'[<bundle> index row <n> "<filespec>"] '`` with whichever of the three the
            context currently knows, or ``''`` when it is not importing a bundle.
        """
        ctx = self._ctx
        ret = ''
        if ctx.current_bundle_id is not None:
            ret = ctx.current_bundle_id
            if ctx.current_index_row_number is not None:
                ret += ' index row ' + str(ctx.current_index_row_number)
            if ctx.current_primary_filespec is not None:
                ret += f' "{ctx.current_primary_filespec}"'
        if ret != '':
            ret = '[' + ret + '] '
        return ret

    def _recorded(self, method: str, args: tuple[Any, ...]) -> bool:
        """Record a call on the context's capture, if it has one.

        Parameters:
            method: The name of the method called.
            args: Its arguments.

        Returns:
            True if the call was recorded, and so is not to be carried out.
        """
        ctx = self._ctx
        if ctx.capture is None:
            return False
        ctx.capture.log((ctx.current_index_row_number, ctx.current_primary_filespec), method, args)
        return True

    def error(self, msg: str, *args: Any) -> None:
        """Log a message at error level and mark the import as having produced bad data.

        Parameters:
            msg: The message, position-prefixed before it is logged.
            args: Further arguments passed to the underlying logger.
        """
        if self._recorded('error', (msg, *args)):
            return
        self._ctx.logger.log('error', self._position() + msg, *args)
        self._ctx.mark_bad_data()

    def warning(self, msg: str, *args: Any) -> None:
        """Log a message at warning level.

        Parameters:
            msg: The message, position-prefixed before it is logged.
            args: Further arguments passed to the underlying logger.
        """
        if self._recorded('warning', (msg, *args)):
            return
        self._ctx.logger.log('warning', self._position() + msg, *args)

    def info(self, msg: str, *args: Any) -> None:
        """Log a message at info level.

        Parameters:
            msg: The message, position-prefixed before it is logged.
            args: Further arguments passed to the underlying logger.
        """
        if self._recorded('info', (msg, *args)):
            return
        self._ctx.logger.log('info', self._position() + msg, *args)

    def debug(self, msg: str, *args: Any) -> None:
        """Log a message at debug level.

        Parameters:
            msg: The message, position-prefixed before it is logged.
            args: Further arguments passed to the underlying logger.
        """
        if self._recorded('debug', (msg, *args)):
            return
        self._ctx.logger.log('debug', self._position() + msg, *args)

    def nonrepeating_error(self, msg: str) -> None:
        """Log an error the first time this run produces it, and mark bad data every time.

        Every call marks the bundle being imported as having errors, so a later bundle
        that repeats an earlier bundle's error is recorded failed too.

        Parameters:
            msg: The message. Two calls with equal messages log once, even though their
                position prefixes differ.
        """
        if self._recorded('nonrepeating_error', (msg,)):
            return
        if msg in self._ctx.logged_import_errors:
            self._ctx.mark_bad_data()
            return
        self._ctx.logged_import_errors.add(msg)
        self.error(msg)

    def nonrepeating_warning(self, msg: str) -> None:
        """Log a warning the first time this run produces it, and ignore it after that.

        Parameters:
            msg: The message. Two calls with equal messages log once, even though their
                position prefixes differ.
        """
        if self._recorded('nonrepeating_warning', (msg,)):
            return
        if msg not in self._ctx.logged_import_warnings:
            self._ctx.logged_import_warnings.add(msg)
            self.warning(msg)

    def unknown_target_name(self, target_name: str) -> None:
        """Report a TARGET_NAME the target tables do not describe.

        Parameters:
            target_name: The name read from the PDS label.
        """
        self.nonrepeating_error(
            f'Unknown TARGET_NAME "{target_name}" - edit config_targets/target_name_info.py'
        )


@dataclass
class ImportContext:
    """Everything one import run needs to share between its layers.

    Exactly one is built per run, by `opus_import.cli.main`, and passed by hand from
    there down. The fields fall into three groups: what the run was given (`args`,
    `logger`, `db`), where it currently is (`current_bundle_id`,
    `current_index_row_number`, `current_primary_filespec`), and what it has accumulated
    (the caches, the deduplication records, and `import_has_bad_data`).

    Attributes:
        args: The parsed command-line arguments.
        logger: The `pdslogger.PdsLogger` every message ends up in. Prefer `log` over
            using it directly; it is here for the ``open``/``close`` section calls and
            for handing to code outside the pipeline.
        db: The open database, or None before `opus_import.cli` connects.
        log: The `ImportLog` bound to this context.
        python_warning_list: Python warnings captured since they were last reported.
            Rebound to a new list each time they are reported, so read it through the
            context rather than holding a reference to it.
        logged_import_errors: Messages `ImportLog.nonrepeating_error` has already logged.
        logged_import_warnings: Messages `ImportLog.nonrepeating_warning` has already
            logged.
        import_has_bad_data: True once the run has produced data not worth keeping. The
            run aborts on it unless ``--ignore-errors`` was given. Every `log` error sets
            it, and a few sites outside `log` set it through `mark_bad_data`; but it is
            not a complete record of the run's errors, because several steps log
            failures straight to `logger` and leave it alone.
        bundle_has_errors: True once the bundle being imported has logged an error,
            set with `import_has_bad_data` and cleared at the start of each bundle; it
            decides whether the bundle registry records the bundle ``failed``.
        bundle_ids: The observation ids the bundle being imported hands out, from its
            registered range (`opus_import.bundle_registry.BundleIds`), or None outside
            a bundle.
        current_bundle_id: The bundle being imported, or None outside a bundle.
        current_index_row_number: The 1-based index row being imported, or None.
        current_primary_filespec: The primary filespec of the observation being imported,
            or None. It is unknown for part of each row, because some bundles take it
            from the supplemental index.
        mult_fields: Every mult field's ``mult_field`` row, keyed by qualified name, once
            `opus_import.mult_fields.ensure_mult_fields` has read them; None before.
        mult_table_cache: Each mult field read during this bundle, keyed by qualified
            name: its rows and a dictionary from value to row
            (`opus_import.steps.do_import_mult.MultFieldCache`). Cleared for each bundle.
        step_timings: Wall-clock seconds per step the run has timed with `timed`,
            keyed by step name, which is what ``--timing-json`` writes out.
        import_path: The path an invocation that imports bundles takes, once
            `opus_import.steps.do_import.choose_import_path` has chosen it from the
            target schema's state, or None before.
        workers: How many processes compute an index's observations; 1 is this
            process, with no pool. `opus_import.cli` sets it from the resolved
            parallelism.
        worker_rows: The index rows one worker task covers.
        index_workers: How many tables finalization builds indexes on at once.
        capture: The record a pool worker keeps in place of database calls and log
            writes (`opus_import.deferred`), or None in the import's own process.
        importer: This process's row and lock as an importer drawing from the queue
            (`opus_import.import_processes.ImporterLock`), or None for a plain import.
        load_guard: What each chunk of the bundle being imported runs in its
            transaction (`opus_import.import_processes.BundleGuard`), or None outside a
            bundle.
        log_path: The run's information log, which an importer records in
            ``import_process``; None until `opus_import.cli` opens it.
        interrupts: How many interrupts (SIGINT) an importer has received: after the
            first it claims nothing new, and the second aborts its bundle.
    """

    args: argparse.Namespace
    logger: pdslogger.PdsLogger
    db: ImportDBSuper | None = None

    python_warning_list: list[str] = field(default_factory=list)
    logged_import_errors: set[str] = field(default_factory=set)
    logged_import_warnings: set[str] = field(default_factory=set)
    import_has_bad_data: bool = False
    bundle_has_errors: bool = False

    bundle_ids: BundleIds | None = None

    current_bundle_id: str | None = None
    current_index_row_number: int | None = None
    current_primary_filespec: str | None = None

    mult_fields: dict[str, MultFieldInfo] | None = None
    mult_table_cache: dict[str, MultFieldCache] = field(default_factory=dict)

    step_timings: dict[str, float] = field(default_factory=dict)

    import_path: str | None = None

    workers: int = DEFAULT_WORKERS
    worker_rows: int = DEFAULT_WORKER_ROWS
    index_workers: int = DEFAULT_INDEX_WORKERS
    capture: Capture | None = None
    importer: ImporterLock | None = None
    load_guard: BundleGuard | None = None
    log_path: str | None = None
    interrupts: int = 0

    log: ImportLog = field(init=False)

    def __post_init__(self) -> None:
        """Bind this context's `ImportLog`."""
        self.log = ImportLog(self)

    def mark_bad_data(self) -> None:
        """Record that the run, and the bundle it is importing, produced an error."""
        self.import_has_bad_data = True
        self.bundle_has_errors = True

    @contextlib.contextmanager
    def timed(self, step: str) -> Iterator[None]:
        """Time the enclosed block and record it in `step_timings` under a step name.

        The time is recorded when the block exits, whether it returns or raises, so a
        step that failed still shows how long it ran. A step timed twice in one run
        accumulates: its entry is the sum of the two.

        Parameters:
            step: The name the time is recorded under.

        Yields:
            Nothing; the block runs inside the timing.
        """
        started = time.perf_counter()
        try:
            yield
        finally:
            elapsed = time.perf_counter() - started
            self.step_timings[step] = self.step_timings.get(step, 0.0) + elapsed
