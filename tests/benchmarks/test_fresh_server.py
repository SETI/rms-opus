"""Every timed import starts on a freshly restarted server."""

from pathlib import Path
from typing import Any, cast

from benchmarks.bench_import import ImportBench
from benchmarks.bench_server import MysqlServer
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
