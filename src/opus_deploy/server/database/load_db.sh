#!/bin/bash
#
# Load a dumped database onto the second server.
#
# Usage: load_db.sh <database name>
#
# Where it reads and which server it loads onto come from deploy.env:
# OPUS_DB_DUMP_DIR and OPUS_PEER_DB_HOST. Nothing here knows the name of any machine,
# and with no peer configured there is nothing for this to do, which it says.
#
# It is the other half of dump_db.sh, and run_full_opus_import.sh runs the pair at the
# end of an import.
set -e

if [[ $# -ne 1 ]]; then
    echo "Usage: $(basename "$0") <database_name>" >&2
    exit 2
fi

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
SCRIPT_ROOT=$(dirname "${SCRIPT_DIR}")
export SECRETS_DIR="${SCRIPT_ROOT}/secrets"
source "${SCRIPT_ROOT}/import_and_deploy/_read_deploy_env.sh"

if [[ -z ${OPUS_PEER_DB_HOST} ]]; then
    echo "OPUS_PEER_DB_HOST is empty in ${SECRETS_DIR}/deploy.env: there is no second"
    echo "server to load onto."
    exit 1
fi

DATABASE=$1
SQLDUMP="${OPUS_DB_DUMP_DIR}/${DATABASE}.sql"

if [[ ! -f ${SQLDUMP} ]]; then
    echo "${SQLDUMP} does not exist. Run dump_db.sh ${DATABASE} first."
    exit 1
fi

echo "Loading ${DATABASE} onto ${OPUS_PEER_DB_HOST} from ${SQLDUMP}"
# The database is created first because a dump holds no CREATE DATABASE, and the load
# needs something to select. It fails if the database is already there, which is the
# refusal to want: loading over a database somebody is serving would replace it row by
# row while they read it.
echo "CREATE DATABASE ${DATABASE};" \
    | mysql -u"${OPUS_DB_USER}" -p"${OPUS_DB_PASSWORD}" -h "${OPUS_PEER_DB_HOST}"
mysql -u"${OPUS_DB_USER}" -p"${OPUS_DB_PASSWORD}" -h "${OPUS_PEER_DB_HOST}" \
    "${DATABASE}" < "${SQLDUMP}"
