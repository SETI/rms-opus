"""The recorder's rules, tested without the holdings they normally read.

`import_tests.tools.make_mini_holdings` runs on the holdings machine and nowhere else,
so the code deciding what goes into the fixture is the one part of this suite that no
run of the suite exercises. Its decisions are pure functions of their inputs, though --
which rows a sampler keeps, how a manifest name maps to a shelf path, how a table is cut
down, which key an index-shelf lookup resolves to -- and those are what this module
holds to their contracts, from data written here.

The one that most needs it is `import_tests.tools.shelf_capture.matching_index_key`: it
reimplements pdsfile's own three-step resolution, so it is the piece of this suite most
able to drift away from the thing it mirrors.
"""

from __future__ import annotations

from typing import Any

import pytest

from import_tests.tools import row_sampling, shelf_capture, shelf_manifests, table_subsets

#: A label just complete enough for the two keywords the subsetter rewrites and the one
#: it measures records with. Real labels carry hundreds of lines around these.
_LABEL = (
    b'PDS_VERSION_ID       = PDS3\r\n'
    b'RECORD_TYPE          = FIXED_LENGTH\r\n'
    b'RECORD_BYTES         = 10\r\n'
    b'FILE_RECORDS         = 4\r\n'
    b'^INDEX_TABLE         = "MINI_INDEX.TAB"\r\n'
    b'OBJECT               = INDEX_TABLE\r\n'
    b'  ROWS               = 4\r\n'
    b'END_OBJECT           = INDEX_TABLE\r\n'
    b'END\r\n'
)

#: Four fixed-length records of ten bytes each, CRLF included, as a PDS3 table is.
_TABLE = b'aaaaaaaa\r\nbbbbbbbb\r\ncccccccc\r\ndddddddd\r\n'


def _rows(*values: tuple[Any, ...]) -> list[dict[str, Any]]:
    """Return index rows with the three columns the sampler's rules all touch.

    Parameters:
        values: One (filter, target, longitude range) triple per row.

    Returns:
        The rows, as a table reader would produce them.
    """
    return [
        {
            'FILTER_NAME': filter_name,
            'TARGET_NAME': target,
            'RING_LONGITUDE_MINIMUM': low,
            'RING_LONGITUDE_MAXIMUM': high,
        }
        for filter_name, target, (low, high) in values
    ]


def test_a_short_index_keeps_every_row() -> None:
    """An index no longer than the floor is not sampled at all.

    The second row is a duplicate of the first, so a sampler that scored it would keep
    only one: the floor is what puts both in the fixture.
    """
    rows = _rows(('CLEAR', 'SATURN', (1.0, 2.0)), ('CLEAR', 'SATURN', (1.0, 2.0)))
    assert row_sampling.select_rows(rows, floor=2, cap=20) == [0, 1]


def test_a_row_is_classified_by_code_path_rather_than_by_value() -> None:
    """The classes one row contributes, written out rather than recomputed.

    Every other assertion here asks the sampler to agree with itself -- `select_rows`
    optimises over `row_classes` and `uncovered_classes` recomputes it, so a wrong class
    is invisible to both. This is the one that says what a class actually is: an
    enumerated cell contributes its own value, a sentinel contributes "missing" whatever
    its spelling, a non-enumerated cell contributes only "present", and a minimum/maximum
    pair contributes one extra class of its own saying whether the range wraps.
    """
    columns = ('FILTER_NAME', 'NOTE', 'QUALITY', 'LON_MINIMUM', 'LON_MAXIMUM')
    rows = [
        dict(zip(columns, values, strict=True))
        for values in [
            ('CLEAR', 'a', 'GOOD', 350.0, 10.0),
            ('CLEAR', 'b', 'GOOD', 1.0, 5.0),
            ('GREEN', 'c', 'N/A', 2.0, 6.0),
            ('GREEN', 'd', 'GOOD', 3.0, 7.0),
        ]
    ]
    # Enumerated means *strictly* fewer distinct present values than the index has rows,
    # so a column holding one value per row is an identifier and a near-constant one is
    # an enumeration. Four rows: two filters and one quality value qualify; the note and
    # the two longitudes have a different value in every row and do not.
    assert row_sampling.enumerated_cells(rows) == {'FILTER_NAME', 'QUALITY'}

    enumerated = row_sampling.enumerated_cells(rows)
    pairs = [('LON_MINIMUM', 'LON_MAXIMUM')]
    assert row_sampling.row_classes(rows[0], pairs, enumerated) == {
        ('FILTER_NAME', '=CLEAR'),
        ('QUALITY', '=GOOD'),
        ('NOTE', row_sampling.PRESENT_CLASS),
        ('LON_MINIMUM', row_sampling.PRESENT_CLASS),
        ('LON_MAXIMUM', row_sampling.PRESENT_CLASS),
        ('LON_MINIMUM/LON_MAXIMUM', row_sampling.WRAPPED_CLASS),
    }
    assert row_sampling.row_classes(rows[2], pairs, enumerated) == {
        ('FILTER_NAME', '=GREEN'),
        ('QUALITY', row_sampling.MISSING_CLASS),
        ('NOTE', row_sampling.PRESENT_CLASS),
        ('LON_MINIMUM', row_sampling.PRESENT_CLASS),
        ('LON_MAXIMUM', row_sampling.PRESENT_CLASS),
        ('LON_MINIMUM/LON_MAXIMUM', row_sampling.UNWRAPPED_CLASS),
    }


def test_sampling_covers_every_class_it_can() -> None:
    """The chosen rows leave nothing uncovered when the cap allows it.

    Three rows, three filters, two targets and one wraparound: a sampler that took the
    first two rows by position would miss the third filter and the wrap.
    """
    rows = _rows(
        ('CLEAR', 'SATURN', (1.0, 2.0)),
        ('CLEAR', 'SATURN', (3.0, 4.0)),
        ('GREEN', 'TITAN', (350.0, 10.0)),
        ('BLUE', 'SATURN', (5.0, 6.0)),
    )
    chosen = row_sampling.select_rows(rows, floor=2, cap=20)
    assert row_sampling.uncovered_classes(rows, chosen) == set()


def test_sampling_reaches_the_wraparound_before_the_repetition() -> None:
    """Given a budget of two, the sampler spends it on two different code paths.

    The wrapped longitude range is a branch; a second identical row is not.
    """
    rows = _rows(
        ('CLEAR', 'SATURN', (1.0, 2.0)),
        ('CLEAR', 'SATURN', (1.0, 2.0)),
        ('CLEAR', 'SATURN', (350.0, 10.0)),
    )
    chosen = row_sampling.select_rows(rows, floor=0, cap=2)
    wrapped = ('RING_LONGITUDE_MINIMUM/RING_LONGITUDE_MAXIMUM', row_sampling.WRAPPED_CLASS)
    assert wrapped not in row_sampling.uncovered_classes(rows, chosen)


def test_the_cap_bounds_what_is_kept_and_is_reported() -> None:
    """A cap below what full coverage needs keeps the cap's worth and says what it cost.

    Ten rows over five filters, so ``FILTER_NAME`` is an enumeration -- fewer distinct
    values than the index has rows -- and three rows cannot show all five.
    """
    rows = _rows(*[(f'FILTER{index % 5}', 'SATURN', (1.0, 2.0)) for index in range(10)])
    chosen = row_sampling.select_rows(rows, floor=2, cap=3)
    assert len(chosen) == 3
    assert chosen == sorted(chosen)
    # Three rows show three of the five filters, so exactly the other two are the cost.
    assert row_sampling.uncovered_classes(rows, chosen) == {
        ('FILTER_NAME', '=FILTER3'),
        ('FILTER_NAME', '=FILTER4'),
    }


def test_sampling_stops_once_there_is_nothing_left_to_cover() -> None:
    """A cap the index does not need is not spent: rows that add no class are not kept.

    A hundred identical rows are one code path, and keeping twenty of them would grow
    the fixture without reaching anything the first two do not.
    """
    rows = _rows(*[('CLEAR', 'SATURN', (1.0, 2.0)) for _ in range(100)])
    chosen = row_sampling.select_rows(rows, floor=2, cap=20)
    assert len(chosen) == 2
    assert row_sampling.uncovered_classes(rows, chosen) == set()


def test_an_identifier_column_is_not_scored_as_an_enumeration() -> None:
    """A column with a different value in every row contributes no per-value classes.

    Without this the sampler would see one class per row and every row would look
    equally valuable, which is the same as sampling by position.
    """
    rows = [{'FILE_NAME': f'N{index}.IMG', 'FILTER_NAME': 'CLEAR'} for index in range(5)]
    assert row_sampling.enumerated_cells(rows) == {'FILTER_NAME'}


@pytest.mark.parametrize(
    'value',
    ['', 'N/A', 'n/a  ', 'UNK', 'NULL', 'UNKNOWN', -1.0e32, float('nan'), None],
)
def test_the_sentinels_are_all_read_as_missing(value: Any) -> None:
    """Every spelling of "nothing here" the archives use lands in one class."""
    assert row_sampling.is_missing(value)


@pytest.mark.parametrize('value', ['CLEAR', 0.0, -1.0, 1.0e29])
def test_a_real_value_is_not_read_as_missing(value: Any) -> None:
    """A measurement, including zero and a large one, is present."""
    assert not row_sampling.is_missing(value)


def test_a_subsetted_table_keeps_whole_records() -> None:
    """Cutting rows out of a fixed-length table leaves the surviving records intact."""
    record_bytes = table_subsets.read_record_bytes(_LABEL)
    assert record_bytes == 10
    assert table_subsets.is_fixed_length(_LABEL)
    subset = table_subsets.subset_fixed_length_table(_TABLE, record_bytes, [0, 2])
    assert subset == b'aaaaaaaa\r\ncccccccc\r\n'


def test_the_label_learns_the_new_record_count() -> None:
    """Both keywords that count records are rewritten, and nothing else moves."""
    rewritten = table_subsets.rewrite_counts(_LABEL, 2)
    assert b'FILE_RECORDS         = 2\r\n' in rewritten
    assert b'  ROWS               = 2\r\n' in rewritten
    assert b'RECORD_BYTES         = 10\r\n' in rewritten
    assert rewritten.count(b'\r\n') == _LABEL.count(b'\r\n')


@pytest.mark.parametrize(
    'name',
    [
        shelf_manifests.ManifestName('info', 'volumes', 'COISS_2xxx', 'COISS_2055'),
        shelf_manifests.ManifestName('link', 'metadata', 'GO_0xxx', 'GO_0011'),
        shelf_manifests.ManifestName(
            'index', 'metadata', 'COISS_2xxx', 'COISS_2055', 'COISS_2055_index'
        ),
        # A PDS4 bundle set whose metadata has no bundle level: pdsfile addresses each
        # file there as a bundle of its own, so the bundle field carries a dot.
        shelf_manifests.ManifestName('info', 'metadata', 'uranus_occs_earthbased', 'u14_opmt.csv'),
    ],
)
def test_a_manifest_name_survives_its_file_name(name: shelf_manifests.ManifestName) -> None:
    """Every field of a shelf's identity comes back out of the file name it goes into."""
    assert shelf_manifests.ManifestName.parse(name.filename) == name


def test_a_manifest_name_becomes_the_shelf_path_pdsfile_reads() -> None:
    """The path a manifest is pickled to is the one pdsfile looks for."""
    info = shelf_manifests.ManifestName('info', 'volumes', 'COISS_2xxx', 'COISS_2055')
    assert info.shelf_relpath == '_infoshelf-volumes/COISS_2xxx/COISS_2055_info.pickle'
    link = shelf_manifests.ManifestName('link', 'volumes', 'COISS_2xxx', 'COISS_2055')
    assert link.shelf_relpath == '_linkshelf-volumes/COISS_2xxx/COISS_2055_links.pickle'
    index = shelf_manifests.ManifestName(
        'index', 'metadata', 'COISS_2xxx', 'COISS_2055', 'COISS_2055_index'
    )
    assert index.shelf_relpath == (
        '_indexshelf-metadata/COISS_2xxx/COISS_2055/COISS_2055_index.pickle'
    )


@pytest.mark.parametrize(
    ('shelf_type', 'table', 'message'),
    [
        ('index', None, 'must name its table'),
        ('info', 'a_table', 'covers a whole bundle'),
        ('link', 'a_table', 'covers a whole bundle'),
        ('nonesuch', None, 'Unknown shelf type'),
    ],
)
def test_a_manifest_name_that_no_shelf_path_exists_for_is_refused(
    shelf_type: str, table: str | None, message: str
) -> None:
    """An index shelf needs a table and the others cannot have one.

    Each case names the message it expects, not just "some ValueError": all three say
    "shelf", so matching on that alone would pass with the two guards swapped.
    """
    with pytest.raises(ValueError, match=message):
        shelf_manifests.ManifestName(shelf_type, 'metadata', 'SET', 'BUNDLE', table)


def test_the_manifest_text_round_trips() -> None:
    """A shelf dictionary written as a manifest reads back as itself."""
    entries = {
        'data/x.img': (10, 0, '2010-03-12 14:00:06.000000', 'abc', (1024, 1024)),
        '': (20, 2, '2010-03-12 14:00:06.000000', '', (0, 0)),
    }
    text = shelf_manifests.format_manifest(entries)
    assert text.splitlines()[1].startswith("    '':")
    assert shelf_manifests.read_manifest_text(text) == entries


@pytest.mark.parametrize(
    ('selection', 'expected'),
    [
        # Exact first.
        ('c3450001', 'C3450001'),
        # Then the longest key the selection starts with: a Voyager image index is keyed
        # by the image number while the observation's file name carries a suffix.
        ('c3450001_raw', 'C3450001'),
        # Then the one key that starts with the selection.
        ('c34500', 'C3450001'),
    ],
)
def test_an_index_key_resolves_the_way_pdsfile_resolves_it(selection: str, expected: str) -> None:
    """The three steps, in order, on a shelf holding one key."""
    keys = {'c3450001': 'C3450001'}
    assert shelf_capture.matching_index_key(keys, selection) == expected


def test_a_prefix_selection_takes_the_longest_key_not_just_any() -> None:
    """With two keys the selection starts with, the longer one wins.

    A one-key shelf cannot show this: "the longest of the keys the selection starts with"
    and "the first one found" agree there, so a resolution that dropped the ``max`` would
    still look right. Two keys is the smallest shelf that tells them apart, and pdsfile
    really does take the longest.
    """
    keys = {'c345': 'C345', 'c3450001': 'C3450001'}
    assert shelf_capture.matching_index_key(keys, 'c3450001_raw') == 'C3450001'


def test_several_keys_the_selection_starts_with_are_not_ambiguous() -> None:
    """Only the *starts-with* step can be ambiguous; the inside step always resolves."""
    keys = {'c345': 'C345', 'c3450001': 'C3450001'}
    assert shelf_capture.matching_index_key(keys, 'c345') == 'C345'


def test_an_ambiguous_index_key_resolves_to_nothing() -> None:
    """Two keys starting with the selection is an error rather than a choice."""
    keys = {'c3450001': 'C3450001', 'c3450002': 'C3450002'}
    assert shelf_capture.matching_index_key(keys, 'c34500') is None


def test_an_unknown_index_key_resolves_to_nothing() -> None:
    """A selection nothing matches resolves to nothing rather than to the nearest key."""
    assert shelf_capture.matching_index_key({'c3450001': 'C3450001'}, 'x9999') is None


def test_a_logical_path_splits_into_the_four_parts_a_shelf_is_addressed_by() -> None:
    """The category, bundle set, bundle and the interior path below it."""
    assert shelf_capture.split_logical_path('volumes/COISS_2xxx/COISS_2055/data/1_1/N1.IMG') == (
        'volumes',
        'COISS_2xxx',
        'COISS_2055',
        'data/1_1/N1.IMG',
    )
    assert shelf_capture.split_logical_path('volumes/COISS_2xxx/COISS_2055') == (
        'volumes',
        'COISS_2xxx',
        'COISS_2055',
        '',
    )


def test_a_path_naming_no_bundle_is_refused() -> None:
    """A documents-tree path names no bundle, and no shelf can be addressed for it."""
    with pytest.raises(ValueError, match='no bundle'):
        shelf_capture.split_logical_path('documents/COISS_2xxx')


def test_a_shelf_key_carries_every_directory_above_it() -> None:
    """A file's key is useless without the directories the listing walks to reach it."""
    assert shelf_capture.ancestor_keys('data/1_1/N1.IMG') == {
        '',
        'data',
        'data/1_1',
        'data/1_1/N1.IMG',
    }
    assert shelf_capture.ancestor_keys('') == {''}
