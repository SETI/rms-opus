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
# this, coverage would pick up the unit-coverage settings in pyproject.toml, which
# measure a different set of packages against a different gate (plan §5a). It is
# exported as well as passed to pytest below because the `coverage` commands after
# the run read it too.
export COVERAGE_RCFILE=integration_tests/.coveragerc

# pytest-cov measures under a per-process data suffix and combines afterwards, so a
# fragment left behind by an interrupted run would be combined into this run's
# totals -- coverage no test in this run produced, which can only make the gate look
# better. Its own erase() removes `.coverage` alone, because this configuration is
# not `parallel`, so remove the fragments here.
rm -f .coverage .coverage.*

# The suites in one run, because the 100% gate measures src/opus_app/apps,
# integration_tests/test_api and src/opus_support together (see the include list in
# integration_tests/.coveragerc). tests/opus_support and tests/opus_app are the only
# directories under tests/ that reach any of that source: they exercise opus_support
# in full and the two parts of the Django app -- the @api_view decorator and the SQL
# builder -- that need no database. Dropping either would deflate the gate rather
# than fail it.
pytest --cov --cov-config=integration_tests/.coveragerc \
       tests/opus_support tests/opus_app integration_tests
if [ $? -ne 0 ]; then
    echo
    echo "******************************"
    echo "*** OPUS FAILED UNIT TESTS ***"
    echo "******************************"
    exit -1
fi

coverage xml
if [ $? -ne 0 ]; then exit -1; fi
coverage html
if [ $? -ne 0 ]; then exit -1; fi
coverage report -m >& $TEST_LOG_DIR/coverage_report.txt
cp $TEST_LOG_DIR/coverage_report.txt .
echo
cat coverage_report.txt

# Don't check coverage amount here so we have a chance to upload to codecov first
# Checking is done later in opus_check_coverage.sh

exit 0
