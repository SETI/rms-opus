"""The auxiliary tables and the dictionary, rebuilt on a finished schema and swapped in.

These run against a schema of their own: one bundle, imported and finished, as a served
database is. Each test reads the rebuilt tables back and compares them with what the
finishing steps wrote, which the main run's goldens pin. The interrupted rebuilds use
``OPUS_IMPORT_FAULT`` to stop between the fill and the rename, the one moment a crash
could expose a reader to a half-built table if the swap were not atomic.
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

import pytest

from import_tests.tools import build_run, fixture_layout, golden_io, negative_cases
from opus_import import import_fault, table_swap

if TYPE_CHECKING:
    from import_tests.tools.golden_io import DatabaseCredentials

#: The schema case these tests run under.
_CASE = 'table_swap'

#: The code-only deploy's line (``deploy_new_code_only.sh``).
_CODE_ONLY_DEPLOY_ARGS = (
    '--create-param-info',
    '--create-partables',
    '--create-table-names',
    '--import-dictionary',
)

#: Every table the line rebuilds, parents before children.
_REBUILT_TABLES = ('param_info', 'partables', 'table_names', 'contexts', 'definitions')

#: Each swap's fault argument, the option that runs it, and the tables it rebuilds.
_SWAPS = [
    ('param_info', '--create-param-info', ('param_info',)),
    ('partables', '--create-partables', ('partables',)),
    ('table_names', '--create-table-names', ('table_names',)),
    ('definitions', '--import-dictionary', ('contexts', 'definitions')),
]


@pytest.fixture(scope='module')
def finished_run(
    tmp_path_factory: pytest.TempPathFactory,
    db_credentials: DatabaseCredentials,
    created_schemas: list[str],
    subprocess_coverage: None,
) -> build_run.ImportRun:
    """Import one bundle and finish the schema, as a served database is.

    Returns:
        The run, in a schema and a log directory of its own.
    """
    root = tmp_path_factory.mktemp('mini_holdings_table_swap')
    bundle = negative_cases.bundle_for_class(negative_cases.DUPLICATE_ID_INSTRUMENT_CLASS)
    schema = fixture_layout.schema_name(os.getpid(), _CASE)
    created_schemas.append(schema)
    return build_run.perform_run(root, schema, db_credentials, bundle_groups=[[bundle]])


@pytest.fixture(scope='module')
def as_finished(
    finished_run: build_run.ImportRun, db_credentials: DatabaseCredentials
) -> dict[str, str]:
    """Return each rebuilt table as the finishing steps wrote it, before any test runs."""
    return {
        table: golden_io.serialize_table(db_credentials, finished_run.schema, table)
        for table in _REBUILT_TABLES
    }


def _leftovers(credentials: DatabaseCredentials, schema: str) -> list[str]:
    """Return every ``__new`` or ``__old`` table the schema holds."""
    suffixes = (table_swap.SWAP_NEW_SUFFIX, table_swap.SWAP_OLD_SUFFIX)
    return [
        table for table in golden_io.list_tables(credentials, schema) if table.endswith(suffixes)
    ]


def _assert_as_finished(
    run: build_run.ImportRun,
    credentials: DatabaseCredentials,
    as_finished: dict[str, str],
    tables: tuple[str, ...] = _REBUILT_TABLES,
) -> None:
    """Assert each table holds exactly what the finishing steps wrote."""
    for table in tables:
        assert golden_io.serialize_table(credentials, run.schema, table) == as_finished[table], (
            table
        )


def test_the_code_only_deploys_line_rebuilds_the_same_tables(
    finished_run: build_run.ImportRun,
    db_credentials: DatabaseCredentials,
    as_finished: dict[str, str],
) -> None:
    """Rebuilt on a finished schema, every table comes back as finalization wrote it."""
    result = build_run.run_pipeline_step(finished_run.paths.config_file, _CODE_ONLY_DEPLOY_ARGS)
    assert result.returncode == 0, result.stderr[-2000:]
    _assert_as_finished(finished_run, db_credentials, as_finished)
    assert _leftovers(db_credentials, finished_run.schema) == []


@pytest.mark.parametrize(
    ('faulted', 'option', 'tables'), _SWAPS, ids=[faulted for faulted, _, _ in _SWAPS]
)
def test_an_interrupted_rebuild_leaves_the_live_tables_and_the_next_one_recovers(
    finished_run: build_run.ImportRun,
    db_credentials: DatabaseCredentials,
    as_finished: dict[str, str],
    monkeypatch: pytest.MonkeyPatch,
    faulted: str,
    option: str,
    tables: tuple[str, ...],
) -> None:
    """A crash between the fill and the rename leaves only ``__new`` tables behind."""
    monkeypatch.setenv(import_fault.IMPORT_FAULT_ENV_VAR, f'{table_swap.SWAP_FAULT_SITE}:{faulted}')
    stopped = build_run.run_pipeline_step(finished_run.paths.config_file, [option])
    assert stopped.returncode != 0
    _assert_as_finished(finished_run, db_credentials, as_finished, tables)
    assert sorted(_leftovers(db_credentials, finished_run.schema)) == sorted(
        table_swap.swap_new_name(table) for table in tables
    )

    monkeypatch.delenv(import_fault.IMPORT_FAULT_ENV_VAR)
    recovered = build_run.run_pipeline_step(finished_run.paths.config_file, [option])
    assert recovered.returncode == 0, recovered.stderr[-2000:]
    _assert_as_finished(finished_run, db_credentials, as_finished, tables)
    assert _leftovers(db_credentials, finished_run.schema) == []


def test_the_swapped_dictionary_keeps_its_foreign_key(
    finished_run: build_run.ImportRun, db_credentials: DatabaseCredentials
) -> None:
    """After a swap, ``definitions`` references the live ``contexts``, not a dropped table."""
    result = build_run.run_pipeline_step(finished_run.paths.config_file, ['--import-dictionary'])
    assert result.returncode == 0, result.stderr[-2000:]
    rows = golden_io.query(
        db_credentials,
        finished_run.schema,
        'SELECT REFERENCED_TABLE_NAME FROM information_schema.KEY_COLUMN_USAGE '
        "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'definitions' "
        'AND REFERENCED_TABLE_NAME IS NOT NULL',
    )
    assert [row[0] for row in rows] == ['contexts']
