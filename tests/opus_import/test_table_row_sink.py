"""The per-index row sink: when it loads each table, and in what order."""

from __future__ import annotations

import datetime
from typing import Any

from opus_import import bundle_registry
from opus_import.steps.do_import_index import TableRowSink

from .conftest import make_context


class _LoadingDB:
    """A stand-in recording every load and every delete, in order."""

    def __init__(self, transaction_rows: int) -> None:
        """Hold the load size the sink reads."""
        self.transaction_rows = transaction_rows
        self.events: list[tuple[str, str, Any]] = []
        self.guards: list[object] = []

    def quote_identifier(self, name: str) -> str:
        """Backtick-quote a name."""
        return f'`{name}`'

    def bulk_load_rows(
        self, table_name: str, rows: list[dict[str, Any]], guard: object = None
    ) -> None:
        """Record a load, its size, and the guard its chunks run under."""
        self.events.append(('load', table_name, len(rows)))
        self.guards.append(guard)

    def delete_rows(self, table_name: str, where: str, where_params: list[Any]) -> None:
        """Record a delete, the column it selects by and the ids it runs from and to."""
        column, rest = where.split(' ', 1)
        assert rest == f'>= %s AND {column} < %s'
        self.events.append(('delete', table_name, (column, *where_params)))


ORDER = ['obs_general', 'obs_surface_geometry_target', 'obs_files']


#: The bundle's registered range: ids 10 to 99.
_RANGE = bundle_registry.BundleRange(
    7, 'B_7', 1, 10, 90, 'importing', datetime.datetime(2026, 11, 10, 12, 0, 0)
)


def _sink(transaction_rows: int) -> tuple[TableRowSink, _LoadingDB]:
    """Return a sink over a recording database, importing a bundle with `_RANGE`."""
    db = _LoadingDB(transaction_rows)
    ctx = make_context(db=db)
    ctx.bundle_ids = bundle_registry.BundleIds(_RANGE)
    return TableRowSink(ctx, list(ORDER)), db


def _loads(db: _LoadingDB) -> list[tuple[str, str, Any]]:
    """Return the loads recorded, without the deletes."""
    return [event for event in db.events if event[0] == 'load']


def test_a_table_is_loaded_each_time_a_transactions_worth_of_rows_waits() -> None:
    """Five rows at two per transaction load two, two, and the last one at the finish."""
    sink, db = _sink(2)
    for number in range(5):
        sink.add('obs_general', {'id': number})
    assert _loads(db) == [('load', 'obs_general', 2), ('load', 'obs_general', 2)]
    sink.finish()
    assert _loads(db)[2:] == [
        ('load', 'obs_general', 1),
        ('load', 'obs_surface_geometry_target', 0),
        ('load', 'obs_files', 0),
    ]


def test_every_load_runs_under_the_bundles_guard() -> None:
    """The guard records the bundle's progress in each chunk's transaction, so the sink
    hands it to every table's load."""
    sink, db = _sink(2)
    guard = object()
    sink.ctx.load_guard = guard  # type: ignore[assignment]
    for number in range(3):
        sink.add('obs_general', {'id': number})
        sink.add('obs_files', {'obs_general_id': number})
    sink.finish()
    assert db.guards
    assert all(given is guard for given in db.guards)


def test_an_importers_failed_index_leaves_the_delete_to_the_whole_bundles() -> None:
    """A queue importer deletes the whole failed bundle while it holds the bundle's
    registry row, so the sink takes nothing back itself."""
    sink, db = _sink(2)
    sink.ctx.importer = object()  # type: ignore[assignment]
    sink.add('obs_general', {'id': 10})
    sink.add('obs_general', {'id': 11})
    sink.add('obs_general', {'id': 12})
    sink.discard()
    sink.finish()
    assert [event for event in db.events if event[0] == 'delete'] == []
    assert _loads(db)[0] == ('load', 'obs_general', 2)
    assert ('load', 'obs_general', 1) not in _loads(db)


def test_the_finish_loads_every_table_in_order() -> None:
    """Every body's rows wait with ``obs_surface_geometry_target``'s and load in its place."""
    sink, db = _sink(100)
    sink.add('obs_general', {'id': 1})
    sink.add('obs_surface_geometry__titan', {'target_name': 4, 'obs_general_id': 1})
    sink.add('obs_surface_geometry__dione', {'target_name': 2, 'obs_general_id': 1})
    sink.add('obs_files', {'obs_general_id': 1})
    sink.finish()
    assert _loads(db) == [
        ('load', 'obs_general', 1),
        ('load', 'obs_surface_geometry_target', 2),
        ('load', 'obs_files', 1),
    ]


def test_every_bodys_rows_count_toward_one_tables_transaction() -> None:
    """Two bodies' rows at two per transaction load together, as one table's."""
    sink, db = _sink(2)
    sink.add('obs_surface_geometry__mimas', {'target_name': 1, 'obs_general_id': 1})
    sink.add('obs_surface_geometry__titan', {'target_name': 4, 'obs_general_id': 1})
    assert db.events == [('load', 'obs_surface_geometry_target', 2)]


def test_a_failed_index_takes_back_what_it_loaded_children_first() -> None:
    """Each table loses its rows from the first one loaded to the end of the bundle's
    range, and no other bundle's; nothing waiting is loaded after.

    ``obs_general``, which numbers its own rows, is selected by ``id``, and every other
    table by ``obs_general_id``, the observation its row belongs to.
    """
    sink, db = _sink(2)
    sink.add('obs_general', {'id': 10})
    for number in range(11, 13):
        sink.add('obs_general', {'id': number})
        sink.add('obs_files', {'obs_general_id': number, 'file_number': 1})
    sink.add('obs_surface_geometry__titan', {'target_name': 4, 'obs_general_id': 12})
    sink.add('obs_surface_geometry__dione', {'target_name': 2, 'obs_general_id': 12})
    sink.discard()
    sink.finish()
    deletes = [event for event in db.events if event[0] == 'delete']
    assert deletes == [
        ('delete', 'obs_surface_geometry_target', ('`obs_general_id`', 12, 100)),
        ('delete', 'obs_files', ('`obs_general_id`', 11, 100)),
        ('delete', 'obs_general', ('`id`', 10, 100)),
    ]
    assert [event for event in db.events if event[0] == 'load' and event[2] > 0] == [
        ('load', 'obs_general', 2),
        ('load', 'obs_files', 2),
        ('load', 'obs_surface_geometry_target', 2),
    ]


def test_the_take_back_deletes_obs_general_last_even_when_it_loaded_after_a_child() -> None:
    """A table with many rows per observation can load first; obs_general still goes last."""
    sink, db = _sink(2)
    sink.add('obs_files', {'obs_general_id': 20, 'file_number': 1})
    sink.add('obs_files', {'obs_general_id': 20, 'file_number': 2})
    sink.add('obs_general', {'id': 20})
    sink.add('obs_general', {'id': 21})
    sink.discard()
    deletes = [event[1] for event in db.events if event[0] == 'delete']
    assert deletes == ['obs_files', 'obs_general']


class _RowKeepingDB(_LoadingDB):
    """A stand-in that also keeps the rows of every load."""

    def __init__(self, transaction_rows: int) -> None:
        """Hold the load size, and no rows yet."""
        super().__init__(transaction_rows)
        self.rows: dict[str, list[dict[str, Any]]] = {}

    def bulk_load_rows(
        self, table_name: str, rows: list[dict[str, Any]], guard: object = None
    ) -> None:
        """Record the load and keep its rows."""
        super().bulk_load_rows(table_name, rows, guard)
        self.rows.setdefault(table_name, []).extend(dict(row) for row in rows)


def _junction_rows(db: _RowKeepingDB) -> dict[str, list[dict[str, Any]]]:
    """Return every row loaded into a junction table, by table."""
    return {
        table: rows
        for table, rows in db.rows.items()
        if table in ('obs_general_target_name', 'obs_general_target_class')
    }


def _keeping_sink(transaction_rows: int) -> tuple[TableRowSink, _RowKeepingDB]:
    """Return a junction sink over a database that keeps what it loads."""
    db = _RowKeepingDB(transaction_rows)
    ctx = make_context(db=db)
    ctx.bundle_ids = bundle_registry.BundleIds(_RANGE)
    sink = TableRowSink(ctx, list(ORDER), {'obs_general': ['target_name', 'target_class']})
    return sink, db


def test_an_obs_general_row_gives_each_list_column_one_junction_row_per_distinct_id() -> None:
    """Each id of each list becomes a row naming the observation; a repeated id one row,
    and an empty list none."""
    sink, db = _keeping_sink(100)
    sink.add('obs_general', {'id': 10, 'target_name': '[4, 9, 4]', 'target_class': '[1]'})
    sink.add('obs_general', {'id': 11, 'target_name': None, 'target_class': '[2, 1]'})
    sink.finish()
    assert _junction_rows(db) == {
        'obs_general_target_name': [
            {'mult_id': 4, 'obs_general_id': 10},
            {'mult_id': 9, 'obs_general_id': 10},
        ],
        'obs_general_target_class': [
            {'mult_id': 1, 'obs_general_id': 10},
            {'mult_id': 2, 'obs_general_id': 11},
            {'mult_id': 1, 'obs_general_id': 11},
        ],
    }


def test_the_junction_tables_load_after_the_tables_and_by_the_transaction() -> None:
    """A junction table loads each time a transaction's worth of its rows waits, and the
    finish loads what is left of it after every listed table."""
    sink, db = _keeping_sink(2)
    sink.add('obs_general', {'id': 10, 'target_name': '[4, 9]', 'target_class': '[1]'})
    assert _loads(db) == [('load', 'obs_general_target_name', 2)]
    sink.finish()
    assert _loads(db)[1:] == [
        ('load', 'obs_general', 1),
        ('load', 'obs_surface_geometry_target', 0),
        ('load', 'obs_files', 0),
        ('load', 'obs_general_target_name', 0),
        ('load', 'obs_general_target_class', 1),
    ]


def test_a_failed_index_takes_back_its_junction_rows_by_observation() -> None:
    """A junction table's rows are taken back by ``obs_general_id``, before obs_general."""
    sink, db = _keeping_sink(1)
    sink.add('obs_general', {'id': 10, 'target_name': '[4]', 'target_class': '[1]'})
    sink.discard()
    deletes = [event for event in db.events if event[0] == 'delete']
    assert deletes == [
        ('delete', 'obs_general_target_class', ('`obs_general_id`', 10, 100)),
        ('delete', 'obs_general_target_name', ('`obs_general_id`', 10, 100)),
        ('delete', 'obs_general', ('`id`', 10, 100)),
    ]


def test_a_table_without_list_columns_gives_no_junction_rows() -> None:
    """Only the tables `junctions` names give junction rows."""
    sink, db = _keeping_sink(100)
    sink.add('obs_files', {'obs_general_id': 10, 'target_name': '[4]'})
    sink.finish()
    assert not any(_junction_rows(db).values())
