"""Tests for the deploy chain's schema version check, run as a shell function.

The deploy scripts run ``sudo`` and are never run by a test. The check is a file of its
own that defines one function and executes nothing, so it is sourced here with a fake
``python`` first on ``PATH`` that answers the two questions the function asks: the
release's version and the served database's row.
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

#: What the fake python prints for the release's version.
_RELEASE = '7'

_BASH = shutil.which('bash')


def _run_check(tmp_path: Path, served: str, *, release_fails: bool = False) -> tuple[int, str]:
    """Source the check with a fake python and call it.

    Parameters:
        tmp_path: A scratch directory.
        served: What the fake python prints for the database's row.
        release_fails: Make the release's version unreadable instead.

    Returns:
        The function's status and everything it printed.
    """
    chain = tmp_path / 'chain'
    scripts.write_scripts(chain)
    fake_bin = tmp_path / 'bin'
    fake_bin.mkdir()
    fake_python = fake_bin / 'python'
    release_line = 'exit 1' if release_fails else f'echo {_RELEASE}'
    fake_python.write_text(
        textwrap.dedent(
            f"""\
            #!/bin/bash
            case "$2" in
                *SCHEMA_VERSION*) {release_line} ;;
                *served_row*) echo '{served}' ;;
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
def test_a_matching_ready_row_passes(tmp_path: Path) -> None:
    """The only row a deploy proceeds over."""
    status, output = _run_check(tmp_path, f'{_RELEASE} ready')
    assert status == 0, output
    assert f'release {_RELEASE}, database {_RELEASE} ready' in output


@pytest.mark.skipif(_BASH is None, reason='needs bash')
@pytest.mark.parametrize(
    ('served', 'expected'),
    [
        ('absent', 'no schema_version row'),
        ('8 ready', 'schema version 8'),
        (f'{_RELEASE} appending', "state is 'appending'"),
        ('2 rows', 'holds 2 rows'),
    ],
    ids=['absent', 'different', 'not-ready', 'several-rows'],
)
def test_any_other_row_refuses_naming_the_remedy(
    tmp_path: Path, served: str, expected: str
) -> None:
    """Absent, different, or not ready: the deploy stops before writing anything."""
    status, output = _run_check(tmp_path, served)
    assert status == 1
    assert expected in output
    assert 'ERROR' in output


@pytest.mark.skipif(_BASH is None, reason='needs bash')
def test_an_unreadable_release_version_refuses(tmp_path: Path) -> None:
    """A staged installation that cannot say its version is not deployed."""
    status, output = _run_check(tmp_path, f'{_RELEASE} ready', release_fails=True)
    assert status == 1
    assert "cannot read the release's schema version" in output


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
