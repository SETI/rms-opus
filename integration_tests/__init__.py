"""The holdings-dependent test suites.

These run against a populated OPUS database and real PDS holdings, so they are
never part of a bare `pytest` run: `testpaths` selects `tests/` only, and this
tree is asked for explicitly. Three suites run: the golden-response API tests
(`test_api`), the view and helper tests that need the database (`apps_db_tests`),
and the checks on the imported data itself (`test_db_data`). A fourth directory,
`test_perf`, holds a hand-run timing script that drives a live server. No runner
collects it: `conftest.py` ignores the directory, and the script's work is behind a
`__main__` guard, so importing the module measures nothing.
"""

