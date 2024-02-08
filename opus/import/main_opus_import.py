################################################################################
# main_import_opus.py
#
# The main entry point for the OPUS import pipeline. To get usage, type:
#
#    python main_opus_import.py --help
################################################################################

import argparse
import cProfile
import io
import logging
import os
import pstats
import sys
import traceback
import warnings

from pdsfile import Pds3File, Pds4File

PROJECT_ROOT = os.path.dirname(os.path.realpath(__file__))
RMS_OPUS_ROOT = os.path.dirname(os.path.dirname(PROJECT_ROOT))
sys.path.insert(0, RMS_OPUS_ROOT) # So we can import opus_secrets

from opus_secrets import * # noqa: E402

sys.path.insert(0, RMS_PDSFILE_PATH)
sys.path.insert(0, RMS_OPUS_LIB_PATH)

IMPORT_ROOT = os.path.dirname(os.path.realpath(__file__))
PROJECT_ROOT = os.path.dirname(IMPORT_ROOT)
sys.path.insert(0, PROJECT_ROOT)

import pdslogger # noqa: E402
pdslogger.TIME_FMT = '%Y-%m-%d %H:%M:%S'
from pdsfile import PdsFile, Pds3File, Pds4File

from config_data import * # noqa: E402
import do_cart # noqa: E402
import do_dictionary # noqa: E402
import do_django # noqa: E402
import do_import # noqa: E402
import do_param_info # noqa: E402
import do_partables # noqa: E402
import do_table_names # noqa: E402
import do_update_mult_info # noqa: E402
import do_validate # noqa: E402
import impglobals # noqa: E402

import importdb # noqa: E402


################################################################################
# COMMAND LINE PROCESSING
################################################################################

command_list = sys.argv[1:]

parser = argparse.ArgumentParser(
    description='OPUS Import Pipeline')

# Database arguments
parser.add_argument(
    '--read-only', action='store_true', default=False,
    help="Don't modify or create any SQL table"
)
parser.add_argument(
    '--override-db-schema', type=str, default=None,
    help='Override the db_schema specified in opus_secrets.py'
)
parser.add_argument(
    '--override-pds-data-dir', type=str, default=None,
    help='Override the PDS_DATA_DIR specified in opus_secrets.py (.../holdings)'
)
parser.add_argument(
    '--dont-use-shelves-only', action='store_true', default=False,
    help='Look at actual pdsdata volumes/bundles instead of using shelve files'
)

# What to actually do - main import
parser.add_argument(
    '--do-it-all', action='store_true', default=False,
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
         """
)

parser.add_argument(
    '--do-all-import', action='store_true', default=False,
    help="""Perform all import functions. This implies, in order:
            --drop-old-import-tables
            --import
            --copy-import-to-permanent-tables
            --drop-new-import-tables
         """
)

parser.add_argument(
    '--do-import-finalization', action='store_true', default=False,
    help="""Perform all import functions related to permanent tables. This implies, in order:
            --copy-import-to-permanent-tables
            --drop-new-import-tables
            --analyze-permanent-tables
            --create-param-info
            --create-partables
            --create-table-names
            --create-cart
            --drop-cache-tables
         """
)

parser.add_argument(
    '--cleanup-aux-tables', action='store_true', default=False,
    help="""Create or clean up auxiliary tables. This implies:
            --create-param-info
            --create-partables
            --create-table-names
            --create-cart
            --drop-cache-tables
         """
)

parser.add_argument(
    '--drop-old-import-tables', action='store_true', default=False,
    help='Drop ALL the old import tables'
)

parser.add_argument(
    '--delete-import-bundles', action='store_true', default=False,
    help='Delete the given bundles from the import tables'
)

parser.add_argument(
    '--import', dest='do_import', action='store_true', default=False,
    help="""Perform an import of the specified bundles; implies
            --delete-import-bundles"""
)
parser.add_argument(
    '--leave-old-import-tables', action='store_true', default=False,
    help="""Leave the previous import tables and just add to them. Overrides
            --drop-old-import-tables."""
)
parser.add_argument(
    '--import-ignore-errors', action='store_true', default=False,
    help='Allow copying to permanent tables even with errors; for debugging'
)
parser.add_argument(
    '--import-suppress-mult-messages', action='store_true', default=False,
    help='Don\'t give messages about mult table maintenance'
)
parser.add_argument(
    '--import-report-missing-ring-geo', action='store_true', default=False,
    help='Report observations that should have ring_geo data but don\'t'
)
parser.add_argument(
    '--import-report-inventory-mismatch', action='store_true', default=False,
    help='Report mismatches between inventory and surface geometry tables'
)
parser.add_argument(
    '--import-force-metadata-index', action='store_true', default=False,
    help='Force the use of metadata index files and fail if none available'
)
parser.add_argument(
    '--import-check-duplicate-id', action='store_true', default=False,
    help='Check for duplicate opus_id; needed for GOSSI,COUVIS,NH'
)
parser.add_argument(
    '--import-ignore-missing-images', action='store_true', default=False,
    help='Don\'t warn about missing browse images'
)
parser.add_argument(
    '--import-dont-use-row-files', action='store_true', default=False,
    help="""Do not use metadata row files to determine whether index and summary
            files should be included in the files table"""
)
parser.add_argument(
    '--import-report-empty-products', action='store_true', default=False,
    help='Report empty products during import'
)
parser.add_argument(
    '--import-fake-images', action='store_true', default=False,
    help='Fake the existence of browse images if real browse files are missing'
)

parser.add_argument(
    '--delete-permanent-import-bundles', action='store_true', default=False,
    help='Delete the bundles in the import tables from the permanent tables'
)
parser.add_argument(
    '--delete-permanent-bundles', action='store_true', default=False,
    help='Delete the given bundles from the permanent tables'
)

parser.add_argument(
    '--copy-import-to-permanent-tables', action='store_true', default=False,
    help="""Copy all temporary import tables to the permanent tables;
            implies --delete-permanent-import-bundles
         """
)
parser.add_argument(
    '--drop-permanent-tables', action='store_true', default=False,
    help="""Delete ALL permanent tables; requires --scorched-earth.
            WARNING: THIS DELETES ALL EXISTING DATA"""
)
parser.add_argument(
    '--scorched-earth', action='store_true', default=False,
    help='You are serious about deleting all tables!'
)

parser.add_argument(
    '--drop-new-import-tables', action='store_true', default=False,
    help='Drop the new import tables after copying to permanent (if selected)'
)

parser.add_argument(
    '--analyze-permanent-tables', action='store_true', default=False,
    help='Analyze (recompute key distribution) the permanent tables'
)

# Import-related auxiliary functions

parser.add_argument(
    '--create-param-info', action='store_true', default=False,
    help='Create the param_info table; includes copying to permanent table'
)
parser.add_argument(
    '--create-partables', action='store_true', default=False,
    help='Create the partables table; includes copying to permanent table'
)
parser.add_argument(
    '--create-table-names', action='store_true', default=False,
    help='Create the table_names table; includes copying to permanent table'
)
parser.add_argument(
    '--update-mult-info', action='store_true', default=False,
    help='Update the details of preprogrammed mult tables'
)

# Functions other than main import

parser.add_argument(
    '--drop-cache-tables', action='store_true', default=False,
    help='Drop the cache tables used by OPUS; also clears user_searches'
)
parser.add_argument(
    '--create-cart', action='store_true', default=False,
    help='Create the cart table used by OPUS'
)

parser.add_argument(
    '--validate-perm', action='store_true', default=False,
    help='Perform validation of the final permanent tables'
)

parser.add_argument(
    '--import-dictionary', action='store_true', default=False,
    help='Import the dictionary and contexts from scratch'
)

# Arguments about bundle selection
parser.add_argument(
    'bundles', type=str, default=None, nargs='*',
    metavar='VOL_DESC,VOL_DESC...',
    help="""Comma-separated list of bundle descriptors (COISS_1xxx,COVIMS_0089)
            to import""")

parser.add_argument(
    '--exclude-bundles', type=str, default=None,
    metavar='VOL_NAME,VOL_NAME...',
    help="""Comma-separated list of bundle names (COVIMS_0089,COISS_2111)
            to exclude from importing""")

# Arguments about logging
parser.add_argument(
    '--no-log-pdsfile', action='store_true', default=False,
    help="""Don't log output of pdsfile actions"""
)
parser.add_argument(
    '--log-sql', action='store_true', default=False,
    help='Also log all SQL commands'
)
parser.add_argument(
    '--log-debug-limit', type=int, default=-1,
    help='Limit the number of debug messages'
)
parser.add_argument(
    '--log-info-limit', type=int, default=-1,
    help='Limit the number of info messages'
)
parser.add_argument(
    '--log-suppress-traceback', action='store_true', default=False,
    help='Omit tracebacks from exception reports'
)

parser.add_argument(
    '--profile', action='store_true', default=False,
    help='Do performance profiling'
)

impglobals.ARGUMENTS = parser.parse_args(command_list)

if impglobals.ARGUMENTS.do_it_all:
    impglobals.ARGUMENTS.drop_old_import_tables = True
    impglobals.ARGUMENTS.do_import = True
    impglobals.ARGUMENTS.copy_import_to_permanent_tables = True
    impglobals.ARGUMENTS.drop_new_import_tables = True
    impglobals.ARGUMENTS.analyze_permanent_tables = True
    impglobals.ARGUMENTS.create_param_info = True
    impglobals.ARGUMENTS.create_partables = True
    impglobals.ARGUMENTS.create_table_names = True
    impglobals.ARGUMENTS.create_cart = True
    impglobals.ARGUMENTS.drop_cache_tables = True

if impglobals.ARGUMENTS.do_all_import:
    impglobals.ARGUMENTS.drop_old_import_tables = True
    impglobals.ARGUMENTS.do_import = True
    impglobals.ARGUMENTS.copy_import_to_permanent_tables = True
    impglobals.ARGUMENTS.drop_new_import_tables = True

if impglobals.ARGUMENTS.do_import_finalization:
    impglobals.ARGUMENTS.copy_import_to_permanent_tables = True
    impglobals.ARGUMENTS.drop_new_import_tables = True
    impglobals.ARGUMENTS.analyze_permanent_tables = True
    impglobals.ARGUMENTS.create_param_info = True
    impglobals.ARGUMENTS.create_partables = True
    impglobals.ARGUMENTS.create_table_names = True
    impglobals.ARGUMENTS.create_cart = True
    impglobals.ARGUMENTS.drop_cache_tables = True

if impglobals.ARGUMENTS.cleanup_aux_tables:
    impglobals.ARGUMENTS.create_param_info = True
    impglobals.ARGUMENTS.create_partables = True
    impglobals.ARGUMENTS.create_table_names = True
    impglobals.ARGUMENTS.create_cart = True
    impglobals.ARGUMENTS.drop_cache_tables = True


################################################################################
# LOGGING INITIALIZATION
################################################################################

LOGNAME = 'opus_import.main'

impglobals.LOGGER = pdslogger.PdsLogger(LOGNAME,
            limits={'info': impglobals.ARGUMENTS.log_info_limit,
                    'debug': impglobals.ARGUMENTS.log_debug_limit})

info_logfile = os.path.abspath(IMPORT_LOG_FILE)
debug_logfile = os.path.abspath(IMPORT_DEBUG_LOG_FILE)

info_handler = pdslogger.file_handler(info_logfile, level=logging.INFO,
                                      rotation='ymdhms')
debug_handler = pdslogger.file_handler(debug_logfile, level=logging.DEBUG,
                                       rotation='ymdhms')

impglobals.LOGGER.add_handler(info_handler)
impglobals.LOGGER.add_handler(debug_handler)
impglobals.LOGGER.add_handler(pdslogger.stdout_handler)

handler = pdslogger.warning_handler(IMPORT_LOGFILE_DIR, rotation='none')
impglobals.LOGGER.add_handler(handler)

handler = pdslogger.error_handler(IMPORT_LOGFILE_DIR, rotation='none')
impglobals.LOGGER.add_handler(handler)

impglobals.PYTHON_WARNING_LIST = []

def _new_warning_handler(message, category, filename, lineno, file, line):
    global PYTHON_WARNING_LIST
    PYTHON_WARNING_LIST.append(str(message))

warnings.showwarning = _new_warning_handler

################################################################################
#
# THE MAIN IMPORT LOOP
#
################################################################################

if (impglobals.ARGUMENTS.drop_permanent_tables !=
    impglobals.ARGUMENTS.scorched_earth):
    impglobals.LOGGER.log('fatal',
        '--drop-permanent-tables and --scorched-earth must be used together')
    sys.exit(-1)

our_schema_name = DB_SCHEMA_NAME
if impglobals.ARGUMENTS.override_db_schema:
    our_schema_name = impglobals.ARGUMENTS.override_db_schema

try: # Top-level exception handling so we always log what's going on
    # Start the profiling
    if impglobals.ARGUMENTS.profile:
        pr = cProfile.Profile()
        pr.enable()

    impglobals.LOGGER.open(
            'Performing all requested import functions',
            limits={'info': impglobals.ARGUMENTS.log_info_limit,
                    'debug': impglobals.ARGUMENTS.log_debug_limit})

    if not impglobals.ARGUMENTS.dont_use_shelves_only:
        Pds3File.use_shelves_only()
        Pds4File.use_shelves_only()
    Pds3File.require_shelves(True)
    Pds4File.require_shelves(True)
    if impglobals.ARGUMENTS.override_pds_data_dir:
        Pds3File.preload(impglobals.ARGUMENTS.override_pds_data_dir)
    else:
        Pds3File.preload(PDS_DATA_DIR)

    # We do this after the preload because we don't want to see all the preload
    # debug messages.
    if not impglobals.ARGUMENTS.no_log_pdsfile:
        Pds3File.set_logger(impglobals.LOGGER)
        Pds4File.set_logger(impglobals.LOGGER)

    try:
        impglobals.DATABASE = importdb.get_db(
                                   DB_BRAND, DB_HOST_NAME,
                                   DB_DATABASE_NAME, our_schema_name,
                                   DB_USER, DB_PASSWORD,
                                   mult_form_types=GROUP_FORM_TYPES,
                                   logger=impglobals.LOGGER,
                                   import_prefix=IMPORT_TABLE_TEMP_PREFIX,
                                   read_only=impglobals.ARGUMENTS.read_only)
    except importdb.ImportDBException:
        sys.exit(-1)

    impglobals.DATABASE.log_sql = impglobals.ARGUMENTS.log_sql

    # This MUST be done before the permanent tables are created, because there
    # could be entries in the cart table that point at the permanent
    # tables, and import could delete entries out of the permanent tables
    # causing a foreign key violation.
    # Note, however, that do_import_steps() might actually delete ALL permanent
    # tables with --scorched-earth, which means our effort here will be wasted,
    # so don't bother in that case.
    if ((impglobals.ARGUMENTS.drop_cache_tables or
         impglobals.ARGUMENTS.create_cart) and
         not impglobals.ARGUMENTS.drop_permanent_tables):
        impglobals.LOGGER.open(
            'Cleaning up OPUS/Django tables',
            limits={'info': impglobals.ARGUMENTS.log_info_limit,
                    'debug': impglobals.ARGUMENTS.log_debug_limit})

        if impglobals.ARGUMENTS.create_cart:
            do_cart.create_cart()
        if impglobals.ARGUMENTS.drop_cache_tables:
            do_django.drop_cache_tables()

        impglobals.LOGGER.close()

    do_import.do_import_steps()

    # This MUST be done after the permanent tables are created, since they
    # are used to determine what goes into the param_info table.

    if (impglobals.ARGUMENTS.create_param_info or
        impglobals.ARGUMENTS.create_partables or
        impglobals.ARGUMENTS.create_table_names):
        impglobals.LOGGER.open(
                'Creating auxiliary tables',
                limits={'info': impglobals.ARGUMENTS.log_info_limit,
                        'debug': impglobals.ARGUMENTS.log_debug_limit})

        if impglobals.ARGUMENTS.create_param_info:
            do_param_info.do_param_info()
        if impglobals.ARGUMENTS.create_partables:
            do_partables.do_partables()
        if impglobals.ARGUMENTS.create_table_names:
            do_table_names.do_table_names()

        impglobals.LOGGER.close()

    if impglobals.ARGUMENTS.update_mult_info:
        impglobals.LOGGER.open(
            'Updating preprogrammed mult tables',
            limits={'info': impglobals.ARGUMENTS.log_info_limit,
                    'debug': impglobals.ARGUMENTS.log_debug_limit})

        do_update_mult_info.update_mult_info()

        impglobals.LOGGER.close()

    if impglobals.ARGUMENTS.validate_perm:
        do_validate.do_validate('perm')

    if (impglobals.ARGUMENTS.create_cart and
        impglobals.TRY_CART_LATER):
        impglobals.LOGGER.open(
            'Trying to create cart table a second time',
            limits={'info': impglobals.ARGUMENTS.log_info_limit,
                    'debug': impglobals.ARGUMENTS.log_debug_limit})

        do_cart.create_cart()

        impglobals.LOGGER.close()

    if impglobals.ARGUMENTS.import_dictionary:
        impglobals.LOGGER.open(
            'Importing dictionary',
            limits={'info': impglobals.ARGUMENTS.log_info_limit,
                    'debug': impglobals.ARGUMENTS.log_debug_limit})
        do_dictionary.do_dictionary()
        impglobals.LOGGER.close()

    if impglobals.ARGUMENTS.profile:
        pr.disable()
        s = io.StringIO()
        sortby = 'cumulative'
        ps = pstats.Stats(pr, stream=s).strip_dirs().sort_stats(sortby)
        ps.print_stats()
        ps.print_callers()
        impglobals.LOGGER.info('Profile results:\n%s', s.getvalue())

    impglobals.LOGGER.close()

except:
    msg = 'Import failed with exception'
    if not impglobals.ARGUMENTS.log_suppress_traceback:
        msg += ':\n' + traceback.format_exc()
    impglobals.LOGGER.log('fatal', msg)
    sys.exit(-1)
