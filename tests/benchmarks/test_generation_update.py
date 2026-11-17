"""The incremental update benchmark: the invocations it makes into a served schema, the
metrics it records, and what it refuses. The server, the side's invocations and the
schema's version row are stand-ins; each invocation moves the row as the side's import
would, and its wall-clock is a distinct power of two, so every sum names the phases it
holds."""

from __future__ import annotations

import contextlib
import socket
from collections.abc import Iterator
from pathlib import Path
from types import SimpleNamespace
from typing import Any, ClassVar

import pytest

from benchmarks import bench_generation, bench_import, bench_server
from benchmarks.app_servers import ServerError
from benchmarks.bench_generation import GenerationBench, GenerationError, GenerationState
from benchmarks.import_scenarios import load_scenario
from benchmarks.monitor import InvocationRecord, RunFailedError
from benchmarks.results import ResultError, make_label
from benchmarks.sides import Side, Spelling

#: The help of a side that can update a schema in a generation.
_HELP = (
    '--import --finalize --validate --write-schema-version --timing-json --reset-search-tables '
    '--scorched-earth --yes --begin-generation --switch-generation --purge-generations '
    '--delete-bundles'
)

#: The same side's help without the generation options.
_HELP_WITHOUT = '--import --finalize --validate --write-schema-version --timing-json'

_SPELLING = Spelling.from_help(_HELP)

#: The timing options every invocation is given.
_TIMING = ('--timing-json', 't.json')

#: Each invocation's wall-clock, by role.
_WALLS = {
    'begin_generation': 1.0,
    'bundle_import': 2.0,
    'delete_bundles': 4.0,
    'finalize': 8.0,
    'validate': 16.0,
    'write_schema_version': 32.0,
    'switch_generation': 64.0,
    'purge_generations': 128.0,
}

#: What each descriptor group expands to.
_EXPANDED = {'COISS_2002': ['COISS_2002'], 'VG_28xx': ['VG_2801', 'VG_2802'], 'CO': ['COISS_2002']}

#: The generation the stand-in schema serves before the update.
_SERVED = 3


class _Server:
    """Records any attempt to stop, start, restart or connect to the owned server."""

    def __init__(self) -> None:
        self.calls: list[str] = []

    def restart(self) -> None:
        self.calls.append('restart')

    def stop(self) -> None:
        self.calls.append('stop')

    def start(self) -> None:
        self.calls.append('start')

    def connect(self, *args: Any, **kwargs: Any) -> None:
        self.calls.append('connect')

    #: Whether a bench_web command holds the web-runs lock.
    web_running = False

    @contextlib.contextmanager
    def web_runs_held(self, *, exclusive: bool) -> Iterator[None]:
        if self.web_running:
            raise ServerError('a bench_web command or another generation switch holds lock')
        self.calls.append(f'lock exclusive={exclusive}')
        try:
            yield
        finally:
            self.calls.append('unlock')


class _Monitor:
    """A monitor that keeps the records the stand-in invocations give it."""

    def __init__(self) -> None:
        self.records: list[InvocationRecord] = []
        self.groups: list[str] = []
        self.generation: int | None = None

    def expect_groups(self, groups: list[str]) -> None:
        self.groups = list(groups)

    def bundles_of(self, group: str) -> list[str]:
        assert group in self.groups
        return _EXPANDED[group]

    def summary(self) -> dict[str, Any]:
        return {'invocations': len(self.records)}


class _Stand:
    """The stand-ins one bench runs against, and what it did to them."""

    def __init__(self) -> None:
        self.server = _Server()
        self.monitor = _Monitor()
        self.state = GenerationState(_SERVED, None, None, revertible=False)
        self.invoked: list[list[str]] = []
        self.generation_at_import: list[int | None] = []
        self.kept: dict[str, int] = {}
        self.retired = 0
        self.busy: set[int] = set()
        #: Roles whose invocation leaves the version row as it found it.
        self.inert: set[str] = set()
        self.prepared: list[str] = []

    def move(self, role: str) -> None:
        """Move the version row as the side's invocation of `role` would."""
        state = self.state
        if role in self.inert:
            return
        if role == 'begin_generation':
            self.state = GenerationState(state.generation, state.generation + 1, 'writing', False)
        elif role == 'write_schema_version':
            self.state = GenerationState(state.generation, state.pending_generation, 'ready', False)
        elif role == 'switch_generation':
            assert state.pending_generation is not None
            self.state = GenerationState(state.pending_generation, None, None, revertible=True)
        elif role == 'purge_generations':
            self.state = GenerationState(state.generation, None, None, revertible=False)


def _bench(stand: _Stand, tmp_path: Path) -> GenerationBench:
    """Return a bench over `stand`; nothing runs."""
    bench = GenerationBench(
        schema='served',
        web_ports=(8000, 21211),
        is_listening=lambda port: port in stand.busy,
        server=stand.server,
        side=Side(python=Path('python'), repo_root=Path()),
        spelling=_SPELLING,
        label=make_label(pr='PR-23', side='after', scale='test', session='g', date='2026-11-14'),
        scenario=None,
        cache_location='127.0.0.1:1',
    )
    statuses = iter(
        [
            {'Com_commit': 1, 'Innodb_rows_inserted': 10},
            {'Com_commit': 5, 'Innodb_rows_inserted': 30},
        ]
    )

    def prepare(run_dir: Path, schema: str) -> tuple[Path, Path, _Monitor, tuple[str, ...]]:
        stand.prepared.append(schema)
        stand.monitor = _Monitor()
        return tmp_path / 'opus.toml', tmp_path / 'ERRORS.log', stand.monitor, _TIMING

    def invoke(monitor: _Monitor, config_file: Path, arguments: list[str]) -> None:
        stand.invoked.append(list(arguments))
        role = _SPELLING.role(arguments)
        name = role.split(':', 1)[0]
        if name == 'bundle_import':
            stand.generation_at_import.append(monitor.generation)
        wall = _WALLS[name]
        monitor.records.append(
            InvocationRecord(
                name=role,
                arguments=tuple(arguments),
                wall_s=wall,
                peak_rss_kb=int(wall * 100),
                peak_tree_pss_kb=int(wall * 10),
                peak_checkpoint_age_bytes=7 if name == 'bundle_import' else None,
                timings={'total': wall, f'{name}_step': wall / 2},
            )
        )
        stand.move(name)

    def status() -> dict[str, int]:
        return next(statuses)

    attributes: dict[str, Any] = {
        '_prepare': prepare,
        '_invoke': invoke,
        '_status': status,
        'generation_state': lambda: stand.state,
        'rows_in_generation': lambda bundles, generation: stand.kept,
        'generation_rows': lambda generation: (10, 4),
        'retired_rows': lambda generation: stand.retired,
    }
    for name, value in attributes.items():
        setattr(bench, name, value)
    return bench


@pytest.fixture(autouse=True)
def dropped_schemas(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    """Record any schema dropped or copied, and check no log or server."""
    dropped: list[str] = []
    for module in (bench_import, bench_server):
        monkeypatch.setattr(module, 'drop_schema', lambda *args: dropped.append('drop'))
        monkeypatch.setattr(module, 'clone_schema', lambda *args, **kw: dropped.append('clone'))
    monkeypatch.setattr(bench_generation, 'require_empty_errors_log', lambda *a, **k: None)
    monkeypatch.setattr(bench_generation, 'bulk_load_paths', lambda log_dir: [])
    return dropped


def _update(bundles: str = 'COISS_2002', drop: str | None = 'VG_28xx') -> Any:
    """Return an update request."""
    return bench_generation.UpdateRequest(bundles=bundles, drop=drop)


def test_an_update_runs_each_phase_in_order_with_its_flags(tmp_path: Path) -> None:
    """Begin, the re-import, the drop, then the closing invocations, each timed."""
    stand = _Stand()
    _bench(stand, tmp_path).run_update(_update())
    assert stand.invoked == [
        ['--begin-generation', *_TIMING],
        ['--import', *_TIMING, 'COISS_2002'],
        ['--delete-bundles', *_TIMING, 'VG_28xx'],
        ['--finalize', *_TIMING],
        ['--validate', *_TIMING],
        ['--write-schema-version', *_TIMING],
    ]
    assert stand.prepared == ['served']


def test_an_update_records_each_phase_and_their_sum(tmp_path: Path) -> None:
    """Each invocation is its own metric; the steps, memory and counters are the update's."""
    stand = _Stand()
    run = _bench(stand, tmp_path).run_update(_update())
    assert run['kind'] == 'generation_update'
    assert run['metrics'] == {
        'import.generation.begin.wall_s': 1.0,
        'import.generation.import.wall_s': 2.0,
        'import.generation.delete.wall_s': 4.0,
        'import.generation.finalize.wall_s': 8.0,
        'import.generation.validate.wall_s': 16.0,
        'import.generation.write_schema_version.wall_s': 32.0,
        'import.generation.update.wall_s': 63.0,
        'import.generation.update.phase.begin_generation_step_s': 0.5,
        'import.generation.update.phase.bundle_import_step_s': 1.0,
        'import.generation.update.phase.delete_bundles_step_s': 2.0,
        'import.generation.update.phase.finalize_step_s': 4.0,
        'import.generation.update.phase.validate_step_s': 8.0,
        'import.generation.update.phase.write_schema_version_step_s': 16.0,
        'import.generation.update.peak_tree_pss_kb': 320,
        'import.generation.update.peak_rss_kb': 3200,
        'import.generation.update.server.peak_checkpoint_age_bytes': 7,
        'import.generation.update.server.Com_commit': 4,
        'import.generation.update.server.Innodb_rows_inserted': 20,
    }


def test_an_update_records_what_it_changed(tmp_path: Path) -> None:
    """The details name the schema, the generation, the bundles each way and the rows."""
    stand = _Stand()
    details = _bench(stand, tmp_path).run_update(_update())['details']
    assert {key: details[key] for key in ('schema', 'generation', 'bundles', 'drop')} == {
        'schema': 'served',
        'generation': _SERVED + 1,
        'bundles': 'COISS_2002',
        'drop': 'VG_28xx',
    }
    assert details['bundles_imported'] == ['COISS_2002']
    assert details['bundles_dropped'] == ['VG_2801', 'VG_2802']
    assert (details['rows_added'], details['rows_retired']) == (10, 4)


def test_the_import_is_checked_in_the_generation_begun(tmp_path: Path) -> None:
    """The bundles' landing check counts the pending generation's rows alone."""
    stand = _Stand()
    _bench(stand, tmp_path).run_update(_update())
    assert stand.generation_at_import == [_SERVED + 1]


def test_an_update_without_a_drop_list_deletes_nothing(tmp_path: Path) -> None:
    """No ``--delete-bundles`` invocation, and no metric for one."""
    stand = _Stand()
    run = _bench(stand, tmp_path).run_update(_update(drop=None))
    assert ['--delete-bundles', *_TIMING, 'VG_28xx'] not in stand.invoked
    assert len(stand.invoked) == 5
    assert 'import.generation.delete.wall_s' not in run['metrics']
    assert run['metrics']['import.generation.update.wall_s'] == 59.0


def test_a_bundle_both_re_imported_and_dropped_is_refused_before_anything_runs(
    tmp_path: Path,
) -> None:
    """A re-import already replaces the bundle's rows; dropping it too is a mistake."""
    stand = _Stand()
    with pytest.raises(RunFailedError, match=r"\['COISS_2002'\] would be both"):
        _bench(stand, tmp_path).run_update(_update(bundles='CO', drop='COISS_2002'))
    assert stand.invoked == []


def test_a_begin_that_leaves_no_generation_writing_fails_the_run(tmp_path: Path) -> None:
    """Nothing is imported into a generation that was not begun."""
    stand = _Stand()
    stand.inert.add('begin_generation')
    with pytest.raises(RunFailedError, match='pending generation None'):
        _bench(stand, tmp_path).run_update(_update())
    assert stand.invoked == [['--begin-generation', *_TIMING]]


def test_a_dropped_bundle_left_in_the_generation_fails_the_run(tmp_path: Path) -> None:
    """The finalization would count a bundle that was asked to go."""
    stand = _Stand()
    stand.kept = {'VG_2801': 12}
    with pytest.raises(RunFailedError, match=r"rows of \{'VG_2801': 12\}"):
        _bench(stand, tmp_path).run_update(_update())
    assert ['--finalize', *_TIMING] not in stand.invoked


def test_an_update_not_stamped_ready_fails_the_run(tmp_path: Path) -> None:
    """A generation the switch would refuse is not a finished update."""
    stand = _Stand()
    stand.inert.add('write_schema_version')
    with pytest.raises(RunFailedError, match="in state 'writing', not 4 'ready'"):
        _bench(stand, tmp_path).run_update(_update())


def _ready() -> GenerationState:
    """Return the version row of a schema whose next generation is ready to switch."""
    return GenerationState(_SERVED, _SERVED + 1, 'ready', revertible=False)


def test_a_switch_switches_then_purges_and_records_each(tmp_path: Path) -> None:
    """The switch is the service's downtime and the purge runs while it serves; each is a
    metric, beside their sum and the run's own steps, memory and counters."""
    stand = _Stand()
    stand.state = _ready()
    run = _bench(stand, tmp_path).run_switch()
    assert stand.invoked == [['--switch-generation', *_TIMING], ['--purge-generations', *_TIMING]]
    assert run['kind'] == 'generation_switch'
    assert run['metrics'] == {
        'import.generation.switch.wall_s': 64.0,
        'import.generation.purge.wall_s': 128.0,
        'import.generation.switch_purge.wall_s': 192.0,
        'import.generation.switch_purge.phase.switch_generation_step_s': 32.0,
        'import.generation.switch_purge.phase.purge_generations_step_s': 64.0,
        'import.generation.switch_purge.peak_tree_pss_kb': 1280,
        'import.generation.switch_purge.peak_rss_kb': 12800,
        'import.generation.switch_purge.server.Com_commit': 4,
        'import.generation.switch_purge.server.Innodb_rows_inserted': 20,
    }
    assert run['details']['generation'] == _SERVED + 1


def test_an_update_and_its_switch_neither_restart_nor_drop(
    tmp_path: Path, dropped_schemas: list[str]
) -> None:
    """The schema is updated in place on the running server, which another process may be
    serving from."""
    stand = _Stand()
    bench = _bench(stand, tmp_path)
    bench.run_update(_update())
    bench._status = iter([{}, {}]).__next__  # type: ignore[method-assign]
    bench.run_switch()
    assert stand.server.calls == ['lock exclusive=True', 'unlock']
    assert dropped_schemas == []


def test_a_switch_is_refused_while_a_bench_web_command_holds_the_lock(tmp_path: Path) -> None:
    """Its ports can all be quiet for a moment while a reset restarts the servers."""
    stand = _Stand()
    stand.state = _ready()
    stand.server.web_running = True
    with pytest.raises(RunFailedError, match='holds lock: the switch empties'):
        _bench(stand, tmp_path).run_switch()
    assert stand.invoked == []


def test_a_switch_holds_the_lock_exclusive_through_the_purge(tmp_path: Path) -> None:
    """Released only after the purge, and released when the switch fails too."""
    stand = _Stand()
    stand.state = _ready()
    stand.server.calls = []
    bench = _bench(stand, tmp_path)
    bench._status = iter([{}] * 4).__next__  # type: ignore[method-assign]
    invoked_while_locked: list[list[str]] = []
    invoke = bench._invoke

    def recording_invoke(*args: Any, **kwargs: Any) -> None:
        invoke(*args, **kwargs)
        assert stand.server.calls[-1] == 'lock exclusive=True'
        invoked_while_locked.append(stand.invoked[-1])

    bench._invoke = recording_invoke  # type: ignore[method-assign]
    bench.run_switch()
    assert [args[0] for args in invoked_while_locked] == [
        '--switch-generation',
        '--purge-generations',
    ]
    assert stand.server.calls[-1] == 'unlock'
    stand.state = _ready()
    stand.inert.add('switch_generation')
    with pytest.raises(RunFailedError):
        bench.run_switch()
    assert stand.server.calls[-1] == 'unlock'


def test_a_switch_is_refused_while_bench_web_listens(tmp_path: Path) -> None:
    """The switch empties the search tables and the cache that a web run is reading."""
    stand = _Stand()
    stand.state = _ready()
    stand.busy = {8000}
    with pytest.raises(RunFailedError, match=r'port \[8000\]: the switch'):
        _bench(stand, tmp_path).run_switch()
    assert stand.invoked == []


@pytest.mark.parametrize(
    'state',
    [
        GenerationState(_SERVED, None, None, revertible=True),
        GenerationState(_SERVED, _SERVED + 1, 'validated', revertible=False),
    ],
    ids=['already-switched', 'not-stamped'],
)
def test_a_switch_without_a_generation_ready_is_refused(
    state: GenerationState, tmp_path: Path
) -> None:
    """The side's switch succeeds doing nothing on a switched schema, which is no
    measurement, and refuses an unstamped one."""
    stand = _Stand()
    stand.state = state
    with pytest.raises(RunFailedError, match='no generation ready to switch'):
        _bench(stand, tmp_path).run_switch()
    assert stand.invoked == []


def test_a_switch_that_does_not_serve_the_generation_fails_before_the_purge(
    tmp_path: Path,
) -> None:
    """Purging a generation that is not served would delete what is."""
    stand = _Stand()
    stand.state = _ready()
    stand.inert.add('switch_generation')
    with pytest.raises(RunFailedError, match='serving generation 3 with 4 pending'):
        _bench(stand, tmp_path).run_switch()
    assert stand.invoked == [['--switch-generation', *_TIMING]]


def test_a_purge_that_leaves_retired_rows_fails_the_run(tmp_path: Path) -> None:
    """The purge's time is only its work when it finished it."""
    stand = _Stand()
    stand.state = _ready()
    stand.retired = 5
    with pytest.raises(RunFailedError, match='with 5 retired rows'):
        _bench(stand, tmp_path).run_switch()


def test_an_invocation_outside_an_update_has_no_phase() -> None:
    """Every recorded invocation is one of the update's or the switch's."""
    with pytest.raises(RunFailedError, match='`erase` is not an invocation'):
        bench_generation.phase_of('erase')


# --- the command line --------------------------------------------------------------------


def _argv(*extra: str) -> list[str]:
    """Return a command line with the given options added."""
    return [
        '--scale', 'test', '--side', 'after', '--pr', 'PR-23', '--session', 'g',
        '--python', 'python', '--repo-root', '.', '--schema', 'served', *extra,
    ]  # fmt: skip


@pytest.mark.parametrize(
    ('extra', 'message'),
    [
        ((), 'give the bundles to update'),
        (('--switch-only', '--bundles', 'A'), 'it takes no bundles'),
        (('--switch-only', '--drop', 'A'), 'it takes no bundles'),
        (('--bundles', 'A', '--incremental-group', 'test'), 'not allowed with argument'),
        (('--bundles', 'A', '--stop-before-switch', '--switch-only'), 'not allowed with'),
    ],
    ids=['no-bundles', 'switch-with-bundles', 'switch-with-drop', 'two-lists', 'two-modes'],
)
def test_incoherent_command_lines_are_refused(
    extra: tuple[str, ...], message: str, capsys: pytest.CaptureFixture[str]
) -> None:
    """Each mode takes what it acts on and nothing else."""
    with pytest.raises(SystemExit):
        bench_generation._parse_arguments(_argv(*extra))
    assert message in capsys.readouterr().err


def test_the_incremental_group_is_the_named_scenarios_largest_bundle(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """The test scale's incremental group can update a schema of any scale."""
    monkeypatch.setenv('PDS_DROPBOX_ROOT', str(tmp_path))
    args = bench_generation._parse_arguments(_argv('--incremental-group', 'test', '--drop', 'B'))
    request = bench_generation.update_request(args)
    assert request.bundles == load_scenario('test').largest
    assert request.drop == 'B'


@pytest.mark.parametrize(
    ('largest', 'incremental'), [(None, False), ('NHPELO_1001', False)], ids=['none', 'alone']
)
def test_a_scenario_without_an_incremental_group_is_refused(
    largest: str | None, incremental: bool, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A scenario names no group, or names a largest bundle it does not append."""
    monkeypatch.setattr(
        bench_generation,
        'load_scenario',
        lambda scale: SimpleNamespace(largest=largest, incremental=incremental),
    )
    args = bench_generation._parse_arguments(_argv('--incremental-group', 'complete'))
    with pytest.raises(GenerationError, match='complete scenario has no incremental group'):
        bench_generation.update_request(args)


def test_a_side_without_generations_is_refused() -> None:
    """Its import has no way to begin one."""
    with pytest.raises(GenerationError, match='has no --begin-generation'):
        bench_generation.require_generations(Spelling.from_help(_HELP_WITHOUT))
    bench_generation.require_generations(_SPELLING)


class _MainServer:
    """The owned server as `main` sees it, recording any start or stop."""

    running = True
    calls: ClassVar[list[str]] = []

    def __init__(self, config: object) -> None:
        self.calls.append('made')

    def is_running(self) -> bool:
        return self.running

    def start(self) -> None:
        self.calls.append('start')

    def stop(self) -> None:
        self.calls.append('stop')


def _patch_main(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, help_text: str, *, running: bool = True
) -> list[tuple[dict[str, Any], list[str]]]:
    """Make `main` run against stand-ins, and return the appends it makes.

    Each append is the environment as it then was, and the kinds of the runs appended.
    """
    monkeypatch.delenv('PYTHONPATH', raising=False)
    monkeypatch.setenv('PDS_DROPBOX_ROOT', str(tmp_path))
    monkeypatch.setattr(bench_generation, 'load_server_config', lambda: (None, 'memcached'))
    monkeypatch.setattr(bench_generation, 'reexec_with_socket', lambda *args: None)
    monkeypatch.setattr(Side, 'import_help', lambda self: help_text)
    monkeypatch.setattr(Side, 'environment', lambda self: {'git_sha': 'abc'})
    monkeypatch.setattr(_MainServer, 'running', running)
    monkeypatch.setattr(_MainServer, 'calls', [])
    monkeypatch.setattr(bench_generation, 'MysqlServer', _MainServer)
    monkeypatch.setattr(bench_generation, 'server_environment', lambda server: {})
    monkeypatch.setattr(bench_generation, 'host_environment', dict)
    monkeypatch.setattr(bench_generation, 'file_bulk_load_path', lambda label, runs: 'x')
    monkeypatch.setattr(
        GenerationBench,
        'run_update',
        lambda self, update: {
            'kind': 'generation_update',
            'metrics': {'import.generation.update.wall_s': 1.0},
        },
    )
    monkeypatch.setattr(
        GenerationBench,
        'run_switch',
        lambda self: {
            'kind': 'generation_switch',
            'metrics': {
                'import.generation.switch.wall_s': 1.0,
                'import.generation.purge.wall_s': 2.0,
            },
        },
    )
    appended: list[tuple[dict[str, Any], list[str]]] = []

    def append(label: Any, environment: dict[str, Any], runs: list[dict[str, Any]]) -> Path:
        appended.append((dict(environment), [run['kind'] for run in runs]))
        return Path('result.json')

    monkeypatch.setattr(bench_generation, 'append_runs', append)
    monkeypatch.setattr(bench_generation, 'require_appendable', lambda label, environment: None)
    return appended


def test_main_refuses_a_side_without_generations_before_using_the_server(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    appended = _patch_main(monkeypatch, tmp_path, _HELP_WITHOUT)
    with pytest.raises(SystemExit, match='has no --begin-generation'):
        bench_generation.main(_argv('--bundles', 'COISS_2002'))
    assert _MainServer.calls == []
    assert appended == []


def test_main_refuses_a_stopped_server_and_never_starts_it(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Starting it here would mean stopping it after, under a web run started meanwhile."""
    appended = _patch_main(monkeypatch, tmp_path, _HELP, running=False)
    with pytest.raises(SystemExit, match='is not running'):
        bench_generation.main(_argv('--bundles', 'COISS_2002'))
    assert _MainServer.calls == ['made']
    assert appended == []


@pytest.mark.parametrize(
    ('mode', 'kinds'),
    [
        ((), [['generation_update'], ['generation_switch']]),
        (('--stop-before-switch',), [['generation_update']]),
    ],
    ids=['full', 'stop-before-switch'],
)
def test_main_records_the_update_and_the_switch_asked_for(
    mode: tuple[str, ...],
    kinds: list[list[str]],
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Each is appended as it finishes, with the schema and the bundles pinned."""
    appended = _patch_main(monkeypatch, tmp_path, _HELP)
    bench_generation.main(_argv('--bundles', 'COISS_2002', '--drop', 'VG_28xx', *mode))
    assert [runs for _, runs in appended] == kinds
    environment = appended[0][0]
    assert environment['generation_schema'] == 'served'
    assert environment['schema'] == 'served'
    assert environment['generation_update'] == {'bundles': 'COISS_2002', 'drop': 'VG_28xx'}
    assert (environment['importers'], environment['coordinator_importers']) == (None, None)


@pytest.mark.parametrize('mode', [(), ('--switch-only',)], ids=['update', 'switch-only'])
def test_main_refuses_a_label_that_cannot_take_its_runs_before_any_work(
    mode: tuple[str, ...], monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A finished update whose runs the file refused would leave a pending generation
    unrecorded, and block the rerun under a corrected label."""
    appended = _patch_main(monkeypatch, tmp_path, _HELP)
    checked: list[dict[str, Any]] = []
    worked: list[str] = []

    def refuse(label: Any, environment: dict[str, Any]) -> None:
        checked.append(dict(environment))
        raise ResultError('generation_update was something else')

    monkeypatch.setattr(bench_generation, 'require_appendable', refuse)
    monkeypatch.setattr(GenerationBench, 'run_update', lambda self, update: worked.append('u'))
    monkeypatch.setattr(GenerationBench, 'run_switch', lambda self: worked.append('s'))
    argv = _argv(*(mode or ('--bundles', 'COISS_2002')))
    with pytest.raises(SystemExit, match='generation_update was'):
        bench_generation.main(argv)
    assert worked == []
    assert appended == []
    assert ('generation_update' in checked[0]) is (mode == ())


def test_main_switches_alone_without_naming_bundles(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A switch of an earlier update's generation pins the schema but no bundle list."""
    appended = _patch_main(monkeypatch, tmp_path, _HELP)
    bench_generation.main(_argv('--switch-only'))
    assert [runs for _, runs in appended] == [['generation_switch']]
    assert appended[0][0]['generation_schema'] == 'served'
    assert 'generation_update' not in appended[0][0]


def test_a_listening_port_is_told_from_a_quiet_one() -> None:
    """What the switch's refusal reads."""
    with socket.socket() as server:
        server.bind(('127.0.0.1', 0))
        server.listen()
        port = server.getsockname()[1]
        assert bench_generation.listening(port) is True
    assert bench_generation.listening(port) is False
