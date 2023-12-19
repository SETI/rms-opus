#!/bin/bash

# opus_main_test.sh
#   opus_set_repos.sh - initialize repos and venv
#   opus_test_one_holdings.sh
#     opus_setup_environment.sh - set up opus_secrets.py
#     opus_import_test_database.sh - import test database
#     opus_run_unittests_coverage.sh - run all tests and coverage check

source ~/opus_runner_secrets
if [ $? -ne 0 ]; then exit -1; fi

if [[ ! -v OPUS_DB_USER ]]; then
    echo "OPUS_DB_USER is not set"
    exit -1
fi
if [[ ! -v OPUS_DB_PASSWORD ]]; then
    echo "OPUS_DB_PASSWORD is not set"
    exit -1
fi
if [[ ! -v TEST_ROOT ]]; then
    echo "TEST_ROOT is not set"
    exit -1
fi
if [[ ! -v PDS_DROPBOX_ROOT ]]; then
    echo "PDS_DROPBOX_ROOT is not set"
    exit -1
fi

UNIQUE_ID=`uuidgen | sed 's/-/_/g'`
TEST_CAT=opus
TEST_CAT_DIR=$TEST_ROOT/$TEST_CAT/$UNIQUE_ID
TEST_LOG_DIR=$TEST_CAT_DIR/test_logs
SRC_DIR=$TEST_CAT_DIR/src
LOG_DIR=$TEST_CAT_DIR/temp_logs
DOWNLOAD_DIR=$TEST_CAT_DIR/downloads
DATA_DIR=$TEST_CAT_DIR/data

mkdir -p $TEST_LOG_DIR
if [ $? -ne 0 ]; then exit -1; fi

# Create new src/log/downloads/data directories

mkdir -p $SRC_DIR
if [ $? -ne 0 ]; then exit -1; fi
mkdir -p $LOG_DIR
if [ $? -ne 0 ]; then exit -1; fi
mkdir -p $DOWNLOAD_DIR
if [ $? -ne 0 ]; then exit -1; fi
mkdir -p $DATA_DIR
if [ $? -ne 0 ]; then exit -1; fi

# Make the individual log directories

mkdir -p $LOG_DIR/opus_logs
if [ $? -ne 0 ]; then exit -1; fi
mkdir -p $LOG_DIR/import_logs
if [ $? -ne 0 ]; then exit -1; fi
mkdir -p $LOG_DIR/test_logs
if [ $? -ne 0 ]; then exit -1; fi

# Make the downloads and manifests directories

mkdir -p $DOWNLOAD_DIR/tar
if [ $? -ne 0 ]; then exit -1; fi
mkdir -p $DOWNLOAD_DIR/manifest
if [ $? -ne 0 ]; then exit -1; fi


echo "================================================================"
echo "OPUS INITIALIZATION"
echo "================================================================"
echo
echo "Start:" `date`
./opus_setup_repos.sh $UNIQUE_ID >& $TEST_LOG_DIR/setup.log
if [ $? -ne 0 ]; then
    echo
    echo
    cat $TEST_LOG_DIR/setup.log
    echo
    echo
    echo "End:  " `date`
    echo
    exit -1
fi
echo "End:  " `date`
echo

EXIT_CODE=0

echo "================================================================"
echo "OPUS CONFIGURATION: $PDS_DROPBOX_ROOT"
echo "================================================================"
echo
echo "Test start:" `date`
./opus_test_one_holdings.sh $UNIQUE_ID dropbox $PDS_DROPBOX_ROOT >& $TEST_LOG_DIR/dropbox.log
if [ $? -ne 0 ]; then
    echo
    cat $TEST_LOG_DIR/dropbox.log
    echo
    EXIT_CODE=-1
fi
echo "Test end:  " `date`
echo

exit $EXIT_CODE
