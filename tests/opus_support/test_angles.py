"""Tests for the DMS/HMS angle conversions in ``opus_support``.

The DMS and HMS parsers share one implementation that differs only in which letter it
accepts and whether the result is scaled by 15, so they share one table of cases:
``{L}`` is replaced by the parser's letter and the expected value is multiplied by the
``ANGLE_SCALE`` entry for that letter.
"""

from collections.abc import Callable

import pytest

from opus_support import (
    format_dms_hms,
    parse_dms,
    parse_dms_hms,
    parse_hms,
    parse_hms_dms,
)

ANGLE_PARSERS = [
    pytest.param(parse_dms, 'd', id='dms'),
    pytest.param(parse_hms, 'h', id='hms'),
]

# An HMS value is in hours, so parsing the same digits as HMS gives fifteen times the
# DMS result. Keyed by letter so the parser table above stays the single source of truth.
ANGLE_SCALE = {'d': 1, 'h': 15}


@pytest.mark.parametrize(('parser', 'letter'), ANGLE_PARSERS)
@pytest.mark.parametrize(('text', 'expected'), [
    # All three components present.
    ('0{L} 0m 0s', 0),
    ('1{L} 0m 0s', 1),
    ('0{L} 30m 0s', 0.5),
    ('0{L} 0m 36s', 0.01),
    ('23{L} 30m 36s', 23.51),
    # Prime/double-prime and their Unicode equivalents stand in for m and s.
    ("23{L} 30' 36\"", 23.51),
    ("23{L} 30' 36''", 23.51),
    # U+2032 PRIME and U+2033 DOUBLE PRIME, written as escapes so the
    # literals cannot be confused with the ASCII quotes above.
    ('23{L} 30\u2032 36\u2033', 23.51),
    # Signs and surrounding whitespace.
    ('+23{L} 30m 36s', 23.51),
    (' + 23{L}  30m 36s', 23.51),
    ('-23{L} 30m 36s', -23.51),
    (' - 23{L}  30m 36s', -23.51),
    # Only the last component present may have a fractional part.
    ('23.{L} 30.m 36.36s', 23.5101),
    ('23.{L}   30.m   36.36s', 23.5101),
    ('23.{L}30.m36.36s', 23.5101),
    ('23.000{L} 30.000m 36.36000s', 23.5101),
    # Components may be omitted.
    ('0{L} 0m', 0),
    ('0{L} 0.30m', 0.005),
    ('0{L} 0s', 0),
    ('0{L} 36.36s', 0.0101),
    ('0m 0s', 0),
    ('10{L}', 10),
    ('10.123{L}', 10.123),
    ('0m', 0),
    ('30m', 0.5),
    ('30.30m', 0.505),
    ('36s', 0.01),
    ('36.36s', 0.0101),
    # Space-separated triples and bare numbers.
    ('0 0 0', 0),
    ('1 30 36.36', 1.5101),
    ('123.456', 123.456),
    # Exponential notation is allowed in the leading component only.
    ('1000000000{L} 0m 0s', 1000000000),
    ('1e+9{L} 0m 0s', 1000000000),
    ('1e+0009{L} 0m 0s', 1000000000),
])
def test_parse_angle(parser: Callable[..., float], letter: str, text: str,
                     expected: float) -> None:
    """DMS and HMS strings parse to degrees; HMS values are scaled by 15."""
    assert parser(text.format(L=letter)) == expected * ANGLE_SCALE[letter]


@pytest.mark.parametrize(('parser', 'text', 'expected'), [
    (parse_dms, '23D 30M 36S', 23.51),
    (parse_dms, '1E+0009d 0m 0s', 1000000000),
    (parse_hms, '23H 30M 36S', 23.51*15),
])
def test_parse_angle_is_case_insensitive(parser: Callable[..., float],
                                         text: str, expected: float) -> None:
    """Component letters and exponent markers may be upper case."""
    assert parser(text) == expected


def test_parse_dms_accepts_degree_symbol() -> None:
    """The degree symbol is an accepted spelling of the DMS degree letter."""
    assert parse_dms('23° 30m 36s') == 23.51


@pytest.mark.parametrize(('parser', 'letter'), ANGLE_PARSERS)
@pytest.mark.parametrize(('text', 'expected'), [
    # A bare number is already in the target unit, so it is not converted.
    ('123.456', 123.456),
    # An explicit unit letter means the value must be converted.
    ('123.456{L}', 123.456/2),
])
def test_parse_angle_conversion_factor(parser: Callable[..., float], letter: str,
                                       text: str, expected: float) -> None:
    """``conversion_factor`` applies only when the unit is stated explicitly."""
    assert parser(text.format(L=letter),
                  conversion_factor=2) == expected * ANGLE_SCALE[letter]


@pytest.mark.parametrize(('parser', 'letter'), ANGLE_PARSERS)
@pytest.mark.parametrize('text', [
    # Only the last stated component may be fractional.
    ('23.1{L} 30m 36s'),
    ('23.1{L} 30m'),
    ('23{L} 30.123m 36s'),
    ('30.123m 36s'),
    # Minutes and seconds must be below 60.
    ('60m'),
    ('1234m'),
    ('60s'),
    ('1234s'),
    # An overflowing exponent yields a non-finite value.
    ('1e400'),
])
def test_parse_angle_rejects_bad_components(parser: Callable[..., float],
                                            letter: str, text: str) -> None:
    """Out-of-range components raise a bare, message-less ValueError.

    The empty message is asserted rather than glossed over because it is the
    module's current contract; giving it text would be a behavior change.
    """
    with pytest.raises(ValueError) as excinfo:
        parser(text.format(L=letter))
    assert str(excinfo.value) == ''


@pytest.mark.parametrize(('parser', 'text'), [
    # The wrong unit letter is not recognized, so the whole string is offered
    # to float() as a plain number.
    (parse_dms, '23h 30m 36s'),
    (parse_dms, '1e400h'),
    (parse_hms, '23d 30m 36s'),
    (parse_hms, '1e400d'),
    # A space-separated pair is neither a triple nor a number.
    (parse_dms, '12 23'),
    (parse_hms, '12 23'),
])
def test_parse_angle_rejects_non_numeric(parser: Callable[..., float],
                                         text: str) -> None:
    """Strings that are neither DMS/HMS nor a number fail the float conversion."""
    with pytest.raises(ValueError, match='could not convert string to float'):
        parser(text)


def test_parse_dms_rejects_overflowing_degrees() -> None:
    """``parse_dms`` accepts the degree letter, so the overflow is caught late."""
    with pytest.raises(ValueError) as excinfo:
        parse_dms('1e400d')
    assert str(excinfo.value) == ''


@pytest.mark.parametrize(('text', 'expected'), [
    ('1d 30m 36s', 1.51),
    ('1h 30m 36s', 1.51*15),
    # A space-separated triple falls back to the parser's default format.
    ('1 30 36', 1.51),
    ('1.5', 1.5),
])
def test_parse_dms_hms(text: str, expected: float) -> None:
    """``parse_dms_hms`` accepts either format and defaults to DMS."""
    assert parse_dms_hms(text) == expected


@pytest.mark.parametrize(('text', 'expected'), [
    ('1.5', 1.5),
    ('1 30 36', 1.51/2),
    ('1.5d', 1.5/2),
    ('1.5h', 1.5*15/2),
])
def test_parse_dms_hms_conversion_factor(text: str, expected: float) -> None:
    """``parse_dms_hms`` leaves a bare number alone but converts stated units."""
    assert parse_dms_hms(text, conversion_factor=2) == expected


@pytest.mark.parametrize(('text', 'expected'), [
    ('1d 30m 36s', 1.51),
    ('1h 30m 36s', 1.51*15),
    # A space-separated triple falls back to the parser's default format.
    ('1 30 36', 1.51*15),
    ('1.5', 1.5*15),
])
def test_parse_hms_dms(text: str, expected: float) -> None:
    """``parse_hms_dms`` accepts either format and defaults to HMS."""
    assert parse_hms_dms(text) == expected


@pytest.mark.parametrize(('text', 'expected'), [
    ('1 30 36', 1.51*15/2),
    ('1.5d', 1.5/2),
    ('1.5h', 1.5*15/2),
])
def test_parse_hms_dms_conversion_factor(text: str, expected: float) -> None:
    """``parse_hms_dms`` converts stated units by the conversion factor."""
    assert parse_hms_dms(text, conversion_factor=2) == expected


@pytest.mark.parametrize('parser', [parse_dms_hms, parse_hms_dms])
@pytest.mark.parametrize('text', ['1e400d', '1e400h', '1e400'])
def test_parse_dms_hms_rejects_overflow(parser: Callable[..., float],
                                        text: str) -> None:
    """Both mixed parsers reject values that overflow to infinity."""
    with pytest.raises(ValueError) as excinfo:
        parser(text)
    assert str(excinfo.value) == ''


@pytest.mark.parametrize(('val', 'unit', 'numerical_format', 'keep_zeros',
                          'expected'), [
    # Plain degrees.
    (0, 'degrees', '.3f', True, '0.000'),
    (0, 'degrees', '.3f', False, '0'),
    (123.4, 'degrees', '.3f', True, '123.400'),
    (123.4, 'degrees', '.3f', False, '123.4'),
    (123.456789, 'degrees', '.3f', True, '123.457'),
    (123.456789, 'degrees', '.3f', False, '123.457'),
    (-123.456789, 'degrees', '.3f', False, '-123.457'),
    (1e7, 'degrees', '.3f', False, '10000000'),
    (1e8, 'degrees', '.3f', False, '1e+08'),
    (1.01e8, 'degrees', '.3f', False, '1.01e+08'),
    # Hours: the value is divided by 15 and gains two decimal places.
    (0, 'hours', '.3f', True, '0.00000'),
    (0, 'hours', '.3f', False, '0'),
    (121.86, 'hours', '.3f', True, '8.12400'),
    (121.86, 'hours', '.3f', False, '8.124'),
    (123.456789, 'hours', '.3f', True, '8.23045'),
    (123.456789, 'hours', '.3f', False, '8.23045'),
    (-123.456789, 'hours', '.3f', False, '-8.23045'),
    (15e8, 'hours', '.3f', False, '1e+08'),
    (15.15e8, 'hours', '.3f', False, '1.01e+08'),
    # Radians also gain two decimal places.
    (0, 'radians', '.3f', True, '0.00000'),
    (0, 'radians', '.3f', False, '0'),
    (1e7, 'radians', '.3f', False, '10000000'),
    (1e8, 'radians', '.3f', False, '1e+08'),
    (1.01e8, 'radians', '.3f', False, '1.01e+08'),
    # DMS: the format applies to the seconds field, three digits smaller.
    (0, 'dms', '.6f', False, '0d 00m 00s'),
    (0, 'dms', '.6f', True, '0d 00m 00.000s'),
    (0.0001, 'dms', '.6f', False, '0d 00m 00.36s'),
    (0.0001, 'dms', '.6f', True, '0d 00m 00.360s'),
    (-0.0001, 'dms', '.6f', False, '-0d 00m 00.36s'),
    (-0.0001, 'dms', '.6f', True, '-0d 00m 00.360s'),
    (700, 'dms', '.6f', False, '700d 00m 00s'),
    # Rounding the seconds field carries into minutes and degrees.
    (699.99999987, 'dms', '.6f', False, '700d 00m 00s'),
    (699.99999986, 'dms', '.6f', False, '699d 59m 59.999s'),
    (-699.99999986, 'dms', '.6f', False, '-699d 59m 59.999s'),
    (1e7, 'dms', '.3f', False, '10000000d 00m 00s'),
    (1e8, 'dms', '.3f', False, '1e+08d 00m 00s'),
    # HMS: the value is divided by 15 and the format is two digits smaller.
    (0, 'hms', '.6f', False, '0h 00m 00s'),
    (0, 'hms', '.6f', True, '0h 00m 00.0000s'),
    (0.0001*15, 'hms', '.6f', False, '0h 00m 00.36s'),
    (0.0001*15, 'hms', '.6f', True, '0h 00m 00.3600s'),
    (-0.0001*15, 'hms', '.6f', False, '-0h 00m 00.36s'),
    (-0.0001*15, 'hms', '.6f', True, '-0h 00m 00.3600s'),
    (700*15, 'hms', '.6f', False, '700h 00m 00s'),
    (699.99999987*15, 'hms', '.5f', False, '700h 00m 00s'),
    (699.99999986*15, 'hms', '.5f', False, '699h 59m 59.999s'),
    (-699.99999986*15, 'hms', '.5f', False, '-699h 59m 59.999s'),
    (1e7*15, 'hms', '.3f', False, '10000000h 00m 00s'),
    (1e8*15, 'hms', '.3f', False, '1e+08h 00m 00s'),
])
def test_format_dms_hms(val: float, unit: str, numerical_format: str,
                        keep_zeros: bool, expected: str) -> None:
    """Angles format as plain numbers or as DMS/HMS depending on the unit."""
    assert format_dms_hms(val, unit=unit, numerical_format=numerical_format,
                          keep_trailing_zeros=keep_zeros) == expected
