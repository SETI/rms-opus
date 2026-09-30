"""The holdings-free end-to-end test suite for the OPUS import pipeline.

The suite runs the real ``opus_import`` command line against a checked-in mini-holdings
tree and a MySQL server. It is not part of the default ``pytest`` run -- ``testpaths``
in ``pyproject.toml`` selects ``tests`` only -- so it is asked for by name::

    pytest import_tests

That is the everyday form: about two minutes, no coverage, and
`import_tests.test_obs_execution`'s three executed-functions tests skip, because the
report they read is not there.

Coverage costs about two and a half times the runtime and takes two invocations, because
that report does not exist until the session producing it has ended::

    pytest import_tests --ignore=import_tests/test_obs_execution.py \\
        --cov --cov-report=json:coverage.json
    pytest import_tests/test_obs_execution.py

`import_tests.tools` holds the programs that build the temporary holdings tree, run the
pipeline, and regenerate the fixture and the goldens.
"""
