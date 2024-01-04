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

cd opus/application
if [ $? -ne 0 ]; then exit -1; fi

./run_coverage.sh
if [ $? -ne 0 ]; then
    echo
    echo "******************************"
    echo "*** OPUS FAILED UNIT TESTS ***"
    echo "******************************"
    exit -1
fi
coverage report >& $TEST_LOG_DIR/coverage_report.txt
cp $TEST_LOG_DIR/coverage_report.txt .

# Don't check coverage amount here so we have a chance to upload to codecov first
# Checking is done later in opus_check_coverage.sh

exit 0
