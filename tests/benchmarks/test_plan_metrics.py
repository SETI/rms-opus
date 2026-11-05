"""A replay's planned statements, turned into one time and one row count per block."""

import pytest

from benchmarks.bench_db import plan_metrics


def _read(tag: str, times: list[float], rows: float) -> dict[str, object]:
    """Return a replay entry for one planned read."""
    return {'tag': tag, 'kind': 'read', 'plan': {'times_s': times, 'rows_examined': rows}}


def test_a_block_s_time_is_summed_execution_by_execution() -> None:
    """Every execution of a block gives one time, so the block has a spread."""
    metrics, samples = plan_metrics(
        [
            _read('search.empty/result_count', [1.0, 2.0, 3.0, 4.0, 5.0], 10.0),
            {'tag': 'search.empty/result_count', 'kind': 'execute'},
            _read('search.empty/result_count', [0.5, 0.5, 0.5, 0.5, 0.5], 2.0),
            _read('pages.empty/page_1', [0.1, 0.1, 0.2, 0.1, 0.1], 7.0),
        ]
    )
    assert samples['db.plan.search.empty/result_count.time_s'] == [1.5, 2.5, 3.5, 4.5, 5.5]
    assert metrics['db.plan.search.empty/result_count.time_s'] == 3.5
    assert metrics['db.plan.search.empty/result_count.rows_examined'] == 12.0
    assert metrics['db.plan.pages.empty/page_1.time_s'] == 0.1
    assert set(samples) == {
        'db.plan.search.empty/result_count.time_s',
        'db.plan.pages.empty/page_1.time_s',
    }


def test_a_block_without_a_planned_statement_has_no_metrics() -> None:
    """A block of connection settings only has nothing to plan."""
    assert plan_metrics([{'tag': 'x/y', 'kind': 'execute'}]) == ({}, {})


def test_statements_executed_unequally_are_refused() -> None:
    """Execution by execution sums need the same number of executions throughout."""
    with pytest.raises(ValueError, match='different numbers of times'):
        plan_metrics([_read('x/y', [1.0, 2.0], 1.0), _read('x/y', [1.0], 1.0)])
