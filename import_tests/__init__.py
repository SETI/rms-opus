"""The holdings-free end-to-end test suite for the OPUS import pipeline.

The suite runs the real ``opus_import`` command line against a checked-in mini-holdings
tree and a MySQL server. It is not part of the default ``pytest`` run -- ``testpaths``
in ``pyproject.toml`` selects ``tests`` only -- so it is asked for by name, in two
invocations, because `import_tests.test_obs_execution` reads the coverage report the
rest of the suite writes and that report does not exist until the session producing it
has ended::

    pytest import_tests --ignore=import_tests/test_obs_execution.py \\
        --cov --cov-report=json:coverage.json
    pytest import_tests/test_obs_execution.py

`import_tests.tools` holds the programs that build the temporary holdings tree, run the
pipeline, and regenerate the fixture and the goldens.
"""
