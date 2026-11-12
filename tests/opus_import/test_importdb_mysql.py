"""SQL generation in the MySQL import backend.

These tests never open a connection: they build an `ImportDBMySQL` through
`ImportDBSuper.__init__` and capture what it would have executed. What they pin is the
shape of the statement: one statement per packet of rows, **every** value passed as a
parameter rather than interpolated, and the key column left out of the update clause.

The middle one is the one to watch: every value is a `%s`, numbers and booleans and
None included, which is what makes "no value is ever formatted into SQL text" true of
this backend rather than nearly true. The identifier tests below cover the other half
of that property, the names that cannot travel as parameters at all.
"""

from __future__ import annotations

import json
import re
import warnings
from pathlib import Path
from typing import Any

import pytest

import opus_import
from opus_import import bundle_registry, import_processes
from opus_import.importdb.super import ImportDBError, ImportDBSuper, RollbackError

# mysqlclient is a runtime dependency, but `importdb/mysql.py` guards its own import so
# the package stays importable without it. Skip the whole module rather than failing
# collection in an environment that does not have the driver.
MySQLdb = pytest.importorskip('MySQLdb')

from opus_import.importdb.mysql import (  # noqa: E402 - follows the skip
    BULK_LOAD_PATH_FILE,
    BULK_LOAD_PATH_INSERT,
    ImportDBMySQL,
    load_data_text,
)


class _SilentConnection:
    """A connection whose cursor runs nothing and whose server reports nothing."""

    def cursor(self) -> _SilentConnection:
        return self

    def __enter__(self) -> _SilentConnection:
        return self

    def __exit__(self, *exc: object) -> None:
        return None

    @staticmethod
    def info() -> None:
        return None

    def commit(self) -> None:
        return None

    @staticmethod
    def fileno() -> None:
        return None


class _RecordingDB(ImportDBMySQL):
    """An ImportDBMySQL that records statements instead of running them."""

    def __init__(self) -> None:
        # Deliberately skips ImportDBMySQL.__init__, which connects to a server.
        ImportDBSuper.__init__(self, 'host', 'db', 'schema', 'user', 'password', logger=None)
        self.conn = _SilentConnection()
        self.executed: list[tuple[str, list[Any] | None]] = []

    def _execute(
        self, cmd: str, param_list: Any = None, cur: Any = None, mutates: bool = False
    ) -> None:
        self.executed.append((cmd, param_list))


def _mult_row(id_num: int, value: str) -> dict[str, Any]:
    return {
        'id': id_num,
        'value': value,
        'label': value,
        'disp_order': f'{id_num:03d}',
        'display': 'Y',
        'grouping': None,
        'group_disp_order': None,
        'aliases': None,
    }


@pytest.fixture
def db() -> _RecordingDB:
    return _RecordingDB()


def test_upsert_rows_writes_every_row_in_one_statement(db: _RecordingDB) -> None:
    """Three rows of one table become one INSERT, not three."""
    db.upsert_rows(
        'mult_obs_general_planet_id',
        'id',
        [_mult_row(0, 'JUP'), _mult_row(1, 'SAT'), _mult_row(2, 'URA')],
    )

    assert len(db.executed) == 1
    cmd, params = db.executed[0]
    assert cmd.startswith('INSERT INTO `mult_obs_general_planet_id` (')
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
    assert params == [
        None,
        '000',
        'Y',
        None,
        None,
        0,
        'JUP',
        'JUP',
        None,
        '001',
        'Y',
        None,
        None,
        1,
        'SAT',
        'SAT',
        None,
        '002',
        'Y',
        None,
        None,
        2,
        'URA',
        'URA',
    ]


def test_upsert_rows_does_not_assign_the_key_column(db: _RecordingDB) -> None:
    """The key identifies the row being updated, so it must not be in the SET list."""
    db.upsert_rows('mult_obs_general_planet_id', 'id', [_mult_row(0, 'JUP')])

    cmd, _params = db.executed[0]
    update_clause = cmd.split('ON DUPLICATE KEY UPDATE', 1)[1]
    assert '`id`=' not in update_clause
    assert '`value`=`new`.`value`' in update_clause


def test_upsert_rows_names_the_new_row_through_the_alias_not_values(db: _RecordingDB) -> None:
    """The update clause reads the row alias, and `VALUES(col)` is gone entirely.

    ``VALUES(col)`` was deprecated in MySQL 8.0.20 and still parses, so a server would
    accept either form and the deprecation would go on being emitted with nothing to
    report it. Only reading the statement catches that, which is what this does: the
    alias is declared once, immediately before the clause that reads it, and the
    deprecated spelling appears nowhere.
    """
    db.upsert_rows('mult_obs_general_planet_id', 'id', [_mult_row(0, 'JUP'), _mult_row(1, 'SAT')])

    cmd, _params = db.executed[0]
    assert 'VALUES(`' not in cmd
    assert cmd.count(' AS `new` ON DUPLICATE KEY UPDATE ') == 1
    update_clause = cmd.split('ON DUPLICATE KEY UPDATE', 1)[1]
    # Every assigned column reads its value off the alias -- the whole point of the
    # form, and what a partial rewrite would leave half true.
    assignments = update_clause.strip().split(',')
    assert len(assignments) == 7
    for assignment in assignments:
        column, value = assignment.split('=')
        assert value == f'`new`.{column}', assignment


def test_upsert_rows_does_not_alias_a_row_as_the_table_it_writes(db: _RecordingDB) -> None:
    """A table called ``new`` gets a different row alias, because MySQL forbids the clash.

    MySQL requires the row alias to differ from the table name, so the one name that
    collides would reach the statement as it is. Nothing in today's schema is called ``new`` --
    which is exactly why this is a test rather than a comment: the collision would first
    appear as a syntax error partway through an import of some future table, and the
    packet loop would already have written the earlier ones.
    """
    db.upsert_rows('new', 'id', [{'id': 0, 'value': 'a'}, {'id': 1, 'value': 'b'}])

    cmd, _params = db.executed[0]
    assert cmd.startswith('INSERT INTO `new` (')
    assert ' AS `new_row` ON DUPLICATE KEY UPDATE `value`=`new_row`.`value`' in cmd
    # The alias and the table must not be the same identifier, which is the whole rule.
    assert ' AS `new` ' not in cmd


def test_upsert_rows_keeps_the_plain_alias_for_every_other_table(db: _RecordingDB) -> None:
    """The rename is confined to the colliding name; nothing else pays for it.

    Without this, widening the guard -- renaming the alias for every table, or matching
    a prefix -- would go unnoticed, and the statement every real import runs would
    quietly stop being the one the tests above pin.
    """
    db.upsert_rows('newer', 'id', [{'id': 0, 'value': 'a'}])

    cmd, _params = db.executed[0]
    assert ' AS `new` ON DUPLICATE KEY UPDATE ' in cmd
    assert '`new_row`' not in cmd


def test_upsert_rows_splits_large_row_sets_into_packets(db: _RecordingDB) -> None:
    """MySQL rejects an unbounded statement, so rows go 1000 at a time."""
    db.upsert_rows(
        'mult_obs_general_target_name', 'id', [_mult_row(i, f'T{i}') for i in range(2500)]
    )

    assert len(db.executed) == 3
    assert [cmd.count('ON DUPLICATE KEY UPDATE') for cmd, _ in db.executed] == [1, 1, 1]
    # Eight columns per row, every one of them a parameter.
    assert [len(params) // 8 for _cmd, params in db.executed if params is not None] == [
        1000,
        1000,
        500,
    ]


def test_upsert_rows_groups_rows_that_have_different_columns(db: _RecordingDB) -> None:
    """A mixed row set still produces correct statements, one per column set."""
    db.upsert_rows('mult_x', 'id', [{'id': 0, 'value': 'a'}, {'id': 1, 'value': 'b', 'extra': 'c'}])

    assert len(db.executed) == 2
    # Sorted-column order per group: (id, value), then (extra, id, value).
    assert db.executed[0][1] == [0, 'a']
    assert db.executed[1][1] == ['c', 1, 'b']


def test_upsert_rows_does_nothing_for_an_empty_row_set(db: _RecordingDB) -> None:
    """An empty mult table must not produce a syntactically invalid INSERT."""
    db.upsert_rows('mult_x', 'id', [])

    assert db.executed == []


def test_upsert_rows_passes_a_missing_value_as_a_parameter(db: _RecordingDB) -> None:
    """None is a bound parameter like any other value; MySQLdb renders it as NULL."""
    db.upsert_rows('mult_x', 'id', [{'id': 0, 'value': None}, {'id': 1, 'value': 'a'}])

    assert len(db.executed) == 1
    cmd, params = db.executed[0]
    assert 'VALUES(%s,%s),(%s,%s)' in cmd
    assert params == [0, None, 1, 'a']


def test_upsert_rows_omits_the_update_clause_for_a_key_only_row(db: _RecordingDB) -> None:
    """With nothing but the key there is nothing to assign, so no dangling clause.

    Not reachable with today's eight-column mult rows, but the row-by-row
    implementation emitted `ON DUPLICATE KEY UPDATE ` with an empty assignment list,
    which is a syntax error.
    """
    db.upsert_rows('mult_x', 'id', [{'id': 0}])

    cmd, params = db.executed[0]
    assert 'ON DUPLICATE KEY UPDATE' not in cmd
    assert cmd == 'INSERT INTO `mult_x` (`id`) VALUES(%s)'
    assert params == [0]


@pytest.mark.parametrize(
    'name',
    ['obs_general', 'mult_obs_general_planet_id', 'cache_12', 'J2000_longitude', '_mult_val_'],
)
def test_quote_identifier_accepts_the_names_opus_uses(db: _RecordingDB, name: str) -> None:
    """Everything OPUS actually names is letters, digits and underscores."""
    assert db.quote_identifier(name) == f'`{name}`'


@pytest.mark.parametrize(
    'name',
    [
        'obs`general',  # would end the quoting early
        'obs_general.id',  # a qualified name is two identifiers, not one
        'obs general',
        'obs;DROP TABLE x',
        '',
        None,
        17,
    ],
)
def test_quote_identifier_rejects_anything_else(db: _RecordingDB, name: Any) -> None:
    """Backticks quote a name but do not escape a backtick inside it."""
    with pytest.raises(ImportDBError):
        db.quote_identifier(name)


def test_where_clause_values_travel_as_parameters(db: _RecordingDB) -> None:
    """delete_rows takes its own parameters.

    Its WHERE clause is the one place in the import pipeline where a value read
    off the command line reaches a statement, so building `bundle_id="COISS_2002"` by
    interpolation here is what parameters have to keep out.
    """
    where = f'{db.quote_identifier("bundle_id")}=%s'
    db.delete_rows('obs_general', where, where_params=['COISS_2002'])

    assert db.executed == [
        ('DELETE FROM `obs_general` WHERE `bundle_id`=%s', ['COISS_2002']),
    ]


def test_a_joined_delete_deletes_the_rows_of_the_parents_it_selects(db: _RecordingDB) -> None:
    """The child is aliased ``c`` and the parent `JOINED_PARENT_ALIAS`; only ``c`` loses rows."""
    q = db.quote_identifier
    parent = q(db.JOINED_PARENT_ALIAS)
    db.delete_joined_rows(
        'obs_pds',
        'obs_general_id',
        'obs_general',
        'id',
        f'{parent}.{q("bundle_id")} = %s AND {parent}.{q("id")} BETWEEN %s AND %s',
        ['COISS_2002', 4, 9],
    )

    assert db.executed == [
        (
            'DELETE `c` FROM `obs_pds` AS `c` JOIN `obs_general` AS `p` '
            'ON `p`.`id` = `c`.`obs_general_id` '
            'WHERE `p`.`bundle_id` = %s AND `p`.`id` BETWEEN %s AND %s',
            ['COISS_2002', 4, 9],
        )
    ]


def test_a_where_clause_with_no_parameters_passes_none(db: _RecordingDB) -> None:
    """An empty parameter list would make MySQLdb interpolate, so pass None."""
    db.delete_rows('obs_general', '`id` > 0')

    assert db.executed == [('DELETE FROM `obs_general` WHERE `id` > 0', None)]


def test_update_row_parameterizes_the_set_values_and_the_where(db: _RecordingDB) -> None:
    """The SET list and the WHERE clause contribute parameters in that order."""
    db.update_row(
        'mult_x',
        {'label': 'Saturn', 'disp_order': 3},
        f'{db.quote_identifier("id")}=%s',
        where_params=[7],
    )

    assert db.executed == [
        ('UPDATE `mult_x` SET `disp_order`=%s,`label`=%s WHERE `id`=%s', [3, 'Saturn', 7]),
    ]


def test_upsert_row_omits_the_update_clause_for_a_key_only_row(db: _RecordingDB) -> None:
    """With nothing but the key there is nothing to assign, so no dangling clause.

    The same rule `upsert_rows` follows. It is not reachable through the pipeline,
    which does not call `upsert_row` at all, but the method is part of the
    `ImportDBSuper` backend interface and an empty assignment list is a syntax
    error, so the two siblings should not disagree about it.
    """
    db.upsert_row('mult_x', 'id', {'id': 0})

    cmd, params = db.executed[0]
    assert 'ON DUPLICATE KEY UPDATE' not in cmd
    assert cmd == 'INSERT INTO `mult_x` (`id`) VALUES(%s)'
    assert params == [0]


def test_upsert_row_assigns_every_column_except_the_key(db: _RecordingDB) -> None:
    """The ordinary case still updates the non-key columns, values bound twice."""
    db.upsert_row('mult_x', 'id', {'id': 0, 'value': 'a'})

    cmd, params = db.executed[0]
    assert cmd == (
        'INSERT INTO `mult_x` (`id`,`value`) VALUES(%s,%s) ON DUPLICATE KEY UPDATE `value`=%s'
    )
    # The row's values, then the values the update clause re-binds.
    assert params == [0, 'a', 'a']


class _FailingDB(_RecordingDB):
    """An ImportDBMySQL whose every statement fails the way the server would."""

    def _execute(
        self, cmd: str, param_list: Any = None, cur: Any = None, mutates: bool = False
    ) -> None:
        raise MySQLdb.Error(1146, "Table 'x' doesn't exist")


@pytest.mark.parametrize(
    ('method', 'args'),
    [
        ('delete_rows', ('obs_general', '`id`=%s', [1])),
        ('delete_joined_rows', ('obs_pds', 'obs_general_id', 'obs_general', 'id', '1', [])),
        ('upsert_rows', ('mult_x', 'id', [{'id': 0, 'value': 'a'}])),
    ],
    ids=['delete_rows', 'delete_joined_rows', 'upsert_rows'],
)
def test_a_failed_statement_becomes_an_import_db_error(method: str, args: tuple[Any, ...]) -> None:
    """Every mutating method reports a server failure as ImportDBError.

    A raw `MySQLdb.Error` escaping `delete_rows` or `upsert_rows` is the one kind of database failure a plain `except Exception:` could swallow
    without the top-level handler ever seeing it, so every one of them wraps.
    """
    db = _FailingDB()

    with pytest.raises(ImportDBError) as excinfo:
        getattr(db, method)(*args)

    assert "Table 'x' doesn't exist" in str(excinfo.value)
    assert isinstance(excinfo.value.__cause__, MySQLdb.Error)


# ---------------------------------------------------------------------------
# Operations are exception-safe
# ---------------------------------------------------------------------------


def test_a_failed_operation_restores_the_warning_handler_and_the_stack() -> None:
    """A raise inside an operation still runs `_exit`.

    `_enter` installs a process-wide `warnings.showwarning` when a logger is set, and
    left installed it would swallow every later warning in the process.
    """

    class _Logger:
        def log(self, level: str, message: str) -> None:
            pass

    db = _FailingDB()
    db.logger = _Logger()
    before = warnings.showwarning

    with pytest.raises(ImportDBError):
        db.delete_rows('obs_general', '`id`=%s', [1])

    assert warnings.showwarning is before
    assert db._enter_stack == []


def test_create_table_records_the_table_without_a_logger(db: _RecordingDB) -> None:
    """The table-name cache learns of a new table whether or not anything is logged.

    Without that, `table_exists` would answer False for the table just created, and a
    second `create_table` would ask the server to create it again.
    """
    # What ImportDBMySQL.__init__ sets after connecting, which _RecordingDB skips.
    db._table_names = set()
    db._table_info_cache = {}
    db.default_engine = 'INNODB'

    db.create_table('cart', [{'field_name': 'id', 'field_type': 'uint4'}])

    assert db.table_exists('cart')
    assert db.create_table('cart', [{'field_name': 'id', 'field_type': 'uint4'}]) is False


def test_create_table_renders_table_level_keys_and_a_digest_column(db: _RecordingDB) -> None:
    """``search_results`` gets its two-column keys, ``user_searches`` its ``BINARY(32)``."""
    db._table_names = set()
    db._table_info_cache = {}
    db.default_engine = 'INNODB'

    for table in ('search_results', 'user_searches'):
        schema_path = Path(opus_import.__file__).parent / 'table_schemas' / f'{table}.json'
        db.create_table(table, json.loads(schema_path.read_text(encoding='utf-8')))

    search_results, user_searches = (cmd for cmd, _ in db.executed)
    assert 'PRIMARY KEY (`search_id`, `sort_order`)' in search_results
    assert 'UNIQUE KEY `search_id` (`search_id`, `obs_general_id`)' in search_results
    assert '`search_hash` binary(32) NOT NULL' in user_searches
    assert 'UNIQUE KEY `search_hash` (`search_hash`)' in user_searches


def test_create_table_renders_a_columns_character_set(db: _RecordingDB) -> None:
    """``field_charset`` follows the type; a column without one takes the schema's."""
    db._table_names = set()
    db._table_info_cache = {}
    db.default_engine = 'INNODB'

    db.create_table(
        'cart',
        [
            {'field_name': 'session_id', 'field_type': 'varchar40', 'field_charset': 'ascii'},
            {'field_name': 'note', 'field_type': 'text', 'field_charset': 'ascii'},
            {'field_name': 'label', 'field_type': 'varchar100', 'field_notnull': True},
        ],
    )

    ((cmd, _),) = db.executed
    assert '`session_id` varchar(40) CHARACTER SET ascii COLLATE ascii_general_ci DEFAULT' in cmd
    assert '`note` text CHARACTER SET ascii COLLATE ascii_general_ci DEFAULT' in cmd
    assert '`label` varchar(100) NOT NULL' in cmd


@pytest.mark.parametrize(
    'column',
    [
        {'field_name': 'c', 'field_type': 'varchar40', 'field_charset': 'latin1'},
        {'field_name': 'c', 'field_type': 'uint4', 'field_charset': 'ascii'},
    ],
    ids=['unknown-charset', 'not-text'],
)
def test_create_table_refuses_a_character_set_it_cannot_render(
    db: _RecordingDB, column: dict[str, str]
) -> None:
    """Only a text column takes a ``field_charset``, and only one MySQL is given here."""
    db._table_names = set()
    db._table_info_cache = {}
    db.default_engine = 'INNODB'

    with pytest.raises(NotImplementedError):
        db.create_table('cart', [column])

    assert db.executed == []


def test_set_next_id_sets_the_tables_auto_increment(db: _RecordingDB) -> None:
    """The next row the table's key hands out takes the given id."""
    db._table_info_cache = {}
    db.set_next_id('user_searches', 501)
    assert db.executed == [('ALTER TABLE `user_searches` AUTO_INCREMENT = 501', None)]


def test_a_server_error_with_one_argument_is_reported() -> None:
    """An error carrying only a message is reported as itself, not as an IndexError."""

    class _OneArgumentDB(_RecordingDB):
        def _execute(
            self, cmd: str, param_list: Any = None, cur: Any = None, mutates: bool = False
        ) -> None:
            raise MySQLdb.Error('lost connection')

    messages: list[str] = []

    class _Logger:
        def log(self, level: str, message: str) -> None:
            messages.append(message)

    db = _OneArgumentDB()
    db.logger = _Logger()

    with pytest.raises(ImportDBError, match='lost connection'):
        db.delete_rows('obs_general', '`id`=%s', [1])

    assert messages == ['Failed to delete rows from "obs_general": lost connection']


def test_delete_rows_refuses_a_missing_where_clause(db: _RecordingDB) -> None:
    """No clause means nothing is deleted, rather than every row."""
    with pytest.raises(ImportDBError, match='needs a WHERE clause or all_rows=True'):
        db.delete_rows('obs_general')
    with pytest.raises(ImportDBError, match='needs a WHERE clause or all_rows=True'):
        db.delete_rows('obs_general', '')

    assert db.executed == []


def test_delete_rows_refuses_a_where_clause_with_all_rows(db: _RecordingDB) -> None:
    """Asking for every row and for some of them at once is a caller's mistake."""
    with pytest.raises(ImportDBError, match='and not both'):
        db.delete_rows('obs_general', '`id`=%s', [1], all_rows=True)

    assert db.executed == []


def test_delete_rows_deletes_every_row_when_asked(db: _RecordingDB) -> None:
    """`all_rows=True` is the one way to empty a table."""
    db.delete_rows('obs_general', all_rows=True)

    assert db.executed == [('DELETE FROM `obs_general`', None)]


# ---------------------------------------------------------------------------
# The bulk load's text
# ---------------------------------------------------------------------------

# One value per field type the packaged schemas use, with the text the load reads it
# from. `varchar<N>` stands for every width. The set of types is
# regenerated by
#     grep -ho '"field_type": "[a-z_0-9]*"' src/opus_import/table_schemas/*.json | sort -u
# and `test_every_schema_field_type_has_a_case` fails when a schema gains a type with no
# case here.
_FIELD_TYPE_CASES: dict[str, tuple[Any, str]] = {
    'varchar': ('co-iss-n1460960653', 'co-iss-n1460960653'),
    'text': ('a\tb\nc\\d\re\0f', 'a\\tb\\nc\\\\d\\re\\0f'),
    'datetime': ('2026-11-06 12:34:56', '2026-11-06 12:34:56'),
    'enum': ('Y', 'Y'),
    'flag_onoff': (1, '1'),
    'flag_yesno': (0, '0'),
    'int1': (-128, '-128'),
    'int2': (-32768, '-32768'),
    'int4': (-2147483648, '-2147483648'),
    'uint1': (255, '255'),
    'uint2': (65535, '65535'),
    'uint4': (4294967295, '4294967295'),
    'uint8': (18446744073709551615, '18446744073709551615'),
    'mult_idx': (17, '17'),
    'real4': (0.1, '0.1'),
    'real8': (1.7976931348623157e308, '1.7976931348623157e+308'),
    'json': ('{"a": "tab\\there"}', '{"a": "tab\\\\there"}'),
    'mult_list': ('["SATURN", "S RINGS"]', '["SATURN", "S RINGS"]'),
}


def _schema_field_types() -> set[str]:
    """Return every field type the packaged schemas use, widths folded away."""
    schema_dir = Path(opus_import.__file__).parent / 'table_schemas'
    types: set[str] = set()
    for path in schema_dir.glob('*.json'):
        for entry in json.loads(path.read_text(encoding='utf-8')):
            if 'field_type' in entry:
                types.add(re.sub(r'^varchar\d+$', 'varchar', entry['field_type']))
    return types


#: The field types no load writes: ``binary32`` is held only by ``user_searches``, which
#: the web application writes and the import only creates, and `load_data_text` refuses
#: bytes.
_UNLOADED_FIELD_TYPES = {'binary32'}


def test_every_schema_field_type_has_a_case() -> None:
    """A field type added to a schema needs a case below before it can be trusted."""
    assert _schema_field_types() - _UNLOADED_FIELD_TYPES == set(_FIELD_TYPE_CASES)


@pytest.mark.parametrize('field_type', sorted(_FIELD_TYPE_CASES))
def test_load_data_text_renders_each_field_type(field_type: str) -> None:
    """Each type's value becomes the text LOAD DATA reads back as that value."""
    value, text = _FIELD_TYPE_CASES[field_type]
    assert load_data_text(value) == text


@pytest.mark.parametrize(
    ('value', 'text'),
    [
        (None, '\\N'),
        ('', ''),
        ('\\N', '\\\\N'),
        ('NULL', 'NULL'),
        (True, '1'),
        (False, '0'),
        (-0.0, '-0.0'),
        (1e-300, '1e-300'),
        (12345678901234567890, '12345678901234567890'),
        ('Saturn°', 'Saturn°'),
    ],
    ids=[
        'none-is-null',
        'empty-string-is-not-null',
        'backslash-n-string-is-not-null',
        'the-word-null-is-text',
        'true',
        'false',
        'negative-zero',
        'tiny-float',
        'big-integer',
        'non-ascii',
    ],
)
def test_load_data_text_renders_the_edge_cases(value: Any, text: str) -> None:
    """NULL, the empty string and a string spelling NULL stay three different things."""
    assert load_data_text(value) == text


def test_load_data_text_renders_a_float_subclass_as_a_float() -> None:
    """A float subclass is written as the double it holds, not as its own repr."""

    class _Tagged(float):
        def __repr__(self) -> str:
            return f'_Tagged({float(self)})'

    assert load_data_text(_Tagged(0.25)) == '0.25'


def test_load_data_text_refuses_bytes() -> None:
    """No OPUS column holds bytes, and the text has no faithful rendering for them."""
    with pytest.raises(TypeError, match='bytes'):
        load_data_text(b'\x00')


# ---------------------------------------------------------------------------
# The bulk load
# ---------------------------------------------------------------------------


class _FakeCursor:
    """A cursor whose only query result is the connection's first warning."""

    def __init__(self, conn: _FakeConnection) -> None:
        self._conn = conn

    def __enter__(self) -> _FakeCursor:
        return self

    def __exit__(self, *exc: object) -> None:
        return None

    def fetchone(self) -> tuple[str, int, str] | None:
        return self._conn.first_warning


class _FakeConnection:
    """The parts of a MySQLdb connection a bulk load uses."""

    def __init__(self) -> None:
        self.info_text: str | None = None
        self.first_warning: tuple[str, int, str] | None = None
        self.commits = 0
        self.rollbacks = 0

    def cursor(self) -> _FakeCursor:
        return _FakeCursor(self)

    def info(self) -> str | None:
        return self.info_text

    def commit(self) -> None:
        self.commits += 1

    def rollback(self) -> None:
        self.rollbacks += 1


def _counts(records: int, skipped: int = 0, warning_count: int = 0) -> str:
    """Return the info string the server sends after a load."""
    return f'Records: {records}  Deleted: 0  Skipped: {skipped}  Warnings: {warning_count}'


class _LoadingDB(_RecordingDB):
    """A recording backend whose LOAD DATA statements read the scratch file they name.

    Each load records the file's path and lines, and answers with the counts `report`
    returns for those lines -- by default, every line read and nothing skipped.
    """

    def __init__(
        self,
        scratch_dir: Path,
        transaction_rows: int = 100_000,
        report: Any = None,
        refuse_at: int | None = None,
    ) -> None:
        super().__init__()
        self.scratch_dir = str(scratch_dir)
        self.transaction_rows = transaction_rows
        self.bulk_load_path = BULK_LOAD_PATH_FILE
        self.conn = _FakeConnection()
        self.loads: list[tuple[str, list[str]]] = []
        self._report = report or (lambda lines: _counts(len(lines)))
        self._refuse_at = refuse_at

    def _execute(
        self, cmd: str, param_list: Any = None, cur: Any = None, mutates: bool = False
    ) -> None:
        super()._execute(cmd, param_list, cur, mutates)
        if cmd.startswith('LOAD DATA'):
            path = param_list[0]
            lines = Path(path).read_text(encoding='utf-8').split('\n')
            assert lines[-1] == ''
            self.loads.append((path, lines[:-1]))
            if self._refuse_at is not None and len(self.loads) > self._refuse_at:
                raise MySQLdb.OperationalError(3948, 'Loading local data is disabled')
            self.conn.info_text = self._report(lines[:-1])


def _obs_rows(count: int) -> list[dict[str, Any]]:
    return [{'id': n, 'opus_id': f'co-iss-{n}', 'note': None} for n in range(count)]


def _statements(db: _RecordingDB, prefix: str) -> list[tuple[str, list[Any] | None]]:
    return [entry for entry in db.executed if entry[0].startswith(prefix)]


@pytest.mark.parametrize(
    ('row_count', 'transaction_rows', 'loads'),
    [(1, 3, 1), (3, 3, 1), (4, 3, 2), (7, 3, 3), (9, 3, 3), (5, 1, 5), (5, 100_000, 1)],
)
def test_bulk_load_issues_one_load_per_chunk(
    tmp_path: Path, row_count: int, transaction_rows: int, loads: int
) -> None:
    """N rows take N divided by transaction_rows, rounded up, loads, each committed."""
    db = _LoadingDB(tmp_path, transaction_rows=transaction_rows)

    db.bulk_load_rows('obs_general', _obs_rows(row_count))

    assert len(db.loads) == loads
    assert [len(lines) for _, lines in db.loads] == [
        min(transaction_rows, row_count - start) for start in range(0, row_count, transaction_rows)
    ]
    assert db.conn.commits == loads
    assert db.conn.rollbacks == 0


def test_bulk_load_names_the_table_columns_and_character_set(tmp_path: Path) -> None:
    """The statement loads the table, in sorted column order, as utf8mb4."""
    db = _LoadingDB(tmp_path)

    db.bulk_load_rows('obs_general', _obs_rows(2))

    [(cmd, params)] = _statements(db, 'LOAD DATA')
    assert cmd == (
        'LOAD DATA LOCAL INFILE %s INTO TABLE `obs_general` CHARACTER SET utf8mb4 '
        "FIELDS TERMINATED BY '\\t' ESCAPED BY '\\\\' LINES TERMINATED BY '\\n' "
        '(`id`,`note`,`opus_id`)'
    )
    assert params == [db.loads[0][0]]
    assert db.loads[0][1] == ['0\t\\N\tco-iss-0', '1\t\\N\tco-iss-1']


def test_bulk_load_files_are_unique_and_removed(tmp_path: Path) -> None:
    """Two loaders sharing a scratch directory never share a file, and leave none behind."""
    first = _LoadingDB(tmp_path, transaction_rows=2)
    second = _LoadingDB(tmp_path, transaction_rows=2)

    first.bulk_load_rows('obs_general', _obs_rows(5))
    second.bulk_load_rows('obs_general', _obs_rows(5))

    paths = [path for db in (first, second) for path, _ in db.loads]
    assert len(paths) == 6
    assert len(set(paths)) == 6
    assert all(Path(path).parent == tmp_path for path in paths)
    assert all(Path(path).name.startswith('obs_general_') for path in paths)
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize(
    ('report', 'warning', 'message'),
    [
        (lambda lines: _counts(len(lines) - 1), None, '1 rows read of 2, 0 skipped, 0 warnings'),
        (
            lambda lines: _counts(len(lines), skipped=1, warning_count=1),
            ('Warning', 1062, "Duplicate entry '1' for key 'obs_general.PRIMARY'"),
            "1 skipped, 1 warnings; the first: Duplicate entry '1'",
        ),
        (
            lambda lines: _counts(len(lines), warning_count=1),
            ('Warning', 1265, "Data truncated for column 'opus_id' at row 2"),
            "0 skipped, 1 warnings; the first: Data truncated for column 'opus_id'",
        ),
        (lambda lines: None, None, 'the server reported no counts for the load (None)'),
    ],
    ids=['rows-missing', 'duplicate-key', 'truncated-value', 'no-counts'],
)
def test_a_load_that_loses_or_changes_a_row_raises(
    tmp_path: Path, report: Any, warning: tuple[str, int, str] | None, message: str
) -> None:
    """A skipped row, a warning or a short count rolls the chunk back and raises."""
    db = _LoadingDB(tmp_path, report=report)
    db.conn.first_warning = warning

    with pytest.raises(ImportDBError, match=re.escape(message)):
        db.bulk_load_rows('obs_general', _obs_rows(2))

    assert db.conn.rollbacks == 1
    assert db.conn.commits == 0
    assert list(tmp_path.iterdir()) == []
    assert db._enter_stack == []
    asked = _statements(db, 'SHOW WARNINGS')
    assert asked == ([('SHOW WARNINGS LIMIT 1', None)] if warning is not None else [])


def test_a_load_stops_at_the_first_bad_chunk(tmp_path: Path) -> None:
    """The chunks before the bad one stay committed, and none after it is loaded."""
    db = _LoadingDB(
        tmp_path,
        transaction_rows=2,
        report=lambda lines: _counts(len(lines), skipped=int(lines[0].startswith('2\t'))),
    )

    with pytest.raises(ImportDBError, match='1 skipped'):
        db.bulk_load_rows('obs_general', _obs_rows(6))

    assert len(db.loads) == 2
    assert (db.conn.commits, db.conn.rollbacks) == (1, 1)


def test_a_refused_load_falls_back_to_insert_statements(tmp_path: Path) -> None:
    """A refused file sends that chunk and every later one through `insert_rows`."""
    db = _LoadingDB(tmp_path, transaction_rows=2, refuse_at=1)

    db.bulk_load_rows('obs_general', _obs_rows(5))
    db.bulk_load_rows('obs_general', _obs_rows(1))

    assert db.bulk_load_path == BULK_LOAD_PATH_INSERT
    assert len(db.loads) == 2
    inserts = _statements(db, 'INSERT INTO')
    assert len(inserts) == 2
    # Rows 2 to 4 of the first call, then the second call's row.
    assert inserts[0][1] == [2, None, 'co-iss-2', 3, None, 'co-iss-3', 4, None, 'co-iss-4']
    assert inserts[1][1] == [0, None, 'co-iss-0']
    assert (db.conn.commits, db.conn.rollbacks) == (1, 1)
    assert list(tmp_path.iterdir()) == []


def test_any_other_load_failure_raises(tmp_path: Path) -> None:
    """A server error that is not a refusal is an ordinary failure."""

    class _BrokenDB(_LoadingDB):
        def _execute(
            self, cmd: str, param_list: Any = None, cur: Any = None, mutates: bool = False
        ) -> None:
            if cmd.startswith('LOAD DATA'):
                raise MySQLdb.OperationalError(1146, "Table 'x' doesn't exist")
            super()._execute(cmd, param_list, cur, mutates)

    db = _BrokenDB(tmp_path)

    with pytest.raises(ImportDBError, match="Table 'x' doesn't exist"):
        db.bulk_load_rows('obs_general', _obs_rows(1))

    assert db.bulk_load_path == BULK_LOAD_PATH_FILE
    assert db.conn.rollbacks == 1
    assert list(tmp_path.iterdir()) == []


def test_the_insert_path_writes_insert_statements(tmp_path: Path) -> None:
    """With local files refused from the start, no scratch file is ever written."""
    db = _LoadingDB(tmp_path)
    db.bulk_load_path = BULK_LOAD_PATH_INSERT

    db.bulk_load_rows('obs_general', _obs_rows(3))

    assert db.loads == []
    assert len(_statements(db, 'INSERT INTO')) == 1


def test_an_empty_load_does_nothing(tmp_path: Path) -> None:
    """No rows, no file, no statement."""
    db = _LoadingDB(tmp_path)

    db.bulk_load_rows('obs_general', [])

    assert db.executed == []
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize('rows', [0, -5], ids=['zero', 'negative'])
def test_a_transaction_size_below_one_is_refused_before_connecting(rows: int) -> None:
    """A direct caller's bad size would otherwise load nothing, or fail mid-import."""
    with pytest.raises(ValueError, match='transaction_rows must be at least 1'):
        ImportDBMySQL('h', 'd', 's', 'u', 'p', transaction_rows=rows)


class _NoSchemaConnection:
    """A server connection on which every ``USE`` names an unknown database."""

    def __init__(self) -> None:
        self.executed: list[str] = []

    def cursor(self) -> _NoSchemaConnection:
        return self

    def __enter__(self) -> _NoSchemaConnection:
        return self

    def __exit__(self, *exc: object) -> None:
        return None

    def execute(self, cmd: str, param_list: Any = None) -> None:
        self.executed.append(cmd)
        if cmd.startswith('USE '):
            raise MySQLdb.OperationalError(1049, "Unknown database 'absent'")

    def commit(self) -> None:
        return None


def test_a_read_only_connection_does_not_create_an_absent_schema(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A read-only run against a schema the server lacks fails instead of creating it."""
    connection = _NoSchemaConnection()
    monkeypatch.setattr(MySQLdb, 'connect', lambda **kwargs: connection)

    with pytest.raises(ImportDBError, match='"absent" does not exist'):
        ImportDBMySQL('host', 'db', 'absent', 'user', 'password', read_only=True)

    assert connection.executed == ['USE `absent`']


@pytest.mark.parametrize(
    ('data_type', 'char_len', 'charset', 'column'),
    [
        ('varchar', 40, 'utf8mb4', {'field_type': 'varchar40'}),
        ('varchar', 50, 'ascii', {'field_type': 'varchar50', 'field_charset': 'ascii'}),
        ('text', 65535, 'ascii', {'field_type': 'text', 'field_charset': 'ascii'}),
        ('datetime', None, None, {'field_type': 'datetime'}),
        ('binary', 32, None, {'field_type': 'binary32'}),
    ],
)
def test_table_info_reads_back_the_column_create_table_renders(
    data_type: str, char_len: int | None, charset: str | None, column: dict[str, str]
) -> None:
    """A column ``create_table`` can make reads back as the schema entry that made it."""

    class _ColumnsDB(_RecordingDB):
        """A backend whose every table has one column of the case's server type."""

        def _execute_and_fetchall(self, cmd: str, func_name: str, param_list: Any = None) -> Any:
            """Answer the columns query with that one column.

            Parameters:
                cmd: The query, unused.
                func_name: Unused.
                param_list: Unused.

            Returns:
                One ``INFORMATION_SCHEMA.COLUMNS`` row.
            """
            return [('c', None, 'YES', data_type, char_len, data_type, charset)]

    db = _ColumnsDB()
    db._table_info_cache = {}
    info = db.table_info('obs_general')[0]
    assert {k: v for k, v in info.items() if k in ('field_type', 'field_charset')} == column


# ---------------------------------------------------------------------------
# Several import processes: isolation, transactions, retries, locks and counters
# ---------------------------------------------------------------------------


class _ScriptedCursor:
    """A cursor that records each statement and answers from its connection's script."""

    def __init__(self, conn: _ScriptedConnection) -> None:
        self._conn = conn
        self.rowcount = conn.rowcount

    def __enter__(self) -> _ScriptedCursor:
        return self

    def __exit__(self, *exc: object) -> None:
        return None

    def execute(self, cmd: str, param_list: Any = None) -> None:
        self._conn.executed.append((cmd, param_list))

    def fetchall(self) -> list[tuple[Any, ...]]:
        cmd = self._conn.executed[-1][0]
        for prefix, rows in self._conn.answers.items():
            if cmd.startswith(prefix):
                return rows
        return []


class _ScriptedConnection:
    """A connection recording statements, commits and rollbacks, answering by prefix."""

    def __init__(self, answers: dict[str, list[tuple[Any, ...]]] | None = None) -> None:
        self.answers = answers or {}
        self.rowcount = 1
        self.executed: list[tuple[str, Any]] = []
        self.commits = 0
        self.rollbacks = 0

    def cursor(self) -> _ScriptedCursor:
        return _ScriptedCursor(self)

    def commit(self) -> None:
        self.commits += 1

    def rollback(self) -> None:
        self.rollbacks += 1

    @staticmethod
    def fileno() -> None:
        """Hold no socket, so a pool worker forked later in this process closes nothing."""
        return None


class _ConnectedDB(ImportDBMySQL):
    """An ImportDBMySQL over a scripted connection, running statements through it."""

    def __init__(self, conn: _ScriptedConnection) -> None:
        ImportDBSuper.__init__(self, 'host', 'db', 'schema', 'user', 'password', logger=None)
        self.conn = conn


class _Logger:
    """A logger keeping every message by level."""

    def __init__(self) -> None:
        self.messages: list[tuple[str, str]] = []

    def log(self, level: str, message: str) -> None:
        self.messages.append((level, message))


def test_a_connection_reads_at_read_committed(monkeypatch: pytest.MonkeyPatch) -> None:
    """Every import connection, siblings included, sets the session's isolation level."""
    conn = _ScriptedConnection({'SELECT VERSION()': [('8.0.36',)], 'SELECT @@GLOBAL': [(1, 0)]})
    monkeypatch.setattr(MySQLdb, 'connect', lambda **kwargs: conn)

    ImportDBMySQL('host', 'db', 'schema', 'user', 'password')

    statements = [cmd for cmd, _ in conn.executed]
    assert 'SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED' in statements


def test_a_transaction_commits_once_at_its_end_and_rolls_back_on_failure() -> None:
    """Statements inside it do not commit themselves; a failure rolls the whole back."""
    conn = _ScriptedConnection()
    db = _ConnectedDB(conn)

    with db.transaction():
        db.read_rows('t', ['a'])
        db.delete_rows('t', '`a`=%s', [1])
        assert conn.commits == 0
    assert conn.commits == 1

    def fail_inside() -> None:
        with db.transaction():
            db.read_rows('t', ['a'])
            raise ImportDBError('stop')

    with pytest.raises(ImportDBError):
        fail_inside()
    assert (conn.commits, conn.rollbacks) == (1, 1)


@pytest.mark.parametrize(
    ('code', 'retryable', 'duplicate'),
    [(1213, True, False), (1205, True, False), (1062, False, True), (1146, False, False)],
    ids=['deadlock', 'lock-wait-timeout', 'duplicate-key', 'other'],
)
def test_the_driver_codes_the_import_reads(code: int, retryable: bool, duplicate: bool) -> None:
    """Deadlocks and lock wait timeouts are retried; a duplicate key is told apart."""
    db = _RecordingDB()
    wrapped = ImportDBError('wrapped')
    wrapped.__cause__ = MySQLdb.OperationalError(code, 'message')
    assert db.is_retryable_error(wrapped) is retryable
    assert db.is_duplicate_key_error(wrapped) is duplicate
    assert db.is_retryable_error(MySQLdb.OperationalError(code, 'message')) is retryable


def _failing(codes: list[int]) -> Any:
    """Return a body that fails with each code in turn, then returns 'done'."""

    def body() -> str:
        if codes:
            raise ImportDBError('failed') from MySQLdb.OperationalError(codes.pop(0), 'x')
        return 'done'

    return body


def test_a_lock_conflict_is_retried_after_growing_sleeps(monkeypatch: pytest.MonkeyPatch) -> None:
    """Each failed attempt is rolled back, and the next runs after the next sleep."""
    sleeps: list[float] = []
    monkeypatch.setattr('opus_import.importdb.super.time.sleep', sleeps.append)
    conn = _ScriptedConnection()
    db = _ConnectedDB(conn)
    db.logger = _Logger()

    assert db.retrying('Claiming', _failing([1213, 1205])) == 'done'

    assert sleeps == [0.5, 1.0]
    assert (conn.rollbacks, conn.commits) == (2, 1)
    assert [level for level, _ in db.logger.messages] == ['debug', 'debug']


def test_the_fifth_failure_is_raised_with_the_statement(monkeypatch: pytest.MonkeyPatch) -> None:
    """Five attempts in all; the last failure is fatal, naming the statement and error."""
    sleeps: list[float] = []
    monkeypatch.setattr('opus_import.importdb.super.time.sleep', sleeps.append)
    db = _ConnectedDB(_ScriptedConnection())
    db.logger = _Logger()

    def body() -> None:
        db.delete_rows('t', '`a`=%s', [1])
        raise ImportDBError('deadlock') from MySQLdb.OperationalError(1213, 'Deadlock found')

    with pytest.raises(ImportDBError):
        db.retrying('Deleting bundle "B_1"', body)

    assert sleeps == [0.5, 1.0, 2.0, 4.0]
    (fatal,) = [message for level, message in db.logger.messages if level == 'fatal']
    assert fatal.startswith('Deleting bundle "B_1" failed on attempt 5 of 5')
    assert 'DELETE FROM `t` WHERE `a`=%s' in fatal


def test_any_other_failure_is_not_retried(monkeypatch: pytest.MonkeyPatch) -> None:
    """A failure that a second attempt would meet again is raised at once."""
    monkeypatch.setattr('opus_import.importdb.super.time.sleep', pytest.fail)
    db = _ConnectedDB(_ScriptedConnection())

    with pytest.raises(ImportDBError):
        db.retrying('Claiming', _failing([1146]))


def test_a_counter_is_counted_on_and_read_back_by_this_connection() -> None:
    """One locking statement and LAST_INSERT_ID(), with no MAX read."""
    conn = _ScriptedConnection({'SELECT LAST_INSERT_ID()': [(7,)]})
    db = _ConnectedDB(conn)

    assert db.increment_counter('mult_field', 'last_id', 'field_id', 3) == 7

    assert conn.executed == [
        (
            'UPDATE `mult_field` SET `last_id` = LAST_INSERT_ID(`last_id` + 1) '
            'WHERE `field_id` = %s',
            [3],
        ),
        ('SELECT LAST_INSERT_ID()', None),
    ]
    assert conn.commits == 1


def test_a_counter_row_that_is_absent_is_an_error() -> None:
    """A field with no ``mult_field`` row is not silently given id 0."""
    conn = _ScriptedConnection()
    conn.rowcount = 0

    with pytest.raises(ImportDBError, match='no row'):
        _ConnectedDB(conn).increment_counter('mult_field', 'last_id', 'field_id', 3)


def test_a_read_only_counter_counts_on_from_the_stored_value_without_an_update() -> None:
    """The UPDATE is logged as simulated, never sent; the stored value is read once and
    each later count goes on from the last."""
    conn = _ScriptedConnection({'SELECT `last_id`': [(4,)]})
    db = _ConnectedDB(conn)
    db.read_only = True
    db.log_sql = True
    db.logger = _Logger()

    counted = [db.increment_counter('mult_field', 'last_id', 'field_id', 3) for _ in range(2)]

    assert counted == [5, 6]
    assert conn.executed == [('SELECT `last_id` FROM `mult_field` WHERE `field_id`=%s', [3])]
    simulated = [message for _level, message in db.logger.messages if '[SIM]' in message]
    assert len(simulated) == 2
    assert 'UPDATE `mult_field` SET `last_id`' in simulated[0]


def test_a_read_only_counter_row_that_is_absent_is_an_error() -> None:
    """A field with no ``mult_field`` row is refused in a read-only run too."""
    db = _ConnectedDB(_ScriptedConnection())
    db.read_only = True

    with pytest.raises(ImportDBError, match='no row whose field_id is 3'):
        db.increment_counter('mult_field', 'last_id', 'field_id', 3)


def test_the_claim_reads_one_row_skipping_locked_ones() -> None:
    """Both order terms descend, so the key serves the order and nothing is sorted."""
    conn = _ScriptedConnection({'SELECT `bundle_number`': [(4,)]})
    db = _ConnectedDB(conn)

    found = db.lock_first_row(
        'import_bundle',
        'bundle_number',
        '`state` = %s',
        ['pending'],
        ['size_estimate', 'bundle_number'],
    )

    assert found == 4
    assert conn.executed == [
        (
            'SELECT `bundle_number` FROM `import_bundle` WHERE `state` = %s ORDER BY '
            '`size_estimate` DESC, `bundle_number` DESC LIMIT 1 FOR UPDATE SKIP LOCKED',
            ['pending'],
        )
    ]


def test_an_insert_keeping_existing_rows_is_a_no_op_update_not_an_ignore(
    db: _RecordingDB,
) -> None:
    """A stored row is left alone, and a data error still fails."""
    db.insert_rows_keeping_existing(
        'mult_group', 'field_id', [{'field_id': 2, 'grouping': 'G', 'group_pin': 1}]
    )
    ((cmd, params),) = db.executed
    assert cmd == (
        'INSERT INTO `mult_group` (`field_id`,`group_pin`,`grouping`) VALUES (%s,%s,%s) '
        'ON DUPLICATE KEY UPDATE `field_id` = `field_id`'
    )
    assert 'IGNORE' not in cmd
    assert params == [2, 1, 'G']


def test_a_named_lock_is_taken_waiting_and_released_however_the_body_ends() -> None:
    """GET_LOCK waits without limit; RELEASE_LOCK follows even a failed body."""
    conn = _ScriptedConnection({'SELECT GET_LOCK': [(1,)], 'SELECT RELEASE_LOCK': [(1,)]})
    db = _ConnectedDB(conn)

    with pytest.raises(RuntimeError), db.named_lock('opus:abc'):
        raise RuntimeError('inside')

    assert conn.executed == [
        ('SELECT GET_LOCK(%s, -1)', ['opus:abc']),
        ('SELECT RELEASE_LOCK(%s)', ['opus:abc']),
    ]


def test_a_named_lock_not_granted_is_an_error() -> None:
    """The body never runs without the lock."""
    conn = _ScriptedConnection({'SELECT GET_LOCK': [(None,)]})

    lock = _ConnectedDB(conn).named_lock('opus:abc')

    with pytest.raises(ImportDBError, match='did not grant'):
        lock.__enter__()


def test_a_conditional_update_counts_the_rows_it_changed() -> None:
    """The condition is the WHERE clause; 0 rows changed means it did not hold."""
    conn = _ScriptedConnection()
    conn.rowcount = 0
    db = _ConnectedDB(conn)

    changed = db.conditional_update(
        'import_bundle', {'state': 'done'}, '`bundle_id`=%s AND `state` IN (%s)', ['B', 'importing']
    )

    assert changed == 0
    assert conn.executed == [
        (
            'UPDATE `import_bundle` SET `state`=%s WHERE `bundle_id`=%s AND `state` IN (%s)',
            ['done', 'B', 'importing'],
        )
    ]
    assert conn.commits == 1


def test_an_expected_failure_is_neither_retried_nor_logged(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A duplicate key the caller reads back is raised at once, with no fatal line."""
    monkeypatch.setattr('opus_import.importdb.super.time.sleep', pytest.fail)
    db = _ConnectedDB(_ScriptedConnection())
    db.logger = _Logger()

    with pytest.raises(ImportDBError):
        db.retrying('Inserting', _failing([1062]), expected=db.is_duplicate_key_error)

    assert db.logger.messages == []


class _DyingConnection(_ScriptedConnection):
    """A connection whose every statement after GET_LOCK fails, as a broken one does."""

    def cursor(self) -> _ScriptedCursor:
        if self.executed and self.executed[-1][0].startswith('SELECT GET_LOCK'):
            raise MySQLdb.OperationalError(2013, 'Lost connection to MySQL server')
        return _ScriptedCursor(self)


def test_a_failed_release_does_not_replace_the_bodys_failure() -> None:
    """The body's own exception reaches the caller when the release fails too."""
    db = _ConnectedDB(_DyingConnection({'SELECT GET_LOCK': [(1,)]}))

    def body() -> None:
        with db.named_lock('opus:abc'):
            raise RuntimeError('the body failed')

    with pytest.raises(RuntimeError, match='the body failed'):
        body()


# ---------------------------------------------------------------------------
# Importers: the startup on the lock connection, and each chunk's guard
# ---------------------------------------------------------------------------


class _CommitRecordingConnection(_ScriptedConnection):
    """A scripted connection that records each commit and rollback among the statements,
    and reports a matched row after each UPDATE."""

    def __init__(
        self, answers: dict[str, list[tuple[Any, ...]]] | None = None, matched: int = 1
    ) -> None:
        super().__init__(answers)
        self.matched = matched

    def commit(self) -> None:
        super().commit()
        self.executed.append(('COMMIT', None))

    def rollback(self) -> None:
        super().rollback()
        self.executed.append(('ROLLBACK', None))

    def info(self) -> str:
        return f'Rows matched: {self.matched}  Changed: {self.matched}  Warnings: 0'


def test_an_importers_startup_commits_its_row_only_once_it_holds_its_lock() -> None:
    """SET SESSION wait_timeout, the insert, LAST_INSERT_ID(), GET_LOCK, then COMMIT."""
    conn = _CommitRecordingConnection(
        {'SELECT LAST_INSERT_ID()': [(7,)], 'SELECT GET_LOCK': [(1,)]}
    )
    db = _ConnectedDB(conn)

    importer = import_processes.start_importer(db, '/logs/opus_import.log')

    statements = [cmd.split(' (')[0] for cmd, _ in conn.executed]
    assert statements == [
        'SET SESSION wait_timeout = %s',
        'INSERT INTO `import_process`',
        'SELECT LAST_INSERT_ID()',
        'SELECT GET_LOCK(%s, 0)',
        'COMMIT',
    ]
    assert conn.executed[0][1] == [31_536_000]
    assert conn.executed[3][1] == [import_processes.importer_lock_name('schema', 7)]
    assert (importer.process_id, importer.name) == (7, conn.executed[3][1][0])


def test_an_importer_refused_its_lock_commits_nothing() -> None:
    """Another connection holding the lock rolls the row back."""
    conn = _CommitRecordingConnection(
        {'SELECT LAST_INSERT_ID()': [(7,)], 'SELECT GET_LOCK': [(0,)]}
    )

    with pytest.raises(ImportDBError, match='did not grant'):
        import_processes.start_importer(_ConnectedDB(conn), 'log')

    assert conn.commits == 0
    assert conn.executed[-1] == ('ROLLBACK', None)


def _guarded(
    matched: int = 1, holds: int = 1, importer: bool = True
) -> tuple[_ConnectedDB, _CommitRecordingConnection, import_processes.BundleGuard]:
    """Return a connection writing by INSERT statements, its scripted connection, and a
    guard for bundle 3 under importer 9 (or no importer)."""
    conn = _CommitRecordingConnection(matched=matched)
    db = _ConnectedDB(conn)
    db.bulk_load_path = BULK_LOAD_PATH_INSERT
    db.transaction_rows = 2
    lock_conn = _ScriptedConnection({'SELECT IS_USED_LOCK': [(holds,)]})
    lock = import_processes.ImporterLock(_ConnectedDB(lock_conn), 9, 'opus:lock')
    ids = bundle_registry.BundleIds(bundle_registry.BundleRange(3, 'B_3', 10, 0, 1000, 'importing'))
    return db, conn, import_processes.BundleGuard(ids, lock if importer else None)


def test_each_guarded_chunk_records_its_progress_first_and_commits_last() -> None:
    """Two chunks of obs_general, each one transaction: the registry, the progress, the
    rows, then the commit; rows_done counts every committed row."""
    db, conn, guard = _guarded()

    db.bulk_load_rows('obs_general', [{'id': 1}, {'id': 2}, {'id': 3}], guard=guard)

    shapes = [cmd.split(' SET ')[0].split(' (')[0] for cmd, _ in conn.executed]
    chunk = ['UPDATE `import_bundle`', 'UPDATE `import_process`', 'INSERT INTO `obs_general`']
    assert shapes == [*chunk, 'COMMIT', *chunk, 'COMMIT']
    first_update, params = conn.executed[0]
    assert first_update == (
        'UPDATE `import_bundle` SET `rows_done`=%s WHERE `bundle_number`=%s AND `state`=%s '
        'AND `process_id`=%s'
    )
    assert params == [2, 3, 'importing', 9]
    assert conn.executed[4][1][0] == 3
    assert guard.ids.rows_done == 3


@pytest.mark.parametrize(('matched', 'holds'), [(0, 1), (1, 0)], ids=['bundle-lost', 'lock-lost'])
def test_a_chunk_whose_importer_lost_its_bundle_or_its_lock_rolls_back(
    matched: int, holds: int
) -> None:
    """Nothing commits, the count stays, and the importer hears it has lost."""
    db, conn, guard = _guarded(matched=matched, holds=holds)

    with pytest.raises(import_processes.LostImporterError, match='opus:lock'):
        db.bulk_load_rows('obs_general', [{'id': 1}], guard=guard)

    assert conn.commits == 0
    assert conn.executed[-1] == ('ROLLBACK', None)
    assert guard.ids.rows_done == 0


def test_a_plain_imports_guard_counts_observations_and_checks_nothing() -> None:
    """Only an obs_general chunk carries the count, matching the bundle's hold, its
    ``started_at``; another table's chunk carries nothing."""
    db, conn, guard = _guarded(holds=0, importer=False)

    db.bulk_load_rows('obs_general', [{'id': 1}], guard=guard)
    db.bulk_load_rows('obs_files', [{'obs_general_id': 1}], guard=guard)

    assert [cmd.split(' (')[0] for cmd, _ in conn.executed] == [
        'UPDATE `import_bundle` SET `rows_done`=%s WHERE `bundle_number`=%s AND `started_at`=%s',
        'INSERT INTO `obs_general`',
        'COMMIT',
        'INSERT INTO `obs_files`',
        'COMMIT',
    ]


def test_an_update_reports_the_rows_it_matched_changed_or_not() -> None:
    """Read from the server's report before the commit replaces it."""
    conn = _CommitRecordingConnection(matched=0)
    assert _ConnectedDB(conn).update_row('t', {'a': 1}, '`b`=%s', [2]) == 0
    conn.matched = 1
    assert _ConnectedDB(conn).update_row('t', {'a': 1}, '`b`=%s', [2]) == 1


def test_a_row_is_locked_passing_over_one_another_session_holds() -> None:
    """FOR UPDATE SKIP LOCKED, the columns asked for, and None for no row."""
    conn = _ScriptedConnection({'SELECT `state`': [('importing', 4)]})
    db = _ConnectedDB(conn)
    assert db.lock_row('import_bundle', ['state', 'process_id'], '`bundle_number`=%s', [3]) == (
        'importing',
        4,
    )
    assert conn.executed == [
        (
            'SELECT `state`,`process_id` FROM `import_bundle` WHERE `bundle_number`=%s '
            'FOR UPDATE SKIP LOCKED',
            [3],
        )
    ]
    assert _ConnectedDB(_ScriptedConnection()).lock_row('t', ['a'], '1=1', []) is None


def test_the_lock_queries_ask_who_holds_a_lock() -> None:
    """Whether this connection holds it, and which connection does."""
    conn = _ScriptedConnection(
        {'SELECT IS_USED_LOCK(%s) = CONNECTION_ID()': [(1,)], 'SELECT IS_USED_LOCK(%s)': [(42,)]}
    )
    db = _ConnectedDB(conn)
    assert db.holds_named_lock('opus:x') is True
    assert db.named_lock_holder('opus:x') == 42
    assert _ConnectedDB(_ScriptedConnection({'SELECT': [(None,)]})).named_lock_holder('x') is None


class _RollbackFailingConnection(_ScriptedConnection):
    """A connection whose rollback fails, as a broken one's does."""

    def rollback(self) -> None:
        raise MySQLdb.OperationalError(2013, 'Lost connection to MySQL server')


@pytest.mark.parametrize(
    ('code', 'wrapped'),
    [(1213, True), (1062, True), (1213, False)],
    ids=['retryable', 'expected', 'driver-error-retryable'],
)
def test_a_failed_rollback_is_fatal_naming_both_failures(
    code: int, wrapped: bool, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Neither retried nor passed to the caller as expected: the transaction's failure is
    the one raised from, and the fatal line names it beside the rollback's."""
    monkeypatch.setattr('opus_import.importdb.super.time.sleep', pytest.fail)
    db = _ConnectedDB(_RollbackFailingConnection())
    db.logger = _Logger()
    driver_error = MySQLdb.OperationalError(code, 'the body failed')
    failure: Exception = ImportDBError('the body failed') if wrapped else driver_error
    if wrapped:
        failure.__cause__ = driver_error

    def body() -> None:
        raise failure

    with pytest.raises(RollbackError, match='Lost connection to MySQL server') as excinfo:
        db.retrying('Claiming', body, expected=db.is_duplicate_key_error)

    assert excinfo.value.__cause__ is failure
    (fatal,) = [message for level, message in db.logger.messages if level == 'fatal']
    assert fatal.startswith('Claiming failed on attempt 1 of 5')
    assert 'the body failed' in fatal


@pytest.mark.parametrize('source', ['schema', 'SCHEMA'], ids=['same-case', 'other-case'])
def test_the_carry_over_refuses_its_own_schema_before_any_statement(source: str) -> None:
    """Emptying the target first would empty the source, so nothing runs; a server with
    ``lower_case_table_names`` set treats names differing in case as one."""
    conn = _ScriptedConnection()
    db = _ConnectedDB(conn)
    db.logger = _Logger()
    with pytest.raises(ImportDBError, match='is the schema it would write into'):
        db.carry_over_sessions(source)
    assert conn.executed == []
    assert db.logger.messages == [
        (
            'fatal',
            f'Failed to carry sessions and carts over from `{source}`: '
            f'`{source}` is the schema it would write into',
        )
    ]


def test_the_carry_over_refuses_to_run_without_the_driver(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Without MySQLdb nothing could be copied, so it fails rather than reporting no rows."""
    monkeypatch.setattr('opus_import.importdb.mysql.MYSQLDB_AVAILABLE', False)
    db = _ConnectedDB(_ScriptedConnection())
    db.logger = _Logger()
    with pytest.raises(ImportDBError, match='the MySQLdb driver is not installed'):
        db.carry_over_sessions('opus_served')
    assert db.logger.messages == [
        (
            'fatal',
            'Failed to carry sessions and carts over from `opus_served`: '
            'the MySQLdb driver is not installed',
        )
    ]
