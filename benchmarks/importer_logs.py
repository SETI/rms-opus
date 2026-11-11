"""Read what queue importers and the coordinator report, for the import benchmark.

A run with several importers (`benchmarks.bench_import.ImportBench.run_importers`) or
under ``opus_import_all`` (`benchmarks.bench_import.ImportBench.run_coordinator`) times
its importers' phase as a whole. What each importer did inside it comes from the
importer's own information log, which the import writes whichever way it was started:
each bundle's ``Importing <bundle>`` block, which closes with the block's elapsed time,
and the importer's last record, written as it exits (`read_importer_log`). From those
come each importer's **idle time**, from the end of its last bundle to the exit of the
last importer of the run (`importer_idle`), and, for importers started by the
coordinator, which cannot be given a timing file each, the per-bundle import times
(`bundle_log_timings`).

The coordinator's own standard output marks where its phases begin: the ``>>>`` line it
prints before each ``opus_import`` invocation it runs, and the event it prints as it
starts each importer. `coordinator_phases` turns those lines, stamped as they were read,
into the registration, the importers' phase and the closing sequence.
"""

from __future__ import annotations

import datetime
import re
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from import_tests.tools import build_run

if TYPE_CHECKING:
    from collections.abc import Sequence
    from pathlib import Path

    from benchmarks.sides import Spelling

#: How pdslogger starts a record: its timestamp, then the logger, the nesting depth, the
#: level and the message.
_RECORD_RE = re.compile(
    r'^(?P<stamp>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d+) \| [^|]+\|-*\| [A-Z]+ \| '
    r'(?P<message>.*)$'
)

#: The record closing a bundle's block, and the one after it giving the block's length.
_BUNDLE_DONE_RE = re.compile(r'^Completed: Importing (?P<bundle>\S+)$')
_ELAPSED_RE = re.compile(r'^Elapsed time = (?P<hours>\d+):(?P<minutes>\d\d):(?P<seconds>[\d.]+)$')

#: What the coordinator prints before each ``opus_import`` invocation it runs.
COMMAND_PREFIX = '>>> '

#: What the coordinator's event for a started importer contains.
STARTED_IMPORTER = ' started importer '

#: How the coordinator's first line ends: each importer's workers, comma-separated.
_DIVISION_RE = re.compile(r'workers per importer (?P<shares>\d+(?:, \d+)*)$')


@dataclass(frozen=True)
class BundleBlock:
    """One bundle an importer imported, as its log records it.

    Attributes:
        bundle: The bundle.
        ended: When its block closed, by the importer's clock.
        elapsed_s: How long the block took, as the log states it.
    """

    bundle: str
    ended: datetime.datetime
    elapsed_s: float


@dataclass(frozen=True)
class ImporterLog:
    """What one importer's information log says it did.

    Attributes:
        path: The log.
        started: Its first record's time.
        exited: Its last record's time, written as the importer exits.
        bundles: Each bundle it imported, in order.
    """

    path: Path
    started: datetime.datetime
    exited: datetime.datetime
    bundles: tuple[BundleBlock, ...] = field(default_factory=tuple)


def read_importer_log(path: Path) -> ImporterLog:
    """Read one importer's information log.

    Parameters:
        path: The log.

    Returns:
        Its first and last records' times and every bundle block it closed, each with
        the elapsed time the record after it states.

    Raises:
        ValueError: If the log holds no record.
    """
    stamps: list[datetime.datetime] = []
    bundles: list[BundleBlock] = []
    closing: tuple[str, datetime.datetime] | None = None
    for line in path.read_text(encoding='utf-8', errors='replace').splitlines():
        match = _RECORD_RE.match(line)
        if match is None:
            continue
        stamp = datetime.datetime.fromisoformat(match['stamp'])
        stamps.append(stamp)
        message = match['message']
        if closing is not None:
            elapsed = _ELAPSED_RE.match(message)
            if elapsed is not None:
                seconds = (
                    int(elapsed['hours']) * 3600
                    + int(elapsed['minutes']) * 60
                    + float(elapsed['seconds'])
                )
                bundles.append(BundleBlock(closing[0], closing[1], seconds))
            closing = None
        done = _BUNDLE_DONE_RE.match(message)
        if done is not None:
            closing = (done['bundle'], stamp)
    if len(stamps) == 0:
        raise ValueError(f'{path} holds no log record')
    return ImporterLog(path, stamps[0], stamps[-1], tuple(bundles))


def importer_logs(log_dirs: Sequence[Path]) -> list[ImporterLog]:
    """Read every queue importer's information log in some log directories.

    Parameters:
        log_dirs: The directories; a queue importer's log carries
            `build_run.JOIN_LOG_SUFFIX` in its name, and every other log is left out.

    Returns:
        One per importer, in the order the directories and the log names give.
    """
    marker = f'_{build_run.JOIN_LOG_SUFFIX}_'
    return [
        read_importer_log(path)
        for log_dir in log_dirs
        for path in build_run.import_logs(log_dir)
        if marker in path.name
    ]


def importer_idle(logs: Sequence[ImporterLog]) -> list[dict[str, object]]:
    """Return each importer's idle time: from its last bundle's end to the last exit.

    An importer that imported no bundle was idle from its start.

    Parameters:
        logs: Every importer of one run.

    Returns:
        One entry per importer, in the order given: its log's name, the bundles it
        imported, and ``idle_s``.
    """
    if len(logs) == 0:
        return []
    last_exit = max(log.exited for log in logs)
    return [
        {
            'log': log.path.name,
            'bundles': [block.bundle for block in log.bundles],
            'idle_s': (
                last_exit - (log.bundles[-1].ended if len(log.bundles) > 0 else log.started)
            ).total_seconds(),
        }
        for log in logs
    ]


def bundle_log_timings(logs: Sequence[ImporterLog]) -> dict[str, float]:
    """Return each bundle's import time, keyed as ``--timing-json`` keys it.

    Parameters:
        logs: Every importer of one run.

    Returns:
        ``import_bundle:<bundle>`` to the seconds its block took; a bundle imported
        twice (after its first importer was lost) counts both.
    """
    timings: dict[str, float] = {}
    for log in logs:
        for block in log.bundles:
            key = f'import_bundle:{block.bundle}'
            timings[key] = timings.get(key, 0.0) + block.elapsed_s
    return timings


@dataclass(frozen=True)
class CoordinatorPhases:
    """Where one ``opus_import_all`` run spent its time, from its standard output.

    Attributes:
        registration_s: From the registration's start to the first importer's.
        importers_s: From the first importer's start to the closing sequence's.
        finish_s: From the closing sequence's start to the coordinator's exit.
        steps: Each closing invocation's seconds, by its role
            (`benchmarks.sides.Spelling.role`).
        workers_per_importer: Each importer's workers, from the coordinator's first
            line.
    """

    registration_s: float
    importers_s: float
    finish_s: float
    steps: dict[str, float]
    workers_per_importer: list[int]


def coordinator_phases(
    lines: Sequence[tuple[float, str]], exited: float, spelling: Spelling
) -> CoordinatorPhases:
    """Split a coordinator's run into its phases, from its stamped output.

    Parameters:
        lines: Each line of its output with the `time.perf_counter` reading it was read
            at, in order.
        exited: The reading when it exited.
        spelling: The side's spelling, which names each closing invocation.

    Returns:
        The phases.

    Raises:
        ValueError: If the output lacks the division line, the registration's command,
            a started importer, or a command after it, so a phase has no start.
    """
    division = next((m for _, line in lines if (m := _DIVISION_RE.search(line))), None)
    registration = next(
        (
            t
            for t, line in lines
            if line.startswith(COMMAND_PREFIX) and '--register-bundles' in line
        ),
        None,
    )
    importers = next((t for t, line in lines if STARTED_IMPORTER in line), None)
    if division is None or registration is None or importers is None:
        raise ValueError(
            'the coordinator printed no division line, registration command or started importer'
        )
    commands = [
        (t, line) for t, line in lines if t >= importers and line.startswith(COMMAND_PREFIX)
    ]
    if len(commands) == 0:
        raise ValueError('the coordinator ran no closing sequence after its importers')
    steps: dict[str, float] = {}
    ends = [t for t, _ in commands[1:]] + [exited]
    for (started, line), ended in zip(commands, ends, strict=True):
        arguments = line.removeprefix(COMMAND_PREFIX).split()
        after_module = arguments[arguments.index('opus_import') + 1 :]
        role = spelling.role(after_module)
        steps[role] = steps.get(role, 0.0) + ended - started
    return CoordinatorPhases(
        registration_s=importers - registration,
        importers_s=commands[0][0] - importers,
        finish_s=exited - commands[0][0],
        steps=steps,
        workers_per_importer=[int(share) for share in division['shares'].split(', ')],
    )
