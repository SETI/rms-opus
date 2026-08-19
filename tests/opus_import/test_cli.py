"""Tests for the import pipeline's command-line surface.

The pipeline used to be a script whose whole body, including the settings it read from
``opus_secrets.py``, ran at import time. These tests pin what replaced it: a parser that
can be built without side effects, and an entry point that reads no settings until it has
arguments to act on.
"""

import os
import subprocess
import sys
from pathlib import Path

import pytest

import opus_import.__main__
from opus_config._secrets_compat import OPUS_SECRETS_ENV_VAR
from opus_import import cli


def test_parser_defaults_to_doing_nothing() -> None:
    """With no arguments every action is off and no bundle is selected."""
    args = cli._create_argument_parser().parse_args([])
    assert args.do_it_all is False
    assert args.do_import is False
    assert args.validate_perm is False
    assert args.bundles == []
    assert args.override_db_schema is None


def test_parser_reads_bundles_and_options() -> None:
    """Bundle descriptors are positional; the options around them keep their names."""
    args = cli._create_argument_parser().parse_args(
        ['--import-check-duplicate-id', '--do-all-import',
         '--override-db-schema', 'opus_test_db', 'COISS_2002,COISS_2008'])
    assert args.bundles == ['COISS_2002,COISS_2008']
    assert args.do_all_import is True
    assert args.import_check_duplicate_id is True
    assert args.override_db_schema == 'opus_test_db'


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


def test_module_execution_dispatches_to_main() -> None:
    """``python -m opus_import`` runs `cli.main`, which PR-22 also wires as a script."""
    assert opus_import.__main__.main is cli.main


def _run_without_settings(directory: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
    """Run ``python -m opus_import`` in a directory holding no settings of any kind."""
    workdir = directory / 'no_settings_here'
    workdir.mkdir()
    env = dict(os.environ)
    env.pop(OPUS_SECRETS_ENV_VAR, None)
    return subprocess.run([sys.executable, '-m', 'opus_import', *arguments],
                          capture_output=True, text=True, cwd=workdir, env=env,
                          check=False)


def test_help_works_without_a_secrets_file(tmp_path: Path) -> None:
    """``--help`` runs with no settings anywhere, which the old script could not do.

    The settings arrived through a module-level wildcard import that ran before argparse,
    so asking for usage on a machine with no ``opus_secrets.py`` failed. Runs in a
    subprocess because the check is about what the process needs at startup.
    """
    result = _run_without_settings(tmp_path, '--help')
    assert result.returncode == 0, result.stderr
    assert result.stdout.startswith('usage: opus_import')
    assert '--do-it-all' in result.stdout


def test_running_without_settings_reports_the_missing_file(tmp_path: Path) -> None:
    """Asking for real work without settings names the file and the variable to set."""
    result = _run_without_settings(tmp_path, '--validate-perm')
    assert result.returncode != 0
    assert 'opus_secrets.py' in result.stderr
    assert OPUS_SECRETS_ENV_VAR in result.stderr
