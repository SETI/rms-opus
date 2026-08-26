"""SQL generation in the MySQL import backend.

These tests never open a connection: they build an `ImportDBMySQL` through
`ImportDBSuper.__init__` and capture what it would have executed. What they pin is the
shape of the statement: one statement per packet of rows, **every** value passed as a
parameter rather than interpolated, and the key column left out of the update clause.

PR-12 tightened the middle one. Before it, only `str` values became parameters and
everything else -- numbers, booleans, None -- was formatted into the statement text with
`str()`; now every value is a `%s`, which is what makes "no value is ever formatted into
SQL text" true of this backend rather than nearly true. The identifier tests below cover
the other half of that change.
"""

from typing import Any

import pytest

from opus_import.importdb.super import ImportDBError, ImportDBSuper

# mysqlclient is a runtime dependency, but `importdb/mysql.py` guards its own import so
# the package stays importable without it. Skip the whole module rather than failing
# collection in an environment that does not have the driver.
MySQLdb = pytest.importorskip('MySQLdb')

from opus_import.importdb.mysql import ImportDBMySQL  # noqa: E402 - follows the skip


class _RecordingDB(ImportDBMySQL):
    """An ImportDBMySQL that records statements instead of running them."""

    def __init__(self) -> None:
        # Deliberately skips ImportDBMySQL.__init__, which connects to a server.
        ImportDBSuper.__init__(self, 'host', 'db', 'schema', 'user', 'password',
                               import_prefix='imp_', logger=None)
        self.executed: list[tuple[str, list[Any] | None]] = []

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
    assert values_clause.count('(%s,%s,%s,%s,%s,%s,%s,%s)') == 3
    # Nothing at all is interpolated into the statement -- not the string values,
    # and not the numeric id or the None columns either.
    assert 'JUP' not in cmd
    assert 'NULL' not in cmd
    # Eight columns per row, in sorted-column order: aliases, disp_order, display,
    # group_disp_order, grouping, id, label, value.
    assert params == [None, '000', 'Y', None, None, 0, 'JUP', 'JUP',
                      None, '001', 'Y', None, None, 1, 'SAT', 'SAT',
                      None, '002', 'Y', None, None, 2, 'URA', 'URA']


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
    # Eight columns per row, every one of them a parameter.
    assert [len(params) // 8 for _cmd, params in db.executed
            if params is not None] == [1000, 1000, 500]


def test_upsert_rows_groups_rows_that_have_different_columns(db: _RecordingDB) -> None:
    """A mixed row set still produces correct statements, one per column set."""
    db.upsert_rows('import', 'mult_x', 'id',
                   [{'id': 0, 'value': 'a'}, {'id': 1, 'value': 'b', 'extra': 'c'}])

    assert len(db.executed) == 2
    # Sorted-column order per group: (id, value), then (extra, id, value).
    assert db.executed[0][1] == [0, 'a']
    assert db.executed[1][1] == ['c', 1, 'b']


def test_upsert_rows_does_nothing_for_an_empty_row_set(db: _RecordingDB) -> None:
    """An empty mult table must not produce a syntactically invalid INSERT."""
    db.upsert_rows('import', 'mult_x', 'id', [])

    assert db.executed == []


def test_upsert_rows_passes_a_missing_value_as_a_parameter(db: _RecordingDB) -> None:
    """None is a bound parameter like any other value; MySQLdb renders it as NULL."""
    db.upsert_rows('import', 'mult_x', 'id',
                   [{'id': 0, 'value': None}, {'id': 1, 'value': 'a'}])

    assert len(db.executed) == 1
    cmd, params = db.executed[0]
    assert 'VALUES(%s,%s),(%s,%s)' in cmd
    assert params == [0, None, 1, 'a']


def test_upsert_rows_omits_the_update_clause_for_a_key_only_row(
        db: _RecordingDB) -> None:
    """With nothing but the key there is nothing to assign, so no dangling clause.

    Not reachable with today's eight-column mult rows, but the row-by-row
    implementation emitted `ON DUPLICATE KEY UPDATE ` with an empty assignment list,
    which is a syntax error.
    """
    db.upsert_rows('import', 'mult_x', 'id', [{'id': 0}])

    cmd, params = db.executed[0]
    assert 'ON DUPLICATE KEY UPDATE' not in cmd
    assert cmd == 'INSERT INTO `imp_mult_x` (`id`) VALUES(%s)'
    assert params == [0]


@pytest.mark.parametrize('name', ['obs_general', 'imp_obs_general', 'cache_12',
                                  'J2000_longitude', '_mult_val_'])
def test_quote_identifier_accepts_the_names_opus_uses(db: _RecordingDB,
                                                      name: str) -> None:
    """Everything OPUS actually names is letters, digits and underscores."""
    assert db.quote_identifier(name) == f'`{name}`'


@pytest.mark.parametrize('name', [
    'obs`general',        # would end the quoting early
    'obs_general.id',     # a qualified name is two identifiers, not one
    'obs general',
    'obs;DROP TABLE x',
    '',
    None,
    17,
])
def test_quote_identifier_rejects_anything_else(db: _RecordingDB,
                                                name: Any) -> None:
    """Backticks quote a name but do not escape a backtick inside it."""
    with pytest.raises(ImportDBError):
        db.quote_identifier(name)


def test_where_clause_values_travel_as_parameters(db: _RecordingDB) -> None:
    """delete_rows and copy_rows_between_namespaces take their own parameters.

    Their callers used to build `bundle_id="COISS_2002"` by interpolation, which is
    the one place in the import pipeline where a value read off the command line
    reached the statement text.
    """
    where = f'{db.quote_identifier("bundle_id")}=%s'
    db.delete_rows('perm', 'obs_general', where, where_params=['COISS_2002'])
    db.copy_rows_between_namespaces('import', 'perm', 'obs_general', where=where,
                                    where_params=['COISS_2002'])

    assert db.executed == [
        ('DELETE FROM `obs_general` WHERE `bundle_id`=%s', ['COISS_2002']),
        ('INSERT INTO `obs_general` SELECT * FROM `imp_obs_general`'
         ' WHERE `bundle_id`=%s', ['COISS_2002']),
    ]


def test_a_where_clause_with_no_parameters_passes_none(db: _RecordingDB) -> None:
    """An empty parameter list would make MySQLdb interpolate, so pass None."""
    db.delete_rows('perm', 'obs_general')

    assert db.executed == [('DELETE FROM `obs_general`', None)]


def test_update_row_parameterizes_the_set_values_and_the_where(
        db: _RecordingDB) -> None:
    """The SET list and the WHERE clause contribute parameters in that order."""
    db.update_row('perm', 'mult_x', {'label': 'Saturn', 'disp_order': 3},
                  f'{db.quote_identifier("id")}=%s', where_params=[7])

    assert db.executed == [
        ('UPDATE `mult_x` SET `disp_order`=%s,`label`=%s WHERE `id`=%s',
         [3, 'Saturn', 7]),
    ]


def test_upsert_row_omits_the_update_clause_for_a_key_only_row(
        db: _RecordingDB) -> None:
    """With nothing but the key there is nothing to assign, so no dangling clause.

    The same rule `upsert_rows` follows. It is not reachable through the pipeline,
    which no longer calls `upsert_row` at all, but the method is part of the
    `ImportDBSuper` backend interface and an empty assignment list is a syntax
    error, so the two siblings should not disagree about it.
    """
    db.upsert_row('import', 'mult_x', 'id', {'id': 0})

    cmd, params = db.executed[0]
    assert 'ON DUPLICATE KEY UPDATE' not in cmd
    assert cmd == 'INSERT INTO `imp_mult_x` (`id`) VALUES(%s)'
    assert params == [0]


def test_upsert_row_assigns_every_column_except_the_key(db: _RecordingDB) -> None:
    """The ordinary case still updates the non-key columns, values bound twice."""
    db.upsert_row('import', 'mult_x', 'id', {'id': 0, 'value': 'a'})

    cmd, params = db.executed[0]
    assert cmd == ('INSERT INTO `imp_mult_x` (`id`,`value`) VALUES(%s,%s) '
                   'ON DUPLICATE KEY UPDATE `value`=%s')
    # The row's values, then the values the update clause re-binds.
    assert params == [0, 'a', 'a']


class _FailingDB(_RecordingDB):
    """An ImportDBMySQL whose every statement fails the way the server would."""

    def _execute(self, cmd: str, param_list: Any = None, cur: Any = None,
                 mutates: bool = False) -> None:
        raise MySQLdb.Error(1146, "Table 'x' doesn't exist")


@pytest.mark.parametrize(('method', 'args'), [
    ('delete_rows', ('import', 'obs_general')),
    ('copy_rows_between_namespaces', ('import', 'perm', 'obs_general')),
    ('upsert_rows', ('import', 'mult_x', 'id', [{'id': 0, 'value': 'a'}])),
], ids=['delete_rows', 'copy_rows_between_namespaces', 'upsert_rows'])
def test_a_failed_statement_becomes_an_import_db_error(method: str,
                                                       args: tuple[Any, ...]
                                                       ) -> None:
    """Every mutating method reports a server failure as ImportDBError.

    `delete_rows` and `copy_rows_between_namespaces` used to let the raw
    `MySQLdb.Error` escape, which is the one kind of database failure a plain
    `except Exception:` could have swallowed without the top-level handler ever
    seeing it.
    """
    db = _FailingDB()

    with pytest.raises(ImportDBError) as excinfo:
        getattr(db, method)(*args)

    assert "Table 'x' doesn't exist" in str(excinfo.value)
    assert isinstance(excinfo.value.__cause__, MySQLdb.Error)
