"""Tests that keep the developer guide's factual claims about the schemas true.

These assert nothing the software needs; they exist because the "Table Schemas"
chapter states facts about `opus_import/table_schemas/` that no other gate checks, and
prose is invisible to every checker in this repository. A claim the build can compute
is one a later reader cannot find wrong.

Each test names the sentence it defends. If one fails, the schemas changed and the
chapter has to change with them -- that is the point, not an inconvenience.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from opus_import import import_util

#: The schema files the chapter says are not tables. It also says which two of them
#: are not even column lists.
NOT_TABLES = {
    'param_info_ranges.json',
    'mult_template.json',
    'obs_surface_geometry_target.json',
    'internal_def_product_types.json',
}
NOT_COLUMN_LISTS = {'param_info_ranges.json', 'internal_def_product_types.json'}


def _schema_dir() -> Path:
    """Return the packaged table_schemas directory.

    Returns:
        The directory the import pipeline reads its schemas from.
    """
    return Path(str(import_util.TABLE_SCHEMA_DIR))


def _schema_files() -> list[Path]:
    """Return every packaged JSON schema file.

    Returns:
        The files, sorted by name.
    """
    return sorted(_schema_dir().glob('*.json'))


def _defines_a_column(entry: dict[str, object]) -> bool:
    """Say whether one schema entry defines a SQL column.

    An entry carrying ``constraint`` contributes raw SQL instead of a column, and one
    carrying ``pi_referred_slug`` is a link to a field defined in another table -- the
    chapter says so, and `opus_import.importdb.mysql` skips both.

    Parameters:
        entry: The schema entry.

    Returns:
        True if the entry names a column of its own.
    """
    return 'field_name' in entry and 'pi_referred_slug' not in entry


def _is_a_link(entry: dict[str, object]) -> bool:
    """Say whether one schema entry is a constraint or a link rather than a column.

    Parameters:
        entry: The schema entry.

    Returns:
        True if the entry deliberately defines no column.
    """
    return 'constraint' in entry or 'pi_referred_slug' in entry


def test_tab_data_sources_exist_only_in_obs_files() -> None:
    """Defends: the ``TAB:`` values in ``obs_files.json`` are the only ones left.

    They are dead data -- `opus_import.steps.do_import_index` builds those rows from a
    literal -- and a ``TAB:`` written into any other schema would be reported as an
    unknown data source rather than doing anything.
    """
    carrying = {path.name for path in _schema_files() if 'TAB:' in path.read_text()}
    assert carrying == {'obs_files.json'}


def test_the_files_that_are_not_column_lists_are_exactly_these() -> None:
    """Defends: "Four files are not tables", and the two-of-four split."""
    not_a_list = set()
    names_no_columns = set()
    for path in _schema_files():
        data = json.loads(path.read_text())
        if not isinstance(data, list):
            not_a_list.add(path.name)
        elif not any(_defines_a_column(entry) for entry in data):
            names_no_columns.add(path.name)
    assert not_a_list | names_no_columns == NOT_COLUMN_LISTS
    # The other two are column lists, and are not tables for a reason no property of
    # the file itself can show -- which is why they are named rather than detected.
    assert NOT_COLUMN_LISTS < NOT_TABLES
    for name in NOT_TABLES - NOT_COLUMN_LISTS:
        assert (_schema_dir() / name).is_file()


def test_every_other_schema_is_a_list_of_columns() -> None:
    """Defends: "one JSON file per OPUS table ... a list of objects, one per column"."""
    for path in _schema_files():
        if path.name in NOT_TABLES:
            continue
        data = json.loads(path.read_text())
        assert isinstance(data, list), path.name
        assert data, path.name
        for entry in data:
            assert _defines_a_column(entry) or _is_a_link(entry), path.name


@pytest.mark.parametrize('key', ['data_source_order', 'pi_units'])
def test_the_keys_said_to_be_unread_are_present_and_unread(key: str) -> None:
    """Defends the "Keys nothing reads" list.

    Both halves matter: the chapter would be wrong if a key it names had been removed
    from the schemas, and wrong in a more misleading way if something started reading
    one. ``definition_results`` is deliberately not covered -- it is read as a computed
    key, which is the blind spot the chapter states.

    Parameters:
        key: The schema key the chapter claims nothing reads.
    """
    assert any(key in path.read_text() for path in _schema_files()), (
        f'{key} is no longer in any schema; the chapter should stop naming it')
    source = _schema_dir().parents[1]
    readers = [str(path) for path in source.rglob('*.py')
               if f"'{key}'" in path.read_text()]
    assert not readers, f'{key} is now read by {readers}; the chapter is out of date'
