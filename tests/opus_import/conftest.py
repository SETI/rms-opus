"""Shared fixtures for the `opus_import` tests."""

from __future__ import annotations

import argparse
import contextlib
import re
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest

from opus_config import OPUS_CONFIG_ENV_VAR
from opus_config.config import ImportConfig
from opus_import import bundle_registry, cli, import_processes, import_util
from opus_import.context import ImportContext
from opus_import.steps import (
    do_import,
    do_import_mult,
    do_import_tables,
    do_recover,
    do_register,
)


class RecordingLogger:
    """A `pdslogger.PdsLogger` stand-in that keeps every message instead of writing it."""

    def __init__(self) -> None:
        self.messages: list[tuple[str, str]] = []

    def log(self, level: str, msg: str, *args: Any, **kwargs: Any) -> None:
        """Record one message.

        Parameters:
            level: The level name the pipeline logged at.
            msg: The formatted message.
            args: Ignored; the pipeline formats its messages before logging them.
            kwargs: Ignored, as `args` is.
        """
        self.messages.append((level, msg))

    def open(self, title: str, *args: Any, **kwargs: Any) -> None:
        """Record the start of a section of the log.

        Parameters:
            title: The section's title.
            args: Ignored.
            kwargs: Ignored, such as the section's limits.
        """
        self.messages.append(('open', title))

    def close(self, *args: Any, **kwargs: Any) -> None:
        """Record the end of a section of the log.

        Parameters:
            args: Ignored.
            kwargs: Ignored.
        """
        self.messages.append(('close', ''))

    def messages_at(self, level: str) -> list[str]:
        """Return every message logged at `level`, in the order they were logged.

        Parameters:
            level: The level name to filter on, such as ``'error'``.

        Returns:
            The messages, oldest first.
        """
        return [msg for msg_level, msg in self.messages if msg_level == level]


def import_table(**keys: object) -> ImportConfig:
    """Return an ``[import]`` table with the keys given and every other default."""
    values: dict[str, object] = {
        'log_file': 'import.log',
        'debug_log_file': 'import_debug.log',
        'bulk_load': True,
        'scratch_dir': None,
        'transaction_rows': 100_000,
        'index_workers': 1,
        'server_tmpdir': None,
        'workers': 1,
        'cpu_fraction': 0.75,
        'worker_rows': 500,
        'importers': 1,
        'stall_warning_minutes': 30,
        'status_interval_minutes': 5,
    }
    values.update(keys)
    return ImportConfig(**values)  # type: ignore[arg-type]


def default_arguments() -> argparse.Namespace:
    """Return what the real command line produces when it is given no options.

    Built by parsing an empty argument list with the pipeline's own parser rather than
    by listing the options a test happens to need. A hand-built namespace holds only
    the options someone remembered, so it stops matching the CLI the moment an option
    is added and any code reading a newer one raises `AttributeError` in the tests
    while working in production -- or, worse, the reverse.

    Returns:
        A namespace carrying every option with its documented default.
    """
    return cli._create_argument_parser().parse_args([])


def make_context(**kwargs: Any) -> ImportContext:
    """Return an `ImportContext` with a recording logger and no database.

    Parameters:
        kwargs: Fields to override, such as ``db=`` or ``args=``.

    Returns:
        A context whose `ImportContext.logger` is a `RecordingLogger` and whose
        `ImportContext.args` is `default_arguments`, unless overridden.
    """
    kwargs.setdefault('args', default_arguments())
    kwargs.setdefault('logger', RecordingLogger())
    return ImportContext(**kwargs)


@pytest.fixture(autouse=True)
def _opus_config(ci_config_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Point the pipeline at the checked-in dummy configuration.

    Anything the pipeline reads out of it comes from that one file, so a test asserting
    on a configured value and the CI jobs are looking at the same settings. The
    process-wide cache is cleared around every test by the root conftest.
    """
    monkeypatch.setenv(OPUS_CONFIG_ENV_VAR, str(ci_config_path))


def row_selected(row: dict[str, Any], where: str, params: list[Any]) -> bool:
    """Return whether a row meets a conjunction of ```col`=%s`` and ```col` IS [NOT] NULL``.

    Parameters:
        row: The row, by column.
        where: The clause, its terms joined by ``AND``.
        params: The values of its ``%s`` placeholders, in order.

    Returns:
        True when the row meets every term.
    """
    values = iter(params)
    for term in where.split(' AND '):
        column = re.match(r'`(\w+)`', term)
        assert column is not None, term
        value = row[column[1]]
        if term.endswith('IS NOT NULL'):
            matched = value is not None
        elif term.endswith('IS NULL'):
            matched = value is None
        else:
            assert term.endswith('=%s'), term
            matched = value == next(values)
        if not matched:
            return False
    return True


class RegistryDB:
    """A stand-in holding a few small tables as lists of rows, and recording events."""

    def __init__(self, tables: dict[str, list[dict[str, Any]]] | None = None) -> None:
        """Hold the tables.

        Parameters:
            tables: Each table's rows, keyed by table; none for an empty schema.
        """
        self.tables = {} if tables is None else tables
        self.db_schema = 'opus_test'
        self.events: list[str] = []
        self.on_lock: Any = None
        self.read_only = False

    def table_exists(self, table_name: str) -> bool:
        """Say whether a table is held."""
        return table_name in self.tables

    def forget_table_names(self) -> None:
        """Record the table names being read again."""
        self.events.append('reread tables')

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

    def read_rows(
        self,
        table_name: str,
        columns: list[str],
        where: str | None = None,
        where_params: list[Any] | None = None,
    ) -> list[tuple[Any, ...]]:
        """Return the rows' values in `columns` order, as the registry's reads select them."""
        rows = self.tables[table_name]
        if where is not None and where.startswith('1=1 ORDER BY'):
            rows = sorted(rows, key=lambda row: row['bundle_number'])
        elif where is not None:
            assert where_params is not None
            rows = self._matching(table_name, where, where_params)
        return [tuple(row[column] for column in columns) for row in rows]

    def quote_identifier(self, name: str) -> str:
        """Backtick-quote a name."""
        return f'`{name}`'

    def _matching(
        self, table_name: str, where: str, where_params: list[Any]
    ) -> list[dict[str, Any]]:
        """Return the rows a clause selects, every one of its terms honored."""
        return [row for row in self.tables[table_name] if row_selected(row, where, where_params)]

    def insert_rows(self, table_name: str, rows: list[dict[str, Any]]) -> None:
        """Append rows, numbering a registry row as its auto-incremented key would."""
        for row in rows:
            added = dict(row)
            if table_name == 'import_bundle':
                numbers = [existing['bundle_number'] for existing in self.tables[table_name]]
                added['bundle_number'] = max(numbers, default=0) + 1
            self.tables[table_name].append(added)

    def update_row(
        self, table_name: str, row: dict[str, Any], where: str, where_params: list[Any]
    ) -> int:
        """Assign `row`'s values to the rows the clause selects, and count them."""
        matched = self._matching(table_name, where, where_params)
        for existing in matched:
            existing.update(row)
        return len(matched)

    def conditional_update(
        self, table_name: str, row: dict[str, Any], where: str, where_params: list[Any]
    ) -> int:
        """Assign `row` to the bundle the clause names if its state, its start when
        named, and a NULL ``process_id`` when asked for, are the ones the clause expects;
        return how many rows changed."""
        bundle_id, *rest = where_params
        state_count = where.split(' IN (', 1)[1].split(')', 1)[0].count('%s')
        states, started = rest[:state_count], rest[state_count:]
        unheld = where.endswith('`process_id` IS NULL')
        changed = 0
        for existing in self._matching(table_name, '`bundle_id`=%s', [bundle_id]):
            if (
                existing['state'] in states
                and (not started or existing.get('started_at') == started[0])
                and (not unheld or existing.get('process_id') is None)
            ):
                existing.update(row)
                changed += 1
        return changed

    def delete_rows(self, table_name: str, where: str, where_params: list[Any]) -> None:
        """Delete the rows the clause selects."""
        doomed = self._matching(table_name, where, where_params)
        self.tables[table_name] = [row for row in self.tables[table_name] if row not in doomed]

    @contextlib.contextmanager
    def named_lock(self, name: str) -> Iterator[None]:
        """Record the lock being held, and run `on_lock` while it is."""
        self.events.append(f'lock {name}')
        try:
            if self.on_lock is not None:
                self.on_lock()
            yield
        finally:
            self.events.append('unlock')

    @contextlib.contextmanager
    def transaction(self) -> Iterator[None]:
        """Record the transaction."""
        self.events.append('begin')
        yield
        self.events.append('commit')

    def retrying(self, description: str, body: Any, expected: Any = None) -> Any:
        """Run the body once, as a transaction."""
        with self.transaction():
            return body()

    def lock_first_row(
        self, table_name: str, column: str, where: str, where_params: list[Any], order_by: list[str]
    ) -> Any:
        """Return the first pending row of the ones the claim may take, highest first."""
        state, *names = where_params
        excluded_count = where.split('NOT IN (', 1)[1].count('%s') if 'NOT IN' in where else 0
        among = names[: len(names) - excluded_count]
        excluded = names[len(names) - excluded_count :]
        rows = [
            row
            for row in self.tables[table_name]
            if row['state'] == state
            and (not among or row['bundle_id'] in among)
            and row['bundle_id'] not in excluded
        ]
        rows.sort(key=lambda row: tuple(row[name] for name in order_by), reverse=True)
        return rows[0][column] if rows else None

    @contextlib.contextmanager
    def foreign_keys_unchecked(self) -> Iterator[None]:
        """Record the checks going off and coming back on."""
        self.events.append('checks off')
        try:
            yield
        finally:
            self.events.append('checks on')

    @staticmethod
    def named_lock_holder(name: str) -> int | None:
        """Report every named lock free."""
        return None

    def lock_row(
        self, table_name: str, columns: list[str], where: str, where_params: list[Any]
    ) -> tuple[Any, ...] | None:
        """Return the first selected row's values in `columns` order; no other session
        holds a row."""
        rows = self._matching(table_name, where, where_params)
        return tuple(rows[0][column] for column in columns) if rows else None

    def open_sibling_connection(self) -> RegistryDB:
        """Return this stand-in, which serves every connection."""
        return self

    def set_idle_timeout(self, seconds: int) -> None:
        """Accept any idle timeout."""

    def close(self) -> None:
        """Record the connection closing."""
        self.events.append('close')

    logger = None

    def states(self) -> dict[str, str]:
        """Return each registered bundle's state."""
        return {row['bundle_id']: row['state'] for row in self.tables.get('import_bundle', [])}


class HeldImporter:
    """An importer that always holds its lock."""

    process_id = 1
    name = 'opus:lock'

    @staticmethod
    def held() -> bool:
        """Say the lock is held."""
        return True

    @staticmethod
    def exit() -> None:
        """Exit, holding nothing."""


#: The size estimate every bundle is given, so each range is a thousand ids.
BUNDLE_SIZE = 10


def registry_rows(states: dict[str, str]) -> list[dict[str, Any]]:
    """Return registry rows holding `states`, numbered and ranged in the order given."""
    capacity = bundle_registry.ID_CAPACITY_FACTOR * BUNDLE_SIZE
    return [
        {
            'bundle_number': number,
            'bundle_id': bundle,
            'size_estimate': BUNDLE_SIZE,
            'first_id': (number - 1) * capacity,
            'id_capacity': capacity,
            'state': state,
            'started_at': None,
            'finished_at': None,
            'process_id': None,
            'rows_done': 0,
            'losses': 0,
        }
        for number, (bundle, state) in enumerate(states.items(), start=1)
    ]


def run_import_loop(
    db: RegistryDB,
    named: list[str],
    monkeypatch: pytest.MonkeyPatch,
    *,
    logging: tuple[str, ...] = (),
    failing: tuple[str, ...] = (),
    during: dict[str, Any] | None = None,
    **arguments: Any,
) -> tuple[bool, Any]:
    """Run the import loop over `named`, each bundle's work recorded on `db`.

    Parameters:
        db: The stand-in.
        named: The bundles the command line names.
        monkeypatch: Replaces the bundle's delete and load.
        logging: Bundles whose import logs an error and still returns True.
        failing: Bundles whose import returns False.
        during: What to call, with the context, while a bundle imports, by bundle.
        arguments: Options to set, by attribute.

    Returns:
        What `do_import_steps` returned, and the context.
    """
    monkeypatch.setattr(import_util, 'yield_import_bundle_ids', lambda ctx: iter(named))
    monkeypatch.setattr(do_register, 'size_estimate', lambda bundle: BUNDLE_SIZE)
    monkeypatch.setattr(do_import_mult, 'register_pinned_fields', lambda ctx: None)
    monkeypatch.setattr(
        do_import_tables,
        'delete_bundle_from_obs_tables',
        lambda ctx, bundle: db.events.append(f'delete {bundle}'),
    )

    def load(ctx: Any, bundle: str) -> bool:
        db.events.append(f'load {bundle} ({db.states().get(bundle)})')
        if during and bundle in during:
            during[bundle](ctx)
        if bundle in logging:
            import_util.log_error(ctx, f'{bundle} went wrong')
        return bundle not in failing

    monkeypatch.setattr(do_import, 'import_one_bundle', load)
    monkeypatch.setattr(
        import_processes, 'start_importer', lambda lock_db, log_path: HeldImporter()
    )

    def release(ctx: Any, bundle: str, number: int, process_id: int, state: str | None) -> bool:
        do_import_tables.delete_bundle_from_obs_tables(ctx, bundle)
        if state is not None:
            db.update_row('import_bundle', {'state': state}, '`bundle_id`=%s', [bundle])
        return True

    monkeypatch.setattr(do_recover, 'release_bundle', release)
    args = default_arguments()
    args.do_import = not (arguments.get('join') or arguments.get('register_bundles'))
    for name, value in arguments.items():
        setattr(args, name, value)
    ctx = make_context(db=db, args=args)
    return do_import.do_import_steps(ctx), ctx
