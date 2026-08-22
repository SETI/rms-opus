#!/bin/bash
# Run the holdings-dependent integration suite under coverage, from the
# repository root. Optional arguments: the Django test labels to run (default
# "integration_tests", i.e. everything); manage.py also accepts its own api-* verbs
# here, e.g. ./run_coverage.sh api-livetest-dev api-all.
#
# The 100%-gate coverage configuration is integration_tests/.coveragerc; without this
# export coverage would fall back to the unit-coverage settings in
# pyproject.toml and measure the wrong tree (plan §5a).
export COVERAGE_RCFILE=integration_tests/.coveragerc

# The suite runs against a populated database, so it needs the configuration of the
# installation that holds it. OPUS has no default location for that file; fail here
# rather than inside Django's startup.
: "${OPUS_CONFIG:?OPUS_CONFIG must name the OPUS configuration file}"

coverage erase
if [ $? -ne 0 ]; then exit -1; fi
coverage run -a -m pytest tests/opus_support
if [ $? -ne 0 ]; then exit -1; fi
coverage run -a manage.py test -b "${@:-integration_tests}"
if [ $? -ne 0 ]; then exit -1; fi
coverage xml
if [ $? -ne 0 ]; then exit -1; fi
coverage html
if [ $? -ne 0 ]; then exit -1; fi
coverage report
