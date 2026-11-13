"""The two write paths' machinery, without a server.

The keys a table is created with, the statements that add the rest, the concurrent index
build, the choice of path, the chunked per-bundle delete, the duplicate step and
validation's orphan count are each driven here against a backend that records statements
or a stand-in that answers the few queries a step makes. The import suite runs the same
code against a server.
"""

from __future__ import annotations

import threading
import time
from types import SimpleNamespace
from typing import Any

import pytest

from opus_import import cli, import_util
from opus_import.importdb.super import ImportDBError, ImportDBSuper, IndexStatement
from opus_import.schema_version import SCHEMA_VERSION
from opus_import.steps import (
    do_duplicate_ids,
    do_import,
    do_import_tables,
    do_indexes,
    do_validate,
)
from opus_import.table_keys import (
    TableKey,
    add_secondary_indexes,
    create_time_keys,
    declared_keys,
)

from .conftest import default_arguments, make_context

MySQLdb = pytest.importorskip('MySQLdb')

from opus_import.importdb.mysql import ImportDBMySQL  # noqa: E402 - follows the skip

#: A child table's schema, cut down to the keys.
_CHILD_SCHEMA: list[dict[str, Any]] = [
    {'field_name': 'obs_general_id', 'field_type': 'uint4', 'field_key': 'primary'},
    {'foreign_key': {'columns': ['obs_general_id'], 'references': ['obs_general', 'id']}},
    {'field_name': 'opus_id', 'field_type': 'char50', 'field_key': True},
    {'field_name': 'bundle_id', 'field_type': 'char75', 'field_key': True},
    {'field_name': 'time1', 'field_type': 'real8', 'field_key': True},
]


class _RecordingDB(ImportDBMySQL):
    """An ImportDBMySQL that records statements, over a schema holding `tables`."""

    def __init__(self, tables: set[str]) -> None:
        """Start with a schema holding `tables` and nothing executed.

        Deliberately skips ImportDBMySQL.__init__, which connects to a server.

        Parameters:
            tables: The table names the schema holds, as the server spells them.
        """
        ImportDBSuper.__init__(self, 'host', 'db', 'schema', 'user', 'password')
        self._table_names = set(tables)
        self._table_info_cache = {}
        self._ddl_buffer_bounds = None
        self._ddl_buffer_size = None
        self.default_engine = 'INNODB'
        self.executed: list[tuple[str, Any]] = []
        self.answers: dict[str, list[tuple[Any, ...]]] = {}

    def _execute(
        self, cmd: str, param_list: Any = None, cur: Any = None, mutates: bool = False
    ) -> None:
        """Record a statement instead of running it.

        Parameters:
            cmd: The statement.
            param_list: Its parameters.
            cur: Unused.
            mutates: Unused.
        """
        self.executed.append((' '.join(cmd.split()), param_list))

    def _execute_and_fetchall(
        self, cmd: str, func_name: str, param_list: Any = None
    ) -> list[tuple[Any, ...]]:
        """Answer a query from `answers`, by the first answer key its text contains.

        Parameters:
            cmd: The query.
            func_name: Unused.
            param_list: Unused.

        Returns:
            The rows of the first matching answer.
        """
        for marker, rows in self.answers.items():
            if marker in cmd:
                return rows
        raise AssertionError(f'no answer for {cmd!r}')


# ------------------------------------------------------------------------------------
# The keys a table is created with, and the statements that add the rest
# ------------------------------------------------------------------------------------


def _create_statement(db: _RecordingDB, table: str) -> str:
    """Create `table` from the child schema and return the statement sent."""
    db.create_table(table, _CHILD_SCHEMA)
    (cmd,) = [cmd for cmd, _ in db.executed if cmd.startswith('CREATE TABLE')]
    return cmd


def test_a_child_is_created_with_only_the_keys_a_load_needs() -> None:
    """The primary key alone: no plain key, not even ``bundle_id``'s, and no foreign key."""
    db = _RecordingDB(set())
    cmd = _create_statement(db, 'obs_pds')
    assert cmd.startswith('CREATE TABLE IF NOT EXISTS `obs_pds`')
    assert 'PRIMARY KEY (`obs_general_id`)' in cmd
    assert '`bundle_id` (`bundle_id`)' not in cmd
    assert 'FOREIGN KEY' not in cmd
    assert '`time1` (`time1`)' not in cmd
    assert '`opus_id` (`opus_id`)' not in cmd


def test_the_surface_geometry_table_is_created_with_the_key_the_delete_reads() -> None:
    """Its primary key starts with the body, so it keeps a key on ``obs_general_id``."""
    db = _RecordingDB(set())
    schema = import_util.read_schema_for_table(make_context(), 'obs_surface_geometry_target')
    assert schema is not None
    db.create_table('obs_surface_geometry_target', schema)
    (cmd,) = [cmd for cmd, _ in db.executed if cmd.startswith('CREATE TABLE')]
    assert 'PRIMARY KEY (`target_name`, `obs_general_id`)' in cmd
    assert 'KEY `obs_general_id` (`obs_general_id`)' in cmd
    assert 'bundle_id' not in cmd
    assert 'FOREIGN KEY' not in cmd
    assert '`center_distance1`' not in cmd.split('PRIMARY KEY')[1]


def test_a_table_outside_the_filter_is_created_with_every_declared_key() -> None:
    """Only observation and mult tables leave keys for finalization."""
    db = _RecordingDB(set())
    cmd = _create_statement(db, 'cart')
    for clause in (
        'FOREIGN KEY (`obs_general_id`) REFERENCES `obs_general`(`id`) '
        'ON DELETE RESTRICT ON UPDATE CASCADE',
        'KEY `opus_id` (`opus_id`)',
        'KEY `bundle_id` (`bundle_id`)',
        'KEY `time1` (`time1`)',
        'PRIMARY KEY (`obs_general_id`)',
    ):
        assert clause in cmd


def test_a_table_level_foreign_key_renders_what_a_delete_does() -> None:
    """The entry is no column, and its ``on_delete`` reaches the clause."""
    db = _RecordingDB(set())
    schema: list[dict[str, Any]] = [
        {'field_name': 'obs_general_id', 'field_type': 'uint4', 'field_notnull': True},
        {
            'foreign_key': {
                'columns': ['obs_general_id'],
                'references': ['obs_general', 'id'],
                'on_delete': 'cascade',
            }
        },
        {'constraint': 'CONSTRAINT one UNIQUE (obs_general_id)'},
    ]
    db.create_table('cart', schema)
    (cmd,) = [cmd for cmd, _ in db.executed if cmd.startswith('CREATE TABLE')]
    assert cmd == (
        'CREATE TABLE IF NOT EXISTS `cart` ( `obs_general_id` int unsigned NOT NULL, '
        'CONSTRAINT one UNIQUE (obs_general_id) , FOREIGN KEY (`obs_general_id`) '
        'REFERENCES `obs_general`(`id`) ON DELETE CASCADE ON UPDATE CASCADE ) ENGINE=INNODB'
    )


def test_the_packaged_cart_cascades_to_its_rows() -> None:
    """Deleting an observation removes the cart rows that name it."""
    schema = import_util.read_schema_for_table(make_context(), 'cart')
    assert schema is not None
    (foreign,) = [key for key in declared_keys(schema) if key.kind == 'foreign']
    assert foreign == TableKey('foreign', ('obs_general_id',), ('obs_general', ('id',)), 'cascade')


def test_the_statements_that_add_keys() -> None:
    """Plain keys are added unnamed in one statement; a foreign key as create_table renders it."""
    db = _RecordingDB(set())
    keys = [TableKey('key', ('time1',)), TableKey('key', ('time1', 'time2'))]
    assert db.add_keys_statement('obs_pds', keys) == (
        'ALTER TABLE `obs_pds` ADD KEY (`time1`), ADD KEY (`time1`, `time2`)'
    )
    foreign = TableKey('foreign', ('obs_general_id',), ('obs_general', ('id',)))
    assert db.add_foreign_key_statement('obs_pds', foreign) == (
        'ALTER TABLE `obs_pds` ADD FOREIGN KEY (`obs_general_id`) REFERENCES '
        '`obs_general`(`id`) ON DELETE RESTRICT ON UPDATE CASCADE'
    )


def test_the_server_keys_are_read_by_kind_and_columns() -> None:
    """``STATISTICS`` gives the indexes, column by column; the constraints give foreign keys."""
    db = _RecordingDB(set())
    db.answers = {
        'STATISTICS': [
            ('obs_pds', 'PRIMARY', 0, 'id', 'BTREE'),
            ('obs_pds', 'time1_2', 1, 'time1', 'BTREE'),
            ('obs_pds', 'time1_2', 1, 'time2', 'BTREE'),
            ('obs_pds', 'note', 1, 'note', 'FULLTEXT'),
            ('obs_pds', 'u', 0, 'opus_id', 'BTREE'),
            ('cart', 'PRIMARY', 0, 'id', 'BTREE'),
        ],
        'KEY_COLUMN_USAGE': [
            ('obs_pds', 'obs_pds_ibfk_1', 'obs_general_id', 'obs_general', 'id', 'RESTRICT'),
            ('cart', 'cart_ibfk_1', 'obs_general_id', 'obs_general', 'id', 'CASCADE'),
        ],
    }
    assert db.read_table_keys() == {
        'obs_pds': [
            TableKey('primary', ('id',)),
            TableKey('key', ('time1', 'time2')),
            TableKey('unique', ('opus_id',)),
            TableKey('foreign', ('obs_general_id',), ('obs_general', ('id',))),
        ],
        'cart': [
            TableKey('primary', ('id',)),
            TableKey('foreign', ('obs_general_id',), ('obs_general', ('id',)), 'cascade'),
        ],
    }


def test_the_space_estimate() -> None:
    """``rows x (key bytes + primary key bytes + 10) x 1.3``, from the server's row count."""
    db = _RecordingDB(set())
    db.answers = {'TABLE_ROWS': [(1000,)]}
    space = db.key_space_bytes('obs_pds', _CHILD_SCHEMA, TableKey('key', ('time1',)))
    assert space == int(1000 * (8 + 4 + 10) * 1.3)
    space = db.key_space_bytes('obs_pds', _CHILD_SCHEMA, TableKey('key', ('opus_id',)))
    assert space == int(1000 * (4 * 50 + 4 + 10) * 1.3)


def test_the_space_budget_is_the_free_space_of_a_local_servers_directory(tmp_path: Any) -> None:
    """A server on this computer: the directory's free space, the data directory's if less."""
    db = _RecordingDB(set())
    db.db_hostname = 'localhost'
    db.answers = {'datadir': [(str(tmp_path),)]}
    budget = db.index_space_budget(str(tmp_path))
    assert budget is not None
    assert budget > 0


def test_there_is_no_space_budget_for_a_remote_server_or_no_directory(tmp_path: Any) -> None:
    """A path read here names this computer's directory, not a remote server's."""
    db = _RecordingDB(set())
    db.db_hostname = 'db.example.org'
    assert db.index_space_budget(str(tmp_path)) is None
    db.db_hostname = 'localhost'
    assert db.index_space_budget(None) is None
    assert db.index_space_budget(str(tmp_path / 'absent')) is None


def test_a_failed_key_build_is_a_failed_step() -> None:
    """A statement the server refuses makes the step return False rather than raise."""
    db = _IndexingDB({'obs_pds': []})

    def refuse(*args: Any, **kwargs: Any) -> Any:
        raise ImportDBError('refused')

    db.build_indexes = refuse  # type: ignore[method-assign]
    ctx = make_context(db=db)
    assert not do_indexes.create_indexes(ctx)
    assert ctx.import_has_bad_data


def test_foreign_keys_are_added_with_the_checks_off_and_turned_back_on() -> None:
    """``foreign_key_checks`` is 0 around the statements and 1 after, even after a failure."""
    db = _RecordingDB(set())
    statement = IndexStatement('ALTER TABLE `obs_pds` ADD FOREIGN KEY x', 'fk', 0, 0, 0)
    timed = db.add_foreign_keys([statement])
    assert [label for label, _ in timed] == ['fk']
    assert [cmd for cmd, _ in db.executed] == [
        'SET SESSION foreign_key_checks = 0',
        'ALTER TABLE `obs_pds` ADD FOREIGN KEY x',
        'SET SESSION foreign_key_checks = 1',
    ]


def test_foreign_key_checks_are_turned_back_on_after_a_refused_foreign_key() -> None:
    """A foreign key the server refuses still leaves the session's checks on."""

    class _RefusingDB(_RecordingDB):
        def _execute(
            self, cmd: str, param_list: Any = None, cur: Any = None, mutates: bool = False
        ) -> None:
            super()._execute(cmd, param_list, cur, mutates)
            if 'ADD FOREIGN KEY' in cmd:
                raise MySQLdb.Error('refused')

    db = _RefusingDB(set())
    statements = [
        IndexStatement('ALTER TABLE `obs_pds` ADD FOREIGN KEY x', 'fk', 0, 0, 0),
        IndexStatement('ALTER TABLE `obs_files` ADD FOREIGN KEY y', 'fk2', 0, 0, 0),
    ]
    with pytest.raises(ImportDBError):
        db.add_foreign_keys(statements)
    assert [cmd for cmd, _ in db.executed] == [
        'SET SESSION foreign_key_checks = 0',
        'ALTER TABLE `obs_pds` ADD FOREIGN KEY x',
        'SET SESSION foreign_key_checks = 1',
    ]


def _prepared_session(
    workers: int, ddl_buffer_size: int, ddl_threads: int = 4, pool: int = 8 * 1024**3
) -> _RecordingDB:
    """Return a session prepared on a server with the given pool, buffer and DDL threads."""
    db = _RecordingDB(set())
    db.answers = {
        'SHOW VARIABLES': [
            ('innodb_buffer_pool_size', pool),
            ('innodb_ddl_buffer_size', ddl_buffer_size),
            ('innodb_ddl_threads', ddl_threads),
        ]
    }
    db._prepare_index_session(workers, None)
    return db


def test_preparing_an_index_session_sets_only_its_temporary_directory() -> None:
    """The sort memory is left for each statement to size; the directory is set at once."""
    db = _RecordingDB(set())
    db.answers = {
        'SHOW VARIABLES': [
            ('innodb_buffer_pool_size', 8 * 1024**3),
            ('innodb_ddl_buffer_size', 1048576),
        ]
    }
    db._prepare_index_session(4, '/var/tmp/sort')
    assert db.executed == [('SET SESSION innodb_tmpdir = %s', ['/var/tmp/sort'])]


def test_an_index_sort_is_sized_to_its_estimate_within_the_bounds() -> None:
    """A small sort keeps the server's buffer, a large one gets the ceiling, one between its estimate.

    The ceiling is a quarter of the pool shared among the connections.
    """
    ceiling = 8 * 1024**3 // 4 // 4
    db = _prepared_session(4, 1048576)
    db._size_index_sort(1000, 1)
    assert db.executed == []
    db._size_index_sort(ceiling * 10, 1)
    db._size_index_sort(64 * 1024**2, 1)
    assert db.executed == [
        ('SET SESSION innodb_ddl_buffer_size = %s', [ceiling]),
        ('SET SESSION innodb_ddl_buffer_size = %s', [64 * 1024**2]),
    ]


def test_an_index_sort_already_sized_is_not_set_again() -> None:
    """Two statements of the same size change the session once."""
    db = _prepared_session(1, 1048576)
    db._size_index_sort(64 * 1024**2, 1)
    db._size_index_sort(64 * 1024**2, 1)
    assert len(db.executed) == 1


def test_a_server_buffer_above_the_ceiling_is_held_to_it() -> None:
    """The ceiling bounds even the server's own setting."""
    ceiling = 8 * 1024**3 // 4 // 22
    db = _prepared_session(22, 4 * 1024**3)
    db._size_index_sort(1000, 1)
    assert db.executed == [('SET SESSION innodb_ddl_buffer_size = %s', [ceiling])]


@pytest.mark.parametrize(('key_count', 'sharing'), [(2, 2), (4, 4), (8, 4)])
def test_the_ceiling_is_shared_among_the_indexes_built_at_once(
    key_count: int, sharing: int
) -> None:
    """Each index a statement builds at once, up to ``innodb_ddl_threads``, holds a buffer."""
    db = _prepared_session(1, 1048576, ddl_threads=4)
    db._size_index_sort(8 * 1024**3, key_count)
    assert db.executed == [
        ('SET SESSION innodb_ddl_buffer_size = %s', [8 * 1024**3 // 4 // sharing])
    ]


def test_the_ceiling_keeps_within_the_values_the_server_accepts() -> None:
    """A large pool's share is held to the largest buffer, a tiny one's raised to the smallest."""
    db = _prepared_session(1, 65536, ddl_threads=1, pool=64 * 1024**3)
    db._size_index_sort(64 * 1024**3, 1)
    assert db.executed == [('SET SESSION innodb_ddl_buffer_size = %s', [4_294_967_295])]
    db = _prepared_session(64, 1048576, pool=16 * 1024**2)
    db._size_index_sort(1024**3, 8)
    assert db.executed == [('SET SESSION innodb_ddl_buffer_size = %s', [65536])]


def test_an_index_session_on_a_server_without_the_buffer_setting_sets_nothing() -> None:
    """A server before 8.0.27 has no ``innodb_ddl_buffer_size``, and no temporary directory is asked for."""
    db = _RecordingDB(set())
    db.answers = {'SHOW VARIABLES': [('innodb_buffer_pool_size', 8 * 1024**3)]}
    db._prepare_index_session(1, None)
    db._size_index_sort(64 * 1024**2, 1)
    assert db.executed == []


# ------------------------------------------------------------------------------------
# build_indexes
# ------------------------------------------------------------------------------------


class _BuildingDB(ImportDBSuper):
    """A backend whose DDL takes a little while, recording which connection ran what."""

    def __init__(self, failing: str | None = None, parent: _BuildingDB | None = None) -> None:
        """Start a connection with nothing run.

        Parameters:
            failing: A statement that fails.
            parent: The connection this one is a sibling of, which keeps the shared
                record; None for the first.
        """
        super().__init__('host', 'db', 'schema', 'user', 'password')
        self.root: _BuildingDB = self if parent is None else parent.root
        self.failing = failing
        self.sort_size: tuple[int, int] | None = None
        if parent is None:
            self.lock = threading.Lock()
            self.ran: list[tuple[int, str]] = []
            self.running = 0
            self.most_running = 0
            self.prepared: list[tuple[int, str | None]] = []
            self.sized: dict[str, tuple[int, int] | None] = {}
            self.closed = 0
            self.siblings = 0

    def open_sibling_connection(self) -> ImportDBSuper:
        """Return a sibling sharing the record."""
        with self.root.lock:
            self.root.siblings += 1
        return _BuildingDB(self.failing, parent=self)

    def _prepare_index_session(self, workers: int, server_tmpdir: str | None) -> None:
        """Record the preparation, refusing a directory named ``refused``."""
        with self.root.lock:
            self.root.prepared.append((workers, server_tmpdir))
        if server_tmpdir == 'refused':
            raise ImportDBError('refused the directory')

    def _size_index_sort(self, sort_bytes: int, key_count: int) -> None:
        """Hold the sort and key count for this connection's next statement."""
        self.sort_size = (sort_bytes, key_count)

    def run_ddl(self, cmd: str) -> None:
        """Run a statement for a few milliseconds, tracking how many run at once."""
        root = self.root
        with root.lock:
            root.running += 1
            root.most_running = max(root.most_running, root.running)
        time.sleep(0.01)
        with root.lock:
            root.running -= 1
            root.ran.append((id(self), cmd))
            root.sized[cmd] = self.sort_size
        self.sort_size = None
        if cmd == self.failing:
            raise ImportDBError(f'refused {cmd}')

    def close(self) -> None:
        """Count the close."""
        with self.root.lock:
            self.root.closed += 1


def _statements(tables: dict[str, int], space: int = 0) -> dict[str, list[IndexStatement]]:
    """Return `count` statements per table, labeled ``<table>.<n>``, each sorting ``n``.

    Statement ``n`` builds ``n + 1`` keys.
    """
    return {
        table: [
            IndexStatement(f'{table}.{n}', f'{table}.{n}', space, n, n + 1) for n in range(count)
        ]
        for table, count in tables.items()
    }


def test_tables_build_at_once_each_on_one_sibling_in_order() -> None:
    """Up to `workers` tables at once, each table's statements in order on one connection."""
    db = _BuildingDB()
    timed = db.build_indexes(_statements({'a': 3, 'b': 2, 'c': 2, 'd': 1}), workers=3)
    assert sorted(timed) == ['a', 'b', 'c', 'd']
    assert [label for label, _ in timed['a']] == ['a.0', 'a.1', 'a.2']
    assert 1 < db.most_running <= 3
    for table in 'abcd':
        connections = {conn for conn, cmd in db.ran if cmd.startswith(table)}
        assert len(connections) == 1
        assert [cmd for _, cmd in db.ran if cmd.startswith(table)] == [
            f'{table}.{n}' for n in range(len(timed[table]))
        ]
    assert db.siblings == db.closed == len(db.prepared)
    assert all(prepared == (3, None) for prepared in db.prepared)


def test_serial_builds_one_table_at_a_time_on_this_connection() -> None:
    """``serial`` uses no sibling and never runs two statements at once."""
    db = _BuildingDB()
    db.build_indexes(_statements({'a': 2, 'b': 2}), workers=4, serial=True)
    assert db.most_running == 1
    assert db.siblings == 0
    assert {conn for conn, _ in db.ran} == {id(db)}
    assert db.prepared == [(1, None)]


def test_a_sibling_whose_session_is_refused_is_closed_at_once() -> None:
    """Every sibling opened is closed, though none could be prepared."""
    db = _BuildingDB()
    with pytest.raises(ImportDBError, match='refused the directory'):
        db.build_indexes(_statements({'a': 1, 'b': 1, 'c': 1}), workers=2, server_tmpdir='refused')
    assert db.siblings >= 1
    assert db.closed == db.siblings
    assert db.ran == []


def test_a_failed_table_does_not_stop_the_others_and_is_raised_after() -> None:
    """The failure stops its own table's later statements; every other table finishes."""
    db = _BuildingDB(failing='b.0')
    with pytest.raises(ImportDBError, match=r'b: refused b\.0'):
        db.build_indexes(_statements({'a': 2, 'b': 2, 'c': 2}), workers=2)
    ran = [cmd for _, cmd in db.ran]
    assert 'b.1' not in ran
    assert {'a.0', 'a.1', 'c.0', 'c.1'} <= set(ran)
    assert db.siblings == db.closed


def test_statements_running_at_once_fit_the_space_budget_together() -> None:
    """Two statements of 60 never run together under a budget of 100."""
    db = _BuildingDB()
    db.build_indexes(_statements({'a': 2, 'b': 2, 'c': 2}, space=60), workers=3, space_budget=100)
    assert db.most_running == 1


def test_a_statement_larger_than_the_budget_is_refused_before_anything_runs() -> None:
    """An index whose own estimate exceeds the budget names itself."""
    db = _BuildingDB()
    with pytest.raises(ValueError, match=r'b: b\.0 needs an estimated 200 bytes'):
        db.build_indexes(
            {'a': _statements({'a': 1})['a'], 'b': [IndexStatement('b.0', 'b.0', 200, 200, 1)]},
            workers=2,
            space_budget=100,
        )
    assert db.ran == []


@pytest.mark.parametrize('workers', [1, 3])
def test_each_statement_runs_on_a_connection_sized_for_it(workers: int) -> None:
    """The connection running a statement was sized to that statement's sort and keys just before."""
    db = _BuildingDB()
    db.build_indexes(_statements({'a': 3, 'b': 2, 'c': 2}), workers=workers)
    assert db.sized == {
        f'{t}.{n}': (n, n + 1) for t, c in (('a', 3), ('b', 2), ('c', 2)) for n in range(c)
    }


def test_no_workers_is_refused() -> None:
    """At least one connection builds."""
    with pytest.raises(ValueError, match='workers must be at least 1'):
        _BuildingDB().build_indexes({}, workers=0)


# ------------------------------------------------------------------------------------
# Choosing the path
# ------------------------------------------------------------------------------------


class _StateDB:
    """A stand-in answering what `choose_import_path` asks of a schema."""

    def __init__(
        self,
        version_rows: list[tuple[int, str]] | None,
        keys: dict[str, list[TableKey]],
        tables: list[str],
    ) -> None:
        """Hold a schema's state.

        Parameters:
            version_rows: The ``schema_version`` rows, or None for no such table.
            keys: Each table's keys, as the server reports them.
            tables: The permanent tables.
        """
        self.version_rows = version_rows
        self.keys = keys
        self.tables = tables
        self.db_schema = 'opus_test'

    def table_exists(self, table: str) -> bool:
        """Say whether the version table exists."""
        assert table == 'schema_version'
        return self.version_rows is not None

    def read_rows(self, table: str, columns: list[str]) -> list[tuple[int, str]]:
        """Return the version rows."""
        assert self.version_rows is not None
        return self.version_rows

    def read_table_keys(self) -> dict[str, list[TableKey]]:
        """Return the keys."""
        return self.keys

    def table_names(self, prefix: Any = None) -> list[str]:
        """Return the tables."""
        return self.tables


def _choose(db: _StateDB) -> tuple[bool, Any]:
    """Choose a path against `db`, returning the answer and the context."""
    ctx = make_context(db=db)
    return do_import.choose_import_path(ctx), ctx


def test_an_empty_schema_is_imported_fresh() -> None:
    """No version row and no tables: the fresh path."""
    chosen, ctx = _choose(_StateDB(None, {}, []))
    assert chosen
    assert ctx.import_path == do_import.IMPORT_PATH_FRESH
    assert ctx.logger.messages_at('info') == [
        'Import path: fresh import, into "opus_test" (no schema_version row)'
    ]


def test_a_fresh_import_in_progress_stays_fresh() -> None:
    """Tables carrying only the keys a load needs are still a fresh import."""
    keys = {'obs_general': [TableKey('primary', ('id',)), TableKey('key', ('bundle_id',))]}
    chosen, ctx = _choose(_StateDB([], keys, ['obs_general']))
    assert chosen
    assert ctx.import_path == do_import.IMPORT_PATH_FRESH


@pytest.mark.parametrize('state', ['ready', 'appending'])
def test_a_schema_of_this_version_is_appended_to(state: str) -> None:
    """A finished schema, or one an earlier append left part way, takes the append."""
    chosen, ctx = _choose(_StateDB([(SCHEMA_VERSION, state)], {}, []))
    assert chosen
    assert ctx.import_path == do_import.IMPORT_PATH_APPEND
    assert ctx.logger.messages_at('info') == [
        f'Import path: append, into "opus_test" (version {SCHEMA_VERSION}, {state})'
    ]


@pytest.mark.parametrize(
    ('rows', 'named'),
    [
        ([(SCHEMA_VERSION - 1, 'ready')], f'is version {SCHEMA_VERSION - 1} and this release'),
        ([(SCHEMA_VERSION, 'ready'), (SCHEMA_VERSION, 'ready')], 'has 2 schema_version rows'),
        ([(SCHEMA_VERSION, 'loading')], "has the state 'loading'"),
    ],
    ids=['another-version', 'two-rows', 'unknown-state'],
)
def test_a_schema_no_import_may_append_to_is_refused(
    rows: list[tuple[int, str]], named: str
) -> None:
    """Another release's schema, or a malformed version table, is re-imported instead."""
    chosen, ctx = _choose(_StateDB(rows, {}, []))
    assert not chosen
    assert ctx.import_path is None
    (message,) = ctx.logger.messages_at('fatal')
    assert named in message
    assert '--scorched-earth --yes' in message


def test_an_interrupted_finalization_refuses_the_import() -> None:
    """No version row but a key finalization adds: refused, naming --finalize."""
    keys = {'obs_general': [TableKey('primary', ('id',)), TableKey('key', ('time1', 'opus_id'))]}
    chosen, ctx = _choose(_StateDB(None, keys, ['obs_general']))
    assert not chosen
    (message,) = ctx.logger.messages_at('fatal')
    assert 'obs_general: KEY (time1, opus_id)' in message
    assert '--finalize' in message


# ------------------------------------------------------------------------------------
# The chunked per-bundle delete
# ------------------------------------------------------------------------------------


class _DeletingDB:
    """A stand-in that answers each table's ids for a bundle and records each delete."""

    def __init__(
        self,
        ids: dict[str, list[Any]] | list[Any],
        tables: list[str],
        id_range: tuple[int, int] | None = None,
    ) -> None:
        """Hold each table's ids for the bundle, the tables, and the bundle's range.

        Parameters:
            ids: Each table's ids, in order, keyed by table; or one list answering every
                select, whatever it reads.
            tables: The ``obs_`` tables.
            id_range: The bundle's registered first id and capacity, or None for a
                bundle the registry does not hold.
        """
        self.ids = ids
        self.tables = tables
        self.id_range = id_range
        self.transaction_rows = 2
        self.selects: list[str] = []
        self.deletes: list[tuple[str, str, list[Any]]] = []

    def table_names(self, prefix: Any = None) -> list[str]:
        """Return the tables."""
        return self.tables

    def quote_identifier(self, name: str) -> str:
        """Backtick-quote a name."""
        return f'`{name}`'

    def table_exists(self, table: str) -> bool:
        """Say whether the registry exists: only when the bundle has a range."""
        assert table == 'import_bundle'
        return self.id_range is not None

    def read_rows(
        self, table: str, columns: list[str], where: str, params: list[Any]
    ) -> list[tuple[Any, ...]]:
        """Return the bundle's registry row."""
        assert self.id_range is not None
        first_id, capacity = self.id_range
        row = {
            'bundle_number': 1,
            'bundle_id': params[0],
            'size_estimate': capacity // 100,
            'first_id': first_id,
            'id_capacity': capacity,
            'state': 'importing',
            'started_at': None,
        }
        return [tuple(row[column] for column in columns)]

    def retrying(self, description: str, body: Any) -> Any:
        """Run the body once."""
        return body()

    def general_select(self, cmd: str, params: Any = None) -> list[tuple[Any]]:
        """Return the ids of the table the query names, one page of them when it asks.

        A paged query's parameters end with the page size, after the bundle and, past
        the first page, the id the page starts after. A ``MAX`` over a range of
        ``obs_general`` ids returns the highest of them.
        """
        if cmd.startswith('MAX('):
            first, last = params
            ids = self.ids if isinstance(self.ids, list) else self.ids.get('obs_general', [])
            inside = [i for i in ids if first <= i <= last]
            return [(max(inside) if inside else None,)]
        self.selects.append(cmd)
        if isinstance(self.ids, list):
            ids = self.ids
        else:
            table = cmd.split('FROM `')[1].split('`')[0]
            ids = self.ids.get(table, [])
        if 'LIMIT' in cmd:
            if '> %s' in cmd:
                ids = [i for i in ids if i > params[1]]
            ids = ids[: params[-1]]
        return [(i,) for i in ids]

    def delete_rows(self, table: str, where: str, where_params: list[Any]) -> None:
        """Record a delete."""
        self.deletes.append((table, where, where_params))

    JOINED_PARENT_ALIAS = 'p'

    def delete_joined_rows(
        self,
        table: str,
        join_column: str,
        parent_table: str,
        parent_column: str,
        where: str,
        where_params: list[Any],
    ) -> None:
        """Record a joined delete, naming its join as ``<table>~<parent>``."""
        assert (join_column, parent_table, parent_column) == ('obs_general_id', 'obs_general', 'id')
        self.deletes.append((f'{table}~{parent_table}', where, where_params))


_IN_RANGE = '`bundle_id`=%s AND `id` BETWEEN %s AND %s'

_PARENT_IN_RANGE = '`p`.`bundle_id` = %s AND `p`.`id` BETWEEN %s AND %s'

_ORPHANS = '`obs_general_id` BETWEEN %s AND %s'


def test_a_bundle_is_deleted_a_chunk_of_obs_general_at_a_time_children_first() -> None:
    """Every child, ``obs_surface_geometry_target`` among them, through each chunk.

    Before the chunks, every child loses its rows in the bundle's range above the highest
    ``obs_general`` id in it, and none outside the range, which another bundle's import
    may be loading. Each chunk is `transaction_rows` of the bundle's ``obs_general`` ids:
    every child's rows joining them go, then the chunk's ``obs_general`` rows.
    """
    tables = ['obs_files', 'obs_general', 'obs_pds', 'obs_surface_geometry_target']
    db = _DeletingDB({'obs_general': [4, 7, 9]}, tables, id_range=(0, 100))
    do_import_tables.delete_bundle_from_obs_tables(make_context(db=db), 'B_1')
    children = ['obs_files', 'obs_pds', 'obs_surface_geometry_target']
    assert db.deletes == [
        *[(child, _ORPHANS, [10, 99]) for child in children],
        *[(f'{child}~obs_general', _PARENT_IN_RANGE, ['B_1', 4, 7]) for child in children],
        ('obs_general', _IN_RANGE, ['B_1', 4, 7]),
        *[(f'{child}~obs_general', _PARENT_IN_RANGE, ['B_1', 9, 9]) for child in children],
        ('obs_general', _IN_RANGE, ['B_1', 9, 9]),
    ]
    # Only obs_general is read, by its bundle key.
    assert {cmd.split('FROM `')[1].split('`')[0] for cmd in db.selects} == {'obs_general'}
    assert all('WHERE `bundle_id`=%s' in cmd for cmd in db.selects)
    assert all(cmd.endswith('ORDER BY `id` LIMIT %s') for cmd in db.selects)
    # A full page asks for the next one, after its last id; a short page ends the table.
    assert sum('`id` > %s' in cmd for cmd in db.selects) == 1


def test_a_bundle_a_table_does_not_hold_deletes_nothing_there() -> None:
    """No ids, no joined statement; a child's rows anywhere in the range go."""
    db = _DeletingDB(
        {}, ['obs_general', 'obs_pds', 'obs_surface_geometry_target'], id_range=(200, 100)
    )
    do_import_tables.delete_bundle_from_obs_tables(make_context(db=db), 'B_1')
    # An empty obs_general leaves no row of a child that joins it.
    assert db.deletes == [
        ('obs_pds', _ORPHANS, [200, 299]),
        ('obs_surface_geometry_target', _ORPHANS, [200, 299]),
    ]


def test_a_bundle_the_registry_lacks_deletes_only_its_joined_rows() -> None:
    """With no range there is nothing to bound the leftover rows by, so none are sought."""
    db = _DeletingDB({'obs_general': [4]}, ['obs_general', 'obs_pds'])
    do_import_tables.delete_bundle_from_obs_tables(make_context(db=db), 'B_1')
    assert db.deletes == [
        ('obs_pds~obs_general', _PARENT_IN_RANGE, ['B_1', 4, 4]),
        ('obs_general', _IN_RANGE, ['B_1', 4, 4]),
    ]


# ------------------------------------------------------------------------------------
# The duplicate step
# ------------------------------------------------------------------------------------


class _DuplicateDB(_DeletingDB):
    """A stand-in whose ``obs_general`` holds the duplicated rows it is given."""

    def __init__(self, rows: list[tuple[int, str, str]], remaining: list[Any]) -> None:
        """Hold the duplicated rows, and what the closing check finds.

        Parameters:
            rows: ``(id, opus_id, bundle_id)`` for every row sharing an OPUS id.
            remaining: What the check after the deletes finds.
        """
        super().__init__([], ['obs_general', 'obs_pds'])
        self.answers = [rows, remaining]
        self.read_only = False

    def table_exists(self, table: str) -> bool:
        """Say obs_general exists."""
        return True

    def general_select(self, cmd: str, params: Any = None) -> list[Any]:
        """Record the query and return the next answer."""
        self.selects.append(cmd)
        return self.answers.pop(0)


def test_the_highest_id_is_kept_and_the_others_deleted_children_first() -> None:
    """Another bundle's copy is logged at info level; the same bundle's as a warning."""
    db = _DuplicateDB(
        [(3, 'a', 'B_1'), (8, 'a', 'B_2'), (4, 'b', 'B_1'), (5, 'b', 'B_1')], remaining=[]
    )
    ctx = make_context(db=db)
    assert do_duplicate_ids.delete_duplicate_opus_ids(ctx)
    # The OPUS id comes from the grouped side, so case variants the collation joins
    # come back under one spelling.
    assert '`g`.`id`, `d`.`opus_id`, `g`.`bundle_id`' in db.selects[0]
    assert db.deletes == [
        ('obs_pds', '`obs_general_id` IN (%s,%s)', [3, 4]),
        ('obs_general', '`id` IN (%s,%s)', [3, 4]),
    ]
    assert ctx.logger.messages_at('warning') == [
        'Duplicate OPUS ID "b": keeping obs_general id 5 from B_1, deleting id 4 from B_1'
    ]
    assert (
        'Duplicate OPUS ID "a": keeping obs_general id 8 from B_2, deleting id 3 from B_1'
        in ctx.logger.messages_at('info')
    )


def test_an_id_left_shared_after_the_step_is_an_error() -> None:
    """The closing check fails the step when any OPUS id still has two rows."""
    db = _DuplicateDB([(3, 'a', 'B_1'), (8, 'a', 'B_2')], remaining=[(1, 'a', 'B_1')])
    ctx = make_context(db=db)
    assert not do_duplicate_ids.delete_duplicate_opus_ids(ctx)
    assert ctx.logger.messages_at('error') == ['An OPUS ID still has more than one obs_general row']


# ------------------------------------------------------------------------------------
# --create-indexes
# ------------------------------------------------------------------------------------


class _IndexingDB(_RecordingDB):
    """A recording backend whose builds are recorded rather than run."""

    def __init__(self, keys: dict[str, list[TableKey]], budget: int | None = None) -> None:
        """Hold the keys the server reports and the space budget.

        Parameters:
            keys: Each table's keys.
            budget: The space budget, or None.
        """
        super().__init__({'obs_pds'})
        self.keys = keys
        self.budget = budget
        self.built: dict[str, list[IndexStatement]] = {}
        self.workers = 0
        self.foreign: list[IndexStatement] = []
        self.analyzed: list[str] = []

    def read_table_keys(self) -> dict[str, list[TableKey]]:
        """Return the keys."""
        return self.keys

    def index_space_budget(self, server_tmpdir: str | None) -> int | None:
        """Return the budget."""
        return self.budget

    def key_space_bytes(self, table_name: str, schema: Any, key: TableKey) -> int:
        """Size every key at 60 bytes."""
        return 60

    def build_indexes(
        self, table_to_statements: Any, **kwargs: Any
    ) -> dict[str, list[tuple[str, float]]]:
        """Record the statements."""
        self.built = dict(table_to_statements)
        self.workers = kwargs['workers']
        return {
            table: [(statement.label, 0.5) for statement in statements]
            for table, statements in table_to_statements.items()
        }

    def add_foreign_keys(self, statements: Any) -> list[tuple[str, float]]:
        """Record the foreign keys."""
        self.foreign = list(statements)
        return [(statement.label, 0.25) for statement in statements]

    def analyze_table(self, table_name: str) -> None:
        """Record the analyze."""
        self.analyzed.append(table_name)


def test_create_indexes_adds_what_a_child_lacks_then_its_foreign_key() -> None:
    """ANALYZE for the estimates, the plain keys in one statement, the foreign key on its own, then ANALYZE."""
    db = _IndexingDB({'obs_pds': [TableKey('primary', ('obs_general_id',))]})
    ctx = make_context(db=db)
    assert do_indexes.create_indexes(ctx)
    (statement,) = db.built['obs_pds']
    assert statement.sort_bytes == 60 < statement.space_bytes
    assert statement.key_count == statement.sql.count('ADD KEY')
    assert statement.sql.startswith('ALTER TABLE `obs_pds` ADD KEY (`opus_id`)')
    assert 'ADD KEY (`bundle_id`)' in statement.sql
    # The primary key leads with the foreign key's column, so no key is added for it.
    assert 'ADD KEY (`obs_general_id`)' not in statement.sql
    assert [s.sql for s in db.foreign] == [
        'ALTER TABLE `obs_pds` ADD FOREIGN KEY (`obs_general_id`) REFERENCES '
        '`obs_general`(`id`) ON DELETE RESTRICT ON UPDATE CASCADE'
    ]
    assert db.analyzed == ['obs_pds', 'obs_pds']
    assert db.workers == 1
    assert ctx.step_timings['create_indexes:obs_pds'] == 0.5


def test_create_indexes_on_a_finished_schema_does_nothing() -> None:
    """Every key in place: no statement, and no ANALYZE."""
    schema = import_util.read_schema_for_existing_table(make_context(), 'obs_pds')
    assert schema is not None
    every = [*create_time_keys('obs_pds', schema), *add_secondary_indexes('obs_pds', schema)]
    db = _IndexingDB({'obs_pds': every})
    ctx = make_context(db=db)
    assert do_indexes.create_indexes(ctx)
    assert db.built == {}
    assert db.foreign == []
    assert db.analyzed == []
    assert 'Every table has every key its schema declares' in ctx.logger.messages_at('info')


def test_under_a_budget_a_tables_keys_are_split_to_fit() -> None:
    """Keys of 60 bytes under a budget of 100 go one to a statement."""
    db = _IndexingDB({'obs_pds': []}, budget=100)
    ctx = make_context(db=db)
    assert do_indexes.create_indexes(ctx)
    assert len(db.built['obs_pds']) > 1
    assert all(statement.space_bytes <= 100 for statement in db.built['obs_pds'])


# ------------------------------------------------------------------------------------
# Validation's orphan count, and the aggregates
# ------------------------------------------------------------------------------------


class _OrphanDB(_DeletingDB):
    """A stand-in reporting an orphan count for every table."""

    def __init__(self, count: int, tables: list[str] | None = None) -> None:
        """Hold the count every anti-join finds, and the tables that exist besides cart."""
        super().__init__([], ['obs_general', 'obs_pds'] if tables is None else tables)
        self.count = count
        self.queries: list[str] = []

    def table_exists(self, table: str) -> bool:
        """Say cart exists, and each of the tables."""
        return table == 'cart' or table in self.tables

    def general_select(self, cmd: str, params: Any = None) -> list[tuple[int]]:
        """Return the count."""
        self.queries.append(' '.join(cmd.split()))
        return [(self.count,)]


def test_rows_whose_obs_general_row_is_missing_are_errors() -> None:
    """Every child and ``cart`` is anti-joined against ``obs_general``."""
    db = _OrphanDB(3)
    ctx = make_context(db=db)
    do_validate.validate_orphans(ctx)
    assert ctx.logger.messages_at('error') == [
        'Table "obs_pds" has 3 rows whose obs_general row is missing',
        'Table "cart" has 3 rows whose obs_general row is missing',
    ]
    assert all('IS NULL' in query for query in db.queries)


class _NullCountDB:
    """A stand-in with two nullable columns in each of obs_pds and the surface table."""

    def __init__(self, counts: tuple[int | None, ...]) -> None:
        """Hold the NULL counts each table's one query returns, column by column."""
        self.counts = counts
        self.queries: list[str] = []

    def quote_identifier(self, name: str) -> str:
        """Backtick-quote a name."""
        return f'`{name}`'

    def table_names(self, prefix: str) -> list[str]:
        """Name obs_pds and ``obs_surface_geometry_target``."""
        return ['obs_pds', 'obs_surface_geometry_target']

    def table_info(self, table: str) -> list[dict[str, Any]]:
        """Describe a table's columns: one NOT NULL key column, then two nullable ones."""
        if table == 'obs_pds':
            return [
                {'field_name': 'obs_general_id', 'field_notnull': True},
                {'field_name': 'note', 'field_notnull': False},
                {'field_name': 'primary_lid', 'field_notnull': False},
            ]
        return [
            {'field_name': 'target_name', 'field_notnull': True},
            {'field_name': 'phase1', 'field_notnull': False},
            {'field_name': 'phase2', 'field_notnull': False},
        ]

    def general_select(self, cmd: str, params: Any = None) -> list[tuple[int | None, ...]]:
        """Record the query and return the counts."""
        self.queries.append(cmd)
        return [self.counts]


def test_one_query_a_table_counts_the_nulls_of_every_nullable_column() -> None:
    """A nullable column that holds no NULL is reported; NOT NULL columns are not counted.

    ``obs_surface_geometry_target`` is counted once, over every body's rows.
    """
    db = _NullCountDB((0, 5))
    ctx = make_context(db=db)
    do_validate.validate_nulls(ctx)
    assert db.queries == [
        'SUM(`note` IS NULL), SUM(`primary_lid` IS NULL) FROM `obs_pds`',
        'SUM(`phase1` IS NULL), SUM(`phase2` IS NULL) FROM `obs_surface_geometry_target`',
    ]
    assert ctx.logger.messages_at('info') == [
        'Column "obs_pds.note" allows NULLs but none found - suggest changing column attributes',
        'Column "obs_surface_geometry_target.phase1" allows NULLs but none found - suggest '
        'changing column attributes',
    ]


def test_an_empty_tables_nullable_columns_are_reported() -> None:
    """The sums over no rows are NULL, which is none found."""
    db = _NullCountDB((None, None))
    ctx = make_context(db=db)
    do_validate.validate_nulls(ctx)
    assert len(ctx.logger.messages_at('info')) == 4


@pytest.mark.parametrize(
    ('tables', 'errors'),
    [
        (['obs_pds'], ['Table "obs_general" is missing, but 1 other obs_ tables exist']),
        ([], []),
    ],
)
def test_child_tables_without_obs_general_are_an_error(
    tables: list[str], errors: list[str]
) -> None:
    """Children with no obs_general are reported; a schema with neither has nothing to check."""
    ctx = make_context(db=_OrphanDB(0, tables))
    do_validate.validate_orphans(ctx)
    assert ctx.logger.messages_at('error') == errors


def test_no_orphans_is_silent() -> None:
    """A count of zero logs nothing."""
    ctx = make_context(db=_OrphanDB(0))
    do_validate.validate_orphans(ctx)
    assert ctx.logger.messages_at('error') == []


@pytest.mark.parametrize(('count', 'errors'), [(2, 1), (0, 0)])
def test_an_obs_pds_bundle_unlike_obs_generals_is_an_error(count: int, errors: int) -> None:
    """``obs_pds`` is joined to ``obs_general`` and rows naming another bundle counted."""
    db = _OrphanDB(count)
    ctx = make_context(db=db)
    do_validate.validate_pds_bundle_ids(ctx)
    assert ctx.logger.messages_at('error') == (
        ['Table "obs_pds" has 2 rows whose bundle_id differs from obs_general'] * errors
    )
    (query,) = db.queries
    assert '`p`.`bundle_id` <> `g`.`bundle_id`' in query


def test_no_obs_pds_has_no_bundle_to_compare() -> None:
    """Without ``obs_pds`` the check reads nothing."""
    db = _OrphanDB(5, ['obs_general'])
    ctx = make_context(db=db)
    do_validate.validate_pds_bundle_ids(ctx)
    assert db.queries == []
    assert ctx.logger.messages_at('error') == []


class _SharedOpusIdDB(_OrphanDB):
    """A stand-in whose ``obs_general`` holds the shared OPUS ids given."""

    def __init__(self, shared: list[str], tables: list[str] | None = None) -> None:
        """Hold the OPUS ids the grouping finds shared."""
        super().__init__(0, tables)
        self.shared = shared

    def general_select(self, cmd: str, params: Any = None) -> list[tuple[Any, ...]]:
        """Return how many OPUS ids are shared, or as many of them as the limit allows."""
        self.queries.append(' '.join(cmd.split()))
        if cmd.startswith('COUNT(*)'):
            return [(len(self.shared),)]
        limit = int(cmd.rsplit('LIMIT', 1)[1])
        return [(opus_id,) for opus_id in self.shared[:limit]]


def test_an_opus_id_on_two_obs_general_rows_is_an_error() -> None:
    """The count and the first ten shared OPUS ids are named."""
    shared = [f'co-iss-n{index:02d}' for index in range(12)]
    db = _SharedOpusIdDB(shared)
    ctx = make_context(db=db)
    do_validate.validate_unique_opus_ids(ctx)
    [error] = ctx.logger.messages_at('error')
    assert error.startswith('12 OPUS IDs have more than one obs_general row')
    assert '"co-iss-n09"' in error
    assert '"co-iss-n10"' not in error
    assert all('HAVING COUNT(*) > 1' in query for query in db.queries)
    assert db.queries[1].endswith('LIMIT 10')


@pytest.mark.parametrize('tables', [['obs_general', 'obs_pds'], []])
def test_unique_opus_ids_or_no_obs_general_is_silent(tables: list[str]) -> None:
    """Nothing shared, or no obs_general to look in, logs no error."""
    ctx = make_context(db=_SharedOpusIdDB([], tables))
    do_validate.validate_unique_opus_ids(ctx)
    assert ctx.logger.messages_at('error') == []


_GROUP = (
    'create_indexes',
    'create_param_info',
    'create_partables',
    'create_table_names',
    'create_cart',
    'reset_search_tables',
    'analyze_tables',
)


@pytest.mark.parametrize('option', ['finalize', 'do_it_all'])
def test_every_aggregate_that_finishes_a_database_runs_the_whole_group(option: str) -> None:
    """``--do-it-all`` expands through ``--finalize``."""
    args = default_arguments()
    setattr(args, option, True)
    cli.expand_aggregate_options(args)
    assert args.finalize
    assert all(getattr(args, step) for step in _GROUP)


def test_do_it_all_imports_and_finalize_alone_does_not() -> None:
    """``--do-it-all`` is ``--import`` then ``--finalize``; ``--finalize`` imports nothing."""
    args = default_arguments()
    args.do_it_all = True
    cli.expand_aggregate_options(args)
    assert args.do_import
    args = default_arguments()
    args.finalize = True
    cli.expand_aggregate_options(args)
    assert not args.do_import


def test_a_new_context_has_chosen_no_path() -> None:
    """The context starts with no path chosen, so `do_import_steps` chooses one."""
    assert make_context(db=SimpleNamespace()).import_path is None
