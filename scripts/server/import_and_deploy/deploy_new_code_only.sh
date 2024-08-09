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

cd ${OPUS_SRC_DIR}/${OPUS_DIR_NAME}/opus/application
yes yes | python manage.py collectstatic
python clear_django_cache.py

cd ${OPUS_SRC_DIR}/${OPUS_DIR_NAME}/opus/import
python main_opus_import.py --create-param-info --create-partables --create-table-names --import-dict

sudo systemctl start memcached
sudo systemctl start apache2

echo
echo "*** New code deployed! ***"
