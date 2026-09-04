#!/bin/bash
#
# Dump one database to a file, so that a second server can load it.
#
# Usage: dump_db.sh <database name>
#
# Where it writes and which server it reads come from deploy.env: OPUS_DB_DUMP_DIR
# and OPUS_DB_HOST. Nothing here knows the name of any machine, and with no dump
# directory configured there is nowhere to write, which it says.
#
# run_full_opus_import.sh runs this at the end of an import when OPUS_DB_DUMP_DIR
# names a directory, and load_db.sh after it when OPUS_PEER_DB_HOST names a second
# server as well.
set -e

if [[ $# -ne 1 ]]; then
    echo "Usage: $(basename "$0") <database_name>" >&2
    exit 2
fi

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
SCRIPT_ROOT=$(dirname "${SCRIPT_DIR}")
export SECRETS_DIR="${SCRIPT_ROOT}/secrets"
source "${SCRIPT_ROOT}/import_and_deploy/_read_deploy_env.sh"

if [[ -z ${OPUS_DB_DUMP_DIR} ]]; then
    echo "OPUS_DB_DUMP_DIR is empty in ${SECRETS_DIR}/deploy.env: there is nowhere to"
    echo "write a dump. Set it to a directory this account can write to."
    exit 1
fi

DATABASE=$1
SQLDUMP="${OPUS_DB_DUMP_DIR}/${DATABASE}.sql"

mkdir -p "${OPUS_DB_DUMP_DIR}"

echo "Dumping ${DATABASE} from ${OPUS_DB_HOST} to ${SQLDUMP}"
# The password reaches mysqldump on its command line, where `ps` can see it for as
# long as the dump runs. That is how this chain has always passed it; a .my.cnf owned
# by OPUS_USER would be the way to stop doing so.
mysqldump -u"${OPUS_DB_USER}" -p"${OPUS_DB_PASSWORD}" -h "${OPUS_DB_HOST}" \
    "${DATABASE}" > "${SQLDUMP}"
