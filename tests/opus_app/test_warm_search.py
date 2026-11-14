"""Tests for ``opus_manage warm_search``: the requests it makes, in what order, and when it fails.

These need no database, no memcached and no server: the command's one HTTP call,
`warm_search.fetch`, is replaced by one that records each URL and answers it. What is
worth pinning, and why:

* **The requests are the landing page's, then the common searches'.** The empty search's
  count and first page, the default widgets' fan-out, and every mult field's counts,
  then one search per counted value of each common field, through the application's own
  routes, so the cache keys are the ones a visitor's requests read.
* **Everything comes from the API.** The fields are ``api/fields.json``'s, and the values
  are the empty search's counts, so a value no observation holds is not searched, and a
  common field the site does not offer is skipped.
* **The order that matters holds when the requests run concurrently.** The field list
  first, then the empty search's count alone, which builds the results every other
  request of the empty search reads; within each common search, its count before its
  pages.
* **It fails when a request does not answer 200,** after making the others.
"""

from __future__ import annotations

import io
import json
import threading
from typing import Any

import pytest
import requests
from django.core.management import CommandError, call_command
from django.test import override_settings

from opus_app.apps.search.management.commands import warm_search

SITE = 'http://opus.example.org/opus/'

#: An ``api/fields.json`` answer: fields of every kind, ``target`` listed again in a
#: second category as a linked field is, and ``mission`` a common field it lacks.
_FIELDS_ANSWER = {
    'data': {
        'General Constraints': {
            'planet': {'field_id': 'planet', 'type': 'multiple'},
            'target': {'field_id': 'target', 'type': 'multiple'},
            'time1': {'field_id': 'time1', 'type': 'range_time'},
            'instrument': {'field_id': 'instrument', 'type': 'multiple'},
            'opusid': {'field_id': 'opusid', 'type': 'string'},
        },
        'Cassini Mission Constraints': {
            'target': {'field_id': 'target', 'type': 'multiple'},
            'observationduration': {'field_id': 'observationduration', 'type': 'range_float'},
        },
    }
}

#: The fields `_FIELDS_ANSWER` describes, as `warm_search.api_fields` returns them.
_FIELDS = [
    ('planet', 'multiple'),
    ('target', 'multiple'),
    ('time1', 'range_time'),
    ('instrument', 'multiple'),
    ('opusid', 'string'),
    ('observationduration', 'range_float'),
]

#: The empty search's counts for the common fields among `_FIELDS`.
_COUNTS = {'planet': {'Saturn': 5, 'Pluto': 0, 'Jupiter': 2}, 'instrument': {'Cassini ISS': 3}}

_DEFAULTS = ['instrument', 'observationtype', 'target']


class _Site:
    """Stands in for the site: records each URL asked for and answers it.

    ``failing`` names the URLs, relative to `SITE`, that answer 500; ``silent`` those that
    raise as an unreachable server does.
    """

    def __init__(self) -> None:
        self.requested: list[str] = []
        self.failing: frozenset[str] = frozenset()
        self.silent: frozenset[str] = frozenset()
        self._lock = threading.Lock()

    def fetch(self, _session: requests.Session, url: str) -> tuple[int, bytes]:
        """Record `url` and answer it as the site would."""
        assert url.startswith(SITE), url
        path = url.removeprefix(SITE)
        with self._lock:
            self.requested.append(path)
        if path in self.silent:
            raise requests.ConnectionError('refused')
        if path in self.failing:
            return 500, b''
        if path == 'api/fields.json':
            return 200, json.dumps(_FIELDS_ANSWER).encode()
        for slug, mults in _COUNTS.items():
            if path == f'__api/meta/mults/{slug}.json?reqno=1':
                return 200, json.dumps({'field_id': slug, 'mults': mults}).encode()
        return 200, b'{}'


@pytest.fixture
def site(monkeypatch: pytest.MonkeyPatch) -> _Site:
    """Replace the command's HTTP call with `_Site`'s."""
    stand_in = _Site()
    monkeypatch.setattr(warm_search, 'fetch', stand_in.fetch)
    return stand_in


def _warm(*args: str) -> str:
    """Run the command against `SITE` with the default widgets `_DEFAULTS`; return its output."""
    output = io.StringIO()
    with override_settings(DEFAULT_WIDGETS=','.join(_DEFAULTS)):
        call_command('warm_search', '--url', SITE, *args, stdout=output)
    return output.getvalue()


def _expected() -> list[str]:
    """Every request a warm-up of `_FIELDS_ANSWER` and `_COUNTS` makes, in sequential order."""
    expected = ['api/fields.json', *warm_search.warm_requests(_FIELDS, _DEFAULTS)]
    for slug, value in [('planet', 'Saturn'), ('planet', 'Jupiter'), ('instrument', 'Cassini ISS')]:
        expected += warm_search.value_search_requests(slug, value, _FIELDS, _DEFAULTS)
    return expected


def test_the_fields_are_the_answers_in_order_each_once() -> None:
    """A linked field's second listing is dropped."""
    assert warm_search.api_fields(json.dumps(_FIELDS_ANSWER).encode()) == _FIELDS


def test_the_requests_are_the_landing_pages() -> None:
    """Count, first page for the results page, ranges among the defaults, the menu, then
    every mult."""
    assert warm_search.warm_requests(_FIELDS, ['instrument', 'time1', 'target']) == [
        '__api/meta/result_count.json?reqno=1',
        '__api/dataimages.json?page=1&limit=100&reqno=1',
        '__api/meta/range/endpoints/time1.json?reqno=1',
        '__menu.json?reqno=1',
        '__api/meta/mults/instrument.json?reqno=1',
        '__api/meta/mults/target.json?reqno=1',
        '__api/meta/mults/planet.json?reqno=1',
    ]


def test_a_value_search_asks_for_the_default_widgets_and_its_own_field() -> None:
    """Count, first page for the results page, ranges among the defaults, the menu, then
    the defaults' mults and the searched field's."""
    assert warm_search.value_search_requests(
        'planet', 'Saturn Rings', _FIELDS, ['instrument', 'time1', 'target']
    ) == [
        '__api/meta/result_count.json?planet=Saturn+Rings&reqno=1',
        '__api/dataimages.json?planet=Saturn+Rings&page=1&limit=100&reqno=1',
        '__api/meta/range/endpoints/time1.json?planet=Saturn+Rings&reqno=1',
        '__menu.json?planet=Saturn+Rings&reqno=1',
        '__api/meta/mults/instrument.json?planet=Saturn+Rings&reqno=1',
        '__api/meta/mults/target.json?planet=Saturn+Rings&reqno=1',
        '__api/meta/mults/planet.json?planet=Saturn+Rings&reqno=1',
    ]


def test_a_value_search_on_a_default_widget_asks_for_its_counts_once() -> None:
    """The searched field is not added again when it is a default widget."""
    requests_ = warm_search.value_search_requests(
        'instrument', 'Cassini ISS', _FIELDS, ['instrument', 'target']
    )
    assert [url for url in requests_ if url.startswith('__api/meta/mults/')] == [
        '__api/meta/mults/instrument.json?instrument=Cassini+ISS&reqno=1',
        '__api/meta/mults/target.json?instrument=Cassini+ISS&reqno=1',
    ]


def test_the_counted_values_are_those_with_observations() -> None:
    """In the answer's order, without a value counted zero."""
    content = json.dumps({'field_id': 'planet', 'mults': _COUNTS['planet']}).encode()
    assert warm_search.counted_values(content) == ['Saturn', 'Jupiter']


@override_settings(PUBLIC_OPUS_URL='https://opus.example.org/', BASE_PATH='opus')
def test_the_default_site_is_the_public_url_under_the_base_path() -> None:
    """The web server serves the application under its base path."""
    assert warm_search.default_site_url() == 'https://opus.example.org/opus/'


def test_one_at_a_time_the_requests_come_in_order(site: _Site) -> None:
    """The fields, the landing page, then each counted value's search in the common
    fields' order; a ``--url`` without its slash is given one."""
    output = _warm('--url', SITE.removesuffix('/'), '--parallel', '1')
    expected = _expected()
    assert site.requested == expected
    assert (
        f'Warmed {len(expected)} of {len(expected)} requests, for the empty search and '
        '3 common searches, in'
    ) in output


def test_concurrently_the_order_that_matters_holds(site: _Site) -> None:
    """Every request, the fields first and the empty search's count next, and each
    search's requests in order."""
    _warm('--parallel', '4')
    expected = _expected()
    assert sorted(site.requested) == sorted(expected)
    assert site.requested[:2] == ['api/fields.json', '__api/meta/result_count.json?reqno=1']
    for slug, value in [('planet', 'Saturn'), ('instrument', 'Cassini ISS')]:
        search = warm_search.value_search_requests(slug, value, _FIELDS, _DEFAULTS)
        assert [url for url in site.requested if url in search] == search


def test_a_field_whose_counts_failed_is_not_searched(site: _Site) -> None:
    """Without the empty search's counts there are no values to search for."""
    site.failing = frozenset({'__api/meta/mults/planet.json?reqno=1'})
    with pytest.raises(CommandError, match='1 requests failed'):
        _warm()
    assert not any('planet=' in url for url in site.requested)
    assert any('instrument=Cassini+ISS' in url for url in site.requested)


def test_a_request_that_fails_fails_the_command_after_the_others(site: _Site) -> None:
    """Every request is still made; the failure names the one that did not answer 200."""
    site.failing = frozenset({'__menu.json?reqno=1'})
    with pytest.raises(CommandError, match=r'1 requests failed: __menu\.json\?reqno=1 \(500\)'):
        _warm()
    assert sorted(site.requested) == sorted(_expected())


def test_a_request_with_no_answer_is_a_failure(site: _Site) -> None:
    """An unreachable server is reported as a request that failed, not raised."""
    site.silent = frozenset({'__menu.json?reqno=1'})
    with pytest.raises(CommandError, match=r'__menu\.json\?reqno=1 \(no answer: refused\)'):
        _warm()


def test_without_the_fields_nothing_else_is_asked_for(site: _Site) -> None:
    """The field list says what to ask for; without it the command stops."""
    site.failing = frozenset({'api/fields.json'})
    with pytest.raises(CommandError, match=r'api/fields\.json answered 500'):
        _warm()
    assert site.requested == ['api/fields.json']


@pytest.mark.parametrize('parallel', ['0', '-1'])
def test_parallel_must_be_positive(site: _Site, parallel: str) -> None:
    """Refused before any request."""
    with pytest.raises(CommandError, match='--parallel must be at least 1'):
        _warm('--parallel', parallel)
    assert site.requested == []


def test_fetch_asks_through_the_session_with_the_timeout() -> None:
    """The status and body of the session's answer, asked for with the request timeout."""

    class _Session:
        def get(self, url: str, timeout: float) -> Any:
            assert (url, timeout) == (SITE, warm_search.REQUEST_TIMEOUT_SECONDS)
            response = requests.Response()
            response.status_code = 204
            response._content = b'body'
            return response

    assert warm_search.fetch(_Session(), SITE) == (204, b'body')  # type: ignore[arg-type]
