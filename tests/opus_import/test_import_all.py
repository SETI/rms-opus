"""Tests for the full-holdings import's command line.

``opus_import_all`` is the one command in this distribution that runs for days, and no
unit test can run it. What is checkable without holdings or a database is what decides
the run: the steps each command line runs and their order, the guards in front of them
(the erase only when asked for, its confirmation, ``--finish``'s refusal of an
unfinished registry, stopping at the first step that fails), and how the workers are
divided among the importers. ``test_coordinator.py`` holds the coordinator's own
decisions.
"""

from __future__ import annotations

from typing import Any

import pytest

from opus_config import ConfigError
from opus_import import import_all

from .conftest import import_table


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
        import_ = import_table(**keys)

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
    division = import_all.resolve_division(import_table(), None, 'auto', detected=8)
    assert (division.workers, division.importers, division.per_importer) == (1, 1, (1,))


def test_a_total_not_divisible_gives_the_first_importers_one_more() -> None:
    """Seven among three: 3, 2, 2, together exactly seven."""
    division = import_all.resolve_division(import_table(), 7, 3, detected=16)
    assert division.per_importer == (3, 2, 2)
    assert import_all.divide(24, 6) == [4, 4, 4, 4, 4, 4]


def test_importers_above_the_total_are_capped_at_it() -> None:
    """Five importers asked for, three workers: three importers of one worker each."""
    division = import_all.resolve_division(import_table(importers=5), 3, 'auto', detected=8)
    assert (division.importers, division.per_importer) == (3, (1, 1, 1))


def test_a_ceiling_that_floors_to_zero_is_one() -> None:
    """One core at three quarters floors to zero; the ceiling is 1, and so is everything."""
    division = import_all.resolve_division(import_table(), 'max', 4, detected=1)
    assert (division.ceiling, division.workers, division.importers) == (1, 1, 1)


def test_a_total_above_the_ceiling_is_refused() -> None:
    """No request takes every core: eight cores at three quarters allow six."""
    with pytest.raises(ConfigError, match='--workers 7 is above the ceiling of 6'):
        import_all.resolve_division(import_table(), 7, 2, detected=8)


def test_the_first_line_states_the_cores_the_fraction_the_ceiling_and_the_division() -> None:
    """Six importers of four workers on thirty cores at 0.8."""
    division = import_all.resolve_division(import_table(cpu_fraction=0.8), 24, 6, detected=30)
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
