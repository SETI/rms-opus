"""Record the mini-holdings fixture from the real PDS holdings.

Run on the holdings machine, on demand. It is the only program that reads the real
holdings, and it never writes into them: everything the maintenance tools produce is
built in a scratch directory and read back from there.

    python -m import_tests.tools.make_mini_holdings \\
        --pds3-holdings /path/to/holdings --pds4-holdings /path/to/pds4-holdings \\
        --scratch /path/to/a/scratch/directory

Re-running it and reading the diff is the drift report: the fixture encodes pdsfile's
current answers, so a pdsfile change that moves them shows up here as changed lines
rather than as a mysterious import failure. Regenerating the fixture comes first;
regenerating the goldens with `import_tests.tools.make_mini_goldens` comes second.
"""

from __future__ import annotations

import argparse
import logging
import shutil
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

import pdslogger
from pdsfile.pds3file import Pds3File
from pdsfile.pds4file import Pds4File

from import_tests.tools import (
    bundle_recorder,
    fixture_layout,
    holdings_survey,
    metadata_subsets,
    row_sampling,
    shelf_capture,
    shelf_manifests,
)
from opus_import.cli import _create_argument_parser
from opus_import.context import ImportContext

if TYPE_CHECKING:
    from collections.abc import Sequence

#: The categories a PDS3 bundle can have shelves for, in the order they are captured.
#: A category with no shelf of a given kind is skipped rather than reported.
_SHELF_KINDS = ('info', 'link')

#: The category whose shelf answers the metadata directory listing, and therefore has to
#: name every file the fixture checks in there.
_METADATA_CATEGORY = 'metadata'

#: Where the maintenance tools' logs go inside the scratch tree.
_SCRATCH_LOG_DIRNAME = 'logs'


@dataclass
class RecorderReport:
    """What one run of the recorder did, for the operator to read and to record.

    Attributes:
        chosen: The bundle recorded for each registry entry, in registry order.
        skipped: One line per candidate the recorder passed over, with the reason.
        excluded: The instrument classes with no bundle in the holdings.
        schema_differences: Bundles whose index schema differs from the representative
            their type chose, which is a reviewed decision rather than a discovery.
        manifest_count: How many shelf manifests were written.
        product_count: How many expected products were recorded.
    """

    chosen: list[bundle_recorder.BundleRecord] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)
    excluded: list[tuple[str, str]] = field(default_factory=list)
    schema_differences: list[str] = field(default_factory=list)
    manifest_count: int = 0
    product_count: int = 0


def _recorder_context() -> ImportContext:
    """Build a context carrying the import pipeline's own default arguments.

    The obs classes read the run's arguments, so the recorder gives them the same
    defaults a real run has rather than a hand-written stand-in that could drift from
    them.

    Returns:
        A context with no database and a logger that writes to standard output.
    """
    args = _create_argument_parser().parse_args([])
    logger = pdslogger.PdsLogger('opus_import.make_mini_holdings')
    logger.add_handler(pdslogger.stdout_handler)
    # Errors only. An index that names support files as well as data files warns once
    # per support row while its rows are resolved, which is hundreds of lines per bundle
    # about rows the fixture is deciding not to keep; the run's report is the output.
    logger.set_level(logging.ERROR)
    return ImportContext(args=args, logger=logger)


def _expand_descriptors(descriptors: Sequence[str], pds3_root: Path, pds4_root: Path) -> set[str]:
    """Turn the integration script's bundle descriptors into bundle ids.

    A descriptor is either a bundle id or a bundle set name standing for every bundle
    in it, which is how one line of the script imports a whole set.

    Parameters:
        descriptors: The descriptors the script names.
        pds3_root: The PDS3 holdings root.
        pds4_root: The PDS4 holdings root.

    Returns:
        Every bundle id the script imports.
    """
    by_bundleset: dict[str, set[str]] = {}
    known: set[str] = set()
    pairs = [
        *holdings_survey.bundle_dirs(pds3_root, holdings_survey.PDS3_BUNDLES_DIRNAME),
        *holdings_survey.bundle_dirs(pds4_root, holdings_survey.PDS4_BUNDLES_DIRNAME),
    ]
    for bundleset, bundle_dir in pairs:
        by_bundleset.setdefault(bundleset, set()).add(bundle_dir.name)
        known.add(bundle_dir.name)

    expanded: set[str] = set()
    for descriptor in descriptors:
        if descriptor in known:
            expanded.add(descriptor)
        elif descriptor in by_bundleset:
            expanded |= by_bundleset[descriptor]
    return expanded


def _write_volinfo(records: Sequence[bundle_recorder.BundleRecord], pds3_root: Path) -> None:
    """Write the volume-set descriptions the fixture's PDS3 volumes need.

    pdsfile reads this directory with a plain ``os.listdir`` during preload, so it has to
    exist on disk rather than being answered by a shelf. Only the lines describing the
    fixture's own volumes are kept.

    Parameters:
        records: The recorded bundles.
        pds3_root: The PDS3 holdings root.
    """
    wanted: dict[str, set[str]] = {}
    for record in records:
        if record.entry.pds_version != 3:
            continue
        wanted.setdefault(record.location.bundleset, set()).add(record.location.bundle_id)
    fixture_layout.PDS3_VOLINFO.mkdir(parents=True, exist_ok=True)
    for bundleset, bundles in sorted(wanted.items()):
        source = pds3_root / '_volinfo' / f'{bundleset}.txt'
        kept = []
        for line in source.read_text(encoding='utf-8').splitlines(keepends=True):
            stripped = line.strip()
            if len(stripped) == 0 or stripped.startswith('#'):
                kept.append(line)
                continue
            key = stripped.split('|')[0].strip()
            if key == bundleset or key.split('/')[-1] in bundles:
                kept.append(line)
        (fixture_layout.PDS3_VOLINFO / f'{bundleset}.txt').write_text(
            ''.join(kept), encoding='utf-8'
        )


def _write_exclusions(report: RecorderReport) -> None:
    """Write the registered types that have no bundle in the holdings.

    Parameters:
        report: The run's report, whose exclusions are written.
    """
    lines = [f'{name}\t{reason}' for name, reason in sorted(report.excluded)]
    fixture_layout.EXCLUSIONS_FILE.parent.mkdir(parents=True, exist_ok=True)
    fixture_layout.EXCLUSIONS_FILE.write_text('\n'.join(lines) + '\n', encoding='utf-8')


def _needed_shelf_keys(
    records: Sequence[bundle_recorder.BundleRecord],
) -> dict[tuple[int, str, str, str], set[str]]:
    """Merge every bundle's shelf requirements into one mapping.

    A metadata shelf gains every file the fixture checks in under that bundle, in the
    expected-products set or not: the import discovers a bundle's summary files by
    listing that directory through the shelf, so a missing entry silently loses one.

    Parameters:
        records: The recorded bundles.

    Returns:
        The interior paths each shelf has to carry, keyed by (regime, category, bundle
        set, bundle).
    """
    needed: dict[tuple[int, str, str, str], set[str]] = {}
    for record in records:
        for key, interior in record.shelf_keys.items():
            needed.setdefault(key, set()).update(interior)
        parts = record.location.metadata_relpath.parts
        if len(parts) != 2:
            # pdsfile addresses a metadata shelf by bundle set and bundle. A PDS4
            # bundle whose metadata sits directly under its set has no such address at
            # all -- asking for one raises -- so the directory listing falls through to
            # the filesystem, which the built tree materializes.
            continue
        metadata_key = (record.entry.pds_version, _METADATA_CATEGORY, parts[0], parts[1])
        entry = needed.setdefault(metadata_key, {''})
        entry.update(record.metadata_basenames)
        entry.add('')
    return needed


def _emit_manifests(
    needed: dict[tuple[int, str, str, str], set[str]],
    roots: dict[int, Path],
    report: RecorderReport,
) -> None:
    """Write one manifest per shelf the fixture needs, from whichever tree holds it.

    Parameters:
        needed: The interior paths each shelf has to carry.
        roots: The holdings root to read each regime's shelves from, which for PDS4 is
            the scratch tree the maintenance tools just wrote into.
        report: The run's report, whose manifest count is updated.
    """
    destinations = {3: fixture_layout.PDS3_MANIFESTS, 4: fixture_layout.PDS4_MANIFESTS}
    for (pds_version, category, bundleset, bundle), keys in sorted(needed.items()):
        selection = shelf_capture.ShelfSelection(
            category=category, bundleset=bundleset, bundle=bundle, keys=keys
        )
        for kind in _SHELF_KINDS:
            captured = shelf_capture.capture_manifest(roots[pds_version], selection, kind)
            if captured is None:
                continue
            name, entries = captured
            shelf_manifests.write_manifest(destinations[pds_version] / name.filename, entries)
            report.manifest_count += 1


def _check_metadata_manifests(records: Sequence[bundle_recorder.BundleRecord]) -> None:
    """Fail the run if a metadata info shelf does not list every checked-in file.

    Parameters:
        records: The recorded bundles.

    Raises:
        ValueError: If a file the fixture checks in under a bundle's metadata directory
            has no entry in that bundle's metadata info-shelf manifest, which would
            silently lose a summary file at import time.
    """
    destinations = {3: fixture_layout.PDS3_MANIFESTS, 4: fixture_layout.PDS4_MANIFESTS}
    for record in records:
        parts = record.location.metadata_relpath.parts
        if len(record.metadata_basenames) == 0 or len(parts) != 2:
            continue
        name = shelf_manifests.ManifestName(
            shelf_type='info',
            category=_METADATA_CATEGORY,
            bundleset=parts[0],
            bundle=parts[1],
        )
        path = destinations[record.entry.pds_version] / name.filename
        entries = shelf_manifests.read_manifest(path)
        missing = sorted(record.metadata_basenames - set(entries))
        if len(missing) > 0:
            raise ValueError(f'{path.name} is missing entries for {missing}')


def _stage_and_build_pds4(
    needed: dict[tuple[int, str, str, str], set[str]], pds4_root: Path, scratch: Path
) -> Path:
    """Copy the PDS4 bundles the fixture needs into scratch and build their shelves.

    Production PDS4 holdings carry no shelves, so the recorder makes them with pdsfile's
    own maintenance tools rather than inventing the format. The tools run over plain
    copies -- never links, because the recorder has to work on Windows and the scratch
    tree may be on another filesystem -- and write only inside the scratch tree.

    Parameters:
        needed: The shelves the fixture needs, of both regimes.
        pds4_root: The real PDS4 holdings root.
        scratch: The scratch directory.

    Returns:
        The scratch PDS4 holdings root the shelves were written under.
    """
    scratch_root = scratch / fixture_layout.PDS4_ROOT_NAME
    log_root = scratch / _SCRATCH_LOG_DIRNAME
    targets = sorted(
        {
            (category, bundleset, bundle)
            for pds_version, category, bundleset, bundle in needed
            if pds_version == 4
        }
    )
    staged_bundlesets = []
    for category, bundleset, bundle in targets:
        source = pds4_root / category / bundleset / bundle
        if not source.is_dir():
            continue
        shelf_capture.stage_copy(source, scratch_root / category / bundleset / bundle)
        if (category, bundleset) not in staged_bundlesets:
            staged_bundlesets.append((category, bundleset))

    # The tools are pointed at each bundle set rather than at each bundle. Their driver
    # expands a bundle set into its children and treats each as one unit, and that is the
    # only way it will accept uranus_occ_support: pdsfile reports that directory as a
    # bundle set of its own, so naming it directly makes the driver expand it a second
    # time and try to checksum the directories inside it. Only the bundles this run
    # staged are under the scratch bundle set, so the expansion covers exactly them.
    for category, bundleset in staged_bundlesets:
        for tool in shelf_capture.PDS4_SHELF_TOOLS:
            shelf_capture.run_shelf_tool(tool, scratch_root / category / bundleset, log_root)
    return scratch_root


def _build_pds3_index_shelves(
    records: Sequence[bundle_recorder.BundleRecord], scratch: Path
) -> Path:
    """Build the PDS3 index shelves over the fixture's own subsetted tables.

    The import checks that an observation is present in an index before listing that
    index among its products, and it answers the question from these shelves. Building
    them over the subsetted tables is what makes the row keys match by construction.

    Parameters:
        records: The recorded bundles.
        scratch: The scratch directory.

    Returns:
        The scratch PDS3 holdings root the shelves were written under.
    """
    scratch_root = scratch / fixture_layout.PDS3_ROOT_NAME
    log_root = scratch / _SCRATCH_LOG_DIRNAME
    for record in records:
        if record.entry.pds_version != 3 or len(record.metadata_basenames) == 0:
            continue
        source = fixture_layout.PDS3_METADATA / record.location.metadata_relpath
        staged = scratch_root / _METADATA_CATEGORY / record.location.metadata_relpath
        shelf_capture.stage_copy(source, staged, refresh=True)
        shelf_capture.run_shelf_tool(shelf_capture.PDS3_INDEX_SHELF_TOOL, staged, log_root)
    return scratch_root


def _emit_index_manifests(
    records: Sequence[bundle_recorder.BundleRecord], scratch_pds3_root: Path, report: RecorderReport
) -> None:
    """Write the index-shelf manifests the PDS3 row-file check reads.

    PDS4 index shelves are not written: the import's row-file check is gated to PDS3, so
    a PDS4 index shelf would be content no code path reads.

    Parameters:
        records: The recorded bundles.
        scratch_pds3_root: Where the index shelves were built.
        report: The run's report, whose manifest count is updated.
    """
    for record in records:
        if record.entry.pds_version != 3:
            continue
        parts = record.location.metadata_relpath.parts
        if len(parts) != 2:
            continue
        captured = shelf_capture.capture_index_manifests(
            scratch_pds3_root, _METADATA_CATEGORY, parts[0], parts[1]
        )
        for name, entries in captured:
            shelf_manifests.write_manifest(fixture_layout.PDS3_MANIFESTS / name.filename, entries)
            report.manifest_count += 1


def _compare_schemas(
    ctx: ImportContext,
    entry: holdings_survey.RegistryEntry,
    chosen: bundle_recorder.BundleRecord,
    siblings: Sequence[holdings_survey.BundleLocation],
    report: RecorderReport,
) -> None:
    """Report any sibling volume whose index schema differs from the chosen one.

    A second volume from the same set earns its place only when its index carries
    fundamentally different values. This makes that a check rather than a memory: the
    operator reads the report and decides, instead of remembering to look.

    Parameters:
        ctx: A context carrying the pipeline's default arguments.
        entry: The registry entry.
        chosen: The recorded representative.
        siblings: Every bundle of the same type.
        report: The run's report, whose schema differences are appended to.
    """
    chosen_files = metadata_subsets.primary_index_files(entry, chosen.location)
    if len(chosen_files) == 0:
        return
    try:
        chosen_rows, _ = metadata_subsets.read_index(ctx, chosen_files[0], entry.pds_version)
    except ValueError:
        return
    chosen_profile = row_sampling.column_profile(chosen_rows)
    for sibling in siblings:
        if sibling.bundle_id == chosen.location.bundle_id:
            continue
        sibling_files = metadata_subsets.primary_index_files(entry, sibling)
        if len(sibling_files) == 0:
            continue
        try:
            sibling_rows, _ = metadata_subsets.read_index(ctx, sibling_files[0], entry.pds_version)
        except ValueError:
            continue
        sibling_profile = row_sampling.column_profile(sibling_rows)
        extra_columns = sorted(set(sibling_profile) - set(chosen_profile))
        if len(extra_columns) > 0:
            report.schema_differences.append(
                f'{sibling.bundle_id} has index columns {chosen.location.bundle_id} does not: '
                f'{extra_columns}'
            )
        # The columns both have, where the sibling shows a class the chosen volume never
        # does. That is the case worth acting on: a shared column carrying a mult value
        # or a missing/sentinel form the representative's rows never take is a code path
        # the fixture cannot reach, and no column-name comparison would see it.
        extra_classes = {
            column: sorted(classes - chosen_profile[column])
            for column, classes in sibling_profile.items()
            if column in chosen_profile and len(classes - chosen_profile[column]) > 0
        }
        if len(extra_classes) > 0:
            report.schema_differences.append(
                f'{sibling.bundle_id} has index values {chosen.location.bundle_id} does not: '
                f'{sorted(extra_classes.items())[:10]}'
            )


def _reset_fixture() -> None:
    """Remove everything the recorder owns, so a re-run replaces rather than adds to it.

    A volume that is no longer chosen has to disappear from the fixture: leaving its
    metadata and its shelf manifests behind would build them into every temporary tree
    and import a bundle nothing records the products of. The warning whitelist is not
    touched -- it is hand-maintained, and the golden generator is what checks it.
    """
    for directory in (
        fixture_layout.PDS3_FIXTURE,
        fixture_layout.PDS4_FIXTURE,
        fixture_layout.EXPECTED_PRODUCTS_DIR,
    ):
        if directory.is_dir():
            shutil.rmtree(directory)


def _parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    """Parse the recorder's command line.

    Parameters:
        argv: The arguments, or None to read ``sys.argv``.

    Returns:
        The parsed arguments.
    """
    parser = argparse.ArgumentParser(
        prog='make_mini_holdings', description='Record the mini-holdings test fixture'
    )
    parser.add_argument('--pds3-holdings', type=Path, required=True, help='The PDS3 holdings root')
    parser.add_argument('--pds4-holdings', type=Path, required=True, help='The PDS4 holdings root')
    parser.add_argument(
        '--scratch',
        type=Path,
        required=True,
        help='A scratch directory for staged copies and built shelves; never the holdings',
    )
    parser.add_argument(
        '--row-cap',
        type=int,
        default=row_sampling.ROW_CAP,
        help='The most index rows to keep per index file',
    )
    parser.add_argument(
        '--compare-schemas',
        action='store_true',
        help='Also report sibling volumes whose index columns or values differ from the '
        'chosen one. Off by default because it parses every volume of every volume set '
        'rather than the two dozen the fixture keeps, which is hours rather than '
        'minutes; run it when deciding whether a type needs a second representative',
    )
    return parser.parse_args(argv)


def _choose_and_record(
    ctx: ImportContext, args: argparse.Namespace, report: RecorderReport
) -> None:
    """Choose one bundle per registered type and record it.

    Parameters:
        ctx: A context carrying the pipeline's default arguments.
        args: The parsed command line.
        report: The run's report, filled in here.

    Raises:
        ValueError: If every candidate of a registered type fails to record, which
            leaves that type without coverage and is not something to paper over.
    """
    located = holdings_survey.locate_bundles(args.pds3_holdings, args.pds4_holdings)
    avoid = _expand_descriptors(
        holdings_survey.script_bundle_descriptors(
            fixture_layout.REPO_ROOT / holdings_survey.INTEGRATION_SCRIPT
        ),
        args.pds3_holdings,
        args.pds4_holdings,
    )
    for entry in holdings_survey.registry_entries():
        if entry.index not in located:
            report.excluded.append(
                (entry.instrument_class_name, 'no bundle matching its pattern in the holdings')
            )
            continue
        siblings = located[entry.index]
        recorded = None
        for candidate in holdings_survey.candidate_order(siblings, avoid):
            try:
                recorded = bundle_recorder.record_bundle(ctx, entry, candidate, cap=args.row_cap)
            except bundle_recorder.BundleSkippedError as exc:
                report.skipped.append(f'{candidate.bundle_id}: {exc}')
                continue
            break
        if recorded is None:
            raise ValueError(f'No candidate could be recorded for {entry.instrument_class_name}')
        report.chosen.append(recorded)
        print(f'recorded {recorded.location.bundle_id}', flush=True)
        if args.compare_schemas:
            _compare_schemas(ctx, entry, recorded, siblings, report)


def main(argv: Sequence[str] | None = None) -> int:
    """Record the whole fixture.

    Parameters:
        argv: The command line, or None to read ``sys.argv``.

    Returns:
        0 once the fixture is written; the run raises rather than returning non-zero.
    """
    args = _parse_args(argv)
    Pds3File.preload(str(args.pds3_holdings))
    Pds4File.preload(str(args.pds4_holdings))

    ctx = _recorder_context()
    report = RecorderReport()
    _reset_fixture()
    _choose_and_record(ctx, args, report)

    for record in report.chosen:
        bundle_recorder.write_expected_products(record, fixture_layout.EXPECTED_PRODUCTS_DIR)
        report.product_count += len(record.products)
    _write_volinfo(report.chosen, args.pds3_holdings)
    _write_exclusions(report)

    needed = _needed_shelf_keys(report.chosen)
    scratch_pds4 = _stage_and_build_pds4(needed, args.pds4_holdings, args.scratch)
    _emit_manifests(needed, {3: args.pds3_holdings, 4: scratch_pds4}, report)
    _check_metadata_manifests(report.chosen)
    scratch_pds3 = _build_pds3_index_shelves(report.chosen, args.scratch)
    _emit_index_manifests(report.chosen, scratch_pds3, report)

    _print_report(report)
    return 0


def _print_report(report: RecorderReport) -> None:
    """Write the run's report to standard output.

    Parameters:
        report: What the run did.
    """
    print(
        f'Recorded {len(report.chosen)} bundles, {report.product_count} expected products, '
        f'{report.manifest_count} shelf manifests'
    )
    for record in report.chosen:
        print(
            f'  {record.location.bundle_id:40s} '
            f'observations={record.observation_count:4d} '
            f'products={len(record.products):5d} '
            f'uncovered_classes={len(record.uncovered):5d}'
        )
    unshelvable = sorted({name for record in report.chosen for name in record.unshelvable})
    for name in unshelvable:
        print(
            f'  UNSHELVABLE {name}: pdsfile addresses no info shelf for its files, so its '
            'products are not part of the fixture'
        )
    for line in report.skipped:
        print(f'  SKIPPED {line}')
    for name, reason in report.excluded:
        print(f'  EXCLUDED {name}: {reason}')
    for line in report.schema_differences:
        print(f'  SCHEMA {line}')


if __name__ == '__main__':
    sys.exit(main())
