"""The memcached and the gunicorn the harness owns, and what every owned server shares.

`benchmarks.bench_server` holds the third owned server, MySQL, and the configuration
file all three are reached through.
"""

from __future__ import annotations

import contextlib
import json
import os
import shutil
import signal
import socket
import subprocess  # nosec B404 - the harness starts and stops its own servers
import time
from pathlib import Path
from typing import TYPE_CHECKING, Any

from benchmarks.gunicorn_hooks import DJANGO_SETTINGS_ENV, READY, SERVED_LOG_ENV

if TYPE_CHECKING:
    from collections.abc import Mapping

#: The gunicorn configuration file every side's application is started with.
GUNICORN_HOOKS = Path(__file__).resolve().parent / 'gunicorn_hooks.py'

#: How long a server may take to come up or go down before the harness gives up.
START_TIMEOUT_S = 600.0
STOP_TIMEOUT_S = 600.0


class ServerError(Exception):
    """Raised when an owned server cannot be configured, started, reached or stopped."""


def wait_for(condition: Any, timeout: float, what: str) -> None:
    """Wait until a condition holds, checking twice a second.

    Parameters:
        condition: A callable returning true once the wait is over.
        timeout: Seconds to wait at most.
        what: What is being waited for, for the error.

    Raises:
        ServerError: If the time runs out first.
    """
    deadline = time.monotonic() + timeout
    while not condition():
        if time.monotonic() > deadline:
            raise ServerError(f'timed out after {timeout:.0f} s waiting for {what}')
        time.sleep(0.5)


def pid_alive(pid: int) -> bool:
    """Return whether a process exists and has not been reaped.

    Parameters:
        pid: The process id.

    Returns:
        True while the process exists and is not a zombie.
    """
    status = Path(f'/proc/{pid}/status')
    if not status.exists():
        return False
    for line in status.read_text(encoding='utf-8').splitlines():
        if line.startswith('State:'):
            return 'Z' not in line.split()[1]
    return True


class MemcachedServer:
    """The harness-owned memcached, on a private port."""

    def __init__(self, binary: str, port: int, memory_mb: int) -> None:
        """Describe the server; nothing is started.

        Parameters:
            binary: The memcached program, a path or a name on PATH.
            port: Its port on 127.0.0.1.
            memory_mb: Its item memory, passed as ``-m``.
        """
        self.binary = binary
        self.port = port
        self.memory_mb = memory_mb
        self._process: subprocess.Popen[bytes] | None = None

    @property
    def location(self) -> str:
        """Its address as the application's ``cache_location`` names it."""
        return f'127.0.0.1:{self.port}'

    def start(self) -> None:
        """Start memcached and wait until it answers.

        Raises:
            ServerError: If the binary is missing, the port is taken, or it never answers.
        """
        program = shutil.which(self.binary)
        if program is None:
            raise ServerError(f'memcached binary {self.binary!r} not found')
        with contextlib.suppress(OSError), socket.create_connection(('127.0.0.1', self.port), 1):
            raise ServerError(f'something is already listening on 127.0.0.1:{self.port}')
        self._process = subprocess.Popen(  # nosec B603 - memcached, fixed arguments
            [
                program,
                '-l',
                '127.0.0.1',
                '-p',
                str(self.port),
                '-U',
                '0',
                '-m',
                str(self.memory_mb),
            ],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        wait_for(self._answers, START_TIMEOUT_S, 'memcached to answer')

    def _answers(self) -> bool:
        """Return whether ``stats`` gets an answer."""
        try:
            self.stats()
        except OSError:
            return False
        return True

    def stop(self) -> None:
        """Stop the memcached this object started, and wait for it to exit."""
        if self._process is None:
            return
        self._process.terminate()
        self._process.wait(timeout=STOP_TIMEOUT_S)
        self._process = None

    def restart(self) -> None:
        """Stop and start memcached, which empties it."""
        self.stop()
        self.start()

    def stats(self) -> dict[str, str]:
        """Return memcached's ``stats``.

        Returns:
            Each statistic's value as text, by name.
        """
        with socket.create_connection(('127.0.0.1', self.port), 5) as connection:
            connection.sendall(b'stats\r\n')
            received = b''
            while not received.endswith(b'END\r\n'):
                chunk = connection.recv(65536)
                if chunk == b'':
                    break
                received += chunk
        stats = {}
        for line in received.decode('ascii', 'replace').splitlines():
            parts = line.split()
            if len(parts) == 3 and parts[0] == 'STAT':
                stats[parts[1]] = parts[2]
        return stats


class GunicornServer:
    """The harness-started gunicorn, running one side's web application."""

    def __init__(
        self,
        *,
        python: Path,
        repo_root: Path,
        env: Mapping[str, str],
        port: int,
        workers: int,
        threads: int,
        log_dir: Path,
        app_log_file: Path,
        served_log: Path,
        django_settings: Mapping[str, object] | None = None,
    ) -> None:
        """Describe the server; nothing is started.

        Parameters:
            python: The side's interpreter, which runs gunicorn and the application.
            repo_root: The side's checkout, the working directory.
            env: The environment, naming the configuration and the database socket.
            port: The port on 127.0.0.1.
            workers: Worker processes.
            threads: Threads per worker, and the connections each worker accepts.
            log_dir: Where gunicorn's own logs go.
            app_log_file: The application's log file, which a worker opens when its
                Django setup configures logging; that is how a worker is known to have
                loaded the application.
            served_log: The file `GUNICORN_HOOKS` writes each worker's readiness and
                every request it serves to, emptied at each start.
            django_settings: The Django settings each worker assigns before it serves
                anything (`GUNICORN_HOOKS`), by name; None or empty for none.
        """
        self.python = python
        self.repo_root = repo_root
        self.env = dict(env)
        self.port = port
        self.workers = workers
        self.threads = threads
        self.log_dir = log_dir
        self.app_log_file = app_log_file
        self.served_log = served_log
        self.django_settings = dict(django_settings or {})
        self._process: subprocess.Popen[bytes] | None = None
        self._no_control_socket: bool | None = None

    @property
    def base_url(self) -> str:
        """The URL requests are sent to."""
        return f'http://127.0.0.1:{self.port}'

    @property
    def server_model(self) -> str:
        """What a result records as the server model."""
        return (
            f'gunicorn gthread workers={self.workers} threads={self.threads} '
            f'worker_connections={self.threads}'
        )

    def worker_pids(self) -> list[int]:
        """Return the worker processes' ids.

        Returns:
            The master's children, as listed under ``/proc``.
        """
        if self._process is None:
            return []
        children = Path(f'/proc/{self._process.pid}/task/{self._process.pid}/children')
        if not children.exists():
            return []
        return [int(pid) for pid in children.read_text(encoding='ascii').split()]

    def _loaded(self, pid: int) -> bool:
        """Return whether a worker has the application's log file open.

        Parameters:
            pid: The worker.

        Returns:
            True once Django's logging configuration has opened the file in it.
        """
        target = str(self.app_log_file.resolve())
        with contextlib.suppress(OSError):
            for descriptor in Path(f'/proc/{pid}/fd').iterdir():
                with contextlib.suppress(OSError):
                    if os.readlink(descriptor) == target:
                        return True
        return False

    def _served_lines(self) -> list[tuple[int, str]]:
        """Return the served log's lines since the last start, as written.

        Returns:
            One worker process id and its text (`READY`, or a request's path and query
            string) per line, in the order they were written.
        """
        if not self.served_log.exists():
            return []
        lines = []
        for line in self.served_log.read_text(encoding='utf-8', errors='replace').splitlines():
            pid, separator, text = line.partition('\t')
            if separator != '' and pid.isdigit():
                lines.append((int(pid), text))
        return lines

    def served(self) -> list[tuple[int, str]]:
        """Return every request the current workers have served since the last start.

        Returns:
            The serving worker's process id and the request's path and query string,
            in the order served.
        """
        return [(pid, text) for pid, text in self._served_lines() if text != READY]

    def served_by(self) -> dict[str, set[int]]:
        """Return which workers have served each path and query string since the start.

        Returns:
            The process ids of the workers that served it, by path and query string.
        """
        by_uri: dict[str, set[int]] = {}
        for pid, uri in self.served():
            by_uri.setdefault(uri, set()).add(pid)
        return by_uri

    def _ready(self) -> bool:
        """Return whether every worker has loaded the application and the port listens.

        A worker counts once it has the application's log file open and has written
        `READY` to the served log, which it does after importing the URLconf.
        """
        if self._process is not None and self._process.poll() is not None:
            raise ServerError(f'gunicorn exited {self._process.returncode}; see {self.log_dir}')
        pids = self.worker_pids()
        if len(pids) != self.workers or not all(self._loaded(pid) for pid in pids):
            return False
        ready = {pid for pid, text in self._served_lines() if text == READY}
        if not set(pids) <= ready:
            return False
        try:
            with socket.create_connection(('127.0.0.1', self.port), 1):
                return True
        except OSError:
            return False

    def _control_socket_options(self) -> list[str]:
        """Return the option that turns gunicorn's control socket off, where it has one.

        A gunicorn with a control socket opens it at one path per user by default, which
        a second gunicorn of the same user -- the other side's, or anyone's -- would
        contend for.

        Returns:
            ``--no-control-socket`` when the side's gunicorn lists it, otherwise nothing.
        """
        if self._no_control_socket is None:
            finished = subprocess.run(  # nosec B603 - the side's gunicorn, fixed arguments
                [str(self.python), '-m', 'gunicorn', '--help'],
                capture_output=True,
                text=True,
                check=False,
            )
            self._no_control_socket = '--no-control-socket' in finished.stdout.split()
        return ['--no-control-socket'] if self._no_control_socket else []

    def process_environment(self) -> dict[str, str]:
        """Return the environment gunicorn is started with.

        Returns:
            The server's environment, the served log's path under `SERVED_LOG_ENV`, and,
            when there are any, the Django settings as JSON under `DJANGO_SETTINGS_ENV`.
        """
        env = {**self.env, SERVED_LOG_ENV: str(self.served_log)}
        if self.django_settings:
            env[DJANGO_SETTINGS_ENV] = json.dumps(self.django_settings)
        return env

    def start(self) -> None:
        """Start gunicorn and wait until every worker has loaded the application.

        No request is sent: a request would touch the caches the reset has just
        emptied. The application is started with `GUNICORN_HOOKS` as gunicorn's
        configuration file, which imports the URLconf in each worker before it serves
        anything and records what each worker serves in the served log.

        Raises:
            ServerError: If gunicorn exits or never becomes ready.
        """
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.app_log_file.parent.mkdir(parents=True, exist_ok=True)
        self.served_log.parent.mkdir(parents=True, exist_ok=True)
        self.served_log.unlink(missing_ok=True)
        arguments = [
            str(self.python),
            '-m',
            'gunicorn',
            '--worker-class',
            'gthread',
            '--workers',
            str(self.workers),
            '--threads',
            str(self.threads),
            '--worker-connections',
            str(self.threads),
            '--bind',
            f'127.0.0.1:{self.port}',
            '--timeout',
            '3600',
            '--error-logfile',
            str(self.log_dir / 'gunicorn_error.log'),
            '--config',
            str(GUNICORN_HOOKS),
            *self._control_socket_options(),
            'opus_app.wsgi:application',
        ]
        self._process = subprocess.Popen(  # nosec B603 - the side's gunicorn
            arguments,
            cwd=self.repo_root,
            env=self.process_environment(),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        wait_for(self._ready, START_TIMEOUT_S, 'gunicorn workers to load the application')

    def stop(self) -> None:
        """Stop gunicorn and wait for the master and its workers to exit."""
        if self._process is None:
            return
        workers = self.worker_pids()
        self._process.send_signal(signal.SIGTERM)
        self._process.wait(timeout=STOP_TIMEOUT_S)
        self._process = None
        wait_for(
            lambda: not any(pid_alive(pid) for pid in workers),
            STOP_TIMEOUT_S,
            'gunicorn workers to exit',
        )

    def restart(self) -> None:
        """Stop and start the application."""
        self.stop()
        self.start()
