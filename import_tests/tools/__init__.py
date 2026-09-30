"""Programs behind the mini-holdings suite.

Two of them are run by hand and own what they write:
`import_tests.tools.make_mini_holdings` records the fixture from the real PDS holdings,
and `import_tests.tools.make_mini_goldens` records the expected database contents from a
clean run. Neither runs in CI.

The rest are shared: `import_tests.tools.build_run` is the only code that assembles the
temporary holdings tree and runs the pipeline, `import_tests.tools.golden_io` is the only
code that serializes a table, and `import_tests.tools.shelf_manifests` is the only code
that maps a manifest to the shelf file it stands for.
"""
