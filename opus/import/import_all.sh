#!/bin/bash
if [ $# -lt 2 ];
then
    echo 'Usage: import_all.sh <production_database_name> "-u<username> -p<password> -h <hostname>" <other_params>'
    exit 1
fi
if [[ ! `hostname` =~ "tools" && ! `hostname` =~ "ringlet" ]];
then
    echo "Please only run this script on tools.pds-rings.seti.org"
    exit 1
fi
echo "************************************************************"
echo "***** About to import ALL PDS DATA into a new database *****"
echo "************************************************************"
echo
echo "The current production database is:"
grep "^DB_SCHEMA_NAME" /opus/src/rms-opus/opus_secrets.py
echo
echo "About to ERASE and import to this database:" $1
echo "with these SQL parameters:" $2
echo "and these import options:" $3
echo "Note this should be the production-style name, not the dev-style name"
echo -n ">>> Type YES to continue: "
read yn
if [ "$yn" != "YES" ]; then
    echo "Aborting"
    exit 1
fi
# source ~/src/rms-opus/p3venv/activate
# pip install -r ../../requirements-python3.txt
echo "Running import with nohup - check nohup.out for status"
nohup ./_import_all_internal.sh "$1" "$2" "$3" &
