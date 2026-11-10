"""A pool of workers imports exactly what one process does, and dies with the import.

The first case imports the same bundles with one worker and with three into two schemas
and compares every table and every log. The second makes one worker task fail after the
rows before it were loaded, and checks that the failed index leaves no row behind. The
third starts an import whose workers stall, kills the import's process, and checks that
no worker and no database session of the run outlives it.
"""

from __future__ import annotations

import os
import re
import signal
import subprocess  # nosec B404
import sys
import time
from typing import TYPE_CHECKING

import pytest

from import_tests.tools import build_run, fixture_layout, golden_io
from opus_import.import_fault import IMPORT_FAULT_ENV_VAR
from opus_import.steps.do_import_pool import FAIL_FAULT_SITE, STALL_FAULT_SITE

if TYPE_CHECKING:
    from pathlib import Path

    from import_tests.tools.golden_io import DatabaseCredentials

#: The bundles both runs import, in one invocation: a Cassini VIMS index, whose rows
#: produce two observations each, with moon, Saturn and ring summaries, and the largest
#: index the fixture has.
BUNDLES = ['COVIMS_0048', 'VGISS_6109']

#: The rows one worker task covers in both runs. The fixture's indexes are small, so a
#: small task is what splits each across several workers.
WORKER_ROWS = 5

#: The leading timestamp of a log line, which is all two runs' logs may differ in.
_TIMESTAMP = re.compile(r'^\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}(\.\d+)?\s*')

#: A section's elapsed time, which differs between any two runs.
_ELAPSED = re.compile(r'\d+:\d{2}:\d{2}(\.\d+)?')

#: The line saying how many workers the run uses, the one line that differs by design.
_PARALLELISM = 'Parallelism: '

#: How long the killed import's workers and session have to disappear.
DEATH_SECONDS = 5


def _import(
    root: Path, credentials: DatabaseCredentials, created: list[str], workers: int, name: str
) -> build_run.ImportRun:
    """Import `BUNDLES` with a given number of workers into a schema of its own."""
    schema = fixture_layout.schema_name(os.getpid(), f'parallel_{name}')
    created.append(schema)
    run = build_run.perform_run(
        root,
        schema,
        credentials,
        bundle_groups=[BUNDLES],
        extra_import={'workers': workers, 'worker_rows': WORKER_ROWS},
        finalize=False,
    )
    for step in run.steps:
        assert step.returncode == 0, step.stderr
    return run


def _log_text(path: Path, run: build_run.ImportRun) -> list[str]:
    """Return a log's lines with what two runs may differ in removed or named generically.

    Parameters:
        path: The log.
        run: The run that wrote it, whose schema and directory its lines name.

    Returns:
        The lines, without timestamps, elapsed times, the run's own schema and directory,
        and the line saying how many workers it used.
    """
    lines = []
    for line in path.read_text(encoding='utf-8').splitlines():
        if _PARALLELISM in line:
            continue
        line = _ELAPSED.sub('<elapsed>', _TIMESTAMP.sub('', line))
        line = line.replace(str(run.paths.root), '<root>').replace(run.schema, '<schema>')
        lines.append(line)
    return lines


def test_three_workers_import_what_one_does(
    tmp_path_factory: pytest.TempPathFactory,
    db_credentials: DatabaseCredentials,
    created_schemas: list[str],
) -> None:
    """Every table, ids included, and every log, timestamps aside, are the same."""
    serial = _import(
        tmp_path_factory.mktemp('parallel_one'), db_credentials, created_schemas, 1, 'one'
    )
    pooled = _import(
        tmp_path_factory.mktemp('parallel_three'), db_credentials, created_schemas, 3, 'three'
    )

    tables = golden_io.list_tables(db_credentials, serial.schema)
    assert golden_io.list_tables(db_credentials, pooled.schema) == tables
    differences = [
        table
        for table in tables
        if golden_io.serialize_table(db_credentials, serial.schema, table)
        != golden_io.serialize_table(db_credentials, pooled.schema, table)
    ]
    assert differences == []

    # Each invocation's log is named after the second it started in, so two invocations
    # starting in one second share a file; the lines are compared in order across all of
    # a run's logs rather than file by file.
    serial_lines = [line for log in serial.paths.import_logs for line in _log_text(log, serial)]
    pooled_lines = [line for log in pooled.paths.import_logs for line in _log_text(log, pooled)]
    assert serial_lines
    assert pooled_lines == serial_lines
    pooled_logs = pooled.paths.import_logs
    for name in (build_run.ERRORS_LOG, build_run.WARNINGS_LOG):
        serial_path, pooled_path = serial.paths.log_dir / name, pooled.paths.log_dir / name
        assert serial_path.exists() == pooled_path.exists()
        if serial_path.exists():
            assert _log_text(pooled_path, pooled) == _log_text(serial_path, serial)

    parallelism = [
        line
        for line in pooled_logs[-1].read_text(encoding='utf-8').splitlines()
        if _PARALLELISM in line
    ]
    assert parallelism
    assert parallelism[0].endswith('workers 3, index_workers 1')


#: The index row whose task fails, late enough that the rows before it were loaded.
FAILING_ROW = 12


def test_a_failed_index_leaves_none_of_its_rows(
    tmp_path_factory: pytest.TempPathFactory,
    db_credentials: DatabaseCredentials,
    created_schemas: list[str],
) -> None:
    """The rows loaded before a worker failed are taken back, so no mult id dangles."""
    paths = build_run.RunPaths.under(tmp_path_factory.mktemp('parallel_fail').resolve())
    build_run.build_holdings_tree(paths)
    schema = fixture_layout.schema_name(os.getpid(), 'parallel_fail')
    created_schemas.append(schema)
    build_run.write_opus_config(
        paths,
        schema,
        db_credentials,
        extra_import={'workers': 3, 'worker_rows': 2, 'transaction_rows': 2},
    )
    environment = build_run.run_environment(paths.config_file)
    environment[IMPORT_FAULT_ENV_VAR] = f'{FAIL_FAULT_SITE}:{FAILING_ROW}'
    finished = subprocess.run(  # nosec B603 - this interpreter and a fixed program
        [sys.executable, '-m', 'opus_import', *build_run.IMPORT_ARGS, 'VGISS_6109'],
        cwd=fixture_layout.REPO_ROOT,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )
    assert finished.returncode != 0
    for table in ('obs_general', 'obs_pds', 'obs_files'):
        rows = golden_io.query(db_credentials, schema, f'SELECT COUNT(*) FROM {table}', [])  # nosec B608 - a fixed table name
        assert rows[0][0] == 0, table


def _children(pid: int) -> list[int]:
    """Return the live processes whose parent is `pid`, read from ``/proc``."""
    found = []
    for entry in os.listdir('/proc'):
        if not entry.isdigit():
            continue
        try:
            with open(f'/proc/{entry}/stat', encoding='utf-8') as stat:
                fields = stat.read().rsplit(')', 1)[1].split()
        except OSError:
            continue
        state, parent = fields[0], int(fields[1])
        if parent == pid and state != 'Z':
            found.append(int(entry))
    return found


def _alive(pid: int) -> bool:
    """Return whether a process exists and is not a zombie."""
    try:
        with open(f'/proc/{pid}/stat', encoding='utf-8') as stat:
            return stat.read().rsplit(')', 1)[1].split()[0] != 'Z'
    except OSError:
        return False


def _sessions(credentials: DatabaseCredentials, schema: str) -> int:
    """Return how many server sessions are using a schema."""
    rows = golden_io.query(
        credentials,
        None,
        'SELECT COUNT(*) FROM information_schema.PROCESSLIST WHERE DB = %s',
        [schema],
    )
    return int(rows[0][0])


@pytest.mark.skipif(
    not sys.platform.startswith('linux'),
    reason='reads /proc, and only Linux kills orphaned workers',
)
def test_killing_the_import_leaves_no_worker_and_no_session(
    tmp_path_factory: pytest.TempPathFactory,
    db_credentials: DatabaseCredentials,
    created_schemas: list[str],
) -> None:
    """The kernel kills each worker with its parent, and no session of the run survives."""
    paths = build_run.RunPaths.under(tmp_path_factory.mktemp('parallel_kill').resolve())
    build_run.build_holdings_tree(paths)
    schema = fixture_layout.schema_name(os.getpid(), 'parallel_kill')
    created_schemas.append(schema)
    build_run.write_opus_config(
        paths, schema, db_credentials, extra_import={'workers': 3, 'worker_rows': WORKER_ROWS}
    )
    environment = build_run.run_environment(paths.config_file)
    environment[IMPORT_FAULT_ENV_VAR] = f'{STALL_FAULT_SITE}:600'
    process = subprocess.Popen(  # nosec B603 - this interpreter and a fixed program
        [sys.executable, '-m', 'opus_import', *build_run.IMPORT_ARGS, 'VGISS_6109'],
        cwd=fixture_layout.REPO_ROOT,
        env=environment,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    workers: list[int] = []
    try:
        deadline = time.monotonic() + 120
        while len(workers) < 3 and process.poll() is None and time.monotonic() < deadline:
            time.sleep(0.2)
            workers = _children(process.pid)
        assert len(workers) == 3, f'the import made {len(workers)} workers before the deadline'
        assert _sessions(db_credentials, schema) >= 1

        os.kill(process.pid, signal.SIGKILL)
        process.wait()
        deadline = time.monotonic() + DEATH_SECONDS
        while any(_alive(pid) for pid in workers) and time.monotonic() < deadline:
            time.sleep(0.1)
        assert [pid for pid in workers if _alive(pid)] == []
        while _sessions(db_credentials, schema) > 0 and time.monotonic() < deadline:
            time.sleep(0.1)
        assert _sessions(db_credentials, schema) == 0
    finally:
        for pid in [process.pid, *workers]:
            if _alive(pid):
                os.kill(pid, signal.SIGKILL)
