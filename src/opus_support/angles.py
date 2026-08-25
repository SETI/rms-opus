"""Angle conversions between DMS/HMS text and a numeric value in degrees.

The parsers accept degrees-minutes-seconds, hours-minutes-seconds, a bare
number, or a space-separated triple, and the formatter renders a value back in
whichever of those the caller's unit asks for.
"""

import math
import re

import numpy as np

from opus_support._numeric_text import _clean_numeric_field, _strip_trailing_zeros

################################################################################
################################################################################
# ANGLE CONVERSION
################################################################################

def parse_dms_hms(s: str, conversion_factor: float = 1, **kwargs: object) -> float:
    """Parse DMS, HMS, or single number, but "x x x" defaults to DMS.

    Parameters:
        s: The angle, written either with the letters or symbols naming its fields
            ("23d 30m 36s", "23h 30m 36s"), as a space-separated triple ("23 30 36"),
            or as a plain number.
        conversion_factor: The number of the caller's units in one degree, which the
            angle is divided by once it is in degrees. It is 1 for an angle in
            degrees and the number of degrees in a radian for one in radians. A
            plain number is taken to be in the caller's units already and is left
            alone.
        **kwargs: Accepted and ignored, so that every parser in this package can be
            called through one uniform dispatch.

    Returns:
        The angle in the caller's units. A triple with no letters is read as
        degrees, minutes and seconds.

    Raises:
        ValueError: If the string is not a value this parser accepts, always with an
            empty message.
    """
    return _parse_dms_hms(s, conversion_factor, allow_dms=True, allow_hms=True,
                          default='dms')

def parse_hms_dms(s: str, conversion_factor: float = 1, **kwargs: object) -> float:
    """Parse DMS, HMS, or single number, but "x x x" defaults to HMS.

    Parameters:
        s: The angle, written either with the letters or symbols naming its fields
            ("23d 30m 36s", "23h 30m 36s"), as a space-separated triple ("23 30 36"),
            or as a plain number.
        conversion_factor: The number of the caller's units in one degree, which the
            angle is divided by once it is in degrees.
        **kwargs: Accepted and ignored, so that every parser in this package can be
            called through one uniform dispatch.

    Returns:
        The angle in the caller's units. A triple with no letters is read as hours,
        minutes and seconds, and so is a plain number, which is multiplied by 15.

    Raises:
        ValueError: If the string is not a value this parser accepts, always with an
            empty message.
    """
    return _parse_dms_hms(s, conversion_factor, allow_dms=True, allow_hms=True,
                          default='hms')

def parse_dms(s: str, conversion_factor: float = 1, **kwargs: object) -> float:
    """Parse a DMS string or single number.

    Parameters:
        s: The angle, written with the letters or symbols naming its fields
            ("23d 30m 36s"), as a space-separated triple ("23 30 36"), or as a plain
            number. An angle written in hours is rejected.
        conversion_factor: The number of the caller's units in one degree, which the
            angle is divided by once it is in degrees.
        **kwargs: Accepted and ignored, so that every parser in this package can be
            called through one uniform dispatch.

    Returns:
        The angle in the caller's units.

    Raises:
        ValueError: If the string is not a value this parser accepts, always with an
            empty message.
    """
    return _parse_dms_hms(s, conversion_factor, allow_dms=True, allow_hms=False,
                          default='dms')

def parse_hms(s: str, conversion_factor: float = 1, **kwargs: object) -> float:
    """Parse an HMS string or single number.

    Parameters:
        s: The angle, written with the letters or symbols naming its fields
            ("23h 30m 36s"), as a space-separated triple ("23 30 36"), or as a plain
            number. An angle written in degrees is rejected.
        conversion_factor: The number of the caller's units in one degree, which the
            angle is divided by once it is in degrees.
        **kwargs: Accepted and ignored, so that every parser in this package can be
            called through one uniform dispatch.

    Returns:
        The angle in the caller's units. A triple and a plain number are both read
        as hours and multiplied by 15.

    Raises:
        ValueError: If the string is not a value this parser accepts, always with an
            empty message.
    """
    return _parse_dms_hms(s, conversion_factor, allow_dms=False, allow_hms=True,
                          default='hms')

def _parse_dms_hms(s: str, conversion_factor: float = 1, allow_dms: bool = True,
                   allow_hms: bool = True, default: str = 'dms') -> float:
    """Parse a DMS or HMS or "x x x" or plain number.

    Parameters:
        s: The angle as the caller typed it.
        conversion_factor: The number of the caller's units in one degree, which the
            angle is divided by once it is in degrees.
        allow_dms: True to accept an angle written in degrees.
        allow_hms: True to accept an angle written in hours.
        default: "dms" or "hms", naming what a space-separated triple with no
            letters, and a plain number, are read as.

    Returns:
        The angle in the caller's units.

    Raises:
        ValueError: If the string is not a value this parser accepts. Whichever of the
            parser's paths rejected it, the exception carries an empty message, so a
            caller never has to tell them apart. Rejection is all this promises: a
            non-string argument, or a conversion_factor of zero on one of the paths that
            divides by it, is a programming error and raises whatever the offending
            operation raises.
    """
    # Note: conversion_factor is used here for unit=radians. In that case if
    # the user enters something like "1d" it needs to be interpreted as degrees
    # and converted to radians. But if the user just types a single number, that
    # should be interpreted as radians directly.
    s = s.lower().strip()
    # '' and variants => s
    s = s.replace("''", 's').replace('"', 's').replace(chr(8243), 's')
    # ' and variants => m
    s = s.replace("'", 'm').replace(chr(8242), 'm')
    # deg symbol => d
    s = s.replace(chr(176), 'd')

    format_types: list[tuple[str, int]] = []
    if allow_dms:
        format_types.append(('d', 1))
    if allow_hms:
        format_types.append(('h', 15))
    for format_char, format_factor in format_types:
        # We allow exponential notation in the first position
        match = re.fullmatch(r'(|[+-]) *(|\d+(|e(|\+)\d+)(|\.\d*)'+format_char+
                             r') *(|\d+(|\.\d*)m) *(|\d+(|\.\d*)s)', s)
        if match is None and format_char == default[0]:
            # Check for just "N N N" if we are looking at the default format
            match = re.fullmatch(r'(|[+-]) *(\d+)()()() +(\d+)() +(\d+(|\.\d*))',
                                 s)
        if match:
            neg = match[1]
            degrees_hours = match[2]
            minute = match[6]
            second = match[8]
            force_dh_int = False
            force_m_int = False
            val: float = 0
            if second:
                second = second.strip('s')
                # Only "second" can have a fractional part if it's provided
                force_m_int = True
                force_dh_int = True
                second = float(second)
                if not math.isfinite(second) or second < 0 or second >= 60:
                    raise ValueError
                val += second / 3600
            if minute:
                minute = minute.strip('m')
                # Only "minute" can have a fractional part if second is not
                # provided
                force_dh_int = True
                minute = float(minute)
                # Range-check before the integrality check: a field long enough to
                # overflow to infinity would make int() raise OverflowError, which
                # is not this parser's rejection contract.
                if not math.isfinite(minute) or minute < 0 or minute >= 60:
                    raise ValueError
                if force_m_int and minute != int(minute):
                    raise ValueError
                val += minute / 60
            if degrees_hours:
                degrees_hours = degrees_hours.strip(format_char)
                try:
                    degrees_hours = float(degrees_hours)
                except ValueError as err:
                    # The regex above accepts an exponent and a fractional part
                    # together ("1e5.5d"), which float() will not. The minute and
                    # second groups have no such hole: stripping their trailing
                    # letter always leaves a valid float.
                    raise ValueError from err
                # Finiteness before integrality, for the same reason as the minutes
                # field above.
                if not math.isfinite(degrees_hours):
                    raise ValueError
                if force_dh_int and degrees_hours != int(degrees_hours):
                    raise ValueError
                val += degrees_hours
            if neg == '-':
                val = -val
            return val * format_factor / conversion_factor

    # We don't want to allow numbers with spaces in them because that will cause
    # potential ambiguity with the "x x x" DMS/HMS format.
    s = _clean_numeric_field(s, compress_spaces=False)
    try:
        ret = float(s)
    except ValueError as err:
        # float() would name the offending text; keep the parser's one rejection
        # contract instead and let the chained cause carry the detail.
        raise ValueError from err
    if not math.isfinite(ret):
        raise ValueError

    # Note: It is very important that parse_hms_dms is NOT USED for things like
    # units == 'radians' because this factor of 15 will be applied
    # inappropriately
    if default == 'hms':
        ret *= 15

    return ret


def format_dms_hms(val: float, *, unit: str, numerical_format: str,
                   unit_id: str | None = None,
                   keep_trailing_zeros: bool = False) -> str:
    """Format a number as DMS or HMS or a single number as appropriate.

    Parameters:
        val: The angle in degrees, or in hours when `unit` asks for hours.
        unit: What to write the angle as: "degrees", "radians" or "hours" for a
            plain number, "dms" for degrees, minutes and seconds, or "hms" for
            hours, minutes and seconds. Anything else fails an assertion.
        numerical_format: A format of the form ".<n>f" giving the number of decimal
            places the angle would carry in degrees. The number is adjusted for
            whichever unit is being written, since a second of arc is a fixed
            fraction of a degree.
        unit_id: The id of the unit system. It is part of the signature every
            formatter in this package shares and is not used here.
        keep_trailing_zeros: True to keep the zeros at the end of a decimal
            fraction, which are otherwise dropped along with a decimal point left
            with nothing after it.

    Returns:
        The formatted angle. A plain number switches to exponential notation at 1e8;
        a DMS or HMS value is written as "<d>d <mm>m <ss.sss>s" with a leading minus
        sign for a negative angle.
    """
    if unit == 'hours' or unit == 'hms':
        # Just do the normal numeric formatting, but divide by 15 first to be
        # in units of hours
        val /= 15

    # numerical_format is in degrees, regardless of whether val is in degrees
    # or hours.
    # For DMS, our fractional amount is in seconds, which is 1/3600 degree.
    # Round it to 1/1000 to be conservative, which is 3 decimal
    # places. Thus we should subtract 3 from the numerical_format size.
    # For HMS, our fractional amount is in seconds (but val is in hours), which
    # is 1/3600*15=1/240 degree. Round it to 1/100 to be conservative, which is
    # 2 decimal places. Thus we should subtract 2 from the numerical_format
    # size.
    # For plain "hour", we need to add two digits to account for the factor of
    # 15.
    # For plain "radians", it's 2 digits for the factor of 57.
    if unit == 'degrees':
        subtract_amt = 0
    elif unit == 'dms':
        subtract_amt = 3
    elif unit == 'hms':
        subtract_amt = 2
    elif unit == 'hours':
        subtract_amt = -2
    else:
        assert unit == 'radians'
        subtract_amt = -2

    new_dec = max(int(numerical_format[1:-1])-subtract_amt, 0)

    if unit in ['degrees', 'radians', 'hours']:
        # Plain numeric formatting
        new_format = f'%.{new_dec}f'
        if abs(val) >= 1e8:
            new_format = new_format.replace('f', 'e')
        ret = new_format % val
        if not keep_trailing_zeros:
            ret = _strip_trailing_zeros(ret)
        return ret

    # For DMS or HMS, the new format is just for the seconds, so we want to have
    # 2 digits with leading zeroes as necessary
    if new_dec == 0:
        new_format = '02d'
    else:
        new_format = f'0{new_dec+3}.{new_dec}f'

    val_sec = val * 3600 # Do all the work in seconds for better rounding
    neg = val_sec < 0
    val_sec = abs(val_sec)
    # Round the input number to the given precision
    prec = 10**new_dec
    val_sec = np.round(val_sec * prec) / prec
    dh = int(val_sec // 3600)
    val_sec = val_sec-dh*3600
    m = min(int(val_sec // 60), 59)
    val_sec = val_sec-m*60

    leading_char = 'h'
    if unit == 'dms':
        leading_char = 'd'
    leading_fmt = 'd'
    if abs(val) >= 1e8:
        leading_fmt = '.0e'
    full_format = f'%{leading_fmt}{leading_char} %02dm %0{new_format}'
    ret = full_format % (dh, m, val_sec)
    if not keep_trailing_zeros:
        ret = _strip_trailing_zeros(ret)
    ret += 's'
    if neg:
        ret = '-' + ret
    return ret
