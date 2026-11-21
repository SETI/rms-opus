"""Which worker served what: the gunicorn hooks, the served log, and the warm-up."""

import http.cookiejar
import itertools
from collections.abc import Mapping, Sequence
from pathlib import Path

import pytest

from benchmarks import gunicorn_hooks
from benchmarks.app_servers import GunicornServer
from benchmarks.bench_web import Client, WebRunError, unserved, warm_every_worker


def _gunicorn(served_log: Path) -> GunicornServer:
    """Return a gunicorn description whose served log is the given file; nothing runs."""
    return GunicornServer(
        python=Path('python'),
        repo_root=Path(),
        env={},
        port=1,
        workers=2,
        threads=2,
        log_dir=served_log.parent,
        app_log_file=served_log.parent / 'opus_log.txt',
        served_log=served_log,
    )


def test_the_hooks_record_readiness_and_each_request(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A worker's readiness and every request it serves are lines the harness reads."""
    served_log = tmp_path / 'served.log'
    monkeypatch.setenv(gunicorn_hooks.SERVED_LOG_ENV, str(served_log))
    gunicorn_hooks._record(gunicorn_hooks.READY)

    class _Request:
        uri = '/api/data.json?page=1&limit=100'

    gunicorn_hooks.post_request(None, _Request(), None, None)
    server = _gunicorn(served_log)
    assert server.served() == [(server_pid(served_log), '/api/data.json?page=1&limit=100')]
    assert server.served_by() == {
        '/api/data.json?page=1&limit=100': {server_pid(served_log)},
    }


def server_pid(served_log: Path) -> int:
    """Return the process id the first line of a served log names."""
    return int(served_log.read_text().split('\t')[0])


def test_the_hooks_write_nothing_without_a_served_log(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Started without the variable, the hooks leave no file behind."""
    monkeypatch.delenv(gunicorn_hooks.SERVED_LOG_ENV, raising=False)
    monkeypatch.chdir(tmp_path)
    gunicorn_hooks._record('anything')
    assert list(tmp_path.iterdir()) == []


def test_readiness_lines_are_not_requests(tmp_path: Path) -> None:
    """A worker that only got ready has served nothing, so a cold scenario may start."""
    served_log = tmp_path / 'served.log'
    served_log.write_text('11\tREADY\n12\tREADY\n11\t/api/categories/x.json\nnot a line\n')
    server = _gunicorn(served_log)
    assert server.served() == [(11, '/api/categories/x.json')]


def test_a_request_is_unserved_until_every_worker_has_served_it() -> None:
    """One worker short is not warm."""
    served = {'/a.json': {1, 2}, '/b.json': {1}}
    assert unserved(['a.json', 'b.json', 'c.json'], served, [1, 2]) == ['b.json', 'c.json']


def test_a_clone_carries_the_session_cookie() -> None:
    """A warm-up request is the scenario's user, not a new visitor."""
    client = Client('http://127.0.0.1:1')
    cookie = http.cookiejar.Cookie(
        0, 'sessionid', 'abc', None, False, '127.0.0.1', False, False, '/', True, False,
        None, False, None, None, {},
    )  # fmt: skip
    client.jar.set_cookie(cookie)
    copy = client.clone()
    assert [c.value for c in copy.jar] == ['abc']
    assert copy.jar is not client.jar


class _Server:
    """A stand-in for gunicorn that hands each request to its workers in turn.

    Like gunicorn, it lets one worker take several requests in a row, here as many as
    `streak`, so a burst smaller than the workers times `streak` can miss a worker.
    """

    def __init__(self, workers: Sequence[int], streak: int) -> None:
        self.served: dict[str, set[int]] = {}
        self._next = itertools.cycle(worker for worker in workers for _ in range(streak))

    def served_by(self) -> Mapping[str, set[int]]:
        return self.served

    def issue(self, tasks: Sequence[tuple[Client, str]], concurrency: int) -> int:
        del concurrency
        for _, url in tasks:
            self.served.setdefault(f'/{url}', set()).add(next(self._next))
        return 0


def test_the_warm_up_reaches_every_worker_with_every_request() -> None:
    """Rounds continue until each request has been served by each worker."""
    server = _Server([1, 2, 3, 4], streak=3)
    client = Client('http://127.0.0.1:1')
    outcome = warm_every_worker(
        [(client, 'a.json'), (client, 'b.json'), (client, 'a.json')],
        workers=[1, 2, 3, 4],
        concurrency=8,
        served_by=server.served_by,
        issue=server.issue,
    )
    assert server.served == {'/a.json': {1, 2, 3, 4}, '/b.json': {1, 2, 3, 4}}
    # The first round's 16 requests miss worker 4 for a.json; the second's 8 reach it.
    assert outcome == {'rounds': 2, 'requests': 24}


def test_requests_every_worker_already_served_need_no_warm_up() -> None:
    """A scenario the cold pass spread over every worker is already warm."""
    server = _Server([1, 2], streak=1)
    server.served['/a.json'] = {1, 2}
    outcome = warm_every_worker(
        [(Client('http://127.0.0.1:1'), 'a.json')],
        workers=[1, 2],
        concurrency=4,
        served_by=server.served_by,
        issue=server.issue,
    )
    assert outcome == {'rounds': 0, 'requests': 0}


def test_a_worker_that_never_serves_fails_the_warm_up() -> None:
    """A worker the requests never reach is a failed run, not a warm one."""
    server = _Server([1, 2], streak=1)
    with pytest.raises(WebRunError, match='has still not served'):
        warm_every_worker(
            [(Client('http://127.0.0.1:1'), 'a.json')],
            workers=[1, 2, 3],
            concurrency=4,
            served_by=server.served_by,
            issue=server.issue,
        )


def test_a_failed_warm_up_request_fails_the_warm_up() -> None:
    """An error during the warm-up is never measured past."""
    with pytest.raises(WebRunError, match='warm-up requests failed'):
        warm_every_worker(
            [(Client('http://127.0.0.1:1'), 'a.json')],
            workers=[1],
            concurrency=2,
            served_by=dict,
            issue=lambda tasks, concurrency: len(tasks),
        )
