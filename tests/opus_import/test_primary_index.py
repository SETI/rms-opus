"""How many rows a primary index file declares, which sizes a bundle's id range.

A label is read by ``pdstable`` with the table's loading deferred, so the count is the
label's, read without the table; an index with no label is counted by its lines.
"""

from __future__ import annotations

import re
import shutil
from pathlib import Path

import pytest

from opus_import import primary_index

#: A PDS3 index label of the mini-holdings fixture, and the rows its ``ROWS`` declares.
_PDS3_LABEL = (
    Path(__file__).resolve().parents[1]
    / 'fixtures/mini_holdings/pds3/metadata/COISS_2xxx/COISS_2055/COISS_2055_index.lbl'
)
_PDS3_ROWS = 20


def test_a_pds3_label_gives_its_rows_without_its_table(tmp_path: Path) -> None:
    """The label alone, copied away from its table, still gives the count."""
    label = tmp_path / _PDS3_LABEL.name
    shutil.copyfile(_PDS3_LABEL, label)
    assert list(tmp_path.iterdir()) == [label]
    assert primary_index.declared_rows(str(label)) == _PDS3_ROWS


def test_a_label_pdstable_cannot_read_is_refused_naming_it(tmp_path: Path) -> None:
    """A label without ``ROWS`` raises, naming the label and pdstable's reason."""
    label = tmp_path / _PDS3_LABEL.name
    lines = _PDS3_LABEL.read_text(encoding='latin-1').splitlines(keepends=True)
    label.write_text(
        ''.join(line for line in lines if not re.match(r'\s*ROWS\s*=', line)), encoding='latin-1'
    )
    with pytest.raises(primary_index.PrimaryIndexError, match=r'cannot be read.*ROWS') as raised:
        primary_index.declared_rows(str(label))
    assert str(label) in str(raised.value)


def test_a_pds4_csv_with_no_label_counts_its_rows_less_the_header(tmp_path: Path) -> None:
    """Blank lines are not rows, and the first line names the columns."""
    table = tmp_path / 'bundle_index.csv'
    table.write_text('a,b\n1,2\n\n3,4\n5,6\n', encoding='utf-8')
    assert primary_index.declared_rows(str(table)) == 3
