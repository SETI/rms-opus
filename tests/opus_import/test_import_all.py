"""Tests for the full-holdings import's coordinator.

``opus_import_all`` is the one command in this distribution that runs for days, and no
unit test can run it. What is checkable without holdings or a database is what decides
the run: the steps each command line runs and their order, the guards in front of them
(the erase only when asked for, its confirmation, ``--finish``'s refusal of an
unfinished registry, stopping at the first step that fails), how the workers are divided
among the importers, and how the coordinator decides, from a reading of the registry,
whether the run is over. ``import_tests/test_coordinator.py`` runs it against MySQL.
"""

from __future__ import annotations

import datetime
from typing import Any

import pytest

from opus_config import ConfigError
from opus_config.config import ImportConfig
from opus_import import import_all
from opus_import.import_processes import BundleStatus, ProcessStatus, Snapshot

#: When the readings below were taken.
_NOW = datetime.datetime(2026, 11, 11, 12, 0, 0)


def _import_table(**keys: object) -> ImportConfig:
    """Return an ``[import]`` table with the keys given and every other default."""
    values: dict[str, object] = {
        'log_file': 'import.log',
        'debug_log_file': 'import_debug.log',
        'bulk_load': True,
        'scratch_dir': None,
        'transaction_rows': 100_000,
        'index_workers': 1,
        'server_tmpdir': None,
        'workers': 1,
        'cpu_fraction': 0.75,
        'worker_rows': 500,
        'importers': 1,
        'stall_warning_minutes': 30,
        'status_interval_minutes': 5,
    }
    values.update(keys)
    return ImportConfig(**values)  # type: ignore[arg-type]


@pytest.fixture
def recorded_steps(monkeypatch: pytest.MonkeyPatch) -> list[list[str]]:
    """Record what `import_all.run_step` and `import_all.coordinate` are asked to run.

    The registry ``--finish`` reads is empty, so it never refuses; the configuration is
    a default one on a computer of eight cores.

    Returns:
        The list each recorded invocation is appended to, in the order the run reaches
        them; a coordinated run is recorded as ``['coordinate', <workers per importer>]``.
    """
    steps: list[list[str]] = []

    def record(arguments: list[str]) -> int:
        steps.append(arguments)
        return 0

    def coordinate(
        schema: str | None, division: import_all.Division, extra: Any, **kwargs: Any
    ) -> int:
        steps.append(['coordinate', ','.join(str(n) for n in division.per_importer)])
        return 0

    monkeypatch.setattr(import_all, 'run_step', record)
    monkeypatch.setattr(import_all, 'coordinate', coordinate)
    monkeypatch.setattr(import_all, 'registry_states', lambda _schema: [])
    _eight_cores(monkeypatch)
    return steps


def _eight_cores(monkeypatch: pytest.MonkeyPatch, **keys: object) -> None:
    """Make the division read a default configuration on a computer of eight cores."""
    import opus_config
    import opus_config.config

    class _Config:
        import_ = _import_table(**keys)

    monkeypatch.setattr(opus_config, 'get_config', lambda: _Config())
    monkeypatch.setattr(opus_config.config, 'detected_cores', lambda: 8)


def _run(monkeypatch: pytest.MonkeyPatch, *arguments: str) -> None:
    """Run ``opus_import_all`` with the given arguments."""
    monkeypatch.setattr('sys.argv', ['opus_import_all', *arguments])
    import_all.main()


# ---------------------------------------------------------------------------
# The division
# ---------------------------------------------------------------------------


def test_the_default_is_one_importer_with_one_worker() -> None:
    """[import] workers and importers both default to 1: one sequential importer."""
    division = import_all.resolve_division(_import_table(), None, 'auto', detected=8)
    assert (division.workers, division.importers, division.per_importer) == (1, 1, (1,))


def test_a_total_not_divisible_gives_the_first_importers_one_more() -> None:
    """Seven among three: 3, 2, 2, together exactly seven."""
    division = import_all.resolve_division(_import_table(), 7, 3, detected=16)
    assert division.per_importer == (3, 2, 2)
    assert import_all.divide(24, 6) == [4, 4, 4, 4, 4, 4]


def test_importers_above_the_total_are_capped_at_it() -> None:
    """Five importers asked for, three workers: three importers of one worker each."""
    division = import_all.resolve_division(_import_table(importers=5), 3, 'auto', detected=8)
    assert (division.importers, division.per_importer) == (3, (1, 1, 1))


def test_a_ceiling_that_floors_to_zero_is_one() -> None:
    """One core at three quarters floors to zero; the ceiling is 1, and so is everything."""
    division = import_all.resolve_division(_import_table(), 'max', 4, detected=1)
    assert (division.ceiling, division.workers, division.importers) == (1, 1, 1)


def test_a_total_above_the_ceiling_is_refused() -> None:
    """No request takes every core: eight cores at three quarters allow six."""
    with pytest.raises(ConfigError, match='--workers 7 is above the ceiling of 6'):
        import_all.resolve_division(_import_table(), 7, 2, detected=8)


def test_the_first_line_states_the_cores_the_fraction_the_ceiling_and_the_division() -> None:
    """Six importers of four workers on thirty cores at 0.8."""
    division = import_all.resolve_division(_import_table(cpu_fraction=0.8), 24, 6, detected=30)
    assert division.describe() == (
        'Parallelism: 30 cores detected, cpu_fraction 0.8, ceiling 24; workers 24 in all, '
        'importers 6, workers per importer 4, 4, 4, 4, 4, 4'
    )


# ---------------------------------------------------------------------------
# The steps
# ---------------------------------------------------------------------------


def test_the_default_prepares_then_coordinates_then_finishes(
    monkeypatch: pytest.MonkeyPatch, recorded_steps: list[list[str]]
) -> None:
    """Registration of every set in import order, the importers, then the closing steps,
    and nothing erased or confirmed."""
    monkeypatch.setattr('builtins.input', lambda _prompt: pytest.fail('asked to confirm'))

    _run(monkeypatch, '--override-db-schema', 'opus3_new', '--importers', '2', '--workers', '5')

    assert recorded_steps[0][0] == '--register-bundles'
    assert recorded_steps[0][-len(import_all.BUNDLE_SETS) :] == list(import_all.BUNDLE_SETS)
    assert recorded_steps[1] == ['coordinate', '3,2']
    assert recorded_steps[2:] == import_all.finish_steps('opus3_new')
    assert all('--scorched-earth' not in step for step in recorded_steps)


def test_sets_register_in_place_of_every_bundle_set(
    monkeypatch: pytest.MonkeyPatch, recorded_steps: list[list[str]]
) -> None:
    """``--sets`` with no step registers only what it names."""
    _run(monkeypatch, '--sets', 'COISS_2001,VGISS_6109')
    assert recorded_steps[0] == ['--register-bundles', 'COISS_2001,VGISS_6109']


def test_scorched_earth_erases_first_as_its_own_invocation(
    monkeypatch: pytest.MonkeyPatch, recorded_steps: list[list[str]]
) -> None:
    """The erase comes before any registration, after the confirmation."""
    monkeypatch.setattr('builtins.input', lambda _prompt: import_all.CONFIRMATION)

    _run(monkeypatch, '--override-db-schema', 'opus3_new', '--scorched-earth')

    assert recorded_steps[0] == ['--scorched-earth', '--yes', '--override-db-schema', 'opus3_new']
    assert recorded_steps[1][0] == '--register-bundles'
    assert recorded_steps[2] == ['coordinate', '1']


def test_a_total_above_the_ceiling_stops_the_run_before_anything_runs(
    monkeypatch: pytest.MonkeyPatch, recorded_steps: list[list[str]]
) -> None:
    """The division is resolved before the erase."""
    monkeypatch.setattr('builtins.input', lambda _prompt: import_all.CONFIRMATION)
    with pytest.raises(SystemExit) as raised:
        _run(monkeypatch, '--scorched-earth', '--workers', '7')
    assert raised.value.code == 2
    assert recorded_steps == []


def test_yes_alone_is_refused(
    monkeypatch: pytest.MonkeyPatch, recorded_steps: list[list[str]]
) -> None:
    """--yes answers the erase's confirmation, so without --scorched-earth it is refused."""
    with pytest.raises(SystemExit) as raised:
        _run(monkeypatch, '--yes')

    assert raised.value.code == 2
    assert recorded_steps == []


def test_the_confirmation_has_to_be_typed_exactly(
    monkeypatch: pytest.MonkeyPatch, recorded_steps: list[list[str]]
) -> None:
    """Anything but ``YES`` stops the run before it drops a table."""
    monkeypatch.setattr('builtins.input', lambda _prompt: 'yes')

    with pytest.raises(SystemExit) as raised:
        _run(monkeypatch, '--override-db-schema', 'opus3_new', '--scorched-earth')

    assert raised.value.code == 1
    assert recorded_steps == []


def test_yes_skips_the_confirmation(
    monkeypatch: pytest.MonkeyPatch, recorded_steps: list[list[str]]
) -> None:
    """What a caller that has already asked, or a run under nohup, passes."""
    monkeypatch.setattr('builtins.input', lambda _prompt: pytest.fail('asked to confirm'))

    _run(monkeypatch, '--scorched-earth', '--yes')

    assert recorded_steps[0] == list(import_all.DROP_OPTIONS)


def test_each_step_runs_alone_when_named(
    monkeypatch: pytest.MonkeyPatch, recorded_steps: list[list[str]]
) -> None:
    """--prepare registers, --join coordinates its importers alone, --finish finishes,
    --requeue requeues."""
    _run(monkeypatch, '--prepare')
    assert recorded_steps == import_all.prepare_steps(None, False, [])
    recorded_steps.clear()

    _run(monkeypatch, '--join', '--sets', 'COISS,COVIMS', '--workers', '4', '--importers', '2')
    assert recorded_steps == [['coordinate', '2,2']]
    recorded_steps.clear()

    _run(monkeypatch, '--join')
    assert recorded_steps == [['coordinate', '1']]
    recorded_steps.clear()

    _run(monkeypatch, '--finish')
    assert recorded_steps == import_all.finish_steps(None)
    recorded_steps.clear()

    _run(monkeypatch, '--requeue', 'COISS_2001', 'COISS_2002')
    assert recorded_steps == [['--requeue', 'COISS_2001', 'COISS_2002']]


@pytest.mark.parametrize(
    'arguments',
    [
        ['--finish', '--importers', '2'],
        ['--prepare', '--workers', '2'],
        ['--finish', '--sets', 'COISS'],
        ['--watch'],
        ['--join', '--recover'],
        ['--status', '--scorched-earth'],
    ],
    ids=['importers', 'workers', 'sets', 'watch', 'recover', 'erase'],
)
def test_options_that_mean_nothing_with_the_step_are_refused(
    arguments: list[str], monkeypatch: pytest.MonkeyPatch, recorded_steps: list[list[str]]
) -> None:
    """Each refusal exits 2 and runs nothing."""
    with pytest.raises(SystemExit) as raised:
        _run(monkeypatch, *arguments)
    assert raised.value.code == 2
    assert recorded_steps == []


def test_finish_refuses_an_unfinished_registry(
    monkeypatch: pytest.MonkeyPatch,
    recorded_steps: list[list[str]],
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Each unfinished bundle is named with its state, and the requeue command where it applies."""
    states = [('A_1', 'done'), ('A_2', 'pending'), ('A_3', 'failed'), ('A_4', 'importing')]
    monkeypatch.setattr(import_all, 'registry_states', lambda _schema: states)

    with pytest.raises(SystemExit) as raised:
        _run(monkeypatch, '--finish')

    assert raised.value.code == 1
    assert recorded_steps == []
    message = capsys.readouterr().err
    assert 'A_1' not in message
    assert 'A_2 (pending)\n' in message
    assert 'A_3 (failed): "opus_import_all --requeue A_3"' in message
    assert 'A_4 (importing): "opus_import_all --requeue A_4"' in message


def test_a_coordinator_that_does_not_finish_leaves_the_schema_unfinalized(
    monkeypatch: pytest.MonkeyPatch, recorded_steps: list[list[str]]
) -> None:
    """A failed bundle, an interrupt or a stranded bundle: no closing step runs."""
    monkeypatch.setattr(import_all, 'coordinate', lambda *args, **kwargs: 1)
    with pytest.raises(SystemExit) as raised:
        _run(monkeypatch)
    assert raised.value.code == 1
    assert [step[0] for step in recorded_steps] == ['--register-bundles']


def test_the_schema_override_reaches_every_step() -> None:
    """Including the importers and the finalization steps."""
    steps = [
        *import_all.prepare_steps('opus3_new', True, []),
        import_all.importer_step('opus3_new', 4, []),
        *import_all.finish_steps('opus3_new'),
    ]

    assert all(step[step.index('--override-db-schema') + 1] == 'opus3_new' for step in steps)


def test_without_a_schema_nothing_overrides_the_configuration() -> None:
    """The configured schema is the default, and is left to the pipeline to read."""
    steps = [
        *import_all.prepare_steps(None, True, []),
        import_all.importer_step(None, 1, []),
        *import_all.finish_steps(None),
    ]
    assert all('--override-db-schema' not in step for step in steps)


def test_extra_options_reach_the_holdings_steps_but_not_the_finalization() -> None:
    """The finishing steps import nothing, so an import option would be an error there."""
    extra = ['--log-debug-limit', '0']
    assert all('--log-debug-limit' in step for step in import_all.prepare_steps(None, True, extra))
    assert '--log-debug-limit' in import_all.importer_step(None, 2, extra)
    assert all('--log-debug-limit' not in step for step in import_all.finish_steps(None))


def test_an_importer_claims_only_its_sets_and_runs_its_share_of_workers() -> None:
    """One importer's command line."""
    assert import_all.importer_step(None, 4, [], 'COISS,COVIMS') == [
        '--join',
        '--workers',
        '4',
        'COISS,COVIMS',
    ]


def test_a_dry_run_shows_the_division_and_runs_nothing(
    monkeypatch: pytest.MonkeyPatch,
    recorded_steps: list[list[str]],
    capsys: pytest.CaptureFixture[str],
) -> None:
    """``--dry-run`` names the division, the erase, the registration, each importer and
    the finish, reading neither the database nor the holdings."""
    _eight_cores(monkeypatch, cpu_fraction=1.0)
    monkeypatch.setattr(
        import_all, 'registry_states', lambda _schema: pytest.fail('read the database')
    )

    _run(
        monkeypatch,
        '--override-db-schema',
        'opus3_new',
        '--scorched-earth',
        '--importers',
        '3',
        '--workers',
        '8',
        '--dry-run',
    )

    assert recorded_steps == []
    printed = capsys.readouterr().out
    assert printed.splitlines()[0] == (
        'Parallelism: 8 cores detected, cpu_fraction 1, ceiling 8; workers 8 in all, '
        'importers 3, workers per importer 3, 3, 2'
    )
    assert 'prepare: erases;' in printed
    assert ' '.join(import_all.BUNDLE_SETS) in printed
    assert 'import: 3 importers on this computer' in printed
    importers = [line for line in printed.splitlines() if line.startswith('opus_import --join')]
    assert importers == [
        'opus_import --join --override-db-schema opus3_new --workers 3',
        'opus_import --join --override-db-schema opus3_new --workers 3',
        'opus_import --join --override-db-schema opus3_new --workers 2',
    ]
    assert printed.count('opus_import ') == 2 + 3 + len(import_all.FINALIZATION_OPTIONS)


def test_a_dry_run_of_one_step_prints_that_step_alone(
    monkeypatch: pytest.MonkeyPatch,
    recorded_steps: list[list[str]],
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A step flag limits the plan printed to that step."""
    _run(monkeypatch, '--finish', '--dry-run')

    printed = capsys.readouterr().out
    assert 'prepare' not in printed
    assert 'Parallelism' not in printed
    assert printed.count('opus_import ') == len(import_all.FINALIZATION_OPTIONS)


def test_the_run_stops_at_the_first_step_that_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    """No importer starts over a failed registration, and the status is reported."""
    attempted: list[list[str]] = []

    def fail_on_the_second(arguments: list[str]) -> int:
        attempted.append(arguments)
        return 3 if len(attempted) == 2 else 0

    monkeypatch.setattr(import_all, 'run_step', fail_on_the_second)
    monkeypatch.setattr(import_all, 'coordinate', lambda *a, **k: pytest.fail('coordinated'))
    monkeypatch.setattr('builtins.input', lambda _prompt: import_all.CONFIRMATION)
    _eight_cores(monkeypatch)

    with pytest.raises(SystemExit) as raised:
        _run(monkeypatch, '--scorched-earth')

    assert raised.value.code == 3
    assert len(attempted) == 2


# ---------------------------------------------------------------------------
# The coordinator's reading of the registry
# ---------------------------------------------------------------------------


def _bundle(
    bundle_id: str,
    state: str,
    process_id: int | None = None,
    rows_done: int = 0,
    size: int = 100,
) -> BundleStatus:
    """Return a registry row."""
    started = _NOW - datetime.timedelta(minutes=2) if state != 'pending' else None
    return BundleStatus(1, bundle_id, state, size, rows_done, process_id, started, None)


def _process(process_id: int, *, alive: bool, idle_minutes: int = 0) -> ProcessStatus:
    """Return an importer's row."""
    return ProcessStatus(
        process_id,
        'host',
        1000 + process_id,
        f'/logs/importer_{process_id}.log',
        _NOW - datetime.timedelta(hours=1),
        _NOW - datetime.timedelta(minutes=idle_minutes),
        'running' if alive else 'exited',
        alive,
    )


class _Config:
    """A configuration with the default ``[import]`` table."""

    import_ = _import_table()


def _coordinator(finishing: bool = True) -> import_all.Coordinator:
    """Return a coordinator that has started nothing."""
    division = import_all.resolve_division(_import_table(), None, 'auto', detected=8)
    coordinator = import_all.Coordinator(
        _Config(),  # type: ignore[arg-type]
        None,
        division,
        [],
        finishing=finishing,
    )
    coordinator.terminal = False
    return coordinator


def test_every_bundle_done_and_no_importer_alive_lets_it_finish() -> None:
    """The one reading after which the closing sequence runs."""
    snapshot = Snapshot((_bundle('A', 'done'), _bundle('B', 'done')), (_process(1, alive=False),))
    assert _coordinator()._settle(snapshot) == 0


def test_an_importer_alive_on_another_computer_is_waited_for() -> None:
    """A joined computer's importer holds a bundle: not over yet."""
    snapshot = Snapshot((_bundle('A', 'importing', 2),), (_process(2, alive=True),))
    assert _coordinator()._settle(snapshot) is None


def test_a_lost_importers_bundle_is_waited_for_until_it_is_recovered() -> None:
    """Its importer's lock is free, so a recovery pass will return it: not over yet."""
    snapshot = Snapshot((_bundle('A', 'importing', 3),), (_process(3, alive=False),))
    assert _coordinator()._settle(snapshot) is None


def test_a_failed_bundle_stops_the_run_naming_its_importers_log(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Exit 1, the bundle named with the log of the importer that failed it."""
    snapshot = Snapshot(
        (_bundle('A', 'done'), _bundle('B', 'failed', 4)), (_process(4, alive=False),)
    )
    assert _coordinator()._settle(snapshot) == 1
    printed = capsys.readouterr().out
    assert "B (its importer's log: host:/logs/importer_4.log)" in printed
    assert 'A (' not in printed


def test_a_bundle_importing_outside_the_queue_stops_the_run(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A plain import's bundle has no importer to recover it from."""
    snapshot = Snapshot((_bundle('A', 'importing'),), ())
    assert _coordinator()._settle(snapshot) == 1
    assert 'importing outside the queue, with no importer: A' in capsys.readouterr().out


def test_the_table_shows_each_live_importer_and_marks_a_stall() -> None:
    """One line per importer alive, its bundle's progress, and STALLED past the limit."""
    snapshot = Snapshot(
        (
            _bundle('A', 'importing', 1, rows_done=40, size=100),
            _bundle('B', 'importing', 2, rows_done=5, size=1000),
            _bundle('C', 'done', 3),
        ),
        (
            _process(1, alive=True),
            _process(2, alive=True, idle_minutes=31),
            _process(3, alive=False),
        ),
    )
    lines = import_all.importer_lines(snapshot, _NOW, 30)
    assert lines[1:] == [
        'host:1001  A  40 of 100  0:02:00  0:00:00',
        'host:1002  B  5 of 1,000  0:02:00  0:31:00  STALLED',
    ]


def test_the_totals_line_labels_the_remaining_time_an_estimate() -> None:
    """Bundles by state, rows of the estimate, elapsed, and remaining."""
    snapshot = Snapshot(
        (
            _bundle('A', 'done', rows_done=100),
            _bundle('B', 'importing', 1, rows_done=50),
            _bundle('C', 'pending'),
            _bundle('D', 'failed', 2),
        ),
        (),
    )
    assert import_all.totals_line(snapshot, 3725, 60) == (
        'Bundles: 1 done, 1 importing, 1 pending, 1 failed; rows 150 of an estimated 400; '
        'elapsed 1:02:05; remaining about 0:01:00 (an estimate from the observed row rate)'
    )
    assert 'remaining not yet estimated' in import_all.totals_line(snapshot, 1, None)


class _Process:
    """A started importer that has exited with a given status."""

    _next_pid = 500

    def __init__(self, code: int | None) -> None:
        _Process._next_pid += 1
        self.pid = _Process._next_pid
        self.code = code

    def poll(self) -> int | None:
        return self.code


def test_a_lost_importer_is_replaced_while_bundles_are_pending(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Its exit, and a pending bundle, start one importer with the same workers."""
    coordinator = _coordinator()
    coordinator._starts_left = 5
    started: list[list[str]] = []

    def start(arguments: list[str]) -> _Process:
        started.append(arguments)
        return _Process(None)

    monkeypatch.setattr(import_all, 'start_importer', start)
    dead = import_all._Importer(_Process(-9), 2)  # type: ignore[arg-type]
    alive = import_all._Importer(_Process(None), 1)  # type: ignore[arg-type]
    coordinator._own = [dead, alive]
    snapshot = Snapshot((_bundle('A', 'pending'), _bundle('B', 'importing', 7)), ())
    _patch_reading(monkeypatch, snapshot)

    assert coordinator._pass(_FakeContext()) is None  # type: ignore[arg-type]
    assert started == [['--join', '--workers', '2']]


def test_an_interrupted_coordinator_starts_nothing_and_exits_unfinished(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """After an interrupt no importer is replaced, and once its own exit the run is over."""
    coordinator = _coordinator()
    coordinator._starts_left = 5
    coordinator.interrupts = 1
    monkeypatch.setattr(import_all, 'start_importer', lambda arguments: pytest.fail('started'))
    coordinator._own = [import_all._Importer(_Process(1), 1)]  # type: ignore[arg-type]
    _patch_reading(monkeypatch, Snapshot((_bundle('A', 'pending'),), ()))

    assert coordinator._pass(_FakeContext()) == 1  # type: ignore[arg-type]


class _FakeContext:
    """A context whose database is never asked anything the patches below do not answer."""

    db = object()


def _patch_reading(monkeypatch: pytest.MonkeyPatch, snapshot: Snapshot) -> None:
    """Make every reading of the registry return `snapshot`, and recover nothing."""
    from opus_import import import_processes
    from opus_import.steps import do_recover

    monkeypatch.setattr(import_processes, 'read_snapshot', lambda db: snapshot)
    monkeypatch.setattr(do_recover, 'recover_lost_importers', lambda ctx: [])
