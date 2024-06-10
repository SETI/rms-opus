# This file should only be used with "source"

if [[ ! -v OPUS_SRC_DIR ]]; then
    echo "INTERNAL ERROR: OPUS_SRC_DIR undefined"
    exit -1
fi

if [[ ! -v OPUS_DIR_NAME ]]; then
    echo "INTERNAL ERROR: OPUS_DIR_NAME undefined"
    exit -1
fi

cd ${OPUS_SRC_DIR}

if [[ -e ${OPUS_SRC_DIR}/${OPUS_DIR_NAME} ]]; then
    echo "INTERNAL ERROR: ${OPUS_SRC_DIR}/${OPUS_DIR_NAME} already exists"
    exit -1
fi

git clone https://github.com/SETI/rms-opus ${OPUS_DIR_NAME} 2>&1
cd ${OPUS_DIR_NAME}
git checkout ${OPUS_BRANCH}
python3.12 -m venv opus_venv 2>&1
source opus_venv/bin/activate
python -m pip install --upgrade pip 2>&1
python -m pip install -r requirements.txt 2>&1

# Create the opus_secrets.py file

echo "import os" > opus_secrets.py
echo "DB_BRAND = 'MySQL'" >> opus_secrets.py
echo "DB_HOST_NAME = 'localhost'" >> opus_secrets.py
echo "DB_DATABASE_NAME = ''" >> opus_secrets.py
echo "DB_SCHEMA_NAME = '${OPUS_DB_NAME}'" >> opus_secrets.py
echo "DB_USER = '${OPUS_DB_USER}'" >> opus_secrets.py
echo "DB_PASSWORD = '${OPUS_DB_PASSWORD}'" >> opus_secrets.py
echo "PDS3_DATA_DIR = '${PDS3_HOLDINGS_DIR}'" >> opus_secrets.py
echo "PDS4_DATA_DIR = '${PDS4_HOLDINGS_DIR}'" >> opus_secrets.py
echo "RMS_OPUS_PATH = '${OPUS_SRC_DIR}/${OPUS_DIR_NAME}'" >> opus_secrets.py
echo "RMS_OPUS_LIB_PATH = os.path.join(RMS_OPUS_PATH, 'lib')" >> opus_secrets.py
echo "ALLOWED_HOSTS = ('127.0.0.1', 'localhost'," >> opus_secrets.py
echo "                 'staging.pds.seti.org',      '10.1.10.15'," >> opus_secrets.py
echo "                 'tools2.pds-rings.seti.org', '104.244.248.30', 'tools2.pds.seti.org', '10.1.10.30'," >> opus_secrets.py
echo "                 'tools.pds-rings.seti.org',  '104.244.248.20', 'tools.pds.seti.org',  '10.1.10.20'," >> opus_secrets.py
echo "                 'opus.pds-rings.seti.org',   '104.244.248.40', 'opus.pds.seti.org',   '10.1.10.40')" >> opus_secrets.py
echo "SECRET_KEY = '${OPUS_SECRET_KEY}'" >> opus_secrets.py
echo "STATIC_ROOT = '${OPUS_DIR}/static_media'" >> opus_secrets.py
echo "OPUS_STATIC_ROOT = '${OPUS_DIR}/static_media'" >> opus_secrets.py
echo "CACHE_SERVER_PREFIX = 'production'" >> opus_secrets.py
echo "TAR_FILE_PATH = '${OPUS_DIR}/downloads/'" >> opus_secrets.py
echo "MANIFEST_FILE_PATH = '${OPUS_DIR}/manifests/'" >> opus_secrets.py
if [[ $HOSTNAME =~ ^staging.*$ ]]; then
    echo "DEBUG = True" >> opus_secrets.py
    echo "PUBLIC_OPUS_URL = 'http://staging.pds.seti.org/'" >> opus_secrets.py
    echo "PRODUCT_HTTP_PATH = 'http://staging.pds.seti.org/'" >> opus_secrets.py
    echo "VIEWMASTER_ROOT_PATH = 'http://staging.pds.seti.org/'" >> opus_secrets.py
    echo "TAR_FILE_URL_PATH = 'http://staging.pds.seti.org/downloads/'" >> opus_secrets.py
else
    echo "DEBUG = False" >> opus_secrets.py
    echo "PUBLIC_OPUS_URL = 'https://opus.pds-rings.seti.org/'" >> opus_secrets.py
    echo "PRODUCT_HTTP_PATH = 'https://opus.pds-rings.seti.org/'" >> opus_secrets.py
    echo "VIEWMASTER_ROOT_PATH = 'https://pds-rings.seti.org/'" >> opus_secrets.py
    echo "TAR_FILE_URL_PATH = 'https://opus.pds-rings.seti.org/downloads/'" >> opus_secrets.py
fi
echo "OPUS_LOGFILE_DIR = '${OPUS_LOG_DIR}/opus_logs'" >> opus_secrets.py
echo "OPUS_LOG_FILE = os.path.join(OPUS_LOGFILE_DIR, 'opus_log.txt')" >> opus_secrets.py
echo "OPUS_LAST_BLOG_UPDATE_FILE = '${LAST_BLOG_UPDATE_FILE}'" >> opus_secrets.py
echo "OPUS_NOTIFICATION_FILE = '${NOTIFICATION_FILE}'" >> opus_secrets.py
echo "OPUS_LOG_FILE_LEVEL = 'INFO'" >> opus_secrets.py
echo "OPUS_LOG_CONSOLE_LEVEL = 'INFO'" >> opus_secrets.py
echo "OPUS_LOG_DJANGO_LEVEL = 'WARN'" >> opus_secrets.py
echo "OPUS_LOG_API_CALLS = False" >> opus_secrets.py
echo "OPUS_FAKE_API_DELAYS = None" >> opus_secrets.py
echo "OPUS_FAKE_SERVER_ERROR404_PROBABILITY = 0." >> opus_secrets.py
echo "OPUS_FAKE_SERVER_ERROR500_PROBABILITY = 0." >> opus_secrets.py
echo "IMPORT_TABLE_TEMP_PREFIX = 'imp_'" >> opus_secrets.py
echo "IMPORT_LOGFILE_DIR = '${OPUS_LOG_DIR}'" >> opus_secrets.py
echo "IMPORT_LOG_FILE = os.path.join(IMPORT_LOGFILE_DIR, 'opus_import.log')" >> opus_secrets.py
echo "IMPORT_DEBUG_LOG_FILE = os.path.join(IMPORT_LOGFILE_DIR, 'opus_import_debug.log')" >> opus_secrets.py
echo "DICTIONARY_PDSDD_FILE = os.path.join(RMS_OPUS_PATH, 'dictionary/pdsdd.full')" >> opus_secrets.py
echo "DICTIONARY_CONTEXTS_FILE = os.path.join(RMS_OPUS_PATH, 'dictionary/contexts.csv')" >> opus_secrets.py
echo "DICTIONARY_JSON_SCHEMA_PATH = os.path.join(RMS_OPUS_PATH, 'opus/import/table_schemas')" >> opus_secrets.py

echo
echo
echo "opus_secrets.py:"
echo
cat opus_secrets.py
