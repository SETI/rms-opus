"""Tests for the collection rules in `integration_tests/conftest.py`.

Two of those rules are guards whose failure mode is silence, which is why they are
worth a test of their own rather than being left to the suite they govern:

* **Nothing in a session that collects `integration_tests/` may ask pytest-django to
  manage the database.** Those tests are plain `unittest.TestCase` subclasses running
  against the schema the import pipeline just wrote, and
  `DATABASES['default']['TEST']['NAME']` is that same schema, so anything reaching
  `setup_databases` rebuilds it. pytest-django decides whether to call it by looking at
  every item in the session, so the refusal is session-wide rather than path-scoped --
  the coverage invocation runs `tests/` and `integration_tests/` together. Nothing else
  in the repository would notice the check being lost.
* **`test_perf/` stays out of collection.** It holds a hand-run timing script that
  drives a live server, and it is named `test_perf_target.py`, so any runner that looks
  at the directory collects it.

The hook is driven with a stub item rather than through a real collection: what is
being checked is the rule, and driving it directly is what lets the forbidden cases be
exercised at all -- a real test asking for a managed database could not be checked in,
because it would break every run of the suite.

`integration_tests` is importable here because pytest-django puts the directory
holding `manage.py` -- the repository root -- on `sys.path` at startup
(`_add_django_project_to_path`), and `manage.py` lives there permanently.
"""

import ast
import importlib.util
import re
from pathlib import Path
from typing import Any
from unittest import TestCase as PlainTestCase

import pytest
from django.test import SimpleTestCase, TestCase, TransactionTestCase

from integration_tests import conftest

#: A module inside the tree the hook governs, and one outside it. Neither has to be a
#: real test: the hook classifies by path.
_INSIDE = Path(conftest.__file__).parent / 'apps_db_tests' / 'test_search.py'
_OUTSIDE = Path(__file__)

#: The hand-run timing script the tree must not collect.
_TIMING_SCRIPT = Path(conftest.__file__).parent / 'test_perf' / 'test_perf_target.py'


class StubItem:
    """The parts of a `pytest.Item` that the collection hook touches."""

    def __init__(
        self,
        path: Path,
        markers: dict[str, Any] | None = None,
        fixturenames: tuple[str, ...] = (),
        cls: type | None = None,
    ) -> None:
        """Record where the stub test lives and what it asks for.

        Parameters:
            path: The module the stub test would have come from.
            markers: Markers the test already carries, keyed by name.
            fixturenames: Fixtures the test requests.
            cls: The class holding the test, for a class-based one.
        """
        self.path = path
        self.nodeid = f'{path}::StubTests::test_stub'
        self.existing = markers or {}
        self.fixturenames = fixturenames
        self.cls = cls
        self.added: list[Any] = []

    def get_closest_marker(self, name: str) -> Any:
        """Return the named marker if the stub carries one.

        Parameters:
            name: The marker's name.

        Returns:
            The marker, or None.
        """
        return self.existing.get(name)

    def add_marker(self, marker: Any) -> None:
        """Record a marker the hook applied.

        Parameters:
            marker: The marker.
        """
        self.added.append(marker)

    @property
    def added_names(self) -> list[str]:
        """The names of the markers the hook applied, in order."""
        return [marker.name for marker in self.added]


def _run_hook(*items: StubItem) -> None:
    """Drive the collection hook with a whole stub session.

    Parameters:
        items: The stubs making up the session.
    """
    conftest.pytest_collection_modifyitems(list(items))  # type: ignore[arg-type]  # stubs


def test_a_test_in_the_tree_is_marked_integration() -> None:
    """Every test under `integration_tests/` is selectable with ``-m integration``."""
    item = StubItem(_INSIDE)
    _run_hook(item)
    assert 'integration' in item.added_names


def test_the_cache_key_warning_is_the_concession_this_tree_makes() -> None:
    """The tree's one warning concession is the memcached key-length warning.

    Asserted against what the filter says rather than against the constant it comes
    from, so that emptying the constant is a failure rather than a vacuous match.
    """
    assert len(conftest.SUPPRESSED_WARNINGS) == 1
    assert 'CacheKeyWarning' in conftest.SUPPRESSED_WARNINGS[0]
    assert conftest.SUPPRESSED_WARNINGS[0].startswith('ignore:')


def test_a_test_in_the_tree_gets_the_suppressed_warning_filters() -> None:
    """The concession reaches the tree's tests, as a per-item marker."""
    item = StubItem(_INSIDE)
    _run_hook(item)
    applied = [marker.args[0] for marker in item.added if marker.name == 'filterwarnings']
    assert applied == list(conftest.SUPPRESSED_WARNINGS)


def test_a_test_outside_the_tree_is_not_marked() -> None:
    """The hook sees every item the session collected, including `tests/`' own."""
    item = StubItem(_OUTSIDE)
    _run_hook(item)
    assert item.added_names == []


def test_the_django_db_marker_is_refused() -> None:
    """A test carrying `django_db` stops the run, and is named."""
    item = StubItem(_INSIDE, markers={'django_db': pytest.mark.django_db})
    with pytest.raises(pytest.UsageError) as excinfo:
        _run_hook(item)
    assert item.nodeid in str(excinfo.value)
    assert 'django_db' in str(excinfo.value)


@pytest.mark.parametrize('fixture', ['db', 'transactional_db', 'live_server', 'django_db_setup'])
def test_a_database_fixture_is_refused(fixture: str) -> None:
    """Each fixture spelling is the same request, and the same hazard.

    `live_server` is the one that is easy to miss: it declares no database fixture, so
    it collects looking harmless, and then calls `getfixturevalue('transactional_db')`
    at run time.
    """
    item = StubItem(_INSIDE, fixturenames=(fixture, 'tmp_path'))
    with pytest.raises(pytest.UsageError, match=fixture):
        _run_hook(item)


def test_the_forbidden_fixtures_cover_what_pytest_django_looks_at() -> None:
    """Fail if pytest-django grows a fixture that means "manage the database".

    `_get_databases_for_test` decides whether to set a database up by testing a handful
    of fixture names. Those names are the authority; this list is a copy, and a copy
    goes stale silently. Reading them back out of the library is what makes that
    audible: if this fails, add the new name to `FORBIDDEN_DB_FIXTURES`.
    """
    from pytest_django import fixtures as pytest_django_fixtures

    source = Path(pytest_django_fixtures.__file__).read_text()
    looked_at = set(re.findall(r'"(\w+)" in fixtures', source))
    assert looked_at, 'the pattern found nothing; re-derive it from the library'
    unhandled = looked_at - set(conftest.FORBIDDEN_DB_FIXTURES)
    # `django_db_serialized_rollback` only modifies a setup that one of the others has
    # already triggered, so it is not itself a request for one.
    assert unhandled <= {'django_db_serialized_rollback'}, unhandled


@pytest.mark.parametrize('base', [SimpleTestCase, TestCase, TransactionTestCase])
def test_a_django_test_case_subclass_is_refused(base: type) -> None:
    """pytest-django manages such a class itself, with no marker and no fixture.

    `TestCase` and `TransactionTestCase` both declare ``databases == {'default'}``,
    which is what makes pytest-django set a database up for them. A bare
    `SimpleTestCase` declares none and is harmless in itself; it is refused because it
    is the base those two share and any subclass may declare `databases`.
    """
    subclass = type('StubDjangoTests', (base,), {})
    item = StubItem(_INSIDE, cls=subclass)
    with pytest.raises(pytest.UsageError, match='StubDjangoTests'):
        _run_hook(item)


def test_a_plain_unittest_class_is_accepted() -> None:
    """The refusal is about a *managed* database, not about class-based tests."""
    item = StubItem(_INSIDE, cls=type('StubPlainTests', (PlainTestCase,), {}))
    _run_hook(item)
    assert 'integration' in item.added_names


def test_a_database_fixture_is_refused_outside_the_tree_too() -> None:
    """The hazard is session-wide, so the refusal has to be.

    pytest-django's `_get_databases_for_setup` iterates every item in the session, so
    one managed-database test in `tests/` would set the database up while
    `integration_tests/` is being collected in the same session -- and that session is
    exactly what the coverage invocation runs. This conftest is only loaded when the
    command line reaches into this directory, so a bare `pytest` leaves `tests/` free.
    """
    item = StubItem(_OUTSIDE, fixturenames=('db',))
    with pytest.raises(pytest.UsageError, match='session'):
        _run_hook(item)


def test_one_bad_item_stops_a_session_of_good_ones() -> None:
    """The refusal has to survive being outnumbered, since it aborts the whole run."""
    good = StubItem(_INSIDE)
    bad = StubItem(_OUTSIDE, fixturenames=('live_server',))
    with pytest.raises(pytest.UsageError, match='live_server'):
        _run_hook(good, bad)


def test_the_timing_script_directory_is_ignored() -> None:
    """`test_perf/` is named in `collect_ignore`, so collection never descends."""
    assert 'test_perf' in conftest.collect_ignore


def test_the_timing_script_defines_no_test_to_collect() -> None:
    """The second guard: `collect_ignore` does not cover a directly-named file.

    ``pytest integration_tests/test_perf/test_perf_target.py`` bypasses
    `collect_ignore` entirely, so what keeps that harmless is the module holding
    nothing pytest would pick up -- its work is behind a `__main__` guard. The module
    is imported rather than parsed, because that is what pytest does: a `test_`
    function nested inside an `if` or a `try`, or a module-level alias of an existing
    function, is collectable and invisible to a scan of the top-level statements.
    Importing it also proves the `__main__` guard holds, since the timing runs would
    otherwise fire here.
    """
    spec = importlib.util.spec_from_file_location('_timing_script', _TIMING_SCRIPT)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    collectable = [
        name for name in vars(module) if name.startswith('test') or name.startswith('Test')
    ]
    assert collectable == []


def test_the_timing_script_keeps_its_work_behind_a_main_guard() -> None:
    """What makes the module safe to import is the guard, so pin the guard itself."""
    tree = ast.parse(_TIMING_SCRIPT.read_text())
    guards = [node for node in tree.body if isinstance(node, ast.If)]
    assert len(guards) == 1
    assert ast.unparse(guards[0].test) == "__name__ == '__main__'"


def test_the_internal_db_flag_is_off_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    """An ordinary run does not compare result counts against the local database."""
    monkeypatch.delenv(conftest.INTERNAL_DB_ENV_VAR, raising=False)
    assert conftest.internal_db_requested() is False


@pytest.mark.parametrize('value', ['1', 'true', 'yes', 'anything'])
def test_any_non_empty_value_turns_the_internal_db_flag_on(
    monkeypatch: pytest.MonkeyPatch, value: str
) -> None:
    """The variable is a switch, not a vocabulary: presence is what it means."""
    monkeypatch.setenv(conftest.INTERNAL_DB_ENV_VAR, value)
    assert conftest.internal_db_requested() is True


def test_an_empty_internal_db_variable_is_off(monkeypatch: pytest.MonkeyPatch) -> None:
    """Exporting the variable empty is how a shell unsets it in practice."""
    monkeypatch.setenv(conftest.INTERNAL_DB_ENV_VAR, '')
    assert conftest.internal_db_requested() is False
