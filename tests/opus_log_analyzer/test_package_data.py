"""Tests for locating the Jinja report templates that ship inside `opus_log_analyzer`.

The templates used to be loaded from the relative path `templates/`, so HTML reports
could only be produced by running the analyzer from its own source directory. These
tests pin the replacement: the templates are package data, located through the package
itself, wherever the process happens to be running.
"""

from pathlib import Path

import pytest

from opus_log_analyzer.jinga_environment import JINJA_ENVIRONMENT

# Every template the two programs ask for by name.
TEMPLATE_NAMES = ('error_analysis.html', 'histogram.html', 'log_analysis.html',
                  'summary.html')


def test_every_template_ships() -> None:
    """The packaged template directory holds exactly the templates the reports use."""
    assert sorted(JINJA_ENVIRONMENT.list_templates()) == sorted(TEMPLATE_NAMES)


@pytest.mark.parametrize('name', TEMPLATE_NAMES)
def test_template_loads_and_compiles(name: str) -> None:
    """Each template is readable through the environment and compiles."""
    assert JINJA_ENVIRONMENT.get_template(name) is not None


def test_templates_are_found_from_any_working_directory(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """The templates are package data, so no working directory is privileged.

    While the loader was a relative file-system path, asking for a template from
    anywhere but the analyzer's own source directory raised `TemplateNotFound`. The
    loader is asked directly rather than through `get_template`, so the environment's
    template cache cannot make the assertion pass for the wrong reason.
    """
    monkeypatch.chdir(tmp_path)
    loader = JINJA_ENVIRONMENT.loader
    assert loader is not None
    source, _filename, _uptodate = loader.get_source(JINJA_ENVIRONMENT, 'log_analysis.html')
    assert source
