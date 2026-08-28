# tools/file_size.py
"""Render a byte count the way the OPUS cart interface displays it.

This replaces the two calls OPUS made into `hurry.filesize` (both in
`cart/views.py`), a package last released in 2010 whose only use here was its
default "traditional" system: powers of 1024, a single-letter suffix, and the
fractional part truncated rather than rounded, so 1,048,575 bytes reads as
"1023K" and not "1M".

The output is part of the public API (`__cart/status.json` reports
`download_size_pretty` and `total_download_size_pretty`) and appears in the golden
response fixtures, so the formatting is reproduced exactly rather than improved.
"""

#: Factor and suffix for each unit above a byte, largest first. There is no entry
#: for bytes themselves: a count below one kilobyte falls out of the loop and is
#: rendered by the final statement, which is also what keeps every branch here
#: reachable.
_SIZE_UNITS = (
    (1024**5, 'P'),
    (1024**4, 'T'),
    (1024**3, 'G'),
    (1024**2, 'M'),
    (1024**1, 'K'),
)


def nice_file_size(size_bytes: int) -> str:
    """Format a byte count as a short human-readable string.

    Parameters:
        size_bytes: A number of bytes.

    Returns:
        The count in the largest unit that does not reduce it below one, with the
        fractional part truncated and the unit's letter appended, e.g. 0 -> '0B',
        2000 -> '1K', 1572864 -> '1M'. A count below one kilobyte keeps its exact
        value and the 'B' suffix.
    """
    for factor, suffix in _SIZE_UNITS:
        if size_bytes >= factor:
            return f'{size_bytes // factor}{suffix}'
    return f'{size_bytes}B'
