"""Every timed import starts on a freshly restarted server, after warm holdings."""

from pathlib import Path
from typing import Any, cast

import pytest

from benchmarks import bench_import
from benchmarks.bench_import import ImportBench
from benchmarks.bench_server import MysqlServer
from benchmarks.compare import COMPARED_KINDS
from benchmarks.import_scenarios import ImportScenario
from benchmarks.results import make_label, new_run
from benchmarks.sides import Side, Spelling


class _Server:
    """Counts restarts in place of the owned server."""

    def __init__(self) -> None:
        self.restarts = 0

    def restart(self) -> None:
        self.restarts += 1


def _bench(server: _Server) -> ImportBench:
    """Return an import bench around a stand-in server; nothing runs."""
    return ImportBench(
        server=cast('MysqlServer', server),
        side=Side(python=Path('python'), repo_root=Path()),
        spelling=Spelling.from_help(''),
        label=make_label(pr='PR-00', side='before', scale='test', session='a', date='2026-11-05'),
        scenario=cast('ImportScenario', None),
        cache_location='127.0.0.1:1',
    )


def test_each_restart_is_recorded_under_what_it_precedes() -> None:
    """A run's details say which of its imports began on a restarted server."""
    server = _Server()
    bench = _bench(server)
    run: dict[str, Any] = new_run('import')
    for before in ('run', 'largest_alone', 'incremental'):
        bench.fresh_server(run, before)
    assert server.restarts == 3
    restarts = run['details']['server_restarts']
    assert set(restarts) == {'run', 'largest_alone', 'incremental'}
    assert all(seconds >= 0 for seconds in restarts.values())


def test_the_warm_up_imports_without_finalizing_and_is_never_compared(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The warm-up reads the holdings once, leaves no schema, and is not a timed kind."""
    bench = _bench(_Server())
    calls: list[tuple[object, dict[str, Any]]] = []
    dropped: list[str] = []

    def run_holdings(index: object, **options: Any) -> tuple[dict[str, Any], str]:
        calls.append((index, options))
        return new_run('import_unfinalized'), 'bench_test_before_a_warmup'

    monkeypatch.setattr(bench, 'run_holdings', run_holdings)
    monkeypatch.setattr(bench_import, 'drop_schema', lambda _server, name: dropped.append(name))
    run = bench.warm_up()
    assert calls == [('warmup', {'profile': False, 'finalize': False})]
    assert dropped == ['bench_test_before_a_warmup']
    assert run['kind'] == 'import_warmup'
    assert run['kind'] not in COMPARED_KINDS
    assert 'complete' not in bench_import.WARMED_SCALES
