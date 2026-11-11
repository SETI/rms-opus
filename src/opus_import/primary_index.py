"""Where a bundle's primary index files are, and how many rows their labels declare.

The import reads a bundle's observations from its primary index files, whose names
`opus_import.config_bundle_info` gives. `locate` finds them, for the import and for the
bundle registry alike, and `declared_rows` reads how many rows one declares without
reading its table, which is what the registry sizes a bundle's id range from.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

import pdsfile

from opus_import import import_util

if TYPE_CHECKING:
    from opus_import.config_bundle_info import BundleInfo

#: A PDS3 label's row count: ``ROWS = <n>`` at the start of a line.
_PDS3_ROWS = re.compile(r'^\s*ROWS\s*=\s*(\d+)', re.MULTILINE)

#: A PDS4 label's row count: ``<records>n</records>``.
_PDS4_RECORDS = re.compile(r'<records>\s*(\d+)\s*</records>')

#: The suffix of a PDS3 label, compared without regard to case.
_PDS3_LABEL_SUFFIX = '.lbl'

#: The suffix of a PDS4 label beside the table it describes.
_PDS4_LABEL_SUFFIX = '.xml'

#: The suffix of a table whose first line names its columns rather than holding a row.
_CSV_SUFFIX = '.csv'


class PrimaryIndexError(Exception):
    """A bundle's primary index files cannot be located; the message says why."""


@dataclass(frozen=True)
class PrimaryIndexes:
    """Where one bundle's primary index files are.

    Attributes:
        searched: Every directory looked in, in the order they were searched; the import
            also looks for a bundle's other index files there.
        files: The primary index files found, in name order, all in the first directory
            that held any; none when no directory held one.
    """

    searched: list[str]
    files: list[str]


def locate(bundle_id: str, vol_info: BundleInfo) -> PrimaryIndexes:
    """Find a bundle's primary index files.

    They are looked for in the bundle's metadata directories, and for PDS3 its own
    ``index`` directory as well, under the names ``vol_info`` gives. Every file found in
    the first directory that has one is returned; later directories are not searched, so
    a bundle whose indexes are split across directories has only the first group.

    Parameters:
        bundle_id: The bundle.
        vol_info: Its `opus_import.config_bundle_info` entry, which has a primary index.

    Returns:
        The directories searched and the files found.

    Raises:
        PrimaryIndexError: If the entry names a PDS version other than 3 or 4, or the
            holdings do not hold the bundle as a bundle.
    """
    if vol_info['pds_version'] == 3:
        bundle_pdsfile = pdsfile.pds3file.Pds3File.from_path(bundle_id)
    elif vol_info['pds_version'] == 4:
        # This works fine for Uranus Occs Earthbased, where bundleset and bundle have
        # different names
        bundle_pdsfile = pdsfile.pds4file.Pds4File.from_path(bundle_id)
        if not bundle_pdsfile.is_bundle:
            # Handle the case where the bundleset and bundle have the same name, in
            # which case PdsFile prefers the bundleset, but we want to prefer the bundle
            bundle_pdsfile = pdsfile.pds4file.Pds4File.from_path(f'bundles/{bundle_id}/{bundle_id}')
    else:
        raise PrimaryIndexError(f'BUNDLE_INFO has illegal PDS version for {bundle_id}!')

    if not bundle_pdsfile.is_bundle:
        raise PrimaryIndexError(f'{bundle_id} is not a bundle!')

    primary_index = vol_info['primary_index']
    # An entry has a primary index exactly when it has an instrument class, and callers
    # pass only bundles OPUS imports.
    assert primary_index is not None
    names = {name.replace('<BUNDLE>', bundle_id) for name in primary_index}

    # These are the metadata directories
    searched = bundle_pdsfile.associated_abspaths('metadata', must_exist=True)
    if vol_info['pds_version'] == 3:
        # These are the plain <volume>/index directories for PDS3 volumes that
        # don't have a separate metadata directory
        bundle_abspath = bundle_pdsfile.abspath
        # A pdsfile below a merged or category-level directory has no absolute path, and
        # neither is a bundle -- which the check above has already required this to be.
        assert bundle_abspath is not None
        searched.append(import_util.safe_join(bundle_abspath, 'INDEX'))
        searched.append(import_util.safe_join(bundle_abspath, 'index'))

    for path in searched:
        if not os.path.exists(path):
            continue
        # Sorted, because a bundle can have several primary indexes -- COCIRS_1xxx has
        # one per cube geometry -- and observation ids are handed out in the order rows
        # are read. Taking them in `os.listdir` order would make every id depend on how
        # one filesystem happened to enumerate one directory.
        found = [
            import_util.safe_join(path, basename)
            for basename in sorted(os.listdir(path))
            if basename in names
        ]
        if found:
            return PrimaryIndexes(searched, found)
    return PrimaryIndexes(searched, [])


def declared_rows(index_file: str) -> int | None:
    """Return how many rows a primary index file's label declares.

    A PDS3 index file is its label, whose ``ROWS`` gives the count; where it declares
    more than one table, the largest. A PDS4 index's label is the ``.xml`` file beside
    it, whose ``<records>`` gives the count. The PDS4 index files OPUS reads have no
    label, so for one without, the table's own lines are counted, less the header line
    of a ``.csv`` file.

    Parameters:
        index_file: The path `locate` found.

    Returns:
        The row count, or None when a label declares none.
    """
    path = Path(index_file)
    if path.suffix.lower() == _PDS3_LABEL_SUFFIX:
        counts = _PDS3_ROWS.findall(path.read_text(encoding='latin-1'))
        return max(int(count) for count in counts) if counts else None
    label = path.with_suffix(_PDS4_LABEL_SUFFIX)
    if label.exists():
        counts = _PDS4_RECORDS.findall(label.read_text(encoding='utf-8'))
        return max(int(count) for count in counts) if counts else None
    with path.open('rb') as table:
        lines = sum(1 for line in table if line.strip())
    return max(0, lines - 1) if path.suffix.lower() == _CSV_SUFFIX else lines
