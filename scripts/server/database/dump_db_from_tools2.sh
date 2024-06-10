#!/bin/bash
set -e
SQLDUMP=/volumes/opus/databases/$1.sql
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
SECRETS_DIR=`dirname ${SCRIPT_DIR}`/secrets
source ${SECRETS_DIR}/opus_secrets
echo "Making backup of database - Dumping $1 @ TOOLS2 to ${SQLDUMP}"
mysqldump -u${OPUS_DB_USER} "-p${OPUS_DB_PASSWORD}" -h tools2.pds-rings.seti.org $1 > ${SQLDUMP}
