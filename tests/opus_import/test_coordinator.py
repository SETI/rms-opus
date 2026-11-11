"""The coordinator's decisions, from readings of the registry, without a database.

How it decides the run is over, which importers it replaces and when it stops starting
them, what it prints and logs, how it survives a failed reading, and what ``--status``
shows. ``import_tests/test_coordinator.py`` runs it against MySQL.
"""

from __future__ import annotations

import datetime
import os
import signal
import time
from typing import Any

import pytest

from opus_import import coordinator as opus_coordinator
from opus_import import import_all
from opus_import.import_processes import BundleStatus, ProcessStatus, Snapshot

from .conftest import import_table

#: When the readings below were taken.
_NOW = datetime.datetime(2026, 11, 11, 12, 0, 0)


def _bundle(
    bundle_id: str,
    state: str,
    process_id: int | None = None,
    rows_done: int = 0,
    size: int = 100,
) -> BundleStatus:
    """Return a registry row, numbered from its id's letter (``A`` is 1)."""
    started = _NOW - datetime.timedelta(minutes=2) if state != 'pending' else None
    number = ord(bundle_id[0]) - ord('A') + 1
    return BundleStatus(number, bundle_id, state, size, rows_done, process_id, started, None)


def _process(process_id: int, *, alive: bool, idle_minutes: int = 0) -> ProcessStatus:
    """Return an importer's row."""
    return ProcessStatus(
        process_id,
        'host',
        1000 + process_id,
        f'/logs/importer_{process_id}.log',
        _NOW - datetime.timedelta(hours=1),
        _NOW - datetime.timedelta(minutes=idle_minutes),
        'running' if alive else 'exited',
        alive,
    )


class _Config:
    """A configuration with the default ``[import]`` table."""

    import_ = import_table()


def _coordinator(finishing: bool = True, workers: int = 1) -> opus_coordinator.Coordinator:
    """Return a coordinator that has started nothing, of `workers` workers divided among
    as many importers as allowed, up to two."""
    division = import_all.resolve_division(
        import_table(workers=workers, importers=2), None, 'auto', detected=8
    )
    coordinator = opus_coordinator.Coordinator(
        _Config(),  # type: ignore[arg-type]
        None,
        division,
        [],
        finishing=finishing,
    )
    coordinator.terminal = False
    return coordinator


def test_every_bundle_done_and_no_importer_alive_lets_it_finish() -> None:
    """The one reading after which the closing sequence runs."""
    snapshot = Snapshot((_bundle('A', 'done'), _bundle('B', 'done')), (_process(1, alive=False),))
    assert _coordinator()._settle(snapshot) == 0


def test_an_importer_alive_on_another_computer_is_waited_for() -> None:
    """A joined computer's importer is alive, between bundles: not over yet."""
    snapshot = Snapshot((_bundle('A', 'done', 2),), (_process(2, alive=True),))
    assert _coordinator()._settle(snapshot) is None


def test_a_lost_importers_bundle_is_waited_for_until_it_is_recovered() -> None:
    """Its importer's lock is free, so a recovery pass will return it: not over yet."""
    snapshot = Snapshot((_bundle('A', 'importing', 3),), (_process(3, alive=False),))
    assert _coordinator()._settle(snapshot) is None


def test_a_failed_bundle_stops_the_run_naming_its_importers_log(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Exit 1, the bundle named with the log of the importer that failed it."""
    snapshot = Snapshot(
        (_bundle('A', 'done'), _bundle('B', 'failed', 4)), (_process(4, alive=False),)
    )
    assert _coordinator()._settle(snapshot) == 1
    printed = capsys.readouterr().out
    assert "B (its importer's log: host:/logs/importer_4.log)" in printed
    assert 'A (' not in printed


def test_a_bundle_importing_outside_the_queue_stops_the_run(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A plain import's bundle has no importer to recover it from."""
    snapshot = Snapshot((_bundle('A', 'importing'),), ())
    assert _coordinator()._settle(snapshot) == 1
    assert 'importing outside the queue, with no importer: A' in capsys.readouterr().out


def test_pending_bundles_no_importer_here_claims_end_the_run_after_one_more_start(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Once nothing runs anywhere, the bundles taken as unclaimable are started for once
    more; if they are still pending after that, the run stops naming them."""
    coordinator = _coordinator()
    coordinator._starts_left = 5
    coordinator._unclaimable = frozenset({1})
    snapshot = Snapshot((_bundle('A', 'pending'),), ())

    assert coordinator._settle(snapshot) is None
    assert coordinator._unclaimable == frozenset()
    assert coordinator._settle(snapshot) == 1
    assert 'Bundles are pending that no importer started here claimed: A;' in (
        capsys.readouterr().out
    )


def test_the_table_shows_each_live_importer_and_marks_a_stall() -> None:
    """One line per importer alive, its bundle's progress, and STALLED past the limit."""
    snapshot = Snapshot(
        (
            _bundle('A', 'importing', 1, rows_done=40, size=100),
            _bundle('B', 'importing', 2, rows_done=5, size=1000),
            _bundle('C', 'done', 3),
        ),
        (
            _process(1, alive=True),
            _process(2, alive=True, idle_minutes=31),
            _process(3, alive=False),
        ),
    )
    lines = opus_coordinator.importer_lines(snapshot, _NOW, 30)
    assert lines[1:] == [
        'host:1001  A  40 of 100  0:02:00  0:00:00',
        'host:1002  B  5 of 1,000  0:02:00  0:31:00  STALLED',
    ]


def test_the_totals_line_labels_the_remaining_time_an_estimate() -> None:
    """Bundles by state, rows of the estimate, elapsed, and remaining."""
    snapshot = Snapshot(
        (
            _bundle('A', 'done', rows_done=100),
            _bundle('B', 'importing', 1, rows_done=50),
            _bundle('C', 'pending'),
            _bundle('D', 'failed', 2),
        ),
        (),
    )
    assert opus_coordinator.totals_line(snapshot, 3725, 60) == (
        'Bundles: 1 done, 1 importing, 1 pending, 1 failed; rows 150 of an estimated 400; '
        'elapsed 1:02:05; remaining about 0:01:00 (an estimate from the observed row rate)'
    )
    assert 'remaining not yet estimated' in opus_coordinator.totals_line(snapshot, 1, None)


class _Process:
    """A started importer that has exited with a given status."""

    _next_pid = 500

    def __init__(self, code: int | None) -> None:
        _Process._next_pid += 1
        self.pid = _Process._next_pid
        self.code = code

    def poll(self) -> int | None:
        return self.code


def test_a_lost_importer_is_replaced_while_bundles_are_pending(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Its exit, and a pending bundle, start one importer with the same workers; the
    importer still running is busy with its own bundle."""
    coordinator = _coordinator(workers=3)
    coordinator._starts_left = 5
    started = _record_starts(monkeypatch)
    dead = opus_coordinator._Importer(_Process(-9), 2)  # type: ignore[arg-type]
    alive = opus_coordinator._Importer(_Process(None), 1, process_id=7)  # type: ignore[arg-type]
    coordinator._own = [dead, alive]
    snapshot = Snapshot((_bundle('A', 'pending'), _bundle('B', 'importing', 7)), ())
    _patch_reading(monkeypatch, snapshot)

    assert coordinator._pass(_FakeContext()) is None  # type: ignore[arg-type]
    assert started == [['--join', '--workers', '2']]


def test_an_interrupted_coordinator_starts_nothing_and_exits_unfinished(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """After an interrupt no importer is replaced, and once its own exit the run is over."""
    coordinator = _coordinator()
    coordinator._starts_left = 5
    coordinator.interrupts = 1
    monkeypatch.setattr(
        opus_coordinator, 'start_importer', lambda arguments: pytest.fail('started')
    )
    coordinator._own = [opus_coordinator._Importer(_Process(1), 1)]  # type: ignore[arg-type]
    _patch_reading(monkeypatch, Snapshot((_bundle('A', 'pending'),), ()))

    assert coordinator._pass(_FakeContext()) == 1  # type: ignore[arg-type]


def test_an_interrupt_while_importers_start_reaches_the_one_starting_and_stops_the_rest(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An interrupt that lands while an importer is being started is passed on to it once
    it is registered, and no importer after it is started."""
    coordinator = _coordinator(workers=2)
    coordinator._starts_left = 5
    signalled: list[tuple[int, int]] = []
    monkeypatch.setattr(os, 'kill', lambda pid, signum: signalled.append((pid, signum)))
    started: list[_Process] = []

    def start(arguments: list[str]) -> _Process:
        started.append(_Process(None))
        coordinator._interrupt(signal.SIGINT, None)
        return started[-1]

    monkeypatch.setattr(opus_coordinator, 'start_importer', start)
    for workers in coordinator.division.per_importer:
        coordinator._start(workers)

    assert len(started) == 1
    assert signalled == [(started[0].pid, signal.SIGINT)]


def _record_starts(monkeypatch: pytest.MonkeyPatch) -> list[list[str]]:
    """Make each importer started a running stand-in, and return their command lines."""
    started: list[list[str]] = []

    def start(arguments: list[str]) -> _Process:
        started.append(arguments)
        return _Process(None)

    monkeypatch.setattr(opus_coordinator, 'start_importer', start)
    return started


def _exited(code: int, pending_at_start: set[int], **fields: Any) -> opus_coordinator._Importer:
    """Return an importer of one worker that exited with `code`, started while the
    bundles numbered `pending_at_start` were pending."""
    return opus_coordinator._Importer(
        _Process(code),  # type: ignore[arg-type]
        1,
        pending_at_start=frozenset(pending_at_start),
        **fields,
    )


def test_a_join_does_not_replace_importers_that_found_nothing_they_may_claim(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Bundles pending all the life of an importer that exited cleanly are others' to
    claim (``--sets``), so a ``--join`` whose importers have exited is over."""
    coordinator = _coordinator(finishing=False, workers=2)
    coordinator._starts_left = 50
    started = _record_starts(monkeypatch)
    coordinator._own = [_exited(0, {1, 2}), _exited(0, {1, 2, 3}, claimed=True)]
    _patch_reading(monkeypatch, Snapshot((_bundle('A', 'pending'), _bundle('B', 'pending')), ()))

    assert coordinator._pass(_FakeContext()) == 0  # type: ignore[arg-type]
    assert started == []


def test_a_bundle_returned_to_the_queue_since_is_started_for_once(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A bundle that became pending after the importers started may be theirs: one
    importer is started for it, and none more while that one has not claimed."""
    coordinator = _coordinator(finishing=False, workers=2)
    coordinator._starts_left = 50
    started = _record_starts(monkeypatch)
    coordinator._own = [_exited(0, {1}), _exited(0, {1})]
    _patch_reading(monkeypatch, Snapshot((_bundle('A', 'pending'), _bundle('C', 'pending')), ()))

    assert coordinator._pass(_FakeContext()) is None  # type: ignore[arg-type]
    assert coordinator._pass(_FakeContext()) is None  # type: ignore[arg-type]
    assert started == [['--join', '--workers', '1']]


def test_importers_that_fail_before_claiming_stop_being_started(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """After `FAILED_STARTS_ALLOWED` in a row, nothing more is started, which is logged."""
    coordinator = _coordinator(workers=2)
    coordinator._starts_left = 50
    started = _record_starts(monkeypatch)
    coordinator._own = [_exited(1, set()) for _ in range(opus_coordinator.FAILED_STARTS_ALLOWED)]
    logged = _record_log(coordinator)
    _patch_reading(monkeypatch, Snapshot((_bundle('A', 'pending'),), ()))

    coordinator._pass(_FakeContext())  # type: ignore[arg-type]

    assert started == []
    assert coordinator._starts_left == 0
    assert (
        'error',
        f'{opus_coordinator.FAILED_STARTS_ALLOWED} importers in a row exited with failure before '
        'claiming a bundle, so no more are started',
    ) in logged


def test_an_importer_that_claimed_resets_the_failed_starts(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A failure after a claim is a lost importer, replaced however many there were."""
    coordinator = _coordinator(workers=2)
    coordinator._starts_left = 50
    started = _record_starts(monkeypatch)
    coordinator._failed_starts = opus_coordinator.FAILED_STARTS_ALLOWED - 1
    coordinator._own = [_exited(-9, set(), claimed=True)]
    _patch_reading(monkeypatch, Snapshot((_bundle('A', 'pending'),), ()))

    coordinator._pass(_FakeContext())  # type: ignore[arg-type]

    assert coordinator._failed_starts == 0
    assert started == [['--join', '--workers', '1']]


def test_an_importer_that_claimed_and_died_since_the_last_reading_is_not_a_failed_start(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The pass's recovery returns the bundle it held to the queue, but the reading before
    the recovery still shows its claim: it is a lost importer, replaced, not a failed
    start."""
    coordinator = _coordinator(workers=2)
    coordinator._starts_left = 50
    coordinator._failed_starts = opus_coordinator.FAILED_STARTS_ALLOWED - 1
    started = _record_starts(monkeypatch)
    coordinator._own = [_exited(-9, set(), process_id=5)]
    _patch_recovery(
        monkeypatch,
        Snapshot((_bundle('A', 'importing', 5),), (_process(5, alive=False),)),
        Snapshot((_bundle('A', 'pending'),), (_process(5, alive=False),)),
    )

    assert coordinator._pass(_FakeContext()) is None  # type: ignore[arg-type]
    assert coordinator._failed_starts == 0
    assert started == [['--join', '--workers', '1']]


def test_a_bundle_recovered_since_the_last_reading_is_not_taken_as_unclaimable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A bundle pending when a clean importer started, then claimed by another importer
    that died, is pending again after the pass's recovery; it was not pending throughout,
    so it is started for."""
    coordinator = _coordinator(finishing=False, workers=2)
    coordinator._starts_left = 50
    started = _record_starts(monkeypatch)
    coordinator._own = [_exited(0, {1})]
    _patch_recovery(
        monkeypatch,
        Snapshot((_bundle('A', 'importing', 9),), (_process(9, alive=False),)),
        Snapshot((_bundle('A', 'pending'),), (_process(9, alive=False),)),
    )

    assert coordinator._pass(_FakeContext()) is None  # type: ignore[arg-type]
    assert coordinator._unclaimable == frozenset()
    assert started == [['--join', '--workers', '1']]


def test_the_end_of_a_run_on_a_terminal_is_printed_and_every_event_logged(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """The failed bundles, named after the table's last redraw, still reach the screen."""
    from opus_import import import_processes

    coordinator = _coordinator()
    coordinator.terminal = True
    logged = _record_log(coordinator)
    monkeypatch.setattr(opus_coordinator.Coordinator, '_context', lambda self: _FakeContext())
    monkeypatch.setattr(import_processes, 'create_process_table', lambda db: None)
    monkeypatch.setattr(opus_coordinator, 'start_importer', lambda arguments: _Process(0))
    _patch_reading(monkeypatch, Snapshot((_bundle('B', 'failed', 4),), (_process(4, alive=False),)))

    assert coordinator.run() == 1

    printed = capsys.readouterr().out.rsplit(opus_coordinator._CLEAR_SCREEN, 1)[1]
    assert "B (its importer's log: host:/logs/importer_4.log)" in printed.split('\n', 2)[2:][0]
    assert [message for level, message in logged if level == 'warning'] == [
        'Bundles failed, so the schema is not finalized; after the fix, '
        '"opus_import_all --requeue <bundle>" and a rerun import them:\n'
        "  B (its importer's log: host:/logs/importer_4.log)"
    ]
    assert ('info', f'importer {_Process._next_pid} exited with status 0') in logged


def test_a_failed_reading_is_logged_and_the_next_pass_reconnects(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A transient failure costs a pass, not the run."""
    from opus_import import import_processes, importdb

    coordinator = _coordinator()
    logged = _record_log(coordinator)
    ctx = _FakeContext()
    readings: list[object] = []

    def read(db: object) -> Snapshot:
        readings.append(db)
        if len(readings) == 1:
            raise importdb.ImportDBError('Lost connection to MySQL server')
        return Snapshot((_bundle('A', 'importing', 3),), (_process(3, alive=True),))

    _patch_reading(monkeypatch, Snapshot((), ()))
    monkeypatch.setattr(import_processes, 'read_snapshot', read)
    reopened = _FakeDB()
    monkeypatch.setattr(opus_coordinator, 'open_target_db', lambda *args, **kwargs: reopened)

    assert coordinator._pass(ctx) is None  # type: ignore[arg-type]
    assert ctx.db is None
    assert ('warning', 'The database could not be read: Lost connection to MySQL server') in (
        logged
    )
    assert coordinator._pass(ctx) is None  # type: ignore[arg-type]
    assert readings[1] is reopened
    assert coordinator._failing_since is None


def test_readings_failing_for_the_outage_limit_stop_the_coordinator(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A persistent failure ends the run, saying so, rather than being retried for ever."""
    from opus_import import importdb

    coordinator = _coordinator()
    logged = _record_log(coordinator)
    coordinator._failing_since = time.monotonic() - opus_coordinator.DATABASE_OUTAGE_SECONDS

    def refuse(*args: Any, **kwargs: Any) -> None:
        raise importdb.ImportDBError("Can't connect to MySQL server")

    monkeypatch.setattr(opus_coordinator, 'open_target_db', refuse)
    ctx = _FakeContext()
    ctx.db = None

    assert coordinator._pass(ctx) == 1  # type: ignore[arg-type]
    (stopped,) = [message for level, message in logged if level == 'error']
    assert stopped.startswith('The database has not been readable for 0:05:00')


class _FakeDB:
    """A connection that only closes."""

    def close(self) -> None:
        """Close nothing."""


class _FakeContext:
    """A context whose database is never asked anything the patches below do not answer."""

    def __init__(self) -> None:
        self.db: _FakeDB | None = _FakeDB()


def _record_log(coordinator: opus_coordinator.Coordinator) -> list[tuple[str, str]]:
    """Give the coordinator a logger recording ``(level, message)`` pairs, and return them."""
    logged: list[tuple[str, str]] = []

    class _Logger:
        def log(self, level: str, message: str) -> None:
            logged.append((level, message))

    coordinator.logger = _Logger()
    return logged


def _patch_reading(monkeypatch: pytest.MonkeyPatch, snapshot: Snapshot) -> None:
    """Make every reading of the registry return `snapshot`, and recover nothing."""
    from opus_import import import_processes
    from opus_import.steps import do_recover

    monkeypatch.setattr(import_processes, 'read_snapshot', lambda db: snapshot)
    monkeypatch.setattr(do_recover, 'recover_lost_importers', lambda ctx: [])


def _patch_recovery(monkeypatch: pytest.MonkeyPatch, before: Snapshot, after: Snapshot) -> None:
    """Make readings return `before` until a recovery returns a bundle, and `after` from
    then on."""
    from opus_import import import_processes
    from opus_import.steps import do_recover

    recovered: list[str] = []

    def recover(ctx: object) -> list[str]:
        recovered.append('A returned to the queue')
        return recovered[-1:]

    monkeypatch.setattr(
        import_processes, 'read_snapshot', lambda db: after if recovered else before
    )
    monkeypatch.setattr(do_recover, 'recover_lost_importers', recover)


class _CachingDB:
    """A connection whose table names are cached until forgotten, holding one registry
    row and no importer."""

    db_schema = 'opus_test'

    def __init__(self) -> None:
        self.cached: set[str] = set()
        self.closed = False

    def forget_table_names(self) -> None:
        """Read the table names again: the registry has been created since."""
        self.cached = {'import_bundle'}

    def table_exists(self, table_name: str) -> bool:
        return table_name in self.cached

    def quote_identifier(self, name: str) -> str:
        return f'`{name}`'

    def read_rows(self, table_name: str, columns: Any, where: str) -> list[tuple[Any, ...]]:
        assert table_name == 'import_bundle'
        return [(1, 'A', 'pending', 100, 0, None, None, None)]

    def close(self) -> None:
        self.closed = True


def test_a_reading_sees_tables_created_after_the_connection_opened() -> None:
    """The registry, created by another process since, is read rather than taken as
    absent from the names the connection cached."""
    from opus_import import import_processes

    snapshot = import_processes.read_snapshot(_CachingDB())  # type: ignore[arg-type]
    assert [bundle.bundle_id for bundle in snapshot.bundles] == ['A']


@pytest.mark.parametrize('watch', [True, False], ids=['watch', 'once'])
def test_status_reports_a_failed_reading_and_a_watch_goes_on(
    watch: bool, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """A reading that fails (the tables dropped by a rerun) is reported without a
    traceback; a watch reads again on a new connection, a single status exits 1."""
    from opus_import import import_processes, importdb

    opened: list[_CachingDB] = []

    def open_db(*args: Any, **kwargs: Any) -> _CachingDB:
        opened.append(_CachingDB())
        return opened[-1]

    def read(db: _CachingDB) -> Snapshot:
        if len(opened) == 1:
            raise importdb.ImportDBError("Table 'opus_test.import_bundle' doesn't exist")
        return Snapshot((_bundle('A', 'pending'),), ())

    def sleep(seconds: float) -> None:
        if len(opened) == 2:
            raise KeyboardInterrupt

    monkeypatch.setattr(opus_coordinator, 'open_target_db', open_db)
    monkeypatch.setattr(import_processes, 'read_snapshot', read)
    monkeypatch.setattr(time, 'sleep', sleep)

    status = opus_coordinator.show_status(_Config(), None, watch=watch, recover=False)  # type: ignore[arg-type]

    captured = capsys.readouterr()
    assert "the schema could not be read: Table 'opus_test.import_bundle'" in captured.err
    assert opened[0].closed
    assert status == (0 if watch else 1)
    assert ('Bundles: 0 done, 0 importing, 1 pending' in captured.out) is watch
