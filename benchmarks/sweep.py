"""Render a thread sweep: web results that differ only in gunicorn's threads per worker.

``python -m benchmarks.compare --sweep RESULT.json RESULT.json [RESULT.json ...]``
prints one Markdown table with a column per result, in order of thread count, and a row
per metric any of them holds, each cell the metric's median and spread over that
result's runs, as `benchmarks.compare.summarize` gives them. Nothing is judged: a sweep chooses a
setting rather than measuring a change.

A comparison (`benchmarks.compare.render`) refuses two results whose ``server_model``
differs, since their numbers are not comparable. A sweep is the one case where it must
differ, so `check_sweep` accepts results only when their ``server_model`` differs in the
thread count alone (and in the worker connections, which the harness always sets equal
to it) and every other environment entry is the same in all of them. The runs' load
averages are recorded per run, not in the environment, so they may differ. Any other
difference is named and refused.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any

from benchmarks.results import ResultError, parse_label

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence
    from pathlib import Path

#: The environment entry a sweep varies.
SWEPT_KEY = 'server_model'

#: Stands for an environment entry a result does not record.
_MISSING = object()

_THREADS = re.compile(r'\bthreads=(\d+)\b')
_WORKER_CONNECTIONS = re.compile(r'\bworker_connections=(\d+)\b')


def thread_count(server_model: str) -> int:
    """Return the threads per worker a ``server_model`` names.

    Parameters:
        server_model: The result environment's ``server_model``.

    Returns:
        Its ``threads=`` count.

    Raises:
        ResultError: If it names none, or names worker connections other than the
            threads.
    """
    threads = _THREADS.search(server_model)
    if threads is None:
        raise ResultError(f'server_model {server_model!r} names no thread count')
    connections = _WORKER_CONNECTIONS.search(server_model)
    if connections is not None and connections.group(1) != threads.group(1):
        raise ResultError(
            f'server_model {server_model!r} names worker connections other than its threads'
        )
    return int(threads.group(1))


def _without_threads(server_model: str) -> str:
    """Return a ``server_model`` with its thread and worker-connection counts blanked."""
    blanked = _THREADS.sub('threads=*', server_model)
    return _WORKER_CONNECTIONS.sub('worker_connections=*', blanked)


def check_sweep(results: Sequence[tuple[Path, Mapping[str, Any]]]) -> list[int]:
    """Refuse a set of results that is not a thread sweep.

    Parameters:
        results: Each result file's path and content.

    Returns:
        Each result's thread count, in the order given.

    Raises:
        ResultError: If there are fewer than two results; their labels differ in PR,
            side, scale or brand; a result has no ``server_model``; two share a thread
            count; their ``server_model`` differs in more than the thread count; or any
            other environment entry differs, each such entry named.
    """
    if len(results) < 2:
        raise ResultError('a sweep takes two or more result files')
    labels = [parse_label(path.name) for path, _ in results]
    first = labels[0]
    for (path, _), label in zip(results, labels, strict=True):
        if (label.pr, label.side, label.scale, label.brand) != (
            first.pr,
            first.side,
            first.scale,
            first.brand,
        ):
            raise ResultError(f'{path.name} is not of the same PR, side, scale and brand')
    models = []
    for path, content in results:
        model = content['environment'].get(SWEPT_KEY)
        if not isinstance(model, str):
            raise ResultError(f'{path.name} records no {SWEPT_KEY}')
        models.append(model)
    counts = [thread_count(model) for model in models]
    if len(set(counts)) != len(counts):
        raise ResultError(f'two results share a thread count: {counts}')
    if len({_without_threads(model) for model in models}) != 1:
        raise ResultError(f'the results differ in {SWEPT_KEY} beyond the thread count: {models}')
    environments = [content['environment'] for _, content in results]
    keys = set().union(*environments) - {SWEPT_KEY}
    differing = sorted(
        key
        for key in keys
        if any(
            environment.get(key, _MISSING) != environments[0].get(key, _MISSING)
            for environment in environments[1:]
        )
    )
    if len(differing) > 0:
        raise ResultError(
            'a sweep varies only the threads per worker, but the results also differ in '
            + ', '.join(differing)
        )
    return counts


def _cell(summary: Any) -> str:
    """Format one result's median and spread of a metric, or a dash."""
    if summary is None:
        return '-'
    center = summary.center
    text = (
        f'{center:.3e}'
        if center != 0 and (abs(center) >= 1e6 or abs(center) < 1e-3)
        else f'{center:.4g}'
    )
    return f'{text} ({100 * summary.spread:.1f}%)'


def render_sweep(
    results: Sequence[tuple[Path, Mapping[str, Any]]], summaries: Sequence[Mapping[str, Any]]
) -> str:
    """Render a thread sweep as one table.

    Parameters:
        results: Each result file's path and content.
        summaries: Each result's metrics, in the same order, each with the ``center``
            and ``spread`` `benchmarks.compare.summarize` gives it.

    Returns:
        The Markdown table, a column per result in order of thread count, a row per
        metric, each cell the median and the spread; then the files each column read.

    Raises:
        ResultError: If the results are not a sweep (`check_sweep`).
    """
    counts = check_sweep(results)
    ordered = sorted(zip(counts, results, summaries, strict=True), key=lambda entry: entry[0])
    header = ' | '.join(f'threads={count}' for count, _, _ in ordered)
    lines = [
        f'| Metric | {header} |',
        '|---|' + '---|' * len(ordered),
    ]
    for name in sorted(set().union(*summaries)):
        cells = ' | '.join(_cell(summary.get(name)) for _, _, summary in ordered)
        lines.append(f'| `{name}` | {cells} |')
    lines.append('')
    lines.append('Each cell is the median over the runs, with the spread in parentheses.')
    lines.append('')
    lines.extend(
        f'- threads={count}: {path.name} ({content["environment"][SWEPT_KEY]})'
        for count, (path, content), _ in ordered
    )
    return '\n'.join(lines) + '\n'
