"""The coordinator: importers killed, a bundle lost twice, interrupts, and the importer lock.

Each case imports the fixture's bundles (or some of them) into a schema of its own with
``opus_import_all`` or ``opus_import --join``, and acts on the importers from outside as
an operator or a crash would: ``SIGKILL`` to an importer, ``SIGINT`` to the coordinator,
``KILL`` to an importer's lock connection. The importers hold at the test-only fault
sites (``OPUS_IMPORT_FAULT``), so each act lands where the case needs it: after a claim,
after a bundle's first chunk, or between an importer's row and its lock.

Every process a case starts, and every importer recorded in its schema that is still
running as one of the case's, is killed when the case ends, however it ends.
"""

from __future__ import annotations

import contextlib
import os
import signal
import socket
import subprocess
import time
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import pytest

from import_tests.tools import build_run, fixture_layout, golden_io
from opus_import import import_fault, import_processes
from opus_import.steps import do_import

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator
    from pathlib import Path

    from import_tests.tools.golden_io import DatabaseCredentials

#: Each importer's ``[import]`` keys: loads split across several transactions and
#: observations computed by a pool of small tasks, as the main run's are. A ceiling of
#: every core lets four workers divide among three importers on a four-core runner.
_KEYS = {'transaction_rows': 7, 'worker_rows': 5, 'cpu_fraction': 1.0}

#: How long a case waits for any one thing before it fails.
_TIMEOUT = 240.0

#: The most seconds an importer's lock may stay held after its process is killed.
_LOCK_FREED_WITHIN = 5.0


@dataclass
class Case:
    """One case's schema, configuration and the processes it started.

    Attributes:
        schema: The schema.
        paths: The configuration and log directory.
        credentials: How to reach the server.
        started: The processes the case started, killed when it ends.
    """

    schema: str
    paths: build_run.RunPaths
    credentials: DatabaseCredentials
    started: list[subprocess.Popen[str]]

    def rows(self, statement: str, parameters: tuple[Any, ...] = ()) -> list[tuple[Any, ...]]:
        """Run a query in the case's schema."""
        return golden_io.query(self.credentials, self.schema, statement, parameters)

    def start(self, module: str, arguments: list[str], fault: str | None = None) -> Any:
        """Start ``python -m <module>`` with the case's configuration, its output to a file.

        Parameters:
            module: ``opus_import`` or ``opus_import.import_all``.
            arguments: The command line after the module.
            fault: The ``OPUS_IMPORT_FAULT`` value, or None.

        Returns:
            The process.
        """
        environment = build_run.run_environment(self.paths.config_file)
        if fault is not None:
            environment[import_fault.IMPORT_FAULT_ENV_VAR] = fault
        output = self.paths.log_dir / f'{module}_{len(self.started)}.out'
        # The process writes through its own copy of the descriptor.
        with output.open('w', encoding='utf-8') as handle:
            process = subprocess.Popen(  # nosec B603 - this interpreter and the pipeline's module
                [str(build_run.THIS_PYTHON), '-m', module, *arguments],
                cwd=fixture_layout.REPO_ROOT,
                env=environment,
                stdout=handle,
                stderr=subprocess.STDOUT,
                text=True,
            )
        process.output_path = output  # type: ignore[attr-defined]
        self.started.append(process)
        return process

    def has(self, table: str) -> bool:
        """Return whether the case's schema has a table yet."""
        found = golden_io.query(
            self.credentials,
            None,
            'SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = %s '
            'AND table_name = %s',
            (self.schema, table),
        )
        return bool(found[0][0])

    def importers(self) -> list[tuple[int, int, str]]:
        """Return each importer's ``process_id``, pid and state, by ``process_id``."""
        if not self.has('import_process'):
            return []
        found = self.rows('SELECT process_id, pid, state FROM import_process ORDER BY process_id')
        return [(int(p), int(pid), str(state)) for p, pid, state in found]

    def lock_holder(self, process_id: int) -> int | None:
        """Return the connection holding an importer's lock, or None when it is free."""
        name = import_processes.importer_lock_name(self.schema, process_id)
        ((holder,),) = golden_io.query(self.credentials, None, 'SELECT IS_USED_LOCK(%s)', (name,))
        return None if holder is None else int(holder)

    def bundle(self, bundle_id: str) -> tuple[str, int | None, int]:
        """Return a bundle's state, ``process_id`` and losses; ``absent`` before it is
        registered."""
        if not self.has('import_bundle'):
            return 'absent', None, 0
        found = self.rows(
            'SELECT state, process_id, losses FROM import_bundle WHERE bundle_id = %s',
            (bundle_id,),
        )
        if not found:
            return 'absent', None, 0
        ((state, process_id, losses),) = found
        return str(state), None if process_id is None else int(process_id), int(losses)


def _wait[T](condition: Callable[[], T | None], what: str, timeout: float = _TIMEOUT) -> T:
    """Poll a condition every tenth of a second until it returns something.

    Parameters:
        condition: What to poll; None or False means not yet.
        what: What is waited for, for the failure message.
        timeout: The most seconds to wait.

    Returns:
        What the condition returned.
    """
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        found = condition()
        if found:
            return found
        time.sleep(0.1)
    pytest.fail(f'timed out waiting for {what}')


def _children(pid: int) -> list[int]:
    """Return a process's children, as Linux lists them."""
    try:
        with open(f'/proc/{pid}/task/{pid}/children', encoding='ascii') as children:
            text = children.read()
    except OSError:
        return []
    return [int(child) for child in text.split()]


def _runs_for(pid: int, config_file: Path) -> bool:
    """Return whether a process runs with a configuration, as Linux lists its environment.

    A pid recorded for an importer that has exited may since name another process; only
    one whose ``OPUS_CONFIG`` is the case's own is one of the case's importers.

    Parameters:
        pid: The process.
        config_file: The case's configuration.

    Returns:
        True if the process is alive and its environment names the configuration.
    """
    try:
        with open(f'/proc/{pid}/environ', 'rb') as environ:
            entries = environ.read().split(b'\0')
    except OSError:
        return False
    expected = f'{build_run.CONFIG_ENV_VAR}={config_file.resolve()}'.encode()
    return expected in entries


def _finish(process: Any, timeout: float = _TIMEOUT) -> tuple[int, str]:
    """Wait for a process, and return its status and its output."""
    status = process.wait(timeout=timeout)
    return status, process.output_path.read_text(encoding='utf-8')


@pytest.fixture
def case(
    request: pytest.FixtureRequest,
    main_run: build_run.ImportRun,
    db_credentials: DatabaseCredentials,
    created_schemas: list[str],
) -> Iterator[Case]:
    """A schema and configuration of the case's own; every process it started is killed
    at the end, and every importer its schema records that still runs as the case's.

    Yields:
        The case.
    """
    name = request.node.name.removeprefix('test_')[:24]
    schema = fixture_layout.schema_name(os.getpid(), f'co_{name}'[:20])
    created_schemas.append(schema)
    paths = build_run.sibling_paths(main_run, f'coordinator_{name}')
    paths.log_dir.mkdir(parents=True, exist_ok=True)
    build_run.write_opus_config(paths, schema, db_credentials, extra_import=_KEYS)
    # Created here, so the case can read it before the first invocation would create it.
    golden_io.execute(db_credentials, None, f'CREATE DATABASE `{schema}`')
    found = Case(schema, paths, db_credentials, [])
    try:
        yield found
    finally:
        for process in found.started:
            if process.poll() is None:
                process.kill()
                process.wait()
        recorded = found.importers()
        if recorded:
            host = socket.gethostname()
            hosts = dict(found.rows('SELECT process_id, host FROM import_process'))
            for process_id, pid, _state in recorded:
                if hosts[process_id] == host and _runs_for(pid, paths.config_file):
                    with contextlib.suppress(ProcessLookupError):
                        os.kill(pid, signal.SIGKILL)


def _register(case: Case, bundles: list[str]) -> None:
    """Register bundles in the case's schema, in the order given."""
    registered = build_run.run_pipeline_step(
        case.paths.config_file, [*build_run.REGISTER_ARGS, ','.join(bundles)]
    )
    assert registered.returncode == 0, registered.stdout[-2000:]


def _compare_with_main_run(case: Case, main_run: build_run.ImportRun) -> None:
    """Every goldened table equals the main run's, mult columns compared by value."""
    differences = [
        table
        for table in golden_io.goldened_tables(fixture_layout.GOLDENS_DIR)
        if golden_io.serialize_table(case.credentials, main_run.schema, table, mult_values=True)
        != golden_io.serialize_table(case.credentials, case.schema, table, mult_values=True)
    ]
    assert differences == []


def test_a_killed_importer_frees_its_lock_and_its_bundle_is_imported_again(
    case: Case, main_run: build_run.ImportRun
) -> None:
    """``SIGKILL`` to one of three importers while its pool runs, mid-bundle: its lock is
    free within seconds, the coordinator returns its bundle to the queue and replaces it,
    and the finished schema equals the one-importer schema."""
    hold = f'{import_processes.HOLD_AFTER_CHUNK_FAULT_SITE}:5'
    coordinator = case.start(
        'opus_import.import_all',
        ['--sets', ','.join(main_run.bundles), '--importers', '3', '--workers', '4'],
        fault=hold,
    )

    def pooled_importer_mid_bundle() -> tuple[int, int, str, list[int]] | None:
        """An importer with a pool, holding a bundle some of whose rows are committed."""
        for process_id, pid, state in case.importers():
            pool = _children(pid)
            if state != 'running' or not pool:
                continue
            held = case.rows(
                'SELECT bundle_id, first_id, first_id + id_capacity FROM import_bundle '
                "WHERE state = 'importing' AND process_id = %s",
                (process_id,),
            )
            for bundle_id, first, end in held:
                committed = (
                    case.rows(
                        'SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = '
                        "DATABASE() AND table_name = 'obs_files'"
                    )[0][0]
                    and case.rows(
                        'SELECT COUNT(*) FROM obs_files WHERE obs_general_id >= %s AND '
                        'obs_general_id < %s',
                        (first, end),
                    )[0][0]
                )
                if committed:
                    return process_id, pid, str(bundle_id), pool
        return None

    process_id, pid, bundle_id, pool = _wait(pooled_importer_mid_bundle, 'an importer mid-bundle')
    os.kill(pid, signal.SIGKILL)
    killed = time.monotonic()
    _wait(lambda: case.lock_holder(process_id) is None, 'the lock to be freed', _LOCK_FREED_WITHIN)
    assert time.monotonic() - killed < _LOCK_FREED_WITHIN
    assert pool

    status, output = _finish(coordinator)

    assert status == 0, output[-3000:]
    assert f'{bundle_id} returned to the queue: importer {process_id} died holding it' in output
    assert case.bundle(bundle_id)[0] == 'done'
    assert case.bundle(bundle_id)[2] == 1
    assert {p: s for p, _pid, s in case.importers()}[process_id] == 'lost'
    assert case.rows('SELECT state FROM schema_version') == [('ready',)]
    _compare_with_main_run(case, main_run)


def test_a_bundle_lost_twice_fails_and_nothing_is_finalized(case: Case) -> None:
    """Its importer killed twice, the bundle is failed; the coordinator names it with its
    importer's log, exits with failure, and writes no schema version row."""
    doomed, other = 'VG_2801', 'VG_2810'
    hold = f'{do_import.HOLD_AFTER_CLAIM_FAULT_SITE}:3'
    coordinator = case.start(
        'opus_import.import_all',
        ['--sets', f'{doomed},{other}', '--importers', '1', '--workers', '1'],
        fault=hold,
    )
    killed: list[int] = []

    def holder_of_doomed() -> tuple[int, int] | None:
        """The importer holding the doomed bundle, not yet killed."""
        state, process_id, _losses = case.bundle(doomed)
        if state != 'importing' or process_id is None or process_id in killed:
            return None
        pids = {p: pid for p, pid, _s in case.importers()}
        return process_id, pids[process_id]

    for _ in range(2):
        process_id, pid = _wait(holder_of_doomed, f'an importer holding {doomed}')
        os.kill(pid, signal.SIGKILL)
        killed.append(process_id)

    status, output = _finish(coordinator)

    assert status != 0
    assert case.bundle(doomed)[0] == 'failed'
    assert case.bundle(doomed)[2] == 2
    assert case.bundle(other)[0] == 'done'
    assert f'{doomed} failed: its importer died holding it 2 times' in output
    assert f"{doomed} (its importer's log: " in output
    assert not case.rows("SHOW TABLES LIKE 'schema_version'")


def test_two_interrupts_abort_and_a_rerun_resumes_to_the_same_result(
    case: Case, main_run: build_run.ImportRun
) -> None:
    """The first interrupt drains, the second returns the importers' bundles to the queue;
    nothing is finalized, no bundle is left importing or counted lost, and running the
    coordinator again finishes a schema equal to the one-importer schema."""
    arguments = ['--sets', ','.join(main_run.bundles), '--importers', '2', '--workers', '2']
    hold = f'{do_import.HOLD_AFTER_CLAIM_FAULT_SITE}:3'
    coordinator = case.start('opus_import.import_all', arguments, fault=hold)
    _wait(
        lambda: (
            case.has('import_bundle')
            and len(case.rows("SELECT 1 FROM import_bundle WHERE state = 'importing'")) == 2
        ),
        'both importers to hold a bundle',
    )
    coordinator.send_signal(signal.SIGINT)
    time.sleep(0.5)
    coordinator.send_signal(signal.SIGINT)

    status, output = _finish(coordinator)

    assert status != 0
    assert 'Interrupted again' in output
    states = dict(case.rows('SELECT bundle_id, state FROM import_bundle'))
    assert 'importing' not in states.values()
    assert 'pending' in states.values()
    assert case.rows('SELECT MAX(losses) FROM import_bundle') == [(0,)]
    assert not case.rows("SHOW TABLES LIKE 'schema_version'")

    status, output = _finish(case.start('opus_import.import_all', arguments))

    assert status == 0, output[-3000:]
    assert case.rows('SELECT state FROM schema_version') == [('ready',)]
    _compare_with_main_run(case, main_run)


def test_an_importer_whose_lock_connection_is_killed_aborts_its_bundle(case: Case) -> None:
    """``KILL`` of the lock connection mid-bundle: the importer exits with failure naming
    its lock, and its bundle is pending with no row of it committed."""
    bundle_id = 'COCIRS_1101'
    _register(case, [bundle_id])
    hold = f'{import_processes.HOLD_AFTER_CHUNK_FAULT_SITE}:5'
    importer = case.start('opus_import', ['--join'], fault=hold)

    def in_the_hold() -> int | None:
        """The importer's lock connection, once a chunk of the bundle is committed."""
        found = case.importers()
        if not found:
            return None
        rows = (
            case.rows(
                'SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = DATABASE() '
                "AND table_name = 'obs_files'"
            )[0][0]
            and case.rows('SELECT COUNT(*) FROM obs_files')[0][0]
        )
        return case.lock_holder(found[0][0]) if rows else None

    holder = _wait(in_the_hold, "the bundle's first chunk")
    lock = import_processes.importer_lock_name(case.schema, case.importers()[0][0])
    golden_io.execute(case.credentials, None, f'KILL {int(holder)}')

    status, output = _finish(importer)

    assert status != 0
    # The first chunk after the hold found the lock gone; none committed after it.
    assert (
        f'lost its lock "{lock}" or its bundle while '
        f'{import_processes.WHILE_COMMITTING_A_CHUNK}' in output
    )
    assert case.bundle(bundle_id)[:2] == ('pending', None)
    assert case.rows('SELECT COUNT(*) FROM obs_general WHERE bundle_id = %s', (bundle_id,)) == [
        (0,)
    ]
    assert case.rows('SELECT COUNT(*) FROM obs_files') == [(0,)]


def test_a_recovery_deletes_rows_in_tables_created_after_it_connected(case: Case) -> None:
    """A coordinator connected to a schema holding only the registry recovers a killed
    importer's bundle: the rows the importer committed, in the tables it created since,
    are deleted. The coordinator's own importers may not claim the bundle, so nothing
    else deletes them."""
    bundle_id = 'COCIRS_1101'
    _register(case, [bundle_id])
    coordinator = case.start(
        'opus_import.import_all',
        ['--sets', bundle_id, '--exclude-bundles', bundle_id, '--importers', '1'],
    )
    _wait(
        lambda: 'exited with status 0' in coordinator.output_path.read_text(encoding='utf-8'),
        "the coordinator's importer to find nothing it may claim",
    )
    assert not case.has('obs_general')
    hold = f'{import_processes.HOLD_AFTER_CHUNK_FAULT_SITE}:5'
    importer = case.start('opus_import', ['--join'], fault=hold)

    def committed() -> int | None:
        """The running importer's ``process_id``, once a chunk of the bundle is committed;
        the coordinator's own importer, which exited, has a row too."""
        running = [p for p, _pid, state in case.importers() if state == 'running']
        rows = (
            running and case.has('obs_files') and case.rows('SELECT COUNT(*) FROM obs_files')[0][0]
        )
        return running[0] if rows else None

    process_id = _wait(committed, "the bundle's first chunk")
    importer.kill()
    importer.wait()

    status, output = _finish(coordinator)

    assert status != 0
    assert f'{bundle_id} returned to the queue: importer {process_id} died holding it' in output
    assert case.bundle(bundle_id) == ('pending', None, 1)
    assert case.rows('SELECT COUNT(*) FROM obs_general WHERE bundle_id = %s', (bundle_id,)) == [
        (0,)
    ]
    assert case.rows('SELECT COUNT(*) FROM obs_files') == [(0,)]


def test_no_reader_sees_an_importer_before_it_holds_its_lock(
    case: Case, main_run: build_run.ImportRun
) -> None:
    """During the hold between an importer's row and its lock, a ``READ COMMITTED`` read
    does not see the row and ``--status --recover`` finds no importer lost; after it,
    ``--status`` shows the importer with its lock held, still ``running``."""
    _register(case, main_run.bundles)
    hold = f'{import_processes.HOLD_BEFORE_LOCK_FAULT_SITE}:8'
    case.start('opus_import', ['--join', '--workers', '1'], fault=hold)

    def uncommitted_insert() -> bool:
        """A transaction on the schema has written a row and not committed it."""
        found = golden_io.query(
            case.credentials,
            None,
            'SELECT COUNT(*) FROM information_schema.innodb_trx t JOIN '
            'information_schema.processlist p ON p.id = t.trx_mysql_thread_id '
            'WHERE p.db = %s AND t.trx_rows_modified > 0',
            (case.schema,),
        )
        return bool(found[0][0])

    _wait(uncommitted_insert, "the importer's uncommitted row")
    rows_during = _read_committed(case, 'SELECT COUNT(*) FROM import_process')
    recovered_during = _status(case, '--recover')
    recovered_in_the_hold = uncommitted_insert()

    process_id = _wait(
        lambda: case.importers()[0][0] if case.importers() else None, "the importer's row"
    )
    holder = case.lock_holder(process_id)
    status_after = _status(case)

    assert rows_during == [(0,)]
    assert recovered_in_the_hold
    assert recovered_during.splitlines()[0] == 'No importer is lost'
    assert holder is not None
    assert case.importers()[0][2] == 'running'
    importer_lines = status_after.splitlines()[2:]
    assert len(importer_lines) == 1
    assert importer_lines[0].startswith(f'{socket.gethostname()}:')


def _status(case: Case, *options: str) -> str:
    """Return what ``opus_import_all --status`` prints, with the options given."""
    finished = subprocess.run(  # nosec B603 - this interpreter and the pipeline's own module
        [str(build_run.THIS_PYTHON), '-m', 'opus_import.import_all', '--status', *options],
        cwd=fixture_layout.REPO_ROOT,
        env=build_run.run_environment(case.paths.config_file),
        capture_output=True,
        text=True,
        check=True,
    )
    return finished.stdout


def _read_committed(case: Case, statement: str) -> list[tuple[Any, ...]]:
    """Run a query at ``READ COMMITTED``, as the import's connections read."""
    connection = golden_io.connect(case.credentials, case.schema)
    try:
        cursor = connection.cursor()
        cursor.execute('SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED')
        cursor.execute(statement)
        return list(cursor.fetchall())
    finally:
        connection.close()
