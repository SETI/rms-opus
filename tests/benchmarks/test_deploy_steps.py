"""The deploy a web run simulates: the landing page's warm-up, and the timed promotion.

The servers are stand-ins that record what they were asked to do, so the order of a
reset and of a promotion is checked without starting any of them.
"""

from __future__ import annotations

import subprocess  # nosec B404 - a stand-in's finished process
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from benchmarks import bench_web
from benchmarks.app_servers import ServerError
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

    def __init__(self, name: str, calls: list[str], failing: str | None = None) -> None:
        """Make a stand-in server.

        Parameters:
            name: The server's name, which prefixes each call recorded.
            calls: The shared list each call is appended to.
            failing: A method that raises once recorded, or None for none.
        """
        self.name = name
        self.calls = calls
        self.failing = failing

    def __getattr__(self, method: str) -> Any:
        """Return a stand-in for any method the stand-in server is asked for.

        Parameters:
            method: The method's name.

        Returns:
            A function that takes any arguments, appends ``<name>.<method>`` to the
            shared list, and returns None, or raises `ServerError` once it has appended
            when `method` is the recorder's ``failing`` method.
        """

        def record(*args: Any, **kwargs: Any) -> None:
            """Append ``<name>.<method>`` to the shared list, whatever the arguments.

            Raises:
                ServerError: After appending, when the method is the failing one.
            """
            self.calls.append(f'{self.name}.{method}')
            if method == self.failing:
                raise ServerError(f'{self.name}.{method} failed')

        return record


class _Side:
    """A side whose warm-up records itself and exits with a given status."""

    def __init__(self, calls: list[str], status: int = 0) -> None:
        """Make a stand-in side.

        Parameters:
            calls: The shared list its warm-up is recorded into.
            status: What its warm-up exits with.
        """
        self.calls = calls
        self.status = status
        self.env: dict[str, str] | None = None

    def warm_search(self, env: dict[str, str]) -> subprocess.CompletedProcess[str]:
        """Record ``side.warm_search`` and the environment it was given.

        Parameters:
            env: The environment the warm-up would run in.

        Returns:
            A finished process exiting with the side's status.
        """
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


#: What each step of a promotion costs on the test's clock, in seconds, each a distinct
#: power of two so that every sum of them names the steps it holds.
_STEP_SECONDS = {
    'gunicorn.stop': 1.0,
    'carry_over': 2.0,
    'memcached.restart': 4.0,
    'gunicorn.start': 8.0,
    'DELETE': 16.0,
}


def _promotion_bench(
    monkeypatch: pytest.MonkeyPatch, calls: list[str], *, failing: str | None = None
) -> WebBench:
    """Return a WebBench ready to time a promotion over stand-ins, on a clock of its steps.

    The module's clock reads the sum of `_STEP_SECONDS` over the steps recorded so far,
    so each step takes its own time.

    Parameters:
        monkeypatch: Undoes the replaced carry-over, query and clock afterwards.
        calls: The list every step is recorded into: a server's method as
            ``<server>.<method>``, the carry-over as ``carry_over``, and a statement as
            its text followed by its parameters.
        failing: A server's step, as recorded (``<server>.<method>``), that raises
            `ServerError` once recorded; None for none.

    Returns:
        The bench, its promotion source ``bench_x_carry_source`` and its schema
        ``bench_x``.
    """
    bench = _bench(calls, frozenset())
    bench.promotion_source = 'bench_x_carry_source'
    bench.schema = 'bench_x'
    bench._connection = object()

    def carry_over(side: object, arguments: list[str], env: object, errors_log: object) -> None:
        """Record the carry-over as ``carry_over`` and then its arguments."""
        calls.append('carry_over')
        calls.append(' '.join(arguments))

    def record_query(connection: object, statement: str, parameters: Any = ()) -> list[Any]:
        """Record a statement and its parameters, and return no rows."""
        calls.append(f'{statement} {list(parameters)}')
        return []

    def now() -> float:
        """Return the seconds the steps recorded so far have taken."""
        return sum(
            seconds
            for call in calls
            for step, seconds in _STEP_SECONDS.items()
            if call == step or (step == 'DELETE' and call.startswith(step))
        )

    monkeypatch.setattr(bench_web, 'run_import_step', carry_over)
    monkeypatch.setattr(bench_web, 'query', record_query)
    monkeypatch.setattr(bench_web, 'time', SimpleNamespace(perf_counter=now))
    if failing is not None:
        server, method = failing.split('.')
        setattr(bench, server, _Recorder(server, calls, failing=method))
    return bench


#: The statements that delete the planted rows, as `_promotion_bench` records them.
_DELETES = [
    "DELETE FROM `bench_x`.cart WHERE session_id LIKE %s ['bench-carry-%']",
    "DELETE FROM `bench_x`.django_session WHERE session_key LIKE %s ['bench-carry-%']",
]


def test_the_promotion_window_runs_from_the_applications_stop_to_its_start(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The stop, the carry-over, the cache restart and the start, as ``_promote.sh`` has
    them; the planted rows go once the window has closed, so their deletion is not in it."""
    calls: list[str] = []
    run: dict[str, Any] = {'metrics': {}}
    _promotion_bench(monkeypatch, calls).time_promotion(run)
    assert calls == [
        'gunicorn.stop',
        'carry_over',
        '--carry-over-sessions-from bench_x_carry_source',
        'memcached.restart',
        'gunicorn.start',
        *_DELETES,
    ]
    assert run['metrics'] == {
        'web.promotion.window_s': 15.0,
        'web.promotion.carry_over_s': 2.0,
    }


@pytest.mark.parametrize('failing', ['memcached.restart', 'gunicorn.start'])
def test_the_planted_rows_are_deleted_when_a_restart_fails(
    monkeypatch: pytest.MonkeyPatch, failing: str
) -> None:
    """The served schema is left as it was found, and the failure reaches the caller."""
    calls: list[str] = []
    bench = _promotion_bench(monkeypatch, calls, failing=failing)
    with pytest.raises(ServerError, match=f'{failing} failed'):
        bench.time_promotion({'metrics': {}})
    assert calls[-3:] == [failing, *_DELETES]
