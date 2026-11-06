"""Render two result files as a before/after table, or write the floors from sessions.

``python -m benchmarks.compare BEFORE.json AFTER.json [--floors-file FLOORS.json]
[--target METRIC ...]`` prints a Markdown table with one row per metric either file
holds: each side's median, spread and maximum, the change, the floor (as a fraction and
in the metric's units at the before median), the metric's role, and the verdict. A metric's p95 over its runs is its maximum, since a session has
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
guards, which are then reported rather than judged: the after side's finalization may
take at most `CEILING_FRACTION` of the before side's full import (its bundle imports
plus its finalization) longer than the before side's.

A comparison refuses two files of different scales, an after file given before a before
file, a target metric neither file holds, and a floors file of another scale or brand.

``python -m benchmarks.compare --floors SESSION.json SESSION.json [SESSION.json]``
writes the floors file of the sessions' scale and brand into the results directory,
and lists the metrics the sessions disagree on and those some session lacks. Every
metric any session holds gets a floor.

The statistics are these. A metric's value in one run is one number; its median is
over the runs; its **spread** is the range of the runs' values divided by their median,
leaving out an **outlying run**, one more than `benchmarks.results.OUTLIER_SIGMAS`
robust standard deviations from the median (`benchmarks.results.without_outliers`):
the median, which every run still enters, is barely moved by one such run, so it does
not set the noise either. A metric whose runs also keep several executions' values
under its own name in their ``samples`` -- a plan time, whose statements are each
executed five times in one run -- takes its median and spread over those executions
instead. The concurrency scenario's p95 is computed once over the latencies of all the
runs pooled, less those of a run whose own p95 is an outlier, and its spread is the range
of the per-run p95s, outliers left out, divided by that pooled figure. Session medians are never left out: the range of several
sessions' medians covers all of them.
The **change** is ``(after - before) / before``. The **floor** of a metric is the
floors file's ``floor``, or its absolute noise over the before median where that is
larger (`effective_floor`), or the before side's own spread where that is larger
still, or the before side's spread alone where there is no floors file. The absolute
noise is the metric's ``floor_abs``, in its own units, or for a time metric its
family's **jitter** where that is larger: small times scatter by a roughly fixed
amount whatever their size, so a fraction measured on one median does not carry over
to a much smaller one. A change beyond the floor in the
better direction is an **improvement**; beyond the floor plus `GUARD_MARGIN` in the
worse direction it is a **regression**; anything else is **within noise**. Several
sessions' floor is the largest of their spreads and of the range of their medians over
the median of their medians, and its ``floor_abs`` the same in the metric's units; they
**agree** on a metric when their medians lie within the widest range of a session's
runs, or for a time metric within its family's jitter where that is larger, and a
metric three sessions still disagree on is **noisy**. A family's jitter is the median
``floor_abs`` of its time metrics (`family_jitter`).
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
    run_spread,
    spread,
    without_outliers,
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

#: The metric families whose time metrics share a jitter: each family's is the median of
#: its time metrics' absolute floors (`family_jitter`).
JITTER_FAMILIES = ('import', 'db', 'web')

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

    @property
    def noise(self) -> float:
        """The range of the per-run values, outliers left out, in the metric's units."""
        kept = without_outliers(self.values)
        return max(kept) - min(kept)


def summarize(content: Mapping[str, Any]) -> dict[str, MetricSummary]:
    """Summarize every metric of a result file's compared runs.

    Parameters:
        content: The result file.

    Returns:
        Each metric's summary, by name.

    Raises:
        ResultError: If a pooled p95 has latencies in some of its runs but not all.
    """
    per_metric: dict[str, list[float]] = {}
    pools: dict[str, list[float]] = {}
    # Each pooled p95's per-run values beside the latencies of the same run.
    per_run_pools: dict[str, list[tuple[float, list[float]]]] = {}
    for run in content['runs']:
        if run['kind'] not in COMPARED_KINDS:
            continue
        for name, value in run['metrics'].items():
            per_metric.setdefault(name, []).append(float(value))
            pool_name = name.removesuffix(_P95_SUFFIX) + _SAMPLES_SUFFIX
            if name.endswith(_P95_SUFFIX) and pool_name in run['samples']:
                latencies = [float(latency) for latency in run['samples'][pool_name]]
                per_run_pools.setdefault(name, []).append((float(value), latencies))
        for name, values in run['samples'].items():
            pools.setdefault(name, []).extend(float(value) for value in values)
    summaries = {}
    for name, values in per_metric.items():
        runs = per_run_pools.get(name, [])
        if len(runs) > 0 and (
            len(runs) != len(values) or any(len(latencies) == 0 for _, latencies in runs)
        ):
            # A run left out of the pool would be left out of the pooled p95 unseen.
            raise ResultError(f'{name}: a run holding it lacks its latencies')
        if len(runs) > 0:
            # A run whose own p95 is an outlier would dominate the pooled tail, so its
            # latencies are left out of the pool as its p95 is left out of the spread.
            kept = without_outliers([run_p95 for run_p95, _ in runs])
            pool = [
                latency for run_p95, latencies in runs if run_p95 in kept for latency in latencies
            ]
            center = p95(pool)
            summaries[name] = MetricSummary(tuple(values), center, run_spread(values, center))
        elif name in pools and len(pools[name]) > 0:
            # A metric whose runs keep every execution's value under its own name, as a
            # plan time does, is summarized over those executions.
            executions = pools[name]
            summaries[name] = MetricSummary(
                tuple(executions), median(executions), run_spread(executions)
            )
        else:
            summaries[name] = MetricSummary(tuple(values), median(values), run_spread(values))
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


def is_time(metric: str) -> bool:
    """Say whether a metric is a time in seconds, not a rate or a count.

    Parameters:
        metric: The metric.

    Returns:
        True for a name ending ``_s`` that is not a per-second rate.
    """
    return metric.endswith('_s') and not metric.endswith('_per_s')


def absolute_noise(metric: str, entry: Mapping[str, Any], jitter: Mapping[str, float]) -> float:
    """Return the noise a metric's change must exceed, in the metric's units.

    Parameters:
        metric: The metric.
        entry: Its floors-file entry.
        jitter: The floors file's ``jitter``, by family.

    Returns:
        The entry's ``floor_abs``, or for a time metric its family's jitter where that is
        larger.
    """
    noise = float(entry['floor_abs'])
    if is_time(metric):
        noise = max(noise, float(jitter.get(metric.split('.')[0], 0.0)))
    return noise


def effective_floor(
    metric: str,
    entry: Mapping[str, Any],
    jitter: Mapping[str, float],
    before: float,
) -> float:
    """Return a metric's floor as a fraction of the before side's median.

    Parameters:
        metric: The metric.
        entry: Its floors-file entry.
        jitter: The floors file's ``jitter``, by family.
        before: The before side's median.

    Returns:
        The larger of the entry's ``floor`` and its `absolute_noise` over ``before``; the
        ``floor`` alone when ``before`` is zero.
    """
    floor = float(entry['floor'])
    if before == 0:
        return floor
    return max(floor, absolute_noise(metric, entry, jitter) / abs(before))


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


def role(
    metric: str,
    targets: Sequence[str],
    warm_statements: Mapping[str, float],
    *,
    import_guards: bool = True,
) -> str:
    """Say whether a metric is judged, and how.

    Parameters:
        metric: The metric.
        targets: The metrics named as the change's targets.
        warm_statements: The larger of the two sides' median statements-executed count of
            each warm scenario, by the scenario's metric prefix (``web.warm.<scenario>``).
        import_guards: False where the finalization ceiling replaces the import guards.

    Returns:
        ``target``, ``guard``, or ``reported``.
    """
    if metric in targets:
        return 'target'
    if not import_guards and metric.startswith('import.'):
        return 'reported'
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


def _floor_cell(floor: float | None, before: MetricSummary | None) -> str:
    """Format a floor as a fraction and, where there is a before median, in its units."""
    if floor is None or before is None or math.isinf(floor):
        return _percent(floor)
    return f'{_percent(floor)} ({_number(floor * abs(before.center))})'


def render(
    before: Mapping[str, Any],
    after: Mapping[str, Any],
    floors: Mapping[str, Any] | None,
    targets: Sequence[str] = (),
    jitter: Mapping[str, float] | None = None,
) -> str:
    """Render the before/after table.

    Parameters:
        before: The before result.
        after: The after result.
        floors: The floors file's ``floors`` table, or None.
        targets: The change's target metrics.
        jitter: The floors file's ``jitter``, by family.

    Returns:
        The Markdown table; then the finalization ceiling, where it applies; then the
        steps each side skipped.

    Raises:
        ResultError: If the results are not comparable, or neither holds a target.
    """
    check_comparable(before, after)
    mine, theirs = summarize(before), summarize(after)
    absent = [target for target in targets if target not in mine and target not in theirs]
    if len(absent) > 0:
        raise ResultError(f'neither result holds the target metric(s) {absent}')
    ceiling = finalization_ceiling(before, after)
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
            floor = effective_floor(
                name, floors[name], {} if jitter is None else jitter, left.center if left else 0.0
            )
        if left is not None and len(left.values) > 1:
            floor = left.spread if floor is None else max(floor, left.spread)
        metric_role = role(name, targets, warm_statements, import_guards=ceiling is None)
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
            f'{spreads} | {maxima} | {_floor_cell(floor, left)} | {metric_role} | {judged} |'
        )
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
        Per metric: its ``floor``, a fraction (the largest session spread, or the range
        of the session medians over their median); its ``floor_abs``, the same noise in
        the metric's units (the widest range of a session's runs, outliers left out, or
        the range of the session medians); the ``spreads`` and ``medians`` of the
        sessions that hold it; how many runs each left out of its spread as
        ``outliers``; the positions of the sessions that do not (``missing_from``);
        whether those sessions ``agree`` (their medians lie within the widest range of a
        session's runs or, for a time metric, its family's `family_jitter` where that is
        larger); and whether it is ``noisy`` (three sessions that still disagree). A
        metric only some sessions hold still gets a floor, from the sessions that hold
        it; held by one session alone, its floor is that session's spread, and it is
        never counted as agreeing.
    """
    summaries = [summarize(session) for session in sessions]
    floors: dict[str, dict[str, Any]] = {}
    for name in sorted(set().union(*summaries)):
        holding = [summary[name] for summary in summaries if name in summary]
        centers = [entry.center for entry in holding]
        spreads = [entry.spread for entry in holding]
        floors[name] = {
            'floor': max(max(spreads), spread(centers)),
            'floor_abs': max(max(entry.noise for entry in holding), max(centers) - min(centers)),
            'spreads': spreads,
            'outliers': [
                len(entry.values) - len(without_outliers(entry.values)) for entry in holding
            ],
            'medians': centers,
            'missing_from': [
                position for position, summary in enumerate(summaries) if name not in summary
            ],
        }
    jitter = family_jitter(floors)
    for name, entry in floors.items():
        holding = [summary[name] for summary in summaries if name in summary]
        noise = max(entry.noise for entry in holding)
        if is_time(name):
            noise = max(noise, jitter.get(name.split('.')[0], 0.0))
        between = max(entry['medians']) - min(entry['medians'])
        agree = len(holding) >= 2 and len(holding) == len(summaries) and between <= noise
        entry['agree'] = agree
        entry['noisy'] = len(holding) >= 3 and not agree
    return floors


def family_jitter(floors: Mapping[str, Mapping[str, Any]]) -> dict[str, float]:
    """Return each family's jitter: the median absolute floor of its time metrics.

    Small times scatter by a roughly fixed amount whatever their size, so a fraction of a
    small median understates what a change must exceed; the jitter is that amount.

    Parameters:
        floors: A floors table, each entry with its ``floor_abs``.

    Returns:
        Per family in `JITTER_FAMILIES` that has time metrics, the jitter in seconds.
    """
    jitter = {}
    for family in JITTER_FAMILIES:
        values = [
            float(entry['floor_abs'])
            for name, entry in floors.items()
            if name.split('.')[0] == family and is_time(name)
        ]
        if len(values) > 0:
            jitter[family] = median(values)
    return jitter


def write_floors(paths: Sequence[Path]) -> tuple[Path, list[str]]:
    """Write the floors file for a set of floor-session result files.

    Parameters:
        paths: Two or three result files of one scale and brand, from one PR.

    Returns:
        The floors file written, and the metrics the sessions disagree on (a metric
        only one session holds among them).

    Raises:
        ResultError: If there are not two or three distinct files, or they differ in PR,
            side, scale or brand, or are not comparable, or were not all measured on one
            clean commit.
    """
    if len(paths) not in (2, 3):
        raise ResultError('a floor needs two sessions, or three where two disagree')
    if len({path.resolve() for path in paths}) != len(paths):
        raise ResultError('a floor session was given twice')
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
    commits = {session['environment'].get('git_sha') for session in sessions}
    clean = all(session['environment'].get('git_dirty') is False for session in sessions)
    if len(commits) != 1 or not all(isinstance(sha, str) and sha for sha in commits) or not clean:
        # Floor sessions measure one commit's noise; two commits' difference is not noise.
        raise ResultError(
            f'floor sessions must all be of one clean commit, not {sorted(map(str, commits))}'
        )
    floors = floors_from_sessions(sessions)
    for entry in floors.values():
        entry['missing_from'] = [paths[position].name for position in entry['missing_from']]
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    output = RESULTS_DIR / f'{first.date}_{first.pr}_floors_{first.scale}_{first.brand}.json'
    content = {
        'format': 2,
        'scale': first.scale,
        'brand': first.brand,
        'sessions': [path.name for path in paths],
        'jitter': family_jitter(floors),
        'floors': floors,
    }
    output.write_text(json.dumps(content, indent=1, sort_keys=True) + '\n', encoding='utf-8')
    return output, [name for name, entry in floors.items() if not entry['agree']]


def check_labels(before: Path, after: Path, floors: Mapping[str, Any] | None) -> None:
    """Refuse a comparison whose file names or floors file do not belong together.

    Parameters:
        before: The before result file.
        after: The after result file.
        floors: The floors file's content, or None.

    Raises:
        ResultError: If the two files are of different scales, the after file comes
            first, or the floors file is of another scale or brand.
    """
    first, second = parse_label(before.name), parse_label(after.name)
    if first.scale != second.scale:
        raise ResultError(f'{before.name} and {after.name} are of different scales')
    if (first.side, second.side) == ('after', 'before'):
        raise ResultError(f'{after.name} is the before side; give it first')
    if floors is not None and (floors.get('scale'), floors.get('brand')) != (
        first.scale,
        first.brand,
    ):
        raise ResultError(
            f'the floors file is of {floors.get("scale")} {floors.get("brand")}, '
            f'not {first.scale} {first.brand}'
        )


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
    jitter = None
    content = None
    if args.floors_file is not None:
        content = json.loads(args.floors_file.read_text(encoding='utf-8'))
        floors, jitter = content['floors'], content['jitter']
    check_labels(args.results[0], args.results[1], content)
    before, after = (load_result(path) for path in args.results)
    sys.stdout.write(render(before, after, floors, args.target, jitter))


if __name__ == '__main__':
    main()
