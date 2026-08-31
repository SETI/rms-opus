"""Record one bundle into the fixture: its sampled metadata and its expected products.

What an observation's product set is cannot be derived -- per-bundle rules generate
candidates and existence filtering decides which of them survive -- so it is recorded from
the real holdings once, and the suite then holds the import to it. That recording is this
module's other half; the first half is the subsetted metadata the import reads.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

from pdsfile.pds3file import Pds3File
from pdsfile.pds4file import Pds4File

from import_tests.tools import fixture_layout, metadata_subsets, shelf_capture
from import_tests.tools.shelf_capture import ancestor_keys, split_logical_path

if TYPE_CHECKING:
    from collections.abc import Sequence

    from import_tests.tools.holdings_survey import BundleLocation, RegistryEntry
    from opus_import.context import ImportContext
    from opus_import.obs.obs_base import ObsBase

#: The categories the fixture never carries a product from. The documents tree has no
#: shelves at all, and a versioned bundle set is a superseded copy whose products would
#: ship a whole extra tree with no test going red if it broke.
_DOCUMENTS_CATEGORY = 'documents'

#: The category a bundle's index tables live in.
_METADATA_CATEGORY = 'metadata'
_VERSIONED_BUNDLESET_RE = re.compile(r'_v\d+(\.\d+)*$')

#: How the two holdings roots are spelled at the front of an expected-products path.
ROOT_NAME_FOR_VERSION = {3: fixture_layout.PDS3_ROOT_NAME, 4: fixture_layout.PDS4_ROOT_NAME}


class BundleSkippedError(Exception):
    """A candidate bundle cannot be recorded, so the next one of its type is tried."""


@dataclass
class BundleRecord:
    """Everything the recorder learned about one fixture bundle.

    Attributes:
        entry: The registry entry the bundle represents.
        location: Where the bundle's files are in the holdings.
        checked_in: The fixture files written for this bundle, as paths under the
            fixture root.
        metadata_basenames: The base names checked in under the bundle's metadata
            directory, which the metadata info shelf has to list in full.
        products: The expected products, as (root-relative path, size in bytes) pairs.
        shelf_keys: The interior paths each shelf has to carry, keyed by (regime,
            category, bundle set, bundle).
        observation_count: How many observations the sampled rows produced.
        uncovered: The (column, class) pairs the row cap left uncovered.
        unshelvable: The bundles whose products pdsfile cannot address a shelf entry
            for, and which the fixture therefore drops.
    """

    entry: RegistryEntry
    location: BundleLocation
    checked_in: list[Path] = field(default_factory=list)
    metadata_basenames: set[str] = field(default_factory=set)
    products: dict[str, int] = field(default_factory=dict)
    shelf_keys: dict[tuple[int, str, str, str], set[str]] = field(default_factory=dict)
    observation_count: int = 0
    uncovered: set[tuple[str, str]] = field(default_factory=set)
    unshelvable: set[str] = field(default_factory=set)


def _fixture_metadata_dir(entry: RegistryEntry, location: BundleLocation) -> Path:
    """Return where a bundle's metadata files are checked in.

    The fixture mirrors the holdings' own layout below ``metadata/``, because pdsfile
    discovers a bundle's metadata by walking that layout: a PDS4 bundle sharing its name
    with its bundle set keeps its files one level higher than a PDS3 volume does.

    Parameters:
        entry: The registry entry the bundle represents, which says which regime it is.
        location: Where the bundle's files are in the holdings.

    Returns:
        The directory under the fixture root.
    """
    root = fixture_layout.PDS3_METADATA if entry.pds_version == 3 else fixture_layout.PDS4_METADATA
    return root / location.metadata_relpath


def _fixture_volume_index_dir(location: BundleLocation) -> Path:
    """Return where a PDS3 volume's own index directory is checked in.

    Parameters:
        location: Where the volume's files are in the holdings.

    Returns:
        The directory under the fixture root.
    """
    return (
        fixture_layout.PDS3_VOLUME_INDEX
        / location.bundleset
        / location.bundle_id
        / fixture_layout.VOLUME_INDEX_DIRNAME
    )


def _instrument_for(
    ctx: ImportContext, entry: RegistryEntry, location: BundleLocation, metadata: dict[str, Any]
) -> ObsBase:
    """Build the obs class instance the import would build for this bundle.

    Parameters:
        ctx: A context carrying the pipeline's default arguments.
        entry: The registry entry.
        location: The bundle.
        metadata: The metadata dictionary the instance reads, shared with the caller.

    Returns:
        The instance, which the caller drives by writing into ``metadata``.
    """
    instrument_class = entry.info['instrument_class']
    assert instrument_class is not None
    return instrument_class(ctx, bundle=location.bundle_id, metadata=metadata)


def _record_products(
    record: BundleRecord, instrument: ObsBase, metadata: dict[str, Any], row: dict[str, Any]
) -> None:
    """Add one observation's products to a bundle's record.

    Parameters:
        record: The record to add to.
        instrument: The obs class instance for this bundle.
        metadata: The metadata dictionary the instance reads.
        row: The primary index row to record.

    Raises:
        BundleSkippedError: If the row's file specification does not resolve to a PDS file,
            which is what the import would report as an error.
    """
    metadata['index_row'] = row
    for phase_name in instrument.phase_names:
        metadata['phase_name'] = phase_name
        filespec = instrument.primary_filespec
        if filespec is None:
            continue
        pds_version = record.entry.pds_version
        file_class = Pds3File if pds_version == 3 else Pds4File
        try:
            pdsf = file_class.from_filespec(filespec, fix_case=True)
        except (KeyError, ValueError) as exc:
            raise BundleSkippedError(f'Cannot resolve filespec "{filespec}": {exc}') from exc
        record.observation_count += 1
        for sublists in pdsf.opus_products().values():
            for sublist in sublists:
                for product in sublist:
                    _record_one_product(record, product)
    metadata['phase_name'] = None


def _record_one_product(record: BundleRecord, product: Any) -> None:
    """Add one product file to a bundle's record, unless it is a family the fixture drops.

    Parameters:
        record: The record to add to.
        product: The `pdsfile.pdsfile.PdsFile` the product enumeration returned.
    """
    logical_path = product.logical_path
    try:
        category, bundleset, bundle, key = split_logical_path(logical_path)
    except ValueError:
        # A path with no bundle is a documents-tree path, which the fixture drops.
        return
    if category == _DOCUMENTS_CATEGORY:
        return
    if _VERSIONED_BUNDLESET_RE.search(bundleset):
        return
    if not _is_shelvable(product):
        record.unshelvable.add(f'{category}/{bundleset}/{bundle}')
        return
    pds_version = 4 if isinstance(product, Pds4File) else 3
    root_name = ROOT_NAME_FOR_VERSION[pds_version]
    record.products[f'{root_name}/{logical_path}'] = product.size_bytes
    shelf_key = (pds_version, category, bundleset, bundle)
    record.shelf_keys.setdefault(shelf_key, set()).update(ancestor_keys(key))


def _is_shelvable(product: Any) -> bool:
    """Return whether pdsfile can read this file's information out of a shelf.

    The built tree holds no data files, so every value the import stores about a product
    has to come from a shelf. pdsfile addresses an info shelf by the bundle name it
    parses out of the path, and there are directories it does not parse one from -- a
    PDS4 bundle set's ``_support`` directory among them -- so a file inside one has no
    shelf to be looked up in whatever the fixture ships. Recording such a product would
    make the run crash trying to size a file that is not there.

    Parameters:
        product: The `pdsfile.pdsfile.PdsFile` the product enumeration returned.

    Returns:
        True if the file's own shelf lookup resolves.
    """
    try:
        product.shelf_path_and_key('info')
    except (KeyError, ValueError):
        return False
    return True


def _selections(
    instrument: ObsBase,
    metadata: dict[str, Any],
    rows: Sequence[dict[str, Any]],
    kept: Sequence[int],
) -> set[str]:
    """Return the keys the import looks each observation up by in an index shelf.

    Parameters:
        instrument: The obs class instance for this bundle.
        metadata: The metadata dictionary the instance reads, updated per row here.
        rows: Every row of the primary index.
        kept: The row numbers to take observations from.

    Returns:
        One key per observation: its primary file specification's base name with the
        extension removed, which is what ``get_opus_products_rows_for_filespec`` looks
        up.
    """
    found: set[str] = set()
    for row_no in kept:
        metadata['index_row'] = rows[row_no]
        for phase_name in instrument.phase_names:
            metadata['phase_name'] = phase_name
            filespec = instrument.primary_filespec
            if filespec is not None:
                found.add(filespec.split('/')[-1].split('.')[0])
    metadata['phase_name'] = None
    return found


def _extend_with_row_file_rows(
    location: BundleLocation, table: str, kept: set[int], selections: set[str]
) -> set[int]:
    """Add the rows an index shelf maps a set of selections to.

    The import lists an index among an observation's products only if the index's shelf
    carries that observation's key, and the key is not always the row's own file name --
    a Voyager occultation index row for a calibration file carries the profile's key. So
    which rows the fixture has to keep is read from the production shelf rather than
    guessed from the rows.

    Parameters:
        location: The bundle.
        table: The index table's base name without its extension.
        kept: The rows already chosen.
        selections: The observations' keys.

    Returns:
        The rows to keep.
    """
    shelf_path = shelf_capture.index_shelf_path(
        location.root, _METADATA_CATEGORY, location.bundleset, location.bundle_id, table
    )
    return kept | shelf_capture.index_shelf_rows(shelf_path, selections)


def record_bundle(
    ctx: ImportContext, entry: RegistryEntry, location: BundleLocation, *, cap: int
) -> BundleRecord:
    """Sample one bundle's indexes, write the fixture files, and record its products.

    Parameters:
        ctx: A context carrying the pipeline's default arguments.
        entry: The registry entry the bundle represents.
        location: The bundle to record.
        cap: The most rows to keep from each index file.

    Returns:
        What was recorded.

    Raises:
        BundleSkippedError: If the bundle has no primary index where the import looks
            for one, if an index cannot be read or holds no rows, or if an observation's
            file specification does not resolve to a PDS file. The caller then tries the
            next bundle of the same type.
    """
    index_files = metadata_subsets.primary_index_files(entry, location)
    if len(index_files) == 0:
        raise BundleSkippedError('No primary index file where the import looks for one')

    in_metadata_dir = index_files[0].parent in location.metadata_dirs
    if in_metadata_dir:
        index_destination = _fixture_metadata_dir(entry, location)
    else:
        index_destination = _fixture_volume_index_dir(location)

    record = BundleRecord(entry=entry, location=location)
    metadata: dict[str, Any] = {
        'phase_name': None,
        'temporal_camera': entry.info['temporal_camera'],
    }
    instrument = _instrument_for(ctx, entry, location, metadata)

    phase_keys: set[str] = set()
    plain_keys: set[str] = set()
    selections: set[str] = set()
    resolve = entry.info['validate_index_rows']
    for index_file in index_files:
        try:
            subset = metadata_subsets.sample_index(
                ctx,
                index_file,
                entry.pds_version,
                cap=cap,
                instrument=instrument if resolve else None,
                metadata=metadata if resolve else None,
            )
        except ValueError as exc:
            raise BundleSkippedError(str(exc)) from exc
        metadata['index'] = subset.rows
        record.uncovered |= subset.uncovered

        # The observations come from the sampled rows; the rows the fixture keeps are
        # those plus the ones their index shelf keys point at, so that the row-file check
        # finds each observation in the index it lists among its products.
        selections |= _selections(instrument, metadata, subset.rows, subset.kept)
        if in_metadata_dir:
            subset.kept = sorted(
                _extend_with_row_file_rows(location, index_file.stem, set(subset.kept), selections)
            )

        written = metadata_subsets.write_index_subset(subset, index_destination)
        record.checked_in.extend(written)
        if in_metadata_dir:
            record.metadata_basenames.update(path.name for path in written)

        # The import resolves ambiguous rows over the subsetted table, not over the whole
        # index, so the observations are recomputed the same way here.
        observation_rows = _observation_rows(instrument, metadata, subset, resolve=resolve)
        new_phase_keys, new_plain_keys = metadata_subsets.observation_keys(
            instrument, metadata, subset.rows, observation_rows
        )
        phase_keys |= new_phase_keys
        plain_keys |= new_plain_keys
        for row_no in observation_rows:
            _record_products(record, instrument, metadata, subset.rows[row_no])

    _record_associated(ctx, record, instrument, location, phase_keys, plain_keys)
    _record_extra_index_products(record, location, selections)
    return record


def _observation_rows(
    instrument: ObsBase,
    metadata: dict[str, Any],
    subset: metadata_subsets.IndexSubset,
    *,
    resolve: bool,
) -> list[int]:
    """Return the rows of a subsetted index the import will turn into observations.

    Parameters:
        instrument: The obs class instance for this bundle.
        metadata: The metadata dictionary the instance reads.
        subset: The index and the rows the fixture keeps.
        resolve: True for a bundle whose index carries several rows per observation.

    Returns:
        The row numbers, in the original index's numbering.
    """
    if not resolve:
        return list(subset.kept)
    subset_rows = [subset.rows[row_no] for row_no in subset.kept]
    surviving = metadata_subsets.valid_row_numbers(instrument, metadata, subset_rows)
    metadata['index'] = subset.rows
    return [subset.kept[position] for position in surviving]


def _record_extra_index_products(
    record: BundleRecord, location: BundleLocation, selections: set[str]
) -> None:
    """Check in the metadata index files the observations name as products.

    A bundle's expected products can include index tables the import never reads as
    metadata -- Hubble's file index, Voyager's image index -- and the row-file check
    still consults their shelves. They are subset to the rows their production shelf maps
    the observations' keys to, so the shelf built over the subset carries exactly those
    keys.

    Parameters:
        record: The bundle's record, whose checked-in files are extended.
        location: The bundle.
        selections: The observations' index-shelf keys.
    """
    if record.entry.pds_version != 3:
        return
    destination = _fixture_metadata_dir(record.entry, location)
    prefix = (
        f'{ROOT_NAME_FOR_VERSION[3]}/{_METADATA_CATEGORY}/'
        f'{location.bundleset}/{location.bundle_id}/'
    )
    for product in sorted(record.products):
        if not product.startswith(prefix):
            continue
        name = product[len(prefix) :]
        if '/' in name:
            continue
        if name in record.metadata_basenames or not name.lower().endswith(('.tab', '.csv')):
            continue
        table = name.rsplit('.', 1)[0]
        rows = shelf_capture.index_shelf_rows(
            shelf_capture.index_shelf_path(
                location.root,
                _METADATA_CATEGORY,
                location.bundleset,
                location.bundle_id,
                table,
            ),
            selections,
        )
        if len(rows) == 0:
            continue
        label = location.metadata_dir / f'{table}.lbl'
        if not label.is_file():
            continue
        subset = metadata_subsets.IndexSubset(
            source=label,
            table_name=metadata_subsets.table_name_for_label(label, 3),
            rows=[],
            kept=sorted(rows),
        )
        written = metadata_subsets.write_index_subset(subset, destination)
        record.checked_in.extend(written)
        record.metadata_basenames.update(path.name for path in written)


def _record_associated(
    ctx: ImportContext,
    record: BundleRecord,
    instrument: ObsBase,
    location: BundleLocation,
    phase_keys: set[str],
    plain_keys: set[str],
) -> None:
    """Subset every metadata file the import reads beside the primary index.

    Parameters:
        ctx: A context carrying the pipeline's default arguments.
        record: The record to add the written files to.
        instrument: The obs class instance for this bundle.
        location: The bundle.
        phase_keys: The keys the geometry and inventory files are keyed by.
        plain_keys: The keys the supplemental index is keyed by.

    Raises:
        BundleSkippedError: If an associated file cannot be read.
    """
    if record.entry.pds_version != 3:
        # The files the import reads beside a primary index are PDS3 labels; the PDS4
        # bundles carry an index CSV and nothing else yet.
        return
    destination = _fixture_metadata_dir(record.entry, location)
    for label_path in metadata_subsets.associated_metadata_files(
        location.metadata_dir, location.bundle_id
    ):
        upper = label_path.name.upper()
        with_phase = metadata_subsets.SUPPLEMENTAL_MARKER not in upper
        keys = phase_keys if with_phase else plain_keys
        table_name = metadata_subsets.table_name_for_label(label_path, 3)
        assert table_name is not None
        if upper.endswith('INVENTORY.LBL'):
            rows = metadata_subsets.read_inventory_rows(label_path.parent / table_name)
        else:
            try:
                rows, _label = metadata_subsets.read_index(ctx, label_path, 3)
            except ValueError as exc:
                raise BundleSkippedError(str(exc)) from exc
        kept = metadata_subsets.select_associated_rows(
            instrument, rows, keys, with_phase=with_phase
        )
        subset = metadata_subsets.IndexSubset(
            source=label_path, table_name=table_name, rows=rows, kept=kept
        )
        written = metadata_subsets.write_index_subset(subset, destination)
        record.checked_in.extend(written)
        record.metadata_basenames.update(path.name for path in written)


def write_expected_products(record: BundleRecord, destination_dir: Path) -> Path:
    """Write one bundle's expected products, sorted, one file per line.

    Parameters:
        record: The bundle's record.
        destination_dir: The expected-products directory. It is created.

    Returns:
        The file written.
    """
    destination_dir.mkdir(parents=True, exist_ok=True)
    target = destination_dir / f'{record.location.bundle_id}.tsv'
    lines = [f'{path}\t{record.products[path]}' for path in sorted(record.products)]
    target.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    return target
