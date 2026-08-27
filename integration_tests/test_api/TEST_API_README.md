# API integration tests

All of these are run with `pytest` from the repository root, against a database
populated by the import pipeline (see `scripts/import/import_for_tests.sh`).
`OPUS_CONFIG` must name that installation's configuration file; there is no default
location for it.

A bare `pytest` does **not** run any of them: `testpaths` selects `tests/`, the
holdings-free unit suite, so this tree is only ever reached by naming it.

**Run this tree serially.** Do not add `-n` to any command below. The suites mutate
shared state in the one database they share -- one of them drops the `cache_*` tables
between tests -- so two workers would answer each other's queries. The unit suite in
`tests/` is the one that runs under `-n auto --dist loadscope`.

## Running the suites

* Everything -- the API tests, the DB integrity checks and the internal app tests:

        pytest integration_tests

* The API tests only:

        pytest integration_tests/test_api

* The DB integrity tests only:

        pytest integration_tests/test_db_data

* One module, or one test:

        pytest integration_tests/apps_db_tests/test_search.py
        pytest "integration_tests/test_api/test_cart_api.py::ApiCartTests::test__api_cart_status_no_reqno"

Markers select within any of those. Every test here carries `integration`;
`test_cart_api.py`, the one module that reads product files out of the PDS holdings
tree, also carries `holdings`, and `test_result_counts.py`, the one module that queries
a server outside this process, carries `livetest`:

        pytest integration_tests -m "not livetest"
        pytest integration_tests -m holdings

## Running against a remote server

`OPUS_TEST_GO_LIVE` points the API suite at a deployed server instead of the
in-process application. Leave it unset (or empty) to run against the locally
imported database; any value other than the two below fails the run immediately.

* Against the production site:

        OPUS_TEST_GO_LIVE=production pytest integration_tests/test_api

* Against the dev server (VPN required):

        OPUS_TEST_GO_LIVE=dev pytest integration_tests/test_api

## Result counts

`test_result_counts.py` compares recorded whole-archive counts against a server.
Selecting it on its own checks nothing unless one of the two variables below says
which archive to ask:

* Against the internal database (only meaningful with a full local database):

        OPUS_TEST_RESULT_COUNTS_AGAINST_INTERNAL_DB=1 \
            pytest integration_tests/test_api/test_result_counts.py

* Against the production site:

        OPUS_TEST_GO_LIVE=production \
            pytest integration_tests/test_api/test_result_counts.py

* Against the dev server:

        OPUS_TEST_GO_LIVE=dev \
            pytest integration_tests/test_api/test_result_counts.py

## Profiling a run

        python -m cProfile -o profile.out -m pytest integration_tests/test_api
        python -c "import pstats; pstats.Stats('profile.out').sort_stats('cumulative').print_stats(40)"

## Coverage

`.github/workflows/run-integration.yml` gates this tree at 100%, in two steps rather
than one. `scripts/automated_tests/opus_run_unittests_coverage.sh` *measures*: it runs
the suites under the coverage configuration in `integration_tests/.coveragerc` and
writes `coverage_report.txt`. `scripts/automated_tests/opus_check_coverage.sh` is what
*fails the build* on anything under 100%, and the workflow runs it as a separate step
after the codecov upload -- so `opus_main_test.sh` exiting 0 is not evidence the gate
passed, and a local run has to invoke the check script itself. To reproduce the
measurement:

        rm -f .coverage .coverage.*
        COVERAGE_RCFILE=integration_tests/.coveragerc \
            pytest --cov --cov-config=integration_tests/.coveragerc \
                   tests/opus_support tests/opus_app integration_tests
        COVERAGE_RCFILE=integration_tests/.coveragerc coverage report -m \
            >& coverage_report.txt

and then to apply the gate to it, from the repository root:

        scripts/automated_tests/opus_check_coverage.sh

The `rm` is not optional and is the first thing the script itself does: pytest-cov
measures under a per-process data suffix and combines afterwards, and its own `erase()`
removes only `.coverage`, because this configuration is not `parallel`. A fragment left
behind by an interrupted run would be combined into the totals -- coverage no test in
this run produced, which can only make the result look *better*. Skipping it can
therefore produce a local 100% that CI would not.

That configuration measures `src/opus_app/apps`, `integration_tests/test_api` and
`src/opus_support`, and `tests/opus_support` and `tests/opus_app` are the directories
under `tests/` holding tests that reach any of it -- which is why the run names all
three. `COVERAGE_RCFILE` is what keeps coverage off the unit-coverage settings in
`pyproject.toml`, which measure a different set of packages against a different gate
(plan §5a).
