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

# The main namespace in which OPUS tables live.
# For MySQL this is the database name.
# For PostgreSQL this is the schema name.
DB_SCHEMA_NAME = '<SCHEMA_NAME>'

# The database user and password. This user needs to have most privileges,
# including table creation and deletion.
DB_USER = '<DB_USER>'
DB_PASSWORD = '<DB_PASSWORD>'

# The root directory of all PDS holdings. Under this directory should be
# volumes, calibrated, metadata, previews, and diagrams.
PDS_DATA_DIR = '<HOLDING_DIR>'

# The directory where rms-opus lives.
RMS_OPUS_PATH = '<RMS_OPUS_PATH>'

# The directory where the rms-opus library lives. This should normally be
# .../rms-opus/lib
RMS_OPUS_LIB_PATH = os.path.join(RMS_OPUS_PATH, 'lib')

# The directory where the rms-pdsfile repo lives. This should
# normally be .../rms-pdsfile
RMS_PDSFILE_PATH = '<RMS_PDSFILE_PATH>'


############################################
### NEEDED FOR THE MAIN OPUS APPLICATION ###
############################################

# The Django debug setting. NEVER deploy a production site with DEBUG set to
# True.
DEBUG = True

# The list of hosts or IP addresses that Django is permitted to serve
ALLOWED_HOSTS = ('127.0.0.1',
                 'localhost',
                 <ADDITIONAL_ALLOWED_HOSTS>)

# These settings are useful to include on a production server
# ADMINS = (<email list>)
# MANAGERS = ADMINS
# EMAIL_* (see https://docs.djangoproject.com/en/2.1/topics/email/)
# SERVER_EMAIL

# The Django "secret key". This needs to be a unique, secret string.
# Generator tools are available:
#   https://www.google.com/search?q=django+secret+generator
SECRET_KEY = '<SECRET_KEY>'

# Where static files are served from in a production environment
# This is ignored in a non-production environment
STATIC_ROOT = '<STATIC_ROOT>'

# Where static files are served from if this is a non-production environment,
# usually .../rms-opus/opus/application/static_media
# If this is a production environment, this should be the same as STATIC_ROOT
OPUS_STATIC_ROOT = '<OPUS_STATIC_ROOT>'

# The prefix to add to all cache keys indicating a unique string for this
# installation on a server. This allows multiple OPUS installations on the
# same server without causing memcached cache key conflicts.
CACHE_SERVER_PREFIX = '<CACHE_SERVER_PREFIX>'

# Where to put zipped cart files for downloading and the manifest file
# Needs a TRAILING SLASH
TAR_FILE_PATH = '<TAR_FILE_PATH>/'
MANIFEST_FILE_PATH = '<MANIFEST_FILE_PATH>/'

# The root URL used to retrieve zipped collections files
# Needs a TRAILING SLASH
TAR_FILE_URL_PATH = '<TAR_FILE_URL>/'

# The public URL to access OPUS
PUBLIC_OPUS_URL = 'https://opus.pds-rings.seti.org/'

# The root URL used to retrieve product files from a web server
PRODUCT_HTTP_PATH = 'https://opus.pds-rings.seti.org/'

# The root URL used to retrieve product files from viewmaster
VIEWMASTER_ROOT_PATH = 'https://pds-rings.seti.org/'

# The directory in which to place log files created by OPUS
OPUS_LOGFILE_DIR = '<OPUS_LOGFILE_DIR>'
OPUS_LOG_FILE = os.path.join(OPUS_LOGFILE_DIR, 'opus_log.txt')

# The file that contains the date of the last blog update
OPUS_LAST_BLOG_UPDATE_FILE = '<LAST_BLOG_UPDATE_FILE>'

# The file that contains the html for any short-term notifications
OPUS_NOTIFICATION_FILE = '<NOTIFICATION_FILE>'

# What level of message to log at each destination
OPUS_LOG_FILE_LEVEL = 'INFO'
OPUS_LOG_CONSOLE_LEVEL = 'INFO'
OPUS_LOG_DJANGO_LEVEL = 'WARN'
OPUS_LOG_API_CALLS = False

# Allow faking of slow network connections
# None = Don't do anything different
# Positive = Delay this exact number of milliseconds
# Negative = Delay a random amount between 0 and abs(delay)
OPUS_FAKE_API_DELAYS = None

# Allow random throwing of Http404 or Http500 errors
OPUS_FAKE_SERVER_ERROR404_PROBABILITY = 0.
OPUS_FAKE_SERVER_ERROR500_PROBABILITY = 0.


##############################
### NEEDED FOR OPUS IMPORT ###
##############################

# The prefix to use for temporary tables during import
IMPORT_TABLE_TEMP_PREFIX = 'imp_'

# The directory in which to place log files created during the import process.
IMPORT_LOGFILE_DIR = '<IMPORT_LOGFILE_DIR>'
IMPORT_LOG_FILE = os.path.join(IMPORT_LOGFILE_DIR, 'opus_import.log')
IMPORT_DEBUG_LOG_FILE = os.path.join(IMPORT_LOGFILE_DIR, 'opus_import_debug.log')


#############################################
### NEEDED FOR THE DICTIONARY APPLICATION ###
#############################################

# The prefix URL to look up individual terms in the dictionary.
DICTIONARY_TERM_URL = '<DICTIONARY_URL>'


####################################
### NEEDED FOR DICTIONARY IMPORT ###
####################################

# The pdsdd.full file including path
DICTIONARY_PDSDD_FILE = os.path.join(RMS_OPUS_PATH,
                                     'dictionary/pdsdd.full')

# The contexts.csv file including path
DICTIONARY_CONTEXTS_FILE = os.path.join(RMS_OPUS_PATH,
                                        'dictionary/contexts.csv')

# The location of the OPUS .json table_schema files
DICTIONARY_JSON_SCHEMA_PATH = os.path.join(RMS_OPUS_PATH,
                                           'opus/import/table_schemas')
