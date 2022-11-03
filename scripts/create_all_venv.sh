#!/bin/bash
#
# Create venv_opus_* for each available version of Python and install the
# required packages.
#
if [ ! -f requirements.txt ]
then
    echo "This script must be run in the pds-opus root directory"
    exit -1
fi

deactivate

for VERSION in 3.8 3.9 3.10 3.11
do
    echo
    echo "*** CREATING VERSION ${VERSION} ***"
    rm -rf venv_opus_${VERSION}
    python${VERSION} -m venv venv_opus_${VERSION}
    source venv_opus_${VERSION}/bin/activate
    pip install -r requirements.txt
    deactivate
done
