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
#
# The peer builds the database's ngram FULLTEXT indexes as it loads, under this load's
# session, and the dump sets neither of the two settings they depend on. So the load
# refuses, before it creates anything, a peer whose ngram_token_size is not 2: the web
# application searches for runs of two characters, and the server reads the setting
# only when it starts. And it turns the stopword list off for its session, since the
# ngram parser drops every token holding a stopword ("a" and "i" among them).
# _load_db_steps.sh holds the load itself.
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

source "${SCRIPT_DIR}/_load_db_steps.sh"

echo "Loading ${DATABASE} onto ${OPUS_PEER_DB_HOST} from ${SQLDUMP}"
load_dump "${DATABASE}" "${SQLDUMP}"
