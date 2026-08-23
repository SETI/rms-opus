"""SQL generation in the MySQL import backend.

These tests never open a connection: they build an `ImportDBMySQL` through
`ImportDBSuper.__init__` and capture what it would have executed. What they pin is the
shape of the statement, which is what a later refactor (plan PR-12 formalizes SQL
assembly) has to keep: one statement per packet of rows, every string value passed as a
parameter rather than interpolated, and the key column left out of the update clause.
"""

from typing import Any

import pytest

from opus_import.importdb.mysql import ImportDBMySQL
from opus_import.importdb.super import ImportDBSuper


class _RecordingDB(ImportDBMySQL):
    """An ImportDBMySQL that records statements instead of running them."""

    def __init__(self) -> None:
        # Deliberately skips ImportDBMySQL.__init__, which connects to a server.
        ImportDBSuper.__init__(self, 'host', 'db', 'schema', 'user', 'password',
                               import_prefix='imp_', logger=None)
        self.executed: list[tuple[str, list[Any]]] = []

    def _execute(self, cmd: str, param_list: Any = None, cur: Any = None,
                 mutates: bool = False) -> None:
        self.executed.append((cmd, param_list))


def _mult_row(id_num: int, value: str) -> dict[str, Any]:
    return {'id': id_num, 'value': value, 'label': value, 'disp_order': f'{id_num:03d}',
            'display': 'Y', 'grouping': None, 'group_disp_order': None, 'aliases': None}


@pytest.fixture
def db() -> _RecordingDB:
    return _RecordingDB()


def test_upsert_rows_writes_every_row_in_one_statement(db: _RecordingDB) -> None:
    """Three rows of one table become one INSERT, not three."""
    db.upsert_rows('import', 'mult_obs_general_planet_id', 'id',
                   [_mult_row(0, 'JUP'), _mult_row(1, 'SAT'), _mult_row(2, 'URA')])

    assert len(db.executed) == 1
    cmd, params = db.executed[0]
    assert cmd.startswith('INSERT INTO `imp_mult_obs_general_planet_id` (')
    assert cmd.count('ON DUPLICATE KEY UPDATE') == 1
    # Three value tuples, one per row, ahead of the update clause.
    values_clause = cmd.split('ON DUPLICATE KEY UPDATE', 1)[0]
    assert values_clause.count('(NULL,%s,%s,NULL,NULL,') == 3
    # Every string value is a parameter; nothing is interpolated into the statement.
    assert 'JUP' not in cmd
    # Four string columns per row, in sorted-column order:
    # disp_order, display, label, value.
    assert params == ['000', 'Y', 'JUP', 'JUP',
                      '001', 'Y', 'SAT', 'SAT',
                      '002', 'Y', 'URA', 'URA']


def test_upsert_rows_does_not_assign_the_key_column(db: _RecordingDB) -> None:
    """The key identifies the row being updated, so it must not be in the SET list."""
    db.upsert_rows('import', 'mult_obs_general_planet_id', 'id', [_mult_row(0, 'JUP')])

    cmd, _params = db.executed[0]
    update_clause = cmd.split('ON DUPLICATE KEY UPDATE', 1)[1]
    assert '`id`=' not in update_clause
    assert '`value`=VALUES(`value`)' in update_clause


def test_upsert_rows_splits_large_row_sets_into_packets(db: _RecordingDB) -> None:
    """MySQL rejects an unbounded statement, so rows go 1000 at a time."""
    db.upsert_rows('perm', 'mult_obs_general_target_name', 'id',
                   [_mult_row(i, f'T{i}') for i in range(2500)])

    assert len(db.executed) == 3
    assert [cmd.count('ON DUPLICATE KEY UPDATE') for cmd, _ in db.executed] == [1, 1, 1]
    assert [len(params) // 4 for _cmd, params in db.executed] == [1000, 1000, 500]


def test_upsert_rows_groups_rows_that_have_different_columns(db: _RecordingDB) -> None:
    """A mixed row set still produces correct statements, one per column set."""
    db.upsert_rows('import', 'mult_x', 'id',
                   [{'id': 0, 'value': 'a'}, {'id': 1, 'value': 'b', 'extra': 'c'}])

    assert len(db.executed) == 2
    assert db.executed[0][1] == ['a']
    assert db.executed[1][1] == ['c', 'b']


def test_upsert_rows_does_nothing_for_an_empty_row_set(db: _RecordingDB) -> None:
    """An empty mult table must not produce a syntactically invalid INSERT."""
    db.upsert_rows('import', 'mult_x', 'id', [])

    assert db.executed == []


def test_upsert_rows_writes_null_for_a_missing_value(db: _RecordingDB) -> None:
    """None becomes the SQL NULL literal rather than a bound parameter."""
    db.upsert_rows('import', 'mult_x', 'id', [{'id': 0, 'value': None}])

    cmd, params = db.executed[0]
    assert 'VALUES(0,NULL)' in cmd
    assert params == []
