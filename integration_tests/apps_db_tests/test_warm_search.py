"""Tests for ``opus_manage warm_search`` against the imported database.

The unit tests in ``tests/opus_app/test_warm_search.py`` answer the command's requests
themselves. Here its one HTTP call is routed through Django's test client into this
process's application, so every request is answered by this database: what is pinned is
that each one the warm-up makes answers 200, that it searches the values the database
holds, and that what it leaves behind is what a visitor's request finds.

The first case runs on Django's dummy cache, so every request runs its queries. The
second also runs on it, and shows that a common search's results are built by the
warm-up, which no cache holds: a visitor's search for one value stores no search and
builds nothing. The third runs on a local-memory cache, so that the landing page's own
requests, issued afterwards with the user interface's whole query string, can be shown
to find their answers already cached.

These tests require the following volumes, imported in this order:
COISS_2002,COISS_2008,COISS_2111,COUVIS_0002,GO_0017,VGISS_6210,VGISS_8201,
HSTI1_2003
"""

from __future__ import annotations

import io
import json
import re
from unittest import TestCase, mock

from django.conf import settings
from django.core.cache import cache
from django.core.management import call_command
from django.db import connection
from django.http import QueryDict
from django.test import Client, override_settings
from django.test.utils import CaptureQueriesContext

from opus_app.apps.search.management.commands import warm_search
from opus_app.apps.search.views import (
    get_param_info_by_slug,
    search_hash,
    search_number_cache_key,
    url_to_search_params,
)

_DUMMY_CACHE = {'default': {'BACKEND': 'django.core.cache.backends.dummy.DummyCache'}}

#: A local-memory cache with room for every answer the warm-up stores; its default
#: limit, 300 entries, would cull the landing page's before the test reads them.
_LOCMEM_CACHE = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'warm-search-landing',
        'OPTIONS': {'MAX_ENTRIES': 100_000},
    }
}

#: The API root the command is told to warm; the client below answers for it.
_SITE = 'http://localhost/opus/'

#: The query string the user interface sends, as ``o_hash.getHash()`` builds it from its
#: preferences, without its ``reqno``.
_LANDING = (
    'cols=opusid,instrument,planet,target,time1,observationduration'
    '&widgets=instrument,observationtype,target&order=time1,opusid&view=search'
    '&browse=gallery&cart_browse=gallery&startobs=1&cart_startobs=1&detail='
)


def _host() -> str:
    """Return the first ``ALLOWED_HOSTS`` entry that is not ``*``, or ``localhost``."""
    return next((host for host in settings.ALLOWED_HOSTS if host != '*'), 'localhost')


def _warm() -> str:
    """Run the command one request at a time, answered by this process; return its output."""
    client = Client(HTTP_HOST=_host(), raise_request_exception=False)

    def fetch(_session: object, url: str) -> tuple[int, bytes]:
        response = client.get('/' + url.removeprefix('http://localhost/'))
        return response.status_code, response.content

    output = io.StringIO()
    with mock.patch.object(warm_search, 'fetch', fetch):
        call_command('warm_search', '--url', _SITE, '--parallel', '1', stdout=output)
    return output.getvalue()


class WarmSearchTests(TestCase):
    """The common searches' requests, answered by the imported database."""

    def test_every_request_is_answered(self) -> None:
        """The command reports every request warmed, the common searches among them."""
        with override_settings(CACHES=_DUMMY_CACHE):
            output = _warm()
        summary = re.search(
            r'Warmed (\d+) of (\d+) requests, for the empty search and (\d+) common searches',
            output,
        )
        assert summary is not None, output
        assert summary[1] == summary[2]
        assert int(summary[3]) > 0
        assert '?planet=' in output
        assert '?instrument=' in output

    def test_a_warmed_search_is_built_without_any_cache(self) -> None:
        """A visitor's search for a planet stores no search and builds no results."""
        client = Client(HTTP_HOST=_host())
        with override_settings(CACHES=_DUMMY_CACHE):
            _warm()
            counts = client.get('/__api/meta/mults/planet.json?reqno=1')
            planet = warm_search.counted_values(counts.content)[0]
            search = QueryDict(mutable=True)
            search['planet'] = planet
            query = f'{search.urlencode()}&{_LANDING}'
            with CaptureQueriesContext(connection) as queries:
                count = client.get(f'/__api/meta/result_count.json?{query}&reqno=9')
        assert count.status_code == 200
        assert json.loads(count.content)['data'][0]['result_count'] > 0
        statements = ' '.join(captured['sql'] for captured in queries.captured_queries).upper()
        assert 'INSERT INTO `USER_SEARCHES`' not in statements
        assert 'INSERT INTO `SEARCH_RESULTS`' not in statements

    def test_the_landing_pages_requests_find_the_warm_up_cached(self) -> None:
        """The search's number and a default widget's counts are cached before the view
        runs, and the view then counts nothing and stores no search."""
        with override_settings(CACHES=_LOCMEM_CACHE):
            cache.clear()
            _warm()
            selections, extras = url_to_search_params(QueryDict(_LANDING))
            assert selections is not None
            assert extras is not None
            cached = cache.get(search_number_cache_key(search_hash(selections, extras)))
            assert cached is not None
            search_number = cached[0]
            for slug in settings.DEFAULT_WIDGETS.split(','):
                param_info = get_param_info_by_slug(slug, 'col')
                assert param_info is not None
                key = (
                    f'{settings.CACHE_SERVER_PREFIX}{settings.CACHE_KEY_PREFIX}:mults_'
                    f'{param_info.param_qualified_name()}:{search_number}'
                )
                assert cache.get(key) is not None, slug
            client = Client(HTTP_HOST=_host())
            with CaptureQueriesContext(connection) as queries:
                counts = client.get(f'/__api/meta/mults/instrument.json?{_LANDING}&reqno=7')
                count = client.get(f'/__api/meta/result_count.json?{_LANDING}&reqno=8')
            cache.clear()
        assert counts.status_code == 200
        assert count.status_code == 200
        statements = ' '.join(captured['sql'] for captured in queries.captured_queries).upper()
        assert 'GROUP BY' not in statements
        assert 'INSERT INTO `USER_SEARCHES`' not in statements
        assert 'INSERT INTO `SEARCH_RESULTS`' not in statements
