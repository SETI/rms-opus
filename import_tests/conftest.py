"""Fixtures for the mini-holdings suite: one import run, and its database schemas.

The suite is one long import followed by fast assertions, so the run is session-scoped
and every test reads the same database. `import_tests.tools.build_run` does all the work;
this is a thin wrapper over it.

Every schema a session creates is dropped when the session ends, pass or fail: a failed
run's evidence is its logs and its golden differences, never a schema parked on the
server. The schema names carry the pytest session's process id, because the collision to
defend against is one developer running two worktrees against one MySQL server at once,
which a user name cannot tell apart.
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

import pytest

from import_tests.tools import build_run, fixture_layout, negative_cases
from import_tests.tools.db_credentials import resolve_credentials

if TYPE_CHECKING:
    from collections.abc import Iterator

    from import_tests.tools.golden_io import DatabaseCredentials


@pytest.fixture(scope='session')
def db_credentials() -> DatabaseCredentials:
    """Return how to reach the MySQL server the suite imports into.

    Returns:
        The credentials the ``OPUS_TEST_DB_*`` variables name, or the ones the
        ``OPUS_CONFIG`` file holds when they name none.
        `import_tests.tools.db_credentials` is where that order is decided.
    """
    return resolve_credentials()


@pytest.fixture(scope='session')
def created_schemas(db_credentials: DatabaseCredentials) -> Iterator[list[str]]:
    """Record every schema this session creates, and drop them all on the way out.

    Yields:
        The list each run appends its schema name to.
    """
    schemas: list[str] = []
    yield schemas
    for schema in schemas:
        build_run.drop_schema(db_credentials, schema)


@pytest.fixture(scope='session')
def subprocess_coverage() -> Iterator[None]:
    """Measure the pipeline's subprocesses too, and leave nothing behind afterwards.

    Coverage reaches a subprocess through a ``.pth`` file in a site directory, which is
    installed only while a measured session is running: left there, it would make every
    later interpreter in that environment import coverage at startup.

    Yields:
        Nothing; the fixture exists for what it installs and removes.
    """
    pth_path = build_run.install_subprocess_coverage()
    yield
    if pth_path is not None:
        pth_path.unlink(missing_ok=True)


@pytest.fixture(scope='session')
def main_run(
    tmp_path_factory: pytest.TempPathFactory,
    db_credentials: DatabaseCredentials,
    created_schemas: list[str],
    subprocess_coverage: None,
) -> build_run.ImportRun:
    """Import the whole fixture once, and hand every test the finished run.

    Returns:
        The completed run, whose logs and schema the assertions read.
    """
    schema = fixture_layout.schema_name(os.getpid())
    created_schemas.append(schema)
    root = tmp_path_factory.mktemp('mini_holdings_main')
    return build_run.perform_run(root, schema, db_credentials)


@pytest.fixture(scope='session')
def duplicate_id_run(
    tmp_path_factory: pytest.TempPathFactory,
    db_credentials: DatabaseCredentials,
    created_schemas: list[str],
    subprocess_coverage: None,
) -> build_run.ImportRun:
    """Import one volume twice in a single invocation, under the duplicate-id check.

    One invocation is what makes this a duplicate: the import tables are dropped once
    per invocation, so a second volume in the same invocation sees the first volume's
    rows and finds its own OPUS ids already there. That is the situation the flag exists
    for, and importing the same volume twice produces it for every observation.

    Returns:
        The completed run, in a schema and a log directory of its own.
    """
    root = tmp_path_factory.mktemp('mini_holdings_dupid')
    bundle = negative_cases.bundle_for_class(negative_cases.DUPLICATE_ID_INSTRUMENT_CLASS)
    schema = fixture_layout.schema_name(os.getpid(), negative_cases.DUPLICATE_ID_CASE)
    created_schemas.append(schema)
    return build_run.perform_run(
        root,
        schema,
        db_credentials,
        bundle_groups=[[bundle, bundle]],
        extra_import_args=['--import-check-duplicate-id'],
        finalize=False,
    )


@pytest.fixture(scope='session')
def ignore_errors_run(
    tmp_path_factory: pytest.TempPathFactory,
    db_credentials: DatabaseCredentials,
    created_schemas: list[str],
    subprocess_coverage: None,
) -> build_run.ImportRun:
    """Import a fixture whose index names a target OPUS does not know.

    Returns:
        A run of the one perturbed bundle under ``--import-ignore-errors``, in a schema
        and a log directory of its own.
    """
    root = tmp_path_factory.mktemp('mini_holdings_ignore_errors')
    recipe = negative_cases.load_recipe(negative_cases.IGNORE_ERRORS_CASE)
    overlay = negative_cases.build_overlay(recipe, root / 'overlay')
    schema = fixture_layout.schema_name(os.getpid(), negative_cases.IGNORE_ERRORS_CASE)
    created_schemas.append(schema)
    return build_run.perform_run(
        root / 'run',
        schema,
        db_credentials,
        overlay=overlay,
        bundle_groups=[[recipe.bundle]],
        extra_import_args=['--import-ignore-errors'],
        finalize=False,
    )
