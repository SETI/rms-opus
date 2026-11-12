"""The deploy a web run simulates: the landing page's warm-up, and the timed promotion.

The servers are stand-ins that record what they were asked to do, so the order of a
reset and of a promotion is checked without starting any of them.
"""

from __future__ import annotations

import subprocess  # nosec B404 - a stand-in's finished process
from pathlib import Path
from typing import Any

import pytest

from benchmarks import bench_web
from benchmarks.bench_web import DeploySteps, WebBench, WebRunError, deploy_steps
from benchmarks.sides import Spelling

#: A side's spelling with the carry-over, and one without it.
_WITH = Spelling.from_help('--reset-search-tables --carry-over-sessions-from')
_WITHOUT = Spelling.from_help('--reset-search-tables')


def test_a_side_with_both_steps_runs_what_was_asked() -> None:
    """Nothing is skipped."""
    steps = deploy_steps(frozenset({'db-cold'}), 10000, has_warm_search=True, spelling=_WITH)
    assert steps == DeploySteps(frozenset({'db-cold'}), 10000, ())


def test_a_side_without_the_steps_skips_and_names_them() -> None:
    """The before side of the change has neither, so its runs are the plain ones."""
    steps = deploy_steps(
        frozenset({'db-cold', 'app-cold'}), 10000, has_warm_search=False, spelling=_WITHOUT
    )
    assert steps == DeploySteps(frozenset(), None, ('warm_search', 'carry_over_sessions'))
    # The environment records what ran, so the before side's file names no warm state.
    assert steps.environment() == {'warm_states': [], 'promotion_carts': None}


def test_the_environment_records_the_states_that_warm() -> None:
    """Sorted, beside the promotion's cart rows."""
    steps = deploy_steps(
        frozenset({'db-cold', 'app-cold'}), 10000, has_warm_search=True, spelling=_WITH
    )
    assert steps.environment() == {'warm_states': ['app-cold', 'db-cold'], 'promotion_carts': 10000}


def test_nothing_asked_is_nothing_skipped() -> None:
    """A side lacking a step nobody asked for records no skip."""
    assert deploy_steps(frozenset(), None, has_warm_search=False, spelling=_WITHOUT) == DeploySteps(
        frozenset(), None, ()
    )


class _Recorder:
    """Records each call made of it, under a name, into a shared list."""

    def __init__(self, name: str, calls: list[str]) -> None:
        self.name = name
        self.calls = calls

    def __getattr__(self, method: str) -> Any:
        def record(*args: Any, **kwargs: Any) -> None:
            self.calls.append(f'{self.name}.{method}')

        return record


class _Side:
    """A side whose warm-up records itself and exits with a given status."""

    def __init__(self, calls: list[str], status: int = 0) -> None:
        self.calls = calls
        self.status = status
        self.env: dict[str, str] | None = None

    def warm_search(self, env: dict[str, str]) -> subprocess.CompletedProcess[str]:
        self.calls.append('side.warm_search')
        self.env = env
        return subprocess.CompletedProcess([], self.status, 'out', 'err')


def _bench(calls: list[str], warm_states: frozenset[str], status: int = 0) -> WebBench:
    """Return a WebBench over stand-ins; nothing is started."""
    bench = object.__new__(WebBench)
    bench.side = _Side(calls, status)  # type: ignore[assignment]
    bench.server = _Recorder('mysql', calls)  # type: ignore[assignment]
    bench.gunicorn = _Recorder('gunicorn', calls)  # type: ignore[assignment]
    bench.memcached = _Recorder('memcached', calls)  # type: ignore[assignment]
    bench.env = {'OPUS_CONFIG': 'opus.toml'}
    bench.warm_states = warm_states
    bench.spelling = _WITH
    bench.errors_log = Path('ERRORS.log')
    bench._connection = None
    bench.reset_search_tables = lambda: calls.append('reset_search_tables')  # type: ignore[method-assign]
    return bench


@pytest.mark.parametrize('state', ['db-cold', 'app-cold'])
def test_a_warmed_state_warms_last_after_its_restarts(state: str) -> None:
    """After memcached's restart, so the warm-up fills the cache the scenario reads."""
    calls: list[str] = []
    seconds = _bench(calls, frozenset({state})).reset(state)
    assert seconds is not None
    assert seconds >= 0
    assert calls[-2:] == ['memcached.restart', 'side.warm_search']
    assert ('mysql.restart' in calls) == (state == 'db-cold')


def test_a_state_not_warmed_ends_with_the_cache_restart() -> None:
    """The plain reset is unchanged."""
    calls: list[str] = []
    assert _bench(calls, frozenset({'db-cold'})).reset('app-cold') is None
    assert calls[-1] == 'memcached.restart'
    assert 'side.warm_search' not in calls


def test_a_failed_warm_up_fails_the_run() -> None:
    """The state would not be the one the run sets out to measure."""
    with pytest.raises(WebRunError, match='warm_search exited 1'):
        _bench([], frozenset({'db-cold'}), status=1).reset('db-cold')


def test_the_promotion_window_holds_the_carry_over_and_the_cache_restart(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Between the application's stop and its start, as ``_promote.sh`` has them."""
    calls: list[str] = []
    bench = _bench(calls, frozenset())
    bench.promotion_source = 'bench_x_carry_source'
    steps: list[list[str]] = []

    def carry_over(side: object, arguments: list[str], env: object, errors_log: object) -> None:
        calls.append('carry_over')
        steps.append(list(arguments))

    def record_query(connection: object, statement: str, parameters: Any = ()) -> list[Any]:
        calls.append(f'{statement} {list(parameters)}')
        return []

    monkeypatch.setattr(bench_web, 'run_import_step', carry_over)
    monkeypatch.setattr(bench_web, 'query', record_query)
    bench.schema = 'bench_x'
    bench._connection = object()
    run: dict[str, Any] = {'metrics': {}}
    bench.time_promotion(run)
    # The planted rows go once the window has closed, before the application starts.
    assert calls == [
        'gunicorn.stop',
        'carry_over',
        'memcached.restart',
        "DELETE FROM `bench_x`.cart WHERE session_id LIKE %s ['bench-carry-%']",
        "DELETE FROM `bench_x`.django_session WHERE session_key LIKE %s ['bench-carry-%']",
        'gunicorn.start',
    ]
    assert steps == [['--carry-over-sessions-from', 'bench_x_carry_source']]
    metrics = run['metrics']
    assert 0 <= metrics['web.promotion.carry_over_s'] <= metrics['web.promotion.window_s']
