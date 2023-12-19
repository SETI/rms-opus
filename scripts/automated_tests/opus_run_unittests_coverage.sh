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

cd opus/application
if [ $? -ne 0 ]; then exit -1; fi

python manage.py test -b >& $TEST_LOG_DIR/$2_unit_tests.log
if [ $? -ne 0 ]; then
    echo "******************************"
    echo "*** OPUS FAILED UNIT TESTS ***"
    echo "******************************"
    echo
    cat $TEST_LOG_DIR/$2_unit_tests.log
    exit -1
fi

EXPECTED=100
./run_coverage.sh >& /dev/null
coverage report >& $TEST_LOG_DIR/$2_coverage_report.txt
grep TOTAL $TEST_LOG_DIR/$2_coverage_report.txt | grep "${EXPECTED}%" >& /dev/null
if [ $? -ne 0 ]; then
    echo "*********************************"
    echo "*** OPUS FAILED TEST COVERAGE ***"
    echo "*********************************"
    echo
    echo "EXPECTED COVERAGE: ${EXPECTED}%"
    echo
    cat $TEST_LOG_DIR/$2_coverage_report.txt
    exit -1
fi
exit 0
