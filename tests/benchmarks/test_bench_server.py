"""The tuning baseline's sizing rules and the server configuration they render into."""

from pathlib import Path

import pytest

from benchmarks import bench_server
from benchmarks.app_servers import ServerError
from benchmarks.bench_server import GIB, MIB, MysqlConfig


@pytest.mark.parametrize(
    ('budget', 'expected'),
    [
        (512 * MIB, 128 * MIB),
        (2 * GIB, 1 * GIB),
        (4 * GIB, 2 * GIB),
        (24 * GIB, 18 * GIB),
        (10 * GIB + 1, 7680 * MIB),
    ],
    ids=['below-1g', '2g-half', '4g-half', '24g-three-quarters', 'rounded-to-chunks'],
)
def test_the_buffer_pool_follows_the_dedicated_server_rule(budget: int, expected: int) -> None:
    """Half up to 4 GiB, three quarters above, in whole 128 MiB chunks."""
    assert bench_server.buffer_pool_size(budget) == expected


@pytest.mark.parametrize(
    ('budget', 'expected'),
    [
        (1 * GIB, 100 * MIB),
        (2 * GIB, 512 * MIB),
        (3 * GIB, 1 * GIB),
        (6 * GIB, 2560 * MIB),
        (8 * GIB, 3 * GIB),
        (24 * GIB, 14 * GIB),
        (256 * GIB, 128 * GIB),
    ],
    ids=[
        'below-2g',
        'at-2g',
        '2g-to-4g',
        'half-rounds-up',
        '4g-to-10g',
        '10g-to-170g',
        'above-170g',
    ],
)
def test_the_redo_log_follows_the_dedicated_server_rule(budget: int, expected: int) -> None:
    """Each band of the documented table gives its capacity."""
    assert bench_server.redo_log_capacity(budget) == expected


def _config(tmp_path: Path) -> MysqlConfig:
    """Return a configuration rooted in a temporary directory."""
    return MysqlConfig(
        basedir=tmp_path / 'mysql',
        library_dir=None,
        data_root=tmp_path / 'data',
        memory_budget_bytes=24 * GIB,
        io_capacity=1000,
    )


@pytest.mark.parametrize(
    'line',
    [
        'innodb_buffer_pool_size = 19327352832',
        'innodb_redo_log_capacity = 15032385536',
        'innodb_io_capacity_max = 2000',
        'innodb_buffer_pool_instances = 1',
        'innodb_flush_method = O_DIRECT',
        'skip-log-bin',
        'local_infile = ON',
        'performance_schema_max_digest_length = 4096',
        'innodb_buffer_pool_dump_at_shutdown = OFF',
        'skip-networking',
    ],
)
def test_the_template_renders_the_baseline(tmp_path: Path, line: str) -> None:
    """Every setting the baseline names reaches the option file the server reads."""
    text = _config(tmp_path).render_my_cnf(bench_server.MY_CNF_TEMPLATE.read_text())
    assert line in text.splitlines()


def test_the_option_file_has_no_binary_log_setting(tmp_path: Path) -> None:
    """``log_bin = OFF`` would name a log file and turn logging on."""
    text = _config(tmp_path).render_my_cnf(bench_server.MY_CNF_TEMPLATE.read_text())
    assert not any(line.startswith('log_bin') for line in text.splitlines())


def test_a_socket_path_mysqld_would_refuse_is_refused_first(tmp_path: Path) -> None:
    """A path of 107 bytes or more is reported before any server is started."""
    deep = tmp_path / ('d' * 120)
    path = tmp_path / 'server.toml'
    path.write_text(
        f'[mysql]\nbasedir = "{tmp_path}"\nlibrary_dir = ""\ndata_root = "{deep}"\n'
        'memory_budget_gb = 1\nio_capacity = 200\n[memcached]\nbinary = "memcached"\n'
    )
    with pytest.raises(ServerError, match='107 bytes or more'):
        bench_server.load_server_config(path)


def test_the_configured_paths_expand_the_home_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A path written with ``~`` is the running user's, so no user's home is written down."""
    monkeypatch.setenv('HOME', str(tmp_path))
    path = tmp_path / 'server.toml'
    path.write_text(
        '[mysql]\nbasedir = "~/mysql"\nlibrary_dir = "~/lib"\ndata_root = "~/d"\n'
        'memory_budget_gb = 1\nio_capacity = 200\n[memcached]\nbinary = "memcached"\n'
    )
    config, binary = bench_server.load_server_config(path)
    assert config.data_root == (tmp_path / 'd').resolve()
    assert config.library_dir == (tmp_path / 'lib').resolve()
    assert binary == 'memcached'


def test_a_memcached_path_expands_the_home_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A memcached binary given as a path is expanded; a bare name is left for PATH."""
    monkeypatch.setenv('HOME', str(tmp_path))
    path = tmp_path / 'server.toml'
    path.write_text(
        '[mysql]\nbasedir = "~/mysql"\nlibrary_dir = ""\ndata_root = "~/d"\n'
        'memory_budget_gb = 1\nio_capacity = 200\n[memcached]\nbinary = "~/bin/memcached"\n'
    )
    _, binary = bench_server.load_server_config(path)
    assert binary == str((tmp_path / 'bin' / 'memcached').resolve())


def test_the_counters_move_by_their_difference() -> None:
    """A counter absent from either snapshot is left out rather than guessed."""
    deltas = bench_server.counter_deltas({'a': 1, 'b': 5}, {'a': 4, 'c': 9}, ['a', 'b', 'c'])
    assert deltas == {'a': 3}


@pytest.mark.parametrize(
    ('name', 'expected'), [('obs_general', '`obs_general`'), ('a`b', '`a``b`')]
)
def test_identifiers_are_quoted(name: str, expected: str) -> None:
    """A backquote inside a name is doubled."""
    assert bench_server.quote_identifier(name) == expected


class _CloneCursor:
    """A cursor that records each statement on its connection and answers the clone's reads."""

    def __init__(self, statements: list[str]) -> None:
        """Record into the connection's list."""
        self.statements = statements
        self.rows: list[tuple[str, ...]] = []

    def execute(self, statement: str, parameters: object = None) -> None:
        """Record a statement and choose the rows it answers."""
        self.statements.append(statement)
        if statement.startswith('SELECT TABLE_NAME'):
            self.rows = [('obs_pds',)]
        elif statement.startswith('SHOW CREATE TABLE'):
            self.rows = [('obs_pds', 'CREATE TABLE `obs_pds` (`bundle_id` varchar(75))')]
        elif statement.startswith('SELECT COLUMN_NAME'):
            self.rows = [('bundle_id',)]
        else:
            self.rows = []

    def fetchall(self) -> list[tuple[str, ...]]:
        """Return the last statement's rows."""
        return self.rows

    def close(self) -> None:
        """Nothing to release."""


class _CloneConnection:
    """A connection whose statements are kept in the order they were sent."""

    def __init__(self) -> None:
        """Start with nothing sent."""
        self.statements: list[str] = []

    def cursor(self) -> _CloneCursor:
        """Return a cursor recording into this connection."""
        return _CloneCursor(self.statements)

    def close(self) -> None:
        """Nothing to release."""


class _CloneServer:
    """A server handing out recording connections, the first being the clone's own."""

    def __init__(self) -> None:
        """Start with no connection."""
        self.connections: list[_CloneConnection] = []

    def connect(self) -> _CloneConnection:
        """Return a new recording connection."""
        connection = _CloneConnection()
        self.connections.append(connection)
        return connection


def test_a_clone_creates_its_tables_with_the_stopword_list_off() -> None:
    """A copied FULLTEXT index keeps the creating session's setting, so the list is off
    before the first table is created."""
    server = _CloneServer()
    bench_server.clone_schema(server, 'source', 'target', version=None, connections=1)  # type: ignore[arg-type]
    statements = server.connections[0].statements
    created = next(i for i, s in enumerate(statements) if s.startswith('CREATE TABLE'))
    assert 'SET SESSION innodb_ft_enable_stopword = OFF' in statements[:created]
