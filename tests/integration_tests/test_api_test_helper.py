"""Tests for the go-live accessor in `integration_tests/test_api/api_test_helper.py`.

The accessor decides which server the golden-response suite drives, and every request
in that suite reads it. A wrong answer means the suite ran against something other than
what was asked for, which looks exactly like a pass -- so what an unknown value does is
the point, and it is what these tests pin.

The accessor is not reachable from the suite that would otherwise cover it: the 100%
integration gate omits `api_test_helper.py`, and the suite only ever runs with the
variable unset. Testing it here is what makes the refusal checkable at all, and puts
it in the holdings-free run.

It sits beside `test_conftest.py` rather than under a `test_api/` directory of its own
because both files test the machinery of the `integration_tests` package rather than
one of its suites. `integration_tests` is importable because pytest-django puts the
directory holding `manage.py` on `sys.path` at startup.
"""

import re

import pytest

from integration_tests.test_api.api_test_helper import (
    GO_LIVE_ENV_VAR,
    GO_LIVE_TARGETS,
    go_live_target,
)


def test_an_unset_variable_means_the_local_database(monkeypatch: pytest.MonkeyPatch) -> None:
    """An ordinary run names no server, and must not have to."""
    monkeypatch.delenv(GO_LIVE_ENV_VAR, raising=False)
    assert go_live_target() is None


def test_an_empty_variable_means_the_local_database(monkeypatch: pytest.MonkeyPatch) -> None:
    """Exporting the variable empty is how a shell unsets it in practice."""
    monkeypatch.setenv(GO_LIVE_ENV_VAR, '')
    assert go_live_target() is None


@pytest.mark.parametrize('target', ['dev', 'production'])
def test_a_known_target_is_returned_unchanged(monkeypatch: pytest.MonkeyPatch, target: str) -> None:
    """The two servers the suite knows how to reach come back as themselves."""
    monkeypatch.setenv(GO_LIVE_ENV_VAR, target)
    assert go_live_target() == target


def test_the_known_targets_are_the_two_the_suite_can_reach() -> None:
    """`_get_response` builds a URL for each of these and for nothing else."""
    assert GO_LIVE_TARGETS == ('dev', 'production')


@pytest.mark.parametrize(
    'target',
    [
        'Production',  # right server, wrong case
        'prod',  # a plausible abbreviation
        'staging',  # a server the suite cannot reach
        'localhost',
        ' dev',  # a stray space from a shell export
    ],
)
def test_an_unknown_target_stops_the_run(monkeypatch: pytest.MonkeyPatch, target: str) -> None:
    """A value naming no server is refused, not read as "run against the local one".

    The two outcomes are indistinguishable to the caller -- a suite pointed at nothing
    and a suite pointed at the local application both pass -- so a typo would otherwise
    report success for a run nobody asked for.
    """
    monkeypatch.setenv(GO_LIVE_ENV_VAR, target)
    expected = re.escape(f'{GO_LIVE_ENV_VAR}={target!r} names no server')
    with pytest.raises(RuntimeError, match=expected):
        go_live_target()


def test_the_refusal_says_what_would_work(monkeypatch: pytest.MonkeyPatch) -> None:
    """The message has to be actionable, so it lists the values that are accepted."""
    monkeypatch.setenv(GO_LIVE_ENV_VAR, 'staging')
    with pytest.raises(RuntimeError) as excinfo:
        go_live_target()
    for known in GO_LIVE_TARGETS:
        assert known in str(excinfo.value)
