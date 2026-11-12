"""Check a set of imported tables for the mistakes a schema edit tends to introduce.

Nothing here changes the database. Each check reports what it finds through the logger,
and a failure is worth attention rather than being fatal: the tables are already
written, and an import that produced them is not undone by a validation error.

The checks are aimed at the OPUS invariants no database constraint can express -- that
every user-visible column is described in ``param_info``, that a paired minimum and
maximum are really in that order, and that observations sharing a filter agree about
that filter's wavelengths -- and at the one a constraint expresses but does not check:
a foreign key added with ``foreign_key_checks`` off, as finalization adds them, never
reads the rows already there, so every row's ``obs_general`` row is counted here, and
``obs_pds``'s copy of each row's bundle is compared with ``obs_general``'s. Every
observation's ``obs_preview`` row, which the results pages read, is counted too.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from opus_import import surface_geometry

if TYPE_CHECKING:
    from opus_import.context import ImportContext
    from opus_import.importdb.super import ImportDBSuper


def _body_category(db: ImportDBSuper) -> str | None:
    """Return the surface geometry body category that stands for every body's.

    Every body's category describes the surface geometry table's columns the same way,
    so the first in order of name describes them for all.

    Parameters:
        db: The open database.

    Returns:
        The first ``obs_surface_geometry__`` category ``param_info`` holds, or None when it
        holds none, which is when the surface geometry table holds no rows.
    """
    q = db.quote_identifier
    res = db.general_select(
        f'MIN({q("category_name")}) FROM {q("param_info")} WHERE {q("category_name")} LIKE %s',
        [surface_geometry.TARGET_CATEGORY_PREFIX.replace('_', '\\_') + '%'],
    )
    category = res[0][0] if res else None
    return None if category is None else str(category)


def _param_info_category(table_name: str, field_name: str, body_category: str | None) -> str | None:
    """Return the ``param_info`` category a column of an ``obs_`` table is described under.

    Parameters:
        table_name: The table.
        field_name: The column.
        body_category: What `_body_category` returned.

    Returns:
        The table's own name, except for the surface geometry table: the selector category
        for its ``target_name``, and `body_category` for every other column.
    """
    if table_name != surface_geometry.SURFACE_GEOMETRY_TABLE:
        return table_name
    if field_name == surface_geometry.TARGET_COLUMN:
        return surface_geometry.SELECTOR_CATEGORY
    return body_category


def validate_param_info(ctx: ImportContext) -> None:
    """Report user-visible columns that ``param_info`` does not describe.

    Every column of every ``obs_`` table needs a ``param_info`` row, under the category
    `_param_info_category` gives it, apart from the ones users never search or see:
    ``id``, ``obs_general_id``, the ``d_`` (delta) columns and any column
    that has one, the ``mult_`` id columns, ``opus_id`` outside ``obs_general``,
    ``bundle_id`` outside ``obs_pds``, ``instrument_id`` outside ``obs_general``, and
    everything in ``obs_files``. A surface geometry column other than ``target_name`` is
    skipped when ``param_info`` has no body's category. A column with no row is
    reported; a column with more than one is not, since the check tests only for
    absence.

    The rows are then scanned for a ``disp_order`` repeated within one category among
    the displayed parameters, and for a repeated slug. Both scans use a subquery that
    skips its first match, so they report a value shared by three or more rows and stay
    silent about one shared by exactly two.

    Parameters:
        ctx: The import run's context, for the open database and the logger.
    """
    # Every column in every obs_ table should have an entry in the param_info
    # table except for id and obs_general_id.
    # Exceptions are:
    #   bundle_id in tables other than obs_pds
    #   instrument_id in tables other than obs_general

    db = ctx.db
    assert db is not None
    logger = ctx.logger

    logger.log('debug', 'Validating param_info table')

    obs_table_names = sorted(db.table_names(prefix='obs_'))
    body_category = _body_category(db)

    pi_table_name = 'param_info'

    q = db.quote_identifier

    for obs_table_name in obs_table_names:
        if obs_table_name == 'obs_files':
            # Not really a user-visible table so no param_info needed
            continue
        column_list = db.table_info(obs_table_name)
        field_names = [x['field_name'] for x in column_list]
        for column in column_list:
            field_name = column['field_name']
            if (
                field_name == 'id'
                or field_name == 'obs_general_id'
                or field_name.startswith('d_')
                or 'd_' + field_name in field_names
                or (field_name == 'opus_id' and obs_table_name != 'obs_general')
                or (field_name.startswith('mult_'))
            ):
                continue
            if field_name == 'bundle_id' and obs_table_name != 'obs_pds':
                continue
            if field_name == 'instrument_id' and obs_table_name != 'obs_general':
                continue
            category = _param_info_category(obs_table_name, field_name, body_category)
            if category is None:
                continue
            cmd = f"""
COUNT(*) FROM {q(pi_table_name)} WHERE {q('category_name')}=%s AND
{q('name')}=%s"""
            res = db.general_select(cmd, [category, field_name])
            count = res[0][0]
            if count == 0:
                logger.log(
                    'error', f'OBS field "{obs_table_name}.{field_name}" missing param_info entry'
                )

    # Every param_info entry should have a unique disp_order
    # This is a hideous query that looks for duplicate disp_order fields
    # within a given category as long as the field is displayed
    # Every interpolation is an identifier produced by quote_identifier
    # (^[A-Za-z0-9_]+$); the statement carries no values at all.
    cmd = f"""
{q('category_name')}, {q('name')} FROM {q(pi_table_name)} {q('pi1')} WHERE EXISTS
    (SELECT 1 FROM {q(pi_table_name)} {q('pi2')} WHERE
        {q('pi1')}.{q('category_name')}={q('pi2')}.{q('category_name')} AND
        {q('pi1')}.{q('disp_order')}={q('pi2')}.{q('disp_order')} AND
        ({q('pi1')}.{q('display')}=1 OR {q('pi1')}.{q('display_results')}=1) AND
        ({q('pi2')}.{q('display')}=1 OR {q('pi2')}.{q('display_results')}=1) AND
        {q('pi1')}.{q('id')}!={q('pi2')}.{q('id')}
        LIMIT 1,1)"""  # nosec B608
    res = db.general_select(cmd)
    for cat_name, field_name in res:
        logger.log('error', f'PARAM_INFO field "{cat_name}.{field_name}" has duplicate disp_order')

    # Every param_info entry should have a unique slug. Period.
    # Every interpolation is an identifier produced by quote_identifier
    # (^[A-Za-z0-9_]+$); the statement carries no values at all.
    cmd = f"""
{q('category_name')}, {q('name')} FROM {q(pi_table_name)} {q('pi1')} WHERE EXISTS
    (SELECT 1 FROM {q(pi_table_name)} {q('pi2')} WHERE
        {q('pi1')}.{q('slug')}={q('pi2')}.{q('slug')} AND
        {q('pi1')}.{q('id')}!={q('pi2')}.{q('id')}
        LIMIT 1,1)"""  # nosec B608
    res = db.general_select(cmd)
    for cat_name, field_name in res:
        logger.log('error', f'PARAM_INFO field "{cat_name}.{field_name}" has duplicate slug')


def validate_nulls(ctx: ImportContext) -> None:
    """Report columns that allow NULL and never contain one.

    Such a column can be tightened to NOT NULL in its table schema, which lets the
    database enforce what the data already satisfies. The suggestion is logged at info
    level, because it is an observation about the schema rather than a fault in the
    data. The surface geometry table is counted once, over every body's rows, so a column
    is reported only when no body's rows hold a NULL in it.

    Parameters:
        ctx: The import run's context, for the open database and the logger.
    """
    # Look for columns in OBS tables that don't contain nulls and yet the
    # column is marked as NULLS-OK and suggest the column type be changed.

    db = ctx.db
    assert db is not None
    logger = ctx.logger

    logger.log('debug', 'Validating non-NULL columns')

    obs_table_names = sorted(db.table_names(prefix='obs_'))
    q = db.quote_identifier

    for obs_table_name in obs_table_names:
        nullable = [
            column['field_name']
            for column in db.table_info(obs_table_name)
            if not column['field_notnull']
        ]
        if not nullable:
            continue
        # One scan of the table counts the NULLs in every nullable column, so the
        # check costs the same whichever columns carry a key. An empty table's sums
        # are NULL, which counts as none found.
        counts = ', '.join(f'SUM({q(name)} IS NULL)' for name in nullable)
        (row,) = db.general_select(f'{counts} FROM {q(obs_table_name)}')
        for field_name, count in zip(nullable, row, strict=True):
            if not count:
                logger.log(
                    'info',
                    f'Column "{obs_table_name}.{field_name}" allows NULLs but none found '
                    + '- suggest changing column attributes',
                )


def validate_min_max_order(ctx: ImportContext) -> None:
    """Report paired columns whose minimum exceeds its maximum.

    A column named with a trailing ``1`` is the low end of a range and its ``2`` sibling
    the high end, so a row where the second is smaller is bad data. A missing sibling,
    and a pair with no ``param_info`` row or more than one, are reported too. Longitude
    pairs are exempt: a longitude range wraps, so the low end legitimately exceeds the
    high end. A bad row is named by its OPUS ID, which a table other than
    ``obs_general`` reads from the ``obs_general`` row it joins. A pair's ``param_info``
    row is looked up under the category `_param_info_category` gives it, and a surface
    geometry pair is skipped when ``param_info`` has no body's category.

    Parameters:
        ctx: The import run's context, for the open database and the logger.
    """
    # Look for pairs of columns X1/X2 and check to make sure that X1 <= X2 in
    # all non-NULL cases.

    db = ctx.db
    assert db is not None
    logger = ctx.logger

    logger.log('debug', 'Validating MIN/MAX columns')

    obs_table_names = sorted(db.table_names(prefix='obs_'))
    body_category = _body_category(db)

    pi_table_name = 'param_info'

    q = db.quote_identifier

    for obs_table_name in obs_table_names:
        full_obs_table_name = obs_table_name
        column_list = db.table_info(obs_table_name)
        column_list.sort(key=lambda x: x['field_name'])
        for column in column_list:
            field_name1 = column['field_name']
            if not field_name1.endswith('1'):
                continue
            field_name2 = field_name1[:-1] + '2'
            if field_name2 not in [x['field_name'] for x in column_list]:
                logger.log(
                    'error',
                    f'Column "{full_obs_table_name}.{field_name1}" present but there is no '
                    + f'{field_name2}',
                )
                continue

            # Check param_info to see if this is a longitude field
            category = _param_info_category(obs_table_name, field_name1, body_category)
            if category is None:
                continue
            cmd = f"""
{q('form_type')} FROM {q(pi_table_name)} WHERE {q('category_name')}=%s AND
{q('name')}=%s"""
            res = db.general_select(cmd, [category, field_name1])
            if len(res) == 0:
                logger.log(
                    'error', f'No param_info entry for "{full_obs_table_name}.{field_name1}"'
                )
                continue
            if len(res) > 1:
                logger.log(
                    'error',
                    f'More than one param_info entry for "{full_obs_table_name}.{field_name1}"',
                )
                continue
            pi_form_type = res[0][0]
            if pi_form_type is None or pi_form_type.startswith('LONG'):
                continue

            # Every interpolation is an identifier produced by quote_identifier
            # (^[A-Za-z0-9_]+$); the statement carries no values at all.
            if obs_table_name == 'obs_general':
                cmd = f"""
{q('opus_id')} FROM {q(full_obs_table_name)} WHERE
{q(field_name2)} < {q(field_name1)}"""  # nosec B608
            else:
                cmd = f"""
{q('g')}.{q('opus_id')} FROM {q(full_obs_table_name)} {q('c')}
JOIN {q('obs_general')} {q('g')} ON {q('g')}.{q('id')} = {q('c')}.{q('obs_general_id')}
WHERE {q('c')}.{q(field_name2)} < {q('c')}.{q(field_name1)}"""  # nosec B608
            res = db.general_select(cmd)
            if len(res):
                opus_ids = [x[0] for x in res]
                logger.log(
                    'error',
                    f'Column "{full_obs_table_name}.{field_name1}" has values greater than '
                    + f'{field_name2} for some OPUS IDs; first 100: '
                    + ' '.join(opus_ids[:100]),
                )


def validate_filter_wavelength_consistency(ctx: ImportContext) -> None:
    """Report filters whose observations disagree about their wavelengths.

    Every observation taken through one filter should record the same wavelength range,
    resolution, wave numbers and spectrum size, so grouping ``obs_wavelength`` by filter
    should give one distinct value per field. Where the minimum and maximum of a group
    differ, both are logged as a warning. Cassini ISS groups by camera as well as
    filter, because its two cameras carry filters of the same name.

    Parameters:
        ctx: The import run's context, for the open database and the logger.
    """
    # For each mission and instrument, then for each filter, look at the
    # wavelength table and see if the wl1 and wl2 fields contain only a single
    # value.

    db = ctx.db
    assert db is not None
    logger = ctx.logger

    logger.log('debug', 'Validating filter/wavelength consistency')

    obs_table_names = sorted(db.table_names(prefix='obs_'))

    q = db.quote_identifier
    wl_table = q('obs_wavelength')
    wl_fields = (
        'wavelength1',
        'wavelength2',
        'wave_res1',
        'wave_res2',
        'wave_no1',
        'wave_no2',
        'wave_no_res1',
        'wave_no_res2',
        'spec_size',
    )

    for obs_table_name in obs_table_names:
        full_obs_table_name = obs_table_name
        column_list = db.table_info(obs_table_name)
        for column in column_list:
            field_name = column['field_name']
            if field_name not in ('filter_name', 'combined_filter'):
                continue

            # Select obs_wavelength entries that match, group by filter name,
            # and check the range for the various wavelength fields
            if obs_table_name == 'obs_instrument_coiss':
                cmd = f'{q("camera")}, {q(field_name)}'
                start_col = 2
            else:
                cmd = f'{q(field_name)}'
                start_col = 1

            for wl_field in wl_fields:
                cmd += f", MIN(IFNULL({q(wl_field)}, 'NULL'))"
                cmd += f", MAX(IFNULL({q(wl_field)}, 'NULL'))"
            cmd += f"""
 FROM {q(full_obs_table_name)}
LEFT JOIN {wl_table} ON {q(full_obs_table_name)}.{q('obs_general_id')} =
{wl_table}.{q('obs_general_id')}"""
            if obs_table_name == 'obs_instrument_coiss':
                cmd += f'GROUP BY {q("camera")}, {q(field_name)}'
            else:
                cmd += f'GROUP BY {q(field_name)}'

            res = db.general_select(cmd)
            for row in res:
                for col in range(start_col, len(row) - 1, 2):
                    pretty_filter = ':'.join([str(x) for x in row[0:start_col]])
                    if row[col] != row[col + 1]:
                        logger.log(
                            'warning',
                            f'"obs_wavelength.{wl_fields[(col - start_col) // 2]}" has inconsistent'
                            + f' values for {full_obs_table_name} filter "{pretty_filter}": '
                            + f'{row[col]} and {row[col + 1]}',
                        )


def validate_orphans(ctx: ImportContext) -> None:
    """Report rows whose ``obs_general`` row does not exist.

    Every observation table other than ``obs_general``, and ``cart``, is anti-joined
    against ``obs_general`` on ``obs_general_id``, and a table with any row left over is
    reported at error level with the count. Observation tables without ``obs_general``
    are an error too; a schema with no observation table at all has nothing to check.

    Parameters:
        ctx: The import run's context, for the open database and the logger.
    """
    db = ctx.db
    assert db is not None
    logger = ctx.logger

    logger.log('debug', 'Validating references to obs_general')

    tables = [name for name in sorted(db.table_names(prefix='obs_')) if name != 'obs_general']
    if not db.table_exists('obs_general'):
        if tables:
            logger.log(
                'error',
                f'Table "obs_general" is missing, but {len(tables)} other obs_ tables exist',
            )
        return
    if db.table_exists('cart'):
        tables.append('cart')
    q = db.quote_identifier
    obs_general = q('obs_general')
    for table_name in tables:
        child = q(table_name)
        # Every interpolation is an identifier produced by quote_identifier
        # (^[A-Za-z0-9_]+$); the statement carries no values at all.
        cmd = f"""
COUNT(*) FROM {child} LEFT JOIN {obs_general} ON
{child}.{q('obs_general_id')} = {obs_general}.{q('id')}
WHERE {obs_general}.{q('id')} IS NULL"""  # nosec B608
        count = db.general_select(cmd)[0][0]
        if count:
            logger.log(
                'error', f'Table "{table_name}" has {count} rows whose obs_general row is missing'
            )


def validate_pds_bundle_ids(ctx: ImportContext) -> None:
    """Report ``obs_pds`` rows whose bundle differs from their ``obs_general`` row's.

    ``obs_pds.bundle_id`` is the public ``bundleid`` field, written by the import
    beside ``obs_general.bundle_id``, which the per-bundle delete selects by; the two
    must agree, or a search by bundle and the delete would see different bundles. Any
    such row is an error, with the count.

    Parameters:
        ctx: The import run's context, for the open database and the logger.
    """
    db = ctx.db
    assert db is not None
    ctx.logger.log('debug', "Validating that obs_pds names each row's bundle")
    if not (db.table_exists('obs_general') and db.table_exists('obs_pds')):
        return
    q = db.quote_identifier
    # Every interpolation is an identifier produced by quote_identifier
    # (^[A-Za-z0-9_]+$); the statement carries no values at all.
    cmd = f"""
COUNT(*) FROM {q('obs_pds')} {q('p')}
JOIN {q('obs_general')} {q('g')} ON {q('g')}.{q('id')} = {q('p')}.{q('obs_general_id')}
WHERE {q('p')}.{q('bundle_id')} <> {q('g')}.{q('bundle_id')}"""  # nosec B608
    count = db.general_select(cmd)[0][0]
    if count:
        ctx.logger.log(
            'error', f'Table "obs_pds" has {count} rows whose bundle_id differs from obs_general'
        )


def validate_previews(ctx: ImportContext) -> None:
    """Report ``obs_general`` rows that have no ``obs_preview`` row.

    The import writes one ``obs_preview`` row for every observation, and the results
    pages read an observation's preview images from it, so an observation without one
    is an error, with the count.

    Parameters:
        ctx: The import run's context, for the open database and the logger.
    """
    db = ctx.db
    assert db is not None
    ctx.logger.log('debug', 'Validating that each observation has an obs_preview row')
    if not (db.table_exists('obs_general') and db.table_exists('obs_preview')):
        return
    q = db.quote_identifier
    # Every interpolation is an identifier produced by quote_identifier
    # (^[A-Za-z0-9_]+$); the statement carries no values at all.
    cmd = f"""
COUNT(*) FROM {q('obs_general')} {q('g')}
LEFT JOIN {q('obs_preview')} {q('p')} ON {q('p')}.{q('obs_general_id')} = {q('g')}.{q('id')}
WHERE {q('p')}.{q('obs_general_id')} IS NULL"""  # nosec B608
    count = db.general_select(cmd)[0][0]
    if count:
        ctx.logger.log('error', f'{count} obs_general rows have no obs_preview row')


def validate_unique_opus_ids(ctx: ImportContext) -> None:
    """Report OPUS IDs that more than one ``obs_general`` row carries.

    ``obs_general.opus_id`` carries a plain key, and finalization's duplicate step is what
    leaves one row per OPUS ID, so a schema that has not been through it can hold two.
    Any such id is an error, naming how many there are and the first ten.

    Parameters:
        ctx: The import run's context, for the open database and the logger.
    """
    db = ctx.db
    assert db is not None
    ctx.logger.log('debug', 'Validating that each OPUS ID has one obs_general row')
    if not db.table_exists('obs_general'):
        return
    q = db.quote_identifier
    obs_general = q('obs_general')
    # Every interpolation is an identifier produced by quote_identifier
    # (^[A-Za-z0-9_]+$); the statement carries no values at all.
    shared = (
        f'SELECT {q("opus_id")} FROM {obs_general} GROUP BY {q("opus_id")} '  # nosec B608
        'HAVING COUNT(*) > 1'
    )
    count = db.general_select(f'COUNT(*) FROM ({shared}) {q("d")}')[0][0]  # nosec B608
    if count:
        rows = db.general_select(
            f'{q("opus_id")} FROM ({shared}) {q("d")} '  # nosec B608
            f'ORDER BY {q("opus_id")} LIMIT 10'
        )
        shown = ', '.join(f'"{row[0]}"' for row in rows)
        ctx.logger.log(
            'error',
            f'{count} OPUS IDs have more than one obs_general row, among them {shown}; '
            '--finalize keeps one copy of each',
        )


def do_validate(ctx: ImportContext) -> bool:
    """Run every validation check, driven by ``--validate``.

    Every check runs, so one run reports every failure; each is logged at error level.

    Parameters:
        ctx: The import run's context, for the open database and the logger.

    Returns:
        True if no check logged an error, False otherwise.
    """
    ctx.logger.open('Performing database validation', limits={'info': -1, 'debug': -1})

    validate_param_info(ctx)
    validate_nulls(ctx)
    validate_min_max_order(ctx)
    validate_filter_wavelength_consistency(ctx)
    validate_orphans(ctx)
    validate_pds_bundle_ids(ctx)
    validate_previews(ctx)
    validate_unique_opus_ids(ctx)

    fatal_count, error_count, _warning_count, _message_count = ctx.logger.close()
    return bool(fatal_count + error_count == 0)
