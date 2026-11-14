"""The re-sort probe: the two shapes it times, and when its measurement is valid."""

from __future__ import annotations

from typing import Any

import MySQLdb
import pytest

from benchmarks import bench_db, resort_probe
from benchmarks.query_capture import EXPLAIN_RUNS, Block, Statement

#: The re-sort's build as the application issues it.
_CAPTURED = (
    'SELECT 8,ROW_NUMBER() OVER (ORDER BY `obs_general`.`time1` DESC,`obs_general`.`opus_id` '
    'ASC),`obs_general`.`id` FROM `obs_general` WHERE `obs_general`.`time2` >= -631195181.0e0 '
    'AND `obs_general`.`time1` <= 568036837.0e0'
)

#: The page read of the built search, in the default order.
_PAGE = (
    'SELECT `obs_general`.`opus_id` FROM `obs_general` INNER JOIN (SELECT '
    '`search_results`.`obs_general_id` AS `id`,`search_results`.`sort_order` FROM '
    '`search_results` WHERE `search_results`.`search_id` = 2) AS `results` ON '
    '`obs_general`.`id`=`results`.`id` ORDER BY `results`.`sort_order`'
)


def _blocks(*, inserts: int = 1, page: str = _PAGE) -> list[Block]:
    """Return a capture's re-sort blocks for the broad search."""
    default = Block('resort.broad/default_order', 'api/data.json', [Statement(1, page)])
    resorted = Block(
        'resort.broad/resorted',
        'api/data.json?order=-time1,opusid',
        [Statement(1, 'SET SESSION innodb_lock_wait_timeout = 270')]
        + [
            Statement(
                1,
                'INSERT INTO `search_results` (`search_id`,`sort_order`,`obs_general_id`) '
                + _CAPTURED,
            )
            for _ in range(inserts)
        ]
        + [Statement(1, _PAGE.replace('= 2)', '= 8)'))],
    )
    return [Block('search.broad/count', 'api/meta/result_count.json'), default, resorted]


def test_the_captured_shape_is_the_resorted_requests_build() -> None:
    """The captured shape is the SELECT of the re-sorted request's INSERT."""
    assert resort_probe.captured_resort(_blocks(), 'broad') == _CAPTURED


@pytest.mark.parametrize('inserts', [0, 2])
def test_a_resorted_request_that_builds_no_search_or_two_is_refused(inserts: int) -> None:
    """A re-sort answered without a build, or built twice, gives no captured shape."""
    with pytest.raises(resort_probe.ProbeError, match='build a search'):
        resort_probe.captured_resort(_blocks(inserts=inserts), 'broad')


def test_a_capture_without_the_scenario_is_refused() -> None:
    """A capture lacking the re-sort scenario's block gives no shape."""
    with pytest.raises(resort_probe.ProbeError, match='0 blocks'):
        resort_probe.captured_resort(_blocks()[:1], 'broad')


def test_a_capture_holding_the_scenario_twice_is_refused() -> None:
    """Two blocks of one tag leave which re-sort to time ambiguous."""
    blocks = _blocks()
    with pytest.raises(resort_probe.ProbeError, match='2 blocks'):
        resort_probe.captured_resort([*blocks, blocks[2]], 'broad')


def test_the_built_search_is_the_one_the_default_order_request_reads() -> None:
    """The set re-sorted is the search the default-order request pages through."""
    assert resort_probe.built_search_id(_blocks(), 'broad') == 2


def test_a_default_order_request_reading_two_searches_is_refused() -> None:
    """Which search is the set must be unambiguous."""
    page = _PAGE + ' UNION ' + _PAGE.replace('= 2)', '= 3)')
    with pytest.raises(resort_probe.ProbeError, match=r'\[2, 3\]'):
        resort_probe.built_search_id(_blocks(page=page), 'broad')


def test_the_generated_shape_joins_the_built_rows_in_place_of_the_predicate() -> None:
    """The columns and the window keep the captured text; the predicate goes, and the
    built search's rows are joined by observation."""
    generated = resort_probe.generated_resort(_CAPTURED, 2)
    head = _CAPTURED[: _CAPTURED.index(' WHERE ')]
    assert generated == (
        f'{head} INNER JOIN `search_results` AS `probe_set` '
        'ON `probe_set`.`obs_general_id`=`obs_general`.`id` '
        'WHERE `probe_set`.`search_id` = 2'
    )
    assert 'time2' not in generated


def test_a_where_inside_parentheses_or_quotes_is_not_the_predicate() -> None:
    """Only the statement's own WHERE is replaced."""
    captured = (
        "SELECT 8,(SELECT 1 FROM `t` WHERE `t`.`a` = 1),'x WHERE y' FROM `obs_general` "
        'WHERE `obs_general`.`time1` < 5'
    )
    generated = resort_probe.generated_resort(captured, 4)
    assert generated.startswith(
        "SELECT 8,(SELECT 1 FROM `t` WHERE `t`.`a` = 1),'x WHERE y' FROM `obs_general` INNER"
    )
    assert generated.endswith('WHERE `probe_set`.`search_id` = 4')


def test_a_captured_shape_without_a_predicate_gains_the_join() -> None:
    """The empty search's re-sort has no WHERE; the join and the set's WHERE are added."""
    captured = 'SELECT 8,ROW_NUMBER() OVER (ORDER BY `obs_general`.`time1`) FROM `obs_general`'
    generated = resort_probe.generated_resort(captured, 4)
    assert generated.startswith(captured + ' INNER JOIN `search_results` AS `probe_set`')


def test_a_clause_after_the_predicate_is_refused() -> None:
    """A top-level ORDER BY or LIMIT would be dropped with the predicate."""
    with pytest.raises(resort_probe.ProbeError, match='LIMIT'):
        resort_probe.generated_resort(_CAPTURED + ' LIMIT 10', 2)


def test_a_search_id_that_is_not_an_int_is_refused() -> None:
    """The id is written into the statement, so only an int is taken."""
    with pytest.raises(TypeError):
        resort_probe.generated_resort(_CAPTURED, '2 OR 1')  # type: ignore[arg-type]


def _shape(returned: list[int], examined: list[int]) -> dict[str, Any]:
    """Return one shape's per-run rows."""
    return {'rows_returned': returned, 'rows_examined': examined}


def test_a_probe_whose_shapes_return_the_result_count_is_valid() -> None:
    """Both shapes returning the built search's count, having examined rows, is valid."""
    shapes = {'captured': _shape([30] * 5, [40] * 5), 'generated': _shape([30] * 5, [60] * 5)}
    assert resort_probe.probe_problems(shapes, 30) == []


@pytest.mark.parametrize(
    ('shapes', 'count', 'problem'),
    [
        (
            {'captured': _shape([30], [40]), 'generated': _shape([30], [60])},
            0,
            'result count 0',
        ),
        (
            {'captured': _shape([30], [40]), 'generated': _shape([30], [60])},
            None,
            'result count None',
        ),
        (
            {'captured': _shape([0], [40]), 'generated': _shape([30], [60])},
            30,
            'captured shape returned no rows',
        ),
        (
            {'captured': _shape([30], [0]), 'generated': _shape([30], [60])},
            30,
            'captured shape examined no rows',
        ),
        (
            {'captured': _shape([30], [40]), 'generated': _shape([29], [60])},
            30,
            'generated shape returned [29] rows',
        ),
    ],
)
def test_a_probe_that_returned_no_rows_or_others_is_a_failed_measurement(
    shapes: dict[str, dict[str, Any]], count: int | None, problem: str
) -> None:
    """No rows, a zero or missing count, or rows unlike the count is never a pass."""
    problems = resort_probe.probe_problems(shapes, count)
    assert any(problem in sentence for sentence in problems), problems


class _ProbeServer:
    """A connection and cursor answering the probe's statements."""

    def __init__(self, rows: dict[str, int], result_count: int | None) -> None:
        """Hold the rows each shape returns and the built search's count."""
        self.rows = rows
        self.result_count = result_count
        self.executed: list[tuple[str, Any]] = []
        self._answer: list[tuple[Any, ...]] = []

    def cursor(self) -> _ProbeServer:
        """Return itself as the cursor."""
        return self

    def close(self) -> None:
        """Close nothing."""

    def execute(self, statement: str, parameters: Any) -> None:
        """Answer the result count's read, or an EXPLAIN ANALYZE of either shape."""
        self.executed.append((statement, parameters))
        if statement.startswith('SELECT result_count'):
            self._answer = [(self.result_count,)]
            return
        assert statement.startswith('EXPLAIN ANALYZE ')
        shape = 'generated' if '`probe_set`' in statement else 'captured'
        rows = self.rows[shape]
        self._answer = [
            (
                f'-> Window aggregate  (actual time=1.5..2.5 rows={rows} loops=1)\n'
                f'    -> Table scan on obs_general  (cost=9 rows=50) '
                f'(actual time=0.1..1.0 rows={rows + 10} loops=1)\n',
            )
        ]

    def fetchall(self) -> list[tuple[Any, ...]]:
        """Return the last statement's rows."""
        return self._answer


def test_the_probe_alternates_the_shapes_and_records_what_the_gate_reads() -> None:
    """Each shape runs EXPLAIN_RUNS times, alternating; each has its times as samples,
    its rows, and the count of the built search read by its id."""
    server = _ProbeServer({'captured': 30, 'generated': 30}, 30)
    metrics, samples, details = resort_probe.probe(server, _blocks())
    explains = [statement for statement, _ in server.executed if statement.startswith('EXPLAIN')]
    assert len(explains) == 2 * EXPLAIN_RUNS
    assert ['probe_set' in statement for statement in explains] == [False, True] * EXPLAIN_RUNS
    assert ('SELECT result_count FROM user_searches WHERE id = %s', (2,)) in server.executed
    prefix = 'db.resort_probe.broad'
    for shape in resort_probe.SHAPES:
        assert len(samples[f'{prefix}.{shape}.time_s']) == EXPLAIN_RUNS
        assert metrics[f'{prefix}.{shape}.rows_returned'] == 30
        assert metrics[f'{prefix}.{shape}.rows_examined'] == 40
        assert metrics[f'{prefix}.{shape}.analyze_ms'] == 2.5
    assert metrics[f'{prefix}.result_count'] == 30
    assert metrics[f'{prefix}.valid'] == 1.0
    assert f'{prefix}.ratio' in metrics
    assert details['search_id'] == 2
    assert details['problems'] == []
    assert details['statements']['captured'] == _CAPTURED


def test_a_probe_whose_shapes_disagree_is_recorded_invalid() -> None:
    """Rows unlike the result count mark the measurement invalid and say why."""
    server = _ProbeServer({'captured': 30, 'generated': 12}, 30)
    metrics, _samples, details = resort_probe.probe(server, _blocks())
    assert metrics['db.resort_probe.broad.valid'] == 0.0
    assert details['problems']


def test_bench_db_refuses_the_probe_without_a_capture(monkeypatch: pytest.MonkeyPatch) -> None:
    """The probe re-sorts the searches the capture's requests built, so it needs one."""
    monkeypatch.delenv('PYTHONPATH', raising=False)
    arguments = ['--scale', 'fixture', '--side', 'after', '--pr', 'PR-nn', '--session', 'a']
    arguments += ['--python', 'python', '--repo-root', '.', '--resort-probe']
    with pytest.raises(SystemExit, match='--resort-probe re-sorts'):
        bench_db.main(arguments)


class _RefusingServer(_ProbeServer):
    """A server that refuses the generated shape's statement."""

    def execute(self, statement: str, parameters: Any) -> None:
        """Refuse an EXPLAIN ANALYZE naming the built search's rows."""
        if '`probe_set`' in statement:
            raise MySQLdb.OperationalError(1054, "Unknown column 'probe_set.obs_general_id'")
        super().execute(statement, parameters)


def test_a_probe_the_server_refuses_is_recorded_as_a_failed_measurement() -> None:
    """A server error in a shape's statement is a problem of the run, not an exception."""
    server = _RefusingServer({'captured': 30, 'generated': 30}, 30)
    metrics, samples, details = resort_probe.measure(server, _blocks())
    assert metrics == {'db.resort_probe.broad.valid': 0.0}
    assert samples == {}
    assert len(details['problems']) == 1
    assert 'probe_set.obs_general_id' in details['problems'][0]


def test_a_capture_without_the_shapes_is_recorded_as_a_failed_measurement() -> None:
    """A re-sorted request that built no search leaves nothing to time, and says so."""
    server = _ProbeServer({'captured': 30, 'generated': 30}, 30)
    metrics, _samples, details = resort_probe.measure(server, _blocks(inserts=0))
    assert metrics == {'db.resort_probe.broad.valid': 0.0}
    assert 'build a search' in details['problems'][0]
    assert server.executed == []


def test_a_probe_that_runs_is_measured_as_probe_measures_it() -> None:
    """With nothing failing, the result is the probe's own."""
    server = _ProbeServer({'captured': 30, 'generated': 30}, 30)
    metrics, samples, details = resort_probe.measure(server, _blocks())
    assert metrics['db.resort_probe.broad.valid'] == 1.0
    assert len(samples['db.resort_probe.broad.captured.time_s']) == EXPLAIN_RUNS
    assert details['problems'] == []


def test_bench_db_records_a_failed_probe_and_then_fails() -> None:
    """A probe the server refused is added to the run with the run's other figures kept,
    and makes the command fail; a run with a valid probe, or none, does not."""
    server = _RefusingServer({'captured': 30, 'generated': 30}, 30)
    run: dict[str, Any] = {
        'metrics': {'db.schema.data_bytes': 1.0},
        'samples': {},
        'details': {'plans': []},
    }
    bench_db.record_resort_probe(run, server, _blocks())
    assert run['metrics'] == {'db.schema.data_bytes': 1.0, 'db.resort_probe.broad.valid': 0.0}
    assert run['details']['plans'] == []
    failure = bench_db.probe_failure(run)
    assert failure is not None
    assert 'probe_set.obs_general_id' in failure
    assert bench_db.probe_failure({'details': {'resort_probe': {'problems': []}}}) is None
    assert bench_db.probe_failure({'details': {}}) is None
