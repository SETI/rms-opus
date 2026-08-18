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

CASSINI_ORBIT_NUMBER = {'A':0, 'B':1, 'C':2}
CASSINI_ORBIT_NAME = {-1:'000', 0:'00A', 1:'00B', 2:'00C'}

def parse_cassini_orbit(orbit, **kwargs):
    """Convert Cassini orbit name to an integer.

    The orbit may be zero-padded ("00A", "004").

    Raises:
        ValueError: If the orbit is none of 0, a number of 3 or more, or a letter name.
            The message names the orbit exactly as it was supplied.
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
    try:
        return CASSINI_ORBIT_NUMBER[name]
    except KeyError as err:
        raise ValueError(f'Invalid Cassini orbit {orbit}') from err

def format_cassini_orbit(value, **kwargs):
    """Convert an internal number for a Cassini orbit to its displayed value.

    Raises:
        ValueError: If the value names no orbit -- one below 3 that is not -1, 0, 1 or 2,
            or one of 3 or more that is not an int.
    """
    if value >= 3:
        return f'{value:03d}'

    try:
        return CASSINI_ORBIT_NAME[value]
    except KeyError as err:
        raise ValueError(f'Invalid Cassini orbit {value}') from err
