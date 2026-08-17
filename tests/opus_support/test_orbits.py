"""Tests for the Cassini orbit-number conversions in ``opus_support``.

These cases were extracted from the ``unittest`` classes that used to live inside
``lib/opus_support.py`` and converted to table-driven pytest tests.
"""

import re

import pytest

from opus_support import format_cassini_orbit, parse_cassini_orbit


@pytest.mark.parametrize('orbit', ['-1', '1', '2'])
def test_parse_cassini_orbit_rejects_bad_orbit(orbit: str) -> None:
    """Numeric orbit names below 3 other than 0 have no letter equivalent."""
    with pytest.raises(ValueError,
                       match=re.escape(f'Invalid Cassini orbit {orbit}')):
        parse_cassini_orbit(orbit)


@pytest.mark.parametrize(('orbit', 'expected'), [
    ('0', -1),
    ('A', 0),
    ('0A', 0),
    ('00A', 0),
    ('a', 0),
    ('0a', 0),
    ('00a', 0),
    ('B', 1),
    ('b', 1),
    ('C', 2),
    ('c', 2),
    ('3', 3),
    ('4', 4),
])
def test_parse_cassini_orbit(orbit: str, expected: int) -> None:
    """Orbit names 0/A/B/C map to -1/0/1/2; 3 and above map to themselves."""
    assert parse_cassini_orbit(orbit) == expected


def test_format_cassini_orbit_rejects_bad_orbit() -> None:
    """There is no orbit name for an internal number below -1."""
    with pytest.raises(ValueError,
                       match=re.escape('Invalid Cassini orbit -2')):
        format_cassini_orbit(-2)


@pytest.mark.parametrize(('value', 'expected'), [
    (-1, '000'),
    (0, '00A'),
    (1, '00B'),
    (2, '00C'),
    (3, '003'),
    (4, '004'),
])
def test_format_cassini_orbit(value: int, expected: str) -> None:
    """Internal orbit numbers format back to their zero-padded orbit names."""
    assert format_cassini_orbit(value) == expected
