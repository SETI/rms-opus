"""The ranks finalization gives a mult field's values and groups.

The rank replaces a sort key the import computed once, when a value was first seen, from
the values already present, so these pin what that key got wrong: the order depended on
the order the values arrived in, negative numbers sorted after positive ones, case decided
the order of two labels, ties had no tiebreaker, and a column with a unit sorted its
absent values among the numbers.
"""

from __future__ import annotations

import itertools

import pytest

import opus_support
from opus_import.mult_rank import RankedGroup, RankedValue, group_ranks, value_ranks


def _values(*labels: str) -> list[RankedValue]:
    """Return unpinned values whose stored value is their label, numbered from 1."""
    return [RankedValue(number, label, label, None) for number, label in enumerate(labels, 1)]


def _order(rows: list[RankedValue], parse: object = None) -> list[str]:
    """Return the rows' labels in the order of their ranks."""
    ranks = value_ranks(rows, parse)  # type: ignore[arg-type]
    by_id = {row.id: row for row in rows}
    return [by_id[row_id].label for row_id in sorted(ranks, key=ranks.__getitem__)]


def test_the_ranks_count_from_one_with_no_gaps() -> None:
    """Every value has its own rank, 1 to the number of values."""
    ranks = value_ranks(_values('b', 'a', 'c', 'a '))

    assert sorted(ranks.values()) == [1, 2, 3, 4]


def test_every_insertion_order_gives_the_same_ranks() -> None:
    """The ranks depend on the values alone, never on the order they were imported in."""
    rows = [
        RankedValue(1, '10', '10', None),
        RankedValue(2, '-3', '-3', None),
        RankedValue(3, '2.5', '2.5', None),
        RankedValue(4, '', 'N/A', None),
        RankedValue(5, 'X', 'Pinned', 0),
    ]
    expected = value_ranks(rows)

    for permutation in itertools.permutations(rows):
        assert value_ranks(list(permutation)) == expected


def test_negative_numbers_sort_before_positive_ones() -> None:
    """Numbers sort as numbers, so -10 comes before -2 and both before 1."""
    assert _order(_values('1', '-2', '-10', '0.5', '10')) == ['-10', '-2', '0.5', '1', '10']


def test_one_label_that_is_not_a_number_sorts_the_field_by_label() -> None:
    """A field whose ordinary values do not all parse sorts by case-folded label."""
    assert _order(_values('10', '9', 'Ten')) == ['10', '9', 'Ten']


def test_case_does_not_decide_the_order_of_two_labels() -> None:
    """Labels compare case-folded, so ``apple`` comes before ``Banana``."""
    assert _order(_values('Banana', 'apple', 'Cherry')) == ['apple', 'Banana', 'Cherry']


def test_labels_equal_but_for_case_are_ordered_by_label_then_value() -> None:
    """A tie on the case-folded label falls to the label, then to the stored value."""
    rows = [
        RankedValue(1, 'b', 'same', None),
        RankedValue(2, 'a', 'same', None),
        RankedValue(3, 'c', 'Same', None),
    ]
    ranks = value_ranks(rows)

    assert sorted(ranks, key=ranks.__getitem__) == [3, 2, 1]


def test_equal_numbers_are_ordered_by_label_then_value() -> None:
    """``1.0`` and ``1`` are one number; the label breaks the tie."""
    assert _order(_values('1.0', '1', '0')) == ['0', '1', '1.0']


def test_yes_and_on_follow_the_ordinary_values_and_no_and_off_follow_them() -> None:
    """The flags' labels form two tiers of their own, after every ordinary value."""
    assert _order(_values('No', 'zebra', 'Yes', 'Off', 'On', 'apple')) == [
        'apple',
        'zebra',
        'On',
        'Yes',
        'No',
        'Off',
    ]


def test_the_absent_values_come_last_in_their_own_order() -> None:
    """``None``, ``N/A`` and ``NULL`` follow everything else, in that order."""
    rows = [
        RankedValue(1, 'NULL', 'NULL', None),
        RankedValue(2, '', 'N/A', None),
        RankedValue(3, 'NONE', 'None', None),
        RankedValue(4, 'B', 'B', None),
        RankedValue(5, 'Y', 'Yes', None),
    ]

    assert _order(rows) == ['B', 'Yes', 'None', 'N/A', 'NULL']


def test_absent_labels_are_compared_case_folded() -> None:
    """``none`` and ``null`` are absent values however they are written."""
    assert _order(_values('null', 'NONE', 'b')) == ['b', 'NONE', 'null']


def test_the_absent_values_of_a_column_with_a_unit_come_last_too() -> None:
    """A unit's parser reads the stored values, and the absent ones still follow them.

    The Cassini orbit parser orders ``00A`` before ``003``, which a plain number cannot.
    """
    parse = opus_support.get_single_parse_function('range_cassini_rev_no')
    assert parse is not None
    rows = [
        RankedValue(1, '', 'N/A', None),
        RankedValue(2, '003', '003', None),
        RankedValue(3, '00A', '00A', None),
        RankedValue(4, '000', '000', None),
    ]

    assert _order(rows, parse) == ['000', '00A', '003', 'N/A']


def test_a_value_the_unit_cannot_parse_sorts_the_field_by_label() -> None:
    """With a unit, one value its parser refuses makes the field sort by label."""
    parse = opus_support.get_single_parse_function('range_cassini_rev_no')
    rows = [
        RankedValue(1, '003', '003', None),
        RankedValue(2, '00A', '00A', None),
        RankedValue(3, 'junk', 'junk', None),
    ]

    assert _order(rows, parse) == ['003', '00A', 'junk']


def test_pinned_values_come_first_in_pin_order() -> None:
    """A pin places a value ahead of every unpinned one, whatever its label."""
    rows = [
        RankedValue(1, 'A', 'Aardvark', None),
        RankedValue(2, 'C', 'Cassini', 0),
        RankedValue(3, 'Z', 'Zulu', None),
        RankedValue(4, 'N', 'N/A', 50),
        RankedValue(5, 'M', 'Middle', 20),
    ]

    assert _order(rows) == ['Cassini', 'Middle', 'N/A', 'Aardvark', 'Zulu']


def test_a_label_like_a_flag_or_absent_value_is_ordinary_when_pinned() -> None:
    """The pin decides first, so a pinned ``Yes`` is listed with the pinned values."""
    rows = [RankedValue(1, 'Y', 'Yes', 2), RankedValue(2, 'N', 'No', 1)]

    assert _order(rows) == ['No', 'Yes']


@pytest.mark.parametrize('label', ['nan', 'inf', '-Infinity'])
def test_a_label_python_reads_as_a_non_finite_number_is_not_a_number(label: str) -> None:
    """``nan`` and ``inf`` are words in a label, so the field sorts by label."""
    assert _order(_values('2', label, '10')) == sorted(['2', label, '10'], key=str.casefold)


def test_groups_are_ranked_by_pin_then_case_folded_name() -> None:
    """The planet groups keep their configured order; a group with no pin follows."""
    groups = [
        RankedGroup('beta', None),
        RankedGroup('Saturn', 60),
        RankedGroup('Alpha', None),
        RankedGroup('Jupiter', 50),
    ]

    assert group_ranks(groups) == {'Jupiter': 1, 'Saturn': 2, 'Alpha': 3, 'beta': 4}
