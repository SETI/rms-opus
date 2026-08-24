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

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import argparse

    import pdslogger

    from opus_import.importdb.super import ImportDBSuper


class ImportLog:
    """The import pipeline's log, bound to one `ImportContext`.

    Every message is prefixed with the bundle, index row and primary filespec the context
    is currently on, so a message read out of a log file names the observation that
    produced it. The ``nonrepeating_`` methods log a given message only once per run,
    which is what keeps a fault shared by every row of an index out of the log a hundred
    thousand times.

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
                ret += ' index row '+str(ctx.current_index_row_number)
            if ctx.current_primary_filespec is not None:
                ret += f' "{ctx.current_primary_filespec}"'
        if ret != '':
            ret = '[' + ret + '] '
        return ret

    def error(self, msg: str, *args: Any) -> None:
        """Log a message at error level and mark the import as having produced bad data.

        Parameters:
            msg: The message, position-prefixed before it is logged.
            args: Further arguments passed to the underlying logger.
        """
        self._ctx.logger.log('error', self._position()+msg, *args)
        self._ctx.import_has_bad_data = True

    def warning(self, msg: str, *args: Any) -> None:
        """Log a message at warning level.

        Parameters:
            msg: The message, position-prefixed before it is logged.
            args: Further arguments passed to the underlying logger.
        """
        self._ctx.logger.log('warning', self._position()+msg, *args)

    def info(self, msg: str, *args: Any) -> None:
        """Log a message at info level.

        Parameters:
            msg: The message, position-prefixed before it is logged.
            args: Further arguments passed to the underlying logger.
        """
        self._ctx.logger.log('info', self._position()+msg, *args)

    def debug(self, msg: str, *args: Any) -> None:
        """Log a message at debug level.

        Parameters:
            msg: The message, position-prefixed before it is logged.
            args: Further arguments passed to the underlying logger.
        """
        self._ctx.logger.log('debug', self._position()+msg, *args)

    def nonrepeating_error(self, msg: str) -> None:
        """Log an error the first time this run produces it, and ignore it after that.

        Parameters:
            msg: The message. Two calls with equal messages log once, even though their
                position prefixes differ.
        """
        if msg not in self._ctx.logged_import_errors:
            self._ctx.logged_import_errors.append(msg)
            self.error(msg)

    def nonrepeating_warning(self, msg: str) -> None:
        """Log a warning the first time this run produces it, and ignore it after that.

        Parameters:
            msg: The message. Two calls with equal messages log once, even though their
                position prefixes differ.
        """
        if msg not in self._ctx.logged_import_warnings:
            self._ctx.logged_import_warnings.append(msg)
            self.warning(msg)

    def unknown_target_name(self, target_name: str) -> None:
        """Report a TARGET_NAME the target tables do not describe.

        Parameters:
            target_name: The name read from the PDS label.
        """
        self.nonrepeating_error(f'Unknown TARGET_NAME "{target_name}" - edit '
                                'config_targets/target_name_info.py')


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
            run aborts on it unless ``--import-ignore-errors`` was given. Every `log`
            error sets it, and a few sites outside `log` set it directly; but it is not
            a complete record of the run's errors, because several steps log failures
            straight to `logger` and leave it alone.
        max_table_id_cache: The highest row id seen per table, so ids can be handed out
            without querying the database for each one. Cleared for each bundle.
        current_bundle_id: The bundle being imported, or None outside a bundle.
        current_index_row_number: The 1-based index row being imported, or None.
        current_primary_filespec: The primary filespec of the observation being imported,
            or None. It is unknown for part of each row, because some bundles take it
            from the supplemental index.
        try_cart_later: True when creating the cart table failed because the permanent
            tables did not exist yet, so it is worth one more attempt after the import.
        mult_table_cache: Each mult table read or created during this bundle, keyed by
            table name. Cleared for each bundle.
        created_import_mult_tables: The import mult tables created empty and not yet
            written out. A table in here has no rows worth reading, so the permanent
            table is read instead. Cleared once per run, not once per bundle.
        modified_mult_tables: The mult tables this bundle added values to, and which
            therefore have to be written back. Cleared for each bundle.
    """

    args: argparse.Namespace
    logger: pdslogger.PdsLogger
    db: ImportDBSuper | None = None

    python_warning_list: list[str] = field(default_factory=list)
    logged_import_errors: list[str] = field(default_factory=list)
    logged_import_warnings: list[str] = field(default_factory=list)
    import_has_bad_data: bool = False

    max_table_id_cache: dict[str, int] = field(default_factory=dict)

    current_bundle_id: str | None = None
    current_index_row_number: int | None = None
    current_primary_filespec: str | None = None

    try_cart_later: bool = False

    mult_table_cache: dict[str, list[dict[str, Any]]] = field(default_factory=dict)
    created_import_mult_tables: set[str] = field(default_factory=set)
    modified_mult_tables: set[str] = field(default_factory=set)

    log: ImportLog = field(init=False)

    def __post_init__(self) -> None:
        """Bind this context's `ImportLog`."""
        self.log = ImportLog(self)
