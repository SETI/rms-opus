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
# so every process this script starts is given its path.
export OPUS_CONFIG="$(pwd)/opus.toml"

echo YES | ./scripts/import/import_for_tests.sh "--log-debug-limit 0 --log-info-limit 0"
IMPORT_STATUS=$?
# Check the import's own exit status, not just its error log. import_for_tests.sh runs
# under `set -e`, so anything that stops it -- a missing interpreter, a failed bundle,
# an aborted confirmation -- exits non-zero. This check is not redundant with the
# `[ -s ERRORS.log ]` test below, and neither covers the other's case: a *missing*
# ERRORS.log is not `-s`, so an import that dies before writing any log at all --
# a missing interpreter, say -- passes that test having imported nothing, while an
# import that runs to completion and logs errors exits zero and is caught only by
# the log test. Removing either one opens a hole that reports success.
if [ $IMPORT_STATUS -ne 0 ]; then
    echo "*******************************************"
    echo "*** OPUS IMPORT FAILED (exit $IMPORT_STATUS) ***"
    echo "*******************************************"
    echo
    if [ -f $LOG_DIR/import_logs/ERRORS.log ]; then
        cat $LOG_DIR/import_logs/ERRORS.log
        cp $LOG_DIR/import_logs/ERRORS.log $TEST_LOG_DIR/import_errors.log
    else
        echo "(no ERRORS.log was written -- the import did not get far enough to log)"
    fi
    exit -1
fi

if [ -s $LOG_DIR/import_logs/ERRORS.log ]; then
    echo "*****************************************"
    echo "*** OPUS IMPORT COMPLETED WITH ERRORS ***"
    echo "*****************************************"
    echo
    cat $LOG_DIR/import_logs/ERRORS.log
    cp $LOG_DIR/import_logs/WARNINGS.log $TEST_LOG_DIR/import_warnings.log
    cp $LOG_DIR/import_logs/ERRORS.log $TEST_LOG_DIR/import_errors.log
    exit -1
fi

exit 0
