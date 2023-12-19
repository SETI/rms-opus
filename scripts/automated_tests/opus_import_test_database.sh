#!/bin/bash
# Arg 1: Unique ID

source ~/opus_runner_secrets
if [ $? -ne 0 ]; then exit -1; fi

UNIQUE_ID=$1
TEST_CAT=opus
TEST_CAT_DIR=$TEST_ROOT/$TEST_CAT/$UNIQUE_ID
TEST_LOG_DIR=$TEST_CAT_DIR/test_logs
SRC_DIR=$TEST_CAT_DIR/src
LOG_DIR=$TEST_CAT_DIR/temp_logs
DOWNLOAD_DIR=$TEST_CAT_DIR/downloads
DATA_DIR=$TEST_CAT_DIR/data

cd opus/import
if [ $? -ne 0 ]; then exit -1; fi

yes YES | ./import_for_tests.sh >& $TEST_LOG_DIR/dropbox_import.log
if [ -s $LOG_DIR/import_logs/ERRORS.log ]; then
    echo "*****************************************"
    echo "*** OPUS IMPORT COMPLETED WITH ERRORS ***"
    echo "*****************************************"
    echo
    cat $LOG_DIR/import_logs/ERRORS.log
    cp $LOG_DIR/import_logs/WARNINGS.log $TEST_LOG_DIR/dropbox_import_warnings.log
    cp $LOG_DIR/import_logs/ERRORS.log $TEST_LOG_DIR/dropbox_import_errors.log
    exit -1
fi

exit 0
