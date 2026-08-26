"""Configuration for the suites that need the imported OPUS database.

`testpaths` names `tests/` only, so nothing here is collected by a bare `pytest`:
these suites are asked for by name -- `pytest integration_tests` -- because they run
against the schema `scripts/import/import_for_tests.sh` populated. This file supplies
what that makes necessary.

**The database is unblocked for the whole session, and no test database is ever
created.** pytest-django blocks database access for any test that has not asked for
it, and nothing here asks: these are plain `unittest.TestCase` subclasses, which
pytest collects natively and which pytest-django therefore does not manage. That is
fixed by the plan rather than chosen here -- the suites read and write the freshly
imported schema with no create, no teardown and no surrounding transaction -- which is
why `@pytest.mark.django_db` is **forbidden** in this tree and the collection hook
below refuses it. That marker would wrap each test in a transaction that is rolled
back, or, with ``transaction=True``, flush the schema the import just filled.

**Markers.** The hook below gives every test collected here `integration`, which is
what the whole tree has in common. The two narrower markers name one module each and
are declared on those modules: `test_api/test_cart_api.py` carries `holdings`,
because building a download archive copies real product files out of the PDS holdings
tree, and `test_api/test_result_counts.py` carries `livetest`, because it queries a
server outside this process. All three select *within* an explicit invocation
(``pytest integration_tests -m "not livetest"``); the default run is directory-scoped
and never reaches this tree at all.

**The run's own configuration.** `manage.py`'s custom `api-*` test verbs used to carry
this, by naming a module whose body assigned a Django setting. Two environment
variables replace them, and both are read once at session start so that a value
naming nothing fails the run before any test does: `OPUS_TEST_GO_LIVE`, through
`test_api.api_test_helper.go_live_target`, and the one named below.
"""

import os
from collections.abc import Iterator
from pathlib import Path

import pytest
from django.conf import settings
from pytest_django import DjangoDbBlocker

from .test_api.api_test_helper import go_live_target

#: `test_perf/` holds a hand-run timing script rather than tests: `test_perf_target.py`
#: measures a server the suite does not start. Ignoring the directory is what lets it
#: keep the name the directory gives it without a runner picking it up.
collect_ignore = ['test_perf']

#: Environment variable that makes `test_result_counts` compare against the locally
#: imported database instead of checking nothing. Any non-empty value turns it on;
#: `manage.py api-internal-db-result-counts` was the verb it replaces.
INTERNAL_DB_ENV_VAR = 'OPUS_TEST_RESULT_COUNTS_AGAINST_INTERNAL_DB'

#: Warning filters this tree adds back on top of `filterwarnings = ["error"]`, which
#: pyproject.toml sets for every run. They are applied as markers on this tree's items
#: rather than written into that list, so the holdings-free suite -- and any suite added
#: later -- still fails on them. (A concession needed by *one* test belongs on that
#: test instead; `apps_db_tests/test_search.py` carries the only other one.)
#:
#: There is one of them, and it is an artifact of how a test installation is named
#: rather than a defect in the code under test. Django warns when a cache key exceeds
#: memcached's 250-character limit. `search.views.set_user_search_number` builds its
#: key from `CACHE_SERVER_PREFIX`, `CACHE_KEY_PREFIX` and four MD5 hashes, and each
#: suite's `setUp` overrides `CACHE_KEY_PREFIX` to ``'opustest:' + DB_SCHEMA_NAME`` --
#: where the schema name is `opus_test_db_<20-character unique id>`. Measured on one
#: such key: 252 characters here, against 219 for a deployed installation whose schema
#: is `opus`. So the limit is exceeded by that 33-character name and by nothing else. The
#: warning was always raised under `manage.py test`; only `filterwarnings` makes it
#: fail, and it fails *inside* the view, where `api_view` turns it into an HTTP 500. The
#: headroom a deployed installation has is not large, though, so the hazard is real and
#: is recorded in the plan's Execution notes.
SUPPRESSED_WARNINGS = (
    'ignore:Cache key will cause errors if used with memcached'
    ':django.core.cache.backends.base.CacheKeyWarning',
)

_SUITE_ROOT = Path(__file__).parent


def _is_ours(item: pytest.Item) -> bool:
    """Return whether a collected test came from this tree.

    The hook below is called once with every item the session collected, which
    includes those of a `tests/` argument given in the same command line.

    Parameters:
        item: The collected test.

    Returns:
        True if the test's module is under `integration_tests/`.
    """
    return _SUITE_ROOT in Path(item.path).parents


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    """Mark every test in this tree `integration`, and refuse the `django_db` marker.

    The narrower markers are not applied here: `holdings` and `livetest` describe two
    named modules and sit on those modules, where a reader meets them.

    Parameters:
        items: Every test the session collected, from this tree and any other.

    Raises:
        pytest.UsageError: If a test here carries `@pytest.mark.django_db`.
    """
    for item in items:
        if not _is_ours(item):
            continue
        if item.get_closest_marker('django_db') is not None:
            raise pytest.UsageError(
                f'{item.nodeid} carries @pytest.mark.django_db, which is forbidden '
                f'in integration_tests/: these suites run against the imported '
                f'schema itself, and the marker would either wrap the test in a '
                f'transaction that is rolled back or, with transaction=True, flush '
                f'that schema. Use a plain unittest.TestCase, as everything else '
                f'here does.')
        item.add_marker(pytest.mark.integration)
        for warning_filter in SUPPRESSED_WARNINGS:
            item.add_marker(pytest.mark.filterwarnings(warning_filter))


@pytest.fixture(scope='session', autouse=True)
def _live_database(django_db_blocker: DjangoDbBlocker) -> Iterator[None]:
    """Let this tree's tests reach the imported database, for the whole session.

    pytest-django replaces `BaseDatabaseWrapper.ensure_connection` with a raiser for
    anything that has not asked for a database, and nothing here asks: these are plain
    `unittest.TestCase` subclasses, so pytest-django's own unittest support -- which
    unblocks for a `django.test.SimpleTestCase` and sets up a test database for it --
    does not apply to them. Unblocking for the session rather than per test is what
    leaves the schema exactly as the import pipeline wrote it.
    """
    with django_db_blocker.unblock():
        yield


@pytest.fixture(scope='session', autouse=True)
def _test_run_configuration() -> None:
    """Read the two settings `manage.py`'s test verbs used to set.

    Both are read before any test runs, so a value naming nothing fails the run
    immediately rather than at whichever test happens to look at it.

    Raises:
        RuntimeError: If `OPUS_TEST_GO_LIVE` names no server.
    """
    go_live_target()
    settings.TEST_RESULT_COUNTS_AGAINST_INTERNAL_DB = bool(
        os.environ.get(INTERNAL_DB_ENV_VAR, ''))
