"""Tests for the full-holdings import sequence.

``opus_import_all`` is the one command in this distribution that runs for days and erases
a database before it starts, and no test can run it. What is checkable without holdings is
the part that matters anyway: the sequence it would run, and the two guards in front of
it -- the confirmation, and stopping at the first step that fails.

The sequence is asserted as a sequence rather than element by element, because the order
is the content: two bundle sets first because they need the duplicate-id check while the
tables are small, then the rest in roughly reverse order of how long each takes, then the
three steps that finish the database.
"""

from __future__ import annotations

import pytest

from opus_import import import_all


@pytest.fixture
def recorded_steps(monkeypatch: pytest.MonkeyPatch) -> list[list[str]]:
    """Record what `import_all.run_step` is asked to run, and run nothing.

    Returns:
        The list each recorded invocation is appended to, in the order the run reaches
        them. ``monkeypatch`` puts the real function back afterwards.
    """
    steps: list[list[str]] = []

    def record(arguments: list[str]) -> int:
        steps.append(arguments)
        return 0

    monkeypatch.setattr(import_all, 'run_step', record)
    return steps


def test_the_sequence_starts_by_dropping_and_ends_by_validating() -> None:
    """The shape of a full import: erase, the duplicate-id sets, the rest, then finish."""
    steps = import_all.import_steps('opus3_new', [])

    assert steps[0][:2] == list(import_all.DROP_OPTIONS)
    assert [step[-1] for step in steps[1:3]] == list(import_all.DUPLICATE_ID_BUNDLE_SETS)
    assert all('--import-check-duplicate-id' in step for step in steps[1:3])
    assert [step[-1] for step in steps[3 : 3 + len(import_all.BUNDLE_SETS)]] == list(
        import_all.BUNDLE_SETS
    )
    assert [step[0] for step in steps[-3:]] == list(import_all.FINALIZATION_OPTIONS)


def test_every_bundle_set_is_imported_once() -> None:
    """No set is imported twice, and none of the two lists overlaps the other."""
    imported = [step[-1] for step in import_all.import_steps(None, []) if '--do-all-import' in step]

    assert sorted(imported) == sorted(
        [*import_all.DUPLICATE_ID_BUNDLE_SETS, *import_all.BUNDLE_SETS]
    )
    assert len(imported) == len(set(imported))


def test_the_schema_override_reaches_every_step() -> None:
    """Including the finalization steps: they would otherwise finish the wrong database."""
    steps = import_all.import_steps('opus3_new', [])

    assert all('--override-db-schema' in step for step in steps)
    assert all(step[step.index('--override-db-schema') + 1] == 'opus3_new' for step in steps)


def test_without_a_schema_nothing_overrides_the_configuration() -> None:
    """The configured schema is the default, and is left to the pipeline to read."""
    assert all('--override-db-schema' not in step for step in import_all.import_steps(None, []))


def test_extra_options_reach_the_imports_but_not_the_finalization() -> None:
    """The finishing steps import nothing, so an import option would be an error there."""
    steps = import_all.import_steps(None, ['--log-debug-limit', '0'])
    finishing = len(import_all.FINALIZATION_OPTIONS)

    assert all('--log-debug-limit' in step for step in steps[:-finishing])
    assert all('--log-debug-limit' not in step for step in steps[-finishing:])


def test_a_dry_run_runs_nothing(
    monkeypatch: pytest.MonkeyPatch,
    recorded_steps: list[list[str]],
    capsys: pytest.CaptureFixture[str],
) -> None:
    """``--dry-run`` is how the sequence is read on a machine that has no checkout."""
    monkeypatch.setattr(
        'sys.argv', ['opus_import_all', '--override-db-schema', 'opus3_new', '--dry-run']
    )

    import_all.main()

    assert recorded_steps == []
    printed = capsys.readouterr().out
    assert printed.count('opus_import ') == len(import_all.import_steps('opus3_new', []))
    assert '--validate-perm' in printed


def test_the_confirmation_has_to_be_typed_exactly(
    monkeypatch: pytest.MonkeyPatch, recorded_steps: list[list[str]]
) -> None:
    """Anything but ``YES`` stops the run before it drops a table."""
    monkeypatch.setattr('sys.argv', ['opus_import_all', '--override-db-schema', 'opus3_new'])
    monkeypatch.setattr('builtins.input', lambda _prompt: 'yes')

    with pytest.raises(SystemExit) as raised:
        import_all.main()

    assert raised.value.code == 1
    assert recorded_steps == []


def test_yes_skips_the_confirmation_and_runs_every_step(
    monkeypatch: pytest.MonkeyPatch, recorded_steps: list[list[str]]
) -> None:
    """What a caller that has already asked, or a run under nohup, passes."""
    monkeypatch.setattr(
        'sys.argv', ['opus_import_all', '--override-db-schema', 'opus3_new', '--yes']
    )

    import_all.main()

    assert recorded_steps == import_all.import_steps('opus3_new', [])


def test_the_run_stops_at_the_first_step_that_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    """A later group must not be imported over a failed one, and the status is reported."""
    attempted: list[list[str]] = []

    def fail_on_the_second(arguments: list[str]) -> int:
        attempted.append(arguments)
        return 3 if len(attempted) == 2 else 0

    monkeypatch.setattr(import_all, 'run_step', fail_on_the_second)
    monkeypatch.setattr('sys.argv', ['opus_import_all', '--yes'])

    with pytest.raises(SystemExit) as raised:
        import_all.main()

    assert raised.value.code == 3
    assert len(attempted) == 2
