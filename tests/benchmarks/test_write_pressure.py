"""What an import run records about the server's writes, and the bulk-load path it took."""

from pathlib import Path

import MySQLdb
import pytest

from benchmarks import bench_import
from benchmarks.monitor import InvocationMonitor, _MemorySampler, checkpoint_age
from benchmarks.results import make_label
from benchmarks.sides import Spelling
from import_tests.tools.build_run import StepResult
from opus_import.importdb import mysql


class _FakeCursor:
    """A cursor answering every query with fixed rows."""

    def __init__(self, rows: list[tuple[str, str]]) -> None:
        self.rows = rows
        self.closed = False

    def execute(self, statement: str) -> None:
        assert 'Innodb_redo_log_current_lsn' in statement

    def fetchall(self) -> list[tuple[str, str]]:
        return self.rows

    def close(self) -> None:
        self.closed = True


class _FakeConnection:
    """A connection whose one cursor answers with fixed rows."""

    def __init__(self, rows: list[tuple[str, str]]) -> None:
        self.cursor_made = _FakeCursor(rows)
        self.closed = False

    def cursor(self) -> _FakeCursor:
        return self.cursor_made

    def close(self) -> None:
        self.closed = True


def test_checkpoint_age_is_the_redo_not_yet_checkpointed() -> None:
    """The age is the current LSN less the checkpoint LSN."""
    connection = _FakeConnection(
        [('Innodb_redo_log_checkpoint_lsn', '1000'), ('Innodb_redo_log_current_lsn', '5096')]
    )

    assert checkpoint_age(connection) == 4096
    assert connection.cursor_made.closed


def test_checkpoint_age_is_none_from_a_server_that_does_not_report_it() -> None:
    """A server before 8.0.30 reports neither number, which is no sample, not zero."""
    assert checkpoint_age(_FakeConnection([])) is None


def test_the_sampler_keeps_the_largest_age() -> None:
    """Missing and failed samples are skipped, and the peak is what remains."""
    answers: list[int | Exception | None] = [
        100,
        None,
        MySQLdb.OperationalError(2013, 'lost'),
        300,
        200,
    ]

    def probe() -> int | None:
        answer = answers.pop(0)
        if isinstance(answer, Exception):
            raise answer
        return answer

    sampler = _MemorySampler(set, probe)
    for _ in range(5):
        sampler._sample_server()

    assert sampler.peak_checkpoint_age_bytes == 300


def test_a_sampler_without_a_probe_records_no_age() -> None:
    """Memory alone is sampled when no server is given."""
    sampler = _MemorySampler(set)
    sampler._sample_server()

    assert sampler.peak_checkpoint_age_bytes is None


def test_the_monitor_closes_each_invocation_s_connection(monkeypatch: pytest.MonkeyPatch) -> None:
    """One connection per invocation, closed when the invocation finishes."""
    monkeypatch.setattr(_MemorySampler, '_sample', lambda self: None)
    connections: list[_FakeConnection] = []

    def connect() -> _FakeConnection:
        connections.append(_FakeConnection([]))
        return connections[-1]

    monitor = InvocationMonitor(
        server=None,  # type: ignore[arg-type]  # never reached: no bundle import
        schema='bench_x',
        spelling=Spelling.from_help('--do-all-import --drop-cache-tables --validate-perm'),
        expand=lambda groups: [[group] for group in groups],
        timing_file=None,
        excluded_pids=set,
        status_connection=connect,
    )
    for _ in range(2):
        monitor.step_started(['--validate-perm'])
        monitor.step_finished(StepResult(('--validate-perm',), 0, '', ''))

    assert [connection.closed for connection in connections] == [True, True]
    assert [record.peak_checkpoint_age_bytes for record in monitor.records] == [None, None]


def _log_line(message: str) -> str:
    return f'2026-11-06 12:00:00.123456 | pds.opus_import.main |-| INFO | {message}'


def test_bulk_load_paths_reads_each_path_once_in_order(tmp_path: Path) -> None:
    """Every invocation names its path; a refusal partway names a second one."""
    first = tmp_path / 'opus_import_2026-11-06T22-13-27.log'
    first.write_text(
        _log_line('Connected to MySQL server "localhost" as "opus"')
        + '\n'
        + _log_line('  Bulk load path: LOAD DATA LOCAL INFILE')
        + '\n',
        encoding='utf-8',
    )
    second = tmp_path / 'opus_import_2026-11-06T22-13-28.log'
    second.write_text(
        _log_line('  Bulk load path: LOAD DATA LOCAL INFILE')
        + '\n'
        + _log_line('  Bulk load path: insert_rows packets (the server refused a file)')
        + '\n',
        encoding='utf-8',
    )
    # The debug log names the paths too, and is not read.
    (tmp_path / 'opus_import_debug_2026-11-06T22-13-27.log').write_text(
        _log_line('  Bulk load path: something else') + '\n', encoding='utf-8'
    )

    assert bench_import.bulk_load_paths(tmp_path) == [
        mysql.BULK_LOAD_PATH_FILE,
        mysql.BULK_LOAD_PATH_INSERT,
    ]


def test_bulk_load_paths_is_empty_for_a_side_that_names_none(tmp_path: Path) -> None:
    """A side from before the bulk load names no path, which the default then stands for."""
    (tmp_path / 'opus_import_2026-11-06T22-13-27.log').write_text(
        _log_line('Connected') + '\n', encoding='utf-8'
    )

    assert bench_import.bulk_load_paths(tmp_path) == []
    assert bench_import.bulk_load_paths(tmp_path / 'missing') == []


def test_the_harness_reads_the_line_the_import_writes() -> None:
    """The harness's copy of the prefix, and its default path, match the import's."""
    assert bench_import.BULK_LOAD_PATH_PREFIX == mysql.BULK_LOAD_PATH_PREFIX
    assert bench_import.DEFAULT_BULK_LOAD_PATH == mysql.BULK_LOAD_PATH_INSERT


def test_a_status_connection_can_bound_its_reads(monkeypatch: pytest.MonkeyPatch) -> None:
    """The sampler's probe must not stall the memory samples on its thread."""
    from benchmarks import bench_server

    seen: list[dict[str, object]] = []
    monkeypatch.setattr(MySQLdb, 'connect', lambda **kwargs: seen.append(kwargs))
    server = bench_server.MysqlServer.__new__(bench_server.MysqlServer)
    server.config = type('Config', (), {'socket': Path('/tmp/s')})()
    server.connect(read_timeout=bench_import.STATUS_READ_TIMEOUT_S)
    server.connect()
    assert seen[0]['read_timeout'] == bench_import.STATUS_READ_TIMEOUT_S
    assert 'read_timeout' not in seen[1]


def _run_naming(paths: list[str] | None) -> dict[str, object]:
    """Return a run whose details name `paths`, or record none when None."""
    return {'details': {} if paths is None else {'bulk_load_paths': paths}}


def test_the_summary_names_every_path_any_run_took() -> None:
    """A session whose runs differ shows both paths, in the order first taken."""
    file_path = mysql.BULK_LOAD_PATH_FILE
    runs = [_run_naming([file_path]), _run_naming([file_path]), _run_naming([])]
    assert bench_import.summarize_bulk_load_paths(runs) == (
        f'{file_path}, {bench_import.DEFAULT_BULK_LOAD_PATH}'
    )


def test_a_run_naming_no_path_counts_as_the_default() -> None:
    """A side whose import names none took the packets path."""
    assert bench_import.summarize_bulk_load_paths([_run_naming([])]) == (
        bench_import.DEFAULT_BULK_LOAD_PATH
    )


def test_a_run_recording_no_paths_adds_nothing() -> None:
    """A run that imported nothing says nothing about the path."""
    runs = [_run_naming(None), _run_naming([mysql.BULK_LOAD_PATH_FILE])]
    assert bench_import.summarize_bulk_load_paths(runs) == mysql.BULK_LOAD_PATH_FILE
    assert bench_import.summarize_bulk_load_paths([_run_naming(None)]) == (
        bench_import.DEFAULT_BULK_LOAD_PATH
    )


def test_a_run_added_to_a_file_keeps_the_paths_its_runs_took(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A reuse or finalize-only run, which names no path, leaves the file's summary intact."""
    label = make_label(pr='PR-04', side='after', scale='fixture', session='a', date='2026-11-07')
    monkeypatch.setattr(bench_import, 'RESULTS_DIR', tmp_path)
    (tmp_path / label.file_name).write_text('{}', encoding='utf-8')
    monkeypatch.setattr(
        bench_import,
        'load_result',
        lambda path: {'runs': [_run_naming([mysql.BULK_LOAD_PATH_FILE])]},
    )
    reuse = {'details': {'reused_schema': 's', 'schema': 's'}}
    assert bench_import.file_bulk_load_path(label, [reuse]) == mysql.BULK_LOAD_PATH_FILE


def test_a_first_run_in_a_new_file_is_summarized_alone(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """With no file yet, only the new runs count."""
    label = make_label(pr='PR-04', side='after', scale='fixture', session='a', date='2026-11-07')
    monkeypatch.setattr(bench_import, 'RESULTS_DIR', tmp_path)
    assert bench_import.file_bulk_load_path(label, [_run_naming([])]) == (
        bench_import.DEFAULT_BULK_LOAD_PATH
    )
