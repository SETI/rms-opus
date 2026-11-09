"""The bundle registry, and the import loop that keeps it, without a server.

The loop runs against an in-memory stand-in holding the registry and the version table,
with each bundle's delete and load replaced by a recording function, so what is asserted
is the order of the work and the state each bundle ends in.
"""

from __future__ import annotations

import contextlib
from collections.abc import Iterator
from typing import Any

import pytest

from opus_import import bundle_registry, cli, import_util
from opus_import.schema_version import (
    SCHEMA_STATE_APPENDING,
    SCHEMA_STATE_READY,
    SCHEMA_VERSION,
    SCHEMA_VERSION_TABLE,
)
from opus_import.steps import do_import, do_import_tables

from .conftest import default_arguments, make_context


class _RegistryDB:
    """A stand-in holding a few small tables as lists of rows, and recording events."""

    def __init__(self, tables: dict[str, list[dict[str, Any]]] | None = None) -> None:
        """Hold the tables.

        Parameters:
            tables: Each table's rows, keyed by table; none for an empty schema.
        """
        self.tables = {} if tables is None else tables
        self.db_schema = 'opus_test'
        self.events: list[str] = []

    def table_exists(self, table_name: str) -> bool:
        """Say whether a table is held."""
        return table_name in self.tables

    def table_names(self, prefix: Any = None) -> list[str]:
        """Return the tables, which hold no key a fresh import's check looks for."""
        return sorted(self.tables)

    def read_table_keys(self) -> dict[str, list[Any]]:
        """Report no keys."""
        return {}

    def create_table(self, table_name: str, schema: Any, ignore_if_exists: bool = True) -> bool:
        """Create an empty table."""
        self.tables.setdefault(table_name, [])
        return True

    def read_rows(self, table_name: str, columns: list[str]) -> list[tuple[Any, ...]]:
        """Return the rows' values in `columns` order."""
        return [tuple(row[column] for column in columns) for row in self.tables[table_name]]

    def quote_identifier(self, name: str) -> str:
        """Backtick-quote a name."""
        return f'`{name}`'

    def _matching(self, table_name: str, where: str, value: Any) -> list[dict[str, Any]]:
        """Return the rows a ```column`=%s`` clause selects."""
        column = where.split('`')[1]
        return [row for row in self.tables[table_name] if row[column] == value]

    def upsert_rows(self, table_name: str, key_name: str, rows: list[dict[str, Any]]) -> None:
        """Insert each row, or update the one with its key."""
        for row in rows:
            existing = self._matching(table_name, f'`{key_name}`=%s', row[key_name])
            if existing:
                existing[0].update(row)
            else:
                self.tables[table_name].append(dict(row))

    def update_row(
        self, table_name: str, row: dict[str, Any], where: str, where_params: list[Any]
    ) -> None:
        """Assign `row`'s values to the rows the clause selects."""
        for existing in self._matching(table_name, where, where_params[0]):
            existing.update(row)

    def delete_rows(self, table_name: str, where: str, where_params: list[Any]) -> None:
        """Delete the rows the clause selects."""
        doomed = self._matching(table_name, where, where_params[0])
        self.tables[table_name] = [row for row in self.tables[table_name] if row not in doomed]

    @contextlib.contextmanager
    def foreign_keys_unchecked(self) -> Iterator[None]:
        """Record the checks going off and coming back on."""
        self.events.append('checks off')
        try:
            yield
        finally:
            self.events.append('checks on')

    def states(self) -> dict[str, str]:
        """Return each registered bundle's state."""
        return {row['bundle_id']: row['state'] for row in self.tables.get('import_bundle', [])}


def _registry(states: dict[str, str]) -> list[dict[str, Any]]:
    """Return registry rows holding `states`."""
    return [{'bundle_id': bundle, 'state': state} for bundle, state in states.items()]


def _run(
    db: _RegistryDB,
    named: list[str],
    monkeypatch: pytest.MonkeyPatch,
    *,
    logging: tuple[str, ...] = (),
    failing: tuple[str, ...] = (),
    **arguments: Any,
) -> tuple[bool, Any]:
    """Run the import loop over `named`, each bundle's work recorded on `db`.

    Parameters:
        db: The stand-in.
        named: The bundles the command line names.
        monkeypatch: Replaces the bundle's delete and load.
        logging: Bundles whose import logs an error and still returns True.
        failing: Bundles whose import returns False.
        arguments: Options to set, by attribute.

    Returns:
        What `do_import_steps` returned, and the context.
    """
    monkeypatch.setattr(import_util, 'yield_import_bundle_ids', lambda ctx: iter(named))
    monkeypatch.setattr(
        do_import_tables,
        'delete_bundle_from_obs_tables',
        lambda ctx, bundle: db.events.append(f'delete {bundle}'),
    )

    def load(ctx: Any, bundle: str) -> bool:
        db.events.append(f'load {bundle} ({db.states().get(bundle)})')
        if bundle in logging:
            import_util.log_error(ctx, f'{bundle} went wrong')
        return bundle not in failing

    monkeypatch.setattr(do_import, 'import_one_bundle', load)
    args = default_arguments()
    args.do_import = True
    for name, value in arguments.items():
        setattr(args, name, value)
    ctx = make_context(db=db, args=args)
    return do_import.do_import_steps(ctx), ctx


def test_each_bundle_is_deleted_then_loaded_unchecked_and_ends_done(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A fresh import registers its bundles, and moves each through importing to done."""
    db = _RegistryDB()
    succeeded, _ctx = _run(db, ['B_1', 'B_2'], monkeypatch)
    assert succeeded
    assert db.states() == {'B_1': 'done', 'B_2': 'done'}
    assert db.events == [
        'delete B_1',
        'checks off',
        'load B_1 (importing)',
        'checks on',
        'delete B_2',
        'checks off',
        'load B_2 (importing)',
        'checks on',
    ]
    assert SCHEMA_VERSION_TABLE not in db.tables


def test_a_bundle_that_logs_an_error_is_failed_and_the_loop_goes_on(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A logged error fails its bundle only; the invocation fails at the end."""
    db = _RegistryDB()
    succeeded, _ctx = _run(db, ['B_1', 'B_2', 'B_3'], monkeypatch, logging=('B_2',))
    assert not succeeded
    assert db.states() == {'B_1': 'done', 'B_2': 'failed', 'B_3': 'done'}


def test_a_bundle_whose_import_fails_stops_the_loop(monkeypatch: pytest.MonkeyPatch) -> None:
    """The bundles after it stay pending."""
    db = _RegistryDB()
    succeeded, _ctx = _run(db, ['B_1', 'B_2', 'B_3'], monkeypatch, failing=('B_2',))
    assert not succeeded
    assert db.states() == {'B_1': 'done', 'B_2': 'failed', 'B_3': 'pending'}


def test_ignore_errors_marks_every_bundle_done_and_goes_on(monkeypatch: pytest.MonkeyPatch) -> None:
    """``--ignore-errors`` is how a debugging run reaches a finished registry."""
    db = _RegistryDB()
    succeeded, _ctx = _run(
        db,
        ['B_1', 'B_2', 'B_3'],
        monkeypatch,
        logging=('B_1',),
        failing=('B_2',),
        ignore_errors=True,
    )
    assert succeeded
    assert db.states() == {'B_1': 'done', 'B_2': 'done', 'B_3': 'done'}


def test_a_bundle_opus_skips_is_never_registered(monkeypatch: pytest.MonkeyPatch) -> None:
    """Its import is still asked for, which logs that it is ignored, but no row waits on it."""
    db = _RegistryDB()
    succeeded, _ctx = _run(db, ['GO_0001', 'COCIRS_0101', 'COISS_2002'], monkeypatch)
    assert succeeded
    assert db.states() == {'COISS_2002': 'done'}
    assert [event for event in db.events if event.startswith('load')] == [
        'load GO_0001 (None)',
        'load COCIRS_0101 (None)',
        'load COISS_2002 (importing)',
    ]


@pytest.mark.parametrize(
    ('bundle', 'imported'),
    [('GO_0001', False), ('COCIRS_0101', False), ('COISS_2002', True), ('NO_SUCH_1', True)],
)
def test_opus_imports_every_bundle_but_the_ones_with_no_instrument_class(
    bundle: str, imported: bool
) -> None:
    """A bundle with no entry is imported, and fails there; one with an empty entry is not."""
    assert do_import_tables.opus_imports_bundle(bundle) is imported


def test_an_append_resumes_the_unfinished_bundles_first(monkeypatch: pytest.MonkeyPatch) -> None:
    """Every registered bundle not done, in bundle order, then the named ones not among them."""
    db = _RegistryDB(
        {
            SCHEMA_VERSION_TABLE: [{'version': SCHEMA_VERSION, 'state': SCHEMA_STATE_READY}],
            'import_bundle': _registry(
                {'B_1': 'done', 'B_7': 'pending', 'B_4': 'failed', 'B_5': 'importing'}
            ),
        }
    )
    succeeded, ctx = _run(db, ['B_9', 'B_5'], monkeypatch)
    assert succeeded
    assert ctx.import_path == do_import.IMPORT_PATH_APPEND
    assert [event for event in db.events if event.startswith('delete')] == [
        'delete B_4',
        'delete B_5',
        'delete B_7',
        'delete B_9',
    ]
    assert db.states() == {
        'B_1': 'done',
        'B_4': 'done',
        'B_5': 'done',
        'B_7': 'done',
        'B_9': 'done',
    }
    assert db.tables[SCHEMA_VERSION_TABLE] == [
        {'version': SCHEMA_VERSION, 'state': SCHEMA_STATE_APPENDING}
    ]


def test_a_fresh_import_does_not_resume(monkeypatch: pytest.MonkeyPatch) -> None:
    """Without a version row the named bundles are imported, and only they."""
    db = _RegistryDB({'import_bundle': _registry({'B_4': 'failed'})})
    _run(db, ['B_9'], monkeypatch)
    assert [event for event in db.events if event.startswith('delete')] == ['delete B_9']
    assert db.states() == {'B_4': 'failed', 'B_9': 'done'}


def test_deleting_bundles_removes_their_registry_rows(monkeypatch: pytest.MonkeyPatch) -> None:
    """A failed bundle the operator drops no longer holds up the schema."""
    db = _RegistryDB({'import_bundle': _registry({'B_4': 'failed', 'B_5': 'done'})})
    succeeded, _ctx = _run(db, ['B_4'], monkeypatch, do_import=False, delete_bundles=True)
    assert succeeded
    assert db.events == ['delete B_4']
    assert db.states() == {'B_5': 'done'}


@pytest.mark.parametrize(
    ('tables', 'finished'),
    [
        ({}, True),
        ({'import_bundle': _registry({'B_1': 'done'})}, True),
        ({'import_bundle': _registry({'B_1': 'done', 'B_3': 'failed', 'B_2': 'pending'})}, False),
    ],
    ids=['no-registry', 'all-done', 'unfinished'],
)
def test_finalization_and_the_version_step_refuse_an_unfinished_registry(
    tables: dict[str, list[dict[str, Any]]], finished: bool
) -> None:
    """The refusal names every bundle that is not done, with its state."""
    ctx = make_context(db=_RegistryDB(tables))
    assert cli._registry_finished(ctx, '--finalize') is finished
    if finished:
        assert ctx.logger.messages_at('fatal') == []
    else:
        assert ctx.logger.messages_at('fatal') == [
            '--finalize refuses to run while bundles in the bundle registry are not done: '
            'B_2 (pending), B_3 (failed). Import them again, or remove them with '
            '--delete-bundles'
        ]


def test_the_registry_reads_nothing_when_it_has_no_table() -> None:
    """An import that never registered anything leaves nothing unfinished."""
    ctx = make_context(db=_RegistryDB())
    assert bundle_registry.unfinished_bundles(ctx) == []
    bundle_registry.unregister_bundles(ctx, ['B_1'])
