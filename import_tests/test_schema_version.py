"""The schema version row: who writes it, who leaves it alone, and when it refuses.

The main run's golden covers the row a finished import writes. These tests need a schema
whose row they can change, so they share one of their own: a single bundle imported and
not finished. Each test puts the version table in the state it needs before it runs, so
any of them runs alone. The erase, which leaves nothing for the others, has a schema of
its own. Each step is a real ``opus_import`` invocation, and its log directory is its
own, since a refusal here is meant to log an error.
"""

from __future__ import annotations

import contextlib
import os
import subprocess  # nosec B404
import sys
from typing import TYPE_CHECKING, Any

import pytest

from import_tests.tools import build_run, fixture_layout, golden_io, negative_cases
from opus_import.schema_version import (
    SCHEMA_STATE_APPENDING,
    SCHEMA_STATE_READY,
    SCHEMA_VERSION,
    SCHEMA_VERSION_TABLE,
)

if TYPE_CHECKING:
    from import_tests.tools.golden_io import DatabaseCredentials

#: The schema case these tests run under.
_CASE = 'schema_version'

#: A version no release has, for the refusal.
_OTHER_VERSION = SCHEMA_VERSION + 1000

#: Loads the WSGI entry point as a web server would, and prints what it would call.
_LOAD_WSGI = 'import opus_app.wsgi as w; print(type(w.application).__name__)'

#: Loads the WSGI entry point and serves it one request, printing the status, then the
#: body on the following lines.
_SERVE_ONE = (
    'import opus_app.wsgi as w\n'
    'statuses = []\n'
    "body = b''.join(w.application({'REQUEST_METHOD': 'GET', 'PATH_INFO': '/'}, "
    'lambda status, headers: statuses.append(status)))\n'
    'print(statuses[0])\n'
    'print(body.decode())\n'
)

#: What `_LOAD_WSGI` prints when the entry point serves Django.
_DJANGO_HANDLER = 'WSGIHandler'


@pytest.fixture(scope='module')
def unfinished_run(
    tmp_path_factory: pytest.TempPathFactory,
    db_credentials: DatabaseCredentials,
    created_schemas: list[str],
    subprocess_coverage: None,
) -> build_run.ImportRun:
    """Import one bundle and stop before the steps that finish the schema.

    Returns:
        The run, in a schema and a log directory of its own.
    """
    root = tmp_path_factory.mktemp('mini_holdings_schema_version')
    bundle = negative_cases.bundle_for_class(negative_cases.DUPLICATE_ID_INSTRUMENT_CLASS)
    schema = fixture_layout.schema_name(os.getpid(), _CASE)
    created_schemas.append(schema)
    return build_run.perform_run(
        root, schema, db_credentials, bundle_groups=[[bundle]], finalize=False
    )


@pytest.fixture(scope='module')
def erase_run(
    tmp_path_factory: pytest.TempPathFactory,
    db_credentials: DatabaseCredentials,
    created_schemas: list[str],
    subprocess_coverage: None,
) -> build_run.ImportRun:
    """Import one bundle into a schema of its own, for the erase to empty.

    Returns:
        The run.
    """
    root = tmp_path_factory.mktemp('mini_holdings_schema_version_erase')
    bundle = negative_cases.bundle_for_class(negative_cases.DUPLICATE_ID_INSTRUMENT_CLASS)
    schema = fixture_layout.schema_name(os.getpid(), f'{_CASE}_erase')
    created_schemas.append(schema)
    return build_run.perform_run(
        root, schema, db_credentials, bundle_groups=[[bundle]], finalize=False
    )


def _step(run: build_run.ImportRun, *arguments: str) -> build_run.StepResult:
    """Run one ``opus_import`` invocation against the run's schema.

    Parameters:
        run: The run.
        arguments: The options.

    Returns:
        What the invocation did.
    """
    return build_run.run_pipeline_step(run.paths.config_file, arguments)


def _query(
    credentials: DatabaseCredentials, schema: str, statement: str, *params: Any
) -> list[tuple[Any, ...]]:
    """Run one statement on the run's schema, committing it.

    Parameters:
        credentials: How to reach the server.
        schema: The schema.
        statement: The SQL.
        params: Values for its placeholders.

    Returns:
        Its rows.
    """
    with contextlib.closing(golden_io.connect(credentials, schema)) as connection:
        with contextlib.closing(connection.cursor()) as cursor:
            cursor.execute(statement, params or None)
            rows = list(cursor.fetchall())
        connection.commit()
    return rows


def _rows(credentials: DatabaseCredentials, schema: str) -> list[tuple[Any, ...]] | None:
    """Return the schema's version rows, or None when it has no version table.

    Parameters:
        credentials: How to reach the server.
        schema: The schema.

    Returns:
        The ``(version, state)`` rows, or None.
    """
    exists = _query(
        credentials,
        schema,
        'SELECT COUNT(*) FROM information_schema.TABLES WHERE TABLE_SCHEMA = %s '
        'AND TABLE_NAME = %s',
        schema,
        SCHEMA_VERSION_TABLE,
    )[0][0]
    if exists == 0:
        return None
    return _query(credentials, schema, f'SELECT version, state FROM {SCHEMA_VERSION_TABLE}')


def _wsgi_application(run: build_run.ImportRun) -> str:
    """Load the web application's entry point against the run's schema, in a process.

    Parameters:
        run: The run.

    Returns:
        The class name of what the web server would call.
    """
    finished = subprocess.run(  # nosec B603 - this interpreter and a fixed program
        [sys.executable, '-c', _LOAD_WSGI],
        env=build_run.run_environment(run.paths.config_file),
        capture_output=True,
        text=True,
        check=True,
    )
    return finished.stdout.strip().splitlines()[-1]


def _serve_one(run: build_run.ImportRun) -> tuple[str, str]:
    """Load the entry point against the run's schema, in a process, and make one request.

    Parameters:
        run: The run.

    Returns:
        The response's status and body.
    """
    finished = subprocess.run(  # nosec B603 - this interpreter and a fixed program
        [sys.executable, '-c', _SERVE_ONE],
        env=build_run.run_environment(run.paths.config_file),
        capture_output=True,
        text=True,
        check=True,
    )
    status, _, body = finished.stdout.partition('\n')
    return status, body


def _no_table(credentials: DatabaseCredentials, schema: str) -> None:
    """Drop the schema's version table, if it has one.

    Parameters:
        credentials: How to reach the server.
        schema: The schema.
    """
    _query(credentials, schema, f'DROP TABLE IF EXISTS {SCHEMA_VERSION_TABLE}')


def _row(
    run: build_run.ImportRun, credentials: DatabaseCredentials, version: int, state: str
) -> None:
    """Give the schema exactly one version row.

    Parameters:
        run: The run.
        credentials: How to reach the server.
        version: The row's version.
        state: The row's state.
    """
    _no_table(credentials, run.schema)
    assert _step(run, *build_run.VERSION_ARGS).returncode == 0
    _query(
        credentials,
        run.schema,
        f'UPDATE {SCHEMA_VERSION_TABLE} SET version = %s, state = %s',
        version,
        state,
    )


def _errors(run: build_run.ImportRun) -> str:
    """Return what the run's error log holds so far.

    Parameters:
        run: The run.

    Returns:
        The log's text, empty when there is none.
    """
    path = run.paths.errors_log
    return path.read_text(encoding='utf-8') if path.exists() else ''


def test_the_finishing_steps_alone_write_no_row(
    unfinished_run: build_run.ImportRun, db_credentials: DatabaseCredentials
) -> None:
    """``--cleanup-aux-tables`` and ``--import-dictionary`` leave the schema unservable."""
    _no_table(db_credentials, unfinished_run.schema)
    for step in (build_run.AUX_ARGS, build_run.DICTIONARY_ARGS, build_run.VALIDATE_ARGS):
        assert _step(unfinished_run, *step).returncode == 0
    assert _rows(db_credentials, unfinished_run.schema) is None


def test_the_web_application_refuses_a_schema_with_no_row(
    unfinished_run: build_run.ImportRun, db_credentials: DatabaseCredentials
) -> None:
    """The entry point answers 503, naming the missing row and the remedy."""
    _no_table(db_credentials, unfinished_run.schema)
    status, body = _serve_one(unfinished_run)
    assert status.startswith('503')
    assert f'no {SCHEMA_VERSION_TABLE} row' in body
    assert 'opus_import --write-schema-version' in body


def test_the_step_writes_this_version_ready(
    unfinished_run: build_run.ImportRun, db_credentials: DatabaseCredentials
) -> None:
    """With no table, the step creates it and inserts the release's version, ``ready``."""
    _no_table(db_credentials, unfinished_run.schema)
    assert _step(unfinished_run, *build_run.VERSION_ARGS).returncode == 0
    assert _rows(db_credentials, unfinished_run.schema) == [(SCHEMA_VERSION, SCHEMA_STATE_READY)]


def test_the_web_application_serves_a_finished_schema(
    unfinished_run: build_run.ImportRun, db_credentials: DatabaseCredentials
) -> None:
    """Once the row is written, the entry point is Django's own application."""
    _row(unfinished_run, db_credentials, SCHEMA_VERSION, SCHEMA_STATE_READY)
    assert _wsgi_application(unfinished_run) == _DJANGO_HANDLER


def test_running_it_again_changes_nothing(
    unfinished_run: build_run.ImportRun, db_credentials: DatabaseCredentials
) -> None:
    """A finished schema stays as it is."""
    _row(unfinished_run, db_credentials, SCHEMA_VERSION, SCHEMA_STATE_READY)
    assert _step(unfinished_run, *build_run.VERSION_ARGS).returncode == 0
    assert _rows(db_credentials, unfinished_run.schema) == [(SCHEMA_VERSION, SCHEMA_STATE_READY)]


def test_an_appending_row_of_this_version_becomes_ready(
    unfinished_run: build_run.ImportRun, db_credentials: DatabaseCredentials
) -> None:
    """The step is the only writer of ``ready``, and it finishes an append."""
    schema = unfinished_run.schema
    _row(unfinished_run, db_credentials, SCHEMA_VERSION, SCHEMA_STATE_APPENDING)
    assert _step(unfinished_run, *build_run.VERSION_ARGS).returncode == 0
    assert _rows(db_credentials, schema) == [(SCHEMA_VERSION, SCHEMA_STATE_READY)]


def test_another_version_is_refused_and_left_alone(
    unfinished_run: build_run.ImportRun, db_credentials: DatabaseCredentials
) -> None:
    """A schema another release imported is never restamped."""
    schema = unfinished_run.schema
    _row(unfinished_run, db_credentials, _OTHER_VERSION, SCHEMA_STATE_READY)
    logged = len(_errors(unfinished_run))
    result = _step(unfinished_run, *build_run.VERSION_ARGS)
    assert result.returncode != 0
    assert f'The schema is version {_OTHER_VERSION}' in _errors(unfinished_run)[logged:]
    assert _rows(db_credentials, schema) == [(_OTHER_VERSION, SCHEMA_STATE_READY)]


def test_the_erase_drops_the_table(
    erase_run: build_run.ImportRun, db_credentials: DatabaseCredentials
) -> None:
    """``--drop-permanent-tables --scorched-earth`` leaves no version row behind."""
    _row(erase_run, db_credentials, SCHEMA_VERSION, SCHEMA_STATE_READY)
    assert _step(erase_run, *build_run.DROP_ARGS).returncode == 0
    assert _rows(db_credentials, erase_run.schema) is None


def test_a_read_only_run_does_not_create_an_absent_schema(
    unfinished_run: build_run.ImportRun,
    db_credentials: DatabaseCredentials,
    created_schemas: list[str],
) -> None:
    """The deploy check's read of a schema the server lacks fails and creates nothing."""
    absent = fixture_layout.schema_name(os.getpid(), f'{_CASE}_absent')
    # Dropped on the way out should a failure here leave it behind.
    created_schemas.append(absent)
    logged = len(_errors(unfinished_run))
    result = _step(unfinished_run, '--read-only', '--override-db-schema', absent, '--validate-perm')
    assert result.returncode != 0
    assert f'"{absent}" does not exist' in _errors(unfinished_run)[logged:]
    assert not _query(
        db_credentials,
        unfinished_run.schema,
        'SELECT schema_name FROM information_schema.schemata WHERE schema_name = %s',
        absent,
    )
