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
observation's ``obs_preview`` row, which the results pages read, is counted too, and each
``mult_list`` column's lists are compared with its junction table, which the search and
the counts read.

With a pending generation the ``param_info`` the checks read is its own,
``param_info__new``, which the switch puts in place (`param_info_table`): the live one
describes the served generation, and lacks any table the pending generation adds. The checks
then read what the update wrote rather than the whole schema
(`opus_import.validation_queries.GenerationScope`): the per-row checks read the observations
the pending generation added and their rows of the other tables, the filter check compares
only the filters those observations carry, and the NULL check, which describes the schema
rather than the rows, does not run.

With no generation pending the checks read the generation the schema serves. From a switch
until the purge, ``obs_general_rows`` still holds the observations the switch retired, with
their rows of the other tables, which the ``obs_general`` view hides; the checks then read
the served generation's observations and their rows alone
(`opus_import.validation_queries.served_generation_only`), as the site does, so a filter the
update corrected is not compared with its retired rows. Otherwise every row is served, and
every row is read with no condition.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from opus_import import (
    generations,
    import_util,
    list_junctions,
    surface_geometry,
    table_keys,
    table_swap,
)
from opus_import.validation_queries import (
    WAVELENGTH_FIELDS,
    filter_groups,
    filter_wavelength_query,
    generation_scope,
    min_max_query,
    null_count_query,
    served_condition,
    served_generation_only,
)

if TYPE_CHECKING:
    from opus_import.context import ImportContext
    from opus_import.importdb.super import ImportDBSuper


#: The table that describes every user-visible column.
PARAM_INFO_TABLE = 'param_info'


def param_info_table(ctx: ImportContext) -> str:
    """Return the ``param_info`` the checks read: the one the schema will serve.

    Parameters:
        ctx: The import run's context, for its pending generation.

    Returns:
        ``param_info__new``, built from the pending generation for its switch, when there
        is one; ``param_info`` otherwise.
    """
    if ctx.pending_generation is None:
        return PARAM_INFO_TABLE
    return table_swap.swap_new_name(PARAM_INFO_TABLE)


def _body_category(db: ImportDBSuper, pi_table_name: str) -> str | None:
    """Return the surface geometry body category that stands for every body's.

    Every body's category describes ``obs_surface_geometry_target``'s columns the same way,
    so the first in order of name describes them for all.

    Parameters:
        db: The open database.
        pi_table_name: The ``param_info`` table read (`param_info_table`).

    Returns:
        The first ``obs_surface_geometry__`` category ``param_info`` holds, or None when it
        holds none. Finalization writes one for each body the table holds, so none means
        an empty table; `validate_param_info` reports one that holds rows.
    """
    q = db.quote_identifier
    res = db.general_select(
        f'MIN({q("category_name")}) FROM {q(pi_table_name)} WHERE {q("category_name")} LIKE %s',
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
        The table's own name, except for ``obs_surface_geometry_target``: the selector category
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
    ``bundle_id`` outside ``obs_pds``, ``instrument_id`` outside ``obs_general``,
    ``obs_general``'s generation columns, and everything in ``obs_files``. The
    ``param_info`` read is `param_info_table`'s. A surface geometry column other than
    ``target_name`` is skipped when ``param_info`` has no body's category; the table
    holding rows then is reported, since finalization gives every body it holds a
    category. A column with no row is reported; a column with more than one is not, since
    the check tests only for absence.

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
    pi_table_name = param_info_table(ctx)
    body_category = _body_category(db, pi_table_name)

    q = db.quote_identifier

    geometry_table = surface_geometry.SURFACE_GEOMETRY_TABLE
    # Only rows of observations in the generation the run validates need a category: a
    # pending generation that retired every observation with surface geometry leaves
    # their rows for the purge, and builds param_info without their bodies.
    generation = ctx.import_generation
    s, g = q('s'), q('g')
    if (
        body_category is None
        and geometry_table in obs_table_names
        and db.general_select(
            f'1 FROM {q(geometry_table)} {s} '  # nosec B608 - quoted identifiers
            f'JOIN {q("obs_general")} {g} ON {g}.{q("id")}={s}.{q("obs_general_id")} '
            f'AND {generations.in_generation_condition(q, "g")} LIMIT 1',
            [generation, generation],
        )
    ):
        logger.log(
            'error',
            f'"{geometry_table}" holds rows but param_info has no '
            f'"{surface_geometry.TARGET_CATEGORY_PREFIX}" category to describe them',
        )

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
                or field_name in generations.GENERATION_COLUMNS
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

    # Every displayed param_info entry should have a disp_order no other displayed
    # entry of its category has: each row is reported that shares one with another row.
    # Every interpolation is an identifier produced by quote_identifier
    # (^[A-Za-z0-9_]+$); the statement carries no values at all.
    cmd = f"""
{q('category_name')}, {q('name')} FROM {q(pi_table_name)} {q('pi1')} WHERE EXISTS
    (SELECT 1 FROM {q(pi_table_name)} {q('pi2')} WHERE
        {q('pi1')}.{q('category_name')}={q('pi2')}.{q('category_name')} AND
        {q('pi1')}.{q('disp_order')}={q('pi2')}.{q('disp_order')} AND
        ({q('pi1')}.{q('display')}=1 OR {q('pi1')}.{q('display_results')}=1) AND
        ({q('pi2')}.{q('display')}=1 OR {q('pi2')}.{q('display_results')}=1) AND
        {q('pi1')}.{q('id')}!={q('pi2')}.{q('id')})"""  # nosec B608
    res = db.general_select(cmd)
    for cat_name, field_name in res:
        logger.log('error', f'PARAM_INFO field "{cat_name}.{field_name}" has duplicate disp_order')

    # Every param_info entry should have a slug no other entry has: each row is
    # reported that shares one with another row.
    # Every interpolation is an identifier produced by quote_identifier
    # (^[A-Za-z0-9_]+$); the statement carries no values at all.
    cmd = f"""
{q('category_name')}, {q('name')} FROM {q(pi_table_name)} {q('pi1')} WHERE EXISTS
    (SELECT 1 FROM {q(pi_table_name)} {q('pi2')} WHERE
        {q('pi1')}.{q('slug')}={q('pi2')}.{q('slug')} AND
        {q('pi1')}.{q('id')}!={q('pi2')}.{q('id')})"""  # nosec B608
    res = db.general_select(cmd)
    for cat_name, field_name in res:
        logger.log('error', f'PARAM_INFO field "{cat_name}.{field_name}" has duplicate slug')


def validate_nulls(ctx: ImportContext) -> None:
    """Report columns that allow NULL and never contain one.

    Such a column can be tightened to NOT NULL in its table schema, which lets the
    database enforce what the data already satisfies. The suggestion is logged at info
    level, because it is an observation about the schema rather than a fault in the
    data. ``obs_surface_geometry_target`` is counted once, over every body's rows, so a column
    is reported only when no body's rows hold a NULL in it. While a generation is pending
    the check does not run, and says so: it describes the whole schema, and the few
    bundles an update writes would make it report columns falsely. While the rows the
    last switch retired await the purge, only the served generation's rows are counted
    (`opus_import.validation_queries.served_generation_only`).

    Parameters:
        ctx: The import run's context, for the open database and the logger.
    """
    # Look for columns in OBS tables that don't contain nulls and yet the
    # column is marked as NULLS-OK and suggest the column type be changed.

    db = ctx.db
    assert db is not None
    logger = ctx.logger

    if ctx.pending_generation is not None:
        logger.log(
            'info',
            f'Not checking for nullable columns that hold no NULL in generation '
            f'{ctx.pending_generation}: the check describes the whole schema',
        )
        return

    logger.log('debug', 'Validating non-NULL columns')

    obs_table_names = sorted(db.table_names(prefix='obs_'))
    served = served_generation_only(ctx)

    for obs_table_name in obs_table_names:
        nullable = [
            column['field_name']
            for column in db.table_info(obs_table_name)
            if not column['field_notnull']
        ]
        if not nullable:
            continue
        (row,) = db.general_select(*null_count_query(db, obs_table_name, nullable, served))
        for field_name, count in zip(nullable, row, strict=True):
            if not count:
                logger.log(
                    'info',
                    f'Column "{obs_table_name}.{field_name}" allows NULLs but none found '
                    + '- suggest changing column attributes',
                )


def validate_min_max_order(ctx: ImportContext) -> None:
    """Report paired columns whose minimum exceeds its maximum.

    A column named with a trailing ``1`` is the low end of a range and its ``2`` sibling the
    high end, so a row where the second is smaller is bad data. A missing sibling, and a
    pair with no ``param_info`` row or more than one, are reported too. Longitude pairs are
    exempt: a longitude range wraps, so the low end legitimately exceeds the high end. A bad
    row is named by its OPUS ID, which a table other than ``obs_general`` reads from the
    ``obs_general`` row it joins. A pair's ``param_info`` row is looked up under the
    category `_param_info_category` gives it, in `param_info_table`'s table, and a surface
    geometry pair is skipped when ``param_info`` has no body's category. While a generation
    is pending only the rows of the observations it added are read
    (`opus_import.validation_queries.GenerationScope`), and while the rows the last switch
    retired await the purge only the served generation's
    (`opus_import.validation_queries.served_generation_only`).

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
    pi_table_name = param_info_table(ctx)
    body_category = _body_category(db, pi_table_name)
    scope = generation_scope(ctx)
    served = served_generation_only(ctx)

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

            res = db.general_select(*min_max_query(db, obs_table_name, field_name1, scope, served))
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

    While a generation is pending only the filters its own observations carry are compared
    (`opus_import.validation_queries.GenerationScope`), but across every observation the
    generation shows, so a bundle that disagrees with the served rows of its filter is still
    reported; a table the generation added no observation to is not read. While the rows the
    last switch retired await the purge only the served generation's observations are
    compared (`opus_import.validation_queries.served_generation_only`), so a filter whose
    wavelengths the update corrected is not compared with its retired rows.

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
    scope = generation_scope(ctx)
    served = served_generation_only(ctx)

    for obs_table_name in obs_table_names:
        column_list = db.table_info(obs_table_name)
        for column in column_list:
            field_name = column['field_name']
            if field_name not in ('filter_name', 'combined_filter'):
                continue

            # Select obs_wavelength entries that match, group by filter name,
            # and check the range for the various wavelength fields
            if obs_table_name == 'obs_instrument_coiss':
                group_columns: tuple[str, ...] = ('camera', field_name)
            else:
                group_columns = (field_name,)
            start_col = len(group_columns)
            groups: list[tuple[Any, ...]] = []
            if scope is not None:
                groups = filter_groups(db, obs_table_name, group_columns, scope)
                if not groups:
                    continue

            res = db.general_select(
                *filter_wavelength_query(db, obs_table_name, group_columns, scope, groups, served)
            )
            for row in res:
                for col in range(start_col, len(row) - 1, 2):
                    pretty_filter = ':'.join([str(x) for x in row[0:start_col]])
                    if row[col] != row[col + 1]:
                        logger.log(
                            'warning',
                            f'"obs_wavelength.{WAVELENGTH_FIELDS[(col - start_col) // 2]}" has '
                            f'inconsistent values for {obs_table_name} filter "{pretty_filter}": '
                            f'{row[col]} and {row[col + 1]}',
                        )


def validate_orphans(ctx: ImportContext) -> None:
    """Report rows whose ``obs_general`` row does not exist.

    Every observation table other than ``obs_general``, and ``cart``, is anti-joined
    against ``obs_general`` on ``obs_general_id``, and a table with any row left over is
    reported at error level with the count. Observation tables without ``obs_general``
    are an error too; a schema with no observation table at all has nothing to check.

    While a generation is pending only the rows naming an observation id it could have
    written are counted (`opus_import.validation_queries.GenerationScope.children`), still
    against every row of ``obs_general_rows``, retired ones included: an orphan has no
    ``obs_general`` row to select it by, so the rows are chosen by their own
    ``obs_general_id``, and every child row an update writes, or leaves behind by deleting
    an observation, names an id from the scope's first up. With no generation pending every
    row is counted against every row of ``obs_general_rows`` too: a retired observation's
    rows are not orphans, and the purge deletes them with it.

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
    scope = generation_scope(ctx)
    for table_name in tables:
        child = q(table_name)
        # Every interpolation is an identifier produced by quote_identifier
        # (^[A-Za-z0-9_]+$); every value is a parameter.
        cmd = f"""
COUNT(*) FROM {child} LEFT JOIN {obs_general} ON
{child}.{q('obs_general_id')} = {obs_general}.{q('id')}
WHERE {obs_general}.{q('id')} IS NULL"""  # nosec B608
        values: list[int] | None = None
        if scope is not None:
            children, values = scope.children(q, table_name)
            cmd += f' AND {children}'
        count = db.general_select(cmd, values)[0][0]
        if count:
            logger.log(
                'error', f'Table "{table_name}" has {count} rows whose obs_general row is missing'
            )


def validate_pds_bundle_ids(ctx: ImportContext) -> None:
    """Report ``obs_pds`` rows whose bundle differs from their ``obs_general`` row's.

    ``obs_pds.bundle_id`` is the public ``bundleid`` field, written by the import beside
    ``obs_general.bundle_id``, which the per-bundle delete selects by; the two must agree,
    or a search by bundle and the delete would see different bundles. Any such row is an
    error, with the count. While a generation is pending only the rows of the observations
    it added are compared (`opus_import.validation_queries.GenerationScope`), and while the
    rows the last switch retired await the purge only the served generation's
    (`opus_import.validation_queries.served_generation_only`).

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
    # (^[A-Za-z0-9_]+$); every value is a parameter.
    cmd = f"""
COUNT(*) FROM {q('obs_pds')} {q('p')}
JOIN {q('obs_general')} {q('g')} ON {q('g')}.{q('id')} = {q('p')}.{q('obs_general_id')}
WHERE {q('p')}.{q('bundle_id')} <> {q('g')}.{q('bundle_id')}"""  # nosec B608
    values: list[int] | None = None
    scope = generation_scope(ctx)
    served = served_generation_only(ctx)
    if scope is not None:
        children, child_values = scope.children(q, 'p')
        added, added_values = scope.added(q, 'g')
        cmd += f' AND {children} AND {added}'
        values = child_values + added_values
    elif served is not None:
        condition, values = served_condition(q, 'g', served)
        cmd += f' AND {condition}'
    count = db.general_select(cmd, values)[0][0]
    if count:
        ctx.logger.log(
            'error', f'Table "obs_pds" has {count} rows whose bundle_id differs from obs_general'
        )


def validate_previews(ctx: ImportContext) -> None:
    """Report ``obs_general`` rows that have no ``obs_preview`` row.

    The import writes one ``obs_preview`` row for every observation, and the results pages
    read an observation's preview images from it, so an observation without one is an error,
    with the count. While a generation is pending only the observations it added are read
    (`opus_import.validation_queries.GenerationScope`), and while the rows the last switch
    retired await the purge only the served generation's
    (`opus_import.validation_queries.served_generation_only`).

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
    # (^[A-Za-z0-9_]+$); every value is a parameter.
    cmd = f"""
COUNT(*) FROM {q('obs_general')} {q('g')}
LEFT JOIN {q('obs_preview')} {q('p')} ON {q('p')}.{q('obs_general_id')} = {q('g')}.{q('id')}
WHERE {q('p')}.{q('obs_general_id')} IS NULL"""  # nosec B608
    values: list[int] | None = None
    scope = generation_scope(ctx)
    served = served_generation_only(ctx)
    if scope is not None:
        added, values = scope.added(q, 'g')
        cmd += f' AND {added}'
    elif served is not None:
        condition, values = served_condition(q, 'g', served)
        cmd += f' AND {condition}'
    count = db.general_select(cmd, values)[0][0]
    if count:
        ctx.logger.log('error', f'{count} obs_general rows have no obs_preview row')


def validate_junctions(ctx: ImportContext) -> None:
    """Report observations whose ``mult_list`` list and junction rows disagree.

    For each ``mult_list`` column of an observation table the schema holds, the distinct ids
    of each observation's JSON list are compared with its rows of the column's junction
    table, both ways (`ImportDBSuper.list_junction_mismatches`): an id with no junction row,
    or a junction row whose id the list lacks. Either is an error, naming the junction
    table, how many observations disagree and the least ``obs_general`` id among them; so is
    a missing junction table. A junction row whose observation is gone is
    `validate_orphans`' to report, and is counted here too. While a generation is pending
    only the lists and the junction rows of observation ids it could have written are
    compared (`opus_import.validation_queries.GenerationScope.first_id`). With none pending
    every list is compared, a retired observation's included: it keeps both its list and its
    junction rows until the purge deletes them together.

    Parameters:
        ctx: The import run's context, for the open database and the logger.
    """
    db = ctx.db
    assert db is not None
    ctx.logger.log('debug', 'Validating the junction tables of the mult_list columns')
    tables = set(db.table_names(prefix='obs_'))
    scope = generation_scope(ctx)
    first_id = None if scope is None else scope.first_id
    for table_name in sorted(tables):
        schema = import_util.read_schema_for_existing_table(ctx, table_name)
        if schema is None:
            continue
        for column in list_junctions.list_columns(schema):
            junction = list_junctions.junction_table(table_name, column)
            if junction not in tables:
                ctx.logger.log(
                    'error',
                    f'Table "{table_name}" has no junction table "{junction}" for its '
                    f'mult_list column "{column}"',
                )
                continue
            observation = (
                'id'
                if table_keys.is_bundle_keyed_table(table_name)
                else list_junctions.JUNCTION_OBSERVATION_COLUMN
            )
            count, first = db.list_junction_mismatches(
                table_name, column, junction, observation, first_id
            )
            if count:
                ctx.logger.log(
                    'error',
                    f'Junction table "{junction}" disagrees with {table_name}.{column} for '
                    f'{count} observations, the first with obs_general id {first}',
                )


def validate_unique_opus_ids(ctx: ImportContext) -> None:
    """Report OPUS IDs that more than one ``obs_general`` row of one generation carries.

    ``obs_general.opus_id`` carries a plain key, and finalization's duplicate step is what
    leaves one row per OPUS ID, so a schema that has not been through it can hold two.
    Any such id is an error, naming how many there are and the first ten. The rows
    compared are those of the generation the run works on
    (`ImportContext.import_generation`): a re-imported bundle's retired rows share their
    OPUS IDs with its rows in the pending generation, and no generation shows both.

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
    generation = [ctx.import_generation] * 2
    # Every interpolation is an identifier produced by quote_identifier
    # (^[A-Za-z0-9_]+$); the generation is a parameter.
    shared = (
        f'SELECT {q("opus_id")} FROM {obs_general} {q("g")} '  # nosec B608
        f'WHERE {generations.in_generation_condition(q, "g")} '
        f'GROUP BY {q("opus_id")} HAVING COUNT(*) > 1'
    )
    count = db.general_select(f'COUNT(*) FROM ({shared}) {q("d")}', generation)[0][0]  # nosec B608
    if count:
        rows = db.general_select(
            f'{q("opus_id")} FROM ({shared}) {q("d")} '  # nosec B608
            f'ORDER BY {q("opus_id")} LIMIT 10',
            generation,
        )
        shown = ', '.join(f'"{row[0]}"' for row in rows)
        ctx.logger.log(
            'error',
            f'{count} OPUS IDs have more than one obs_general row, among them {shown}; '
            '--finalize keeps one copy of each',
        )


def _log_scope(ctx: ImportContext) -> None:
    """Log what validation reads, unless it reads every row.

    A pending generation's validation names the generation and the observations it added;
    one while retired rows await the purge names the served generation.

    Parameters:
        ctx: The import run's context, for the open database and the logger.
    """
    served = served_generation_only(ctx)
    if served is not None:
        ctx.logger.log(
            'info',
            f'Validating generation {served}, the one served, while the observations the '
            'last switch retired await "opus_import --purge-generations"',
        )
        return
    scope = generation_scope(ctx)
    if scope is None:
        return
    db = ctx.db
    assert db is not None
    count = 0
    if db.table_exists('obs_general'):
        q = db.quote_identifier
        added, values = scope.added(q, 'g')
        # Every interpolation is an identifier produced by quote_identifier
        # (^[A-Za-z0-9_]+$); every value is a parameter.
        cmd = f'COUNT(*) FROM {q("obs_general")} {q("g")} WHERE {added}'  # nosec B608
        count = int(db.general_select(cmd, values)[0][0])
    ctx.logger.log(
        'info',
        f'Validating generation {scope.generation}: {count} observations, from obs_general '
        f'id {scope.first_id}',
    )


def do_validate(ctx: ImportContext) -> bool:
    """Run every validation check, driven by ``--validate``.

    Every check runs, so one run reports every failure; each is logged at error level. While
    a generation is pending the checks read what the update wrote
    (`opus_import.validation_queries.GenerationScope`); while the rows the last switch
    retired await the purge, the served generation
    (`opus_import.validation_queries.served_generation_only`). Either is logged first.

    Parameters:
        ctx: The import run's context, for the open database and the logger.

    Returns:
        True if no check logged an error, False otherwise.
    """
    ctx.logger.open('Performing database validation', limits={'info': -1, 'debug': -1})

    db = ctx.db
    assert db is not None
    pi_table_name = param_info_table(ctx)
    db.forget_table_names()
    _log_scope(ctx)
    described = db.table_exists(pi_table_name)
    if not described:
        ctx.logger.log(
            'error',
            f'"{pi_table_name}" does not exist, so no column is checked against it; '
            '"opus_import --finalize" builds it',
        )
    if described:
        validate_param_info(ctx)
    validate_nulls(ctx)
    if described:
        validate_min_max_order(ctx)
    validate_filter_wavelength_consistency(ctx)
    validate_orphans(ctx)
    validate_pds_bundle_ids(ctx)
    validate_previews(ctx)
    validate_junctions(ctx)
    validate_unique_opus_ids(ctx)

    fatal_count, error_count, _warning_count, _message_count = ctx.logger.close()
    return bool(fatal_count + error_count == 0)
