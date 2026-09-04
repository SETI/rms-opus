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

PDS3_HOLDINGS_DIR=$PDS_HOLDINGS_ROOT/holdings
PDS4_HOLDINGS_DIR=$PDS_HOLDINGS_ROOT/pds4-holdings
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
# Every value below is interpolated into a TOML basic string, where a backslash
# escapes and a double quote ends the string. Escaping those two is not enough on
# its own: TOML also forbids a literal control character anywhere in a basic
# string, and no escape written here can smuggle one in. A newline or a tab in a
# password or a path is a configuration error rather than something to encode, so
# it is refused before anything is written, naming the variable at fault -- the
# alternative is a file that this script's own loader rejects at startup.
for _toml_var in \
    UNIQUE_ID OPUS_DB_USER OPUS_DB_PASSWORD PDS3_HOLDINGS_DIR PDS4_HOLDINGS_DIR \
    LOG_DIR DOWNLOAD_DIR DATA_DIR CWD; do
    case "${!_toml_var}" in
        *[[:cntrl:]]*)
            echo "ERROR: $_toml_var contains a control character (newline, tab or"
            echo "       similar). TOML forbids one inside a quoted value, so"
            echo "       opus.toml cannot be written. Correct the value and re-run."
            exit 1
            ;;
    esac
done
unset _toml_var

toml_escape() {
    printf '%s' "$1" | sed -e 's/\\/\\\\/g' -e 's/"/\\"/g'
}

( umask 077; cat > opus.toml.tmp <<EOF
[database]
brand = "MySQL"
host = "localhost"
database = ""
schema = "opus_test_db_$(toml_escape "${UNIQUE_ID}")"
user = "$(toml_escape "${OPUS_DB_USER}")"
password = "$(toml_escape "${OPUS_DB_PASSWORD}")"

[paths]
pds3_holdings = "$(toml_escape "${PDS3_HOLDINGS_DIR}")"
pds4_holdings = "$(toml_escape "${PDS4_HOLDINGS_DIR}")"
opus_log_file = "$(toml_escape "${LOG_DIR}")/opus_logs/opus_log.txt"
import_log_dir = "$(toml_escape "${LOG_DIR}")/import_logs"
tar_dir = "$(toml_escape "${DOWNLOAD_DIR}")/tar/"
manifest_dir = "$(toml_escape "${DOWNLOAD_DIR}")/manifest/"
last_blog_update_file = "$(toml_escape "${DATA_DIR}")/last_update.txt"
notification_file = "$(toml_escape "${DATA_DIR}")/notification.html"
opus_static_root = "$(toml_escape "${CWD}")/src/opus_app/static"

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
log_django_level = "WARNING"
log_api_calls = false
fake_error404_probability = 0.0
fake_error500_probability = 0.0

[import]
table_temp_prefix = "imp_"
log_file = "$(toml_escape "${LOG_DIR}")/import_logs/opus_import.log"
debug_log_file = "$(toml_escape "${LOG_DIR}")/import_logs/opus_import_debug.log"
EOF
)
if [ $? -ne 0 ]; then exit -1; fi
# The rename is atomic within the filesystem, so opus.toml is never present with
# the caller's umask while it already holds the database password.
mv opus.toml.tmp opus.toml
if [ $? -ne 0 ]; then exit -1; fi
chmod 600 opus.toml


echo "opus.toml:"
echo
cat opus.toml

exit 0
