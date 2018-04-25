################################################################################
# main_import_opus.py
#
# The main entry point for the OPUS import pipeline. To get usage, type:
#
#    python main_opus_import.py --help
################################################################################

from secrets import *

import argparse
import json
import logging
import os
import sys
import traceback
import warnings

sys.path.insert(0, PDS_WEBSERVER_PYTHON_PATH)
sys.path.insert(0, PDS_TOOLS_PATH)

import pdslogger
pdslogger.TIME_FMT = '%Y-%m-%d %H:%M:%S'
import pdsfile

from config_data import *
import do_django
import do_grouping_target_name
import do_import
import do_param_info
import do_partables
import do_table_names
import do_validate
import impglobals
import import_util

import importdb


################################################################################
# COMMAND LINE PROCESSING
################################################################################

command_list = sys.argv[1:]

parser = argparse.ArgumentParser(
    description='OPUS Import Pipeline')

# What to actually do
parser.add_argument(
    '--do-it-all', action='store_true', default=False,
    help="""Perform all import functions. This implies, in order:
            --drop-old-import-tables
            --import
            --copy-import-to-permanent-tables
            --drop-new-import-tables
            --create-param-info
            --create-partables
            --create-table-names
            --drop-cache-tables
            --drop-collections-tables
         """
)

parser.add_argument(
    '--read-only', action='store_true', default=False,
    help='Don\'t modify or create any SQL table'
)

parser.add_argument(
    '--cleanup-aux-tables', action='store_true', default=False,
    help="""Create or clean up auxiliary tables. This implies:
            --create-param-info
            --create-partables
            --create-table-names
            --drop-cache-tables
            --drop-collections-tables
         """
)

parser.add_argument(
    '--drop-old-import-tables', action='store_true', default=False,
    help='Drop ALL the old import tables'
)

parser.add_argument(
    '--delete-import-volumes', action='store_true', default=False,
    help='Delete the given volumes from the import tables'
)

parser.add_argument(
    '--import', dest='do_import', action='store_true', default=False,
    help="""Perform an import of the specified volumes; implies
            --delete-import-volumes"""
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
    '--import-force-metadata-index', action='store_true', default=False,
    help='Force the use of metadata index files and fail if none available'
)
parser.add_argument(
    '--import-check-duplicate-id', action='store_true', default=False,
    help='Check for duplicate rms_obs_id; needed for GOSSI'
)

parser.add_argument(
    '--delete-permanent-import-volumes', action='store_true', default=False,
    help='Delete the volumes in the import tables from the permanent tables'
)
parser.add_argument(
    '--delete-permanent-volumes', action='store_true', default=False,
    help='Delete the given volumes from the permanent tables'
)

parser.add_argument(
    '--copy-import-to-permanent-tables', action='store_true', default=False,
    help="""Copy all temporary import tables to the permanent tables;
            implies --delete-permanent-import-volumes
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
    '--create-grouping-target-name', action='store_true', default=False,
    help="""Create the grouping_target_name table;
            includes copying to permanent table"""
)

parser.add_argument(
    '--drop-cache-tables', action='store_true', default=False,
    help='Drop the cache tables used by OPUS; also clears user_searches'
)
parser.add_argument(
    '--drop-collections-tables', action='store_true', default=False,
    help='Drop the collections tables used by OPUS'
)
parser.add_argument(
    '--create-django-session-table', action='store_true', default=False,
    help='Create the django_session table used by OPUS if not already present'
)

parser.add_argument(
    '--validate-perm', action='store_true', default=False,
    help='Perform validation of the final permanent tables'
)


# Arguments about volume selection
parser.add_argument(
    '--volumes', type=str, default=None,
    metavar='VOL_DESC,VOL_DESC...',
    help="""Comma-separated list of volume descriptors (COISS_1xxx,COVIMS_0089)
            to import""")

# Arguments about logging
parser.add_argument(
    '--log-pdsfile', action='store_true', default=False,
    help='Also log output of pdsfile actions'
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


impglobals.ARGUMENTS = parser.parse_args(command_list)

if impglobals.ARGUMENTS.do_it_all:
    impglobals.ARGUMENTS.drop_old_import_tables = True
    impglobals.ARGUMENTS.do_import = True
    impglobals.ARGUMENTS.copy_import_to_permanent_tables = True
    impglobals.ARGUMENTS.drop_new_import_tables = True
    impglobals.ARGUMENTS.create_param_info = True
    impglobals.ARGUMENTS.create_partables = True
    impglobals.ARGUMENTS.create_table_names = True
    impglobals.ARGUMENTS.create_grouping_target_name = True
    impglobals.ARGUMENTS.drop_cache_tables = True
    impglobals.ARGUMENTS.drop_collections_tables = True
    impglobals.ARGUMENTS.create_django_session_table = True

if impglobals.ARGUMENTS.cleanup_aux_tables:
    impglobals.ARGUMENTS.create_param_info = True
    impglobals.ARGUMENTS.create_partables = True
    impglobals.ARGUMENTS.create_table_names = True
    impglobals.ARGUMENTS.create_grouping_target_name = True
    impglobals.ARGUMENTS.drop_cache_tables = True
    impglobals.ARGUMENTS.drop_collections_tables = True
    impglobals.ARGUMENTS.create_django_session_table = True


################################################################################
# LOGGING INITIALIZATION
################################################################################

LOGNAME = 'opus_import.main'

impglobals.LOGGER = pdslogger.PdsLogger(LOGNAME,
            limits={'info': impglobals.ARGUMENTS.log_info_limit,
                    'debug': impglobals.ARGUMENTS.log_debug_limit})

info_logfile = os.path.abspath(LOG_FILE)
debug_logfile = os.path.abspath(DEBUG_LOG_FILE)

info_handler = pdslogger.file_handler(info_logfile, level=logging.INFO,
                                      rotation='ymdhms')
debug_handler = pdslogger.file_handler(debug_logfile, level=logging.DEBUG,
                                       rotation='ymdhms')

impglobals.LOGGER.add_handler(info_handler)
impglobals.LOGGER.add_handler(debug_handler)
impglobals.LOGGER.add_handler(pdslogger.stdout_handler)

handler = pdslogger.warning_handler(LOGFILE_DIR, rotation='none')
impglobals.LOGGER.add_handler(handler)

handler = pdslogger.error_handler(LOGFILE_DIR, rotation='none')
impglobals.LOGGER.add_handler(handler)

if impglobals.ARGUMENTS.log_pdsfile:
    import_util.pdsfile.set_logger(impglobals.LOGGER, True)

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

try: # Top-level exception handling so we always log what's going on

    impglobals.LOGGER.open(
            f'Performing all requested import functions',
            limits={'info': impglobals.ARGUMENTS.log_info_limit,
                    'debug': impglobals.ARGUMENTS.log_debug_limit})

    pdsfile.preload(PDS_DATA_DIR, VOLUME_INFO_PATH)

    try:
        impglobals.DATABASE = importdb.get_db(
                                   DB_BRAND, OPUS_HOST_NAME,
                                   OPUS_DATABASE_NAME, OPUS_SCHEMA_NAME,
                                   DB_USER, DB_PASSWORD,
                                   mult_form_types=GROUP_FORM_TYPES,
                                   logger=impglobals.LOGGER,
                                   import_prefix=
                                        IMPORT_TABLE_TEMP_PREFIX,
                                   read_only=impglobals.ARGUMENTS.read_only)
    except importdb.ImportDBException:
        sys.exit(-1)

    impglobals.DATABASE.log_sql = impglobals.ARGUMENTS.log_sql

    do_import.do_import_steps()

    # This MUST be done after the permanent tables are created, since they
    # are used to determine what goes into the param_info table.

    if (impglobals.ARGUMENTS.create_param_info or
        impglobals.ARGUMENTS.create_partables or
        impglobals.ARGUMENTS.create_table_names or
        impglobals.ARGUMENTS.create_grouping_target_name):
        impglobals.LOGGER.open(
                f'Creating auxiliary tables',
                limits={'info': impglobals.ARGUMENTS.log_info_limit,
                        'debug': impglobals.ARGUMENTS.log_debug_limit})

        if impglobals.ARGUMENTS.create_param_info:
            do_param_info.do_param_info()
        if impglobals.ARGUMENTS.create_partables:
            do_partables.do_partables()
        if impglobals.ARGUMENTS.create_table_names:
            do_table_names.do_table_names()
        if impglobals.ARGUMENTS.create_grouping_target_name:
            do_grouping_target_name.do_grouping_target_name()

        impglobals.LOGGER.close()

    if (impglobals.ARGUMENTS.drop_cache_tables or
        impglobals.ARGUMENTS.drop_collections_tables or
        impglobals.ARGUMENTS.create_django_session_table):
        impglobals.LOGGER.open(
            f'Cleaning up OPUS/Django tables',
            limits={'info': impglobals.ARGUMENTS.log_info_limit,
                    'debug': impglobals.ARGUMENTS.log_debug_limit})

        if impglobals.ARGUMENTS.drop_cache_tables:
            do_django.drop_cache_tables()
        if impglobals.ARGUMENTS.drop_collections_tables:
            do_django.drop_collections_tables()
        if impglobals.ARGUMENTS.create_django_session_table:
            do_django.create_django_session_table()

        impglobals.LOGGER.close()

    if impglobals.ARGUMENTS.validate_perm:
        do_validate.do_validate('perm')

    impglobals.LOGGER.close()

except:
    msg = 'Import failed with exception'
    if not impglobals.ARGUMENTS.log_suppress_traceback:
        msg += ':\n' + traceback.format_exc()
    impglobals.LOGGER.log('fatal', msg)
    sys.exit(-1)
