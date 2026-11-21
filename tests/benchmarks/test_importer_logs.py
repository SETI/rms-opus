"""What the import benchmark reads from queue importers' logs and the coordinator's output:
each bundle's block, each importer's idle time, and the coordinator's phases; and the
``--coordinator`` arguments it refuses."""

import subprocess
from pathlib import Path

import pytest

from benchmarks import bench_import, importer_logs
from benchmarks.sides import Side, Spelling

#: A queue importer's information log: two bundles, then its exit.
_IMPORTER_LOG = """\
2026-11-11 08:00:00.000000 | pds.opus_import.main || HEADER | Performing all requested import functions
2026-11-11 08:00:00.500000 | pds.opus_import.main |-| INFO | Claimed bundle A_1
2026-11-11 08:00:00.600000 | pds.opus_import.main |-| HEADER | Importing A_1
2026-11-11 08:00:05.600000 | pds.opus_import.main |-| SUMMARY | Completed: Importing A_1
2026-11-11 08:00:05.600010 | pds.opus_import.main |-| SUMMARY | Elapsed time = 0:00:05.000000
2026-11-11 08:00:05.700000 | pds.opus_import.main |-| HEADER | Importing B_2
traceback text that continues a record
2026-11-11 08:01:10.700000 | pds.opus_import.main |-| SUMMARY | Completed: Importing B_2
2026-11-11 08:01:10.700010 | pds.opus_import.main |-| SUMMARY | Elapsed time = 0:01:05.000000
2026-11-11 08:01:11.000000 | pds.opus_import.main || SUMMARY | Completed: Performing all requested import functions
"""

#: An importer that found nothing to claim.
_IDLE_LOG = """\
2026-11-11 08:00:01.000000 | pds.opus_import.main || HEADER | Performing all requested import functions
2026-11-11 08:00:02.000000 | pds.opus_import.main |-| INFO | No pending bundle is left to claim; this importer exits
"""


def _write(directory: Path, name: str, text: str) -> Path:
    """Write a log file and return its path."""
    path = directory / name
    path.write_text(text, encoding='utf-8')
    return path


def test_an_importer_log_gives_each_bundle_block_and_the_exit(tmp_path: Path) -> None:
    """Each closed block with its stated length, and the first and last records' times."""
    log = importer_logs.read_importer_log(_write(tmp_path, 'a.log', _IMPORTER_LOG))

    assert [(block.bundle, block.elapsed_s) for block in log.bundles] == [
        ('A_1', 5.0),
        ('B_2', 65.0),
    ]
    assert log.bundles[1].ended.isoformat() == '2026-11-11T08:01:10.700000'
    assert log.started.isoformat() == '2026-11-11T08:00:00'
    assert log.exited.isoformat() == '2026-11-11T08:01:11'


def test_a_log_without_a_record_is_refused(tmp_path: Path) -> None:
    """Nothing to time from means the run is not measured."""
    with pytest.raises(ValueError, match='holds no log record'):
        importer_logs.read_importer_log(_write(tmp_path, 'empty.log', 'no records\n'))


def test_each_importer_is_idle_from_its_last_bundle_to_the_last_exit(tmp_path: Path) -> None:
    """The busy importer's idle time ends at its own exit, which is the last; the one that
    imported nothing was idle from its start."""
    logs = [
        importer_logs.read_importer_log(_write(tmp_path, 'busy.log', _IMPORTER_LOG)),
        importer_logs.read_importer_log(_write(tmp_path, 'idle.log', _IDLE_LOG)),
    ]

    idle = importer_logs.importer_idle(logs)

    assert idle == [
        {'log': 'busy.log', 'bundles': ['A_1', 'B_2'], 'idle_s': pytest.approx(0.3)},
        {'log': 'idle.log', 'bundles': [], 'idle_s': pytest.approx(70.0)},
    ]


def test_no_importer_is_no_idle_time() -> None:
    """A run with no importer log has nothing to report."""
    assert importer_logs.importer_idle([]) == []


def test_bundle_times_are_keyed_as_timing_files_key_them(tmp_path: Path) -> None:
    """A bundle imported twice, after its first importer was lost, counts both blocks."""
    logs = [
        importer_logs.read_importer_log(_write(tmp_path, 'a.log', _IMPORTER_LOG)),
        importer_logs.read_importer_log(
            _write(tmp_path, 'b.log', _IMPORTER_LOG.replace('B_2', 'C_3'))
        ),
    ]

    assert importer_logs.bundle_log_timings(logs) == {
        'import_bundle:A_1': 10.0,
        'import_bundle:B_2': 65.0,
        'import_bundle:C_3': 65.0,
    }


def test_only_queue_importers_logs_are_read(tmp_path: Path) -> None:
    """The registration's and the closing sequence's logs, and debug logs, are left out."""
    _write(tmp_path, 'opus_import_2026-11-11T08-00-00.log', _IDLE_LOG)
    _write(tmp_path, 'opus_import_2026-11-11T08-00-01_join_host_11.log', _IMPORTER_LOG)
    _write(tmp_path, 'opus_import_debug_2026-11-11T08-00-01_join_host_11.log', _IMPORTER_LOG)
    _write(tmp_path, 'opus_import_2026-11-11T08-00-02_join_host_12.log', _IDLE_LOG)

    logs = importer_logs.importer_logs([tmp_path])

    assert [log.path.name for log in logs] == [
        'opus_import_2026-11-11T08-00-01_join_host_11.log',
        'opus_import_2026-11-11T08-00-02_join_host_12.log',
    ]


def test_an_importers_own_directory_is_read_whatever_its_log_is_named(tmp_path: Path) -> None:
    """Each hand-started importer has a directory of its own, whose log may lack the suffix."""
    for number, text in ((0, _IMPORTER_LOG), (1, _IDLE_LOG)):
        directory = tmp_path / f'importer_{number}'
        directory.mkdir()
        _write(directory, 'opus_import_2026-11-11T08-00-00.log', text)
        _write(directory, 'opus_import_debug_2026-11-11T08-00-00.log', text)
    directories = [tmp_path / 'importer_0', tmp_path / 'importer_1']

    logs = importer_logs.importer_logs(directories, joined_only=False)

    assert [log.path.parent.name for log in logs] == ['importer_0', 'importer_1']
    assert importer_logs.importer_logs(directories) == []


_SPELLING = Spelling.from_help(
    '--import --finalize --validate --write-schema-version --yes --register-bundles --join'
)

#: A coordinator's output, each line with the moment it was read.
_COORDINATOR_OUTPUT = [
    (0.5, 'Parallelism: 30 cores detected, cpu_fraction 0.75, ceiling 22; workers 22 in all, '
     'importers 4, workers per importer 6, 6, 5, 5'),
    (1.0, '>>> /venv/bin/python -m opus_import --register-bundles A_1,B_2'),
    (1.2, '2026-11-11 08:00:00.1 | pds.opus_import.main || INFO | registration output'),
    (3.0, '2026-11-11 16:00:03 started importer 101 with 6 workers'),
    (3.1, '2026-11-11 16:00:03 started importer 102 with 6 workers'),
    (40.0, 'Bundles: 2 done, 0 importing, 0 pending, 0 failed'),
    (50.0, '>>> /venv/bin/python -m opus_import --finalize'),
    (70.0, '>>> /venv/bin/python -m opus_import --import-dictionary'),
    (72.0, '>>> /venv/bin/python -m opus_import --validate'),
    (80.0, '>>> /venv/bin/python -m opus_import --write-schema-version'),
    (81.0, 'Import is complete. Read ERRORS.log before trusting it.'),
]  # fmt: skip


def test_the_coordinators_output_marks_its_phases() -> None:
    """The registration runs to the first importer's start, the importers' phase to the
    first command after it, and the closing sequence to the exit, step by step."""
    phases = importer_logs.coordinator_phases(_COORDINATOR_OUTPUT, 82.0, _SPELLING)

    assert phases.registration_s == pytest.approx(2.0)
    assert phases.importers_s == pytest.approx(47.0)
    assert phases.finish_s == pytest.approx(32.0)
    assert phases.steps == {
        'finalize': pytest.approx(20.0),
        'import_dictionary': pytest.approx(2.0),
        'validate': pytest.approx(8.0),
        'write_schema_version': pytest.approx(2.0),
    }
    assert phases.workers_per_importer == [6, 6, 5, 5]


@pytest.mark.parametrize(
    'left_out',
    ['workers per importer', '--register-bundles', 'started importer', '--finalize'],
    ids=['division', 'registration', 'importers', 'closing'],
)
def test_an_output_without_a_phase_marker_is_refused(left_out: str) -> None:
    """Without each marker a phase has no start, and the run is not measured."""
    lines = _COORDINATOR_OUTPUT
    if left_out == '--finalize':
        lines = [(t, line) for t, line in lines if not line.startswith('>>>') or t < 3.0]
    else:
        lines = [(t, line) for t, line in lines if left_out not in line]

    with pytest.raises(ValueError, match='the coordinator'):
        importer_logs.coordinator_phases(lines, 82.0, _SPELLING)


def _argv(*extra: str) -> list[str]:
    """Return a fixture-scale command line with the given options added."""
    return [
        '--scale', 'fixture', '--side', 'after', '--pr', 'PR-16a', '--session', 'a',
        '--python', 'python', '--repo-root', '.', *extra,
    ]  # fmt: skip


def test_a_coordinator_run_takes_an_uneven_total() -> None:
    """The coordinator divides the total itself, unevenly when it must."""
    args = bench_import._parse_arguments(_argv('--coordinator', '4', '--import-key', 'workers=22'))
    assert args.coordinator == 4
    assert args.import_keys == {'workers': 22}


@pytest.mark.parametrize(
    ('extra', 'message'),
    [
        (['--coordinator', '0'], '--coordinator takes a count of at least 1'),
        (['--coordinator', '2'], 'at least one per importer'),
        (['--coordinator', '4', '--import-key', 'workers=3'], 'not 3'),
        (['--coordinator', '2', '--import-key', 'workers=max'], "not 'max'"),
        (
            ['--coordinator', '2', '--import-key', 'workers=2', '--importers', '2'],
            '--coordinator times full runs and takes no other mode',
        ),
        (
            ['--coordinator', '1', '--stop-before-finalization'],
            '--coordinator times full runs and takes no other mode',
        ),
    ],
    ids=['zero', 'default-total', 'fewer-workers', 'max', 'with-importers', 'unfinalized'],
)
def test_a_malformed_coordinator_run_is_refused(
    extra: list[str], message: str, capsys: pytest.CaptureFixture[str]
) -> None:
    """The arguments are checked before anything runs."""
    with pytest.raises(SystemExit):
        bench_import._parse_arguments(_argv(*extra))
    assert message in capsys.readouterr().err


@pytest.mark.parametrize(
    ('returncode', 'help_text', 'has'),
    [
        (0, 'usage: opus_import_all [--sets DESC,DESC] [--workers N] [--importers M]', True),
        (0, 'usage: opus_import_all [--sets DESC,DESC] [--workers N]', False),
        (1, 'No module named opus_import.import_all', False),
    ],
    ids=['coordinator', 'without-importers', 'without-module'],
)
def test_a_side_has_the_coordinator_when_its_help_lists_importers_and_sets(
    returncode: int, help_text: str, has: bool, monkeypatch: pytest.MonkeyPatch
) -> None:
    """PR-16's ``opus_import_all`` has ``--sets`` and no ``--importers``; it is measured with
    ``--importers`` instead."""
    side = Side(python=Path('python'), repo_root=Path())

    def run(arguments: list[str], *, env: object = None) -> subprocess.CompletedProcess[str]:
        assert arguments == ['-m', 'opus_import.import_all', '--help']
        return subprocess.CompletedProcess(arguments, returncode, stdout=help_text, stderr='')

    monkeypatch.setattr(Side, 'run', lambda self, arguments, env=None: run(arguments, env=env))

    assert side.has_coordinator() is has
