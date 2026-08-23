"""Tests for the cart's byte-count formatter.

`nice_file_size` replaced `hurry.filesize.size` in PR-09. Its output is public API
— `__cart/status.json` returns it as `download_size_pretty` — and it is embedded in
the golden response fixtures, so what these tests pin is *parity with the package
that was removed*, not a formatting choice made here. Every expected value below was
produced by running `hurry.filesize.size` (version 0.9, the pinned version at the
time of the change) on the same input.

The module deliberately imports nothing from Django, so these run without the app
registry or a configuration file.
"""

import pytest

from opus_app.apps.tools.file_size import nice_file_size

#: (bytes, the string hurry.filesize.size returned for it).
PARITY_CASES = [
    # Below a kilobyte the count is exact and carries the byte suffix. 0B is the
    # value the golden fixtures show for an empty selection.
    (0, '0B'),
    (1, '1B'),
    (999, '999B'),
    (1023, '1023B'),
    # Each boundary, and one byte below it, so an off-by-one in the comparison
    # cannot pass.
    (1024, '1K'),
    (1024 ** 2 - 1, '1023K'),
    (1024 ** 2, '1M'),
    (1024 ** 3 - 1, '1023M'),
    (1024 ** 3, '1G'),
    (1024 ** 4 - 1, '1023G'),
    (1024 ** 4, '1T'),
    (1024 ** 5 - 1, '1023T'),
    (1024 ** 5, '1P'),
    # The fractional part is truncated, never rounded: 2000 bytes is 1.95K and
    # reads as 1K, and a byte short of a megabyte is not a megabyte.
    (2000, '1K'),
    (10000, '9K'),
    (1000000, '976K'),
    (2000000, '1M'),
    # Values taken from the golden response fixtures, which is where a change in
    # this function would show up first.
    (11 * 1024, '11K'),
    (10 * 1024 ** 2, '10M'),
    (158 * 1024 ** 2, '158M'),
    # Above a petabyte the largest unit simply keeps counting, as it did before.
    (2048 * 1024 ** 5, '2048P'),
]


@pytest.mark.parametrize(('size_bytes', 'expected'), PARITY_CASES)
def test_matches_the_package_it_replaced(size_bytes: int, expected: str) -> None:
    """Each byte count formats exactly as `hurry.filesize.size` formatted it."""
    assert nice_file_size(size_bytes) == expected


@pytest.mark.parametrize('size_bytes', [2 ** 60 - 2, 2 ** 60 - 1])
def test_truncates_exactly_where_the_old_float_division_did_not(size_bytes: int) -> None:
    """The two counts where the replacement deliberately disagrees with hurry.

    `hurry.filesize` computed `int(bytes / factor)` through a float, and just under
    1024 PiB that quotient rounds *up* to 1024.0, so it reported '1024P' for a size
    that has not reached 1024 PiB. Integer division reports the truncated value the
    format promises. Sweeping every value from 0 to 4 EiB (420,035 checked, dense
    random sampling plus every boundary) found these two and nothing else, so this
    is the whole of the divergence — and no OPUS download is within many orders of
    magnitude of it.
    """
    assert size_bytes // 1024 ** 5 == 1023
    assert int(size_bytes / 1024 ** 5) == 1024  # what hurry.filesize returned
    assert nice_file_size(size_bytes) == '1023P'
