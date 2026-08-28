"""Tests for the time parsing and formatting helpers in ``opus_support``.

The arithmetic belongs to ``julian``, which has its own suite, so these tests check only
that ``opus_support`` picks the right representation for each epoch, enforces its
supported date range, and formats a parsed value back to the string it came from.
"""

import re
from collections.abc import Callable

import pytest

from opus_support import (
    format_time_et,
    format_time_jd,
    format_time_jed,
    format_time_mjd,
    format_time_mjed,
    format_time_ydoy,
    format_time_ymd,
    parse_time,
)

# TAI values reach hundreds of millions of seconds, where pytest.approx's
# relative default would tolerate whole minutes, so epoch comparisons state an
# absolute tolerance instead: half a millisecond.
TIME_ABS_TOL = 5e-4


@pytest.mark.parametrize(
    ('formatter', 'tai', 'expected'),
    [
        (format_time_ymd, 0, '2000-01-01T11:59:28.000'),
        (format_time_ymd, 600000000, '2019-01-05T22:39:23.000'),
        (format_time_ydoy, 0, '2000-001T11:59:28.000'),
        (format_time_ydoy, 600000000, '2019-005T22:39:23.000'),
        (format_time_jd, 0, 'JD2451544.99962963'),
        (format_time_jd, 600000000, 'JD2458489.44401620'),
        (format_time_jed, 0, 'JED2451545.00037250'),
        (format_time_jed, 600000000, 'JED2458489.44481695'),
        (format_time_mjd, 0, 'MJD51544.49962963'),
        (format_time_mjd, 600000000, 'MJD58488.94401620'),
        (format_time_mjed, 0, 'MJED51544.50037250'),
        (format_time_mjed, 600000000, 'MJED58488.94481695'),
        (format_time_et, 0, '32.184'),
        (format_time_et, 600000000, '600000032.184'),
    ],
)
def test_format_time(formatter: Callable[[float], str], tai: float, expected: str) -> None:
    """Each time formatter renders a TAI value in its own calendar or epoch."""
    assert formatter(tai) == expected


@pytest.mark.parametrize(
    ('iso', 'expected'),
    [
        ('2000-01-01T11:59:28.000', 0),
        ('2019-005T22:39:23.000', 600000000),
    ],
)
def test_parse_time_exact(iso: str, expected: float) -> None:
    """ISO date strings parse to an exact TAI value."""
    assert parse_time(iso) == expected


@pytest.mark.parametrize(
    ('iso', 'unit', 'expected'),
    [
        ('JD2451544.99962963', None, 0),
        ('JD2458489.44401620', None, 600000000),
        ('JED2451544.49962963', None, -43199.999987363815),
        ('JED2458488.94401620', None, 599956799.9996822),
        ('MJD51543.99962963', None, -43199.99996787589),
        ('MJD58488.44401620', None, 599956799.9996803),
        ('MJED51543.99962963', None, -43199.999987363815),
        ('MJED58488.44401620', None, 599956799.9996822),
        ('2000-01-01 UTC', None, -43168.0),
        ('2000-01-01 TDB', None, -43168.0),
        # A bare number is interpreted using the caller-supplied unit.
        ('2458489.44401620', 'jd', 600000000),
        ('2451544.49962963', 'jed', -43199.999987363815),
        ('58488.44401620', 'mjd', 599956799.9996803),
        ('51543.99962963', 'mjed', -43199.99996787589),
        ('50000', 'et', 49967.816055978896),
    ],
)
def test_parse_time_epochs(iso: str, unit: str | None, expected: float) -> None:
    """Prefixed and bare epoch values parse to the expected TAI value."""
    assert parse_time(iso, unit=unit) == pytest.approx(expected, abs=TIME_ABS_TOL)


@pytest.mark.parametrize(
    ('iso', 'message'),
    [
        ('nan', 'Invalid time syntax: nan'),
        ('inf', 'Invalid time syntax: inf'),
        ('2000', 'Invalid time syntax: 2000'),
        ('2000-01-01. TAI', 'Invalid time syntax: 2000-01-01. TAI'),
        ('2000-01-01 TAI', 'Invalid time system TAI when parsing 2000-01-01 TAI'),
    ],
)
def test_parse_time_rejects_bad_syntax(iso: str, message: str) -> None:
    """Unparseable strings and unsupported time systems raise ValueError."""
    with pytest.raises(ValueError, match=re.escape(message)):
        parse_time(iso)


def test_parse_time_rejects_out_of_range_date() -> None:
    """Dates outside the years 1000-2999 raise a bare, message-less ValueError.

    The empty message is asserted rather than glossed over because it is the
    module's current contract; giving it text would be a behavior change.
    """
    with pytest.raises(ValueError) as excinfo:
        parse_time('JD9999999999')
    assert str(excinfo.value) == ''


@pytest.mark.parametrize('unit', ['jed', 'mjd', 'mjed'])
def test_parse_time_rejects_an_epoch_too_large_to_convert(unit: str) -> None:
    """An epoch too large for the conversion is rejected, not raised through.

    ``julian`` accepts a Julian date far outside its own supported range and only
    fails when converting it, with an ``OverflowError`` rather than a
    ``ValueError``. Anything but a ``ValueError`` escapes the caller's guard and
    reaches the user as an internal error rather than as a rejected value.
    """
    with pytest.raises(ValueError) as excinfo:
        parse_time('9' * 30, unit=unit)
    assert str(excinfo.value) == f'Invalid time syntax: {unit.upper()}{"9" * 30}'
    assert isinstance(excinfo.value.__cause__, OverflowError)


@pytest.mark.parametrize(
    ('formatter', 'iso', 'expected'),
    [
        (format_time_ymd, '2015-05-03T10:12:34.123', '2015-05-03T10:12:34.123'),
        (format_time_ydoy, '2015-122T10:12:34.123', '2015-122T10:12:34.123'),
        (format_time_jd, 'JD2234567.123', 'JD2234567.12300000'),
        (format_time_jed, 'JED2234567.123', 'JED2234567.12348824'),
    ],
)
def test_parse_time_round_trip(formatter: Callable[[float], str], iso: str, expected: str) -> None:
    """Formatting a parsed time reproduces the original string."""
    assert formatter(parse_time(iso)) == expected
