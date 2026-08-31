"""Read one bundle's index files and cut them down to a sampled set of observations.

The import is index-driven: every value it computes comes from a primary index and the
summary, inventory and supplemental files beside it, cross-referenced by primary
filespec. So the fixture's content is those files with rows removed, and the rows that
survive in one file have to be exactly the rows that survive in the others.

How an associated row is keyed to a primary row is instrument-specific -- the files do
not agree on how they spell a file specification -- so this module asks the same obs
class the import asks, rather than guessing from column names.
"""

from __future__ import annotations

import csv
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal

from pdsfile.pds3file import Pds3File
from pdsfile.pds4file import Pds4File

from import_tests.tools import row_sampling, table_subsets
from opus_import import import_util

if TYPE_CHECKING:
    from collections.abc import Sequence

    from import_tests.tools.holdings_survey import BundleLocation, RegistryEntry
    from opus_import.context import ImportContext
    from opus_import.obs.obs_base import ObsBase

#: The three ways an associated metadata file's name ends. The import discovers these
#: files by listing the metadata directory and matching on the name alone.
_ASSOCIATED_SUFFIXES = ('SUMMARY.LBL', 'SUPPLEMENTAL_INDEX.LBL', 'INVENTORY.LBL')

#: A metadata file whose name contains this is a cumulative file covering the whole
#: bundle set, which the import skips.
_CUMULATIVE_MARKER = '999'

#: How a PDS3 label names the file holding its table: a caret keyword whose value is the
#: base name, sometimes inside a parenthesised pair with a record offset.
_POINTER_RE = re.compile(rb'(?m)^\^\w+\s*=\s*\(?\s*"(?P<name>[^"]+\.(?i:tab|csv))"')

#: How a supplemental index is told apart from the files keyed by phase. A supplemental
#: row is keyed without a phase; a geometry or inventory row is keyed with one.
SUPPLEMENTAL_MARKER = 'SUPPLEMENTAL_INDEX'


@dataclass
class IndexSubset:
    """One index file and the rows the fixture keeps from it.

    Attributes:
        source: The file the rows were read from -- a label for PDS3, the CSV itself
            for PDS4.
        table_name: The base name of the table file the label describes, or None when
            the source is the table.
        rows: Every row the file holds.
        kept: The row numbers the fixture keeps, ascending.
        uncovered: The (column, class) pairs the kept rows do not cover, which is what
            the row cap cost this file.
    """

    source: Path
    table_name: str | None
    rows: list[dict[str, Any]]
    kept: list[int]
    uncovered: set[tuple[str, str]] = field(default_factory=set)


def read_index(
    ctx: ImportContext, path: Path, pds_version: Literal[3, 4]
) -> tuple[list[dict[str, Any]], dict[str, Any] | None]:
    """Read an index file the way the import reads it.

    Parameters:
        ctx: A context whose arguments carry the pipeline's defaults.
        path: The PDS3 label, or the PDS4 CSV.
        pds_version: 3 or 4.

    Returns:
        The rows and, for PDS3, the label dictionary.

    Raises:
        ValueError: If the file could not be read, which the pipeline reports through
            the log and turns into a skipped bundle.
    """
    rows, label = import_util.safe_pdstable_read(ctx, str(path), pds_version)
    if rows is None:
        raise ValueError(f'Could not read index: {path}')
    return rows, label


def table_name_for_label(label_path: Path, pds_version: Literal[3, 4]) -> str | None:
    """Return the base name of the table file a PDS3 label describes.

    The name comes from the label's own pointer rather than from the label's file name
    with an extension swapped, because that is the name `pdstable` opens: the holdings
    sit on a case-insensitive filesystem where ``OBSINDEX.tab`` and ``OBSINDEX.TAB``
    are the same file, and the fixture is read back on one where they are not.

    Parameters:
        label_path: The label file.
        pds_version: 3 or 4. A PDS4 index has no label, so the answer is None.

    Returns:
        The table's base name, or None for PDS4.

    Raises:
        ValueError: If the label names no table file, or names one that is not there.
    """
    if pds_version == 4:
        return None
    match = _POINTER_RE.search(label_path.read_bytes())
    if match is None:
        raise ValueError(f'{label_path} carries no table pointer')
    name = match.group('name').decode('ascii')
    beside = {path.name.lower() for path in label_path.parent.iterdir()}
    if name.lower() not in beside:
        raise ValueError(f'{label_path} points at {name}, which is not beside it')
    return name


def primary_index_files(entry: RegistryEntry, location: BundleLocation) -> list[Path]:
    """Return the bundle's primary index files, from the first directory holding any.

    The import searches the metadata directory first and then, for PDS3, the volume's
    own index directory, and imports every index it finds in the first directory that
    has one.

    Parameters:
        entry: The registry entry the bundle belongs to.
        location: Where the bundle's files are.

    Returns:
        The matching files, sorted by name. Empty if no directory holds one.
    """
    names = entry.info['primary_index']
    assert names is not None
    wanted = {name.replace('<BUNDLE>', location.bundle_id) for name in names}

    search_dirs = list(location.metadata_dirs)
    if entry.pds_version == 3:
        volume_index_dir = location.volume_index_dir
        if volume_index_dir is not None:
            search_dirs.append(volume_index_dir)

    for directory in search_dirs:
        if not directory.is_dir():
            continue
        found = sorted(path for path in directory.iterdir() if path.name in wanted)
        if len(found) > 0:
            return found
    return []


def associated_metadata_files(metadata_dir: Path, bundle_id: str) -> list[Path]:
    """Return the metadata files beside a primary index that the import reads.

    Parameters:
        metadata_dir: The bundle's metadata directory.
        bundle_id: The bundle id, which every file the import reads starts with.

    Returns:
        The summary, supplemental-index and inventory labels, sorted by name.
    """
    if not metadata_dir.is_dir():
        return []
    found = []
    for path in sorted(metadata_dir.iterdir()):
        name = path.name
        if _CUMULATIVE_MARKER in name or not name.startswith(bundle_id):
            continue
        if name.upper().endswith(_ASSOCIATED_SUFFIXES):
            found.append(path)
    return found


def observation_keys(
    instrument: ObsBase,
    metadata: dict[str, Any],
    rows: Sequence[dict[str, Any]],
    kept: Sequence[int],
) -> tuple[set[str], set[str]]:
    """Return the keys the kept observations are found by in the associated files.

    Parameters:
        instrument: The obs class instance for this bundle, sharing ``metadata``.
        metadata: The metadata dictionary the instance reads, updated per row here.
        rows: Every row of the primary index.
        kept: The row numbers the fixture keeps.

    Returns:
        The phase-qualified keys, which the geometry and inventory files are keyed by,
        and the plain keys, which the supplemental index is keyed by. Both are
        upper-cased, as the import upper-cases them.
    """
    phase_keys: set[str] = set()
    plain_keys: set[str] = set()
    for row_no in kept:
        metadata['index_row'] = rows[row_no]
        metadata['phase_name'] = None
        filespec = instrument.primary_filespec
        if filespec is not None:
            plain_keys.add(instrument.convert_filespec_from_lbl(filespec).upper())
        for phase_name in instrument.phase_names:
            metadata['phase_name'] = phase_name
            qualified = instrument.primary_filespec_from_index_row(
                rows[row_no], convert_lbl=True, add_phase_from_inst=True
            )
            if qualified is not None:
                phase_keys.add(qualified.upper())
    metadata['phase_name'] = None
    return phase_keys, plain_keys


def _associated_row_key(
    instrument: ObsBase, row: dict[str, Any], *, with_phase: bool
) -> str | None:
    """Return the key one associated metadata row is cross-referenced by.

    Parameters:
        instrument: The obs class instance for this bundle.
        row: The associated file's row.
        with_phase: True for a geometry or inventory row, whose key carries the phase
            the row itself names.

    Returns:
        The upper-cased key, or None for a row that names no file.
    """
    key = instrument.primary_filespec_from_index_row(
        row, convert_lbl=True, add_phase_from_row=with_phase
    )
    if key is None:
        return None
    return key.upper()


def read_inventory_rows(csv_path: Path) -> list[dict[str, Any]]:
    """Read an inventory CSV the way the import reads it.

    The inventory has no fixed-length records, so `pdstable` cannot read it: the import
    parses the CSV itself, and each row names a bundle, a file and the targets in the
    field of view.

    Parameters:
        csv_path: The inventory CSV.

    Returns:
        One dictionary per line, in file order.
    """
    rows = []
    with csv_path.open(encoding='utf-8', newline='') as handle:
        for csv_row in csv.reader(handle):
            if len(csv_row) > 2 and csv_row[2].count('-') > 1:
                bundle, filespec, ring_obs_id, *targets = csv_row
            else:
                ring_obs_id = ''
                bundle, filespec, *targets = csv_row
            if len(targets) == 1:
                targets = targets[0].split(',')
            row: dict[str, Any] = {
                'BUNDLE_ID': bundle.strip(),
                'FILE_SPECIFICATION_NAME': filespec.strip(),
                'TARGET_LIST': targets,
            }
            if len(ring_obs_id) > 0:
                row['OPUS_ID'] = ring_obs_id.strip()
            rows.append(row)
    return rows


def select_associated_rows(
    instrument: ObsBase,
    rows: Sequence[dict[str, Any]],
    keys: set[str],
    *,
    with_phase: bool,
) -> list[int]:
    """Return the rows of an associated file that describe the kept observations.

    Parameters:
        instrument: The obs class instance for this bundle.
        rows: The associated file's rows.
        keys: The keys the kept observations are found by.
        with_phase: True for a geometry or inventory file.

    Returns:
        The row numbers to keep, ascending. A surface geometry file contributes several
        rows per observation -- one per target -- and all of them are kept.
    """
    return [
        row_no
        for row_no, row in enumerate(rows)
        if _associated_row_key(instrument, row, with_phase=with_phase) in keys
    ]


def valid_row_numbers(
    instrument: ObsBase, metadata: dict[str, Any], rows: Sequence[dict[str, Any]]
) -> list[int]:
    """Return the rows of an index the import would keep, for a bundle that resolves them.

    Some bundles carry several index rows per observation -- a data file and the support
    files beside it -- and the import keeps the one whose file specification survives a
    round trip through the OPUS id, dropping the rest. Sampling before that resolution
    would put rows in the fixture that the import then discards, and could leave an
    observation represented only by rows it discards, so the fixture is sampled from what
    survives.

    Parameters:
        instrument: The obs class instance for this bundle.
        metadata: The metadata dictionary the instance reads, updated per row here.
        rows: Every row of the primary index.

    Returns:
        The surviving row numbers, ascending.
    """
    by_opus_id: dict[str, list[int]] = {}
    valid = [True] * len(rows)
    for row_no, row in enumerate(rows):
        metadata['index_row'] = row
        opus_id = instrument.opus_id_from_index_row(row)
        if opus_id is None:
            valid[row_no] = False
            continue
        by_opus_id.setdefault(opus_id, []).append(row_no)

    for opus_id, row_nos in by_opus_id.items():
        if len(row_nos) == 1:
            continue
        for row_no in row_nos:
            valid[row_no] = False
        derived = _filespec_for_opus_id(opus_id)
        if derived is None:
            continue
        for row_no in row_nos:
            metadata['index_row'] = rows[row_no]
            original = instrument.primary_filespec_from_index_row(rows[row_no], convert_lbl=True)
            if original is None:
                continue
            if instrument.convert_filespec_from_lbl(original) in derived:
                valid[row_no] = True
    return [row_no for row_no, keep in enumerate(valid) if keep]


def _filespec_for_opus_id(opus_id: str) -> str | None:
    """Return the file an OPUS id names, asking both regimes in the import's order.

    Parameters:
        opus_id: The OPUS id.

    Returns:
        The absolute path, or None if neither regime can resolve the id.
    """
    for file_class in (Pds3File, Pds4File):
        try:
            abspath: str | None = file_class.from_opus_id(opus_id).abspath
        except (KeyError, ValueError):
            continue
        return abspath
    return None


def sample_index(
    ctx: ImportContext,
    path: Path,
    pds_version: Literal[3, 4],
    *,
    cap: int,
    instrument: ObsBase | None = None,
    metadata: dict[str, Any] | None = None,
) -> IndexSubset:
    """Read one primary index and choose the rows the fixture keeps from it.

    Parameters:
        ctx: A context whose arguments carry the pipeline's defaults.
        path: The PDS3 label, or the PDS4 CSV.
        pds_version: 3 or 4.
        cap: The most rows to keep.
        instrument: The obs class instance, for a bundle whose rows have to be resolved
            before they are sampled. None samples every row.
        metadata: The metadata dictionary that instance reads.

    Returns:
        The file, its rows, and the row numbers chosen.

    Raises:
        ValueError: If the index could not be read, has no rows at all, or has none the
            import would keep.
    """
    rows, _label = read_index(ctx, path, pds_version)
    if len(rows) == 0:
        raise ValueError(f'Index has no rows: {path}')
    if instrument is None or metadata is None:
        eligible = list(range(len(rows)))
    else:
        metadata['index'] = rows
        eligible = valid_row_numbers(instrument, metadata, rows)
    if len(eligible) == 0:
        raise ValueError(f"No row of {path} survives the import's own row resolution")
    candidates = [rows[row_no] for row_no in eligible]
    chosen = row_sampling.select_rows(candidates, cap=cap)
    kept = [eligible[position] for position in chosen]
    return IndexSubset(
        source=path,
        table_name=table_name_for_label(path, pds_version),
        rows=rows,
        kept=kept,
        uncovered=row_sampling.uncovered_classes(candidates, chosen),
    )


def write_index_subset(subset: IndexSubset, destination_dir: Path) -> list[Path]:
    """Write one index file's subset into the fixture.

    Parameters:
        subset: The index and the rows to keep.
        destination_dir: Where the files go. It is created.

    Returns:
        The files written.
    """
    destination_dir.mkdir(parents=True, exist_ok=True)
    if subset.table_name is None:
        target = destination_dir / subset.source.name
        target.write_bytes(table_subsets.subset_csv(subset.source.read_bytes(), subset.kept))
        return [target]
    table_subsets.write_subset(
        subset.source, destination_dir / subset.source.name, subset.table_name, subset.kept
    )
    return [destination_dir / subset.source.name, destination_dir / subset.table_name]
