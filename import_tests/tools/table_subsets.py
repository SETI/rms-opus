"""Cut a PDS index down to a chosen set of rows without changing anything else.

The fixture's index and summary files are the real archive files with rows removed. A
label ships whole -- `pdstable` needs every column definition to parse the table it
describes -- and only the two keywords that count records are edited. Everything is done
on bytes so that a label's CRLF line endings and its exact column alignment survive.
"""

from __future__ import annotations

import re
from pathlib import Path

#: The label keywords that state how many records a table has. Both are rewritten when
#: rows are dropped; nothing else in a label describes the row count.
_COUNT_KEYWORDS = ('FILE_RECORDS', 'ROWS')

#: How a PDS3 label states the length of one fixed-length record.
_RECORD_BYTES_RE = re.compile(rb'(?m)^\s*RECORD_BYTES\s*=\s*(\d+)')

#: How a PDS3 label states its record type.
_RECORD_TYPE_RE = re.compile(rb'(?m)^\s*RECORD_TYPE\s*=\s*(\S+)')


def read_record_bytes(label_bytes: bytes) -> int:
    """Return the length of one record of the table a label describes.

    Parameters:
        label_bytes: The label file's contents.

    Returns:
        The ``RECORD_BYTES`` value.

    Raises:
        ValueError: If the label states no ``RECORD_BYTES``, which means the table is
            not fixed-length and cannot be sliced by record number.
    """
    match = _RECORD_BYTES_RE.search(label_bytes)
    if match is None:
        raise ValueError('Label states no RECORD_BYTES')
    return int(match.group(1))


def is_fixed_length(label_bytes: bytes) -> bool:
    """Return whether a label describes a fixed-length table.

    Parameters:
        label_bytes: The label file's contents.

    Returns:
        True if ``RECORD_TYPE`` is ``FIXED_LENGTH``. A stream table -- what the
        inventory files are -- is subset by line instead.
    """
    match = _RECORD_TYPE_RE.search(label_bytes)
    if match is None:
        return False
    return match.group(1).upper() == b'FIXED_LENGTH'


def rewrite_counts(label_bytes: bytes, row_count: int) -> bytes:
    """Return a label with its record counts replaced.

    Parameters:
        label_bytes: The label file's contents.
        row_count: The number of rows the subsetted table has.

    Returns:
        The label with every ``FILE_RECORDS`` and ``ROWS`` value replaced by
        ``row_count``. The keyword, its padding and the rest of the line are untouched,
        so the label's alignment survives even though the number's width changes.
    """
    result = label_bytes
    for keyword in _COUNT_KEYWORDS:
        pattern = re.compile(rb'(?m)^(\s*' + keyword.encode() + rb'\s*=\s*)(\d+)')
        result = pattern.sub(lambda m: m.group(1) + str(row_count).encode(), result)
    return result


def subset_fixed_length_table(table_bytes: bytes, record_bytes: int, rows: list[int]) -> bytes:
    """Return the chosen records of a fixed-length table, concatenated.

    Parameters:
        table_bytes: The table file's contents.
        record_bytes: The length of one record.
        rows: The row numbers to keep, zero-based.

    Returns:
        The kept records in the order given.

    Raises:
        ValueError: If the file's length is not a whole number of records, or a row
            number is past its end.
    """
    if len(table_bytes) % record_bytes != 0:
        raise ValueError(
            f'Table length {len(table_bytes)} is not a multiple of RECORD_BYTES {record_bytes}'
        )
    total = len(table_bytes) // record_bytes
    parts = []
    for row in rows:
        if row >= total:
            raise ValueError(f'Row {row} is past the end of a {total}-row table')
        parts.append(table_bytes[row * record_bytes : (row + 1) * record_bytes])
    return b''.join(parts)


def subset_line_table(table_bytes: bytes, rows: list[int]) -> bytes:
    """Return the chosen lines of a table that has one record per line.

    Parameters:
        table_bytes: The table file's contents.
        rows: The line numbers to keep, zero-based.

    Returns:
        The kept lines with their original terminators.

    Raises:
        ValueError: If a line number is past the end of the file.
    """
    lines = table_bytes.splitlines(keepends=True)
    parts = []
    for row in rows:
        if row >= len(lines):
            raise ValueError(f'Line {row} is past the end of a {len(lines)}-line file')
        parts.append(lines[row])
    return b''.join(parts)


def subset_csv(csv_bytes: bytes, rows: list[int]) -> bytes:
    """Return the header line of a CSV plus the chosen data lines.

    Parameters:
        csv_bytes: The CSV file's contents, whose first line is the header.
        rows: The data row numbers to keep, zero-based and not counting the header.

    Returns:
        The header followed by the kept rows.

    Raises:
        ValueError: If the file has no header line, or a row number is past its end.
    """
    lines = csv_bytes.splitlines(keepends=True)
    if len(lines) == 0:
        raise ValueError('CSV file is empty')
    parts = [lines[0]]
    for row in rows:
        if row + 1 >= len(lines):
            raise ValueError(f'Row {row} is past the end of a {len(lines) - 1}-row CSV')
        parts.append(lines[row + 1])
    return b''.join(parts)


def write_subset(
    source_label: Path, destination_label: Path, table_name: str, rows: list[int]
) -> None:
    """Write a PDS3 label and its table to a new location, keeping only some rows.

    Parameters:
        source_label: The label file to read.
        destination_label: Where to write the label. Its directory is created.
        table_name: The base name of the table file beside the label, whose subset is
            written beside the new label under the same name.
        rows: The row numbers to keep, zero-based.

    Raises:
        ValueError: If the label describes a fixed-length table whose length does not
            divide evenly, or a row number is past the table's end.
    """
    label_bytes = source_label.read_bytes()
    table_bytes = (source_label.parent / table_name).read_bytes()
    if is_fixed_length(label_bytes):
        subset = subset_fixed_length_table(table_bytes, read_record_bytes(label_bytes), rows)
    else:
        subset = subset_line_table(table_bytes, rows)
    destination_label.parent.mkdir(parents=True, exist_ok=True)
    destination_label.write_bytes(rewrite_counts(label_bytes, len(rows)))
    (destination_label.parent / table_name).write_bytes(subset)
