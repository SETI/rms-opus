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
imported schema with no create, no teardown and no surrounding transaction.

**Three ways of asking pytest-django to manage the database are therefore refused**,
and the collection hook below rejects all of them by name: `@pytest.mark.django_db`,
the `db`/`transactional_db` fixtures, and a `django.test.SimpleTestCase` subclass.
Each would either wrap a test in a transaction that is rolled back or, worse, run
`django_db_setup` -- and `DATABASES['default']['TEST']['NAME']` is the live schema
itself, so that would rebuild the database the import just filled.

**Markers.** The hook gives every test collected here `integration`, which is what the
whole tree has in common. The two narrower markers name one module each and are
declared on those modules: `test_api/test_cart_api.py` carries `holdings`, because
building a download archive copies real product files out of the PDS holdings tree,
and `test_api/test_result_counts.py` carries `livetest`, because it queries a server
outside this process. All three select *within* an explicit invocation
(``pytest integration_tests -m "not livetest"``); the default run is directory-scoped
and never reaches this tree at all.

**The run's own configuration.** Two environment variables choose what a run checks
against: `OPUS_TEST_GO_LIVE`, read through `test_api.api_test_helper.go_live_target`,
and `OPUS_TEST_RESULT_COUNTS_AGAINST_INTERNAL_DB`, read through
`internal_db_requested` below.
"""

import os
from collections.abc import Iterator
from pathlib import Path

import pytest
from django.conf import settings
from django.test import SimpleTestCase
from pytest_django import DjangoDbBlocker

from .test_api.api_test_helper import go_live_target

#: `test_perf/` holds a hand-run timing script rather than tests: `test_perf_target.py`
#: measures a server the suite does not start. Ignoring the directory is what lets it
#: keep the name the directory gives it without a runner picking it up.
collect_ignore = ['test_perf']

#: Environment variable that makes `test_result_counts` compare against the locally
#: imported database instead of checking nothing. `manage.py
#: api-internal-db-result-counts` was the verb it replaces.
INTERNAL_DB_ENV_VAR = 'OPUS_TEST_RESULT_COUNTS_AGAINST_INTERNAL_DB'

#: The ways of asking pytest-django to manage the database, none of which this tree may
#: use. `django_db_setup` is what makes them dangerous rather than merely wrong.
FORBIDDEN_DB_MARKER = 'django_db'
FORBIDDEN_DB_FIXTURES = ('db', 'transactional_db')

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
#: suite's `setUp` overrides `CACHE_KEY_PREFIX` to ``'opustest:' + DB_SCHEMA_NAME``.
#: Measured on one such key: 252 characters against a test installation's
#: ``opustest:opus_test_db_<20-character id>``, and 219 against a deployed one's
#: ``opus:opus`` -- a 33-character difference, of which 29 is the schema name and 4 the
#: ``opustest:``/``opus:`` prefix. Note where the failure lands: the warning is raised
#: *inside* a view, so `api_view` catches it and answers HTTP 500 rather than letting
#: it surface as a warning. A deployed installation's 31 characters of headroom are not
#: much, so the hazard is real and is recorded in the plan's Execution notes.
SUPPRESSED_WARNINGS = (
    'ignore:Cache key will cause errors if used with memcached'
    ':django.core.cache.backends.base.CacheKeyWarning',
)

_SUITE_ROOT = Path(__file__).parent


def internal_db_requested() -> bool:
    """Return whether result counts are to be checked against the local database.

    Any non-empty value of `INTERNAL_DB_ENV_VAR` turns the comparison on; the variable
    being unset or empty leaves it off, which is what an ordinary run wants.

    This parses an environment variable, which is why it is a function. It is not the
    kind of accessor that wraps a declared Django setting and hides it from the type
    checker: the setting it feeds, `TEST_RESULT_COUNTS_AGAINST_INTERNAL_DB`, is
    declared in `opus_app.settings` and `test_result_counts` reads it directly.

    Returns:
        True if the environment asks for the comparison.
    """
    return bool(os.environ.get(INTERNAL_DB_ENV_VAR, ''))


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


def _managed_database_request(item: pytest.Item) -> str | None:
    """Return how a test asks pytest-django to manage the database, if it does.

    Parameters:
        item: The collected test.

    Returns:
        A phrase naming what the test asked for, or None if it asked for nothing.
    """
    if item.get_closest_marker(FORBIDDEN_DB_MARKER) is not None:
        return f'@pytest.mark.{FORBIDDEN_DB_MARKER}'
    fixtures = getattr(item, 'fixturenames', ())
    for name in FORBIDDEN_DB_FIXTURES:
        if name in fixtures:
            return f'the {name!r} fixture'
    test_class = getattr(item, 'cls', None)
    if isinstance(test_class, type) and issubclass(test_class, SimpleTestCase):
        return (f'{test_class.__name__}, which subclasses '
                f'django.test.{SimpleTestCase.__name__}')
    return None


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    """Mark every test in this tree `integration`, and refuse a managed database.

    The narrower markers are not applied here: `holdings` and `livetest` describe two
    named modules and sit on those modules, where a reader meets them.

    Parameters:
        items: Every test the session collected, from this tree and any other.

    Raises:
        pytest.UsageError: If a test here asks pytest-django to manage the database.
    """
    for item in items:
        if not _is_ours(item):
            continue
        asked_for = _managed_database_request(item)
        if asked_for is not None:
            raise pytest.UsageError(
                f'{item.nodeid} uses {asked_for}, which is forbidden in '
                f'integration_tests/: these suites run against the imported schema '
                f'itself, and letting pytest-django manage the database would wrap '
                f'the test in a transaction that is rolled back or rebuild that '
                f'schema outright. Use a plain unittest.TestCase, as everything else '
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
    """Read what the environment says this run checks against.

    Both variables are read before the first test *of this tree*, so a value naming
    nothing stops the run rather than being discovered by whichever test looks at it.
    A command line that also names `tests/` runs that suite first, so the failure
    arrives after it rather than at session start.

    Raises:
        RuntimeError: If `OPUS_TEST_GO_LIVE` names no server.
    """
    go_live_target()
    settings.TEST_RESULT_COUNTS_AGAINST_INTERNAL_DB = internal_db_requested()
