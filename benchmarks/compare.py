"""Render two result files as a before/after table, or write the floors from sessions.

``python -m benchmarks.compare BEFORE.json AFTER.json [--floors-file FLOORS.json]
[--target METRIC ...]`` prints a Markdown table with one row per metric either file
holds: each side's median, spread and maximum, the change, the floor, the metric's
role, and the verdict. A metric's p95 over its runs is its maximum, since a session has
fewer than twenty runs, so the maximum column is its p95 too. It refuses two results whose ``server_model``, server ownership, cache backend
or brand differ, because their numbers are not comparable.

A metric's **role** decides whether it is judged. A **target** (``--target``) is judged
on improving beyond its floor. A **guard** -- the metrics `GUARD_PATTERNS` matches: the
full import's wall-clock, the largest bundle's ``--import`` time and the import's peak
tree PSS, the schema's data and index bytes, the medians of the empty, broad and
surface-geometry searches and of the fan-out in the app-cold and warm states, of the
empty search's pages in the app-cold state, of its first and last page in the warm state,
of autocomplete in the app-cold state, and the concurrency scenario's p95 -- is judged on not regressing beyond its floor plus
`GUARD_MARGIN`; a warm guard whose scenario executed no statements on either side is
reported instead, since it measured only a cache. Every other metric is **reported**,
not judged; warm autocomplete is one of them, because Django's site cache answers it.

When both results hold a finalization of a copy (a change measured on clones), a line
under the table holds the two finalizations to the ceiling that replaces the import
guards: the after side's finalization may take at most `CEILING_FRACTION` of the before
side's full import (its bundle imports plus its finalization) longer than the before
side's.

``python -m benchmarks.compare --floors SESSION.json SESSION.json [SESSION.json]``
writes the floors file of the sessions' scale and brand into ``benchmarks/results/``,
and lists the metrics the sessions disagree on and those some session lacks. Every
metric any session holds gets a floor.

The statistics are these. A metric's value in one run is one number; its median is
over the runs; its **spread** is the range of the runs' values divided by their median.
A metric whose runs also keep several executions' values under its own name in their
``samples`` -- a plan time, whose statements are each executed five times in one run --
takes its median and spread over those executions instead.
The concurrency scenario's p95 is computed once over every latency of all the runs
pooled, and its spread is the range of the per-run p95s divided by that pooled figure.
The **change** is ``(after - before) / before``. The **floor** of a metric is the
floors file's, or the before side's own spread where that is larger, or the before
side's spread alone where there is no floors file. A change beyond the floor in the
better direction is an **improvement**; beyond the floor plus `GUARD_MARGIN` in the
worse direction it is a **regression**; anything else is **within noise**. Several
sessions' floor is the largest of their spreads and of the range of their medians over
the median of their medians; they **agree** on a metric when that range is no larger
than their largest spread, and a metric three sessions still disagree on is **noisy**.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

from benchmarks.results import (
    RESULTS_DIR,
    ResultError,
    higher_is_better,
    load_result,
    median,
    p95,
    parse_label,
    spread,
)

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

#: What a regression must exceed beyond its floor to count against a guard.
GUARD_MARGIN = 0.05

#: The run kinds whose metrics are compared; profiled and reused-schema runs are not.
COMPARED_KINDS = ('import', 'import_unfinalized', 'finalize', 'db', 'web')

#: The guarded metrics, by name. The web ones are medians (each run's value of a
#: scenario is its wall-clock, of a request its latency), except the concurrency p95. A
#: cold state is guarded on a scenario's wall-clock, never on one request's latency: a
#: cold request's latency depends on whether an earlier request of the scenario reached
#: the same worker.
GUARD_PATTERNS = tuple(
    re.compile(pattern)
    for pattern in (
        r'import\.wall_s',
        r'import\.largest\.import_s',
        r'import\.peak_tree_pss_kb',
        r'db\.schema\.(data|index)_bytes',
        r'web\.(app-cold|warm)\.search\.(empty|broad|surface_geometry)\.wall_s',
        r'web\.app-cold\.pages\.empty\.wall_s',
        r'web\.warm\.pages\.empty\.page_(1|last)\.latency_s',
        r'web\.(app-cold|warm)\.fanout\.[^.]+\.wall_s',
        r'web\.app-cold\.autocomplete\.[^.]+\.wall_s',
        r'web\.(app-cold|warm)\.concurrency\.(distinct|shared)\.p95_s',
    )
)

#: The share of the before side's full import that the after side's finalization of a
#: copy may add.
CEILING_FRACTION = 0.10

#: Environment entries two compared results must share.
MATCHING_ENVIRONMENT_KEYS = ('server_model', 'server_owned', 'cache_backend', 'brand')

_P95_SUFFIX = '.p95_s'
_SAMPLES_SUFFIX = '.latency_s'


@dataclass(frozen=True)
class MetricSummary:
    """One metric's runs in one result file.

    Attributes:
        values: The per-run values.
        center: The median, or for a pooled p95 the p95 of the pool.
        spread: The spread of the per-run values about `center`.
    """

    values: tuple[float, ...]
    center: float
    spread: float

    @property
    def maximum(self) -> float:
        """The largest per-run value."""
        return max(self.values)


def summarize(content: Mapping[str, Any]) -> dict[str, MetricSummary]:
    """Summarize every metric of a result file's compared runs.

    Parameters:
        content: The result file.

    Returns:
        Each metric's summary, by name.
    """
    per_metric: dict[str, list[float]] = {}
    pools: dict[str, list[float]] = {}
    for run in content['runs']:
        if run['kind'] not in COMPARED_KINDS:
            continue
        for name, value in run['metrics'].items():
            per_metric.setdefault(name, []).append(float(value))
        for name, values in run['samples'].items():
            pools.setdefault(name, []).extend(float(value) for value in values)
    summaries = {}
    for name, values in per_metric.items():
        pool_name = name.removesuffix(_P95_SUFFIX) + _SAMPLES_SUFFIX
        if name.endswith(_P95_SUFFIX) and pool_name in pools and len(pools[pool_name]) > 0:
            center = p95(pools[pool_name])
            low, high = min(values), max(values)
            pooled_spread = (
                0.0 if high == low else (high - low) / center if center > 0 else math.inf
            )
            summaries[name] = MetricSummary(tuple(values), center, pooled_spread)
        elif name in pools and len(pools[name]) > 0:
            # A metric whose runs keep every execution's value under its own name, as a
            # plan time does, is summarized over those executions.
            executions = pools[name]
            summaries[name] = MetricSummary(
                tuple(executions), median(executions), spread(executions)
            )
        else:
            summaries[name] = MetricSummary(tuple(values), median(values), spread(values))
    return summaries


def check_comparable(before: Mapping[str, Any], after: Mapping[str, Any]) -> None:
    """Refuse two results that were not measured the same way.

    Parameters:
        before: The before result.
        after: The after result.

    Raises:
        ResultError: Naming the first `MATCHING_ENVIRONMENT_KEYS` entry that differs.
    """
    for key in MATCHING_ENVIRONMENT_KEYS:
        mine, theirs = before['environment'].get(key), after['environment'].get(key)
        if mine is not None and theirs is not None and mine != theirs:
            raise ResultError(f'the two results differ in {key}: {mine!r} and {theirs!r}')


def change(before: float, after: float) -> float | None:
    """Return the relative change from before to after.

    Parameters:
        before: The before median.
        after: The after median.

    Returns:
        ``(after - before) / before``; None when before is zero and after is not, and
        zero when both are.
    """
    if before == 0:
        return 0.0 if after == 0 else None
    return (after - before) / abs(before)


def verdict(metric: str, relative: float | None, floor: float | None) -> str:
    """Judge one change against its floor.

    Parameters:
        metric: The metric, whose name says which direction is better.
        relative: The change, or None when it has no relative size.
        floor: The floor, or None when there is none.

    Returns:
        ``improved``, ``regressed``, ``within noise``, ``undefined change`` (the before
        median is zero and the after one is not), or ``no floor``.
    """
    if relative is None:
        return 'undefined change'
    if floor is None:
        return 'no floor'
    better = -relative if not higher_is_better(metric) else relative
    if better > floor:
        return 'improved'
    if -better > floor + GUARD_MARGIN:
        return 'regressed'
    return 'within noise'


def role(metric: str, targets: Sequence[str], warm_statements: Mapping[str, float]) -> str:
    """Say whether a metric is judged, and how.

    Parameters:
        metric: The metric.
        targets: The metrics named as the change's targets.
        warm_statements: The larger of the two sides' median statements-executed count of
            each warm scenario, by the scenario's metric prefix (``web.warm.<scenario>``).

    Returns:
        ``target``, ``guard``, or ``reported``.
    """
    if metric in targets:
        return 'target'
    if not any(pattern.fullmatch(metric) for pattern in GUARD_PATTERNS):
        return 'reported'
    if metric.startswith('web.warm.'):
        scenario = '.'.join(metric.split('.')[:4])
        if warm_statements.get(scenario, 1.0) == 0:
            return 'reported'
    return 'guard'


def judgement(metric_role: str, classification: str) -> str:
    """Turn a classification into the verdict a role allows.

    Parameters:
        metric_role: What `role` said.
        classification: What `verdict` said.

    Returns:
        ``reported`` for a reported metric; for a target, ``improved`` or ``not
        improved``; for a guard, ``regressed`` or ``held``; the classification itself
        where there is no floor or no relative change to judge.
    """
    if metric_role == 'reported':
        return 'reported'
    if classification in {'no floor', 'undefined change'}:
        return classification
    if metric_role == 'target':
        return 'improved' if classification == 'improved' else 'not improved'
    return 'regressed' if classification == 'regressed' else 'held'


def _runs_of(content: Mapping[str, Any], kind: str, metric: str) -> list[float]:
    """Return one metric's per-run values over one kind of run.

    Parameters:
        content: A result file.
        kind: The run kind.
        metric: The metric.

    Returns:
        The values, in run order, of the runs of that kind that recorded it.
    """
    return [
        float(run['metrics'][metric])
        for run in content['runs']
        if run['kind'] == kind and metric in run['metrics']
    ]


def finalization_ceiling(
    before: Mapping[str, Any], after: Mapping[str, Any]
) -> dict[str, float] | None:
    """Hold the after side's finalization of a copy to the before side's ceiling.

    Parameters:
        before: The before result, holding its run stopped before finalization and its
            finalization of a copy.
        after: The after result, holding its finalization of a copy.

    Returns:
        None unless both results hold a finalization and the before result its bundle
        imports; otherwise the medians of the two finalizations, the before side's full
        import (its bundle imports plus its finalization), the allowance
        (`CEILING_FRACTION` of that), the after side's excess over the before side's
        finalization, and ``within``: 1.0 when the excess is no more than the allowance,
        0.0 when it is more.
    """
    base = _runs_of(before, 'finalize', 'import.finalization.wall_s')
    head = _runs_of(after, 'finalize', 'import.finalization.wall_s')
    imports = _runs_of(before, 'import_unfinalized', 'import.bundle_imports.wall_s')
    if len(base) == 0 or len(head) == 0 or len(imports) == 0:
        return None
    base_full = median(imports) + median(base)
    allowance = CEILING_FRACTION * base_full
    excess = median(head) - median(base)
    return {
        'before_finalization_s': median(base),
        'after_finalization_s': median(head),
        'before_full_import_s': base_full,
        'allowance_s': allowance,
        'excess_s': excess,
        'within': 1.0 if excess <= allowance else 0.0,
    }


def _number(value: float | None) -> str:
    """Format a number for the table compactly."""
    if value is None:
        return '-'
    if value != 0 and (abs(value) >= 1e6 or abs(value) < 1e-3):
        return f'{value:.3e}'
    return f'{value:.4g}'


def _percent(value: float | None) -> str:
    """Format a fraction as a percentage, or a dash."""
    if value is None:
        return '-'
    if math.isinf(value):
        return 'inf'
    return f'{100 * value:+.1f}%'


def render(
    before: Mapping[str, Any],
    after: Mapping[str, Any],
    floors: Mapping[str, Any] | None,
    targets: Sequence[str] = (),
) -> str:
    """Render the before/after table.

    Parameters:
        before: The before result.
        after: The after result.
        floors: The floors file's ``floors`` table, or None.
        targets: The change's target metrics.

    Returns:
        The Markdown table; then the finalization ceiling, where it applies; then the
        steps each side skipped.
    """
    check_comparable(before, after)
    mine, theirs = summarize(before), summarize(after)
    warm_statements = {
        name.removesuffix('.statements'): max(mine[name].center, theirs[name].center)
        for name in set(mine) & set(theirs)
        if name.startswith('web.warm.') and name.endswith('.statements')
    }
    lines = [
        '| Metric | Before | After | Change | Spread (before / after) | Max (before / after) '
        '| Floor | Role | Verdict |',
        '|---|---|---|---|---|---|---|---|---|',
    ]
    for name in sorted(set(mine) | set(theirs)):
        left, right = mine.get(name), theirs.get(name)
        relative = None if left is None or right is None else change(left.center, right.center)
        floor = None
        if floors is not None and name in floors:
            floor = float(floors[name]['floor'])
        if left is not None and len(left.values) > 1:
            floor = left.spread if floor is None else max(floor, left.spread)
        metric_role = role(name, targets, warm_statements)
        judged = '-'
        if left is not None and right is not None:
            judged = judgement(metric_role, verdict(name, relative, floor))
        spreads = (
            f'{_percent(None if left is None else left.spread)} / '
            f'{_percent(None if right is None else right.spread)}'
        )
        maxima = (
            f'{_number(None if left is None else left.maximum)} / '
            f'{_number(None if right is None else right.maximum)}'
        )
        lines.append(
            f'| `{name}` | {_number(None if left is None else left.center)} | '
            f'{_number(None if right is None else right.center)} | {_percent(relative)} | '
            f'{spreads} | {maxima} | {_percent(floor)} | {metric_role} | {judged} |'
        )
    ceiling = finalization_ceiling(before, after)
    if ceiling is not None:
        outcome = 'within the ceiling' if ceiling['within'] else 'beyond the ceiling'
        lines.append('')
        lines.append(
            "Finalization ceiling: the after side's finalization took "
            f"{ceiling['excess_s']:+.3f} s against the before side's, which allows "
            f"{ceiling['allowance_s']:.3f} s ({CEILING_FRACTION:.0%} of the before side's "
            f'full import, {ceiling["before_full_import_s"]:.3f} s): {outcome}.'
        )
    for side, content in (('before', before), ('after', after)):
        skipped = content['environment'].get('skipped_steps', [])
        if len(skipped) > 0:
            lines.append('')
            lines.append(f'Steps the {side} side does not have: {", ".join(skipped)}.')
    return '\n'.join(lines) + '\n'


def floors_from_sessions(sessions: Sequence[Mapping[str, Any]]) -> dict[str, dict[str, Any]]:
    """Compute every metric's floor from two or three floor sessions.

    Parameters:
        sessions: The sessions' result files, all of one scale and brand.

    Returns:
        Per metric: its ``floor``, the ``spreads`` and ``medians`` of the sessions that
        hold it, the positions of the sessions that do not (``missing_from``), whether
        those sessions ``agree``, and whether it is ``noisy`` (three sessions that
        still disagree). A metric only some sessions hold still gets a floor, from the
        sessions that hold it; held by one session alone, its floor is that session's
        spread, and it is never counted as agreeing.
    """
    summaries = [summarize(session) for session in sessions]
    floors = {}
    for name in sorted(set().union(*summaries)):
        holding = [summary[name] for summary in summaries if name in summary]
        centers = [entry.center for entry in holding]
        spreads = [entry.spread for entry in holding]
        between = spread(centers)
        largest = max(spreads)
        agree = len(holding) >= 2 and between <= largest
        floors[name] = {
            'floor': max(largest, between),
            'spreads': spreads,
            'medians': centers,
            'missing_from': [
                position for position, summary in enumerate(summaries) if name not in summary
            ],
            'agree': agree,
            'noisy': len(holding) >= 3 and not agree,
        }
    return floors


def write_floors(paths: Sequence[Path]) -> tuple[Path, list[str]]:
    """Write the floors file for a set of floor-session result files.

    Parameters:
        paths: Two or three result files of one scale and brand, from one PR.

    Returns:
        The floors file written, and the metrics the sessions disagree on (a metric
        only one session holds among them).

    Raises:
        ResultError: If there are not two or three files, or they differ in PR, side,
            scale or brand, or are not comparable.
    """
    if len(paths) not in (2, 3):
        raise ResultError('a floor needs two sessions, or three where two disagree')
    labels = [parse_label(path.name) for path in paths]
    first = labels[0]
    for label in labels[1:]:
        if (label.pr, label.side, label.scale, label.brand) != (
            first.pr,
            first.side,
            first.scale,
            first.brand,
        ):
            raise ResultError(f'{paths[0].name} and the others are not one set of floor sessions')
    sessions = [load_result(path) for path in paths]
    for session in sessions[1:]:
        check_comparable(sessions[0], session)
    floors = floors_from_sessions(sessions)
    for entry in floors.values():
        entry['missing_from'] = [paths[position].name for position in entry['missing_from']]
    output = RESULTS_DIR / f'{first.date}_{first.pr}_floors_{first.scale}_{first.brand}.json'
    content = {
        'format': 1,
        'scale': first.scale,
        'brand': first.brand,
        'sessions': [path.name for path in paths],
        'floors': floors,
    }
    output.write_text(json.dumps(content, indent=1, sort_keys=True) + '\n', encoding='utf-8')
    return output, [name for name, entry in floors.items() if not entry['agree']]


def main(argv: Sequence[str] | None = None) -> None:
    """Print a before/after table, or write a floors file.

    Parameters:
        argv: The arguments, or None for the command line's.
    """
    parser = argparse.ArgumentParser(
        prog='python -m benchmarks.compare',
        description='Compare two result files, or compute floors from floor sessions.',
    )
    parser.add_argument('results', nargs='+', type=Path, help='result files')
    parser.add_argument(
        '--floors', action='store_true', help='write the floors file of these floor sessions'
    )
    parser.add_argument('--floors-file', type=Path, default=None, help='judge against these floors')
    parser.add_argument(
        '--target',
        action='append',
        default=[],
        metavar='METRIC',
        help='a metric the change sets out to improve; may be given more than once',
    )
    args = parser.parse_args(argv)
    if args.floors:
        output, disagreeing = write_floors(args.results)
        sys.stdout.write(f'wrote {output}\n')
        floors = json.loads(output.read_text(encoding='utf-8'))['floors']
        partial = [name for name, entry in floors.items() if len(entry['missing_from']) > 0]
        if len(partial) > 0:
            sys.stdout.write(
                f'{len(partial)} metrics are missing from some session:\n'
                + ''.join(f'  {name}\n' for name in partial)
            )
        if len(disagreeing) > 0:
            sys.stdout.write(
                f'{len(disagreeing)} metrics disagree between the sessions:\n'
                + ''.join(f'  {name}\n' for name in disagreeing)
            )
        return
    if len(args.results) != 2:
        parser.error('a comparison takes exactly two result files, before then after')
    floors = None
    if args.floors_file is not None:
        floors = json.loads(args.floors_file.read_text(encoding='utf-8'))['floors']
    before, after = (load_result(path) for path in args.results)
    sys.stdout.write(render(before, after, floors, args.target))


if __name__ == '__main__':
    main()
