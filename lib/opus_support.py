################################################################################
# opus_support.py
#
# General routines that are shared by the OPUS import pipeline and the OPUS
# Django backend and thus can't be in either directory.
#
# These are generally related to conversion of values to/from various text
# formats.
################################################################################

import math
import numpy as np
import re
import unittest

import julian # From pds-tools

DEG_RAD = np.degrees(1)

# We limit the available times because julian doesn't support parsing dates
# outside of this range
MIN_TIME = -31556908800 # 1000-01-01T00:00:00
MAX_TIME =  31556995236 # 2999-12-31T23:59:59

################################################################################
# General routines for handling a spacecraft clock where:
#   - there are exactly two fields
#   - the clock partition is always one
################################################################################

def _parse_two_field_sclk(sclk, ndigits, sep, modval, scname):
    """Convert a two-field clock string to a numeric value.

    Input:
        sclk        the spacecraft clock string.
        ndigits     the maximum number of digits in the leading field.
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
    if (ints[0] < 0 or len(parts[0]) > ndigits or
        ints[1] < 0 or ints[1] >= modval):
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
# digits with leading zeros if necessary. The second is a two-digit number
# 0-90. The partition is always 1.
#
# According to the SCLK kernel for Galileo, there are additional subfields.
# However, the first two are all we need for the Galilieo images currently in
# our archive.
################################################################################

def parse_galileo_sclk(sclk, **kwargs):
    """Convert a Galileo clock string to a numeric value."""

    return _parse_two_field_sclk(sclk, 8, '.', 91, 'Galileo')

def format_galileo_sclk(value, **kwargs):
    """Convert a number into a valid Galileo clock string.
    """

    return _format_two_field_sclk(value, 8, '.', 91, 'Galileo')

class GalileoTest(unittest.TestCase):
    def test_parse_extra_slash(self):
        "Galileo parse: Two slashes"
        with self.assertRaises(ValueError):
            parse_galileo_sclk('1/2/03464059.00')

    def test_parse_bad_partition(self):
        "Galileo parse: Partition number other than 1"
        with self.assertRaises(ValueError):
            parse_galileo_sclk('2/03464059.00')
        with self.assertRaises(ValueError):
            parse_galileo_sclk('0/03464059.00')
        with self.assertRaises(ValueError):
            parse_galileo_sclk('1.0/03464059.00')
        with self.assertRaises(ValueError):
            parse_galileo_sclk('-1/03464059.00')
        with self.assertRaises(ValueError):
            parse_galileo_sclk('a/03464059.00')
        with self.assertRaises(ValueError):
            parse_galileo_sclk('/03464059.00')
        with self.assertRaises(ValueError):
            parse_galileo_sclk('1/03464059.00.00')

    def test_parse_bad_value(self):
        "Galileo parse: Bad sclk value"
        with self.assertRaises(ValueError):
            parse_galileo_sclk('1/a')
        with self.assertRaises(ValueError):
            parse_galileo_sclk('1/0123456a')
        with self.assertRaises(ValueError):
            parse_galileo_sclk('1/03464059.0a')
        with self.assertRaises(ValueError):
            parse_galileo_sclk('1/03464059.-1')
        with self.assertRaises(ValueError):
            parse_galileo_sclk('1/03464059.91')
        with self.assertRaises(ValueError):
            parse_galileo_sclk('1/03464059.450')
        with self.assertRaises(ValueError):
            parse_galileo_sclk('1/034640590.00')
        with self.assertRaises(ValueError):
            parse_galileo_sclk('.00')
        with self.assertRaises(ValueError):
            parse_galileo_sclk('1/.00')
        with self.assertRaises(ValueError):
            parse_galileo_sclk('1/-1.00')
        with self.assertRaises(ValueError):
            parse_galileo_sclk('1/-34640590.00')

    def test_parse_good_sclk(self):
        "Galileo parse: Good sclk format"
        self.assertEqual(parse_galileo_sclk('1.'), 1)
        self.assertEqual(parse_galileo_sclk('1.0'), 1)
        self.assertEqual(parse_galileo_sclk('1.00'), 1)
        self.assertEqual(parse_galileo_sclk('1/03464059.00'), 3464059)
        self.assertAlmostEqual(parse_galileo_sclk('1/03464059.90'),
                               3464059.989010989)
        self.assertAlmostEqual(parse_galileo_sclk('1/3464059.90'),
                               3464059.989010989)
        self.assertAlmostEqual(parse_galileo_sclk('1/3464059.9'),
                               3464059.989010989)
        self.assertAlmostEqual(parse_galileo_sclk('03464059.90'),
                               3464059.989010989)

    def test_format_good_sclk(self):
        "Galileo format: Good value"
        self.assertEqual(format_galileo_sclk(0), '00000000.00')
        self.assertEqual(format_galileo_sclk(1234), '00001234.00')
        self.assertEqual(format_galileo_sclk(12345678), '12345678.00')
        self.assertEqual(format_galileo_sclk(1234.989010989), '00001234.90')
        self.assertEqual(format_galileo_sclk(99999999.989010989), '99999999.90')


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

def parse_new_horizons_sclk(sclk, **kwargs):
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
    value = _parse_two_field_sclk(sclk, 10, ':', 50000, 'New Horizons')

    # Validate the partition number if any
    if parts[1]:
        if ((parts[0] == '3' and value < 150000000.) or
            (parts[0] == '1' and value > 150000000.)):
                raise ValueError('New Horizons partition number is invalid: ' +
                                 original_sclk)

    return value

def format_new_horizons_sclk(value, **kwargs):
    """Convert a number into a valid New Horizons clock string.
    """

    return _format_two_field_sclk(value, 10, ':', 50000, 'New Horizons')

class NewHorizonsTest(unittest.TestCase):
    def test_parse_extra_slash(self):
        "NewHorizons parse: Two slashes"
        with self.assertRaises(ValueError):
            parse_new_horizons_sclk('1/2/0003103485:49000')

    def test_parse_bad_partition(self):
        "NewHorizons parse: Partition number other than 1 or 3"
        with self.assertRaises(ValueError):
            parse_new_horizons_sclk('4/0003103485:49000')
        with self.assertRaises(ValueError):
            parse_new_horizons_sclk('2/0003103485:49000')
        with self.assertRaises(ValueError):
            parse_new_horizons_sclk('0/0003103485:49000')
        with self.assertRaises(ValueError):
            parse_new_horizons_sclk('1.0/0003103485:49000')
        with self.assertRaises(ValueError):
            parse_new_horizons_sclk('-1/0003103485:49000')
        with self.assertRaises(ValueError):
            parse_new_horizons_sclk('a/0003103485:49000')
        with self.assertRaises(ValueError):
            parse_new_horizons_sclk('/0003103485:49000')
        with self.assertRaises(ValueError):
            parse_new_horizons_sclk('1/0003103485:49000:49000')

    def test_parse_bad_value(self):
        "NewHorizons parse: Bad sclk value"
        with self.assertRaises(ValueError):
            parse_new_horizons_sclk('1/a')
        with self.assertRaises(ValueError):
            parse_new_horizons_sclk('1/000310348a')
        with self.assertRaises(ValueError):
            parse_new_horizons_sclk('1/0003103485:4900a')
        with self.assertRaises(ValueError):
            parse_new_horizons_sclk('1/0003103485:-10000')
        with self.assertRaises(ValueError):
            parse_new_horizons_sclk('1/0003103485:50000')
        with self.assertRaises(ValueError):
            parse_new_horizons_sclk('1/0003103485:99999')
        with self.assertRaises(ValueError):
            parse_new_horizons_sclk('1/00003103485:49000')
        with self.assertRaises(ValueError):
            parse_new_horizons_sclk(':00000')
        with self.assertRaises(ValueError):
            parse_new_horizons_sclk('1/:00000')
        with self.assertRaises(ValueError):
            parse_new_horizons_sclk('1/-1.00000')
        with self.assertRaises(ValueError):
            parse_new_horizons_sclk('1/-0003103485:00000')
        with self.assertRaises(ValueError):
            parse_new_horizons_sclk('1/0150000000:00001')
        with self.assertRaises(ValueError):
            parse_new_horizons_sclk('3/0149999999:49999')

    def test_parse_good_sclk(self):
        "NewHorizons parse: Good sclk format"
        self.assertEqual(parse_new_horizons_sclk('1:'), 1)
        self.assertEqual(parse_new_horizons_sclk('1:0'), 1)
        self.assertEqual(parse_new_horizons_sclk('1:00'), 1)
        self.assertEqual(parse_new_horizons_sclk('1/0003103485:25'), 3103485.5)
        self.assertEqual(parse_new_horizons_sclk('1/0003103485:25000'),
                         3103485.5)
        self.assertEqual(parse_new_horizons_sclk('3/1003103485:25000'),
                         1003103485.5)
        self.assertEqual(parse_new_horizons_sclk('1/3103485:25000'),
                         3103485.5)
        self.assertEqual(parse_new_horizons_sclk('1/3103485:25'),
                         3103485.5)
        self.assertEqual(parse_new_horizons_sclk('0003103485:25000'),
                         3103485.5)
        self.assertEqual(parse_new_horizons_sclk('3/9999999999:49999'),
                         9999999999.99998)
        self.assertEqual(parse_new_horizons_sclk('1/0149999999:49999'),
                         149999999.99998)
        self.assertEqual(parse_new_horizons_sclk('3/0150000000:00001'),
                         150000000.00002)

    def test_format_good_sclk(self):
        "NewHorizons format: Good value"
        self.assertEqual(format_new_horizons_sclk(0), '0000000000:00000')
        self.assertEqual(format_new_horizons_sclk(1234), '0000001234:00000')
        self.assertEqual(format_new_horizons_sclk(1234567890),
                         '1234567890:00000')
        self.assertEqual(format_new_horizons_sclk(1234.5), '0000001234:25000')


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

def parse_cassini_sclk(sclk, **kwargs):
    """Convert a Cassini clock string to a numeric value."""

    return _parse_two_field_sclk(sclk, 10, '.', 256, 'Cassini')

def format_cassini_sclk(value, **kwargs):
    """Convert a number into a valid Cassini clock string.
    """

    return _format_two_field_sclk(value, 10, '.', 256, 'Cassini')

class CassiniTest(unittest.TestCase):
    def test_parse_extra_slash(self):
        "Cassini parse: Two slashes"
        with self.assertRaises(ValueError):
            parse_cassini_sclk('1/2/1294341579.000')

    def test_parse_bad_partition(self):
        "Cassini parse: Partition number other than 1"
        with self.assertRaises(ValueError):
            parse_cassini_sclk('2/1294341579.000')
        with self.assertRaises(ValueError):
            parse_cassini_sclk('0/1294341579.000')
        with self.assertRaises(ValueError):
            parse_cassini_sclk('1.0/1294341579.000')
        with self.assertRaises(ValueError):
            parse_cassini_sclk('-1/1294341579.000')
        with self.assertRaises(ValueError):
            parse_cassini_sclk('a/1294341579.000')
        with self.assertRaises(ValueError):
            parse_cassini_sclk('/1294341579.000')
        with self.assertRaises(ValueError):
            parse_cassini_sclk('1/1294341579.000.000')

    def test_parse_bad_value(self):
        "Cassini parse: Bad sclk value"
        with self.assertRaises(ValueError):
            parse_cassini_sclk('1/a')
        with self.assertRaises(ValueError):
            parse_cassini_sclk('1/0123456a')
        with self.assertRaises(ValueError):
            parse_cassini_sclk('1/1294341579.00a')
        with self.assertRaises(ValueError):
            parse_cassini_sclk('1/1294341579.-1')
        with self.assertRaises(ValueError):
            parse_cassini_sclk('1/1294341579.256')
        with self.assertRaises(ValueError):
            parse_cassini_sclk('1/1294341579.2560')
        with self.assertRaises(ValueError):
            parse_cassini_sclk('1/01294341579.000')
        with self.assertRaises(ValueError):
            parse_cassini_sclk('.000')
        with self.assertRaises(ValueError):
            parse_cassini_sclk('1/.000')
        with self.assertRaises(ValueError):
            parse_cassini_sclk('1/-1.000')
        with self.assertRaises(ValueError):
            parse_cassini_sclk('1/-34640590.000')

    def test_parse_good_sclk(self):
        "Cassini parse: Good sclk format"
        self.assertEqual(parse_cassini_sclk('1.'), 1)
        self.assertEqual(parse_cassini_sclk('1.0'), 1)
        self.assertEqual(parse_cassini_sclk('1.00'), 1)
        self.assertEqual(parse_cassini_sclk('1/03464059.00'), 3464059)
        self.assertEqual(parse_cassini_sclk('1/0003464059.064'),
                         3464059.25)
        self.assertEqual(parse_cassini_sclk('1/3464059.064'),
                         3464059.25)
        self.assertEqual(parse_cassini_sclk('03464059.064'),
                         3464059.25)

    def test_format_good_sclk(self):
        "Cassini format: Good value"
        self.assertEqual(format_cassini_sclk(0), '0000000000.000')
        self.assertEqual(format_cassini_sclk(1234), '0000001234.000')
        self.assertEqual(format_cassini_sclk(1234567890), '1234567890.000')
        self.assertEqual(format_cassini_sclk(1234.250), '0000001234.064')
        self.assertEqual(format_cassini_sclk(1234.5), '0000001234.128')
        self.assertEqual(format_cassini_sclk(1234.750), '0000001234.192')


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
        raise ValueError('Invalid Cassini orbit %s' % orbit)
    except ValueError:
        pass

    orbit = orbit.upper().strip('0')
    try:
        return CASSINI_ORBIT_NUMBER[orbit]
    except KeyError:
        raise ValueError('Invalid Cassini orbit %s' % orbit)

def format_cassini_orbit(value, **kwargs):
    """Convert an internal number for a Cassini orbit to its displayed value."""

    if value >= 3:
        return '%03d' % value

    try:
        return CASSINI_ORBIT_NAME[value]
    except KeyError:
        raise ValueError('Invalid Cassini orbit %s' % str(value))

class CassiniOrbitTest(unittest.TestCase):
    def test_parse_bad_orbit(self):
        "CassiniOrbit parse: Bad orbit"
        with self.assertRaises(ValueError):
            parse_cassini_orbit('-1')
        with self.assertRaises(ValueError):
            parse_cassini_orbit('1')
        with self.assertRaises(ValueError):
            parse_cassini_orbit('2')

    def test_parse_good_orbit(self):
        "CassiniOrbit parse: Good orbit"
        self.assertEqual(parse_cassini_orbit('0'), -1)
        self.assertEqual(parse_cassini_orbit('A'), 0)
        self.assertEqual(parse_cassini_orbit('0A'), 0)
        self.assertEqual(parse_cassini_orbit('00A'), 0)
        self.assertEqual(parse_cassini_orbit('a'), 0)
        self.assertEqual(parse_cassini_orbit('0a'), 0)
        self.assertEqual(parse_cassini_orbit('00a'), 0)
        self.assertEqual(parse_cassini_orbit('B'), 1)
        self.assertEqual(parse_cassini_orbit('b'), 1)
        self.assertEqual(parse_cassini_orbit('C'), 2)
        self.assertEqual(parse_cassini_orbit('c'), 2)
        self.assertEqual(parse_cassini_orbit('3'), 3)
        self.assertEqual(parse_cassini_orbit('4'), 4)

    def test_format_bad_orbit(self):
        "CassiniOrbit format: Bad orbit"
        with self.assertRaises(ValueError):
            format_cassini_orbit(-2)

    def test_format_good_orbit(self):
        "CassiniOrbit format: Good orbit"
        self.assertEqual(format_cassini_orbit(-1), '000')
        self.assertEqual(format_cassini_orbit(0), '00A')
        self.assertEqual(format_cassini_orbit(1), '00B')
        self.assertEqual(format_cassini_orbit(2), '00C')
        self.assertEqual(format_cassini_orbit(3), '003')
        self.assertEqual(format_cassini_orbit(4), '004')


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

def parse_voyager_sclk(sclk, planet=None, **kwargs):
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

def format_voyager_sclk(value, sep=':', fields=3, **kwargs):
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

class VoyagerTest(unittest.TestCase):
    def test_parse_extra_slash(self):
        "Cassini parse: Two slashes"
        with self.assertRaises(ValueError):
            parse_voyager_sclk('1/2/08966:30:752')

    def test_parse_bad_partition(self):
        "Voyager parse: Bad partition/planet"
        with self.assertRaises(ValueError):
            parse_voyager_sclk('1/08966:30:752')
        with self.assertRaises(ValueError):
            parse_voyager_sclk('5/08966:30:752')
        with self.assertRaises(ValueError):
            parse_voyager_sclk('-1/08966:30:752')
        with self.assertRaises(ValueError):
            parse_voyager_sclk('6/08966:30:752')
        with self.assertRaises(ValueError):
            parse_voyager_sclk('a/08966:30:752')
        with self.assertRaises(AssertionError):
            parse_voyager_sclk('1/08966:30:752', planet=4)
        with self.assertRaises(AssertionError):
            parse_voyager_sclk('1/08966:30:752', planet=9)
        with self.assertRaises(ValueError):
            parse_voyager_sclk('1/08966:30:752', planet=5)
        with self.assertRaises(ValueError):
            parse_voyager_sclk('3/08966:30:752', planet=5)
        with self.assertRaises(ValueError):
            parse_voyager_sclk('1/08966:30:752', planet=6)
        with self.assertRaises(ValueError):
            parse_voyager_sclk('3/08966:30:752', planet=6)
        with self.assertRaises(ValueError):
            parse_voyager_sclk('1/08966:30:752', planet=7)
        with self.assertRaises(ValueError):
            parse_voyager_sclk('2/08966:30:752', planet=7)
        with self.assertRaises(ValueError):
            parse_voyager_sclk('1/08966:30:752', planet=8)
        with self.assertRaises(ValueError):
            parse_voyager_sclk('5/08966:30:752', planet=8)

    def test_parse_bad_sclk(self):
        "Voyager parse: Bad sclk"
        with self.assertRaises(ValueError):
            parse_voyager_sclk('0:0:0')
        with self.assertRaises(ValueError):
            parse_voyager_sclk('0:0:801')
        with self.assertRaises(ValueError):
            parse_voyager_sclk('0:-1:0')
        with self.assertRaises(ValueError):
            parse_voyager_sclk('0:61:0')
        with self.assertRaises(ValueError):
            parse_voyager_sclk('-1:0:0')
        with self.assertRaises(ValueError):
            parse_voyager_sclk('65536:0:0')
        with self.assertRaises(ValueError):
            parse_voyager_sclk('0:0:a')
        with self.assertRaises(ValueError):
            parse_voyager_sclk('0:a:0')
        with self.assertRaises(ValueError):
            parse_voyager_sclk('a:0:0')

    def test_parse_good_partition(self):
        "Voyager parse: Good partition/planet"
        self.assertAlmostEqual(parse_voyager_sclk('2/0:0:1'), 0)
        self.assertAlmostEqual(parse_voyager_sclk('3/0:0:1'), 0)
        self.assertAlmostEqual(parse_voyager_sclk('4/0:0:1'), 0)
        self.assertAlmostEqual(parse_voyager_sclk('2/0:0:1', planet=5), 0)
        self.assertAlmostEqual(parse_voyager_sclk('2/0:0:1', planet=6), 0)
        self.assertAlmostEqual(parse_voyager_sclk('3/0:0:1', planet=7), 0)
        self.assertAlmostEqual(parse_voyager_sclk('4/0:0:1', planet=8), 0)

    def test_parse_good_sclk(self):
        "Voyager parse: Good sclk"
        self.assertEqual(parse_voyager_sclk('0'), 0)
        self.assertEqual(parse_voyager_sclk('0:0'), 0)
        self.assertEqual(parse_voyager_sclk('0:0:1'), 0)
        self.assertEqual(parse_voyager_sclk('0:0:401'), .5/60.)
        self.assertEqual(parse_voyager_sclk('0:1:1'), 1/60.)
        self.assertEqual(parse_voyager_sclk('1:0:1'), 1)
        self.assertEqual(parse_voyager_sclk('1000:00:001'), 1000)
        self.assertEqual(parse_voyager_sclk('1000.00.001'), 1000)
        self.assertEqual(parse_voyager_sclk('100000'), 1000)

    def test_format_good_sclk(self):
        self.assertEqual(format_voyager_sclk(0), '00000:00:001')
        self.assertEqual(format_voyager_sclk(.5/60), '00000:00:401')
        self.assertEqual(format_voyager_sclk(1/60), '00000:01:001')
        self.assertEqual(format_voyager_sclk(1), '00001:00:001')
        self.assertEqual(format_voyager_sclk(5000), '05000:00:001')


################################################################################
################################################################################
# TIME CONVERSION
################################################################################

def parse_time(iso, unit=None, **kwargs):
    iso = str(iso)
    try:
        # For raw numbers, try to use the current unit to figure out what
        # to do
        et = float(iso)
        if not math.isfinite(et):
            raise ValueError('Invalid time syntax: '+iso)
        if unit == 'et':
            return julian.tai_from_tdb(et)
        elif unit == 'jd':
            iso = 'JD' + iso
        elif unit == 'jed':
            iso = 'JED' + iso
        elif unit == 'mjd':
            iso = 'MJD' + iso
        elif unit == 'mjed':
            iso = 'MJED' + iso
    except:
        pass
    try:
        (day, sec, time_type) = julian.day_sec_type_from_string(iso)
    except:
        raise ValueError('Invalid time syntax: '+iso)
    if time_type != 'UTC':
        raise ValueError('Invalid time syntax: '+iso)
    ret = julian.tai_from_day(day) + sec
    if ret < MIN_TIME or ret > MAX_TIME:
        raise ValueError
    return ret

def format_time_ymd(tai, **kwargs):
    return julian.iso_from_tai(tai, ymd=True, digits=3)

def format_time_ydoy(tai, **kwargs):
    return julian.iso_from_tai(tai, ymd=False, digits=3)

def format_time_jd(tai, **kwargs):
    (day, sec) = julian.day_sec_from_tai(tai)
    jd = julian.jd_from_day_sec(day, sec)
    # We want seconds at a resolution of .001
    # There are 86400 seconds in a day, which is roughly 100,000
    # So we want 5+3=8 decimal places
    return 'JD%.8f' % jd

def format_time_jed(tai, **kwargs):
    jed = julian.jed_from_tai(tai)
    # We want seconds at a resolution of .001
    # There are 86400 seconds in a day, which is roughly 100,000
    # So we want 5+3=8 decimal places
    return 'JED%.8f' % jed

def format_time_mjd(tai, **kwargs):
    (day, sec) = julian.day_sec_from_tai(tai)
    mjd = julian.mjd_from_day_sec(day, sec)
    # We want seconds at a resolution of .001
    # There are 86400 seconds in a day, which is roughly 100,000
    # So we want 5+3=8 decimal places
    return 'MJD%.8f' % mjd

def format_time_mjed(tai, **kwargs):
    mjed = julian.mjed_from_tai(tai)
    # We want seconds at a resolution of .001
    # There are 86400 seconds in a day, which is roughly 100,000
    # So we want 5+3=8 decimal places
    return 'MJED%.8f' % mjed

def format_time_et(tai, **kwargs):
    et = julian.tdb_from_tai(tai)
    return '%.3f' % et

class TimeTest(unittest.TestCase):
    # Note - julian.py has its own test suite, so we don't need to duplicate
    # all that here. We just do a couple of simple tests to make sure the
    # interface is working.
    def test_format_ymd(self):
        "Time format: YMD"
        self.assertEqual(format_time_ymd(0), '1999-12-31T23:59:28.000')
        self.assertEqual(format_time_ymd(600000000), '2019-01-05T10:39:23.000')

    def test_format_ydoy(self):
        "Time format: YDOY"
        self.assertEqual(format_time_ydoy(0), '1999-365T23:59:28.000')
        self.assertEqual(format_time_ydoy(600000000), '2019-005T10:39:23.000')

    def test_format_jd(self):
        "Time format: JD"
        self.assertEqual(format_time_jd(0), 'JD2451544.49962963')
        self.assertEqual(format_time_jd(600000000), 'JD2458488.94401620')

    def test_format_jed(self):
        "Time format: JED"
        self.assertEqual(format_time_jed(0), 'JED2451544.50037250')
        self.assertEqual(format_time_jed(600000000), 'JED2458488.94481695')

    def test_format_mjd(self):
        "Time format: MJD"
        self.assertEqual(format_time_mjd(0), 'MJD51543.99962963')
        self.assertEqual(format_time_mjd(600000000), 'MJD58488.44401620')

    def test_format_mjed(self):
        "Time format: MJED"
        self.assertEqual(format_time_mjed(0), 'MJED51544.00037250')
        self.assertEqual(format_time_mjed(600000000), 'MJED58488.44481695')

    def test_format_et(self):
        "Time format: ET"
        self.assertEqual(format_time_et(0), '-43167.816')
        self.assertEqual(format_time_et(600000000), '599956832.184')

    def test_parse(self):
        "Time parse"
        self.assertEqual(parse_time('1999-12-31T23:59:28.000'), 0)
        self.assertEqual(parse_time('2019-005T10:39:23.000'), 600000000)
        self.assertEqual(julian.jd_from_time(julian.time_from_jd(0)), 0)
        self.assertAlmostEqual(julian.jd_from_time(
                                julian.time_from_jd(1000.123)),
                               1000.123)
        self.assertEqual(julian.mjd_from_time(julian.time_from_mjd(0)), 0)
        self.assertAlmostEqual(julian.mjd_from_time(
                                julian.time_from_mjd(1000.123)),
                               1000.123)
        self.assertAlmostEqual(parse_time('JD2451544.49962963'), 0, places=3)
        self.assertAlmostEqual(parse_time('JD2458488.94401620'), 600000000,
                               places=3)
        self.assertAlmostEqual(parse_time('JED2451544.49962963'),
                               -64.18391461631109, places=3)
        self.assertAlmostEqual(parse_time('JED2458488.94401620'),
                               599999930.8156223, places=3)
        self.assertAlmostEqual(parse_time('MJD51543.99962963'), 0, places=3)
        self.assertAlmostEqual(parse_time('MJD58488.44401620'), 600000000,
                               places=3)
        self.assertAlmostEqual(parse_time('MJED51543.99962963'),
                               -64.18391461631109, places=3)
        self.assertAlmostEqual(parse_time('MJED58488.44401620'),
                               599999930.8156223, places=3)
        with self.assertRaises(ValueError):
            parse_time('nan')
        with self.assertRaises(ValueError):
            parse_time('inf')
        self.assertAlmostEqual(parse_time('-43167.816'), 0, places=3)
        self.assertAlmostEqual(parse_time('599956832.184'), 600000000, places=3)

    def test_idopotent(self):
        "Time idempotency"
        self.assertEqual(format_time_ymd(parse_time('2015-05-03T10:12:34.123')),
                         '2015-05-03T10:12:34.123')
        self.assertEqual(format_time_ydoy(parse_time('2015-122T10:12:34.123')),
                         '2015-122T10:12:34.123')
        self.assertEqual(format_time_jd(parse_time('JD123456789.123')),
                         'JD123456789.12300000')
        self.assertEqual(format_time_jed(parse_time('JED123456789.123')),
                         'JED123456789.12300000')


################################################################################
################################################################################
# ANGLE CONVERSION
################################################################################

def parse_dms_hms(s, conversion_factor=1, **kwargs):
    """Parse DMS, HMS, or single number, but "x x x" defaults to DMS."""
    return _parse_dms_hms(s, conversion_factor, allow_dms=True, allow_hms=True,
                          default='dms')

def parse_hms_dms(s, conversion_factor=1, **kwargs):
    """Parse DMS, HMS, or single number, but "x x x" defaults to HMS."""
    return _parse_dms_hms(s, conversion_factor, allow_dms=True, allow_hms=True,
                          default='hms')

def parse_dms(s, conversion_factor=1, **kwargs):
    """Parse a DMS string or single number."""
    return _parse_dms_hms(s, conversion_factor, allow_dms=True, allow_hms=False,
                          default='dms')

def parse_hms(s, conversion_factor=1, **kwargs):
    """Parse an HMS string or single number."""
    return _parse_dms_hms(s, conversion_factor, allow_dms=False, allow_hms=True,
                          default='hms')

def _parse_dms_hms(s, conversion_factor=1, allow_dms=True, allow_hms=True,
                   default='dms'):
    """Parse a DMS or HMS or "x x x" or plain number."""
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

    format_types = []
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
            match = re.fullmatch(r'(|[+-]) *(\d+)()()() +(\d+)() +(\d+(|.\d*))', s)
        if match:
            neg = match[1]
            degrees_hours = match[2]
            minute = match[6]
            second = match[8]
            force_dh_int = False
            force_m_int = False
            val = 0
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
                if force_m_int:
                    if minute != int(minute):
                        raise ValueError
                if not math.isfinite(minute) or minute < 0 or minute >= 60:
                    raise ValueError
                val += minute / 60
            if degrees_hours:
                degrees_hours = degrees_hours.strip(format_char)
                degrees_hours = float(degrees_hours)
                if force_dh_int:
                    if degrees_hours != int(degrees_hours):
                        raise ValueError
                if not math.isfinite(degrees_hours):
                    raise ValueError
                val += degrees_hours
            if neg == '-':
                val = -val
            return val * format_factor / conversion_factor

    # We don't want to allow numbers with spaces in them because that will cause
    # potential ambiguity with the "x x x" DMS/HMS format.
    s = _clean_numeric_field(s, compress_spaces=False)
    ret = float(s)
    if not math.isfinite(ret):
        raise ValueError

    # Note: It is very important that parse_hms_dms is NOT USED for things like
    # units == 'radians' because this factor of 15 will be applied
    # inappropriately
    if default == 'hms':
        ret *= 15

    return ret


def format_dms_hms(val, unit_id=None, unit=None, numerical_format=None,
                   keep_trailing_zeros=False):
    """Format a number as DMS or HMS or a single number as appropriate."""
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
    elif unit == 'radians':
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

class TimeTest(unittest.TestCase):
    def test_parse_hms(self):
        "HMS parse"
        self.assertEqual(parse_hms('0h 0m 0s'), 0*15)
        self.assertEqual(parse_hms('1h 0m 0s'), 1*15)
        self.assertEqual(parse_hms('0h 30m 0s'), 0.5*15)
        self.assertEqual(parse_hms('0h 0m 36s'), 0.01*15)
        self.assertEqual(parse_hms('23h 30m 36s'), 23.51*15)
        self.assertEqual(parse_hms('23h 30\' 36"'), 23.51*15)
        self.assertEqual(parse_hms('23h 30\' 36\'\''), 23.51*15)
        self.assertEqual(parse_hms('+23h 30m 36s'), 23.51*15)
        self.assertEqual(parse_hms(' + 23h  30m 36s'), 23.51*15)
        self.assertEqual(parse_hms('-23h 30m 36s'), -23.51*15)
        self.assertEqual(parse_hms(' - 23h  30m 36s'), -23.51*15)
        self.assertEqual(parse_hms('23H 30M 36S'), 23.51*15)
        with self.assertRaises(ValueError):
            parse_hms('23.1h 30m 36s')
        with self.assertRaises(ValueError):
            parse_hms('23.1h 30m')
        with self.assertRaises(ValueError):
            parse_hms('23h 30.123m 36s')
        with self.assertRaises(ValueError):
            parse_hms('30.123m 36s')
        with self.assertRaises(ValueError):
            parse_hms('23d 30m 36s')
        self.assertEqual(parse_hms('23.h 30.m 36.36s'), 23.5101*15)
        self.assertEqual(parse_hms('23.h   30.m   36.36s'), 23.5101*15)
        self.assertEqual(parse_hms('23.h30.m36.36s'), 23.5101*15)
        self.assertEqual(parse_hms('23.000h 30.000m 36.36000s'), 23.5101*15)
        self.assertEqual(parse_hms('0h 0m'), 0*15)
        self.assertEqual(parse_hms('0h 0.30m'), 0.005*15)
        self.assertEqual(parse_hms('0h 0s'), 0*15)
        self.assertEqual(parse_hms('0h 36.36s'), 0.0101*15)
        self.assertEqual(parse_hms('0m 0s'), 0*15)
        self.assertEqual(parse_hms('10h'), 10*15)
        self.assertEqual(parse_hms('10.123h'), 10.123*15)
        self.assertEqual(parse_hms('0m'), 0*15)
        self.assertEqual(parse_hms('30m'), 0.5*15)
        self.assertEqual(parse_hms('30.30m'), 0.505*15)
        self.assertEqual(parse_hms('36s'), 0.01*15)
        self.assertEqual(parse_hms('36.36s'), 0.0101*15)
        with self.assertRaises(ValueError):
            parse_hms('60m')
        with self.assertRaises(ValueError):
            parse_hms('1234m')
        with self.assertRaises(ValueError):
            parse_hms('60s')
        with self.assertRaises(ValueError):
            parse_hms('1234s')
        self.assertEqual(parse_hms('0 0 0'), 0*15)
        self.assertEqual(parse_hms('1 30 36.36'), 1.5101*15)
        with self.assertRaises(ValueError):
            parse_hms('12 23')
        self.assertEqual(parse_hms('123.456'), 123.456*15)
        self.assertEqual(parse_hms('1000000000h 0m 0s'), 1000000000*15)
        self.assertEqual(parse_hms('1e+9h 0m 0s'), 1000000000*15)
        self.assertEqual(parse_hms('1e+0009h 0m 0s'), 1000000000*15)
        self.assertEqual(parse_hms('123.456', conversion_factor=2),
                         123.456*15)
        self.assertEqual(parse_hms('123.456h', conversion_factor=2),
                         123.456*15/2)

    def test_parse_dms(self):
        "DMS parse"
        self.assertEqual(parse_dms('0d 0m 0s'), 0)
        self.assertEqual(parse_dms('1d 0m 0s'), 1)
        self.assertEqual(parse_dms('0d 30m 0s'), 0.5)
        self.assertEqual(parse_dms('0d 0m 36s'), 0.01)
        self.assertEqual(parse_dms('23d 30m 36s'), 23.51)
        self.assertEqual(parse_dms('23d 30\' 36"'), 23.51)
        self.assertEqual(parse_dms('23d 30\' 36\'\''), 23.51)
        self.assertEqual(parse_dms('+23d 30m 36s'), 23.51)
        self.assertEqual(parse_dms(' + 23d  30m 36s'), 23.51)
        self.assertEqual(parse_dms('-23d 30m 36s'), -23.51)
        self.assertEqual(parse_dms(' - 23d  30m 36s'), -23.51)
        self.assertEqual(parse_dms('23D 30M 36S'), 23.51)
        with self.assertRaises(ValueError):
            parse_dms('23.1d 30m 36s')
        with self.assertRaises(ValueError):
            parse_dms('23.1d 30m')
        with self.assertRaises(ValueError):
            parse_dms('23d 30.123m 36s')
        with self.assertRaises(ValueError):
            parse_dms('30.123m 36s')
        with self.assertRaises(ValueError):
            parse_dms('23h 30m 36s')
        self.assertEqual(parse_dms('23.d 30.m 36.36s'), 23.5101)
        self.assertEqual(parse_dms('23.d   30.m   36.36s'), 23.5101)
        self.assertEqual(parse_dms('23.d30.m36.36s'), 23.5101)
        self.assertEqual(parse_dms('23.000d 30.000m 36.36000s'), 23.5101)
        self.assertEqual(parse_dms('0d 0m'), 0)
        self.assertEqual(parse_dms('0d 0.30m'), 0.005)
        self.assertEqual(parse_dms('0d 0s'), 0)
        self.assertEqual(parse_dms('0d 36.36s'), 0.0101)
        self.assertEqual(parse_dms('0m 0s'), 0)
        self.assertEqual(parse_dms('10d'), 10)
        self.assertEqual(parse_dms('10.123d'), 10.123)
        self.assertEqual(parse_dms('0m'), 0)
        self.assertEqual(parse_dms('30m'), 0.5)
        self.assertEqual(parse_dms('30.30m'), 0.505)
        self.assertEqual(parse_dms('36s'), 0.01)
        self.assertEqual(parse_dms('36.36s'), 0.0101)
        with self.assertRaises(ValueError):
            parse_dms('60m')
        with self.assertRaises(ValueError):
            parse_dms('1234m')
        with self.assertRaises(ValueError):
            parse_dms('60s')
        with self.assertRaises(ValueError):
            parse_dms('1234s')
        self.assertEqual(parse_dms('0 0 0'), 0)
        self.assertEqual(parse_dms('1 30 36.36'), 1.5101)
        with self.assertRaises(ValueError):
            parse_dms('12 23')
        self.assertEqual(parse_dms('123.456'), 123.456)
        self.assertEqual(parse_dms('1000000000d 0m 0s'), 1000000000)
        self.assertEqual(parse_dms('1e+9d 0m 0s'), 1000000000)
        self.assertEqual(parse_dms('1e+0009d 0m 0s'), 1000000000)
        self.assertEqual(parse_dms('1E+0009d 0m 0s'), 1000000000)
        self.assertEqual(parse_dms('123.456', conversion_factor=2), 123.456)
        self.assertEqual(parse_dms('123.456d', conversion_factor=2), 123.456/2)

    def test_parse_dms_hms(self):
        "DMS_HMS parse"
        self.assertEqual(parse_dms_hms('1d 30m 36s'), 1.51)
        self.assertEqual(parse_dms_hms('1h 30m 36s'), 1.51*15)
        self.assertEqual(parse_dms_hms('1 30 36'), 1.51)
        self.assertEqual(parse_dms_hms('1.5'), 1.5)
        self.assertEqual(parse_dms_hms('1.5', conversion_factor=2), 1.5)
        self.assertEqual(parse_dms_hms('1 30 36', conversion_factor=2), 1.51/2)
        self.assertEqual(parse_dms_hms('1.5d', conversion_factor=2), 1.5/2)
        self.assertEqual(parse_dms_hms('1.5h', conversion_factor=2), 1.5*15/2)

    def test_parse_hms_dms(self):
        "DMS_HMS parse"
        self.assertEqual(parse_hms_dms('1d 30m 36s'), 1.51)
        self.assertEqual(parse_hms_dms('1h 30m 36s'), 1.51*15)
        self.assertEqual(parse_hms_dms('1.5'), 1.5*15)
        self.assertEqual(parse_hms_dms('1 30 36'), 1.51*15)
        self.assertEqual(parse_hms_dms('1 30 36', conversion_factor=2),
                                       1.51*15/2)
        self.assertEqual(parse_hms_dms('1.5d', conversion_factor=2), 1.5/2)
        self.assertEqual(parse_hms_dms('1.5h', conversion_factor=2), 1.5*15/2)

    def test_format_dms_hms(self):
        "DMS_HMS format"
        self.assertEqual(format_dms_hms(0, None, 'degrees', '.3f', True),
                         '0.000')
        self.assertEqual(format_dms_hms(0, None, 'degrees', '.3f', False),
                         '0')
        self.assertEqual(format_dms_hms(123.4, None, 'degrees', '.3f',
                                        True), '123.400')
        self.assertEqual(format_dms_hms(123.4, None, 'degrees', '.3f',
                                        False), '123.4')
        self.assertEqual(format_dms_hms(123.456789, None, 'degrees', '.3f',
                                        True), '123.457')
        self.assertEqual(format_dms_hms(123.456789, None, 'degrees', '.3f',
                                        False), '123.457')
        self.assertEqual(format_dms_hms(-123.456789, None, 'degrees', '.3f',
                                        False), '-123.457')
        self.assertEqual(format_dms_hms(1e7, None, 'degrees', '.3f',
                                        False), '10000000')
        self.assertEqual(format_dms_hms(1e8, None, 'degrees', '.3f',
                                        False), '1e+08')
        self.assertEqual(format_dms_hms(1.01e8, None, 'degrees', '.3f',
                                        False), '1.01e+08')

        self.assertEqual(format_dms_hms(0, None, 'hours', '.3f', True),
                         '0.00000')
        self.assertEqual(format_dms_hms(0, None, 'hours', '.3f', False),
                         '0')
        self.assertEqual(format_dms_hms(121.86, None, 'hours', '.3f',
                                        True), '8.12400')
        self.assertEqual(format_dms_hms(121.86, None, 'hours', '.3f',
                                        False), '8.124')
        self.assertEqual(format_dms_hms(123.456789, None, 'hours', '.3f',
                                        True), '8.23045')
        self.assertEqual(format_dms_hms(123.456789, None, 'hours', '.3f',
                                        False), '8.23045')
        self.assertEqual(format_dms_hms(-123.456789, None, 'hours', '.3f',
                                        False), '-8.23045')
        self.assertEqual(format_dms_hms(15e8, None, 'hours', '.3f',
                                        False), '1e+08')
        self.assertEqual(format_dms_hms(15.15e8, None, 'hours', '.3f',
                                        False), '1.01e+08')

        self.assertEqual(format_dms_hms(0, None, 'radians', '.3f', True),
                         '0.00000')
        self.assertEqual(format_dms_hms(0, None, 'radians', '.3f', False),
                         '0')
        self.assertEqual(format_dms_hms(1e7, None, 'radians', '.3f',
                                        False), '10000000')
        self.assertEqual(format_dms_hms(1e8, None, 'radians', '.3f',
                                        False), '1e+08')
        self.assertEqual(format_dms_hms(1.01e8, None, 'radians', '.3f',
                                        False), '1.01e+08')

        self.assertEqual(format_dms_hms(0, None, 'dms', '.6f', False),
                         '0d 00m 00s')
        self.assertEqual(format_dms_hms(0, None, 'dms', '.6f', True),
                         '0d 00m 00.000s')
        self.assertEqual(format_dms_hms(0.0001, None, 'dms', '.6f', False),
                         '0d 00m 00.36s')
        self.assertEqual(format_dms_hms(0.0001, None, 'dms', '.6f', True),
                         '0d 00m 00.360s')
        self.assertEqual(format_dms_hms(-0.0001, None, 'dms', '.6f', False),
                         '-0d 00m 00.36s')
        self.assertEqual(format_dms_hms(-0.0001, None, 'dms', '.6f', True),
                         '-0d 00m 00.360s')
        self.assertEqual(format_dms_hms(700, None, 'dms', '.6f', False),
                         '700d 00m 00s')
        self.assertEqual(format_dms_hms(699.99999987, None, 'dms', '.6f',
                                        False), '700d 00m 00s')
        self.assertEqual(format_dms_hms(699.99999986, None, 'dms', '.6f',
                                        False), '699d 59m 59.999s')
        self.assertEqual(format_dms_hms(-699.99999986, None, 'dms', '.6f',
                                        False), '-699d 59m 59.999s')
        self.assertEqual(format_dms_hms(1e7, None, 'dms', '.3f',
                                        False), '10000000d 00m 00s')
        self.assertEqual(format_dms_hms(1e8, None, 'dms', '.3f',
                                        False), '1e+08d 00m 00s')


        self.assertEqual(format_dms_hms(0, None, 'hms', '.6f', False),
                         '0h 00m 00s')
        self.assertEqual(format_dms_hms(0, None, 'hms', '.6f', True),
                         '0h 00m 00.0000s')
        self.assertEqual(format_dms_hms(0.0001*15, None, 'hms', '.6f', False),
                         '0h 00m 00.36s')
        self.assertEqual(format_dms_hms(0.0001*15, None, 'hms', '.6f', True),
                         '0h 00m 00.3600s')
        self.assertEqual(format_dms_hms(-0.0001*15, None, 'hms', '.6f', False),
                         '-0h 00m 00.36s')
        self.assertEqual(format_dms_hms(-0.0001*15, None, 'hms', '.6f', True),
                         '-0h 00m 00.3600s')
        self.assertEqual(format_dms_hms(700*15, None, 'hms', '.6f', False),
                         '700h 00m 00s')
        self.assertEqual(format_dms_hms(699.99999987*15, None, 'hms', '.5f',
                                        False), '700h 00m 00s')
        self.assertEqual(format_dms_hms(699.99999986*15, None, 'hms', '.5f',
                                        False), '699h 59m 59.999s')
        self.assertEqual(format_dms_hms(-699.99999986*15, None, 'hms', '.5f',
                                        False), '-699h 59m 59.999s')
        self.assertEqual(format_dms_hms(1e7*15, None, 'hms', '.3f',
                                        False), '10000000h 00m 00s')
        self.assertEqual(format_dms_hms(1e8*15, None, 'hms', '.3f',
                                        False), '1e+08h 00m 00s')

################################################################################
################################################################################
# UNITS AND FORMATS
################################################################################

# This dictionary is keyed by "unit_id", which is the name of the group of
# formats/units. Within a given "unit_id" is a set of "details" that include
# 1) The display name for the unit/format in the UI. This might be in a
#    dropdown box on the Search tab or in the Table View header or Detail Tab.
# 2) The numerical conversion factor to apply to the number in the database.
#    If the value in the database is already the correct value, or is just being
#    sent to a formatting function, then the conversion factor is 1.
# 3) The function to call, if any, to parse a string into a value with this
#    format/unit. Often the parse routine is the same for multiple units/formats
#    because we want the input to be free-form.
# 4) The function to call, if any, to format a value with this format/unit as a
#    string.
# In addition:
#    'display_search': True or False, indicating whether the unit/format names
#                      should be displayed on the Search Tab in a dropdown box.
#                      This will generally be False when we're just doing a
#                      format that has no alternative selections, like an SCLK.
#    'display_result': True or False, indicating whether the unit/format names
#                      should be displayed in any results (Table View, Detail
#                      Tab). This will generally be False when it's really
#                      obvious what the displayed format is, like YMDhms.
#    'default': The name of the default unit/format.

UNIT_FORMAT_DB = {
    'range_cassini_sclk': {
        'display_search': False,
        'display_result': False,
        'default': 'range_cassini_sclk',
        'conversions': {
            'range_cassini_sclk': (None, 1,
                                   parse_cassini_sclk, format_cassini_sclk, [])
        }
    },
    'range_galileo_sclk': {
        'display_search': False,
        'display_result': False,
        'default': 'range_galileo_sclk',
        'conversions': {
            'range_galileo_sclk': (None, 1,
                                   parse_galileo_sclk, format_galileo_sclk, [])
        }
    },
    'range_new_horizons_sclk': {
        'display_search': False,
        'display_result': False,
        'default': 'range_new_horizons_sclk',
        'conversions': {
            'range_new_horizons_sclk': (None, 1,
                                        parse_new_horizons_sclk,
                                        format_new_horizons_sclk, [])
        }
    },
    'range_voyager_sclk': {
        'display_search': False,
        'display_result': False,
        'default': 'range_voyager_sclk',
        'conversions': {
            'range_voyager_sclk': (None, 1,
                                   parse_voyager_sclk, format_voyager_sclk, [])
        }
    },
    'range_cassini_rev_no': {
        'display_search': False,
        'display_result': False,
        'default': 'range_cassini_rev_no',
        'conversions': {
            'range_cassini_rev_no': (None, 1,
                                     parse_cassini_orbit, format_cassini_orbit,
                                     [])
        }
    },
    'datetime': {
        'display_search': True,
        'display_result': True,
        'default': 'ymdhms',
        'conversions': {
            'ymdhms':       ('YMDhms',   1, parse_time, format_time_ymd,  []),
            'ydhms':        ('YDhms',    1, parse_time, format_time_ydoy, []),
            'jd':           ('JD',       1, parse_time, format_time_jd,   []),
            'jed':          ('JED',      1, parse_time, format_time_jed,  []),
            'mjd':          ('MJD',      1, parse_time, format_time_mjd,  []),
            'mjed':         ('MJED',     1, parse_time, format_time_mjed, []),
            'et':           ('SPICE ET', 1, parse_time, format_time_et,   [])
        }
    },
    'duration': { # Difference between two datetimes
        'display_search': True,
        'display_result': True,
        'default': 'seconds',
        'conversions': {
            'seconds':      ('secs',    1,           None, None,
                             ['s', 'sec', 'secs', 'second', 'seconds']),
            'microseconds': ('usecs',   0.000001,    None, None,
                             ['us', 'usec', 'usecs', 'microsecond',
                              'microseconds']),
            'milliseconds': ('msecs',   0.001,       None, None,
                             ['ms', 'msec', 'msecs', 'millisecond',
                              'milliseconds']),
            'minutes':      ('minutes', 60.,         None, None,
                             ['min', 'mins', 'minute', 'minutes']),
            'hours':        ('hours',   60.*60.,     None, None,
                             ['h', 'hr', 'hrs', 'hour', 'hours']),
            'days':         ('days',    60.*60.*24., None, None,
                             ['d', 'day', 'days']),
        }
    },
    'generic_angle': { # Generic degrees, like lighting geometry
        'display_search': True,
        'display_result': True,
        'default': 'degrees',
        'conversions': {
            'degrees':      ('degrees',    1.,      None, None,
                             ['d', 'deg', 'degs', 'degree', 'degrees']),
            'radians':      ('radians',    DEG_RAD, None, None,
                             ['r', 'rad', 'rads', 'radians']),
        }
    },
    'latitude': { # Latitude on a body; includes declination
        'display_search': True,
        'display_result': True,
        'default': 'degrees',
        'conversions': {
            'degrees':      ('degrees',    1.,      parse_dms, format_dms_hms,
                             []),
            'dms':          ('DMS',        1.,      parse_dms, format_dms_hms,
                             []),
            'radians':      ('radians',    DEG_RAD, parse_dms, format_dms_hms,
                             []),
        }
    },
    'longitude': { # Longitude on a body or ring
        'display_search': True,
        'display_result': True,
        'default': 'degrees',
        'conversions': {
            'degrees':      ('degrees',    1.,      parse_dms, format_dms_hms,
                             []),
            'dms':          ('DMS',        1.,      parse_dms, format_dms_hms,
                             []),
            'radians':      ('radians',    DEG_RAD, parse_dms, format_dms_hms,
                             []),
        }
    },
    # We do something unusual for hour_angle, since we need people to be
    # able to type in a number in either "dms" or "hms" format at any time and
    # have it do the right thing. As a result, we can't use the *15 unit
    # conversion factor, and we need a special format routine for hours as
    # a floating point number (which divides by 15) rather than using the normal
    # number conversion.
    'hour_angle': { # Hour angle; includes right ascension
        'display_search': True,
        'display_result': True,
        'default': 'degrees',
        'conversions': {
            'degrees':      ('degrees',    1.,  parse_dms_hms, format_dms_hms,
                             []),
            'dms':          ('DMS',        1.,  parse_dms_hms, format_dms_hms,
                             []),
            'hours':        ('hours',      1.,  parse_hms_dms, format_dms_hms,
                             []),
            'hms':          ('HMS',        1.,  parse_hms_dms, format_dms_hms,
                             []),
            'radians':      ('radians',    DEG_RAD,
                                           parse_dms_hms, format_dms_hms,
                             []),
        }
    },
    'distance_ring': {
        'display_search': True,
        'display_result': True,
        'default': 'km',
        'conversions': {
            'km':           ('km',         1,      None, None,
                             ['km', 'kms', 'kilometer', 'kilometers']),
            'm':            ('m',          1e-3,   None, None,
                             ['m', 'ms', 'meter', 'meters']),
            'jupiterradii': ('Rj (71492)', 71492., None, None,
                             ['rj(71492)', 'rj']),
            'saturnradii':  ('Rs (60330)', 60330., None, None,
                             ['rs(60330)', 'rs']),
            'neptuneradii': ('Rn (25225)', 25225., None, None,
                             ['rn(25225)', 'rn']),
            'uranusradii':  ('Ru (25559)', 25559., None, None,
                             ['ru(25559)', 'ru']),
        }
    },
    'distance': {
        'display_search': True,
        'display_result': True,
        'default': 'km',
        'conversions': {
            'km':           ('km',         1,             None, None,
                             ['km', 'kms', 'kilometer', 'kilometers']),
            'm':            ('m',          1e-3,          None, None,
                             ['m', 'ms', 'meter', 'meters']),
            'au':           ('AU',         149597870.700, None, None,
                             ['au'])
        }
    },
    'distance_resolution': {
        'display_search': True,
        'display_result': True,
        'default': 'km_pixel',
        'conversions': {
            'km_pixel':     ('km/pixel', 1,    None, None,
                             ['km/p', 'km/pix', 'km/pixel', 'kmperpix',
                              'kmperpixel',
                              'kms/p', 'kms/pix', 'kms/pixel', 'kmsperpix',
                              'kmsperpixel',
                              'kilometer/p', 'kilometer/pix', 'kilometer/pixel',
                              'kilometerperpix', 'kilometerperpixel',
                              'kilometers/p', 'kilometers/pix',
                              'kilometers/pixel', 'kilometersperpix',
                              'kilometersperpixel']),
            'm_pixel':      ('m/pixel',  1e-3, None, None,
                             ['m/p', 'm/pix', 'm/pixel', 'mperpix',
                              'mperpixel',
                              'ms/p', 'ms/pix', 'ms/pixel', 'msperpix',
                              'msperpixel',
                              'meter/p', 'meter/pix', 'meter/pixel',
                              'meterperpix', 'meterperpixel',
                              'meters/p', 'meters/pix',
                              'meters/pixel', 'metersperpix',
                              'metersperpixel']),
        }
    },
    'wavelength': {
        'display_search': True,
        'display_result': True,
        'default': 'microns',
        'conversions': {
            'microns':      ('microns',   1.,   None, None,
                             ['um', 'umeter', 'umeters',
                              'micron', 'microns',
                              'micrometer', 'micrometers']),
            'angstroms':    ('angstroms', 1e-4, None, None,
                             ['ang', 'angstrom', 'angstroms']),
            'nm':           ('nm',        1e-3, None, None,
                             ['nm', 'nanometer', 'nanometers']),
            'cm':           ('cm',        1e4,  None, None,
                             ['cm', 'centimeter', 'centimeters']),
        }
    },
    'wavelength_resolution': {
        'display_search': True,
        'display_result': True,
        'default': 'microns_pixel',
        'conversions': {
            'microns_pixel':      ('microns/pixel',   1,    None, None,
                                   ['um/p', 'um/pix', 'um/pixel', 'umperpix',
                                    'umperpixel',
                                    'micron/p', 'micron/pix', 'micron/pixel',
                                    'micronperpix', 'micronperpixel',
                                    'microns/p', 'microns/pix', 'microns/pixel',
                                    'micronsperpix', 'micronsperpixel',
                                    'micrometer/p', 'micrometer/pix',
                                    'micrometer/pixel',
                                    'micrometerperpix', 'micrometerperpixel',
                                    'micrometers/p', 'micrometers/pix',
                                    'micrometers/pixel', 'micrometersperpix',
                                    'micrometersperpixel']),
            'angstroms_pixel':    ('angstroms/pixel', 1e-4, None, None,
                                   ['ang/p', 'ang/pix', 'ang/pixel',
                                    'angperpix', 'angperpixel',
                                    'angstrom/p', 'angstrom/pix',
                                    'angstrom/pixel',
                                    'angstromperpix', 'angstromperpixel',
                                    'angstroms/p', 'angstroms/pix',
                                    'angstroms/pixel',
                                    'angstromsperpix', 'angstromsperpixel']),
            'nm_pixel':           ('nm/pixel',        1e-3, None, None,
                                   ['nm/p', 'nm/pix', 'nm/pixel', 'nmperpix',
                                    'nmperpixel',
                                    'nanometer/p', 'nanometer/pix',
                                    'nanometer/pixel',
                                    'nanometerperpix', 'nanometerperpixel',
                                    'nanometers/p', 'nanometers/pix',
                                    'nanometers/pixel', 'nanometersperpix',
                                    'nanometersperpixel']),
            'cm_pixel':           ('cm/pixel',        1e4,  None, None,
                                   ['cm/p', 'cm/pix', 'cm/pixel', 'cmperpix',
                                    'cmperpixel',
                                    'centimeter/p', 'centimeter/pix',
                                    'centimeter/pixel',
                                    'centimeterperpix', 'centimeterperpixel',
                                    'centimeters/p', 'centimeters/pix',
                                    'centimeters/pixel', 'centimetersperpix',
                                    'centimetersperpixel']),
        }
    },
    'wavenumber': {
        'display_search': True,
        'display_result': True,
        'default': '1_cm',
        'conversions': {
            '1_cm':         ('cm^-1', 1.,   None, None,
                             ['1/cm', 'cm^-1', 'cm**-1']),
            '1_m':          ('m^-1',  1e-2, None, None,
                             ['1/m', 'm^-1', 'm**-1']),
        }
    },
    'wavenumber_resolution': {
        'display_search': True,
        'display_result': True,
        'default': '1_cm_pixel',
        'conversions': {
            '1_cm_pixel':  ('cm^-1/pixel', 1.,   None, None,
                            ['1/cm/p', '1/cm/pix', '1/cm/pixel', '1/cmperpix',
                             '1/cmperpixel',
                             '1/centimeter/p', '1/centimeter/pix',
                             '1/centimeter/pixel',
                             '1/centimeterperpix', '1/centimeterperpixel',
                             'cm^-1/p', 'cm^-1/pix', 'cm^-1/pixel',
                             'cm^-1perpix', 'cm^-1perpixel'
                             'cm**-1/p', 'cm**-1/pix', 'cm**-1/pixel',
                             'cm**-1perpix', 'cm**-1perpixel']),
            '1_m_pixel':   ('m^-1/pixel',  1e-2, None, None,
                            ['1/m/p', '1/m/pix', '1/m/pixel', '1/mperpix',
                             '1/mperpixel',
                             '1/meter/p', '1/meter/pix',
                             '1/meter/pixel',
                             '1/meterperpix', '1/meterperpixel',
                             'm^-1/p', 'm^-1/pix', 'm^-1/pixel',
                             'm^-1perpix', 'm^-1perpixel'
                             'm**-1/p', 'm**-1/pix', 'm**-1/pixel',
                             'm**-1perpix', 'm**-1perpixel']),
        }
    },
}

### NUMERICAL CONVERSION
### (These routines *numerically* convert to/from the value stored in the
###  database with no formatting)

def convert_to_default_unit(val, unit_id, unit):
    "Convert a value from a specific unit to the default unit for unit_id."
    if unit_id is None and unit is not None:
        raise KeyError
    if val is None or unit_id is None or unit is None:
        return val
    unit = unit.lower()
    default_unit = UNIT_FORMAT_DB[unit_id]['default']
    if default_unit == unit:
        return val
    ret = val * UNIT_FORMAT_DB[unit_id]['conversions'][unit][1]
    if not math.isfinite(ret):
        raise ValueError
    return ret

def convert_from_default_unit(val, unit_id, unit):
    "Convert a value from the default unit to a specific unit for unit_id."
    if unit_id is None and unit is not None:
        raise KeyError
    if val is None or unit_id is None or unit is None:
        return val
    unit = unit.lower()
    default_unit = UNIT_FORMAT_DB[unit_id]['default']
    if default_unit == unit:
        return val
    ret = val / UNIT_FORMAT_DB[unit_id]['conversions'][unit][1]
    if not math.isfinite(ret):
        raise ValueError
    return ret

### GET INFORMATION ABOUT UNITS

def get_valid_units(unit_id):
    "Get the list of valid units for a unit_id."
    unit_info = UNIT_FORMAT_DB.get(unit_id, None)
    valid_units = None
    if unit_info is not None:
        # This will create a list with the same order as written in the dict
        # initalization above.
        valid_units = list(unit_info['conversions'].keys())
    return valid_units

def get_unit_display_names(unit_id):
    "Get a dictionary with valid units as keys and display names as values."
    unit_info = UNIT_FORMAT_DB.get(unit_id, None)
    display_names = None
    if unit_info is not None:
        display_names = {}
        valid_units = unit_info['conversions']
        for unit in valid_units:
            display_names[unit] = valid_units[unit][0]
    return display_names

def get_unit_display_name(unit_id, unit):
    "Get the display name for a given unit_id and unit."
    unit = unit.lower()
    return UNIT_FORMAT_DB[unit_id]['conversions'][unit][0]

def is_valid_unit_id(unit_id):
    "Check if a unit_id is valid."
    return unit_id in UNIT_FORMAT_DB

def is_valid_unit(unit_id, unit):
    "Check if a unit is a valid unit for unit_id."
    unit = unit.lower()
    return unit in UNIT_FORMAT_DB[unit_id]['conversions']

def get_default_unit(unit_id):
    "Return the default unit for a unit_id."
    if unit_id is None:
        return None
    return UNIT_FORMAT_DB[unit_id]['default']

def display_search_unit(unit_id):
    "Check if a unit name should be displayed for a unit_id on the Search tab."
    if not unit_id:
        return False
    return UNIT_FORMAT_DB[unit_id]['display_search']

def display_result_unit(unit_id):
    "Check if a unit name should be displayed for a unit_id for results."
    if not unit_id:
        return False
    return UNIT_FORMAT_DB[unit_id]['display_result']

def display_unit_ever(unit_id):
    "Check if a unit name should ever be displayed for a unit_id."
    return display_search_unit(unit_id) or display_result_unit(unit_id)

def get_disp_default_and_avail_units(param_form_type):
    "Return display, default, and available units for a given param form type."
    (form_type, form_type_format,
     form_type_unit_id) = parse_form_type(param_form_type)

    is_displayed = display_result_unit(form_type_unit_id)
    if not is_displayed:
        return None, None, None

    available_units = get_unit_display_names(form_type_unit_id)
    default_unit = get_default_unit(form_type_unit_id)
    if default_unit is not None:
        disp_unit = get_unit_display_name(form_type_unit_id, default_unit)
    else:
        disp_unit = None
    return disp_unit, default_unit, available_units

### FORMAT A VALUE FOR A GIVEN UNIT

def adjust_format_string_for_units(numerical_format, unit_id, unit):
    "Adjust a format string size for a change of units."
    if unit_id is None:
        return numerical_format
    if (not numerical_format.startswith('.') or
        not numerical_format.endswith('f')):
        return numerical_format
    unit = unit.lower()
    default_unit = UNIT_FORMAT_DB[unit_id]['default']
    if default_unit == unit:
        return numerical_format
    assert unit_id in UNIT_FORMAT_DB
    # The behavior of ceil is to increase the number of positive numbers
    # (which is adding decimal places), which is good. And it's to decrease
    # the absolute value of negative numbers (which is removing decimal places),
    # which is also good. In both cases we're being conservative - adding too
    # many or removing too few.
    factor = int(np.ceil(np.log10(
                 UNIT_FORMAT_DB[unit_id]['conversions'][unit][1])))
    dec = max(int(numerical_format[1:-1]) + factor, 0)
    return '.' + str(dec) + 'f'

def format_unit_value(val, numerical_format, unit_id, unit,
                      keep_trailing_zeros=False, convert_from_default=True):
    """Format a value based on the unit_id and specific unit.

    val                     The value to be formatted.
    numerical_format        A string like ".5f" that specifies the numerical format to be
                            used if this unit system does not include a formatting
                            function. The number of decimal places will be adjusted, as
                            appropriate, based on the units requested.
    unit_id                 The id of the unit system.
    unit                    The requested output unit. None means use the default unit.
    keep_trailing_zeros     If True, keep the zeros at the end of a decimal floating point
                            number (e.g. 2.1000).
    convert_from_default    If True, convert the value from the default unit to the
                            requested unit.
    """
    if val is None or isinstance(val, str):
        return val
    format_func = None
    if unit_id is not None:
        if unit is None:
            unit = get_default_unit(unit_id)
        unit = unit.lower()
        if convert_from_default:
            val = convert_from_default_unit(val, unit_id, unit)
        format_func = UNIT_FORMAT_DB[unit_id]['conversions'][unit][3]
    if format_func is None:
        if numerical_format is None:
            return str(val)
        if abs(val) >= 1e8:
            numerical_format = numerical_format.replace('f', 'e')
        new_format = adjust_format_string_for_units(numerical_format,
                                                    unit_id, unit)
        ret = ('{:'+new_format+'}').format(val)
        if not keep_trailing_zeros:
            ret = _strip_trailing_zeros(ret)
        return ret
    return format_func(val, unit_id=unit_id, unit=unit,
                       numerical_format=numerical_format,
                       keep_trailing_zeros=keep_trailing_zeros)

def _strip_trailing_zeros(s):
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
    def clean_func(x):
        ret = x.lower().replace(',', '').replace('_','')
        if compress_spaces:
            ret = ret.replace(' ', '')
        return ret
    if isinstance(s, (list, tuple)):
        return [clean_func(z) for z in s]

    return clean_func(s)

def parse_unit_value(s, numerical_format, unit_id, unit):
    """Parse a string given the unit and numerical format."""
    if s is None or s == '':
        return None
    parse_func = None
    if unit_id is not None:
        if unit is None:
            unit = get_default_unit(unit_id)
        unit = unit.lower()
        (display_name, conversion_factor, parse_func,
         display_func, _) = UNIT_FORMAT_DB[unit_id]['conversions'][unit]
    if parse_func is None:
        # Direct numeric conversion with no special parsing
        # Choose between float or int parsing
        parse_func = float
        if numerical_format and numerical_format[-1] == 'd':
            parse_func = int

        # Clean the string, including converting to lower case and eliminating
        # spaces
        s = _clean_numeric_field(s)
        force_unit = None
        if unit_id:
            # Look for an overriding unit name suffix, like "1 km"
            conversions = UNIT_FORMAT_DB[unit_id]['conversions']
            # Build a list of all possible suffixes. Sort the possible suffixes
            # by descending length so that we find, for example, "km" before "m"
            sorted_suffixes = []
            for trial_unit, trial_conversion in conversions.items():
                trial_suffix_list = trial_conversion[4]
                for suffix in trial_suffix_list:
                    sorted_suffixes.append((suffix, trial_unit, trial_conversion))
            sorted_suffixes.sort(key=lambda x: -len(x[0]))
            for trial_suffix, trial_unit, trial_conversion in sorted_suffixes:
                if s.endswith(trial_suffix):
                    force_unit = trial_unit
                    # Strip off the unit name from the number
                    s = s[:-len(trial_suffix)]
                    break
        ret = parse_func(s) # Parse the int or float
        if not math.isfinite(ret):
            raise ValueError
        if force_unit is not None:
            ret = convert_to_default_unit(ret, unit_id, force_unit)
            ret = convert_from_default_unit(ret, unit_id, unit)
        return ret

    # We only adjust for the conversion factor for non-standard parsers, because
    # those are ones that might specify an explicit unit (like "1d" for radians)
    # but we wouldn't have caught it as part of the generic numeric processing
    # above
    return parse_func(s, conversion_factor=conversion_factor,
                      numerical_format=numerical_format,
                      unit_id=unit_id, unit=unit)

def parse_form_type(s):
    """Parse the ParamInfo FORM_TYPE with its subfields.

    Subfields are:
        TYPE[%format][:unit]
    """
    if s is None:
        return None, None, None

    form_type = s
    form_type_format = None
    form_type_unit = None

    if form_type.find(':') != -1:
        form_type, form_type_unit = form_type.split(':')
    if form_type.find('%') != -1:
        form_type, form_type_format = form_type.split('%')

    return form_type, form_type_format, form_type_unit

def get_single_parse_function(unit_id):
    """Return the parse func for a unit_id with a single non-displayed unit."""
    parse_func = None
    if unit_id and not display_unit_ever(unit_id):
        default_unit = get_default_unit(unit_id)
        parse_func = (UNIT_FORMAT_DB[unit_id]
                                    ['conversions']
                                    [default_unit]
                                    [2])
    return parse_func

def get_single_format_function(unit_id):
    """Return the format func for a unit_id with a single non-displayed unit."""
    format_func = None
    if unit_id and not display_unit_ever(unit_id):
        default_unit = get_default_unit(unit_id)
        format_func = (UNIT_FORMAT_DB[unit_id]
                                    ['conversions']
                                    [default_unit]
                                    [3])
    return format_func


if __name__ == '__main__':
    unittest.main()
