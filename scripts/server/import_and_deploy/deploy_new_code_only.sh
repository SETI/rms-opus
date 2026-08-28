#!/bin/bash
#
# Upgrade the code of an existing OPUS installation, leaving its database alone.
#
# We assume a directory structure like:
#    /opus/src/rms-opus            a symlink to the current installation
#    /opus/src/rms-opus/opus_venv  its virtualenv, with rms-opus installed
#    /opus/src/rms-opus/opus.toml  its configuration
#
# There is no checkout to pull: the installation is a virtualenv holding the
# released distribution, so upgrading the code is a pip upgrade.
#
set -e

echo "*** Starting code-only OPUS deploy ***"
echo

if [[ $# > 1 ]]; then
    echo "Usage: deploy_new_code_only.sh [<version_spec>]"
    echo
    echo "  <version_spec>  a PEP 440 specifier appended to the distribution name,"
    echo "                  for example '==3.23.0'. Omit it to upgrade to the newest"
    echo "                  release. (This argument used to name a git branch; the"
    echo "                  deploy installs from PyPI now.)"
    exit 1
fi

export OPUS_VERSION_SPEC=${1:-}

export IMPORT_SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

export SCRIPT_DIR=`dirname ${IMPORT_SCRIPT_DIR}`
export SECRETS_DIR=${SCRIPT_DIR}/secrets

source ${IMPORT_SCRIPT_DIR}/_read_deploy_env.sh

export OPUS_SRC_DIR=${OPUS_DIR}/src
export OPUS_DIR_NAME=rms-opus
INSTALL_DIR=${OPUS_SRC_DIR}/${OPUS_DIR_NAME}

# Refuse anything that is not an installation this chain created -- a git checkout at
# this path, a missing virtualenv, a missing opus.toml. An in-place upgrade of one of
# those would leave a half-converted installation: no virtualenv holding the
# distribution, and configuration OPUS does not read. The way forward is a full
# deploy, which builds the installation from nothing, so this says so rather than
# failing later and less clearly.
if [[ -d ${INSTALL_DIR}/.git ]]; then
    echo "${INSTALL_DIR} is a git checkout, not a pip installation."
    echo "Run deploy_new_code_and_database.sh to replace it with one."
    echo "*** ABORTING ***"
    exit 1
fi
if [[ ! -f ${INSTALL_DIR}/opus_venv/bin/activate ]]; then
    echo "No virtualenv at ${INSTALL_DIR}/opus_venv."
    echo "Run deploy_new_code_and_database.sh to create the installation."
    echo "*** ABORTING ***"
    exit 1
fi
if [[ ! -f ${INSTALL_DIR}/opus.toml ]]; then
    echo "No configuration at ${INSTALL_DIR}/opus.toml."
    echo "Run deploy_new_code_and_database.sh to create the installation."
    echo "*** ABORTING ***"
    exit 1
fi

# This deploy reuses the installation's existing configuration file rather than
# writing one, because only a full deploy knows which database to name in it. OPUS
# has no default location for it, so every process this script starts is given
# its path.
export OPUS_CONFIG=${INSTALL_DIR}/opus.toml
export DJANGO_SETTINGS_MODULE=opus_app.settings

cd ${INSTALL_DIR}

# Get sudo password input and cached
sudo echo

source opus_venv/bin/activate

sudo systemctl stop apache2
sudo systemctl stop memcached

python -m pip install --upgrade pip
python -m pip install --upgrade "rms-opus${OPUS_VERSION_SPEC}"

# The wsgi module moves with the Python version inside site-packages, so the symlink
# Apache's vhost points at is re-pointed on every upgrade rather than only on a full
# deploy. find_spec locates it without importing it -- importing opus_app.wsgi builds
# the application and opens the log file, which is not what asking for a path should
# do, and whose failure would leave `ln` with an empty target.
OPUS_WSGI_PATH=$(python -c \
    'import importlib.util; print(importlib.util.find_spec("opus_app.wsgi").origin)')
if [[ -z ${OPUS_WSGI_PATH} || ! -f ${OPUS_WSGI_PATH} ]]; then
    echo "ERROR: cannot locate opus_app/wsgi.py in the installed distribution."
    echo "       Apache's WSGIScriptAlias target cannot be created."
    exit 1
fi
ln -sfn "${OPUS_WSGI_PATH}" ${INSTALL_DIR}/wsgi.py

echo "Installed rms-opus $(python -c 'import importlib.metadata as m; print(m.version("rms-opus"))')"

# Django's own contrib tables. A no-op when there is nothing to apply, and the
# reason it is not optional: this deploy upgrades to the newest release by default,
# so it can cross a Django version that adds a contrib migration, and without this
# the session and auth tables would silently stay behind.
django-admin migrate
django-admin collectstatic --noinput
python -m opus_app.clear_django_cache

opus_import --create-param-info --create-partables --create-table-names --import-dictionary

sudo systemctl start memcached
sudo systemctl start apache2

echo
echo "*** New code deployed! ***"
