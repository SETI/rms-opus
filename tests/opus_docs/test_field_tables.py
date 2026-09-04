"""Tests for the API guide's metadata-field table generator.

The generator answers, from the packaged table schemas alone, the question the web
application answers from a populated database: which metadata fields exist, what they
are called, what units they take, and what an API call names them by. Nothing else in
the repository would notice if it stopped agreeing with the schemas, because the
documentation build has no database to check itself against -- so these tests run it
against the real packaged schemas and check the properties that make its output usable.
"""

from __future__ import annotations

import json
from typing import Any

import opus_field_tables
import pytest

from opus_import import import_util


@pytest.fixture(scope='module')
def rows() -> list[opus_field_tables.FieldRow]:
    """Return the table the generator builds from the packaged schemas."""
    return opus_field_tables.build_field_rows()


def _schema_fields() -> list[dict[str, Any]]:
    """Return every packaged column that carries a ``param_info`` category.

    This reads the schemas independently of the generator -- deliberately, so that a
    generator that silently dropped a category or a whole table would be caught rather
    than agreeing with itself.

    Returns:
        The column definitions, with the surface geometry template read as it is
        written, placeholders and all.
    """
    columns: list[dict[str, Any]] = []
    for entry in import_util.table_schema_files('obs_*.json'):
        for column in json.loads(entry.read_text(encoding='utf-8')):
            if column.get('pi_category_name') is not None:
                columns.append(column)
    return columns


def test_runs_against_the_packaged_schemas(rows: list[opus_field_tables.FieldRow]) -> None:
    """The generator produces a table from the schemas that ship in the package."""
    assert rows
    assert all(isinstance(row, opus_field_tables.FieldRow) for row in rows)


def test_describes_every_searchable_column(rows: list[opus_field_tables.FieldRow]) -> None:
    """Every column that becomes a param_info row is described, and nothing else.

    A column is left out only for one of the two reasons the application leaves it
    out: it names no field at all, or its field id marks it internal.
    """
    columns = _schema_fields()
    internal = [column for column in columns if (column.get('pi_slug') or '').startswith('**')]
    nameless = [
        column
        for column in columns
        if not column.get('pi_slug') and not column.get('pi_referred_slug')
    ]
    assert internal, 'the schemas should still carry internal fields to exclude'
    assert nameless, 'the schemas should still carry a definition-only column'
    assert len(rows) == len(columns) - len(internal) - len(nameless)


def test_field_ids_are_unique_within_a_category(rows: list[opus_field_tables.FieldRow]) -> None:
    """No category lists the same field id twice.

    A field id can appear in more than one category, because a category may carry a
    link to a field defined elsewhere -- an instrument's category offers the general
    observation duration, for instance. Such a row is labelled with the category the
    field really belongs to, in brackets, which is what tells a reader the two entries
    are one field. What must never happen is the same id twice in one category.
    """
    pairs = [(row.category, row.field_id) for row in rows]
    assert len(pairs) == len(set(pairs))

    repeated = {row.field_id for row in rows if [r.field_id for r in rows].count(row.field_id) > 1}
    assert repeated, 'the schemas should still carry linked fields'
    for field_id in repeated:
        labels = [row.label for row in rows if row.field_id == field_id]
        assert any('[' in label for label in labels), (
            f'{field_id} appears in several categories with no label saying where it is defined'
        )


def test_every_row_is_usable(rows: list[opus_field_tables.FieldRow]) -> None:
    """Every row carries a category, a label and a field id, with no placeholder left.

    ``<SLUGTARGET>`` and the collapsed target's own name are what a half-applied
    substitution would leave behind, and either would send a reader to a field id that
    does not exist.
    """
    for row in rows:
        assert row.category
        assert row.label
        assert row.field_id
        assert '<SLUGTARGET>' not in row.field_id
        assert opus_field_tables.COLLAPSED_SURFACE_GEO_TARGET not in row.field_id


def test_surface_geometry_is_collapsed_onto_one_target(
    rows: list[opus_field_tables.FieldRow],
) -> None:
    """The per-target surface geometry fields appear once, under ``<TARGET>``."""
    surface = [row for row in rows if row.field_id.startswith('SURFACEGEO')]
    assert surface
    assert all(row.field_id.startswith('SURFACEGEO<TARGET>') for row in surface)
    assert {row.category for row in surface} == {'<TARGET> Surface Geometry Constraints'}


def test_categories_are_contiguous_and_ordered(rows: list[opus_field_tables.FieldRow]) -> None:
    """Each category's rows are together, and General Constraints comes first.

    ``table_names`` decides the order, and a reader depends on a category not being
    split across the table.
    """
    seen: list[str] = []
    for row in rows:
        if not seen or seen[-1] != row.category:
            assert row.category not in seen, f'{row.category} appears twice'
            seen.append(row.category)
    assert seen[0] == 'General Constraints'


def test_units_come_from_the_form_type(rows: list[opus_field_tables.FieldRow]) -> None:
    """A field with units lists them, and the first one is the unit it is stored in."""
    by_id = {row.field_id: row for row in rows}
    # Observation duration is a range in seconds; the alternatives are what
    # opus_support offers for that unit id.
    duration = by_id['observationduration']
    assert duration.units[0] == 'seconds'
    assert 'milliseconds' in duration.units
    # A multiple-choice field has no units at all.
    assert by_id['planet'].units == ()


def test_writes_the_table_only_when_it_changes(tmp_path: Any) -> None:
    """The generated page is left alone when its content has not changed.

    Sphinx re-reads a source file whose modification time moved, so rewriting an
    identical table would make every build re-read the page that includes it.
    """
    destination = tmp_path / 'api_guide_fields_table.rst'
    count = opus_field_tables.write_field_table(destination)
    assert count > 0
    first = destination.stat().st_mtime_ns
    text = destination.read_text(encoding='utf-8')
    assert opus_field_tables.write_field_table(destination) == count
    assert destination.stat().st_mtime_ns == first
    assert destination.read_text(encoding='utf-8') == text


def test_renders_a_list_table(rows: list[opus_field_tables.FieldRow]) -> None:
    """The rendered table is a list-table with one entry per field."""
    text = opus_field_tables.render_field_table_rst(rows)
    assert '.. list-table::' in text
    assert text.count('   * - ') == len(rows) + 1  # the rows, plus the header
    # A field's units are shown under its label, separated by the line break the
    # documentation defines as |br|.
    assert '|br|' in text
