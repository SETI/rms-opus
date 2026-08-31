"""Every table the import writes, compared row by row against a recorded run.

From an empty database the import is deterministic: ids are handed out in table order
from the highest already present. So the goldens are the whole of the expected output,
and any difference outside a timestamp column is a change in behavior rather than noise.

Which tables are compared is a rule, not a list: everything the schema holds except the
tables ``manage.py migrate`` created. A table the import newly writes shows up here as a
golden that does not exist, and one it stops writing as a golden nothing produced.

The re-import assertions at the end are the exception to "the goldens are the whole of
the expected output", and they say so where they make it: importing a bundle a second
time renumbers that bundle's rows, because ids are handed out from the highest already
present and the old rows are deleted only afterwards.
"""

from __future__ import annotations

import difflib
import re
from typing import TYPE_CHECKING

import pytest

from import_tests.tools import build_run, fixture_layout, golden_io, holdings_survey

if TYPE_CHECKING:
    from import_tests.tools.build_run import ImportRun
    from import_tests.tools.golden_io import DatabaseCredentials

#: The registered type whose fixture volume is imported a second time. Imaging carries
#: the widest set of tables of any single volume, so re-importing it exercises the update
#: half of the most upserts for one bundle's worth of work.
REIMPORT_INSTRUMENT_CLASS = 'ObsVolumeCOISS12xxx'

#: The tables the goldens cover, read at collection time so each one is its own test and
#: a failure names the table rather than the suite.
GOLDENED_TABLES = golden_io.goldened_tables(fixture_layout.GOLDENS_DIR)


#: How many lines of a golden difference a failure prints. A change that moves every row
#: of a table with thousands of them is diagnosed from its first rows; printing all of
#: them buries the other failures in the same run.
DIFF_LINE_LIMIT = 60


def _unified_diff(table: str, expected: str, actual: str) -> str:
    """Return a readable difference between a golden and what the run produced.

    Parameters:
        table: The table's name.
        expected: The golden text.
        actual: The serialized table.

    Returns:
        A unified diff, so a failure reads as rows rather than as a boolean, truncated
        to `DIFF_LINE_LIMIT` lines with a count of what was left out.
    """
    lines = list(
        difflib.unified_diff(
            expected.splitlines(),
            actual.splitlines(),
            fromfile=f'golden/{table}',
            tofile=f'run/{table}',
            lineterm='',
        )
    )
    if len(lines) > DIFF_LINE_LIMIT:
        remaining = len(lines) - DIFF_LINE_LIMIT
        lines = [*lines[:DIFF_LINE_LIMIT], f'... and {remaining} more difference lines']
    return '\n'.join(lines)


def reimport_bundle_id(run: ImportRun) -> str:
    """Return the fixture bundle imported a second time.

    Parameters:
        run: The completed run.

    Returns:
        The bundle id representing `REIMPORT_INSTRUMENT_CLASS`.

    Raises:
        ValueError: If the fixture carries no bundle for that type.
    """
    for entry in holdings_survey.registry_entries():
        if entry.instrument_class_name != REIMPORT_INSTRUMENT_CLASS:
            continue
        for bundle in run.bundles:
            if re.fullmatch(entry.pattern, bundle):
                return bundle
    raise ValueError(f'The fixture carries no bundle for {REIMPORT_INSTRUMENT_CLASS}')


@pytest.fixture(scope='session')
def run_tables(main_run: ImportRun, db_credentials: DatabaseCredentials) -> list[str]:
    """Return the tables the run left behind that the goldens are expected to cover."""
    return [
        table
        for table in golden_io.list_tables(db_credentials, main_run.schema)
        if table not in main_run.django_tables
    ]


def test_goldens_cover_exactly_the_tables_the_run_wrote(run_tables: list[str]) -> None:
    """No table escapes comparison, and no golden describes a table nothing writes."""
    assert sorted(GOLDENED_TABLES) == sorted(run_tables)


def test_django_tables_are_the_only_ones_excluded(main_run: ImportRun) -> None:
    """The migration created some tables, which is what the golden exclusion is for.

    A migration that created nothing would mean the exclusion is measuring the wrong
    thing, and every Django table would then arrive as an unexplained extra table.
    """
    assert len(main_run.django_tables) > 0


@pytest.mark.parametrize('table', GOLDENED_TABLES)
def test_table_matches_its_golden(
    table: str, main_run: ImportRun, db_credentials: DatabaseCredentials
) -> None:
    """One table's rows are exactly what a clean recorded run produced."""
    expected = golden_io.read_golden(fixture_layout.GOLDENS_DIR, table)
    actual = golden_io.serialize_table(db_credentials, main_run.schema, table)
    assert actual == expected, _unified_diff(table, expected, actual)


@pytest.fixture(scope='session')
def reimport(
    main_run: ImportRun, db_credentials: DatabaseCredentials, run_tables: list[str]
) -> tuple[list[str], list[str]]:
    """Import one fixture volume a second time, and split the tables around it.

    This is not a determinism check -- the import is deterministic by design. It is the
    only thing in the suite that runs the update half of every upsert, which is the
    documented re-import operational mode and where the row alias in the generated SQL
    lives.

    It mutates the finished database, so it is deliberately the last thing this module
    does: the golden comparisons above are defined before it and run before it.

    Returns:
        The tables holding the re-imported bundle's rows, and the tables holding none of
        them, each sorted.
    """
    bundle = reimport_bundle_id(main_run)
    build_run.reimport_bundle(main_run, bundle, db_credentials)
    holding = golden_io.tables_holding_bundle(db_credentials, main_run.schema, run_tables, bundle)
    return sorted(holding), sorted(set(run_tables) - holding)


def test_reimport_leaves_the_rest_of_the_database_untouched(
    reimport: tuple[list[str], list[str]],
    main_run: ImportRun,
    db_credentials: DatabaseCredentials,
) -> None:
    """Every table holding none of that bundle's rows is byte-identical to its golden.

    That is every mult table, and every table the dictionary and finalization steps
    write. The mult tables are where the upsert lands, so this is the assertion that
    says the update half of the upsert reproduced what the insert half wrote, ids
    included: a second write of a value the table already holds updates its row rather
    than adding a second one under a new id.
    """
    _holding, untouched = reimport
    differences = {}
    for table in untouched:
        expected = golden_io.read_golden(fixture_layout.GOLDENS_DIR, table)
        actual = golden_io.serialize_table(db_credentials, main_run.schema, table)
        if actual != expected:
            differences[table] = _unified_diff(table, expected, actual)
    assert differences == {}


def test_reimport_rewrites_the_bundles_rows_unchanged(
    reimport: tuple[list[str], list[str]],
    main_run: ImportRun,
    db_credentials: DatabaseCredentials,
) -> None:
    """Every table holding that bundle's rows still holds exactly the same rows.

    Not the same *ids*: the pipeline hands out row ids from the largest already present
    and deletes the bundle's old rows only afterwards, so a re-imported bundle is
    renumbered above everything else in the table by construction. Nothing else may
    move -- no row gained, lost, or given a different value -- which is what comparing
    with `golden_io.without_surrogate_ids` asks.
    """
    holding, _untouched = reimport
    differences = {}
    for table in holding:
        expected = golden_io.without_surrogate_ids(
            golden_io.read_golden(fixture_layout.GOLDENS_DIR, table)
        )
        actual = golden_io.without_surrogate_ids(
            golden_io.serialize_table(db_credentials, main_run.schema, table)
        )
        if actual != expected:
            differences[table] = _unified_diff(table, expected, actual)
    assert differences == {}


def test_the_reimport_reached_the_tables_that_hold_the_bundle(
    reimport: tuple[list[str], list[str]],
) -> None:
    """The two assertions above divide the tables between them, and neither half is empty.

    Without this, a bundle id that matched nothing would leave the first assertion
    covering every table and the second covering none, and both would pass.
    """
    holding, untouched = reimport
    assert len(holding) > 0
    assert len(untouched) > 0
