"""Perturb the fixture on the way into a run, for the cases that must go wrong.

A negative case is a hand-authored recipe naming one edit to one index row: which
registered type's volume, which row, which column, and what to write into it. Naming the
type rather than a bundle id is what lets the recipe follow the recorder's choice of
representative instead of going stale the day that choice changes, and the edit is
applied to a copy in a scratch overlay -- the checked-in fixture is never touched.

The result is an overlay tree `import_tests.tools.build_run` copies over the built
holdings once it is complete, so a case perturbs the run and nothing else.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from import_tests.tools import build_run, fixture_layout, holdings_survey, table_subsets

#: The extension a recipe file carries.
RECIPE_EXT = '.tsv'

#: One COLUMN object of a PDS3 label, from its OBJECT line to its END_OBJECT line.
_COLUMN_BLOCK_RE = re.compile(
    r'(?ms)^\s*OBJECT\s*=\s*COLUMN\s*$(.*?)^\s*END_OBJECT\s*=\s*COLUMN\s*$'
)

#: The negative cases the suite runs. Each name is a schema suffix, and for the crafted
#: one it is also its recipe's file name.
DUPLICATE_ID_CASE = 'dupid'
IGNORE_ERRORS_CASE = 'ignore_errors'

#: The registered type whose volume is imported twice in one invocation, which is what
#: puts two copies of every OPUS id in the same import tables. Galileo is the type the
#: production import script applies ``--import-check-duplicate-id`` to, because its
#: volumes really do share observations.
DUPLICATE_ID_INSTRUMENT_CLASS = 'ObsVolumeGO0xxx'

#: What a recipe can ask for: overwrite one column of one row, which is how an unknown
#: value is put where the import has to decide what to do with it. The replacement is
#: padded to the column's own width, so every field after it stays where the label says
#: it is.
SET_COLUMN = 'set_column'
OPERATIONS = (SET_COLUMN,)


@dataclass(frozen=True)
class Recipe:
    """One negative case's edit.

    Attributes:
        name: The case's name, which is also its schema suffix.
        instrument_class: The registered type whose fixture volume is perturbed.
        bundle: The fixture bundle that type is represented by.
        label: The primary index label in the fixture, before the edit.
        table: The table file beside it.
        operation: `SET_COLUMN`.
        row: The zero-based row of the fixture's subsetted table to edit.
        column: The column to overwrite.
        value: The text to write into it.
    """

    name: str
    instrument_class: str
    bundle: str
    label: Path
    table: Path
    operation: str
    row: int
    column: str | None
    value: str | None


def _fixture_index_files(bundle: str) -> tuple[Path, Path]:
    """Return the fixture's primary index label and table for one bundle.

    Parameters:
        bundle: The bundle id.

    Returns:
        The label and the table beside it.

    Raises:
        ValueError: If the fixture holds no primary index for that bundle, which means
            the recipe names a type the fixture no longer carries.
    """
    for bundleset_dir in sorted(fixture_layout.PDS3_METADATA.glob('*')):
        candidate = bundleset_dir / bundle
        if not candidate.is_dir():
            continue
        labels = sorted(candidate.glob(f'{bundle}_index.lbl'))
        if len(labels) == 0:
            labels = sorted(candidate.glob('*.lbl'))
        for label in labels:
            table = label.with_suffix('.tab')
            if table.is_file():
                return label, table
    raise ValueError(f'The fixture holds no PDS3 primary index for {bundle}')


def bundle_for_class(instrument_class: str) -> str:
    """Return the fixture bundle representing one registered type.

    Parameters:
        instrument_class: The name of the type's obs class.

    Returns:
        The bundle id.

    Raises:
        ValueError: If no registered type has that class name, or the fixture carries no
            bundle for it.
    """
    for entry in holdings_survey.registry_entries():
        if entry.instrument_class_name != instrument_class:
            continue
        for bundle in build_run.fixture_bundles():
            if re.fullmatch(entry.pattern, bundle):
                return bundle
        raise ValueError(f'The fixture carries no bundle for {instrument_class}')
    raise ValueError(f'No registered bundle type is imported by {instrument_class}')


def load_recipe(name: str) -> Recipe:
    """Read one negative case's recipe and resolve it against the fixture.

    Parameters:
        name: The case's name, which is the recipe's file name without its extension.

    Returns:
        The recipe, with the fixture files it names resolved.

    Raises:
        ValueError: If the recipe is missing a field, names an unknown operation, or
            names a type the fixture does not carry.
    """
    path = fixture_layout.NEGATIVE_DIR / f'{name}{RECIPE_EXT}'
    fields: dict[str, str] = {}
    for line in path.read_text(encoding='utf-8').splitlines():
        if line.startswith('#') or len(line.strip()) == 0:
            continue
        key, _, value = line.partition('\t')
        fields[key.strip()] = value
    missing = {'instrument_class', 'operation', 'row'} - set(fields)
    if len(missing) > 0:
        raise ValueError(f'{path.name} is missing {sorted(missing)}')
    operation = fields['operation']
    if operation not in OPERATIONS:
        raise ValueError(f'{path.name} names an unknown operation: {operation}')
    bundle = bundle_for_class(fields['instrument_class'])
    label, table = _fixture_index_files(bundle)
    return Recipe(
        name=name,
        instrument_class=fields['instrument_class'],
        bundle=bundle,
        label=label,
        table=table,
        operation=operation,
        row=int(fields['row']),
        column=fields.get('column'),
        value=fields.get('value'),
    )


def _column_span(label: Path, column: str) -> tuple[int, int]:
    """Return where one column sits inside a fixed-length record.

    The label is read directly rather than through `pdstable`, which is the reader the
    pipeline uses: this runs inside the pytest process, where the suite turns warnings
    into errors, and that reader raises a NumPy deprecation on some archives. Reading
    two keywords out of one COLUMN object needs none of it.

    Parameters:
        label: The index label.
        column: The column name.

    Returns:
        The zero-based offset of the column's first content byte and its length. A PDS
        label counts from one and its START_BYTE points past the opening quote of a
        quoted value, so the span covers the value and not the quotes around it.

    Raises:
        ValueError: If the label defines no such column, or defines it without both of
            the keywords that place it.
    """
    text = label.read_text(encoding='latin-1')
    for block in _COLUMN_BLOCK_RE.findall(text):
        name = _keyword(block, 'NAME')
        if name is None or name.strip('"\' ') != column:
            continue
        start_byte = _keyword(block, 'START_BYTE')
        width = _keyword(block, 'BYTES')
        if start_byte is None or width is None:
            raise ValueError(f'{label.name} places column {column} incompletely')
        return int(start_byte) - 1, int(width)
    raise ValueError(f'{label.name} defines no column {column}')


def _keyword(block: str, keyword: str) -> str | None:
    """Return one keyword's value from a label block.

    Parameters:
        block: The text between an OBJECT line and its END_OBJECT.
        keyword: The keyword to read.

    Returns:
        The value with surrounding whitespace removed, or None if the block does not
        carry that keyword.
    """
    match = re.search(rf'(?m)^\s*{keyword}\s*=\s*(?P<value>\S+)', block)
    if match is None:
        return None
    return match.group('value').strip()


def _edited_table(recipe: Recipe) -> bytes:
    """Return the perturbed contents of the recipe's table file.

    Parameters:
        recipe: The case's recipe.

    Returns:
        The table with the edit applied.

    Raises:
        ValueError: If the row is past the end of the table, or the replacement value is
            wider than the column it goes in -- which would shift every field after it.
    """
    label_bytes = recipe.label.read_bytes()
    record_bytes = table_subsets.read_record_bytes(label_bytes)
    data = bytearray(recipe.table.read_bytes())
    total = len(data) // record_bytes
    if recipe.row >= total:
        raise ValueError(f'Row {recipe.row} is past the end of a {total}-row table')
    start = recipe.row * record_bytes

    assert recipe.column is not None
    assert recipe.value is not None
    offset, width = _column_span(recipe.label, recipe.column)
    replacement = recipe.value.encode('ascii')
    if len(replacement) > width:
        raise ValueError(
            f'"{recipe.value}" does not fit in the {width}-byte column {recipe.column}'
        )
    replacement = replacement.ljust(width)
    data[start + offset : start + offset + width] = replacement
    return bytes(data)


def build_overlay(recipe: Recipe, destination: Path) -> Path:
    """Write the overlay tree that applies one negative case.

    Parameters:
        recipe: The case's recipe.
        destination: The overlay's own directory. It is created.

    Returns:
        The overlay directory, whose ``holdings`` subtree the builder copies over the
        built one.
    """
    relative = recipe.label.relative_to(fixture_layout.PDS3_METADATA)
    target_dir = destination / fixture_layout.PDS3_ROOT_NAME / 'metadata' / relative.parent
    target_dir.mkdir(parents=True, exist_ok=True)

    table_bytes = _edited_table(recipe)
    label_bytes = recipe.label.read_bytes()
    record_bytes = table_subsets.read_record_bytes(label_bytes)
    row_count = len(table_bytes) // record_bytes
    (target_dir / recipe.label.name).write_bytes(
        table_subsets.rewrite_counts(label_bytes, row_count)
    )
    (target_dir / recipe.table.name).write_bytes(table_bytes)
    return destination
