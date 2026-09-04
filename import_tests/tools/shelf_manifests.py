"""The text form of a pdsfile shelf, and the mapping between the two.

A shelf is a pickled dictionary inside the holdings tree. The fixture checks in one text
manifest per pickle instead, so the values a test depends on -- real checksums, sizes,
image dimensions and index row keys -- are reviewable in a diff. This module is the only
place that knows the manifest file name, the shelf path it stands for, and the layout of
the text: `import_tests.tools.make_mini_holdings` writes manifests through it and
`import_tests.tools.build_run` turns them back into pickles through it.

A manifest is a single Python dictionary literal read with `ast.literal_eval`, so it is
data and not code. The ``.pydict`` extension keeps it out of every Python gate.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path
from typing import Any

#: The extension every manifest carries. Deliberately not ``.py``: a manifest is data,
#: and this keeps the files outside ruff, mypy and vulture entirely.
MANIFEST_EXT = '.pydict'

#: The shelf kinds a manifest can describe, spelled the way pdsfile spells them.
SHELF_TYPES = ('info', 'link', 'index')

#: What pdsfile appends to a bundle name to name its shelf file, per shelf kind. The
#: index shelves are absent because they are one pickle per index table inside a
#: directory named for the bundle, not one pickle named for the bundle.
_SHELF_FILE_SUFFIX = {'info': '_info', 'link': '_links'}


@dataclass(frozen=True)
class ManifestName:
    """Which shelf one manifest file stands for.

    Attributes:
        shelf_type: ``info``, ``link`` or ``index``.
        category: The holdings category the shelf covers -- ``volumes``, ``metadata``,
            ``previews``, ``calibrated`` or ``diagrams`` for PDS3, ``bundles`` and its
            siblings for PDS4.
        bundleset: The bundle set (PDS3 volume set) the bundle belongs to.
        bundle: The bundle (PDS3 volume) the shelf covers.
        table: The index table an index shelf covers, without its extension. None for
            an info or link shelf, which cover a whole bundle.
    """

    shelf_type: str
    category: str
    bundleset: str
    bundle: str
    table: str | None = None

    def __post_init__(self) -> None:
        """Reject a name no shelf path can be built from.

        Raises:
            ValueError: If the shelf type is not one of `SHELF_TYPES`, if an index
                shelf carries no table name, or if an info or link shelf carries one.
        """
        if self.shelf_type not in SHELF_TYPES:
            raise ValueError(f'Unknown shelf type: {self.shelf_type}')
        if self.shelf_type == 'index' and self.table is None:
            raise ValueError('An index shelf manifest must name its table')
        if self.shelf_type != 'index' and self.table is not None:
            raise ValueError(f'A {self.shelf_type} shelf manifest covers a whole bundle')

    @property
    def filename(self) -> str:
        """The manifest's file name, which encodes every field of this name."""
        parts = [f'{self.shelf_type}shelf-{self.category}', self.bundleset, self.bundle]
        if self.table is not None:
            parts.append(self.table)
        return '.'.join(parts) + MANIFEST_EXT

    @property
    def shelf_relpath(self) -> str:
        """Where the shelf pickle sits, relative to the holdings root."""
        if self.shelf_type == 'index':
            return f'_indexshelf-{self.category}/{self.bundleset}/{self.bundle}/{self.table}.pickle'
        suffix = _SHELF_FILE_SUFFIX[self.shelf_type]
        return (
            f'_{self.shelf_type}shelf-{self.category}/{self.bundleset}/{self.bundle}{suffix}.pickle'
        )

    @classmethod
    def parse(cls, filename: str) -> ManifestName:
        """Recover a name from a manifest's file name.

        Parameters:
            filename: The base name of a manifest file, extension included.

        Returns:
            The name it encodes.

        Raises:
            ValueError: If the name does not have the manifest extension, does not
                start with a recognized ``<type>shelf-<category>`` field, or carries
                too few fields for the shelf kind that field names.

        Notes:
            The shelf type is read first and decides how many fields follow, because a
            bundle name can itself contain a dot: pdsfile addresses each file of a PDS4
            metadata directory that has no bundle level as a bundle of its own, so
            ``<bundle>`` there is a file name with an extension.
        """
        if not filename.endswith(MANIFEST_EXT):
            raise ValueError(f'Not a shelf manifest: {filename}')
        head, _, remainder = filename[: -len(MANIFEST_EXT)].partition('.')
        shelf_type, _, category = head.partition('shelf-')
        if len(category) == 0 or shelf_type not in SHELF_TYPES:
            raise ValueError(f'Malformed shelf manifest name: {filename}')
        expected_fields = 3 if shelf_type == 'index' else 2
        fields = remainder.split('.', expected_fields - 1)
        if len(fields) != expected_fields:
            raise ValueError(f'Malformed shelf manifest name: {filename}')
        bundleset, bundle = fields[0], fields[1]
        table = fields[2] if expected_fields == 3 else None
        return cls(
            shelf_type=shelf_type,
            category=category,
            bundleset=bundleset,
            bundle=bundle,
            table=table,
        )


def format_manifest(entries: dict[str, Any]) -> str:
    """Render a shelf dictionary as the manifest text.

    The layout is pinned so that a regenerated manifest's diff shows exactly the entries
    whose values changed: one entry per line with its whole value on that line, keys
    sorted, and the braces on lines of their own. A width-driven pretty printer would
    split a value tuple across lines and turn one changed number into a multi-line
    difference.

    Parameters:
        entries: The shelf's own dictionary, whose values are plain Python data.

    Returns:
        The manifest text, ending in a newline.
    """
    lines = ['{']
    lines += [f'    {key!r}: {entries[key]!r},' for key in sorted(entries)]
    lines.append('}')
    return '\n'.join(lines) + '\n'


def write_manifest(path: Path, entries: dict[str, Any]) -> None:
    """Write a shelf dictionary to a manifest file, proving the text round-trips.

    Parameters:
        path: The manifest file to write. Its parent directory is created.
        entries: The shelf's own dictionary.

    Raises:
        ValueError: If reading the rendered text back does not reproduce ``entries``,
            which means the layout altered the data rather than only its presentation.
    """
    text = format_manifest(entries)
    if read_manifest_text(text, str(path)) != entries:
        raise ValueError(f'Manifest text does not round-trip: {path}')
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding='utf-8')


def read_manifest_text(text: str, source: str = '<text>') -> dict[str, Any]:
    """Read manifest text back into the shelf dictionary it holds.

    Parameters:
        text: The manifest's contents.
        source: What to name in an error message.

    Returns:
        The dictionary the text contains.

    Raises:
        ValueError: If the text does not hold a single dictionary literal.
    """
    value = ast.literal_eval(text)
    if not isinstance(value, dict):
        raise ValueError(f'Manifest does not hold a dictionary: {source}')
    return value


def read_manifest(path: Path) -> dict[str, Any]:
    """Read a manifest file back into the shelf dictionary it holds.

    Parameters:
        path: The manifest file.

    Returns:
        The dictionary the file contains.

    Raises:
        ValueError: If the file does not hold a single dictionary literal.
    """
    return read_manifest_text(path.read_text(encoding='utf-8'), str(path))
