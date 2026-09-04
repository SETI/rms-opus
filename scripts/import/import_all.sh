#!/bin/bash
#
# A full-holdings import on one of the Ring-Moon Systems Node's servers.
#
# The sequence itself is `opus_import_all`, a command the distribution installs, so
# it can be run anywhere OPUS is installed and needs no checkout:
#
#     OPUS_CONFIG=/opt/opus/opus.toml opus_import_all --override-db-schema <database name>
#
# This wrapper adds only what is specific to running it here: the check that it is
# one of the Ring-Moon Systems Node's servers, the banner naming the database currently
# being served,
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
# A full import is days of work against the real holdings, so a machine can say which
# hosts it may be started on. OPUS_IMPORT_HOSTS is a space-separated list of substrings
# matched against the host name; with it unset there is no restriction, which is what a
# machine that only ever does this deliberately wants.
if [[ -n ${OPUS_IMPORT_HOSTS:-} ]]; then
    allowed=false
    for _host in ${OPUS_IMPORT_HOSTS}; do
        if [[ `hostname` =~ ${_host} ]]; then allowed=true; fi
    done
    if [[ ${allowed} != true ]]; then
        echo "`hostname` is not in OPUS_IMPORT_HOSTS (${OPUS_IMPORT_HOSTS})."
        exit 1
    fi
fi
echo "************************************************************"
echo "***** About to import ALL PDS DATA into a new database *****"
echo "************************************************************"
echo
# The database currently being served, for comparison with the one about to be built.
# It is a different installation from this one, so it is named by its own configuration
# file: set OPUS_SERVED_CONFIG to it. Reading $OPUS_CONFIG instead would print the same
# name twice, and hard-coding a path would name one server's layout.
if [[ -n ${OPUS_SERVED_CONFIG:-} && -r ${OPUS_SERVED_CONFIG} ]]; then
    echo "The database currently being served is:"
    grep "^schema" "${OPUS_SERVED_CONFIG}"
    echo
fi
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
