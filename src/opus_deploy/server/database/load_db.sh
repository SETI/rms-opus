#!/bin/bash
#
# Load a dumped database onto the second server.
#
# Usage: load_db.sh <dumped database name> [<target database name>]
#
# It reads the dump dump_db.sh wrote of the first database and creates the second on the
# peer from it; without a second name, the database keeps the dump's name. Where it reads
# and which server it loads onto come from deploy.env: OPUS_DB_DUMP_DIR and
# OPUS_PEER_DB_HOST. Nothing here knows the name of any machine, and with no peer
# configured there is nothing for this to do, which it says.
#
# It is the other half of dump_db.sh. Both run scripts, run_full_opus_import.sh and
# run_incremental_opus_update.sh, call the pair through copy_database_to_peer
# (import_and_deploy/_copy_database_to_peer.sh) at their end. A full import loads its new
# database under its own name; an incremental update loads the served database under a
# new one, since the peer's own served database cannot be loaded over.
set -e

if [[ $# -lt 1 || $# -gt 2 ]]; then
    echo "Usage: $(basename "$0") <dumped_database_name> [<target_database_name>]" >&2
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

DUMPED=$1
DATABASE=${2:-$1}
SQLDUMP="${OPUS_DB_DUMP_DIR}/${DUMPED}.sql"

if [[ ! -f ${SQLDUMP} ]]; then
    echo "${SQLDUMP} does not exist. Run dump_db.sh ${DUMPED} first."
    exit 1
fi

echo "Loading ${DATABASE} onto ${OPUS_PEER_DB_HOST} from ${SQLDUMP}"
# The database is created first because a dump holds no CREATE DATABASE, and the load
# needs something to select. It fails if the database is already there, which is the
# refusal to want: loading over a database somebody is serving would replace it row by
# row while they read it.
echo "CREATE DATABASE ${DATABASE};" \
    | mysql -u"${OPUS_DB_USER}" -p"${OPUS_DB_PASSWORD}" -h "${OPUS_PEER_DB_HOST}"
# A view's definer names an account of the first server, which the second may not have
# and which only an account with SET_USER_ID may name. The obs_general view runs with its
# reader's rights (SQL SECURITY INVOKER), so the clause is dropped from the dump as it is
# read.
set -o pipefail
sed -e 's/ DEFINER=`[^`]*`@`[^`]*`//g' "${SQLDUMP}" \
    | mysql -u"${OPUS_DB_USER}" -p"${OPUS_DB_PASSWORD}" -h "${OPUS_PEER_DB_HOST}" \
        "${DATABASE}"
