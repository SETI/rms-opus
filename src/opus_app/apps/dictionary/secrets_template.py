################################################################################
# secrets_template.py
#
# These configuration parameters are specific to a particular installation
# of the import pipeline.
################################################################################

## The username and password for the import user. This user needs to have most
# privileges including table creation and deletion.
DB_USER = 'XXX'
DB_PASSWORD = 'XXX'

# The hostname and database name in which the OPUS schema lives.
# For MySQL, the database is IGNORED.
# For PostgreSQL, this is the database to connect to.
# Note that the dictionary import pipeline only handles MySQL at the moment!
DICTIONARY_HOST_NAME = 'XXX'
DICTIONARY_DATABASE_NAME = 'XXX'

# The main namespace in which Dictionary tables live.
# For MySQL this is the database name.
# For PostgreSQL this is the schema name.
DICTIONARY_SCHEMA_NAME = 'XXX'

# The pdsdd.full file.
PDSDD_FILE = 'XXX'

# The directory where the .json files live
JSON_SCHEMA_PATH = 'XXX'
