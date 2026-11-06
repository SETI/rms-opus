"""Result files, the facts every result records about the machine, and the statistics.

A **result file** holds one label's measurements: one side of one A/B (``before`` or
``after``) at one scale on one brand, in one session. Its name says all of that::

    YYYY-MM-DD_PR-nn_<side>_<scale>_<brand>_<session>.json

and its content is ``{"format": 1, "environment": {...}, "runs": [...]}``. Every bench
command appends its runs to the file of the label it was given, so one file ends up
holding the label's imports, its database statistics and its web runs. Result files
live in the results directory, ``[results] root`` in ``scenarios/server.toml``, outside
the repository; only the floors files `benchmarks.compare` writes from them, under
``benchmarks/floors/``, are committed.

A run is ``{"kind", "index", "started_at", "load_average_1m", "metrics", "samples",
"details"}``. ``metrics`` maps a metric name to one number for that run; ``samples``
maps a pooled metric (the concurrency scenario's latencies) to the list of numbers the
run contributed to the pool; ``details`` holds what is recorded but never compared.

A metric's name says which way is better: a name ending in ``_per_s`` is better higher,
every other name is better lower (seconds, bytes, kilobytes, counts).
"""

from __future__ import annotations

import contextlib
import datetime
import hashlib
import json
import math
import os
import platform
import re
import socket
import statistics
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Iterable, Sequence

#: The harness's own directory, and the directories it reads and writes under it.
BENCHMARKS_DIR = Path(__file__).resolve().parent
REPO_ROOT = BENCHMARKS_DIR.parent
SCENARIOS_DIR = BENCHMARKS_DIR / 'scenarios'
FLOORS_DIR = BENCHMARKS_DIR / 'floors'
SCRATCH_DIR = BENCHMARKS_DIR / 'scratch'

#: The file naming the directories the harness keeps outside the repository.
SERVER_TOML = SCENARIOS_DIR / 'server.toml'

#: The version of the result-file layout this module writes and reads.
FORMAT_VERSION = 1

#: The two sides of an A/B, the scales, and the brands a result can be labeled with.
SIDES = ('before', 'after')
SCALES = ('fixture', 'test', 'complete')
BRANDS = ('mysql',)

#: The suffix of a metric that is better higher; every other metric is better lower.
HIGHER_IS_BETTER_SUFFIX = '_per_s'

#: Environment entries that must not change within one result file: a file whose runs
#: came from two commits, two interpreters or two servers is not one label's runs.
PINNED_ENVIRONMENT_KEYS = (
    'git_sha',
    'git_dirty',
    'python_version',
    'brand',
    'server_version',
    'server_owned',
    'hostname',
)

_RESULT_NAME = re.compile(
    r'^(?P<date>\d{4}-\d{2}-\d{2})_(?P<pr>PR-[0-9A-Za-z]+)_(?P<side>before|after)_'
    r'(?P<scale>fixture|test|complete)_(?P<brand>mysql)_(?P<session>[0-9A-Za-z]+)\.json$'
)


class ResultError(Exception):
    """Raised when a result file is malformed, mislabeled, or would mix two labels."""


def results_root(path: Path = SERVER_TOML) -> Path:
    """Read where the result files live: ``[results] root`` in ``server.toml``.

    Parameters:
        path: The file.

    Returns:
        The directory, with ``~`` and environment variables expanded.

    Raises:
        ResultError: If it names an environment variable that is not set.
    """
    with path.open('rb') as stream:
        value = str(tomllib.load(stream)['results']['root'])
    expanded = os.path.expandvars(os.path.expanduser(value))
    if '$' in expanded:
        raise ResultError(f'{value!r} names an environment variable that is not set')
    return Path(expanded).resolve()


#: Where every result file is written and looked up.
RESULTS_DIR = results_root()


@dataclass(frozen=True)
class Label:
    """Which measurements a result file holds.

    Attributes:
        date: The session's date, ``YYYY-MM-DD``.
        pr: The PR being measured, ``PR-nn``.
        side: ``before`` (the base) or ``after`` (the head).
        scale: ``fixture``, ``test`` or ``complete``.
        brand: The database brand; always ``mysql`` until a second brand exists.
        session: A short label the executor chooses so two sessions on one day differ.
    """

    date: str
    pr: str
    side: str
    scale: str
    brand: str
    session: str

    @property
    def file_name(self) -> str:
        """The result file's name, which `parse_label` reads back."""
        return f'{self.date}_{self.pr}_{self.side}_{self.scale}_{self.brand}_{self.session}.json'

    @property
    def scratch_dir(self) -> Path:
        """The session's scratch directory for this label's raw logs and captures."""
        return SCRATCH_DIR / self.session / f'{self.side}_{self.scale}'


def parse_label(name: str) -> Label:
    """Read a label back out of a result file's name.

    Parameters:
        name: The file name, without a directory.

    Returns:
        The label the name encodes.

    Raises:
        ResultError: If the name is not a result file's name.
    """
    match = _RESULT_NAME.match(name)
    if match is None:
        raise ResultError(f'{name!r} is not a result file name (see benchmarks/results.py)')
    return Label(**match.groupdict())


def make_label(*, pr: str, side: str, scale: str, session: str, date: str | None = None) -> Label:
    """Build a label, checking each part the way `parse_label` would.

    Parameters:
        pr: The PR being measured, ``PR-nn``.
        side: ``before`` or ``after``.
        scale: ``fixture``, ``test`` or ``complete``.
        session: Letters and digits only.
        date: ``YYYY-MM-DD``, or None for today.

    Returns:
        The label.

    Raises:
        ResultError: If any part could not be read back from the file name.
    """
    label = Label(
        date=date if date is not None else datetime.date.today().isoformat(),
        pr=pr,
        side=side,
        scale=scale,
        brand=BRANDS[0],
        session=session,
    )
    parse_label(label.file_name)
    return label


def load_result(path: Path) -> dict[str, Any]:
    """Read a result file and check its shape.

    Parameters:
        path: The file.

    Returns:
        Its content.

    Raises:
        ResultError: If it is not JSON, or lacks the format, environment or runs.
    """
    try:
        content = json.loads(path.read_text(encoding='utf-8'))
    except json.JSONDecodeError as err:
        raise ResultError(f'{path} is not valid JSON: {err}') from err
    validate_result(content, str(path))
    return content  # type: ignore[no-any-return]  # validated just above


def validate_result(content: object, source: str) -> None:
    """Check that a result file's content has the layout this module writes.

    Parameters:
        content: The parsed file.
        source: What to call it in an error.

    Raises:
        ResultError: Naming the first thing wrong.
    """
    if not isinstance(content, dict):
        raise ResultError(f'{source}: a result file holds one JSON object')
    if content.get('format') != FORMAT_VERSION:
        raise ResultError(f'{source}: format is {content.get("format")!r}, not {FORMAT_VERSION}')
    if not isinstance(content.get('environment'), dict):
        raise ResultError(f'{source}: "environment" must be an object')
    runs = content.get('runs')
    if not isinstance(runs, list):
        raise ResultError(f'{source}: "runs" must be a list')
    for position, run in enumerate(runs):
        where = f'{source}: run {position}'
        if not isinstance(run, dict):
            raise ResultError(f'{where} is not an object')
        for key in ('kind', 'index', 'metrics', 'samples', 'details'):
            if key not in run:
                raise ResultError(f'{where} has no {key!r}')
        if not isinstance(run['metrics'], dict) or not isinstance(run['samples'], dict):
            raise ResultError(f'{where}: "metrics" and "samples" must be objects')
        if not all(_is_finite_number(value) for value in run['metrics'].values()):
            raise ResultError(f'{where}: every metric must be a finite number')
        for name, values in run['samples'].items():
            if not isinstance(values, list) or not all(map(_is_finite_number, values)):
                raise ResultError(f'{where}: sample {name!r} must be a list of finite numbers')


def _is_finite_number(value: object) -> bool:
    """Say whether a parsed JSON value is a finite number (JSON's NaN is not one)."""
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def merge_environment(existing: dict[str, Any], update: dict[str, Any], source: str) -> None:
    """Add entries to a result's environment, refusing to change a pinned one.

    Parameters:
        existing: The environment already in the file; updated in place.
        update: The entries this command measured.
        source: What to call the file in an error.

    Raises:
        ResultError: If a `PINNED_ENVIRONMENT_KEYS` entry would change, which means the
            command ran against a different commit, interpreter or server from the one
            the file's earlier runs did.
    """
    for key in PINNED_ENVIRONMENT_KEYS:
        if key in existing and key in update and existing[key] != update[key]:
            raise ResultError(
                f'{source}: {key} was {existing[key]!r} and is now {update[key]!r}; one '
                'result file holds one label, so start a new session label instead'
            )
    existing.update(update)


def append_runs(label: Label, environment: dict[str, Any], runs: Sequence[dict[str, Any]]) -> Path:
    """Add runs to a label's result file, creating it if needed.

    Each run's ``index`` is assigned here, counting on from the runs of the same kind
    already in the file.

    Parameters:
        label: The file to add to.
        environment: Environment entries to merge in (`merge_environment`).
        runs: The runs, each with ``kind``, ``metrics``, ``samples`` and ``details``.

    Returns:
        The file's path.
    """
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    path = RESULTS_DIR / label.file_name
    if path.exists():
        content = load_result(path)
    else:
        content = {'format': FORMAT_VERSION, 'environment': {}, 'runs': []}
    merge_environment(content['environment'], portable(environment), str(path))
    for run in portable(list(runs)):
        kind = run['kind']
        run['index'] = 1 + sum(1 for old in content['runs'] if old['kind'] == kind)
        content['runs'].append(run)
    validate_result(content, str(path))
    temporary = path.with_suffix('.json.tmp')
    temporary.write_text(json.dumps(content, indent=1, sort_keys=True) + '\n', encoding='utf-8')
    temporary.replace(path)
    return path


def portable(value: Any) -> Any:
    """Return a value with every absolute path in its strings made machine-neutral.

    A path inside the checkout becomes relative to its root, and any other path in
    the home directory starts with ``~``, so a committed result names no one's
    directory layout.

    Parameters:
        value: A JSON-shaped value.

    Returns:
        A copy, with dictionaries, lists and strings rewritten throughout.
    """
    if isinstance(value, str):
        return value.replace(f'{REPO_ROOT}{os.sep}', '').replace(f'{Path.home()}{os.sep}', '~/')
    if isinstance(value, dict):
        return {key: portable(item) for key, item in value.items()}
    if isinstance(value, list):
        return [portable(item) for item in value]
    return value


def new_run(kind: str) -> dict[str, Any]:
    """Return an empty run of one kind, stamped with its start and the load average.

    Parameters:
        kind: ``import``, ``db`` or ``web``.

    Returns:
        A run whose ``metrics``, ``samples`` and ``details`` are empty.
    """
    return {
        'kind': kind,
        'index': 0,
        'started_at': datetime.datetime.now(datetime.UTC).isoformat(timespec='seconds'),
        'load_average_1m': os.getloadavg()[0],
        'metrics': {},
        'samples': {},
        'details': {},
    }


def scenario_hash(paths: Iterable[Path]) -> str:
    """Return one SHA-256 over the scenario files a command read, in the order given.

    Parameters:
        paths: The files.

    Returns:
        The hex digest, which changes when any byte of any of them does.
    """
    digest = hashlib.sha256()
    for path in paths:
        digest.update(path.name.encode('utf-8'))
        digest.update(path.read_bytes())
    return digest.hexdigest()


def _cpu_governor() -> str:
    """Return the CPU frequency governor, or ``unavailable`` where none is exposed.

    Returns:
        The distinct governors of every CPU, joined by commas.
    """
    governors = set()
    for path in Path('/sys/devices/system/cpu').glob('cpu*/cpufreq/scaling_governor'):
        # A CPU whose frequency driver is busy answers EBUSY; the others still count.
        with contextlib.suppress(OSError):
            governors.add(path.read_text(encoding='utf-8').strip())
    return ','.join(sorted(governors)) if len(governors) > 0 else 'unavailable'


def _total_memory_bytes() -> int:
    """Return the machine's total memory, from ``/proc/meminfo``.

    Returns:
        Bytes.
    """
    for line in Path('/proc/meminfo').read_text(encoding='utf-8').splitlines():
        if line.startswith('MemTotal:'):
            return int(line.split()[1]) * 1024
    raise ResultError('/proc/meminfo has no MemTotal line')


def filesystem_type(path: Path) -> str:
    """Return the type of the filesystem a path is on, from ``/proc/mounts``.

    Parameters:
        path: An existing path.

    Returns:
        The type of the longest mount point containing it, such as ``ext4``.
    """
    resolved = str(path.resolve())
    best, best_type = '', 'unknown'
    for line in Path('/proc/mounts').read_text(encoding='utf-8').splitlines():
        fields = line.split()
        mount_point = fields[1]
        inside = resolved == mount_point or resolved.startswith(mount_point.rstrip('/') + '/')
        if inside and len(mount_point) > len(best):
            best, best_type = mount_point, fields[2]
    return best_type


def host_environment() -> dict[str, Any]:
    """Return the facts about the machine every result records.

    Returns:
        The CPU count, CPU frequency governor, total memory and hostname.
    """
    return {
        'cpu_count': os.cpu_count(),
        'cpu_governor': _cpu_governor(),
        'total_memory_bytes': _total_memory_bytes(),
        'hostname': socket.gethostname(),
        'platform': platform.platform(),
    }


def median(values: Sequence[float]) -> float:
    """Return the median of a non-empty sequence.

    Parameters:
        values: The values.

    Returns:
        The middle value, or the mean of the two middle values.
    """
    return float(statistics.median(values))


def spread(values: Sequence[float]) -> float:
    """Return a metric's spread: its range divided by its median.

    Parameters:
        values: The per-run values; one value has no spread.

    Returns:
        A fraction. Zero when every value is equal; infinity when the median is zero
        and the values are not all zero, because no fraction of zero covers them.
    """
    low, high = min(values), max(values)
    middle = median(values)
    if high == low:
        return 0.0
    if middle == 0:
        return math.inf
    return (high - low) / abs(middle)


#: How far from a session's median, in robust standard deviations, a run may lie and
#: still count toward the session's spread (`without_outliers`).
OUTLIER_SIGMAS = 3.0

#: The median absolute deviation times this estimates a normal distribution's standard
#: deviation.
MAD_TO_SIGMA = 1.4826


def without_outliers(values: Sequence[float]) -> list[float]:
    """Return a session's runs less those that lie far from the rest.

    A run is an outlier when it lies more than `OUTLIER_SIGMAS` robust standard
    deviations (`MAD_TO_SIGMA` times the median absolute deviation) from the median.
    Fewer than three runs, or runs more than half of which equal the median, have no
    outliers.

    Parameters:
        values: The per-run values.

    Returns:
        The values kept, in their order.
    """
    if len(values) < 3:
        return list(values)
    middle = median(values)
    deviation = median([abs(value - middle) for value in values])
    if deviation == 0:
        return list(values)
    limit = OUTLIER_SIGMAS * MAD_TO_SIGMA * deviation
    return [value for value in values if abs(value - middle) <= limit]


def run_spread(values: Sequence[float], center: float | None = None) -> float:
    """Return a metric's spread within one session, its outlying runs left out.

    The range of the runs `without_outliers` keeps, divided by ``center``. A session is
    judged on its median, which one outlying run barely moves, so the run does not set
    the noise either.

    Parameters:
        values: The per-run values.
        center: What the range is a fraction of; the median of every value when None.

    Returns:
        A fraction, with `spread`'s zero and infinity cases.
    """
    kept = without_outliers(values)
    low, high = min(kept), max(kept)
    middle = median(values) if center is None else center
    if high == low:
        return 0.0
    if middle == 0:
        return math.inf
    return (high - low) / abs(middle)


def p95(values: Sequence[float]) -> float:
    """Return the 95th percentile by the nearest-rank rule.

    The value at rank ``ceil(0.95 * n)`` of the sorted values, so it is always one of
    the values and, below twenty values, it is the maximum.

    Parameters:
        values: A non-empty sequence.

    Returns:
        The percentile.
    """
    ordered = sorted(values)
    rank = max(1, math.ceil(0.95 * len(ordered)))
    return float(ordered[rank - 1])


def higher_is_better(metric: str) -> bool:
    """Return whether a metric improves upward.

    Parameters:
        metric: The metric's name.

    Returns:
        True for a name ending in `HIGHER_IS_BETTER_SUFFIX`.
    """
    return metric.endswith(HIGHER_IS_BETTER_SUFFIX)
