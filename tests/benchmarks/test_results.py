"""The result-file schema, its labels, and the statistics every comparison rests on."""

import json
import math
import re
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


def test_runs_with_other_import_keys_are_refused_within_a_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A file's runs share one set of ``--import-key`` values."""
    monkeypatch.setattr(results, 'RESULTS_DIR', tmp_path)
    label = Label('2026-11-03', 'PR-00', 'after', 'test', 'mysql', 'a')
    results.append_runs(label, {'import_keys': {'index_workers': 22}}, [_run()])
    results.append_runs(label, {'import_keys': {'index_workers': 22}}, [_run()])
    with pytest.raises(ResultError, match='import_keys was'):
        results.append_runs(label, {'import_keys': {}}, [_run()])


def test_a_file_whose_runs_record_no_import_keys_holds_runs_that_set_none(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A file whose runs record no ``import_keys`` takes only runs that set none."""
    monkeypatch.setattr(results, 'RESULTS_DIR', tmp_path)
    label = Label('2026-11-03', 'PR-00', 'after', 'test', 'mysql', 'a')
    results.append_runs(label, {'git_sha': 'abc'}, [_run()])
    results.append_runs(label, {'git_sha': 'abc', 'import_keys': {}}, [_run()])
    other = Label('2026-11-03', 'PR-00', 'after', 'test', 'mysql', 'b')
    results.append_runs(other, {'git_sha': 'abc'}, [_run()])
    with pytest.raises(ResultError, match=re.escape('import_keys was {} and is now')):
        results.append_runs(
            other, {'git_sha': 'abc', 'import_keys': {'index_workers': 2}}, [_run()]
        )


def test_runs_with_no_environment_recorded_take_only_runs_that_set_no_import_keys(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The default applies because the file holds runs, not because it records anything."""
    monkeypatch.setattr(results, 'RESULTS_DIR', tmp_path)
    label = Label('2026-11-03', 'PR-00', 'after', 'test', 'mysql', 'a')
    results.append_runs(label, {}, [_run()])
    with pytest.raises(ResultError, match=re.escape('import_keys was {} and is now')):
        results.append_runs(label, {'import_keys': {'index_workers': 2}}, [_run()])


@pytest.mark.parametrize(
    ('first', 'then'),
    [(4, None), (None, 4), (4, 6)],
    ids=['coordinator-then-one-process', 'one-process-then-coordinator', 'other-count'],
)
@pytest.mark.parametrize('key', ['coordinator_importers', 'importers'])
def test_runs_shared_among_importers_another_way_are_refused_within_a_file(
    key: str, first: int | None, then: int | None, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A file's import runs share one importer count, or none (one process)."""
    monkeypatch.setattr(results, 'RESULTS_DIR', tmp_path)
    label = Label('2026-11-11', 'PR-16a', 'after', 'test', 'mysql', 'a')
    results.append_runs(label, {key: first}, [_run('import')])
    results.append_runs(label, {key: first}, [_run('import')])
    with pytest.raises(ResultError, match=f'{key} was {first!r} and is now {then!r}'):
        results.append_runs(label, {key: then}, [_run('import')])


def test_a_file_whose_runs_record_no_importer_count_takes_only_one_process_runs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Runs that record no count imported in one process; a command recording none, such
    as a web run, still appends."""
    monkeypatch.setattr(results, 'RESULTS_DIR', tmp_path)
    label = Label('2026-11-11', 'PR-16a', 'after', 'test', 'mysql', 'a')
    results.append_runs(label, {}, [_run('import')])
    results.append_runs(label, {'coordinator_importers': None}, [_run('import')])
    results.append_runs(label, {}, [_run()])
    with pytest.raises(ResultError, match='coordinator_importers was None and is now 4'):
        results.append_runs(label, {'coordinator_importers': 4}, [_run('import')])


def test_web_runs_that_warmed_or_promoted_another_way_are_refused_within_a_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A file's web runs share their warmed states and their promotion; its import runs,
    which record neither, do not stand for a plain web run."""
    monkeypatch.setattr(results, 'RESULTS_DIR', tmp_path)
    label = Label('2026-11-11', 'PR-18', 'after', 'test', 'mysql', 'a')
    results.append_runs(label, {}, [_run('import')])
    warmed = {'warm_states': ['db-cold'], 'promotion_carts': 10000}
    results.append_runs(label, warmed, [_run()])
    results.append_runs(label, warmed, [_run()])
    with pytest.raises(ResultError, match=re.escape("warm_states was ['db-cold'] and is now []")):
        results.append_runs(label, {**warmed, 'warm_states': []}, [_run()])
    with pytest.raises(ResultError, match='promotion_carts was 10000 and is now None'):
        results.append_runs(label, {**warmed, 'promotion_carts': None}, [_run()])


def test_runs_given_other_django_settings_are_refused_within_a_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A file's runs share their Django settings; runs that record none gave none."""
    monkeypatch.setattr(results, 'RESULTS_DIR', tmp_path)
    label = Label('2026-11-14', 'PR-22', 'after', 'test', 'mysql', 'a')
    results.append_runs(label, {}, [_run('import')])
    forced = {'django_settings': {'STRINGCHOICE_FULL_SEARCH_COUNT_THRESHOLD': 1}}
    with pytest.raises(ResultError, match=re.escape('django_settings was {} and is now')):
        results.append_runs(label, forced, [_run()])
    results.append_runs(label, {'django_settings': {}}, [_run()])
    other = Label('2026-11-14', 'PR-22', 'after', 'test', 'mysql', 'b')
    results.append_runs(other, forced, [_run()])
    with pytest.raises(ResultError, match='django_settings was'):
        results.append_runs(other, {'django_settings': {}}, [_run()])


def test_web_runs_that_planted_another_number_of_rows_are_refused_within_a_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The same request plants fewer rows against a schema with fewer observations, so
    the rows planted are pinned beside the rows asked for."""
    monkeypatch.setattr(results, 'RESULTS_DIR', tmp_path)
    label = Label('2026-11-11', 'PR-18', 'after', 'test', 'mysql', 'a')
    asked = {'warm_states': [], 'promotion_carts': 10000}
    results.append_runs(label, {**asked, 'promotion_cart_rows': 10000}, [_run()])
    with pytest.raises(ResultError, match='promotion_cart_rows was 10000 and is now 9000'):
        results.append_runs(label, {**asked, 'promotion_cart_rows': 9000}, [_run()])


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
            'every metric must be a finite number',
        ),
        (
            {'format': 1, 'environment': {}, 'runs': [{**_run(), 'metrics': {'x': math.nan}}]},
            'every metric must be a finite number',
        ),
        (
            {'format': 1, 'environment': {}, 'runs': [{**_run(), 'metrics': [1.0]}]},
            '"metrics" and "samples" must be objects',
        ),
        (
            {'format': 1, 'environment': {}, 'runs': [{**_run(), 'samples': {'a': ['x']}}]},
            "sample 'a' must be a list of finite numbers",
        ),
    ],
    ids=[
        'not-object',
        'format',
        'environment',
        'runs',
        'run-key',
        'metric-type',
        'metric-nan',
        'metrics-container',
        'sample-type',
    ],
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


@pytest.mark.parametrize(
    ('values', 'kept'),
    [
        ([384.0, 425.2, 385.9], [384.0, 385.9]),
        ([0.19, 0.87, 0.22, 0.19, 0.18], [0.19, 0.22, 0.19, 0.18]),
        ([100.0, 101.0, 103.0], [100.0, 101.0, 103.0]),
        ([10.0, 10.0, 10.0, 12.0, 10.0], [10.0, 10.0, 10.0, 12.0, 10.0]),
        ([1.0, 9.0], [1.0, 9.0]),
        ([1.0, 2.0, 2.0, 100.0], [1.0, 2.0, 2.0]),
    ],
    ids=['slow-import', 'slow-request', 'ordinary', 'mostly-equal', 'two-runs', 'half-equal'],
)
def test_an_outlying_run_is_left_out(values: list[float], kept: list[float]) -> None:
    """Only a run far beyond the others' scatter goes; two runs, or a tie, keep all."""
    assert results.without_outliers(values) == kept


def test_a_run_spread_leaves_the_outlier_out_but_keeps_the_median() -> None:
    """The range is over the kept runs; the median it divides by is over every run."""
    assert results.run_spread([384.0, 425.2, 385.9]) == pytest.approx(1.9 / 385.9)
    assert results.run_spread([1.0, 2.0, 3.0]) == pytest.approx(1.0)
    assert results.run_spread([1.0, 2.0, 3.0], center=4.0) == pytest.approx(0.5)


def test_the_results_root_is_read_from_server_toml_and_expanded(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config = tmp_path / 'server.toml'
    config.write_text('[results]\nroot = "$BENCH_TEST_ROOT/results"\n', encoding='utf-8')
    monkeypatch.setenv('BENCH_TEST_ROOT', str(tmp_path))
    assert results.results_root(config) == (tmp_path / 'results').resolve()
    monkeypatch.delenv('BENCH_TEST_ROOT')
    with pytest.raises(ResultError, match='not set'):
        results.results_root(config)


@pytest.mark.parametrize(
    ('content', 'message'),
    [
        (None, 'cannot read the results directory'),
        ('[results\n', 'cannot read the results directory'),
        ('[server]\n', 'has no \\[results\\] root'),
    ],
    ids=['missing', 'invalid', 'no-root'],
)
def test_an_unusable_server_toml_is_a_result_error(
    tmp_path: Path, content: str | None, message: str
) -> None:
    """A missing, malformed or incomplete file says what is wrong with it."""
    config = tmp_path / 'server.toml'
    if content is not None:
        config.write_text(content, encoding='utf-8')
    with pytest.raises(ResultError, match=message):
        results.results_root(config)


def test_the_results_directory_is_outside_the_repository() -> None:
    assert not results.RESULTS_DIR.is_relative_to(results.REPO_ROOT)
