"""Every table the import writes, compared row by row against a recorded run.

From an empty database the import is deterministic: ids are handed out in table order
from the highest already present. So a difference between a golden and a run is a change
in behavior rather than noise.

The goldens are not quite the whole of the expected output, and both gaps are deliberate
and guarded here. A few tables are excused by name with a written reason, and a column
that another column rebuilds is dropped rather than stored twice -- with the rebuilding
asserted against the database, so dropping it costs bytes and not coverage.

Which tables are compared is otherwise a rule, not a list: everything the schema holds
except the tables ``manage.py migrate`` created. A table the import newly writes shows up
here as a golden that does not exist, and one it stops writing as a golden nothing
produced.

The re-import assertions at the end carry a normalization of their own, and say so where
they make it: importing a bundle a second time renumbers that bundle's rows, because ids
are handed out from the highest already present and the old rows are deleted only
afterwards.
"""

from __future__ import annotations

import difflib
import re
from typing import TYPE_CHECKING

import pytest

from import_tests.tools import build_run, fixture_layout, golden_io, holdings_survey, run_logs

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

#: How many rows on each side the report hands to `difflib`, starting at the first row
#: that differs. difflib compares the whole of both sequences before it yields anything,
#: and ``obs_files`` has ten thousand rows: a change that moves most of them would spend
#: minutes building a report of which only the first `DIFF_LINE_LIMIT` lines are printed.
#: A report that takes longer than the job it runs in is a report nobody reads.
DIFF_WINDOW = 400


def _first_difference(expected: list[str], actual: list[str]) -> int:
    """Return the index of the first line the two sides disagree on.

    Parameters:
        expected: The golden's lines.
        actual: The run's lines.

    Returns:
        The first index where they differ, or the length of the shorter one when the
        shorter is a prefix of the longer.
    """
    for index, (left, right) in enumerate(zip(expected, actual, strict=False)):
        if left != right:
            return index
    return min(len(expected), len(actual))


def _unified_diff(table: str, expected: str, actual: str) -> str:
    """Return a readable difference between a golden and what the run produced.

    Parameters:
        table: The table's name.
        expected: The golden text.
        actual: The serialized table.

    Returns:
        A unified diff of at most `DIFF_WINDOW` rows on each side, starting at the first
        row that differs, so a failure reads as rows rather than as a boolean. The header
        states both row counts, so a truncated view still says how big the change is.
    """
    expected_lines = expected.splitlines()
    actual_lines = actual.splitlines()
    start = _first_difference(expected_lines, actual_lines)
    lines = [
        f'{table}: {len(expected_lines)} golden lines, {len(actual_lines)} run lines, '
        f'first difference at line {start + 1}',
        *difflib.unified_diff(
            expected_lines[start : start + DIFF_WINDOW],
            actual_lines[start : start + DIFF_WINDOW],
            fromfile=f'golden/{table}',
            tofile=f'run/{table}',
            lineterm='',
        ),
    ]
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
    return golden_io.tables_to_golden(db_credentials, main_run.schema, main_run.django_tables)


def test_goldens_cover_exactly_the_tables_the_run_wrote(run_tables: list[str]) -> None:
    """No table escapes comparison, and no golden describes a table nothing writes."""
    assert sorted(GOLDENED_TABLES) == sorted(run_tables)


def test_the_migration_created_tables_to_exclude(main_run: ImportRun) -> None:
    """The migration created some tables, which is what the golden exclusion is for.

    A migration that created nothing would mean the exclusion is measuring the wrong
    thing, and every Django table would then arrive as an unexplained extra table.
    """
    assert len(main_run.django_tables) > 0


def test_every_excused_table_is_one_the_run_writes(
    main_run: ImportRun, db_credentials: DatabaseCredentials
) -> None:
    """No entry in the excused list names a table the import no longer produces.

    An entry that excuses nothing is the same defect as a whitelist line that admits
    nothing: it is a claim about the run that has stopped being true, and it would go on
    excusing whatever later took that name.

    Existing is not enough, so the rows are counted too. An excused table that the step
    creates and then fills with nothing looks identical to a healthy one from the
    schema's point of view, and no golden is watching it.
    """
    written = set(golden_io.list_tables(db_credentials, main_run.schema))
    missing = sorted(set(golden_io.EXCLUDED_TABLES) - written)
    assert missing == []
    empty = sorted(
        table
        for table in golden_io.EXCLUDED_TABLES
        if int(
            golden_io.query(db_credentials, main_run.schema, f'SELECT COUNT(*) FROM `{table}`')[0][
                0
            ]
        )
        == 0
    )
    assert empty == []


def test_no_excused_table_is_also_goldened() -> None:
    """A table cannot be both excused from comparison and compared.

    Without this, deleting an entry's reason while leaving its golden in place -- or the
    reverse -- would leave the two halves disagreeing with nothing to say so.
    """
    assert sorted(set(golden_io.EXCLUDED_TABLES) & set(GOLDENED_TABLES)) == []


def test_every_excused_table_gives_a_reason() -> None:
    """Each exclusion is a judgement call, so each one is written down and justified."""
    unexplained = sorted(
        table for table, reason in golden_io.EXCLUDED_TABLES.items() if len(reason.strip()) == 0
    )
    assert unexplained == []


#: How to rebuild each column the goldens drop, from columns they keep.
#:
#: A column may be dropped only if it can be re-derived, and this is where the derivation
#: is written down and run. Without it `golden_io.DERIVED_COLUMNS` would be a way to
#: delete coverage silently: naming a genuinely independent column there and regenerating
#: would leave the suite green with the values gone. The check costs no golden bytes,
#: which is the whole point of dropping the column in the first place.
DERIVATIONS = {
    ('obs_files', 'url'): (
        "CONCAT(CASE pds_version WHEN 3 THEN %s WHEN 4 THEN %s END, '/', logical_path)",
        [fixture_layout.PDS3_ROOT_NAME, fixture_layout.PDS4_ROOT_NAME],
    ),
}


def test_every_dropped_column_has_a_derivation() -> None:
    """No column is dropped without a rule for rebuilding it, and none is left over."""
    dropped = {
        (table, column)
        for table, columns in golden_io.DERIVED_COLUMNS.items()
        for column in columns
    }
    assert sorted(dropped) == sorted(DERIVATIONS)


def test_no_derivation_rebuilds_a_column_from_itself() -> None:
    """A derivation has to use other columns, or it proves nothing.

    ``('checksum', [])`` would satisfy every other check here -- ``WHERE checksum <>
    checksum`` selects no rows whatever the values are -- and would delete that column's
    coverage while looking like it had kept it. That is the failure the derivation table
    exists to prevent, so it must not be able to pass through it.
    """
    circular = sorted(
        (table, column)
        for (table, column), (expression, _parameters) in DERIVATIONS.items()
        if re.search(rf'\b{re.escape(column)}\b', expression)
    )
    assert circular == []


@pytest.mark.parametrize(('table', 'column'), sorted(DERIVATIONS))
def test_a_dropped_column_still_holds_what_it_is_derived_from(
    table: str, column: str, main_run: ImportRun, db_credentials: DatabaseCredentials
) -> None:
    """Every row's dropped column is exactly what the golden's own columns rebuild.

    ``obs_files.url`` is the case this exists for, and it is not merely pdsfile's answer
    repeated: pdsfile serves a file from an HTML root that *begins* with a slash, and
    ``do_import_index`` strips it. That strip is this repository's behavior, and dropping
    the column from the golden left nothing observing it -- the expected-products
    comparison never reads ``url``, it re-derives the same path itself and compares that
    against the recorder. So the derivation is asserted here instead, against the
    database, where it costs nothing to store.
    """
    expression, parameters = DERIVATIONS[table, column]
    rows = golden_io.query(
        db_credentials,
        main_run.schema,
        f'SELECT `{column}`, {expression} FROM `{table}` '
        f'WHERE NOT (`{column}` <=> {expression}) LIMIT 5',
        [*parameters, *parameters],
    )
    assert rows == []


@pytest.mark.parametrize(('table', 'column'), sorted(DERIVATIONS))
def test_the_derivation_check_is_looking_at_rows(
    table: str, column: str, main_run: ImportRun, db_credentials: DatabaseCredentials
) -> None:
    """The table the derivation is checked against is not empty.

    A comparison over no rows passes, and would go on passing if the import stopped
    writing the table entirely.
    """
    rows = golden_io.query(db_credentials, main_run.schema, f'SELECT COUNT(*) FROM `{table}`')
    assert int(rows[0][0]) > 0


@pytest.mark.parametrize('table', GOLDENED_TABLES)
def test_table_matches_its_golden(
    table: str, main_run: ImportRun, db_credentials: DatabaseCredentials
) -> None:
    """One table's rows are exactly what a clean recorded run produced.

    The assertion is on the report rather than on the two texts, deliberately: pytest
    explains a failed ``==`` between two strings with ``difflib.ndiff``, which on
    ``obs_files``' ten thousand rows takes longer than the job it runs in. `_unified_diff`
    is the bounded report that replaces it.
    """
    expected = golden_io.read_golden(fixture_layout.GOLDENS_DIR, table)
    actual = golden_io.serialize_table(db_credentials, main_run.schema, table)
    difference = None if actual == expected else _unified_diff(table, expected, actual)
    assert difference is None, difference


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

    The invocation's own status is checked here rather than left to the assertions below,
    because a re-import that died on startup leaves the database exactly as the first
    import left it -- and all three of those assertions pass on a database nothing
    touched. This fixture is the only place that can tell "unchanged because the update
    path is correct" from "unchanged because nothing ran".

    Returns:
        The tables holding the re-imported bundle's rows, and the tables holding none of
        them, each sorted.

    Raises:
        AssertionError: If the re-import invocation exited non-zero or logged an error.
    """
    bundle = reimport_bundle_id(main_run)
    step = build_run.reimport_bundle(main_run, bundle, db_credentials)
    assert step.returncode == 0, f'the re-import exited {step.returncode}: {step.stderr[-2000:]}'
    errors_log = build_run.reimport_paths(main_run).errors_log
    assert errors_log.is_file(), f'the re-import wrote no log to {errors_log}'
    errors = run_logs.distinct(run_logs.read_messages(errors_log))
    assert errors == [], errors
    holding = golden_io.tables_holding_bundle(db_credentials, main_run.schema, run_tables, bundle)
    return sorted(holding), sorted(set(run_tables) - holding)


def test_reimport_leaves_the_rest_of_the_database_untouched(
    reimport: tuple[list[str], list[str]],
    main_run: ImportRun,
    db_credentials: DatabaseCredentials,
) -> None:
    """Every table holding none of that bundle's rows is byte-identical to its golden.

    That is every mult table, and every table the finalization and dictionary steps write
    that carries no bundle of its own. The mult tables are where the upsert lands, so this is the assertion that
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
