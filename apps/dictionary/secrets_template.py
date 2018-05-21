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
DICTIONARY_HOST_NAME = 'XXX'
# For MySQL this is the database name.
DICTIONARY_SCHEMA_NAME = 'XXX'

# The directory where the pds-tools repo lives.
PDS_TOOLS_PATH = 'XXX'

# The pdsdd.full file.
PDSDD_FILE = 'XXX'
#pds_file = "c:/seti/opus_dbs/pdsdd.full"

# The directory where the .json files live
JSON_SCHEMA_PATH = 'XXX'

# The root OPUS directory
OPUS_ROOT_PATH = 'XXX'
