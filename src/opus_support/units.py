"""The unit/format database and the conversions driven by it.

``UNIT_FORMAT_DB`` maps each ``unit_id`` (a group of interchangeable units or
formats, e.g. ``distance`` or ``datetime``) to its units, their conversion
factors relative to the group's default unit, and the parse/format functions
that unit needs. Everything else in this module is a lookup, a numeric
conversion, or a format/parse operation driven by that table.
"""

import math
from collections.abc import Callable
from typing import TypedDict

import numpy as np

from opus_support._numeric_text import _clean_numeric_field, _strip_trailing_zeros
from opus_support.angles import (
    format_dms_hms,
    parse_dms,
    parse_dms_hms,
    parse_hms_dms,
)
from opus_support.orbits import format_cassini_orbit, parse_cassini_orbit
from opus_support.sclk import (
    format_cassini_sclk,
    format_galileo_sclk,
    format_new_horizons_sclk,
    format_voyager_sclk,
    parse_cassini_sclk,
    parse_galileo_sclk,
    parse_new_horizons_sclk,
    parse_voyager_sclk,
)
from opus_support.time_parsing import (
    format_time_et,
    format_time_jd,
    format_time_jed,
    format_time_mjd,
    format_time_mjed,
    format_time_ydoy,
    format_time_ymd,
    parse_time,
)

DEG_RAD = np.degrees(1)

#: A function that converts text the user typed into a number. Every parser in this
#: package accepts the text positionally and ignores whichever of the keyword
#: arguments ``conversion_factor``, ``numerical_format``, ``unit_id`` and ``unit`` it
#: has no use for, so that one dispatch can drive them all.
ParseFunc = Callable[..., float]

#: A function that converts a number into text for display. Every formatter in this
#: package accepts the number positionally and ignores whichever of the keyword
#: arguments ``unit_id``, ``unit``, ``numerical_format`` and ``keep_trailing_zeros``
#: it has no use for.
FormatFunc = Callable[..., str]

#: One unit of a unit_id -- its display name (None for a unit that is never shown), the
#: factor that converts a value in this unit to the unit_id's default unit, the
#: function that parses text in this unit (None to read it as a plain number), the
#: function that formats a value in this unit (None to format it as a plain number),
#: and the suffixes a user may type to name this unit explicitly.
UnitConversion = tuple[str | None, float, ParseFunc | None, FormatFunc | None,
                       list[str]]


class UnitInfo(TypedDict):
    """Everything `UNIT_FORMAT_DB` records about one unit_id.

    Attributes:
        display_search: True if the unit names belong in a dropdown on the Search
            tab. False for a unit_id with a single unit the user cannot change.
        display_result: True if the unit name belongs beside a value in the Table
            View or the Detail tab.
        default: The unit values are stored in, and the one used when the caller
            names none.
        conversions: The unit_id's units, keyed by unit name, in the order they are
            offered to the user.
    """

    display_search: bool
    display_result: bool
    default: str
    conversions: dict[str, UnitConversion]

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

UNIT_FORMAT_DB: dict[str, UnitInfo] = {
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
    'angle_resolution': {
        'display_search': True,
        'display_result': True,
        'default': 'degrees_pixel',
        'conversions': {
            'degrees_pixel': ('degrees/pixel',    1.,      None, None,
                              ['d/p', 'd/pix', 'd/pixel', 'dperpix',
                               'dperpixel',
                               'deg/p', 'deg/pix', 'deg/pixel', 'degperpix',
                               'degperpixel',
                               'degs/p', 'degs/pix', 'degs/pixel',
                               'degsperpix', 'degsperpixel',
                               'degree/p', 'degree/pix', 'degree/pixel',
                               'degreeperpix', 'degreeperpixel',
                               'degrees/p', 'degrees/pix', 'degrees/pixel',
                               'degreesperpix', 'degreesperpixel']),
            'radians_pixel': ('radians/pixel',    DEG_RAD, None, None,
                              ['r/p', 'r/pix', 'r/pixel', 'rperpix',
                               'rperpixel',
                               'rad/p', 'rad/pix', 'rad/pixel', 'radperpix',
                               'radperpixel',
                               'rads/p', 'rads/pix', 'rads/pixel',
                               'radsperpix', 'radsperpixel',
                               'radians/p', 'radians/pix', 'radians/pixel',
                               'radiansperpix', 'radiansperpixel']),
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
                             'cm^-1perpix', 'cm^-1perpixel',
                             'cm**-1/p', 'cm**-1/pix', 'cm**-1/pixel',
                             'cm**-1perpix', 'cm**-1perpixel']),
            '1_m_pixel':   ('m^-1/pixel',  1e-2, None, None,
                            ['1/m/p', '1/m/pix', '1/m/pixel', '1/mperpix',
                             '1/mperpixel',
                             '1/meter/p', '1/meter/pix',
                             '1/meter/pixel',
                             '1/meterperpix', '1/meterperpixel',
                             'm^-1/p', 'm^-1/pix', 'm^-1/pixel',
                             'm^-1perpix', 'm^-1perpixel',
                             'm**-1/p', 'm**-1/pix', 'm**-1/pixel',
                             'm**-1perpix', 'm**-1perpixel']),
        }
    },
}

### NUMERICAL CONVERSION
### (These routines *numerically* convert to/from the value stored in the
###  database with no formatting)

# In all of the following functions, unit_id must be in the proper case. This is
# a safe assumption because the unit_id comes from the ParamInfo structure.
# On the other hand, unit can be in any case, since it's potentially supplied
# by the user, and we force it to lower case.

def convert_to_default_unit(val: float | None, unit_id: str | None,
                            unit: str | None) -> float | None:
    """Convert a value from a specific unit to the default unit for unit_id.

    Parameters:
        val: The value in `unit`, or None.
        unit_id: The id of the unit system, or None for a value that carries no
            units. `unit` must then be None as well.
        unit: The unit `val` is in, in any case. It is required whenever `unit_id`
            is given and `val` is not None; the other combinations return before the
            unit is read.

    Returns:
        The value in the default unit of `unit_id`, or `val` unchanged when it is
        None, when it is already in the default unit, or when it carries no units.

    Raises:
        KeyError: If `unit` is named without a `unit_id`, if `unit_id` names no unit
            system, or if `unit` names no unit of that system.
        ValueError: If the converted value overflows to infinity.
    """
    if unit_id is None and unit is not None:
        raise KeyError
    if val is None or (unit_id is None and unit is None):
        return val
    # Past both guards a unit_id is always present, and every caller that supplies
    # one supplies the unit that goes with it.
    assert unit_id is not None
    assert unit is not None
    unit = unit.lower()
    default_unit = UNIT_FORMAT_DB[unit_id]['default']
    if default_unit == unit:
        return val
    ret = val * UNIT_FORMAT_DB[unit_id]['conversions'][unit][1]
    if not math.isfinite(ret):
        raise ValueError
    return ret

def convert_from_default_unit(val: float | None, unit_id: str | None,
                              unit: str | None) -> float | None:
    """Convert a value from the default unit to a specific unit for unit_id.

    Parameters:
        val: The value in the default unit of `unit_id`, or None.
        unit_id: The id of the unit system, or None for a value that carries no
            units. `unit` must then be None as well.
        unit: The unit to convert to, in any case. It is required whenever `unit_id`
            is given and `val` is not None; the other combinations return before the
            unit is read.

    Returns:
        The value in `unit`, or `val` unchanged when it is None, when `unit` is
        already the default unit, or when it carries no units.

    Raises:
        KeyError: If `unit` is named without a `unit_id`, if `unit_id` names no unit
            system, or if `unit` names no unit of that system.
        ValueError: If the converted value overflows to infinity.
    """
    if unit_id is None and unit is not None:
        raise KeyError
    if val is None or (unit_id is None and unit is None):
        return val
    # Past both guards a unit_id is always present, and every caller that supplies
    # one supplies the unit that goes with it.
    assert unit_id is not None
    assert unit is not None
    unit = unit.lower()
    default_unit = UNIT_FORMAT_DB[unit_id]['default']
    if default_unit == unit:
        return val
    ret = val / UNIT_FORMAT_DB[unit_id]['conversions'][unit][1]
    if not math.isfinite(ret):
        raise ValueError
    return ret

### GET INFORMATION ABOUT UNITS

def get_valid_units(unit_id: str | None) -> list[str] | None:
    """Get the list of valid units for a unit_id.

    Parameters:
        unit_id: The id of the unit system, or None.

    Returns:
        The unit names, in the order they are offered to the user, or None if
        `unit_id` is None or names no unit system.
    """
    unit_info = None if unit_id is None else UNIT_FORMAT_DB.get(unit_id)
    valid_units = None
    if unit_info is not None:
        # This will create a list with the same order as written in the dict
        # initialization above.
        valid_units = list(unit_info['conversions'].keys())
    return valid_units

def get_unit_display_names(unit_id: str | None) -> dict[str, str | None] | None:
    """Get a dictionary with valid units as keys and display names as values.

    Parameters:
        unit_id: The id of the unit system, or None.

    Returns:
        Each unit name mapped to the name shown for it in the user interface, which
        is None for a unit that is never shown. Returns None if `unit_id` is None or
        names no unit system.
    """
    unit_info = None if unit_id is None else UNIT_FORMAT_DB.get(unit_id)
    display_names: dict[str, str | None] | None = None
    if unit_info is not None:
        display_names = {}
        valid_units = unit_info['conversions']
        for unit in valid_units:
            display_names[unit] = valid_units[unit][0]
    return display_names

def get_unit_display_name(unit_id: str, unit: str) -> str | None:
    """Get the display name for a given valid unit_id and unit.

    Parameters:
        unit_id: The id of the unit system.
        unit: The unit, in any case.

    Returns:
        The name shown for that unit in the user interface, which is None for a unit
        that is never shown.

    Raises:
        KeyError: If `unit_id` names no unit system, or `unit` names no unit of it.
    """
    unit = unit.lower()
    return UNIT_FORMAT_DB[unit_id]['conversions'][unit][0]

def is_valid_unit_id(unit_id: str | None) -> bool:
    """Check if a unit_id is valid.

    Parameters:
        unit_id: The id to check, or None.

    Returns:
        True if `unit_id` names a unit system.
    """
    return unit_id in UNIT_FORMAT_DB

def is_valid_unit(unit_id: str, unit: str) -> bool:
    """Check if a unit is a valid unit for a valid unit_id.

    Parameters:
        unit_id: The id of the unit system.
        unit: The unit to check, in any case.

    Returns:
        True if `unit` names a unit of `unit_id`.

    Raises:
        KeyError: If `unit_id` names no unit system.
    """
    unit = unit.lower()
    return unit in UNIT_FORMAT_DB[unit_id]['conversions']

def get_default_unit(unit_id: str | None) -> str | None:
    """Return the default unit for a unit_id.

    Parameters:
        unit_id: The id of the unit system, or None.

    Returns:
        The unit values of this unit_id are stored in, or None if `unit_id` is None.

    Raises:
        KeyError: If `unit_id` names no unit system.
    """
    if unit_id is None:
        return None
    return UNIT_FORMAT_DB[unit_id]['default']

def display_search_unit(unit_id: str | None) -> bool:
    """Check if a unit name should be displayed for a unit_id on the Search tab.

    Parameters:
        unit_id: The id of the unit system, or None.

    Returns:
        True if the Search tab should offer a dropdown of this unit_id's units.
        False if `unit_id` is None or empty.

    Raises:
        KeyError: If `unit_id` names no unit system.
    """
    if not unit_id:
        return False
    return UNIT_FORMAT_DB[unit_id]['display_search']

def display_result_unit(unit_id: str | None) -> bool:
    """Check if a unit name should be displayed for a unit_id for results.

    Parameters:
        unit_id: The id of the unit system, or None.

    Returns:
        True if the Table View and Detail tab should name the unit beside a value of
        this unit_id. False if `unit_id` is None or empty.

    Raises:
        KeyError: If `unit_id` names no unit system.
    """
    if not unit_id:
        return False
    return UNIT_FORMAT_DB[unit_id]['display_result']

def display_unit_ever(unit_id: str | None) -> bool:
    """Check if a unit name should ever be displayed for a unit_id.

    Parameters:
        unit_id: The id of the unit system, or None.

    Returns:
        True if the unit is named either on the Search tab or beside a result. False
        if `unit_id` is None or empty.

    Raises:
        KeyError: If `unit_id` names no unit system.
    """
    return display_search_unit(unit_id) or display_result_unit(unit_id)

def get_disp_default_and_avail_units(
        param_form_type: str | None
) -> tuple[str | None, str | None, dict[str, str | None] | None]:
    """Return display, default, and available units for a given ParamInfo form type.

    Parameters:
        param_form_type: A ParamInfo form type, ``TYPE[%format][:unit]``, or None.

    Returns:
        A triple of the display name of the default unit, the name of the default
        unit, and every unit name mapped to its display name. All three are None
        when the form type names no unit system, or names one whose unit is never
        shown beside a result.

    Raises:
        KeyError: If the form type names a unit system that does not exist.
    """
    (_form_type, _form_type_format,
     form_type_unit_id) = parse_form_type(param_form_type)

    is_displayed = display_result_unit(form_type_unit_id)
    if not is_displayed:
        return None, None, None

    # display_result_unit is only true for a unit_id that exists, and every unit_id
    # that exists has a default unit.
    assert form_type_unit_id is not None
    available_units = get_unit_display_names(form_type_unit_id)
    default_unit = get_default_unit(form_type_unit_id)
    assert default_unit is not None
    disp_unit = get_unit_display_name(form_type_unit_id, default_unit)
    return disp_unit, default_unit, available_units

### FORMAT A VALUE FOR A GIVEN UNIT

def adjust_format_string_for_units(numerical_format: str, unit_id: str | None,
                                   unit: str | None) -> str:
    """Adjust a format string size for a change of units.

    This takes a format string of the form ".<n>f" and adjusts the value
    of <n> based on the ratio of the given unit to the default unit.
    If the format string is anything else, it is left unchanged.

    Parameters:
        numerical_format: The format, ".<n>f" to be adjusted or anything else to be
            returned as it is.
        unit_id: The id of the unit system, or None to return the format unchanged.
        unit: The unit the value will be written in, in any case. It is required
            whenever `unit_id` is given and `numerical_format` both starts with "."
            and ends with "f"; the other combinations return before the unit is read.

    Returns:
        A format ".<n>f" whose number of decimal places is adjusted by the power of
        ten separating `unit` from the default unit, never below zero. A format of
        any other shape is returned unchanged.

    Raises:
        KeyError: If `unit_id` names no unit system, or `unit` names no unit of it.
    """
    if unit_id is None:
        return numerical_format
    if (not numerical_format.startswith('.') or
        not numerical_format.endswith('f')):
        return numerical_format
    # A unit_id always arrives with the unit that goes with it.
    assert unit is not None
    unit = unit.lower()
    default_unit = UNIT_FORMAT_DB[unit_id]['default']
    if default_unit == unit:
        return numerical_format
    # The behavior of ceil is to increase the number of positive numbers
    # (which is adding decimal places), which is good. And it's to decrease
    # the absolute value of negative numbers (which is removing decimal places),
    # which is also good. In both cases we're being conservative - adding too
    # many or removing too few.
    factor = int(np.ceil(np.log10(
                 UNIT_FORMAT_DB[unit_id]['conversions'][unit][1])))
    dec = max(int(numerical_format[1:-1]) + factor, 0)
    return '.' + str(dec) + 'f'

def format_unit_value(val: float | str | None, numerical_format: str | None,
                      unit_id: str | None, unit: str | None,
                      keep_trailing_zeros: bool = False,
                      convert_from_default: bool = True) -> str | None:
    """Format a value based on the unit_id and specific unit.

    Parameters:
        val: The value to be formatted. None and a value that is already text are
            returned unchanged.
        numerical_format: A string like ".5f" that specifies the numerical format to
            be used if this unit system does not include a formatting function. The
            number of decimal places will be adjusted, as appropriate, based on the
            units requested. None formats the value with ``str``.
        unit_id: The id of the unit system, or None for a value that carries no
            units.
        unit: The requested output unit. None means use the default unit.
        keep_trailing_zeros: If True, keep the zeros at the end of a decimal floating
            point number (e.g. 2.1000).
        convert_from_default: If True, convert the value from the default unit to the
            requested unit.

    Returns:
        The formatted value, or `val` itself when it is None or already text. A
        number is written by the unit's own formatter if it has one, and otherwise
        with `numerical_format`, switching to exponential notation at 1e8.

    Raises:
        KeyError: If `unit_id` names no unit system, or `unit` names no unit of it.
        ValueError: If converting the value out of the default unit overflows to
            infinity.
    """
    if val is None or isinstance(val, str):
        return val
    format_func = None
    if unit_id is not None:
        if unit is None:
            unit = get_default_unit(unit_id)
        # get_default_unit returns a unit for every unit_id that exists, and raises
        # for one that does not.
        assert unit is not None
        unit = unit.lower()
        if convert_from_default:
            converted = convert_from_default_unit(val, unit_id, unit)
            # A value that was not None cannot come back as None.
            assert converted is not None
            val = converted
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

def parse_unit_value(s: str | None, numerical_format: str | None,
                     unit_id: str | None, unit: str | None) -> float | None:
    """Parse a string given the unit and numerical format.

    We assume that the value returned should be in the given unit, so
    normally there is no conversion done. However, if the user explicitly
    specifies a unit, like "1 km", then we convert from that unit to the
    passed-in unit.

    Parameters:
        s: The text the user typed. None and the empty string parse to None.
        numerical_format: The format the value is stored with, used only to choose
            between whole-number and floating-point parsing when the unit has no
            parser of its own: a format ending in ``d`` reads the text as a whole
            number.
        unit_id: The id of the unit system, or None for a value that carries no
            units.
        unit: The unit the text is in. None means the default unit.

    Returns:
        The parsed value in `unit`, or None for empty text. The value is a whole
        number when `numerical_format` asked for one and the unit has no parser of
        its own.

    Raises:
        KeyError: If `unit_id` names no unit system, or `unit` names no unit of it.
        ValueError: If the text names no value of this unit, or the value is
            infinite, or converting a value the user labelled with another unit
            overflows to infinity.
    """
    if s is None or s == '':
        return None
    parse_func = None
    if unit_id is not None:
        if unit is None:
            unit = get_default_unit(unit_id)
        # get_default_unit returns a unit for every unit_id that exists, and raises
        # for one that does not.
        assert unit is not None
        unit = unit.lower()
        (_display_name, conversion_factor, parse_func,
         _display_func, _) = UNIT_FORMAT_DB[unit_id]['conversions'][unit]
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
            sorted_suffixes: list[tuple[str, str, UnitConversion]] = []
            for trial_unit, trial_conversion in conversions.items():
                trial_suffix_list = trial_conversion[4]
                for suffix in trial_suffix_list:
                    sorted_suffixes.append((suffix, trial_unit, trial_conversion))
            sorted_suffixes.sort(key=lambda x: -len(x[0]))
            for trial_suffix, trial_unit, _trial_conversion in sorted_suffixes:
                if s.endswith(trial_suffix):
                    force_unit = trial_unit
                    # Strip off the unit name from the number
                    s = s[:-len(trial_suffix)]
                    break
        ret = parse_func(s) # Parse the int or float
        # math.isfinite() raises OverflowError - not ValueError - on an int too
        # large to convert to a float, and every rejection from this parser must
        # be a ValueError or it escapes the caller's guard. A 400-digit numeric
        # value reaches this from any integer-formatted field, so the overflow is
        # reachable input, not a theoretical case.
        try:
            value_is_finite = math.isfinite(ret)
        except OverflowError as err:
            raise ValueError from err
        if not value_is_finite:
            raise ValueError
        if force_unit is not None:
            in_default = convert_to_default_unit(ret, unit_id, force_unit)
            return convert_from_default_unit(in_default, unit_id, unit)
        return ret

    # We only adjust for the conversion factor for non-standard parsers, because
    # those are ones that might specify an explicit unit (like "1d" for radians)
    # but we wouldn't have caught it as part of the generic numeric processing
    # above
    return parse_func(s, conversion_factor=conversion_factor,
                      numerical_format=numerical_format,
                      unit_id=unit_id, unit=unit)

def parse_form_type(s: str | None) -> tuple[str | None, str | None, str | None]:
    """Parse the ParamInfo FORM_TYPE with its subfields.

    Subfields are:
        TYPE[%format][:unit]

    Parameters:
        s: The form type, or None.

    Returns:
        A triple of the type, the numerical format without its leading ``%``, and
        the unit_id without its leading ``:``. The format and the unit_id are None
        when the form type leaves them out, and all three are None when `s` is None.
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

def get_single_parse_function(unit_id: str | None) -> ParseFunc | None:
    """Return the parse func for a unit_id with a single non-displayed unit.

    Parameters:
        unit_id: The id of the unit system, or None.

    Returns:
        The parser of the unit_id's default unit, or None when `unit_id` is None or
        empty, when its unit is ever shown to the user, or when its default unit is
        read as a plain number.

    Raises:
        KeyError: If `unit_id` names no unit system.
    """
    parse_func = None
    if unit_id and not display_unit_ever(unit_id):
        default_unit = get_default_unit(unit_id)
        # unit_id is not None here, so neither is its default unit.
        assert default_unit is not None
        parse_func = (UNIT_FORMAT_DB[unit_id]['conversions'][default_unit][2])
    return parse_func

def get_single_format_function(unit_id: str | None) -> FormatFunc | None:
    """Return the format func for a unit_id with a single non-displayed unit.

    Parameters:
        unit_id: The id of the unit system, or None.

    Returns:
        The formatter of the unit_id's default unit, or None when `unit_id` is None
        or empty, when its unit is ever shown to the user, or when its default unit
        is written as a plain number.

    Raises:
        KeyError: If `unit_id` names no unit system.
    """
    format_func = None
    if unit_id and not display_unit_ever(unit_id):
        default_unit = get_default_unit(unit_id)
        # unit_id is not None here, so neither is its default unit.
        assert default_unit is not None
        format_func = (UNIT_FORMAT_DB[unit_id]['conversions'][default_unit][3])
    return format_func
