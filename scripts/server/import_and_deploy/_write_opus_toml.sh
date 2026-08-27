#!/bin/bash
#
# Write a server installation's opus.toml from the deploy environment.
#
# Usage:
#     _write_opus_toml.sh <output_path>
#
# This is a separate program rather than a block inside _opus_setup_environment.sh
# so that it can be run on its own against a controlled environment and the file it
# produces loaded through opus_config.load_config -- which is what
# tests/opus_packaging/test_deploy_config_generator.py does. A generator whose only
# exercise is a production deploy is a generator nobody has checked.
#
# Every variable below must be exported by the caller. The deploy chain reads them
# from scripts/server/secrets/deploy.env (see deploy.env.template) plus the values
# _opus_setup_environment.sh derives per host.

set -euo pipefail

if [[ $# -ne 1 ]]; then
    echo "Usage: $(basename "$0") <output_path>" >&2
    exit 2
fi
OUTPUT_PATH=$1

# Every value below is interpolated into a TOML basic string, where a backslash
# escapes and a double quote ends the string. Escaping those two is not enough on its
# own: TOML also forbids a literal control character anywhere in a basic string, and
# no escape written here can smuggle one in. A newline or a tab in a password or a
# path is a configuration error rather than something to encode, so it is refused
# before anything is written, naming the variable at fault -- the alternative is a
# file that this installation's own loader rejects at startup.
#
# The same loop catches an unset or empty variable, so a deploy environment missing a
# key stops here rather than writing a file with an empty database password or -- the
# case that used to slip through the old opus_secrets reader entirely -- an empty
# Django secret key. `set -u` alone is not enough: it reports `!_toml_var: unbound
# variable`, naming this loop's own variable rather than the one the operator has to
# fix, so the check is explicit and the message names the culprit.
for _toml_var in \
    OPUS_DB_NAME OPUS_DB_USER OPUS_DB_PASSWORD PDS3_HOLDINGS_DIR PDS4_HOLDINGS_DIR \
    OPUS_LOG_DIR OPUS_DIR LAST_BLOG_UPDATE_FILE NOTIFICATION_FILE OPUS_SECRET_KEY \
    OPUS_PUBLIC_URL OPUS_PRODUCT_HTTP_PATH OPUS_VIEWMASTER_URL OPUS_TAR_FILE_URL; do
    if [[ ! -v $_toml_var ]]; then
        echo "ERROR: $_toml_var is not set in the deploy environment." >&2
        exit 1
    fi
    if [[ -z ${!_toml_var} ]]; then
        echo "ERROR: $_toml_var is empty in the deploy environment." >&2
        exit 1
    fi
    case "${!_toml_var}" in
        *[[:cntrl:]]*)
            echo "ERROR: $_toml_var contains a control character (newline, tab or" >&2
            echo "       similar). TOML forbids one inside a quoted value, so" >&2
            echo "       opus.toml cannot be written. Correct the value and re-run." >&2
            exit 1
            ;;
    esac
done
unset _toml_var

# OPUS_DEBUG is a TOML boolean rather than a string, so it is checked by value
# instead of being escaped. Anything else would produce a file the loader rejects.
case "${OPUS_DEBUG}" in
    true|false) ;;
    *)
        echo "ERROR: OPUS_DEBUG must be exactly 'true' or 'false' (got '${OPUS_DEBUG}')." >&2
        exit 1
        ;;
esac

toml_escape() {
    printf '%s' "$1" | sed -e 's/\\/\\\\/g' -e 's/"/\\"/g'
}

# On a deployed server collectstatic gathers the static files into
# ${OPUS_DIR}/static_media, which is unrelated to the source directory inside the
# installed distribution, and both static_root and opus_static_root point there.
( umask 077; cat > "${OUTPUT_PATH}.tmp" <<EOF
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
# The rename is atomic within the filesystem, so the destination is never present
# with the caller's umask while it already holds the database password and the
# Django secret key.
mv "${OUTPUT_PATH}.tmp" "${OUTPUT_PATH}"
chmod 600 "${OUTPUT_PATH}"
