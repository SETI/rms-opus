"""Turn real and freshly built pdsfile shelves into the fixture's text manifests.

PDS3 shelves are read straight out of the production holdings: they already carry the
checksums, sizes and image dimensions the import puts in ``obs_files``, so subsetting
them puts real values in the database for free. PDS4 holdings have no shelves yet, so the
recorder builds them with pdsfile's own maintenance tools in a scratch tree and subsets
the result the same way. Nothing is ever written into the holdings.

A shelf is subset to the products the fixture's observations actually name, plus every
directory above them, plus -- for a metadata shelf -- every file the fixture checks in,
because the import discovers a bundle's summary files by listing that directory through
the shelf.
"""

from __future__ import annotations

import os
import pickle
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from import_tests.tools.shelf_manifests import ManifestName

#: The maintenance tools that build a PDS4 bundle's shelves, in the only order that
#: works: the info shelf reads its digests out of the checksum file rather than
#: computing them, so the checksums have to exist first.
PDS4_SHELF_TOOLS = ('pds4checksums', 'pds4infoshelf', 'pds4linkshelf')

#: The tool that builds a PDS3 bundle's index shelves, one pickle per index table.
PDS3_INDEX_SHELF_TOOL = 'pdsindexshelf'

#: The task every one of those tools is asked to perform. Reinitialize rather than
#: initialize, so that a second recorder run over a scratch tree that still holds the
#: first run's staged copies rewrites the shelves instead of refusing to start.
SHELF_TOOL_TASK = '--reinitialize'

#: Shelf modification times are formatted in the local time zone, so an unpinned zone
#: makes the recorder's diff depend on which machine ran it and on the time of year.
SHELF_TOOL_TZ = 'UTC'


@dataclass
class ShelfSelection:
    """Which keys of one shelf the fixture keeps.

    Attributes:
        category: The holdings category the shelf covers.
        bundleset: The bundle set.
        bundle: The bundle.
        keys: The interior paths to keep, every ancestor directory included.
    """

    category: str
    bundleset: str
    bundle: str
    keys: set[str] = field(default_factory=set)


def split_logical_path(logical_path: str) -> tuple[str, str, str, str]:
    """Split a holdings-relative path into the four parts a shelf is addressed by.

    Parameters:
        logical_path: A path below a holdings root, such as
            ``volumes/COISS_2xxx/COISS_2111/data/1_1/N1_1.IMG``.

    Returns:
        The category, bundle set, bundle, and the interior path below the bundle, which
        is the empty string for the bundle directory itself.

    Raises:
        ValueError: If the path names no bundle, which a documents-tree path does.
    """
    parts = logical_path.strip('/').split('/')
    if len(parts) < 3:
        raise ValueError(f'Path names no bundle: {logical_path}')
    return parts[0], parts[1], parts[2], '/'.join(parts[3:])


def ancestor_keys(key: str) -> set[str]:
    """Return an interior path and every directory above it, the bundle included.

    Parameters:
        key: An interior path below a bundle.

    Returns:
        The key itself, each of its parent directories, and the empty string, which is
        how a shelf spells the bundle directory.
    """
    keys = {''}
    parts = key.split('/') if len(key) > 0 else []
    for depth in range(1, len(parts) + 1):
        keys.add('/'.join(parts[:depth]))
    return keys


def read_shelf(path: Path) -> dict[str, Any]:
    """Read a pickled shelf.

    Parameters:
        path: The shelf pickle.

    Returns:
        The dictionary it holds.
    """
    with path.open('rb') as handle:
        loaded = pickle.load(handle)
    if not isinstance(loaded, dict):
        raise ValueError(f'Shelf does not hold a dictionary: {path}')
    return loaded


def subset_shelf(shelf: dict[str, Any], keys: set[str]) -> dict[str, Any]:
    """Return the entries of a shelf whose keys the fixture keeps.

    A key the shelf does not carry is dropped rather than invented: the shelf is the
    record of what the holdings hold, and the caller's key set comes from a different
    question.

    Parameters:
        shelf: The whole shelf.
        keys: The keys to keep.

    Returns:
        The kept entries.
    """
    return {key: shelf[key] for key in keys if key in shelf}


def capture_manifest(
    root: Path, selection: ShelfSelection, shelf_type: str
) -> tuple[ManifestName, dict[str, Any]] | None:
    """Read one shelf out of a holdings tree and subset it.

    Parameters:
        root: The holdings root the shelf lives under.
        selection: Which shelf, and which keys of it to keep.
        shelf_type: ``info`` or ``link``.

    Returns:
        The manifest's name and its entries, or None if that shelf does not exist --
        the holdings carry an ``_infoshelf-previews`` but no ``_linkshelf-previews``,
        and a category with no shelf of one kind is not an error.
    """
    name = ManifestName(
        shelf_type=shelf_type,
        category=selection.category,
        bundleset=selection.bundleset,
        bundle=selection.bundle,
    )
    shelf_path = root / name.shelf_relpath
    if not shelf_path.is_file():
        return None
    return name, subset_shelf(read_shelf(shelf_path), selection.keys)


def capture_index_manifests(
    root: Path, category: str, bundleset: str, bundle: str
) -> list[tuple[ManifestName, dict[str, Any]]]:
    """Read every index shelf of one bundle, whole.

    An index shelf maps an observation's selection key to its row numbers, and the
    import consults it to decide whether an index file describes a given observation.
    It is built over the already-subsetted tables, so it is kept whole rather than
    filtered: every key in it is a row the fixture has.

    Parameters:
        root: The holdings root the shelves live under.
        category: The category the index tables belong to, which is ``metadata``.
        bundleset: The bundle set.
        bundle: The bundle.

    Returns:
        One (name, entries) pair per index table, sorted by table name. Empty if the
        bundle has no index shelf directory.
    """
    shelf_dir = root / f'_indexshelf-{category}' / bundleset / bundle
    if not shelf_dir.is_dir():
        return []
    captured = []
    for shelf_path in sorted(shelf_dir.glob('*.pickle')):
        name = ManifestName(
            shelf_type='index',
            category=category,
            bundleset=bundleset,
            bundle=bundle,
            table=shelf_path.stem,
        )
        captured.append((name, read_shelf(shelf_path)))
    return captured


def matching_index_key(keys_by_lower: dict[str, str], selection: str) -> str | None:
    """Return the index-shelf key one selection resolves to, in pdsfile's own order.

    pdsfile takes an exact match first; failing that, the longest key the selection
    starts with -- a Voyager image index is keyed by the image number while the
    observation's file name carries a ``_RAW`` suffix -- and failing that, the single key
    that starts with the selection. An ambiguous selection resolves to nothing, which is
    what pdsfile reports as an error rather than a choice.

    The first step cannot change an answer the second would give: a key is the longest
    thing the selection starting with it can start with, so an exact match is what the
    second step would return anyway. It is kept because this function exists to mirror
    pdsfile's order, not to be the shortest expression of pdsfile's result, and no test
    here can tell the two apart.

    Parameters:
        keys_by_lower: The shelf's keys, each under its own lower-cased form.
        selection: The key to look up, lower-cased.

    Returns:
        The shelf's own spelling of the key, or None if nothing resolves.
    """
    if selection in keys_by_lower:
        return keys_by_lower[selection]
    inside = [key for key in keys_by_lower if selection.startswith(key)]
    if len(inside) > 0:
        return keys_by_lower[max(inside, key=len)]
    starting = [key for key in keys_by_lower if key.startswith(selection)]
    if len(starting) == 1:
        return keys_by_lower[starting[0]]
    return None


def index_shelf_rows(shelf_path: Path, selections: set[str]) -> set[int]:
    """Return the rows of an index that a set of selection keys names.

    An index shelf maps the key an observation is looked up by to the rows of that index
    describing it, and the key is not always the same string as the row's own file name:
    a Voyager occultation index row for a calibration file carries the profile's key, and
    a Voyager image index is keyed by the image number rather than by the file. That is
    why the fixture cannot decide which rows to keep from the rows alone.

    Parameters:
        shelf_path: The production index shelf for one table.
        selections: The keys to look up, resolved as pdsfile resolves them.

    Returns:
        The row numbers, empty when the shelf resolves none of the keys or is not there.
    """
    if not shelf_path.is_file():
        return set()
    shelf = read_shelf(shelf_path)
    keys_by_lower = {key.lower(): key for key in shelf}
    rows: set[int] = set()
    for selection in selections:
        key = matching_index_key(keys_by_lower, selection.lower())
        if key is None:
            continue
        value = shelf[key]
        rows.update(value if isinstance(value, (list, tuple)) else [value])
    return rows


def index_shelf_path(root: Path, category: str, bundleset: str, bundle: str, table: str) -> Path:
    """Return where one index table's shelf sits under a holdings root.

    Parameters:
        root: The holdings root.
        category: The category the table belongs to, which is ``metadata``.
        bundleset: The bundle set.
        bundle: The bundle.
        table: The table's base name without its extension.

    Returns:
        The shelf pickle's path, which need not exist.
    """
    return root / f'_indexshelf-{category}' / bundleset / bundle / f'{table}.pickle'


def run_shelf_tool(tool: str, target: Path, log_root: Path) -> None:
    """Run one pdsfile maintenance tool over a staged tree.

    The tool's log root is pointed into the scratch tree and the time zone is pinned, so
    nothing the run writes lands outside the scratch directory and the modification
    times it formats do not depend on the machine.

    Parameters:
        tool: The console script to run, one of `PDS4_SHELF_TOOLS` or
            `PDS3_INDEX_SHELF_TOOL`.
        target: The staged bundle directory to build shelves for.
        log_root: The directory the tool writes its logs under. It is created.

    Raises:
        FileNotFoundError: If the tool is not installed. The dependency floor still
            admits a released rms-pdsfile, which ships none of these console scripts, so
            this says what to install rather than failing on an opaque exec error.
        subprocess.CalledProcessError: If the tool reports a failure.
    """
    if shutil.which(tool) is None:
        raise FileNotFoundError(
            f'{tool} is not on PATH. The PDS4 shelf builders are console scripts of the '
            'pdsfile rewrite, which the released rms-pdsfile does not provide: install '
            '"rms-pdsfile @ git+https://github.com/SETI/rms-pdsfile@rewrite" and re-run.'
        )
    log_root.mkdir(parents=True, exist_ok=True)
    environment = dict(os.environ)
    environment['TZ'] = SHELF_TOOL_TZ
    environment['PDS_LOG_ROOT'] = str(log_root)
    subprocess.run(
        [tool, SHELF_TOOL_TASK, str(target), '--log', str(log_root), '--quiet'],
        check=True,
        env=environment,
    )


def stage_copy(source: Path, destination: Path, *, refresh: bool = False) -> None:
    """Copy a directory tree into the scratch tree, by value.

    Plain copies rather than links: the recorder has to run on Windows, and the scratch
    tree may sit on a different filesystem from the holdings.

    Parameters:
        source: The directory to copy.
        destination: Where it goes. Its parent is created.
        refresh: True to replace an existing destination, which is what a tree the
            recorder itself just wrote needs -- reusing the previous run's copy would
            build shelves over files that are no longer the fixture's. False keeps an
            existing copy, which is what the gigabyte-scale PDS4 bundles want, since
            they come from the holdings and do not change between runs.
    """
    if destination.exists():
        if not refresh:
            return
        shutil.rmtree(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source, destination)
