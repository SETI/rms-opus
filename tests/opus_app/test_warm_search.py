"""Tests for ``opus_manage warm_search``: the requests it issues, and when it refuses.

These need no database and no memcached: the searchable fields are given, and Django's
test client is replaced by one that records each request and answers it. What is worth
pinning, and why:

* **The requests are the landing page's.** The empty search's count and first page, the
  default widgets' fan-out, and every searchable mult field's counts, through the
  application's own routes, so the cache keys are the ones a visitor's requests read.
* **The client names an allowed host.** The test client's default host is not in
  ``ALLOWED_HOSTS``, and every request would answer 400.
* **It refuses the local-memory cache,** which would hold the entries in a process that
  is about to exit, and it fails when a request does not answer 200.
"""

from __future__ import annotations

import io
from typing import Any, ClassVar

import pytest
from django.core.management import CommandError, call_command
from django.http import HttpResponse
from django.test import override_settings

from opus_app.apps.search.management.commands import warm_search

#: A cache backend that is not the local-memory fallback. Nothing connects to it here.
_MEMCACHED = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}

_LOCMEM = {'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}}

#: Searchable fields of every kind the requests are chosen by.
_FIELDS = [
    ('planet', 'GROUP'),
    ('target', 'MULTIGROUP'),
    ('time1', 'RANGE'),
    ('instrument', 'GROUP'),
    ('opusid', 'STRING'),
    ('observationduration', 'RANGE'),
]


class _RecordingClient:
    """Stands in for `django.test.Client`: records each request and answers it."""

    created: ClassVar[list[dict[str, Any]]] = []
    requested: ClassVar[list[str]] = []
    failing: ClassVar[frozenset[str]] = frozenset()

    def __init__(self, **defaults: Any) -> None:
        _RecordingClient.created.append(defaults)

    def get(self, path: str) -> HttpResponse:
        """Record a request and answer 500 for a failing one, 200 otherwise."""
        _RecordingClient.requested.append(path)
        return HttpResponse(status=500 if path in self.failing else 200)


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> type[_RecordingClient]:
    """Replace the test client and the fields' database read."""
    _RecordingClient.created = []
    _RecordingClient.requested = []
    _RecordingClient.failing = frozenset()
    monkeypatch.setattr(warm_search, 'Client', _RecordingClient)
    monkeypatch.setattr(warm_search, 'searchable_fields', lambda: list(_FIELDS))
    return _RecordingClient


def test_the_requests_are_the_landing_pages() -> None:
    """Count, first page twice, ranges among the defaults, the menu, then every mult."""
    assert warm_search.warm_requests(_FIELDS, ['instrument', 'time1', 'target']) == [
        '__api/meta/result_count.json?reqno=1',
        'api/data.json?page=1&limit=100',
        '__api/dataimages.json?page=1&limit=100&reqno=1',
        '__api/meta/range/endpoints/time1.json?reqno=1',
        '__menu.json?reqno=1',
        '__api/meta/mults/instrument.json?reqno=1',
        '__api/meta/mults/target.json?reqno=1',
        '__api/meta/mults/planet.json?reqno=1',
    ]


@pytest.mark.parametrize(
    ('allowed', 'host'),
    [
        (['*', 'opus.example.org', 'localhost'], 'opus.example.org'),
        (['*'], 'localhost'),
        ([], 'localhost'),
    ],
    ids=['first-not-wildcard', 'only-wildcard', 'none'],
)
def test_the_host_is_the_first_allowed_one_that_is_not_a_wildcard(
    allowed: list[str], host: str
) -> None:
    """``localhost`` when every entry is ``*``."""
    assert warm_search.warm_host(allowed) == host


@override_settings(
    CACHES=_MEMCACHED,
    ALLOWED_HOSTS=['*', 'opus.example.org'],
    DEFAULT_WIDGETS='instrument,observationtype,target',
)
def test_the_command_issues_every_request_through_the_client(
    client: type[_RecordingClient],
) -> None:
    """Every request, rooted at ``/``, from a client naming the allowed host."""
    output = io.StringIO()
    call_command('warm_search', stdout=output)
    expected = warm_search.warm_requests(_FIELDS, ['instrument', 'observationtype', 'target'])
    assert client.requested == [f'/{url}' for url in expected]
    assert client.created == [{'HTTP_HOST': 'opus.example.org', 'raise_request_exception': False}]
    assert f'Warmed {len(expected)} of {len(expected)} requests in' in output.getvalue()


@override_settings(CACHES=_LOCMEM)
def test_the_command_refuses_the_local_memory_cache(client: type[_RecordingClient]) -> None:
    """It names the fallback and issues nothing."""
    with pytest.raises(CommandError, match='local-memory fallback'):
        call_command('warm_search', stdout=io.StringIO())
    assert client.created == []
    assert client.requested == []


@override_settings(CACHES=_MEMCACHED)
def test_a_request_that_fails_fails_the_command_after_the_others(
    client: type[_RecordingClient],
) -> None:
    """Every request is still issued; the failure names the one that did not answer 200."""
    client.failing = frozenset({'/__menu.json?reqno=1'})
    with pytest.raises(CommandError, match=r'1 requests failed: __menu\.json\?reqno=1 \(500\)'):
        call_command('warm_search', stdout=io.StringIO())
    assert '/__api/meta/mults/planet.json?reqno=1' in client.requested
