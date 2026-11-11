"""The order a mult field's values and groups are listed in.

Finalization numbers every field's values, ``disp_rank``, and its groups, ``group_rank``,
from what they hold, so the order never depends on the order the values were imported in.
The functions here compute those numbers and touch no database.

A field's values are sorted on a tuple whose first element is the value's **tier**:

1. the pinned values, in order of their pin;
2. the ordinary values;
3. ``Yes`` and ``On``;
4. ``No`` and ``Off``;
5. the absent-value labels, in the order ``None``, ``N/A``, ``NULL``.

Labels are compared case-folded when their tier is decided. Among the ordinary values,
the next element is a number when every ordinary value of the field has one (the stored
value through the column's unit parser when the column has a unit, otherwise the label
read as a number), and the case-folded label otherwise. The label and then the stored
value break every remaining tie, so no two values of a field share a rank.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable, Sequence

#: The labels of the tier after the ordinary values, case-folded.
YES_LABELS = ('yes', 'on')

#: The labels of the tier after that, case-folded.
NO_LABELS = ('no', 'off')

#: The absent-value labels, case-folded, in the order they are listed, after every other
#: value.
ABSENT_LABELS = ('none', 'n/a', 'null')

#: The tiers, in the order they are listed.
_TIER_PINNED = 0
_TIER_ORDINARY = 1
_TIER_YES = 2
_TIER_NO = 3
_TIER_ABSENT = 4


@dataclass(frozen=True)
class RankedValue:
    """What the rank of one ``mult`` row is computed from.

    Attributes:
        id: The row's id within its field.
        value: The stored value; the absent value is the empty string.
        label: How the value is shown.
        pin: The value's pin, or None.
    """

    id: int
    value: str
    label: str
    pin: int | None


@dataclass(frozen=True)
class RankedGroup:
    """What the rank of one ``mult_group`` row is computed from.

    Attributes:
        grouping: The group's name.
        group_pin: The group's pin, or None.
    """

    grouping: str
    group_pin: int | None


def _tier(row: RankedValue) -> int:
    """Return the tier a value is listed in, as the module describes it."""
    if row.pin is not None:
        return _TIER_PINNED
    label = row.label.casefold()
    if label in YES_LABELS:
        return _TIER_YES
    if label in NO_LABELS:
        return _TIER_NO
    if label in ABSENT_LABELS:
        return _TIER_ABSENT + ABSENT_LABELS.index(label)
    return _TIER_ORDINARY


def _number(row: RankedValue, parse: Callable[[str], Any] | None) -> float | None:
    """Return the number an ordinary value sorts by, or None if it has none.

    Parameters:
        row: The value.
        parse: The column's unit parser, or None for a column with no unit.

    Returns:
        The stored value through the parser when there is one, otherwise the label read
        as a number; None when that fails or gives something that is not a finite number.
    """
    try:
        number = float(parse(row.value)) if parse is not None else float(row.label)
    except (ValueError, TypeError, ArithmeticError):
        return None
    return number if math.isfinite(number) else None


def value_ranks(
    rows: Iterable[RankedValue], parse: Callable[[str], Any] | None = None
) -> dict[int, int]:
    """Return the rank of every value of one field.

    Parameters:
        rows: The field's values.
        parse: The column's unit parser (`opus_support.get_single_parse_function`), or
            None for a column with no unit.

    Returns:
        Each value's rank keyed by its id, counting 1, 2, 3, ... in the order the module
        describes, with no gaps and no two values sharing one.
    """
    rows = list(rows)
    tiers = {row.id: _tier(row) for row in rows}
    ordinary = [row for row in rows if tiers[row.id] == _TIER_ORDINARY]
    numbers = {row.id: _number(row, parse) for row in ordinary}
    numeric = all(number is not None for number in numbers.values())

    def key(row: RankedValue) -> tuple[Any, ...]:
        tier = tiers[row.id]
        if tier == _TIER_PINNED:
            return (tier, row.pin, row.label.casefold(), row.label, row.value)
        if tier == _TIER_ORDINARY and numeric:
            return (tier, numbers[row.id], row.label, row.value)
        return (tier, row.label.casefold(), row.label, row.value)

    return {row.id: rank for rank, row in enumerate(sorted(rows, key=key), start=1)}


def group_ranks(groups: Sequence[RankedGroup]) -> dict[str, int]:
    """Return the rank of every group of one field.

    Parameters:
        groups: The field's groups.

    Returns:
        Each group's rank keyed by its name, counting 1, 2, 3, ...: the pinned groups in
        order of their pin, then the others by case-folded name, the name breaking a tie.
    """

    def key(group: RankedGroup) -> tuple[Any, ...]:
        pinned = group.group_pin is not None
        return (not pinned, group.group_pin or 0, group.grouping.casefold(), group.grouping)

    return {group.grouping: rank for rank, group in enumerate(sorted(groups, key=key), start=1)}
