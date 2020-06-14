from __future__ import annotations

import collections
import csv
import glob
import itertools
import os
import re
from typing import NamedTuple, Sequence, Callable, Tuple, List, Dict


class ManifestEntry(NamedTuple):
    """Information from one line of an Apache log entry."""
    opus_id: str
    product_category: str
    product_type: str
    file_path: str
    size: int
    # product_type_abbr: str
    # version: str

    @staticmethod
    def from_csv_line(line: Dict[str, str]) -> ManifestEntry:
        return ManifestEntry(opus_id=line['OPUS ID'],
                             product_category=line['Product Category'],
                             product_type=line['Product Type'],
                             file_path=line['File Path'],
                             size=int(line['Size']),
                             # product_type_abbr=line['Product Type Abbrev'],
                             # version=line['Version']
               )

    @property
    def volume_set(self) -> str:
        match = re.match(r'/\w+/(\w+)[/$]', self.file_path)
        return match.group(1)


class Manifest(NamedTuple):
    file_name: str
    entries: Sequence[ManifestEntry]

    @staticmethod
    def read_manifest(file_name: str) -> Manifest:
        with open(file_name, 'r', newline='') as file:
            reader = csv.DictReader(file)
            entries = [ManifestEntry.from_csv_line(line) for line in reader]
            return Manifest(file_name, entries)

    @staticmethod
    def read_manifests(file_patterns: Sequence[file_name]) -> Sequence[Manifest]:
        return [Manifest.read_manifest(file_name)
                for file_pattern in file_patterns
                for file_name in glob.glob(file_pattern)]

    def __repr__(self):
        name = os.path.basename(self.file_name)
        return f'<Manifest {name}>'

    def __hash__(self):
        return hash(self.file_name)

    def __eq__(self, other):
        return isinstance(other, Manifest) and other.file_name == self.file_name


class SummaryLine(NamedTuple):
    key: Tuple[str, ...]
    manifest_count: int
    opus_id_count: int
    file_path_count: int
    file_path_bytes: int


class Summary(NamedTuple):
    headers: Sequence[str]
    lines: Sequence[SummaryLine]


class ManifestStatus:
    _manifests: Sequence[Manifest]

    def __init__(self, manifests: Sequence[Manifest]):
        self._manifests = manifests

    def get_summary(self, grouper: Callable[[ManifestEntry], Tuple[str, ...]]) -> Sequence[SummaryLine]:

        all_items = [(manifest, entry) for manifest in self._manifests for entry in manifest.entries]
        all_items.sort(key=lambda item: [x.upper() for x in grouper(item[1])])

        result: List[Summary] = []
        for key, iter_items in itertools.groupby(all_items, key=lambda item: grouper(item[1])):
            items = list(iter_items)
            manifest_count = len({manifest for manifest, _ in items})
            opus_id_count = len({(manifest, entry.opus_id) for manifest, entry in items})
            file_path_to_size = collections.defaultdict(int)
            for manifest, entry in items:
                if file_path_to_size[manifest, entry.file_path] < entry.size:
                    file_path_to_size[manifest, entry.file_path] = entry.size
            file_path_count = len(file_path_to_size)
            file_path_bytes = sum(file_path_to_size.values())
            result.append(SummaryLine(key=key, manifest_count=manifest_count, opus_id_count=opus_id_count,
                                      file_path_count=file_path_count, file_path_bytes=file_path_bytes))
        return result

    @staticmethod
    def get_temporary_results() -> Sequence[Summary]:
        manifests = Manifest.read_manifests(["/users/fy/Dropbox/Shared-Frank-Yellin/manifests/*"])
        status = ManifestStatus(manifests)

        result1 = status.get_summary(lambda entry: (entry.product_category, entry.product_type))
        result2 = status.get_summary(lambda entry: (entry.volume_set,))
        result3 = status.get_summary(lambda entry: (entry.volume_set, entry.product_type))

        return [Summary(headers=('Product Category', 'Product Type'), lines=result1),
                Summary(headers=('Volume Set',), lines=result2),
                Summary(headers=('Volume Set', 'Product Type'), lines=result3)
               ]


if __name__ == '__main__':
    result1, result2, result3 = ManifestStatus.get_temporary_results()
