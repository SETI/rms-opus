#!/bin/bash
#
# Dump one database to a file, so that a second server can load it.
#
# Usage: dump_db.sh <database name> [<dump name>]
#
# It writes <dump name>.sql, or <database name>.sql without a second name. Where it
# writes and which server it reads come from deploy.env: OPUS_DB_DUMP_DIR and
# OPUS_DB_HOST. Nothing here knows the name of any machine, and with no dump directory
# configured there is nowhere to write, which it says.
#
# Both run scripts, run_full_opus_import.sh and run_incremental_opus_update.sh, call it
# through copy_database_to_peer (import_and_deploy/_copy_database_to_peer.sh) at their end
# when OPUS_DB_DUMP_DIR names a directory, and load_db.sh after it when OPUS_PEER_DB_HOST
# names a second server as well.
set -e

if [[ $# -lt 1 || $# -gt 2 ]]; then
    echo "Usage: $(basename "$0") <database_name> [<dump_name>]" >&2
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
SQLDUMP="${OPUS_DB_DUMP_DIR}/${2:-$1}.sql"

mkdir -p "${OPUS_DB_DUMP_DIR}"

echo "Dumping ${DATABASE} from ${OPUS_DB_HOST} to ${SQLDUMP}"
# The password reaches mysqldump on its command line, where `ps` can see it for as
# long as the dump runs. That is how this chain has always passed it; a .my.cnf owned
# by OPUS_USER would be the way to stop doing so.
#
# --single-transaction reads every table in one consistent snapshot and takes no table
# locks, so the dump of a database that is being served is whole while the site goes on
# writing carts and searches to it. The snapshot does not survive DDL on the tables it
# reads, which is why nothing that runs DDL on the database may run during a dump.
mysqldump --single-transaction -u"${OPUS_DB_USER}" -p"${OPUS_DB_PASSWORD}" \
    -h "${OPUS_DB_HOST}" "${DATABASE}" > "${SQLDUMP}"
