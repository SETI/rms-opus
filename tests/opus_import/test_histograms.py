"""The range-search histograms: which columns get one, and the statements that build them."""

from __future__ import annotations

from typing import Any

import pytest

from opus_import import histograms
from opus_import.generations import GenerationState
from opus_import.importdb.mysql import ImportDBMySQL
from opus_import.importdb.super import ImportDBError, ImportDBSuper
from opus_import.schema_version import SCHEMA_VERSION
from opus_import.steps import do_import_tables
from opus_import.table_keys import TableKey

from .conftest import make_context


def test_every_range_row_names_its_column_at_the_table_its_rows_are_written_to() -> None:
    """A range row of any display counts; a body's category reads the surface geometry
    table; a longitude, a group and a string do not count."""
    rows = [
        ('obs_ring_geometry', 'emission1', 'RANGE%.3f:generic_angle'),
        ('obs_ring_geometry', 'emission2', 'RANGE%.3f:generic_angle'),
        ('obs_general', 'time1', 'RANGE:datetime'),
        ('obs_surface_geometry__saturn', 'phase1', 'RANGE%.3f:generic_angle'),
        ('obs_surface_geometry__titan', 'phase1', 'RANGE%.3f:generic_angle'),
        ('obs_ring_geometry', 'sub_solar_ring_long1', 'LONG%.3f:longitude'),
        ('obs_general', 'planet_id', 'GROUP'),
        ('obs_pds', 'note', 'STRING'),
        ('obs_general', 'preview_images', None),
    ]
    assert histograms.range_search_columns(rows) == {
        ('obs_ring_geometry', 'emission1'),
        ('obs_ring_geometry', 'emission2'),
        ('obs_general', 'time1'),
        ('obs_surface_geometry_target', 'phase1'),
    }


def test_a_column_that_leads_an_index_gets_no_histogram() -> None:
    """A leading column is estimated from its index; the second column of a composite
    leads nothing; a foreign key's columns are another index's, so it is passed over."""
    ranges = {
        ('obs_general', 'time1'),
        ('obs_general', 'time2'),
        ('obs_general', 'opus_id'),
        ('obs_ring_geometry', 'emission1'),
        ('obs_ring_geometry', 'emission2'),
        ('obs_ring_geometry', 'obs_general_id'),
        ('obs_type_image', 'levels'),
    }
    keys = {
        'obs_general': [
            TableKey('primary', ('id',)),
            TableKey('key', ('time1', 'opus_id')),
            TableKey('unique', ('time2',)),
        ],
        'obs_ring_geometry': [
            TableKey('primary', ('obs_general_id',)),
            TableKey('foreign', ('emission2',), ('obs_general', ('id',))),
        ],
    }
    assert histograms.histogram_columns(ranges, keys) == {
        'obs_general': ['opus_id'],
        'obs_ring_geometry': ['emission1', 'emission2'],
        'obs_type_image': ['levels'],
    }


class _HistogramDB:
    """A database holding a ``param_info``, some keys, and some histograms."""

    def __init__(
        self, histograms_now: dict[str, list[str]], *, param_info: tuple[str, ...] = ('param_info',)
    ) -> None:
        self.histograms_now = histograms_now
        self.param_info = param_info
        self.read_from: list[str] = []
        self.calls: list[tuple[str, str, list[str]]] = []

    def table_names(self, prefix: Any = None) -> list[str]:
        names = ['obs_general', 'obs_ring_geometry', *self.param_info]
        if prefix is None:
            return names
        return [name for name in names if name.startswith(tuple(prefix))]

    def read_rows(self, table_name: str, column_names: Any) -> list[tuple[str, str, str]]:
        assert table_name in self.param_info
        assert tuple(column_names) == histograms.PARAM_INFO_COLUMNS
        self.read_from.append(table_name)
        return [
            ('obs_general', 'time1', 'RANGE:datetime'),
            ('obs_ring_geometry', 'emission1', 'RANGE%.3f'),
            ('obs_ring_geometry', 'emission2', 'RANGE%.3f'),
        ]

    def read_table_keys(self) -> dict[str, list[TableKey]]:
        return {'obs_general': [TableKey('key', ('time1', 'opus_id'))]}

    def read_histograms(self) -> dict[str, list[str]]:
        return self.histograms_now

    def update_histograms(self, table_name: str, column_names: list[str]) -> None:
        self.calls.append(('update', table_name, list(column_names)))

    def drop_histograms(self, table_name: str, column_names: list[str]) -> None:
        self.calls.append(('drop', table_name, list(column_names)))


def test_the_histograms_are_built_and_any_other_on_an_observation_table_dropped() -> None:
    """The wanted ones are built again; a stale one goes; another table's is left alone."""
    db = _HistogramDB(
        {
            'obs_general': ['time1'],
            'obs_ring_geometry': ['emission1', 'incidence1'],
            'user_searches': ['result_count'],
        }
    )
    do_import_tables.update_histograms(make_context(db=db))
    assert db.calls == [
        ('drop', 'obs_general', ['time1']),
        ('drop', 'obs_ring_geometry', ['incidence1']),
        ('update', 'obs_ring_geometry', ['emission1', 'emission2']),
    ]


def test_a_schema_without_param_info_gets_no_histogram_and_keeps_its_own() -> None:
    """Before its finalization a schema has no range columns to read."""
    db = _HistogramDB({'obs_ring_geometry': ['emission1']}, param_info=())
    ctx = make_context(db=db)
    do_import_tables.update_histograms(ctx)
    assert db.calls == []


@pytest.mark.parametrize(
    ('pending', 'tables', 'expected'),
    [
        (None, ('param_info', 'param_info__new'), 'param_info'),
        (2, ('param_info', 'param_info__new'), 'param_info__new'),
        (2, ('param_info',), 'param_info'),
    ],
    ids=['served', 'pending-built', 'pending-not-built'],
)
def test_a_pending_generation_reads_the_param_info_built_for_its_switch(
    pending: int | None, tables: tuple[str, ...], expected: str
) -> None:
    """A pending generation's finalization leaves its ``param_info`` as ``__new``."""
    db = _HistogramDB({}, param_info=tables)
    state = GenerationState(SCHEMA_VERSION, 'ready', 1, pending, None, False)
    do_import_tables.update_histograms(make_context(db=db, generation_state=state))
    assert db.read_from == [expected]


def test_analyze_all_tables_analyzes_then_builds_the_histograms(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The histograms follow the tables' ANALYZE, in the same step."""
    events: list[str] = []

    class _Analyzing(_HistogramDB):
        def analyze_table(self, table_name: str) -> None:
            events.append(f'analyze {table_name}')

    monkeypatch.setattr(
        do_import_tables, 'update_histograms', lambda ctx: events.append('histograms')
    )
    do_import_tables.analyze_all_tables(make_context(db=_Analyzing({})))
    assert events == ['analyze obs_general', 'analyze obs_ring_geometry', 'histograms']


class _AnswerDB(ImportDBMySQL):
    """An ImportDBMySQL that records each query and answers it with fixed rows."""

    def __init__(self, answer: list[tuple[Any, ...]], *, read_only: bool = False) -> None:
        # Deliberately skips ImportDBMySQL.__init__, which connects to a server.
        ImportDBSuper.__init__(
            self, 'host', 'db', 'schema', 'user', 'password', logger=None, read_only=read_only
        )
        self.answer = answer
        self.queries: list[tuple[str, Any]] = []
        self.executed: list[str] = []

    def _execute_and_fetchall(
        self, cmd: str, func_name: str, param_list: Any = None
    ) -> list[tuple[Any, ...]]:
        self.queries.append((cmd, param_list))
        return self.answer

    def _execute(
        self, cmd: str, param_list: Any = None, cur: Any = None, mutates: bool = False
    ) -> None:
        self.executed.append(cmd)


def test_update_histograms_names_the_base_table_and_every_column() -> None:
    """One statement for the table, ``obs_general`` rendered as its base table."""
    db = _AnswerDB([('schema.obs_general_rows', 'histogram', 'status', 'Histogram ... created')])
    db.update_histograms('obs_general', ['opus_id', 'quantity'])
    assert db.queries == [
        (
            'ANALYZE TABLE `obs_general_rows` UPDATE HISTOGRAM ON `opus_id`,`quantity`',
            None,
        )
    ]


def test_drop_histograms_drops_from_every_column() -> None:
    """The drop takes the same shape."""
    db = _AnswerDB([('schema.obs_pds', 'histogram', 'status', 'Histogram ... deleted')])
    db.drop_histograms('obs_pds', ['note'])
    assert db.queries == [('ANALYZE TABLE `obs_pds` DROP HISTOGRAM ON `note`', None)]


def test_an_error_row_in_the_result_raises() -> None:
    """The statement reports a failure as a row, not as a server error."""
    db = _AnswerDB(
        [
            ('schema.obs_pds', 'histogram', 'status', "Histogram ... created for 'a'"),
            ('schema.obs_pds', 'histogram', 'Error', "The column 'b' does not exist."),
        ]
    )
    with pytest.raises(ImportDBError, match="The column 'b' does not exist"):
        db.update_histograms('obs_pds', ['a', 'b'])


def test_no_column_is_refused_before_anything_runs() -> None:
    """``ON`` with no column would be a syntax error, and nothing to do."""
    db = _AnswerDB([])
    with pytest.raises(ImportDBError, match='at least one column'):
        db.update_histograms('obs_pds', [])
    assert db.queries == []


def test_a_read_only_run_builds_no_histogram() -> None:
    """A simulated run logs the statement and reads no result."""
    db = _AnswerDB([], read_only=True)
    db.update_histograms('obs_pds', ['note'])
    assert db.queries == []
    assert db.executed == ['ANALYZE TABLE `obs_pds` UPDATE HISTOGRAM ON `note`']


def test_read_histograms_reports_the_base_table_as_obs_general() -> None:
    """The import names ``obs_general``'s base table by the view's name."""
    db = _AnswerDB([('obs_general_rows', 'opus_id'), ('obs_pds', 'note'), ('obs_pds', 'zz')])
    assert db.read_histograms() == {'obs_general': ['opus_id'], 'obs_pds': ['note', 'zz']}
    ((statement, parameters),) = db.queries
    assert 'COLUMN_STATISTICS' in statement
    assert parameters == ['schema']
