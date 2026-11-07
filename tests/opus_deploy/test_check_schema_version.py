"""Tests for the deploy chain's schema version check, run as a shell function.

The deploy scripts run ``sudo`` and are never run by a test. The check is a file of its
own that defines one function and executes nothing, so it is sourced here with a fake
``python`` first on ``PATH`` that answers the one question the function asks: what would
keep the served database from being served.
"""

from __future__ import annotations

import shutil
import subprocess  # nosec B404
import textwrap
from typing import TYPE_CHECKING

import pytest

from opus_deploy import scripts

if TYPE_CHECKING:
    from pathlib import Path

#: The check, inside the packaged chain.
_CHECK = 'import_and_deploy/_check_schema_version.sh'

_BASH = shutil.which('bash')


def _run_check(tmp_path: Path, problem: str, *, unreadable: bool = False) -> tuple[int, str]:
    """Source the check with a fake python and call it.

    Parameters:
        tmp_path: A scratch directory.
        problem: What the fake python prints: empty when the database may be served.
        unreadable: Make the database unreadable instead.

    Returns:
        The function's status and everything it printed.
    """
    chain = tmp_path / 'chain'
    scripts.write_scripts(chain)
    fake_bin = tmp_path / 'bin'
    fake_bin.mkdir()
    fake_python = fake_bin / 'python'
    answer = 'echo Traceback >&2; exit 1' if unreadable else f"echo '{problem}'"
    fake_python.write_text(
        textwrap.dedent(
            f"""\
            #!/bin/bash
            case "$2" in
                *served_schema_version_problem*) {answer} ;;
                *) exit 2 ;;
            esac
            """
        ),
        encoding='utf-8',
    )
    fake_python.chmod(0o755)
    assert _BASH is not None
    finished = subprocess.run(  # nosec B603 - bash and a fixed script
        [_BASH, '-c', f'source "{chain / _CHECK}"; check_schema_version'],
        env={'PATH': f'{fake_bin}:/usr/bin:/bin', 'OPUS_CONFIG': str(tmp_path / 'opus.toml')},
        capture_output=True,
        text=True,
        check=False,
    )
    return finished.returncode, finished.stdout + finished.stderr


@pytest.mark.skipif(_BASH is None, reason='needs bash')
def test_a_servable_database_passes(tmp_path: Path) -> None:
    """The only database a deploy proceeds over."""
    status, output = _run_check(tmp_path, '')
    assert status == 0, output
    assert 'ERROR' not in output


@pytest.mark.skipif(_BASH is None, reason='needs bash')
def test_a_database_the_application_would_refuse_is_refused(tmp_path: Path) -> None:
    """The refusal carries the application's own sentence, then the deploy's remedy."""
    problem = 'the schema is version 8, and this release is version 7: re-import it'
    status, output = _run_check(tmp_path, problem)
    assert status == 1
    assert f'ERROR: this release would not serve the database: {problem}.' in output
    assert 'run_full_opus_import.sh' in output


@pytest.mark.skipif(_BASH is None, reason='needs bash')
def test_an_unreadable_database_refuses(tmp_path: Path) -> None:
    """A database the check cannot read is not deployed onto."""
    status, output = _run_check(tmp_path, '', unreadable=True)
    assert status == 1
    assert 'cannot read the schema_version row' in output


def test_sourcing_the_check_runs_nothing(tmp_path: Path) -> None:
    """Its only top-level statement is the function, so the test above can source it."""
    scripts.write_scripts(tmp_path)
    lines = [
        line
        for line in (tmp_path / _CHECK).read_text(encoding='utf-8').splitlines()
        if line.strip() != '' and not line.startswith('#')
    ]
    assert lines[0] == 'check_schema_version() {'
    assert lines[-1] == '}'
