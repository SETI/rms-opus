"""Time web scenarios against a gunicorn the harness starts, in three cache states.

One **run** is two passes over ``web.toml``'s scenarios. In the **db-cold** pass every
scenario is preceded by the db-cold reset: the search tables emptied with the side's own
reset option, the application stopped, the database server restarted (an exact cold
start, since it runs with ``O_DIRECT`` and no buffer pool dump), the application started,
and the harness's memcached restarted last. In the **app-cold** pass every scenario is
preceded by the app-cold reset (the same, without the database restart) and is then
issued twice: the first time recorded as app-cold, the second as **warm**.

The application is started without a request: the harness waits until every worker has
loaded it, its URLconf included (`benchmarks.gunicorn_hooks`), because a request would
fill the caches the reset has just emptied, and memcached is restarted after that so it
starts every scenario empty. Every worker therefore starts a cold scenario having served
nothing, which the harness checks in the served log before issuing the scenario.

gunicorn hands each connection to whichever worker accepts it, so a scenario issued
twice in succession does not reach the same workers twice, and a worker meeting a
request for the first time pays its own first-use costs. Before the warm repetition the
harness therefore **warms every worker**: it reissues the scenario's requests, with the
scenario's cookies, as many at a time as the server has request slots (so that no one
worker can take them all), until the served log shows that every worker has served
every one of them, and refuses the run if `WARMUP_MAX_ROUNDS` rounds do not get there.
The concurrency scenario's users' requests are warmed the same way.

Before anything is measured the harness asks the side's settings, in the same
environment, which cache backend they chose, and **refuses to run** on Django's
local-memory fallback; after each run it refuses the run if memcached served nothing.

Example, one side's web runs at fixture scale against the schema its import built::

    python -m benchmarks.bench_web --scale fixture --side before --pr PR-nn \\
        --session a --python venv-head/bin/python --repo-root .
"""

from __future__ import annotations

import argparse
import concurrent.futures
import contextlib
import http.cookiejar
import json
import math
import sys
import threading
import time
import urllib.error
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

from benchmarks.app_servers import GunicornServer, MemcachedServer, ServerError
from benchmarks.bench_server import (
    MysqlServer,
    counter_deltas,
    global_status,
    load_server_config,
    query,
    reexec_with_socket,
    server_environment,
    write_opus_config,
)
from benchmarks.import_scenarios import holdings_for
from benchmarks.monitor import read_kb
from benchmarks.results import (
    RESULTS_DIR,
    SCALES,
    SIDES,
    Label,
    append_runs,
    host_environment,
    load_result,
    make_label,
    new_run,
    p95,
    scenario_hash,
)
from benchmarks.sides import Side, SideError, Spelling
from benchmarks.web_scenarios import (
    PAGE_LIMIT,
    Concurrency,
    Request,
    Scenario,
    WebConfig,
    load_web_config,
)
from import_tests.tools import build_run

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

#: The server counters whose movement over each scenario a web result records.
SCENARIO_COUNTERS = (
    'Innodb_buffer_pool_reads',
    'Connections',
    'Sort_merge_passes',
    'Created_tmp_disk_tables',
    'Max_execution_time_exceeded',
)

#: How many statement shapes each scenario keeps, by total latency.
TOP_DIGESTS = 20

#: Seconds a request may take before it counts as an error.
REQUEST_TIMEOUT_S = 3600.0

#: The part of a cache backend's class path that marks Django's local-memory fallback.
LOCMEM_MARKER = 'locmem'

#: How many rounds the warm-up may take to have every worker serve every request.
WARMUP_MAX_ROUNDS = 50


class WebRunError(Exception):
    """Raised when a web run cannot be measured as asked."""


@dataclass
class RequestTiming:
    """One request as issued.

    Attributes:
        name: The request's name within its scenario.
        url: What was requested.
        started: When it started, from `time.perf_counter`.
        latency_s: How long it took to the last byte of the response.
        status: The HTTP status, or 0 when no response came.
        body: The response body, kept only where the harness reads it.
    """

    name: str
    url: str
    started: float
    latency_s: float
    status: int
    body: bytes = b''

    @property
    def failed(self) -> bool:
        """Whether the request counts as an error: no response, or a status of 400 up."""
        return self.status == 0 or self.status >= 400


class Client:
    """Issues requests to the application with one cookie jar, as one browser would."""

    def __init__(self, base_url: str) -> None:
        """Start a client with an empty cookie jar.

        Parameters:
            base_url: The server's root URL.
        """
        self.base_url = base_url
        self.jar = http.cookiejar.CookieJar()
        self._opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.jar))

    def clone(self) -> Client:
        """Return a new client holding a copy of this one's cookies.

        Returns:
            The client, which sends the same session cookie as this one.
        """
        copy = Client(self.base_url)
        for cookie in self.jar:
            copy.jar.set_cookie(cookie)
        return copy

    def get(self, name: str, url: str) -> RequestTiming:
        """Issue one GET and read the whole response.

        ``Connection: close`` goes with every request, because gthread counts an idle
        keep-alive connection against a worker's connections.

        Parameters:
            name: The request's name.
            url: Its URL, relative to the server's root.

        Returns:
            Its timing and status.
        """
        request = urllib.request.Request(  # nosec B310 - a fixed http URL on 127.0.0.1
            f'{self.base_url}/{url}', headers={'Connection': 'close'}
        )
        started = time.perf_counter()
        status = 0
        body = b''
        try:
            with self._opener.open(request, timeout=REQUEST_TIMEOUT_S) as response:  # nosec B310 - http on 127.0.0.1
                body = response.read()
                status = response.status
        except urllib.error.HTTPError as err:
            body = err.read()
            status = err.code
        except (urllib.error.URLError, OSError):
            status = 0
        return RequestTiming(name, url, started, time.perf_counter() - started, status, body)


def result_count(timing: RequestTiming) -> int:
    """Read the count out of a result-count response.

    Parameters:
        timing: The response to ``__api/meta/result_count.json``.

    Returns:
        The count.

    Raises:
        WebRunError: If the request failed or the response holds no count.
    """
    if timing.failed:
        raise WebRunError(f'{timing.url} answered {timing.status}')
    return int(json.loads(timing.body)['data'][0]['result_count'])


#: What `run_sequence` can wrap each request in: given the request, its completed URL,
#: and a function that issues it, return what issuing it returned.
Around = Callable[[Request, str, Callable[[], RequestTiming]], RequestTiming]


def run_sequence(
    client: Client, scenario: Scenario, *, around: Around | None = None
) -> list[RequestTiming]:
    """Issue a scenario's requests one after another.

    A ``pages`` scenario's last-page request is completed from its untimed result
    count; a search with fewer than ten pages asks for its last page as the tenth.

    Parameters:
        client: The scenario's client.
        scenario: The scenario.
        around: Wraps each request, as the query capture does to log its statements,
            or None.

    Returns:
        Every request's timing, untimed ones included, in order.
    """
    timings: list[RequestTiming] = []
    last_page = 1
    for request in scenario.requests:
        url = request.url
        if scenario.last_page_of is not None:
            url = url.replace('{last}', str(last_page))
            if request.name == 'page_10':
                url = url.replace('page=10&', f'page={min(10, last_page)}&')

        def issue(name: str = request.name, url: str = url) -> RequestTiming:
            """Issue the request."""
            return client.get(name, url)

        timing = issue() if around is None else around(request, url, issue)
        timings.append(timing)
        if scenario.last_page_of is not None and request.name == 'build':
            last_page = max(1, math.ceil(result_count(timing) / PAGE_LIMIT))
    return timings


@dataclass
class ConcurrencyOutcome:
    """What one half of the concurrency scenario produced.

    Attributes:
        latencies: Every request's latency.
        errors: How many requests failed.
        throughput_per_s: Requests per second, from the first start to the last end.
        issued: Each request's client and URL, for the warm-up.
    """

    latencies: list[float] = field(default_factory=list)
    errors: int = 0
    throughput_per_s: float = 0.0
    issued: list[tuple[Client, str]] = field(default_factory=list)


def run_concurrency_half(
    clients: Sequence[Client], searches: Sequence[str], fanout: Sequence[Request]
) -> ConcurrencyOutcome:
    """Have one simulated user per search issue its fan-out, all starting together.

    Parameters:
        clients: One client per user, and so one cookie jar and session each.
        searches: Each user's search, as a query string, in the clients' order.
        fanout: The fan-out's requests, with ``{search}`` for the search.

    Returns:
        The latencies, errors and throughput of every user's requests together.
    """
    barrier = threading.Barrier(len(searches))
    results: list[list[RequestTiming]] = [[] for _ in searches]

    def user(position: int) -> None:
        """Issue one user's fan-out once every user is ready."""
        client = clients[position]
        barrier.wait()
        for request in fanout:
            url = request.url.replace('{search}', searches[position])
            results[position].append(client.get(request.name, url))

    threads = [threading.Thread(target=user, args=(position,)) for position in range(len(searches))]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    timings = [timing for user_timings in results for timing in user_timings]
    first = min(timing.started for timing in timings)
    last = max(timing.started + timing.latency_s for timing in timings)
    return ConcurrencyOutcome(
        latencies=[timing.latency_s for timing in timings],
        errors=sum(1 for timing in timings if timing.failed),
        throughput_per_s=len(timings) / (last - first) if last > first else 0.0,
        issued=[
            (clients[position], timing.url)
            for position, user_timings in enumerate(results)
            for timing in user_timings
        ],
    )


def issue_concurrently(tasks: Sequence[tuple[Client, str]], concurrency: int) -> int:
    """Issue requests, each from a copy of its client, so many at a time.

    Parameters:
        tasks: Each request's client, whose cookies it carries, and URL.
        concurrency: How many are in flight at once.

    Returns:
        How many failed.
    """
    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as pool:
        timings = list(pool.map(lambda task: task[0].clone().get('warm-up', task[1]), tasks))
    return sum(1 for timing in timings if timing.failed)


def warm_every_worker(
    issued: Sequence[tuple[Client, str]],
    *,
    workers: Sequence[int],
    concurrency: int,
    served_by: Callable[[], Mapping[str, set[int]]],
    issue: Callable[[Sequence[tuple[Client, str]], int], int],
) -> dict[str, int]:
    """Reissue a scenario's requests until every worker has served every one of them.

    Each round reissues each request some worker has not yet served, as many times as
    `concurrency` and with its own client's cookies, `concurrency` at a time, then asks
    again which workers have served what. With as many requests in flight as the server
    has request slots, no worker can take them all.

    Parameters:
        issued: Each request's client and URL, as the scenario issued them.
        workers: Every worker's process id.
        concurrency: The server's request slots, workers times threads.
        served_by: Returns which workers have served each path and query string.
        issue: Issues requests, so many at a time, and returns how many failed
            (`issue_concurrently`).

    Returns:
        The rounds it took and the requests it issued.

    Raises:
        WebRunError: If a warm-up request fails, or `WARMUP_MAX_ROUNDS` rounds leave a
            request some worker has not served.
    """
    clients: dict[str, Client] = {}
    for client, url in issued:
        clients.setdefault(url, client)
    requests = 0
    rounds = 0
    pending = unserved(list(clients), served_by(), workers)
    while len(pending) > 0:
        if rounds == WARMUP_MAX_ROUNDS:
            raise WebRunError(
                f'after {WARMUP_MAX_ROUNDS} warm-up rounds some worker has still not '
                f'served {pending[:5]}'
            )
        tasks = [(clients[url], url) for url in pending for _ in range(concurrency)]
        failed = issue(tasks, concurrency)
        requests += len(tasks)
        rounds += 1
        if failed > 0:
            raise WebRunError(f'{failed} warm-up requests failed')
        pending = unserved(list(clients), served_by(), workers)
    return {'rounds': rounds, 'requests': requests}


def unserved(
    urls: Sequence[str], served_by: Mapping[str, set[int]], workers: Sequence[int]
) -> list[str]:
    """Return the URLs some worker has not served yet.

    Parameters:
        urls: The URLs, relative to the server's root, as a client issues them.
        served_by: The workers that served each path and query string.
        workers: Every worker's process id.

    Returns:
        The URLs, in the order given, that at least one of the workers has not served.
    """
    every = set(workers)
    return [url for url in urls if not every <= served_by.get(f'/{url}', set())]


def reset_search_tables(
    side: Side, spelling: Spelling, env: Mapping[str, str], errors_log: Path
) -> None:
    """Empty a schema's search tables with the side's own reset option.

    The reset is held to the rule an import run is: it may log an error and still exit
    zero, so ``ERRORS.log`` growing during it fails it too.

    Parameters:
        side: The side whose import runs the reset.
        spelling: The side's spelling of it.
        env: The environment, whose ``OPUS_CONFIG`` names the schema.
        errors_log: The ``ERRORS.log`` under that configuration's import log directory.

    Raises:
        WebRunError: If the reset exits non-zero or logs an error.
    """
    size = errors_log.stat().st_size if errors_log.exists() else 0
    finished = side.run(['-m', 'opus_import', spelling.reset_search_tables], env=env)
    if finished.returncode != 0:
        raise WebRunError(
            f'{spelling.reset_search_tables} exited {finished.returncode}:\n'
            f'{finished.stderr[-4000:]}'
        )
    if errors_log.exists() and errors_log.stat().st_size > size:
        logged = errors_log.read_text(encoding='utf-8', errors='replace')[size:][:4000]
        raise WebRunError(f'{spelling.reset_search_tables} logged an error:\n{logged}')


class WebBench:
    """Runs one side's web runs against one schema."""

    def __init__(
        self,
        *,
        server: MysqlServer,
        memcached: MemcachedServer,
        side: Side,
        spelling: Spelling,
        label: Label,
        config: WebConfig,
        schema: str,
        holdings: tuple[Path, Path],
        single_worker: bool = False,
    ) -> None:
        """Prepare the servers for one side; nothing is started.

        Parameters:
            server: The owned MySQL server, running.
            memcached: The owned memcached, not yet started.
            side: The side being measured.
            spelling: The side's spelling of the search-table reset.
            label: The result file's label.
            config: ``web.toml``.
            schema: The schema to serve.
            holdings: The PDS3 and PDS4 holdings roots the application is given.
            single_worker: Start gunicorn with one worker of one thread instead of
                ``web.toml``'s, so that every request is served by the same process and
                thread, as the query capture needs.
        """
        self.server = server
        self.memcached = memcached
        self.side = side
        self.spelling = spelling
        self.label = label
        self.config = config
        self.schema = schema
        run_dir = label.scratch_dir / 'web'
        self.config_file = write_opus_config(
            run_dir / 'opus.toml',
            schema=schema,
            pds3_holdings=holdings[0],
            pds4_holdings=holdings[1],
            run_dir=run_dir,
            cache_location=memcached.location,
        )
        self.env = server.client_environment(self.config_file)
        self.errors_log = run_dir / 'logs' / build_run.ERRORS_LOG
        self.gunicorn = GunicornServer(
            python=side.python,
            repo_root=side.repo_root,
            env=self.env,
            port=config.server.port,
            workers=1 if single_worker else config.server.workers,
            threads=1 if single_worker else config.server.threads,
            log_dir=run_dir / 'gunicorn',
            app_log_file=run_dir / 'logs' / 'opus_log.txt',
            served_log=run_dir / 'gunicorn' / 'served.log',
        )
        self._connection: Any = None
        self._cache_gets = 0

    @property
    def connection(self) -> Any:
        """The harness's own connection, opened again after a database restart."""
        if self._connection is None:
            self._connection = self.server.connect()
        return self._connection

    def _close_connection(self) -> None:
        """Close the harness's connection before the database restarts."""
        if self._connection is not None:
            with contextlib.suppress(Exception):
                self._connection.close()
            self._connection = None

    def application_settings(self) -> dict[str, Any]:
        """Ask the side's settings which cache they use, and refuse the local-memory one.

        Returns:
            The cache backend, its location, ``CACHE_MIDDLEWARE_SECONDS``, and the
            isolation level a connection reports.

        Raises:
            WebRunError: If the settings fell back to Django's local-memory cache, or
                point at a memcached other than the harness's.
        """
        settings: dict[str, Any] = self.side.probe(['settings'], env=self.env)
        if LOCMEM_MARKER in str(settings['cache_backend']).lower():
            raise WebRunError(
                f'the application chose {settings["cache_backend"]}, the local-memory '
                f'fallback, rather than the harness memcached at {self.memcached.location}: '
                "is pymemcache installed in the side's environment, and memcached running?"
            )
        if settings['cache_location'] != self.memcached.location:
            raise WebRunError(
                f'the application caches at {settings["cache_location"]}, not at the harness '
                f'memcached {self.memcached.location}'
            )
        return settings

    def reset_search_tables(self) -> None:
        """Empty the search tables with the side's own reset option."""
        reset_search_tables(self.side, self.spelling, self.env, self.errors_log)

    def reset(self, state: str) -> None:
        """Bring the servers to a cold state before a scenario.

        Parameters:
            state: ``db-cold`` or ``app-cold``.
        """
        self.reset_search_tables()
        self.gunicorn.stop()
        if state == 'db-cold':
            self._close_connection()
            self.server.restart()
        self.gunicorn.start()
        self.memcached.restart()

    def require_cold(self) -> None:
        """Check that no worker has served a request since the application started.

        Raises:
            WebRunError: Naming what was served, if anything was.
        """
        served = self.gunicorn.served()
        if len(served) > 0:
            raise WebRunError(
                f'a cold scenario would start on workers that have served {served[:5]}'
            )

    def warm_up(self, issued: Sequence[tuple[Client, str]]) -> dict[str, int]:
        """Have every worker serve every request a scenario issued (`warm_every_worker`).

        Parameters:
            issued: Each request's client and URL, as the scenario issued them.

        Returns:
            The rounds it took and the requests it issued.
        """
        return warm_every_worker(
            issued,
            workers=self.gunicorn.worker_pids(),
            concurrency=self.gunicorn.workers * self.gunicorn.threads,
            served_by=self.gunicorn.served_by,
            issue=issue_concurrently,
        )

    def _scenario_start(self) -> tuple[dict[str, int], dict[str, str]]:
        """Snapshot the counters and empty the statement statistics before a scenario.

        Returns:
            The server's counters and memcached's statistics.
        """
        query(self.connection, 'TRUNCATE performance_schema.events_statements_summary_by_digest')
        return global_status(self.connection), self.memcached.stats()

    def _scenario_end(
        self, prefix: str, run: dict[str, Any], before: tuple[dict[str, int], dict[str, str]]
    ) -> None:
        """Record what the server, memcached and workers did during a scenario.

        Parameters:
            prefix: The scenario's metric prefix, ``web.<state>.<scenario>``.
            run: The run to record into.
            before: What `_scenario_start` returned.
        """
        metrics = run['metrics']
        after = global_status(self.connection)
        for name, delta in counter_deltas(before[0], after, SCENARIO_COUNTERS).items():
            metrics[f'{prefix}.server.{name}'] = delta
        statements = query(
            self.connection,
            'SELECT COALESCE(SUM(COUNT_STAR), 0) FROM '
            'performance_schema.events_statements_summary_by_digest WHERE SCHEMA_NAME = %s',
            [self.schema],
        )
        metrics[f'{prefix}.statements'] = int(statements[0][0])
        digests = query(
            self.connection,
            'SELECT DIGEST_TEXT, COUNT_STAR, SUM_TIMER_WAIT, QUANTILE_95, '
            'SUM_SORT_MERGE_PASSES, SUM_CREATED_TMP_DISK_TABLES FROM '
            'performance_schema.events_statements_summary_by_digest WHERE SCHEMA_NAME = %s '
            f'ORDER BY SUM_TIMER_WAIT DESC LIMIT {TOP_DIGESTS}',  # nosec B608 - a constant
            [self.schema],
        )
        run['details'].setdefault('top_statements', {})[prefix] = [
            {
                'digest_text': text,
                'count': int(count),
                'total_s': int(total) / 1e12,
                'p95_s': int(quantile) / 1e12,
                'sort_merge_passes': int(merges),
                'tmp_disk_tables': int(disk),
            }
            for text, count, total, quantile, merges, disk in digests
        ]
        tables = query(
            self.connection,
            'SELECT COUNT(*) FROM information_schema.TABLES WHERE TABLE_SCHEMA = %s',
            [self.schema],
        )
        metrics[f'{prefix}.table_count'] = int(tables[0][0])
        stats = self.memcached.stats()
        metrics[f'{prefix}.memcached_evictions'] = int(stats['evictions']) - int(
            before[1]['evictions']
        )
        self._cache_gets += int(stats['cmd_get']) - int(before[1]['cmd_get'])
        metrics[f'{prefix}.worker_peak_rss_kb'] = max(
            (read_kb(Path(f'/proc/{pid}/status'), 'VmHWM') for pid in self.gunicorn.worker_pids()),
            default=0,
        )

    def run_scenario(
        self, state: str, scenario: Scenario, run: dict[str, Any], client: Client
    ) -> list[tuple[Client, str]]:
        """Issue one sequential scenario once and record it under a state.

        Parameters:
            state: The state it is recorded as.
            scenario: The scenario.
            run: The run to record into.
            client: The scenario's client: a new one after a reset, the same one again
                for the warm repetition, as a browser keeps its session.

        Returns:
            Each request's client and URL as issued, untimed ones included.
        """
        prefix = f'web.{state}.{scenario.name}'
        before = self._scenario_start()
        timings = run_sequence(client, scenario)
        self._scenario_end(prefix, run, before)
        timed = [
            timing
            for timing, request in zip(timings, scenario.requests, strict=True)
            if request.timed
        ]
        metrics = run['metrics']
        metrics[f'{prefix}.wall_s'] = (timed[-1].started + timed[-1].latency_s) - timed[0].started
        metrics[f'{prefix}.errors'] = sum(1 for timing in timings if timing.failed)
        for timing in timed:
            metrics[f'{prefix}.{timing.name}.latency_s'] = timing.latency_s
        return [(client, timing.url) for timing in timings]

    def run_concurrency(
        self,
        state: str,
        concurrency: Concurrency,
        run: dict[str, Any],
        clients: dict[str, list[Client]],
    ) -> list[tuple[Client, str]]:
        """Run both halves of the concurrency scenario once under a state.

        Parameters:
            state: The state it is recorded as.
            concurrency: The scenario.
            run: The run to record into.
            clients: Each half's users' clients, kept across the warm repetition.

        Returns:
            Every request's client and URL as issued, both halves together.
        """
        issued: list[tuple[Client, str]] = []
        halves = {
            'distinct': [concurrency.distinct.format(i=i) for i in range(concurrency.users)],
            'shared': [concurrency.shared] * concurrency.users,
        }
        for half, searches in halves.items():
            prefix = f'web.{state}.concurrency.{half}'
            before = self._scenario_start()
            outcome = run_concurrency_half(clients[half], searches, concurrency.fanout)
            self._scenario_end(prefix, run, before)
            run['samples'][f'{prefix}.latency_s'] = outcome.latencies
            run['metrics'][f'{prefix}.p95_s'] = p95(outcome.latencies)
            run['metrics'][f'{prefix}.throughput_per_s'] = outcome.throughput_per_s
            run['metrics'][f'{prefix}.errors'] = outcome.errors
            issued.extend(outcome.issued)
        return issued

    def one_run(self) -> dict[str, Any]:
        """Make one run: the db-cold pass, then the app-cold pass.

        Returns:
            The result run.

        Raises:
            WebRunError: If memcached answered no lookup in any scenario of the run.
        """
        run = new_run('web')
        self._cache_gets = 0
        base_url = self.gunicorn.base_url
        concurrency = self.config.concurrency
        warmups = run['details'].setdefault('warmup', {})
        for state in ('db-cold', 'app-cold'):
            for scenario in self.config.scenarios:
                self.reset(state)
                self.require_cold()
                # One cookie jar per scenario, emptied only by the reset.
                client = Client(base_url)
                issued = self.run_scenario(state, scenario, run, client)
                if state == 'app-cold':
                    warmups[f'web.warm.{scenario.name}'] = self.warm_up(issued)
                    self.run_scenario('warm', scenario, run, client)
            if concurrency is not None:
                self.reset(state)
                self.require_cold()
                clients = {
                    half: [Client(base_url) for _ in range(concurrency.users)]
                    for half in ('distinct', 'shared')
                }
                issued = self.run_concurrency(state, concurrency, run, clients)
                if state == 'app-cold':
                    warmups['web.warm.concurrency'] = self.warm_up(issued)
                    self.run_concurrency('warm', concurrency, run, clients)
        if self._cache_gets == 0:
            raise WebRunError(
                'memcached answered no lookup in any scenario of the run: the application '
                'is not using the harness memcached'
            )
        return run


def side_schema(label: Label, override: str | None) -> tuple[str, tuple[Path, Path]]:
    """Find the schema a side's web runs serve, and the holdings they are given.

    The holdings come from the scale, never from a result file
    (`benchmarks.import_scenarios.holdings_for`).

    Parameters:
        label: The side's label, whose result file names the schema its import built.
        override: A schema to use instead, or None.

    Returns:
        The schema, and the PDS3 and PDS4 holdings roots.

    Raises:
        WebRunError: If no schema is named and the label has no result file naming one.
    """
    schema = override
    if schema is None:
        path = RESULTS_DIR / label.file_name
        if not path.exists():
            raise WebRunError(f'{path} does not exist: run bench_import for this label first')
        schema = str(load_result(path)['environment']['schema'])
    return schema, holdings_for(label)


def _parse_arguments(argv: Sequence[str] | None) -> argparse.Namespace:
    """Read the command line.

    Parameters:
        argv: The arguments, or None for the command line's.

    Returns:
        The parsed arguments.
    """
    parser = argparse.ArgumentParser(
        prog='python -m benchmarks.bench_web',
        description='Time the web scenarios of one side against a gunicorn the harness starts.',
    )
    parser.add_argument('--scale', choices=SCALES, required=True)
    parser.add_argument('--side', choices=SIDES, required=True)
    parser.add_argument('--pr', required=True)
    parser.add_argument('--session', required=True)
    parser.add_argument('--date', default=None)
    parser.add_argument('--python', type=Path, required=True)
    parser.add_argument('--repo-root', type=Path, required=True)
    parser.add_argument('--runs', type=int, default=None, help="default: web.toml's for the scale")
    parser.add_argument('--schema', default=None, help="serve this schema instead of the import's")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    """Make the web runs the command line asks for and record them.

    Parameters:
        argv: The arguments, or None for the command line's.
    """
    args = _parse_arguments(argv)
    server_config, memcached_binary = load_server_config()
    reexec_with_socket(
        server_config, 'benchmarks.bench_web', sys.argv[1:] if argv is None else argv
    )
    config = load_web_config(scale=args.scale)
    server = MysqlServer(server_config)
    memcached = MemcachedServer(
        memcached_binary, config.server.memcached_port, config.server.memcached_mb
    )
    side = Side(python=args.python.absolute(), repo_root=args.repo_root.resolve())
    spelling = Spelling.from_help(side.import_help())
    label = make_label(
        pr=args.pr, side=args.side, scale=args.scale, session=args.session, date=args.date
    )
    schema, holdings = side_schema(label, args.schema)
    bench = WebBench(
        server=server,
        memcached=memcached,
        side=side,
        spelling=spelling,
        label=label,
        config=config,
        schema=schema,
        holdings=holdings,
    )
    count = config.runs[args.scale] if args.runs is None else args.runs
    with server.running():
        environment: dict[str, Any] = {
            **host_environment(),
            **side.environment(),
            **server_environment(server),
            'skipped_steps': list(spelling.skipped_steps),
            'web_scenario_hash': scenario_hash([config.path]),
            'server_model': bench.gunicorn.server_model,
            'app_loading': 'eager',
            'cache_owned': True,
        }
        memcached.start()
        try:
            settings = bench.application_settings()
            environment.update(
                {
                    'cache_backend': settings['cache_backend'],
                    'cache_location': settings['cache_location'],
                    'cache_middleware_seconds': settings['cache_middleware_seconds'],
                    'isolation_level': settings['isolation_level'],
                    'memcached_limit_maxbytes': int(memcached.stats()['limit_maxbytes']),
                }
            )
            for position in range(count):
                run = bench.one_run()
                path = append_runs(label, environment, [run])
                sys.stdout.write(f'web run {position + 1} of {count} recorded in {path}\n')
        except (SideError, ServerError) as err:
            raise WebRunError(str(err)) from err
        finally:
            bench.gunicorn.stop()
            memcached.stop()


if __name__ == '__main__':
    main()
