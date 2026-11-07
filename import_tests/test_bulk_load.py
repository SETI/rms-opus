"""The bulk load against a real server: what it stores, and what it refuses.

`ImportDBMySQL.bulk_load_rows` writes rows as text for ``LOAD DATA LOCAL INFILE`` to read,
and `insert_rows` sends them as statement parameters. The two must store the same values,
which only a server can say, so the round trip here writes one set of rows both ways into
two tables and reads both back. Matching the driver's own text is not the goal -- its
float rendering differs from ``repr`` -- matching what the server stores is.

A load behaves as though ``IGNORE`` were given, so a duplicate key and a value too long
for its column would otherwise load with a warning. The two tests after the round trip
are the check that each raises instead, with nothing of the chunk left behind.

The last tests read the import runs' logs: the main run, whose goldens are only evidence
about the bulk load if its rows went through it, and the session with ``bulk_load =
false``, which is the path an import takes when the server refuses local files.
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING, Any

import pytest

from import_tests.tools import fixture_layout, golden_io, negative_cases, run_logs
from opus_import import importdb
from opus_import.importdb.mysql import (
    BULK_LOAD_PATH_FILE,
    BULK_LOAD_PATH_INSERT,
    BULK_LOAD_PATH_PREFIX,
    ImportDBMySQL,
)
from opus_import.importdb.super import ImportDBError

if TYPE_CHECKING:
    from collections.abc import Iterator

    from import_tests.tools.build_run import ImportRun
    from import_tests.tools.golden_io import DatabaseCredentials

#: One column per field type the packaged schemas use (the set
#: ``tests/opus_import/test_importdb_mysql.py`` checks against the schemas), under the
#: name of its type.
_COLUMNS: list[dict[str, Any]] = [
    {'field_name': 'id', 'field_type': 'uint4', 'field_key': 'primary', 'field_notnull': True},
    {'field_name': 'f_char', 'field_type': 'char40'},
    {'field_name': 'f_varchar', 'field_type': 'varchar255'},
    {'field_name': 'f_text', 'field_type': 'text'},
    {'field_name': 'f_datetime', 'field_type': 'datetime'},
    {'field_name': 'f_timestamp', 'field_type': 'timestamp'},
    {'field_name': 'f_enum', 'field_type': 'enum', 'field_enum_options': "'Y','N'"},
    {'field_name': 'f_flag_onoff', 'field_type': 'flag_onoff'},
    {'field_name': 'f_flag_yesno', 'field_type': 'flag_yesno'},
    {'field_name': 'f_int1', 'field_type': 'int1'},
    {'field_name': 'f_int2', 'field_type': 'int2'},
    {'field_name': 'f_int4', 'field_type': 'int4'},
    {'field_name': 'f_uint2', 'field_type': 'uint2'},
    {'field_name': 'f_uint4', 'field_type': 'uint4'},
    {'field_name': 'f_mult_idx', 'field_type': 'mult_idx'},
    {'field_name': 'f_real4', 'field_type': 'real4'},
    {'field_name': 'f_real8', 'field_type': 'real8'},
    {'field_name': 'f_json', 'field_type': 'json'},
    {'field_name': 'f_mult_list', 'field_type': 'mult_list'},
]

_ROWS: list[dict[str, Any]] = [
    {
        'id': 1,
        'f_char': 'COISS_2002',
        'f_varchar': 'co-iss-n1460960653',
        'f_text': 'Cassini ISS',
        'f_datetime': '2026-11-06 12:34:56',
        'f_timestamp': '2026-11-06 12:34:56',
        'f_enum': 'Y',
        'f_flag_onoff': 1,
        'f_flag_yesno': 0,
        'f_int1': -128,
        'f_int2': -32768,
        'f_int4': -2147483648,
        'f_uint2': 65535,
        'f_uint4': 4294967295,
        'f_mult_idx': 17,
        'f_real4': 0.1,
        'f_real8': 0.1,
        'f_json': '{"a": [1, 2.5, null], "b": "x"}',
        'f_mult_list': '["SATURN", "S RINGS"]',
    },
    {
        'id': 2,
        'f_char': 'tab\there',
        'f_varchar': 'back\\slash and \\N and NULL',
        'f_text': 'line\nbreak, return\r, nul\0 and ° degrees',
        'f_datetime': None,
        'f_timestamp': None,
        'f_enum': None,
        'f_flag_onoff': None,
        'f_flag_yesno': None,
        'f_int1': None,
        'f_int2': None,
        'f_int4': None,
        'f_uint2': None,
        'f_uint4': None,
        'f_mult_idx': None,
        'f_real4': -0.0,
        'f_real8': 1.7976931348623157e308,
        'f_json': '{"tab": "a\\tb", "quote": "\\"", "slash": "\\\\"}',
        'f_mult_list': None,
    },
    {
        'id': 3,
        'f_char': '',
        'f_varchar': '\\',
        'f_text': '\\\\N',
        'f_datetime': '1970-01-01 00:00:01',
        'f_timestamp': '2030-01-01 00:00:00',
        'f_enum': 'N',
        'f_flag_onoff': 0,
        'f_flag_yesno': 1,
        'f_int1': 127,
        'f_int2': 32767,
        'f_int4': 2147483647,
        'f_uint2': 0,
        'f_uint4': 0,
        'f_mult_idx': 0,
        'f_real4': 3.4e38,
        'f_real8': 2.2250738585072014e-308,
        'f_json': '[]',
        'f_mult_list': '["N/A"]',
    },
]


@pytest.fixture(scope='module')
def bulk_db(
    db_credentials: DatabaseCredentials, created_schemas: list[str]
) -> Iterator[ImportDBMySQL]:
    """Open a backend on a schema of its own, loading two rows to a transaction.

    Yields:
        The backend, which has chosen the bulk-load path.
    """
    schema = fixture_layout.schema_name(os.getpid(), 'bulk_load')
    created_schemas.append(schema)
    db = importdb.get_db(
        'MySQL',
        db_credentials.host,
        '',
        schema,
        db_credentials.user,
        db_credentials.password,
        transaction_rows=2,
    )
    assert isinstance(db, ImportDBMySQL)
    yield db
    db.conn.close()


def _read_back(db: ImportDBMySQL, table: str) -> list[tuple[Any, ...]]:
    return list(db.general_select(f'* FROM {db.quote_identifier(table)} ORDER BY `id`'))


def test_the_backend_chose_the_bulk_load_path(bulk_db: ImportDBMySQL) -> None:
    """Every test below exercises the file path only if the server accepted it."""
    assert bulk_db.bulk_load_path == BULK_LOAD_PATH_FILE


def test_bulk_load_stores_what_insert_statements_store(bulk_db: ImportDBMySQL) -> None:
    """One row set, written both ways, reads back the same from both tables."""
    bulk_db.create_table('perm', 'round_trip_bulk', _COLUMNS)
    bulk_db.create_table('perm', 'round_trip_insert', _COLUMNS)

    bulk_db.bulk_load_rows('perm', 'round_trip_bulk', _ROWS)
    bulk_db.insert_rows('perm', 'round_trip_insert', _ROWS)

    loaded = _read_back(bulk_db, 'round_trip_bulk')
    inserted = _read_back(bulk_db, 'round_trip_insert')
    assert len(loaded) == len(_ROWS)
    assert loaded == inserted
    # And each string came back as written, escapes undone.
    text_columns = [column['field_name'] for column in _COLUMNS][1:4]
    for row, stored in zip(_ROWS, loaded, strict=True):
        assert [stored[1 + n] for n in range(3)] == [row[name] for name in text_columns]


def test_a_duplicate_key_raises_and_loads_nothing(bulk_db: ImportDBMySQL) -> None:
    """The load would skip the second row with a warning; the check raises instead."""
    bulk_db.create_table('perm', 'duplicate_key', _COLUMNS[:2])
    rows = [{'id': 1, 'f_char': 'first'}, {'id': 1, 'f_char': 'second'}]

    with pytest.raises(ImportDBError, match=r"1 skipped.*Duplicate entry '1'"):
        bulk_db.bulk_load_rows('perm', 'duplicate_key', rows)

    assert _read_back(bulk_db, 'duplicate_key') == []


def test_a_truncated_value_raises_and_loads_nothing(bulk_db: ImportDBMySQL) -> None:
    """The load would cut the value short with a warning; the check raises instead."""
    columns = [_COLUMNS[0], {'field_name': 'short', 'field_type': 'char3'}]
    bulk_db.create_table('perm', 'truncated_value', columns)
    rows = [{'id': 1, 'short': 'abc'}, {'id': 2, 'short': 'abcdef'}]

    with pytest.raises(ImportDBError, match="Data truncated for column 'short'"):
        bulk_db.bulk_load_rows('perm', 'truncated_value', rows)

    assert _read_back(bulk_db, 'truncated_value') == []


def _bulk_load_paths(run: ImportRun) -> list[str]:
    """Return every bulk-load path a run's import log names, in order."""
    return [
        message.removeprefix(BULK_LOAD_PATH_PREFIX)
        for import_log in run.paths.import_logs
        for message in run_logs.read_messages(import_log)
        if message.startswith(BULK_LOAD_PATH_PREFIX)
    ]


def test_the_main_run_bulk_loaded_every_bundle(main_run: ImportRun) -> None:
    """The goldens speak for the bulk load only if every invocation took its path."""
    paths = _bulk_load_paths(main_run)
    assert len(paths) > 0
    assert set(paths) == {BULK_LOAD_PATH_FILE}


def test_the_insert_path_run_says_which_path_it_took(insert_path_run: ImportRun) -> None:
    """With bulk loading switched off, the log says so and names the reason."""
    paths = _bulk_load_paths(insert_path_run)
    assert set(paths) == {f'{BULK_LOAD_PATH_INSERT} ([import] bulk_load is false)'}


def test_the_insert_path_run_ran_cleanly(insert_path_run: ImportRun) -> None:
    """Every invocation exited zero and nothing was logged as an error."""
    assert [step.returncode for step in insert_path_run.steps] == [0] * len(insert_path_run.steps)
    assert run_logs.read_messages(insert_path_run.paths.errors_log) == []


def test_the_insert_path_run_imported_the_observations(
    insert_path_run: ImportRun, main_run: ImportRun, db_credentials: DatabaseCredentials
) -> None:
    """Writing with INSERT statements keeps every observation the bulk load writes."""
    bundle = negative_cases.bundle_for_class(negative_cases.DUPLICATE_ID_INSTRUMENT_CLASS)
    counts = [
        golden_io.query(
            db_credentials,
            run.schema,
            'SELECT COUNT(*) FROM `obs_general` WHERE `bundle_id` = %s',
            [bundle],
        )[0][0]
        for run in (insert_path_run, main_run)
    ]
    assert counts[0] == counts[1]
    assert counts[0] > 0
