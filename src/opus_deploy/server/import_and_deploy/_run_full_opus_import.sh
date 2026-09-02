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

mkdir -p ${OPUS_LOG_DIR}/opus_logs
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

if [[ ${HOSTNAME} =~ ^tools.*$ ]]; then
    echo "================================"
    echo "=== DUMP DATABASE TO ARCHIVE ==="
    echo "================================"
    echo
    echo "Start time:" `date`
    echo
    if [[ ${HOSTNAME} =~ ^tools(\.pds.*)?$ ]]; then
        ${DATABASE_SCRIPT_DIR}/dump_db_from_tools.sh ${OPUS_DB_NAME}
    else
        ${DATABASE_SCRIPT_DIR}/dump_db_from_tools2.sh ${OPUS_DB_NAME}
    fi
    echo
    echo
fi

if [[ ${HOSTNAME} =~ ^tools(\.pds.*)?$ ]]; then
    echo "============================================"
    echo "=== LOAD DATABASE ON TOOLS2 FROM ARCHIVE ==="
    echo "============================================"
    echo
    echo "Start time:" `date`
    echo
    ${DATABASE_SCRIPT_DIR}/load_tools2_db_from_dump.sh ${OPUS_DB_NAME}
    echo
    echo
elif [[ ${HOSTNAME} =~ ^tools2(\.pds.*)?$ ]]; then
    echo "==========================================="
    echo "=== LOAD DATABASE ON TOOLS FROM ARCHIVE ==="
    echo "==========================================="
    echo
    echo "Start time:" `date`
    echo
    ${DATABASE_SCRIPT_DIR}/load_tools_db_from_dump.sh ${OPUS_DB_NAME}
    echo
    echo
fi

echo "End time:" `date`
echo
echo "================================="
echo "=== ALL IMPORT TASKS COMPLETE ==="
echo "================================="
