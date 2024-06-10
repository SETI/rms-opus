#!/bin/bash
set -e
SQLDUMP=/volumes/opus/databases/$1.sql
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
SECRETS_DIR=`dirname ${SCRIPT_DIR}`/secrets
source ${SECRETS_DIR}/opus_secrets
echo "Loading TOOLS database from $1"
echo "CREATE DATABASE $1;" | mysql -u${OPUS_DB_USER} "-p${OPUS_DB_PASSWORD}" -h tools.pds-rings.seti.org
mysql $1 -u${OPUS_DB_USER} "-p${OPUS_DB_PASSWORD}" -h tools.pds-rings.seti.org < ${SQLDUMP}
