#!/bin/bash
# Arg 1: Unique ID
# Arg 2: Config name
# Arg 3: Holdings dir

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

# Create opus_secrets.py

./scripts/automated_tests/opus_setup_environment.sh $1 $2 $3 >& $TEST_LOG_DIR/$1_test_setup.log
if [ $? -ne 0 ]; then
    echo "******************************************"
    echo "*** OPUS TEST ENVIRONMENT SETUP FAILED ***"
    echo "******************************************"
    echo
    cat $TEST_LOG_DIR/$1_test_setup.log
    exit -1
fi

# Import the test database

./scripts/automated_tests/opus_import_test_database.sh $1 $2 $3
if [ $? -ne 0 ]; then exit -1; fi

# Run the unit tests and coverage

./scripts/automated_tests/opus_run_unittests_coverage.sh $1 $2 $3
if [ $? -ne 0 ]; then exit -1; fi

# Delete the test database

echo "DROP DATABASE opus_test_db_$UNIQUE_ID;" | mysql -u $OPUS_DB_USER -p$OPUS_DB_PASSWORD >& /dev/null

exit 0
