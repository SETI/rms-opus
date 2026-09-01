"""Tests for locating the data files that ship inside `opus_import`.

The table schemas and the PDS dictionary sources are package data, found through
importlib.resources rather than through a path relative to the caller. These tests pin
that: the files resolve from any working directory, and they are in a built wheel, so an
installed pipeline reads them out of site-packages with no checkout anywhere.
"""

from pathlib import Path

import pytest

from opus_import import import_util

from .conftest import make_context


def test_table_schema_dir_holds_the_schemas() -> None:
    """The packaged schema directory is present and holds the OPUS table schemas."""
    assert (import_util.TABLE_SCHEMA_DIR / 'obs_general.json').is_file()
    assert (import_util.TABLE_SCHEMA_DIR / 'param_info_ranges.json').is_file()


def test_dictionary_data_dir_holds_the_context_tree() -> None:
    """The packaged dictionary directory holds the one file `--import-dictionary` reads.

    The definitions themselves come from the table schemas; this directory supplies only
    the context tree they are filed under.
    """
    assert (import_util.DICTIONARY_DATA_DIR / 'contexts.csv').is_file()


def test_table_schema_files_matches_the_pattern() -> None:
    """The pattern is matched against the file name alone, prefix and suffix both."""
    names = [entry.name for entry in import_util.table_schema_files('obs*.json')]
    assert names, 'no obs schemas found'
    assert all(name.startswith('obs') for name in names)
    assert all(name.endswith('.json') for name in names)
    assert 'param_info.json' not in names
    # The directory also holds .txt and .md files that the pattern must not admit.
    assert 'obs_general_unused_telescopes.txt' not in names


def test_table_schema_files_is_sorted() -> None:
    """The result is ordered by name, so an import run does not depend on the file system."""
    names = [entry.name for entry in import_util.table_schema_files('*.json')]
    assert names == sorted(names)


def test_table_schema_files_returns_nothing_for_an_unmatched_pattern() -> None:
    """A pattern matching no file yields an empty list rather than raising."""
    assert import_util.table_schema_files('no_such_prefix*.json') == []


def test_read_schema_for_table_parses_a_schema() -> None:
    """A known table's schema is returned as the parsed JSON list of its columns."""
    schema = import_util.read_schema_for_table(make_context(), 'obs_general')
    assert isinstance(schema, list)
    assert any(column.get('field_name') == 'opus_id' for column in schema)


def test_read_schema_for_table_strips_the_import_prefix() -> None:
    """An import-table name resolves to the schema of the table it is a copy of."""
    assert import_util.read_schema_for_table(
        make_context(), 'imp_obs_general'
    ) == import_util.read_schema_for_table(make_context(), 'obs_general')


def test_read_schema_for_table_substitutes_the_surface_geometry_target() -> None:
    """A per-target surface geometry table gets the target substituted into its schema."""
    schema = import_util.read_schema_for_table(make_context(), 'obs_surface_geometry__saturn')
    assert schema is not None
    rendered = str(schema)
    assert '<TARGET>' not in rendered
    assert '<SLUGTARGET>' not in rendered
    assert 'saturn' in rendered


def test_read_schema_for_table_returns_none_for_an_unknown_table() -> None:
    """An unknown table is reported by returning None, not by raising."""
    assert import_util.read_schema_for_table(make_context(), 'no_such_table') is None


def test_schemas_are_found_from_any_working_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A schema resolves from a working directory unrelated to the package.

    The lookup goes through importlib.resources, so nothing about it depends on the
    caller's location. A path-relative lookup would return None here rather than fail,
    which is why this asserts on the result and not on an exception.
    """
    monkeypatch.chdir(tmp_path)
    assert import_util.read_schema_for_table(make_context(), 'obs_general') is not None
