"""Reading OPUS download manifests and summarizing what they contain.

A manifest is the CSV OPUS writes alongside a user download, one row per file.
`ManifestStatus` aggregates a set of them into the three summary tables the
report shows: by product category and type, by volume set, and by both.

Sizes are de-duplicated by file path within a manifest before being summed,
because one file can appear under several product types.
"""

from __future__ import annotations

import collections
import csv
import itertools
import os
from collections.abc import Callable, Sequence
from pathlib import PosixPath
from typing import Any, NamedTuple


class ManifestEntry(NamedTuple):
    """One row of a manifest CSV: a single file in a single download."""

    opus_id: str
    product_category: str
    product_type: str
    file_path: str
    size: int
    # product_type_abbr: str
    # version: str

    @staticmethod
    def from_csv_line(line: dict[str, str]) -> ManifestEntry | None:
        """Build an entry from one `csv.DictReader` row.

        Parameters:
            line: The row, keyed by the manifest's column headings.

        Returns:
            The entry, or None if any column this reads is absent or the size is
            not an integer. A malformed row is dropped rather than failing the
            manifest.
        """
        try:
            return ManifestEntry(
                opus_id=line['OPUS ID'],
                product_category=line['Product Category'],
                product_type=line['Product Type'],
                file_path=line['File Path'],
                size=int(line['Size']),
                # product_type_abbr=line['Product Type Abbrev'],
                # version=line['Version']
            )
        except Exception:
            return None

    @property
    def volume_set(self) -> str:
        """The volume set this file belongs to, read out of its path.

        Returns:
            The third path component, the archive laying paths out as
            `/volumes/<volume set>/...`.

        Raises:
            AssertionError: If the file path is not absolute.
            IndexError: If the file path is absolute but has fewer than three
                components.
        """
        path = PosixPath(self.file_path)
        assert path.is_absolute()
        return path.parts[2]  #   ["/" "volume" volumename, .....]


class Manifest(NamedTuple):
    """One manifest file and the entries read from it."""

    file_name: str
    entries: Sequence[ManifestEntry]

    @staticmethod
    def read_manifest(file_name: str) -> Manifest | None:
        """Read one manifest CSV.

        Parameters:
            file_name: Path to the manifest.

        Returns:
            The manifest, or None if the file could not be read or parsed, in
            which case the reason is printed. Individual malformed rows are
            dropped without failing the file.
        """
        try:
            with open(file_name, newline='') as file:
                reader = csv.DictReader(file)
                entries = [
                    entry
                    for line in reader
                    for entry in [ManifestEntry.from_csv_line(line)]
                    if entry
                ]
                return Manifest(file_name, entries)
        except Exception:
            print(f'Error while reading Manifest file {file_name}')
            return None

    @staticmethod
    def read_manifests(file_names: Sequence[str]) -> Sequence[Manifest]:
        """Read several manifests, skipping the ones that fail.

        Parameters:
            file_names: Paths to the manifests.

        Returns:
            One manifest per file that could be read; a file that could not is
            omitted rather than reported here.
        """
        return [
            manifest
            for file_name in file_names
            for manifest in [Manifest.read_manifest(file_name)]
            if manifest is not None
        ]

    def size_in_bytes(self) -> int:
        """Total bytes this manifest accounts for, counting each file once.

        Returns:
            The sum over distinct file paths of the largest size recorded for
            that path, since one file can appear under several product types.
        """
        file_to_size: dict[str, int] = collections.defaultdict(int)
        for entry in self.entries:
            file_to_size[entry.file_path] = max(file_to_size[entry.file_path], entry.size)
        return sum(file_to_size.values())

    def __repr__(self) -> str:
        """Render the manifest as its file's base name."""
        name = os.path.basename(self.file_name)
        return f'<Manifest {name}>'

    def __hash__(self) -> int:
        """Hash on the file name, so manifests can key the per-file totals."""
        return hash(self.file_name)

    def __eq__(self, other: Any) -> bool:
        """Compare on the file name, ignoring the entries read from it."""
        return isinstance(other, Manifest) and other.file_name == self.file_name


class SummaryLine(NamedTuple):
    """One row of a summary table: a group key and the totals under it."""

    key: tuple[str, ...]
    manifest_count: int
    opus_id_count: int
    file_path_count: int
    file_path_bytes: int


class Summary(NamedTuple):
    """One summary table: its column headings, its rows, and its total row."""

    headers: Sequence[str]
    lines: Sequence[SummaryLine]
    total: SummaryLine


class ManifestStatus:
    """Aggregates a set of manifests into the report's summary tables."""

    _manifests: Sequence[Manifest]

    def __init__(self, manifests: Sequence[Manifest]) -> None:
        """Parameters:
        manifests: The manifests to summarize.
        """
        self._manifests = manifests

    def __get_one_table(
        self, grouper: Callable[[ManifestEntry], tuple[str, ...]]
    ) -> tuple[Sequence[SummaryLine], SummaryLine]:
        """Build one summary table by grouping every entry on a key.

        Parameters:
            grouper: Reads the group key out of an entry.

        Returns:
            The table's rows, ordered by key, and its total row. The total's
            manifest and OPUS-id counts are 0, because summing them across
            groups would double-count anything appearing in more than one.
        """
        all_items = [
            (manifest, entry) for manifest in self._manifests for entry in manifest.entries
        ]
        all_items.sort(key=lambda item: grouper(item[1]))

        result: list[SummaryLine] = []
        for key, iter_items in itertools.groupby(all_items, key=lambda item: grouper(item[1])):
            items = list(iter_items)
            manifest_count = len({manifest for manifest, _ in items})
            opus_id_count = len({(manifest, entry.opus_id) for manifest, entry in items})
            file_path_to_size: dict[tuple[Manifest, str], int] = collections.defaultdict(int)
            for manifest, entry in items:
                if file_path_to_size[manifest, entry.file_path] < entry.size:
                    file_path_to_size[manifest, entry.file_path] = entry.size
            file_path_count = len(file_path_to_size)
            file_path_bytes = sum(file_path_to_size.values())
            result.append(
                SummaryLine(
                    key=key,
                    manifest_count=manifest_count,
                    opus_id_count=opus_id_count,
                    file_path_count=file_path_count,
                    file_path_bytes=file_path_bytes,
                )
            )

        total = SummaryLine(
            key=(),
            manifest_count=0,
            opus_id_count=0,
            file_path_count=sum(x.file_path_count for x in result),
            file_path_bytes=sum(x.file_path_bytes for x in result),
        )
        return result, total

    def __get_statistics(self) -> dict[str, Any]:
        """Build the whole manifest section of the report.

        Returns:
            The template context -- `tables` (the three summaries),
            `manifest_count`, `opus_id_count` counted across all manifests, and
            `data`, the per-manifest byte totals.
        """
        result1, total1 = self.__get_one_table(
            lambda entry: (entry.product_category, entry.product_type)
        )
        result2, total2 = self.__get_one_table(lambda entry: (entry.volume_set,))
        result3, total3 = self.__get_one_table(lambda entry: (entry.volume_set, entry.product_type))

        summary1 = Summary(
            lines=result1, total=total1, headers=('Product Category', 'Product Type')
        )
        summary2 = Summary(lines=result2, total=total2, headers=('Volume Set',))
        summary3 = Summary(lines=result3, total=total3, headers=('Volume Set', 'Product Type'))

        manifest_count = len(self._manifests)
        opus_id_count = len(
            {entry.opus_id for manifest in self._manifests for entry in manifest.entries}
        )
        data = tuple(manifest.size_in_bytes() for manifest in self._manifests)

        return {
            'tables': (summary1, summary2, summary3),
            'manifest_count': manifest_count,
            'opus_id_count': opus_id_count,
            'data': data,
        }

    @staticmethod
    def get_statistics(manifest_files: Sequence[str]) -> dict[str, Any]:
        """Read the named manifests and summarize them.

        Parameters:
            manifest_files: Paths to the manifests; unreadable ones are skipped.

        Returns:
            The template context described by `__get_statistics`.
        """
        manifests = Manifest.read_manifests(manifest_files)
        status = ManifestStatus(manifests)
        return status.__get_statistics()
