"""Cassini orbit-number conversions."""

################################################################################
# Conversion routines for the Cassini orbit number.
#
# Cassini Saturn orbits are numbered 0, A, B, C, 3, 4, 5, ...
#
# In this conversion, the mapping is:
#   0 -> -1
#   A -> 0
#   B -> 1
#   C -> 2
#   3 -> 3
#   All higher numbers map to themselves.
################################################################################

CASSINI_ORBIT_NUMBER: dict[str, int] = {'A':0, 'B':1, 'C':2}
CASSINI_ORBIT_NAME: dict[int, str] = {-1:'000', 0:'00A', 1:'00B', 2:'00C'}

def parse_cassini_orbit(orbit: str, **kwargs: object) -> int:
    """Convert Cassini orbit name to an integer.

    The orbit may be zero-padded ("00A", "004").

    Parameters:
        orbit: The orbit name, either the digits of an orbit numbered 0 or 3 and
            above, or one of the letters A, B and C naming the second, third and
            fourth orbits.
        **kwargs: Accepted and ignored, so that every parser in this package can be
            called through one uniform dispatch.

    Returns:
        The internal orbit number -- -1 for orbit 0, 0, 1 and 2 for A, B and C, and
        the orbit's own number for every orbit of 3 or more.

    Raises:
        ValueError: If the orbit is none of 0, a number of 3 or more, or a letter
            name. The message names the orbit exactly as it was supplied.
    """
    try:
        intval = int(orbit)
    except ValueError:
        pass  # Not a number, so it has to be one of the letter names below.
    else:
        if intval >= 3:
            return intval
        if intval == 0:
            return -1
        raise ValueError(f'Invalid Cassini orbit {orbit}')

    name = orbit.upper().strip('0')
    if name not in CASSINI_ORBIT_NUMBER:
        raise ValueError(f'Invalid Cassini orbit {orbit}')
    return CASSINI_ORBIT_NUMBER[name]

def format_cassini_orbit(value: int, **kwargs: object) -> str:
    """Convert an internal number for a Cassini orbit to its displayed value.

    Parameters:
        value: The internal orbit number, as `parse_cassini_orbit` returns it.
        **kwargs: Accepted and ignored, so that every formatter in this package can
            be called through one uniform dispatch.

    Returns:
        The orbit name -- "000", "00A", "00B" and "00C" for -1, 0, 1 and 2, and the
        number itself zero-padded to three digits for every value of 3 or more.

    Raises:
        ValueError: If the value names no orbit -- one below 3 that is not -1, 0, 1
            or 2, or one of 3 or more that is not an int.
    """
    if value >= 3:
        return f'{value:03d}'

    if value not in CASSINI_ORBIT_NAME:
        raise ValueError(f'Invalid Cassini orbit {value}')
    return CASSINI_ORBIT_NAME[value]
