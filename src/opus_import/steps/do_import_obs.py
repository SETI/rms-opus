"""Compute one row of one observation table by calling the obs class field functions.

A table's schema names, for each column, where its value comes from: a Python method on
the bundle's obs class (``COMPUTE``), the ``obs_general`` row this observation already
produced, one of two longitude computations, or the next id in sequence. This module
walks the schema, obtains each value, checks it against the type and range the schema
declares, replaces an enumerated value with its ``mult_`` table id, and assembles the
row.

Validation reports rather than raises, so one bad row does not end the run: a flag with
an unrecognized spelling and a number that does not parse both become NULL and log an
error, while a ``char`` column keeps a value of the right type by truncating an
over-long one and substituting an empty string for one that is not a string. Logging an
error is what marks the import as having produced bad data, so the run fails at the end.

A value outside the column's declared range is the exception, and which way it goes is
the schema's choice: it becomes NULL either way, but a column carrying
``val_set_invalid_to_null`` logs at **debug** rather than error, so out-of-range values
in that column are discarded silently and the run still succeeds.

These are the per-observation internals of `opus_import.steps.do_import`, not a step of
their own.
"""

from __future__ import annotations

import json
import traceback
from typing import TYPE_CHECKING, Any

from opus_import import config_data, import_util
from opus_import.obs.obs_base import ObsBase
from opus_import.obs.obs_ring_geometry import ObsRingGeometry
from opus_import.obs.obs_surface_geometry_target import ObsSurfaceGeometryTarget
from opus_import.steps import do_import_mult

if TYPE_CHECKING:
    from opus_import.context import ImportContext
    from opus_import.import_util import TableSchema


def import_observation_table(ctx: ImportContext, instrument_obj: ObsBase,
                             table_name: str,
                             table_schema: TableSchema,
                             metadata: dict[str, Any]) -> dict[str, Any] | None:
    """Compute one observation's row of one table.

    Three kinds of column are skipped: ``timestamp``, which the database maintains
    itself; a column marked ``put_mults_here``, which holds another column's mult id;
    and a ``pi_referred_slug`` entry, which describes a search parameter rather than a
    column.

    A column whose form type is a GROUP type stores a ``mult_`` table id rather than the
    value, and the value is added to that table if it is new. A ``mult_list`` column
    holds several values and is written as a JSON array, with a missing value omitted
    rather than stored as null; every other column holds exactly one value.

    The row is left on ``metadata`` under ``<table_name>_row`` as well as returned, so
    that a later table's field functions can read what an earlier one computed.

    Parameters:
        ctx: The import run's context.
        instrument_obj: The obs class instance for this bundle, whose
            ``field_<table>_<column>`` methods compute the ``COMPUTE`` columns.
        table_name: The table being filled.
        table_schema: That table's column definitions.
        metadata: What the import has computed for this observation so far, added to
            here.

    Returns:
        The row, keyed by column name, or None if a mult column's field function
        returned something that is not a mult specification, which is not recoverable.
    """
    new_row: dict[str, Any] = {}

    metadata[table_name+'_row'] = new_row

    # Run through all the based columns and compute their values.
    # Always skip "id" for tables other than obs_general, because this is just
    # an AUTO_INCREMENT field used by Django and has no other purpose.
    # Always skip "timestamp" fields because these are automatically filled in
    # by SQL because we mark them as ON CREATE and ON UPDATE.
    # Skip "mult_" tables because they are handled separately when the search
    # type is a GROUP-type.

    for table_column in table_schema:
        if (table_column.get('put_mults_here', False) or
            table_column.get('pi_referred_slug', False)):
            continue
        field_name = table_column['field_name']
        field_type = table_column['field_type']

        metadata['table_name'] = table_name
        metadata['field_name'] = field_name

        if field_name == 'timestamp':
            continue

        data_source = table_column.get('data_source', None)
        if not data_source:
            import_util.log_nonrepeating_warning(
                ctx,
                f'No data source for column "{field_name}" in table '+
                f'"{table_name}"')
            column_val_list: list[Any] | None = []
        else:
            ### COMPUTE THE NEW COLUMN VALUE ###

            column_val_list = None
            mult_label_list: list[Any] | None = None
            aliases_list: list[Any] | None = None
            disp_list: list[Any] | None = None
            # Might be set with mult_label but not otherwise
            disp_order_list: list[Any] | None = None
            grouping_list: list[Any] | None = None
            group_disp_order_list: list[Any] | None = None

            if data_source == 'OBS_GENERAL_ID':
                obs_general_row = metadata['obs_general_row']
                column_val_list = [import_util.safe_column(obs_general_row, 'id')]

            elif data_source == 'COMPUTE':
                ok, ret = import_run_field_function(ctx, instrument_obj,
                                                    table_name,
                                                    table_schema,
                                                    metadata,
                                                    field_name)
                if ok:
                    # For a mult_list field, it's OK to return a single value, just to
                    # make the populate_ code simpler. In that case we turn it into a
                    # single-element list.
                    # Note that if one return value is a dict (full-spec mult field) then
                    # they all have to be.
                    if not isinstance(ret, (list, tuple)):
                        ret = [ret]
                    if isinstance(ret[0], dict):
                        column_val_list = [x['col_val'] for x in ret]
                        mult_label_list = [x['disp_name'] for x in ret]
                        aliases_list = [x['aliases'] for x in ret]
                        disp_list = [x['disp'] for x in ret]
                        disp_order_list = [x['disp_order'] for x in ret]
                        grouping_list = [x['grouping'] for x in ret]
                        group_disp_order_list = [x['group_disp_order'] for x in ret]
                    else:
                        column_val_list = ret
                else:
                    # Error will already be logged by import_run_field_function
                    column_val_list = [None]

            elif data_source == 'LONGITUDE_FIELD':
                column_val_list = [instrument_obj.compute_longitude_field()]

            elif data_source == 'D_LONGITUDE_FIELD':
                column_val_list = [instrument_obj.compute_d_longitude_field()]

            elif data_source == 'MAX_ID':
                if table_name not in ctx.max_table_id_cache:
                    ctx.max_table_id_cache[table_name] = (
                        import_util.find_max_table_id(ctx, table_name))
                ctx.max_table_id_cache[table_name] = (
                    ctx.max_table_id_cache[table_name]+1)
                column_val_list = [ctx.max_table_id_cache[table_name]]

            else:
                import_util.log_nonrepeating_error(
                    ctx,
                    f'Unknown data_source type "{data_source}" for '+
                    f'"{field_name}" in table "{table_name}"')

        ### VALIDATE THE COLUMN VALUE ###

        if column_val_list is None:
            # Only the unknown-data_source branch above leaves this unset, and it has
            # already logged the schema fault. Raising here rather than asserting keeps
            # the diagnostic under `python -O`, and this is control flow -- whether the
            # variable got a value at all -- not an internal invariant.
            raise ValueError(
                f'No value computed for column "{field_name}" in table "{table_name}": '
                f'unknown data_source "{data_source}"')

        # For a mult_list field, the column_val_list contains a list of column_vals.
        # Otherwise it contains a list with a single entry for the single value.
        assert field_type == 'mult_list' or len(column_val_list) == 1

        row_val: list[Any] = []

        for column_val_num, column_val in enumerate(column_val_list):
            if column_val is None:
                notnull = table_column.get('field_notnull', False)
                if notnull:
                    import_util.log_nonrepeating_error(
                        ctx,
                        f'Column "{field_name}" in table "{table_name}" '+
                        'has NULL value but NOT NULL is set')
            else:
                if field_type.startswith('flag'):
                    if column_val in [0, 'n', 'N', 'no', 'No', 'NO', 'off', 'OFF']:
                        if field_type == 'flag_onoff':
                            column_val = 'Off'
                        else:
                            column_val = 'No'
                    elif column_val in [1, 'y', 'Y', 'yes', 'Yes', 'YES', 'on', 'ON']:
                        if field_type == 'flag_onoff':
                            column_val = 'On'
                        else:
                            column_val = 'Yes'
                    elif column_val in ['N/A', 'UNK', 'NULL']:
                        column_val = None
                    else:
                        import_util.log_nonrepeating_error(
                            ctx,
                            f'Column "{field_name}" in table "{table_name}" '+
                            f'has FLAG type but value "{column_val}" is not '+
                            'a valid flag value')
                        column_val = None
                if field_type.startswith('char'):
                    field_size = int(field_type[4:])
                    if not isinstance(column_val, str):
                        import_util.log_nonrepeating_error(
                            ctx,
                            f'Column "{field_name}" in table "{table_name}" '+
                            f'has CHAR type but value "{column_val}" is of '+
                            f'type "{type(column_val)}"')
                        column_val = ''
                    elif len(column_val) > field_size:
                        import_util.log_nonrepeating_error(
                            ctx,
                            f'Column "{field_name}" in table "{table_name}" '+
                            f'has CHAR size {field_size} but value '+
                            f'"{column_val}" is too long')
                        column_val = column_val[:field_size]
                elif (field_type.startswith('real') or
                      field_type.startswith('int') or
                      field_type.startswith('uint')):
                    the_val = None
                    if field_type.startswith('real'):
                        try:
                            the_val = float(column_val)
                        except ValueError:
                            import_util.log_nonrepeating_error(
                                ctx,
                                f'Column "{field_name}" in table '+
                                f'"{table_name}" has REAL type but '+
                                f'"{column_val}" is not a float')
                            column_val = None
                    else:
                        try:
                            the_val = int(column_val)
                        except ValueError:
                            import_util.log_nonrepeating_error(
                                ctx,
                                f'Column "{field_name}" in table '+
                                f'"{table_name}" has INT type but '+
                                f'"{column_val}" is not an int')
                            column_val = None
                    if column_val is not None and the_val is not None:
                        val_sentinel = table_column.get('val_sentinel', None)
                        if not isinstance(val_sentinel, list):
                            val_sentinel = [val_sentinel]
                        if the_val in val_sentinel:
                            column_val = None
                            import_util.log_nonrepeating_error(
                                ctx,
                                f'Caught sentinel value {the_val} for column '+
                                f'"{field_name}" that was missed'+
                                ' by the PDS label!')
                    if column_val is not None and the_val is not None:
                        val_min = table_column.get('val_min', None)
                        val_max = table_column.get('val_max', None)
                        val_use_null = table_column.get('val_set_invalid_to_null',
                                                        False)
                        if val_min is not None and the_val < val_min:
                            if val_use_null:
                                msg = (f'Column "{field_name}" in table '+
                                       f'"{table_name}" has minimum value '+
                                       f'{val_min} but {column_val} is too small -'+
                                       ' substituting NULL')
                                import_util.log_debug(ctx, msg)
                            else:
                                msg = (f'Column "{field_name}" in table '+
                                       f'"{table_name}" has minimum value '+
                                       f'{val_min} but {column_val} is too small')
                                import_util.log_nonrepeating_error(ctx, msg)
                            column_val = None
                        if val_max is not None and the_val > val_max:
                            if val_use_null:
                                msg = (f'Column "{field_name}" in table '+
                                       f'"{table_name}" has maximum value {val_max}'+
                                       f' but {column_val} is too large - '+
                                       'substituting NULL')
                                import_util.log_debug(ctx, msg)
                            else:
                                msg = (f'Column "{field_name}" in table '+
                                       f'"{table_name}" has maximum value '+
                                       f'{val_max} but {column_val} is too large')
                                import_util.log_nonrepeating_error(ctx, msg)
                            column_val = None

            ### CHECK TO SEE IF THERE IS AN ASSOCIATED MULT_ TABLE ###

            form_type = table_column.get('pi_form_type', None)
            if form_type is not None and form_type.find(':') != -1:
                form_type = form_type[:form_type.find(':')]
            if form_type in config_data.GROUP_FORM_TYPES:
                # Handle the case when display value is not set. This stays here because
                # mult_label gets updated based on column_val after column_val is validated.
                # (ex: flag)
                mult_label = None
                if mult_label_list is None:
                    import_util.log_nonrepeating_error(
                        ctx,
                        f'Fatal error processing column "{field_name}" in '
                        f'table "{table_name}" - bad data type returned for mult'
                    )
                    return None
                # The seven lists are assigned together in the full-spec mult branch
                # above, so the check just made establishes the other five as well.
                assert aliases_list is not None
                assert disp_list is not None
                assert disp_order_list is not None
                assert grouping_list is not None
                assert group_disp_order_list is not None
                mult_label = mult_label_list[column_val_num]
                if mult_label is None:
                    if column_val is None:
                        mult_label = 'N/A'
                    else:
                        mult_label = str(column_val)
                        if (not mult_label[0].isdigit() or
                            not mult_label[-1].isdigit()):
                            # This catches things like 2014 MU69 and leaves them
                            # in all caps
                            mult_label = mult_label.title()

                column_val = do_import_mult.update_mult_table(
                              ctx, table_name, field_name, table_column,
                              column_val, mult_label,
                              aliases_list[column_val_num],
                              disp_list[column_val_num],
                              disp_order_list[column_val_num],
                              grouping_list[column_val_num],
                              group_disp_order_list[column_val_num])

            if field_type != 'mult_list' or column_val is not None:
                # When making a list for a mult_list field, don't include None
                # results because then we end up with a weird list like
                # ['SATURN', None, 'S RINGS'] which doesn't convert to JSON
                # propertly.
                row_val.append(column_val)

        if field_type == 'mult_list':
            # An empty list corresponds to a NULL database field
            if len(row_val) == 0:
                new_row[field_name] = None
            else:
                new_row[field_name] = json.dumps(row_val)
        else:
            new_row[field_name] = row_val[0] # Only a single value

    if not ctx.args.import_ignore_geo_mismatch:
        if table_name == 'obs_ring_geometry':
            # A geometry table is only ever filled by a class that mixes in the module
            # defining it, which every class in config_bundle_info does.
            assert isinstance(instrument_obj, ObsRingGeometry)
            instrument_obj.validate_ring_geo_fields(new_row, metadata)
        elif table_name.startswith('obs_surface_geometry__'):
            assert isinstance(instrument_obj, ObsSurfaceGeometryTarget)
            instrument_obj.validate_surface_geo_fields(new_row, metadata, table_name)

    return new_row

def field_function_name(table_name: str, field_name: str) -> str:
    """Return the name of the obs method that computes one column.

    This is the pipeline's only rule for finding a field method, so a method whose name
    it cannot produce is a method that is never called.
    ``tests/opus_import/test_obs_field_annotations.py`` resolves the hierarchy against
    the schemas through this function rather than restating it, so that changing the
    rule here changes what that test checks.

    Parameters:
        table_name: The table being filled. Every ``obs_surface_geometry__<TARGET>``
            table shares the methods named for ``obs_surface_geometry_target``, since
            they are all built from that one template.
        field_name: The column being computed.

    Returns:
        The method name, such as ``field_obs_general_opus_id``.
    """
    if table_name.startswith('obs_surface_geometry__'):
        table_name = 'obs_surface_geometry_target'
    return 'field_'+table_name+'_'+field_name

def import_run_field_function(ctx: ImportContext, instrument_obj: ObsBase,
                              table_name: str, table_schema: TableSchema,
                              metadata: dict[str, Any],
                              field_name: str) -> tuple[bool, Any]:
    """Call the obs class method that computes one column's value.

    The method is named ``field_<table>_<column>``, and every
    ``obs_surface_geometry__<TARGET>`` table shares the one named for
    ``obs_surface_geometry_target``, since they are all built from that template.

    Parameters:
        ctx: The import run's context, for the logger.
        instrument_obj: The obs class instance for this bundle.
        table_name: The table being filled.
        table_schema: That table's column definitions. Not read here: a field function
            takes what it needs off the obs instance.
        metadata: What the import has computed for this observation so far. Not read
            here, for the same reason.
        field_name: The column being computed.

    Returns:
        Whether the call succeeded, and what it returned. On failure the value is None
        and the reason -- no such method, or an exception with its traceback -- has been
        logged as an error.
    """
    func_name = field_function_name(table_name, field_name)
    if (not hasattr(instrument_obj, func_name) or
        not callable(func := getattr(instrument_obj, func_name))):
        class_name = type(instrument_obj).__name__
        import_util.log_nonrepeating_error(
            ctx,
            f'Unknown table field func "{class_name}::{func_name}"')
        return (False, None)
    try:
        res = func()
    except Exception:
        tb = traceback.format_exc()
        class_name = type(instrument_obj).__name__
        import_util.log_nonrepeating_error(
            ctx,
            f'Execution of field function {class_name}::{func_name} failed with '
            f'exception:\n{tb}')
        return False, None
    return (True, res)
