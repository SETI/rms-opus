"""The import benchmark's incremental append, and how it tells that the append reloaded the
bundle. The server, the invocations and the schema copy are stand-ins; what is driven is
the check on the bundle's rows after the append."""

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
        '_server_now': lambda: 'the start',
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

    assert done == ['fresh server', f'--import {BUNDLE}', 'finalize']
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
        self.statements: list[str] = []

    def close(self) -> None:
        """Nothing to close."""


def _rows_written(
    monkeypatch: pytest.MonkeyPatch, answers: dict[str, list[tuple[Any, ...]]]
) -> tuple[int, int]:
    """Run the append check against a schema that answers as `answers` say.

    Returns:
        The check's count of rows, and of rows written before the append began.
    """
    connection = _Connection(answers)

    def query(conn: _Connection, statement: str, parameters: Any = ()) -> list[tuple[Any, ...]]:
        conn.statements.append(statement)
        return next(rows for key, rows in conn.answers.items() if key in statement)

    monkeypatch.setattr(bench_import, 'query', query)
    bench = object.__new__(bench_import.ImportBench)
    bench.server = SimpleNamespace(connect=lambda: connection)  # type: ignore[assignment]
    return bench._rows_written_since('bench_0', BUNDLE, ('local now', 10))


def test_a_side_with_a_timestamp_column_is_judged_by_it(monkeypatch: pytest.MonkeyPatch) -> None:
    """Each row's ``timestamp`` says when it was written."""
    answers: dict[str, list[tuple[Any, ...]]] = {
        'information_schema': [(1,)],
        'SUM(`timestamp`': [(40, 3)],
    }
    assert _rows_written(monkeypatch, answers) == (40, 3)


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
    answers: dict[str, list[tuple[Any, ...]]] = {
        'information_schema': [(0,)],
        'import_bundle': registry,
        'COUNT(*) FROM': [(40,)],
    }
    assert _rows_written(monkeypatch, answers) == expected
