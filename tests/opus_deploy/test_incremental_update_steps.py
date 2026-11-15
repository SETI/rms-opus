"""Tests for the incremental update's steps, run as shell functions.

``_run_incremental_opus_update.sh`` builds an installation and writes the served schema,
and is never run for real by a test. Its logic is functions in
``_incremental_opus_update_steps.sh``, which defines them and executes nothing, so it is
sourced here, beside ``_promote_steps.sh`` whose rule it reads the served schema by, under
``set -e`` as the scripts run, with a fake ``opus_import`` first on ``PATH`` that records
each invocation and can fail one or write an error into ``ERRORS.log`` for one.
"""

from __future__ import annotations

import shlex
import subprocess  # nosec B404
from typing import TYPE_CHECKING

import pytest

from opus_deploy import scripts

from .conftest import BASH, defines_only_functions, write_recorder

if TYPE_CHECKING:
    from pathlib import Path

#: The steps, and the promotion's steps they need, inside the packaged chain.
_STEPS = 'import_and_deploy/_incremental_opus_update_steps.sh'
_PROMOTE_STEPS = 'import_and_deploy/_promote_steps.sh'

#: The usage line the update's scripts print.
_USAGE = (
    'Usage: run_incremental_opus_update.sh [<version_spec>] '
    '[--drop <bundle>[,<bundle>...]] [<bundle> ...]'
)

#: The invocations every update begins and ends with.
_BEGIN = 'opus_import --begin-generation'
_CLOSING = [
    'opus_import --finalize',
    'opus_import --validate',
    'opus_import --write-schema-version',
]


def _run_steps(
    tmp_path: Path,
    call: str,
    *,
    failing: str | None = None,
    logs_error: str | None = None,
) -> tuple[int, str, list[str]]:
    """Source the steps with a fake ``opus_import`` under ``set -e`` and run one line.

    Parameters:
        tmp_path: A scratch directory. Its ``logs`` directory, which starts empty, is
            the update's log directory, named to the line as ``$LOGS``.
        call: The line to run after sourcing.
        failing: The arguments, joined by spaces, for which the fake exits 1.
        logs_error: The arguments for which the fake writes a line into ERRORS.log and
            exits 0, as an import step that reports a failure through the log does.

    Returns:
        The line's status, everything it printed, and each ``opus_import`` invocation.
    """
    chain = tmp_path / 'chain'
    scripts.write_scripts(chain)
    fake_bin = tmp_path / 'bin'
    fake_bin.mkdir()
    logs = tmp_path / 'logs'
    logs.mkdir()
    calls = tmp_path / 'calls'
    body = ''
    if failing is not None:
        body += f'[[ "$*" == {shlex.quote(failing)} ]] && exit 1\n'
    if logs_error is not None:
        errors = shlex.quote(str(logs / 'ERRORS.log'))
        body += f'[[ "$*" == {shlex.quote(logs_error)} ]] && echo "ERROR: bad label" >> {errors}\n'
    write_recorder(fake_bin / 'opus_import', calls, body)
    sourced = ' '.join(
        f'source {shlex.quote(str(chain / name))};' for name in (_PROMOTE_STEPS, _STEPS)
    )
    assert BASH is not None
    finished = subprocess.run(  # nosec B603 - bash and the packaged files
        [BASH, '-c', f'set -e; {sourced} {call}'],
        env={'PATH': f'{fake_bin}:/usr/bin:/bin', 'LOGS': str(logs)},
        capture_output=True,
        text=True,
        check=False,
    )
    ran = calls.read_text(encoding='utf-8').splitlines() if calls.exists() else []
    return finished.returncode, finished.stdout + finished.stderr, ran


def _update(arguments: str) -> str:
    """Return the line that parses the arguments and runs the update's invocations."""
    return f'parse_update_arguments {arguments}; run_update_invocations "$LOGS"; echo DONE'


@pytest.mark.skipif(BASH is None, reason='needs bash')
@pytest.mark.parametrize(
    ('arguments', 'middle'),
    [
        ('COISS_2001 COISS_2002,COISS_2003', ['--import COISS_2001 COISS_2002 COISS_2003']),
        ('--drop COISS_2001,COISS_2002', ['--delete-bundles COISS_2001 COISS_2002']),
        (
            '==3.25.0 --drop COISS_2009 COISS_2001',
            ['--import COISS_2001', '--delete-bundles COISS_2009'],
        ),
        (
            'COISS_2001,COISS_2002 --drop COISS_2002,COISS_2003',
            ['--import COISS_2001 COISS_2002', '--delete-bundles COISS_2003'],
        ),
        ('COISS_2001 --drop COISS_2001', ['--import COISS_2001']),
        ('--drop COISS_2001 --drop ,COISS_2002,', ['--delete-bundles COISS_2001 COISS_2002']),
    ],
    ids=[
        'bundles-only',
        'drop-only',
        'both',
        'one-named-both-ways',
        'only-named-both-ways',
        'repeated-drop',
    ],
)
def test_the_update_runs_its_invocations_in_order(
    tmp_path: Path, arguments: str, middle: list[str]
) -> None:
    """The generation is begun first and closed last, exactly once each; the import comes
    before the drop, and a bundle named both ways is imported and not dropped."""
    status, output, ran = _run_steps(tmp_path, _update(arguments))
    assert status == 0, output
    assert ran == [_BEGIN, *[f'opus_import {step}' for step in middle], *_CLOSING]
    assert 'DONE' in output


@pytest.mark.skipif(BASH is None, reason='needs bash')
@pytest.mark.parametrize(
    ('arguments', 'version_spec'),
    [('==3.25.0 COISS_2001', '==3.25.0'), ('COISS_2001', '')],
    ids=['given', 'omitted'],
)
def test_a_leading_version_specifier_is_not_a_bundle(
    tmp_path: Path, arguments: str, version_spec: str
) -> None:
    """The first argument is the version specifier when it begins with an operator."""
    status, output, _ran = _run_steps(
        tmp_path,
        f'parse_update_arguments {arguments}; echo "[$OPUS_VERSION_SPEC] [${{UPDATE_BUNDLES[*]}}]"',
    )
    assert status == 0, output
    assert output.strip() == f'[{version_spec}] [COISS_2001]'


@pytest.mark.skipif(BASH is None, reason='needs bash')
@pytest.mark.parametrize(
    'arguments',
    [
        '',
        '==3.25.0',
        '--drop',
        '--drop ,',
        ',',
        'COISS_2001 --drop --verbose',
        'COISS_2001 --force',
        'A ==3.25.0',
    ],
    ids=[
        'nothing',
        'only-a-version',
        'drop-without-value',
        'drop-of-nothing',
        'bundle-of-nothing',
        'drop-followed-by-option',
        'unknown-option',
        'version-not-first',
    ],
)
def test_arguments_that_name_nothing_to_do_print_the_usage_line(
    tmp_path: Path, arguments: str
) -> None:
    """The exact usage line, a non-zero return, and no invocation."""
    status, output, ran = _run_steps(
        tmp_path, f'if ! parse_update_arguments {arguments}; then exit 3; fi; echo PARSED'
    )
    assert status == 3
    assert output.strip() == _USAGE
    assert ran == []


@pytest.mark.skipif(BASH is None, reason='needs bash')
def test_a_failed_invocation_stops_the_update_and_names_what_is_left(tmp_path: Path) -> None:
    """Nothing runs after it; the message names it, the rest, and the abandon."""
    status, output, ran = _run_steps(
        tmp_path, _update('COISS_2001 --drop COISS_2002'), failing='--import COISS_2001'
    )
    assert status != 0
    assert ran == [_BEGIN, 'opus_import --import COISS_2001']
    assert 'ERROR: opus_import --import COISS_2001 failed or logged errors.' in output
    assert '    opus_import --delete-bundles COISS_2002\n' in output
    assert '    opus_import --write-schema-version\n' in output
    assert '    opus_import --abandon-generation\n' in output
    assert 'DONE' not in output


@pytest.mark.skipif(BASH is None, reason='needs bash')
def test_an_error_in_the_log_stops_the_update_before_the_stamp(tmp_path: Path) -> None:
    """A step that logs an error and exits zero still stops the update, so the generation
    is never stamped ready to switch."""
    status, output, ran = _run_steps(tmp_path, _update('COISS_2001'), logs_error='--validate')
    assert status != 0
    assert ran == [_BEGIN, 'opus_import --import COISS_2001', *_CLOSING[:2]]
    assert 'ERROR: bad label' in output
    assert 'THE UPDATE LOGGED ERRORS' in output
    assert 'DONE' not in output


@pytest.mark.skipif(BASH is None, reason='needs bash')
@pytest.mark.parametrize(
    ('contents', 'expected'),
    [(None, 0), ('', 0), ('ERROR: bad label\n', 1)],
    ids=['absent', 'empty', 'non-empty'],
)
def test_the_error_log_check_fails_only_on_a_non_empty_log(
    tmp_path: Path, contents: str | None, expected: int
) -> None:
    """An absent or empty ERRORS.log passes; one that holds anything fails and is shown."""
    errors = tmp_path / 'logs' / 'ERRORS.log'
    write = '' if contents is None else f'printf %s {shlex.quote(contents)} > {errors}; '
    status, output, _ran = _run_steps(
        tmp_path, f'{write}if check_update_error_log "$LOGS"; then exit 0; else exit 1; fi'
    )
    assert status == expected
    assert ('ERROR: bad label' in output) == (expected == 1)


@pytest.mark.skipif(BASH is None, reason='needs bash')
@pytest.mark.parametrize(
    ('toml', 'expected_status', 'expected_output'),
    [
        ('[database]\nschema = "opus3_served"\n', 0, 'opus3_served'),
        ('[database]\n', 1, 'ERROR: cannot read the served schema'),
        (None, 1, 'ERROR: cannot read the served schema'),
    ],
    ids=['named', 'unnamed', 'missing'],
)
def test_the_served_schema_is_read_from_the_deployed_configuration(
    tmp_path: Path, toml: str | None, expected_status: int, expected_output: str
) -> None:
    """The schema line of ``deployed/opus.toml``, or an error when there is none."""
    deployed = tmp_path / 'opus.toml'
    if toml is not None:
        deployed.write_text(toml, encoding='utf-8')
    status, output, _ran = _run_steps(
        tmp_path, f'if served_schema_name {deployed}; then exit 0; else exit 1; fi'
    )
    assert status == expected_status
    assert expected_output in output


def test_sourcing_the_steps_runs_nothing(tmp_path: Path) -> None:
    """Every top-level line belongs to a function definition, so the tests can source it."""
    scripts.write_scripts(tmp_path)
    assert defines_only_functions(tmp_path / _STEPS)


@pytest.mark.skipif(BASH is None, reason='needs bash')
@pytest.mark.parametrize(
    ('release', 'printed', 'status'),
    [
        ('3.25.0', '==3.25.0', 0),
        ('', 'cannot read the rms-opus release', 1),
        ('3.25.1.dev4+g1234abc', 'a local build PyPI does not have', 1),
    ],
    ids=['release', 'unreadable', 'local-build'],
)
def test_the_deployed_release_is_read_from_the_deployed_interpreter(
    tmp_path: Path, release: str, printed: str, status: int
) -> None:
    """A release PyPI has is pinned; anything else is an error and prints no pin."""
    deployed = tmp_path / 'deployed'
    interpreter = deployed / 'opus_venv' / 'bin' / 'python'
    interpreter.parent.mkdir(parents=True)
    interpreter.write_text(f'#!/bin/sh\necho {shlex.quote(release)}\n', encoding='utf-8')
    interpreter.chmod(0o755)
    found, output, _ran = _run_steps(
        tmp_path, f'deployed_release_spec {shlex.quote(str(deployed))}'
    )
    assert found == status
    assert printed in output
    if status:
        assert '==' not in output
