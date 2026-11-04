"""The before/after table and the floors, from hand-built result files."""

import json
from pathlib import Path
from typing import Any

import pytest

from benchmarks import compare
from benchmarks.results import ResultError


def _result(
    runs: list[dict[str, float]],
    *,
    samples: list[dict[str, list[float]]] | None = None,
    environment: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return a result file whose web runs hold the given metrics and samples."""
    content: dict[str, Any] = {
        'format': 1,
        'environment': environment if environment is not None else {},
        'runs': [],
    }
    for position, metrics in enumerate(runs):
        content['runs'].append(
            {
                'kind': 'web',
                'index': position + 1,
                'metrics': metrics,
                'samples': samples[position] if samples is not None else {},
                'details': {},
            }
        )
    return content


def test_a_metric_is_summarized_by_its_median_and_spread() -> None:
    """Three runs give the middle value and the range over it."""
    summary = compare.summarize(_result([{'m_s': 1.0}, {'m_s': 3.0}, {'m_s': 2.0}]))['m_s']
    assert summary.center == 2.0
    assert summary.spread == 1.0


def test_profiled_runs_are_left_out_of_the_comparison() -> None:
    """A profiled import measures the profiler too, so it never enters a median."""
    content = _result([{'import.wall_s': 10.0}])
    content['runs'].append(
        {
            'kind': 'import_profile',
            'index': 1,
            'metrics': {'import.wall_s': 99.0},
            'samples': {},
            'details': {},
        }
    )
    assert compare.summarize(content)['import.wall_s'].values == (10.0,)


def test_the_concurrency_p95_is_pooled_across_runs() -> None:
    """The pooled p95 is not the median of the per-run p95s."""
    pools = [
        {'web.warm.concurrency.shared.latency_s': [1.0] * 19 + [10.0]},
        {'web.warm.concurrency.shared.latency_s': [1.0] * 20},
    ]
    runs = [
        {'web.warm.concurrency.shared.p95_s': 1.0},
        {'web.warm.concurrency.shared.p95_s': 1.0},
    ]
    summary = compare.summarize(_result(runs, samples=pools))['web.warm.concurrency.shared.p95_s']
    assert summary.center == 1.0
    assert summary.spread == 0.0
    pools[1]['web.warm.concurrency.shared.latency_s'] = [5.0] * 20
    runs[1]['web.warm.concurrency.shared.p95_s'] = 5.0
    pooled = compare.summarize(_result(runs, samples=pools))['web.warm.concurrency.shared.p95_s']
    assert pooled.center == 5.0
    assert pooled.spread == pytest.approx((5.0 - 1.0) / 5.0)


@pytest.mark.parametrize(
    ('metric', 'relative', 'floor', 'expected'),
    [
        ('web.warm.search.empty.wall_s', -0.20, 0.10, 'improved'),
        ('web.warm.search.empty.wall_s', -0.05, 0.10, 'within noise'),
        ('web.warm.search.empty.wall_s', 0.14, 0.10, 'within noise'),
        ('web.warm.search.empty.wall_s', 0.16, 0.10, 'regressed'),
        ('web.warm.concurrency.shared.throughput_per_s', 0.20, 0.10, 'improved'),
        ('web.warm.concurrency.shared.throughput_per_s', -0.20, 0.10, 'regressed'),
        ('import.wall_s', -0.5, None, 'no floor'),
        ('import.wall_s', None, 0.1, 'undefined change'),
    ],
    ids=[
        'faster',
        'faster-within-floor',
        'slower-within-margin',
        'slower-beyond-margin',
        'rate-up',
        'rate-down',
        'no-floor',
        'no-relative-change',
    ],
)
def test_a_change_is_judged_against_its_floor(
    metric: str, relative: float | None, floor: float | None, expected: str
) -> None:
    """Improvement needs more than the floor; a regression needs the margin beyond it."""
    assert compare.verdict(metric, relative, floor) == expected


@pytest.mark.parametrize(
    ('before', 'after', 'expected'),
    [(2.0, 1.0, -0.5), (0.0, 0.0, 0.0), (0.0, 1.0, None)],
    ids=['halved', 'both-zero', 'from-zero'],
)
def test_change_is_relative_to_before(before: float, after: float, expected: float | None) -> None:
    """A change from zero has no relative size."""
    assert compare.change(before, after) == expected


def test_the_table_carries_medians_change_floor_role_and_verdict() -> None:
    """A target row is judged against the floors file where it has the metric."""
    before = _result([{'a_s': 10.0}, {'a_s': 10.0}, {'a_s': 10.0}])
    after = _result([{'a_s': 5.0}, {'a_s': 5.0}, {'a_s': 5.0}])
    table = compare.render(before, after, {'a_s': {'floor': 0.1}}, ['a_s'])
    assert '| `a_s` | 10 | 5 | -50.0% | +0.0% / +0.0% | +10.0% | target | improved |' in table


def test_a_before_spread_larger_than_the_floor_replaces_it() -> None:
    """A noisy session judges against its own spread, not the recorded floor."""
    before = _result([{'a_s': 8.0}, {'a_s': 10.0}, {'a_s': 12.0}])
    after = _result([{'a_s': 7.0}, {'a_s': 7.0}, {'a_s': 7.0}])
    table = compare.render(before, after, {'a_s': {'floor': 0.1}}, ['a_s'])
    assert '| +40.0% | target | not improved |' in table


def test_a_metric_neither_target_nor_guard_is_reported_not_judged() -> None:
    """However far it moves, a reported metric gets no verdict."""
    before = _result([{'a_s': 10.0}, {'a_s': 10.0}])
    after = _result([{'a_s': 50.0}, {'a_s': 50.0}])
    assert '| reported | reported |' in compare.render(before, after, None)


@pytest.mark.parametrize(
    ('metric', 'expected'),
    [
        ('import.wall_s', 'guard'),
        ('import.largest.import_s', 'guard'),
        ('import.peak_tree_pss_kb', 'guard'),
        ('db.schema.index_bytes', 'guard'),
        ('web.app-cold.search.empty.wall_s', 'guard'),
        ('web.warm.search.surface_geometry.wall_s', 'guard'),
        ('web.app-cold.pages.empty.page_last.latency_s', 'guard'),
        ('web.warm.fanout.selected.wall_s', 'guard'),
        ('web.app-cold.autocomplete.bundleid.wall_s', 'guard'),
        ('web.warm.autocomplete.bundleid.wall_s', 'reported'),
        ('web.db-cold.search.empty.wall_s', 'reported'),
        ('web.app-cold.search.ring_radius.wall_s', 'reported'),
        ('web.warm.concurrency.shared.p95_s', 'guard'),
        ('web.warm.concurrency.shared.throughput_per_s', 'reported'),
        ('import.invocation.validate.wall_s', 'reported'),
    ],
)
def test_the_guards_are_the_ones_the_acceptance_rule_names(metric: str, expected: str) -> None:
    """Warm autocomplete and db-cold are reported; the named medians are guarded."""
    assert compare.role(metric, [], {}) == expected


def test_a_warm_guard_that_ran_no_statements_on_either_side_is_reported() -> None:
    """A warm scenario that executed nothing on both sides measured only a cache."""
    statements = {'web.warm.search.empty': 0.0}
    assert compare.role('web.warm.search.empty.wall_s', [], statements) == 'reported'


def test_a_target_is_judged_as_a_target_even_when_it_is_a_guard() -> None:
    """Naming a guard as the target makes improvement, not holding, the question."""
    assert compare.role('import.wall_s', ['import.wall_s'], {}) == 'target'


@pytest.mark.parametrize(
    ('metric_role', 'classification', 'expected'),
    [
        ('target', 'improved', 'improved'),
        ('target', 'within noise', 'not improved'),
        ('target', 'regressed', 'not improved'),
        ('guard', 'improved', 'held'),
        ('guard', 'within noise', 'held'),
        ('guard', 'regressed', 'regressed'),
        ('guard', 'no floor', 'no floor'),
        ('reported', 'regressed', 'reported'),
    ],
)
def test_a_role_decides_what_a_classification_means(
    metric_role: str, classification: str, expected: str
) -> None:
    """A target must improve; a guard must not regress; a reported metric is not judged."""
    assert compare.judgement(metric_role, classification) == expected


def _clone_measured(
    bundle_imports: float, base: float, head: float
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Return a before and after result of a change measured on clones."""
    before = _result([])
    before['runs'] = [
        {
            'kind': 'import_unfinalized',
            'index': 1,
            'metrics': {'import.bundle_imports.wall_s': bundle_imports},
            'samples': {},
            'details': {},
        },
        {
            'kind': 'finalize',
            'index': 1,
            'metrics': {'import.finalization.wall_s': base},
            'samples': {},
            'details': {},
        },
    ]
    after = _result([])
    after['runs'] = [
        {
            'kind': 'finalize',
            'index': 1,
            'metrics': {'import.finalization.wall_s': head},
            'samples': {},
            'details': {},
        },
    ]
    return before, after


def test_a_finalization_within_ten_percent_of_the_full_import_holds() -> None:
    """90 s of imports and 10 s of finalization allow the after side 10 s more."""
    before, after = _clone_measured(90.0, 10.0, 20.0)
    ceiling = compare.finalization_ceiling(before, after)
    assert ceiling == {
        'before_finalization_s': 10.0,
        'after_finalization_s': 20.0,
        'before_full_import_s': 100.0,
        'allowance_s': pytest.approx(10.0),
        'excess_s': 10.0,
        'within': 1.0,
    }


def test_a_finalization_beyond_the_ceiling_is_reported_beyond_it() -> None:
    """One second more than the allowance is beyond the ceiling, and the table says so."""
    before, after = _clone_measured(90.0, 10.0, 21.0)
    assert '+11.000 s' in compare.render(before, after, None)
    assert 'beyond the ceiling' in compare.render(before, after, None)


def test_results_without_a_finalization_of_a_copy_have_no_ceiling() -> None:
    """The ceiling replaces the import guards only for a change measured on clones."""
    assert compare.finalization_ceiling(_result([{'a_s': 1.0}]), _result([{'a_s': 1.0}])) is None


def test_a_metric_on_one_side_only_is_listed_unjudged() -> None:
    """A metric only one side measured shows a dash where the other side would be."""
    table = compare.render(_result([{'a_s': 1.0}]), _result([{'b_s': 1.0}]), None)
    assert '| `b_s` | - | 1 | - |' in table


def test_skipped_steps_are_printed_under_the_table() -> None:
    """A step one side does not have is named, so a missing number is explained."""
    before = _result([{'a_s': 1.0}], environment={'skipped_steps': ['write_schema_version']})
    table = compare.render(before, _result([{'a_s': 1.0}]), None)
    assert 'Steps the before side does not have: write_schema_version.' in table


@pytest.mark.parametrize('key', compare.MATCHING_ENVIRONMENT_KEYS)
def test_results_measured_differently_are_refused(key: str) -> None:
    """Two server models, ownerships, cache backends or brands are not compared."""
    before = _result([{'a_s': 1.0}], environment={key: 'one'})
    after = _result([{'a_s': 1.0}], environment={key: 'two'})
    with pytest.raises(ResultError, match=f'differ in {key}'):
        compare.render(before, after, None)


def test_two_agreeing_sessions_give_the_larger_spread() -> None:
    """Sessions whose medians differ less than their spreads agree."""
    first = _result([{'a_s': 9.0}, {'a_s': 10.0}, {'a_s': 11.0}])
    second = _result([{'a_s': 10.0}, {'a_s': 10.5}, {'a_s': 10.0}])
    entry = compare.floors_from_sessions([first, second])['a_s']
    assert entry['floor'] == pytest.approx(0.2)
    assert entry['agree'] is True
    assert entry['noisy'] is False


def test_disagreeing_sessions_give_the_range_of_their_medians() -> None:
    """Medians further apart than any spread set the floor, and are flagged."""
    first = _result([{'a_s': 10.0}, {'a_s': 10.0}])
    second = _result([{'a_s': 20.0}, {'a_s': 20.0}])
    entry = compare.floors_from_sessions([first, second])['a_s']
    assert entry['floor'] == pytest.approx(10.0 / 15.0)
    assert entry['agree'] is False
    assert entry['noisy'] is False


def test_three_sessions_that_still_disagree_mark_the_metric_noisy() -> None:
    """A third session does not hide the disagreement; it is recorded."""
    sessions = [_result([{'a_s': value}, {'a_s': value}]) for value in (10.0, 20.0, 30.0)]
    assert compare.floors_from_sessions(sessions)['a_s']['noisy'] is True


def test_the_floors_file_is_named_for_its_pr_scale_and_brand(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The floors file sits beside the sessions, named as the layout says."""
    monkeypatch.setattr(compare, 'RESULTS_DIR', tmp_path)
    paths = []
    for session, value in (('a', 1.0), ('b', 3.0)):
        path = tmp_path / f'2026-11-03_PR-00_before_fixture_mysql_{session}.json'
        path.write_text(json.dumps(_result([{'a_s': value}])))
        paths.append(path)
    output, disagreeing = compare.write_floors(paths)
    assert output == tmp_path / '2026-11-03_PR-00_floors_fixture_mysql.json'
    assert disagreeing == ['a_s']
    assert json.loads(output.read_text())['sessions'] == [path.name for path in paths]


def test_sessions_of_two_scales_are_not_one_floor(tmp_path: Path) -> None:
    """A floor is per scale; mixing scales is refused."""
    paths = []
    for scale in ('fixture', 'test'):
        path = tmp_path / f'2026-11-03_PR-00_before_{scale}_mysql_a.json'
        path.write_text(json.dumps(_result([{'a_s': 1.0}])))
        paths.append(path)
    with pytest.raises(ResultError, match='not one set of floor sessions'):
        compare.write_floors(paths)


def test_a_floor_needs_two_or_three_sessions(tmp_path: Path) -> None:
    """One session has no between-session range to measure."""
    with pytest.raises(ResultError, match='two sessions, or three'):
        compare.write_floors([tmp_path / '2026-11-03_PR-00_before_fixture_mysql_a.json'])


def test_a_metric_one_session_lacks_still_gets_a_floor() -> None:
    """Every metric the sessions produce has a floor, and the gap is recorded."""
    first = _result([{'a_s': 10.0, 'b_s': 4.0}, {'a_s': 12.0, 'b_s': 5.0}])
    second = _result([{'a_s': 11.0}, {'a_s': 11.0}])
    floors = compare.floors_from_sessions([first, second])
    assert floors['a_s']['missing_from'] == []
    entry = floors['b_s']
    assert entry['floor'] == pytest.approx(1.0 / 4.5)
    assert entry['missing_from'] == [1]
    assert entry['agree'] is False
    assert entry['noisy'] is False
