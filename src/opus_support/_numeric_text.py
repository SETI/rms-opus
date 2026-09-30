"""Text-tidying helpers shared by the angle and unit conversions.

This module is private: neither helper is part of the package's public surface.
"""

import re


def _strip_trailing_zeros(s: str) -> str:
    """Strip meaningless trailing zeros (like after a decimal point).

    Parameters:
        s: The formatted number to tidy.

    Returns:
        The number with the trailing zeros of its fractional part removed, and the
        decimal point removed too if nothing is left after it. A number in
        exponential notation is tidied in its mantissa only, so its exponent is
        untouched. Anything that is neither shape is returned unchanged.
    """
    if re.fullmatch(r'.*\.\d*0*', s):
        # Strip trailing .000s from NNN.DDDZZZ
        s = s.rstrip('0').rstrip('.')
    elif re.fullmatch(r'.*\.\d*0*e[+-]\d+', s):
        # Strip trailing .000s from the mantissa part of NNN.DDDZZZe+EEE
        s1, s2 = s.split('e')
        s1 = s1.rstrip('0').rstrip('.')
        s = s1 + 'e' + s2
    return s


def _clean_numeric_field(s: str, compress_spaces: bool = True) -> str:
    """Remove useless characters like , or _ from a string.

    Parameters:
        s: The text a user typed into a numeric search field.
        compress_spaces: True to remove spaces as well, which a value that may hold
            a space-separated group of numbers has to leave alone.

    Returns:
        The text in lower case with every comma and underscore removed, and every
        space removed as well unless `compress_spaces` is False.
    """
    ret = s.lower().replace(',', '').replace('_', '')
    if compress_spaces:
        ret = ret.replace(' ', '')
    return ret
