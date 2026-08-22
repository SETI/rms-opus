#/bin/sh
#
# We assume a directory structure like:
#    /opus/src/rms-opus
#    /opus/src/rms-opus/opus_venv
#
set -e

echo "*** Starting code-only OPUS deploy ***"
echo

export OPUS_BRANCH=${1:-main}

export IMPORT_SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

export SCRIPT_DIR=`dirname ${IMPORT_SCRIPT_DIR}`
export SECRETS_DIR=${SCRIPT_DIR}/secrets

source ${IMPORT_SCRIPT_DIR}/_read_opus_secrets.sh

export OPUS_SRC_DIR=${OPUS_DIR}/src
export OPUS_DIR_NAME=rms-opus

# This deploy reuses the checkout's existing configuration file rather than writing
# one. OPUS has no default location for it, so every process this script starts is
# given its path.
export OPUS_CONFIG=${OPUS_SRC_DIR}/${OPUS_DIR_NAME}/opus.toml

cd ${OPUS_SRC_DIR}/${OPUS_DIR_NAME}

if [ -n "$(git status --porcelain)" ]; then
    echo "There are unstaged changes in ${OPUS_SRC_DIR}/${OPUS_DIR_NAME}:"
    echo
    git status --porcelain
    echo
    echo "*** ABORTING ***"
    exit -1
fi

# Get sudo password input and cached
sudo echo

source opus_venv/bin/activate

sudo systemctl stop apache2
sudo systemctl stop memcached

git fetch
git checkout ${OPUS_BRANCH}
git pull

python -m pip install --upgrade pip
python -m pip install --upgrade -r requirements.txt
# opus_support is imported from the installed distribution rather than
# through a sys.path insertion, so the package itself must be installed.
python -m pip install -e .

cd ${OPUS_SRC_DIR}/${OPUS_DIR_NAME}
yes yes | python manage.py collectstatic
python -m opus_app.clear_django_cache

python -m opus_import --create-param-info --create-partables --create-table-names --import-dict

sudo systemctl start memcached
sudo systemctl start apache2

echo
echo "*** New code deployed! ***"
