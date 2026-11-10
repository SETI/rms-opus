"""Build the ``param_info`` table, which describes every search parameter to the UI.

One row per searchable or displayable column: its label, its form type and unit, where it
belongs in the search form, and what the data dictionary calls it. The web application
reads nothing else to decide what the search form contains, so a column that has no
``param_info`` row is invisible to users no matter what the import wrote into it.

The rows are derived from the packaged table schemas of the ``obs_`` tables,
which is why this step has to run after the import rather than alongside it. The table is
built beside the live one and swapped in (`opus_import.table_swap`), so the step can run
on a schema that is being served.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

import opus_support
from opus_import import import_util, table_swap

if TYPE_CHECKING:
    from opus_import.context import ImportContext


def fill_param_info(ctx: ImportContext, new_table: str) -> bool:
    """Fill an empty ``param_info`` table from the ``obs_`` tables' schemas.

    Every column of every ``obs_`` table that carries a ``pi_category_name``
    contributes one row. A column's ``pi_ranges`` names an entry in the packaged
    ``param_info_ranges.json``, which is stored as JSON text in the row.

    Parameters:
        ctx: The import run's context, for the open database and the logger.
        new_table: The table to fill, already created from ``param_info``'s
            schema.

    Returns:
        True on success. False if a table's schema could not be read, a form type names
        a unit `opus_support` does not know, or a ``pi_ranges`` entry is missing -- each
        of which is logged as an error. The rows are written in one call at the end, so
        a failure leaves the table empty rather than partly built.

    Raises:
        json.JSONDecodeError: If ``param_info_ranges.json`` is not valid JSON.
    """
    db = ctx.db
    assert db is not None
    logger = ctx.logger

    logger.log('info', f'Filling {new_table}')

    # The obs_ tables that exist determine what goes into param_info
    table_names = db.table_names(prefix='obs_')

    # read json file for ranges info
    ranges_file = import_util.TABLE_SCHEMA_DIR / 'param_info_ranges.json'
    contents = ranges_file.read_text(encoding='utf-8')
    try:
        # convert the contents (str) to a json object (dict)
        ranges_json = json.loads(contents)
    except json.decoder.JSONDecodeError:
        logger.log('debug', f'Was reading ranges json file "{ranges_file}"')
        raise

    rows: list[dict[str, Any]] = []
    for table_name in table_names:
        table_schema = import_util.read_schema_for_table(ctx, table_name)
        if table_schema is None:
            logger.log('error', f'Unable to read table schema for "{table_name}"')
            return False
        for column in table_schema:
            category_name = column.get('pi_category_name', None)
            if category_name is None:
                continue
            field_name = column.get('field_name', None)
            form_type_str = column.get('pi_form_type', None)
            (_form_type, _form_type_format, form_type_unit_id) = opus_support.parse_form_type(
                form_type_str
            )
            if form_type_unit_id and not opus_support.is_valid_unit_id(form_type_unit_id):
                logger.log(
                    'error',
                    f'"{form_type_unit_id}" '
                    + f'in "{category_name}/{field_name}" is not '
                    + 'a valid unit',
                )
                return False
            # if pi_ranges exists in .json, get the corresponding ranges info
            # from dict and convert it to str before storing to database
            ranges = column.get('pi_ranges', None)
            if ranges:
                if ranges in ranges_json:
                    ranges = ranges_json[ranges]
                    ranges = json.dumps(ranges)
                else:
                    logger.log('error', f'pi_ranges: "{ranges}" is not in "{ranges_file}"')
                    return False

            new_row = {
                'category_name': category_name,
                'dict_context': column.get('pi_dict_context', None),
                'dict_name': column.get('pi_dict_name', None),
                'dict_context_results': column.get('pi_dict_context_results', None),
                'dict_name_results': column.get('pi_dict_name_results', None),
                'disp_order': column['pi_disp_order'],
                'display': column['pi_display'],
                'display_results': column['pi_display_results'],
                'referred_slug': column.get('pi_referred_slug', None),
                'form_type': column.get('pi_form_type', None),
                'intro': column.get('pi_intro', None),
                'label': column.get('pi_label', None),
                'label_results': column.get('pi_label_results', None),
                'name': column.get('field_name', None),
                'slug': column.get('pi_slug', None),
                'old_slug': column.get('pi_old_slug', None),
                'sub_heading': column.get('pi_sub_heading', None),
                'tooltip': column.get('pi_tooltip', None),
                'ranges': ranges,
                'field_hints1': column.get('pi_field_hints1', None),
                'field_hints2': column.get('pi_field_hints2', None),
            }
            rows.append(new_row)
    db.insert_rows(new_table, rows)

    return True


def do_param_info(ctx: ImportContext) -> bool:
    """Rebuild the ``param_info`` table, driven by ``--create-param-info``.

    A failed build leaves the live table as the previous run wrote it.

    Parameters:
        ctx: The import run's context, for the open database and the logger.

    Returns:
        True if the table was rebuilt, False if the build failed, having logged why.
    """
    new_name = table_swap.swap_new_name('param_info')
    return table_swap.rebuild_tables_by_swap(
        ctx, ['param_info'], lambda: fill_param_info(ctx, new_name)
    )
