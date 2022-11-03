#!/bin/bash
#
# Run full tests and code coverage on each available opus_venv_*
#
if [ ! -f requirements.txt ]
then
    echo "This script must be run in the pds-opus root directory"
    exit -1
fi

grep DB_SCHEMA_NAME opus_secrets.py
read -p "This is the database that will be overwritten. OK? " confirm
if [ x$confirm != "xY" ] && [ x$confirm != "x" ] && [ x$confirm != "xy" ]
then
  exit 0
fi

deactivate

for VENV in `echo venv_opus_*`
do
    echo "Testing ${VENV}"
    source ${VENV}/bin/activate
    cd opus/import
    yes YES | ./import_for_tests.sh
    cd ../application
    ./run_coverage.sh >& ../../test_out_$VENV.txt
    coverage report >& ../../coverage_out_$VENV.txt
    cd ..
    ./run_flake8_import.sh >> test_out_$VENV.txt
    ./run_flake8_application.sh >> test_out_$VENV.txt
    deactivate
    cd ..
done
