#!/bin/bash
# Arg 1: Unique ID

source ~/opus_runner_secrets

UNIQUE_ID=$1
TEST_CAT=opus
TEST_CAT_DIR=$TEST_ROOT/$TEST_CAT/$UNIQUE_ID
TEST_LOG_DIR=$TEST_CAT_DIR/test_logs
LOG_DIR=$TEST_CAT_DIR/temp_logs
DOWNLOAD_DIR=$TEST_CAT_DIR/downloads
DATA_DIR=$TEST_CAT_DIR/data

PDS3_HOLDINGS_DIR=$PDS_DROPBOX_ROOT/holdings
PDS4_HOLDINGS_DIR=$PDS_DROPBOX_ROOT/pds4-holdings
if [ ! -d "$PDS3_HOLDINGS_DIR" ]; then
    echo "Directory not found:" $PDS3_HOLDINGS_DIR
    exit -1
fi
if [ ! -d "$PDS4_HOLDINGS_DIR" ]; then
    echo "Directory not found:" $PDS4_HOLDINGS_DIR
    exit -1
fi

# Create the opus.toml configuration file

echo "Ignore any error about pwd here..."
CWD=`pwd -W` # So Windows bash will return a directory with C:
if [ $? -ne 0 ]; then
    CWD=`pwd`
fi

# Enable these commands to override the default PdsFile with a particular branch
# git clone https://github.com/SETI/rms-pdsfile
# (cd rms-pdsfile; git checkout rf_251117_gossi)
# pip uninstall -y rms-pdsfile
# pip install -e ./rms-pdsfile

# paths.static_root is deliberately absent: collectstatic never runs here, so
# Django's own default applies. django.fake_api_delays is absent for the same
# kind of reason: the tests delay nothing.
cat > opus.toml <<EOF
[database]
brand = "MySQL"
host = "localhost"
database = ""
schema = "opus_test_db_${UNIQUE_ID}"
user = "${OPUS_DB_USER}"
password = "${OPUS_DB_PASSWORD}"

[paths]
pds3_holdings = "${PDS3_HOLDINGS_DIR}"
pds4_holdings = "${PDS4_HOLDINGS_DIR}"
opus_log_file = "${LOG_DIR}/opus_logs/opus_log.txt"
import_log_dir = "${LOG_DIR}/import_logs"
tar_dir = "${DOWNLOAD_DIR}/tar/"
manifest_dir = "${DOWNLOAD_DIR}/manifest/"
last_blog_update_file = "${DATA_DIR}/last_update.txt"
notification_file = "${DATA_DIR}/notification.html"
opus_static_root = "${CWD}/src/opus_app/static"

[django]
secret_key = "fred"
debug = true
allowed_hosts = ["127.0.0.1", "localhost"]
cache_server_prefix = "staging_test"
public_url = "https://opus.pds-rings.seti.org/"
product_http_path = "https://opus.pds-rings.seti.org/"
viewmaster_url = "https://pds-rings.seti.org/"
tar_file_url = "https://bad-host.org/"
log_file_level = "INFO"
log_console_level = "INFO"
log_django_level = "WARN"
log_api_calls = false
fake_error404_probability = 0.0
fake_error500_probability = 0.0

[import]
table_temp_prefix = "imp_"
log_file = "${LOG_DIR}/import_logs/opus_import.log"
debug_log_file = "${LOG_DIR}/import_logs/opus_import_debug.log"
EOF
if [ $? -ne 0 ]; then exit -1; fi

echo "opus.toml:"
echo
cat opus.toml

exit 0
