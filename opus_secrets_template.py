################################################################################
# Settings that are local to the current installation and need to be
# set separately for each installation and server.
################################################################################

import os

### NEEDED FOR ALL APPLICATIONS ###

# The brand of the back-end SQL database.
# Valid values are: MySQL, PostgreSQL
DB_BRAND = 'MySQL'

# The hostname and database name in which the OPUS and dictionary schemas live.
# In most cases, the hostname will be 'localhost'.
# For MySQL, the database is IGNORED.
# For PostgreSQL, this is the database to connect to.
DB_HOST_NAME = '<HOST_NAME>'
DB_DATABASE_NAME = '<DB_NAME>'

# The database user and password. This user needs to have most privileges,
# including table creation and deletion.
DB_USER = '<DB_USER>'
DB_PASSWORD = '<DB_PASSWORD>'

# The root directory of all PDS holdings. Under this directory should be
# volumes, calibrated, metadata, previews, and diagrams.
PDS_DATA_DIR = '<HOLDING_DIR>'

# The directory where pds-opus lives.
PDS_OPUS_PATH = '<PATH>'

# The directory where the pds-opus library lives. This should normally be
# .../pds-opus/lib
PDS_OPUS_LIB_PATH = os.path.join(PDS_OPUS_PATH, 'lib')

# The directory where the pds-webtools repo lives. This should
# normally be .../pds-webtools
PDS_WEBTOOLS_PATH = '<PATH>'

# The directory where the pds-tools repo lives. This should
# normally be .../pds-tools
PDS_TOOLS_PATH = '<PATH>'


############################################
### NEEDED FOR THE MAIN OPUS APPLICATION ###
############################################

# The main namespace in which OPUS tables live.
# For MySQL this is the database name.
# For PostgreSQL this is the schema name.
OPUS_SCHEMA_NAME = 'XXX'

# The Django "secret key". This needs to be a unique, secret string.
# Generator tools are available:
#   https://www.google.com/search?q=django+secret+generator
SECRET_KEY = '<SECRET_KEY>'

# Where static files are served from in a production environment
STATIC_ROOT = '<STATIC_DIR>'

# Where to put zipped cart files for downloading
# Needs a TRAILING SLASH
TAR_FILE_PATH = '<TAR_FILE_PATH>/'

# The root URL used to retrieve zipped collections files
# Needs a TRAILING SLASH
TAR_FILE_URL_PATH = '<URL>/'

# The directory in which to place log files created by OPUS
OPUS_LOGFILE_DIR = '<LOGFILE_DIR>'
OPUS_LOG_FILE = os.path.join(OPUS_LOGFILE_DIR, 'opus_log.txt')

# What level of message to log at each destination
OPUS_LOG_FILE_LEVEL = 'INFO'
OPUS_LOG_CONSOLE_LEVEL = 'INFO'
OPUS_LOG_DJANGO_LEVEL = 'WARN'
OPUS_LOG_API_CALLS = False


##############################
### NEEDED FOR OPUS IMPORT ###
##############################

# The prefix to use for temporary tables during import
IMPORT_TABLE_TEMP_PREFIX = 'imp_'

# The directory in which to place log files created during the import process.
IMPORT_LOGFILE_DIR = '<LOGFILE_DIR>'
IMPORT_LOG_FILE = os.path.join(IMPORT_LOGFILE_DIR, 'opus_import.log')
IMPORT_DEBUG_LOG_FILE = os.path.join(IMPORT_LOGFILE_DIR, 'opus_import_debug.log')


#############################################
### NEEDED FOR THE DICTIONARY APPLICATION ###
#############################################

# The prefix URL to look up individual terms in the dictionary.
DICTIONARY_TERM_URL = '<URL>'


####################################
### NEEDED FOR DICTIONARY IMPORT ###
####################################

# The pdsdd.full file including path
DICTIONARY_PDSDD_FILE = os.path.join(PDS_OPUS_PATH,
                                     'dictionary/PDSDD/pdsdd.full')

# The contexts.csv file including path
DICTIONARY_CONTEXTS_FILE = os.path.join(PDS_OPUS_PATH,
                                        'dictionary/contexts.csv')

# The location of the OPUS .json table_schema files
DICTIONARY_JSON_SCHEMA_PATH = os.path.join(PDS_OPUS_PATH,
                                           'opus/import/table_schemas')
