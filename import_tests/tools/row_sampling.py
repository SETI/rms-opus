"""Choose the index rows a fixture volume keeps, by code path rather than by position.

A volume's early rows are its least interesting: a mission's first volume is
pre-encounter, and the first rows of any index are one instrument mode repeated. What
the import branches on is not a value's magnitude but its *class* -- which enumerated
value it is, whether it is present at all, whether a longitude range wraps -- so this
module scores rows on classes and keeps adding the row that introduces the most unseen
ones.

An exposure of 0.1 s and one of 100 s execute exactly the same code, so numeric spread
buys nothing and is not scored. What is scored is the value itself only where the column
is an enumeration -- few enough distinct values, and fewer than it has rows -- which is
what an OPUS ``mult`` column is made from. An identifier column, whose value is different
in every row, would otherwise drown every real class in noise.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from typing import Any

import numpy

#: Below this many rows a volume is not sampled at all: every row is kept.
ROW_FLOOR = 2

#: The most rows any volume contributes, whatever its class count. Labels and shelf
#: manifests dominate the fixture's size and do not grow with the row count, so this is
#: a bound on runtime rather than on bytes.
ROW_CAP = 20

#: The most distinct values a column can hold and still be read as an enumeration. A
#: column with more than this is a measurement or an identifier, whose individual values
#: no code path branches on.
ENUM_VALUE_CAP = 200

#: Strings that mean "no value here" in a PDS index, whatever the column. Compared
#: after stripping and upper-casing.
SENTINEL_STRINGS = frozenset(
    {
        '',
        'N/A',
        'NULL',
        'UNK',
        'NONE',
        'UNKNOWN',
        'NOT APPLICABLE',
        'UNAVAILABLE',
    }
)

#: A float at or beyond this magnitude is a PDS fill value rather than a measurement.
#: The archives use -1e32 and its relatives; no real quantity OPUS imports is this big.
SENTINEL_FLOAT_MAGNITUDE = 1e30

#: The class every present-and-unremarkable value collapses into.
PRESENT_CLASS = 'present'

#: The class every absent or fill value collapses into, whatever its spelling.
MISSING_CLASS = 'missing'

#: The two classes a paired minimum/maximum column gets, which is the wraparound case
#: the longitude code branches on.
WRAPPED_CLASS = 'wrapped'
UNWRAPPED_CLASS = 'unwrapped'

#: How a column name spells the two ends of a range. A pair is recognized when two
#: columns differ only by swapping the first spelling for the second.
_RANGE_SUFFIXES = (('_MINIMUM', '_MAXIMUM'), ('_MIN', '_MAX'))


def is_missing(value: Any) -> bool:
    """Return whether a value means "nothing here".

    Parameters:
        value: A value out of an index row.

    Returns:
        True for None, for a string the archives use to mean absent, and for a float
        that is a fill value rather than a measurement.
    """
    if value is None:
        return True
    if isinstance(value, str):
        return value.strip().upper() in SENTINEL_STRINGS
    if isinstance(value, float):
        return math.isnan(value) or abs(value) >= SENTINEL_FLOAT_MAGNITUDE
    return False


def _plain(value: Any) -> Any:
    """Return a hashable Python value for whatever a table reader produced.

    Parameters:
        value: One scalar out of an index row.

    Returns:
        The value itself, or the Python equivalent of a NumPy scalar, which `pdstable`
        produces for a typed column and which does not compare equal across dtypes.
    """
    if isinstance(value, numpy.generic):
        return value.item()
    return value


def _cells(column: str, value: Any) -> list[tuple[str, Any]]:
    """Return the scalar cells one column of one row holds.

    Parameters:
        column: The column name.
        value: Its value, which a multi-valued PDS column makes a sequence -- a NumPy
            array, where `pdstable` typed the column.

    Returns:
        (cell name, scalar) pairs. A sequence contributes one per element, keyed by
        position, because an instrument reads those positions separately.
    """
    if isinstance(value, (list, tuple, numpy.ndarray)):
        return [(f'{column}[{i}]', _plain(item)) for i, item in enumerate(value)]
    return [(column, _plain(value))]


def enumerated_cells(rows: Sequence[dict[str, Any]]) -> set[str]:
    """Return the cells whose distinct values are worth scoring individually.

    Parameters:
        rows: Every row of one index file.

    Returns:
        The cell names that hold an enumeration: at most `ENUM_VALUE_CAP` distinct
        present values, and fewer distinct values than the index has rows. A column
        holding a different value in every row is an identifier, not an enumeration.
    """
    seen: dict[str, set[Any]] = {}
    for row in rows:
        for column, value in row.items():
            for name, item in _cells(column, value):
                if is_missing(item):
                    continue
                seen.setdefault(name, set()).add(item)
    return {
        name
        for name, values in seen.items()
        if len(values) <= ENUM_VALUE_CAP and len(values) < len(rows)
    }


def _cell_class(value: Any, *, enumerated: bool) -> str:
    """Return the class one scalar value puts its cell in.

    Parameters:
        value: The scalar.
        enumerated: True if this cell's distinct values are worth scoring individually.

    Returns:
        `MISSING_CLASS`, ``=<value>`` for an enumerated cell, or `PRESENT_CLASS`.
    """
    if is_missing(value):
        return MISSING_CLASS
    if not enumerated:
        return PRESENT_CLASS
    if isinstance(value, str):
        return f'={value.strip()}'
    return f'={value}'


def _range_pairs(columns: Sequence[str]) -> list[tuple[str, str]]:
    """Return the minimum/maximum column pairs among a set of column names.

    Parameters:
        columns: Every column name in the index.

    Returns:
        The (minimum column, maximum column) pairs, in the order the minimum columns
        appear.
    """
    present = set(columns)
    pairs = []
    for column in columns:
        for low, high in _RANGE_SUFFIXES:
            if column.endswith(low):
                partner = column[: -len(low)] + high
                if partner in present:
                    pairs.append((column, partner))
                break
    return pairs


def row_classes(
    row: dict[str, Any], range_pairs: Sequence[tuple[str, str]], enumerated: set[str]
) -> set[tuple[str, str]]:
    """Return every (cell, class) pair one index row covers.

    Parameters:
        row: One index row, as `pdstable` or the PDS4 CSV reader produced it.
        range_pairs: The minimum/maximum column pairs, from `_range_pairs`.
        enumerated: The cells whose values are scored individually.

    Returns:
        The pairs. A range pair contributes one extra pair of its own, keyed by the two
        column names, whose class says whether the range wraps.
    """
    pairs: set[tuple[str, str]] = set()
    for column, value in row.items():
        for name, item in _cells(column, value):
            pairs.add((name, _cell_class(item, enumerated=name in enumerated)))
    for low, high in range_pairs:
        low_value = row.get(low)
        high_value = row.get(high)
        if is_missing(low_value) or is_missing(high_value):
            continue
        if not isinstance(low_value, (int, float)) or not isinstance(high_value, (int, float)):
            continue
        wrapped = WRAPPED_CLASS if low_value > high_value else UNWRAPPED_CLASS
        pairs.add((f'{low}/{high}', wrapped))
    return pairs


def _all_row_classes(rows: Sequence[dict[str, Any]]) -> list[set[tuple[str, str]]]:
    """Return the classes each row of an index covers.

    Parameters:
        rows: Every row of one index file.

    Returns:
        One set of (cell, class) pairs per row, in row order.
    """
    if len(rows) == 0:
        return []
    range_pairs = _range_pairs(list(rows[0].keys()))
    enumerated = enumerated_cells(rows)
    return [row_classes(row, range_pairs, enumerated) for row in rows]


def select_rows(
    rows: Sequence[dict[str, Any]], *, floor: int = ROW_FLOOR, cap: int = ROW_CAP
) -> list[int]:
    """Choose which rows of an index the fixture keeps.

    The first row chosen is the one covering the most classes; after that the row
    covering the most classes nothing chosen so far covers is added, until every class
    the index shows is covered or the cap is reached. Ties go to the lower row number,
    so the result depends only on the index's contents.

    Parameters:
        rows: Every row of one index file, in file order.
        floor: The fewest rows to keep, when the index has at least that many.
        cap: The most rows to keep.

    Returns:
        The row numbers to keep, ascending. An index with no more rows than the floor
        keeps all of them.
    """
    if len(rows) <= floor:
        return list(range(len(rows)))

    per_row = _all_row_classes(rows)
    chosen: list[int] = []
    taken: set[int] = set()
    covered: set[tuple[str, str]] = set()
    limit = min(cap, len(rows))
    while len(chosen) < limit:
        best_row = -1
        best_gain = -1
        for row_no, classes in enumerate(per_row):
            if row_no in taken:
                continue
            gain = len(classes - covered)
            if gain > best_gain:
                best_gain = gain
                best_row = row_no
        if best_gain <= 0 and len(chosen) >= floor:
            break
        chosen.append(best_row)
        taken.add(best_row)
        covered |= per_row[best_row]

    return sorted(chosen)


def uncovered_classes(
    rows: Sequence[dict[str, Any]], chosen: Sequence[int]
) -> set[tuple[str, str]]:
    """Return the classes an index shows that the chosen rows do not cover.

    Parameters:
        rows: Every row of the index.
        chosen: The row numbers `select_rows` returned.

    Returns:
        The pairs left over, which is what the cap cost this volume. An empty set means
        the sample reaches every branch the index can send the import down.
    """
    per_row = _all_row_classes(rows)
    everything: set[tuple[str, str]] = set()
    for classes in per_row:
        everything |= classes
    covered: set[tuple[str, str]] = set()
    for row_no in chosen:
        covered |= per_row[row_no]
    return everything - covered


def column_profile(rows: Sequence[dict[str, Any]]) -> dict[str, set[str]]:
    """Return the classes each cell of an index shows.

    This is what makes "does this volume's index carry fundamentally different values
    from the one the fixture chose?" a check rather than a memory.

    Parameters:
        rows: Every row of one index file.

    Returns:
        The set of classes seen, keyed by cell name.
    """
    profile: dict[str, set[str]] = {}
    for classes in _all_row_classes(rows):
        for name, class_name in classes:
            profile.setdefault(name, set()).add(class_name)
    return profile
