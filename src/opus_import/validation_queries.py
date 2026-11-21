"""The rows validation reads, and the statements its per-row checks read them with.

`opus_import.steps.do_validate` checks every row while every row is served. While a
generation is pending it checks what the update wrote (`GenerationScope`), and from a
switch until the purge the served generation alone (`served_generation_only`). The
statement builders here take either and give the statement and its values; none of them
reads the database but `filter_groups`, which finds the filters a pending generation's
observations carry.

This module is imported by `opus_import.steps.do_validate` and imports nothing from it.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from opus_import import bundle_registry, generations

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    from opus_import.context import ImportContext
    from opus_import.importdb.super import ImportDBSuper


@dataclass(frozen=True)
class GenerationScope:
    """The rows a pending generation's validation reads: those the update wrote.

    Registration in a pending generation lays each bundle's id range out after every range
    already registered (`bundle_registry.end_before_generation`), so every ``obs_general``
    row the generation adds has an id of at least `first_id`, and every served row's id is
    below it. The observations the generation added are its ``obs_general_rows`` from
    `first_id` up with ``added_generation`` the generation, read by the primary key; their
    rows of another table are the ones whose ``obs_general_id`` is at least `first_id`, read
    by the key every observation table has on that column. The child rows an update deletes
    are its own observations', from `first_id` up, including those of a range it registered
    and then deleted with ``--delete-bundles``, whose registry row is gone; the served rows
    it hides are retired, never deleted, and keep their child rows.

    Attributes:
        generation: The pending generation.
        first_id: The first id after every range an earlier generation registered.
    """

    generation: int
    first_id: int

    def added(self, q: Callable[[str], str], alias: str) -> tuple[str, list[int]]:
        """Return the test that an ``obs_general`` row is one the generation added.

        Parameters:
            q: The database's identifier quoting.
            alias: The alias the row's columns are qualified by, unquoted.

        Returns:
            The condition, and the values its placeholders take.
        """
        row = q(alias)
        return (
            f'{row}.{q("id")} >= %s AND {row}.{q(generations.ADDED_GENERATION_COLUMN)} = %s',
            [self.first_id, self.generation],
        )

    def children(self, q: Callable[[str], str], alias: str) -> tuple[str, list[int]]:
        """Return the test that a row of another table belongs to one of those observations.

        Parameters:
            q: The database's identifier quoting.
            alias: The alias the row's columns are qualified by, unquoted.

        Returns:
            The condition, and the value its placeholder takes.
        """
        return f'{q(alias)}.{q("obs_general_id")} >= %s', [self.first_id]


def generation_scope(ctx: ImportContext) -> GenerationScope | None:
    """Return the rows validation reads while a generation is pending.

    Parameters:
        ctx: The import run's context, for its pending generation and the open database.

    Returns:
        The pending generation's scope, or None when no generation is pending and every
        row is read.
    """
    pending = ctx.pending_generation
    if pending is None:
        return None
    assert ctx.db is not None
    return GenerationScope(pending, bundle_registry.end_before_generation(ctx.db, pending))


def served_generation_only(ctx: ImportContext) -> int | None:
    """Return the served generation while the rows the last switch retired await the purge.

    From a switch until the purge no generation is pending, and ``obs_general_rows`` still
    holds the observations the switch retired, with their rows of the other tables, which
    the ``obs_general`` view hides. The checks then read the served generation alone.

    Parameters:
        ctx: The import run's context, for its generation state.

    Returns:
        The served generation while no generation is pending and the last switch is
        revertible; None otherwise, when either a generation is pending
        (`generation_scope`) or every row is served.
    """
    state = ctx.generation_state
    if state is None or state.pending is not None or not state.revertible:
        return None
    return state.generation


def served_condition(q: Callable[[str], str], alias: str, generation: int) -> tuple[str, list[int]]:
    """Return the test that an ``obs_general`` row is in the served generation.

    Parameters:
        q: The database's identifier quoting.
        alias: The alias the row's columns are qualified by, unquoted.
        generation: The served generation (`served_generation_only`).

    Returns:
        The condition, and the values its placeholders take.
    """
    return generations.in_generation_condition(q, alias), [generation, generation]


def null_count_query(
    db: ImportDBSuper, table_name: str, nullable: Sequence[str], served: int | None
) -> tuple[str, list[int] | None]:
    """Return the query counting the NULLs of each nullable column of a table.

    One scan of the table counts the NULLs in every nullable column, so the check costs
    the same whichever columns carry a key. An empty table's sums are NULL, which counts
    as none found.

    Parameters:
        db: The open database.
        table_name: The observation table.
        nullable: Its columns that allow NULL.
        served: The served generation while retired rows await the purge
            (`served_generation_only`), or None for every row.

    Returns:
        The statement for `ImportDBSuper.general_select`, and its values, or None when it
        has none.
    """
    q = db.quote_identifier
    # Every interpolation is an identifier produced by quote_identifier
    # (^[A-Za-z0-9_]+$); every value is a parameter.
    if served is None:
        counts = ', '.join(f'SUM({q(name)} IS NULL)' for name in nullable)
        return f'{counts} FROM {q(table_name)}', None  # nosec B608
    child, observation = q('c'), q('g')
    counts = ', '.join(f'SUM({child}.{q(name)} IS NULL)' for name in nullable)
    if table_name == generations.OBS_GENERAL_VIEW:
        condition, values = served_condition(q, 'c', served)
        return f'{counts} FROM {q(table_name)} {child} WHERE {condition}', values  # nosec B608
    condition, values = served_condition(q, 'g', served)
    cmd = (
        f'{counts} FROM {q(table_name)} {child} '  # nosec B608
        f'JOIN {q("obs_general")} {observation} ON {observation}.{q("id")} = '
        f'{child}.{q("obs_general_id")} WHERE {condition}'
    )
    return cmd, values


def min_max_query(
    db: ImportDBSuper,
    table_name: str,
    field_name1: str,
    scope: GenerationScope | None,
    served: int | None,
) -> tuple[str, list[int] | None]:
    """Return the query for the OPUS IDs of the rows whose pair of columns is out of order.

    Parameters:
        db: The open database.
        table_name: The observation table.
        field_name1: The pair's low end; its high end ends in ``2`` instead.
        scope: The pending generation's rows (`generation_scope`), or None.
        served: Without a scope, the served generation while retired rows await the purge
            (`served_generation_only`); None with neither, for every row.

    Returns:
        The statement for `ImportDBSuper.general_select`, and its values, or None when it
        has none.
    """
    q = db.quote_identifier
    field_name2 = field_name1[:-1] + '2'
    # Every interpolation is an identifier produced by quote_identifier
    # (^[A-Za-z0-9_]+$); every value is a parameter.
    if scope is None and served is None:
        if table_name == 'obs_general':
            cmd = f"""
{q('opus_id')} FROM {q(table_name)} WHERE
{q(field_name2)} < {q(field_name1)}"""  # nosec B608
        else:
            cmd = f"""
{q('g')}.{q('opus_id')} FROM {q(table_name)} {q('c')}
JOIN {q('obs_general')} {q('g')} ON {q('g')}.{q('id')} = {q('c')}.{q('obs_general_id')}
WHERE {q('c')}.{q(field_name2)} < {q('c')}.{q(field_name1)}"""  # nosec B608
        return cmd, None
    children = ''
    child_values: list[int] = []
    if scope is None:
        assert served is not None
        observations, values = served_condition(q, 'g', served)
    else:
        observations, values = scope.added(q, 'g')
        condition, child_values = scope.children(q, 'c')
        children = f' AND {condition}'
    if table_name == 'obs_general':
        cmd = f"""
{q('g')}.{q('opus_id')} FROM {q(table_name)} {q('g')} WHERE
{q('g')}.{q(field_name2)} < {q('g')}.{q(field_name1)} AND {observations}"""  # nosec B608
        return cmd, values
    cmd = f"""
{q('g')}.{q('opus_id')} FROM {q(table_name)} {q('c')}
JOIN {q('obs_general')} {q('g')} ON {q('g')}.{q('id')} = {q('c')}.{q('obs_general_id')}
WHERE {q('c')}.{q(field_name2)} < {q('c')}.{q(field_name1)}{children}
AND {observations}"""  # nosec B608
    return cmd, child_values + values


#: The ``obs_wavelength`` columns that observations through one filter agree about.
WAVELENGTH_FIELDS = (
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


def filter_groups(
    db: ImportDBSuper, table_name: str, group_columns: Sequence[str], scope: GenerationScope
) -> list[tuple[Any, ...]]:
    """Return the filters the observations a pending generation added carry.

    Parameters:
        db: The open database.
        table_name: The observation table holding the filter.
        group_columns: The columns a filter is grouped by, the filter's last.
        scope: The pending generation's rows (`generation_scope`).

    Returns:
        Each distinct combination of the columns' values, NULL included, as a tuple.
    """
    q = db.quote_identifier
    columns = ', '.join(f'{q("c")}.{q(name)}' for name in group_columns)
    children, child_values = scope.children(q, 'c')
    added, values = scope.added(q, 'g')
    # Every interpolation is an identifier produced by quote_identifier
    # (^[A-Za-z0-9_]+$); every value is a parameter.
    cmd = (
        f'DISTINCT {columns} FROM {q(table_name)} {q("c")} '  # nosec B608
        f'JOIN {q("obs_general")} {q("g")} ON {q("g")}.{q("id")} = '
        f'{q("c")}.{q("obs_general_id")} WHERE {children} AND {added}'
    )
    return [tuple(row) for row in db.general_select(cmd, child_values + values)]


def filter_wavelength_query(
    db: ImportDBSuper,
    table_name: str,
    group_columns: Sequence[str],
    scope: GenerationScope | None,
    groups: Sequence[tuple[Any, ...]],
    served: int | None,
) -> tuple[str, list[Any] | None]:
    """Return the query for each filter's least and greatest wavelength values.

    Parameters:
        db: The open database.
        table_name: The observation table holding the filter.
        group_columns: The columns a filter is grouped by, the filter's last.
        scope: The pending generation's rows (`generation_scope`), or None.
        groups: With a scope, the filters to compare (`filter_groups`); not empty.
        served: Without a scope, the served generation while retired rows await the purge
            (`served_generation_only`); None with neither, for every row.

    Returns:
        The statement for `ImportDBSuper.general_select`, grouped by `group_columns`, and
        its values, or None when it has none. With a scope it reads every observation of
        the pending generation, the served ones it keeps included and the ones it retires
        left out, that carries one of `groups`; with `served`, every observation of the
        served generation.
    """
    q = db.quote_identifier
    child, wavelength = q('c'), q('w')
    grouped = ', '.join(f'{child}.{q(name)}' for name in group_columns)
    ranges = ', '.join(
        f"MIN(IFNULL({wavelength}.{q(name)}, 'NULL')), MAX(IFNULL({wavelength}.{q(name)}, 'NULL'))"
        for name in WAVELENGTH_FIELDS
    )
    # Every interpolation is an identifier produced by quote_identifier
    # (^[A-Za-z0-9_]+$); every value is a parameter.
    source = f'{q(table_name)} {child}'
    joined = (
        f'LEFT JOIN {q("obs_wavelength")} {wavelength} ON '
        f'{child}.{q("obs_general_id")} = {wavelength}.{q("obs_general_id")}'
    )
    observation = q('g')
    if scope is None and served is None:
        cmd = f'{grouped}, {ranges} FROM {source} {joined} GROUP BY {grouped}'  # nosec B608
        return cmd, None
    if scope is None:
        assert served is not None
        condition, served_values = served_condition(q, 'g', served)
        cmd = (
            f'{grouped}, {ranges} FROM {source} '  # nosec B608
            f'JOIN {q("obs_general")} {observation} ON {observation}.{q("id")} = '
            f'{child}.{q("obs_general_id")} {joined} '
            f'WHERE {condition} GROUP BY {grouped}'
        )
        return cmd, list(served_values)
    live = generations.in_generation_condition(q, 'g')
    match = ' AND '.join(f'{child}.{q(name)} <=> %s' for name in group_columns)
    carried = ' OR '.join(f'({match})' for _group in groups)
    cmd = (
        f'{grouped}, {ranges} FROM {source} '  # nosec B608
        f'JOIN {q("obs_general")} {observation} ON {observation}.{q("id")} = '
        f'{child}.{q("obs_general_id")} {joined} '
        f'WHERE {live} AND ({carried}) GROUP BY {grouped}'
    )
    values: list[Any] = [scope.generation, scope.generation]
    for group in groups:
        values.extend(group)
    return cmd, values
