#!/bin/bash
# Arg 1: Unique ID
# Arg 2: Config name
# Arg 3: Holdings root

source ~/opus_runner_secrets

UNIQUE_ID=$1
TEST_CAT=opus
TEST_CAT_DIR=$TEST_ROOT/$TEST_CAT/$UNIQUE_ID
TEST_LOG_DIR=$TEST_CAT_DIR/test_logs
SRC_DIR=$TEST_CAT_DIR/src
LOG_DIR=$TEST_CAT_DIR/temp_logs
DOWNLOAD_DIR=$TEST_CAT_DIR/downloads
DATA_DIR=$TEST_CAT_DIR/data

HOLDINGS_DIR=$3/holdings
if [ ! -d "$HOLDINGS_DIR" ]; then
    echo "Directory not found:" $HOLDINGS_DIR
    exit -1
fi

cd $SRC_DIR/rms-opus
if [ $? -ne 0 ]; then exit -1; fi

# Checkout the correct branch/tag

git checkout master
if [ $? -ne 0 ]; then exit -1; fi
#if [ $1 == "admin" ]; then
#    git checkout pdsadmin
#    if [ $? -ne 0 ]; then exit -1; fi
#fi

# Create the opus_secrets.py file

rm -rf opus_secrets.py
if [ $? -ne 0 ]; then exit -1; fi
echo "import os" > opus_secrets.py
if [ $? -ne 0 ]; then exit -1; fi
echo "DB_BRAND = 'MySql'" >> opus_secrets.py
echo "DB_HOST_NAME = 'localhost'" >> opus_secrets.py
echo "DB_DATABASE_NAME = ''" >> opus_secrets.py
echo "DB_SCHEMA_NAME = 'opus_test_db_${UNIQUE_ID}'" >> opus_secrets.py
echo "DB_USER = '${OPUS_DB_USER}'" >> opus_secrets.py
echo "DB_PASSWORD = '${OPUS_DB_PASSWORD}'" >> opus_secrets.py
echo "PDS_DATA_DIR = '${HOLDINGS_DIR}'" >> opus_secrets.py
echo "RMS_OPUS_PATH = '${SRC_DIR}/rms-opus'" >> opus_secrets.py
echo "RMS_OPUS_LIB_PATH = os.path.join(RMS_OPUS_PATH, 'lib')" >> opus_secrets.py
echo "RMS_WEBTOOLS_PATH = '${SRC_DIR}/rms-webtools'" >> opus_secrets.py
echo "DEBUG = True" >> opus_secrets.py
echo "ALLOWED_HOSTS = ('127.0.0.1', 'localhost')" >> opus_secrets.py
echo "SECRET_KEY = 'fred'" >> opus_secrets.py
echo "OPUS_STATIC_ROOT = '${SRC_DIR}/rms-opus/opus/application/static_media'" >> opus_secrets.py
echo "CACHE_SERVER_PREFIX = 'staging_test'" >> opus_secrets.py
echo "TAR_FILE_PATH = '${DOWNLOAD_DIR}/tar/'" >> opus_secrets.py
echo "MANIFEST_FILE_PATH = '${DOWNLOAD_DIR}/manifest/'" >> opus_secrets.py
echo "TAR_FILE_URL_PATH = 'https://bad-host.org/'" >> opus_secrets.py
echo "PUBLIC_OPUS_URL = 'https://opus.pds-rings.seti.org/'" >> opus_secrets.py
echo "PRODUCT_HTTP_PATH = 'https://opus.pds-rings.seti.org/'" >> opus_secrets.py
echo "VIEWMASTER_ROOT_PATH = 'https://pds-rings.seti.org/'" >> opus_secrets.py
echo "OPUS_LOGFILE_DIR = '${LOG_DIR}/opus_logs'" >> opus_secrets.py
echo "OPUS_LOG_FILE = os.path.join(OPUS_LOGFILE_DIR, 'opus_log.txt')" >> opus_secrets.py
echo "OPUS_LAST_BLOG_UPDATE_FILE = '${DATA_DIR}/last_update.txt'" >> opus_secrets.py
echo "OPUS_NOTIFICATION_FILE = '${DATA_DIR}/notification.html'" >> opus_secrets.py
echo "OPUS_LOG_FILE_LEVEL = 'INFO'" >> opus_secrets.py
echo "OPUS_LOG_CONSOLE_LEVEL = 'INFO'" >> opus_secrets.py
echo "OPUS_LOG_DJANGO_LEVEL = 'WARN'" >> opus_secrets.py
echo "OPUS_LOG_API_CALLS = False" >> opus_secrets.py
echo "OPUS_FAKE_API_DELAYS = None" >> opus_secrets.py
echo "OPUS_FAKE_SERVER_ERROR404_PROBABILITY = 0." >> opus_secrets.py
echo "OPUS_FAKE_SERVER_ERROR500_PROBABILITY = 0." >> opus_secrets.py
echo "IMPORT_TABLE_TEMP_PREFIX = 'imp_'" >> opus_secrets.py
echo "IMPORT_LOGFILE_DIR = '${LOG_DIR}/import_logs'" >> opus_secrets.py
echo "IMPORT_LOG_FILE = os.path.join(IMPORT_LOGFILE_DIR, 'opus_impot.log')" >> opus_secrets.py
echo "IMPORT_DEBUG_LOG_FILE = os.path.join(IMPORT_LOGFILE_DIR, 'opus_import_debug.log')" >> opus_secrets.py
echo "DICTIONARY_PDSDD_FILE = os.path.join(RMS_OPUS_PATH, 'dictionary/pdsdd.full')" >> opus_secrets.py
echo "DICTIONARY_CONTEXTS_FILE = os.path.join(RMS_OPUS_PATH, 'dictionary/contexts.csv')" >> opus_secrets.py
echo "DICTIONARY_JSON_SCHEMA_PATH = os.path.join(RMS_OPUS_PATH, 'opus/import/table_schemas')" >> opus_secrets.py
if [ $? -ne 0 ]; then exit -1; fi
exit 0