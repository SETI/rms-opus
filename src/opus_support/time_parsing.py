"""Time conversions between text formats and the internal TAI seconds value.

All parsing and formatting is delegated to the ``julian`` package; this module
only chooses the representation and enforces the supported date range.
"""

import math

import julian

# We limit the available times because julian doesn't support parsing dates
# outside of this range
MIN_TIME = -31556908800  # 1000-01-01T00:00:00
MAX_TIME =  31556995236  # 2999-12-31T23:59:59

################################################################################
################################################################################
# TIME CONVERSION
################################################################################

def parse_time(iso, unit=None, **kwargs):
    iso = str(iso)
    # For raw numbers, try to use the current unit to figure out what
    # to do
    try:
        et = float(iso)
    except Exception:
        pass
    else:
        if not math.isfinite(et):
            raise ValueError(f'Invalid time syntax: {iso}')
        if unit == 'et':
            return julian.tai_from_tdb(et)
        if unit == 'jd':
            iso = 'JD' + iso
        elif unit == 'jed':
            iso = 'JED' + iso
        elif unit == 'mjd':
            iso = 'MJD' + iso
        elif unit == 'mjed':
            iso = 'MJED' + iso
    try:
        (day, sec, time_type) = julian.day_sec_from_string(iso, timesys=True)
    except Exception:
        raise ValueError(f'Invalid time syntax: {iso}') from None
    if time_type not in ('UTC', 'TDB'):
        raise ValueError(f'Invalid time system {time_type} when parsing {iso}')
    # julian parses a Julian date far outside its own supported range without
    # complaint and only fails on the conversion, with whatever exception the
    # arithmetic happens to raise - an OverflowError for a day number too large
    # for a C long. Every rejection here must be a ValueError or it escapes the
    # caller's guard, so the conversion is part of the parse.
    try:
        ret = julian.tai_from_day(day) + sec
    except Exception as err:
        raise ValueError(f'Invalid time syntax: {iso}') from err
    if ret < MIN_TIME or ret > MAX_TIME:
        raise ValueError
    return float(ret)

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
    return f'JD{jd:.8f}'

def format_time_jed(tai, **kwargs):
    jed = julian.jd_from_time(tai, timesys='TAI', jdsys='TDB')
    # We want seconds at a resolution of .001
    # There are 86400 seconds in a day, which is roughly 100,000
    # So we want 5+3=8 decimal places
    return f'JED{jed:.8f}'

def format_time_mjd(tai, **kwargs):
    (day, sec) = julian.day_sec_from_tai(tai)
    mjd = julian.mjd_from_day_sec(day, sec)
    # We want seconds at a resolution of .001
    # There are 86400 seconds in a day, which is roughly 100,000
    # So we want 5+3=8 decimal places
    return f'MJD{mjd:.8f}'

def format_time_mjed(tai, **kwargs):
    mjed = julian.mjd_from_time(tai, timesys='TAI', mjdsys='TDB')
    # We want seconds at a resolution of .001
    # There are 86400 seconds in a day, which is roughly 100,000
    # So we want 5+3=8 decimal places
    return f'MJED{mjed:.8f}'

def format_time_et(tai, **kwargs):
    et = julian.tdb_from_tai(tai)
    return f'{et:.3f}'
