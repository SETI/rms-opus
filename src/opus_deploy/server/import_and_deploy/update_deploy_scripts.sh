#!/bin/bash
#
# Bring this copy of the deploy chain up to a release of OPUS.
#
# The chain ships inside the distribution, so a copy of it is one release's chain, and
# it changes between releases like anything else. Deploying a new release with an old
# chain runs one release's deploy against another release's application, which is how
# a step that a release added goes missing. **This is therefore the first command of
# every upgrade**, before the deploy itself:
#
#     ./import_and_deploy/update_deploy_scripts.sh ==3.24.1
#     ./import_and_deploy/deploy_new_code_only.sh  ==3.24.1
#
# It upgrades rms-opus in the environment named by OPUS_DEPLOY_VENV -- the one these
# commands come from, not any installation that serves anything -- and then rewrites
# this directory from it, ${SECRETS_DIR} excepted: secrets/ is not part of what ships,
# so it is not part of what is written.
#
# The body is a function called on the last line, and that is not a style: this script
# rewrites itself. Bash reads a script as it runs it, so a file replaced underneath it
# resumes at a byte offset into different text. Everything inside a function is parsed
# before the function is called, so by the time `opus_deploy_scripts` replaces this
# file, bash has nothing left to read from it.

main() {
    set -e

    if [[ $# > 1 ]]; then
        echo "Usage: update_deploy_scripts.sh [<version_spec>]"
        echo
        echo "  <version_spec>  a PEP 440 specifier appended to the distribution name,"
        echo "                  for example '==3.24.1'. Omit it for the newest release."
        exit 1
    fi

    local version_spec=${1:-}

    export IMPORT_SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
    export SCRIPT_DIR=`dirname ${IMPORT_SCRIPT_DIR}`
    export SECRETS_DIR=${SCRIPT_DIR}/secrets

    source ${IMPORT_SCRIPT_DIR}/_read_deploy_env.sh
    source ${IMPORT_SCRIPT_DIR}/_activate_deploy_venv.sh

    echo "*** Updating the deploy chain in ${SCRIPT_DIR} ***"
    echo
    if [[ -f ${SCRIPT_DIR}/CHAIN_VERSION ]]; then
        echo "From: rms-opus $(cat ${SCRIPT_DIR}/CHAIN_VERSION)"
    fi
    echo "To:   rms-opus ${version_spec:-(newest release)}"
    echo "In:   ${OPUS_DEPLOY_VENV}"
    echo

    python -m pip install --upgrade pip
    python -m pip install --upgrade "rms-opus${version_spec}"

    opus_deploy_scripts --directory ${SCRIPT_DIR} --force

    echo
    echo "*** The deploy chain is now rms-opus $(cat ${SCRIPT_DIR}/CHAIN_VERSION) ***"
}

main "$@"
