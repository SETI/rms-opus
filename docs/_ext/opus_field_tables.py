"""Build the API guide's metadata-field table from the packaged table schemas.

The public API guide ends with a table of every searchable and displayable metadata
field: the category it belongs to, the label a result carries, the units its values may
be requested in, and the field id an API call names it by. The web application renders
that table from the ``param_info`` table, which only a completed import populates. This
module answers the same question from ``opus_import/table_schemas/*.json`` instead, so
the documentation build needs neither a database nor PDS holdings.

The schemas hold the same ``pi_*`` metadata `opus_import.steps.do_param_info` writes
into ``param_info``, and the category names and their order come from
`opus_import.steps.do_table_names.build_table_names_rows`, which is what fills
``table_names``. The remaining rules -- which columns are listed, how a linked field is
labelled, and how the per-target surface geometry categories are collapsed -- follow
`opus_app.apps.metadata.views.get_fields_info`, which is what the application renders
the table from.

`setup` registers this module as a Sphinx extension: it writes the table into the
documentation source tree before each build.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any, NamedTuple

from opus_import import import_util
from opus_import.steps.do_table_names import build_table_names_rows
from opus_support import get_valid_units, parse_form_type

if TYPE_CHECKING:
    from pathlib import Path

    from sphinx.application import Sphinx

#: The one surface geometry target the guide's table describes.
#:
#: A separate set of surface geometry fields exists for every target OPUS has geometry
#: for, and they differ only in the target's name. ``get_fields_info`` collapses them
#: onto a single target and prints ``<TARGET>`` where its name would go, reaching for
#: Saturn because every OPUS database has Saturn geometry in it. This generator drives
#: the same collapse from the same target so that the table it writes says what the
#: application says.
COLLAPSED_SURFACE_GEO_TARGET = 'saturn'

#: The table the collapsed surface geometry fields are read from.
COLLAPSED_SURFACE_GEO_TABLE = f'obs_surface_geometry__{COLLAPSED_SURFACE_GEO_TARGET}'

#: Schemas that define no permanent ``obs_`` table of their own.
#:
#: ``obs_surface_geometry_target`` is the template every per-target surface geometry
#: table is made from rather than a table, and is read under
#: `COLLAPSED_SURFACE_GEO_TABLE` instead.
_TEMPLATE_SCHEMAS = frozenset({'obs_surface_geometry_target'})

#: The suffixes that turn a category label into the name a linked field is qualified
#: with, as ``body_qualified_label_results`` in ``opus_app.apps.paraminfo.models``
#: strips them.
_CATEGORY_LABEL_SUFFIXES = (' Surface Geometry Constraints', ' Geometry Constraints',
                            ' Mission Constraints', ' Constraints')


class FieldRow(NamedTuple):
    """One row of the API guide's metadata-field table.

    Attributes:
        category: The label of the "Constraints" category the field belongs to.
        label: The label a result carries for the field.
        units: The units the field's values may be requested in, in the order the
            application offers them, or an empty tuple for a field with no units.
        field_id: The name an API call refers to the field by.
    """

    category: str
    label: str
    units: tuple[str, ...]
    field_id: str


def _packaged_obs_table_names() -> list[str]:
    """Return the permanent ``obs_`` tables the packaged schemas define.

    Returns:
        One name per ``obs_*.json`` schema that defines a table of its own, plus
        `COLLAPSED_SURFACE_GEO_TABLE` in place of the per-target template.
    """
    names = [entry.name.removesuffix('.json')
             for entry in import_util.table_schema_files('obs_*.json')]
    names = [name for name in names if name not in _TEMPLATE_SCHEMAS]
    names.append(COLLAPSED_SURFACE_GEO_TABLE)
    return names


def _read_schema(table_name: str) -> list[dict[str, Any]]:
    """Read one table's packaged schema, with the surface geometry target substituted.

    This is `opus_import.import_util.read_schema_for_table` without the parts that
    need an import run: no configuration is read and nothing is logged.

    Parameters:
        table_name: The permanent table whose schema to read.

    Returns:
        The column definitions in the order the schema lists them.
    """
    replace: list[tuple[str, str]] = []
    if table_name.startswith('obs_surface_geometry__'):
        target_name = table_name.removeprefix('obs_surface_geometry__')
        table_name = 'obs_surface_geometry_target'
        replace = [('<TARGET>', import_util.table_name_for_sfc_target(target_name)),
                   ('<SLUGTARGET>', import_util.slug_name_for_sfc_target(target_name))]
    contents = (import_util.TABLE_SCHEMA_DIR /
                (table_name+'.json')).read_text(encoding='utf-8')
    for old, new in replace:
        contents = contents.replace(old, new)
    schema: list[dict[str, Any]] = json.loads(contents)
    return schema


def _collapse_category(label: str) -> str:
    """Replace the collapsed target's name in a category label with ``<TARGET>``.

    Parameters:
        label: A category label.

    Returns:
        The label with the target's capitalized name replaced by ``<TARGET>``.
    """
    return label.replace(COLLAPSED_SURFACE_GEO_TARGET.title(), '<TARGET>')


def _collapse_field_id(field_id: str) -> str:
    """Replace the collapsed target's name in a field id with ``<TARGET>``.

    Parameters:
        field_id: A field id.

    Returns:
        The field id with the target's lower-case name replaced by ``<TARGET>``.
    """
    return field_id.replace(COLLAPSED_SURFACE_GEO_TARGET, '<TARGET>')


def _units_for(form_type: str | None) -> tuple[str, ...]:
    """Return the units a field's values may be requested in.

    Parameters:
        form_type: The column's ``pi_form_type``, which names a unit system after a
            ``:``.

    Returns:
        The unit names in the order the application offers them, empty for a form
        type that names no unit system.
    """
    _form_type, _form_type_format, unit_id = parse_form_type(form_type)
    return tuple(get_valid_units(unit_id) or ())


def _results_label(column: dict[str, Any]) -> str:
    """Return the label a result carries for one column.

    ``pi_label_results`` is nullable and one shipping column leaves it unset, which
    the application's own table renders as the literal text ``None``. The search
    label stands in for it here, which is the same name under a different heading.

    Parameters:
        column: The column's schema entry.

    Returns:
        The results label, or the search label where the schema has no results label.
    """
    label: str | None = column.get('pi_label_results') or column.get('pi_label')
    assert label is not None, f'{column["pi_slug"]} has neither label'
    return label


def _qualified_label(label: str, category_label: str) -> str:
    """Return a linked field's label with the category it really belongs to appended.

    A field that only links to another one is labelled with the name of the category
    the field it links to lives in, so that a reader can tell the two apart. This is
    ``body_qualified_label_results(referred=True)``: reaching a field through another
    field's referred slug qualifies its label even in the categories that are
    otherwise left alone.

    Parameters:
        label: The referred field's own results label.
        category_label: The label of the category the referred field belongs to.

    Returns:
        The label with ``[<category>]`` appended, unless it carries that already.
    """
    name = category_label
    for suffix in _CATEGORY_LABEL_SUFFIXES:
        name = name.replace(suffix, '')
    if f'[{name}]' in label:
        return label
    return f'{label} [{name}]'


def _sort_key(column: dict[str, Any], table_name: str) -> tuple[Any, ...]:
    """Return the position a column takes within its category.

    ``get_fields_info`` sorts each category's fields by display order, stably, over a
    dictionary already in ``ParamInfo`` order -- which its model's ``Meta.ordering``
    makes ``(category_name, sub_heading, disp_order)``. So a display order shared by
    two fields is broken first by their category and then by their sub-heading, both
    ascending, with an absent sub-heading first as SQL sorts NULL.

    Parameters:
        column: The column's schema entry.
        table_name: The table the column belongs to, which is its category name.

    Returns:
        The sort key.
    """
    sub_heading = column.get('pi_sub_heading')
    return (column['pi_disp_order'], table_name,
            sub_heading is not None, sub_heading or '')


def build_field_rows() -> list[FieldRow]:
    """Describe every metadata field the API guide's table lists.

    Returns:
        The rows in the order the guide shows them: categories in the order
        ``table_names`` gives them, and each category's fields in display order.
    """
    table_names = _packaged_obs_table_names()
    ordered_tables = build_table_names_rows(
        table_names.__contains__,
        [name for name in table_names if name.startswith('obs_surface_geometry__')])
    label_by_table = {row['table_name']: row['label'] for row in ordered_tables}

    # Every column carrying a param_info category, indexed so that a pi_referred_slug
    # can be resolved to the field it names -- by current slug first and then by old
    # slug, which is the order get_param_info_by_slug looks them up in.
    columns_by_table: dict[str, list[dict[str, Any]]] = {}
    by_slug: dict[str, tuple[dict[str, Any], str]] = {}
    by_old_slug: dict[str, tuple[dict[str, Any], str]] = {}
    for table_name in label_by_table:
        columns = [column for column in _read_schema(table_name)
                   if column.get('pi_category_name') is not None]
        columns_by_table[table_name] = columns
        for column in columns:
            if column.get('pi_slug'):
                by_slug.setdefault(column['pi_slug'], (column, table_name))
            if column.get('pi_old_slug'):
                by_old_slug.setdefault(column['pi_old_slug'], (column, table_name))

    # Two tables share the label "Surface Geometry Constraints", and the guide shows
    # their fields as one category, so the grouping is by label rather than by table.
    # A shared category takes the display position of whichever of its tables comes
    # last in ParamInfo order, which is the alphabetically last category name.
    entries: dict[str, list[tuple[tuple[Any, ...], FieldRow]]] = {}
    position: dict[str, int] = {}
    for table_row in sorted(ordered_tables, key=lambda row: row['table_name']):
        table_name = table_row['table_name']
        category_label = _collapse_category(table_row['label'])
        position[category_label] = table_row['disp_order']
        group = entries.setdefault(category_label, [])
        for column in columns_by_table[table_name]:
            slug = column.get('pi_slug')
            if not slug:
                referred = column.get('pi_referred_slug')
                if not referred:
                    # A column with neither is not a search field: it contributes
                    # only a definition to the data dictionary.
                    continue
                referred_column, referred_table = (by_slug.get(referred) or
                                                   by_old_slug[referred])
                label = _qualified_label(_results_label(referred_column),
                                         label_by_table[referred_table])
                units = _units_for(referred_column.get('pi_form_type'))
                slug = referred_column['pi_slug']
            elif slug.startswith('**'):
                # Internal use only; the guide does not list it.
                continue
            else:
                label = _results_label(column)
                units = _units_for(column.get('pi_form_type'))
            group.append((_sort_key(column, table_name),
                          FieldRow(category_label, label, units,
                                   _collapse_field_id(slug))))

    rows: list[FieldRow] = []
    for category_label in sorted(entries, key=lambda label: position[label]):
        rows.extend(row for _key, row in sorted(entries[category_label],
                                                key=lambda entry: entry[0]))
    return rows


def render_field_table_rst(rows: list[FieldRow]) -> str:
    """Render the metadata-field rows as a reStructuredText list table.

    Parameters:
        rows: The rows to render, in the order they should appear.

    Returns:
        The table as reStructuredText, headed by a comment saying it is generated.
    """
    lines = ['.. Written by docs/_ext/opus_field_tables.py at build time. Change the',
             '   generator, or the table schemas it reads, rather than this file.',
             '',
             '.. list-table::',
             '   :header-rows: 1',
             '   :widths: 25 45 30',
             '',
             '   * - Category',
             '     - Label and units',
             '     - Field ID']
    for row in rows:
        label = row.label
        if row.units:
            label = f'{label} |br| {", ".join(row.units)}'
        lines += [f'   * - {row.category}',
                  f'     - {label}',
                  f'     - ``{row.field_id}``']
    lines.append('')
    return '\n'.join(lines)


def write_field_table(destination: Path) -> int:
    """Write the metadata-field table into the documentation source tree.

    The file is rewritten only when its content changes, so an unchanged table does
    not make Sphinx re-read the page including it.

    Parameters:
        destination: The reStructuredText file to write.

    Returns:
        The number of fields described.
    """
    rows = build_field_rows()
    text = render_field_table_rst(rows)
    if not destination.is_file() or destination.read_text(encoding='utf-8') != text:
        destination.write_text(text, encoding='utf-8')
    return len(rows)


def setup(app: Sphinx) -> dict[str, Any]:
    """Register this module as a Sphinx extension.

    Parameters:
        app: The Sphinx application being configured.

    Returns:
        The extension metadata Sphinx expects, declaring the extension safe for both
        the parallel read and the parallel write phase.
    """
    write_field_table(app.srcdir / 'api_guide_fields_table.rst')
    return {'parallel_read_safe': True, 'parallel_write_safe': True}
