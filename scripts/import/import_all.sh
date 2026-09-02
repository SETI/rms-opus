#!/bin/bash
#
# A full-holdings import on one of the Node's servers.
#
# The sequence itself is `opus_import_all`, a command the distribution installs, so
# it can be run anywhere OPUS is installed and needs no checkout:
#
#     OPUS_CONFIG=/opt/opus/opus.toml opus_import_all --override-db-schema <database name>
#
# This wrapper adds only what is specific to running it here: the check that it is
# one of the Node's servers, the banner naming the database currently being served,
# and nohup, so that a run measured in days survives the terminal it was started
# from. `opus_import_all --yes` below is answering the confirmation this script has
# already taken; the command would otherwise ask again, under nohup, where nobody
# could answer.
#
# Run from anywhere, with rms-opus installed in the active environment and
# OPUS_CONFIG naming the configuration file. The import runs under nohup, so a
# missing configuration would otherwise surface in nohup.out after the operator has
# already confirmed the erase.
: "${OPUS_CONFIG:?OPUS_CONFIG must name the OPUS configuration file}"

if [ $# -lt 1 ];
then
    echo 'Usage: scripts/import/import_all.sh <production_database_name> <other opus_import options>'
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
# Deliberately the production installation's file rather than $OPUS_CONFIG: this is
# the database being compared against the one named in $1, which is a different
# installation. Reading $OPUS_CONFIG would print the same name twice.
grep "^schema" /opus/src/rms-opus/opus.toml
echo
echo "About to ERASE and import to this database:" $1
echo "and these import options:" "${@:2}"
echo "Note this should be the production-style name, not the dev-style name"
echo -n ">>> Type YES to continue: "
read yn
if [ "$yn" != "YES" ]; then
    echo "Aborting"
    exit 1
fi
echo "Running import with nohup - check nohup.out for status"
nohup opus_import_all --yes --override-db-schema "$1" "${@:2}" &
