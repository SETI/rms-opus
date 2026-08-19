"""Tests for locating the data files that ship inside `opus_import`.

The table schemas and the PDS dictionary sources used to be found through a relative
path and through settings pointing into a source checkout, so they were reachable only
from one working directory. These tests pin the replacement: the files are package data,
found through importlib.resources, wherever the process happens to be running.
"""

from pathlib import Path

import pytest

from opus_import import import_util


def test_table_schema_dir_holds_the_schemas() -> None:
    """The packaged schema directory is present and holds the OPUS table schemas."""
    assert (import_util.TABLE_SCHEMA_DIR / 'obs_general.json').is_file()
    assert (import_util.TABLE_SCHEMA_DIR / 'param_info_ranges.json').is_file()


def test_dictionary_data_dir_holds_the_pds_sources() -> None:
    """The packaged dictionary directory holds both files `--import-dictionary` reads."""
    assert (import_util.DICTIONARY_DATA_DIR / 'pdsdd.full').is_file()
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
    schema = import_util.read_schema_for_table('obs_general')
    assert isinstance(schema, list)
    assert any(column.get('field_name') == 'opus_id' for column in schema)


def test_read_schema_for_table_strips_the_import_prefix() -> None:
    """An import-table name resolves to the schema of the table it is a copy of."""
    assert (import_util.read_schema_for_table('imp_obs_general')
            == import_util.read_schema_for_table('obs_general'))


def test_read_schema_for_table_substitutes_the_surface_geometry_target() -> None:
    """A per-target surface geometry table gets the target substituted into its schema."""
    schema = import_util.read_schema_for_table('obs_surface_geometry__saturn')
    assert schema is not None
    rendered = str(schema)
    assert '<TARGET>' not in rendered
    assert '<SLUGTARGET>' not in rendered
    assert 'saturn' in rendered


def test_read_schema_for_table_returns_none_for_an_unknown_table() -> None:
    """An unknown table is reported by returning None, not by raising."""
    assert import_util.read_schema_for_table('no_such_table') is None


def test_schemas_are_found_from_any_working_directory(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """The schemas are package data, so they no longer have to be run from one directory.

    Before the pipeline became a package this lookup was a relative path, and running
    from anywhere but its own source directory silently returned None.
    """
    monkeypatch.chdir(tmp_path)
    assert import_util.read_schema_for_table('obs_general') is not None
