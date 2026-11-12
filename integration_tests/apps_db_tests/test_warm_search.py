"""Tests for ``opus_manage warm_search`` against the imported database.

The unit tests in ``tests/opus_app/test_warm_search.py`` give the command its fields and
answer its requests themselves. Here it reads ``param_info`` and issues every request
through the application, so what is pinned is that each one the landing page warms is
answered 200 by this database, and that the mult fields it warms are the searchable
ones ``param_info`` holds, the default widgets among them.

The first case's cache is Django's dummy backend: the command refuses only the
local-memory one, and with nothing stored every request runs its queries. The second
runs the warm-up in this process on a local-memory cache, its refusal set aside, so that
the landing page's own requests, issued afterwards with the user interface's whole query
string, can be shown to find their answers already cached.

These tests require the following volumes, imported in this order:
COISS_2002,COISS_2008,COISS_2111,COUVIS_0002,GO_0017,VGISS_6210,VGISS_8201,
HSTI1_2003
"""

from __future__ import annotations

import io
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

_LOCMEM_CACHE = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'warm-search-landing',
    }
}

#: The query string the user interface's landing page sends, as ``o_hash.getHash()``
#: builds it from its preferences, without its ``reqno``.
_LANDING = (
    'cols=opusid,instrument,planet,target,time1,observationduration'
    '&widgets=instrument,observationtype,target&order=time1,opusid&view=search'
    '&browse=gallery&cart_browse=gallery&startobs=1&cart_startobs=1&detail='
)


class WarmSearchTests(TestCase):
    """The landing page's requests, issued against the imported database."""

    def test_every_request_is_answered(self) -> None:
        """The command reports every request warmed, and raises on none."""
        defaults = settings.DEFAULT_WIDGETS.split(',')
        requests = warm_search.warm_requests(warm_search.searchable_fields(), defaults)
        output = io.StringIO()
        with override_settings(CACHES=_DUMMY_CACHE):
            call_command('warm_search', stdout=output)
        assert f'Warmed {len(requests)} of {len(requests)} requests in' in output.getvalue()
        mults = [url for url in requests if url.startswith('__api/meta/mults/')]
        assert mults[: len(defaults)] == [
            f'__api/meta/mults/{slug}.json?reqno=1' for slug in defaults
        ]
        assert len(mults) > len(defaults)

    def test_the_landing_pages_requests_find_the_warm_up_cached(self) -> None:
        """The search's number and a default widget's counts are cached before the view
        runs, and the view then counts nothing and stores no search."""
        host = warm_search.warm_host(settings.ALLOWED_HOSTS)
        with (
            override_settings(CACHES=_LOCMEM_CACHE),
            mock.patch.object(warm_search, 'LOCMEM_MARKER', 'no-such-backend'),
        ):
            cache.clear()
            call_command('warm_search', stdout=io.StringIO())
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
            client = Client(HTTP_HOST=host)
            with CaptureQueriesContext(connection) as queries:
                counts = client.get(f'/__api/meta/mults/instrument.json?{_LANDING}&reqno=7')
                count = client.get(f'/__api/meta/result_count.json?{_LANDING}&reqno=8')
            cache.clear()
        assert counts.status_code == 200
        assert count.status_code == 200
        statements = ' '.join(query['sql'] for query in queries.captured_queries).upper()
        assert 'GROUP BY' not in statements
        assert 'INSERT INTO `USER_SEARCHES`' not in statements
        assert 'INSERT INTO `SEARCH_RESULTS`' not in statements
