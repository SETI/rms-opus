"""The per-index row sink: when it loads each table, and in what order."""

from __future__ import annotations

from typing import Any

from opus_import.steps.do_import_index import TableRowSink

from .conftest import make_context


class _LoadingDB:
    """A stand-in recording every table created and every load, in order."""

    def __init__(self, transaction_rows: int) -> None:
        """Hold the load size the sink reads."""
        self.transaction_rows = transaction_rows
        self.events: list[tuple[str, str, Any]] = []

    def quote_identifier(self, name: str) -> str:
        """Backtick-quote a name."""
        return f'`{name}`'

    def create_table(self, table_name: str, schema: Any) -> bool:
        """Record a table created."""
        self.events.append(('create', table_name, len(schema)))
        return True

    def bulk_load_rows(self, table_name: str, rows: list[dict[str, Any]]) -> None:
        """Record a load and its size."""
        self.events.append(('load', table_name, len(rows)))

    def delete_rows(self, table_name: str, where: str, where_params: list[Any]) -> None:
        """Record a delete, the column it selects by and the id it starts from."""
        column, rest = where.split(' ', 1)
        assert rest == '>= %s'
        self.events.append(('delete', table_name, (column, where_params[0])))


ORDER = ['obs_general', 'obs_surface_geometry__<TARGET>', 'obs_files']


def _sink(transaction_rows: int) -> tuple[TableRowSink, _LoadingDB]:
    """Return a sink over a recording database."""
    db = _LoadingDB(transaction_rows)
    return TableRowSink(make_context(db=db), list(ORDER)), db


def test_a_table_is_loaded_each_time_a_transactions_worth_of_rows_waits() -> None:
    """Five rows at two per transaction load two, two, and the last one at the finish."""
    sink, db = _sink(2)
    for number in range(5):
        sink.add('obs_general', {'id': number}, None)
    assert [event for event in db.events if event[0] == 'load'] == [
        ('load', 'obs_general', 2),
        ('load', 'obs_general', 2),
    ]
    sink.finish()
    assert db.events[2:] == [('load', 'obs_general', 1), ('load', 'obs_files', 0)]


def test_the_finish_loads_every_table_in_order_and_targets_by_name() -> None:
    """Targets load in their template's place, sorted by target name, each created first."""
    sink, db = _sink(100)
    sink.add('obs_general', {'id': 1}, None)
    sink.add('obs_surface_geometry__titan', {'id': 1, 'obs_general_id': 1}, 'TITAN')
    sink.add('obs_surface_geometry__dione', {'id': 1, 'obs_general_id': 1}, 'DIONE')
    sink.add('obs_files', {'obs_general_id': 1}, None)
    sink.finish()
    assert [(kind, table) for kind, table, _size in db.events] == [
        ('load', 'obs_general'),
        ('create', 'obs_surface_geometry__dione'),
        ('load', 'obs_surface_geometry__dione'),
        ('create', 'obs_surface_geometry__titan'),
        ('load', 'obs_surface_geometry__titan'),
        ('load', 'obs_files'),
    ]


def test_a_new_target_is_logged_once_and_its_table_created_once() -> None:
    """The first row of a target names it; a table loaded twice is created only before the first."""
    sink, db = _sink(1)
    sink.add('obs_surface_geometry__mimas', {'id': 1, 'obs_general_id': 1}, 'MIMAS')
    sink.add('obs_surface_geometry__mimas', {'id': 2, 'obs_general_id': 2}, 'MIMAS')
    sink.finish()
    assert [event[:2] for event in db.events if event[1].endswith('mimas')] == [
        ('create', 'obs_surface_geometry__mimas'),
        ('load', 'obs_surface_geometry__mimas'),
        ('load', 'obs_surface_geometry__mimas'),
        ('load', 'obs_surface_geometry__mimas'),
    ]
    debug = sink.ctx.logger.messages_at('debug')
    assert debug.count('Creating surface geo table for new target MIMAS') == 1


def test_a_failed_index_takes_back_what_it_loaded_children_first() -> None:
    """Each table loses its rows from the first one loaded; nothing waiting is loaded after.

    ``obs_general`` and a surface geometry table, which number their own rows, are
    selected by ``id``, and every other table by ``obs_general_id``, the observation its
    row belongs to.
    """
    sink, db = _sink(2)
    sink.add('obs_general', {'id': 10}, None)
    for number in range(11, 13):
        sink.add('obs_general', {'id': number}, None)
        sink.add('obs_files', {'obs_general_id': number, 'file_number': 1}, None)
    sink.add('obs_surface_geometry__titan', {'id': 7, 'obs_general_id': 12}, 'TITAN')
    sink.add('obs_surface_geometry__titan', {'id': 8, 'obs_general_id': 12}, 'TITAN')
    sink.discard()
    sink.finish()
    deletes = [event for event in db.events if event[0] == 'delete']
    assert deletes == [
        ('delete', 'obs_surface_geometry__titan', ('`id`', 7)),
        ('delete', 'obs_files', ('`obs_general_id`', 11)),
        ('delete', 'obs_general', ('`id`', 10)),
    ]
    assert [event for event in db.events if event[0] == 'load' and event[2] > 0] == [
        ('load', 'obs_general', 2),
        ('load', 'obs_files', 2),
        ('load', 'obs_surface_geometry__titan', 2),
    ]
