"""What `perform_run` runs, with which interpreter, and what it tells an observer.

The benchmark harness measures a side whose code is another checkout, so every
invocation `perform_run` makes has to use the interpreter and checkout it is given, and
each step's command line has to be the one the caller passes rather than this
checkout's constant. The defaults have to stay this suite's own sequence. Nothing here
runs a subprocess or reaches a database: the runners are replaced by recorders.
"""

from collections.abc import Sequence
from pathlib import Path

import pytest

from import_tests.tools import build_run, golden_io
from import_tests.tools.build_run import StepResult
from import_tests.tools.fixture_layout import REPO_ROOT
from import_tests.tools.golden_io import DatabaseCredentials
from opus_config import load_config


class _Recorder:
    """Stands in for the step runners and the observer, recording every call."""

    def __init__(self) -> None:
        """Start with nothing recorded."""
        self.runs: list[tuple[str, tuple[str, ...], Path, Path]] = []
        self.events: list[tuple[str, tuple[str, ...]]] = []

    def pipeline_step(
        self, config_file: Path, arguments: Sequence[str], *, python: Path, repo_root: Path
    ) -> StepResult:
        """Record an ``opus_import`` invocation."""
        self.runs.append(('opus_import', tuple(arguments), python, repo_root))
        return StepResult(tuple(arguments), 0, '', '')

    def migrate(self, config_file: Path, *, python: Path, repo_root: Path) -> StepResult:
        """Record the migration."""
        self.runs.append(('migrate', build_run.MIGRATE_ARGS, python, repo_root))
        return StepResult(build_run.MIGRATE_ARGS, 0, '', '')

    def step_started(self, arguments: Sequence[str]) -> None:
        """Record the observer hearing an invocation start."""
        self.events.append(('started', tuple(arguments)))

    def step_finished(self, result: StepResult) -> None:
        """Record the observer hearing an invocation finish."""
        self.events.append(('finished', result.arguments))


@pytest.fixture
def recorder(monkeypatch: pytest.MonkeyPatch) -> _Recorder:
    """Replace everything `perform_run` reaches outside this process."""
    recorder = _Recorder()
    monkeypatch.setattr(build_run, 'build_holdings_tree', lambda paths, overlay=None: None)
    monkeypatch.setattr(
        build_run, 'write_opus_config', lambda paths, schema, credentials, extra_import=None: None
    )
    monkeypatch.setattr(build_run, 'run_pipeline_step', recorder.pipeline_step)
    monkeypatch.setattr(build_run, 'run_migrate', recorder.migrate)
    monkeypatch.setattr(golden_io, 'list_tables', lambda credentials, schema: [])
    return recorder


def _perform(tmp_path: Path, **kwargs: object) -> None:
    """Run the sequence over two one-bundle groups with the given overrides."""
    build_run.perform_run(
        tmp_path,
        'schema',
        DatabaseCredentials('h', 'u', 'p'),
        bundle_groups=[['A_0001'], ['B_0001']],
        **kwargs,  # type: ignore[arg-type]  # each test passes its own keywords
    )


def test_the_defaults_are_this_suites_own_sequence(tmp_path: Path, recorder: _Recorder) -> None:
    """With no overrides, this interpreter and checkout run the module's constants."""
    _perform(tmp_path)
    assert recorder.runs == [
        (
            'opus_import',
            build_run.DROP_ARGS,
            build_run.THIS_PYTHON,
            REPO_ROOT,
        ),
        (
            'opus_import',
            (*build_run.IMPORT_ARGS, 'A_0001'),
            build_run.THIS_PYTHON,
            REPO_ROOT,
        ),
        (
            'opus_import',
            (*build_run.IMPORT_ARGS, 'B_0001'),
            build_run.THIS_PYTHON,
            REPO_ROOT,
        ),
        (
            'opus_import',
            build_run.AUX_ARGS,
            build_run.THIS_PYTHON,
            REPO_ROOT,
        ),
        (
            'opus_import',
            build_run.DICTIONARY_ARGS,
            build_run.THIS_PYTHON,
            REPO_ROOT,
        ),
        (
            'migrate',
            build_run.MIGRATE_ARGS,
            build_run.THIS_PYTHON,
            REPO_ROOT,
        ),
        (
            'opus_import',
            build_run.VALIDATE_ARGS,
            build_run.THIS_PYTHON,
            REPO_ROOT,
        ),
        (
            'opus_import',
            build_run.VERSION_ARGS,
            build_run.THIS_PYTHON,
            REPO_ROOT,
        ),
    ]


def test_every_invocation_uses_the_given_interpreter_steps_and_checkout(
    tmp_path: Path, recorder: _Recorder
) -> None:
    """Each override reaches its step, and the interpreter and checkout reach all of them."""
    python, repo_root = Path('/side/bin/python'), Path('/side')
    _perform(
        tmp_path,
        python=python,
        repo_root=repo_root,
        drop_args=('--erase',),
        import_args=('--load', '--timing-json', 't.json'),
        aux_args=('--finish',),
        dictionary_args=('--dictionary', '--timing-json', 't.json'),
        validate_args=('--check',),
        version_args=('--stamp',),
    )
    assert recorder.runs == [
        ('opus_import', ('--erase',), python, repo_root),
        ('opus_import', ('--load', '--timing-json', 't.json', 'A_0001'), python, repo_root),
        ('opus_import', ('--load', '--timing-json', 't.json', 'B_0001'), python, repo_root),
        ('opus_import', ('--finish',), python, repo_root),
        ('opus_import', ('--dictionary', '--timing-json', 't.json'), python, repo_root),
        ('migrate', build_run.MIGRATE_ARGS, python, repo_root),
        ('opus_import', ('--check',), python, repo_root),
        ('opus_import', ('--stamp',), python, repo_root),
    ]


def test_an_empty_version_step_is_skipped(tmp_path: Path, recorder: _Recorder) -> None:
    """A side whose import has no version step ends the sequence with its validation."""
    _perform(tmp_path, version_args=())
    assert recorder.runs[-1][1] == build_run.VALIDATE_ARGS


def test_the_observer_hears_each_invocation_start_and_finish_in_order(
    tmp_path: Path, recorder: _Recorder
) -> None:
    """Every invocation, the migration included, is bracketed by the two calls."""
    _perform(tmp_path, observer=recorder)
    expected = []
    for name, arguments, _, _ in recorder.runs:
        expected += [('started', arguments), ('finished', arguments)]
        assert name in {'opus_import', 'migrate'}
    assert recorder.events == expected


def test_a_run_stopped_after_the_imports_tells_the_observer_of_nothing_more(
    tmp_path: Path, recorder: _Recorder
) -> None:
    """``finalize=False`` ends after the bundle imports, for the observer too."""
    _perform(tmp_path, observer=recorder, finalize=False)
    assert [event for event in recorder.events if event[0] == 'started'] == [
        ('started', build_run.DROP_ARGS),
        ('started', (*build_run.IMPORT_ARGS, 'A_0001')),
        ('started', (*build_run.IMPORT_ARGS, 'B_0001')),
    ]


def test_a_relative_configuration_reaches_a_subprocess_as_absolute(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The subprocess runs in another checkout, so a relative path would name another file."""
    monkeypatch.chdir(tmp_path)
    environment = build_run.run_environment(Path('opus.toml'))
    assert environment[build_run.CONFIG_ENV_VAR] == str(tmp_path.resolve() / 'opus.toml')


def test_extra_import_keys_reach_the_configuration(tmp_path: Path) -> None:
    """A session's `extra_import` keys are in the file the pipeline loads, with their types."""
    paths = build_run.RunPaths.under(tmp_path)
    build_run.write_opus_config(
        paths,
        'schema',
        DatabaseCredentials('h', 'u', 'p'),
        extra_import={'transaction_rows': 5, 'bulk_load': False, 'scratch_dir': '/scratch/a"b'},
    )

    config = load_config(paths.config_file).import_
    assert (config.transaction_rows, config.bulk_load, config.scratch_dir) == (
        5,
        False,
        '/scratch/a"b',
    )


def test_a_newline_in_a_value_survives_the_configuration(tmp_path: Path) -> None:
    """A control character is escaped rather than breaking the file."""
    paths = build_run.RunPaths.under(tmp_path)
    build_run.write_opus_config(
        paths,
        'schema',
        DatabaseCredentials('h', 'u', 'p'),
        extra_import={'scratch_dir': '/scratch/a\nb\tc\\d\x7f'},
    )
    assert load_config(paths.config_file).import_.scratch_dir == '/scratch/a\nb\tc\\d\x7f'


def test_perform_run_hands_extra_import_to_the_configuration(
    tmp_path: Path, recorder: _Recorder, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A session's keys reach the file its pipeline reads, not just the writer's tests."""
    written: list[object] = []
    monkeypatch.setattr(
        build_run,
        'write_opus_config',
        lambda paths, schema, credentials, extra_import=None: written.append(extra_import),
    )
    _perform(tmp_path, extra_import={'transaction_rows': 7})
    assert written == [{'transaction_rows': 7}]
