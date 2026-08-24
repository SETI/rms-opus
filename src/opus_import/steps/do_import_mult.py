################################################################################
# do_import_mult.py
#
# Read, cache, and write the mult_ tables that hold the enumerated values of the
# obs_ table columns. These are the mult-handling internals of do_import, not a
# step of their own.
################################################################################

import opus_support
from opus_import import import_util


def _mult_table_column_names():
    """Return the list of columns every mult table has.

       The grouping columns are part of that list rather than being added for the
       *_target_name tables only, so this is the same for every mult table. The
       docstring used to say the opposite and the function took a table_name it
       never read."""

    return ['id', 'value', 'label', 'disp_order', 'display',
            'grouping', 'group_disp_order', 'aliases']

def _convert_sql_response_to_mult_table(mult_table_name, rows):
    """Given a set of rows from an SQL query of a mult table, convert it into
       our internal dictionary representation."""
    mult_rows = []
    for row in rows:
        if len(row) == 8:
            (id_num, value, label, disp_order,
             display, grouping, group_disp_order, aliases) = row
        else:
            # preprogrammed mult options list doesn't have aliases field
            (id_num, value, label, disp_order,
             display, grouping, group_disp_order) = row
            aliases = None

        row_dict = {
            'id': id_num,
            'value': value,
            'label': str(label),
            'aliases': aliases,
            'disp_order': disp_order,
            'display': display,
            'grouping': grouping,
            'group_disp_order': group_disp_order
        }
        mult_rows.append(row_dict)
    return mult_rows

def read_or_create_mult_table(ctx, mult_table_name, table_column):
    """Given a mult table name, either read the table from the database or
       return the cached version if we previously read it."""

    if mult_table_name in ctx.mult_table_cache:
        return ctx.mult_table_cache[mult_table_name]

    if 'mult_options' in table_column:
        if not ctx.args.import_suppress_mult_messages:
            import_util.log_debug(
                ctx, f'Using preprogrammed mult table "{mult_table_name}"')
        mult_rows = _convert_sql_response_to_mult_table(mult_table_name,
                                                        table_column['mult_options'])
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
    use_namespace = None

    if (mult_table_name not in ctx.created_import_mult_tables and
        ctx.db.table_exists('import', mult_table_name)):
        # Previous import table available
        use_namespace = 'import'

    elif ctx.db.table_exists('perm', mult_table_name):
        use_namespace = 'perm'
        # If we just created an import version but are reading the permanent
        # version, we have to write out the import version before doing
        # anything else too
        if mult_table_name in ctx.created_import_mult_tables:
            ctx.modified_mult_tables.add(mult_table_name)

    if use_namespace is not None:
        ns_mult_table_name = (
            ctx.db.convert_raw_to_namespace(use_namespace, mult_table_name))
        if not ctx.args.import_suppress_mult_messages:
            import_util.log_debug(ctx, f'Reading from mult table "{ns_mult_table_name}"')
        rows = ctx.db.read_rows(use_namespace, mult_table_name,
                                _mult_table_column_names())
        mult_rows = _convert_sql_response_to_mult_table(mult_table_name, rows)
        ctx.mult_table_cache[mult_table_name] = mult_rows
        return mult_rows

    rows = []
    ctx.mult_table_cache[mult_table_name] = rows
    return rows


def mult_table_lookup_id(ctx, table_name, field_name, table_column, val):
    """Lookup the id for a single value in the cached version of a mult table."""
    mult_table_name = import_util.table_name_mult(table_name, field_name)
    mult_table = read_or_create_mult_table(ctx, mult_table_name, table_column)
    if val is not None:
        val = str(val)
    for entry in mult_table:
        if entry['value'] == val:
            # The value is already in the mult table, so we're done here
            return entry['id']
    return None


def update_mult_table(ctx, table_name, field_name, table_column, val, label,
                      aliases=None, disp='Y', disp_order=None, grouping=None,
                      group_disp_order=None):
    """Update a single value in the cached version of a mult table."""

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
            ctx,
            f'Unable to add value "{val}" to preprogrammed mult table '
            f'"{mult_table_name}"')
        return 0

    label = str(label)

    if disp_order is None:
        # No disp_order specified, so make one up
        # Update the display_order
        (_form_type, _form_type_format,
         form_type_unit_id) = opus_support.parse_form_type(table_column['pi_form_type'])
        parse_func = opus_support.get_single_parse_function(form_type_unit_id)

        # See if all values in the mult table are numeric
        all_numeric = True
        for row in mult_table:
            if (row['label'] is None or
                str(row['label']).upper() == 'NONE' or
                str(row['label']).upper() == 'NULL'):
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
                    ctx,
                    f'Unable to parse "{label}" for unit type '
                    f'"{form_type_unit_id}": {e}')
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
        next_id = max([x['id'] for x in mult_table])+1
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
        'display': disp, # default display: 'Y'
        'grouping': grouping,
        'group_disp_order': group_disp_order
    }
    mult_table.append(new_entry)

    ctx.modified_mult_tables.add(mult_table_name)
    if not ctx.args.import_suppress_mult_messages:
        import_util.log_info(ctx, f'Added new value "{val}" ("{label}") to mult table '+
                             f'"{mult_table_name}"')

    return next_id


def dump_import_mult_tables(ctx):
    """Dump all of the cached import mult tables into the database."""

    for mult_table_name in sorted(ctx.modified_mult_tables):
        rows = ctx.mult_table_cache[mult_table_name]
        # Insert or update all the rows
        imp_mult_table_name = ctx.db.convert_raw_to_namespace('import',
                                                              mult_table_name)
        import_util.log_debug(ctx, f'Writing mult table "{imp_mult_table_name}"')
        ctx.db.upsert_rows('import', mult_table_name, 'id', rows)
        # If we wrote out a mult table, that means we didn't just create it
        # empty anymore, so remove it from ctx.created_import_mult_tables.
        if mult_table_name in ctx.created_import_mult_tables:
            ctx.created_import_mult_tables.remove(mult_table_name)


def copy_mult_from_import_to_permanent(ctx):
    """Copy ALL mult tables from import to permanent. We have to do all tables,
       not just the ones that have changed, because tables might have changed
       during previous import runs or previous bundles and we don't have a
       record of that."""

    table_names = ctx.db.table_names('import', prefix='mult_')
    for table_name in table_names:
        imp_mult_table_name = ctx.db.convert_raw_to_namespace('import',
                                                              table_name)
        import_util.log_debug(ctx, f'Copying mult table "{imp_mult_table_name}"')
        # Read the import mult table
        column_list = _mult_table_column_names()
        rows = ctx.db.read_rows('import', table_name, column_list)
        mult_rows = _convert_sql_response_to_mult_table(table_name, rows)
        # Write the permanent table
        ctx.db.upsert_rows('perm', table_name, 'id', mult_rows)
