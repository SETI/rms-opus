#!/bin/bash
# Arg 1: Unique ID

source ~/opus_runner_secrets
if [ $? -ne 0 ]; then exit -1; fi

UNIQUE_ID=$1
TEST_CAT=opus
TEST_CAT_DIR=$TEST_ROOT/$TEST_CAT/$UNIQUE_ID
TEST_LOG_DIR=$TEST_CAT_DIR/test_logs
LOG_DIR=$TEST_CAT_DIR/temp_logs
DOWNLOAD_DIR=$TEST_CAT_DIR/downloads
DATA_DIR=$TEST_CAT_DIR/data

# opus_setup_environment.sh wrote opus_secrets.py into the repository root, which is
# also where this script runs; name it explicitly rather than relying on the working
# directory, because the import pipeline is now an installed package and no longer
# resolves anything relative to where it is invoked from.
export OPUS_SECRETS="$(pwd)/opus_secrets.py"

echo YES | ./scripts/import/import_for_tests.sh "--log-debug-limit 0 --log-info-limit 0"
if [ -s $LOG_DIR/import_logs/ERRORS.log ]; then
    echo "*****************************************"
    echo "*** OPUS IMPORT COMPLETED WITH ERRORS ***"
    echo "*****************************************"
    echo
    cat $LOG_DIR/import_logs/ERRORS.log
    cp $LOG_DIR/import_logs/WARNINGS.log $TEST_LOG_DIR/import_warnings.log
    cp $LOG_DIR/import_logs/ERRORS.log $TEST_LOG_DIR/import_errors.log
    exit -1
fi

exit 0
