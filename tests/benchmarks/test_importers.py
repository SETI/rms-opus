"""The import benchmark's runs with several queue importers: the division of the workers
total, the merging of the importers' timings, and the arguments it refuses."""

import json
import signal
import subprocess
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest

from benchmarks import bench_import
from benchmarks.bench_server import MysqlServer
from benchmarks.import_scenarios import ImportScenario
from benchmarks.results import make_label
from benchmarks.sides import Side, Spelling


@pytest.mark.parametrize(
    ('total', 'importers', 'shares'),
    [(8, 1, [8]), (8, 2, [4, 4]), (8, 4, [2, 2, 2, 2]), (1, 1, [1])],
    ids=['one', 'two', 'four', 'the-default-alone'],
)
def test_the_workers_total_is_divided_evenly(total: int, importers: int, shares: list[int]) -> None:
    """Together the importers use exactly the total asked for."""
    assert bench_import.divide_workers(total, importers) == shares


@pytest.mark.parametrize(
    ('total', 'importers', 'message'),
    [
        (6, 4, 'cannot divide 6 workers evenly'),
        (1, 2, 'cannot divide 1 workers evenly'),
        ('max', 2, "not 'max'"),
        (True, 1, 'not True'),
    ],
    ids=['uneven', 'default-split', 'max', 'boolean'],
)
def test_a_total_that_does_not_divide_is_refused(
    total: object, importers: int, message: str
) -> None:
    """A rounding rule would make the importers' total differ from the one-process run's."""
    with pytest.raises(ValueError, match=message):
        bench_import.divide_workers(total, importers)


def test_the_importers_timings_merge_to_their_per_bundle_steps(tmp_path: Path) -> None:
    """Each bundle's steps come from the importer that took it; the overlapping ones go."""
    first, second, absent = tmp_path / 'a.json', tmp_path / 'b.json', tmp_path / 'c.json'
    first.write_text(
        json.dumps({'import': 9.0, 'import_bundle:A': 4.0, 'delete_bundle:A': 0.5, 'total': 10}),
        encoding='utf-8',
    )
    second.write_text(json.dumps({'import': 7.0, 'import_bundle:B': 6.0}), encoding='utf-8')

    merged = bench_import.merged_bundle_timings([first, second, absent])

    assert merged == {'import_bundle:A': 4.0, 'delete_bundle:A': 0.5, 'import_bundle:B': 6.0}


def _argv(*extra: str) -> list[str]:
    """Return a fixture-scale command line with the given options added."""
    return [
        '--scale', 'fixture', '--side', 'after', '--pr', 'PR-16', '--session', 'a',
        '--python', 'python', '--repo-root', '.', *extra,
    ]  # fmt: skip


def test_importers_divide_the_workers_key_and_keep_the_other_keys() -> None:
    """``transaction_rows`` and the other keys go to every importer as given."""
    args = bench_import._parse_arguments(
        _argv(
            '--importers', '4', '--import-key', 'workers=8', '--import-key', 'transaction_rows=1000'
        )
    )
    assert args.worker_shares == [2, 2, 2, 2]
    assert args.import_keys == {'workers': 8, 'transaction_rows': 1000}


@pytest.mark.parametrize(
    ('extra', 'message'),
    [
        (['--importers', '0'], '--importers takes a count of at least 1'),
        (['--importers', '3', '--import-key', 'workers=8'], 'cannot divide 8 workers evenly'),
        (['--importers', '2'], 'cannot divide 1 workers evenly'),
        (
            ['--importers', '2', '--import-key', 'workers=2', '--register-only'],
            '--importers times full runs and takes no other mode',
        ),
        (
            ['--register-only', '--stop-before-finalization'],
            '--register-only times the registration alone and takes no other mode',
        ),
    ],
    ids=['zero', 'uneven', 'default-total', 'with-register-only', 'register-with-a-mode'],
)
def test_a_malformed_importers_run_is_refused(
    extra: list[str], message: str, capsys: pytest.CaptureFixture[str]
) -> None:
    """The arguments are checked before anything runs."""
    with pytest.raises(SystemExit):
        bench_import._parse_arguments(_argv(*extra))
    assert message in capsys.readouterr().err


class _InterruptedOutput:
    """A coordinator's output whose reading is interrupted once, after its first line."""

    def __init__(self, lines: list[str], events: list[str]) -> None:
        self._lines = iter(lines)
        self._events = events
        self._interrupted = False

    def __iter__(self) -> Iterator[str]:
        return self

    def __next__(self) -> str:
        if self._events.count('read') == 1 and not self._interrupted:
            self._interrupted = True
            raise KeyboardInterrupt
        line = next(self._lines)
        self._events.append('read')
        return line


class _Coordinator:
    """A coordinator process recording the signals it is sent and when it is waited for."""

    def __init__(self, options: dict[str, Any]) -> None:
        self.events: list[str] = []
        self.options = options
        self.stdout = _InterruptedOutput(['division', 'finished'], self.events)

    def send_signal(self, signum: int) -> None:
        self.events.append(f'signal {signum}')

    def wait(self) -> int:
        self.events.append('exited')
        return 1


def test_an_interrupted_coordinator_run_waits_for_the_coordinator_to_exit(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """The interrupt is passed on to the coordinator, in a process group of its own, its
    output is read to the end, and the interrupt is raised only once it has exited, so the
    server is not stopped under its importers."""
    started: list[_Coordinator] = []

    def start(*args: Any, **kwargs: Any) -> _Coordinator:
        started.append(_Coordinator(kwargs))
        return started[-1]

    monkeypatch.setattr(subprocess, 'Popen', start)
    bench = bench_import.ImportBench(
        server=MysqlServer.__new__(MysqlServer),
        side=Side(python=Path('python'), repo_root=tmp_path),
        spelling=Spelling.from_help(''),
        label=make_label(pr='PR-00', side='after', scale='test', session='a', date='2026-11-11'),
        scenario=ImportScenario.__new__(ImportScenario),
        cache_location='127.0.0.1:1',
    )

    with pytest.raises(KeyboardInterrupt):
        bench._run_stamped(tmp_path / 'opus.toml', ['-m', 'opus_import.import_all'])

    (coordinator,) = started
    assert coordinator.options['process_group'] == 0
    assert coordinator.events == ['read', f'signal {signal.SIGINT}', 'read', 'exited']
