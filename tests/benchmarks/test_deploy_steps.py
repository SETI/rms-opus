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

    def __init__(
        self, calls: list[str], status: int = 0, served: list[tuple[int, str]] | None = None
    ) -> None:
        """Make a stand-in side.

        Parameters:
            calls: The shared list its warm-up is recorded into.
            status: What its warm-up exits with.
            served: The server's served log, which its warm-up's request is added to.
        """
        self.calls = calls
        self.status = status
        self.served = served if served is not None else []
        self.env: dict[str, str] | None = None
        self.url: str | None = None

    def warm_search(self, env: dict[str, str], url: str) -> subprocess.CompletedProcess[str]:
        """Record ``side.warm_search``, the environment and the server it was given.

        Parameters:
            env: The environment the warm-up would run in.
            url: The server it would warm.

        Returns:
            A finished process exiting with the side's status.
        """
        self.calls.append('side.warm_search')
        self.served.append((1, '/api/meta/result_count.json'))
        self.env = env
        self.url = url
        return subprocess.CompletedProcess([], self.status, 'out', 'err')


class _Gunicorn(_Recorder):
    """A recording gunicorn with a served log, which its start empties."""

    def __init__(self, calls: list[str]) -> None:
        """Make a stand-in gunicorn.

        Parameters:
            calls: The shared list each call is appended to.
        """
        super().__init__('gunicorn', calls)
        self.requests: list[tuple[int, str]] = []

    def start(self) -> None:
        """Record the start and empty the served log, as new workers have served nothing."""
        self.calls.append('gunicorn.start')
        self.requests.clear()

    def served(self) -> list[tuple[int, str]]:
        """Return the served log's requests since the last start.

        Returns:
            Each request's worker process id and path.
        """
        return list(self.requests)


def _bench(calls: list[str], warm_states: frozenset[str], status: int = 0) -> WebBench:
    """Return a WebBench over stand-ins; nothing is started."""
    bench = object.__new__(WebBench)
    gunicorn = _Gunicorn(calls)
    bench.side = _Side(calls, status, gunicorn.requests)  # type: ignore[assignment]
    bench.server = _Recorder('mysql', calls)  # type: ignore[assignment]
    bench.gunicorn = gunicorn  # type: ignore[assignment]
    bench.gunicorn.base_url = 'http://127.0.0.1:8000'  # type: ignore[misc]
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
    bench = _bench(calls, frozenset({state}))
    seconds = bench.reset(state)
    assert seconds is not None
    assert seconds >= 0
    assert calls[-2:] == ['memcached.restart', 'side.warm_search']
    assert bench.side.url == 'http://127.0.0.1:8000/'  # type: ignore[attr-defined]
    assert ('mysql.restart' in calls) == (state == 'db-cold')


def test_a_state_not_warmed_ends_with_the_cache_restart() -> None:
    """The plain reset is unchanged."""
    calls: list[str] = []
    assert _bench(calls, frozenset({'db-cold'})).reset('app-cold') is None
    assert calls[-1] == 'memcached.restart'
    assert 'side.warm_search' not in calls


def test_the_cold_check_comes_before_the_warm_up() -> None:
    """A request served before the warm-up fails the reset, and the warm-up never runs."""
    calls: list[str] = []
    bench = _bench(calls, frozenset({'db-cold'}))
    requests = bench.gunicorn.requests  # type: ignore[attr-defined]
    # A request reaches a worker between the application's start and the check.
    bench.memcached = SimpleNamespace(  # type: ignore[assignment]
        restart=lambda: requests.append((7, '/opus/'))
    )
    with pytest.raises(WebRunError, match='have served'):
        bench.reset('db-cold')
    assert 'side.warm_search' not in calls


def test_a_run_whose_states_warm_passes_the_cold_check() -> None:
    """The warm-up's own requests through the server do not fail the scenario after it."""
    calls: list[str] = []
    bench = _bench(calls, frozenset({'db-cold', 'app-cold'}))
    bench.config = SimpleNamespace(  # type: ignore[assignment]
        scenarios=[SimpleNamespace(name='landing')], concurrency=None
    )
    bench.promotion_source = None
    scenario_states: list[str] = []

    def run_scenario(state: str, *args: Any) -> list[Any]:
        scenario_states.append(state)
        bench._cache_gets += 1
        return []

    bench.run_scenario = run_scenario  # type: ignore[method-assign, assignment]
    bench.warm_up = lambda issued: {'rounds': 0}  # type: ignore[method-assign]
    run = bench.one_run()
    assert scenario_states == ['db-cold', 'app-cold', 'warm']
    assert sorted(run['details']['warm_search_s']) == [
        'web.app-cold.landing',
        'web.db-cold.landing',
    ]
    assert calls.count('side.warm_search') == 2


def test_a_failed_warm_up_fails_the_run() -> None:
    """The state would not be the one the run sets out to measure."""
    with pytest.raises(WebRunError, match='warm_search exited 1'):
        _bench([], frozenset({'db-cold'}), status=1).reset('db-cold')


#: What each step of a promotion costs on the test's clock, in seconds, each a distinct
#: power of two so that every sum of them names the steps it holds. A statement costs its
#: verb's.
_STEP_SECONDS = {
    'gunicorn.stop': 1.0,
    'carry_over': 2.0,
    'memcached.restart': 4.0,
    'gunicorn.start': 8.0,
    'DELETE': 16.0,
    'INSERT': 32.0,
}


class _StatementError(Exception):
    """Raised by the stand-in query for the statement a test makes fail."""


def _promotion_bench(
    monkeypatch: pytest.MonkeyPatch,
    calls: list[str],
    *,
    failing: str | None = None,
    failing_statement: str | None = None,
    rows: dict[str, int] | None = None,
) -> WebBench:
    """Return a WebBench ready to time a promotion over stand-ins, on a clock of its steps.

    The module's clock reads the sum of `_STEP_SECONDS` over the steps recorded so far,
    so each step takes its own time.

    Parameters:
        monkeypatch: Undoes the replaced carry-over, query and clock afterwards.
        calls: The list every step is recorded into: a server's method as
            ``<server>.<method>``, the carry-over as ``carry_over``, and a statement as
            its text followed by its parameters.
        failing: A step, as recorded (``<server>.<method>`` or ``carry_over``), that
            raises once recorded, `ServerError` for a server's and `WebRunError` for the
            carry-over; None for none.
        failing_statement: The beginning of a statement that raises `_StatementError`
            once recorded; None for none.
        rows: The single count a statement returns, by a part of its text; any other
            statement returns no rows.

    Returns:
        The bench, its promotion source ``bench_x_carry_source`` and its schema
        ``bench_x``.
    """
    bench = _bench(calls, frozenset())
    bench.promotion_source = 'bench_x_carry_source'
    bench.restore_pending = False
    bench.schema = 'bench_x'
    bench._connection = object()

    def carry_over(side: object, arguments: list[str], env: object, errors_log: object) -> None:
        """Record the carry-over as ``carry_over`` and then its arguments.

        Raises:
            WebRunError: After recording, when the carry-over is the failing step.
        """
        calls.append('carry_over')
        calls.append(' '.join(arguments))
        if failing == 'carry_over':
            raise WebRunError('carry_over failed')

    def record_query(connection: object, statement: str, parameters: Any = ()) -> list[Any]:
        """Record a statement and its parameters, and return its rows.

        Raises:
            _StatementError: After recording, when the statement is the failing one.
        """
        calls.append(f'{statement} {list(parameters)}')
        if failing_statement is not None and statement.startswith(failing_statement):
            raise _StatementError(statement)
        return [(count,) for part, count in (rows or {}).items() if part in statement]

    def now() -> float:
        """Return the seconds the steps recorded so far have taken."""
        return sum(
            seconds
            for call in calls
            for step, seconds in _STEP_SECONDS.items()
            if call == step or call.startswith(f'{step} ')
        )

    monkeypatch.setattr(bench_web, 'run_import_step', carry_over)
    monkeypatch.setattr(bench_web, 'query', record_query)
    monkeypatch.setattr(bench_web, 'time', SimpleNamespace(perf_counter=now))
    if failing is not None and failing != 'carry_over':
        server, method = failing.split('.')
        setattr(bench, server, _Recorder(server, calls, failing=method))
    return bench


#: The served schema's tables, as the statements `_promotion_bench` records name them.
_SERVED = {table: f'`bench_x`.`{table}`' for table in ('cart', 'django_session')}

#: Their saved copies in the promotion source, likewise.
_SAVED = {table: f'`bench_x_carry_source`.`saved_{table}`' for table in ('cart', 'django_session')}

#: The promotion source's mark, likewise.
_MARK = '`bench_x_carry_source`.`bench_web_promotion_source`'


def _replacing(target: dict[str, str], source: dict[str, str], mark: str) -> list[str]:
    """Return the statements that replace two tables' rows with others', as recorded."""
    return [
        'START TRANSACTION []',
        f'DELETE FROM {target["cart"]} []',
        f'DELETE FROM {target["django_session"]} []',
        f'INSERT INTO {target["django_session"]} SELECT * FROM {source["django_session"]} []',
        f'INSERT INTO {target["cart"]} SELECT * FROM {source["cart"]} []',
        f'{mark} []',
        'COMMIT []',
    ]


#: The statements that save the served schema's rows, marking a restore pending, and that
#: put them back, clearing the mark.
_SAVE = _replacing(_SAVED, _SERVED, f'INSERT INTO {_MARK} (`id`) VALUES (1)')
_RESTORE = _replacing(_SERVED, _SAVED, f'DELETE FROM {_MARK}')

#: The statement that drops the promotion source when the command ends, as recorded.
_DROP_SOURCE = 'DROP DATABASE IF EXISTS `bench_x_carry_source` []'


def test_the_promotion_window_runs_from_the_applications_stop_to_its_start(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The stop, the carry-over, the cache restart and the start, as ``_promote.sh`` has
    them; the served schema's own rows are saved before the window opens and put back
    after it has closed, so neither is in it."""
    calls: list[str] = []
    run: dict[str, Any] = {'metrics': {}}
    _promotion_bench(monkeypatch, calls).time_promotion(run)
    assert calls == [
        *_SAVE,
        'gunicorn.stop',
        'carry_over',
        '--carry-over-sessions-from bench_x_carry_source',
        'memcached.restart',
        'gunicorn.start',
        *_RESTORE,
    ]
    assert run['metrics'] == {
        'web.promotion.window_s': 15.0,
        'web.promotion.carry_over_s': 2.0,
    }


@pytest.mark.parametrize(
    ('failing', 'error', 'last'),
    [
        ('carry_over', WebRunError, '--carry-over-sessions-from bench_x_carry_source'),
        ('memcached.restart', ServerError, 'memcached.restart'),
        ('gunicorn.start', ServerError, 'gunicorn.start'),
    ],
)
def test_the_served_rows_are_put_back_when_a_step_fails(
    monkeypatch: pytest.MonkeyPatch, failing: str, error: type[Exception], last: str
) -> None:
    """The served schema is left as it was found, the failure reaches the caller, and
    nothing is left to put back, so the source is dropped when the command ends."""
    calls: list[str] = []
    bench = _promotion_bench(monkeypatch, calls, failing=failing)
    with pytest.raises(error, match=f'{failing} failed'):
        bench.time_promotion({'metrics': {}})
    assert calls[-len(_RESTORE) - 1 :] == [last, *_RESTORE]
    bench.drop_promotion_source()
    assert calls[-1] == _DROP_SOURCE


def test_a_save_that_fails_stops_nothing_and_puts_nothing_back(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Its transaction is rolled back, and the saved copies, which may be stale, are never
    copied over the served schema's rows."""
    calls: list[str] = []
    bench = _promotion_bench(monkeypatch, calls, failing_statement=f'INSERT INTO {_SAVED["cart"]}')
    with pytest.raises(_StatementError):
        bench.time_promotion({'metrics': {}})
    assert calls == [*_SAVE[:-2], 'ROLLBACK []']
    bench.drop_promotion_source()
    assert calls[-1] == _DROP_SOURCE


def test_a_restore_that_fails_is_rolled_back_and_raised(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The served tables are either all put back or left as the promotion left them."""
    calls: list[str] = []
    bench = _promotion_bench(monkeypatch, calls, failing_statement=f'INSERT INTO {_SERVED["cart"]}')
    with pytest.raises(_StatementError):
        bench.time_promotion({'metrics': {}})
    assert calls[-len(_RESTORE) + 1 :] == [*_RESTORE[:-2], 'ROLLBACK []']


def test_a_source_whose_restore_failed_is_kept_and_named(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """It holds the only copy of the served schema's rows, so the drop at the end raises
    naming it and drops nothing."""
    calls: list[str] = []
    bench = _promotion_bench(monkeypatch, calls, failing_statement=f'INSERT INTO {_SERVED["cart"]}')
    with pytest.raises(_StatementError):
        bench.time_promotion({'metrics': {}})
    recorded = len(calls)
    with pytest.raises(WebRunError, match='schema bench_x_carry_source is kept'):
        bench.drop_promotion_source()
    assert len(calls) == recorded
    assert bench.promotion_source == 'bench_x_carry_source'


#: The statement that asks whether the promotion source exists, as recorded.
_SOURCE_EXISTS = (
    'SELECT COUNT(*) FROM information_schema.SCHEMATA WHERE SCHEMA_NAME = %s '
    "['bench_x_carry_source']"
)

#: The statement that asks whether it holds the harness's mark, as recorded.
_SOURCE_MARKED = (
    'SELECT COUNT(*) FROM information_schema.TABLES WHERE TABLE_SCHEMA = %s AND '
    "TABLE_NAME = %s ['bench_x_carry_source', 'bench_web_promotion_source']"
)

#: The statement that asks whether its saved rows wait to be put back, as recorded.
_SOURCE_PENDING = f'SELECT COUNT(*) FROM {_MARK} []'


def _schema_statements(calls: list[str]) -> list[str]:
    """Return the statements recorded that make, drop or inspect a schema or table."""
    return [
        call
        for call in calls
        if call.startswith(('CREATE', 'DROP')) or 'information_schema' in call
    ]


#: The statements that make the promotion source, as recorded.
_MAKE_SOURCE = [
    'CREATE DATABASE `bench_x_carry_source` []',
    'CREATE TABLE `bench_x_carry_source`.`bench_web_promotion_source` (`id` INT) ENGINE=InnoDB []',
    'CREATE TABLE `bench_x_carry_source`.`django_session` LIKE `bench_x`.`django_session` []',
    'CREATE TABLE `bench_x_carry_source`.`saved_django_session` LIKE `bench_x`.`django_session` []',
    'CREATE TABLE `bench_x_carry_source`.`cart` LIKE `bench_x`.`cart` []',
    'CREATE TABLE `bench_x_carry_source`.`saved_cart` LIKE `bench_x`.`cart` []',
]


@pytest.mark.parametrize(
    ('exists', 'dropped'),
    [
        (0, []),
        (1, [_SOURCE_MARKED, 'DROP DATABASE `bench_x_carry_source` []']),
    ],
    ids=['absent', 'leftover'],
)
def test_the_promotion_source_is_made_after_dropping_the_harnesss_leftover(
    monkeypatch: pytest.MonkeyPatch, exists: int, dropped: list[str]
) -> None:
    """A schema of its name that holds the harness's mark is an earlier run's, and goes;
    the source made holds the mark, and the planted rows are counted."""
    calls: list[str] = []
    bench = _promotion_bench(
        monkeypatch,
        calls,
        rows={
            'SCHEMATA': exists,
            'information_schema.TABLES': 1,
            _SOURCE_PENDING[: -len(' []')]: 0,
            'FROM `bench_x_carry_source`.cart': 7,
        },
    )
    bench.promotion_source = None
    assert bench.prepare_promotion(10) == 7
    assert _schema_statements(calls) == [_SOURCE_EXISTS, *dropped, *_MAKE_SOURCE]
    assert bench.promotion_source == 'bench_x_carry_source'


def test_a_leftover_holding_saved_rows_puts_them_back_before_it_is_dropped(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """An earlier run that ended between its save and its restore left the served schema
    with the planted rows and the leftover with the only copy of its own: they are put
    back, and the mark's row cleared, before the leftover goes."""
    calls: list[str] = []
    bench = _promotion_bench(
        monkeypatch,
        calls,
        rows={
            'SCHEMATA': 1,
            'information_schema.TABLES': 1,
            _SOURCE_PENDING[: -len(' []')]: 1,
            'FROM `bench_x_carry_source`.cart': 7,
        },
    )
    bench.promotion_source = None
    assert bench.prepare_promotion(10) == 7
    recovered = [
        _SOURCE_EXISTS,
        _SOURCE_MARKED,
        _SOURCE_PENDING,
        *_RESTORE,
        'DROP DATABASE `bench_x_carry_source` []',
    ]
    assert calls[: len(recovered)] == recovered
    assert _schema_statements(calls[len(recovered) :]) == _MAKE_SOURCE
    assert (
        'put back the sessions and cart rows schema bench_x_carry_source' in capsys.readouterr().out
    )


def test_a_leftover_whose_saved_rows_cannot_be_put_back_is_kept_and_named(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The restore is rolled back, and nothing is dropped or made, then or when the command
    ends."""
    calls: list[str] = []
    bench = _promotion_bench(
        monkeypatch,
        calls,
        rows={'SCHEMATA': 1, 'information_schema.TABLES': 1, _SOURCE_PENDING[: -len(' []')]: 1},
        failing_statement=f'INSERT INTO {_SERVED["cart"]}',
    )
    bench.promotion_source = None
    with pytest.raises(
        WebRunError,
        match='schema bench_x_carry_source holds the sessions and cart rows a promotion saved',
    ):
        bench.prepare_promotion(10)
    bench.drop_promotion_source()
    assert calls == [
        _SOURCE_EXISTS,
        _SOURCE_MARKED,
        _SOURCE_PENDING,
        *_RESTORE[:-2],
        'ROLLBACK []',
    ]


def test_a_schema_of_the_sources_name_the_harness_did_not_make_is_refused_and_kept(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Without the mark it is someone else's: nothing is dropped or made, then or when the
    command ends."""
    calls: list[str] = []
    bench = _promotion_bench(
        monkeypatch, calls, rows={'SCHEMATA': 1, 'information_schema.TABLES': 0}
    )
    bench.promotion_source = None
    with pytest.raises(
        WebRunError,
        match='schema bench_x_carry_source exists and the harness did not make it',
    ):
        bench.prepare_promotion(10)
    bench.drop_promotion_source()
    assert calls == [_SOURCE_EXISTS, _SOURCE_MARKED]


def test_a_source_whose_making_fails_is_dropped_when_the_command_ends(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """It is named as soon as it exists, so the drop at the end finds it."""
    calls: list[str] = []
    bench = _promotion_bench(
        monkeypatch,
        calls,
        rows={'SCHEMATA': 0},
        failing_statement='CREATE TABLE `bench_x_carry_source`.`bench_web',
    )
    bench.promotion_source = None
    with pytest.raises(_StatementError):
        bench.prepare_promotion(10)
    bench.drop_promotion_source()
    assert calls[-1] == _DROP_SOURCE
