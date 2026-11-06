"""What the harness watches while an import invocation runs, and what it checks after.

`InvocationMonitor` is the `import_tests.tools.build_run.StepObserver` the import
benchmark hands to `build_run.perform_run`, and the one it wraps around each
`build_run.run_pipeline_step` it makes itself, so every invocation is measured the same
way at every scale: its wall-clock; its memory, sampled once a second from ``/proc``
(each process's peak resident set, ``VmHWM``, and the peak over the samples of the
import process tree's summed proportional set size, ``Pss``, which counts a page that
forked workers share once rather than once per process); its own ``--timing-json``
step timings; and, after a bundle-import invocation, the check that the permanent
``obs_general`` holds rows for every bundle the invocation imports.
"""

from __future__ import annotations

import contextlib
import json
import os
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

import MySQLdb

from benchmarks.bench_server import quote_identifier

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    from benchmarks.bench_server import MysqlServer
    from benchmarks.sides import Spelling
    from import_tests.tools.build_run import StepResult

#: Seconds between memory samples.
SAMPLE_INTERVAL_S = 1.0


class RunFailedError(Exception):
    """Raised when an invocation fails or a check after it does; the run is not a result."""


@dataclass
class InvocationRecord:
    """What one invocation did and what was measured while it ran.

    Attributes:
        name: The invocation's role in the run, as `benchmarks.sides.Spelling.role` names it.
        arguments: Its command line after the interpreter.
        wall_s: Its wall-clock seconds, from just before the process started to just
            after it exited.
        returncode: Its exit status.
        peak_rss_kb: The largest ``VmHWM`` any process of its tree reached.
        peak_tree_pss_kb: The largest summed ``Pss`` of its tree over the samples.
        samples: How many memory samples were taken.
        timings: Its own step timings, from ``--timing-json``, or empty.
        bundles: The bundles a bundle-import invocation imports, or empty.
    """

    name: str
    arguments: tuple[str, ...]
    wall_s: float = 0.0
    returncode: int = 0
    peak_rss_kb: int = 0
    peak_tree_pss_kb: int = 0
    samples: int = 0
    timings: dict[str, float] = field(default_factory=dict)
    bundles: list[str] = field(default_factory=list)


def read_kb(path: Path, key: str) -> int:
    """Return one ``kB`` figure from a ``/proc`` file, or zero if it cannot be read.

    Parameters:
        path: ``/proc/<pid>/status`` or ``/proc/<pid>/smaps_rollup``.
        key: The line's key, such as ``VmHWM``.

    Returns:
        The figure in kilobytes; zero when the process has gone or the line is absent.
    """
    with contextlib.suppress(OSError):
        for line in path.read_text(encoding='ascii', errors='replace').splitlines():
            if line.startswith(key + ':'):
                return int(line.split()[1])
    return 0


class _MemorySampler:
    """Samples the memory of this process's children, once a second, on a thread."""

    def __init__(self, excluded: Callable[[], set[int]]) -> None:
        """Prepare to sample.

        Parameters:
            excluded: Returns the process ids not to count (the owned servers).
        """
        self._excluded = excluded
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._peak_hwm: dict[int, int] = {}
        self.peak_tree_pss_kb = 0
        self.samples = 0

    def _sample(self) -> None:
        """Take one sample of every child process not excluded."""
        # psutil comes with the benchmarks extra only, so the unit tests, which run
        # without it, can import this module.
        import psutil

        excluded = self._excluded()
        try:
            children = psutil.Process(os.getpid()).children(recursive=True)
        except psutil.Error:
            return
        tree_pss = 0
        for child in children:
            if child.pid in excluded:
                continue
            proc = Path('/proc') / str(child.pid)
            hwm = read_kb(proc / 'status', 'VmHWM')
            if hwm > 0:
                self._peak_hwm[child.pid] = max(self._peak_hwm.get(child.pid, 0), hwm)
            tree_pss += read_kb(proc / 'smaps_rollup', 'Pss')
        self.peak_tree_pss_kb = max(self.peak_tree_pss_kb, tree_pss)
        self.samples += 1

    def _loop(self) -> None:
        """Sample until told to stop."""
        while not self._stop.is_set():
            # A process can exit between being listed and being read.
            with contextlib.suppress(OSError):
                self._sample()
            self._stop.wait(SAMPLE_INTERVAL_S)

    def start(self) -> None:
        """Start sampling."""
        self._thread.start()

    def stop(self) -> int:
        """Stop sampling.

        Returns:
            The largest ``VmHWM`` any sampled process reached, in kilobytes.
        """
        self._stop.set()
        self._thread.join()
        return max(self._peak_hwm.values(), default=0)


class InvocationMonitor:
    """Measures each invocation of an import run and checks each bundle import's result.

    It implements `import_tests.tools.build_run.StepObserver`. An invocation that
    exits non-zero, or a bundle import after which ``obs_general`` lacks a bundle,
    raises `RunFailedError` from `step_finished`, which ends the run.
    """

    def __init__(
        self,
        *,
        server: MysqlServer,
        schema: str,
        spelling: Spelling,
        expand: Callable[[Sequence[str]], list[list[str]]],
        timing_file: Path | None,
        excluded_pids: Callable[[], set[int]],
    ) -> None:
        """Prepare to watch one run.

        Parameters:
            server: The owned server, which the check connects to.
            schema: The schema the run imports into.
            spelling: The side's spelling, which names each invocation by its role and
                recognizes a bundle import.
            expand: Expands invocations' descriptor groups into the bundles each
                imports, with the side's own interpreter. Called once, with every
                group the run will import, by `expand_groups` or else just before the
                first bundle import starts its timing.
            timing_file: The file each invocation's ``--timing-json`` writes, or None
                where the side has no such option.
            excluded_pids: Returns the process ids the memory figures leave out.
        """
        self._server = server
        self._schema = schema
        self._spelling = spelling
        self._expand = expand
        self._timing_file = timing_file
        self._excluded_pids = excluded_pids
        self._groups: list[str] = []
        self._expanded: dict[str, list[str]] = {}
        self._current: InvocationRecord | None = None
        self._sampler: _MemorySampler | None = None
        self._started = 0.0
        self.records: list[InvocationRecord] = []

    def expect_groups(self, groups: Sequence[str]) -> None:
        """Name every descriptor group the run's bundle imports will be given.

        Parameters:
            groups: Each bundle-import invocation's last argument, in order.
        """
        self._groups = list(groups)

    def expand_groups(self) -> None:
        """Expand every announced group now, so no invocation's timing includes it."""
        if len(self._expanded) == 0 and len(self._groups) > 0:
            self._expanded = dict(zip(self._groups, self._expand(self._groups), strict=True))

    def is_bundle_import(self, arguments: Sequence[str]) -> bool:
        """Return whether an invocation imports bundles.

        Parameters:
            arguments: Its command line after the interpreter.

        Returns:
            True when it carries the side's bundle-import option.
        """
        return self._spelling.bundle_import in arguments

    def step_started(self, arguments: Sequence[str]) -> None:
        """Start timing and sampling an invocation.

        Parameters:
            arguments: Its command line after the interpreter.
        """
        record = InvocationRecord(name=self._spelling.role(arguments), arguments=tuple(arguments))
        if self.is_bundle_import(arguments):
            self.expand_groups()
            if arguments[-1] not in self._expanded:
                raise RunFailedError(f'the bundle group {arguments[-1]!r} was not announced')
            record.bundles = self._expanded[arguments[-1]]
        if self._timing_file is not None:
            self._timing_file.unlink(missing_ok=True)
        self._current = record
        self._sampler = _MemorySampler(self._excluded_pids)
        self._sampler.start()
        self._started = time.perf_counter()

    def step_finished(self, result: StepResult) -> None:
        """Finish measuring an invocation, then check it.

        Parameters:
            result: What the invocation did.

        Raises:
            RunFailedError: If it exited non-zero, it was asked for its timings and wrote
                none, or it imported bundles and ``obs_general`` has no row for one of
                them.
        """
        wall = time.perf_counter() - self._started
        record, sampler = self._current, self._sampler
        assert record is not None
        assert sampler is not None
        record.peak_rss_kb = sampler.stop()
        record.peak_tree_pss_kb = sampler.peak_tree_pss_kb
        record.samples = sampler.samples
        record.wall_s = wall
        record.returncode = result.returncode
        if self._timing_file is not None and self._timing_file.exists():
            record.timings = json.loads(self._timing_file.read_text(encoding='utf-8'))
        self.records.append(record)
        self._current = None
        if result.returncode != 0:
            raise RunFailedError(
                f'`{record.name}` exited {result.returncode}:\n{result.stderr[-4000:]}'
            )
        asked = self._timing_file is not None and str(self._timing_file) in result.arguments
        if asked and len(record.timings) == 0:
            raise RunFailedError(f'`{record.name}` was asked for its timings and wrote none')
        if self.is_bundle_import(result.arguments):
            self.check_bundles_landed(record.bundles)

    def check_bundles_landed(self, bundles: Sequence[str]) -> None:
        """Check that the permanent ``obs_general`` holds a row for every bundle.

        An invocation that imported into a namespace other than the permanent tables,
        or into nothing, leaves them out, and its timing would measure work that a
        served database never sees.

        Parameters:
            bundles: The bundles the invocation imports.

        Raises:
            RunFailedError: Naming every bundle with no row.
        """
        if len(bundles) == 0:
            return
        with contextlib.closing(self._server.connect()) as connection:
            cursor = connection.cursor()
            try:
                placeholders = ', '.join(['%s'] * len(bundles))
                cursor.execute(
                    f'SELECT DISTINCT bundle_id FROM {quote_identifier(self._schema)}.obs_general '  # nosec B608 - quoted identifier, placeholders
                    f'WHERE bundle_id IN ({placeholders})',
                    tuple(bundles),
                )
                present = {str(row[0]) for row in cursor.fetchall()}
            except MySQLdb.Error as err:
                raise RunFailedError(
                    f'cannot read {self._schema}.obs_general after importing {list(bundles)}: {err}'
                ) from err
            finally:
                cursor.close()
        missing = [bundle for bundle in bundles if bundle not in present]
        if len(missing) > 0:
            raise RunFailedError(
                f'after importing {list(bundles)}, {self._schema}.obs_general has no row for '
                f'{missing}: the invocation did not write the permanent tables'
            )

    def summary(self) -> dict[str, Any]:
        """Return every invocation's record, for a run's details.

        Returns:
            One dictionary per invocation, in order.
        """
        return {
            'invocations': [
                {
                    'name': record.name,
                    'arguments': list(record.arguments),
                    'wall_s': record.wall_s,
                    'returncode': record.returncode,
                    'peak_rss_kb': record.peak_rss_kb,
                    'peak_tree_pss_kb': record.peak_tree_pss_kb,
                    'samples': record.samples,
                    'timings': record.timings,
                    'bundles': record.bundles,
                }
                for record in self.records
            ]
        }
