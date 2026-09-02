#!/bin/bash
#
# Deploy a new OPUS installation against a newly imported database.
#
# We assume a directory structure like:
#    /opus/src/rms-opus_<databasename>          the installation: opus_venv,
#                                               opus.toml and the wsgi.py symlink
#    /opus/src/rms-opus                         a symlink to the current one
#
# The installation is a virtualenv with the released rms-opus distribution in it,
# not a checkout: nothing here builds from source. The only checkout on the server
# is the one holding these scripts, which is where deploy.env lives too.
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

export OPUS_LOG_DIR=${OPUS_DIR}/opus_logs
export OPUS_SRC_DIR=${OPUS_DIR}/src
export OPUS_DIR_NAME=rms-opus_${OPUS_DB_NAME}

mkdir -p ${OPUS_LOG_DIR}/opus_logs
if [ -f ${OPUS_LOG_DIR}/opus_logs/opus_log.txt ]; then
    sudo chmod ug+w ${OPUS_LOG_DIR}/opus_logs/opus_log.txt
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
echo "OPUS_SRC_DIR: ${OPUS_SRC_DIR}"
echo
echo "OPUS_DB_NAME: ${OPUS_DB_NAME}"
echo

# Get sudo password input and cached
sudo echo

sudo systemctl stop apache2
sudo systemctl stop memcached

sudo rm -rf ${OPUS_SRC_DIR}/rms-opus
sudo rm -rf ${OPUS_SRC_DIR}/${OPUS_DIR_NAME}

source ${IMPORT_SCRIPT_DIR}/_opus_setup_environment.sh
pip install mod-wsgi

ln -s ${OPUS_SRC_DIR}/${OPUS_DIR_NAME} ${OPUS_SRC_DIR}/rms-opus

# Apache's vhost points at ${OPUS_SRC_DIR}/rms-opus/wsgi.py, the symlink
# _opus_setup_environment.sh wrote into this installation. That path is stable
# across deploys; the file it points at is inside the virtualenv's site-packages
# and moves with the Python version. docs/user_guide_deployment.rst has the stanza.

# Django's contrib tables (sessions, auth, contenttypes, admin). The OPUS tables
# are created from scratch by the import and have no migrations. `opus_manage` is
# Django's own command line with the settings module already named, so OPUS_CONFIG,
# exported above, is all it needs; the installed distribution ships no manage.py.
opus_manage migrate
opus_manage collectstatic --noinput
python -m opus_app.clear_django_cache

opus_import --import-dictionary --cleanup-aux-tables

sudo systemctl start memcached
sudo systemctl start apache2

echo
echo "*** New code and database deployed! ***"
