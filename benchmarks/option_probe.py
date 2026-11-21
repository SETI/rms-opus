"""Time the statements a measured option would answer with, beside the application's own.

Each measured schema option (`benchmarks.option_prototypes`) answers some requests with a
statement other than the one the application issues. The probe pairs each such
statement, the **prototype** shape, with the **captured** shape the application issued
for the same request, taken from the session's capture, and times both on one side's
schema. Its statements are generated at replay time from the capture and the built
searches' ids, and are written to no capture file. The pairs:

``default_rank`` (on a schema whose ``obs_general`` has the ``default_rank`` column)
    ``empty_page_1`` and ``empty_page_last``: the empty search's first and last page
    read as ``obs_general.default_rank BETWEEN <first> AND <last>``, with no search
    built, against the page reads of ``pages.empty/page_1`` and ``pages.empty/page_last``
    from ``search_results`` (`rank_page`). ``broad_build``: the ``SELECT`` of the broad
    search's build, ``search.broad/result_count``, numbering its rows by
    ``default_rank`` against the captured one numbering them by ``(time1, opus_id)``
    (`rank_build`).
``facet`` (on a schema with the ``obs_facet`` table)
    ``<search>.mults_<slug>``: each mult count of the ``mults.broad`` and
    ``mults.selective`` scenarios whose column ``obs_facet`` holds, counted from
    ``obs_facet`` joined to the search's ``search_results`` rows (`facet_count`), against
    the captured count from the column's own table. A count of a column ``obs_facet``
    does not hold, such as a list column's junction table, is not probed, and the
    details say so.

On a schema without an option's prototype the probe times the option's captured shapes
alone and says the option is not carried; that is not a failure. So a floor session on a
copy without either option (`benchmarks.option_prototypes`, ``none``) measures the noise
of the captured shapes.

**Cold and warm.** Each shape is timed by restarting the server (a cold start, with
``O_DIRECT`` and no buffer pool dump), then running its ``SELECT`` under ``EXPLAIN
ANALYZE`` once on a new connection, its **cold** time, and `EXPLAIN_RUNS` more times on
the same connection, whose median is its **warm** time. A round times every shape so; a
probe makes ``rounds`` rounds, and each metric is the median of the rounds' values, each
round's value in the run's samples (for the warm figures, each round's median; every
execution is in the details). After the timed runs each shape's rows are read once: a page
or a count is fetched whole and compared with its pair's, row for row (in order for a
page), and a build, too large to fetch, is reduced on the server to its row count and two
checksums of the numbering it gives each observation (`build_checksum`), so a rank that
numbers the rows otherwise than ``(time1, opus_id)`` does not pass.

**Metrics**, under ``db.option_probe.<option>.<pair>.``: ``cold_s``, ``warm_s``,
``cold_analyze_ms`` and ``warm_analyze_ms`` (the server's time to its top iterator's
last row), ``rows_examined`` (from its plans) and ``rows_returned``, of the shape the
schema answers the pair with: the prototype shape where the schema carries the option,
the captured one otherwise. So `benchmarks.compare` compares a floor session on a copy
without the option with a run on a prototype's copy pair by pair, and ``compare
--floors`` takes the floors of the captured shapes. Where the prototype shape is timed, the
captured shape's figures on the same schema are under ``.captured.``, with
``cold_ratio`` and ``warm_ratio``, the prototype's time over the captured one's. Each
pair has ``valid``, 1 or 0, and each option ``db.option_probe.<option>.valid`` and
``db.option_probe.<option>.carried``, 1 where the schema carries its prototype.

A pair is a failed measurement when a shape returned no rows, the two shapes returned
different numbers of rows or different rows, or a statement failed in any round; an
option whose captured shapes the capture lacks fails as a whole. A failed pair records
``valid`` at 0 and no other metric, so nothing ``compare`` judges comes from it; its
figures are in the details with every problem.
"""

from __future__ import annotations

import collections
import contextlib
import re
import statistics
import time
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import MySQLdb

from benchmarks.app_servers import ServerError
from benchmarks.bench_server import OBS_GENERAL_TABLE, query, quote_identifier
from benchmarks.option_prototypes import (
    DEFAULT_RANK_COLUMN,
    FACET_KEY_COLUMN,
    FACET_TABLE,
    facet_columns,
)
from benchmarks.query_capture import EXPLAIN_RUNS, summarize_analyze
from benchmarks.resort_probe import (
    SEARCH_ID_READ,
    WHERE_KEYWORD,
    ProbeError,
    search_build,
    tagged_block,
    top_level,
)

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    from benchmarks.query_capture import Block

#: The options the probe times, in the order it times them.
OPTIONS = ('default_rank', 'facet')

#: The metric names' prefix.
METRIC_PREFIX = 'db.option_probe'

#: The two shapes of a pair, in the order a round times them.
SHAPES = ('captured', 'prototype')

#: The empty search's page requests whose reads the rank answers, of ``pages.empty``.
EMPTY_PAGE_REQUESTS = ('page_1', 'page_last')

#: The block whose search build the rank renumbers.
BUILD_TAG = 'search.broad/result_count'

#: The searches whose mult counts the facet table answers, each a ``mults`` scenario.
MULTS_SEARCHES = ('broad', 'selective')

#: How a pair's rows are compared: a page in order, a count as a set of rows, and a
#: build, too large to fetch, by its count and checksums (`build_checksum`).
ORDERED, UNORDERED, COUNTED = 'ordered', 'unordered', 'counted'

#: The columns a search build's ``SELECT`` gives, those of ``search_results`` it fills.
BUILD_COLUMNS = ('search_id', 'sort_order', 'obs_general_id')

#: An empty-search page read: the page's rows of the search's ``search_results`` rows,
#: joined to ``obs_general`` and ordered by their place in the search.
_PAGE_JOIN = re.compile(
    r'\s+INNER\s+JOIN\s+\(\s*SELECT\s+`search_results`\.`obs_general_id`\s+AS\s+`id`\s*,\s*'
    r'`search_results`\.`sort_order`\s+FROM\s+`search_results`\s+WHERE\s+'
    r'`search_results`\.`search_id`\s*=\s*\d+\s*\)\s+AS\s+`results`\s+ON\s+'
    r'`obs_general`\.`id`\s*=\s*`results`\.`id`\s+AND\s+`results`\.`sort_order`\s+'
    r'BETWEEN\s+(?P<first>\d+)\s+AND\s+(?P<last>\d+)\s+ORDER\s+BY\s+`results`\.`sort_order`\s*\Z',
    re.IGNORECASE,
)

#: A search build's numbering of its rows in the default sort order.
_DEFAULT_WINDOW = re.compile(
    r'ROW_NUMBER\(\)\s*OVER\s*\(\s*ORDER\s+BY\s+`obs_general`\.`time1`\s+ASC\s*,\s*'
    r'`obs_general`\.`opus_id`\s+ASC\s*\)',
    re.IGNORECASE,
)

#: A mult count: the counted column, then the count, as the application builds it.
_MULT_COUNT = re.compile(
    r'\A\s*SELECT\s+`(?P<table>[^`]+)`\.`(?P<column>[^`]+)`\s*,\s*COUNT\(\*\)\s+AS\s+'
    r'`[^`]*__count`',
    re.IGNORECASE,
)


@dataclass(frozen=True)
class Pair:
    """One request an option answers, in its two shapes.

    Attributes:
        option: The option, one of `OPTIONS`.
        name: The pair's name within the option.
        captured: The application's ``SELECT``, from the capture.
        prototype: The option's ``SELECT``, or None on a schema without the option.
        rows: How the two shapes' rows are compared: `ORDERED`, `UNORDERED` or
            `COUNTED`.
    """

    option: str
    name: str
    captured: str
    prototype: str | None
    rows: str

    @property
    def statements(self) -> dict[str, str]:
        """Each shape's ``SELECT``, by shape, in `SHAPES` order; the captured one alone on a
        schema without the option."""
        shapes = {'captured': self.captured}
        if self.prototype is not None:
            shapes['prototype'] = self.prototype
        return shapes

    @property
    def answer(self) -> str:
        """The shape the schema answers the request with."""
        return 'captured' if self.prototype is None else 'prototype'

    @property
    def prefix(self) -> str:
        """The pair's metric prefix."""
        return f'{METRIC_PREFIX}.{self.option}.{self.name}'


@dataclass(frozen=True)
class Checksum:
    """A search build's rows, reduced on the server.

    Attributes:
        rows: How many rows the build numbers.
        weighted: The sum over the rows of each row's number times its observation's id.
        hashed: The ``BIT_XOR`` over the rows of the first 64 bits of the ``MD5`` of
            ``<number>,<id>``.
    """

    rows: int
    weighted: int
    hashed: int


#: What a shape's rows are read as: the rows of a page or a count, a build's checksum.
Rows = list[tuple[Any, ...]] | Checksum


@dataclass(frozen=True)
class ProbeSession:
    """How the probe reaches the side's schema, and gives it a cold start.

    Attributes:
        connect: Opens a connection with the side's schema as its default.
        restart: Stops the server and starts it again.
    """

    connect: Callable[[], Any]
    restart: Callable[[], None]


def empty_page_read(blocks: Sequence[Block], request: str) -> str:
    """Return the empty search's page read of one of its page requests.

    Parameters:
        blocks: The capture's blocks.
        request: The ``pages.empty`` request, one of `EMPTY_PAGE_REQUESTS`.

    Returns:
        The block's one statement reading a range of the search's ``search_results`` rows.

    Raises:
        ProbeError: If the capture holds no such block, or its block holds no such read
            or several.
    """
    tag = f'pages.empty/{request}'
    reads = [
        statement.text
        for statement in tagged_block(blocks, tag).statements
        if _PAGE_JOIN.search(statement.text)
    ]
    if len(reads) != 1:
        raise ProbeError(f'{tag}: {len(reads)} statements read a page of the search, not one')
    return reads[0]


def rank_page(captured: str) -> str:
    """Return a page read of the empty search as a range of the rank instead.

    Parameters:
        captured: The application's page read (`empty_page_read`).

    Returns:
        The same columns and joins, with the join to the search's rows replaced by
        ``WHERE obs_general.default_rank BETWEEN <first> AND <last>`` ordered by the rank,
        the bounds being the captured range of ``sort_order``.

    Raises:
        ProbeError: If the statement is not such a read, or has a predicate of its own,
            which the empty search's reads never have.
    """
    match = _PAGE_JOIN.search(captured)
    if match is None:
        raise ProbeError('the captured page read does not page through the search')
    head = captured[: match.start()]
    if len(top_level(head, WHERE_KEYWORD.pattern)) > 0:
        raise ProbeError('the captured page read has a WHERE clause of its own')
    rank = f'`obs_general`.{quote_identifier(DEFAULT_RANK_COLUMN)}'
    return (
        f'{head} WHERE {rank} BETWEEN {int(match["first"])} AND {int(match["last"])} '
        f'ORDER BY {rank}'
    )


def rank_build(captured: str) -> str:
    """Return a search build's ``SELECT`` numbering its rows by the rank instead.

    Parameters:
        captured: The ``SELECT`` of the application's build (`search_build`).

    Returns:
        The same statement with its ``ROW_NUMBER() OVER (ORDER BY time1 ASC, opus_id
        ASC)`` ordered by ``default_rank`` instead.

    Raises:
        ProbeError: If the statement numbers its rows in the default order not exactly
            once.
    """
    found = list(_DEFAULT_WINDOW.finditer(captured))
    if len(found) != 1:
        raise ProbeError(
            f'the captured build numbers its rows in the default order {len(found)} times, not once'
        )
    rank = f'`obs_general`.{quote_identifier(DEFAULT_RANK_COLUMN)}'
    window = f'ROW_NUMBER() OVER (ORDER BY {rank} ASC)'
    return captured[: found[0].start()] + window + captured[found[0].end() :]


def mult_counts(blocks: Sequence[Block], search: str) -> dict[str, str]:
    """Return each mult count of one search's ``mults`` scenario.

    Parameters:
        blocks: The capture's blocks.
        search: The search, as ``web.toml`` names it.

    Returns:
        Each ``mults_<slug>`` request's one mult count, by request name, in capture order.

    Raises:
        ProbeError: If the capture holds no mult count request of the search, or one
            whose block holds no mult count or several.
    """
    scenario = f'mults.{search}/'
    counts: dict[str, str] = {}
    for block in blocks:
        if not block.tag.startswith(f'{scenario}mults_'):
            continue
        found = [s.text for s in block.statements if _MULT_COUNT.match(s.text)]
        if len(found) != 1:
            raise ProbeError(f'{block.tag}: {len(found)} statements count mults, not one')
        counts[block.tag.removeprefix(scenario)] = found[0]
    if len(counts) == 0:
        raise ProbeError(f'the capture holds no mult count of the {search} search')
    return counts


def counted_column(captured: str) -> str:
    """Return the qualified name of the column a mult count counts.

    Parameters:
        captured: The mult count.

    Returns:
        ``<table>.<column>``, lowercased, as a mult field's qualified name is.

    Raises:
        ProbeError: If the statement is not a mult count.
    """
    match = _MULT_COUNT.match(captured)
    if match is None:
        raise ProbeError('the statement is not a mult count')
    return f'{match["table"]}.{match["column"]}'.lower()


def facet_count(captured: str, column: str) -> str:
    """Return a mult count from the facet table, of the search the captured count reads.

    Parameters:
        captured: The application's mult count, joined to one search's results.
        column: The facet column, the counted field's qualified name.

    Returns:
        The count of ``obs_facet``'s column over the search's ``search_results`` rows,
        joined by observation as the application joins them. A column of a table other
        than ``obs_general`` leaves out the observations holding NULL, which have no row
        in that table and so no row in the captured count.

    Raises:
        ProbeError: If the captured count reads no search's results, or several.
    """
    ids = {int(found) for found in SEARCH_ID_READ.findall(captured)}
    if len(ids) != 1:
        raise ProbeError(f'the captured count reads the results of searches {sorted(ids)}')
    q = quote_identifier
    counted = f'{q(FACET_TABLE)}.{q(column)}'
    condition = f'{q(FACET_TABLE)}.{q(FACET_KEY_COLUMN)}=`results`.`id`'
    if not column.startswith(f'{OBS_GENERAL_TABLE}.'):
        condition += f' AND {counted} IS NOT NULL'
    return (
        f'SELECT {counted},COUNT(*) AS `facet__count` FROM {q(FACET_TABLE)},'  # nosec B608 - quoted identifiers
        '(SELECT `search_results`.`obs_general_id` AS `id`,`search_results`.`sort_order` '
        f'FROM `search_results` WHERE `search_results`.`search_id` = {ids.pop()}) AS `results` '
        f'WHERE {condition} GROUP BY {counted}'
    )


def carried_options(connection: Any) -> dict[str, set[str] | None]:
    """Read which options' prototypes the connection's schema carries.

    Parameters:
        connection: A connection with the side's schema as its default.

    Returns:
        For ``default_rank``, an empty set when ``obs_general`` has the column, and for
        ``facet`` the columns of ``obs_facet``; None for an option the schema lacks.
    """
    rank = query(
        connection,
        'SELECT COUNT(*) FROM information_schema.COLUMNS WHERE TABLE_SCHEMA = DATABASE() '
        'AND TABLE_NAME = %s AND COLUMN_NAME = %s',
        [OBS_GENERAL_TABLE, DEFAULT_RANK_COLUMN],
    )[0][0]
    facet = {
        str(row[0])
        for row in query(
            connection,
            'SELECT COLUMN_NAME FROM information_schema.COLUMNS WHERE TABLE_SCHEMA = DATABASE() '
            'AND TABLE_NAME = %s',
            [FACET_TABLE],
        )
    }
    return {
        'default_rank': set() if int(rank) > 0 else None,
        'facet': facet if len(facet) > 0 else None,
    }


def require_carried(connection: Any, options: Sequence[str]) -> None:
    """Refuse a schema that lacks an option it is meant to carry.

    Parameters:
        connection: A connection with the side's schema as its default.
        options: The options whose prototypes the schema is meant to carry, such as those
            the label's ``prototype`` runs built.

    Raises:
        ProbeError: Naming each of those options the schema does not carry
            (`carried_options`), whose pairs would otherwise be timed in their captured
            shape under the names a prototype's figures take.
    """
    carried = carried_options(connection)
    missing = [option for option in options if option in carried and carried[option] is None]
    if len(missing) > 0:
        raise ProbeError(
            f'the schema is meant to carry the {", ".join(missing)} prototype but does not; '
            "measure the copy the label's prototype run built"
        )


def rank_pairs(blocks: Sequence[Block], carried: set[str] | None) -> list[Pair]:
    """Return the rank option's pairs.

    Parameters:
        blocks: The capture's blocks.
        carried: What `carried_options` read for the option.

    Returns:
        The empty search's page reads and the broad search's build, each with its
        prototype shape where the schema carries the option.

    Raises:
        ProbeError: If the capture lacks a captured shape, or one cannot be rewritten.
    """
    pairs = []
    for request in EMPTY_PAGE_REQUESTS:
        captured = empty_page_read(blocks, request)
        prototype = None if carried is None else rank_page(captured)
        pairs.append(Pair('default_rank', f'empty_{request}', captured, prototype, ORDERED))
    captured = search_build(blocks, BUILD_TAG)
    prototype = None if carried is None else rank_build(captured)
    pairs.append(Pair('default_rank', 'broad_build', captured, prototype, COUNTED))
    return pairs


def facet_pairs(
    blocks: Sequence[Block], carried: set[str] | None
) -> tuple[list[Pair], dict[str, str]]:
    """Return the facet option's pairs, and the mult counts it does not answer.

    Parameters:
        blocks: The capture's blocks.
        carried: What `carried_options` read for the option.

    Returns:
        A pair for each mult count of `MULTS_SEARCHES` whose column is one of
        `benchmarks.option_prototypes.facet_columns`, with its prototype shape where the
        schema carries the option; and each other count's pair name, with the reason.

    Raises:
        ProbeError: If the capture lacks a search's counts, or the schema's facet table
            lacks a column the option holds.
    """
    held = {column.name for column in facet_columns()}
    pairs = []
    not_probed: dict[str, str] = {}
    for search in MULTS_SEARCHES:
        for request, captured in mult_counts(blocks, search).items():
            name = f'{search}.{request}'
            column = counted_column(captured)
            if column not in held:
                not_probed[name] = f'{FACET_TABLE} holds no column {column}'
                continue
            prototype = None
            if carried is not None:
                if column not in carried:
                    raise ProbeError(f"the schema's {FACET_TABLE} has no column {column}")
                prototype = facet_count(captured, column)
            pairs.append(Pair('facet', name, captured, prototype, UNORDERED))
    return pairs, not_probed


def _explain(connection: Any, statement: str) -> dict[str, Any]:
    """Run a ``SELECT`` under ``EXPLAIN ANALYZE`` once, timing it."""
    started = time.perf_counter()
    tree = str(query(connection, f'EXPLAIN ANALYZE {statement}')[0][0])
    elapsed = time.perf_counter() - started
    summary = summarize_analyze(tree)
    return {
        'time_s': elapsed,
        'analyze_ms': float(summary['top_last_row_ms']),
        'plan_rows': float(summary['top_rows']),
        'rows_examined': float(summary['rows_examined']),
        'tree': tree,
    }


def time_shape(session: ProbeSession, statement: str) -> dict[str, Any]:
    """Time one shape cold and warm.

    Parameters:
        session: The side's schema and server.
        statement: The shape's ``SELECT``.

    Returns:
        The cold execution's ``cold_s`` and ``cold_analyze_ms``; the lists ``warm_s`` and
        ``warm_analyze_ms`` of the `EXPLAIN_RUNS` executions after it; ``plan_rows`` and
        ``rows_examined`` of every execution, cold first; and the last tree as
        ``explain_analyze``.
    """
    session.restart()
    with contextlib.closing(session.connect()) as connection:
        runs = [_explain(connection, statement) for _ in range(1 + EXPLAIN_RUNS)]
    cold, warm = runs[0], runs[1:]
    return {
        'cold_s': cold['time_s'],
        'cold_analyze_ms': cold['analyze_ms'],
        'warm_s': [run['time_s'] for run in warm],
        'warm_analyze_ms': [run['analyze_ms'] for run in warm],
        'plan_rows': [run['plan_rows'] for run in runs],
        'rows_examined': [run['rows_examined'] for run in runs],
        'explain_analyze': runs[-1]['tree'],
    }


def build_checksum(connection: Any, statement: str) -> Checksum:
    """Reduce a search build's rows to their count and two checksums, on the server.

    Parameters:
        connection: A connection with the side's schema as its default.
        statement: The build's ``SELECT``, whose columns are `BUILD_COLUMNS`.

    Returns:
        The count, ``SUM(sort_order * obs_general_id)``, and the ``BIT_XOR`` of the first
        64 bits of ``MD5(CONCAT(sort_order, ',', obs_general_id))``: two builds agree on
        all three only when they number the same observations alike. The hash is MD5's,
        not ``CRC32``'s: a CRC is affine over XOR, so two rows exchanging their numbers
        between equal-length texts leave an XOR of CRCs unchanged.
    """
    names = ', '.join(quote_identifier(name) for name in BUILD_COLUMNS)
    reduced = (
        'SELECT COUNT(*), COALESCE(SUM(`sort_order` * `obs_general_id`), 0), '  # nosec B608 - the capture's statement or one generated from it
        "COALESCE(BIT_XOR(CAST(CONV(LEFT(MD5(CONCAT(`sort_order`, ',', `obs_general_id`)), "
        '16), 16, 10) AS UNSIGNED)), 0) '
        f'FROM ({statement}) AS `numbered` ({names})'
    )
    rows, weighted, hashed = query(connection, reduced)[0]
    return Checksum(int(rows), int(weighted), int(hashed))


def _rows(connection: Any, pair: Pair, statement: str) -> Rows:
    """Return a shape's rows, or for a build its checksum."""
    if pair.rows == COUNTED:
        return build_checksum(connection, statement)
    return [tuple(row) for row in query(connection, statement)]


def _row_count(found: Rows) -> int:
    """Return how many rows a shape returned."""
    return found.rows if isinstance(found, Checksum) else len(found)


def pair_problems(pair: Pair, rows: dict[str, Rows]) -> list[str]:
    """Return why a pair's measurement is not valid; none for a valid one.

    Parameters:
        pair: The pair.
        rows: Each timed shape's rows (`_rows`): the rows themselves, or for a build
            their checksum.

    Returns:
        A sentence for each shape that returned no rows, and one when the two shapes
        returned different numbers of rows, different rows, or for a build a different
        numbering.
    """
    counts = {shape: _row_count(found) for shape, found in rows.items()}
    problems = [
        f'the {shape} shape returned no rows' for shape, count in counts.items() if count == 0
    ]
    if 'prototype' not in rows or len(problems) > 0:
        return problems
    captured, prototype = rows['captured'], rows['prototype']
    if counts['captured'] != counts['prototype']:
        problems.append(
            f'the prototype shape returned {counts["prototype"]} rows, not the captured '
            f"shape's {counts['captured']}"
        )
    elif isinstance(captured, Checksum) or isinstance(prototype, Checksum):
        if captured != prototype:
            problems.append(
                'the prototype shape numbered its rows otherwise than the captured shape'
            )
    else:
        same = (
            captured == prototype
            if pair.rows == ORDERED
            else collections.Counter(captured) == collections.Counter(prototype)
        )
        if not same:
            problems.append('the prototype shape returned other rows than the captured shape')
    return problems


def _spread(values: Sequence[float]) -> float:
    """Return the range of some times over their median, or 0 for a zero median."""
    middle = statistics.median(values)
    return (max(values) - min(values)) / middle if middle > 0 else 0.0


def record_pair(
    pair: Pair,
    timings: dict[str, list[dict[str, Any]]],
    rows: dict[str, Rows],
    problems: list[str],
) -> tuple[dict[str, float], dict[str, list[float]], dict[str, Any]]:
    """Turn a pair's timed rounds and rows into its metrics, samples and details.

    Parameters:
        pair: The pair.
        timings: Each timed shape's rounds, each what `time_shape` returned.
        rows: Each shape's rows as read after the timed runs (`pair_problems`).
        problems: Why the pair is not valid; empty for a valid pair.

    Returns:
        The metrics: for a valid pair, each shape's ``cold_s``, ``cold_analyze_ms``,
        ``warm_s`` and ``warm_analyze_ms`` (the median of one value per round, a warm
        value being its round's median), ``rows_examined`` and ``rows_returned``, under
        the pair's prefix for the shape the schema answers with and under ``.captured.``
        for the other, with ``cold_ratio`` and ``warm_ratio`` where both were timed; for a
        pair with a problem, none of those. Always ``valid``. The samples: each timed
        figure's values per round, under its metric's name, for a valid pair only. The
        details: every figure of every round, every warm execution, a build's checksums,
        the statements and the problems.
    """
    metrics: dict[str, float] = {}
    samples: dict[str, list[float]] = {}
    shapes: dict[str, Any] = {}
    for shape, rounds in timings.items():
        # One value per round: a warm figure is its round's median, so the samples hold
        # what compare summarizes over, round by round.
        figures = {
            'cold_s': [run['cold_s'] for run in rounds],
            'cold_analyze_ms': [run['cold_analyze_ms'] for run in rounds],
            'warm_s': [statistics.median(run['warm_s']) for run in rounds],
            'warm_analyze_ms': [statistics.median(run['warm_analyze_ms']) for run in rounds],
        }
        examined = [value for run in rounds for value in run['rows_examined']]
        prefix = pair.prefix if shape == pair.answer else f'{pair.prefix}.{shape}'
        for name, values in figures.items():
            metrics[f'{prefix}.{name}'] = statistics.median(values)
            samples[f'{prefix}.{name}'] = values
        metrics[f'{prefix}.rows_examined'] = statistics.median(examined)
        found = rows.get(shape)
        if found is not None:
            metrics[f'{prefix}.rows_returned'] = _row_count(found)
        shapes[shape] = {
            **figures,
            'warm_executions_s': [value for run in rounds for value in run['warm_s']],
            'warm_executions_analyze_ms': [
                value for run in rounds for value in run['warm_analyze_ms']
            ],
            'rows_examined': examined,
            'plan_rows': [value for run in rounds for value in run['plan_rows']],
            'cold_spread': _spread(figures['cold_s']),
            'warm_spread': _spread(figures['warm_s']),
            'explain_analyze': rounds[-1]['explain_analyze'],
        }
    if pair.prototype is not None and len(timings) == len(SHAPES):
        for state in ('cold', 'warm'):
            captured = metrics[f'{pair.prefix}.captured.{state}_s']
            if captured > 0:
                metrics[f'{pair.prefix}.{state}_ratio'] = (
                    metrics[f'{pair.prefix}.{state}_s'] / captured
                )
    if len(problems) > 0:
        metrics, samples = {}, {}
    metrics[f'{pair.prefix}.valid'] = 0.0 if len(problems) > 0 else 1.0
    if isinstance(rows.get('captured'), Checksum):
        for shape, found in rows.items():
            shapes.setdefault(shape, {})['checksum'] = vars(found)
    details = {
        'answer': pair.answer,
        'statements': pair.statements,
        'rows_compared': pair.rows,
        'shapes': shapes,
        'problems': problems,
    }
    return metrics, samples, details


def _option_pairs(
    blocks: Sequence[Block], carried: dict[str, set[str] | None]
) -> tuple[dict[str, list[Pair]], dict[str, dict[str, Any]]]:
    """Find every option's pairs, recording an option the capture cannot give as failed."""
    found: dict[str, list[Pair]] = {}
    entries: dict[str, dict[str, Any]] = {}
    for option in OPTIONS:
        entry: dict[str, Any] = {
            'carried': carried[option] is not None,
            'not_probed': {},
            'problems': [],
        }
        if carried[option] is None:
            entry['skipped'] = (
                f'the schema carries no {option} prototype; only the captured shapes are timed'
            )
        try:
            if option == 'default_rank':
                found[option] = rank_pairs(blocks, carried[option])
            else:
                found[option], entry['not_probed'] = facet_pairs(blocks, carried[option])
        except ProbeError as err:
            found[option] = []
            entry['problems'].append(str(err))
        entries[option] = entry
    return found, entries


def probe(
    session: ProbeSession, blocks: Sequence[Block], *, rounds: int = 1
) -> tuple[dict[str, float], dict[str, list[float]], dict[str, Any]]:
    """Time every option's pairs cold and warm, round by round, on the side's schema.

    Parameters:
        session: The side's schema and server, in the session whose requests built the
            searches the capture names.
        blocks: The capture's blocks.
        rounds: How many times each shape is timed from a cold start.

    Returns:
        The metrics and samples the module docstring names, and the details: the rounds,
        per option whether the schema carries it (and why its prototype shapes were
        skipped where it does not), the counts it does not answer, its problems, and per
        pair its statements, every execution's figures, the last tree of each shape and
        its problems; and every problem, each prefixed by its option and pair.

    Raises:
        ValueError: If ``rounds`` is less than 1.
    """
    if rounds < 1:
        raise ValueError(f'rounds must be at least 1, not {rounds}')
    with contextlib.closing(session.connect()) as connection:
        carried = carried_options(connection)
    found, entries = _option_pairs(blocks, carried)
    pairs = [pair for option in OPTIONS for pair in found[option]]
    timings: dict[str, dict[str, list[dict[str, Any]]]] = {pair.prefix: {} for pair in pairs}
    failures: dict[str, str] = {}
    for _ in range(rounds):
        for pair in pairs:
            if pair.prefix in failures:
                continue
            for shape, statement in pair.statements.items():
                try:
                    result = time_shape(session, statement)
                except MySQLdb.Error as err:
                    failures[pair.prefix] = f'the {shape} shape failed: {err}'
                    break
                timings[pair.prefix].setdefault(shape, []).append(result)
    metrics: dict[str, float] = {}
    samples: dict[str, list[float]] = {}
    with contextlib.closing(session.connect()) as connection:
        for pair in pairs:
            rows: dict[str, Rows] = {}
            problems = []
            if pair.prefix in failures:
                problems.append(failures[pair.prefix])
            else:
                try:
                    rows = {
                        shape: _rows(connection, pair, statement)
                        for shape, statement in pair.statements.items()
                    }
                except MySQLdb.Error as err:
                    problems.append(f'reading the rows failed: {err}')
                else:
                    problems = pair_problems(pair, rows)
            pair_metrics, pair_samples, details = record_pair(
                pair, timings[pair.prefix], rows, problems
            )
            metrics.update(pair_metrics)
            samples.update(pair_samples)
            entries[pair.option].setdefault('pairs', {})[pair.name] = details
    every_problem = []
    for option in OPTIONS:
        entry = entries[option]
        own = [f'{option}: {problem}' for problem in entry['problems']]
        own += [
            f'{option}.{name}: {problem}'
            for name, details in entry.get('pairs', {}).items()
            for problem in details['problems']
        ]
        metrics[f'{METRIC_PREFIX}.{option}.valid'] = 0.0 if len(own) > 0 else 1.0
        metrics[f'{METRIC_PREFIX}.{option}.carried'] = 1.0 if entry['carried'] else 0.0
        every_problem += own
    details = {'rounds': rounds, 'options': entries, 'problems': every_problem}
    return metrics, samples, details


def measure(
    session: ProbeSession, blocks: Sequence[Block], *, rounds: int = 1
) -> tuple[dict[str, float], dict[str, list[float]], dict[str, Any]]:
    """Run `probe`, recording a probe that could not run as a failed measurement.

    Parameters:
        session: As `probe` takes it.
        blocks: The capture's blocks.
        rounds: As `probe` takes it.

    Returns:
        What `probe` returns; or, when the server refused a statement outside a pair or
        could not be restarted, every option's ``valid`` at 0, no samples, and details
        whose ``problems`` holds the error's message.
    """
    try:
        return probe(session, blocks, rounds=rounds)
    except (MySQLdb.Error, ServerError) as err:
        message = f'{type(err).__name__}: {err}'
        metrics = {f'{METRIC_PREFIX}.{option}.valid': 0.0 for option in OPTIONS}
        return metrics, {}, {'rounds': rounds, 'problems': [message]}
