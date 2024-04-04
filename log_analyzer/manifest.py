from __future__ import annotations

import collections
import csv
import itertools
import os
import re
from pathlib import Path, PosixPath
from typing import NamedTuple, Sequence, Callable, Tuple, List, Dict, Any, Optional


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
    def from_csv_line(line: Dict[str, str]) -> Optional[ManifestEntry]:
        try:
            return ManifestEntry(opus_id=line['OPUS ID'],
                                 product_category=line['Product Category'],
                                 product_type=line['Product Type'],
                                 file_path=line['File Path'],
                                 size=int(line['Size']),
                                 # product_type_abbr=line['Product Type Abbrev'],
                                 # version=line['Version']
                                 )
        except:
            return None

    @property
    def volume_set(self) -> str:
        path = PosixPath(self.file_path)
        assert path.is_absolute()
        return path.parts[2]  #   ["/" "volume" volumename, .....]

class Manifest(NamedTuple):
    file_name: str
    entries: Sequence[ManifestEntry]

    @staticmethod
    def read_manifest(file_name: str) -> Optional[Manifest]:
        try:
            with open(file_name, 'r', newline='') as file:
                reader = csv.DictReader(file)
                entries = [entry for line in reader
                           for entry in [ManifestEntry.from_csv_line(line)] if entry]
                return Manifest(file_name, entries)
        except:
            print(f"Error while reading Manifest file {file_name}")
            return None

    @staticmethod
    def read_manifests(file_names: Sequence[str]) -> Sequence[Manifest]:
        return [manifest for file_name in file_names
                for manifest in [Manifest.read_manifest(file_name)]
                if manifest is not None]

    def size_in_bytes(self):
        file_to_size: Dict[str, int] = collections.defaultdict(int)
        for entry in self.entries:
            file_to_size[entry.file_path] = max(file_to_size[entry.file_path], entry.size)
        return sum(file_to_size.values())

    def __repr__(self) -> str:
        name = os.path.basename(self.file_name)
        return f'<Manifest {name}>'

    def __hash__(self) -> int:
        return hash(self.file_name)

    def __eq__(self, other: Any) -> bool:
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
    total: SummaryLine


class ManifestStatus:
    _manifests: Sequence[Manifest]

    def __init__(self, manifests: Sequence[Manifest]):
        self._manifests = manifests

    def __get_one_table(self, grouper: Callable[[ManifestEntry], Tuple[str, ...]]) -> \
            Tuple[Sequence[SummaryLine], SummaryLine]:
        all_items = [(manifest, entry) for manifest in self._manifests for entry in manifest.entries]
        all_items.sort(key=lambda item: grouper(item[1]))

        result: List[SummaryLine] = []
        for key, iter_items in itertools.groupby(all_items, key=lambda item: grouper(item[1])):
            items = list(iter_items)
            manifest_count = len({manifest for manifest, _ in items})
            opus_id_count = len({(manifest, entry.opus_id) for manifest, entry in items})
            file_path_to_size: Dict[Tuple[Manifest, str], int] = collections.defaultdict(int)
            for manifest, entry in items:
                if file_path_to_size[manifest, entry.file_path] < entry.size:
                    file_path_to_size[manifest, entry.file_path] = entry.size
            file_path_count = len(file_path_to_size)
            file_path_bytes = sum(file_path_to_size.values())
            result.append(SummaryLine(key=key,
                                      manifest_count=manifest_count,
                                      opus_id_count=opus_id_count,
                                      file_path_count=file_path_count, file_path_bytes=file_path_bytes))

        total = SummaryLine(key=(),
                            manifest_count=0,
                            opus_id_count=0,
                            file_path_count=sum(x.file_path_count for x in result),
                            file_path_bytes=sum(x.file_path_bytes for x in result))
        return result, total

    def __get_statistics(self) -> Dict[str, Any]:
        result1, total1 = self.__get_one_table(lambda entry: (entry.product_category, entry.product_type))
        result2, total2 = self.__get_one_table(lambda entry: (entry.volume_set,))
        result3, total3 = self.__get_one_table(lambda entry: (entry.volume_set, entry.product_type))

        summary1 = Summary(lines=result1, total=total1, headers=('Product Category', 'Product Type'))
        summary2 = Summary(lines=result2, total=total2, headers=('Volume Set',))
        summary3 = Summary(lines=result3, total=total3, headers=('Volume Set', 'Product Type'))

        manifest_count = len(self._manifests)
        opus_id_count = len({entry.opus_id
                             for manifest in self._manifests
                             for entry in manifest.entries})
        data = tuple(manifest.size_in_bytes() for manifest in self._manifests)

        return {
            "tables": (summary1, summary2, summary3),
            "manifest_count": manifest_count,
            "opus_id_count": opus_id_count,
            "data": data,
        }

    @staticmethod
    def get_statistics(manifest_files: Sequence[str]) -> Dict[str, Any]:
        manifests = Manifest.read_manifests(manifest_files)
        status = ManifestStatus(manifests)
        return status.__get_statistics()
