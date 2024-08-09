#!/bin/bash
export IMPORT_SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
export NOHUP_LOGFILE="/tmp/opus_import_$$.log"

nohup ${IMPORT_SCRIPT_DIR}/_full_opus_import_wrapper.sh > /dev/null &

echo "*** IMPORT IS RUNNING ***"
echo "Log file: ${NOHUP_LOGFILE}"
