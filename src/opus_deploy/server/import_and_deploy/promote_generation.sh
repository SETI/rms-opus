#!/bin/bash
#
# Switch the generation an incremental update wrote into the served database, or, with
# --revert, switch back to the generation served before it.
#
# Usage: promote_generation.sh [--revert]
#
# run_incremental_opus_update.sh leaves the update as a pending generation of the served
# schema, which the site does not show. The switch makes it the one served: it swaps in
# the auxiliary tables built from it, points the carts at its rows, and empties the stored
# searches (opus_import --switch-generation). The workers are stopped while it runs, and
# afterwards the cache service is restarted, the workers are started, and the common
# searches are warmed, as at the end of a deploy, because each worker and the shared cache
# hold what they read from the generation being replaced.
#
# It first asks whether opus_import would refuse the step -- no generation ready to switch,
# no switch to revert, another generation command holding the schema's generation lock,
# or an invocation still writing the pending generation -- and then stops nothing.
#
# **On failure the web service stays stopped.** Starting it on a half-switched schema
# would serve one generation's auxiliary tables, carts and caches against the other's
# rows. Running this again completes an interrupted switch; --revert runs the switch
# backward (opus_import --revert-generation), and starts the web service only when that
# succeeds. A revert is possible until opus_import --purge-generations deletes the rows the
# switch retired. A step refused after the stop changed nothing, and when the web service
# was serving before the stop, it is started again.
#
# It runs opus_import from the deployed installation, against the configuration it
# serves, and holds the deploy lock throughout, since it changes what is served.
set -e

# The status opus_import exits with when it refuses a generation command, having changed
# nothing (opus_import.steps.do_generation.GENERATION_REFUSED_EXIT_STATUS).
GENERATION_REFUSED_STATUS=3

REVERT=false
if [[ ${1:-} == --revert ]]; then
    REVERT=true
    shift
fi

if [[ $# -gt 0 ]]; then
    echo "Usage: promote_generation.sh [--revert]"
    echo
    echo "  --revert  switch back to the generation served before the last switch."
    exit 1
fi

export IMPORT_SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

export SCRIPT_DIR=`dirname ${IMPORT_SCRIPT_DIR}`
export SECRETS_DIR=${SCRIPT_DIR}/secrets

source ${IMPORT_SCRIPT_DIR}/_read_deploy_env.sh
source ${IMPORT_SCRIPT_DIR}/_deploy_lock.sh
if ! take_deploy_lock "${OPUS_DIR}/deploy.lock"; then
    echo "*** ABORTING: nothing was changed ***"
    exit 1
fi
source ${IMPORT_SCRIPT_DIR}/_promote_steps.sh
source ${IMPORT_SCRIPT_DIR}/_incremental_opus_update_steps.sh

DEPLOYED_DIR=${OPUS_DIR}/deployed
if ! OPUS_DB_NAME=$(served_schema_name "${DEPLOYED_DIR}/opus.toml"); then
    echo "*** ABORTING: nothing was changed ***"
    exit 1
fi

# The deployed installation's own opus_import and opus_manage, and the configuration it
# serves, which names the schema. The lock keeps any deploy from moving the symlink
# meanwhile.
INSTALL_DIR=$(readlink -f "${DEPLOYED_DIR}")
export OPUS_CONFIG=${INSTALL_DIR}/opus.toml
source "${INSTALL_DIR}/opus_venv/bin/activate"

if ${REVERT}; then
    STEP=--revert-generation
    echo "*** Reverting the last generation switch of ${OPUS_DB_NAME} ***"
else
    STEP=--switch-generation
    echo "*** Switching in the pending generation of ${OPUS_DB_NAME} ***"
fi
echo
echo "Installation: ${INSTALL_DIR}"
echo

# Asked before the stop, so a command opus_import would refuse leaves the site up.
if ! REFUSAL=$(python -c "from opus_import.steps.do_generation import generation_command_problem as p; print(p('${STEP}') or '')"); then
    echo "ERROR: cannot read the schema_version row of ${OPUS_DB_NAME}."
    echo "*** ABORTING: nothing was changed ***"
    exit 1
fi
if [[ -n ${REFUSAL} ]]; then
    echo "ERROR: opus_import ${STEP} would be refused: ${REFUSAL}."
    echo "*** ABORTING: nothing was changed ***"
    exit 1
fi

# Whether the site was serving before the stop: after a refusal, which changes nothing,
# starting the web service again restores what was served only if it was serving.
WAS_SERVING=false
if systemctl is-active --quiet "${OPUS_WEB_SERVICE}"; then
    WAS_SERVING=true
fi

sudo systemctl stop "${OPUS_WEB_SERVICE}"

STATUS=0
opus_import "${STEP}" || STATUS=$?
if [[ ${STATUS} -eq ${GENERATION_REFUSED_STATUS} ]]; then
    echo
    echo "ERROR: opus_import ${STEP} was refused, and changed nothing; its log says why."
    if ${WAS_SERVING}; then
        echo "       The web service is started again, serving what it served before."
        sudo systemctl start "${OPUS_WEB_SERVICE}"
    else
        echo "       The web service was stopped before this ran, and stays stopped: an"
        echo "       earlier switch or revert may have stopped part way. Once the cause"
        echo "       of the refusal is gone, run promote_generation.sh again, which"
        echo "       completes a switch, or promote_generation.sh --revert."
    fi
    exit 1
fi
if [[ ${STATUS} -ne 0 ]]; then
    echo
    echo "ERROR: opus_import ${STEP} failed. The web service stays stopped: starting it"
    echo "       on a half-switched schema would serve one generation's auxiliary"
    echo "       tables, carts and caches against the other's rows."
    if ${REVERT}; then
        echo "       Run promote_generation.sh --revert again, which completes the"
        echo "       interrupted revert."
    else
        echo "       Either run promote_generation.sh again, which completes the"
        echo "       interrupted switch, or run promote_generation.sh --revert."
    fi
    exit 1
fi

# The shared cache holds answers computed from the generation just replaced, and a cache
# key does not say which generation it was computed from. A failure is reported rather
# than fatal, because the switch is made and stopping here would leave the site down; an
# installation with no shared cache leaves OPUS_CACHE_SERVICE empty.
if [[ -n ${OPUS_CACHE_SERVICE} ]]; then
    if ! sudo systemctl restart "${OPUS_CACHE_SERVICE}"; then
        echo "WARNING: ${OPUS_CACHE_SERVICE} did not restart. If this installation"
        echo "         uses it, the shared cache still holds entries computed from the"
        echo "         generation that was replaced."
    fi
fi

sudo systemctl start "${OPUS_WEB_SERVICE}"

warm_search

OPUS_IMPORT_COMMAND="OPUS_CONFIG=${DEPLOYED_DIR}/opus.toml ${DEPLOYED_DIR}/opus_venv/bin/opus_import"
echo
if ${REVERT}; then
    echo "*** The generation served before the last switch is served again ***"
    echo
    echo "The reverted update is pending again. Throw it away with"
    echo "    ${OPUS_IMPORT_COMMAND} --abandon-generation"
    echo "or switch it in again with promote_generation.sh."
else
    echo "*** The new generation is served ***"
    echo
    echo "Check the site. Until the purge, promote_generation.sh --revert switches back."
    echo "Then delete the rows the switch retired, while the site serves:"
    echo "    ${OPUS_IMPORT_COMMAND} --purge-generations"
fi
