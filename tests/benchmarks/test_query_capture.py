"""How captured statements are written, read back, classified, and summarized."""

import json
from pathlib import Path

import pytest

from benchmarks import query_capture
from benchmarks.query_capture import Block, Statement

ANALYZE_TREE = """\
-> Limit: 100 row(s)  (cost=10.5 rows=100) (actual time=0.512..3.250 rows=100 loops=1)
    -> Nested loop inner join  (cost=10.5 rows=100) (actual time=0.5..3.2 rows=100 loops=1)
        -> Table scan on cache_12  (cost=1.1 rows=100) (actual time=0.1..0.3 rows=100 loops=1)
        -> Single-row index lookup on obs_general using PRIMARY (id=cache_12.id)  (cost=0.25 rows=1) (actual time=0.02..0.02 rows=1 loops=100)
"""


@pytest.mark.parametrize(
    ('text', 'expected'),
    [
        ('SELECT * FROM obs_general', 'read'),
        ('  select 1', 'read'),
        ('WITH t AS (SELECT 1) SELECT * FROM t', 'read'),
        ('SET SESSION sql_auto_is_null = 0', 'execute'),
        (
            'CREATE TEMPORARY TABLE temp_1 AS SELECT id FROM cache_1 LIMIT 10',
            'create_temporary_select',
        ),
        ('CREATE TEMPORARY TABLE temp_1 (id INT)', 'execute'),
        ('DROP TEMPORARY TABLE temp_1', 'execute'),
        ('INSERT INTO cache_1 (id) SELECT id FROM obs_general', 'write_select'),
        ('CREATE TABLE cache_1 AS SELECT id FROM obs_general', 'write_select'),
        ("INSERT INTO user_searches (selections_json) VALUES ('{}')", 'write'),
        ("UPDATE django_session SET expire_date = NOW() WHERE session_key = 'x'", 'write'),
        ('CREATE TABLE cache_1 (id INT)', 'record'),
        ('DROP TABLE cache_1', 'record'),
        ('SHOW FULL TABLES', 'record'),
        ('COMMIT', 'skip'),
        ('START TRANSACTION', 'skip'),
    ],
)
def test_each_statement_is_replayed_by_its_shape(text: str, expected: str) -> None:
    """Reads are planned, connection state is executed, and other writes never run."""
    assert query_capture.classify(text) == expected


def test_a_write_is_planned_by_its_select() -> None:
    """The plan of an INSERT ... SELECT is the plan of the SELECT it reads."""
    text = 'INSERT INTO cache_1 (id) SELECT id FROM obs_general WHERE time1 > 0'
    assert query_capture.inner_select(text) == 'SELECT id FROM obs_general WHERE time1 > 0'


def test_a_capture_reads_back_as_written(tmp_path: Path) -> None:
    """Tags, URLs, connections and multi-line statements survive the file."""
    blocks = [
        Block(
            tag='pages.empty/page_1',
            url='api/data.json?page=1&limit=100',
            statements=[
                Statement(7, 'SELECT id\nFROM obs_general\nWHERE x = 1'),
                Statement(8, 'SET SESSION a = 1'),
            ],
        ),
        Block(tag='search.empty/result_count', url='__api/meta/result_count.json?reqno=1'),
    ]
    path = tmp_path / 'queries.sql'
    query_capture.write_capture(path, blocks)
    assert query_capture.read_capture(path) == blocks


def test_the_analyze_tree_is_summarized_from_its_top_and_its_tables() -> None:
    """Rows returned come from the top iterator, rows examined from the table accesses."""
    summary = query_capture.summarize_analyze(ANALYZE_TREE)
    assert summary['top_rows'] == 100.0
    assert summary['top_last_row_ms'] == 3.25
    assert summary['tables'] == {'cache_12': 100.0, 'obs_general': 100.0}
    assert summary['rows_examined'] == 200.0


def test_an_empty_tree_reads_as_nothing_examined() -> None:
    """A statement with no iterator reads as zero rows, not as a failure."""
    assert query_capture.summarize_analyze('-> Rows fetched before execution')['top_rows'] == 0.0


def test_access_types_are_read_from_every_table_in_the_plan() -> None:
    """Nested tables are found wherever the JSON plan puts them."""
    plan = {
        'query_block': {
            'nested_loop': [
                {'table': {'table_name': 'cache_1', 'access_type': 'ALL'}},
                {'table': {'table_name': 'obs_general', 'access_type': 'eq_ref'}},
            ]
        }
    }
    assert query_capture.access_types(json.dumps(plan)) == {
        'cache_1': 'ALL',
        'obs_general': 'eq_ref',
    }
