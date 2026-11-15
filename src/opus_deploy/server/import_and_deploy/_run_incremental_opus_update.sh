#!/bin/bash
#
# Update the served database in place: import changed or new bundles, and drop others,
# as a pending import generation that the site does not show until promote_generation.sh
# switches it in. run_incremental_opus_update.sh runs this detached; it is not what an
# operator types.
#
# Usage: _run_incremental_opus_update.sh [<version_spec>] [--drop <bundle>[,<bundle>...]] [<bundle> ...]
#
# The update runs under an installation of its own, built beside the one being served
# and naming the same schema, as a full import's does: it installs the release the version
# specifier names, and its log directory is new, so ERRORS.log holds only what this run
# wrote. The steps are functions in _incremental_opus_update_steps.sh.
#
# It holds the deploy lock until it ends. It writes the served schema, and nothing else
# may run DDL on it meanwhile: a code-only deploy rebuilds tables the update's
# finalization also builds, a promotion switches the generation the update is writing,
# and either would spoil the dump that ends the update when deploy.env names a peer.
set -e

export IMPORT_SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

export SCRIPT_DIR=`dirname ${IMPORT_SCRIPT_DIR}`
export SECRETS_DIR=${SCRIPT_DIR}/secrets
export DATABASE_SCRIPT_DIR=${SCRIPT_DIR}/database

source ${IMPORT_SCRIPT_DIR}/_incremental_opus_update_steps.sh
if ! parse_update_arguments "$@"; then
    exit 1
fi
export OPUS_VERSION_SPEC

source ${IMPORT_SCRIPT_DIR}/_read_deploy_env.sh
source ${IMPORT_SCRIPT_DIR}/_deploy_lock.sh
if ! take_deploy_lock "${OPUS_DIR}/deploy.lock"; then
    echo "*** ABORTING: nothing was changed ***"
    exit 1
fi
source ${IMPORT_SCRIPT_DIR}/_activate_deploy_venv.sh
source ${IMPORT_SCRIPT_DIR}/_chain_version.sh
source ${IMPORT_SCRIPT_DIR}/_promote_steps.sh
source ${IMPORT_SCRIPT_DIR}/_copy_database_to_peer.sh

if ! OPUS_DB_NAME=$(served_schema_name "${OPUS_DIR}/deployed/opus.toml"); then
    echo "*** ABORTING: nothing was changed ***"
    exit 1
fi
export OPUS_DB_NAME

export DATETIMEPID="`date +%Y%m%dT%H%M%S`_$$"
export OPUS_LOG_DIR=${OPUS_DIR}/import_logs/${DATETIMEPID}
export OPUS_SRC_DIR=${OPUS_DIR}/staged
export OPUS_DIR_NAME=${OPUS_DB_NAME}_${DATETIMEPID}
# A second server cannot take the update into the schema it serves, so it receives the
# whole updated schema under a name of its own.
PEER_DB_NAME=$(new_schema_name "${DATETIMEPID}")

mkdir -p ${OPUS_LOG_DIR}
mkdir -p ${OPUS_SRC_DIR}

HOSTNAME=`hostname`

echo "========================================"
echo "=== STARTING OPUS INCREMENTAL UPDATE ==="
echo "========================================"
echo
echo "Start time:" `date`
echo
echo "Hostname:" ${HOSTNAME}
echo
echo "Version spec:" "${OPUS_VERSION_SPEC:-(newest release)}"
echo
echo "Bundles to import:" "${UPDATE_BUNDLES[*]:-(none)}"
echo "Bundles to drop:" "${UPDATE_DROPS[*]:-(none)}"
echo
echo "OPUS_LOG_DIR: ${OPUS_LOG_DIR}"
echo "OPUS_SRC_DIR: ${OPUS_SRC_DIR}"
echo
echo "Served schema, updated: ${OPUS_DB_NAME}"
if [[ -n ${OPUS_PEER_DB_HOST} ]]; then
    echo "Copied to ${OPUS_PEER_DB_HOST} as: ${PEER_DB_NAME}"
fi
echo
echo

echo "==============================="
echo "=== SET UP OPUS ENVIRONMENT ==="
echo "==============================="
echo
echo "Start time:" `date`
echo
source ${IMPORT_SCRIPT_DIR}/_opus_setup_environment.sh
echo
echo

echo "======================================="
echo "=== WRITE THE NEW IMPORT GENERATION ==="
echo "======================================="
echo
echo "Start time:" `date`
echo
run_update_invocations "${OPUS_LOG_DIR}"
echo
echo

copy_database_to_peer "${OPUS_DB_NAME}" "${PEER_DB_NAME}"

echo "End time:" `date`
echo
echo "The new generation is ready to switch in, and the site does not show it yet."
echo "Read this log, then switch it in with promote_generation.sh."
echo
echo "============================================="
echo "=== ALL INCREMENTAL UPDATE TASKS COMPLETE ==="
echo "============================================="
