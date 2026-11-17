"""The thread sweep's table, and what it refuses, from hand-built result files."""

import json
from pathlib import Path
from typing import Any

import pytest

from benchmarks import compare, sweep
from benchmarks.results import ResultError

_P95 = 'web.warm.concurrency.shared.p95_s'
_THROUGHPUT = 'web.warm.concurrency.shared.throughput_per_s'


def _environment(threads: int, **changes: Any) -> dict[str, Any]:
    """Return a web result's environment at a thread count, with entries changed."""
    environment: dict[str, Any] = {
        'git_sha': 'abc',
        'git_dirty': False,
        'server_model': f'gunicorn gthread workers=4 threads={threads} '
        f'worker_connections={threads}',
        'concurrency_users': 64,
        'concurrency_only': True,
        'web_scenario_hash': 'h',
    }
    environment.update(changes)
    return environment


def _result(threads: int, p95_values: list[float], **changes: Any) -> dict[str, Any]:
    """Return a result file whose web runs hold one p95 each, at a thread count."""
    runs = []
    for position, value in enumerate(p95_values):
        runs.append(
            {
                'kind': 'web',
                'index': position + 1,
                'load_average_1m': float(position),
                'metrics': {_P95: value, _THROUGHPUT: 10.0 * threads},
                'samples': {},
                'details': {},
            }
        )
    return {'format': 2, 'environment': _environment(threads, **changes), 'runs': runs}


def _path(session: str) -> Path:
    """Return a result file's path, labeled as one session of one PR's after side."""
    return Path(f'2026-11-17_PR-25_after_test_mysql_{session}.json')


def test_a_sweep_s_columns_are_in_thread_order_with_medians_and_spreads() -> None:
    """Each column is one thread count, whatever order the files came in."""
    results = [
        (_path('t8'), _result(8, [3.0, 3.0, 3.0])),
        (_path('t2'), _result(2, [1.0, 2.0, 3.0])),
    ]
    table = sweep.render_sweep(results, [compare.summarize(content) for _, content in results])
    assert '| Metric | threads=2 | threads=8 |' in table
    assert f'| `{_P95}` | 2 (100.0%) | 3 (0.0%) |' in table
    assert f'| `{_THROUGHPUT}` | 20 (0.0%) | 80 (0.0%) |' in table
    assert '- threads=2: 2026-11-17_PR-25_after_test_mysql_t2.json' in table


def test_runs_whose_load_averages_differ_are_still_a_sweep() -> None:
    """The load average is recorded per run, and a sweep's runs differ in it."""
    first, second = _result(2, [1.0]), _result(4, [1.0])
    second['runs'][0]['load_average_1m'] = 9.5
    assert sweep.check_sweep([(_path('a'), first), (_path('b'), second)]) == [2, 4]


@pytest.mark.parametrize(
    ('key', 'value'),
    [('git_sha', 'def'), ('concurrency_users', 32), ('web_scenario_hash', 'other')],
)
def test_results_differing_in_another_entry_are_refused_by_name(key: str, value: Any) -> None:
    """Anything else that differs would be measured with the threads, so it is named."""
    results = [(_path('a'), _result(2, [1.0])), (_path('b'), _result(4, [1.0], **{key: value}))]
    with pytest.raises(ResultError, match=key):
        sweep.check_sweep(results)


def test_an_entry_one_result_lacks_is_a_difference() -> None:
    """A result that does not record an entry the other does was not run alike."""
    second = _result(4, [1.0])
    del second['environment']['concurrency_only']
    with pytest.raises(ResultError, match='concurrency_only'):
        sweep.check_sweep([(_path('a'), _result(2, [1.0])), (_path('b'), second)])


def test_server_models_differing_beyond_the_threads_are_refused() -> None:
    """Another worker count is not a thread sweep."""
    second = _result(4, [1.0])
    second['environment']['server_model'] = (
        'gunicorn gthread workers=8 threads=4 worker_connections=4'
    )
    with pytest.raises(ResultError, match='beyond the thread count'):
        sweep.check_sweep([(_path('a'), _result(2, [1.0])), (_path('b'), second)])


def test_two_results_of_one_thread_count_are_refused() -> None:
    """A thread count measured twice is two sessions, not two points of a sweep."""
    with pytest.raises(ResultError, match='share a thread count'):
        sweep.check_sweep([(_path('a'), _result(2, [1.0])), (_path('b'), _result(2, [1.0]))])


def test_one_result_is_not_a_sweep() -> None:
    """A sweep compares thread counts, so it needs two at least."""
    with pytest.raises(ResultError, match='two or more'):
        sweep.check_sweep([(_path('a'), _result(2, [1.0]))])


def test_results_of_two_scales_are_refused() -> None:
    """A test-scale and a fixture-scale result measure different data."""
    other = Path('2026-11-17_PR-25_after_fixture_mysql_b.json')
    with pytest.raises(ResultError, match='same PR, side, scale and brand'):
        sweep.check_sweep([(_path('a'), _result(2, [1.0])), (other, _result(4, [1.0]))])


@pytest.mark.parametrize(
    'model',
    [
        'gunicorn gthread workers=4',
        'gunicorn gthread workers=4 threads=4 worker_connections=2',
    ],
)
def test_a_server_model_without_a_usable_thread_count_is_refused(model: str) -> None:
    """The thread count is read from server_model, which must name it plainly."""
    with pytest.raises(ResultError):
        sweep.thread_count(model)


def test_compare_prints_a_sweep_and_refuses_its_judging_options(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """``--sweep`` prints the table; a floors file or a target would judge, so it refuses them."""
    paths = []
    for threads in (2, 4):
        path = tmp_path / _path(f't{threads}').name
        path.write_text(json.dumps(_result(threads, [1.0, 1.0, 1.0])), encoding='utf-8')
        paths.append(str(path))
    monkeypatch.setattr(compare, 'load_result', lambda path: json.loads(path.read_text()))
    compare.main(['--sweep', *paths])
    assert '| Metric | threads=2 | threads=4 |' in capsys.readouterr().out
    with pytest.raises(SystemExit):
        compare.main(['--sweep', *paths, '--target', _P95])
    with pytest.raises(SystemExit):
        compare.main(['--sweep', '--floors', *paths])


def test_compare_still_refuses_two_server_models_without_sweep() -> None:
    """Outside a sweep, results of two thread counts are not comparable."""
    with pytest.raises(ResultError, match='server_model'):
        compare.render(_result(2, [1.0]), _result(4, [1.0]), None)
