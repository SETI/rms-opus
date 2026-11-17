"""The columns finalization gives a histogram: the range-searched columns no index leads.

The optimizer estimates how many rows a range condition selects from the index the
column leads, by looking into it. A column that leads no index has no such estimate, and
the optimizer guesses a fixed share of the table's rows, which can make it read the
wrong table of a search first. A histogram on the column (``ANALYZE TABLE ... UPDATE
HISTOGRAM``) gives it a measured estimate instead. A column that leads an index gets
none, since the optimizer reads the index rather than a histogram for it.

The columns are derived, never listed: every row of ``param_info`` whose form type is a
range (`RANGE_FORM_TYPE`), at the table its category's rows are written to
(`opus_import.surface_geometry.physical_table`), less every column the server reports in
the first position of a plain, unique or primary key. Every such row counts, displayed or
not: a range search on the ``1`` column of a pair filters on its ``2`` partner too, whose
row is often not displayed. A longitude (form type ``LONG``)
is searched by its angular separation from the requested centre, an expression no
histogram estimates, so it is not one of them.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from opus_import import surface_geometry
from opus_support import parse_form_type

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping, Sequence

    from opus_import.table_keys import TableKey

#: The form type, less its format and unit, of a search parameter compared as a range.
RANGE_FORM_TYPE = 'RANGE'

#: The table the range-searched columns are read from.
PARAM_INFO_TABLE = 'param_info'

#: The ``param_info`` columns `range_search_columns` reads, in the order it takes them.
PARAM_INFO_COLUMNS = ('category_name', 'name', 'form_type')


def range_search_columns(rows: Iterable[Sequence[Any]]) -> set[tuple[str, str]]:
    """Return the table columns a range search filters on.

    Parameters:
        rows: ``param_info`` rows, each holding `PARAM_INFO_COLUMNS` in order.

    Returns:
        Each range parameter's table and column, the table being the one its category's
        rows are written to.
    """
    columns = set()
    for category_name, name, form_type in rows:
        kind, _format, _unit = parse_form_type(form_type)
        if kind == RANGE_FORM_TYPE:
            columns.add((surface_geometry.physical_table(str(category_name)), str(name)))
    return columns


def histogram_columns(
    range_columns: Iterable[tuple[str, str]], keys: Mapping[str, Sequence[TableKey]]
) -> dict[str, list[str]]:
    """Return the range-searched columns that lead no index, by table.

    Parameters:
        range_columns: Each range-searched table and column (`range_search_columns`).
        keys: Each table's keys, as `ImportDBSuper.read_table_keys` reports them.

    Returns:
        Per table, its columns that lead no plain, unique or primary key, sorted; a table
        with none is absent.
    """
    leading = {
        (table, key.columns[0])
        for table, table_keys in keys.items()
        for key in table_keys
        if key.kind != 'foreign' and len(key.columns) > 0
    }
    columns: dict[str, list[str]] = {}
    for table, column in sorted(set(range_columns)):
        if (table, column) not in leading:
            columns.setdefault(table, []).append(column)
    return columns
