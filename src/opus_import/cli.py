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

from opus_config import get_config
from opus_import import import_util, importdb
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
        help="""Perform all import and finalization functions. This implies, in order:
                --drop-old-import-tables
                --import
                --copy-import-to-permanent-tables
                --drop-new-import-tables
                --finalize
             """,
    )

    parser.add_argument(
        '--do-all-import',
        action='store_true',
        default=False,
        help="""Perform all import functions. This implies, in order:
                --drop-old-import-tables
                --import
                --copy-import-to-permanent-tables
                --drop-new-import-tables
             """,
    )

    parser.add_argument(
        '--do-import-finalization',
        action='store_true',
        default=False,
        help="""Perform all import functions related to permanent tables. This implies, in order:
                --copy-import-to-permanent-tables
                --drop-new-import-tables
                --finalize
             """,
    )

    parser.add_argument(
        '--finalize',
        action='store_true',
        default=False,
        help="""Finish the database after its bundles are imported. This implies, in order:
                --create-indexes,
                the deletion of every copy of a duplicated OPUS ID but the last imported,
                --create-param-info
                --create-partables
                --create-table-names
                --create-cart
                --drop-cache-tables
                --analyze-permanent-tables
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
        '--drop-old-import-tables',
        action='store_true',
        default=False,
        help='Drop ALL the old import tables',
    )

    parser.add_argument(
        '--delete-import-bundles',
        action='store_true',
        default=False,
        help='Delete the given bundles from the import tables',
    )

    parser.add_argument(
        '--import',
        dest='do_import',
        action='store_true',
        default=False,
        help="""Perform an import of the specified bundles; implies
                --delete-import-bundles""",
    )
    parser.add_argument(
        '--leave-old-import-tables',
        action='store_true',
        default=False,
        help="""Leave the previous import tables and just add to them. Overrides
                --drop-old-import-tables.""",
    )
    parser.add_argument(
        '--import-ignore-errors',
        action='store_true',
        default=False,
        help='Copy to the permanent tables even with errors, and substitute made-up '
        'values where a real one cannot be determined -- an unknown target name '
        'becomes OTHER rather than dropping the observation. The result is '
        'wrong on purpose; for debugging',
    )
    parser.add_argument(
        '--import-suppress-mult-messages',
        action='store_true',
        default=False,
        help="Don't give messages about mult table maintenance",
    )
    parser.add_argument(
        '--import-report-missing-ring-geo',
        action='store_true',
        default=False,
        help="Report observations that should have ring_geo data but don't",
    )
    parser.add_argument(
        '--import-report-missing-sky-geo',
        action='store_true',
        default=False,
        help="Report observations that should have sky_geo data but don't",
    )
    parser.add_argument(
        '--import-report-inventory-mismatch',
        action='store_true',
        default=False,
        help='Report mismatches between inventory and surface geometry tables',
    )
    parser.add_argument(
        '--import-force-metadata-index',
        action='store_true',
        default=False,
        help='Force the use of metadata index files and fail if none available',
    )
    parser.add_argument(
        '--import-check-duplicate-id',
        action='store_true',
        default=False,
        help='Check for duplicate opus_id; needed for GOSSI,COUVIS,NH',
    )
    parser.add_argument(
        '--import-ignore-missing-images',
        action='store_true',
        default=False,
        help="Don't warn about missing browse images",
    )
    parser.add_argument(
        '--import-ignore-geo-mismatch',
        action='store_true',
        default=False,
        help="Don't warn about gridless column mismatch in geo files",
    )
    parser.add_argument(
        '--import-dont-use-row-files',
        action='store_true',
        default=False,
        help="""Do not use metadata row files to determine whether index and summary
                files should be included in the files table""",
    )
    parser.add_argument(
        '--import-report-empty-products',
        action='store_true',
        default=False,
        help='Report empty products during import',
    )
    parser.add_argument(
        '--import-fake-images',
        action='store_true',
        default=False,
        help='Fake the existence of browse images if real browse files are missing',
    )

    parser.add_argument(
        '--delete-permanent-import-bundles',
        action='store_true',
        default=False,
        help='Delete the bundles in the import tables from the permanent tables',
    )
    parser.add_argument(
        '--delete-permanent-bundles',
        action='store_true',
        default=False,
        help='Delete the given bundles from the permanent tables',
    )

    parser.add_argument(
        '--copy-import-to-permanent-tables',
        action='store_true',
        default=False,
        help="""Copy all temporary import tables to the permanent tables;
                implies --delete-permanent-import-bundles
             """,
    )
    parser.add_argument(
        '--drop-permanent-tables',
        action='store_true',
        default=False,
        help="""Delete ALL permanent tables; requires --scorched-earth.
                WARNING: THIS DELETES ALL EXISTING DATA""",
    )
    parser.add_argument(
        '--scorched-earth',
        action='store_true',
        default=False,
        help='You are serious about deleting all tables!',
    )

    parser.add_argument(
        '--drop-new-import-tables',
        action='store_true',
        default=False,
        help='Drop the new import tables after copying to permanent (if selected)',
    )

    parser.add_argument(
        '--analyze-permanent-tables',
        action='store_true',
        default=False,
        help='Analyze (recompute key distribution) the permanent tables',
    )

    # Import-related auxiliary functions

    parser.add_argument(
        '--create-param-info',
        action='store_true',
        default=False,
        help='Rebuild the param_info table beside the live one and swap it in',
    )
    parser.add_argument(
        '--create-partables',
        action='store_true',
        default=False,
        help='Rebuild the partables table beside the live one and swap it in',
    )
    parser.add_argument(
        '--create-table-names',
        action='store_true',
        default=False,
        help='Rebuild the table_names table beside the live one and swap it in',
    )
    parser.add_argument(
        '--update-mult-info',
        action='store_true',
        default=False,
        help='Update the details of preprogrammed mult tables',
    )

    # Functions other than main import

    parser.add_argument(
        '--drop-cache-tables',
        action='store_true',
        default=False,
        help='Drop the cache tables used by OPUS; also clears user_searches',
    )
    parser.add_argument(
        '--create-cart',
        action='store_true',
        default=False,
        help='Create the cart table used by OPUS',
    )

    parser.add_argument(
        '--validate-perm',
        action='store_true',
        default=False,
        help='Perform validation of the final permanent tables',
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
                Refuses, exiting non-zero, when the schema holds another version""",
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

    ``--do-it-all`` and ``--do-import-finalization`` finish a database, and do it through
    ``--finalize``, so each runs every step of the finalization group, the duplicate step
    among them, which has no option of its own.

    Parameters:
        args: The parsed arguments, changed in place.
    """
    if args.do_it_all:
        args.drop_old_import_tables = True
        args.do_import = True
        args.copy_import_to_permanent_tables = True
        args.drop_new_import_tables = True
        args.finalize = True

    if args.do_all_import:
        args.drop_old_import_tables = True
        args.do_import = True
        args.copy_import_to_permanent_tables = True
        args.drop_new_import_tables = True

    if args.do_import_finalization:
        args.copy_import_to_permanent_tables = True
        args.drop_new_import_tables = True
        args.finalize = True

    if args.finalize:
        args.create_indexes = True
        args.create_param_info = True
        args.create_partables = True
        args.create_table_names = True
        args.create_cart = True
        args.drop_cache_tables = True
        args.analyze_permanent_tables = True


def main() -> None:
    """Run the import steps requested on the command line.

    Every step is driven by its own option, apart from the duplicate step, which only
    ``--finalize`` runs; ``--finalize``, ``--do-it-all`` and their siblings turn several
    of them on, and the two aggregates that finish a database do it through
    ``--finalize``, so they run every step of its group. The database connection, the
    holdings directories and the log file locations come from the configuration file
    named by ``OPUS_CONFIG``, which is read only once the arguments parse, so ``--help``
    works without one.

    Raises:
        SystemExit: With a non-zero status, logged first, when the arguments are
            contradictory, a bundle descriptor is bad, the database connection fails,
            the observation import fails or is refused, ``--write-schema-version``
            refuses, an exception reaches the top-level handler, or -- unless
            ``--import-ignore-errors`` -- ``--create-indexes``, the duplicate step,
            ``--create-param-info``, ``--import-dictionary`` or ``--validate-perm``
            failed, after the invocation's other steps have run.
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

    ################################################################################
    #
    # THE MAIN IMPORT LOOP
    #
    ################################################################################

    if args.drop_permanent_tables != args.scorched_earth:
        logger.log('fatal', '--drop-permanent-tables and --scorched-earth must be used together')
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
                import_prefix=config.import_.table_temp_prefix,
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
        if (
            args.do_import
            and not args.drop_permanent_tables
            and not do_import.choose_import_path(ctx)
        ):
            sys.exit(-1)

        # This MUST be done before the permanent tables are created, because there
        # could be entries in the cart table that point at the permanent
        # tables, and import could delete entries out of the permanent tables
        # causing a foreign key violation.
        # Note, however, that do_import_steps() might actually delete ALL permanent
        # tables with --scorched-earth, which means our effort here will be wasted,
        # so don't bother in that case.
        if (args.drop_cache_tables or args.create_cart) and not args.drop_permanent_tables:
            logger.open(
                'Cleaning up OPUS/Django tables',
                limits={'info': args.log_info_limit, 'debug': args.log_debug_limit},
            )

            if args.create_cart:
                with ctx.timed('create_cart'):
                    do_cart.create_cart(ctx)
            if args.drop_cache_tables:
                with ctx.timed('drop_cache_tables'):
                    do_django.drop_cache_tables(ctx)

            logger.close()

        if not do_import.do_import_steps(ctx):
            sys.exit(-1)

        # The finishing steps that failed in this invocation. Any failure keeps it from
        # marking the schema ready, and makes it exit with failure once its other steps
        # have run, so opus_import_all, which runs each finishing step as its own
        # invocation, stops before its --write-schema-version. --import-ignore-errors
        # overrides both, for a debugging run.
        failed_steps: list[str] = []

        # The finalization group's sequence, which later steps extend in place: the keys,
        # then the duplicate step, then the auxiliary tables, then ANALYZE.
        if args.create_indexes:
            logger.open(
                'Creating secondary keys',
                limits={'info': args.log_info_limit, 'debug': args.log_debug_limit},
            )
            with ctx.timed('create_indexes'):
                if not do_indexes.create_indexes(ctx):
                    failed_steps.append('--create-indexes')
            logger.close()

        if args.finalize:
            logger.open(
                'Deleting duplicate OPUS IDs',
                limits={'info': args.log_info_limit, 'debug': args.log_debug_limit},
            )
            with ctx.timed('duplicate_step'):
                if not do_duplicate_ids.delete_duplicate_opus_ids(ctx):
                    failed_steps.append('the duplicate step of --finalize')
            logger.close()

        # This MUST be done after the permanent tables are created, since they
        # are used to determine what goes into the param_info table.

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

        # After the auxiliary tables, so that the statistics count every table's rows.
        if args.analyze_permanent_tables:
            import_util.log_info(ctx, 'Analyzing all permanent tables')
            with ctx.timed('analyze_permanent_tables'):
                do_import_tables.analyze_all_tables(ctx, 'perm')

        if args.update_mult_info:
            logger.open(
                'Updating preprogrammed mult tables',
                limits={'info': args.log_info_limit, 'debug': args.log_debug_limit},
            )

            with ctx.timed('update_mult_info'):
                do_update_mult_info.update_mult_info(ctx)

            logger.close()

        if args.validate_perm:
            with ctx.timed('validate_perm'):
                if not do_validate.do_validate(ctx, 'perm'):
                    failed_steps.append('--validate-perm')

        if args.create_cart and ctx.try_cart_later:
            logger.open(
                'Trying to create cart table a second time',
                limits={'info': args.log_info_limit, 'debug': args.log_debug_limit},
            )

            with ctx.timed('create_cart'):
                do_cart.create_cart(ctx)

            logger.close()

        if args.import_dictionary:
            logger.open(
                'Importing dictionary',
                limits={'info': args.log_info_limit, 'debug': args.log_debug_limit},
            )
            with ctx.timed('import_dictionary'):
                if not do_dictionary.do_dictionary(ctx):
                    failed_steps.append('--import-dictionary')
            logger.close()

        failure_refuses = len(failed_steps) > 0 and not args.import_ignore_errors

        # Last, after validation, because the row is what makes the schema servable.
        if args.write_schema_version:
            if failure_refuses:
                import_util.log_error(
                    ctx,
                    f'{", ".join(failed_steps)} failed, so the schema is not marked ready; '
                    '--import-ignore-errors marks it ready regardless',
                )
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
