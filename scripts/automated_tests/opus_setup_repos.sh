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

# Clone the repos

git clone https://github.com/SETI/rms-webtools.git $SRC_DIR/rms-webtools
if [ $? -ne 0 ]; then exit -1; fi

pip3 install wheel
if [ $? -ne 0 ]; then exit -1; fi

pip3 install -r requirements.txt
if [ $? -ne 0 ]; then exit -1; fi

exit 0
