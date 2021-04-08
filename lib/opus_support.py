################################################################################
# opus_support.py
#
# Various parsing and formating routines for the OPUS UI.
#
# MRS 6/5/18
################################################################################

import math
import numpy as np

import julian

################################################################################
# General routines for handling a spacecraft clock where:
#   - there are exactly two fields
#   - the clock partition is always one
################################################################################

def _parse_two_field_sclk(sclk, sep, modval, scname):
    """Convert a two-field clock string to a numeric value.

    Input:
        sclk        the spacecraft clock string.
        sep         the character that separates the fields, typically a colon
                    or a period.
        modval      the modulus value of the second field.
        scname      name of the spacecraft, used for error messages.
        """

    # Check the partition number before ignoring it
    parts = sclk.split('/')
    if len(parts) > 2:
        raise ValueError('Invalid %s clock format, ' % scname +
                         'extraneous slash: ' + sclk)

    if len(parts) == 2:
        if parts[0].strip() != '1':
            raise ValueError('%s partition number must be one: ' % scname +
                             sclk)

        sclk = parts[1]

    # Interpret the fields
    parts = sclk.split(sep)
    # if len(parts) == 1:
    #     raise ValueError('Invalid %s clock format, ' % scname +
    #                      'no field separator: ' + sclk)

    if len(parts) > 2:
        raise ValueError('More than two %s clock fields: ' % scname + sclk)

    if len(parts) != 1:
        # The second field must have the required number of digits
        ndigits2 = len(str(modval - 1))

        while len(parts[1]) < ndigits2:
            parts[1] = parts[1] + '0'

    # Make sure both fields are integers
    ints = []
    try:
        for part in parts:
            ints.append(int(part))
    except ValueError:
        raise ValueError('%s clock fields must be integers: ' % scname + sclk)

    # Append fields to make two
    if len(ints) == 1:
        ints.append(0)

    # Check fields for valid ranges
    if ints[1] >= modval:
        raise ValueError('%s clock trailing field out of range ' % scname +
                         '0-%d: ' % (modval-1) + sclk)

    return ints[0] + ints[1]/float(modval)

def _format_two_field_sclk(value, ndigits, sep, modval, scname):
    """Convert a number into a valid spacecraft clock string.

    Input:
        sclk        the spacecraft clock string.
        ndigits     the number of digits in the leading field. Leading zeros
                    will be used for padding
        sep         the character that separates the fields, typically a colon
                    or a period.
        modval      the modulus value of the second field.
        scname      name of the spacecraft, used for error messages.
        """

    # Extract fields
    hours = int(value)
    value -= hours
    value *= modval

    # Round off minutes
    minutes = int(value + 0.5)
    if minutes >= modval:
        minutes -= modval
        hours += 1

    # Format
    ndigits2 = len(str(modval - 1))
    fmt = '%0' + str(ndigits) + 'd' + sep + '%0' + str(ndigits2) + 'd'
    return fmt % (hours, minutes)

################################################################################
################################################################################
# GALILEO
################################################################################
# Conversion routines for the Galileo spacecraft clock.
#
# The clock has two fields separated by a period. The first field has eight
# digits with leading zeros if necessary. The second is a tw0-digit number
# 0-90. The partition is always 1.
#
# According to the SCLK kernel for Galileo, there are additional subfields.
# However, the first two are all we need for the Galilieo images currently in
# our archive.
################################################################################

def parse_galileo_sclk(sclk):
    """Convert a Galileo clock string to a numeric value."""

    return _parse_two_field_sclk(sclk, '.', 91, 'Galileo')

def format_galileo_sclk(value):
    """Convert a number into a valid Galileo clock string.
    """

    return _format_two_field_sclk(value, 8, '.', 91, 'Galileo')

################################################################################
################################################################################
# NEW HORIZONS
################################################################################
# Conversion routines for the New Horizons spacecraft clock.
#
# The clock has two fields separated by a colon. The first field is a ten-digit
# number with leading zeros if necessary. The second is a five-digit number
# 0-50000. The partition is 1 through 0139810086 and 3 starting at 0168423778.
# No observations in between are archived at the RMS Node. Note that the clock
# count does not roll over between partitions.
################################################################################

def parse_new_horizons_sclk(sclk):
    """Convert a New Horizons clock string to a numeric value."""

    original_sclk = sclk

    # Check for partition number
    parts = sclk.partition('/')
    if parts[1]:        # a slash if present, otherwise an empty string
        if parts[0] not in ('1', '3'):
            raise ValueError('New Horizons partition number must be 1 or 3: ' +
                             sclk)
        sclk = parts[2]

    # Convert to numeric value
    value = _parse_two_field_sclk(sclk, ':', 50000, 'New Horizons')

    # Validate the partition number if any
    if parts[1]:
        if ((parts[0] == '3' and value < 150000000.) or
            (parts[0] == '1' and value > 150000000.)):
                raise ValueError('New Horizons partition number is invalid: ' +
                                 original_sclk)

    return value

def format_new_horizons_sclk(value):
    """Convert a number into a valid New Horizons clock string.
    """

    return _format_two_field_sclk(value, 10, ':', 50000, 'New Horizons')

################################################################################
################################################################################
# CASSINI
################################################################################
# Conversion routines for the Cassini spacecraft clock.
#
# The clock has two fields separated by a dot. The first field has ten digits.
# The second field has three digits 0-255. The partition is always 1. The
# separator is always a dot.
################################################################################

def parse_cassini_sclk(sclk):
    """Convert a Cassini clock string to a numeric value."""

    return _parse_two_field_sclk(sclk, '.', 256, 'Cassini')

def format_cassini_sclk(value):
    """Convert a number into a valid Cassini clock string.
    """

    return _format_two_field_sclk(value, 10, '.', 256, 'Cassini')

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

def parse_cassini_orbit(orbit):
    """Convert Cassini orbit name to an integer."""

    try:
        intval = int(orbit)
        if intval >= 3:
            return intval
        if intval == 0:
            return -1
        raise ValueError('Invalid Cassini orbit %s' % orbit)
    except ValueError:
        pass

    orbit = orbit.upper().strip('0')
    try:
        return CASSINI_ORBIT_NUMBER[orbit]
    except KeyError:
        raise ValueError('Invalid Cassini orbit %s' % orbit)

def format_cassini_orbit(value):
    """Convert an internal number for a Cassini orbit to its displayed value."""

    if value >= 3:
        return '%03d' % value

    try:
        return CASSINI_ORBIT_NAME[value]
    except KeyError:
        raise ValueError('Invalid Cassini orbit %s' % str(value))

################################################################################
# VOYAGER
################################################################################
# Conversion routines for the Voyager spacecraft clock, also known as the
# "FDS" or "Flight Data System" count.
#
# The clock has three fields:
#   "hours": 0-65535
#   "minutes": 0-60
#   "seconds": 1-800 (not 0-799!)
#
# The separator between fields can be a colon or a dot.
#
# The partition is ignored when formatting. When parsing, an FDS count can
# optionally begin with "2/", "3/" or "4/" because these are the partitions
# for the flybys.
#
# When dealing with Voyager products, sometimes we ignore the first separator,
# so parsing six- or seven-digit numbers are handled assuming that the hours and
# minutes have been appended with no separator.
################################################################################

VOYAGER_PLANET_NAMES = {5:'Jupiter', 6:'Saturn', 7:'Uranus', 8:'Neptune'}
VOYAGER_PLANET_PARTITIONS = {5:2, 6:2, 7:3, 8:4}

def parse_voyager_sclk(sclk, planet=None):
    """Convert a Voyager clock string (FDS) to a numeric value.

    Typically, a partition number is not specified for FDS counts. However, if
    it is, it must be compatible with the planetary flyby. The partition number
    is 2 for Jupiter and Saturn, 3 for Uranus, and 4 for Neptune.

    If the planet is not specified (planet = None), then any partition value in
    the range 2-4 is allowed and its value is ignored. If the planet is given as
    input (5 for Jupiter, 6 for Saturn, 7 for Uranus, 8 for Neptune), then an
    explicitly stated partition number must be compatible with the associated
    planetary flyby.
    """

    assert planet in (None, 5, 6, 7, 8), 'Invalid planet value: ' + str(planet)

    # Check the partition number before ignoring it
    parts = sclk.split('/')
    if len(parts) > 2:
        raise ValueError('Invalid FDS format, extraneous "/": ' + sclk)

    if len(parts) == 2:
        try:
            partition = int(parts[0])
        except ValueError:
            raise ValueError('Partition number is not an integer: ' + sclk)

        if planet is None:
            if partition not in VOYAGER_PLANET_PARTITIONS.values():
                raise ValueError('Partition number out of range 2-4: ' + sclk)
        else:
            required_partition = VOYAGER_PLANET_PARTITIONS[planet]
            if partition != required_partition:
                name = VOYAGER_PLANET_NAMES[planet]
                raise ValueError('Partition number for %s flyby ' % name +
                                 'must be %d: ' % required_partition + sclk)

        sclk = parts[1]

    # Separator can be '.' or ':'
    if '.' in sclk:
        parts = sclk.split('.')
    elif ':' in sclk:
        parts = sclk.split(':')
    else:
        parts = [sclk]

    if len(parts) > 3:
        raise ValueError('More than three fields in Voyager clock: ' + sclk)

    # Make sure field are integers
    ints = []
    try:
        for part in parts:
            ints.append(int(part))
    except ValueError:
        raise ValueError('Voyager clock fields must be integers: ' + sclk)

    # If we have just a single six- or seven-digit number, maybe the separator
    # was omitted. This is how Voyager image names are handled.
    if len(ints) == 1 and ints[0] >= 100000:
        ints = [ints[0] // 100, ints[0] % 100]

    # Append fields to make three
    if len(ints) == 1:
        ints.append(0)
    if len(ints) == 2:
        ints.append(1)

    # Check fields for valid ranges
    if ints[0] > 65535 or ints[0] < 0:
        raise ValueError('Voyager clock "hours" out of range 0-65535: ' + sclk)
    if ints[1] > 59 or ints[1] < 0:
        raise ValueError('Voyager clock "minutes" out of range 0-59: ' + sclk)
    if ints[2] > 800 or ints[2] < 1:
        raise ValueError('Voyager clock "seconds" out of range 1-800: ' + sclk)

    # Return in units of FDS hours
    return ints[0] + (ints[1] + (ints[2]-1) / 800.) / 60.

def format_voyager_sclk(value, sep=':', fields=3):
    """Convert a number in units of FDS hours into a valid Voyager clock string.
    """

    assert sep in (':', '.'), 'Separator must be ":" or ".": ' + str(sep)
    assert fields in (2,3), 'Fields must be 2 or 3: ' + str(fields)

    saved_value = value

    # Extract hours, minutes seconds
    hours = int(value)
    value -= hours
    value *= 60

    # Fields == 2
    if fields == 2:
        minutes = int(value + 0.5)  # round off minutes

        # Handle carry
        if minutes >= 60:
            minutes -= 60
            hours += 1

    # Fields == 3
    else:
        minutes = int(value)
        value -= minutes
        value *= 800
        value += 1
        seconds = int(value + 0.5)    # round off seconds

        # Handle carry
        if seconds > 800:
            seconds -= 800
            minutes += 1

            if minutes >= 60:
                minutes -= 60
                hours += 1

    # Check range
    if hours > 65535:
        raise ValueError('Voyager clock "hours" cannot exceed 65535: ' +
                         str(saved_value))

    # Format
    if fields == 3:
        sclk = '%05d%s%02d%s%03d' % (hours, sep, minutes, sep, seconds)
    else:
        sclk = '%05d%s%02d' % (hours, sep, minutes)

    return sclk

################################################################################



def _range_time_encode(tai):
    return julian.iso_from_tai(tai, digits=3)
def _range_time_decode(iso):
    iso = str(iso)
    try:
        (day, sec, time_type) = julian.day_sec_type_from_string(iso)
    except:
        raise ValueError('Invalid time syntax: '+iso)
    if time_type != 'UTC':
        raise ValueError('Invalid time syntax: '+iso)
    return julian.tai_from_day(day) + sec

# Format is decode float->string, encode string->float

RANGE_FUNCTIONS = {
    'range_time':              (_range_time_encode,
                                _range_time_decode),
    'range_cassini_sclk':      (format_cassini_sclk,
                                parse_cassini_sclk),
    'range_galileo_sclk':      (format_galileo_sclk,
                                parse_galileo_sclk),
    'range_new_horizons_sclk': (format_new_horizons_sclk,
                                parse_new_horizons_sclk),
    'range_voyager_sclk':      (format_voyager_sclk,
                                parse_voyager_sclk),
    'range_cassini_rev_no':    (format_cassini_orbit,
                                parse_cassini_orbit),
}

# Unit translation table
# db name : displayed name
UNIT_CONVERSION = {
    '1/cm':
        {
            'display_name': 'cm^-1',
            'conversions': {
                '1/m':         ('m^-1', 1e-2),
            }
        },
    '1/cm/pixel':
        {
            'display_name': 'cm^-1/pixel',
            'conversions': {
                '1/m/pixel':   ('m^-1/pixel', 1e-2),
            }
        },
    'degrees':
        {
            'display_name': 'degrees',
            'conversions': {
                'hourangle':    ('hour angle', 360./24.),
                'radians':      ('radians', 180./3.141592653589)
            }
        },
    'km':
        {
            'display_name': 'km',
            'conversions': {
                'm':            ('m', 1e-3),
                'jupiterradii': ('Rj (71492)', 71492.),
                'saturnradii':  ('Rs (60330)', 60330.),
                'neptuneradii': ('Rn (25225)', 25225.),
                'uranusradii':  ('Ru (25559)', 25559.),
            }
        },
    'km/pixel':
        {
            'display_name': 'km/pixel',
            'conversions': {
                'm/pixel':      ('m/pixel', 1e-3),
            }
        },
    'microns':
        {
            'display_name': 'microns',
            'conversions': {
                'angstroms':    ('angstroms', 1e-4),
                'nm':           ('nm', 1e-3),
                'cm':           ('cm', 1e4),
            }
        },
    'microns/pixel':
        {
            'display_name': 'microns/pixel',
            'conversions': {
                'angstroms/pixel':    ('angstroms/pixel', 1e-4),
                'nm/pixel':           ('nm/pixel', 1e-3),
                'cm/pixel':           ('cm/pixel', 1e4),
            }
        },
    'seconds':
        {
            'display_name': 'secs',
            'conversions': {
                'milliseconds': ('msecs', 1e-3),
                'minutes':      ('minutes', 60.),
                'hours':        ('hours', 60.*60.),
                'days':         ('days', 60.*60.*24.),
            }
        },
    'milliseconds':
        {
            'display_name': 'msec',
            'conversions': {
                'seconds':      ('secs', 1e3),
            }
        },
}

def convert_to_default_unit(val, default_unit, unit):
    if val is None:
        return val
    if default_unit == unit:
        return val
    assert default_unit in UNIT_CONVERSION
    ret = val * UNIT_CONVERSION[default_unit]['conversions'][unit][1]
    if not math.isfinite(ret):
        raise ValueError
    return ret


def convert_from_default_unit(val, default_unit, unit):
    if val is None:
        return val
    if default_unit is None or default_unit == unit:
        return val
    assert default_unit in UNIT_CONVERSION
    ret = val / UNIT_CONVERSION[default_unit]['conversions'][unit][1]
    if not math.isfinite(ret):
        raise ValueError
    return ret

def get_valid_units(default_unit):
    default_unit_info = UNIT_CONVERSION.get(default_unit, None)
    valid_units = None
    if default_unit_info is not None:
        valid_units = list(default_unit_info['conversions'].keys())
        valid_units = [default_unit] + valid_units
    return valid_units

# Get a dictionary with valid units as keys and display names as values.
def get_display_names(default_unit):
    default_unit_info = UNIT_CONVERSION.get(default_unit, None)
    display_names = None
    if default_unit_info is not None:
        display_names = {}
        display_names[default_unit] = default_unit_info['display_name']
        valid_units = default_unit_info['conversions']
        for unit in valid_units:
            display_names[unit] =  valid_units[unit][0]
    return display_names

def is_valid_unit(default_unit, unit):
    if default_unit == unit:
        return True
    return unit in UNIT_CONVERSION[default_unit]['conversions']

def adjust_format_string_for_units(format, default_unit, unit):
    if default_unit is None or default_unit == unit:
        return format
    if not format.startswith('.') or not format.endswith('f'):
        return format
    assert default_unit in UNIT_CONVERSION
    # The behavior of ceil is to increase the number of positive numbers
    # (which is adding decimal places), which is good. And it's to decrease
    # the absolute value of negative numbers (which is removing decimal places),
    # which is also good. In both cases we're being conservative - adding too
    # many or removing too few.
    factor = int(np.ceil(np.log10(
                UNIT_CONVERSION[default_unit]['conversions'][unit][1])))
    dec = max(int(format[1:-1]) + factor, 0)
    return '.' + str(dec) + 'f'
