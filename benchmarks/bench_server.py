"""The MySQL server the harness owns, and the schemas on it.

`benchmarks.app_servers` holds the other two owned servers, memcached and gunicorn, and
`benchmarks.opus_config_file` the ``OPUS_CONFIG`` the harness writes.
Nothing here touches a server the harness did not start. The MySQL server runs from
the generic tarball named in ``scenarios/server.toml``, with its own data directory,
socket and ``my.cnf`` rendered from ``scenarios/my.cnf.template``; the import and
the web application reach it through the socket, which the harness puts in their
environment as ``MYSQL_UNIX_PORT`` (the MySQL client library's own variable for the
default socket) beside the ``OPUS_CONFIG`` it writes with ``host = "localhost"``.

Run as a command to manage the MySQL server between bench commands::

    python -m benchmarks.bench_server init     # create the data directory once
    python -m benchmarks.bench_server start
    python -m benchmarks.bench_server status
    python -m benchmarks.bench_server stop
"""

from __future__ import annotations

import argparse
import contextlib
import fcntl
import math
import os
import subprocess  # nosec B404 - the harness starts and stops its own servers
import sys
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

import MySQLdb

from benchmarks.app_servers import (
    START_TIMEOUT_S,
    STOP_TIMEOUT_S,
    ServerError,
    pid_alive,
    wait_for,
)
from benchmarks.results import SCENARIOS_DIR, filesystem_type

if TYPE_CHECKING:
    from collections.abc import Iterator, Mapping, Sequence

SERVER_TOML = SCENARIOS_DIR / 'server.toml'
MY_CNF_TEMPLATE = SCENARIOS_DIR / 'my.cnf.template'

MIB = 1024**2
GIB = 1024**3

#: InnoDB's default buffer pool chunk. The pool must be a multiple of the chunk size
#: times the instance count, and the template sets one instance.
BUFFER_POOL_CHUNK = 128 * MIB

#: A Unix socket path longer than this is refused by mysqld.
MAX_SOCKET_PATH = 107

#: The application's credentials on the owned server: its root account, which
#: ``mysqld --initialize-insecure`` creates with no password and only for local
#: connections.
DB_HOST = 'localhost'
DB_USER = 'root'
DB_PASSWORD = ''  # nosec B105 - the owned server's root has none, and listens locally only

#: The environment variable the MySQL client library reads its default socket from.
SOCKET_ENV_VAR = 'MYSQL_UNIX_PORT'


def expand_path(value: str) -> Path:
    """Expand ``~`` and environment variables in a configured path.

    Parameters:
        value: The path as written.

    Returns:
        The absolute path.

    Raises:
        ServerError: If it names an environment variable that is not set.
    """
    expanded = os.path.expandvars(os.path.expanduser(value))
    if '$' in expanded:
        raise ServerError(f'{value!r} names an environment variable that is not set')
    return Path(expanded).resolve()


def buffer_pool_size(budget_bytes: int) -> int:
    """Size the buffer pool from a memory budget by ``innodb_dedicated_server``'s rule.

    Parameters:
        budget_bytes: The memory treated as the server's.

    Returns:
        128 MiB below 1 GiB, half of the budget up to 4 GiB, three quarters above,
        rounded down to a whole number of buffer pool chunks.
    """
    if budget_bytes < GIB:
        return 128 * MIB
    share = budget_bytes * 0.5 if budget_bytes <= 4 * GIB else budget_bytes * 0.75
    return max(BUFFER_POOL_CHUNK, int(share) // BUFFER_POOL_CHUNK * BUFFER_POOL_CHUNK)


def redo_log_capacity(budget_bytes: int) -> int:
    """Size the redo log from a memory budget by ``innodb_dedicated_server``'s rule.

    The rule is the one for MySQL 8.0.30 and later with the buffer pool configured.

    Parameters:
        budget_bytes: The memory treated as the server's.

    Returns:
        100 MiB below 2 GiB; ``round(0.5 * GB) * 0.5`` GiB from 2 GiB up to 4 GiB,
        rounding halves up; ``round(0.75 * GB) * 0.5`` GiB up to 10.66 GiB; ``round(0.5625 * GB)`` GiB up to
        170.66 GiB; and 128 GiB above, where GB is the budget in GiB.
    """
    gb = budget_bytes / GIB
    if gb < 2:
        return 100 * MIB
    if gb <= 4:
        return int(_round_half_up(0.5 * gb) * 0.5 * GIB)
    if gb <= 10.66:
        return int(_round_half_up(0.75 * gb) * 0.5 * GIB)
    if gb <= 170.66:
        return int(_round_half_up(0.5625 * gb) * GIB)
    return 128 * GIB


def _round_half_up(value: float) -> int:
    """Round to the nearest whole number, halves upward, as the documented rule does.

    Parameters:
        value: A non-negative number.

    Returns:
        The rounded value. Python's own `round` sends halves to the even neighbor,
        which would give 4 for 4.5.
    """
    return math.floor(value + 0.5)


@dataclass(frozen=True)
class MysqlConfig:
    """Where the owned MySQL server lives and how it is sized.

    Attributes:
        basedir: The unpacked generic tarball.
        library_dir: A directory put first on ``LD_LIBRARY_PATH`` for mysqld, or None.
        data_root: The directory holding the data directory, socket, ``my.cnf`` and
            error log.
        memory_budget_bytes: The memory the sizing rules treat as the server's.
        io_capacity: ``innodb_io_capacity``.
    """

    basedir: Path
    library_dir: Path | None
    data_root: Path
    memory_budget_bytes: int
    io_capacity: int

    @property
    def datadir(self) -> Path:
        """The server's data directory."""
        return self.data_root / 'data'

    @property
    def socket(self) -> Path:
        """The server's Unix socket."""
        return self.data_root / 'mysqld.sock'

    @property
    def my_cnf(self) -> Path:
        """The rendered option file the server starts with."""
        return self.data_root / 'my.cnf'

    @property
    def pid_file(self) -> Path:
        """The file mysqld writes its process id to."""
        return self.data_root / 'mysqld.pid'

    @property
    def error_log(self) -> Path:
        """The server's error log."""
        return self.data_root / 'error.log'

    @property
    def web_runs_lock(self) -> Path:
        """The file `MysqlServer.web_runs_held` locks."""
        return self.data_root / 'web_runs.lock'

    def render_my_cnf(self, template: str) -> str:
        """Fill the option-file template.

        Parameters:
            template: The text of ``my.cnf.template``.

        Returns:
            The option file.
        """
        return template.format(
            basedir=self.basedir,
            datadir=self.datadir,
            socket=self.socket,
            pid_file=self.pid_file,
            error_log=self.error_log,
            buffer_pool_size=buffer_pool_size(self.memory_budget_bytes),
            buffer_pool_chunk_size=BUFFER_POOL_CHUNK,
            redo_log_capacity=redo_log_capacity(self.memory_budget_bytes),
            io_capacity=self.io_capacity,
            io_capacity_max=2 * self.io_capacity,
        )


def load_server_config(path: Path = SERVER_TOML) -> tuple[MysqlConfig, str]:
    """Read ``server.toml``.

    Parameters:
        path: The file.

    Returns:
        The MySQL server's configuration and the memcached binary: a bare name, which
        is looked up on ``PATH``, or an expanded path.

    Raises:
        ServerError: If the socket path would be too long for mysqld, or a path names an
            environment variable that is not set.
    """
    with path.open('rb') as stream:
        raw = tomllib.load(stream)
    mysql = raw['mysql']
    library_dir = mysql['library_dir']
    config = MysqlConfig(
        basedir=expand_path(mysql['basedir']),
        library_dir=None if library_dir == '' else expand_path(library_dir),
        data_root=expand_path(mysql['data_root']),
        memory_budget_bytes=int(float(mysql['memory_budget_gb']) * GIB),
        io_capacity=int(mysql['io_capacity']),
    )
    if len(str(config.socket).encode()) >= MAX_SOCKET_PATH:
        raise ServerError(f'the socket path {config.socket} is {MAX_SOCKET_PATH} bytes or more')
    binary = str(raw['memcached']['binary'])
    # A bare name is looked up on PATH; anything else is a path, expanded like the others.
    if '/' in binary or binary.startswith(('~', '$')):
        binary = str(expand_path(binary))
    return config, binary


class MysqlServer:
    """The harness-owned mysqld.

    The server is found by its pid file and socket, so a server one command started
    can be used and stopped by the next.
    """

    def __init__(self, config: MysqlConfig) -> None:
        """Describe the server; nothing is started.

        Parameters:
            config: Where it lives and how it is sized.
        """
        self.config = config
        self._process: subprocess.Popen[bytes] | None = None

    def _binary(self, name: str) -> str:
        """Return the path of one of the tarball's programs.

        Parameters:
            name: The program, such as ``mysqld``.

        Returns:
            Its path.
        """
        return str(self.config.basedir / 'bin' / name)

    def _environment(self) -> dict[str, str]:
        """Return the environment mysqld runs under, with the private library directory.

        Returns:
            This process's environment, with `MysqlConfig.library_dir` first on
            ``LD_LIBRARY_PATH``.
        """
        env = dict(os.environ)
        if self.config.library_dir is not None:
            existing = env.get('LD_LIBRARY_PATH', '')
            env['LD_LIBRARY_PATH'] = os.pathsep.join(
                part for part in (str(self.config.library_dir), existing) if part != ''
            )
        return env

    def write_my_cnf(self) -> None:
        """Render the option file from the template into the data root."""
        # Private to the account running the harness: the socket in it reaches a root
        # account with no password.
        self.config.data_root.mkdir(mode=0o700, parents=True, exist_ok=True)
        self.config.data_root.chmod(0o700)
        text = self.config.render_my_cnf(MY_CNF_TEMPLATE.read_text(encoding='utf-8'))
        self.config.my_cnf.write_text(text, encoding='utf-8')

    def initialize(self) -> None:
        """Create the data directory, with a root account that has no password.

        Raises:
            ServerError: If the data directory already holds anything, or mysqld fails.
        """
        if self.config.datadir.exists() and any(self.config.datadir.iterdir()):
            raise ServerError(f'{self.config.datadir} is not empty; it is initialized already')
        self.write_my_cnf()
        finished = subprocess.run(  # nosec B603 - the tarball's mysqld, fixed arguments
            [
                self._binary('mysqld'),
                f'--defaults-file={self.config.my_cnf}',
                '--initialize-insecure',
            ],
            env=self._environment(),
            capture_output=True,
            text=True,
            check=False,
        )
        if finished.returncode != 0:
            raise ServerError(f'mysqld --initialize-insecure failed; see {self.config.error_log}')

    def pid(self) -> int | None:
        """Return the running server's process id, from its pid file.

        Returns:
            The id, or None when no server of this data root is running.
        """
        if not self.config.pid_file.exists():
            return None
        text = self.config.pid_file.read_text(encoding='utf-8').strip()
        if not text.isdigit() or not pid_alive(int(text)):
            return None
        return int(text)

    @contextlib.contextmanager
    def web_runs_held(self, *, exclusive: bool) -> Iterator[None]:
        """Hold the lock that keeps a generation switch apart from ``bench_web`` commands.

        A ``bench_web`` command holds it shared for as long as it runs, so any number of
        them run together; a generation switch holds it exclusive, since the switch empties
        the search tables and flushes the cache that a web run measures. The lock is taken
        without waiting, and the operating system releases it when its holder exits.

        Parameters:
            exclusive: Whether to hold it exclusive, as a switch does, rather than shared.

        Yields:
            Nothing; the lock is held until the block exits.

        Raises:
            ServerError: If the other kind holds it, or another switch holds it exclusive.
        """
        path = self.config.web_runs_lock
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('a', encoding='utf-8') as stream:
            try:
                fcntl.flock(stream, (fcntl.LOCK_EX if exclusive else fcntl.LOCK_SH) | fcntl.LOCK_NB)
            except BlockingIOError:
                holder = (
                    'a bench_web command or another generation switch'
                    if exclusive
                    else 'a generation switch'
                )
                raise ServerError(f'{holder} holds {path}') from None
            try:
                yield
            finally:
                fcntl.flock(stream, fcntl.LOCK_UN)

    def is_running(self) -> bool:
        """Return whether the server answers on its socket.

        Returns:
            True when a connection succeeds.
        """
        if self.pid() is None:
            return False
        try:
            self.connect().close()
        except MySQLdb.Error:
            return False
        return True

    def start(self) -> None:
        """Start the server and wait until it answers.

        Raises:
            ServerError: If the data directory was never initialized, a server is
                already running, or it does not come up.
        """
        if not (self.config.datadir / 'mysql').is_dir():
            raise ServerError(
                f'{self.config.datadir} is not initialized: run '
                '`python -m benchmarks.bench_server init` once'
            )
        if self.pid() is not None:
            raise ServerError(f'a server is already running from {self.config.data_root}')
        self.write_my_cnf()
        with self.config.error_log.open('ab') as log:
            self._process = subprocess.Popen(  # nosec B603 - the tarball's mysqld
                [self._binary('mysqld'), f'--defaults-file={self.config.my_cnf}'],
                env=self._environment(),
                stdout=log,
                stderr=log,
                stdin=subprocess.DEVNULL,
                start_new_session=True,
            )
        process = self._process

        def answering() -> bool:
            """Return whether the server accepts a connection, failing if it died."""
            if process.poll() is not None:
                raise ServerError(
                    f'mysqld exited {process.returncode}; see {self.config.error_log}'
                )
            return self.config.socket.exists() and self.is_running()

        wait_for(answering, START_TIMEOUT_S, 'mysqld to accept connections')

    def stop(self) -> None:
        """Shut the server down cleanly and wait for its process to exit.

        Raises:
            ServerError: If the shutdown fails or the process outlives the timeout.
        """
        pid = self.pid()
        if pid is None:
            process = self._process
            if process is not None and process.poll() is None:
                # Started here but not yet answering, so there is no pid file to shut
                # down by: SIGTERM is mysqld's own clean shutdown.
                process.terminate()
                process.wait(timeout=STOP_TIMEOUT_S)
            self._process = None
            return
        finished = subprocess.run(  # nosec B603 - the tarball's mysqladmin
            [
                self._binary('mysqladmin'),
                # First, so no option file can redirect the shutdown to another server.
                '--no-defaults',
                f'--socket={self.config.socket}',
                f'--user={DB_USER}',
                'shutdown',
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        if finished.returncode != 0:
            raise ServerError(f'mysqladmin shutdown failed: {finished.stderr.strip()}')
        if self._process is not None:
            self._process.wait(timeout=STOP_TIMEOUT_S)
            self._process = None
        wait_for(lambda: not pid_alive(pid), STOP_TIMEOUT_S, 'mysqld to exit')

    def restart(self) -> None:
        """Stop the server and start it again: with this configuration, a cold start."""
        self.stop()
        self.start()

    @contextlib.contextmanager
    def running(self) -> Iterator[MysqlServer]:
        """Use the server, starting it first if it is down and stopping it again after.

        Yields:
            This server, answering.
        """
        started_here = not self.is_running()
        try:
            if started_here:
                self.start()
            yield self
        finally:
            if started_here:
                self.stop()

    def connect(self, schema: str | None = None, *, read_timeout: int | None = None) -> Any:
        """Open a connection as root through the socket, in autocommit mode.

        Parameters:
            schema: The default schema, or None for none.
            read_timeout: The seconds a read may wait before it fails, or None to wait as
                long as it takes.

        Returns:
            A MySQLdb connection.
        """
        kwargs: dict[str, Any] = {}
        if schema is not None:
            kwargs['db'] = schema
        if read_timeout is not None:
            kwargs['read_timeout'] = read_timeout
        return MySQLdb.connect(
            unix_socket=str(self.config.socket),
            user=DB_USER,
            passwd=DB_PASSWORD,
            charset='utf8mb4',
            autocommit=True,
            **kwargs,
        )

    def client_environment(self, config_file: Path | None = None) -> dict[str, str]:
        """Return the environment a program reaching this server runs under.

        Parameters:
            config_file: The ``OPUS_CONFIG`` to name, or None to leave it as it is.

        Returns:
            This process's environment with the socket set as the client library's
            default, and the configuration file named.
        """
        env = dict(os.environ)
        env[SOCKET_ENV_VAR] = str(self.config.socket)
        if config_file is not None:
            env['OPUS_CONFIG'] = str(config_file)
        return env


def reexec_with_socket(config: MysqlConfig, module: str, argv: Sequence[str]) -> None:
    """Make sure this process's MySQL client library defaults to the owned socket.

    The client library reads `SOCKET_ENV_VAR` once, when ``MySQLdb`` is first imported,
    so setting it later changes nothing for this process: a connection made by host
    name alone (as `import_tests.tools.golden_io` makes them) would reach whatever
    server owns the system's default socket. When the variable does not already name
    the owned socket, this replaces the process with the same command and the variable
    set, before anything has connected. It returns only when the variable was right.

    Parameters:
        config: The owned server's configuration.
        module: The ``python -m`` module being run.
        argv: Its arguments.
    """
    if os.environ.get(SOCKET_ENV_VAR) == str(config.socket):
        return
    env = dict(os.environ)
    env[SOCKET_ENV_VAR] = str(config.socket)
    os.execve(sys.executable, [sys.executable, '-m', module, *argv], env)  # nosec B606 - this same command again


def query(connection: Any, statement: str, parameters: Sequence[Any] = ()) -> list[tuple[Any, ...]]:
    """Run one statement on a connection and return its rows.

    Parameters:
        connection: An open connection.
        statement: The SQL.
        parameters: Values for its ``%s`` placeholders.

    Returns:
        Every row, as tuples; empty for a statement that returns none.
    """
    with contextlib.closing(connection.cursor()) as cursor:
        cursor.execute(statement, tuple(parameters) if len(parameters) > 0 else None)
        rows = cursor.fetchall()
    return list(rows) if rows is not None else []


def global_status(connection: Any) -> dict[str, int]:
    """Return the server's numeric global status counters.

    Parameters:
        connection: An open connection.

    Returns:
        Each counter whose value is a whole number, by name.
    """
    return {
        name: int(value)
        for name, value in query(connection, 'SHOW GLOBAL STATUS')
        if isinstance(value, str) and value.isdigit()
    }


def counter_deltas(
    before: Mapping[str, int], after: Mapping[str, int], names: Sequence[str]
) -> dict[str, int]:
    """Return how far each named counter moved between two snapshots.

    Parameters:
        before: The first snapshot.
        after: The second.
        names: The counters wanted.

    Returns:
        ``after - before`` per name; a counter missing from either snapshot is left out.
    """
    return {name: after[name] - before[name] for name in names if name in before and name in after}


#: The connections the harness holds open on the owned server beside a web run's request
#: slots: its own, and the side's import or management command that resets the search
#: tables or warms the landing page.
HARNESS_CONNECTIONS = 2


def require_connection_room(connection: Any, slots: int) -> int:
    """Refuse a web run whose request slots the server could not all connect.

    Each request slot keeps the database connection its first request opened, so every
    slot may hold one at once, beside the harness's own (`HARNESS_CONNECTIONS`). A server
    that refused one would fail requests that a larger ``max_connections`` would have
    served, and a thread sweep would time the refusals.

    Parameters:
        connection: An open connection to the owned server.
        slots: The web run's request slots, workers times threads.

    Returns:
        The server's ``max_connections``.

    Raises:
        ServerError: If ``max_connections`` does not exceed the slots plus the harness's
            own connections.
    """
    rows = query(connection, 'SELECT @@GLOBAL.max_connections')
    limit = int(rows[0][0])
    needed = slots + HARNESS_CONNECTIONS
    if limit <= needed:
        raise ServerError(
            f"the server's max_connections is {limit}, which does not exceed the {slots} "
            f"request slots and the harness's {HARNESS_CONNECTIONS} connections; raise it "
            "in the owned server's my.cnf.template or ask for fewer slots"
        )
    return limit


def server_settings(connection: Any, names: Sequence[str]) -> dict[str, str]:
    """Return the current values of the named server variables.

    Parameters:
        connection: An open connection.
        names: The variables; one the server does not have is left out.

    Returns:
        Each variable's value as the server reports it.
    """
    placeholders = ', '.join(['%s'] * len(names))
    rows = query(
        connection,
        f'SELECT VARIABLE_NAME, VARIABLE_VALUE FROM performance_schema.global_variables '  # nosec B608 - placeholders only
        f'WHERE VARIABLE_NAME IN ({placeholders})',
        names,
    )
    return {str(name): str(value) for name, value in rows}


#: The server variables every result records.
RECORDED_SETTINGS = (
    'innodb_buffer_pool_size',
    'innodb_buffer_pool_chunk_size',
    'innodb_buffer_pool_instances',
    'innodb_flush_method',
    'innodb_flush_log_at_trx_commit',
    'innodb_redo_log_capacity',
    'innodb_io_capacity',
    'innodb_io_capacity_max',
    'innodb_parallel_read_threads',
    'innodb_ddl_threads',
    'innodb_ddl_buffer_size',
    'innodb_ft_enable_stopword',
    'ngram_token_size',
    'local_infile',
    'log_bin',
    'max_digest_length',
    'performance_schema_max_digest_length',
    'sort_buffer_size',
    'tmp_table_size',
    'temptable_max_ram',
    'transaction_isolation',
)


def server_environment(server: MysqlServer) -> dict[str, Any]:
    """Return the facts about the owned server every result records.

    Parameters:
        server: The owned server, running.

    Returns:
        Its brand, version, ownership, the variables in `RECORDED_SETTINGS`, the
        filesystem its data directory is on, and the memory budget it was sized from.
    """
    with contextlib.closing(server.connect()) as connection:
        version = str(query(connection, 'SELECT VERSION()')[0][0])
        settings = server_settings(connection, RECORDED_SETTINGS)
    return {
        'brand': 'mysql',
        'server_version': version,
        'server_owned': True,
        'server_settings': settings,
        'datadir_fstype': filesystem_type(server.config.datadir),
        'server_memory_budget_bytes': server.config.memory_budget_bytes,
    }


def quote_identifier(name: str) -> str:
    """Quote a schema or table name for MySQL.

    Parameters:
        name: The name.

    Returns:
        The name in backquotes, with any backquote in it doubled.
    """
    return '`' + name.replace('`', '``') + '`'


def drop_schema(server: MysqlServer, schema: str) -> None:
    """Drop a schema if it exists.

    Parameters:
        server: The owned server.
        schema: The schema.
    """
    with contextlib.closing(server.connect()) as connection:
        query(connection, f'DROP DATABASE IF EXISTS {quote_identifier(schema)}')


#: The table holding a schema's one version row.
SCHEMA_VERSION_TABLE = 'schema_version'

#: The only version-row state a side serves, and the only one the harness restamps. The
#: harness reads it from the schema as text rather than importing a side's code, so it
#: repeats the value.
SCHEMA_ROW_READY_STATE = 'ready'


def restamp_version(server: MysqlServer, schema: str, version: int) -> str | None:
    """Set the version in a finished schema's version row, leaving its state alone.

    The import's own step never overwrites a different version, so where a side's code
    expects another version than the schema it is given carries, the harness sets the
    row itself. Only a ``ready`` row is changed: a schema an import or an append is still
    writing keeps the version that import will finish it under.

    Parameters:
        server: The owned server.
        schema: The schema.
        version: The version to record, the ``SCHEMA_VERSION`` of the side that will use
            the schema.

    Returns:
        The row's state, or None when the schema has no ``schema_version`` table or the
        table is empty.

    Raises:
        ServerError: If the table holds more than one row, which no side would serve.
    """
    with contextlib.closing(server.connect()) as connection:
        exists = query(
            connection,
            'SELECT COUNT(*) FROM information_schema.TABLES '
            'WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s',
            [schema, SCHEMA_VERSION_TABLE],
        )[0][0]
        if exists == 0:
            return None
        table = f'{quote_identifier(schema)}.{quote_identifier(SCHEMA_VERSION_TABLE)}'
        states = query(connection, f'SELECT state FROM {table}')  # nosec B608 - quoted identifier
        if len(states) == 0:
            return None
        if len(states) > 1:
            raise ServerError(
                f'schema {schema} has {len(states)} schema_version rows, not one; no side '
                'would serve it'
            )
        state = str(states[0][0])
        if state == SCHEMA_ROW_READY_STATE:
            query(connection, f'UPDATE {table} SET version = %s', [version])  # nosec B608 - quoted identifier
        return state


#: The base table holding the observations of a schema whose ``obs_general`` is a view of
#: the rows in the import generation it serves. The harness reads the schema rather than
#: importing a side's code, so it repeats the name.
OBS_GENERAL_ROWS_TABLE = 'obs_general_rows'

#: ``obs_general``, the base table holding the observations of every other schema.
OBS_GENERAL_TABLE = 'obs_general'

#: The columns of `OBS_GENERAL_ROWS_TABLE` naming the import generation that added a row
#: and the one that retired it (NULL while no generation has).
ADDED_GENERATION_COLUMN = 'added_generation'
REMOVED_GENERATION_COLUMN = 'removed_generation'


def obs_general_table(connection: Any, schema: str) -> str:
    """Return the base table that holds a schema's observations, in whichever generation.

    A schema whose ``obs_general`` is a view shows only the rows of the generation it
    serves, and none at all before its version row is written, so the harness's checks
    on what an import wrote read the base table.

    Parameters:
        connection: An open connection.
        schema: The schema.

    Returns:
        `OBS_GENERAL_ROWS_TABLE` when the schema has that base table, else
        `OBS_GENERAL_TABLE`.
    """
    found = query(
        connection,
        'SELECT COUNT(*) FROM information_schema.TABLES '
        "WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s AND TABLE_TYPE = 'BASE TABLE'",
        [schema, OBS_GENERAL_ROWS_TABLE],
    )
    return OBS_GENERAL_ROWS_TABLE if int(found[0][0]) > 0 else OBS_GENERAL_TABLE


def main(argv: Sequence[str] | None = None) -> None:
    """Initialize, start, stop, or report on the owned MySQL server.

    Parameters:
        argv: The arguments, or None for the command line's.
    """
    parser = argparse.ArgumentParser(
        prog='python -m benchmarks.bench_server',
        description='Manage the harness-owned MySQL server named in scenarios/server.toml.',
    )
    parser.add_argument('action', choices=['init', 'start', 'stop', 'status'])
    args = parser.parse_args(argv)
    config, _ = load_server_config()
    server = MysqlServer(config)
    if args.action == 'init':
        server.initialize()
    elif args.action == 'start':
        server.start()
    elif args.action == 'stop':
        server.stop()
    running = server.is_running()
    sys.stdout.write(
        f'mysqld from {config.basedir}\n  data root {config.data_root}\n'
        f'  {"running, pid " + str(server.pid()) if running else "not running"}\n'
    )


if __name__ == '__main__':
    main()
