"""Two latent defects in the per-index import, both pre-existing.

Neither was introduced by splitting `do_import.py`; both are byte-identical in
`24ef9256`'s pre-split file. CodeRabbit found them because cutting a 1,782-line module
into five made them legible. They are fixed here rather than deferred, because this PR
rewrote the very lines they sit on.

1. `get_opus_products_rows_for_filespec` returned a bare `None` when the filespec could
   not be converted, while its only caller does
   ``table_rows[table_name].extend(rows)`` -- so a recoverable, logged error became
   ``TypeError: 'NoneType' object is not iterable`` and aborted the whole index import.
2. The ``obs_surface_geometry`` guard tested one dictionary key and initialized another.
"""

import ast
from pathlib import Path

import pytest

import opus_import.steps.do_import_index as do_import_index
from opus_import import import_util


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
def failing_pdsfile(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    """Make every filespec conversion fail, and capture the errors it logs."""
    logged: list[str] = []
    monkeypatch.setattr(do_import_index, 'pdsfile', _FailingPdsFile)
    monkeypatch.setattr(import_util, 'log_nonrepeating_error',
                        lambda msg: logged.append(msg))
    return logged


@pytest.mark.parametrize('pds_version', [3, 4])
def test_a_failed_filespec_conversion_returns_an_empty_list(
        pds_version: int, failing_pdsfile: list[str]) -> None:
    """The result must be iterable: the caller extends its row list with it."""
    rows = do_import_index.get_opus_products_rows_for_filespec(
        pds_version, 'BOGUS/FILESPEC.LBL', 1, 'co-iss-n0', 'COISS_2002', 'COISS')

    assert rows == []
    assert failing_pdsfile == ['Failed to convert filespec "BOGUS/FILESPEC.LBL"']


def test_a_failed_filespec_conversion_can_be_extended_by_the_caller(
        failing_pdsfile: list[str]) -> None:
    """Reproduces the caller's exact use, which used to raise TypeError on None."""
    table_rows: dict[str, list] = {'obs_files': []}

    rows = do_import_index.get_opus_products_rows_for_filespec(
        3, 'BOGUS/FILESPEC.LBL', 1, 'co-iss-n0', 'COISS_2002', 'COISS')
    table_rows['obs_files'].extend(rows)

    assert table_rows == {'obs_files': []}


def test_every_table_rows_guard_initializes_the_key_it_tested() -> None:
    """``if X not in table_rows`` must be followed by ``table_rows[X] = []``.

    The ``obs_surface_geometry`` guard tested ``table_name`` and created
    ``table_rows[new_table_name]``, so the append on the next line would have raised
    `KeyError` -- and `new_table_name` is a leftover from an earlier loop that need not
    even be bound, which would have raised `NameError` first.

    The guard is unreachable today (``table_rows`` is pre-populated with every entry of
    ``table_names_in_order`` before the row loop, and that loop only yields names from
    the same list), which is exactly why the mistake survived: no test and no import run
    can execute it. So this checks the source rather than the behavior. The other three
    guards -- two for the derived ``obs_surface_geometry__<TARGET>`` names, which *are*
    reachable, and one for ``obs_files`` -- are held to the same rule.
    """
    source = Path(do_import_index.__file__).read_text(encoding='utf-8')
    tree = ast.parse(source)

    guards = []
    for node in ast.walk(tree):
        # if <key> not in table_rows: table_rows[<key2>] = []
        if not isinstance(node, ast.If) or not isinstance(node.test, ast.Compare):
            continue
        test = node.test
        if not (len(test.ops) == 1 and isinstance(test.ops[0], ast.NotIn)):
            continue
        if not (isinstance(test.comparators[0], ast.Name)
                and test.comparators[0].id == 'table_rows'):
            continue
        assigns = [stmt for stmt in node.body if isinstance(stmt, ast.Assign)]
        assert assigns, f'line {node.lineno}: guard body assigns nothing'
        target = assigns[0].targets[0]
        assert isinstance(target, ast.Subscript), f'line {node.lineno}'
        guards.append((node.lineno, ast.unparse(test.left), ast.unparse(target.slice)))

    assert len(guards) == 4, f'expected 4 table_rows guards, found {guards}'
    mismatched = [(line, tested, created)
                  for line, tested, created in guards if tested != created]
    assert mismatched == [], (
        'a table_rows guard initializes a different key than it tested, so the append '
        f'that follows it raises KeyError: {mismatched}')
