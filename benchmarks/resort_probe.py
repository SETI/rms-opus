"""Time a built search's re-sort in two shapes: the application's, and one from its rows.

A re-sort of a search the application has already built asks for the same observations
in a new order. The application builds it as a new search: an ``INSERT INTO
search_results ... SELECT`` that evaluates the search's predicate again and numbers the
matching rows in the new order. A re-sort could instead number the built search's own
``search_results`` rows, joined to ``obs_general`` for the sort columns, without
evaluating the predicate. `probe` times the two shapes' ``SELECT`` statements against
one side's schema, in the session that captured them:

* **captured**: the re-sort's ``SELECT`` as the capture recorded it, from the block of the
  re-sort scenario's re-sorted request (`captured_resort`);
* **generated**: the same ``SELECT`` with its ``WHERE`` clause replaced by a join to the
  built search's ``search_results`` rows (`generated_resort`), the built search being the
  one the scenario's default-order request reads (`built_search_id`).

Each shape is run under ``EXPLAIN ANALYZE`` `EXPLAIN_RUNS` times, the two shapes
alternating, and never executed as a write: both would insert the same rows. The probe
records each shape's times, the rows its top iterator returned and the rows it examined,
and the built search's stored ``result_count``. A measurement is valid only when both
shapes returned that many rows and it is not zero (`probe_problems`).

The probe's statements are generated at replay time from the capture and the built
search's id, and are written to no capture file. Both shapes run on any commit whose
searches are rows of ``search_results``.
"""

from __future__ import annotations

import re
import statistics
import time
from typing import TYPE_CHECKING, Any

import MySQLdb

from benchmarks.bench_server import query
from benchmarks.query_capture import EXPLAIN_RUNS, inner_select, summarize_analyze

if TYPE_CHECKING:
    from collections.abc import Sequence

    from benchmarks.query_capture import Block

#: The search whose re-sort is probed: the broad time-range search.
PROBE_SEARCH = 'broad'

#: The re-sort scenario's request in the default order, which reads the built search.
DEFAULT_ORDER_REQUEST = 'default_order'

#: The re-sort scenario's request in the new order, which builds the re-sort.
RESORTED_REQUEST = 'resorted'

#: The two shapes, in the order each round runs them.
SHAPES = ('captured', 'generated')

#: The alias the generated shape joins the built search's rows under.
SET_ALIAS = 'probe_set'

#: A read of one search's rows, which names the search by its id.
_SEARCH_ID = re.compile(r'`search_results`\.`search_id` = (\d+)')

#: The statement that builds a search's rows.
_RESULTS_INSERT = re.compile(r'\AINSERT\s+INTO\s+`search_results`', re.IGNORECASE)

#: A quoted string or name, masked before the clauses are looked for.
_QUOTED = re.compile(r"'(?:[^'\\]|\\.|'')*'|\"(?:[^\"\\]|\\.|\"\")*\"|`(?:[^`]|``)*`", re.DOTALL)

#: The keyword of a statement's predicate.
_WHERE = re.compile(r'\bWHERE\b', re.IGNORECASE)

#: The clause keywords a top-level ``WHERE`` may be followed by.
_TRAILING_CLAUSE = re.compile(r'\b(GROUP\s+BY|ORDER\s+BY|LIMIT|HAVING|WINDOW)\b', re.IGNORECASE)

#: The metric names' prefix.
METRIC_PREFIX = 'db.resort_probe'


class ProbeError(Exception):
    """Raised when the capture does not hold what the probe needs."""


def _block(blocks: Sequence[Block], tag: str) -> Block:
    """Return the one block with a tag.

    Parameters:
        blocks: The capture's blocks.
        tag: ``<scenario>/<request>``.

    Returns:
        The block.

    Raises:
        ProbeError: If the capture holds no block with the tag, or more than one.
    """
    found = [block for block in blocks if block.tag == tag]
    if len(found) != 1:
        raise ProbeError(f'{tag}: the capture holds {len(found)} blocks of that tag, not one')
    return found[0]


def captured_resort(blocks: Sequence[Block], search: str) -> str:
    """Return the ``SELECT`` with which the application built a search's re-sort.

    Parameters:
        blocks: The capture's blocks.
        search: The search, as ``web.toml`` names it.

    Returns:
        The ``SELECT`` of the one ``INSERT INTO search_results`` of the re-sort
        scenario's re-sorted request.

    Raises:
        ProbeError: If that block builds no search, or more than one.
    """
    tag = f'resort.{search}/{RESORTED_REQUEST}'
    inserts = [
        statement.text
        for statement in _block(blocks, tag).statements
        if _RESULTS_INSERT.match(statement.text)
    ]
    if len(inserts) != 1:
        raise ProbeError(f'{tag}: {len(inserts)} statements build a search, not one')
    return inner_select(inserts[0])


def built_search_id(blocks: Sequence[Block], search: str) -> int:
    """Return the id of the built search a re-sort scenario re-sorts.

    Parameters:
        blocks: The capture's blocks.
        search: The search, as ``web.toml`` names it.

    Returns:
        The one search id the re-sort scenario's default-order request reads rows of.

    Raises:
        ProbeError: If that block reads no search's rows, or several searches'.
    """
    tag = f'resort.{search}/{DEFAULT_ORDER_REQUEST}'
    ids = {
        int(match)
        for statement in _block(blocks, tag).statements
        for match in _SEARCH_ID.findall(statement.text)
    }
    if len(ids) != 1:
        raise ProbeError(f'{tag}: reads the rows of searches {sorted(ids)}, not of one')
    return ids.pop()


def _top_level(text: str, keyword: str) -> list[re.Match[str]]:
    """Find a keyword where it appears outside quotes and parentheses.

    Parameters:
        text: A statement, or the end of one.
        keyword: A regular expression for the keyword.

    Returns:
        Each match outside every quoted string or name and every parenthesis, whose
        offsets are the text's own.
    """
    masked = _QUOTED.sub(lambda quoted: ' ' * len(quoted.group()), text)
    depth = 0
    found = []
    for match in re.finditer(rf'[()]|{keyword}', masked, re.IGNORECASE):
        if match.group() == '(':
            depth += 1
        elif match.group() == ')':
            depth -= 1
        elif depth == 0:
            found.append(match)
    return found


def generated_resort(captured: str, search_id: int) -> str:
    """Return a re-sort's ``SELECT`` over a built search's rows rather than its predicate.

    The captured ``SELECT`` keeps its columns, its order and the tables it joins for its
    sort columns; its ``WHERE`` clause, the search's predicate, gives way to a join to the
    built search's ``search_results`` rows under `SET_ALIAS`.

    Parameters:
        captured: The re-sort's ``SELECT`` as the application issued it, which reads
            ``obs_general`` and orders only inside its window function.
        search_id: The built search, whose rows are the set re-sorted.

    Returns:
        The ``SELECT``.

    Raises:
        TypeError: If the search id is not an integer, since it is written into the
            statement.
        ProbeError: If the captured statement has a clause after its ``WHERE``, which the
            generated shape would drop with the predicate.
    """
    if not isinstance(search_id, int):
        raise TypeError(f'search_id {search_id!r} is not an int')
    wheres = _top_level(captured, _WHERE.pattern)
    head = captured
    if wheres:
        head = captured[: wheres[0].start()].rstrip()
        trailing = _top_level(captured[wheres[0].start() :], _TRAILING_CLAUSE.pattern)
        if trailing:
            raise ProbeError(
                f'the captured re-sort has a {trailing[0].group()} clause after its WHERE'
            )
    return (
        f'{head} INNER JOIN `search_results` AS `{SET_ALIAS}` '
        f'ON `{SET_ALIAS}`.`obs_general_id`=`obs_general`.`id` '
        f'WHERE `{SET_ALIAS}`.`search_id` = {search_id}'
    )


def _spread(values: Sequence[float]) -> float:
    """Return the range of some times over their median, or 0 for a zero median."""
    middle = statistics.median(values)
    return (max(values) - min(values)) / middle if middle > 0 else 0.0


def probe_problems(shapes: dict[str, dict[str, Any]], result_count: int | None) -> list[str]:
    """Return why a probe's measurement is not valid; none for a valid one.

    Parameters:
        shapes: Each shape's ``rows_returned`` and ``rows_examined``, every run's.
        result_count: The built search's stored ``result_count``, or None if its row
            holds none.

    Returns:
        A sentence for each problem: no result count, or a zero one; a shape that
        examined or returned no rows in some run; or a shape whose rows differ from the
        result count in some run.
    """
    problems = []
    if not result_count:
        problems.append(f'the built search holds the result count {result_count!r}')
    for name, shape in shapes.items():
        if min(shape['rows_examined']) == 0:
            problems.append(f'the {name} shape examined no rows in a run')
        if min(shape['rows_returned']) == 0:
            problems.append(f'the {name} shape returned no rows in a run')
        elif result_count and set(shape['rows_returned']) != {result_count}:
            problems.append(
                f'the {name} shape returned {sorted(set(shape["rows_returned"]))} rows, '
                f'not the result count {result_count}'
            )
    return problems


def probe(
    connection: Any, blocks: Sequence[Block], search: str = PROBE_SEARCH
) -> tuple[dict[str, float], dict[str, list[float]], dict[str, Any]]:
    """Time both shapes of a built search's re-sort, alternating, on the replay connection.

    Parameters:
        connection: A connection to the side's schema, in the session whose requests
            built the searches the capture names.
        blocks: The capture's blocks.
        search: The search, as ``web.toml`` names it.

    Returns:
        The metrics, under ``db.resort_probe.<search>.``: each shape's ``time_s`` (the
        median wall-clock of its ``EXPLAIN ANALYZE``), ``analyze_ms`` (the median time to
        its top iterator's last row, as the server reports it), ``rows_returned`` and
        ``rows_examined``; ``result_count``; ``ratio``, the generated shape's ``time_s``
        over the captured shape's; and ``valid``, 1 or 0. The samples: each shape's
        times and server times, under their metrics' names. The details: both
        statements, the built search's id, every run's figures, each shape's spread, the
        last ``EXPLAIN ANALYZE`` tree of each, and the problems `probe_problems` found.
    """
    captured = captured_resort(blocks, search)
    search_id = built_search_id(blocks, search)
    statements = {'captured': captured, 'generated': generated_resort(captured, search_id)}
    stored = query(connection, 'SELECT result_count FROM user_searches WHERE id = %s', [search_id])
    result_count = int(stored[0][0]) if stored and stored[0][0] is not None else None
    runs: dict[str, dict[str, Any]] = {
        name: {'times_s': [], 'analyze_ms': [], 'rows_returned': [], 'rows_examined': []}
        for name in SHAPES
    }
    trees: dict[str, str] = {}
    for _ in range(EXPLAIN_RUNS):
        for name in SHAPES:
            started = time.perf_counter()
            tree = str(query(connection, f'EXPLAIN ANALYZE {statements[name]}')[0][0])
            runs[name]['times_s'].append(time.perf_counter() - started)
            summary = summarize_analyze(tree)
            runs[name]['analyze_ms'].append(summary['top_last_row_ms'])
            runs[name]['rows_returned'].append(int(summary['top_rows']))
            runs[name]['rows_examined'].append(int(summary['rows_examined']))
            trees[name] = tree
    prefix = f'{METRIC_PREFIX}.{search}'
    metrics: dict[str, float] = {}
    samples: dict[str, list[float]] = {}
    for name in SHAPES:
        shape = runs[name]
        metrics[f'{prefix}.{name}.time_s'] = statistics.median(shape['times_s'])
        samples[f'{prefix}.{name}.time_s'] = list(shape['times_s'])
        metrics[f'{prefix}.{name}.analyze_ms'] = statistics.median(shape['analyze_ms'])
        samples[f'{prefix}.{name}.analyze_ms'] = list(shape['analyze_ms'])
        metrics[f'{prefix}.{name}.rows_returned'] = statistics.median(shape['rows_returned'])
        metrics[f'{prefix}.{name}.rows_examined'] = statistics.median(shape['rows_examined'])
    problems = probe_problems(runs, result_count)
    if result_count is not None:
        metrics[f'{prefix}.result_count'] = result_count
    captured_time = metrics[f'{prefix}.captured.time_s']
    if captured_time > 0:
        metrics[f'{prefix}.ratio'] = metrics[f'{prefix}.generated.time_s'] / captured_time
    metrics[f'{prefix}.valid'] = 0.0 if problems else 1.0
    details = {
        'search': search,
        'search_id': search_id,
        'result_count': result_count,
        'statements': statements,
        'runs': runs,
        'spreads': {name: _spread(runs[name]['times_s']) for name in SHAPES},
        'explain_analyze': trees,
        'problems': problems,
    }
    return metrics, samples, details


def measure(
    connection: Any, blocks: Sequence[Block], search: str = PROBE_SEARCH
) -> tuple[dict[str, float], dict[str, list[float]], dict[str, Any]]:
    """Run `probe`, recording a capture that lacks a shape or a statement the server
    refused as a failed measurement rather than raising.

    Parameters:
        connection: As `probe` takes it.
        blocks: The capture's blocks.
        search: The search, as ``web.toml`` names it.

    Returns:
        What `probe` returns; or, when it raises `ProbeError` or a server error, the
        metric ``db.resort_probe.<search>.valid`` at 0, no samples, and details whose
        ``problems`` holds the error's message.
    """
    try:
        return probe(connection, blocks, search)
    except (ProbeError, MySQLdb.Error) as err:
        details: dict[str, Any] = {'search': search, 'problems': [f'{type(err).__name__}: {err}']}
        return {f'{METRIC_PREFIX}.{search}.valid': 0.0}, {}, details
