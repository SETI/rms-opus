"""Tests for the command that writes the configuration template.

``opus_config_template`` is how an operator gets a configuration file to fill in: an
installation is a ``pip install`` with no checkout on the machine, so there is nothing
else to copy the template from. What is worth pinning is that the template really ships
inside the package, that a copy is written where the operator asked, and that an existing
copy -- which may be one somebody has already edited -- is not silently replaced.
"""

import tomllib
from pathlib import Path

import pytest

from opus_config import TABLE_NAMES
from opus_config.template import TEMPLATE_NAME, template_text, write_template


def test_the_template_ships_inside_the_package() -> None:
    """It is read through ``importlib.resources``, so this fails if it is not in the wheel."""
    assert template_text().lstrip().startswith('#')


def test_the_template_holds_exactly_the_tables_the_loader_requires() -> None:
    """The template is valid TOML and names every table, placeholders and all.

    Every placeholder is inside a quoted string, so the file parses as it ships. That is
    what lets this compare its tables with `opus_config.TABLE_NAMES` and catch a table
    added to the schema and forgotten here.
    """
    assert tuple(tomllib.loads(template_text())) == TABLE_NAMES


def test_a_copy_is_written_where_it_was_asked_for(tmp_path: Path) -> None:
    """The copy is the packaged file, byte for byte."""
    written = write_template(tmp_path)

    assert written == tmp_path / TEMPLATE_NAME
    assert written.read_text(encoding='utf-8') == template_text()


def test_an_existing_copy_is_not_replaced(tmp_path: Path) -> None:
    """Refusing is the point: the file already there may be one somebody has edited."""
    (tmp_path / TEMPLATE_NAME).write_text('mine', encoding='utf-8')

    with pytest.raises(FileExistsError, match=TEMPLATE_NAME):
        write_template(tmp_path)

    assert (tmp_path / TEMPLATE_NAME).read_text(encoding='utf-8') == 'mine'


def test_force_replaces_it(tmp_path: Path) -> None:
    """Asking for it explicitly is how a stale copy is refreshed."""
    (tmp_path / TEMPLATE_NAME).write_text('mine', encoding='utf-8')

    write_template(tmp_path, force=True)

    assert (tmp_path / TEMPLATE_NAME).read_text(encoding='utf-8') == template_text()


def test_a_directory_that_is_not_one_is_refused(tmp_path: Path) -> None:
    """Naming a file, or a directory that does not exist, says so rather than failing later."""
    with pytest.raises(NotADirectoryError):
        write_template(tmp_path / 'absent')
