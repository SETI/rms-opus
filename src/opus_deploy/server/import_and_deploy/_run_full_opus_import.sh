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
export OPUS_DB_NAME="opus3_${DATETIMEPID}"
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
echo "=== IMPORT ALL VOLUMES ==="
echo "=========================="
echo
echo "Start time:" `date`
echo
source ${IMPORT_SCRIPT_DIR}/_opus_import_volumes.sh
echo
echo

# What happens to the finished database, which is whatever deploy.env asked for. With
# OPUS_DB_DUMP_DIR empty the import is done when the database is built -- a dump of the
# full holdings is tens of gigabytes and hours of writing, so it happens because a
# server asked for it. With a directory but no peer, the dump is written and stays
# there; with both, it is written and loaded onto the second server. A peer with no
# directory cannot happen: _read_deploy_env.sh refuses that combination before any of
# this runs.
if [[ -n ${OPUS_DB_DUMP_DIR} ]]; then
    echo "================================"
    echo "=== DUMP DATABASE TO ARCHIVE ==="
    echo "================================"
    echo
    echo "Start time:" `date`
    echo
    "${DATABASE_SCRIPT_DIR}/dump_db.sh" "${OPUS_DB_NAME}"
    echo
    echo

    if [[ -n ${OPUS_PEER_DB_HOST} ]]; then
        echo "==========================================="
        echo "=== LOAD DATABASE ON THE SECOND SERVER  ==="
        echo "==========================================="
        echo
        echo "Start time:" `date`
        echo
        "${DATABASE_SCRIPT_DIR}/load_db.sh" "${OPUS_DB_NAME}"
        echo
        echo
    fi
fi

echo "End time:" `date`
echo
echo "================================="
echo "=== ALL IMPORT TASKS COMPLETE ==="
echo "================================="
