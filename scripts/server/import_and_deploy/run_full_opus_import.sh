#!/bin/bash
#
# Usage: run_full_opus_import.sh [<version_spec>]
#
#   <version_spec>  a PEP 440 specifier appended to the distribution name, for
#                   example '==3.23.0'. Omit it to install the newest release.
#
export IMPORT_SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
export NOHUP_LOGFILE="/tmp/opus_import_$$.log"

# The argument is forwarded the whole way down. It was not before -- this outer
# script dropped it, so the inner script's ${1:-main} always took its default and a
# branch named on the command line was silently ignored.
nohup ${IMPORT_SCRIPT_DIR}/_full_opus_import_wrapper.sh "$@" > /dev/null &

echo "*** IMPORT IS RUNNING ***"
echo "Log file: ${NOHUP_LOGFILE}"
