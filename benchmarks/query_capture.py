"""Capture the SQL the web scenarios issue, write it out, read it back, and replay it.

The statements are captured from the server, not from the application: the general log
is switched on with ``log_output = TABLE`` and emptied before each request, so every
statement logged while a request ran belongs to it. Each request's statements are a
**block**, tagged ``<scenario>/<request>``; each statement keeps the connection that
issued it. A capture file is plain SQL with the tags in comments::

    -- block: pages.empty/page_1 api/data.json?page=1&limit=100
    -- statement: connection 812
    SELECT ...

A capture names the tables of the commit and the session that made it (a per-search
table, say), so it is only replayed by the same side in the same session.

Replaying a block runs its statements in order on one connection. A statement that
changes only that connection's state (``SET``, ``CREATE TEMPORARY TABLE``, ``DROP
TEMPORARY TABLE``, ``USE``) is executed, so a later statement that names its temporary
table finds it; a ``CREATE TEMPORARY TABLE ... SELECT`` is planned first, by its
``SELECT``. A read (``SELECT``, ``WITH``, ``TABLE``) is planned with ``EXPLAIN
ANALYZE``, `EXPLAIN_RUNS` times, and with ``EXPLAIN FORMAT=JSON`` once. A write that
reads (``INSERT ... SELECT``, ``CREATE TABLE ... SELECT``, ``REPLACE ... SELECT``) is
planned by its ``SELECT``. Any other ``INSERT``, ``REPLACE``, ``UPDATE`` or ``DELETE`` is
planned with ``EXPLAIN FORMAT=JSON`` only, never executed. Other DDL and ``SHOW`` are
recorded and neither planned nor executed, because the request already did them; and
transaction control is skipped. A statement that fails to replay fails the replay.
"""

from __future__ import annotations

import contextlib
import json
import re
import statistics
import time
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

import MySQLdb

from benchmarks.bench_server import query

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence
    from pathlib import Path

#: How many times each read is run under ``EXPLAIN ANALYZE``.
EXPLAIN_RUNS = 5

_BLOCK = '-- block: '
_STATEMENT = '-- statement: connection '

#: The general log's command types that carry a statement.
STATEMENT_COMMANDS = ('Query', 'Execute')

#: A number as ``EXPLAIN ANALYZE`` prints one: in decimal, or in exponent notation for
#: the very small and very large (``952e-6``, ``1.2e+6``).
_NUMBER = r'\d+(?:\.\d*)?(?:e[+-]?\d+)?'
_ANALYZE_LINE = re.compile(
    rf'-> (?P<what>.*?)\s+\(cost=[^)]*\)?.*?\(actual time=(?P<first>{_NUMBER})\.\.'
    rf'(?P<last>{_NUMBER}) rows=(?P<rows>{_NUMBER}) loops=(?P<loops>\d+)\)'
)
_ON_TABLE = re.compile(r'\bon (?P<table>\w+)')
_INNER_SELECT = re.compile(r'\b(SELECT|WITH)\b', re.IGNORECASE)


class ReplayError(Exception):
    """Raised when a captured statement cannot be replayed."""


@dataclass
class Statement:
    """One captured statement.

    Attributes:
        connection: The id of the connection that issued it.
        text: The statement.
    """

    connection: int
    text: str


@dataclass
class Block:
    """The statements one scenario request issued.

    Attributes:
        tag: ``<scenario>/<request>``.
        url: The request's URL.
        statements: Its statements, in the order the server logged them.
    """

    tag: str
    url: str
    statements: list[Statement] = field(default_factory=list)


def start_capture(connection: Any) -> None:
    """Send the general log to its table, and switch it on.

    Parameters:
        connection: The harness's connection.
    """
    query(connection, "SET GLOBAL log_output = 'TABLE'")
    query(connection, 'TRUNCATE mysql.general_log')
    query(connection, 'SET GLOBAL general_log = ON')


def stop_capture(connection: Any) -> None:
    """Switch the general log off and empty its table.

    Parameters:
        connection: The harness's connection.
    """
    query(connection, 'SET GLOBAL general_log = OFF')
    query(connection, 'TRUNCATE mysql.general_log')


def capture_block(connection: Any, tag: str, url: str, issue: Callable[[], None]) -> Block:
    """Capture what the server logged while one request ran.

    Parameters:
        connection: The harness's connection, whose own statements are left out.
        tag: The block's tag.
        url: The request's URL.
        issue: Issues the request.

    Returns:
        The block.
    """
    query(connection, 'TRUNCATE mysql.general_log')
    issue()
    own = int(query(connection, 'SELECT CONNECTION_ID()')[0][0])
    # The general log's CSV table is read back in the order it was written.
    rows = query(
        connection,
        'SELECT thread_id, command_type, CONVERT(argument USING utf8mb4) FROM mysql.general_log',
    )
    block = Block(tag=tag, url=url)
    for thread, command, argument in rows:
        if int(thread) == own or command not in STATEMENT_COMMANDS:
            continue
        block.statements.append(Statement(connection=int(thread), text=str(argument).strip()))
    return block


def write_capture(path: Path, blocks: Sequence[Block]) -> None:
    """Write blocks to a capture file.

    Parameters:
        path: The file.
        blocks: The blocks, in capture order.
    """
    lines = [
        '-- Captured by benchmarks/bench_db.py --dump-queries from the harness-owned server.',
        '-- Regenerate it; do not edit it.',
        '',
    ]
    for block in blocks:
        lines.append(f'{_BLOCK}{block.tag} {block.url}')
        for statement in block.statements:
            lines.append(f'{_STATEMENT}{statement.connection}')
            lines.append(statement.text.rstrip().rstrip(';') + ';')
        lines.append('')
    path.write_text('\n'.join(lines), encoding='utf-8')


def read_capture(path: Path) -> list[Block]:
    """Read a capture file back.

    Parameters:
        path: The file `write_capture` wrote.

    Returns:
        The blocks, in file order.
    """
    blocks: list[Block] = []
    current: Statement | None = None
    for line in path.read_text(encoding='utf-8').splitlines():
        if line.startswith(_BLOCK):
            tag, _, url = line[len(_BLOCK) :].partition(' ')
            blocks.append(Block(tag=tag, url=url))
            current = None
        elif line.startswith(_STATEMENT):
            current = Statement(connection=int(line[len(_STATEMENT) :]), text='')
            blocks[-1].statements.append(current)
        elif current is not None:
            current.text = f'{current.text}\n{line}' if current.text != '' else line
    for block in blocks:
        for statement in block.statements:
            statement.text = statement.text.rstrip().removesuffix(';').rstrip()
    return blocks


def classify(text: str) -> str:
    """Say how a statement is replayed.

    Parameters:
        text: The statement.

    Returns:
        ``execute`` (connection state), ``read``, ``write_select`` (a write whose
        ``SELECT`` is planned), ``create_temporary_select`` (executed, its ``SELECT``
        planned first), ``write`` (planned only), ``record`` (DDL and ``SHOW``, kept
        as they are), or ``skip`` (transaction control).
    """
    words = text.split(None, 4)
    first = words[0].upper() if len(words) > 0 else ''
    second = words[1].upper() if len(words) > 1 else ''
    if first in {'START', 'BEGIN', 'COMMIT', 'ROLLBACK', 'SAVEPOINT', 'RELEASE'}:
        return 'skip'
    if first in {'SET', 'USE'} or (first == 'DROP' and second == 'TEMPORARY'):
        return 'execute'
    if first == 'CREATE' and second == 'TEMPORARY':
        return 'create_temporary_select' if _INNER_SELECT.search(text) else 'execute'
    if first in {'SELECT', 'WITH', 'TABLE', '(SELECT'}:
        return 'read'
    if first in {'INSERT', 'REPLACE', 'CREATE'} and _INNER_SELECT.search(text):
        return 'write_select'
    if first in {'INSERT', 'REPLACE', 'UPDATE', 'DELETE'}:
        return 'write'
    return 'record'


def inner_select(text: str) -> str:
    """Return the ``SELECT`` (or ``WITH``) a write statement reads from.

    Parameters:
        text: An ``INSERT ... SELECT``, ``REPLACE ... SELECT`` or ``CREATE ... SELECT``.

    Returns:
        The statement from its first ``SELECT`` or ``WITH`` keyword on.
    """
    match = _INNER_SELECT.search(text)
    assert match is not None
    return text[match.start() :]


def summarize_analyze(plan: str) -> dict[str, Any]:
    """Read the top iterator and the per-table rows out of an ``EXPLAIN ANALYZE`` tree.

    Parameters:
        plan: The tree.

    Returns:
        The top iterator's actual rows returned and its time to the last row in
        milliseconds, and for each table named by an access iterator the rows it
        returned over all its loops, summed as ``rows_examined``.
    """
    lines = [match for line in plan.splitlines() if (match := _ANALYZE_LINE.search(line))]
    tables: dict[str, float] = {}
    for match in lines:
        table = _ON_TABLE.search(match['what'])
        if table is not None:
            rows = float(match['rows']) * int(match['loops'])
            tables[table['table']] = tables.get(table['table'], 0.0) + rows
    if len(lines) == 0:
        return {'top_rows': 0.0, 'top_last_row_ms': 0.0, 'rows_examined': 0.0, 'tables': {}}
    top = lines[0]
    return {
        'top_rows': float(top['rows']) * int(top['loops']),
        'top_last_row_ms': float(top['last']),
        'rows_examined': sum(tables.values()),
        'tables': tables,
    }


def access_types(plan_json: str) -> dict[str, str]:
    """Read each table's access type out of an ``EXPLAIN FORMAT=JSON`` plan.

    Parameters:
        plan_json: The plan.

    Returns:
        The access type (``ALL``, ``ref``, ``range`` ...) of every table the plan names.
    """
    found: dict[str, str] = {}

    def walk(node: object) -> None:
        """Visit every object in the plan."""
        if isinstance(node, dict):
            if 'table_name' in node and 'access_type' in node:
                found[str(node['table_name'])] = str(node['access_type'])
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for value in node:
                walk(value)

    walk(json.loads(plan_json))
    return found


def _plan_read(connection: Any, text: str) -> dict[str, Any]:
    """Plan one read, running it under ``EXPLAIN ANALYZE`` `EXPLAIN_RUNS` times.

    Parameters:
        connection: The replay connection.
        text: The ``SELECT``.

    Returns:
        Every execution's wall-clock in order, their median and spread, the top
        iterator's rows, the rows examined, each table's access type and rows, and both
        plans whole.
    """
    times = []
    analyzed = ''
    for _ in range(EXPLAIN_RUNS):
        started = time.perf_counter()
        analyzed = str(query(connection, f'EXPLAIN ANALYZE {text}')[0][0])
        times.append(time.perf_counter() - started)
    plan_json = str(query(connection, f'EXPLAIN FORMAT=JSON {text}')[0][0])
    middle = statistics.median(times)
    summary = summarize_analyze(analyzed)
    return {
        'times_s': times,
        'median_s': middle,
        'spread': (max(times) - min(times)) / middle if middle > 0 else 0.0,
        'top_rows': summary['top_rows'],
        'rows_examined': summary['rows_examined'],
        'table_rows': summary['tables'],
        'access_types': access_types(plan_json),
        'explain_analyze': analyzed,
        'explain_json': plan_json,
    }


def replay(connection: Any, blocks: Sequence[Block]) -> list[dict[str, Any]]:
    """Replay every block's statements in order on one connection, planning each read.

    Parameters:
        connection: The replay connection, with the side's schema as its default.

    Returns:
        One entry per statement, with its block's tag, the statement, how it was
        replayed, and its plan where it has one.

    Raises:
        ReplayError: Naming the block and statement that failed.
    """
    entries: list[dict[str, Any]] = []
    for block in blocks:
        for position, statement in enumerate(block.statements):
            kind = classify(statement.text)
            entry: dict[str, Any] = {
                'tag': block.tag,
                'position': position,
                'kind': kind,
                'statement': statement.text,
            }
            try:
                if kind == 'read':
                    entry['plan'] = _plan_read(connection, statement.text)
                elif kind in {'write_select', 'create_temporary_select'}:
                    entry['plan'] = _plan_read(connection, inner_select(statement.text))
                elif kind == 'write':
                    entry['explain_json'] = str(
                        query(connection, f'EXPLAIN FORMAT=JSON {statement.text}')[0][0]
                    )
                if kind in {'execute', 'create_temporary_select'}:
                    query(connection, statement.text)
            except MySQLdb.Error as err:
                raise ReplayError(
                    f'{block.tag} statement {position} ({kind}) failed to replay: {err}\n'
                    f'{statement.text[:2000]}'
                ) from err
            entries.append(entry)
    with contextlib.suppress(MySQLdb.Error):
        query(connection, 'ROLLBACK')
    return entries
