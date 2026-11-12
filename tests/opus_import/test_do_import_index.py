"""`get_opus_products_rows_for_filespec`: no `None` on a failed conversion, no trailing spaces.

When the filespec cannot be converted, the function logs the error and returns no rows.
Its only caller iterates the result, so a `None` would turn a recoverable, logged error
into ``TypeError: 'NoneType' object is not iterable`` and abort the whole index import.

A row it returns holds each ``varchar`` value without trailing spaces, as the ``char``
column it replaced returned it.
"""

from typing import Any, Literal

import pytest

import opus_import.steps.do_import_index as do_import_index
from opus_import.context import ImportContext

from .conftest import make_context


class _RejectingPdsFile:
    """A `Pds3File`/`Pds4File` stand-in that rejects every filespec."""

    @staticmethod
    def from_filespec(filespec: str, **_kwargs: object) -> object:
        """Reject every filespec; `**_kwargs` absorbs the real call's `fix_case`."""
        raise ValueError(f'no such filespec: {filespec}')


class _FailingPdsFile:
    """Stands in for the `pdsfile` package, mirroring its two-level attribute path."""

    class pds3file:  # noqa: N801 - mirrors the real module's name
        Pds3File = _RejectingPdsFile

    class pds4file:  # noqa: N801 - mirrors the real module's name
        Pds4File = _RejectingPdsFile


@pytest.fixture
def failing_pdsfile(monkeypatch: pytest.MonkeyPatch) -> ImportContext:
    """Make every filespec conversion fail, and return the context it reports through.

    The error travels the real route -- `import_util.log_nonrepeating_error` to
    `ImportLog` to the logger -- so the recorded message is the one an operator would
    read in the import log.
    """
    monkeypatch.setattr(do_import_index, 'pdsfile', _FailingPdsFile)
    return make_context()


@pytest.mark.parametrize('pds_version', [3, 4])
def test_a_failed_filespec_conversion_returns_an_empty_list(
    pds_version: Literal[3, 4], failing_pdsfile: ImportContext
) -> None:
    """The result must be iterable: the caller extends its row list with it."""
    rows = do_import_index.get_opus_products_rows_for_filespec(
        failing_pdsfile, pds_version, 'BOGUS/FILESPEC.LBL', 1, 'co-iss-n0', 'COISS_2002', 'COISS'
    )

    assert rows == []
    assert failing_pdsfile.logger.messages_at('error') == [
        'Failed to convert filespec "BOGUS/FILESPEC.LBL"'
    ]
    assert failing_pdsfile.import_has_bad_data is True


def test_a_failed_filespec_conversion_can_be_iterated_by_the_caller(
    failing_pdsfile: ImportContext,
) -> None:
    """Reproduces the caller's exact use: iterating a bare None is a TypeError."""
    emitted: list[Any] = []

    rows = do_import_index.get_opus_products_rows_for_filespec(
        failing_pdsfile, 3, 'BOGUS/FILESPEC.LBL', 1, 'co-iss-n0', 'COISS_2002', 'COISS'
    )
    for row in rows:
        emitted.append(row)

    assert emitted == []


class _File:
    """One file of a product, with the attributes the row builder reads."""

    version_rank = 1
    version_id = ''
    logical_path = 'volumes/COISS_2xxx/COISS_2002/data/N1460960653_1.IMG'
    is_index = False
    url = '/holdings/volumes/COISS_2xxx/COISS_2002/data/N1460960653_1.IMG'
    checksum = '0123456789abcdef0123456789abcdef  '
    size_bytes = 1024
    width = None
    height = None


class _AcceptingPdsFile:
    """A `Pds4File` stand-in whose one product type has names padded with spaces."""

    @staticmethod
    def from_filespec(filespec: str, **_kwargs: object) -> '_AcceptingPdsFile':
        """Accept any filespec."""
        return _AcceptingPdsFile()

    def opus_products(self) -> dict[tuple[Any, ...], list[list[_File]]]:
        """Return one product type of one file."""
        return {('standard', 10, 'coiss_raw  ', 'Raw Image  ', True): [[_File()]]}


class _AcceptingPdsFiles:
    """Stands in for the `pdsfile` package with the accepting class."""

    class pds3file:  # noqa: N801 - mirrors the real module's name
        Pds3File = _AcceptingPdsFile

    class pds4file:  # noqa: N801 - mirrors the real module's name
        Pds4File = _AcceptingPdsFile


def test_a_files_strings_are_stored_without_trailing_spaces(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Each ``varchar`` value loses its trailing spaces; a ``text`` value keeps its own."""
    monkeypatch.setattr(do_import_index, 'pdsfile', _AcceptingPdsFiles)
    (row,) = do_import_index.get_opus_products_rows_for_filespec(
        make_context(),
        4,
        'COISS_2002/data/N1460960653_1.LBL',
        1,
        'co-iss-n0',
        'COISS_2002',
        'COISS ',
    )

    assert (row['short_name'], row['full_name'], row['checksum'], row['instrument_id']) == (
        'coiss_raw',
        'Raw Image',
        '0123456789abcdef0123456789abcdef',
        'COISS',
    )
    assert row['url'] == _File.url.strip('/')
