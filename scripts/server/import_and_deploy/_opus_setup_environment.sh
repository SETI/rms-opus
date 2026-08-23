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
# opus_support is imported from the installed distribution rather than
# through a sys.path insertion, so the package itself must be installed.
python -m pip install -e . 2>&1

# Create the opus.toml configuration file

if [[ $HOSTNAME =~ ^staging.*$ ]]; then
    OPUS_DEBUG=true
    OPUS_PUBLIC_URL=http://staging.pds.seti.org/
    OPUS_PRODUCT_HTTP_PATH=http://staging.pds.seti.org/
    OPUS_VIEWMASTER_URL=http://staging.pds.seti.org/
    OPUS_TAR_FILE_URL=http://staging.pds.seti.org/downloads/
else
    OPUS_DEBUG=false
    OPUS_PUBLIC_URL=https://opus.pds-rings.seti.org/
    OPUS_PRODUCT_HTTP_PATH=https://opus.pds-rings.seti.org/
    OPUS_VIEWMASTER_URL=https://pds-rings.seti.org/
    OPUS_TAR_FILE_URL=https://opus.pds-rings.seti.org/downloads/
fi

# On a deployed server collectstatic gathers the static files into
# ${OPUS_DIR}/static_media, which is unrelated to the in-repo source directory
# (src/opus_app/static), and both static_root and opus_static_root point there.
# Every value below is interpolated into a TOML basic string, where a backslash
# escapes and a double quote ends the string. Escaping those two is not enough on
# its own: TOML also forbids a literal control character anywhere in a basic
# string, and no escape written here can smuggle one in. A newline or a tab in a
# password or a path is a configuration error rather than something to encode, so
# it is refused before anything is written, naming the variable at fault -- the
# alternative is a file that this script's own loader rejects at startup.
for _toml_var in \
    OPUS_DB_NAME OPUS_DB_USER OPUS_DB_PASSWORD PDS3_HOLDINGS_DIR PDS4_HOLDINGS_DIR \
    OPUS_LOG_DIR OPUS_DIR LAST_BLOG_UPDATE_FILE NOTIFICATION_FILE OPUS_SECRET_KEY \
    OPUS_PUBLIC_URL OPUS_PRODUCT_HTTP_PATH OPUS_VIEWMASTER_URL OPUS_TAR_FILE_URL; do
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
schema = "$(toml_escape "${OPUS_DB_NAME}")"
user = "$(toml_escape "${OPUS_DB_USER}")"
password = "$(toml_escape "${OPUS_DB_PASSWORD}")"

[paths]
pds3_holdings = "$(toml_escape "${PDS3_HOLDINGS_DIR}")"
pds4_holdings = "$(toml_escape "${PDS4_HOLDINGS_DIR}")"
opus_log_file = "$(toml_escape "${OPUS_LOG_DIR}")/opus_logs/opus_log.txt"
import_log_dir = "$(toml_escape "${OPUS_LOG_DIR}")"
tar_dir = "$(toml_escape "${OPUS_DIR}")/downloads/"
manifest_dir = "$(toml_escape "${OPUS_DIR}")/manifests/"
last_blog_update_file = "$(toml_escape "${LAST_BLOG_UPDATE_FILE}")"
notification_file = "$(toml_escape "${NOTIFICATION_FILE}")"
static_root = "$(toml_escape "${OPUS_DIR}")/static_media"
opus_static_root = "$(toml_escape "${OPUS_DIR}")/static_media"

[django]
secret_key = "$(toml_escape "${OPUS_SECRET_KEY}")"
debug = ${OPUS_DEBUG}
allowed_hosts = [
    "127.0.0.1", "localhost",
    "staging.pds.seti.org", "10.1.10.15",
    "tools2.pds-rings.seti.org", "104.244.248.30", "tools2.pds.seti.org", "10.1.10.30",
    "tools.pds-rings.seti.org", "104.244.248.20", "tools.pds.seti.org", "10.1.10.20",
    "opus.pds-rings.seti.org", "104.244.248.40", "opus.pds.seti.org", "10.1.10.40",
]
cache_server_prefix = "production"
public_url = "$(toml_escape "${OPUS_PUBLIC_URL}")"
product_http_path = "$(toml_escape "${OPUS_PRODUCT_HTTP_PATH}")"
viewmaster_url = "$(toml_escape "${OPUS_VIEWMASTER_URL}")"
tar_file_url = "$(toml_escape "${OPUS_TAR_FILE_URL}")"
log_file_level = "INFO"
log_console_level = "INFO"
log_django_level = "WARNING"
log_api_calls = false
fake_error404_probability = 0.0
fake_error500_probability = 0.0

[import]
table_temp_prefix = "imp_"
log_file = "$(toml_escape "${OPUS_LOG_DIR}")/opus_import.log"
debug_log_file = "$(toml_escape "${OPUS_LOG_DIR}")/opus_import_debug.log"
EOF
)
# The rename is atomic within the filesystem, so opus.toml is never present with
# the caller's umask while it already holds the database password and secret key.
mv opus.toml.tmp opus.toml
chmod 600 opus.toml

# The import pipeline and the web application are installed packages, so they
# locate the configuration by this variable instead of by the directory they
# happen to be invoked from. This file is sourced, so the export reaches every
# later step of the deploy.
export OPUS_CONFIG=${OPUS_SRC_DIR}/${OPUS_DIR_NAME}/opus.toml

echo
echo
echo "opus.toml:"
echo
cat opus.toml
