#/bin/sh
#
# We assume a directory structure like:
#    /opus/src/rms-opus
#    /opus/src/rms-opus/opus_venv
# where /opus/src/rms-opus is a symlink to
#    /opus/src/rms-opus_<databasename>
#
set -e

echo "*** Starting CODE & DATABASE OPUS deploy ***"
echo

if [[ $# < 1 || $# > 2 ]]; then
    echo "Usage: deploy_new_code_and_database.sh <database_name> [<branch_name>]"
    exit -1
fi

export OPUS_DB_NAME=$1
export OPUS_BRANCH=${2:-main}

export IMPORT_SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

export SCRIPT_DIR=`dirname ${IMPORT_SCRIPT_DIR}`
export SECRETS_DIR=${SCRIPT_DIR}/secrets

source ${IMPORT_SCRIPT_DIR}/_read_opus_secrets.sh

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
echo "OPUS branch:" ${OPUS_BRANCH}
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

cd ${OPUS_SRC_DIR}/${OPUS_DIR_NAME}
# The WSGI application is opus_app/wsgi.py inside the installed distribution,
# so nothing is generated here. The Apache vhost's WSGIScriptAlias must point at
# ${OPUS_SRC_DIR}/rms-opus/src/opus_app/wsgi.py; PR-22 rewrites this deploy
# chain around `pip install rms-opus` and owns that vhost change.
python manage.py migrate
yes yes | python manage.py collectstatic
python -m opus_app.clear_django_cache

python -m opus_import --import-dict --clean

sudo systemctl start memcached
sudo systemctl start apache2

echo
echo "*** New code and database deployed! ***"
