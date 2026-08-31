"""The holdings-free end-to-end test suite for the OPUS import pipeline.

The suite runs the real ``opus_import`` command line against a checked-in mini-holdings
tree and a MySQL server. It is not part of the default ``pytest`` run -- ``testpaths``
in ``pyproject.toml`` selects ``tests`` only -- so it is asked for by name::

    pytest import_tests

`import_tests.tools` holds the programs that build the temporary holdings tree, run the
pipeline, and regenerate the fixture and the goldens.
"""
