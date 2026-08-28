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
# an aborted confirmation -- exits non-zero. Without this check the only gate was
# `[ -s ERRORS.log ]` below, and a *missing* ERRORS.log is not `-s`: an import that died
# before writing any log at all reported success, and this whole stage exited 0 having
# imported nothing. Found when the venv was off a background shell's PATH, so
# `python: command not found` killed the import and all three stages "completed"
# inside the same wall-clock second.
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
