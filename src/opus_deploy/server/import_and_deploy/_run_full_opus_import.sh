#!/bin/bash
set -e

# A PEP 440 version specifier appended to the distribution name ("==3.23.0"),
# or empty for the newest release. The deploy installs rms-opus from PyPI, so
# this selects a release rather than a source revision.
export OPUS_VERSION_SPEC=${1:-}

export IMPORT_SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

export SCRIPT_DIR=`dirname ${IMPORT_SCRIPT_DIR}`
export SECRETS_DIR=${SCRIPT_DIR}/secrets
export DATABASE_SCRIPT_DIR=${SCRIPT_DIR}/database

source ${IMPORT_SCRIPT_DIR}/_read_deploy_env.sh
source ${IMPORT_SCRIPT_DIR}/_activate_deploy_venv.sh
source ${IMPORT_SCRIPT_DIR}/_chain_version.sh

export DATETIMEPID="`date +%Y%m%dT%H%M%S`_$$"
source ${IMPORT_SCRIPT_DIR}/_copy_database_to_peer.sh
export OPUS_DB_NAME=$(new_schema_name "${DATETIMEPID}")
export OPUS_LOG_DIR=${OPUS_DIR}/import_logs/${DATETIMEPID}

# The import runs under an installation of its own, built beside the one being
# served and never touching it. That is not tidiness: a release that changes the
# table schemas has to do the import itself, because the release now serving cannot
# write a database the new one will read. The installation goes where a deploy would
# find it, so that promoting the result afterwards is a switch rather than a rebuild.
export OPUS_SRC_DIR=${OPUS_DIR}/staged
export OPUS_DIR_NAME=${OPUS_DB_NAME}

mkdir -p ${OPUS_LOG_DIR}
mkdir -p ${OPUS_SRC_DIR}

HOSTNAME=`hostname`

echo "============================"
echo "=== STARTING OPUS IMPORT ==="
echo "============================"
echo
echo "Start time:" `date`
echo
echo "Hostname:" ${HOSTNAME}
echo
echo "Version spec:" "${OPUS_VERSION_SPEC:-(newest release)}"
echo
echo "PDS3_HOLDINGS_DIR: ${PDS3_HOLDINGS_DIR}"
echo "PDS4_HOLDINGS_DIR: ${PDS4_HOLDINGS_DIR}"
echo
echo "OPUS_LOG_DIR: ${OPUS_LOG_DIR}"
echo "OPUS_SRC_DIR: ${OPUS_SRC_DIR}"
echo
echo "OPUS_DB_NAME: ${OPUS_DB_NAME}"
echo
echo

echo "==============================="
echo "=== SET UP OPUS ENVIRONMENT ==="
echo "==============================="
echo
echo "Start time:" `date`
echo
source ${IMPORT_SCRIPT_DIR}/_opus_setup_environment.sh

# A stable name for the installation currently importing, so that its configuration
# and its virtualenv can be found without knowing the timestamp. It is a symlink of
# the same kind as ${OPUS_DIR}/deployed, and the two are what tell the staged
# installations apart.
ln -sfn ${OPUS_SRC_DIR}/${OPUS_DIR_NAME} ${OPUS_DIR}/import.new
mv -Tf ${OPUS_DIR}/import.new ${OPUS_DIR}/import
echo
echo

echo "=========================="
echo "=== IMPORT ALL BUNDLES ==="
echo "=========================="
echo
echo "Start time:" `date`
echo
source ${IMPORT_SCRIPT_DIR}/_opus_import_bundles.sh
echo
echo

# The dump, and the load onto a second server, that deploy.env asks for.
copy_database_to_peer "${OPUS_DB_NAME}" "${OPUS_DB_NAME}"

echo "End time:" `date`
echo
echo "================================="
echo "=== ALL IMPORT TASKS COMPLETE ==="
echo "================================="
