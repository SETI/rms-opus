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
    """Convert Cassini orbit name to an integer."""
    try:
        intval = int(orbit)
        if intval >= 3:
            return intval
        if intval == 0:
            return -1
        raise ValueError(f'Invalid Cassini orbit {orbit}')
    except ValueError:
        pass

    orbit = orbit.upper().strip('0')
    try:
        return CASSINI_ORBIT_NUMBER[orbit]
    except KeyError as err:
        raise ValueError(f'Invalid Cassini orbit {orbit}') from err

def format_cassini_orbit(value, **kwargs):
    """Convert an internal number for a Cassini orbit to its displayed value."""
    if value >= 3:
        return f'{value:03d}'

    try:
        return CASSINI_ORBIT_NAME[value]
    except KeyError as err:
        raise ValueError(f'Invalid Cassini orbit {value}') from err
