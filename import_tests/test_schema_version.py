"""The schema version row: who writes it, who leaves it alone, and when it refuses.

The main run's golden covers the row a finished import writes. These tests need a schema
whose row they can change, so they share one of their own: a single bundle imported and
not finished, then taken through the steps one by one, in the order the tests below run.
Each step is a real ``opus_import`` invocation, and its log directory is its own, since a
refusal here is meant to log an error.
"""

from __future__ import annotations

import contextlib
import os
import subprocess  # nosec B404
import sys
from typing import TYPE_CHECKING, Any

import pytest

from import_tests.tools import build_run, fixture_layout, golden_io, negative_cases
from opus_import.schema_version import SCHEMA_VERSION, STATE_APPENDING, STATE_READY, TABLE_NAME

if TYPE_CHECKING:
    from import_tests.tools.golden_io import DatabaseCredentials

#: The schema case these tests run under.
_CASE = 'schema_version'

#: A version no release has, for the refusal.
_OTHER_VERSION = SCHEMA_VERSION + 1000

#: Loads the WSGI entry point as a web server would, and prints what it would call.
_LOAD_WSGI = 'import opus_app.wsgi as w; print(type(w.application).__name__)'

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
        TABLE_NAME,
    )[0][0]
    if exists == 0:
        return None
    return _query(credentials, schema, f'SELECT version, state FROM {TABLE_NAME}')


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
    for step in (build_run.AUX_ARGS, build_run.DICTIONARY_ARGS, build_run.VALIDATE_ARGS):
        assert _step(unfinished_run, *step).returncode == 0
    assert _rows(db_credentials, unfinished_run.schema) is None


def test_the_web_application_refuses_a_schema_with_no_row(
    unfinished_run: build_run.ImportRun,
) -> None:
    """The entry point serves the 503 stub rather than Django."""
    assert _wsgi_application(unfinished_run) != _DJANGO_HANDLER


def test_the_step_writes_this_version_ready(
    unfinished_run: build_run.ImportRun, db_credentials: DatabaseCredentials
) -> None:
    """With no table, the step creates it and inserts the release's version, ``ready``."""
    assert _step(unfinished_run, *build_run.VERSION_ARGS).returncode == 0
    assert _rows(db_credentials, unfinished_run.schema) == [(SCHEMA_VERSION, STATE_READY)]


def test_the_web_application_serves_a_finished_schema(
    unfinished_run: build_run.ImportRun,
) -> None:
    """Once the row is written, the entry point is Django's own application."""
    assert _wsgi_application(unfinished_run) == _DJANGO_HANDLER


def test_running_it_again_changes_nothing(
    unfinished_run: build_run.ImportRun, db_credentials: DatabaseCredentials
) -> None:
    """A finished schema stays as it is."""
    assert _step(unfinished_run, *build_run.VERSION_ARGS).returncode == 0
    assert _rows(db_credentials, unfinished_run.schema) == [(SCHEMA_VERSION, STATE_READY)]


def test_an_appending_row_of_this_version_becomes_ready(
    unfinished_run: build_run.ImportRun, db_credentials: DatabaseCredentials
) -> None:
    """The step is the only writer of ``ready``, and it finishes an append."""
    schema = unfinished_run.schema
    _query(db_credentials, schema, f'UPDATE {TABLE_NAME} SET state = %s', STATE_APPENDING)
    assert _step(unfinished_run, *build_run.VERSION_ARGS).returncode == 0
    assert _rows(db_credentials, schema) == [(SCHEMA_VERSION, STATE_READY)]


def test_another_version_is_refused_and_left_alone(
    unfinished_run: build_run.ImportRun, db_credentials: DatabaseCredentials
) -> None:
    """A schema another release imported is never restamped."""
    schema = unfinished_run.schema
    _query(db_credentials, schema, f'UPDATE {TABLE_NAME} SET version = %s', _OTHER_VERSION)
    logged = len(_errors(unfinished_run))
    result = _step(unfinished_run, *build_run.VERSION_ARGS)
    assert result.returncode != 0
    assert f'The schema is version {_OTHER_VERSION}' in _errors(unfinished_run)[logged:]
    assert _rows(db_credentials, schema) == [(_OTHER_VERSION, STATE_READY)]


def test_the_erase_drops_the_table(
    unfinished_run: build_run.ImportRun, db_credentials: DatabaseCredentials
) -> None:
    """``--drop-permanent-tables --scorched-earth`` leaves no version row behind."""
    assert _step(unfinished_run, *build_run.DROP_ARGS).returncode == 0
    assert _rows(db_credentials, unfinished_run.schema) is None
