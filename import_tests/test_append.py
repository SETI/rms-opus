"""The append path against a server: replacing and adding bundles, and failing part way.

Each case starts from a copy of the main run's finished schema, which has a version row
and so takes the append, and runs real ``opus_import`` invocations against it, each case
with a configuration and a log directory of its own. A failure is made with the import's
test-only fault, ``OPUS_IMPORT_FAULT=log_error:<bundle>``, at which the import logs one
error inside that bundle and carries on. The fresh import's own case is a small run of
its own.
"""

from __future__ import annotations

import os
import subprocess  # nosec B404
import sys
from dataclasses import dataclass
from typing import TYPE_CHECKING

import pytest

from import_tests.tools import build_run, fixture_layout, golden_io, negative_cases
from opus_import import import_fault
from opus_import.schema_version import (
    SCHEMA_STATE_APPENDING,
    SCHEMA_STATE_READY,
    SCHEMA_VERSION,
    SCHEMA_VERSION_TABLE,
)
from opus_import.steps import do_import

if TYPE_CHECKING:
    from import_tests.tools.golden_io import DatabaseCredentials

#: Loads the WSGI entry point and serves it one request, printing the status.
_SERVE_ONE = (
    'import opus_app.wsgi as w\n'
    'statuses = []\n'
    "b''.join(w.application({'REQUEST_METHOD': 'GET', 'PATH_INFO': '/'}, "
    'lambda status, headers: statuses.append(status)))\n'
    'print(statuses[0])\n'
)


@dataclass
class _Copy:
    """A copy of the main run's schema, with a configuration and logs of its own.

    Attributes:
        schema: The copy.
        paths: Its configuration file and log directory, over the main run's tree.
    """

    schema: str
    paths: build_run.RunPaths

    def step(self, *arguments: str) -> build_run.StepResult:
        """Run one ``opus_import`` invocation against the copy.

        Parameters:
            arguments: The options.

        Returns:
            What the invocation did.
        """
        return build_run.run_pipeline_step(self.paths.config_file, arguments)

    def errors(self) -> str:
        """Return what the copy's error log holds so far."""
        path = self.paths.errors_log
        return path.read_text(encoding='utf-8') if path.exists() else ''


def _copy(
    main_run: build_run.ImportRun,
    credentials: DatabaseCredentials,
    created_schemas: list[str],
    case: str,
) -> _Copy:
    """Copy the main run's finished schema for one case.

    Parameters:
        main_run: The main run.
        credentials: How to reach the server.
        created_schemas: The session's schemas, which the copy joins.
        case: What distinguishes the copy's schema, configuration and logs.

    Returns:
        The copy.
    """
    schema = fixture_layout.schema_name(os.getpid(), case)
    created_schemas.append(schema)
    build_run.clone_schema(credentials, main_run.schema, schema)
    paths = build_run.sibling_paths(main_run, case)
    build_run.write_opus_config(paths, schema, credentials)
    return _Copy(schema, paths)


def _version_rows(credentials: DatabaseCredentials, schema: str) -> list[tuple[int, str]] | None:
    """Return a schema's version rows, or None when it has no version table."""
    if SCHEMA_VERSION_TABLE not in golden_io.list_tables(credentials, schema):
        return None
    return [
        (int(version), str(state))
        for version, state in golden_io.query(
            credentials, schema, f'SELECT version, state FROM {SCHEMA_VERSION_TABLE}'
        )
    ]


def _registry(credentials: DatabaseCredentials, schema: str, *bundles: str) -> dict[str, str]:
    """Return the registry's states of the given bundles, leaving out any it lacks."""
    return {
        str(bundle): str(state)
        for bundle, state in golden_io.query(
            credentials, schema, 'SELECT bundle_id, state FROM import_bundle'
        )
        if bundle in bundles
    }


def _rows_of(credentials: DatabaseCredentials, schema: str, bundle: str) -> int:
    """Return how many ``obs_general`` rows a bundle has."""
    query = 'SELECT COUNT(*) FROM obs_general WHERE bundle_id = %s'
    return int(golden_io.query(credentials, schema, query, [bundle])[0][0])


def _plant_cart_rows(credentials: DatabaseCredentials, schema: str, *bundles: str) -> None:
    """Put one cart row in the copy for every observation of the given bundles."""
    placeholders = ', '.join(['%s'] * len(bundles))
    connection = golden_io.connect(credentials, schema)
    try:
        cursor = connection.cursor()
        cursor.execute(
            'INSERT INTO cart (session_id, obs_general_id, opus_id, recycled) '
            "SELECT 'append', id, opus_id, 0 FROM obs_general "
            f'WHERE bundle_id IN ({placeholders})',  # nosec B608 - placeholders only
            bundles,
        )
        connection.commit()
    finally:
        connection.close()


def _cart_bundles(credentials: DatabaseCredentials, schema: str) -> set[str]:
    """Return the bundles whose observations the copy's cart rows name."""
    query = 'SELECT DISTINCT g.bundle_id FROM cart c JOIN obs_general g ON g.id = c.obs_general_id'
    return {str(bundle) for (bundle,) in golden_io.query(credentials, schema, query)}


def _cart_rows(credentials: DatabaseCredentials, schema: str) -> int:
    """Return how many rows the copy's cart holds."""
    return int(golden_io.query(credentials, schema, 'SELECT COUNT(*) FROM cart')[0][0])


def _serves(copy: _Copy) -> str:
    """Load the web application against the copy, in a process, and return one status."""
    finished = subprocess.run(  # nosec B603 - this interpreter and a fixed program
        [sys.executable, '-c', _SERVE_ONE],
        env=build_run.run_environment(copy.paths.config_file),
        capture_output=True,
        text=True,
        check=True,
    )
    return finished.stdout.strip().splitlines()[-1]


def _failing(monkeypatch: pytest.MonkeyPatch, bundle: str) -> None:
    """Make the invocations that follow log an error inside `bundle`."""
    monkeypatch.setenv(
        import_fault.IMPORT_FAULT_ENV_VAR, f'{do_import.LOG_ERROR_FAULT_SITE}:{bundle}'
    )


def test_an_append_that_replaces_one_bundle_and_adds_one_matches_a_fresh_import(
    main_run: build_run.ImportRun,
    db_credentials: DatabaseCredentials,
    created_schemas: list[str],
) -> None:
    """Every table ends as the full fresh import's goldens hold it, ids aside.

    The added bundle is removed first with ``--delete-bundles``, so the append adds its
    rows back; the replaced one is deleted and loaded again. A table holding bundles'
    rows is compared without its server-numbered columns, since both bundles are
    renumbered; every other table, the mult tables among them, exactly. The mult values
    the added bundle brings stay in their tables through the deletion, since mult rows
    are never deleted, so this shows the append's rows and finalization, not an append
    writing a mult value the schema has never held.

    Before the append, the cart names every observation of the replaced bundle and of
    one the append leaves alone; straight after it, before finalization re-creates the
    cart, only the second bundle's rows remain, removed by the cart's cascade when the
    replaced bundle was deleted.
    """
    copy = _copy(main_run, db_credentials, created_schemas, 'append')
    replaced, added = main_run.bundles[0], main_run.bundles[-1]
    kept = next(bundle for bundle in main_run.bundles if bundle not in (replaced, added))
    assert copy.step('--delete-bundles', added).returncode == 0
    assert _rows_of(db_credentials, copy.schema, added) == 0
    assert _version_rows(db_credentials, copy.schema) == [(SCHEMA_VERSION, SCHEMA_STATE_APPENDING)]
    _plant_cart_rows(db_credentials, copy.schema, replaced, kept)
    planted = _cart_rows(db_credentials, copy.schema)
    assert _cart_bundles(db_credentials, copy.schema) == {replaced, kept}
    appended = copy.step(*build_run.IMPORT_ARGS, f'{replaced},{added}')
    assert appended.returncode == 0, appended.stderr
    assert f'{do_import.IMPORT_PATH_PREFIX}{do_import.IMPORT_PATH_APPEND}' in appended.stdout
    assert _cart_bundles(db_credentials, copy.schema) == {kept}
    assert _cart_rows(db_credentials, copy.schema) == planted - _rows_of(
        db_credentials, copy.schema, replaced
    )
    for closing in build_run.closing_steps(copy.paths.config_file):
        assert closing.returncode == 0, closing.stderr
    assert copy.errors() == ''

    differences = {}
    for table in golden_io.goldened_tables(fixture_layout.GOLDENS_DIR):
        expected = golden_io.read_golden(fixture_layout.GOLDENS_DIR, table)
        actual = golden_io.serialize_table(db_credentials, copy.schema, table)
        if golden_io.holds_observations(expected.splitlines()[0].split('\t')):
            expected = golden_io.without_surrogate_ids(expected)
            actual = golden_io.without_surrogate_ids(actual)
        if actual != expected:
            differences[table] = actual[:2000]
    assert differences == {}


def _plant_orphans(credentials: DatabaseCredentials, schema: str, tables: tuple[str, ...]) -> int:
    """Copy one row of each table to the observation id above ``obs_general``'s highest.

    The copies are what a run that stopped partway through an index leaves: rows of a
    child loaded before their ``obs_general`` rows were. They are written with foreign
    keys unchecked, as the import loads.

    Parameters:
        credentials: How to reach the server.
        schema: The schema to plant them in.
        tables: The tables to copy a row of.

    Returns:
        The id they name.
    """
    connection = golden_io.connect(credentials, schema)
    try:
        cursor = connection.cursor()
        cursor.execute('SELECT MAX(id) + 1 FROM obs_general')
        (orphan_id,) = cursor.fetchone()
        cursor.execute('SET SESSION foreign_key_checks = 0')
        for table in tables:
            cursor.execute(f'CREATE TEMPORARY TABLE `plant` AS SELECT * FROM `{table}` LIMIT 1')  # nosec B608 - a fixed table name
            cursor.execute('UPDATE `plant` SET `obs_general_id` = %s', [orphan_id])
            if table == 'obs_files':
                cursor.execute('UPDATE `plant` SET `file_number` = 1')
            cursor.execute(f'INSERT INTO `{table}` SELECT * FROM `plant`')  # nosec B608
            cursor.execute('DROP TEMPORARY TABLE `plant`')
        connection.commit()
    finally:
        connection.close()
    return int(orphan_id)


def test_rows_left_above_obs_generals_highest_id_are_removed_before_a_bundle_loads(
    main_run: build_run.ImportRun,
    db_credentials: DatabaseCredentials,
    created_schemas: list[str],
) -> None:
    """A child's rows with no ``obs_general`` row, above its highest id, go first.

    The bundle's ids are handed out again from ``obs_general``'s highest, so its first
    observation takes the id the planted rows name: the import succeeds only if they are
    removed before its rows load, and validation then finds no row without its
    ``obs_general`` row.
    """
    copy = _copy(main_run, db_credentials, created_schemas, 'append_orphans')
    added = main_run.bundles[-1]
    assert copy.step('--delete-bundles', added).returncode == 0
    orphan_id = _plant_orphans(db_credentials, copy.schema, ('obs_files', 'obs_pds'))
    appended = copy.step(*build_run.IMPORT_ARGS, added)
    assert appended.returncode == 0, appended.stderr
    (owner,) = golden_io.query(
        db_credentials, copy.schema, 'SELECT bundle_id FROM obs_general WHERE id = %s', [orphan_id]
    )[0]
    assert owner == added
    for closing in build_run.closing_steps(copy.paths.config_file):
        assert closing.returncode == 0, closing.stderr
    assert copy.errors() == ''
    assert _rows_of(db_credentials, copy.schema, added) == _rows_of(
        db_credentials, main_run.schema, added
    )


def test_a_failed_append_stays_appending_until_a_rerun_resumes_it(
    main_run: build_run.ImportRun,
    db_credentials: DatabaseCredentials,
    created_schemas: list[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The closing invocations refuse, the web application refuses, and a rerun finishes it."""
    copy = _copy(main_run, db_credentials, created_schemas, 'append_failed')
    first, second = main_run.bundles[0], main_run.bundles[1]
    _failing(monkeypatch, second)
    failed = copy.step(*build_run.IMPORT_ARGS, f'{first},{second}')
    monkeypatch.delenv(import_fault.IMPORT_FAULT_ENV_VAR)
    assert failed.returncode != 0
    assert _registry(db_credentials, copy.schema, first, second) == {
        first: 'done',
        second: 'failed',
    }
    assert _version_rows(db_credentials, copy.schema) == [(SCHEMA_VERSION, SCHEMA_STATE_APPENDING)]
    assert _serves(copy).startswith('503')

    logged = len(copy.errors())
    finalize = copy.step(*build_run.AUX_ARGS)
    assert finalize.returncode != 0
    assert f'{second} (failed)' in finalize.stdout
    assert copy.step(*build_run.VALIDATE_ARGS).returncode == 0
    version = copy.step(*build_run.VERSION_ARGS)
    assert version.returncode != 0
    assert f'{second} (failed)' in version.stdout
    assert '--write-schema-version refuses' in copy.errors()[logged:]
    assert _version_rows(db_credentials, copy.schema) == [(SCHEMA_VERSION, SCHEMA_STATE_APPENDING)]

    resumed = copy.step(*build_run.IMPORT_ARGS)
    assert resumed.returncode == 0, resumed.stderr
    assert f'Resuming the unfinished bundles of an earlier append: {second}' in resumed.stdout
    for closing in build_run.closing_steps(copy.paths.config_file):
        assert closing.returncode == 0, closing.stderr
    assert _registry(db_credentials, copy.schema, first, second) == {first: 'done', second: 'done'}
    assert _version_rows(db_credentials, copy.schema) == [(SCHEMA_VERSION, SCHEMA_STATE_READY)]
    assert _rows_of(db_credentials, copy.schema, second) == _rows_of(
        db_credentials, main_run.schema, second
    )


def test_deleting_the_failed_bundle_lets_the_schema_be_finished_without_it(
    main_run: build_run.ImportRun,
    db_credentials: DatabaseCredentials,
    created_schemas: list[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """``--delete-bundles`` removes its rows and its registry row, and the schema ends ready."""
    copy = _copy(main_run, db_credentials, created_schemas, 'append_deleted')
    first, second = main_run.bundles[0], main_run.bundles[1]
    _failing(monkeypatch, second)
    assert copy.step(*build_run.IMPORT_ARGS, f'{first},{second}').returncode != 0
    monkeypatch.delenv(import_fault.IMPORT_FAULT_ENV_VAR)
    assert copy.step('--delete-bundles', second).returncode == 0
    for closing in build_run.closing_steps(copy.paths.config_file):
        assert closing.returncode == 0, closing.stderr
    assert _version_rows(db_credentials, copy.schema) == [(SCHEMA_VERSION, SCHEMA_STATE_READY)]
    assert _registry(db_credentials, copy.schema, first, second) == {first: 'done'}
    assert _rows_of(db_credentials, copy.schema, second) == 0


def test_ignore_errors_records_the_failing_bundle_done(
    main_run: build_run.ImportRun,
    db_credentials: DatabaseCredentials,
    created_schemas: list[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Under ``--ignore-errors`` neither --finalize nor the version step refuses."""
    copy = _copy(main_run, db_credentials, created_schemas, 'append_ignored')
    first, second = main_run.bundles[0], main_run.bundles[1]
    _failing(monkeypatch, second)
    ignored = copy.step(*build_run.IMPORT_ARGS, '--ignore-errors', f'{first},{second}')
    monkeypatch.delenv(import_fault.IMPORT_FAULT_ENV_VAR)
    assert ignored.returncode == 0, ignored.stderr
    assert _registry(db_credentials, copy.schema, first, second) == {first: 'done', second: 'done'}
    for closing in build_run.closing_steps(copy.paths.config_file):
        assert closing.returncode == 0, closing.stderr
    assert _version_rows(db_credentials, copy.schema) == [(SCHEMA_VERSION, SCHEMA_STATE_READY)]


def test_a_fresh_import_with_a_failed_bundle_writes_no_version_row(
    tmp_path_factory: pytest.TempPathFactory,
    db_credentials: DatabaseCredentials,
    created_schemas: list[str],
    subprocess_coverage: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The registry gates a fresh import as it gates an append."""
    bundle = negative_cases.bundle_for_class(negative_cases.DUPLICATE_ID_INSTRUMENT_CLASS)
    schema = fixture_layout.schema_name(os.getpid(), 'fresh_failed')
    created_schemas.append(schema)
    _failing(monkeypatch, bundle)
    run = build_run.perform_run(
        tmp_path_factory.mktemp('mini_holdings_fresh_failed'),
        schema,
        db_credentials,
        bundle_groups=[[bundle]],
        finalize=False,
    )
    monkeypatch.delenv(import_fault.IMPORT_FAULT_ENV_VAR)
    assert run.steps[-1].returncode != 0
    assert _registry(db_credentials, schema, bundle) == {bundle: 'failed'}
    version = build_run.run_pipeline_step(run.paths.config_file, build_run.VERSION_ARGS)
    assert version.returncode != 0
    assert f'{bundle} (failed)' in version.stdout
    assert _version_rows(db_credentials, schema) is None
