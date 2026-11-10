"""Command line for the OPUS import pipeline.

The pipeline is run as ``python -m opus_import``; ``--help`` lists every option. The
options are grouped into database selection, the import steps to perform (each maps to
one ``opus_import.steps`` module), bundle selection, and logging.
"""

from __future__ import annotations

import argparse
import atexit
import cProfile
import io
import json
import logging
import os
import pstats
import sys
import time
import traceback
import warnings
from pathlib import Path
from typing import TYPE_CHECKING

import pdslogger
from pdsfile import Pds3File, Pds4File

from opus_config import MAX_WORKERS, ConfigError, get_config, resolve_parallelism
from opus_import import bundle_registry, import_util, importdb
from opus_import.config_data import GROUP_FORM_TYPES
from opus_import.context import ImportContext
from opus_import.steps import (
    do_cart,
    do_dictionary,
    do_django,
    do_duplicate_ids,
    do_import,
    do_import_tables,
    do_indexes,
    do_param_info,
    do_partables,
    do_schema_version,
    do_table_names,
    do_update_mult_info,
    do_validate,
)

if TYPE_CHECKING:
    from typing import TextIO

    from opus_import.importdb.super import WarningHandler

LOGNAME = 'opus_import.main'


def _worker_count(text: str) -> int | str:
    """Parse ``--workers``: a whole number of at least 1, or ``max``.

    Parameters:
        text: The argument as given.

    Returns:
        The number, or `opus_config.MAX_WORKERS`.

    Raises:
        argparse.ArgumentTypeError: If the argument is neither.
    """
    if text == MAX_WORKERS:
        return text
    try:
        count = int(text)
    except ValueError:
        count = 0
    if count < 1:
        raise argparse.ArgumentTypeError(
            f'must be a whole number of at least 1 or "{MAX_WORKERS}", not {text!r}'
        )
    return count


def _make_warning_handler(ctx: ImportContext) -> WarningHandler:
    """Return a `warnings.showwarning` that collects warnings on the context.

    Parameters:
        ctx: The context to collect the warnings on.

    Returns:
        A handler with `warnings.showwarning`'s signature. It reads the list off
        the context on every call rather than closing over it, because reporting
        the accumulated warnings replaces the list with a fresh one.
    """

    def handler(
        message: Warning | str,
        category: type[Warning],
        filename: str,
        lineno: int,
        file: TextIO | None,
        line: str | None,
    ) -> None:
        """Record one warning's text on the context, discarding everything else.

        Parameters:
            message: The warning, or its text.
            category: The warning class. Not recorded.
            filename: Where the warning was raised. Not recorded.
            lineno: The line it was raised on. Not recorded.
            file: Where the standard handler would have written it. Unused.
            line: The source line, if the caller supplied one. Not recorded.
        """
        ctx.python_warning_list.append(str(message))

    return handler


def _write_step_timings(path: Path, ctx: ImportContext, started: float) -> None:
    """Write the run's step timings, plus its total, as one JSON object.

    Parameters:
        path: The file to write. Its directory must exist.
        ctx: The run's context, whose `ImportContext.step_timings` are written.
        started: The `time.perf_counter` reading the run started at, from which the
            ``total`` entry is computed.
    """
    timings = {**ctx.step_timings, 'total': time.perf_counter() - started}
    path.write_text(json.dumps(timings, indent=1) + '\n', encoding='utf-8')


def _create_argument_parser() -> argparse.ArgumentParser:
    """Build the pipeline's argument parser.

    Returns:
        A parser whose ``prog`` is ``opus_import``, matching the way the pipeline is
        invoked (``python -m opus_import``).
    """
    parser = argparse.ArgumentParser(prog='opus_import', description='OPUS Import Pipeline')

    # Database arguments
    parser.add_argument(
        '--read-only',
        action='store_true',
        default=False,
        help="Don't modify or create any SQL table",
    )
    parser.add_argument(
        '--override-db-schema',
        type=str,
        default=None,
        help='Override the database schema specified in the configuration file',
    )
    parser.add_argument(
        '--override-pds3-data-dir',
        type=str,
        default=None,
        help='Override the PDS3 holdings directory specified in the configuration '
        'file (.../holdings)',
    )
    parser.add_argument(
        '--override-pds4-data-dir',
        type=str,
        default=None,
        help='Override the PDS4 holdings directory specified in the configuration '
        'file (.../pds4-holdings)',
    )
    parser.add_argument(
        '--dont-use-shelves-only',
        action='store_true',
        default=False,
        help='Look at actual pdsdata volumes/bundles instead of using shelve files',
    )

    # What to actually do - main import
    parser.add_argument(
        '--do-it-all',
        action='store_true',
        default=False,
        help="""Import the given bundles and finalize the schema in one invocation. This
                implies, in order:
                --import
                --finalize
             """,
    )

    parser.add_argument(
        '--finalize',
        action='store_true',
        default=False,
        help="""Finish the database after its bundles are imported; refused while any
                bundle in the bundle registry is not done. This implies, in order:
                --create-indexes,
                the deletion of every copy of a duplicated OPUS ID but the last imported,
                --create-param-info
                --create-partables
                --create-table-names
                --create-cart
                --reset-search-tables
                --analyze-tables
             """,
    )

    parser.add_argument(
        '--create-indexes',
        action='store_true',
        default=False,
        help="""Add every key the table schemas declare and an observation or mult table
                lacks, which a fresh import leaves for finalization""",
    )

    parser.add_argument(
        '--import',
        dest='do_import',
        action='store_true',
        default=False,
        help="Import the given bundles; the target schema's state chooses a fresh import "
        'or an append',
    )
    parser.add_argument(
        '--workers',
        type=_worker_count,
        default=None,
        metavar='N',
        help='Compute each index\'s observations in N processes, or "max" for the ceiling '
        '([import] cpus and cpu_fraction); replaces [import] workers',
    )
    parser.add_argument(
        '--ignore-errors',
        action='store_true',
        default=False,
        help='Mark a bundle done even when it logs errors, so that --finalize and '
        '--write-schema-version accept it, and substitute made-up values where a real one '
        'cannot be determined -- an unknown target name becomes OTHER rather than dropping '
        'the observation. The result is wrong on purpose; for debugging',
    )
    parser.add_argument(
        '--suppress-mult-messages',
        action='store_true',
        default=False,
        help="Don't give messages about mult table maintenance",
    )
    parser.add_argument(
        '--report-missing-ring-geo',
        action='store_true',
        default=False,
        help="Report observations that should have ring_geo data but don't",
    )
    parser.add_argument(
        '--report-missing-sky-geo',
        action='store_true',
        default=False,
        help="Report observations that should have sky_geo data but don't",
    )
    parser.add_argument(
        '--report-inventory-mismatch',
        action='store_true',
        default=False,
        help='Report mismatches between inventory and surface geometry tables',
    )
    parser.add_argument(
        '--force-metadata-index',
        action='store_true',
        default=False,
        help='Force the use of metadata index files and fail if none available',
    )
    parser.add_argument(
        '--ignore-missing-images',
        action='store_true',
        default=False,
        help="Don't warn about missing browse images",
    )
    parser.add_argument(
        '--ignore-geo-mismatch',
        action='store_true',
        default=False,
        help="Don't warn about gridless column mismatch in geo files",
    )
    parser.add_argument(
        '--no-row-files',
        action='store_true',
        default=False,
        help="""Do not use metadata row files to determine whether index and summary
                files should be included in the files table""",
    )
    parser.add_argument(
        '--report-empty-products',
        action='store_true',
        default=False,
        help='Report empty products during import',
    )
    parser.add_argument(
        '--fake-images',
        action='store_true',
        default=False,
        help='Fake the existence of browse images if real browse files are missing',
    )

    parser.add_argument(
        '--delete-bundles',
        action='store_true',
        default=False,
        help="Delete the given bundles' rows from every observation table, and their bundle "
        'registry rows',
    )
    parser.add_argument(
        '--scorched-earth',
        action='store_true',
        default=False,
        help="Drop every table the import creates in the schema -- all but Django's own -- "
        'before any other step; requires --yes. WARNING: THIS DELETES ALL EXISTING DATA',
    )
    parser.add_argument(
        '--yes',
        action='store_true',
        default=False,
        help='Confirm --scorched-earth; refused without it',
    )

    parser.add_argument(
        '--analyze-tables',
        action='store_true',
        default=False,
        help='Analyze every observation and mult table (recompute its key distribution)',
    )

    # Import-related auxiliary functions

    parser.add_argument(
        '--create-param-info',
        action='store_true',
        default=False,
        help='Rebuild the param_info table from the table schemas and swap it in atomically',
    )
    parser.add_argument(
        '--create-partables',
        action='store_true',
        default=False,
        help="Rebuild the partables table from the code's mission and instrument lists and "
        'the imported mult ids, and swap it in atomically',
    )
    parser.add_argument(
        '--create-table-names',
        action='store_true',
        default=False,
        help="Rebuild the table_names table from the code's list of categories and the "
        'imported tables, and swap it in atomically',
    )
    parser.add_argument(
        '--update-mult-info',
        action='store_true',
        default=False,
        help='Update the details of preprogrammed mult tables',
    )

    # Functions other than main import

    parser.add_argument(
        '--reset-search-tables',
        action='store_true',
        default=False,
        help="""Re-create the web application's search tables, user_searches and
                search_results, empty, and flush its cache""",
    )
    parser.add_argument(
        '--create-cart',
        action='store_true',
        default=False,
        help='Create the cart table used by OPUS',
    )

    parser.add_argument(
        '--validate',
        action='store_true',
        default=False,
        help='Validate the imported tables',
    )

    parser.add_argument(
        '--import-dictionary',
        action='store_true',
        default=False,
        help='Rebuild the definitions and contexts tables beside the live ones and swap them in',
    )

    parser.add_argument(
        '--write-schema-version',
        action='store_true',
        default=False,
        help="""Mark the schema finished under this release's schema version, the last
                step of every sequence that finishes a database; implied by nothing.
                Refuses, exiting non-zero, when the schema holds another version or any
                bundle in the bundle registry is not done""",
    )

    # Arguments about bundle selection
    parser.add_argument(
        'bundles',
        type=str,
        default=None,
        nargs='*',
        metavar='VOL_DESC,VOL_DESC...',
        help="""Comma-separated list of bundle descriptors (COISS_1xxx,COVIMS_0089)
                to import""",
    )

    parser.add_argument(
        '--exclude-bundles',
        type=str,
        default=None,
        metavar='VOL_NAME,VOL_NAME...',
        help="""Comma-separated list of bundle names (COVIMS_0089,COISS_2111)
                to exclude from importing""",
    )

    # Arguments about logging
    parser.add_argument(
        '--no-log-pdsfile',
        action='store_true',
        default=False,
        help="""Don't log output of pdsfile actions""",
    )
    parser.add_argument(
        '--log-sql', action='store_true', default=False, help='Also log all SQL commands'
    )
    parser.add_argument(
        '--log-debug-limit', type=int, default=-1, help='Limit the number of debug messages'
    )
    parser.add_argument(
        '--log-info-limit', type=int, default=-1, help='Limit the number of info messages'
    )
    parser.add_argument(
        '--log-suppress-traceback',
        action='store_true',
        default=False,
        help='Omit tracebacks from exception reports',
    )

    parser.add_argument(
        '--profile', action='store_true', default=False, help='Do performance profiling'
    )
    parser.add_argument(
        '--timing-json',
        type=Path,
        default=None,
        metavar='PATH',
        help='When the run exits, write the wall-clock seconds of each step it ran to '
        'this file, as one JSON object keyed by step name',
    )

    return parser


def expand_aggregate_options(args: argparse.Namespace) -> None:
    """Turn on the steps each aggregate option given stands for.

    ``--do-it-all`` imports and then finalizes, through ``--finalize``, so it runs every
    step of the finalization group, the duplicate step among them, which has no option of
    its own.

    Parameters:
        args: The parsed arguments, changed in place.
    """
    if args.do_it_all:
        args.do_import = True
        args.finalize = True

    if args.finalize:
        args.create_indexes = True
        args.create_param_info = True
        args.create_partables = True
        args.create_table_names = True
        args.create_cart = True
        args.reset_search_tables = True
        args.analyze_tables = True


def _registry_finished(ctx: ImportContext, step: str) -> bool:
    """Return whether every bundle in the bundle registry is done, refusing a step if not.

    Parameters:
        ctx: The import run's context, for the open database and the logger.
        step: The option refused, as the message names it.

    Returns:
        True when the registry is absent or every bundle in it is ``done``; otherwise
        False, after a fatal message naming every other bundle with its state.
    """
    unfinished = bundle_registry.unfinished_bundles(ctx)
    if not unfinished:
        return True
    ctx.logger.log(
        'fatal',
        f'{step} refuses to run while bundles in the bundle registry are not done: '
        f'{bundle_registry.unfinished_message(unfinished)}. Import them again, or remove '
        'them with --delete-bundles',
    )
    return False


def main() -> None:
    """Run the import steps requested on the command line.

    Every step is driven by its own option, apart from the duplicate step, which only
    ``--finalize`` runs; ``--finalize`` and ``--do-it-all`` turn several of them on, and
    ``--do-it-all`` finalizes through ``--finalize``, so it runs every step of its group.
    The database connection, the holdings directories and the log file locations come
    from the configuration file named by ``OPUS_CONFIG``, which is read only once the
    arguments parse, so ``--help`` works without one.

    Raises:
        SystemExit: With a non-zero status, logged first, when the arguments are
            contradictory, a bundle descriptor is bad, the database connection fails,
            the observation import fails or is refused, ``--finalize`` or
            ``--write-schema-version`` refuses, an exception reaches the top-level
            handler, or -- unless ``--ignore-errors`` -- ``--create-indexes``, the
            duplicate step, ``--create-param-info``, ``--import-dictionary`` or
            ``--validate`` failed, after the invocation's other steps have run.
            **A non-zero status means the run stopped, not that a zero status means it
            was clean:** other steps report failure through the log and leave the
            status zero. Read ``ERRORS.log`` to judge whether a run was clean.
    """
    command_list = sys.argv[1:]

    parser = _create_argument_parser()
    args = parser.parse_args(command_list)
    if args.timing_json is not None and not args.timing_json.parent.is_dir():
        # The file is written at exit, too late for its failure to change the exit status.
        parser.error(f'--timing-json: the directory {args.timing_json.parent} does not exist')

    expand_aggregate_options(args)

    ################################################################################
    # LOGGING INITIALIZATION
    ################################################################################

    # Reading the settings is deferred until the arguments have parsed so that --help
    # works without a configuration file.
    config = get_config()

    logger = pdslogger.PdsLogger(
        LOGNAME, limits={'info': args.log_info_limit, 'debug': args.log_debug_limit}
    )
    ctx = ImportContext(args=args, logger=logger)
    if args.timing_json is not None:
        # Registered rather than written in a finally block, because the run leaves
        # through sys.exit from several places; atexit runs on every one of them.
        atexit.register(_write_step_timings, args.timing_json, ctx, time.perf_counter())

    info_logfile = os.path.abspath(config.import_.log_file)
    debug_logfile = os.path.abspath(config.import_.debug_log_file)

    info_handler = pdslogger.file_handler(info_logfile, level=logging.INFO, rotation='ymdhms')
    debug_handler = pdslogger.file_handler(debug_logfile, level=logging.DEBUG, rotation='ymdhms')

    logger.add_handler(info_handler)
    logger.add_handler(debug_handler)
    logger.add_handler(pdslogger.stdout_handler)

    handler = pdslogger.warning_handler(config.paths.import_log_dir, rotation='none')
    logger.add_handler(handler)

    handler = pdslogger.error_handler(config.paths.import_log_dir, rotation='none')
    logger.add_handler(handler)

    warnings.showwarning = _make_warning_handler(ctx)

    # First, so the log says how much of the computer the run may use before anything
    # uses it.
    try:
        parallelism = resolve_parallelism(config.import_, args.workers)
    except ConfigError as e:
        logger.log('fatal', str(e))
        sys.exit(-1)
    logger.log('info', parallelism.describe())
    if parallelism.cores > parallelism.detected_cores:
        logger.log(
            'info',
            f'[import] cpus {parallelism.cores} is more than the {parallelism.detected_cores} '
            'cores detected; the stated count is used',
        )
    ctx.workers = parallelism.workers
    ctx.index_workers = parallelism.index_workers
    ctx.worker_rows = config.import_.worker_rows

    ################################################################################
    #
    # THE MAIN IMPORT LOOP
    #
    ################################################################################

    if args.scorched_earth and not args.yes:
        logger.log(
            'fatal', '--scorched-earth drops every OPUS table in the schema; give --yes to confirm'
        )
        sys.exit(-1)
    if args.yes and not args.scorched_earth:
        logger.log('fatal', '--yes confirms --scorched-earth and is refused without it')
        sys.exit(-1)

    our_schema_name = config.database.schema
    if args.override_db_schema:
        our_schema_name = args.override_db_schema

    try:  # Top-level exception handling so we always log what's going on
        # Start the profiling
        if args.profile:
            pr = cProfile.Profile()
            pr.enable()

        logger.open(
            'Performing all requested import functions',
            limits={'info': args.log_info_limit, 'debug': args.log_debug_limit},
        )

        if not args.dont_use_shelves_only:
            Pds3File.use_shelves_only()
            Pds4File.use_shelves_only()
            Pds3File.require_shelves(True)
            # PDS4 asks the shelves first and falls back to the file system when no
            # shelf covers a path. The production holdings have no PDS4 shelves at all,
            # so today every PDS4 existence check takes that fallback and this line
            # costs nothing; a tree that does have them -- one a test builds, or the
            # production tree once it grows them -- gets the shelf-answered existence
            # PDS3 has. Requiring shelves turns a missing one into an exception, so the
            # line below waits until every PDS4 bundle in the holdings has one.
            # Pds4File.require_shelves(True)
        if args.override_pds3_data_dir:
            Pds3File.preload(args.override_pds3_data_dir)
        else:
            Pds3File.preload(config.paths.pds3_holdings)
        if args.override_pds4_data_dir:
            Pds4File.preload(args.override_pds4_data_dir)
        else:
            Pds4File.preload(config.paths.pds4_holdings)

        # We do this after the preload because we don't want to see all the preload
        # debug messages.
        if not args.no_log_pdsfile:
            Pds3File.set_logger(import_util.NoDupLogger(logger))
            Pds4File.set_logger(import_util.NoDupLogger(logger))

        try:
            ctx.db = importdb.get_db(
                config.database.brand,
                config.database.host,
                config.database.database,
                our_schema_name,
                config.database.user,
                config.database.password,
                mult_form_types=GROUP_FORM_TYPES,
                logger=logger,
                read_only=args.read_only,
                bulk_load=config.import_.bulk_load,
                scratch_dir=config.import_.scratch_dir,
                transaction_rows=config.import_.transaction_rows,
            )
        except importdb.ImportDBError:
            sys.exit(-1)

        ctx.db.log_sql = args.log_sql

        # The path an import takes is chosen before anything else writes, so an import
        # refused for an interrupted finalization changes nothing. An invocation that
        # erases the schema first chooses after the erase, in do_import_steps.
        if args.do_import and not args.scorched_earth and not do_import.choose_import_path(ctx):
            sys.exit(-1)

        if not do_import.do_import_steps(ctx):
            sys.exit(-1)

        # Before the first finalization step, so a refused finalization changes nothing;
        # after the bundles this invocation imports or deletes, which can finish the
        # registry.
        if args.finalize and not _registry_finished(ctx, '--finalize'):
            sys.exit(-1)

        # The finishing steps that failed in this invocation. Any failure keeps it from
        # marking the schema ready, and makes it exit with failure once its other steps
        # have run, so opus_import_all, which runs each finishing step as its own
        # invocation, stops before its --write-schema-version. --ignore-errors overrides
        # both, for a debugging run.
        failed_steps: list[str] = []

        # The finalization group's sequence, which later steps extend in place: the keys,
        # then the duplicate step, then the auxiliary tables, the cart and the cache
        # tables, then ANALYZE.
        if args.create_indexes:
            logger.open(
                'Creating secondary keys',
                limits={'info': args.log_info_limit, 'debug': args.log_debug_limit},
            )
            with ctx.timed('create_indexes'):
                if not do_indexes.create_indexes(ctx):
                    failed_steps.append('--create-indexes')
            logger.close()

        # The duplicate step deletes by obs_general_id, which only the keys just built
        # index, so it waits for a run whose key builds succeed.
        if args.finalize and '--create-indexes' not in failed_steps:
            logger.open(
                'Deleting duplicate OPUS IDs',
                limits={'info': args.log_info_limit, 'debug': args.log_debug_limit},
            )
            with ctx.timed('duplicate_step'):
                if not do_duplicate_ids.delete_duplicate_opus_ids(ctx):
                    failed_steps.append('the duplicate step of --finalize')
            logger.close()

        # After the import, since the imported tables are what determine what goes into
        # the auxiliary tables.
        if args.create_param_info or args.create_partables or args.create_table_names:
            logger.open(
                'Creating auxiliary tables',
                limits={'info': args.log_info_limit, 'debug': args.log_debug_limit},
            )

            if args.create_param_info:
                with ctx.timed('create_param_info'):
                    if not do_param_info.do_param_info(ctx):
                        failed_steps.append('--create-param-info')
            if args.create_partables:
                with ctx.timed('create_partables'):
                    do_partables.do_partables(ctx)
            if args.create_table_names:
                with ctx.timed('create_table_names'):
                    do_table_names.do_table_names(ctx)

            logger.close()

        # After the import, since the cart's foreign key needs obs_general.
        if args.create_cart or args.reset_search_tables:
            logger.open(
                'Cleaning up OPUS/Django tables',
                limits={'info': args.log_info_limit, 'debug': args.log_debug_limit},
            )
            if args.create_cart:
                with ctx.timed('create_cart'):
                    do_cart.create_cart(ctx)
            if args.reset_search_tables:
                with ctx.timed('reset_search_tables'):
                    do_django.reset_search_tables(ctx)
            logger.close()

        # After the auxiliary tables, so that the statistics count every table's rows.
        if args.analyze_tables:
            import_util.log_info(ctx, 'Analyzing all tables')
            with ctx.timed('analyze_tables'):
                do_import_tables.analyze_all_tables(ctx)

        if args.update_mult_info:
            logger.open(
                'Updating preprogrammed mult tables',
                limits={'info': args.log_info_limit, 'debug': args.log_debug_limit},
            )

            with ctx.timed('update_mult_info'):
                do_update_mult_info.update_mult_info(ctx)

            logger.close()

        if args.validate:
            with ctx.timed('validate'):
                if not do_validate.do_validate(ctx):
                    failed_steps.append('--validate')

        if args.import_dictionary:
            logger.open(
                'Importing dictionary',
                limits={'info': args.log_info_limit, 'debug': args.log_debug_limit},
            )
            with ctx.timed('import_dictionary'):
                if not do_dictionary.do_dictionary(ctx):
                    failed_steps.append('--import-dictionary')
            logger.close()

        failure_refuses = len(failed_steps) > 0 and not args.ignore_errors

        # Last, after validation, because the row is what makes the schema servable.
        if args.write_schema_version:
            if failure_refuses:
                import_util.log_error(
                    ctx,
                    f'{", ".join(failed_steps)} failed, so the schema is not marked ready; '
                    '--ignore-errors marks it ready regardless',
                )
                sys.exit(-1)
            if not _registry_finished(ctx, '--write-schema-version'):
                sys.exit(-1)
            with ctx.timed('write_schema_version'):
                written = do_schema_version.write_schema_version(ctx)
            if not written:
                sys.exit(-1)

        if args.profile:
            pr.disable()
            s = io.StringIO()
            sortby = 'cumulative'
            ps = pstats.Stats(pr, stream=s).strip_dirs().sort_stats(sortby)
            ps.print_stats()
            ps.print_callers()
            logger.info('Profile results:\n%s', s.getvalue())

        logger.close()
        if failure_refuses:
            sys.exit(-1)

    # This top-level handler logs the import failures that reach it, including an
    # ImportDBError raised from the pipeline. It catches Exception rather than
    # BaseException deliberately: SystemExit and KeyboardInterrupt mean the run was
    # stopped on purpose, which is not an import failure to log and report. That also
    # means a failure which has already called sys.exit does not arrive here: the
    # get_db() error above exits directly, so this handler never sees it.
    except Exception:
        msg = 'Import failed with exception'
        if not args.log_suppress_traceback:
            msg += ':\n' + traceback.format_exc()
        logger.log('fatal', msg)
        sys.exit(-1)
