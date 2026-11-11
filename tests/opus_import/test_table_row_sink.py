"""The per-index row sink: when it loads each table, and in what order."""

from __future__ import annotations

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

    def quote_identifier(self, name: str) -> str:
        """Backtick-quote a name."""
        return f'`{name}`'

    def bulk_load_rows(self, table_name: str, rows: list[dict[str, Any]]) -> None:
        """Record a load and its size."""
        self.events.append(('load', table_name, len(rows)))

    def delete_rows(self, table_name: str, where: str, where_params: list[Any]) -> None:
        """Record a delete, the column it selects by and the ids it runs from and to."""
        column, rest = where.split(' ', 1)
        assert rest == f'>= %s AND {column} < %s'
        self.events.append(('delete', table_name, (column, *where_params)))

    def update_row(
        self, table_name: str, row: dict[str, Any], where: str, where_params: list[Any]
    ) -> None:
        """Record the bundle's progress."""
        assert (table_name, where) == ('import_bundle', '`bundle_number`=%s')
        self.events.append(('progress', str(where_params[0]), row['rows_done']))


ORDER = ['obs_general', 'obs_surface_geometry_target', 'obs_files']


#: The bundle's registered range: ids 10 to 99.
_RANGE = bundle_registry.BundleRange(7, 'B_7', 1, 10, 90, 'importing')


def _sink(transaction_rows: int) -> tuple[TableRowSink, _LoadingDB]:
    """Return a sink over a recording database, importing a bundle with `_RANGE`."""
    db = _LoadingDB(transaction_rows)
    ctx = make_context(db=db)
    ctx.bundle_ids = bundle_registry.BundleIds(_RANGE)
    return TableRowSink(ctx, list(ORDER)), db


def _loads(db: _LoadingDB) -> list[tuple[str, str, Any]]:
    """Return the loads recorded, without the progress records."""
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


def test_each_obs_general_load_records_the_bundles_rows_done() -> None:
    """The registry's count follows every load of observations, and no other table's."""
    sink, db = _sink(2)
    for number in range(5):
        sink.add('obs_general', {'id': number})
        sink.add('obs_files', {'obs_general_id': number})
    sink.finish()
    assert [event for event in db.events if event[0] == 'progress'] == [
        ('progress', '7', 2),
        ('progress', '7', 4),
        ('progress', '7', 5),
    ]


def test_the_finish_loads_every_table_in_order() -> None:
    """Every body's rows wait with the surface geometry table's and load in its place."""
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
