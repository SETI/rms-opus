"""Command line for the OPUS import pipeline.

The pipeline is run as ``python -m opus_import``; ``--help`` lists every option. The
options are grouped into database selection, the import steps to perform (each maps to
one ``opus_import.steps`` module), bundle selection, and logging.
"""

from __future__ import annotations

import argparse
import cProfile
import io
import logging
import os
import pstats
import sys
import traceback
import warnings
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
    do_import,
    do_param_info,
    do_partables,
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
        help="""Perform all import and aux functions. This implies, in order:
                --drop-old-import-tables
                --import
                --copy-import-to-permanent-tables
                --drop-new-import-tables
                --analyze-permanent-tables
                --create-param-info
                --create-partables
                --create-table-names
                --create-cart
                --drop-cache-tables
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
                --analyze-permanent-tables
                --create-param-info
                --create-partables
                --create-table-names
                --create-cart
                --drop-cache-tables
             """,
    )

    parser.add_argument(
        '--cleanup-aux-tables',
        action='store_true',
        default=False,
        help="""Create or clean up auxiliary tables. This implies:
                --create-param-info
                --create-partables
                --create-table-names
                --create-cart
                --drop-cache-tables
             """,
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
        help='Create the param_info table; includes copying to permanent table',
    )
    parser.add_argument(
        '--create-partables',
        action='store_true',
        default=False,
        help='Create the partables table; includes copying to permanent table',
    )
    parser.add_argument(
        '--create-table-names',
        action='store_true',
        default=False,
        help='Create the table_names table; includes copying to permanent table',
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
        help='Import the dictionary and contexts from scratch',
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

    return parser


def main() -> None:
    """Run the import steps requested on the command line.

    Every step is driven by its own option; ``--do-it-all`` and its siblings simply turn
    several of them on. The database connection, the holdings directories and the log
    file locations come from the configuration file named by ``OPUS_CONFIG``, which is
    read only once the arguments parse, so ``--help`` works without one.

    Raises:
        SystemExit: With a non-zero status, logged first, when the arguments are
            contradictory, a bundle descriptor is bad, the database connection fails,
            the observation import fails, or an exception reaches the top-level handler.
            **A non-zero status means the run stopped, not that a zero status means it
            was clean:** several steps report failure through the log and leave the
            status zero, a failed dictionary import and every validation error among
            them. Read ``ERRORS.log`` to judge whether a run was clean.
    """
    command_list = sys.argv[1:]

    args = _create_argument_parser().parse_args(command_list)

    if args.do_it_all:
        args.drop_old_import_tables = True
        args.do_import = True
        args.copy_import_to_permanent_tables = True
        args.drop_new_import_tables = True
        args.analyze_permanent_tables = True
        args.create_param_info = True
        args.create_partables = True
        args.create_table_names = True
        args.create_cart = True
        args.drop_cache_tables = True

    if args.do_all_import:
        args.drop_old_import_tables = True
        args.do_import = True
        args.copy_import_to_permanent_tables = True
        args.drop_new_import_tables = True

    if args.do_import_finalization:
        args.copy_import_to_permanent_tables = True
        args.drop_new_import_tables = True
        args.analyze_permanent_tables = True
        args.create_param_info = True
        args.create_partables = True
        args.create_table_names = True
        args.create_cart = True
        args.drop_cache_tables = True

    if args.cleanup_aux_tables:
        args.create_param_info = True
        args.create_partables = True
        args.create_table_names = True
        args.create_cart = True
        args.drop_cache_tables = True

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
            )
        except importdb.ImportDBError:
            sys.exit(-1)

        ctx.db.log_sql = args.log_sql

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
                do_cart.create_cart(ctx)
            if args.drop_cache_tables:
                do_django.drop_cache_tables(ctx)

            logger.close()

        if not do_import.do_import_steps(ctx):
            sys.exit(-1)

        # This MUST be done after the permanent tables are created, since they
        # are used to determine what goes into the param_info table.

        if args.create_param_info or args.create_partables or args.create_table_names:
            logger.open(
                'Creating auxiliary tables',
                limits={'info': args.log_info_limit, 'debug': args.log_debug_limit},
            )

            if args.create_param_info:
                do_param_info.do_param_info(ctx)
            if args.create_partables:
                do_partables.do_partables(ctx)
            if args.create_table_names:
                do_table_names.do_table_names(ctx)

            logger.close()

        if args.update_mult_info:
            logger.open(
                'Updating preprogrammed mult tables',
                limits={'info': args.log_info_limit, 'debug': args.log_debug_limit},
            )

            do_update_mult_info.update_mult_info(ctx)

            logger.close()

        if args.validate_perm:
            do_validate.do_validate(ctx, 'perm')

        if args.create_cart and ctx.try_cart_later:
            logger.open(
                'Trying to create cart table a second time',
                limits={'info': args.log_info_limit, 'debug': args.log_debug_limit},
            )

            do_cart.create_cart(ctx)

            logger.close()

        if args.import_dictionary:
            logger.open(
                'Importing dictionary',
                limits={'info': args.log_info_limit, 'debug': args.log_debug_limit},
            )
            do_dictionary.do_dictionary(ctx)
            logger.close()

        if args.profile:
            pr.disable()
            s = io.StringIO()
            sortby = 'cumulative'
            ps = pstats.Stats(pr, stream=s).strip_dirs().sort_stats(sortby)
            ps.print_stats()
            ps.print_callers()
            logger.info('Profile results:\n%s', s.getvalue())

        logger.close()

    # This top-level handler exists to log every import failure, including the
    # ImportDBError the pipeline raises on any DB error. It catches Exception rather
    # than BaseException deliberately: SystemExit and KeyboardInterrupt mean the run
    # was stopped on purpose, which is not an import failure to log and report.
    except Exception:
        msg = 'Import failed with exception'
        if not args.log_suppress_traceback:
            msg += ':\n' + traceback.format_exc()
        logger.log('fatal', msg)
        sys.exit(-1)
