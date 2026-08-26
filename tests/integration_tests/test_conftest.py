"""Tests for the collection rules in `integration_tests/conftest.py`.

Two of those rules are guards whose failure mode is silence, which is why they are
worth a test of their own rather than being left to the suite they govern:

* **Nothing may ask pytest-django to manage the database.** The plan fixes the DB
  lifecycle for `integration_tests/`: its tests are plain `unittest.TestCase`
  subclasses running against the schema the import pipeline just wrote. A test that
  asked for a managed database would be rolled back inside a transaction, or -- since
  `DATABASES['default']['TEST']['NAME']` is that same schema -- would have it rebuilt
  underneath it. Nothing else in the repository would notice; the hook is the whole
  enforcement, so losing the check would go unremarked.
* **`test_perf/` stays out of collection.** It holds a hand-run timing script that
  drives a live server, and it is named `test_perf_target.py`, so any runner that
  looks at the directory collects it.

The hook is driven with a stub item rather than through a real collection: what is
being checked is the rule, and driving it directly is what lets the forbidden cases be
exercised at all -- a real test asking for a managed database could not be checked in,
because it would break every run of the suite.

`integration_tests` is importable here because pytest-django puts the directory
holding `manage.py` -- the repository root -- on `sys.path` at startup
(`_add_django_project_to_path`), and `manage.py` lives there permanently.
"""

import ast
from pathlib import Path
from typing import Any
from unittest import TestCase as PlainTestCase

import pytest
from django.test import SimpleTestCase, TestCase

from integration_tests import conftest

#: A module inside the tree the hook governs, and one outside it. Neither has to be a
#: real test: the hook classifies by path.
_INSIDE = Path(conftest.__file__).parent / 'apps_db_tests' / 'test_search.py'
_OUTSIDE = Path(__file__)

#: The hand-run timing script the tree must not collect.
_TIMING_SCRIPT = Path(conftest.__file__).parent / 'test_perf' / 'test_perf_target.py'


class StubItem:
    """The parts of a `pytest.Item` that the collection hook touches."""

    def __init__(self, path: Path, markers: dict[str, Any] | None = None,
                 fixturenames: tuple[str, ...] = (),
                 cls: type | None = None) -> None:
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


def _run_hook(item: StubItem) -> None:
    """Drive the collection hook with one stub item.

    Parameters:
        item: The stub.
    """
    conftest.pytest_collection_modifyitems([item])  # type: ignore[list-item]  # stub


def test_a_test_in_the_tree_is_marked_integration() -> None:
    """Every test under `integration_tests/` is selectable with ``-m integration``."""
    item = StubItem(_INSIDE)
    _run_hook(item)
    assert 'integration' in item.added_names


def test_a_test_in_the_tree_gets_the_suppressed_warning_filters() -> None:
    """The tree's warning concessions reach its tests and are the declared ones."""
    item = StubItem(_INSIDE)
    _run_hook(item)
    applied = [marker.args[0] for marker in item.added
               if marker.name == 'filterwarnings']
    assert applied == list(conftest.SUPPRESSED_WARNINGS)


def test_a_test_outside_the_tree_is_left_alone() -> None:
    """The hook sees every item the session collected, including `tests/`' own."""
    item = StubItem(_OUTSIDE)
    _run_hook(item)
    assert item.added_names == []


def test_the_django_db_marker_is_refused() -> None:
    """A test in the tree carrying `django_db` stops the run, and is named."""
    item = StubItem(_INSIDE, markers={'django_db': pytest.mark.django_db})
    with pytest.raises(pytest.UsageError) as excinfo:
        _run_hook(item)
    assert item.nodeid in str(excinfo.value)
    assert 'django_db' in str(excinfo.value)


@pytest.mark.parametrize('fixture', ['db', 'transactional_db'])
def test_a_database_fixture_is_refused(fixture: str) -> None:
    """The fixture spelling of the marker is the same request, and the same hazard."""
    item = StubItem(_INSIDE, fixturenames=(fixture, 'tmp_path'))
    with pytest.raises(pytest.UsageError, match=fixture):
        _run_hook(item)


@pytest.mark.parametrize('base', [SimpleTestCase, TestCase])
def test_a_django_test_case_subclass_is_refused(base: type) -> None:
    """This is the dangerous spelling: pytest-django manages such a class itself.

    It needs no marker and no fixture, so it would slip past a check that looked only
    for those -- and `django_db_setup` would then run against the live schema.
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


def test_a_database_fixture_is_allowed_outside_the_tree() -> None:
    """The ban is about this tree, not about the fixtures: `tests/` may use them."""
    item = StubItem(_OUTSIDE, fixturenames=('db',))
    _run_hook(item)
    assert item.added_names == []


def test_the_timing_script_directory_is_ignored() -> None:
    """`test_perf/` is named in `collect_ignore`, so collection never descends."""
    assert 'test_perf' in conftest.collect_ignore


def test_the_timing_script_defines_no_test_to_collect() -> None:
    """The second guard: `collect_ignore` does not cover a directly-named file.

    ``pytest integration_tests/test_perf/test_perf_target.py`` bypasses
    `collect_ignore` entirely, so what keeps that harmless is the module holding
    nothing pytest would pick up -- its work is behind a `__main__` guard.
    """
    module = ast.parse(_TIMING_SCRIPT.read_text())
    collectable = [node.name for node in module.body
                   if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef
                                 | ast.ClassDef)
                   and node.name.lower().startswith('test')]
    assert collectable == []


def test_the_internal_db_flag_is_off_by_default(
        monkeypatch: pytest.MonkeyPatch) -> None:
    """An ordinary run does not compare result counts against the local database."""
    monkeypatch.delenv(conftest.INTERNAL_DB_ENV_VAR, raising=False)
    assert conftest.internal_db_requested() is False


@pytest.mark.parametrize('value', ['1', 'true', 'yes', 'anything'])
def test_any_non_empty_value_turns_the_internal_db_flag_on(
        monkeypatch: pytest.MonkeyPatch, value: str) -> None:
    """The variable is a switch, not a vocabulary: presence is what it means."""
    monkeypatch.setenv(conftest.INTERNAL_DB_ENV_VAR, value)
    assert conftest.internal_db_requested() is True


def test_an_empty_internal_db_variable_is_off(
        monkeypatch: pytest.MonkeyPatch) -> None:
    """Exporting the variable empty is how a shell unsets it in practice."""
    monkeypatch.setenv(conftest.INTERNAL_DB_ENV_VAR, '')
    assert conftest.internal_db_requested() is False
