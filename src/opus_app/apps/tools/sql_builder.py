################################################################################
#
# tools/sql_builder.py
#
# Composable assembly of the raw SQL the OPUS API issues through
# django.db.connection.cursor().
#
################################################################################

"""Assemble raw SQL from structure instead of from string concatenation.

Most of the OPUS API is served by hand-written SQL rather than by the ORM: the
search results live in ``search_results``, which has no Django model and is joined as
one search's rows (:func:`search_results_source`), and the queries that join a search
to its results are wide joins over the generated ``obs_*`` tables that are far clearer
as SQL than as ORM expressions.

This module is the one place allowed to turn Python values into SQL text. Every
call site elsewhere describes the *structure* of its statement -- these columns,
this join, that condition -- and this module renders it. That gives three
properties uniformly, none of which a concatenating call site can be checked for
by inspection:

* **Identifiers are quoted and validated.** Every table, column and alias goes
  through :func:`quote_identifier`, which rejects anything outside
  ``[A-Za-z0-9_]`` before handing the name to the database backend's quoting.
  Django's ``quote_name`` wraps a name in backticks but does not escape a backtick
  *inside* it, so validation, not quoting, is what closes that hole. It matters
  here because several identifiers are computed at runtime: the column names that come
  from the ``param_info`` table.
* **Values are always parameters.** Anything that is data is rendered as ``%s``
  and collected into a parameter list; the module never formats a value into SQL
  text. There are exactly **two** exceptions, and both are numbers that shape the
  statement rather than data it operates on, so both are checked with
  ``isinstance(..., int)`` before being rendered literally: ``LIMIT``/``OFFSET``
  (see :meth:`Select.limit`) and the ``MAX_EXECUTION_TIME`` optimizer hint (given to
  the :class:`Select` constructor).

  Note that "MySQL will not accept a placeholder there" would be the wrong reason,
  at least for ``LIMIT``: the server takes one, and so does mysqlclient given an
  ``int``. What mysqlclient does *not* take is a ``LIMIT`` parameter that is not a
  number, because it interpolates client-side and quotes anything else, producing
  ``LIMIT '1'`` and a syntax error. The ``isinstance`` check is therefore the actual
  guarantee, and rendering the value literally states that rather than leaning on
  the driver's type handling.
* **Parameters come out in placeholder order.** A statement is rendered in a fixed
  clause order and each clause contributes its parameters at the point its
  placeholders appear, so a caller cannot get the ordering wrong by appending a
  parameter to the wrong list.

The rendering conventions (a comma with no following space between list items,
``=`` with no surrounding spaces between two columns, spaces around an operator
that compares a column with a parameter) reproduce the SQL these call sites
already emitted, so the refactor that introduced this module is verifiable
against the SQL text the integration suite pins.

The expression layer is deliberately small: it grew from the call sites in
``search``, ``results``, ``cart``, ``metadata`` and ``tools``, and it has no
constructs those call sites do not use.
"""

import re
import unicodedata
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any, NamedTuple

from django.db import connection

from opus_import import list_junctions
from opus_support import UNSTORED_ASCII_CHARACTER

#: The only identifier shape OPUS uses. Table, column and alias names come from
#: the generated models, from the `param_info` table, and from names computed at
#: runtime; none of them ever needs a character outside this set, so anything else
#: is a bug or an injection attempt rather than an exotic identifier.
_IDENTIFIER_RE = re.compile(r'\A[A-Za-z0-9_]+\Z')

#: Operators that may appear between two rendered expressions. Restricting the set
#: means `binary_op` cannot be handed arbitrary SQL text through its operator.
_BINARY_OPERATORS = frozenset(['=', '<', '<=', '>', '>=', '+', '-', 'LIKE', 'NOT LIKE', 'RLIKE'])

#: How the items of a list are separated. No space: the suites assert the exact SQL
#: text of statements built here, so the separator is pinned rather than free.
_SEPARATOR = ','

#: The alias one search's rows of ``search_results`` are joined under
#: (`search_results_source`), whose ``id`` is the observation's ``obs_general.id`` and
#: whose ``sort_order`` is the observation's position in the search's order, 1, 2, 3, ....
SEARCH_RESULTS_ALIAS = 'results'


class SQLIdentifierError(ValueError):
    """Raised when a name that is about to be used as an SQL identifier is unsafe."""


def quote_identifier(name: str) -> str:
    """Return `name` quoted for use as an identifier, rejecting unsafe names.

    Parameters:
        name: The table, column or alias name to quote.

    Returns:
        The name quoted by the database backend (backticks on MySQL).

    Raises:
        SQLIdentifierError: If the name is not a string made up solely of ASCII
            letters, digits and underscores.
    """
    if not isinstance(name, str) or not _IDENTIFIER_RE.match(name):
        raise SQLIdentifierError(f'Unsafe SQL identifier: {name!r}')
    return connection.ops.quote_name(name)


class Expr(NamedTuple):
    """A rendered SQL expression and the parameters its placeholders consume.

    This is a tuple of `(sql, params)` so that the search query builders can keep
    returning that pair to their callers while still handing this module something
    it can compose.
    """

    sql: str
    params: list[Any]


def column(name: str, table: str | None = None) -> Expr:
    """Return a reference to a column, optionally qualified by its table.

    Parameters:
        name: The column name, or the alias of a computed SELECT column.
        table: The table (or table alias) that owns it, or None to leave the
            reference unqualified -- used for a `SELECT ... AS x` alias referred
            to later in `GROUP BY`/`ORDER BY`, and for the columns of a statement
            that names only one table.
    """
    if table is None:
        return Expr(quote_identifier(name), [])
    return Expr(f'{quote_identifier(table)}.{quote_identifier(name)}', [])


def value(val: Any) -> Expr:
    """Return a placeholder that carries `val` as a parameter."""
    return Expr('%s', [val])


def ascii_comparable(text: str, *, compatibility: bool = True) -> str:
    """Return text as it may be compared with a column in the ASCII character set.

    MySQL refuses to compare an ASCII column with text holding any other character
    ("illegal mix of collations"). The text is folded toward ASCII as the accent-blind
    ``utf8mb4_0900_ai_ci`` compares it: decomposed (NFKD), with the combining marks
    dropped, so ``Müller`` compares as ``Muller``, the ligature U+FB01 as ``fi`` and the
    full-width U+FF21 as ``A``, and the ASCII column's own collation ignores the case. A
    character that still has no ASCII form becomes
    `opus_support.UNSTORED_ASCII_CHARACTER`, which the import refuses in an ASCII column
    and ``LIKE`` and a regular expression read as itself, so it matches nothing and the
    comparison finds what it finds for any value the column does not hold: ``=`` and
    ``LIKE`` no row with the character, ``NOT LIKE`` every row.

    A regular expression is folded with canonical decomposition alone (NFD,
    `compatibility` False): the accents still go, but a compatibility character is not
    mapped onto its ASCII form, which may be an operator (the full-width full stop U+FF0E
    would be ``.``, which matches any character). Such a character becomes
    `opus_support.UNSTORED_ASCII_CHARACTER` and matches only itself, which no stored
    value holds.

    Parameters:
        text: A value the caller gave, to be bound as a parameter.
        compatibility: True to decompose compatibility characters as well (NFKD), for a
            value compared literally; False for canonical decomposition alone (NFD), for
            a regular expression.

    Returns:
        The folded text, in ASCII.
    """
    decomposed = unicodedata.normalize('NFKD' if compatibility else 'NFD', text)
    return ''.join(
        c if c.isascii() else UNSTORED_ASCII_CHARACTER
        for c in decomposed
        if not unicodedata.combining(c)
    )


def ascii_collation_key(text: str) -> str:
    """Return the form of text that a comparison with an ASCII column sees.

    Two strings have equal keys exactly when an ASCII column's collation
    (`opus_support.ASCII_COLLATION`) calls their `ascii_comparable` forms equal: the folded text, its trailing
    spaces dropped (the collation pads with spaces) and its letters in lower case (the
    collation ignores case). A value read from such a column is its own folded form, so
    a stored OPUS ID and every caller's spelling that finds it have the same key.

    Parameters:
        text: A value the caller gave, or one read from an ASCII column.

    Returns:
        The key, in ASCII.
    """
    return ascii_comparable(text).rstrip(' ').lower()


def count_star() -> Expr:
    """Return `COUNT(*)`."""
    return Expr('COUNT(*)', [])


def _function(func_name: str, *args: Expr) -> Expr:
    """Return `func_name(arg, ...)` with the arguments' parameters in order."""
    params: list[Any] = []
    for arg in args:
        params += arg.params
    rendered = _SEPARATOR.join(arg.sql for arg in args)
    return Expr(f'{func_name}({rendered})', params)


def count_distinct(expr: Expr) -> Expr:
    """Return `COUNT(DISTINCT expr)`."""
    return Expr(f'COUNT(DISTINCT {expr.sql})', list(expr.params))


def sum_of(expr: Expr) -> Expr:
    """Return `SUM(expr)`."""
    return _function('SUM', expr)


def min_of(expr: Expr) -> Expr:
    """Return `MIN(expr)`."""
    return _function('MIN', expr)


def max_of(expr: Expr) -> Expr:
    """Return `MAX(expr)`."""
    return _function('MAX', expr)


def json_extract_first(expr: Expr) -> Expr:
    """Return `JSON_EXTRACT(expr, "$[0]")`, the first element of a JSON array.

    A MULTIGROUP field has no single value to sort or join on, so the first
    element of its list stands in for it.
    """
    return Expr(f'JSON_EXTRACT({expr.sql}, "$[0]")', list(expr.params))


def angular_separation(longitude_column: Expr, target_longitude: float) -> Expr:
    """Return the angular distance in degrees between a column and a longitude.

    Renders `ABS(MOD(%s - <column> + 540., 360.) - 180.)`, which maps the
    difference of two angles into [0, 180] regardless of how either one wraps
    through 360 degrees. Longitude searches compare this distance against the
    half-width of the user's range and of the observation's own range, which is
    what makes a search that straddles 0 degrees work.
    """
    return Expr(
        f'ABS(MOD(%s - {longitude_column.sql} + 540., 360.) - 180.)',
        [target_longitude, *longitude_column.params],
    )


def binary_op(left: Expr, operator: str, right: Expr) -> Expr:
    """Return `left <operator> right`, with spaces around the operator.

    Parameters:
        left: The left-hand expression.
        operator: One of the operators in `_BINARY_OPERATORS`.
        right: The right-hand expression.

    Raises:
        ValueError: If the operator is not one this module renders.
    """
    if operator not in _BINARY_OPERATORS:
        raise ValueError(f'Unsupported SQL operator: {operator!r}')
    return Expr(f'{left.sql} {operator} {right.sql}', list(left.params) + list(right.params))


def columns_equal(left: Expr, right: Expr) -> Expr:
    """Return `left=right` for two column references, with no surrounding spaces.

    Kept distinct from `binary_op(left, '=', right)` because a join condition and
    a comparison against user data are different things: this one takes no
    parameters at all, which is the property that makes a join condition safe.
    """
    if left.params or right.params:
        raise ValueError('columns_equal takes no parameters')
    return Expr(f'{left.sql}={right.sql}', [])


def is_null(expr: Expr) -> Expr:
    """Return `expr IS NULL`."""
    return Expr(f'{expr.sql} IS NULL', list(expr.params))


def in_values(expr: Expr, vals: list[Any]) -> Expr:
    """Return `expr IN (%s,...)` with one placeholder per value."""
    placeholders = _SEPARATOR.join(['%s'] * len(vals))
    return Expr(f'{expr.sql} IN ({placeholders})', list(expr.params) + list(vals))


def in_sequence(expr: Expr, vals: list[Any] | tuple[Any, ...]) -> Expr:
    """Return `expr IN %s`, passing the whole sequence as one parameter.

    mysqlclient expands a list or tuple parameter into a parenthesized list, so
    this renders the same statement as `in_values` while keeping the sequence a
    single parameter. It is what the call sites that pass an opus_id list already
    used.
    """
    return Expr(f'{expr.sql} IN %s', [*expr.params, vals])


def between(expr: Expr, low: Any, high: Any) -> Expr:
    """Return `expr BETWEEN %s AND %s`, the two bounds as parameters."""
    return Expr(f'{expr.sql} BETWEEN %s AND %s', [*expr.params, low, high])


def sort_order_range(table: str, offset: int, count: int) -> Expr:
    """Return the condition selecting one page of an ordered list by its `sort_order`.

    In a search's results (`search_results_source`), and in the cart listed in a sort
    order with `row_number`, `sort_order` is each row's position, counting 1, 2, 3, ...
    with no gaps. So the `count` rows after the first `offset` are exactly those whose
    `sort_order` lies in the range, and a key on `sort_order` reads only them.

    Parameters:
        table: The table, or the alias of the derived table, whose `sort_order` is
            meant.
        offset: How many rows come before the window.
        count: How many rows the window holds.
    """
    return between(column('sort_order', table), offset + 1, offset + count)


def row_number(order_terms: Sequence[tuple[Expr, bool | None]]) -> Expr:
    """Return `ROW_NUMBER() OVER (ORDER BY ...)`, numbering rows from 1 in that order.

    Parameters:
        order_terms: The sort, as `(expression, descending)` pairs; descending is
            True for DESC, False for ASC, or None for no keyword, as in
            `Select.add_order_by`. With none, the rows are numbered in no stated order,
            as `ROW_NUMBER() OVER ()`.
    """
    if not order_terms:
        return Expr('ROW_NUMBER() OVER ()', [])
    terms: list[str] = []
    params: list[Any] = []
    for expr, descending in order_terms:
        term = expr.sql
        if descending is not None:
            term += ' DESC' if descending else ' ASC'
        terms.append(term)
        params += expr.params
    return Expr(f'ROW_NUMBER() OVER (ORDER BY {_SEPARATOR.join(terms)})', params)


def parenthesize(expr: Expr) -> Expr:
    """Return `(expr)`."""
    return Expr(f'({expr.sql})', list(expr.params))


def join_exprs(exprs: list[Expr], operator: str) -> Expr:
    """Return the expressions joined by `operator`, without adding parentheses.

    Parameters:
        exprs: The expressions to join, in the order their placeholders appear.
        operator: 'AND' or 'OR'.
    """
    if operator not in ('AND', 'OR'):
        raise ValueError(f'Unsupported logical operator: {operator!r}')
    params: list[Any] = []
    for expr in exprs:
        params += expr.params
    return Expr(f' {operator} '.join(expr.sql for expr in exprs), params)


def combine_exprs(exprs: list[Expr], operator: str) -> Expr:
    """Return the expressions combined by `operator`, parenthesized if there is more than one.

    A single expression is returned unchanged, so a one-clause search reads as
    plainly as it did before there was anything to combine it with.

    Parameters:
        exprs: The expressions to combine, in the order their placeholders appear.
        operator: 'AND' or 'OR'.
    """
    if len(exprs) == 1:
        return exprs[0]
    return join_exprs([parenthesize(expr) for expr in exprs], operator)


@dataclass(frozen=True)
class Subquery:
    """A `Select` used as a table source, under a mandatory alias."""

    select: 'Select'
    alias: str

    def render(self) -> tuple[str, list[Any]]:
        """Return the `(sql, params)` of this source as it appears in a FROM clause."""
        sql, params = self.select.build()
        return f'({sql}) AS {quote_identifier(self.alias)}', params


def scalar_subquery(select: 'Select') -> Expr:
    """Return a `Select` of one column and at most one row as a value, `(SELECT ...)`.

    Parameters:
        select: The statement, which may name the outer statement's tables.

    Returns:
        An `Expr` whose SQL is the statement's in parentheses and whose parameters are
        the statement's, in order.
    """
    sql, params = select.build()
    return Expr(f'({sql})', params)


def search_results_source(search_id: int) -> Subquery:
    """Return one search's rows of ``search_results``, as a source to join.

    The source is ``(SELECT obs_general_id AS id, sort_order FROM search_results WHERE
    search_id = %s)`` under `SEARCH_RESULTS_ALIAS`. The server merges a derived table
    this simple into the statement that names it, so a join on ``id`` reads the table's
    ``(search_id, obs_general_id)`` key and a range of ``sort_order`` its primary key.

    Parameters:
        search_id: The search's ``user_searches`` row.
    """
    select = Select()
    select.add_column(column('obs_general_id', 'search_results'), 'id')
    select.add_column(column('sort_order', 'search_results'))
    select.add_from('search_results')
    select.add_where(binary_op(column('search_id', 'search_results'), '=', value(search_id)))
    return Subquery(select, SEARCH_RESULTS_ALIAS)


@dataclass(frozen=True)
class AliasedTable:
    """A table joined under an alias, rendered `<table> AS <alias>`.

    The ``mult`` table is joined once for each mult column a statement reads, each time
    under its own alias, and ``obs_surface_geometry_target`` once for each surface geometry
    category, under the category's name.

    `ignore_for_group_by` names keys the server is not to use for the statement's
    grouping, rendered as MySQL's `IGNORE INDEX FOR GROUP BY (...)` after the alias.
    """

    table: str
    alias: str
    ignore_for_group_by: tuple[str, ...] = ()

    def render(self) -> tuple[str, list[Any]]:
        """Return the `(sql, params)` of this source as it appears in a FROM clause."""
        sql = f'{quote_identifier(self.table)} AS {quote_identifier(self.alias)}'
        if self.ignore_for_group_by:
            keys = ','.join(quote_identifier(key) for key in self.ignore_for_group_by)
            sql += f' IGNORE INDEX FOR GROUP BY ({keys})'
        return sql, []


TableSource = str | Subquery | AliasedTable
"""The sources a FROM clause or a join can name -- a table, a `Subquery` or an
`AliasedTable`."""


def _render_source(source: TableSource) -> tuple[str, list[Any]]:
    """Return the `(sql, params)` for a table name or any other `TableSource`."""
    if isinstance(source, str):
        return quote_identifier(source), []
    return source.render()


def exists(source: TableSource, where: Expr) -> Expr:
    """Return a condition that holds when a source has a row meeting another condition.

    Renders `EXISTS (SELECT 1 FROM <source> WHERE <where>)`. A condition on a table that
    can hold several rows of one observation is put this way rather than as a join, which
    would repeat the observation once for each row it matched.

    Parameters:
        source: The table, or other `TableSource`, the rows are looked for in.
        where: The condition a row must meet, which may name the outer statement's
            tables.

    Returns:
        An `Expr` whose parameters are the source's followed by the condition's, in the
        order their placeholders appear.
    """
    source_sql, params = _render_source(source)
    # The source is rendered from identifiers validated by quote_identifier, and the
    # condition's own values are %s placeholders in where.params.
    return Expr(
        f'EXISTS (SELECT 1 FROM {source_sql} WHERE {where.sql})',  # nosec B608
        params + list(where.params),
    )


def list_contains_any(table: str, column_name: str, mult_ids: Sequence[int]) -> Expr:
    """Return the condition that an observation's ``mult_list`` column holds any of some ids.

    The column's junction table (`opus_import.list_junctions`) holds one row per id of
    each observation's list, so the condition is a semi-join on it: `EXISTS (SELECT 1 FROM
    <junction> WHERE <junction>.obs_general_id=obs_general.id AND <junction>.mult_id IN
    (%s,...))`, one placeholder per id, which reads the junction table's
    ``(mult_id, obs_general_id)`` primary key. The statement it goes into names
    ``obs_general``.

    Parameters:
        table: The table holding the column.
        column_name: The ``mult_list`` column.
        mult_ids: The ids, any of which the list must hold, bound as the integers they
            are.

    Returns:
        An `Expr` whose parameters are the ids, in order.
    """
    junction = list_junctions.junction_table(table, column_name)
    where = join_exprs(
        [
            columns_equal(
                column(list_junctions.JUNCTION_OBSERVATION_COLUMN, junction),
                column('id', 'obs_general'),
            ),
            in_values(
                column(list_junctions.JUNCTION_MULT_COLUMN, junction),
                list(mult_ids),
            ),
        ],
        'AND',
    )
    return exists(junction, where)


@dataclass(frozen=True)
class Join:
    """One join onto a table source."""

    #: 'INNER' or 'LEFT'.
    kind: str
    #: The table name, or other `TableSource`, being joined in.
    source: TableSource
    #: The ON condition.
    on: Expr

    def render(self) -> tuple[str, list[Any]]:
        """Return the `(sql, params)` of this join."""
        if self.kind not in ('INNER', 'LEFT'):
            raise ValueError(f'Unsupported join kind: {self.kind!r}')
        source_sql, params = _render_source(self.source)
        return f' {self.kind} JOIN {source_sql} ON {self.on.sql}', params + list(self.on.params)


@dataclass
class FromSource:
    """One entry of a FROM clause: a table source plus the joins hung off it.

    A statement may have more than one of these, rendered comma-separated. The
    comma binds more loosely than JOIN, so `a, b INNER JOIN c ON ...` joins c to b
    and then cross-joins the result with a -- which is what the cart's download
    summary and the queries that join a search to its results rely on.
    """

    source: TableSource
    joins: list[Join] = field(default_factory=list)

    def add_join(self, kind: str, source: TableSource, on: Expr) -> 'FromSource':
        """Append a join to this source and return self."""
        self.joins.append(Join(kind, source, on))
        return self

    def append_join(self, join: Join) -> 'FromSource':
        """Append a join built elsewhere, such as by `mult_join`, and return self."""
        self.joins.append(join)
        return self

    def render(self) -> tuple[str, list[Any]]:
        """Return the `(sql, params)` of this source and its joins."""
        sql, params = _render_source(self.source)
        for join in self.joins:
            join_sql, join_params = join.render()
            sql += join_sql
            params = params + join_params
        return sql, params


#: The table holding every mult field's values, keyed ``(field_id, id)``.
MULT_TABLE = 'mult'


def mult_join(alias: str, field_id: int, mult_column: Expr) -> Join:
    """Return the join that reads one mult column's labels.

    Renders `LEFT JOIN mult AS <alias> ON <alias>.field_id = %s AND <alias>.id =
    <mult_column>`, the field id as a parameter, so a statement reads each mult column's
    rows of ``mult`` through the table's primary key, under an alias of its own.

    Parameters:
        alias: The alias the join's columns are read under, such as ``<alias>.label``.
        field_id: The ``mult_field`` id of the column's field.
        mult_column: The column holding the id, or an expression giving it.
    """
    on = binary_op(column('field_id', alias), '=', value(field_id))
    on = join_exprs([on, columns_equal(column('id', alias), mult_column)], 'AND')
    return Join('LEFT', AliasedTable(MULT_TABLE, alias), on)


class _OrderBy(NamedTuple):
    """One ORDER BY item. `descending` of None emits no direction keyword."""

    expr: Expr
    descending: bool | None


class Select:
    """A SELECT statement assembled from its parts.

    The clauses are rendered in a fixed order -- columns, FROM (with its joins),
    WHERE, GROUP BY, ORDER BY, LIMIT/OFFSET -- and each contributes its parameters
    where its placeholders appear, so `build()` always returns a parameter list in
    placeholder order.
    """

    def __init__(self, distinct: bool = False, max_execution_time: int | None = None) -> None:
        """Create an empty statement.

        Parameters:
            distinct: True to emit SELECT DISTINCT.
            max_execution_time: Milliseconds, or None. When given, emits MySQL's
                `MAX_EXECUTION_TIME` optimizer hint, which makes the server abort
                the query itself rather than leaving the user waiting. A hint is a
                *comment*, and the server never scans a comment for placeholders --
                preparing one that contains `?` yields a statement with zero
                parameters -- so the value is checked to be an `int` and rendered
                literally, exactly as `limit` is. (mysqlclient would interpolate a
                `%s` here, because it formats the whole query text, comments
                included; that would be relying on an accident of the driver.)
        """
        self._distinct = distinct
        if max_execution_time is not None and not isinstance(max_execution_time, int):
            raise ValueError(
                f'max_execution_time must be an int number of milliseconds: {max_execution_time!r}'
            )
        self._max_execution_time = max_execution_time
        self._columns: list[Expr] = []
        self._from: list[FromSource] = []
        self._where: list[Expr] = []
        self._group_by: list[Expr] = []
        self._order_by: list[_OrderBy] = []
        self._limit: int | None = None
        self._offset: int | None = None

    def add_column(self, expr: Expr, alias: str | None = None) -> 'Select':
        """Add a result column, optionally under an alias, and return self."""
        if alias is not None:
            expr = Expr(f'{expr.sql} AS {quote_identifier(alias)}', expr.params)
        self._columns.append(expr)
        return self

    def add_from(self, source: TableSource) -> FromSource:
        """Add a comma-separated table source and return the `FromSource` for it.

        The return value is the `FromSource`, not the statement, so that joins can
        be hung on the source they belong to.
        """
        return self.add_from_source(FromSource(source))

    def add_from_source(self, from_source: FromSource) -> FromSource:
        """Add an already-built `FromSource` and return it.

        This is for a FROM clause that is assembled once and used by more than one
        statement, which is how the cart's range editor counts the rows it is
        about to change and then changes them.
        """
        self._from.append(from_source)
        return from_source

    def add_where(self, expr: Expr) -> 'Select':
        """AND another condition into the WHERE clause and return self."""
        self._where.append(expr)
        return self

    def add_group_by(self, expr: Expr) -> 'Select':
        """Add a GROUP BY term and return self."""
        self._group_by.append(expr)
        return self

    def add_order_by(self, expr: Expr, descending: bool | None = None) -> 'Select':
        """Add an ORDER BY term and return self.

        Parameters:
            expr: The expression to sort on.
            descending: True for DESC, False for ASC, or None to emit no
                direction keyword and take the server's default.
        """
        self._order_by.append(_OrderBy(expr, descending))
        return self

    def limit(self, count: int) -> 'Select':
        """Set LIMIT and return self.

        The count is rendered as a literal rather than as a parameter: it is a
        row count, never user data that reaches this point unchecked, and both
        call sites have already range-checked it. It must be an `int`, which is
        what makes rendering it literally safe.
        """
        if not isinstance(count, int):
            raise ValueError(f'LIMIT must be an int: {count!r}')
        self._limit = count
        return self

    def offset(self, count: int) -> 'Select':
        """Set OFFSET and return self. The count is an `int`; see `limit`."""
        if not isinstance(count, int):
            raise ValueError(f'OFFSET must be an int: {count!r}')
        self._offset = count
        return self

    def build(self) -> tuple[str, list[Any]]:
        """Return the `(sql, params)` of the finished statement."""
        params: list[Any] = []
        sql = 'SELECT '
        if self._max_execution_time is not None:
            sql += f'/*+ MAX_EXECUTION_TIME({self._max_execution_time}) */ '
        if self._distinct:
            sql += 'DISTINCT '
        sql += _SEPARATOR.join(col.sql for col in self._columns)
        for col in self._columns:
            params += col.params

        from_sql: list[str] = []
        for from_source in self._from:
            source_sql, source_params = from_source.render()
            from_sql.append(source_sql)
            params += source_params
        sql += ' FROM ' + _SEPARATOR.join(from_sql)

        if self._where:
            where = join_exprs(self._where, 'AND')
            sql += f' WHERE {where.sql}'
            params += where.params

        if self._group_by:
            sql += ' GROUP BY ' + _SEPARATOR.join(g.sql for g in self._group_by)
            for group in self._group_by:
                params += group.params

        if self._order_by:
            terms: list[str] = []
            for order in self._order_by:
                term = order.expr.sql
                if order.descending is not None:
                    term += ' DESC' if order.descending else ' ASC'
                terms.append(term)
                params += order.expr.params
            sql += ' ORDER BY ' + _SEPARATOR.join(terms)

        if self._limit is not None:
            sql += f' LIMIT {self._limit}'
        if self._offset is not None:
            sql += f' OFFSET {self._offset}'

        return sql, params


def delete_from(table_name: str, where: Expr) -> tuple[str, list[Any]]:
    """Return the `(sql, params)` of a DELETE from one table.

    Parameters:
        table_name: The table to delete from.
        where: The WHERE condition. It is required: this module has no call site
            that empties a table, and making it optional would let a caller emit
            one by leaving an argument out.
    """
    # The table name is the only interpolation and identifiers are validated by quote_identifier (^[A-Za-z0-9_]+$);
    # the WHERE clause's own values are %s placeholders in where.params.
    return (
        f'DELETE FROM {quote_identifier(table_name)} WHERE {where.sql}',  # nosec B608
        list(where.params),
    )


def delete_joined(target_table: str, from_source: FromSource, where: Expr) -> tuple[str, list[Any]]:
    """Return the `(sql, params)` of a DELETE that selects its rows through a join.

    Renders `DELETE <target> FROM <source> ... WHERE ...`: the rows to delete come
    from `target_table`, but which ones is decided by joining it to another table.

    Parameters:
        target_table: The table whose rows are deleted.
        from_source: The `FromSource` naming that table and its joins.
        where: The WHERE condition.
    """
    from_sql, from_params = from_source.render()
    # Every interpolation is an identifier or an already-rendered clause, and identifiers are validated by quote_identifier (^[A-Za-z0-9_]+$);
    # all values travel in from_params and where.params as %s placeholders.
    return (
        f'DELETE {quote_identifier(target_table)} FROM {from_sql}'  # nosec B608
        f' WHERE {where.sql}',
        from_params + list(where.params),
    )


def _quoted_column_list(column_names: tuple[str, ...] | list[str]) -> str:
    """Return the column names quoted and validated, separated by commas.

    The parentheses that enclose a column list are added by the caller.
    """
    return _SEPARATOR.join(quote_identifier(name) for name in column_names)


def replace_into_values(table_name: str, column_names: tuple[str, ...] | list[str]) -> str:
    """Return the SQL of a `REPLACE INTO <table> (...) VALUES (%s,...)`.

    One placeholder per column, so the statement is what `cursor.executemany` wants:
    the caller supplies one tuple of values per row.

    REPLACE INTO, rather than a delete followed by an insert, is what makes adding
    an observation that is already in the cart safe against a concurrent request:
    the cart table's (session_id, obs_general_id) unique key turns the second write
    into a replacement instead of a duplicate.
    """
    placeholders = _SEPARATOR.join(['%s'] * len(column_names))
    return (
        f'REPLACE INTO {quote_identifier(table_name)}'
        f' ({_quoted_column_list(column_names)}) VALUES ({placeholders})'
    )


def insert_into_select(
    table_name: str, column_names: tuple[str, ...] | list[str], select: Select
) -> tuple[str, list[Any]]:
    """Return the `(sql, params)` of an `INSERT INTO <table> (...) SELECT ...`."""
    sql, params = select.build()
    return (
        f'INSERT INTO {quote_identifier(table_name)} ({_quoted_column_list(column_names)}) {sql}',
        params,
    )


def replace_into_select(
    table_name: str, column_names: tuple[str, ...] | list[str], select: Select
) -> tuple[str, list[Any]]:
    """Return the `(sql, params)` of a `REPLACE INTO <table> (...) SELECT ...`."""
    sql, params = select.build()
    return (
        f'REPLACE INTO {quote_identifier(table_name)} ({_quoted_column_list(column_names)}) {sql}',
        params,
    )


def update(
    table_name: str, assignments: list[tuple[str, Any]], where: Expr
) -> tuple[str, list[Any]]:
    """Return the `(sql, params)` of an UPDATE.

    Parameters:
        table_name: The table to update.
        assignments: A list of `(column_name, value)` pairs. Each value is
            rendered as a parameter.
        where: The WHERE condition. Required, for the reason `delete_from` gives.
    """
    params: list[Any] = []
    sets: list[str] = []
    for column_name, val in assignments:
        sets.append(f'{quote_identifier(column_name)}=%s')
        params.append(val)
    # Table and column names are the only interpolations and identifiers are validated by quote_identifier (^[A-Za-z0-9_]+$);
    # every assigned value is a %s placeholder appended to params above.
    return (
        f'UPDATE {quote_identifier(table_name)} SET '  # nosec B608
        f'{_SEPARATOR.join(sets)} WHERE {where.sql}',
        params + list(where.params),
    )
