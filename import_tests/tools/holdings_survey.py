"""Which bundle each registered volume type is represented by, and where its files are.

The fixture carries one bundle per entry of `opus_import.config_bundle_info.BUNDLE_INFO`
that OPUS actually imports, so a newly registered type fails the suite rather than
quietly going untested -- the recorder records it as an exclusion with a reason, and
`import_tests.test_expected_products` is what refuses to accept one it cannot match to a
registered type. Which bundle is a rule, not a list: the entry's own pattern is
matched against the holdings, the bundles the self-hosted integration run already imports
are dropped, and the middle of what remains is taken. A volume set's early volumes are
its least representative -- pre-encounter, before the instrument has anything to look at
-- so a first-volume rule would systematically pick the worst one.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Literal

from pdsfile.pds3file import Pds3File
from pdsfile.pds4file import Pds4File
from pdsfile.pdsfile import PdsFile

from opus_import.config_bundle_info import BUNDLE_INFO

if TYPE_CHECKING:
    from collections.abc import Iterable, Sequence

    from opus_import.config_bundle_info import BundleInfo

#: A bundle set whose name ends this way is a superseded version of another one. The
#: holdings carry both single-digit forms (``COISS_2xxx_v2``) and dotted ones
#: (``GO_0xxx_v4.1``), and a fixture that shipped one would import products no test
#: expects.
VERSIONED_BUNDLESET_RE = re.compile(r'_v\d+(\.\d+)*$')

#: Where each regime keeps its bundles, relative to its holdings root.
PDS3_BUNDLES_DIRNAME = 'volumes'
PDS4_BUNDLES_DIRNAME = 'bundles'

#: The in-volume index directory names a PDS3 volume can use, in the order the import
#: searches them.
VOLUME_INDEX_DIRNAMES = ('INDEX', 'index')

#: The shell script whose bundle list the fixture avoids, relative to the repository
#: root. Its bundles are already imported by the self-hosted integration run, so a
#: fixture that repeated them would buy coverage CI already has.
INTEGRATION_SCRIPT = Path('scripts') / 'import' / 'import_for_tests.sh'


@dataclass(frozen=True)
class RegistryEntry:
    """One entry of the bundle registry that OPUS imports.

    Attributes:
        index: The entry's position in `BUNDLE_INFO`, which is the order bundles are
            imported in and therefore the order the goldens encode.
        pattern: The regular expression matching the bundle ids the entry covers.
        info: What the registry says about them.
        instrument_class_name: The name of the class that imports them, which is how an
            entry is named in the exclusions file.
    """

    index: int
    pattern: str
    info: BundleInfo
    instrument_class_name: str

    @property
    def pds_version(self) -> Literal[3, 4]:
        """Which PDS regime the entry's bundles belong to."""
        return self.info['pds_version']


@dataclass(frozen=True)
class BundleLocation:
    """Where one bundle's files are in a holdings tree.

    Attributes:
        bundle_id: The bundle (PDS3 volume) id.
        bundleset: The bundle set (PDS3 volume set) it belongs to.
        pds_version: 3 or 4.
        root: The holdings root the bundle lives under.
        bundle_dir: The bundle's own directory under ``volumes/`` or ``bundles/``.
    """

    bundle_id: str
    bundleset: str
    pds_version: Literal[3, 4]
    root: Path
    bundle_dir: Path

    @property
    def pdsfile(self) -> PdsFile:
        """The `pdsfile` object for this bundle, resolved as the import resolves it.

        A PDS4 bundle set can share its name with its one bundle, and pdsfile then
        prefers the set; the import asks again by full path to get the bundle, and so
        does this.
        """
        if self.pds_version == 3:
            return Pds3File.from_path(self.bundle_id)
        resolved = Pds4File.from_path(self.bundle_id)
        if not resolved.is_bundle:
            resolved = Pds4File.from_path(
                f'{PDS4_BUNDLES_DIRNAME}/{self.bundle_id}/{self.bundle_id}'
            )
        return resolved

    @property
    def metadata_dirs(self) -> list[Path]:
        """The bundle's metadata directories, found the way the import finds them.

        A PDS4 bundle whose set carries only itself keeps its metadata directly under
        the set, with no directory of its own, so the layout is asked for rather than
        assumed.
        """
        return [
            Path(path) for path in self.pdsfile.associated_abspaths('metadata', must_exist=True)
        ]

    @property
    def metadata_dir(self) -> Path:
        """The bundle's own metadata directory, or where one would go if it had none."""
        found = self.metadata_dirs
        if len(found) > 0:
            return found[0]
        return self.root / 'metadata' / self.bundleset / self.bundle_id

    @property
    def metadata_relpath(self) -> Path:
        """Where the fixture keeps this bundle's metadata, below its own metadata root.

        The fixture mirrors the holdings' own layout below ``metadata/``, because
        pdsfile's discovery walks that layout rather than being told where to look.
        """
        return self.metadata_dir.relative_to(self.root / 'metadata')

    @property
    def volume_index_dir(self) -> Path | None:
        """The bundle's own index directory, for a PDS3 volume that has one."""
        for name in VOLUME_INDEX_DIRNAMES:
            candidate = self.bundle_dir / name
            if candidate.is_dir():
                return candidate
        return None


def registry_entries() -> list[RegistryEntry]:
    """Return every registry entry OPUS imports, in registry order.

    An entry whose instrument class is None names bundles OPUS knows about and
    deliberately ignores, so it is not part of the fixture's coverage obligation.

    Returns:
        The entries, in the order `BUNDLE_INFO` lists them.
    """
    entries = []
    for index, (pattern, info) in enumerate(BUNDLE_INFO):
        instrument_class = info['instrument_class']
        if instrument_class is None:
            continue
        entries.append(
            RegistryEntry(
                index=index,
                pattern=pattern,
                info=info,
                instrument_class_name=instrument_class.__name__,
            )
        )
    return entries


def bundle_dirs(root: Path, bundles_dirname: str) -> list[tuple[str, Path]]:
    """Return every unversioned bundle directory under a holdings root.

    Parameters:
        root: The holdings root.
        bundles_dirname: ``volumes`` or ``bundles``.

    Returns:
        (bundle set, bundle directory) pairs, sorted by bundle set then bundle.
    """
    found = []
    container = root / bundles_dirname
    for bundleset_dir in sorted(container.iterdir()):
        if not bundleset_dir.is_dir():
            continue
        if VERSIONED_BUNDLESET_RE.search(bundleset_dir.name):
            continue
        for bundle_dir in sorted(bundleset_dir.iterdir()):
            if bundle_dir.is_dir():
                found.append((bundleset_dir.name, bundle_dir))
    return found


def locate_bundles(pds3_root: Path, pds4_root: Path) -> dict[int, list[BundleLocation]]:
    """Find every bundle in the holdings that a registered type covers.

    Parameters:
        pds3_root: The PDS3 holdings root.
        pds4_root: The PDS4 holdings root.

    Returns:
        The matching bundles, sorted by bundle id, keyed by registry entry index. An
        entry with no bundle in the holdings is absent from the mapping.
    """
    per_regime = {
        3: (pds3_root, bundle_dirs(pds3_root, PDS3_BUNDLES_DIRNAME)),
        4: (pds4_root, bundle_dirs(pds4_root, PDS4_BUNDLES_DIRNAME)),
    }
    located: dict[int, list[BundleLocation]] = {}
    for entry in registry_entries():
        root, candidates = per_regime[entry.pds_version]
        matches = [
            BundleLocation(
                bundle_id=bundle_dir.name,
                bundleset=bundleset,
                pds_version=entry.pds_version,
                root=root,
                bundle_dir=bundle_dir,
            )
            for bundleset, bundle_dir in candidates
            if re.fullmatch(entry.pattern, bundle_dir.name)
        ]
        if len(matches) > 0:
            located[entry.index] = sorted(matches, key=lambda loc: loc.bundle_id)
    return located


def script_bundle_descriptors(script_path: Path) -> list[str]:
    """Return the bundle descriptors the integration import script names.

    A commented-out line names a bundle the script does not import, so it is not one
    the fixture has to avoid.

    Parameters:
        script_path: The shell script to read.

    Returns:
        Every descriptor on an active ``--do-all-import`` line, in script order.
    """
    descriptors: list[str] = []
    for line in script_path.read_text(encoding='utf-8').splitlines():
        stripped = line.strip()
        if stripped.startswith('#'):
            continue
        if '--do-all-import' not in stripped:
            continue
        fields = stripped.split()
        position = fields.index('--do-all-import')
        if position + 1 < len(fields):
            descriptors.extend(fields[position + 1].split(','))
    return descriptors


def preference_order(eligible: Sequence[str]) -> list[str]:
    """Return the bundles of one type in the order the recorder should try them.

    The middle of the sorted list comes first; the rest follow in order, wrapping to
    the start. A candidate that fails the fixture's own gates is skipped in favour of
    the next one, which is what makes this an order rather than a single choice.

    Parameters:
        eligible: The bundle ids to choose among, sorted.

    Returns:
        The same ids, rotated so the middle one is first.
    """
    if len(eligible) == 0:
        return []
    start = len(eligible) // 2
    return list(eligible[start:]) + list(eligible[:start])


def candidate_order(
    bundles: Sequence[BundleLocation], avoid: Iterable[str]
) -> list[BundleLocation]:
    """Return one type's bundles in the order the recorder should try them.

    The bundles the integration run already imports are dropped first, so the fixture
    and that run cover different volumes between them. Where dropping them leaves
    nothing -- a type whose pattern matches exactly one bundle -- the overlap is
    unavoidable and the full list is used.

    Parameters:
        bundles: Every bundle of one type in the holdings, sorted by id.
        avoid: The bundle ids the integration run imports.

    Returns:
        The bundles to try, best first.
    """
    avoid_set = set(avoid)
    by_id = {bundle.bundle_id: bundle for bundle in bundles}
    eligible = [bundle.bundle_id for bundle in bundles if bundle.bundle_id not in avoid_set]
    if len(eligible) == 0:
        eligible = [bundle.bundle_id for bundle in bundles]
    return [by_id[bundle_id] for bundle_id in preference_order(eligible)]
