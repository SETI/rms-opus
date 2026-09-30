"""Every file under ``src/`` is tracked by git, because git is what decides what ships.

setuptools-scm's file finder builds the sdist and the wheel out of the files **git
tracks**, not out of the files present in a working tree. So a source file that is
untracked is in every developer's checkout, passes every test run from one, and is
missing from every installation built from the repository -- which is the one place
nobody looks until a server stops on it.

``.gitignore`` is how that happens. Its patterns are written for build output and
scratch files, and they match source files by accident: ``temp*.*`` swallowed
``opus_config/template.py``, and ``*venv*`` swallowed the deploy chain's
``_activate_deploy_venv.sh``, which then shipped in no wheel while every check here
passed. Each was fixed with a ``!`` line beside the pattern that caused it; this test is
what makes the next one fail in the repository rather than on a server.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SOURCE = REPO_ROOT / 'src'

#: Files under ``src/`` that are untracked on purpose. ``_version.py`` is written by
#: setuptools-scm at build time from the git tag, so a checked-in one would be a
#: version claim that the build then contradicts.
GENERATED = {'opus_config/_version.py'}

#: Directories a walk of ``src/`` finds and git never tracks: bytecode caches and the
#: metadata an editable install leaves behind.
SKIP_DIRECTORIES = {'__pycache__'}


def _is_a_git_checkout() -> bool:
    """Whether these tests are running inside a git working tree."""
    result = subprocess.run(
        ['git', 'rev-parse', '--is-inside-work-tree'],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    return result.returncode == 0


@pytest.mark.skipif(
    not _is_a_git_checkout(), reason='there is nothing to compare outside a checkout'
)
def test_every_source_file_is_tracked() -> None:
    """A file only a working tree has is a file no installation gets.

    The failure names the paths and the command that says which ``.gitignore`` line is
    responsible, because the pattern is never the obvious one -- both of the files this
    has caught were matched by a rule written for something else entirely.
    """
    tracked = {
        line
        for line in subprocess.run(
            ['git', 'ls-files', 'src'],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.splitlines()
        if line
    }

    present = {
        str(path.relative_to(REPO_ROOT))
        for path in SOURCE.rglob('*')
        if path.is_file()
        and not SKIP_DIRECTORIES & set(path.parts)
        and path.suffix != '.pyc'
        and '.egg-info' not in str(path)
    }

    untracked = sorted(present - tracked - {f'src/{name}' for name in GENERATED})
    assert untracked == [], (
        'These files are in the working tree and in no wheel:\n  '
        + '\n  '.join(untracked)
        + '\n\nWhich .gitignore line is swallowing each one:\n  '
        + '\n  '.join(f'git check-ignore -v {path}' for path in untracked)
    )
