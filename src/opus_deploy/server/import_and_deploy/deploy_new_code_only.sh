#!/bin/bash
#
# Deploy a release against the database already being served.
#
# **Only for a release that does not change the database schema.** Every OPUS table
# is created by the import pipeline from the JSON table schemas that ship with the
# release, so a release that changes one of them cannot read a database an earlier
# release imported: columns it expects are missing, and columns it does not know
# about are there. Nothing here can tell the two cases apart -- a database carries no
# record of the release that wrote it -- so it is the operator's call, from the
# release notes. When the schemas did change, the deploy is an import under the new
# release (run_full_opus_import.sh) followed by deploy_new_code_and_database.sh.
#
# What this does not do, deliberately, is upgrade the running installation in place.
# A pip upgrade rewrites the files a running Apache is serving from, and these very
# scripts are part of the distribution being upgraded. Instead it builds a new
# installation beside the running one, pointing at the same database, and switches to
# it with one rename:
#
#    /opt/opus/staged/<database>_<timestamp>/   the new installation
#    /opt/opus/deployed                         a symlink, moved onto it at the end
#
set -e

echo "*** Starting code-only OPUS deploy ***"
echo

if [[ $# > 1 ]]; then
    echo "Usage: deploy_new_code_only.sh [<version_spec>]"
    echo
    echo "  <version_spec>  a PEP 440 specifier appended to the distribution name,"
    echo "                  for example '==3.23.0'. Omit it to install the newest"
    echo "                  release. The deploy installs rms-opus from PyPI, so this"
    echo "                  selects a release rather than a source revision."
    exit 1
fi

export OPUS_VERSION_SPEC=${1:-}

export IMPORT_SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

export SCRIPT_DIR=`dirname ${IMPORT_SCRIPT_DIR}`
export SECRETS_DIR=${SCRIPT_DIR}/secrets

source ${IMPORT_SCRIPT_DIR}/_read_deploy_env.sh
source ${IMPORT_SCRIPT_DIR}/_chain_version.sh

DEPLOYED_DIR=${OPUS_DIR}/deployed

if [[ ! -f ${DEPLOYED_DIR}/opus.toml ]]; then
    echo "No installation is deployed: ${DEPLOYED_DIR}/opus.toml does not exist."
    echo "Run deploy_new_code_and_database.sh to create one."
    echo "*** ABORTING ***"
    exit 1
fi

# The database to go on serving, read from the installation currently serving it.
# Asking the operator for it instead would make a typo a deploy against the wrong
# database, and this script exists precisely because the database is not changing.
export OPUS_DB_NAME=$(sed -n 's/^schema *= *"\(.*\)"/\1/p' ${DEPLOYED_DIR}/opus.toml)
if [[ -z ${OPUS_DB_NAME} ]]; then
    echo "Cannot read the schema name from ${DEPLOYED_DIR}/opus.toml."
    echo "*** ABORTING ***"
    exit 1
fi

export OPUS_LOG_DIR=${OPUS_DIR}/opus_logs
export OPUS_SRC_DIR=${OPUS_DIR}/staged
export OPUS_DIR_NAME=${OPUS_DB_NAME}_`date +%Y%m%dT%H%M%S`
INSTALL_DIR=${OPUS_SRC_DIR}/${OPUS_DIR_NAME}

mkdir -p ${OPUS_LOG_DIR}/opus_logs
mkdir -p ${OPUS_SRC_DIR}

echo "Hostname:" ${HOSTNAME}
echo
echo "Version spec:" "${OPUS_VERSION_SPEC:-(newest release)}"
echo
echo "Currently serving: $(readlink -f ${DEPLOYED_DIR})"
echo "Database, unchanged: ${OPUS_DB_NAME}"
echo "Staging into: ${INSTALL_DIR}"
echo
echo "This deploy assumes the new release does not change the database schema."
echo

# Get sudo password input and cached, before anything long runs.
sudo echo

# Beside the running installation, which goes on serving until the switch.
source ${IMPORT_SCRIPT_DIR}/_opus_setup_environment.sh
pip install mod-wsgi

# Django's own contrib tables. A no-op when there is nothing to apply, and the
# reason it is not optional: this deploy installs the newest release by default, so
# it can cross a Django version that adds a contrib migration, and without this the
# session and auth tables would silently stay behind.
opus_manage migrate
opus_manage collectstatic --noinput

# The tables that describe the metadata rather than hold it. They are rebuilt from
# the release's own configuration, so a release that renamed a field or moved it
# between categories describes itself correctly against the database it inherited.
opus_import --create-param-info --create-partables --create-table-names --import-dictionary

source ${IMPORT_SCRIPT_DIR}/_promote.sh

echo
echo "*** New code deployed! ***"
