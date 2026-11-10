"""Tests for the import pipeline's command-line surface.

Two properties, both of which a module-level parser or a module-level settings read
would break: the parser can be built without side effects, so its shape is assertable
without running an import, and the entry point reads no settings until it has arguments
to act on, so `--help` works on a machine that has none.
"""

import json
import os
import subprocess
import sys
import warnings
from pathlib import Path

import pdslogger
import pytest

import opus_config.config
import opus_import.__main__
from opus_config import OPUS_CONFIG_ENV_VAR
from opus_import import cli, importdb

from .conftest import RecordingLogger, make_context


def test_parser_defaults_to_doing_nothing() -> None:
    """With no arguments every action is off and no bundle is selected."""
    args = cli._create_argument_parser().parse_args([])
    assert args.do_it_all is False
    assert args.do_import is False
    assert args.validate is False
    assert args.bundles == []
    assert args.override_db_schema is None


def test_parser_reads_bundles_and_options() -> None:
    """Bundle descriptors are positional; the options around them keep their names."""
    args = cli._create_argument_parser().parse_args(
        [
            '--ignore-errors',
            '--import',
            '--override-db-schema',
            'opus_test_db',
            'COISS_2002,COISS_2008',
        ]
    )
    assert args.bundles == ['COISS_2002,COISS_2008']
    assert args.do_import is True
    assert args.ignore_errors is True
    assert args.override_db_schema == 'opus_test_db'


@pytest.mark.parametrize(
    ('option', 'attribute'),
    [
        ('--delete-bundles', 'delete_bundles'),
        ('--analyze-tables', 'analyze_tables'),
        ('--validate', 'validate'),
        ('--ignore-errors', 'ignore_errors'),
        ('--suppress-mult-messages', 'suppress_mult_messages'),
        ('--report-missing-ring-geo', 'report_missing_ring_geo'),
        ('--report-missing-sky-geo', 'report_missing_sky_geo'),
        ('--report-inventory-mismatch', 'report_inventory_mismatch'),
        ('--force-metadata-index', 'force_metadata_index'),
        ('--ignore-missing-images', 'ignore_missing_images'),
        ('--ignore-geo-mismatch', 'ignore_geo_mismatch'),
        ('--report-empty-products', 'report_empty_products'),
        ('--fake-images', 'fake_images'),
        ('--no-row-files', 'no_row_files'),
        ('--scorched-earth', 'scorched_earth'),
        ('--yes', 'yes'),
    ],
)
def test_each_option_sets_the_attribute_named_after_it(option: str, attribute: str) -> None:
    """An option's attribute is the option with ``_`` for ``-``, off unless given."""
    parser = cli._create_argument_parser()
    assert getattr(parser.parse_args([]), attribute) is False
    assert getattr(parser.parse_args([option]), attribute) is True


@pytest.mark.parametrize(
    'option',
    [
        '--drop-old-import-tables',
        '--delete-import-bundles',
        '--leave-old-import-tables',
        '--delete-permanent-import-bundles',
        '--copy-import-to-permanent-tables',
        '--drop-new-import-tables',
        '--do-all-import',
        '--do-import-finalization',
        '--import-check-duplicate-id',
        '--drop-permanent-tables',
        '--delete-permanent-bundles',
        '--analyze-permanent-tables',
        '--validate-perm',
        '--import-ignore-errors',
        '--import-dont-use-row-files',
    ],
)
def test_no_option_of_the_import_namespace_or_its_old_spellings_remains(
    option: str, capsys: pytest.CaptureFixture[str]
) -> None:
    """The removed and renamed options are refused, with no alias kept."""
    with pytest.raises(SystemExit) as excinfo:
        cli._create_argument_parser().parse_args([option])
    assert excinfo.value.code == 2
    assert option in capsys.readouterr().err


def test_no_help_text_names_the_permanent_tables_or_a_namespace() -> None:
    """One set of tables remains, so no option's help distinguishes two."""
    for action in cli._create_argument_parser()._actions:
        text = (action.help or '').lower()
        assert 'permanent' not in text, action.option_strings
        assert 'import table' not in text, action.option_strings
        assert 'namespace' not in text, action.option_strings


@pytest.mark.parametrize(
    ('arguments', 'message'),
    [
        (
            ['--scorched-earth'],
            '--scorched-earth drops every OPUS table in the schema; give --yes to confirm',
        ),
        (['--yes'], '--yes confirms --scorched-earth and is refused without it'),
    ],
    ids=['erase-without-yes', 'yes-without-erase'],
)
def test_an_unconfirmed_erase_or_a_stray_yes_is_refused_before_the_database_opens(
    arguments: list[str],
    message: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Both refusals exit non-zero, logged, and neither connects."""
    monkeypatch.setattr(warnings, 'showwarning', warnings.showwarning)
    logger = _HandlerlessLogger()
    monkeypatch.setattr(pdslogger, 'PdsLogger', lambda *args, **kwargs: logger)
    for factory in ('file_handler', 'warning_handler', 'error_handler'):
        monkeypatch.setattr(pdslogger, factory, lambda *args, **kwargs: None)
    opened: list[object] = []
    monkeypatch.setattr(importdb, 'get_db', lambda *args, **kwargs: opened.append(args))
    monkeypatch.setattr(sys, 'argv', ['opus_import', *arguments])
    with pytest.raises(SystemExit) as excinfo:
        cli.main()
    assert excinfo.value.code != 0
    assert opened == []
    assert logger.messages_at('fatal') == [message]


def _main_until_refused(
    arguments: list[str], monkeypatch: pytest.MonkeyPatch
) -> tuple[RecordingLogger, list[object]]:
    """Run `cli.main` with handlerless logging and eight detected cores until it exits.

    Returns:
        The logger, and the connections it would have opened.
    """
    monkeypatch.setattr(warnings, 'showwarning', warnings.showwarning)
    logger = _HandlerlessLogger()
    monkeypatch.setattr(pdslogger, 'PdsLogger', lambda *args, **kwargs: logger)
    for factory in ('file_handler', 'warning_handler', 'error_handler'):
        monkeypatch.setattr(pdslogger, factory, lambda *args, **kwargs: None)
    monkeypatch.setattr(opus_config.config, 'detected_cores', lambda: 8)
    opened: list[object] = []
    monkeypatch.setattr(importdb, 'get_db', lambda *args, **kwargs: opened.append(args))
    monkeypatch.setattr(sys, 'argv', ['opus_import', *arguments])
    with pytest.raises(SystemExit) as excinfo:
        cli.main()
    assert excinfo.value.code != 0
    return logger, opened


def test_the_first_line_logged_says_how_much_of_the_computer_the_run_may_use(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The cores and their source, the fraction, the ceiling, and both counts, first."""
    logger, _opened = _main_until_refused(['--workers', 'max', '--scorched-earth'], monkeypatch)
    assert logger.messages[0] == (
        'info',
        'Parallelism: 8 cores (detected), cpu_fraction 0.75, ceiling 6; workers 6, index_workers 1',
    )


def test_a_worker_count_above_the_ceiling_is_refused_before_the_database_opens(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The refusal names the ceiling and how it was reached, and nothing connects."""
    logger, opened = _main_until_refused(['--workers', '7', '--import', 'COISS_2002'], monkeypatch)
    assert opened == []
    assert logger.messages_at('fatal') == [
        '--workers 7 is above the ceiling of 6: 8 cores (detected) times cpu_fraction 0.75'
    ]


@pytest.mark.parametrize(('given', 'parsed'), [('1', 1), ('12', 12), ('max', 'max')])
def test_parser_reads_a_worker_count_or_max(given: str, parsed: int | str) -> None:
    """``--workers`` takes a whole number of at least 1, or ``max``; it is absent by default."""
    parser = cli._create_argument_parser()
    assert parser.parse_args([]).workers is None
    assert parser.parse_args(['--workers', given]).workers == parsed


@pytest.mark.parametrize('given', ['0', '-2', 'MAX', 'two'])
def test_parser_rejects_a_worker_count_that_is_neither(
    given: str, capsys: pytest.CaptureFixture[str]
) -> None:
    """Anything else is a usage error naming what it takes."""
    with pytest.raises(SystemExit) as excinfo:
        cli._create_argument_parser().parse_args(['--workers', given])
    assert excinfo.value.code == 2
    assert 'must be a whole number of at least 1 or "max"' in capsys.readouterr().err


class _HandlerlessLogger(RecordingLogger):
    """A recording logger that accepts the handlers `cli.main` adds, and keeps none."""

    def add_handler(self, handler: object) -> None:
        """Ignore a handler.

        Parameters:
            handler: The handler.
        """


def test_parser_names_the_import_option_do_import() -> None:
    """``--import`` cannot be an attribute name, so it keeps its explicit dest."""
    args = cli._create_argument_parser().parse_args(['--import'])
    assert args.do_import is True


def test_parser_rejects_an_unknown_option(capsys: pytest.CaptureFixture[str]) -> None:
    """An unknown option is refused rather than ignored, and named in the error."""
    with pytest.raises(SystemExit) as excinfo:
        cli._create_argument_parser().parse_args(['--no-such-option'])
    assert excinfo.value.code == 2
    assert '--no-such-option' in capsys.readouterr().err


def test_module_entry_point_binds_main() -> None:
    """``opus_import.__main__`` dispatches to exactly `cli.main` and to nothing else.

    That the module runs at all under ``python -m`` is covered end to end by the
    subprocess tests below; this pins *which* callable it runs, which is also the
    one the ``opus_import`` console script names in pyproject.toml.
    """
    assert opus_import.__main__.main is cli.main


def _run_without_settings(directory: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
    """Run ``python -m opus_import`` in a directory holding no settings of any kind."""
    workdir = directory / 'no_settings_here'
    workdir.mkdir()
    env = dict(os.environ)
    env.pop(OPUS_CONFIG_ENV_VAR, None)
    return subprocess.run(
        [sys.executable, '-m', 'opus_import', *arguments],
        capture_output=True,
        text=True,
        cwd=workdir,
        env=env,
        check=False,
    )


def test_help_works_without_a_configuration_file(tmp_path: Path) -> None:
    """``--help`` runs with no settings anywhere.

    `main()` loads the configuration after the arguments parse, so asking for usage
    needs nothing but the package. Runs in a subprocess because the check is about what
    the process requires at startup, which an in-process call cannot show.
    """
    result = _run_without_settings(tmp_path, '--help')
    assert result.returncode == 0, result.stderr
    assert result.stdout.startswith('usage: opus_import')
    assert '--do-it-all' in result.stdout


def test_running_without_settings_reports_the_missing_variable(tmp_path: Path) -> None:
    """Asking for real work without settings names the variable that has to be set."""
    result = _run_without_settings(tmp_path, '--validate')
    assert result.returncode != 0
    assert OPUS_CONFIG_ENV_VAR in result.stderr
    assert 'ConfigError' in result.stderr


def test_parser_reads_the_timing_file_as_a_path() -> None:
    """``--timing-json`` takes a path; without it no timing file is asked for."""
    parser = cli._create_argument_parser()
    assert parser.parse_args([]).timing_json is None
    assert parser.parse_args(['--timing-json', 'out/t.json']).timing_json == Path('out/t.json')


def test_a_timing_file_in_a_missing_directory_is_refused_at_once(tmp_path: Path) -> None:
    """The file is written at exit, so a directory it cannot be written in fails up front."""
    result = _run_without_settings(tmp_path, '--timing-json', 'missing/t.json', '--validate')
    assert result.returncode == 2
    assert '--timing-json: the directory missing does not exist' in result.stderr


def test_step_timings_are_written_with_their_total(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The file holds every timed step plus ``total``, measured from the run's start."""
    ctx = make_context()
    ctx.step_timings.update({'import': 1.5, 'import_bundle:COISS_2002': 1.25})
    monkeypatch.setattr('opus_import.cli.time.perf_counter', lambda: 107.0)
    path = tmp_path / 'timings.json'
    cli._write_step_timings(path, ctx, 100.0)
    assert json.loads(path.read_text()) == {
        'import': 1.5,
        'import_bundle:COISS_2002': 1.25,
        'total': 7.0,
    }
