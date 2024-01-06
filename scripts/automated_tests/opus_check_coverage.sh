#!/bin/bash

cd opus/application

EXPECTED=100

grep TOTAL coverage_report.txt | grep "${EXPECTED}%" >& /dev/null
if [ $? -ne 0 ]; then
    echo
    echo "*********************************"
    echo "*** OPUS FAILED TEST COVERAGE ***"
    echo "*********************************"
    echo
    echo "EXPECTED COVERAGE: ${EXPECTED}%"
    echo
    cat coverage_report.txt
    exit -1
fi

exit 0
