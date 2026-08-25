"""Build the ``param_info`` table, which describes every search parameter to the UI.

One row per searchable or displayable column: its label, its form type and unit, where it
belongs in the search form, and what the data dictionary calls it. The web application
reads nothing else to decide what the search form contains, so a column that has no
``param_info`` row is invisible to users no matter what the import wrote into it.

The rows are derived from the packaged table schemas of the permanent ``obs_`` tables,
which is why this step has to run after the import rather than alongside it.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

import opus_support
from opus_import import import_util

if TYPE_CHECKING:
    from opus_import.context import ImportContext


def create_import_param_info_table(ctx: ImportContext) -> bool:
    """Fill the import ``param_info`` table from the permanent tables' schemas.

    Every column of every permanent ``obs_`` table that carries a ``pi_category_name``
    contributes one row. A column's ``pi_ranges`` names an entry in the packaged
    ``param_info_ranges.json``, which is stored as JSON text in the row.

    Parameters:
        ctx: The import run's context, for the open database and the logger.

    Returns:
        True on success. False if a table's schema could not be read, a form type names
        a unit `opus_support` does not know, or a ``pi_ranges`` entry is missing -- each
        of which is logged as an error, and leaves the import table partly built.

    Raises:
        json.decoder.JSONDecodeError: If ``param_info_ranges.json`` is not valid JSON.
    """
    db = ctx.db
    assert db is not None
    logger = ctx.logger

    logger.log('info', 'Creating new import param_info table')
    pi_schema = import_util.read_schema_for_table(ctx, 'param_info')
    # param_info.json is packaged with opus_import, so the schema is always found.
    assert pi_schema is not None
    # Start from scratch
    db.drop_table('import', 'param_info')
    db.create_table('import', 'param_info', pi_schema, ignore_if_exists=False)

    # We use the permanent tables to determine what goes into param_info
    table_names = db.table_names('perm', prefix='obs_')

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
            logger.log('error',
                       f'Unable to read table schema for "{table_name}"')
            return False
        for column in table_schema:
            category_name = column.get('pi_category_name', None)
            if category_name is None:
                continue
            field_name = column.get('field_name', None)
            form_type_str = column.get('pi_form_type', None)
            (_form_type, _form_type_format,
             form_type_unit_id) = opus_support.parse_form_type(form_type_str)
            if form_type_unit_id and not opus_support.is_valid_unit_id(form_type_unit_id):
                logger.log('error',
                           f'"{form_type_unit_id}" '
                           +f'in "{category_name}/{field_name}" is not '
                           +'a valid unit')
                return False
            # if pi_ranges exists in .json, get the corresponding ranges info
            # from dict and convert it to str before storing to database
            ranges = column.get('pi_ranges', None)
            if ranges:
                if ranges in ranges_json:
                    ranges = ranges_json[ranges]
                    ranges = json.dumps(ranges)
                else:
                    logger.log('error',
                               f'pi_ranges: "{ranges}" is not in "{ranges_file}"')
                    return False

            new_row = {
                'category_name': category_name,
                'dict_context': column.get('pi_dict_context', None),
                'dict_name': column.get('pi_dict_name', None),
                'dict_context_results': column.get('pi_dict_context_results',
                                                   None),
                'dict_name_results': column.get('pi_dict_name_results',
                                                None),
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
    db.insert_rows('import', 'param_info', rows)

    return True

def copy_param_info_from_import_to_permanent(ctx: ImportContext) -> None:
    """Replace the permanent ``param_info`` table with the import one.

    Parameters:
        ctx: The import run's context, for the open database and the logger.
    """
    db = ctx.db
    assert db is not None
    logger = ctx.logger

    logger.log('info', 'Copying param_info table from import to permanent')
    # Start from scratch
    pi_schema = import_util.read_schema_for_table(ctx, 'param_info')
    # param_info.json is packaged with opus_import, so the schema is always found.
    assert pi_schema is not None
    db.drop_table('perm', 'param_info')
    db.create_table('perm', 'param_info', pi_schema, ignore_if_exists=False)

    db.copy_rows_between_namespaces('import', 'perm', 'param_info')


def do_param_info(ctx: ImportContext) -> None:
    """Rebuild the permanent ``param_info`` table, driven by ``--create-param-info``.

    The import table is dropped either way, so a failed build leaves nothing behind; a
    failure also leaves the permanent table as the previous run wrote it.

    Parameters:
        ctx: The import run's context, for the open database and the logger.
    """
    if create_import_param_info_table(ctx):
        copy_param_info_from_import_to_permanent(ctx)
    assert ctx.db is not None
    ctx.db.drop_table('import', 'param_info')
