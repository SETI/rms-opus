"""Text-tidying helpers shared by the angle and unit conversions.

This module is private: neither helper is part of the package's public surface.
"""

import re


def _strip_trailing_zeros(s):
    """Strip meaningless trailing zeros (like after a decimal point)."""
    if re.fullmatch(r'.*\.\d*0*', s):
        # Strip trailing .000s from NNN.DDDZZZ
        s = s.rstrip('0').rstrip('.')
    elif re.fullmatch(r'.*\.\d*0*e[+-]\d+', s):
        # Strip trailing .000s from the mantissa part of NNN.DDDZZZe+EEE
        s1, s2 = s.split('e')
        s1 = s1.rstrip('0').rstrip('.')
        s = s1+'e'+s2
    return s

def _clean_numeric_field(s, compress_spaces=True):
    """Remove useless characters like , or _ from a string."""
    ret = s.lower().replace(',', '').replace('_','')
    if compress_spaces:
        ret = ret.replace(' ', '')
    return ret
