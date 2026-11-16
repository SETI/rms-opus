"""The import benchmark's incremental append, and how it tells that the append reloaded the
bundle. The server, the invocations and the schema copy are stand-ins; what is driven is
the wait for the server's clock before the append and the check on the bundle's rows after
it."""

import time
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from benchmarks import bench_import
from benchmarks.monitor import RunFailedError

#: The bundle the stand-in scenario names as its largest.
BUNDLE = 'COISS_2002'


def _bench(tmp_path: Path, rows: int, stale: int) -> tuple[bench_import.ImportBench, list[str]]:
    """Return a bench whose append leaves the bundle `rows` rows, `stale` of them older.

    Returns:
        The bench, and the record of what it did, in order.
    """
    done: list[str] = []
    bench = object.__new__(bench_import.ImportBench)

    def server_now() -> str:
        """Record that the append's start was taken, and return a stand-in for it."""
        done.append('clock read')
        return 'the start'

    monitor = SimpleNamespace(
        expect_groups=lambda groups: None,
        expand_groups=lambda: None,
        records=[SimpleNamespace(wall_s=2.0)],
        summary=lambda: {'invocations': 1},
    )
    attributes: dict[str, Any] = {
        'scenario': SimpleNamespace(largest=BUNDLE),
        'server': object(),
        'schema_version': None,
        'label': SimpleNamespace(scratch_dir=tmp_path),
        'spelling': SimpleNamespace(bundle_import='--import'),
        'schema_name': lambda index, suffix='': f'bench_{index}{suffix}',
        '_prepare': lambda run_dir, schema: (tmp_path / 'opus.toml', tmp_path, monitor, []),
        'fresh_server': lambda run, before: done.append('fresh server'),
        '_wait_past_registered_start': lambda schema, bundle: done.append(
            f'wait past {bundle} in {schema}'
        ),
        '_server_now': server_now,
        '_invoke': lambda monitor, config, arguments: done.append(' '.join(arguments)),
        '_rows_written_since': lambda schema, bundle, since: (rows, stale),
        '_finalization': lambda monitor, config, timing: done.append('finalize'),
    }
    for name, value in attributes.items():
        setattr(bench, name, value)
    return bench, done


@pytest.fixture(autouse=True)
def _no_schemas(monkeypatch: pytest.MonkeyPatch) -> None:
    """Copy, drop and check nothing on a server."""
    monkeypatch.setattr(bench_import, 'clone_schema', lambda *args, **kwargs: 1.5)
    monkeypatch.setattr(bench_import, 'drop_schema', lambda *args, **kwargs: None)
    monkeypatch.setattr(bench_import, 'require_empty_errors_log', lambda *args, **kwargs: None)


def test_an_append_that_rewrote_every_row_is_measured_whatever_its_ids(tmp_path: Path) -> None:
    """Reloaded rows may keep their ids, as rows from a registered range do; what counts
    is that every one was written after the append began."""
    bench, done = _bench(tmp_path, rows=40, stale=0)
    run: dict[str, Any] = {'metrics': {}, 'details': {}}

    bench._incremental(run, 0, 'bench_0')

    assert done == [
        'fresh server',
        f'wait past {BUNDLE} in bench_0_incremental',
        'clock read',
        f'--import {BUNDLE}',
        'finalize',
    ]
    assert run['metrics'] == {
        'import.incremental.clone_s': 1.5,
        'import.incremental.wall_s': 2.0,
    }


@pytest.mark.parametrize(
    ('rows', 'stale'), [(40, 3), (40, 40), (0, 0)], ids=['some-old', 'all-old', 'none']
)
def test_an_append_that_left_old_rows_or_none_fails_the_run(
    rows: int, stale: int, tmp_path: Path
) -> None:
    """A row written before the append, or no row at all, means it did not reload the
    bundle, and nothing is finalized."""
    bench, done = _bench(tmp_path, rows=rows, stale=stale)

    with pytest.raises(RunFailedError, match=f'appending {BUNDLE} to bench_0_incremental'):
        bench._incremental({'metrics': {}, 'details': {}}, 0, 'bench_0')

    assert 'finalize' not in done


class _Connection:
    """A connection that answers the append check's queries from a table of answers."""

    def __init__(self, answers: dict[str, list[tuple[Any, ...]]]) -> None:
        """Answer each statement by the first key it contains."""
        self.answers = answers
        self.queries: list[tuple[str, list[Any]]] = []

    def close(self) -> None:
        """Nothing to close."""

    def bound(self, key: str) -> list[Any]:
        """Return the parameters bound to the first statement that contains `key`."""
        return next(parameters for statement, parameters in self.queries if key in statement)


def _bench_on(monkeypatch: pytest.MonkeyPatch, connection: _Connection) -> bench_import.ImportBench:
    """Return a bench whose server's every connection is `connection`.

    Parameters:
        monkeypatch: Replaces the harness's query function with one that answers from
            the connection's table.
        connection: The connection that records each statement and answers it.

    Returns:
        The bench.
    """

    def query(conn: _Connection, statement: str, parameters: Any = ()) -> list[tuple[Any, ...]]:
        """Record a statement and its parameters, and answer it by substring match.

        Parameters:
            conn: The connection the statement runs on.
            statement: The SQL, answered by the first key of the connection's table that
                it contains.
            parameters: The values bound to its placeholders.

        Returns:
            The rows the table gives for that key.
        """
        conn.queries.append((statement, list(parameters)))
        return next(rows for key, rows in conn.answers.items() if key in statement)

    monkeypatch.setattr(bench_import, 'query', query)
    bench = object.__new__(bench_import.ImportBench)
    bench.server = SimpleNamespace(connect=lambda: connection)  # type: ignore[assignment]
    return bench


def _rows_written(monkeypatch: pytest.MonkeyPatch, connection: _Connection) -> tuple[int, int]:
    """Run the append check against a schema that answers as `connection` says.

    The append began at ``('local now', 10)``: the server's clock in its own time zone
    and in UTC.

    Parameters:
        monkeypatch: Replaces the harness's query function (`_bench_on`).
        connection: The connection that answers the check's statements.

    Returns:
        The check's count of rows, and of rows written before the append began.
    """
    bench = _bench_on(monkeypatch, connection)
    return bench._rows_written_since('bench_0', BUNDLE, ('local now', 10))


def test_a_side_with_a_timestamp_column_is_judged_by_it(monkeypatch: pytest.MonkeyPatch) -> None:
    """Each row's ``timestamp`` says when it was written, against the append's local start."""
    connection = _Connection({'information_schema': [(1,)], 'SUM(`timestamp`': [(40, 3)]})
    assert _rows_written(monkeypatch, connection) == (40, 3)
    assert connection.bound('SUM(`timestamp`') == ['local now', BUNDLE]


@pytest.mark.parametrize(
    ('registry', 'expected'),
    [
        ([('done', 10, 40)], (40, 0)),
        ([('done', 9, 40)], (40, 40)),
        ([('done', 10, 39)], (40, 40)),
        ([('failed', 10, 40)], (40, 40)),
        ([('done', None, 40)], (40, 40)),
        ([], (40, 40)),
    ],
    ids=['reloaded', 'began-before', 'rows-uncounted', 'not-done', 'never-began', 'unregistered'],
)
def test_a_side_without_one_is_judged_by_the_registry(
    monkeypatch: pytest.MonkeyPatch, registry: list[tuple[Any, ...]], expected: tuple[int, int]
) -> None:
    """The bundle is done, its import began after the append did, and it counted every row."""
    connection = _Connection(
        {'information_schema': [(0,)], 'import_bundle': registry, 'COUNT(*) FROM': [(40,)]}
    )
    assert _rows_written(monkeypatch, connection) == expected


def _wait(
    monkeypatch: pytest.MonkeyPatch,
    connection: _Connection,
    slept: list[float],
    *,
    passes_after: int | None,
) -> None:
    """Run the wait for the clock against a schema that answers as `connection` says.

    Parameters:
        monkeypatch: Replaces the harness's query function, its sleep and its clock.
        connection: The connection that answers the wait's statements.
        slept: Given empty; receives the seconds of each sleep, in order.
        passes_after: How many sleeps pass before the server's clock is later than the
            registered start, or None for a clock that never passes it. Each sleep
            advances the harness's clock by the seconds slept.
    """

    def sleep(seconds: float) -> None:
        """Record a sleep, and let the server's clock pass the start after enough."""
        slept.append(seconds)
        if passes_after is not None and len(slept) == passes_after:
            connection.answers['UTC_TIMESTAMP() >'] = [(1,)]

    monkeypatch.setattr(time, 'sleep', sleep)
    monkeypatch.setattr(time, 'monotonic', lambda: sum(slept))
    bench = _bench_on(monkeypatch, connection)
    bench._wait_past_registered_start('bench_0_incremental', BUNDLE)


def test_the_append_waits_for_the_clock_to_pass_the_copied_start(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A copied ``started_at`` in the current second is waited out, polling the server."""
    connection = _Connection({'information_schema': [(1,)], 'UTC_TIMESTAMP() >': [(0,)]})
    slept: list[float] = []
    _wait(monkeypatch, connection, slept, passes_after=2)
    assert slept == [bench_import.CLOCK_POLL_S] * 2
    assert connection.bound('UTC_TIMESTAMP() >') == [BUNDLE]


@pytest.mark.parametrize(
    'answers',
    [
        {'information_schema': [(1,)], 'UTC_TIMESTAMP() >': [(1,)]},
        {'information_schema': [(1,)], 'UTC_TIMESTAMP() >': []},
        {'information_schema': [(0,)]},
    ],
    ids=['already-past', 'never-began', 'no-registry'],
)
def test_the_append_does_not_wait_without_a_later_start(
    monkeypatch: pytest.MonkeyPatch, answers: dict[str, list[tuple[Any, ...]]]
) -> None:
    """A start already past, a bundle never begun, or no registry: nothing to wait for."""
    slept: list[float] = []
    _wait(monkeypatch, _Connection(answers), slept, passes_after=None)
    assert slept == []


def test_a_clock_that_never_passes_the_start_fails_the_run(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The wait is bounded, so a registered start ahead of the server's clock is an error
    once the harness's clock has run `CLOCK_WAIT_LIMIT_S` seconds."""
    connection = _Connection({'information_schema': [(1,)], 'UTC_TIMESTAMP() >': [(0,)]})
    slept: list[float] = []
    with pytest.raises(RunFailedError, match=f'registered start of {BUNDLE} in bench_0_incr'):
        _wait(monkeypatch, connection, slept, passes_after=None)
    assert sum(slept) == pytest.approx(bench_import.CLOCK_WAIT_LIMIT_S)
