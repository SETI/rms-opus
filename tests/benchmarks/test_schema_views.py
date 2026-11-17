"""How the harness copies and reads a schema whose ``obs_general`` is a view of the rows
in the import generation it serves. The server and its connections are stand-ins that
record each statement and answer it from a table."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from benchmarks import bench_import, bench_server, bench_web, schema_copy
from benchmarks.bench_import import ImportBench
from benchmarks.monitor import (
    InvocationMonitor,
    InvocationRecord,
    RunFailedError,
    _MemorySampler,
)
from benchmarks.sides import Spelling

#: The view as ``SHOW CREATE VIEW`` prints it from a connection whose default schema is
#: another, with every name qualified by the source schema and a definer.
_SOURCE_VIEW = (
    'CREATE ALGORITHM=MERGE DEFINER=`opus`@`local``host` SQL SECURITY INVOKER VIEW '
    '`src`.`obs_general` AS select `src`.`obs_general_rows`.`id` AS `id` '
    'from `src`.`obs_general_rows` where (`src`.`obs_general_rows`.`added_generation` <= '
    '(select `src`.`schema_version`.`generation` from `src`.`schema_version`))'
)

#: The same view as the clone must create it.
_TARGET_VIEW = (
    'CREATE ALGORITHM=MERGE SQL SECURITY INVOKER VIEW '
    '`dst`.`obs_general` AS select `dst`.`obs_general_rows`.`id` AS `id` '
    'from `dst`.`obs_general_rows` where (`dst`.`obs_general_rows`.`added_generation` <= '
    '(select `dst`.`schema_version`.`generation` from `dst`.`schema_version`))'
)


class _Connection:
    """A connection that records each statement and answers it by the first key it holds."""

    def __init__(self, answers: dict[str, list[tuple[Any, ...]]]) -> None:
        """Answer from `answers`; a statement holding no key returns no rows."""
        self.answers = answers
        self.statements: list[tuple[str, tuple[Any, ...]]] = []
        self._rows: list[tuple[Any, ...]] = []

    def cursor(self) -> _Connection:
        """Act as its own cursor."""
        return self

    def execute(self, statement: str, parameters: Any = None) -> None:
        """Record a statement and choose its answer."""
        self.statements.append((statement, tuple(parameters or ())))
        self._rows = next((rows for key, rows in self.answers.items() if key in statement), [])

    def fetchall(self) -> list[tuple[Any, ...]]:
        """Return the answer to the last statement."""
        return self._rows

    def close(self) -> None:
        """Nothing to close."""


class _Server:
    """A server whose every connection is one recording connection."""

    def __init__(self, connection: _Connection) -> None:
        self.connection = connection

    def connect(self) -> _Connection:
        """Return the one connection."""
        return self.connection


def _clone_statements() -> list[str]:
    """Clone a schema holding two tables and the view, and return every statement issued."""
    connection = _Connection(
        {
            "TABLE_TYPE = 'BASE TABLE'": [('obs_general_rows',), ('schema_version',)],
            "TABLE_TYPE = 'VIEW'": [('obs_general',)],
            'SHOW CREATE TABLE': [('t', 'CREATE TABLE `t` (`id` int)')],
            'SHOW CREATE VIEW': [('obs_general', _SOURCE_VIEW, 'utf8mb4', 'utf8mb4_0900_ai_ci')],
            'information_schema.COLUMNS': [('id',)],
        }
    )
    schema_copy.clone_schema(_Server(connection), 'src', 'dst', version=None, connections=1)  # type: ignore[arg-type]
    return [statement for statement, _ in connection.statements]


def test_a_clone_creates_the_view_naming_the_target_and_no_definer() -> None:
    """The view reads the clone's own tables, and creating it names no other account."""
    views = [
        statement for statement in _clone_statements() if statement.startswith('CREATE ALGORITHM')
    ]
    assert views == [_TARGET_VIEW]


def test_a_clone_creates_the_view_after_every_table() -> None:
    """The view names tables, so they must exist when it is created."""
    statements = _clone_statements()
    view = statements.index(_TARGET_VIEW)
    tables = [i for i, statement in enumerate(statements) if statement.startswith('CREATE TABLE')]
    assert len(tables) == 2
    assert max(tables) < view


def test_a_view_definition_keeps_its_algorithm_and_security() -> None:
    """Only the definer goes; a name another schema qualifies is left alone."""
    definition = (
        'CREATE ALGORITHM=MERGE DEFINER=`root`@`%` SQL SECURITY INVOKER VIEW `v` AS '
        'select `src`.`t`.`a` AS `a` from `src`.`t` join `other`.`u`'
    )
    assert schema_copy.portable_view_definition(definition, 'src', 'dst') == (
        'CREATE ALGORITHM=MERGE SQL SECURITY INVOKER VIEW `v` AS '
        'select `dst`.`t`.`a` AS `a` from `dst`.`t` join `other`.`u`'
    )


def test_a_view_definition_keeps_the_source_name_inside_a_string_literal() -> None:
    """A literal holding the source's qualifier is data, so only the table moves."""
    definition = "CREATE VIEW `v` AS select '`src`.marker' AS `label` from `src`.`t`"
    assert schema_copy.portable_view_definition(definition, 'src', 'dst') == (
        "CREATE VIEW `v` AS select '`src`.marker' AS `label` from `dst`.`t`"
    )


def test_views_are_created_after_the_views_they_read() -> None:
    """A view reading another is created after it, through a chain, whatever the names."""
    connection = _Connection(
        {
            'VIEW_TABLE_USAGE': [
                ('a_summary', 'm_middle'),
                ('m_middle', 'z_rows'),
                ('m_middle', 'base'),
                ('b_other', 'base'),
            ],
            "TABLE_TYPE = 'VIEW'": [('a_summary',), ('b_other',), ('m_middle',), ('z_rows',)],
            'SHOW CREATE VIEW': [('v', 'CREATE VIEW `src`.`v` AS select 1', 'utf8mb4', 'c')],
        }
    )
    created = schema_copy.copy_views(connection, 'src', 'dst')
    assert created == ['b_other', 'z_rows', 'm_middle', 'a_summary']
    shown = [
        statement.rsplit('.', 1)[1]
        for statement, _ in connection.statements
        if statement.startswith('SHOW CREATE VIEW')
    ]
    assert shown == [f'`{view}`' for view in created]


@pytest.mark.parametrize(
    ('found', 'table'), [(1, 'obs_general_rows'), (0, 'obs_general')], ids=['view', 'table']
)
def test_the_observations_are_read_from_the_base_table(found: int, table: str) -> None:
    """A schema whose obs_general is a view holds its rows in obs_general_rows."""
    connection = _Connection({'information_schema.TABLES': [(found,)]})
    assert bench_server.obs_general_table(connection, 'dst') == table
    assert connection.statements[0][1] == ('dst', 'obs_general_rows')


def _landing_check(
    monkeypatch: pytest.MonkeyPatch, present: list[str], generation: int | None
) -> _Connection:
    """Check that two bundles landed in a schema whose observations are a view's rows.

    Parameters:
        monkeypatch: Keeps the memory sampler from sampling.
        present: The bundles the base table answers as holding rows.
        generation: The generation the import wrote, or None.

    Returns:
        The connection, with the statements the check issued.
    """
    monkeypatch.setattr(_MemorySampler, '_sample', lambda self: None)
    connection = _Connection(
        {
            'information_schema.TABLES': [(1,)],
            'SELECT DISTINCT bundle_id': [(bundle,) for bundle in present],
        }
    )
    monitor = InvocationMonitor(
        server=_Server(connection),  # type: ignore[arg-type]
        schema='dst',
        spelling=Spelling.from_help('--import'),
        expand=lambda groups: [[group] for group in groups],
        timing_file=None,
        excluded_pids=set,
    )
    monitor.generation = generation
    monitor.check_bundles_landed(['A', 'B'])
    return connection


def test_a_bundle_import_is_checked_in_the_base_table(monkeypatch: pytest.MonkeyPatch) -> None:
    """The view shows no rows before the version row exists, so it cannot be checked."""
    connection = _landing_check(monkeypatch, ['A', 'B'], None)
    statement, parameters = connection.statements[-1]
    assert '`dst`.`obs_general_rows`' in statement
    assert parameters == ('A', 'B')


def test_an_import_into_a_generation_is_checked_among_that_generations_rows(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Rows of the bundle that the served generation holds would pass for the re-import."""
    connection = _landing_check(monkeypatch, ['A', 'B'], 7)
    statement, parameters = connection.statements[-1]
    assert statement.endswith('AND `added_generation` = %s')
    assert parameters == ('A', 'B', 7)


def test_a_bundle_without_rows_in_the_generation_fails_the_run(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The failure names the generation and the bundle missing from it."""
    with pytest.raises(RunFailedError, match=r"no row in generation 7 for \['B'\]"):
        _landing_check(monkeypatch, ['A'], 7)


def test_the_table_count_leaves_out_views(monkeypatch: pytest.MonkeyPatch) -> None:
    """A view is no per-search table, and would set a schema of either shape apart."""
    counts = {"TABLE_TYPE = 'BASE TABLE'": [(40,)], 'information_schema.TABLES': [(41,)]}
    monkeypatch.setattr(
        bench_web,
        'query',
        lambda _connection, statement, parameters=(): next(
            rows for key, rows in counts.items() if key in statement
        ),
    )
    assert bench_web.base_table_count(None, 'dst') == 40


def _import_bench(monkeypatch: pytest.MonkeyPatch, connection: _Connection) -> ImportBench:
    """Return an import bench whose every query is answered by `connection`."""

    def answer(conn: _Connection, statement: str, parameters: Any = ()) -> list[tuple[Any, ...]]:
        conn.execute(statement, parameters)
        return conn.fetchall()

    for module in (bench_import, bench_server):
        monkeypatch.setattr(module, 'query', answer)
    monkeypatch.setattr(bench_import, 'global_status', lambda conn: {})
    bench = object.__new__(ImportBench)
    bench.server = _Server(connection)  # type: ignore[assignment]
    bench.scenario = SimpleNamespace(largest=None)  # type: ignore[assignment]
    return bench


def test_a_bundles_rows_are_counted_in_the_base_table(monkeypatch: pytest.MonkeyPatch) -> None:
    """A sweep imports without the version row, so the view would count nothing."""
    connection = _Connection(
        {'information_schema.TABLES': [(1,)], 'SELECT COUNT(*) FROM `': [(40,)]}
    )
    assert _import_bench(monkeypatch, connection)._rows('dst', 'A') == 40
    assert '`dst`.`obs_general_rows`' in connection.statements[-1][0]


def test_a_runs_rows_are_counted_in_the_base_table(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A run stopped before finalization has no version row, so the view would show none."""
    connection = _Connection(
        {'information_schema.TABLES': [(1,)], 'GROUP BY bundle_id': [('A', 30), ('B', 10)]}
    )
    monitor = SimpleNamespace(
        records=[
            InvocationRecord(name='bundle_import:A,B', arguments=('--import', 'A,B'), wall_s=2.0)
        ],
        is_bundle_import=lambda arguments: True,
        summary=dict,
    )
    run: dict[str, Any] = {'metrics': {}, 'details': {}}
    _import_bench(monkeypatch, connection)._fill_run(
        run,
        monitor,  # type: ignore[arg-type]  # a stand-in monitor
        'dst',
        {},
        full=False,
        log_dir=tmp_path,
    )
    grouped = next(statement for statement, _ in connection.statements if 'GROUP BY' in statement)
    assert '`dst`.`obs_general_rows`' in grouped
    assert run['details']['obs_general_rows'] == 40
