"""The fresh import against a server: the keys it leaves, and the states it passes through.

The main run is imported fresh and finalized, so its schema is where the keys are
checked: every observation and mult table carries exactly the keys its schema file
declares, read back from ``information_schema`` and matched by kind and ordered columns.
The goldens record tables, columns and primary keys only, so they prove the data and not
the keys.

The rest runs one sequence on a schema of its own: two bundles imported fresh by two
invocations, a copy of two observations planted under higher ids (one under another
bundle, one under the same), ``--finalize``, then an import into the finalized but
unstamped schema, which is refused, then two of its keys dropped, as an interrupted
finalization leaves them, and ``--finalize`` again. Each test reads what one stage left.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

import pytest

from import_tests.tools import build_run, fixture_layout, golden_io, run_logs
from opus_import import import_util
from opus_import.steps import do_import
from opus_import.table_keys import (
    TableKey,
    add_secondary_indexes,
    create_time_keys,
    is_key_filtered_table,
)

if TYPE_CHECKING:
    from import_tests.tools.golden_io import DatabaseCredentials

#: The schema case the sequence runs under.
_CASE = 'fresh'

#: The two bundles the sequence imports, one invocation each.
_FIRST_BUNDLE = 'GO_0011'
_SECOND_BUNDLE = 'COISS_2055'

#: How far a planted copy's child-table ids are moved, past every id the fixture holds.
_CHILD_ID_OFFSET = 1_000_000

#: Where the packaged table schemas are.
_SCHEMA_DIR = Path(str(import_util.TABLE_SCHEMA_DIR))


def _schema_for(table: str) -> list[dict[str, Any]]:
    """Return the schema an observation or mult table was created from.

    Parameters:
        table: The table's name.

    Returns:
        Its schema file's entries, the templates standing for the per-target surface
        geometry tables and the mult tables.
    """
    if table.startswith('mult_'):
        name = 'mult_template'
    elif table.startswith('obs_surface_geometry__'):
        name = 'obs_surface_geometry_target'
    else:
        name = table
    schema: list[dict[str, Any]] = json.loads(
        (_SCHEMA_DIR / f'{name}.json').read_text(encoding='utf-8')
    )
    return schema


def _server_keys(credentials: DatabaseCredentials, schema: str) -> dict[str, set[TableKey]]:
    """Return every observation and mult table's keys, as ``information_schema`` lists them.

    Parameters:
        credentials: How to reach the server.
        schema: The schema to read.

    Returns:
        Each table's keys, keyed by table name.
    """
    indexes: dict[tuple[str, str], tuple[str, list[str]]] = {}
    for table, index, non_unique, column in golden_io.query(
        credentials,
        None,
        'SELECT TABLE_NAME, INDEX_NAME, NON_UNIQUE, COLUMN_NAME FROM information_schema.STATISTICS '
        'WHERE TABLE_SCHEMA = %s ORDER BY TABLE_NAME, INDEX_NAME, SEQ_IN_INDEX',
        [schema],
    ):
        kind = 'primary' if index == 'PRIMARY' else 'key' if int(non_unique) else 'unique'
        indexes.setdefault((table, index), (kind, []))[1].append(column)
    keys: dict[str, set[TableKey]] = {}
    for (table, _index), (kind, columns) in indexes.items():
        keys.setdefault(table, set()).add(TableKey(kind, tuple(columns)))  # type: ignore[arg-type]
    foreign: dict[tuple[str, str], tuple[str, list[str], list[str]]] = {}
    for table, constraint, column, ref_table, ref_column in golden_io.query(
        credentials,
        None,
        'SELECT TABLE_NAME, CONSTRAINT_NAME, COLUMN_NAME, REFERENCED_TABLE_NAME, '
        'REFERENCED_COLUMN_NAME FROM information_schema.KEY_COLUMN_USAGE '
        'WHERE TABLE_SCHEMA = %s AND REFERENCED_TABLE_NAME IS NOT NULL '
        'ORDER BY TABLE_NAME, CONSTRAINT_NAME, ORDINAL_POSITION',
        [schema],
    ):
        entry = foreign.setdefault((table, constraint), (ref_table, [], []))
        entry[1].append(column)
        entry[2].append(ref_column)
    for (table, _constraint), (ref_table, columns, ref_columns) in foreign.items():
        keys.setdefault(table, set()).add(
            TableKey('foreign', tuple(columns), (ref_table, tuple(ref_columns)))
        )
    return {table: found for table, found in keys.items() if is_key_filtered_table(table)}


def _key_differences(credentials: DatabaseCredentials, schema: str) -> dict[str, Any]:
    """Return each observation or mult table whose keys are not exactly what it declares.

    Parameters:
        credentials: How to reach the server.
        schema: The schema to read.

    Returns:
        For each such table, the keys missing and the keys extra; empty when every table
        carries exactly the keys created with it plus the keys finalization adds.
    """
    differences: dict[str, Any] = {}
    tables = [t for t in golden_io.list_tables(credentials, schema) if is_key_filtered_table(t)]
    found = _server_keys(credentials, schema)
    for table in tables:
        declared = _schema_for(table)
        expected = {*create_time_keys(table, declared), *add_secondary_indexes(table, declared)}
        have = found.get(table, set())
        if have != expected:
            differences[table] = {
                'missing': sorted(map(TableKey.describe, expected - have)),
                'extra': sorted(map(TableKey.describe, have - expected)),
            }
    return differences


def test_the_finalized_schema_carries_exactly_the_declared_keys(
    main_run: build_run.ImportRun, db_credentials: DatabaseCredentials
) -> None:
    """Every observation and mult table of the main run, after finalization."""
    assert _key_differences(db_credentials, main_run.schema) == {}


def test_every_main_run_import_took_the_fresh_path(main_run: build_run.ImportRun) -> None:
    """Each bundle invocation logged its path, and it was the fresh import's."""
    import_steps = [step for step in main_run.steps if '--import' in step.arguments]
    assert import_steps != []
    for step in import_steps:
        assert f'{do_import.IMPORT_PATH_PREFIX}{do_import.IMPORT_PATH_FRESH}' in step.stdout


@dataclass
class _Planted:
    """One observation copied under a higher id.

    Attributes:
        original_id: The observation's ``obs_general`` id.
        copy_id: The copy's.
        opus_id: The OPUS id they share.
        bundle: The bundle the copy claims.
        rows: How many rows the observation has in each table, keyed by table.
    """

    original_id: int
    copy_id: int
    opus_id: str
    bundle: str
    rows: dict[str, int] = field(default_factory=dict)


@dataclass
class _Sequence:
    """What each stage of the sequence left.

    Attributes:
        run: The two import invocations.
        imported_rows: Each bundle's ``obs_general`` rows after them, keyed by bundle.
        planted: The two copies: under another bundle, then under the same one.
        finalize: The first ``--finalize``.
        rows_after_finalize: Each planted observation's rows per table after it, keyed
            by ``obs_general`` id.
        refused: The import into the finalized, unstamped schema.
        before_refusal: Every table's row count and checksum before it.
        after_refusal: The same, after it.
        keys_before_refusal: The server's keys before it.
        keys_after_refusal: The same, after it.
        dropped_keys: The keys dropped before the second ``--finalize``.
        recovery: The second ``--finalize``.
    """

    run: build_run.ImportRun
    imported_rows: dict[str, int]
    planted: list[_Planted]
    finalize: build_run.StepResult
    rows_after_finalize: dict[int, dict[str, int]]
    refused: build_run.StepResult
    before_refusal: dict[str, tuple[int, int]]
    after_refusal: dict[str, tuple[int, int]]
    keys_before_refusal: dict[str, set[TableKey]]
    keys_after_refusal: dict[str, set[TableKey]]
    dropped_keys: list[str]
    recovery: build_run.StepResult


def _observation_tables(credentials: DatabaseCredentials, schema: str) -> list[str]:
    """Return the schema's observation tables, ``obs_general`` first."""
    tables = [t for t in golden_io.list_tables(credentials, schema) if t.startswith('obs_')]
    return ['obs_general', *sorted(t for t in tables if t != 'obs_general')]


def _rows_of(credentials: DatabaseCredentials, schema: str, obs_general_id: int) -> dict[str, int]:
    """Return how many rows one observation has in each observation table."""
    counts = {}
    for table in _observation_tables(credentials, schema):
        column = 'id' if table == 'obs_general' else 'obs_general_id'
        (count,) = golden_io.query(
            credentials,
            schema,
            f'SELECT COUNT(*) FROM `{table}` WHERE `{column}` = %s',
            [obs_general_id],
        )[0]
        counts[table] = int(count)
    return counts


def _plant_copy(
    credentials: DatabaseCredentials, schema: str, original_id: int, copy_id: int, bundle: str
) -> _Planted:
    """Copy one observation's rows in every table under a new ``obs_general`` id.

    Parameters:
        credentials: How to reach the server.
        schema: The schema.
        original_id: The observation to copy.
        copy_id: The copy's ``obs_general`` id, above every existing one.
        bundle: The bundle the copy claims.

    Returns:
        The copy.
    """
    (opus_id,) = golden_io.query(
        credentials, schema, 'SELECT opus_id FROM obs_general WHERE id = %s', [original_id]
    )[0]
    planted = _Planted(original_id, copy_id, str(opus_id), bundle)
    planted.rows = _rows_of(credentials, schema, original_id)
    connection = golden_io.connect(credentials, schema)
    try:
        cursor = connection.cursor()
        for table in _observation_tables(credentials, schema):
            if table == 'obs_general':
                where, assign = '`id` = %s', '`id` = %s, `bundle_id` = %s'
                params = [copy_id, bundle]
            else:
                # A child keyed on its observation takes the copy's id; the surface
                # geometry tables, which number their own rows and hold the bundle, move
                # their ids clear of the originals' and name the bundle too.
                where = '`obs_general_id` = %s'
                columns = {
                    name for name, _type in golden_io.table_columns(credentials, schema, table)
                }
                parts, params = ['`obs_general_id` = %s'], [copy_id]
                if 'id' in columns:
                    parts.insert(0, '`id` = `id` + %s')
                    params.insert(0, _CHILD_ID_OFFSET + copy_id)
                if 'bundle_id' in columns:
                    parts.append('`bundle_id` = %s')
                    params.append(bundle)
                assign = ', '.join(parts)
            cursor.execute(
                f'CREATE TEMPORARY TABLE `plant` AS SELECT * FROM `{table}` WHERE {where}',
                [original_id],
            )
            cursor.execute(f'UPDATE `plant` SET {assign}', params)
            cursor.execute(f'INSERT INTO `{table}` SELECT * FROM `plant`')
            cursor.execute('DROP TEMPORARY TABLE `plant`')
        connection.commit()
    finally:
        connection.close()
    return planted


def _snapshot(credentials: DatabaseCredentials, schema: str) -> dict[str, tuple[int, int]]:
    """Return every table's row count and checksum."""
    snapshot = {}
    for table in golden_io.list_tables(credentials, schema):
        (count,) = golden_io.query(credentials, schema, f'SELECT COUNT(*) FROM `{table}`')[0]
        (_name, checksum) = golden_io.query(credentials, schema, f'CHECKSUM TABLE `{table}`')[0]
        snapshot[table] = (int(count), int(checksum or 0))
    return snapshot


def _drop_two_keys(credentials: DatabaseCredentials, schema: str) -> list[str]:
    """Drop one plain key and one foreign key, as an interrupted finalization leaves them.

    Returns:
        What was dropped.
    """
    (constraint,) = golden_io.query(
        credentials,
        None,
        'SELECT CONSTRAINT_NAME FROM information_schema.REFERENTIAL_CONSTRAINTS '
        "WHERE CONSTRAINT_SCHEMA = %s AND TABLE_NAME = 'obs_pds'",
        [schema],
    )[0]
    (index,) = golden_io.query(
        credentials,
        None,
        'SELECT INDEX_NAME FROM information_schema.STATISTICS WHERE TABLE_SCHEMA = %s '
        "AND TABLE_NAME = 'obs_general' AND COLUMN_NAME = 'opus_id'",
        [schema],
    )[0]
    golden_io.execute(credentials, schema, f'ALTER TABLE `obs_pds` DROP FOREIGN KEY `{constraint}`')
    golden_io.execute(credentials, schema, f'ALTER TABLE `obs_general` DROP KEY `{index}`')
    return [f'obs_pds: {constraint}', f'obs_general: {index}']


@pytest.fixture(scope='module')
def sequence(
    tmp_path_factory: pytest.TempPathFactory,
    db_credentials: DatabaseCredentials,
    created_schemas: list[str],
    subprocess_coverage: None,
) -> _Sequence:
    """Run the sequence, recording what each stage left.

    Returns:
        The stages' results.
    """
    root = tmp_path_factory.mktemp('mini_holdings_fresh')
    schema = fixture_layout.schema_name(os.getpid(), _CASE)
    created_schemas.append(schema)
    run = build_run.perform_run(
        root,
        schema,
        db_credentials,
        bundle_groups=[[_FIRST_BUNDLE], [_SECOND_BUNDLE]],
        finalize=False,
    )
    imported_rows = {
        bundle: int(
            golden_io.query(
                db_credentials,
                schema,
                'SELECT COUNT(*) FROM obs_general WHERE bundle_id = %s',
                [bundle],
            )[0][0]
        )
        for bundle in (_FIRST_BUNDLE, _SECOND_BUNDLE)
    }
    first_ids = [
        int(row[0])
        for row in golden_io.query(
            db_credentials,
            schema,
            'SELECT id FROM obs_general WHERE bundle_id = %s ORDER BY id LIMIT 2',
            [_FIRST_BUNDLE],
        )
    ]
    (top,) = golden_io.query(db_credentials, schema, 'SELECT MAX(id) FROM obs_general')[0]
    planted = [
        _plant_copy(db_credentials, schema, first_ids[0], int(top) + 1, _SECOND_BUNDLE),
        _plant_copy(db_credentials, schema, first_ids[1], int(top) + 2, _FIRST_BUNDLE),
    ]

    def step(*arguments: str) -> build_run.StepResult:
        """Run one invocation against the sequence's schema."""
        return build_run.run_pipeline_step(run.paths.config_file, arguments)

    finalize = step('--finalize')
    rows_after = {
        obs_id: _rows_of(db_credentials, schema, obs_id)
        for copy in planted
        for obs_id in (copy.original_id, copy.copy_id)
    }
    before = _snapshot(db_credentials, schema)
    keys_before = _server_keys(db_credentials, schema)
    refused = step('--import', _FIRST_BUNDLE)
    after = _snapshot(db_credentials, schema)
    keys_after = _server_keys(db_credentials, schema)
    dropped = _drop_two_keys(db_credentials, schema)
    recovery = step('--finalize')
    return _Sequence(
        run=run,
        imported_rows=imported_rows,
        planted=planted,
        finalize=finalize,
        rows_after_finalize=rows_after,
        refused=refused,
        before_refusal=before,
        after_refusal=after,
        keys_before_refusal=keys_before,
        keys_after_refusal=keys_after,
        dropped_keys=dropped,
        recovery=recovery,
    )


def test_a_second_invocation_keeps_the_first_invocations_bundles(
    sequence: _Sequence, main_run: build_run.ImportRun, db_credentials: DatabaseCredentials
) -> None:
    """Both invocations took the fresh path, and both bundles are whole afterwards."""
    for step in sequence.run.steps[1:]:
        assert step.returncode == 0, step.stderr
        assert f'{do_import.IMPORT_PATH_PREFIX}{do_import.IMPORT_PATH_FRESH}' in step.stdout
    query = 'SELECT COUNT(*) FROM obs_general WHERE bundle_id = %s'
    for bundle in (_FIRST_BUNDLE, _SECOND_BUNDLE):
        clean = golden_io.query(db_credentials, main_run.schema, query, [bundle])[0][0]
        assert sequence.imported_rows[bundle] == clean, bundle


def test_the_duplicate_step_keeps_each_copy_and_deletes_each_original(sequence: _Sequence) -> None:
    """The higher id wins in every table; the original's rows are gone from every table."""
    assert sequence.finalize.returncode == 0, sequence.finalize.stderr
    for copy in sequence.planted:
        assert sequence.rows_after_finalize[copy.copy_id] == copy.rows
        assert set(sequence.rows_after_finalize[copy.original_id].values()) == {0}


def test_the_duplicate_step_logs_another_bundle_at_info_and_the_same_bundle_as_a_warning(
    sequence: _Sequence,
) -> None:
    """A copy from another bundle is expected; one from the same bundle is a data fault."""
    other, same = sequence.planted
    warnings = run_logs.read_messages(sequence.run.paths.warnings_log)
    other_line = (
        f'Duplicate OPUS ID "{other.opus_id}": keeping obs_general id {other.copy_id} from '
        f'{other.bundle}, deleting id {other.original_id} from {_FIRST_BUNDLE}'
    )
    same_line = (
        f'Duplicate OPUS ID "{same.opus_id}": keeping obs_general id {same.copy_id} from '
        f'{same.bundle}, deleting id {same.original_id} from {_FIRST_BUNDLE}'
    )
    assert other_line in sequence.finalize.stdout
    assert not any(other_line in message for message in warnings)
    assert any(same_line in message for message in warnings)


def test_an_import_into_an_interrupted_finalization_is_refused_and_changes_nothing(
    sequence: _Sequence,
) -> None:
    """No version row but finalization's keys: the import exits with failure, naming --finalize."""
    assert sequence.refused.returncode != 0
    assert '--finalize' in sequence.refused.stdout
    assert sequence.after_refusal == sequence.before_refusal
    assert sequence.keys_after_refusal == sequence.keys_before_refusal


def test_a_finalization_only_rerun_completes_an_interrupted_finalization(
    sequence: _Sequence, db_credentials: DatabaseCredentials
) -> None:
    """The keys an interruption left out are added, and every table's keys are whole again."""
    assert len(sequence.dropped_keys) == 2
    assert sequence.recovery.returncode == 0, sequence.recovery.stderr
    assert _key_differences(db_credentials, sequence.run.schema) == {}
