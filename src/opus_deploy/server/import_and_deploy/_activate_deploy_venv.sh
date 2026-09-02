# This file should only be used with "source"
#
# Activate the virtual environment the deploy chain's own commands come from.
#
# Every script here activates it for itself rather than expecting the operator to have
# done it: a deploy is also run from cron and from nohup, where there is no operator
# and no shell that ever activated anything, and a script that quietly used whichever
# python happened to be first on PATH would install into it.
#
# This is not one of the installations under ${OPUS_DIR}/staged. Those are what a
# deploy builds and replaces; this one holds the release whose deploy chain is in this
# directory, and update_deploy_scripts.sh is what moves it forward.
# _opus_setup_environment.sh deactivates it before activating the installation it
# builds, so that the console scripts a deploy runs are unambiguously that
# installation's.
#
# Inputs: OPUS_DEPLOY_VENV, from deploy.env.

if [[ ! -v OPUS_DEPLOY_VENV ]]; then
    echo "INTERNAL ERROR: OPUS_DEPLOY_VENV undefined"
    exit 1
fi

if [[ ! -f "${OPUS_DEPLOY_VENV}/bin/activate" ]]; then
    echo "No virtual environment at ${OPUS_DEPLOY_VENV}."
    echo "OPUS_DEPLOY_VENV in deploy.env has to name the environment these scripts"
    echo "were written out of:"
    echo
    echo "    python3.12 -m venv \"${OPUS_DEPLOY_VENV}\""
    echo "    source \"${OPUS_DEPLOY_VENV}/bin/activate\""
    echo "    python -m pip install rms-opus"
    echo
    exit 1
fi

source "${OPUS_DEPLOY_VENV}/bin/activate"
