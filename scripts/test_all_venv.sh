#!/bin/bash
#
# Run full tests and code coverage on each available opus_venv_*
#
if [ ! -f requirements.txt ]
then
    echo "This script must be run in the pds-opus root directory"
    exit -1
fi

deactivate

for VENV in `echo venv_opus_*`
do
    echo "Testing ${VENV}"
    source ${VENV}/bin/activate
    cd opus/application
    ./run_coverage.sh >& ../../test_out_$VENV.txt
    coverage report >& ../../coverage_out_$VENV.txt
    deactivate
    cd ../..
done
