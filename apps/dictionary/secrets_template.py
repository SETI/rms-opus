################################################################################
# config.py
#
# These configuration parameters are specific to a particular installation
# of the import pipeline.
################################################################################

import sys

################################################################################
# THINGS THAT YOU LIKELY WANT TO CHANGE
################################################################################

## The username and password for the import user. This user needs to have most
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

# The path to pds_tools; generally at opus root so default is '.'
PDS_TOOLS_DIR = "XXX"

# The directory where the pds-tools repo lives.
PDS_TOOLS_PATH = 'XXX'

# The pdsdd.full file.
PDSDD_FILE = 'XXX'
#pds_file = "c:/seti/opus_dbs/pdsdd.full"

# The directory where the .json files live
JSON_SCHEMA_PATH = 'XXX'

# The root OPUS directory
OPUS_ROOT_PATH = 'XXX'

sys.path.append(PDS_TOOLS_DIR)
sys.path.append(f'{OPUS_ROOT_PATH}/apps/dictionary')

import importUtils
from importUtils import ImportDictionaryData

# Example usage:
obj = ImportDictionaryData()
obj.create_dictionary(drop="")
