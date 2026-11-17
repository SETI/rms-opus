"""The option probe: the shapes it pairs, how it times them, and when a pair is valid."""

from __future__ import annotations

import re
from typing import Any

import MySQLdb
import pytest

from benchmarks import bench_db, option_probe, web_scenarios
from benchmarks.app_servers import ServerError
from benchmarks.option_probe import ORDERED, UNORDERED, Pair, ProbeSession
from benchmarks.query_capture import EXPLAIN_RUNS, Block, Statement
from benchmarks.resort_probe import ProbeError

#: The broad search's build, as the application issues it.
_BUILD = (
    'SELECT 2,ROW_NUMBER() OVER (ORDER BY `obs_general`.`time1` ASC,`obs_general`.`opus_id` '
    'ASC),`obs_general`.`id` FROM `obs_general` WHERE `obs_general`.`time2` >= -631195181.0e0 '
    'AND `obs_general`.`time1` <= 568036837.0e0'
)

#: The columns and joins of an empty-search page read.
_PAGE_HEAD = (
    'SELECT `obs_general`.`opus_id`,`mult_i`.`label` FROM `obs_general` LEFT JOIN `mult` AS '
    '`mult_i` ON `mult_i`.`field_id` = 2 AND `mult_i`.`id`=`obs_general`.`instrument_id`'
)


def _page(first: int, last: int) -> str:
    """Return the empty search's read of one page, as the application issues it."""
    return (
        f'{_PAGE_HEAD} INNER JOIN (SELECT `search_results`.`obs_general_id` AS `id`,'
        '`search_results`.`sort_order` FROM `search_results` WHERE `search_results`.`search_id` '
        '= 1) AS `results` ON `obs_general`.`id`=`results`.`id` AND `results`.`sort_order` '
        f'BETWEEN {first} AND {last} ORDER BY `results`.`sort_order`'
    )


def _count(table: str, column: str, search_id: int) -> str:
    """Return a mult count of one search, as the application issues it."""
    joined = 'id' if table == 'obs_general' else 'obs_general_id'
    return (
        f'SELECT `{table}`.`{column}`,COUNT(*) AS `{column}__count` FROM `{table}`,'
        '(SELECT `search_results`.`obs_general_id` AS `id`,`search_results`.`sort_order` FROM '
        f'`search_results` WHERE `search_results`.`search_id` = {search_id}) AS `results` '
        f'WHERE `{table}`.`{joined}`=`results`.`id` GROUP BY `{table}`.`{column}`'
    )


_LOOKUP = 'SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = 1'


def _blocks(*, pages: bool = True, mults: bool = True) -> list[Block]:
    """Return a capture holding every block the probe reads."""
    blocks = [
        Block(
            'search.broad/result_count',
            'api/meta/result_count.json',
            [
                Statement(1, _LOOKUP),
                Statement(
                    1,
                    'INSERT INTO `search_results` (`search_id`,`sort_order`,`obs_general_id`) '
                    + _BUILD,
                ),
            ],
        )
    ]
    if pages:
        blocks += [
            Block(
                'pages.empty/page_1',
                'api/data.json',
                [Statement(1, _LOOKUP), Statement(1, _page(1, 100))],
            ),
            Block('pages.empty/page_last', 'api/data.json', [Statement(1, _page(301, 400))]),
        ]
    if mults:
        for search, search_id in (('broad', 2), ('selective', 3)):
            for slug, table, column in (
                ('instrument', 'obs_general', 'instrument_id'),
                ('target', 'obs_general_target_name', 'mult_id'),
                ('imagetype', 'obs_type_image', 'image_type_id'),
            ):
                blocks.append(
                    Block(
                        f'mults.{search}/mults_{slug}',
                        f'__api/meta/mults/{slug}.json',
                        [Statement(1, _LOOKUP), Statement(1, _count(table, column, search_id))],
                    )
                )
    return blocks


def test_the_scenario_file_issues_every_request_the_probe_reads() -> None:
    """The empty search's pages, the broad search's build, and the mult counts of each
    search the facet pairs, a widget on a child table among them."""
    config = web_scenarios.load_web_config()
    tags = {
        f'{scenario.name}/{request.name}'
        for scenario in config.scenarios
        for request in scenario.requests
    }
    assert {f'pages.empty/{request}' for request in option_probe.EMPTY_PAGE_REQUESTS} <= tags
    assert option_probe.BUILD_TAG in tags
    for search in option_probe.MULTS_SEARCHES:
        assert f'mults.{search}/mults_instrument' in tags
        assert f'mults.{search}/mults_imagetype' in tags


def test_a_page_read_becomes_a_range_of_the_rank() -> None:
    """The columns and joins stay; the join to the search's rows gives way to the rank."""
    assert option_probe.rank_page(_page(301, 400)) == (
        f'{_PAGE_HEAD} WHERE `obs_general`.`default_rank` BETWEEN 301 AND 400 '
        'ORDER BY `obs_general`.`default_rank`'
    )


def test_a_page_read_with_a_predicate_of_its_own_is_refused() -> None:
    """The empty search's reads have no WHERE; one that has would be given a second."""
    captured = _page(1, 100).replace(' INNER JOIN', ' WHERE `obs_general`.`id` > 0 INNER JOIN')
    with pytest.raises(ProbeError, match='WHERE clause of its own'):
        option_probe.rank_page(captured)


def test_a_statement_that_does_not_page_is_not_rewritten() -> None:
    """Only a read of a range of the search's rows is a page read."""
    with pytest.raises(ProbeError, match='does not page'):
        option_probe.rank_page(_BUILD)


def test_a_build_is_renumbered_by_the_rank() -> None:
    """Only the window's order changes."""
    assert option_probe.rank_build(_BUILD) == _BUILD.replace(
        '`obs_general`.`time1` ASC,`obs_general`.`opus_id` ASC', '`obs_general`.`default_rank` ASC'
    )


@pytest.mark.parametrize(
    'captured',
    [_BUILD.replace('`time1` ASC', '`time1` DESC'), _BUILD + ' UNION ' + _BUILD],
    ids=['another-order', 'twice'],
)
def test_a_build_not_numbered_once_in_the_default_order_is_refused(captured: str) -> None:
    """A re-sort's build, or two windows, have no one window to renumber."""
    with pytest.raises(ProbeError, match='default order'):
        option_probe.rank_build(captured)


def test_the_page_read_is_the_one_statement_reading_a_range_of_the_search() -> None:
    """The lookup beside it is not the page."""
    assert option_probe.empty_page_read(_blocks(), 'page_1') == _page(1, 100)


@pytest.mark.parametrize('reads', [0, 2])
def test_a_page_block_with_no_read_or_two_is_refused(reads: int) -> None:
    """Which statement read the page must be unambiguous."""
    blocks = [Block('pages.empty/page_1', 'api', [Statement(1, _page(1, 100))] * reads)]
    with pytest.raises(ProbeError, match=f'{reads} statements read a page'):
        option_probe.empty_page_read(blocks, 'page_1')


def test_each_mult_count_of_a_search_is_found_by_its_request() -> None:
    """Every mults_<slug> block of the search's scenario gives its one count."""
    counts = option_probe.mult_counts(_blocks(), 'selective')
    assert list(counts) == ['mults_instrument', 'mults_target', 'mults_imagetype']
    assert counts['mults_imagetype'] == _count('obs_type_image', 'image_type_id', 3)


def test_a_capture_without_a_searchs_counts_is_refused() -> None:
    """A capture from a scenario file without the mults scenarios gives nothing to pair."""
    with pytest.raises(ProbeError, match='no mult count of the broad search'):
        option_probe.mult_counts(_blocks(mults=False), 'broad')


def test_a_count_block_with_two_counts_is_refused() -> None:
    """Which statement counted must be unambiguous."""
    statement = Statement(1, _count('obs_general', 'instrument_id', 2))
    blocks = [Block('mults.broad/mults_instrument', 'api', [statement, statement])]
    with pytest.raises(ProbeError, match='2 statements count mults'):
        option_probe.mult_counts(blocks, 'broad')


def test_the_counted_column_is_named_as_a_qualified_name() -> None:
    """The table and column, lowercased, as a mult field's qualified name is."""
    captured = _count('OBS_General', 'Instrument_ID', 2)
    assert option_probe.counted_column(captured) == 'obs_general.instrument_id'


def test_a_statement_that_counts_nothing_has_no_counted_column() -> None:
    """A page read is not a mult count."""
    with pytest.raises(ProbeError, match='not a mult count'):
        option_probe.counted_column(_page(1, 100))


def test_a_facet_count_of_a_hub_column_reads_the_search_by_observation() -> None:
    """The count joins the facet table's key to the captured search's rows."""
    generated = option_probe.facet_count(
        _count('obs_general', 'instrument_id', 7), 'obs_general.instrument_id'
    )
    assert generated == (
        'SELECT `obs_facet`.`obs_general.instrument_id`,COUNT(*) AS `facet__count` FROM '
        '`obs_facet`,(SELECT `search_results`.`obs_general_id` AS `id`,'
        '`search_results`.`sort_order` FROM `search_results` WHERE '
        '`search_results`.`search_id` = 7) AS `results` WHERE '
        '`obs_facet`.`obs_general_id`=`results`.`id` GROUP BY `obs_facet`.`obs_general.instrument_id`'
    )


def test_a_facet_count_of_a_child_column_leaves_out_observations_without_a_row() -> None:
    """An observation with no row in the child table holds NULL in the facet table."""
    generated = option_probe.facet_count(
        _count('obs_type_image', 'image_type_id', 7), 'obs_type_image.image_type_id'
    )
    assert ' AND `obs_facet`.`obs_type_image.image_type_id` IS NOT NULL GROUP BY' in generated


@pytest.mark.parametrize(
    'captured',
    [
        'SELECT `obs_general`.`instrument_id`,COUNT(*) AS `x__count` FROM `obs_general` GROUP BY 1',
        _count('obs_general', 'instrument_id', 2)
        + ' UNION '
        + _count('obs_general', 'instrument_id', 3),
    ],
    ids=['no-search', 'two-searches'],
)
def test_a_count_of_no_search_or_of_two_has_no_facet_count(captured: str) -> None:
    """The facet count reads one search's rows, the one the captured count reads."""
    with pytest.raises(ProbeError, match='reads the results of searches'):
        option_probe.facet_count(captured, 'obs_general.instrument_id')


def test_a_count_whose_column_the_facet_table_does_not_hold_is_not_probed() -> None:
    """A list column's junction table has no facet column; the reason is kept."""
    pairs, not_probed = option_probe.facet_pairs(_blocks(), None)
    assert [pair.name for pair in pairs] == [
        'broad.mults_instrument',
        'broad.mults_imagetype',
        'selective.mults_instrument',
        'selective.mults_imagetype',
    ]
    assert not_probed['broad.mults_target'] == (
        'obs_facet holds no column obs_general_target_name.mult_id'
    )
    assert all(pair.prototype is None for pair in pairs)


def test_a_facet_table_lacking_a_column_it_should_hold_is_refused() -> None:
    """A prototype built without a column cannot answer that column's count."""
    with pytest.raises(ProbeError, match=r'has no column obs_type_image\.image_type_id'):
        option_probe.facet_pairs(_blocks(), {'obs_general.instrument_id'})


class _Server:
    """A server answering the probe's statements, and recording each with its restarts."""

    def __init__(
        self,
        *,
        rank: bool = False,
        facet: bool = False,
        rows: dict[str, Any] | None = None,
        refuse: str | None = None,
    ) -> None:
        """Hold which prototypes the schema carries, each shape's rows by a text it
        contains, and a text whose statements the server refuses."""
        self.rank = rank
        self.facet = facet
        self.rows = rows or {}
        self.refuse = refuse
        self.log: list[str] = []
        self.connections = 0
        self._answer: list[tuple[Any, ...]] = []

    def connect(self) -> _Server:
        """Open a connection, which is this server."""
        self.connections += 1
        self.log.append('connect')
        return self

    def restart(self) -> None:
        """Note a restart."""
        self.log.append('restart')

    def session(self) -> ProbeSession:
        """Return the probe's way to this server."""
        return ProbeSession(connect=self.connect, restart=self.restart)

    def cursor(self) -> _Server:
        """Return itself as the cursor."""
        return self

    def close(self) -> None:
        """Close nothing."""

    def _rows_of(self, statement: str) -> Any:
        """Return the rows a shape returns: the first entry whose text it contains."""
        for text, rows in self.rows.items():
            if text in statement:
                return rows
        if '`facet__count`' in statement or '__count`' in statement:
            return [(1, 10), (2, 5)]
        if 'BETWEEN' in statement:
            return [('a', 'x'), ('b', 'y')]
        return 30

    def execute(self, statement: str, parameters: Any) -> None:
        """Answer the prototype lookups, a shape's EXPLAIN ANALYZE, its count or its rows."""
        self.log.append(statement)
        if self.refuse is not None and self.refuse in statement:
            raise MySQLdb.OperationalError(1054, f'refused {self.refuse}')
        if statement.startswith('SELECT COUNT(*) FROM information_schema.COLUMNS'):
            self._answer = [(1 if self.rank else 0,)]
            return
        if statement.startswith('SELECT COLUMN_NAME FROM information_schema.COLUMNS'):
            names = ['obs_general_id', 'obs_general.instrument_id', 'obs_type_image.image_type_id']
            self._answer = [(name,) for name in names] if self.facet else []
            return
        if statement.startswith('EXPLAIN ANALYZE '):
            self._answer = [
                (
                    '-> Group aggregate  (actual time=0.5..2.5 rows=7 loops=1)\n'
                    '    -> Table scan on obs_general  (cost=9 rows=50) '
                    '(actual time=0.1..1.0 rows=40 loops=1)\n',
                )
            ]
            return
        if statement.startswith('SELECT COUNT(*) FROM ('):
            self._answer = [(self._rows_of(statement),)]
            return
        self._answer = list(self._rows_of(statement))

    def fetchall(self) -> list[tuple[Any, ...]]:
        """Return the last statement's rows."""
        return self._answer


def test_a_schema_without_the_prototypes_times_the_captured_shapes_alone() -> None:
    """Each captured shape is timed once from a restart, under the pair's own names, and
    each option says it is not carried; nothing fails."""
    server = _Server()
    metrics, samples, details = option_probe.probe(server.session(), _blocks())
    assert server.log.count('restart') == 7
    assert metrics['db.option_probe.default_rank.broad_build.rows_returned'] == 30
    assert metrics['db.option_probe.default_rank.empty_page_1.rows_returned'] == 2
    assert metrics['db.option_probe.facet.selective.mults_imagetype.rows_returned'] == 2
    assert not any('.captured.' in name for name in metrics)
    assert not any(name.endswith('_ratio') for name in metrics)
    assert len(samples['db.option_probe.facet.broad.mults_instrument.cold_s']) == 1
    assert len(samples['db.option_probe.facet.broad.mults_instrument.warm_s']) == EXPLAIN_RUNS
    assert metrics['db.option_probe.default_rank.valid'] == 1.0
    assert metrics['db.option_probe.facet.valid'] == 1.0
    assert details['problems'] == []
    assert details['options']['default_rank']['carried'] is False
    assert 'no default_rank prototype' in details['options']['default_rank']['skipped']
    assert details['options']['facet']['pairs']['broad.mults_instrument']['answer'] == 'captured'


def test_each_shape_is_timed_cold_on_a_new_connection_after_a_restart_then_warm() -> None:
    """A restart, a new connection, the cold EXPLAIN ANALYZE, then EXPLAIN_RUNS more,
    before any other shape's restart."""
    server = _Server(rank=True)
    option_probe.probe(server.session(), _blocks(mults=False))
    first = server.log.index('restart')
    following = server.log[first : first + 3 + EXPLAIN_RUNS]
    assert following[:2] == ['restart', 'connect']
    assert all(entry.startswith('EXPLAIN ANALYZE ') for entry in following[2:])
    assert server.log[first + 2 + 1 + EXPLAIN_RUNS] == 'restart'


def test_a_schema_carrying_both_prototypes_times_both_shapes_of_every_pair() -> None:
    """The pair's names hold the prototype shape, the captured shape is under .captured.,
    and the ratios compare them."""
    server = _Server(rank=True, facet=True)
    metrics, _samples, details = option_probe.probe(server.session(), _blocks())
    assert server.log.count('restart') == 14
    prefix = 'db.option_probe.default_rank.empty_page_last'
    assert metrics[f'{prefix}.valid'] == 1.0
    assert f'{prefix}.captured.cold_s' in metrics
    assert metrics[f'{prefix}.cold_ratio'] == pytest.approx(
        metrics[f'{prefix}.cold_s'] / metrics[f'{prefix}.captured.cold_s']
    )
    assert f'{prefix}.warm_ratio' in metrics
    pair = details['options']['default_rank']['pairs']['empty_page_last']
    assert pair['answer'] == 'prototype'
    assert 'default_rank` BETWEEN 301 AND 400' in pair['statements']['prototype']
    facet = details['options']['facet']['pairs']['selective.mults_imagetype']
    assert '`obs_facet`' in facet['statements']['prototype']
    assert details['problems'] == []


def test_rounds_time_every_shape_from_that_many_cold_starts() -> None:
    """Each round restarts once per shape; the samples hold every round's figures."""
    server = _Server()
    metrics, samples, details = option_probe.probe(server.session(), _blocks(), rounds=3)
    assert server.log.count('restart') == 3 * 7
    name = 'db.option_probe.default_rank.broad_build'
    assert len(samples[f'{name}.cold_s']) == 3
    assert len(samples[f'{name}.warm_s']) == 3 * EXPLAIN_RUNS
    assert metrics[f'{name}.warm_analyze_ms'] == 2.5
    assert metrics[f'{name}.rows_examined'] == 40
    assert details['rounds'] == 3


def test_fewer_than_one_round_is_refused() -> None:
    """A probe of no rounds would time nothing."""
    with pytest.raises(ValueError, match='at least 1'):
        option_probe.probe(_Server().session(), _blocks(), rounds=0)


def _pair(rows: str) -> Pair:
    """Return a pair with both shapes, comparing its rows as given."""
    return Pair('facet', 'p', 'SELECT 1', 'SELECT 2', rows)


@pytest.mark.parametrize(
    ('rows', 'found', 'problem'),
    [
        (UNORDERED, {'captured': [], 'prototype': []}, 'captured shape returned no rows'),
        (UNORDERED, {'captured': [(1, 2)], 'prototype': [(1, 2), (3, 4)]}, 'returned 2 rows, not'),
        (UNORDERED, {'captured': [(1, 2)], 'prototype': [(1, 3)]}, 'other rows'),
        (ORDERED, {'captured': [(1,), (2,)], 'prototype': [(2,), (1,)]}, 'other rows'),
        (option_probe.COUNTED, {'captured': 30, 'prototype': 29}, 'returned 29 rows, not'),
        (
            option_probe.COUNTED,
            {'captured': 30, 'prototype': 0},
            'prototype shape returned no rows',
        ),
    ],
    ids=['no-rows', 'more-rows', 'other-counts', 'other-order', 'other-count', 'no-count'],
)
def test_a_pair_whose_shapes_disagree_or_return_nothing_is_a_failed_measurement(
    rows: str, found: dict[str, Any], problem: str
) -> None:
    """No rows, other row counts, or other rows are never a pass."""
    problems = option_probe.pair_problems(_pair(rows), found)
    assert any(problem in sentence for sentence in problems), problems


@pytest.mark.parametrize(
    ('rows', 'found'),
    [
        (UNORDERED, {'captured': [(1, 2), (3, 4)], 'prototype': [(3, 4), (1, 2)]}),
        (ORDERED, {'captured': [(1,), (2,)], 'prototype': [(1,), (2,)]}),
        (option_probe.COUNTED, {'captured': 30, 'prototype': 30}),
        (UNORDERED, {'captured': [(1, 2)]}),
    ],
    ids=['counts-in-any-order', 'pages-in-order', 'builds-of-one-count', 'captured-alone'],
)
def test_a_pair_whose_shapes_agree_is_valid(rows: str, found: dict[str, Any]) -> None:
    """Counts agree in any order, pages in order, builds by count; a captured shape alone
    is valid when it returned rows."""
    assert option_probe.pair_problems(_pair(rows), found) == []


def test_a_prototype_returning_other_rows_is_recorded_invalid() -> None:
    """The facet count's rows unlike the captured count's mark that pair invalid alone."""
    server = _Server(facet=True, rows={'`obs_facet`.`obs_general.instrument_id`': [(1, 99)]})
    metrics, _samples, details = option_probe.probe(server.session(), _blocks())
    assert metrics['db.option_probe.facet.broad.mults_instrument.valid'] == 0.0
    assert metrics['db.option_probe.facet.broad.mults_imagetype.valid'] == 1.0
    assert metrics['db.option_probe.facet.valid'] == 0.0
    assert metrics['db.option_probe.default_rank.valid'] == 1.0
    assert details['problems'][0].startswith('facet.broad.mults_instrument: ')


def test_a_rank_page_returning_the_rows_in_another_order_is_recorded_invalid() -> None:
    """A page is compared in order: the rank must page as the search's order does."""
    server = _Server(rank=True, rows={'`default_rank` BETWEEN 1 AND': [('b', 'y'), ('a', 'x')]})
    metrics, _samples, _details = option_probe.probe(server.session(), _blocks(mults=False))
    assert metrics['db.option_probe.default_rank.empty_page_1.valid'] == 0.0
    assert metrics['db.option_probe.default_rank.empty_page_last.valid'] == 1.0


def test_a_refused_statement_fails_its_pair_and_the_others_are_still_timed() -> None:
    """A server error in one shape is that pair's problem; the probe goes on."""
    server = _Server(rank=True, refuse='`default_rank` ASC')
    metrics, _samples, details = option_probe.probe(server.session(), _blocks())
    assert metrics['db.option_probe.default_rank.broad_build.valid'] == 0.0
    assert metrics['db.option_probe.default_rank.empty_page_1.valid'] == 1.0
    problems = details['options']['default_rank']['pairs']['broad_build']['problems']
    assert problems[0].startswith('the prototype shape failed: ')
    assert 'db.option_probe.default_rank.broad_build.captured.cold_s' in metrics


def test_a_capture_without_an_options_shapes_fails_that_option_alone() -> None:
    """The rank's page reads missing fail the rank; the facet's pairs are measured."""
    server = _Server()
    metrics, _samples, details = option_probe.probe(server.session(), _blocks(pages=False))
    assert metrics['db.option_probe.default_rank.valid'] == 0.0
    assert metrics['db.option_probe.facet.valid'] == 1.0
    assert re.match(
        r'default_rank: pages\.empty/page_1: the capture holds 0 blocks', details['problems'][0]
    )


class _DeadServer(_Server):
    """A server that cannot be restarted."""

    def restart(self) -> None:
        """Fail to come back."""
        raise ServerError('mysqld exited 1')


def test_a_probe_whose_server_cannot_restart_is_recorded_as_a_failed_measurement() -> None:
    """A server that does not come back fails every option, as a problem, not a raise."""
    metrics, samples, details = option_probe.measure(_DeadServer().session(), _blocks())
    assert metrics == {
        'db.option_probe.default_rank.valid': 0.0,
        'db.option_probe.facet.valid': 0.0,
    }
    assert samples == {}
    assert details['problems'] == ['ServerError: mysqld exited 1']


def test_a_probe_that_runs_is_measured_as_probe_measures_it() -> None:
    """With nothing failing, the result is the probe's own."""
    metrics, _samples, details = option_probe.measure(_Server().session(), _blocks(), rounds=2)
    assert metrics['db.option_probe.facet.valid'] == 1.0
    assert details['rounds'] == 2


def _arguments(*extra: str) -> list[str]:
    """Return a bench_db command line with the given options."""
    arguments = ['--scale', 'fixture', '--side', 'after', '--pr', 'PR-nn', '--session', 'a']
    return [*arguments, '--python', 'python', '--repo-root', '.', *extra]


def test_bench_db_refuses_the_probe_without_a_capture(monkeypatch: pytest.MonkeyPatch) -> None:
    """The probe reads the searches the capture's requests built, so it needs one."""
    monkeypatch.delenv('PYTHONPATH', raising=False)
    with pytest.raises(SystemExit, match='--option-probe reads'):
        bench_db.main(_arguments('--option-probe'))


def test_bench_db_refuses_fewer_than_one_round(monkeypatch: pytest.MonkeyPatch) -> None:
    """A round count below one is refused before anything runs."""
    monkeypatch.delenv('PYTHONPATH', raising=False)
    with pytest.raises(SystemExit, match='at least 1'):
        bench_db.main(_arguments('--dump-queries', '--option-probe', '--option-probe-rounds', '0'))


def test_bench_db_records_a_failed_probe_and_then_fails() -> None:
    """A probe whose pair failed is added to the run with the run's other figures kept, and
    makes the command fail, naming both probes' problems; a valid one does not."""
    server = _Server(facet=True, rows={'`obs_facet`.`obs_general.instrument_id`': [(1, 99)]})
    run: dict[str, Any] = {
        'metrics': {'db.schema.data_bytes': 1.0},
        'samples': {},
        'details': {'resort_probe': {'problems': ['shapes differ']}},
    }
    bench_db.record_option_probe(run, server.session(), _blocks(), 1)
    assert run['metrics']['db.schema.data_bytes'] == 1.0
    assert run['metrics']['db.option_probe.facet.valid'] == 0.0
    failure = bench_db.probe_failure(run)
    assert failure is not None
    assert 'the re-sort probe is not a valid measurement: shapes differ' in failure
    assert 'the option probe is not a valid measurement: facet.broad.mults_instrument' in failure
    assert bench_db.probe_failure({'details': {'option_probe': {'problems': []}}}) is None
