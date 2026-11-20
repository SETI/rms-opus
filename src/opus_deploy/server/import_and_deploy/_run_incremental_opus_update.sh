#!/bin/bash
#
# Update the served database in place: import changed or new bundles, and drop others,
# as a pending import generation that the site does not show until promote_generation.sh
# switches it in. run_incremental_opus_update.sh runs this detached; it is not what an
# operator types.
#
# Usage: _run_incremental_opus_update.sh [<version_spec>] [--continue]
#            [--drop <bundle>[,<bundle>...]] [<bundle> ...]
#
# The update runs under an installation of its own, built beside the one being served
# and naming the same schema, as a full import's does: it installs the release the version
# specifier names, or with none the release being served, and its log directory is new, so
# ERRORS.log holds only what this run wrote. The steps are functions in
# _incremental_opus_update_steps.sh.
#
# It holds the deploy lock until it ends. It writes the served schema, and nothing else
# may run DDL on it meanwhile: a code-only deploy rebuilds tables the update's
# finalization also builds, a promotion switches the generation the update is writing,
# and either would spoil the dump that ends the update when deploy.env names a peer.
set -e

# The status opus_import exits with when it refuses a generation command, or when
# --check says an action would be refused, having changed nothing
# (opus_import.steps.do_generation.GENERATION_REFUSED_EXIT_STATUS).
GENERATION_REFUSED_STATUS=3

export IMPORT_SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

export SCRIPT_DIR=`dirname ${IMPORT_SCRIPT_DIR}`
export SECRETS_DIR=${SCRIPT_DIR}/secrets
export DATABASE_SCRIPT_DIR=${SCRIPT_DIR}/database

source ${IMPORT_SCRIPT_DIR}/_version_spec.sh
source ${IMPORT_SCRIPT_DIR}/_incremental_opus_update_steps.sh
if ! parse_update_arguments "$@"; then
    exit 1
fi

source ${IMPORT_SCRIPT_DIR}/_read_deploy_env.sh
source ${IMPORT_SCRIPT_DIR}/_deploy_lock.sh
if ! take_deploy_lock "${OPUS_DIR}/deploy.lock"; then
    echo "*** ABORTING: nothing was changed ***"
    exit 1
fi
source ${IMPORT_SCRIPT_DIR}/_activate_deploy_venv.sh
source ${IMPORT_SCRIPT_DIR}/_promote_steps.sh
source ${IMPORT_SCRIPT_DIR}/_copy_database_to_peer.sh

if ! OPUS_DB_NAME=$(served_schema_name "${OPUS_DIR}/deployed/opus.toml"); then
    echo "*** ABORTING: nothing was changed ***"
    exit 1
fi
export OPUS_DB_NAME

# The generation is switched in and served by the deployed installation, whose schema
# version --begin-generation requires, so with no version spec the update installs what
# it runs -- its release, or the git commit it was built from -- rather than the newest.
if [[ -z ${OPUS_VERSION_SPEC} ]]; then
    if ! OPUS_VERSION_SPEC=$(deployed_release_spec "${OPUS_DIR}/deployed"); then
        echo "*** ABORTING: nothing was changed ***"
        exit 1
    fi
fi
export OPUS_VERSION_SPEC
# After the specifier is settled, so the chain's release is checked against the one the
# update installs.
source ${IMPORT_SCRIPT_DIR}/_chain_version.sh

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
echo "Version spec:" "${OPUS_VERSION_SPEC}"
echo
if ${UPDATE_CONTINUE}; then
    echo "Continuing the pending generation an earlier update began"
    echo
fi
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

# Asked of the schema before anything writes it: an import with no pending generation
# takes the append path and writes the rows the site serves. The check logs its answer,
# which says why when the update cannot continue.
if ${UPDATE_CONTINUE}; then
    STATUS=0
    opus_import --check continue || STATUS=$?
    if [[ ${STATUS} -eq ${GENERATION_REFUSED_STATUS} ]]; then
        echo "ERROR: the update cannot continue; the check above says why."
        echo "*** ABORTING: the database was not changed ***"
        exit 1
    fi
    if [[ ${STATUS} -ne 0 ]]; then
        echo "ERROR: cannot read the schema_version row of ${OPUS_DB_NAME}."
        echo "*** ABORTING: the database was not changed ***"
        exit 1
    fi
fi

echo "======================================="
echo "=== WRITE THE NEW IMPORT GENERATION ==="
echo "======================================="
echo
echo "Start time:" `date`
echo
run_update_invocations "${OPUS_LOG_DIR}" || exit 1
echo
echo

copy_database_to_peer "${OPUS_DB_NAME}" "${PEER_DB_NAME}" || exit 1

echo "End time:" `date`
echo
echo "The new generation is ready to switch in, and the site does not show it yet."
echo "Read this log, then switch it in with promote_generation.sh."
echo
echo "============================================="
echo "=== ALL INCREMENTAL UPDATE TASKS COMPLETE ==="
echo "============================================="
