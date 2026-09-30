"""Tests for the unit lookup, conversion, parsing and formatting in ``opus_support``.

``UNIT_FORMAT_DB`` drives all of it. These tests cover the lookups it answers, the
numeric conversions to and from each group's default unit, and the formatting and
parsing of a value in a requested unit.
"""

from collections.abc import Callable
from typing import Any

import pytest

from opus_support import (
    UNIT_FORMAT_DB,
    adjust_format_string_for_units,
    convert_from_default_unit,
    convert_to_default_unit,
    display_result_unit,
    display_search_unit,
    display_unit_ever,
    format_cassini_orbit,
    format_unit_value,
    get_default_unit,
    get_disp_default_and_avail_units,
    get_single_format_function,
    get_single_parse_function,
    get_unit_display_name,
    get_unit_display_names,
    get_valid_units,
    is_valid_unit,
    is_valid_unit_id,
    parse_cassini_orbit,
    parse_form_type,
    parse_unit_value,
)

################################################################################
# NUMERICAL CONVERSION
################################################################################


@pytest.mark.parametrize('converter', [convert_to_default_unit, convert_from_default_unit])
def test_convert_rejects_unit_without_unit_id(converter: Callable[..., Any]) -> None:
    """Naming a unit without a unit_id raises a bare, message-less KeyError.

    The empty message is asserted rather than glossed over because it is the
    module's current contract; giving it text would be a behavior change.
    """
    with pytest.raises(KeyError) as excinfo:
        converter(0, None, 'm')
    assert str(excinfo.value) == ''


@pytest.mark.parametrize('converter', [convert_to_default_unit, convert_from_default_unit])
def test_convert_passes_through_none_value(converter: Callable[..., Any]) -> None:
    """A None value is returned unchanged whatever the units are."""
    assert converter(None, 'x', 'y') is None


@pytest.mark.parametrize('converter', [convert_to_default_unit, convert_from_default_unit])
def test_convert_passes_through_without_units(converter: Callable[..., Any]) -> None:
    """With no unit_id and no unit there is nothing to convert."""
    assert converter(10, None, None) == 10


@pytest.mark.parametrize(
    ('converter', 'unit', 'expected'),
    [
        (convert_to_default_unit, 'seconds', 100),
        (convert_to_default_unit, 'milliseconds', 0.1),
        (convert_from_default_unit, 'seconds', 100),
        (convert_from_default_unit, 'milliseconds', 100000),
    ],
)
def test_convert_duration(converter: Callable[..., Any], unit: str, expected: float) -> None:
    """Converting to and from the default unit applies the conversion factor."""
    assert converter(100, 'duration', unit) == expected


@pytest.mark.parametrize(
    ('converter', 'unit'),
    [
        (convert_to_default_unit, 'days'),
        (convert_from_default_unit, 'milliseconds'),
    ],
)
def test_convert_rejects_overflow(converter: Callable[..., Any], unit: str) -> None:
    """A conversion that overflows to infinity raises a bare ValueError.

    The empty message is asserted rather than glossed over because it is the
    module's current contract; giving it text would be a behavior change.
    """
    with pytest.raises(ValueError) as excinfo:
        converter(1e307, 'duration', unit)
    assert str(excinfo.value) == ''


################################################################################
# UNIT INFORMATION
################################################################################


def test_get_valid_units_unknown_unit_id() -> None:
    """An unrecognized unit_id has no unit list."""
    assert get_valid_units('fred') is None


def test_get_valid_units() -> None:
    """The unit list preserves the order the units are declared in."""
    assert get_valid_units('duration') == [
        'seconds',
        'microseconds',
        'milliseconds',
        'minutes',
        'hours',
        'days',
    ]


def test_get_unit_display_names_unknown_unit_id() -> None:
    """An unrecognized unit_id has no display names."""
    assert get_unit_display_names('fred') is None


def test_get_unit_display_names() -> None:
    """Every unit of a unit_id maps to its user-visible display name."""
    assert get_unit_display_names('datetime') == {
        'ymdhms': 'YMDhms',
        'ydhms': 'YDhms',
        'jd': 'JD',
        'jed': 'JED',
        'mjd': 'MJD',
        'mjed': 'MJED',
        'et': 'SPICE ET',
    }


def test_get_unit_display_name() -> None:
    """A single unit maps to its user-visible display name."""
    assert get_unit_display_name('latitude', 'dms') == 'DMS'


@pytest.mark.parametrize(
    ('unit_id', 'expected'),
    [
        ('fred', False),
        ('generic_angle', True),
    ],
)
def test_is_valid_unit_id(unit_id: str, expected: bool) -> None:
    """Only unit_ids present in the unit database are valid."""
    assert is_valid_unit_id(unit_id) is expected


@pytest.mark.parametrize(
    ('unit', 'expected'),
    [
        ('fred', False),
        ('radians', True),
    ],
)
def test_is_valid_unit(unit: str, expected: bool) -> None:
    """Only units declared for the unit_id are valid."""
    assert is_valid_unit('generic_angle', unit) is expected


def test_get_default_unit_without_unit_id() -> None:
    """A missing unit_id has no default unit."""
    assert get_default_unit(None) is None


def test_get_default_unit() -> None:
    """Each unit_id declares one default unit."""
    assert get_default_unit('longitude') == 'degrees'


@pytest.mark.parametrize('checker', [display_search_unit, display_result_unit, display_unit_ever])
@pytest.mark.parametrize(
    ('unit_id', 'expected'),
    [
        (None, False),
        ('longitude', True),
        # A single non-selectable format never shows its unit name.
        ('range_cassini_rev_no', False),
    ],
)
def test_display_unit(
    checker: Callable[[str | None], bool], unit_id: str | None, expected: bool
) -> None:
    """Unit names are shown for selectable units and hidden for fixed formats."""
    assert checker(unit_id) is expected


def test_get_disp_default_and_avail_units_hidden() -> None:
    """A form type whose unit is never displayed reports no units at all."""
    assert get_disp_default_and_avail_units('%d:range_cassini_rev_no') == (None, None, None)


def test_get_disp_default_and_avail_units() -> None:
    """A displayed unit reports its display name, default, and alternatives."""
    assert get_disp_default_and_avail_units('%d:wavenumber') == (
        'cm^-1',
        '1_cm',
        {'1_cm': 'cm^-1', '1_m': 'm^-1'},
    )


################################################################################
# FORMATTING
################################################################################


@pytest.mark.parametrize(
    ('numerical_format', 'unit_id', 'unit', 'expected'),
    [
        # No unit_id means nothing to adjust.
        ('.6f', None, None, '.6f'),
        # Only ".<n>f" formats are adjusted.
        ('6d', 'wavenumber', '1_m', '6d'),
        # The unit is matched case-insensitively.
        ('.6f', 'wavenumber', '1_M', '.4f'),
        ('.6f', 'duration', 'days', '.11f'),
        # The default unit needs no adjustment.
        ('.6f', 'duration', 'seconds', '.6f'),
    ],
)
def test_adjust_format_string_for_units(
    numerical_format: str, unit_id: str | None, unit: str | None, expected: str
) -> None:
    """Decimal places grow or shrink with the size ratio to the default unit."""
    assert adjust_format_string_for_units(numerical_format, unit_id, unit) == expected


def test_format_unit_value_passes_through_string() -> None:
    """A value that is already a string is returned unchanged."""
    assert format_unit_value('string', None, None, None) == 'string'


def test_format_unit_value_passes_through_none() -> None:
    """A None value has nothing to format."""
    assert format_unit_value(None, None, 'datetime', 'ydhms') is None


@pytest.mark.parametrize(
    ('unit', 'expected'),
    [
        ('ydhms', '2019-005T22:39:23.000'),
        ('ymdhms', '2019-01-05T22:39:23.000'),
    ],
)
def test_format_unit_value_uses_unit_format_function(unit: str, expected: str) -> None:
    """A unit that declares a format function delegates to it."""
    assert format_unit_value(600000000, None, 'datetime', unit) == expected


@pytest.mark.parametrize(
    ('val', 'numerical_format', 'unit_id', 'unit', 'kwargs', 'expected'),
    [
        (100.1, '.3f', 'duration', 'seconds', {}, '100.1'),
        (100.1, '.3f', None, None, {}, '100.1'),
        # A unit of None falls back to the unit_id's default unit.
        (100.1, '.3f', 'duration', None, {}, '100.1'),
        (100.1, '.3f', 'duration', 'seconds', {'keep_trailing_zeros': True}, '100.100'),
        (100.1, '.3f', 'duration', 'days', {'keep_trailing_zeros': True}, '0.00115856'),
        (
            100.1,
            '.3f',
            'duration',
            'days',
            {'keep_trailing_zeros': True, 'convert_from_default': False},
            '100.10000000',
        ),
        # A missing numerical format falls back to str().
        (100, None, 'duration', 'seconds', {}, '100'),
        # Large magnitudes switch to exponential notation.
        (1e7, '.3f', 'duration', 'seconds', {}, '10000000'),
        (1e8, '.3f', 'duration', 'seconds', {}, '1e+08'),
    ],
)
def test_format_unit_value_numeric(
    val: float,
    numerical_format: str | None,
    unit_id: str | None,
    unit: str | None,
    kwargs: dict[str, bool],
    expected: str,
) -> None:
    """Units with no format function are rendered with the numerical format."""
    assert format_unit_value(val, numerical_format, unit_id, unit, **kwargs) == expected


################################################################################
# PARSING
################################################################################


@pytest.mark.parametrize('text', [None, ''])
def test_parse_unit_value_empty(text: str | None) -> None:
    """An absent value parses to None whatever the units are."""
    assert parse_unit_value(text, 'x', 'x', 'x') is None


def test_parse_unit_value_default_unit() -> None:
    """A unit of None falls back to the unit_id's default unit."""
    assert parse_unit_value('100', '.3f', 'duration', None) == 100


@pytest.mark.parametrize(
    ('text', 'expected'),
    [
        ('100000', 100000),
        # A recognized unit suffix overrides the requested unit.
        ('100s', 100000),
    ],
)
def test_parse_unit_value_float(text: str, expected: float) -> None:
    """A ".<n>f" format parses the value as a float."""
    val = parse_unit_value(text, '.3f', 'duration', 'milliseconds')
    assert isinstance(val, float)
    assert val == expected


@pytest.mark.parametrize(
    ('text', 'expected'),
    [
        # The "perpixel" and "**-1" spellings of both wavenumber-resolution units.
        ('1 cm^-1perpix', 1),
        ('1 cm^-1perpixel', 1),
        ('1 cm**-1/p', 1),
        ('1 cm**-1perpixel', 1),
        ('1 m^-1perpix', 0.01),
        ('1 m^-1perpixel', 0.01),
        ('1 m**-1/p', 0.01),
        ('1 m**-1perpixel', 0.01),
    ],
)
def test_parse_unit_value_wavenumber_resolution_suffix(text: str, expected: float) -> None:
    """The four wavenumber-resolution spellings a missing comma destroyed, plus neighbors.

    Each is parsed and converted to cm^-1/pixel, so a spelling that resolved to the
    wrong one of the two units would give the wrong number rather than passing.
    """
    assert parse_unit_value(text, '.10f', 'wavenumber_resolution', '1_cm_pixel') == pytest.approx(
        expected
    )


def _suffix_cases() -> list[tuple[str, str, str]]:
    """Return every (unit_id, unit, suffix) the unit database declares.

    Only units parsed by the generic numeric path are included; a unit with its own
    parse function never consults the suffix list.
    """
    return [
        (unit_id, unit, suffix)
        for unit_id, info in UNIT_FORMAT_DB.items()
        for unit, conversion in info['conversions'].items()
        if conversion[2] is None
        for suffix in conversion[4]
    ]


@pytest.mark.parametrize(('unit_id', 'unit', 'suffix'), _suffix_cases())
def test_parse_unit_value_suffix_resolves_to_its_own_unit(
    unit_id: str, unit: str, suffix: str
) -> None:
    """Every declared suffix selects the unit that declares it.

    Suffixes are matched longest-first across all of a unit_id's units, so a spelling
    can be declared and still never win. Parsing "1<suffix>" while asking for that
    same unit must give back exactly 1: any other value means a sibling unit's
    suffix claimed the text and its conversion factor was applied instead.

    This reads the suffixes out of the database, so it cannot see a spelling that is
    missing from the database in the first place -- a suffix fused to its neighbor by
    a missing comma tests as its fused self and passes. Guarding against that needs the
    spellings written out, as in the wavenumber-resolution test above.
    """
    assert parse_unit_value('1' + suffix, '.10f', unit_id, unit) == pytest.approx(1)


def test_parse_unit_value_int() -> None:
    """A "d" format parses the value as an int."""
    val = parse_unit_value('100', 'd', None, None)
    assert isinstance(val, int)
    assert val == 100


def test_parse_unit_value_rejects_infinity() -> None:
    """A non-finite value raises a bare, message-less ValueError.

    The empty message is asserted rather than glossed over because it is the
    module's current contract; giving it text would be a behavior change.
    """
    with pytest.raises(ValueError) as excinfo:
        parse_unit_value('inf', '.3f', 'duration', 'milliseconds')
    assert str(excinfo.value) == ''


def test_parse_unit_value_rejects_an_int_too_large_for_a_float() -> None:
    """An integer too large to convert to a float is rejected, not raised through.

    ``math.isfinite`` raises ``OverflowError`` rather than returning False for such
    an integer, and an ``OverflowError`` escaping this parser reaches the caller as
    an internal error rather than as a rejected value. The rejection carries the
    same empty message as every other rejection here.
    """
    with pytest.raises(ValueError) as excinfo:
        parse_unit_value('1' * 400, 'd', None, None)
    assert str(excinfo.value) == ''
    assert isinstance(excinfo.value.__cause__, OverflowError)


def test_parse_unit_value_uses_unit_parse_function() -> None:
    """A unit that declares a parse function delegates to it."""
    assert parse_unit_value('2019-01-05T10:39:23.000', None, 'datetime', 'YMDhms') == 599956800.0


@pytest.mark.parametrize(
    ('form_type', 'expected'),
    [
        (None, (None, None, None)),
        ('X', ('X', None, None)),
        ('X:Y', ('X', None, 'Y')),
        ('X%Z', ('X', 'Z', None)),
        ('X%Z:Y', ('X', 'Z', 'Y')),
    ],
)
def test_parse_form_type(
    form_type: str | None, expected: tuple[str | None, str | None, str | None]
) -> None:
    """A form type splits into TYPE[%format][:unit]."""
    assert parse_form_type(form_type) == expected


@pytest.mark.parametrize('getter', [get_single_parse_function, get_single_format_function])
@pytest.mark.parametrize('unit_id', [None, 'datetime'])
def test_get_single_function_none(getter: Callable[..., Any], unit_id: str | None) -> None:
    """A missing unit_id, or one whose units are displayed, has no single func."""
    assert getter(unit_id) is None


@pytest.mark.parametrize(
    ('getter', 'expected'),
    [
        (get_single_parse_function, parse_cassini_orbit),
        (get_single_format_function, format_cassini_orbit),
    ],
)
def test_get_single_function(getter: Callable[..., Any], expected: Callable[..., Any]) -> None:
    """A unit_id with one never-displayed unit exposes that unit's functions."""
    assert getter('range_cassini_rev_no') is expected
