#!/bin/bash
#
# The whole integration chain: set up the environment and opus.toml, import the
# test bundles into a fresh opus_test_db_<id> schema, run the suites under the
# integration coverage configuration, then drop the schema.
#
# THIS SCRIPT DOES NOT APPLY THE 100% COVERAGE GATE. It exits 0 on a run whose
# coverage is 99%. opus_run_unittests_coverage.sh only measures; the gate is
# opus_check_coverage.sh, which .github/workflows/run-integration.yml runs as a
# separate step so that a coverage failure still reaches codecov first. Run
#
#     scripts/automated_tests/opus_check_coverage.sh
#
# yourself after this script if you are using it to reproduce CI locally. Reading
# this script's exit status as the coverage gate's verdict is the mistake to
# avoid: a 99% run reaches the end of this script and exits 0.

source ~/opus_runner_secrets
if [ $? -ne 0 ]; then exit -1; fi

# Can't use -v because it isn't supported by bash on MacOS
if [[ -z ${OPUS_DB_USER+x} ]]; then
    echo "OPUS_DB_USER is not set"
    exit -1
fi
if [[ -z ${OPUS_DB_PASSWORD+x} ]]; then
    echo "OPUS_DB_PASSWORD is not set"
    exit -1
fi
if [[ -z ${TEST_ROOT+x} ]]; then
    echo "TEST_ROOT is not set"
    exit -1
fi
if [[ -z ${PDS_HOLDINGS_ROOT+x} ]]; then
    echo "PDS_HOLDINGS_ROOT is not set"
    exit -1
fi

# Can't use date because nanoseconds %N isn't supported by bash on MacOS
UNIQUE_ID=`python3 -c "from datetime import datetime; print(datetime.now().strftime('%y%m%d_%H%M%S_%f'))"`
TEST_CAT=opus
TEST_CAT_DIR=$TEST_ROOT/$TEST_CAT/$UNIQUE_ID
TEST_LOG_DIR=$TEST_CAT_DIR/test_logs
LOG_DIR=$TEST_CAT_DIR/temp_logs
DOWNLOAD_DIR=$TEST_CAT_DIR/downloads
DATA_DIR=$TEST_CAT_DIR/data

echo "Unique ID: $UNIQUE_ID"
echo "TEST_LOG_DIR: $TEST_LOG_DIR"
echo "LOG_DIR: $LOG_DIR"
echo "DOWNLOAD_DIR: $DOWNLOAD_DIR"
echo "DATA_DIR: $DATA_DIR"
echo

mkdir -p $TEST_LOG_DIR
if [ $? -ne 0 ]; then exit -1; fi

# Create new log/downloads/data directories

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


EXIT_CODE=0

echo "================================================================"
echo "OPUS SETUP ENVIRONMENT"
echo "================================================================"
echo
echo "Start:" `date`
echo
./scripts/automated_tests/opus_setup_environment.sh $UNIQUE_ID
if [ $? -ne 0 ]; then
    rm -rf $TEST_CAT_DIR
    echo
    echo "End:  " `date`
    echo
    echo "******************************************"
    echo "*** OPUS TEST ENVIRONMENT SETUP FAILED ***"
    echo "******************************************"
    exit -1
fi
echo
echo "End:  " `date`
echo

# Import the test database

echo "================================================================"
echo "OPUS IMPORT TEST DATABASE"
echo "================================================================"
echo
echo "Start:" `date`
echo
./scripts/automated_tests/opus_import_test_database.sh $UNIQUE_ID
if [ $? -ne 0 ]; then
    rm -rf $TEST_CAT_DIR
    echo
    echo "DROP DATABASE opus_test_db_$UNIQUE_ID;" | mysql -u $OPUS_DB_USER -p$OPUS_DB_PASSWORD
    echo "End:  " `date`
    exit -1
fi
echo
echo "End:  " `date`
echo

# Run the unit tests and coverage

echo "================================================================"
echo "OPUS RUN UNIT TESTS AND COVERAGE"
echo "================================================================"
echo
echo "Start:" `date`
echo
./scripts/automated_tests/opus_run_unittests_coverage.sh $UNIQUE_ID
if [ $? -ne 0 ]; then
    rm -rf $TEST_CAT_DIR
    echo
    echo "DROP DATABASE opus_test_db_$UNIQUE_ID;" | mysql -u $OPUS_DB_USER -p$OPUS_DB_PASSWORD
    echo "End:  " `date`
    exit -1
fi
echo
echo "End:  " `date`
echo

# Delete the test database

echo "DROP DATABASE opus_test_db_$UNIQUE_ID;" | mysql -u $OPUS_DB_USER -p$OPUS_DB_PASSWORD

# Delete the temporary directories

rm -rf $TEST_CAT_DIR

exit 0
