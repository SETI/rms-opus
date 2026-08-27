"""Tests for the console scripts the installed distribution declares.

The server chains invoke ``opus_import``, ``opus_log_analyzer`` and
``opus_error_analyzer`` **by name** -- no repository-relative paths and no bare
``python -m`` -- so a console script whose target has moved breaks a deploy rather than
a test run. These tests read the entry points back out of the *installed* metadata
rather than out of ``pyproject.toml``, because the installed metadata is what ``pip``
writes and what the shell finds on ``PATH``, and they run the installed commands rather
than importing their targets, because running is the only thing that proves the wrapper
scripts themselves were written.
"""

from __future__ import annotations

import importlib.metadata
import os
import subprocess
import sys
from pathlib import Path

import pytest

# The commands this distribution promises, and the ``module:attribute`` each one must
# name. The plan (PR-22) fixes both the names -- underscores, not hyphens -- and the
# targets; this mapping is the assertion, not a description of one.
EXPECTED_SCRIPTS = {
    'opus_import': 'opus_import.cli:main',
    'opus_log_analyzer': 'opus_log_analyzer.log_analyzer:main',
    'opus_error_analyzer': 'opus_log_analyzer.error_analyzer:main',
}

# The ``python -m`` form documented as equivalent to each console script. The error
# analyzer names a module rather than a package: a package has one ``__main__`` and the
# log analyzer holds it.
PYTHON_M_EQUIVALENT = {
    'opus_import': 'opus_import',
    'opus_log_analyzer': 'opus_log_analyzer',
    'opus_error_analyzer': 'opus_log_analyzer.error_analyzer',
}


def _console_scripts() -> dict[str, importlib.metadata.EntryPoint]:
    """Return this distribution's console-script entry points, keyed by command name."""
    entry_points = importlib.metadata.distribution('rms-opus').entry_points
    return {ep.name: ep for ep in entry_points if ep.group == 'console_scripts'}


def _installed_command(name: str) -> Path:
    """Return the path of an installed console script beside the running interpreter.

    ``pip`` writes console scripts into the same directory as the interpreter they were
    installed for, so this locates the script belonging to *this* environment rather
    than whichever same-named command happens to be first on ``PATH``.
    """
    bindir = Path(sys.executable).parent
    for candidate in (bindir / name, bindir / f'{name}.exe'):
        if candidate.exists():
            return candidate
    pytest.fail(f'console script {name!r} is not installed in {bindir}')


def _run(command: list[str]) -> subprocess.CompletedProcess[str]:
    """Run a command to completion, capturing its output as text.

    The environment is inherited so that ``OPUS_CONFIG`` reaches the child, which every
    process reading OPUS settings needs.
    """
    return subprocess.run(
        command, capture_output=True, text=True, check=False, env=os.environ.copy()
    )


def test_every_promised_console_script_is_declared() -> None:
    """The installed distribution declares exactly these commands and no others.

    Equality rather than a subset: a command silently dropped breaks a deploy, and one
    added without a test is one nothing checks.
    """
    assert set(_console_scripts()) == set(EXPECTED_SCRIPTS)


@pytest.mark.parametrize(('name', 'target'), sorted(EXPECTED_SCRIPTS.items()))
def test_console_script_names_its_documented_target(name: str, target: str) -> None:
    """Each command names the ``module:attribute`` this project documents it as naming."""
    assert _console_scripts()[name].value == target


@pytest.mark.parametrize('name', sorted(EXPECTED_SCRIPTS))
def test_console_script_target_resolves(name: str) -> None:
    """Loading the entry point imports its module and finds its attribute.

    A moved or renamed ``main`` makes ``load()`` raise ``ModuleNotFoundError`` or
    ``AttributeError`` here rather than at the top of a production import run.
    """
    assert callable(_console_scripts()[name].load())


@pytest.mark.parametrize('name', sorted(EXPECTED_SCRIPTS))
def test_installed_command_runs_and_names_itself(name: str) -> None:
    """The installed command runs, and argparse reports the command's own name.

    Every parser sets ``prog`` explicitly. Without that, argparse names the file it is
    executing -- ``__main__.py`` for the ``python -m`` form -- and the usage line stops
    matching the command an operator typed.
    """
    result = _run([str(_installed_command(name)), '--help'])
    assert result.returncode == 0, result.stderr
    assert result.stdout.startswith(f'usage: {name} ')


@pytest.mark.parametrize('name', sorted(EXPECTED_SCRIPTS))
def test_installed_command_and_python_m_form_agree(name: str) -> None:
    """Both documented ways of running a program produce the same command-line surface.

    The guide offers ``python -m`` alongside each console script, so the two must not
    drift: they share one ``main``, and this is what proves the sharing is real rather
    than a claim in prose.
    """
    console = _run([str(_installed_command(name)), '--help'])
    module = _run([sys.executable, '-m', PYTHON_M_EQUIVALENT[name], '--help'])
    assert module.returncode == 0, module.stderr
    assert console.stdout == module.stdout
