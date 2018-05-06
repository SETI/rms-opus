################################################################################
# secrets_template.py
#
# These configuration parameters are specific to a particular installation
# of the import pipeline.
################################################################################

import os

# The brand of the back-end SQL database.
# Valid values are: MySQL, PostgreSQL
DB_BRAND = 'MySQL'
# DB_BRAND = 'PostgreSQL'

# The username and password for the import user. This user needs to have most
# privileges including table creation and deletion.
DB_USER = 'XXX'
DB_PASSWORD = 'XXX'

# The hostname and database name in which the OPUS schema lives.
# For MySQL, the database is IGNORED.
# For PostgreSQL, this is the database to connect to.
OPUS_HOST_NAME = 'XXX'
OPUS_DATABASE_NAME = 'XXX'

# The main namespace in which OPUS tables live.
# For MySQL this is the database name.
# For PostgreSQL this is the schema name.
OPUS_SCHEMA_NAME = 'XXX'

# The prefix to use for temporary tables during import
IMPORT_TABLE_TEMP_PREFIX = 'imp_'

# The root directory of all PDS holdings. Under this directory should be
# volumes, calibrated, metadata, previews, and diagrams.
PDS_DATA_DIR = 'XXX'

# The directory in which to store SQL dumps of tables or databases that are
# created before changes are made during import.
SQL_BACKUP_DIR = 'XXX'

# The directory in which to place log files created during the import process.
LOGFILE_DIR = 'XXX'

LOG_FILE = os.path.join(LOGFILE_DIR, 'opus_import.log')
DEBUG_LOG_FILE = os.path.join(LOGFILE_DIR, 'opus_import_debug.log')

# The directory where the pds-webserver repo lives.
PDS_WEBSERVER_PATH = 'XXX'

# The directory where the pds-webserver Python routines live.
PDS_WEBSERVER_PYTHON_PATH = os.path.join(PDS_WEBSERVER_PATH, 'python')

# The directory where the pds-tools repo lives.
PDS_TOOLS_PATH = 'XXX'
