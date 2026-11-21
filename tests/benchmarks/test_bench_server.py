"""The tuning baseline's sizing rules and the server configuration they render into."""

import contextlib
from collections.abc import Iterator
from pathlib import Path

import pytest

from benchmarks import bench_server, bench_web
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


def test_web_commands_share_the_web_runs_lock(tmp_path: Path) -> None:
    """Any number of bench_web commands hold it together."""
    server = bench_server.MysqlServer(_config(tmp_path))
    with server.web_runs_held(exclusive=False), server.web_runs_held(exclusive=False):
        pass


@pytest.mark.parametrize(
    ('first', 'second', 'holder'),
    [
        (False, True, 'a bench_web command or another generation switch'),
        (True, False, 'a generation switch'),
        (True, True, 'a bench_web command or another generation switch'),
    ],
    ids=['switch-beside-web', 'web-beside-switch', 'switch-beside-switch'],
)
def test_a_switch_and_a_web_command_exclude_each_other(
    first: bool, second: bool, holder: str, tmp_path: Path
) -> None:
    """The second is refused at once, naming what holds the lock, which is then free."""
    server = bench_server.MysqlServer(_config(tmp_path))
    with (
        server.web_runs_held(exclusive=first),
        pytest.raises(ServerError, match=f'^{holder} holds '),
        server.web_runs_held(exclusive=second),
    ):
        pass
    with server.web_runs_held(exclusive=second):
        pass


class _HeldServer:
    """The owned server as a web command takes it, recording what it does."""

    def __init__(self, *, up: bool, switching: bool = False) -> None:
        self.up = up
        self.switching = switching
        self.calls: list[str] = []

    def is_running(self) -> bool:
        return self.up

    @contextlib.contextmanager
    def web_runs_held(self, *, exclusive: bool) -> Iterator[None]:
        if self.switching:
            raise ServerError('a generation switch holds lock')
        self.calls.append(f'lock exclusive={exclusive}')
        yield
        self.calls.append('unlock')

    @contextlib.contextmanager
    def running(self) -> Iterator[None]:
        self.calls.append('start if down')
        yield
        self.calls.append('stop if started')


@pytest.mark.parametrize('up', [True, False], ids=['up', 'down'])
def test_a_web_command_making_every_pass_owns_the_server(up: bool) -> None:
    """It may start the server, and stops it after if so, all under the shared lock."""
    server = _HeldServer(up=up)
    with bench_web.hold_server(server, app_cold_only=False):  # type: ignore[arg-type]
        assert server.calls == ['lock exclusive=False', 'start if down']
    assert server.calls[2:] == ['stop if started', 'unlock']


def test_an_app_cold_only_command_never_starts_or_stops_the_server() -> None:
    """Stopping it would stop the incremental update sharing it."""
    server = _HeldServer(up=True)
    with bench_web.hold_server(server, app_cold_only=True):  # type: ignore[arg-type]
        pass
    assert server.calls == ['lock exclusive=False', 'unlock']
    stopped = _HeldServer(up=False)
    with pytest.raises(ServerError, match='is not running'):
        bench_web.hold_server(stopped, app_cold_only=True)  # type: ignore[arg-type]
    assert stopped.calls == []


def test_a_web_command_is_refused_during_a_switch() -> None:
    """Nothing is started when the lock is refused."""
    server = _HeldServer(up=False, switching=True)
    with pytest.raises(ServerError, match='switch holds'):
        bench_web.hold_server(server, app_cold_only=False)  # type: ignore[arg-type]
    assert server.calls == []


class _MaxConnections:
    """A connection whose one query answers with a ``max_connections``."""

    def __init__(self, limit: int) -> None:
        self.limit = limit
        self.statements: list[str] = []

    def cursor(self) -> '_MaxConnections':
        return self

    def execute(self, statement: str, parameters: object = None) -> None:
        self.statements.append(statement)

    def fetchall(self) -> list[tuple[int]]:
        return [(self.limit,)]

    def close(self) -> None:
        pass


def test_a_server_with_room_for_every_slot_and_the_harness_is_accepted() -> None:
    """One connection more than the slots and the harness's own is enough."""
    connection = _MaxConnections(32 + bench_server.HARNESS_CONNECTIONS + 1)
    assert bench_server.require_connection_room(connection, 32) == connection.limit
    assert connection.statements == ['SELECT @@GLOBAL.max_connections']


def test_a_server_without_room_for_every_slot_and_the_harness_is_refused() -> None:
    """A server at exactly the slots and the harness's own connections could refuse one."""
    connection = _MaxConnections(32 + bench_server.HARNESS_CONNECTIONS)
    with pytest.raises(ServerError, match='max_connections is 34'):
        bench_server.require_connection_room(connection, 32)
