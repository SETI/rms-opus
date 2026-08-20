"""Tests for locating the Jinja report templates that ship inside `opus_log_analyzer`.

The templates are package data, located through the package itself, so an installed
analyzer renders its HTML reports from any working directory.
"""

import subprocess
import sys
from pathlib import Path

import pytest

from opus_log_analyzer.jinga_environment import JINJA_ENVIRONMENT

# Every template the reports use, directly or through an {% include %}.
TEMPLATE_NAMES = ('error_analysis.html', 'histogram.html', 'log_analysis.html',
                  'summary.html')


def test_every_template_ships() -> None:
    """The packaged template directory holds exactly the templates the reports use."""
    assert sorted(JINJA_ENVIRONMENT.list_templates()) == sorted(TEMPLATE_NAMES)


@pytest.mark.parametrize('name', TEMPLATE_NAMES)
def test_template_loads_and_compiles(name: str) -> None:
    """Each template is readable through the environment and compiles.

    `get_template` both resolves the name against the packaged directory and compiles the
    source, so a template missing from the wheel or carrying a syntax error fails here.
    """
    assert JINJA_ENVIRONMENT.get_template(name).name == name


def test_templates_are_found_from_any_working_directory(tmp_path: Path) -> None:
    """No working directory is privileged, including the one the package is imported from.

    The environment resolves its template root while `jinga_environment` is being
    imported, so this has to be a fresh interpreter started somewhere else entirely; a
    `chdir` inside this process would come too late to prove anything.
    """
    result = subprocess.run(
        [sys.executable, '-c',
         'from opus_log_analyzer.jinga_environment import JINJA_ENVIRONMENT\n'
         "print(JINJA_ENVIRONMENT.get_template('log_analysis.html').name)"],
        cwd=tmp_path, capture_output=True, text=True, check=False, timeout=60)
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == 'log_analysis.html'
