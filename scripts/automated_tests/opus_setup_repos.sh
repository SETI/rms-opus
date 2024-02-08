#!/bin/bash
# Arg 1: Unique ID

source ~/opus_runner_secrets
if [ $? -ne 0 ]; then exit -1; fi

mkdir -p $TEST_ROOT
if [ $? -ne 0 ]; then exit -1; fi

UNIQUE_ID=$1
TEST_CAT=opus
TEST_CAT_DIR=$TEST_ROOT/$TEST_CAT/$UNIQUE_ID
TEST_LOG_DIR=$TEST_CAT_DIR/test_logs
SRC_DIR=$TEST_CAT_DIR/src
LOG_DIR=$TEST_CAT_DIR/temp_logs
DOWNLOAD_DIR=$TEST_CAT_DIR/downloads
DATA_DIR=$TEST_CAT_DIR/data

echo "Unique ID: $UNIQUE_ID"
echo "TEST_LOG_DIR: $TEST_LOG_DIR"
echo "SRC_DIR: $SRC_DIR"
echo "LOG_DIR: $LOG_DIR"
echo "DOWNLOAD_DIR: $DOWNLOAD_DIR"
echo "DATA_DIR: $DATA_DIR"
echo

exit 0
