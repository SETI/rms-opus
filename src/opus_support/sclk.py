"""Spacecraft clock (SCLK) conversions.

Parses and formats the Galileo, New Horizons, Cassini and Voyager spacecraft
clocks. Every parser converts a clock string to a number and every formatter
converts that number back to the mission's canonical clock string, so the pair
round-trips within the resolution of the clock's smallest field.
"""

################################################################################
# General routines for handling a spacecraft clock where:
#   - there are two or more fields
#   - the clock partition is always one
################################################################################

def _parse_multi_field_sclk(sclk, ndigits, sep, modvals, scname):
    """Convert a multi-field clock string to a numeric value.

    Input:
        sclk        the spacecraft clock string.
        ndigits     the maximum number of digits in the leading field.
        sep         the character that separates the fields, typically a colon
                    or a period.
        modvals     For a 2-field sclk, the modulus value of the second field.
                    For a general sclk, a list containing the modulus value of
                    each field from 2 onward.
        scname      name of the spacecraft, used for error messages.
    """
    if not isinstance(modvals, (list, tuple)):
        modvals = [modvals]

    # Check the partition number before ignoring it
    parts = sclk.split('/')
    if len(parts) > 2:
        raise ValueError(f'Invalid {scname} clock format, extraneous slash: {sclk}')

    if len(parts) == 2:
        if parts[0].strip() != '1':
            raise ValueError(f'{scname} partition number must be one: {sclk}')

        sclk = parts[1]

    # Interpret the fields
    nfields = len(modvals)+1  # this is how many fields we want
    parts = sclk.split(sep)

    if len(parts) > nfields:
        raise ValueError(f'More than {nfields} {scname} clock fields: {sclk}')

    # Append fields to make the proper number
    while len(parts) < nfields:
        parts.append('')

    # Append zeroes to make each field the proper length. A field the caller left
    # empty -- a trailing separator, or one of the fields appended just above --
    # therefore becomes all zeroes.
    for idx in range(1, len(parts)):
        modval_len = len(str(modvals[idx-1]-1))
        if len(parts[idx]) > modval_len:
            raise ValueError(f'{scname} clock field {idx+1} "{parts[idx]}" has too many '
                             f'digits: {sclk}')
        parts[idx] = parts[idx] + '0' * (modval_len - len(parts[idx]))

    # Make sure all fields are integers
    ints = []
    for part in parts:
        try:
            ints.append(int(part))
        except ValueError as err:
            raise ValueError(f'{scname} clock fields must be integers: {sclk}') from err

    # Check fields for valid ranges and add them up
    if ints[0] < 0 or len(parts[0]) > ndigits:
        raise ValueError(f'{scname} clock leading field has too many digits: {sclk}')

    result = 0
    for idx in range(nfields-1, 0, -1):
        modval = modvals[idx-1]
        if not 0 <= ints[idx] < modval:
            raise ValueError(f'{scname} clock field {idx+1} out of range '
                            f'0-{modval-1:d}: {sclk}')
        result = (result + ints[idx]) / float(modval)

    return result + ints[0]

def _format_multi_field_sclk(value, ndigits, sep, modvals, scname):
    """Convert a number into a valid spacecraft clock string.

    Input:
        sclk        the spacecraft clock string.
        ndigits     the number of digits in the leading field. Leading zeros
                    will be used for padding
        sep         the character that separates the fields, typically a colon
                    or a period.
        modvals     For a 2-field sclk, the modulus value of the second field.
                    For a general sclk, a list containing the modulus value of
                    each field from 2 onward.
        scname      name of the spacecraft, used for error messages.
    """
    if not isinstance(modvals, (list, tuple)):
        modvals = [modvals]

    # Extract fields
    ret_vals = [int(value)]
    value -= ret_vals[0]

    fmts = [f'%0{ndigits}d']

    for idx, modval in enumerate(modvals):
        fmts.append(f'%0{len(str(modval-1))}d')
        value *= modval
        if idx != len(modvals)-1:
            # Don't round up intermediate fields
            field_val = int(value)
        else:
            # Round up the final field
            field_val = int(value + 0.5)
        ret_vals.append(field_val)
        value -= field_val

    # If rounding up the final field made it too large, then propagate a carry
    # to earlier fields
    for idx in range(len(ret_vals)-1, 0, -1):
        modval = modvals[idx-1]
        if ret_vals[idx] < modval:
            break
        ret_vals[idx] -= modval
        ret_vals[idx-1] += 1

    fmt = sep.join(fmts)
    return fmt % tuple(ret_vals)


################################################################################
################################################################################
# GALILEO
################################################################################
# Conversion routines for the Galileo spacecraft clock.
#
# There are conflicting formats. The PDS3 labels have the format
#   xxxxxxxx.mm
# while the SPICE kernel supports
#   xxxxxxxx:mm:n:o
# The first field has eight digits with leading zeros if necessary.
# The second is a two-digit number 00-90.
# The third is a one-digit number 0-9.
# The fourth is a one-digit number 0-7.
# The partition is always 1.
#
# We use the second option for formatting Galileo clocks for display.
# We support both formats for parsing by converting any "." into ":" before
# parsing, and allowing any missing fields to be set to zero.
################################################################################

def parse_galileo_sclk(sclk, **kwargs):
    """Convert a Galileo clock string to a numeric value."""
    sclk = sclk.replace('.', ':')
    return _parse_multi_field_sclk(sclk, 8, ':', (91, 10, 8), 'Galileo')

def format_galileo_sclk(value, **kwargs):
    """Convert a number into a valid Galileo clock string."""
    return _format_multi_field_sclk(value, 8, ':', (91, 10, 8), 'Galileo')


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
            raise ValueError(f'New Horizons partition number must be 1 or 3: {sclk}')
        sclk = parts[2]

    # Convert to numeric value
    value = _parse_multi_field_sclk(sclk, 10, ':', 50000, 'New Horizons')

    # Validate the partition number if any
    if parts[1] and ((parts[0] == '3' and value < 150000000.) or
        (parts[0] == '1' and value > 150000000.)):
        raise ValueError('New Horizons partition number is invalid: '
                            f'{original_sclk}')

    return value

def format_new_horizons_sclk(value, **kwargs):
    """Convert a number into a valid New Horizons clock string."""
    return _format_multi_field_sclk(value, 10, ':', 50000, 'New Horizons')


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
    return _parse_multi_field_sclk(sclk, 10, '.', 256, 'Cassini')

def format_cassini_sclk(value, **kwargs):
    """Convert a number into a valid Cassini clock string."""
    return _format_multi_field_sclk(value, 10, '.', 256, 'Cassini')


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
    assert planet in (None, 5, 6, 7, 8), f'Invalid planet value: {planet}'

    # Check the partition number before ignoring it
    parts = sclk.split('/')
    if len(parts) > 2:
        raise ValueError(f'Invalid FDS format, extraneous "/": {sclk}')

    if len(parts) == 2:
        try:
            partition = int(parts[0])
        except ValueError as err:
            raise ValueError(f'Partition number is not an integer: {sclk}') from err

        if planet is None:
            if partition not in VOYAGER_PLANET_PARTITIONS.values():
                raise ValueError(f'Partition number out of range 2-4: {sclk}')
        else:
            required_partition = VOYAGER_PLANET_PARTITIONS[planet]
            if partition != required_partition:
                name = VOYAGER_PLANET_NAMES[planet]
                raise ValueError(f'Partition number for {name} flyby '
                                 f'must be {required_partition:d}: {sclk}')

        sclk = parts[1]

    # Separator can be '.' or ':'
    if '.' in sclk:
        parts = sclk.split('.')
    elif ':' in sclk:
        parts = sclk.split(':')
    else:
        parts = [sclk]

    if len(parts) > 3:
        raise ValueError(f'More than three fields in Voyager clock: {sclk}')


    # Append zeroes to make each field the proper length
    if len(parts) > 1 and len(parts[1]) < 2:
        parts[1] = parts[1] + '0' * (2 - len(parts[1]))
    if len(parts) > 2 and len(parts[2]) < 3:
        parts[2] = parts[2] + '0' * (3 - len(parts[2]))

    # Make sure field are integers
    ints = []
    try:
        for part in parts:
            ints.append(int(part))
    except ValueError as err:
        raise ValueError(f'Voyager clock fields must be integers: {sclk}') from err

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
        raise ValueError(f'Voyager clock "hours" out of range 0-65535: {sclk}')
    if ints[1] > 59 or ints[1] < 0:
        raise ValueError(f'Voyager clock "minutes" out of range 0-59: {sclk}')
    if ints[2] > 800 or ints[2] < 1:
        raise ValueError(f'Voyager clock "seconds" out of range 1-800: {sclk}')

    # Return in units of FDS hours
    return ints[0] + (ints[1] + (ints[2]-1) / 800.) / 60.

def format_voyager_sclk(value, sep=':', fields=3, **kwargs):
    """Convert a number in units of FDS hours to valid Voyager clock string."""
    assert sep in (':', '.'), f'Separator must be ":" or ".": {sep}'
    assert fields in (2,3), f'Fields must be 2 or 3: {fields}'

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
        raise ValueError(f'Voyager clock "hours" cannot exceed 65535: {saved_value}')

    # Format
    if fields == 3:
        sclk = f'{hours:05d}{sep}{minutes:02d}{sep}{seconds:03d}'
    else:
        sclk = f'{hours:05d}{sep}{minutes:02d}'

    return sclk
