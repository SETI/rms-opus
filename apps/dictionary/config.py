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

# The username and password for the import user. This user needs to have most
# privileges including table creation and deletion.
DB_USER = 'debby'
DB_PASSWORD = 'debby'

# The hostname and database name in which the OPUS schema lives.
# For MySQL, the database is IGNORED.
# For PostgreSQL, this is the database to connect to.
OPUS_HOST_NAME = '127.0.0.1'
OPUS_DATABASE_NAME = 'dictionary'

# The main namespace in which OPUS tables live.
# For MySQL this is the database name.
# For PostgreSQL this is the schema name.
OPUS_SCHEMA_NAME = 'dictionary'

# The directory where the pds-tools repo lives.
PDS_TOOLS_PATH = "c:/seti/opus/pds-tools"

# The pdsdd.full file.
PDSDD_FILE = "c:/seti/opus_dbs/pdsdd.full"
#pds_file = "c:/seti/opus_dbs/pdsdd.full"

# The directory where the .json files live
JSON_SCHEMA_PATH ="C:/seti/opus/import/table_schemas"

# The root OPUS directory
OPUS_ROOT_PATH = 'C:/seti/opus'

sys.path.append(PDS_TOOLS_PATH)
sys.path.append(f'{OPUS_ROOT_PATH}/apps/dictionary')

import importUtils
from importUtils import ImportDictionaryData

# Example usage:
obj = ImportDictionaryData()
obj.create_dictionary(drop="")
