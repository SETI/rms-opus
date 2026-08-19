#!/bin/bash
# Run the holdings-dependent integration suite under coverage, from the
# repository root. Optional argument: the Django test label to run (default
# "integration", i.e. everything); manage.py also accepts its own api-* verbs
# here, e.g. ./run_coverage.sh api-all.
#
# The 100%-gate coverage configuration is integration/.coveragerc; without this
# export coverage would fall back to the unit-coverage settings in
# pyproject.toml and measure the wrong tree (plan §5a).
export COVERAGE_RCFILE=integration/.coveragerc

coverage erase
if [ $? -ne 0 ]; then exit -1; fi
coverage run -a -m pytest tests/opus_support
if [ $? -ne 0 ]; then exit -1; fi
coverage run -a manage.py test -b "${1:-integration}"
if [ $? -ne 0 ]; then exit -1; fi
coverage xml
if [ $? -ne 0 ]; then exit -1; fi
coverage html
if [ $? -ne 0 ]; then exit -1; fi
coverage report
