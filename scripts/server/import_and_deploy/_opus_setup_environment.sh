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
cat > opus.toml <<EOF
[database]
brand = "MySQL"
host = "localhost"
database = ""
schema = "${OPUS_DB_NAME}"
user = "${OPUS_DB_USER}"
password = "${OPUS_DB_PASSWORD}"

[paths]
pds3_holdings = "${PDS3_HOLDINGS_DIR}"
pds4_holdings = "${PDS4_HOLDINGS_DIR}"
opus_log_file = "${OPUS_LOG_DIR}/opus_logs/opus_log.txt"
import_log_dir = "${OPUS_LOG_DIR}"
tar_dir = "${OPUS_DIR}/downloads/"
manifest_dir = "${OPUS_DIR}/manifests/"
last_blog_update_file = "${LAST_BLOG_UPDATE_FILE}"
notification_file = "${NOTIFICATION_FILE}"
static_root = "${OPUS_DIR}/static_media"
opus_static_root = "${OPUS_DIR}/static_media"

[django]
secret_key = "${OPUS_SECRET_KEY}"
debug = ${OPUS_DEBUG}
allowed_hosts = [
    "127.0.0.1", "localhost",
    "staging.pds.seti.org", "10.1.10.15",
    "tools2.pds-rings.seti.org", "104.244.248.30", "tools2.pds.seti.org", "10.1.10.30",
    "tools.pds-rings.seti.org", "104.244.248.20", "tools.pds.seti.org", "10.1.10.20",
    "opus.pds-rings.seti.org", "104.244.248.40", "opus.pds.seti.org", "10.1.10.40",
]
cache_server_prefix = "production"
public_url = "${OPUS_PUBLIC_URL}"
product_http_path = "${OPUS_PRODUCT_HTTP_PATH}"
viewmaster_url = "${OPUS_VIEWMASTER_URL}"
tar_file_url = "${OPUS_TAR_FILE_URL}"
log_file_level = "INFO"
log_console_level = "INFO"
log_django_level = "WARNING"
log_api_calls = false
fake_error404_probability = 0.0
fake_error500_probability = 0.0

[import]
table_temp_prefix = "imp_"
log_file = "${OPUS_LOG_DIR}/opus_import.log"
debug_log_file = "${OPUS_LOG_DIR}/opus_import_debug.log"
EOF

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
