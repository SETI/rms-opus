"""Time conversions between text formats and the internal TAI seconds value.

All parsing and formatting is delegated to the ``julian`` package; this module
only chooses the representation and enforces the supported date range.
"""

import math

import julian

# We limit the available times because julian doesn't support parsing dates
# outside of this range
MIN_TIME = -31556908800  # 1000-01-01T00:00:00
MAX_TIME = 31556995236  # 2999-12-31T23:59:59

################################################################################
################################################################################
# TIME CONVERSION
################################################################################


def parse_time(iso: object, unit: str | None = None, **kwargs: object) -> float:
    """Convert a time to the internal value, seconds of TAI from J2000.

    Parameters:
        iso: The time to parse, in any format ``julian`` recognizes -- an ISO date
            and time, a year and day of year, or a Julian or Modified Julian date
            written with its ``JD``, ``JED``, ``MJD`` or ``MJED`` prefix. A bare
            number is read as a value of `unit`. A value that is not a string is
            converted with ``str`` first, so a number may be supplied as one.
        unit: The unit a bare number is in: ``et`` for barycentric dynamical time,
            or ``jd``, ``jed``, ``mjd`` or ``mjed`` for a date whose prefix was left
            off. None, or any other name, leaves a bare number to be read as a
            Julian date the way ``julian`` reads one.
        **kwargs: Accepted and ignored, so that every parser in this package can be
            called through one uniform dispatch.

    Returns:
        The time in seconds of TAI from the J2000 epoch, between `MIN_TIME` and
        `MAX_TIME`.

    Raises:
        ValueError: If the text names no time, names one in a time system other
            than UTC or TDB, or names one outside the supported range of years 1000
            to 2999. Only the out-of-range rejection carries an empty message.
    """
    iso = str(iso)
    # For raw numbers, try to use the current unit to figure out what
    # to do
    try:
        et = float(iso)
    except Exception:
        # Not a plain number, which is not an error here: the else branch below
        # is skipped and the caller falls through to the next parse strategy.
        pass  # nosec B110
    else:
        if not math.isfinite(et):
            raise ValueError(f'Invalid time syntax: {iso}')
        if unit == 'et':
            tai_from_et: float = julian.tai_from_tdb(et)
            return tai_from_et
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


def format_time_ymd(tai: float, **kwargs: object) -> str:
    """Format an internal time as a calendar date and time.

    Parameters:
        tai: The time in seconds of TAI from the J2000 epoch.
        **kwargs: Accepted and ignored, so that every formatter in this package can
            be called through one uniform dispatch.

    Returns:
        The UTC date and time as ``YYYY-MM-DDThh:mm:ss.sss``, to a resolution of a
        millisecond.
    """
    iso: str = julian.iso_from_tai(tai, ymd=True, digits=3)
    return iso


def format_time_ydoy(tai: float, **kwargs: object) -> str:
    """Format an internal time as a year, day of year, and time.

    Parameters:
        tai: The time in seconds of TAI from the J2000 epoch.
        **kwargs: Accepted and ignored, so that every formatter in this package can
            be called through one uniform dispatch.

    Returns:
        The UTC date and time as ``YYYY-DDDThh:mm:ss.sss``, to a resolution of a
        millisecond.
    """
    iso: str = julian.iso_from_tai(tai, ymd=False, digits=3)
    return iso


def format_time_jd(tai: float, **kwargs: object) -> str:
    """Format an internal time as a Julian date.

    Parameters:
        tai: The time in seconds of TAI from the J2000 epoch.
        **kwargs: Accepted and ignored, so that every formatter in this package can
            be called through one uniform dispatch.

    Returns:
        The Julian date in UTC, prefixed with ``JD`` and carrying eight decimal
        places, which is a resolution of about a millisecond.
    """
    (day, sec) = julian.day_sec_from_tai(tai)
    jd = julian.jd_from_day_sec(day, sec)
    # We want seconds at a resolution of .001
    # There are 86400 seconds in a day, which is roughly 100,000
    # So we want 5+3=8 decimal places
    return f'JD{jd:.8f}'


def format_time_jed(tai: float, **kwargs: object) -> str:
    """Format an internal time as a Julian ephemeris date.

    Parameters:
        tai: The time in seconds of TAI from the J2000 epoch.
        **kwargs: Accepted and ignored, so that every formatter in this package can
            be called through one uniform dispatch.

    Returns:
        The Julian date in barycentric dynamical time, prefixed with ``JED`` and
        carrying eight decimal places, which is a resolution of about a millisecond.
    """
    jed = julian.jd_from_time(tai, timesys='TAI', jdsys='TDB')
    # We want seconds at a resolution of .001
    # There are 86400 seconds in a day, which is roughly 100,000
    # So we want 5+3=8 decimal places
    return f'JED{jed:.8f}'


def format_time_mjd(tai: float, **kwargs: object) -> str:
    """Format an internal time as a Modified Julian date.

    Parameters:
        tai: The time in seconds of TAI from the J2000 epoch.
        **kwargs: Accepted and ignored, so that every formatter in this package can
            be called through one uniform dispatch.

    Returns:
        The Modified Julian date in UTC, prefixed with ``MJD`` and carrying eight
        decimal places, which is a resolution of about a millisecond.
    """
    (day, sec) = julian.day_sec_from_tai(tai)
    mjd = julian.mjd_from_day_sec(day, sec)
    # We want seconds at a resolution of .001
    # There are 86400 seconds in a day, which is roughly 100,000
    # So we want 5+3=8 decimal places
    return f'MJD{mjd:.8f}'


def format_time_mjed(tai: float, **kwargs: object) -> str:
    """Format an internal time as a Modified Julian ephemeris date.

    Parameters:
        tai: The time in seconds of TAI from the J2000 epoch.
        **kwargs: Accepted and ignored, so that every formatter in this package can
            be called through one uniform dispatch.

    Returns:
        The Modified Julian date in barycentric dynamical time, prefixed with
        ``MJED`` and carrying eight decimal places, which is a resolution of about a
        millisecond.
    """
    mjed = julian.mjd_from_time(tai, timesys='TAI', mjdsys='TDB')
    # We want seconds at a resolution of .001
    # There are 86400 seconds in a day, which is roughly 100,000
    # So we want 5+3=8 decimal places
    return f'MJED{mjed:.8f}'


def format_time_et(tai: float, **kwargs: object) -> str:
    """Format an internal time as an ephemeris time.

    Parameters:
        tai: The time in seconds of TAI from the J2000 epoch.
        **kwargs: Accepted and ignored, so that every formatter in this package can
            be called through one uniform dispatch.

    Returns:
        The barycentric dynamical time in seconds from the J2000 epoch, carrying
        three decimal places.
    """
    et = julian.tdb_from_tai(tai)
    return f'{et:.3f}'
