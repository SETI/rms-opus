"""Tests for the import pipeline's command-line surface.

Two properties, both of which a module-level parser or a module-level settings read
would break: the parser can be built without side effects, so its shape is assertable
without running an import, and the entry point reads no settings until it has arguments
to act on, so `--help` works on a machine that has none.
"""

import atexit
import json
import os
import signal
import socket
import subprocess
import sys
import types
import warnings
from collections.abc import Callable
from pathlib import Path

import pdslogger
import pytest

import opus_config.config
import opus_import.__main__
from opus_config import OPUS_CONFIG_ENV_VAR
from opus_import import cli, importdb, schema_version
from opus_import.context import ImportContext
from opus_import.generations import PENDING_READY, GenerationState
from opus_import.schema_version import SCHEMA_VERSION
from opus_import.steps import (
    do_cart,
    do_django,
    do_duplicate_ids,
    do_finalize_mult,
    do_generation,
    do_import,
    do_import_tables,
    do_indexes,
    do_param_info,
    do_partables,
    do_schema_version,
    do_table_names,
)

from .conftest import RecordingLogger, make_context

#: What the stubbed log handler factories return: a handler naming a log file, which the
#: run records as its log's path.
_FILE_HANDLER = types.SimpleNamespace(baseFilename='opus_import.log')


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
        (
            ['--join', '--read-only'],
            '--join imports from the queue alone; it is refused with --read-only',
        ),
    ],
    ids=['erase-without-yes', 'yes-without-erase', 'join-read-only'],
)
def test_a_refused_combination_of_options_exits_before_the_database_opens(
    arguments: list[str],
    message: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Each refusal exits non-zero, logged, and none connects."""
    monkeypatch.setattr(warnings, 'showwarning', warnings.showwarning)
    logger = _HandlerlessLogger()
    monkeypatch.setattr(pdslogger, 'PdsLogger', lambda *args, **kwargs: logger)
    for factory in ('file_handler', 'warning_handler', 'error_handler'):
        monkeypatch.setattr(pdslogger, factory, lambda *args, **kwargs: _FILE_HANDLER)
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
        monkeypatch.setattr(pdslogger, factory, lambda *args, **kwargs: _FILE_HANDLER)
    monkeypatch.setattr(opus_config.config, 'detected_cores', lambda: 8)
    opened: list[object] = []
    monkeypatch.setattr(importdb, 'get_db', lambda *args, **kwargs: opened.append(args))
    monkeypatch.setattr(sys, 'argv', ['opus_import', *arguments])
    with pytest.raises(SystemExit) as excinfo:
        cli.main()
    assert excinfo.value.code != 0
    return logger, opened


class _LockedSchema:
    """A database whose generation lock another connection holds, and which has no
    version row."""

    db_schema = 'opus_ci_db'
    log_sql = False

    def forget_table_names(self) -> None:
        """Read nothing."""

    def table_exists(self, table: str) -> bool:
        """Hold no table."""
        return False

    def try_named_lock(self, name: str) -> bool:
        """Refuse every lock."""
        return False


def test_a_refused_generation_command_exits_with_its_own_status(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The deploy chain tells a refusal, which changed nothing, from a failure by it."""
    monkeypatch.setattr(warnings, 'showwarning', warnings.showwarning)
    logger = _HandlerlessLogger()
    monkeypatch.setattr(pdslogger, 'PdsLogger', lambda *args, **kwargs: logger)
    for factory in ('file_handler', 'warning_handler', 'error_handler'):
        monkeypatch.setattr(pdslogger, factory, lambda *args, **kwargs: _FILE_HANDLER)
    monkeypatch.setattr(importdb, 'get_db', lambda *args, **kwargs: _LockedSchema())
    monkeypatch.setattr(sys, 'argv', ['opus_import', '--switch-generation'])
    with pytest.raises(SystemExit) as excinfo:
        cli.main()
    assert excinfo.value.code == do_generation.GENERATION_REFUSED_EXIT_STATUS
    (message,) = logger.messages_at('fatal')
    assert message.startswith('--switch-generation refused: another generation command holds')


class _CheckedSchema:
    """A connection `cli.main` opens for ``--check``, recording its close."""

    def __init__(self) -> None:
        self.closed = False

    def close(self) -> None:
        """Record the close."""
        self.closed = True


def _run_check(
    arguments: list[str],
    monkeypatch: pytest.MonkeyPatch,
    *,
    problem: str | None = None,
    unreadable: bool = False,
) -> tuple[int | str | None, RecordingLogger, list[dict[str, object]], _CheckedSchema]:
    """Run `cli.main` with ``--check`` arguments against a stand-in schema.

    Parameters:
        arguments: The command line after ``opus_import``.
        monkeypatch: The fixture.
        problem: What the check finds, or None for nothing.
        unreadable: Make the schema unreadable instead.

    Returns:
        The exit status, the logger, the keywords each connection was opened with, and
        the connection.
    """
    monkeypatch.setattr(warnings, 'showwarning', warnings.showwarning)
    logger = _HandlerlessLogger()
    monkeypatch.setattr(pdslogger, 'PdsLogger', lambda *args, **kwargs: logger)
    for factory in ('file_handler', 'warning_handler', 'error_handler'):
        monkeypatch.setattr(pdslogger, factory, lambda *args, **kwargs: _FILE_HANDLER)
    schema = _CheckedSchema()
    opened: list[dict[str, object]] = []

    def get_db(*args: object, **kwargs: object) -> _CheckedSchema:
        opened.append(kwargs)
        return schema

    def check_problem(db: object, action: str) -> str | None:
        assert db is schema
        if unreadable:
            raise importdb.ImportDBError('lost connection')
        return problem

    monkeypatch.setattr(importdb, 'get_db', get_db)
    monkeypatch.setattr(cli, '_check_problem', check_problem)
    monkeypatch.setattr(sys, 'argv', ['opus_import', *arguments])
    with pytest.raises(SystemExit) as excinfo:
        cli.main()
    return excinfo.value.code, logger, opened, schema


@pytest.mark.parametrize('action', cli.CHECK_ACTIONS)
def test_a_check_that_would_run_exits_zero_having_read_only(
    action: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The connection is read-only and closed, and the answer is logged at info."""
    code, logger, opened, schema = _run_check(['--check', action], monkeypatch)
    assert code == 0
    assert [keywords['read_only'] for keywords in opened] == [True]
    assert schema.closed
    assert logger.messages_at('info')[-1] == f'--check {action}: would run'


def test_a_check_that_would_be_refused_exits_with_the_refused_status(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The reason is logged at info, not as an error: the refusal is the caller's to act
    on, and a deploy reading ERRORS.log afterwards finds nothing of it."""
    code, logger, _opened, _schema = _run_check(
        ['--check', 'switch'], monkeypatch, problem='no pending generation is ready'
    )
    assert code == do_generation.GENERATION_REFUSED_EXIT_STATUS
    assert logger.messages_at('info')[-1] == (
        '--check switch: refused: no pending generation is ready'
    )
    assert logger.messages_at('error') == []
    assert logger.messages_at('fatal') == []


def test_a_check_of_an_unreadable_schema_fails_otherwise(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Neither 0 nor the refused status, so the deploy chain tells it from both."""
    code, logger, _opened, schema = _run_check(['--check', 'serve'], monkeypatch, unreadable=True)
    assert code == -1
    assert schema.closed
    assert logger.messages_at('error') == [
        '--check serve: "opus_ci_db" cannot be read: lost connection'
    ]


def test_the_check_runs_alone(monkeypatch: pytest.MonkeyPatch) -> None:
    """It answers a question and does nothing else, so it shares the invocation with
    nothing, and the refusal comes before any connection."""
    code, logger, opened, _schema = _run_check(
        ['--check', 'continue', '--import', 'COISS_2002'], monkeypatch
    )
    assert code == -1
    assert opened == []
    assert logger.messages_at('fatal') == [
        '--check runs alone; it is refused with --import, bundle descriptors'
    ]


def test_the_check_asks_the_web_applications_rule_or_the_generation_rule(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """``serve`` is the schema version check; the rest are generation actions."""
    asked: list[tuple[str, object]] = []
    monkeypatch.setattr(
        schema_version,
        'served_schema_version_problem',
        lambda db: asked.append(('serve', db)),
    )
    monkeypatch.setattr(
        do_generation, 'generation_problem', lambda db, action: asked.append((action, db))
    )
    for action in cli.CHECK_ACTIONS:
        cli._check_problem('db', action)  # type: ignore[arg-type]
    assert asked == [(action, 'db') for action in cli.CHECK_ACTIONS]


def test_the_first_line_logged_says_how_much_of_the_computer_the_run_may_use(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The cores detected, the fraction, the ceiling, and both counts, first."""
    logger, _opened = _main_until_refused(['--workers', 'max', '--scorched-earth'], monkeypatch)
    assert logger.messages[0] == (
        'info',
        'Parallelism: 8 cores detected, cpu_fraction 0.75, ceiling 6; workers 6, index_workers 1',
    )


def test_a_worker_count_above_the_ceiling_is_lowered_and_logged(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The run goes on at the ceiling, and its first line names what was asked for."""
    logger, _opened = _main_until_refused(['--workers', '7', '--scorched-earth'], monkeypatch)
    assert logger.messages[0] == (
        'info',
        'Parallelism: 8 cores detected, cpu_fraction 0.75, ceiling 6; workers 6, '
        'index_workers 1; capped at the ceiling: --workers 7',
    )


@pytest.mark.parametrize(
    'arguments',
    [
        ['--carry-over-sessions-from', 'opus_ci_db'],
        ['--override-db-schema', 'opus_new', '--carry-over-sessions-from', 'opus_new'],
        ['--carry-over-sessions-from', 'OPUS_CI_DB'],
    ],
    ids=['configured-schema', 'overridden-schema', 'other-case'],
)
def test_the_carry_over_refuses_the_schema_it_would_write_into(
    arguments: list[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Its target is emptied first, so the source being the target would empty both; the
    refusal names the schema and comes before the database opens, so no statement runs.
    A server with ``lower_case_table_names`` set treats names differing in case as one."""
    logger, opened = _main_until_refused(arguments, monkeypatch)
    assert opened == []
    assert logger.messages_at('fatal') == [
        f'--carry-over-sessions-from {arguments[-1]} names the schema it would write into; '
        'name the schema being served'
    ]


def test_the_carry_over_runs_alone(monkeypatch: pytest.MonkeyPatch) -> None:
    """It runs while the web service is stopped, so no other step shares the invocation."""
    logger, opened = _main_until_refused(
        ['--carry-over-sessions-from', 'opus_old', '--finalize', 'COISS_2002'], monkeypatch
    )
    assert opened == []
    assert logger.messages_at('fatal') == [
        '--carry-over-sessions-from runs alone; it is refused with --finalize, '
        '--create-indexes, --create-param-info, --create-partables, --create-table-names, '
        '--reset-search-tables, --create-cart, --analyze-tables, bundle descriptors'
    ]


#: The options that change how a step runs rather than adding one, which the carry-over
#: accepts.
_STEP_MODIFIERS = frozenset(
    {
        'yes',
        'suppress_mult_messages',
        'report_missing_ring_geo',
        'report_missing_sky_geo',
        'report_inventory_mismatch',
        'force_metadata_index',
        'ignore_missing_images',
        'ignore_geo_mismatch',
        'no_row_files',
        'report_empty_products',
        'fake_images',
        'dont_use_shelves_only',
        'no_log_pdsfile',
        'log_sql',
        'log_suppress_traceback',
        'profile',
        'require_pending_generation',
    }
)


def test_every_step_option_is_refused_with_the_carry_over() -> None:
    """A step added to the parser is refused with it too, or named a modifier above."""
    refused = {name for name, _option in cli.CARRY_OVER_CONFLICTS}
    flags = {
        action.dest
        for action in cli._create_argument_parser()._actions
        if action.const is True and action.dest != 'help'
    }
    assert flags - refused - _STEP_MODIFIERS == set()


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


def test_an_importers_first_interrupt_drains_and_its_second_aborts() -> None:
    """The first SIGINT is only counted; the second raises, which aborts the bundle; a
    third, arriving during the abort, is only counted."""
    ctx = make_context()
    ctx.importer = object()  # type: ignore[assignment]
    handler = cli._interrupt_handler(ctx)

    handler(signal.SIGINT, None)
    assert ctx.interrupts == 1
    with pytest.raises(KeyboardInterrupt):
        handler(signal.SIGINT, None)
    assert ctx.interrupts == 2
    handler(signal.SIGINT, None)
    assert ctx.interrupts == 3


def test_a_second_interrupt_while_the_importer_records_itself_is_only_counted() -> None:
    """Between the start of its record in ``import_process`` and its loop, or while it
    records its exit, nothing is raised: the queue loop's check of the count stops it."""
    ctx = make_context()
    ctx.queue_entered = True
    handler = cli._interrupt_handler(ctx)

    handler(signal.SIGINT, None)
    handler(signal.SIGINT, None)
    assert ctx.interrupts == 2


def test_a_second_interrupt_before_the_importer_records_itself_stops_it() -> None:
    """Reading the holdings or opening the database, it holds nothing a stop would leave
    behind, so the second interrupt raises there too, and a third is only counted."""
    ctx = make_context()
    handler = cli._interrupt_handler(ctx)

    handler(signal.SIGINT, None)
    with pytest.raises(KeyboardInterrupt):
        handler(signal.SIGINT, None)
    handler(signal.SIGINT, None)
    assert ctx.interrupts == 3


def test_a_queue_importer_names_its_logs_after_its_computer_and_process(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Several importers started in one second write files of their own; a plain run's
    logs carry no such suffix."""
    suffixes: list[str] = []

    def file_handler(*args: object, **kwargs: object) -> object:
        suffixes.append(str(kwargs.get('suffix', '')))
        return _FILE_HANDLER

    for arguments in (['--join'], ['--import', 'COISS_2002']):
        monkeypatch.setattr(sys, 'argv', ['opus_import', '--workers', '7', *arguments])
        monkeypatch.setattr(warnings, 'showwarning', warnings.showwarning)
        monkeypatch.setattr(pdslogger, 'PdsLogger', lambda *args, **kwargs: _HandlerlessLogger())
        monkeypatch.setattr(pdslogger, 'file_handler', file_handler)
        for factory in ('warning_handler', 'error_handler'):
            monkeypatch.setattr(pdslogger, factory, lambda *args, **kwargs: _FILE_HANDLER)
        monkeypatch.setattr(opus_config.config, 'detected_cores', lambda: 8)
        with pytest.raises(SystemExit):
            cli.main()
    host_and_pid = f'{cli.JOIN_LOG_SUFFIX}_{socket.gethostname()}_{os.getpid()}'
    assert suffixes == [host_and_pid, host_and_pid, '', '']


class _ErasedSchema:
    """A database the run opens, which the stubbed steps below never touch."""

    db_schema = 'opus_ci_db'
    log_sql = False


@pytest.mark.parametrize(
    ('outcome', 'failed'),
    [
        ('true', False),
        ('none', False),
        ('warning', False),
        ('false', True),
        ('error', True),
        ('fatal', True),
        ('cache', True),
    ],
)
def test_a_finishing_step_fails_by_its_result_or_by_an_error_it_logs(
    outcome: str, failed: bool
) -> None:
    """A step that returns nothing, as the cart and the analysis do, still fails when it
    logs an error, from itself or the database layer; a warning does not fail it."""
    logger = RecordingLogger()

    def step() -> object:
        if outcome in ('warning', 'error', 'fatal'):
            logger.log(outcome, 'something happened')
        if outcome == 'cache':
            raise do_django.CacheFlushError('the flush exited with status 1')
        return {'true': True, 'false': False}.get(outcome)

    failed_steps: list[str] = []
    cli._run_finishing_step(logger, failed_steps, '--create-cart', step)
    assert failed_steps == (['--create-cart'] if failed else [])
    if outcome == 'cache':
        assert logger.messages_at('error') == ['--create-cart: the flush exited with status 1']


def test_a_finishing_step_that_logs_an_error_keeps_the_schema_unmarked(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The cart step logs its failure and returns nothing; --write-schema-version refuses,
    naming it, and the invocation exits with failure."""
    monkeypatch.setattr(warnings, 'showwarning', warnings.showwarning)
    logger = _HandlerlessLogger()
    monkeypatch.setattr(pdslogger, 'PdsLogger', lambda *args, **kwargs: logger)
    for factory in ('file_handler', 'warning_handler', 'error_handler'):
        monkeypatch.setattr(pdslogger, factory, lambda *args, **kwargs: _FILE_HANDLER)
    monkeypatch.setattr(opus_config.config, 'detected_cores', lambda: 8)
    monkeypatch.setattr(importdb, 'get_db', lambda *args, **kwargs: _ErasedSchema())
    monkeypatch.setattr(cli, '_prepare_holdings', lambda *args: None)
    monkeypatch.setattr(cli, '_registry_finished', lambda ctx, step: True)
    monkeypatch.setattr(
        do_generation, 'load_generation_state', lambda ctx: setattr(ctx, 'generation_state', None)
    )
    monkeypatch.setattr(do_import, 'do_import_steps', lambda ctx: True)
    monkeypatch.setattr(
        do_cart, 'create_cart', lambda ctx: logger.log('error', 'Unable to create cart')
    )
    stamped: list[bool] = []

    def write_schema_version(ctx: ImportContext) -> bool:
        stamped.append(True)
        return True

    monkeypatch.setattr(do_schema_version, 'write_schema_version', write_schema_version)
    monkeypatch.setattr(sys, 'argv', ['opus_import', '--create-cart', '--write-schema-version'])
    with pytest.raises(SystemExit) as excinfo:
        cli.main()
    assert excinfo.value.code == -1
    assert stamped == []
    assert logger.messages_at('error')[-1] == (
        '--create-cart failed, so the schema is not marked ready; --ignore-errors marks it '
        'ready regardless'
    )


def test_an_erase_forgets_the_pending_generation_it_dropped(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """After --scorched-earth, finalization runs as on a fresh import -- the mult step,
    the cart and the search tables' reset -- and records no pending generation's state,
    since the erase dropped the version row that named one."""
    monkeypatch.setattr(warnings, 'showwarning', warnings.showwarning)
    logger = _HandlerlessLogger()
    monkeypatch.setattr(pdslogger, 'PdsLogger', lambda *args, **kwargs: logger)
    for factory in ('file_handler', 'warning_handler', 'error_handler'):
        monkeypatch.setattr(pdslogger, factory, lambda *args, **kwargs: _FILE_HANDLER)
    monkeypatch.setattr(opus_config.config, 'detected_cores', lambda: 8)
    monkeypatch.setattr(importdb, 'get_db', lambda *args, **kwargs: _ErasedSchema())
    monkeypatch.setattr(cli, '_prepare_holdings', lambda *args: None)
    monkeypatch.setattr(cli, '_registry_finished', lambda ctx, step: True)
    pending = GenerationState(SCHEMA_VERSION, 'ready', 1, 2, PENDING_READY, False)
    monkeypatch.setattr(
        do_generation,
        'load_generation_state',
        lambda ctx: setattr(ctx, 'generation_state', pending),
    )

    def erase(ctx: ImportContext) -> bool:
        """Drop the version row, as the erase does."""
        ctx.generation_state = None
        return True

    monkeypatch.setattr(do_import, 'do_import_steps', erase)
    ran: list[str] = []

    def recorder(name: str) -> Callable[..., bool]:
        """Return a stand-in step that records its name and succeeds."""

        def step(*args: object) -> bool:
            ran.append(name)
            return True

        return step

    for module, name in [
        (do_indexes, 'create_indexes'),
        (do_duplicate_ids, 'delete_duplicate_opus_ids'),
        (do_finalize_mult, 'finalize_mult'),
        (do_param_info, 'do_param_info'),
        (do_partables, 'do_partables'),
        (do_table_names, 'do_table_names'),
        (do_cart, 'create_cart'),
        (do_django, 'reset_search_tables'),
        (do_import_tables, 'analyze_all_tables'),
    ]:
        monkeypatch.setattr(module, name, recorder(name))
    monkeypatch.setattr(
        do_generation, 'set_pending_state', lambda ctx, state: ran.append(f'pending {state}')
    )
    monkeypatch.setattr(sys, 'argv', ['opus_import', '--scorched-earth', '--yes', '--finalize'])
    cli.main()
    assert ran == [
        'create_indexes',
        'delete_duplicate_opus_ids',
        'finalize_mult',
        'do_param_info',
        'do_partables',
        'do_table_names',
        'create_cart',
        'reset_search_tables',
        'analyze_all_tables',
    ]
    assert logger.messages_at('fatal') == []


class _Writer:
    """A writer's record, which the run frees at exit."""

    def exit(self) -> None:
        """Free nothing."""


@pytest.mark.parametrize(
    ('step', 'started', 'registered', 'refusal'),
    [
        (
            ['--import', 'COISS_2002'],
            None,
            None,
            '--require-pending-generation: "opus_ci_db" has no pending generation, so this '
            'invocation writes nothing',
        ),
        (['--import', 'COISS_2002'], 2, 2, None),
        (
            ['--reset-search-tables'],
            2,
            2,
            '--require-pending-generation: this invocation does not register as a writer of '
            'the schema, so nothing holds a generation command off while it writes; it '
            'writes nothing',
        ),
    ],
    ids=['none-pending', 'pending', 'not-a-registered-writer'],
)
def test_an_invocation_requiring_a_pending_generation_writes_only_into_one(
    monkeypatch: pytest.MonkeyPatch,
    step: list[str],
    started: int | None,
    registered: int | None,
    refusal: str | None,
) -> None:
    """The answer is the version row the registration read under the generation lock
    (a generation changed since the invocation started is refused there): with none
    pending the invocation stops before its steps, with the refused status, as it does
    when an abandon ran before it started. An invocation that registers no writer has
    only the row it read as it started, so it is refused even with a generation pending."""
    monkeypatch.setattr(warnings, 'showwarning', warnings.showwarning)
    logger = _HandlerlessLogger()
    monkeypatch.setattr(pdslogger, 'PdsLogger', lambda *args, **kwargs: logger)
    for factory in ('file_handler', 'warning_handler', 'error_handler'):
        monkeypatch.setattr(pdslogger, factory, lambda *args, **kwargs: _FILE_HANDLER)
    monkeypatch.setattr(opus_config.config, 'detected_cores', lambda: 8)
    monkeypatch.setattr(importdb, 'get_db', lambda *args, **kwargs: _ErasedSchema())
    monkeypatch.setattr(cli, '_prepare_holdings', lambda *args: None)
    monkeypatch.setattr(atexit, 'register', lambda function: None)

    def state(pending: int | None) -> GenerationState:
        return GenerationState(
            SCHEMA_VERSION, 'ready', 1, pending, None if pending is None else 'writing', False
        )

    monkeypatch.setattr(
        do_generation,
        'load_generation_state',
        lambda ctx: setattr(ctx, 'generation_state', state(started)),
    )

    def register_writer(ctx: ImportContext, *, sole: bool) -> _Writer:
        ctx.generation_state = state(registered)
        return _Writer()

    monkeypatch.setattr(do_generation, 'register_writer', register_writer)
    monkeypatch.setattr(do_import, 'choose_import_path', lambda ctx: True)
    ran: list[str] = []

    def steps(ctx: ImportContext) -> bool:
        ran.append('steps')
        return True

    monkeypatch.setattr(do_import, 'do_import_steps', steps)
    monkeypatch.setattr(sys, 'argv', ['opus_import', '--require-pending-generation', *step])
    if refusal is None:
        cli.main()
        assert ran == ['steps']
        return
    with pytest.raises(SystemExit) as excinfo:
        cli.main()
    assert excinfo.value.code == do_generation.GENERATION_REFUSED_EXIT_STATUS
    assert ran == []
    assert logger.messages_at('fatal') == [refusal]


@pytest.mark.parametrize(
    ('arguments', 'has_row', 'registers'),
    [
        (['--import', 'COISS_2002'], True, True),
        (['--finalize'], True, True),
        (['--validate'], True, True),
        (['--write-schema-version'], True, True),
        (['--delete-bundles', 'COISS_2002'], True, True),
        (['--import', 'COISS_2002'], False, False),
        (['--scorched-earth', '--yes', '--do-it-all', 'COISS_2002'], True, False),
        (['--read-only', '--finalize'], True, False),
        (['--import-dictionary'], True, False),
    ],
    ids=[
        'import',
        'finalize',
        'validate',
        'stamp',
        'delete',
        'no-version-row',
        'erase',
        'read-only',
        'dictionary',
    ],
)
def test_a_writer_of_a_schema_with_a_version_row_registers(
    arguments: list[str], has_row: bool, registers: bool
) -> None:
    """Only a schema with a version row can be begun on; an erase drops the table a
    registration is in, and a read-only run writes nothing."""
    args = cli._create_argument_parser().parse_args(arguments)
    cli.expand_aggregate_options(args)
    state = GenerationState(SCHEMA_VERSION, 'ready', 1, None, None, False) if has_row else None
    assert cli._registers_writer(args, state) is registers


@pytest.mark.parametrize(
    ('arguments', 'pending', 'sole'),
    [
        (['--finalize'], 2, True),
        (['--validate'], 2, True),
        (['--write-schema-version'], 2, True),
        (['--do-it-all', 'COISS_2002'], 2, True),
        (['--import', 'COISS_2002'], 2, False),
        (['--create-param-info'], 2, False),
        (['--finalize'], None, False),
    ],
    ids=['finalize', 'validate', 'stamp', 'do-it-all', 'import', 'rebuild', 'nothing-pending'],
)
def test_the_invocations_that_move_a_generation_forward_write_it_alone(
    arguments: list[str], pending: int | None, sole: bool
) -> None:
    """Finalization, validation and the stamp record a state of the pending generation's
    rows, so each writes it alone; the served rows have no state to record."""
    args = cli._create_argument_parser().parse_args(arguments)
    cli.expand_aggregate_options(args)
    assert cli._writes_as_sole_writer(args, pending) is sole
