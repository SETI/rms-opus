"""Tests for the spacecraft-clock (SCLK) conversions in ``opus_support``.

Each mission has a parser that turns a clock string into a number and a formatter that
turns that number back into the mission's canonical string. The tables below cover the
spellings each parser accepts, the ones it rejects, and the message every rejection
carries.
"""

import re

import pytest

from opus_support import (
    format_cassini_sclk,
    format_galileo_sclk,
    format_new_horizons_sclk,
    format_voyager_sclk,
    parse_cassini_sclk,
    parse_galileo_sclk,
    parse_new_horizons_sclk,
    parse_voyager_sclk,
)

# Clock counts run into the millions, where pytest.approx's relative default of
# 1e-6 would tolerate an error of several whole ticks, so comparisons state an
# absolute tolerance instead: half a unit in the seventh decimal place.
SCLK_ABS_TOL = 5e-8


################################################################################
# GALILEO
################################################################################

@pytest.mark.parametrize(('sclk', 'message'), [
    # Partition handling.
    ('1/2/03464059.00', 'Invalid Galileo clock format, extraneous slash: '
                        '1/2/03464059:00'),
    ('2/03464059:00', 'Galileo partition number must be one: 2/03464059:00'),
    ('0/03464059.00', 'Galileo partition number must be one: 0/03464059:00'),
    ('1.0/03464059:00', 'Galileo partition number must be one: 1:0/03464059:00'),
    ('-1/03464059.00', 'Galileo partition number must be one: -1/03464059:00'),
    ('a/03464059:00', 'Galileo partition number must be one: a/03464059:00'),
    ('/03464059.00', 'Galileo partition number must be one: /03464059:00'),
    # Non-integer or out-of-range fields.
    ('1/a', 'Galileo clock fields must be integers: a'),
    ('1/0123456a', 'Galileo clock fields must be integers: 0123456a'),
    ('1/03464059.0a', 'Galileo clock fields must be integers: 03464059:0a'),
    ('1/03464059.-1', 'Galileo clock field 2 out of range 0-90: 03464059:-1'),
    ('1/03464059.91', 'Galileo clock field 2 out of range 0-90: 03464059:91'),
    ('1/03464059.450', 'Galileo clock field 2 "450" has too many digits: '
                       '03464059:450'),
    ('1/034640590.00', 'Galileo clock leading field has too many digits: '
                       '034640590:00'),
    ('.00', 'Galileo clock fields must be integers: :00'),
    ('1/.00', 'Galileo clock fields must be integers: :00'),
    ('1/-1.00', 'Galileo clock leading field has too many digits: -1:00'),
    ('1/-34640590.00', 'Galileo clock leading field has too many digits: '
                       '-34640590:00'),
    # Wrong number of fields, or fields that are individually too long.
    ('01234567:000', 'Galileo clock field 2 "000" has too many digits: '
                     '01234567:000'),
    ('01234567:00:91', 'Galileo clock field 3 "91" has too many digits: '
                       '01234567:00:91'),
    ('01234567:00:-2', 'Galileo clock field 3 "-2" has too many digits: '
                       '01234567:00:-2'),
    ('01234567:00:00', 'Galileo clock field 3 "00" has too many digits: '
                       '01234567:00:00'),
    ('01234567:00:0:00', 'Galileo clock field 4 "00" has too many digits: '
                         '01234567:00:0:00'),
    ('01234567:00:0:8', 'Galileo clock field 4 out of range 0-7: '
                        '01234567:00:0:8'),
    ('01234567:00:0:a', 'Galileo clock fields must be integers: '
                        '01234567:00:0:a'),
    ('01234567:00:0:0:0', 'More than 4 Galileo clock fields: '
                          '01234567:00:0:0:0'),
])
def test_parse_galileo_sclk_rejects_bad_input(sclk: str, message: str) -> None:
    """Malformed Galileo clocks raise ValueError naming the specific problem."""
    with pytest.raises(ValueError, match=re.escape(message)):
        parse_galileo_sclk(sclk)


@pytest.mark.parametrize(('sclk', 'expected'), [
    ('1', 1),
    ('1.', 1),
    ('1.0', 1),
    ('1.00', 1),
    ('1/03464059.00', 3464059),
])
def test_parse_galileo_sclk_exact(sclk: str, expected: float) -> None:
    """Galileo clocks with no fractional part parse to an exact value."""
    assert parse_galileo_sclk(sclk) == expected


@pytest.mark.parametrize(('sclk', 'expected'), [
    ('03464059:00:0:3', 3464059.000412087),
    ('03464059:00:3:0', 3464059.003296703),
    ('1/03464059:90', 3464059.989010989),
    ('1/3464059:90', 3464059.989010989),
    ('1/3464059:9', 3464059.989010989),
    ('03464059:90', 3464059.989010989),
    ('03464059:90:0:0', 3464059.989010989),
    ('03464059:90:4', 3464059.9934065933),
    ('03464059:90:4:5', 3464059.9940934065),
])
def test_parse_galileo_sclk_fractional(sclk: str, expected: float) -> None:
    """Missing Galileo subfields default to zero and shorter fields are padded."""
    assert parse_galileo_sclk(sclk) == pytest.approx(expected, abs=SCLK_ABS_TOL)


@pytest.mark.parametrize(('value', 'expected'), [
    (0, '00000000:00:0:0'),
    (1234, '00001234:00:0:0'),
    (12345678, '12345678:00:0:0'),
    (3464059.000412087, '03464059:00:0:3'),
    (3464059.003296703, '03464059:00:3:0'),
    (1234.989010989, '00001234:90:0:0'),
    (99999999.989010989, '99999999:90:0:0'),
    (99999999.9940934065, '99999999:90:4:5'),
    # Rounding the last field can carry into the fields above it.
    (99999999.995467033, '99999999:90:5:7'),
    (99999999.99554945, '99999999:90:6:0'),
    (99999999.99995, '100000000:00:0:0'),
])
def test_format_galileo_sclk(value: float, expected: str) -> None:
    """Galileo values format as zero-padded four-field clock strings."""
    assert format_galileo_sclk(value) == expected


################################################################################
# NEW HORIZONS
################################################################################

@pytest.mark.parametrize(('sclk', 'message'), [
    ('1/2/0003103485:49000', 'New Horizons partition number must be one: '
                             '2/0003103485:49000'),
    ('4/0003103485:49000', 'New Horizons partition number must be 1 or 3: '
                           '4/0003103485:49000'),
    ('2/0003103485:49000', 'New Horizons partition number must be 1 or 3: '
                           '2/0003103485:49000'),
    ('0/0003103485:49000', 'New Horizons partition number must be 1 or 3: '
                           '0/0003103485:49000'),
    ('1.0/0003103485:49000', 'New Horizons partition number must be 1 or 3: '
                             '1.0/0003103485:49000'),
    ('-1/0003103485:49000', 'New Horizons partition number must be 1 or 3: '
                            '-1/0003103485:49000'),
    ('a/0003103485:49000', 'New Horizons partition number must be 1 or 3: '
                           'a/0003103485:49000'),
    ('/0003103485:49000', 'New Horizons partition number must be 1 or 3: '
                          '/0003103485:49000'),
    ('1/0003103485:49000:49000', 'More than 2 New Horizons clock fields: '
                                 '0003103485:49000:49000'),
    ('1/a', 'New Horizons clock fields must be integers: a'),
    ('1/000310348a', 'New Horizons clock fields must be integers: 000310348a'),
    ('1/0003103485:4900a', 'New Horizons clock fields must be integers: '
                           '0003103485:4900a'),
    ('1/0003103485:-10000', 'New Horizons clock field 2 "-10000" has too many '
                            'digits: 0003103485:-10000'),
    ('1/0003103485:50000', 'New Horizons clock field 2 out of range 0-49999: '
                           '0003103485:50000'),
    ('1/0003103485:99999', 'New Horizons clock field 2 out of range 0-49999: '
                           '0003103485:99999'),
    ('1/00003103485:49000', 'New Horizons clock leading field has too many '
                            'digits: 00003103485:49000'),
    (':00000', 'New Horizons clock fields must be integers: :00000'),
    ('1/:00000', 'New Horizons clock fields must be integers: :00000'),
    ('1/-1.00000', 'New Horizons clock fields must be integers: -1.00000'),
    ('1/-0003103485:00000', 'New Horizons clock leading field has too many '
                            'digits: -0003103485:00000'),
    # The partition must agree with the clock count it is paired with.
    ('1/0150000000:00001', 'New Horizons partition number is invalid: '
                           '1/0150000000:00001'),
    ('3/0149999999:49999', 'New Horizons partition number is invalid: '
                           '3/0149999999:49999'),
])
def test_parse_new_horizons_sclk_rejects_bad_input(sclk: str,
                                                   message: str) -> None:
    """Malformed New Horizons clocks raise ValueError naming the problem."""
    with pytest.raises(ValueError, match=re.escape(message)):
        parse_new_horizons_sclk(sclk)


@pytest.mark.parametrize(('sclk', 'expected'), [
    ('1:', 1),
    ('1:0', 1),
    ('1:00', 1),
    ('1/0003103485:25', 3103485.5),
    ('1/0003103485:25000', 3103485.5),
    ('3/1003103485:25000', 1003103485.5),
    ('1/3103485:25000', 3103485.5),
    ('1/3103485:25', 3103485.5),
    ('0003103485:25000', 3103485.5),
    # Boundary values on either side of the partition-1/partition-3 split.
    ('3/9999999999:49999', 9999999999.99998),
    ('1/0149999999:49999', 149999999.99998),
    ('3/0150000000:00001', 150000000.00002),
])
def test_parse_new_horizons_sclk(sclk: str, expected: float) -> None:
    """Valid New Horizons clocks parse to their numeric value."""
    assert parse_new_horizons_sclk(sclk) == expected


@pytest.mark.parametrize(('value', 'expected'), [
    (0, '0000000000:00000'),
    (1234, '0000001234:00000'),
    (1234567890, '1234567890:00000'),
    (1234.5, '0000001234:25000'),
])
def test_format_new_horizons_sclk(value: float, expected: str) -> None:
    """New Horizons values format as a ten-digit count and a five-digit field."""
    assert format_new_horizons_sclk(value) == expected


################################################################################
# CASSINI
################################################################################

@pytest.mark.parametrize(('sclk', 'message'), [
    ('1/2/1294341579.000', 'Invalid Cassini clock format, extraneous slash: '
                           '1/2/1294341579.000'),
    ('2/1294341579.000', 'Cassini partition number must be one: '
                         '2/1294341579.000'),
    ('0/1294341579.000', 'Cassini partition number must be one: '
                         '0/1294341579.000'),
    ('1.0/1294341579.000', 'Cassini partition number must be one: '
                           '1.0/1294341579.000'),
    ('-1/1294341579.000', 'Cassini partition number must be one: '
                          '-1/1294341579.000'),
    ('a/1294341579.000', 'Cassini partition number must be one: '
                         'a/1294341579.000'),
    ('/1294341579.000', 'Cassini partition number must be one: '
                        '/1294341579.000'),
    ('1/1294341579.000.000', 'More than 2 Cassini clock fields: '
                             '1294341579.000.000'),
    ('1/a', 'Cassini clock fields must be integers: a'),
    ('1/0123456a', 'Cassini clock fields must be integers: 0123456a'),
    ('1/1294341579.00a', 'Cassini clock fields must be integers: '
                         '1294341579.00a'),
    ('1/1294341579.-1', 'Cassini clock field 2 out of range 0-255: '
                        '1294341579.-1'),
    ('1/1294341579.256', 'Cassini clock field 2 out of range 0-255: '
                         '1294341579.256'),
    ('1/1294341579.2560', 'Cassini clock field 2 "2560" has too many digits: '
                          '1294341579.2560'),
    ('1/01294341579.000', 'Cassini clock leading field has too many digits: '
                          '01294341579.000'),
    ('.000', 'Cassini clock fields must be integers: .000'),
    ('1/.000', 'Cassini clock fields must be integers: .000'),
    ('1/-1.000', 'Cassini clock leading field has too many digits: -1.000'),
    ('1/-34640590.000', 'Cassini clock leading field has too many digits: '
                        '-34640590.000'),
])
def test_parse_cassini_sclk_rejects_bad_input(sclk: str, message: str) -> None:
    """Malformed Cassini clocks raise ValueError naming the specific problem."""
    with pytest.raises(ValueError, match=re.escape(message)):
        parse_cassini_sclk(sclk)


@pytest.mark.parametrize(('sclk', 'expected'), [
    ('1.', 1),
    ('1.0', 1),
    ('1.00', 1),
    ('1/03464059.00', 3464059),
    ('1/0003464059.064', 3464059.25),
    ('1/3464059.064', 3464059.25),
    ('03464059.064', 3464059.25),
])
def test_parse_cassini_sclk(sclk: str, expected: float) -> None:
    """Valid Cassini clocks parse to their numeric value."""
    assert parse_cassini_sclk(sclk) == expected


@pytest.mark.parametrize(('value', 'expected'), [
    (0, '0000000000.000'),
    (1234, '0000001234.000'),
    (1234567890, '1234567890.000'),
    (1234.250, '0000001234.064'),
    (1234.5, '0000001234.128'),
    (1234.750, '0000001234.192'),
])
def test_format_cassini_sclk(value: float, expected: str) -> None:
    """Cassini values format as a ten-digit count and a 0-255 subfield."""
    assert format_cassini_sclk(value) == expected


################################################################################
# VOYAGER
################################################################################

@pytest.mark.parametrize(('sclk', 'message'), [
    ('1/2/08966:30:752', 'Invalid FDS format, extraneous "/": '
                         '1/2/08966:30:752'),
    ('1/08966:30:752', 'Partition number out of range 2-4: 1/08966:30:752'),
    ('5/08966:30:752', 'Partition number out of range 2-4: 5/08966:30:752'),
    ('-1/08966:30:752', 'Partition number out of range 2-4: -1/08966:30:752'),
    ('6/08966:30:752', 'Partition number out of range 2-4: 6/08966:30:752'),
    ('a/08966:30:752', 'Partition number is not an integer: a/08966:30:752'),
    ('1:0:1:0', 'More than three fields in Voyager clock: 1:0:1:0'),
    ('0:0:0', 'Voyager clock "seconds" out of range 1-800: 0:0:0'),
    ('0:0:801', 'Voyager clock "seconds" out of range 1-800: 0:0:801'),
    ('0:-1:0', 'Voyager clock "minutes" out of range 0-59: 0:-1:0'),
    ('0:61:0', 'Voyager clock "minutes" out of range 0-59: 0:61:0'),
    ('-1:0:0', 'Voyager clock "hours" out of range 0-65535: -1:0:0'),
    ('65536:0:0', 'Voyager clock "hours" out of range 0-65535: 65536:0:0'),
    ('0:0:a', 'Voyager clock fields must be integers: 0:0:a'),
    ('0:a:0', 'Voyager clock fields must be integers: 0:a:0'),
    ('a:0:0', 'Voyager clock fields must be integers: a:0:0'),
])
def test_parse_voyager_sclk_rejects_bad_input(sclk: str, message: str) -> None:
    """Malformed FDS counts raise ValueError naming the specific problem."""
    with pytest.raises(ValueError, match=re.escape(message)):
        parse_voyager_sclk(sclk)


@pytest.mark.parametrize('planet', [4, 9])
def test_parse_voyager_sclk_rejects_unknown_planet(planet: int) -> None:
    """Only the four Voyager flyby planet codes (5-8) are accepted."""
    with pytest.raises(AssertionError,
                       match=re.escape(f'Invalid planet value: {planet}')):
        parse_voyager_sclk('1/08966:30:752', planet=planet)


@pytest.mark.parametrize(('sclk', 'planet', 'message'), [
    ('1/08966:30:752', 5, 'Partition number for Jupiter flyby must be 2: '
                          '1/08966:30:752'),
    ('3/08966:30:752', 5, 'Partition number for Jupiter flyby must be 2: '
                          '3/08966:30:752'),
    ('1/08966:30:752', 6, 'Partition number for Saturn flyby must be 2: '
                          '1/08966:30:752'),
    ('3/08966:30:752', 6, 'Partition number for Saturn flyby must be 2: '
                          '3/08966:30:752'),
    ('1/08966:30:752', 7, 'Partition number for Uranus flyby must be 3: '
                          '1/08966:30:752'),
    ('2/08966:30:752', 7, 'Partition number for Uranus flyby must be 3: '
                          '2/08966:30:752'),
    ('1/08966:30:752', 8, 'Partition number for Neptune flyby must be 4: '
                          '1/08966:30:752'),
    ('5/08966:30:752', 8, 'Partition number for Neptune flyby must be 4: '
                          '5/08966:30:752'),
])
def test_parse_voyager_sclk_rejects_wrong_partition_for_planet(
        sclk: str, planet: int, message: str) -> None:
    """An explicit partition must match the requested planetary flyby."""
    with pytest.raises(ValueError, match=re.escape(message)):
        parse_voyager_sclk(sclk, planet=planet)


@pytest.mark.parametrize(('sclk', 'planet'), [
    ('2/0:0:001', None),
    ('3/0:0:001', None),
    ('4/0:0:001', None),
    ('2/0:0:001', 5),
    ('2/0:0:001', 6),
    ('3/0:0:001', 7),
    ('4/0:0:001', 8),
])
def test_parse_voyager_sclk_accepts_matching_partition(sclk: str,
                                                       planet: int | None
                                                       ) -> None:
    """A partition consistent with the flyby (or with no planet) is accepted."""
    assert parse_voyager_sclk(sclk, planet=planet) == pytest.approx(
        0, abs=SCLK_ABS_TOL)


@pytest.mark.parametrize(('sclk', 'expected'), [
    ('0', 0),
    ('0:0', 0),
    ('0:0:001', 0),
    ('0:0:401', .5/60.),
    ('0:0:400', 399/800/60.),
    # Short trailing fields are right-padded with zeros.
    ('0:0:40', 399/800/60.),
    ('0:0:4', 399/800/60.),
    ('0:1:1', 10/60.+99/800/60.),
    ('0:1:001', 10/60.),
    ('1:0:1', 1+99/800/60.),
    ('1:0:001', 1),
    ('1000:00:001', 1000),
    ('1000.00.001', 1000),
    # A bare six- or seven-digit number has an implied hours/minutes separator.
    ('100000', 1000),
])
def test_parse_voyager_sclk(sclk: str, expected: float) -> None:
    """Valid FDS counts parse to a value in units of FDS hours."""
    assert parse_voyager_sclk(sclk) == expected


@pytest.mark.parametrize(('value', 'expected'), [
    (0, '00000:00:001'),
    (.5/60, '00000:00:401'),
    (1/60, '00000:01:001'),
    (1, '00001:00:001'),
    (5000, '05000:00:001'),
    (59.97/3600, '00000:01:001'),
    (5000.9999999, '05001:00:001'),
])
def test_format_voyager_sclk_three_fields(value: float, expected: str) -> None:
    """FDS values format as hours:minutes:seconds by default."""
    assert format_voyager_sclk(value) == expected


@pytest.mark.parametrize(('value', 'expected'), [
    (0, '00000:00'),
    (.39/60, '00000:00'),
    (.5/60, '00000:01'),
    (59.6/60, '00001:00'),
    (1, '00001:00'),
    (5000, '05000:00'),
])
def test_format_voyager_sclk_two_fields(value: float, expected: str) -> None:
    """With ``fields=2`` the seconds field is dropped and minutes are rounded."""
    assert format_voyager_sclk(value, fields=2) == expected


@pytest.mark.parametrize(('fields', 'expected'), [
    (2, '05000.00'),
    (3, '05000.00.001'),
])
def test_format_voyager_sclk_accepts_dot_separator(fields: int,
                                                   expected: str) -> None:
    """The field separator can be switched from a colon to a dot."""
    assert format_voyager_sclk(5000, sep='.', fields=fields) == expected


def test_format_voyager_sclk_rejects_out_of_range_hours() -> None:
    """FDS hours above 65535 cannot be represented."""
    with pytest.raises(ValueError,
                       match=re.escape('Voyager clock "hours" cannot exceed '
                                       '65535: 65536')):
        format_voyager_sclk(65536)
