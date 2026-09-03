#!/bin/bash
#
# Deploy a release together with the database it imported.
#
# This is the deploy to use whenever the database has been rebuilt -- which is every
# release that changes the table schemas, because such a release cannot read a
# database the previous one imported. The import that built that database ran under
# its own installation of the same release (run_full_opus_import.sh); this builds a
# fresh installation naming that database and switches to it.
#
# The layout it works in:
#    /opt/opus/staged/<database>_<timestamp>/   an installation: opus_venv, opus.toml
#                                              and the wsgi.py symlink
#    /opt/opus/deployed                         a symlink to the one being served
#
# An installation is a virtualenv with the released rms-opus distribution in it, not
# a checkout: nothing here builds from source, and nothing on the server needs one.
# These scripts are themselves part of the distribution, written out with
# `opus_deploy_scripts`; run them from that copy rather than from inside an
# installation, which a deploy replaces.
#
set -e

echo "*** Starting CODE & DATABASE OPUS deploy ***"
echo

if [[ $# < 1 || $# > 2 ]]; then
    echo "Usage: deploy_new_code_and_database.sh <database_name> [<version_spec>]"
    echo
    echo "  <version_spec>  a PEP 440 specifier appended to the distribution name,"
    echo "                  for example '==3.23.0'. Omit it to install the newest"
    echo "                  release. The deploy installs rms-opus from PyPI, so this"
    echo "                  selects a release rather than a source revision."
    exit 1
fi

export OPUS_DB_NAME=$1
export OPUS_VERSION_SPEC=${2:-}

export IMPORT_SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

export SCRIPT_DIR=`dirname ${IMPORT_SCRIPT_DIR}`
export SECRETS_DIR=${SCRIPT_DIR}/secrets

source ${IMPORT_SCRIPT_DIR}/_read_deploy_env.sh
source ${IMPORT_SCRIPT_DIR}/_activate_deploy_venv.sh
source ${IMPORT_SCRIPT_DIR}/_chain_version.sh

export OPUS_LOG_DIR=${OPUS_DIR}/opus_logs
export OPUS_SRC_DIR=${OPUS_DIR}/staged
# Every build gets a directory of its own, named for the database it serves and the
# moment it was built. Nothing is built over: the installation being served is still
# there afterwards, which is what makes a bad deploy a switch back rather than a
# rebuild.
export OPUS_DIR_NAME=${OPUS_DB_NAME}_`date +%Y%m%dT%H%M%S`
INSTALL_DIR=${OPUS_SRC_DIR}/${OPUS_DIR_NAME}

mkdir -p ${OPUS_LOG_DIR}
# The application's log outlives the installation that wrote it, so a file left by a
# deploy that ran as another account is made writable again rather than being an
# installation that starts and cannot log.
if [ -f ${OPUS_LOG_DIR}/opus_log.txt ]; then
    sudo chmod ug+w ${OPUS_LOG_DIR}/opus_log.txt
fi
mkdir -p ${OPUS_SRC_DIR}

echo "Hostname:" ${HOSTNAME}
echo
echo "Version spec:" "${OPUS_VERSION_SPEC:-(newest release)}"
echo
echo "PDS3_HOLDINGS_DIR: ${PDS3_HOLDINGS_DIR}"
echo "PDS4_HOLDINGS_DIR: ${PDS4_HOLDINGS_DIR}"
echo
echo "OPUS_LOG_DIR: ${OPUS_LOG_DIR}"
echo "Staging into: ${INSTALL_DIR}"
echo
echo "OPUS_DB_NAME: ${OPUS_DB_NAME}"
echo

# Get sudo password input and cached, before anything long runs: the switch at the
# end needs it, and being asked for it then would leave a built installation waiting
# on a prompt nobody is watching.
sudo echo

# Everything from here to the switch happens beside the running installation, which
# goes on serving.
source ${IMPORT_SCRIPT_DIR}/_opus_setup_environment.sh
pip install mod-wsgi

# Django's contrib tables (sessions, auth, contenttypes, admin). The OPUS tables
# are created from scratch by the import and have no migrations. `opus_manage` is
# Django's own command line with the settings module already named, so OPUS_CONFIG,
# which _opus_setup_environment.sh exported, is all it needs.
opus_manage migrate
opus_manage collectstatic --noinput

opus_import --import-dictionary --cleanup-aux-tables

# The staged installation is complete. Switch to it, empty the shared cache, and
# restart the workers.
source ${IMPORT_SCRIPT_DIR}/_promote.sh

echo
echo "*** New code and database deployed! ***"
