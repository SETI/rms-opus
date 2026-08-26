"""Write the checked-in display details back over the permanent ``mult_`` tables.

A ``mult_`` table holds the enumerated values one column can take, along with how the
web application should present them. Where a table schema pins those presentation
details in a ``mult_options`` entry, this step copies them over whatever the import
wrote, so that editing a schema is enough to change a label or a sort order without
re-importing.

The step runs only when ``--update-mult-info`` is given; nothing else calls it, and
``--do-it-all`` does not imply it.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from opus_import import import_util
from opus_import.import_util import MultOption

if TYPE_CHECKING:
    from opus_import.context import ImportContext


def update_mult_info(ctx: ImportContext) -> None:
    """Update every permanent ``mult_`` table whose schema pins its values.

    The table's name says which schema and which column it belongs to, so the name is
    split apart and matched against the packaged schemas. A table whose schema or column
    cannot be found is reported and skipped rather than aborting the run, and a column
    with no ``mult_options`` entry is left exactly as the import wrote it.

    Every presentation column a schema pins is written: the label, the sort key, whether
    the value is offered in the search form, the group it belongs to and that group's
    sort key. The value itself and the row id are not touched -- the id is what the
    ``obs_`` rows already reference, and the value is what a row means rather than how it
    is shown.

    Parameters:
        ctx: The import run's context, for the open database and the logger.

    Raises:
        TypeError: If a ``mult_options`` entry does not carry exactly the seven values
            `opus_import.import_util.MultOption` names. That is a fault in the packaged
            schema, and stopping is better than writing a row built from values that
            landed in the wrong columns.
    """
    db = ctx.db
    assert db is not None
    logger = ctx.logger

    # Find all the permanent mult_ tables
    table_names = db.table_names('perm', prefix='mult_')

    for table_name in table_names:
        # A mult table's name is its observation table's name joined to its column's,
        # and both halves contain underscores, so where the split falls has to be
        # decided by trying them. A table name alone is not enough to decide it: both
        # `obs_surface_geometry` and `obs_surface_geometry_name` are real tables, so
        # `mult_obs_surface_geometry_name_target_name` matches a schema at the shorter
        # split and only the longer one leaves a column that exists. The split is
        # therefore the one where the schema *and* the column both resolve.
        splits = table_name.split('_')
        table_schema = None
        column = None
        for n_splits in range(3, len(splits)):
            trial_name = '_'.join(splits[1:n_splits])
            trial_schema = import_util.read_schema_for_table(ctx, trial_name)
            if trial_schema is None:
                continue
            if table_schema is None:
                # Remembered so that a table whose column resolves nowhere is reported
                # against a schema that exists, rather than as an unknown table.
                table_schema = trial_schema
            mult_field_name = '_'.join(splits[n_splits:])
            for trial_column in trial_schema:
                if trial_column['field_name'] == mult_field_name:
                    table_schema, column = trial_schema, trial_column
                    break
            if column is not None:
                break
        if table_schema is None:
            logger.log('error',
                f'Unable to find table schema for mult "{table_name}"')
            continue
        if column is None:
            logger.log('error',
                f'Unable to find a column matching mult table "{table_name}"')
            continue

        mult_options = column.get('mult_options', False)
        if not mult_options:
            continue

        for mult_info in mult_options:
            option = MultOption(*mult_info)

            row_dict = {
                'label': str(option.label),
                'disp_order': option.disp_order,
                'display': option.display,
                'grouping': option.grouping,
                'group_disp_order': option.group_disp_order,
            }

            db.update_row('perm', table_name, row_dict,
                          f'{db.quote_identifier("id")}=%s',
                          where_params=[option.id])
