"""The result-file schema, its labels, and the statistics every comparison rests on."""

import json
import math
from pathlib import Path
from typing import Any

import pytest

from benchmarks import results
from benchmarks.results import Label, ResultError


def _run(kind: str = 'web', **metrics: float) -> dict[str, Any]:
    """Return a run of one kind holding the given metrics."""
    run = results.new_run(kind)
    run['metrics'].update(metrics)
    return run


def test_a_label_names_its_file_and_reads_back() -> None:
    """Every part of a label survives the trip through its file name."""
    label = results.make_label(
        pr='PR-00', side='before', scale='test', session='a', date='2026-11-03'
    )
    assert label.file_name == '2026-11-03_PR-00_before_test_mysql_a.json'
    assert results.parse_label(label.file_name) == label


@pytest.mark.parametrize(
    'name',
    [
        '2026-11-03_PR-00_middle_test_mysql_a.json',
        '2026-11-03_PR-00_before_huge_mysql_a.json',
        '2026-11-03_PR-00_before_test_oracle_a.json',
        '2026-11-03_PR-00_before_test_mysql_a-b.json',
        '2026-11-03_PR-00_floors_test_mysql.json',
    ],
    ids=['side', 'scale', 'brand', 'session', 'floors-file'],
)
def test_a_name_that_is_not_a_result_file_is_refused(name: str) -> None:
    """A name with any part outside its set is not read as a label."""
    with pytest.raises(ResultError, match='is not a result file name'):
        results.parse_label(name)


def test_a_label_with_an_unreadable_part_is_refused() -> None:
    """A label is checked as it is made, not when its file is next read."""
    with pytest.raises(ResultError, match='is not a result file name'):
        results.make_label(pr='PR-00', side='before', scale='test', session='a b')


@pytest.mark.parametrize(
    ('values', 'expected'),
    [
        ([2.0], 0.0),
        ([2.0, 2.0, 2.0], 0.0),
        ([1.0, 2.0, 3.0], 1.0),
        ([10.0, 11.0, 12.0, 13.0], 3.0 / 11.5),
        ([0.0, 0.0, 1.0], math.inf),
    ],
    ids=['one-run', 'equal', 'odd', 'even', 'zero-median'],
)
def test_spread_is_the_range_over_the_median(values: list[float], expected: float) -> None:
    """Spread is a fraction of the median, zero for one run, infinite about zero."""
    assert results.spread(values) == pytest.approx(expected)


@pytest.mark.parametrize(
    ('count', 'expected'),
    [(1, 1.0), (5, 5.0), (19, 19.0), (20, 19.0), (100, 95.0)],
)
def test_p95_is_the_nearest_rank(count: int, expected: float) -> None:
    """The 95th percentile is a member of the values, the maximum below twenty."""
    assert results.p95([float(value) for value in range(count, 0, -1)]) == expected


@pytest.mark.parametrize(
    ('metric', 'expected'),
    [('web.warm.concurrency.shared.throughput_per_s', True), ('import.wall_s', False)],
)
def test_the_metric_name_says_which_way_is_better(metric: str, expected: bool) -> None:
    """Only a rate improves upward."""
    assert results.higher_is_better(metric) is expected


def test_runs_are_appended_and_numbered_per_kind(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Each kind counts its own runs, across separate appends to one file."""
    monkeypatch.setattr(results, 'RESULTS_DIR', tmp_path)
    label = Label('2026-11-03', 'PR-00', 'before', 'fixture', 'mysql', 'a')
    results.append_runs(label, {'git_sha': 'abc'}, [_run('import'), _run('web')])
    path = results.append_runs(label, {'git_sha': 'abc'}, [_run('import')])
    content = json.loads(path.read_text())
    assert [(run['kind'], run['index']) for run in content['runs']] == [
        ('import', 1),
        ('web', 1),
        ('import', 2),
    ]


def test_a_pinned_environment_entry_cannot_change_within_a_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Runs from another commit are refused rather than mixed into the label's file."""
    monkeypatch.setattr(results, 'RESULTS_DIR', tmp_path)
    label = Label('2026-11-03', 'PR-00', 'after', 'fixture', 'mysql', 'a')
    results.append_runs(label, {'git_sha': 'abc'}, [_run()])
    with pytest.raises(ResultError, match="git_sha was 'abc' and is now 'def'"):
        results.append_runs(label, {'git_sha': 'def'}, [_run()])


@pytest.mark.parametrize(
    ('content', 'message'),
    [
        ([], 'holds one JSON object'),
        ({'format': 2, 'environment': {}, 'runs': []}, 'format is 2'),
        ({'format': 1, 'environment': [], 'runs': []}, '"environment" must be an object'),
        ({'format': 1, 'environment': {}, 'runs': {}}, '"runs" must be a list'),
        (
            {'format': 1, 'environment': {}, 'runs': [{'kind': 'web', 'index': 1}]},
            "run 0 has no 'metrics'",
        ),
        (
            {
                'format': 1,
                'environment': {},
                'runs': [
                    {
                        'kind': 'web',
                        'index': 1,
                        'metrics': {'x': 'fast'},
                        'samples': {},
                        'details': {},
                    }
                ],
            },
            'every metric must be a number',
        ),
    ],
    ids=['not-object', 'format', 'environment', 'runs', 'run-key', 'metric-type'],
)
def test_a_malformed_result_is_refused(content: object, message: str) -> None:
    """The schema is checked on every read and write, naming what is wrong."""
    with pytest.raises(ResultError, match=message):
        results.validate_result(content, 'x.json')


def test_filesystem_type_finds_the_longest_mount(tmp_path: Path) -> None:
    """The type reported is the innermost mount's, never the root's by default."""
    assert results.filesystem_type(tmp_path) != 'unknown'


def test_a_result_names_no_machines_directories(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Checkout paths become relative and home paths start with ``~``, wherever they sit."""
    monkeypatch.setattr(results, 'RESULTS_DIR', tmp_path)
    label = Label('2026-11-03', 'PR-00', 'before', 'test', 'mysql', 'a')
    run = _run('import')
    run['details']['arguments'] = [
        '--timing-json',
        str(results.REPO_ROOT / 'benchmarks' / 't.json'),
    ]
    run['details']['holdings'] = {'pds3': str(Path.home() / 'data' / 'holdings')}
    path = results.append_runs(label, {'schema': 'bench_x'}, [run])
    details = json.loads(path.read_text())['runs'][0]['details']
    assert details['arguments'] == ['--timing-json', 'benchmarks/t.json']
    assert details['holdings'] == {'pds3': '~/data/holdings'}
