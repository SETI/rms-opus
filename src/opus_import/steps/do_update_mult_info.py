"""Write the checked-in display details back over the permanent ``mult_`` tables.

A ``mult_`` table holds the enumerated values one column can take, along with how the
web application should present them. Where a table schema pins those presentation
details in a ``mult_options`` entry, this step copies them over whatever the import
wrote, so that editing a schema is enough to change a label or a sort order without
re-importing.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from opus_import import import_util

if TYPE_CHECKING:
    from opus_import.context import ImportContext


def update_mult_info(ctx: ImportContext) -> None:
    """Update every permanent ``mult_`` table whose schema pins its values.

    The table's name says which schema and which column it belongs to, so the name is
    split apart and matched against the packaged schemas. A table whose schema or column
    cannot be found is reported and skipped rather than aborting the run, and a column
    with no ``mult_options`` entry is left exactly as the import wrote it.

    Parameters:
        ctx: The import run's context, for the open database and the logger.
    """
    db = ctx.db
    assert db is not None
    logger = ctx.logger

    # Find all the permanent mult_ tables
    table_names = db.table_names('perm', prefix='mult_')

    for table_name in table_names:
        # Try to figure out what the table name is
        splits = table_name.split('_')
        table_schema = None
        for n_splits in range(3, 6):
            # Covers mult_obs_general to mult_obs_mission_new_horizons
            trial_name = '_'.join(splits[1:n_splits])
            table_schema = import_util.read_schema_for_table(ctx, trial_name)
            if table_schema is not None:
                break
        if table_schema is None:
            logger.log('error',
                f'Unable to find table schema for mult "{table_name}"')
            continue
        mult_field_name = '_'.join(splits[n_splits:])
        for column in table_schema:
            field_name = column['field_name']
            if field_name == mult_field_name:
                break
        else:
            logger.log('error',
        f'Unable to find field "{mult_field_name}" in table "{table_name}"')
            continue

        mult_options = column.get('mult_options', False)
        if not mult_options:
            continue

        for mult_info in mult_options:
            id_num, _value, label, disp_order, display, _definition = mult_info

            row_dict = {
                'label': str(label),
                'disp_order': disp_order,
                'display': display
            }

            db.update_row('perm', table_name, row_dict,
                          f'{db.quote_identifier("id")}=%s',
                          where_params=[id_num])
