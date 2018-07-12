# Settings that are local to the current installation and need to be
# set separately for each server.

# The name of the MySQL database to use for OPUS
OPUS_DB = '<DB_NAME>'

# The name of the MySQL database to use for the dictionary
DICTIONARY_DB = '<DB_NAME>'

# The MySQL user and password
DB_USER = '<DB_USER>'
DB_PASS = '<DB_PASS>'

# The Django "secret key". This needs to be a unique, secret string.
# Generator tools are available:
#   https://www.google.com/search?q=django+secret+generator
SECRET_KEY = '<SECRET_KEY>'

# Where the real PDS data is mounted
PDS_DATA_DIR = '<HOLDING_DIR>'

# Where static files are served from in a production environment
STATIC_ROOT = '<STATIC_DIR'>

# Where to put zipped cart files for downloading
# Needs a TRAILING SLASH
TAR_FILE_PATH = '<TAR_FILE_PATH>/'

# The root URL used to retrieve zipped collections files
# Needs a TRAILING SLASH
TAR_FILE_URL_PATH = 'http://pds-rings-downloads.seti.org/opus/'
