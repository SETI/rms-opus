"""Tests for the collection rules in `integration_tests/conftest.py`.

Two of those rules are guards whose failure mode is silence, which is why they are
worth a test of their own rather than being left to the suite they govern:

* **`@pytest.mark.django_db` is refused.** The plan fixes the DB lifecycle for
  `integration_tests/`: its tests are plain `unittest.TestCase` subclasses running
  against the schema the import pipeline just wrote, so the marker would either roll
  each test back inside a transaction or -- with ``transaction=True`` -- flush that
  schema. Nothing else in the repository would notice the marker being added; the hook
  is the whole enforcement, so deleting the check would go unremarked.
* **`test_perf/` stays out of collection.** It holds a hand-run timing script that
  drives a live server. It is named `test_perf_target.py`, so any runner that looks at
  the directory collects it.

The hook is called with a stub item rather than through a real collection: what is
being checked is the rule, and driving it directly is what lets the forbidden case be
exercised at all -- a real test carrying the marker could not be checked in, because
it would break every run of the suite.

`integration_tests` is importable here because pytest-django puts the directory
holding `manage.py` -- the repository root -- on `sys.path` at startup
(`_add_django_project_to_path`), and `manage.py` lives there permanently.
"""

from pathlib import Path
from typing import Any

import pytest

from integration_tests import conftest

#: A module inside the tree the hook governs, and one outside it. Neither has to
#: exist as a test: the hook classifies by path.
_INSIDE = Path(conftest.__file__).parent / 'apps_db_tests' / 'test_search.py'
_OUTSIDE = Path(__file__)


class StubItem:
    """The four parts of a `pytest.Item` that the collection hook touches."""

    def __init__(self, path: Path, markers: dict[str, Any] | None = None) -> None:
        """Record where the stub test lives and which markers it already carries.

        Parameters:
            path: The module the stub test would have come from.
            markers: Markers the test already carries, keyed by name.
        """
        self.path = path
        self.nodeid = f'{path}::StubTests::test_stub'
        self.existing = markers or {}
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


def test_a_test_in_the_tree_is_marked_integration() -> None:
    """Every test under `integration_tests/` is selectable with ``-m integration``."""
    item = StubItem(_INSIDE)
    conftest.pytest_collection_modifyitems([item])  # type: ignore[list-item]  # stub
    assert 'integration' in item.added_names


def test_a_test_in_the_tree_gets_the_suppressed_warning_filters() -> None:
    """The tree's warning concessions reach its tests and are the declared ones."""
    item = StubItem(_INSIDE)
    conftest.pytest_collection_modifyitems([item])  # type: ignore[list-item]  # stub
    applied = [marker.args[0] for marker in item.added if marker.name == 'filterwarnings']
    assert applied == list(conftest.SUPPRESSED_WARNINGS)


def test_a_test_outside_the_tree_is_left_alone() -> None:
    """The hook sees every item the session collected, including `tests/`' own."""
    item = StubItem(_OUTSIDE)
    conftest.pytest_collection_modifyitems([item])  # type: ignore[list-item]  # stub
    assert item.added_names == []


def test_the_django_db_marker_is_refused() -> None:
    """A test in the tree carrying `django_db` stops the run, and is named."""
    item = StubItem(_INSIDE, markers={'django_db': pytest.mark.django_db})
    with pytest.raises(pytest.UsageError) as excinfo:
        conftest.pytest_collection_modifyitems([item])  # type: ignore[list-item]  # stub
    assert item.nodeid in str(excinfo.value)
    assert 'django_db' in str(excinfo.value)


def test_the_django_db_marker_is_allowed_outside_the_tree() -> None:
    """The ban is about this tree, not about the marker: `tests/` may use it."""
    item = StubItem(_OUTSIDE, markers={'django_db': pytest.mark.django_db})
    conftest.pytest_collection_modifyitems([item])  # type: ignore[list-item]  # stub


def test_the_timing_script_directory_is_not_collected() -> None:
    """`test_perf/` is ignored, so its module body never runs during a collection."""
    assert 'test_perf' in conftest.collect_ignore
    assert (Path(conftest.__file__).parent / 'test_perf' /
            'test_perf_target.py').is_file()
