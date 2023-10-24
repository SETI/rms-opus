#!/bin/bash
#
# Upgrade all pip-installable packages to their latest version. Note that this
# may require user intervention because pip does not do a great job of
# figuring out dependency trees.
#
if [ ! -f requirements.txt ]
then
    echo "This script must be run in the rms-opus root directory"
    exit -1
fi

pip install --upgrade `sed 's/==/>=/' requirements.txt`
pip freeze > requirements.txt
