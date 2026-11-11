"""Tests for the full-holdings import sequence.

``opus_import_all`` is the one command in this distribution that runs for days, and no
test can run it. What is checkable without holdings is the part that matters anyway: the
sequence each step would run, and the guards in front of it -- the erase only when asked
for, its confirmation, ``--finish``'s refusal of an unfinished registry, and stopping at
the first step that fails.

The sequence is asserted as a sequence rather than element by element, because the order
is the content: the registration of the bundle sets in import order, the importer, then
the steps that finish the database, the schema version last.
"""

from __future__ import annotations

import pytest

from opus_import import import_all


@pytest.fixture
def recorded_steps(monkeypatch: pytest.MonkeyPatch) -> list[list[str]]:
    """Record what `import_all.run_step` is asked to run, and run nothing.

    The registry ``--finish`` reads is empty, so it never refuses.

    Returns:
        The list each recorded invocation is appended to, in the order the run reaches
        them. ``monkeypatch`` puts the real functions back afterwards.
    """
    steps: list[list[str]] = []

    def record(arguments: list[str]) -> int:
        steps.append(arguments)
        return 0

    monkeypatch.setattr(import_all, 'run_step', record)
    monkeypatch.setattr(import_all, 'registry_states', lambda _schema: [])
    return steps


def _run(monkeypatch: pytest.MonkeyPatch, *arguments: str) -> None:
    """Run ``opus_import_all`` with the given arguments."""
    monkeypatch.setattr('sys.argv', ['opus_import_all', *arguments])
    import_all.main()


def test_the_default_sequence_registers_imports_and_finishes() -> None:
    """Registration of every set in import order, one importer, then the closing steps."""
    steps = import_all.import_steps('opus3_new', [])

    assert steps[0][0] == '--register-bundles'
    assert steps[0][-len(import_all.BUNDLE_SETS) :] == list(import_all.BUNDLE_SETS)
    assert steps[1][0] == '--join'
    assert [step[0] for step in steps[2:]] == [
        '--finalize',
        '--import-dictionary',
        '--validate',
        '--write-schema-version',
    ]


def test_the_default_erases_nothing(
    monkeypatch: pytest.MonkeyPatch, recorded_steps: list[list[str]]
) -> None:
    """Without --scorched-earth no invocation erases, and nothing asks for confirmation."""
    monkeypatch.setattr('builtins.input', lambda _prompt: pytest.fail('asked to confirm'))

    _run(monkeypatch, '--override-db-schema', 'opus3_new')

    assert recorded_steps == import_all.import_steps('opus3_new', [])
    assert all('--scorched-earth' not in step for step in recorded_steps)


def test_scorched_earth_erases_first_as_its_own_invocation(
    monkeypatch: pytest.MonkeyPatch, recorded_steps: list[list[str]]
) -> None:
    """The erase comes before any registration, after the confirmation."""
    monkeypatch.setattr('builtins.input', lambda _prompt: import_all.CONFIRMATION)

    _run(monkeypatch, '--override-db-schema', 'opus3_new', '--scorched-earth')

    assert recorded_steps[0] == ['--scorched-earth', '--yes', '--override-db-schema', 'opus3_new']
    assert recorded_steps[1][0] == '--register-bundles'
    assert recorded_steps[1:] == import_all.import_steps('opus3_new', [])


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
    """--prepare registers, --join imports, --finish finishes, --requeue requeues."""
    _run(monkeypatch, '--prepare')
    assert recorded_steps == import_all.prepare_steps(None, False, [])
    recorded_steps.clear()

    _run(monkeypatch, '--join', '--sets', 'COISS,COVIMS', '--workers', '4')
    assert recorded_steps == [['--join', '--workers', '4', 'COISS,COVIMS']]
    recorded_steps.clear()

    _run(monkeypatch, '--finish')
    assert recorded_steps == import_all.finish_steps(None)
    recorded_steps.clear()

    _run(monkeypatch, '--requeue', 'COISS_2001', 'COISS_2002')
    assert recorded_steps == [['--requeue', 'COISS_2001', 'COISS_2002']]


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


def test_the_schema_override_reaches_every_step() -> None:
    """Including the finalization steps: they would otherwise finish the wrong database."""
    steps = import_all.import_steps('opus3_new', [], erase=True)

    assert all('--override-db-schema' in step for step in steps)
    assert all(step[step.index('--override-db-schema') + 1] == 'opus3_new' for step in steps)


def test_without_a_schema_nothing_overrides_the_configuration() -> None:
    """The configured schema is the default, and is left to the pipeline to read."""
    assert all('--override-db-schema' not in step for step in import_all.import_steps(None, []))


def test_extra_options_reach_the_holdings_steps_but_not_the_finalization() -> None:
    """The finishing steps import nothing, so an import option would be an error there."""
    steps = import_all.import_steps(None, ['--log-debug-limit', '0'], erase=True)
    finishing = len(import_all.FINALIZATION_OPTIONS)

    assert all('--log-debug-limit' in step for step in steps[:-finishing])
    assert all('--log-debug-limit' not in step for step in steps[-finishing:])


def test_a_dry_run_runs_nothing_and_reads_nothing(
    monkeypatch: pytest.MonkeyPatch,
    recorded_steps: list[list[str]],
    capsys: pytest.CaptureFixture[str],
) -> None:
    """``--dry-run`` names the erase, the registration, the importer and the finish."""
    monkeypatch.setattr(
        import_all, 'registry_states', lambda _schema: pytest.fail('read the database')
    )

    _run(monkeypatch, '--override-db-schema', 'opus3_new', '--scorched-earth', '--dry-run')

    assert recorded_steps == []
    printed = capsys.readouterr().out
    expected = import_all.import_steps('opus3_new', [], erase=True)
    assert printed.count('opus_import ') == len(expected)
    assert 'prepare: erases;' in printed
    assert ' '.join(import_all.BUNDLE_SETS) in printed
    assert 'join: 1 importer' in printed
    assert '--write-schema-version' in printed


def test_a_dry_run_of_one_step_prints_that_step_alone(
    monkeypatch: pytest.MonkeyPatch,
    recorded_steps: list[list[str]],
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A step flag limits the plan printed to that step."""
    _run(monkeypatch, '--finish', '--dry-run')

    printed = capsys.readouterr().out
    assert 'prepare' not in printed
    assert 'join' not in printed
    assert printed.count('opus_import ') == len(import_all.FINALIZATION_OPTIONS)


def test_the_run_stops_at_the_first_step_that_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    """An importer must not run over a failed registration, and the status is reported."""
    attempted: list[list[str]] = []

    def fail_on_the_second(arguments: list[str]) -> int:
        attempted.append(arguments)
        return 3 if len(attempted) == 2 else 0

    monkeypatch.setattr(import_all, 'run_step', fail_on_the_second)
    monkeypatch.setattr('builtins.input', lambda _prompt: import_all.CONFIRMATION)

    with pytest.raises(SystemExit) as raised:
        _run(monkeypatch, '--scorched-earth')

    assert raised.value.code == 3
    assert len(attempted) == 2
