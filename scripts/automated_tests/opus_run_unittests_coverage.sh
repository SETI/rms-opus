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

# opus_setup_environment.sh wrote opus.toml into the repository root, which is also
# where this script runs. OPUS has no default location for the configuration file,
# so opus_app.settings is given its path.
export OPUS_CONFIG="$(pwd)/opus.toml"

# The integration suite's 100% coverage gate has its own configuration; without
# this, coverage would pick up the unit-coverage settings in pyproject.toml.
export COVERAGE_RCFILE=integration_tests/.coveragerc

./run_coverage.sh
if [ $? -ne 0 ]; then
    echo
    echo "******************************"
    echo "*** OPUS FAILED UNIT TESTS ***"
    echo "******************************"
    exit -1
fi
coverage report -m >& $TEST_LOG_DIR/coverage_report.txt
cp $TEST_LOG_DIR/coverage_report.txt .
echo
cat coverage_report.txt

# Don't check coverage amount here so we have a chance to upload to codecov first
# Checking is done later in opus_check_coverage.sh

exit 0
