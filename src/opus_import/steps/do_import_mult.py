"""Read, cache and write the ``mult_`` tables holding the ``obs_`` columns' values.

A column whose values come from a fixed set stores a row id into a ``mult_`` table
rather than the value itself, and that table carries how the web application should
present each value: its label, its sort key, whether it is displayed, and which group it
belongs to. A value the import has never seen before is appended to the table as it is
encountered, which is why the tables are built alongside the observations rather than
ahead of them.

Every table is read once per bundle into `opus_import.context.ImportContext`'s cache and
written back at the end of the bundle, so importing an index of a hundred thousand rows
does not query for the same enumeration a hundred thousand times.

These are the mult-handling internals of `opus_import.steps.do_import`, not a step of
their own.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import opus_support
from opus_import import import_util

if TYPE_CHECKING:
    from collections.abc import Sequence

    from opus_import.context import ImportContext
    from opus_import.importdb.super import Namespace

MultRow = dict[str, Any]
"""One row of a ``mult_`` table: a value, its id, and how it is presented."""


def _mult_table_column_names() -> list[str]:
    """Return the list of columns every mult table has.

    Every mult table has the same columns, the grouping pair included; they are not
    added for the ``*_target_name`` tables alone.

    Returns:
        The column names, in the order the tables are read and written in.
    """

    return [
        'id',
        'value',
        'label',
        'disp_order',
        'display',
        'grouping',
        'group_disp_order',
        'aliases',
    ]


def _convert_sql_response_to_mult_table(rows: Sequence[Sequence[Any]]) -> list[MultRow]:
    """Convert queried or preprogrammed mult rows into the internal representation.

    Parameters:
        rows: The rows, each holding the columns `_mult_table_column_names` names, in
            that order. A row of seven values instead of eight is a preprogrammed
            ``mult_options`` entry from a table schema, which carries no aliases; the
            other seven are `opus_import.import_util.MultOption` either way.

    Returns:
        One dictionary per row, keyed by column name, with the label rendered as a
        string and a missing aliases column filled in as None.

    Raises:
        TypeError: If a row carries neither seven nor eight values, since it then names
            neither shape.
    """
    mult_rows = []
    for row in rows:
        aliases: Any = None
        if len(row) == 8:
            *option_values, aliases = row
        else:
            # preprogrammed mult options list doesn't have aliases field
            option_values = list(row)
        option = import_util.MultOption(*option_values)

        row_dict = {
            'id': option.id,
            'value': option.value,
            'label': str(option.label),
            'aliases': aliases,
            'disp_order': option.disp_order,
            'display': option.display,
            'grouping': option.grouping,
            'group_disp_order': option.group_disp_order,
        }
        mult_rows.append(row_dict)
    return mult_rows


def read_or_create_mult_table(
    ctx: ImportContext, mult_table_name: str, table_column: dict[str, Any]
) -> list[MultRow]:
    """Return a mult table's rows, reading them into the cache the first time.

    A column whose schema carries ``mult_options`` has its values fixed there, so those
    are used and the table is marked for writing. Otherwise the rows come from the
    database: from the import table when a previous run left one, and from the permanent
    table otherwise. An import table this run created empty is not read, because it has
    nothing in it yet; the permanent table is read instead and marked for writing, so
    the values it holds survive into the import table.

    A table that exists in neither namespace starts out with no rows, and the import
    fills it as it meets values.

    Parameters:
        ctx: The import run's context, for the open database, the caches and the
            arguments.
        mult_table_name: The mult table, without its namespace prefix.
        table_column: The definition of the column the table belongs to.

    Returns:
        The table's rows, which are the cache itself -- appending to the returned list is
        how `update_mult_table` adds a value.
    """
    if mult_table_name in ctx.mult_table_cache:
        return ctx.mult_table_cache[mult_table_name]

    if 'mult_options' in table_column:
        if not ctx.args.import_suppress_mult_messages:
            import_util.log_debug(ctx, f'Using preprogrammed mult table "{mult_table_name}"')
        mult_rows = _convert_sql_response_to_mult_table(table_column['mult_options'])
        ctx.mult_table_cache[mult_table_name] = mult_rows
        ctx.modified_mult_tables.add(mult_table_name)
        return mult_rows

    # If there is already an import version of the table, it means this is a
    # second run of the import pipeline without copying over to the new
    # database, so read the contents of the import version. But it's also
    # possible we just created the mult table during the initialization phase
    # and it's empty. In that case ignore the import one.
    # Otherwise, if there is already a non-import version, read that one.
    # And if there's no table to be found anyway, create a new one.
    use_namespace: Namespace | None = None

    db = ctx.db
    assert db is not None
    if mult_table_name not in ctx.created_import_mult_tables and db.table_exists(
        'import', mult_table_name
    ):
        # Previous import table available
        use_namespace = 'import'

    elif db.table_exists('perm', mult_table_name):
        use_namespace = 'perm'
        # If we just created an import version but are reading the permanent
        # version, we have to write out the import version before doing
        # anything else too
        if mult_table_name in ctx.created_import_mult_tables:
            ctx.modified_mult_tables.add(mult_table_name)

    if use_namespace is not None:
        ns_mult_table_name = db.convert_raw_to_namespace(use_namespace, mult_table_name)
        if not ctx.args.import_suppress_mult_messages:
            import_util.log_debug(ctx, f'Reading from mult table "{ns_mult_table_name}"')
        rows = db.read_rows(use_namespace, mult_table_name, _mult_table_column_names())
        mult_rows = _convert_sql_response_to_mult_table(rows)
        ctx.mult_table_cache[mult_table_name] = mult_rows
        return mult_rows

    empty_rows: list[MultRow] = []
    ctx.mult_table_cache[mult_table_name] = empty_rows
    return empty_rows


def mult_table_lookup_id(
    ctx: ImportContext, table_name: str, field_name: str, table_column: dict[str, Any], val: Any
) -> Any:
    """Return the id a mult table already gives a value, without adding it.

    Parameters:
        ctx: The import run's context, for the open database and the caches.
        table_name: The observation table the column belongs to.
        field_name: The column.
        table_column: The definition of that column.
        val: The value to look up. It is compared as a string, which is how mult tables
            store their values; None matches a row whose value is None.

    Returns:
        The row id, or None if the table has no row for that value.
    """
    mult_table_name = import_util.table_name_mult(table_name, field_name)
    mult_table = read_or_create_mult_table(ctx, mult_table_name, table_column)
    if val is not None:
        val = str(val)
    for entry in mult_table:
        if entry['value'] == val:
            # The value is already in the mult table, so we're done here
            return entry['id']
    return None


def update_mult_table(
    ctx: ImportContext,
    table_name: str,
    field_name: str,
    table_column: dict[str, Any],
    val: Any,
    label: Any,
    aliases: str | None = None,
    disp: str = 'Y',
    disp_order: Any = None,
    grouping: str | None = None,
    group_disp_order: Any = None,
) -> Any:
    """Return the id a mult table gives a value, adding a row for it if it is new.

    A new row is appended to the cached table and the table is marked for writing at the
    end of the bundle. When no ``disp_order`` is given, one is made up so that the web
    application's ordering is sensible without every schema having to state it: the
    values are sorted numerically if they all parse as numbers or the column has a unit,
    and ``Yes`` sorts before ``No`` and ``On`` before ``Off``. The absent-value labels
    sort to the end, ``None`` then ``N/A`` then ``NULL`` -- but only for a column with no
    unit, since a column that has one sorts them by their own text instead.

    Parameters:
        ctx: The import run's context, for the open database, the caches and the
            arguments.
        table_name: The observation table the column belongs to.
        field_name: The column.
        table_column: The definition of that column.
        val: The value to find or add. It is stored as a string.
        label: How the value is shown to users. It is rendered with ``str``, so None
            becomes ``'None'`` and sorts with the other absent-value labels; a caller
            that wants ``'N/A'`` passes it.
        aliases: Other spellings a search should accept for this value.
        disp: ``'Y'`` to show the value in the search form, ``'N'`` to hide it.
        disp_order: The sort key, or None to derive one as described above.
        grouping: The group the value belongs to in the search form, or None.
        group_disp_order: The group's sort key, or None to sort groups by name.

    Returns:
        The row id -- the existing one if the table already had the value, the new one if
        a row was added, and 0 if the value is missing from a preprogrammed table, which
        is reported as an error because such a table cannot be added to.
    """
    mult_table_name = import_util.table_name_mult(table_name, field_name)
    mult_table = read_or_create_mult_table(ctx, mult_table_name, table_column)
    if val is not None:
        val = str(val)
    for entry in mult_table:
        if entry['value'] == val:
            # The value is already in the mult table, so we're done here
            return entry['id']

    if 'mult_options' in table_column:
        import_util.log_nonrepeating_error(
            ctx, f'Unable to add value "{val}" to preprogrammed mult table "{mult_table_name}"'
        )
        return 0

    label = str(label)

    if disp_order is None:
        # No disp_order specified, so make one up
        # Update the display_order
        (_form_type, _form_type_format, form_type_unit_id) = opus_support.parse_form_type(
            table_column['pi_form_type']
        )
        parse_func = opus_support.get_single_parse_function(form_type_unit_id)

        # See if all values in the mult table are numeric
        all_numeric = True
        for row in mult_table:
            if (
                row['label'] is None
                or str(row['label']).upper() == 'NONE'
                or str(row['label']).upper() == 'NULL'
            ):
                continue
            try:
                float(row['label'])
            except ValueError:
                all_numeric = False
                break
        try:
            float(label)
        except ValueError:
            all_numeric = False

        # Null always comes last. N/A always comes before that.
        # None always comes before that.
        # Yes comes before No. On comes before Off.
        if label in [None, 'NULL', 'Null']:
            if parse_func is not None:
                disp_order = label
            else:
                disp_order = 'zzz' + str(label)
        elif label == 'N/A':
            if parse_func is not None:
                disp_order = label
            else:
                disp_order = 'zzy' + str(label)
        elif label in ['NONE', 'None']:
            if parse_func is not None:
                disp_order = label
            else:
                disp_order = 'zzx' + str(label)
        elif parse_func:
            try:
                disp_order = f'{parse_func(str(val)):030.9f}'
            except Exception as e:
                import_util.log_nonrepeating_error(
                    ctx, f'Unable to parse "{label}" for unit type "{form_type_unit_id}": {e}'
                )
                disp_order = label
        elif all_numeric:
            disp_order = f'{float(label):20.9f}'
        elif label in ('Yes', 'On'):
            disp_order = 'zzAYes'
        elif label in ('No', 'Off'):
            disp_order = 'zzBNo'
        else:
            disp_order = label

    if isinstance(disp_order, (int, float)):
        disp_order = f'{disp_order:030.9f}'
    if len(mult_table) == 0:
        next_id = 0
    else:
        next_id = max([x['id'] for x in mult_table]) + 1
    if label is None:
        label = 'N/A'

    # If we didn't specify the group_disp_order, we will order groups
    # alphabetically
    if grouping is not None and group_disp_order is None:
        group_disp_order = grouping

    new_entry = {
        'id': next_id,
        'value': val,
        'label': label,
        'aliases': aliases,
        'disp_order': disp_order,
        'display': disp,  # default display: 'Y'
        'grouping': grouping,
        'group_disp_order': group_disp_order,
    }
    mult_table.append(new_entry)

    ctx.modified_mult_tables.add(mult_table_name)
    if not ctx.args.import_suppress_mult_messages:
        import_util.log_info(
            ctx, f'Added new value "{val}" ("{label}") to mult table ' + f'"{mult_table_name}"'
        )

    return next_id


def dump_import_mult_tables(ctx: ImportContext) -> None:
    """Write every mult table this bundle changed out to the import namespace.

    Parameters:
        ctx: The import run's context, for the open database and the caches.
    """
    db = ctx.db
    assert db is not None
    for mult_table_name in sorted(ctx.modified_mult_tables):
        rows = ctx.mult_table_cache[mult_table_name]
        # Insert or update all the rows
        imp_mult_table_name = db.convert_raw_to_namespace('import', mult_table_name)
        import_util.log_debug(ctx, f'Writing mult table "{imp_mult_table_name}"')
        db.upsert_rows('import', mult_table_name, 'id', rows)
        # If we wrote out a mult table, that means we didn't just create it
        # empty anymore, so remove it from ctx.created_import_mult_tables.
        if mult_table_name in ctx.created_import_mult_tables:
            ctx.created_import_mult_tables.remove(mult_table_name)


def copy_mult_from_import_to_permanent(ctx: ImportContext) -> None:
    """Copy every import mult table over its permanent counterpart.

    All of them, not just the ones this run changed: an earlier run or an earlier bundle
    may have changed a table, and nothing records that.

    Parameters:
        ctx: The import run's context, for the open database.
    """
    db = ctx.db
    assert db is not None
    table_names = db.table_names('import', prefix='mult_')
    for table_name in table_names:
        imp_mult_table_name = db.convert_raw_to_namespace('import', table_name)
        import_util.log_debug(ctx, f'Copying mult table "{imp_mult_table_name}"')
        # Read the import mult table
        column_list = _mult_table_column_names()
        rows = db.read_rows('import', table_name, column_list)
        mult_rows = _convert_sql_response_to_mult_table(rows)
        # Write the permanent table
        db.upsert_rows('perm', table_name, 'id', mult_rows)
