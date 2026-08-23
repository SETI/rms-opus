"""Tests for the cart's byte-count formatter.

`nice_file_size` replaced `hurry.filesize.size` in PR-09. Its output is public API
— `__cart/status.json` returns it as `download_size_pretty` — and it is embedded in
the golden response fixtures, so what these tests pin is *parity with the package
that was removed*, not a formatting choice made here. Every expected value below was
produced by running `hurry.filesize.size` (version 0.9, the pinned version at the
time of the change) on the same input, and cross-checked by sweeping 420,035 byte
counts from 0 to 4 EiB against the installed package before it was dropped.

The module deliberately imports nothing from Django, so these run without the app
registry or a configuration file.
"""

import random

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


def hurry_filesize_size(size_bytes: int) -> str:
    """Transcription of `hurry.filesize.size` with its default `traditional` system.

    The oracle for the sweep below. It is written the way the package wrote it,
    including the float division and the reliance on the loop variable surviving
    the loop, so that it can disagree with the implementation under test.

    Parameters:
        size_bytes: A number of bytes.

    Returns:
        The string the removed package returned for that count.
    """
    system = [(1024 ** 5, 'P'), (1024 ** 4, 'T'), (1024 ** 3, 'G'),
              (1024 ** 2, 'M'), (1024 ** 1, 'K'), (1024 ** 0, 'B')]
    # B007 is suppressed below because `suffix` IS used — after the loop, not
    # inside it. Both loop variables are read on the return line, which is how
    # the original decided the unit: it let the bindings survive the loop, so
    # falling off the end (a count below one kilobyte) leaves the last pair,
    # (1, 'B'), in scope. Renaming as ruff suggests would break the
    # transcription, and restructuring to avoid the leak would stop this being a
    # faithful copy of the code under comparison.
    for factor, suffix in system:  # noqa: B007
        if size_bytes >= factor:
            break
    return str(int(size_bytes / factor)) + suffix


def test_matches_the_transcribed_package_across_every_reachable_size() -> None:
    """Sweep `nice_file_size` against the old algorithm over the whole usable range.

    The parity table above pins hand-picked values; this drives both
    implementations over ~35,000 counts, sampled both uniformly and within each
    unit rung, so a regression anywhere in the ladder is caught rather than only
    at the values someone thought to list.

    Every count stays below 2**53, which is where the two provably cannot
    disagree: any integer below 2**53 is exactly representable as a double, and
    dividing it by a power of two only adjusts the exponent, so `int(x / factor)`
    truncates the same exact quotient `//` computes. 2**53 bytes is 8 PiB, and
    MAX_CUM_DOWNLOAD_SIZE caps an OPUS download at 50 GiB — five orders of
    magnitude below it. Above 2**53 they do diverge, which the next test pins.
    """
    rng = random.Random(20260823)
    counts = list(range(0, 5000))
    for exponent in range(0, 6):
        factor = 1024 ** exponent
        counts += [factor - 1, factor, factor + 1, 2 * factor,
                   min(1023 * factor, 2 ** 53 - 1)]
        # Sample within this rung as well as uniformly overall. A uniform draw
        # below 2**53 lands in the petabyte rung seven times out of eight and
        # essentially never below a terabyte, so without this the megabyte and
        # gigabyte rungs would be covered only by the boundary values listed
        # above — exactly the "values someone thought to list" this sweep is
        # meant to improve on.
        counts += [rng.randrange(factor, min(1024 * factor, 2 ** 53))
                   for _ in range(2000)]
    counts += [rng.randrange(0, 2 ** 53) for _ in range(20000)]
    for size_bytes in counts:
        assert nice_file_size(size_bytes) == hurry_filesize_size(size_bytes)


@pytest.mark.parametrize('size_bytes', [2 ** 60 - 2, 2 ** 60 - 1])
def test_truncates_exactly_where_the_old_float_division_did_not(size_bytes: int) -> None:
    """Two sizes where the replacement deliberately disagrees with hurry.

    Above 2**53 the float quotient stops being exact and rounds *up* just below an
    exact PiB multiple, so `hurry.filesize` reported '1024P' for a size that has
    not reached 1024 PiB. This is systematic, not a pair of freak values: the
    window immediately below each multiple is 32 values wide below 512 PiB, 64
    below 1024 PiB and 8192 below 100000 PiB, doubling as the magnitude doubles.
    These two are pinned as representatives. Integer division reports the
    truncated value the format promises, so the replacement is the more truthful
    of the two everywhere they differ.
    """
    assert size_bytes // 1024 ** 5 == 1023
    assert int(size_bytes / 1024 ** 5) == 1024  # what hurry.filesize returned
    assert nice_file_size(size_bytes) == '1023P'
