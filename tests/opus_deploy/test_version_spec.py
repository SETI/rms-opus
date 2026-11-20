"""Tests for the version spec every deploy script takes: a release, or a git revision.

``_version_spec.sh`` defines its functions and the repository and runs nothing else, so
it is sourced here and each function called; the deploy scripts that read a spec are run
through `run_deploy`.
"""

from __future__ import annotations

import shlex
import subprocess  # nosec B404
from typing import TYPE_CHECKING

import pytest

from opus_deploy import scripts

from .conftest import BASH, run_deploy

if TYPE_CHECKING:
    from pathlib import Path

#: The helper, inside the packaged chain.
_HELPER = 'import_and_deploy/_version_spec.sh'

#: The repository a git ref is installed from.
_REPOSITORY = 'https://github.com/SETI/rms-opus.git'

#: Specs the helper accepts, with the requirement it gives pip for each.
_ACCEPTED = [
    ('==3.25.0', 'rms-opus==3.25.0'),
    ('>=3.25', 'rms-opus>=3.25'),
    ('~=3.25.0', 'rms-opus~=3.25.0'),
    ('@main', f'rms-opus @ git+{_REPOSITORY}@main'),
    ('@review-branch', f'rms-opus @ git+{_REPOSITORY}@review-branch'),
    ('@v3.25.0', f'rms-opus @ git+{_REPOSITORY}@v3.25.0'),
    ('@feature/x_1', f'rms-opus @ git+{_REPOSITORY}@feature/x_1'),
    ('@208b19c0', f'rms-opus @ git+{_REPOSITORY}@208b19c0'),
]

#: Arguments the helper refuses.
_REFUSED = ['3.25.0', 'review-branch', '@', '@-x', '@a..b', '@a b', '@a;rm', 'main@x']


def _source(tmp_path: Path, call: str) -> tuple[int, str]:
    """Source the helper under ``set -e`` and run one line.

    Parameters:
        tmp_path: A scratch directory.
        call: The line to run after sourcing.

    Returns:
        The line's status, and everything it printed.
    """
    chain = tmp_path / 'chain'
    scripts.write_scripts(chain)
    assert BASH is not None
    finished = subprocess.run(  # nosec B603 - bash and the packaged file
        [BASH, '-c', f'set -e; source {shlex.quote(str(chain / _HELPER))}; {call}'],
        env={'PATH': '/usr/bin:/bin'},
        capture_output=True,
        text=True,
        check=False,
    )
    return finished.returncode, finished.stdout + finished.stderr


@pytest.mark.skipif(BASH is None, reason='needs bash')
@pytest.mark.parametrize(('spec', 'needed'), _ACCEPTED)
def test_a_spec_is_accepted_and_turned_into_what_pip_installs(
    tmp_path: Path, spec: str, needed: str
) -> None:
    """A PEP 440 specifier is appended to the name; a git ref names the repository."""
    status, output = _source(
        tmp_path,
        f'is_version_spec {shlex.quote(spec)} && opus_requirement {shlex.quote(spec)}',
    )
    assert status == 0, output
    assert output.strip() == needed


@pytest.mark.skipif(BASH is None, reason='needs bash')
@pytest.mark.parametrize('spec', _REFUSED)
def test_anything_else_is_refused(tmp_path: Path, spec: str) -> None:
    """``check_version_spec`` names the script, the argument and both forms."""
    status, output = _source(
        tmp_path, f'check_version_spec deploy_x.sh {shlex.quote(spec)} || exit 3'
    )
    assert status == 3
    assert f"deploy_x.sh: '{spec}' is not a version spec" in output
    assert "'@main'" in output


@pytest.mark.skipif(BASH is None, reason='needs bash')
def test_no_spec_is_the_newest_release(tmp_path: Path) -> None:
    """Empty passes the check, and pip is given the bare distribution."""
    status, output = _source(tmp_path, 'check_version_spec deploy_x.sh "" && opus_requirement')
    assert status == 0, output
    assert output.strip() == 'rms-opus'


@pytest.mark.skipif(BASH is None, reason='needs bash')
@pytest.mark.parametrize(
    ('script', 'arguments'),
    [
        ('import_and_deploy/deploy_new_code_and_database.sh', ('opus_new', 'review-branch')),
        ('import_and_deploy/deploy_new_code_only.sh', ('review-branch',)),
        ('import_and_deploy/run_full_opus_import.sh', ('review-branch',)),
        ('import_and_deploy/update_deploy_scripts.sh', ('review-branch',)),
    ],
    ids=['code-and-database', 'code-only', 'full-import', 'update-scripts'],
)
def test_a_deploy_refuses_a_mistyped_spec_before_anything_runs(
    tmp_path: Path, script: str, arguments: tuple[str, ...]
) -> None:
    """A spec without its "@" is refused by name, and nothing is run."""
    status, output, ran = run_deploy(tmp_path, script, *arguments)
    assert status == 1
    assert ran == []
    assert "'review-branch' is not a version spec" in output


@pytest.mark.skipif(BASH is None, reason='needs bash')
def test_a_deploy_takes_a_git_ref(tmp_path: Path) -> None:
    """The deploy goes on to the promotion, and says which revision it deploys."""
    status, output, ran = run_deploy(
        tmp_path, 'import_and_deploy/deploy_new_code_only.sh', '@review-branch'
    )
    assert status == 0, output
    assert ran[-1].startswith('promote ')
    assert 'Version spec: @review-branch' in output
