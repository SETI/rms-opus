"""Tests for ``opus_manage warm_search`` against the imported database.

The unit tests in ``tests/opus_app/test_warm_search.py`` give the command its fields and
answer its requests themselves. Here it reads ``param_info`` and issues every request
through the application, so what is pinned is that each one the landing page warms is
answered 200 by this database, and that the mult fields it warms are the searchable
ones ``param_info`` holds, the default widgets among them.

The cache is Django's dummy backend: the command refuses only the local-memory one,
and with nothing stored every request runs its queries.

These tests require the following volumes, imported in this order:
COISS_2002,COISS_2008,COISS_2111,COUVIS_0002,GO_0017,VGISS_6210,VGISS_8201,
HSTI1_2003
"""

from __future__ import annotations

import io
from unittest import TestCase

from django.conf import settings
from django.core.management import call_command
from django.test import override_settings

from opus_app.apps.search.management.commands import warm_search

_DUMMY_CACHE = {'default': {'BACKEND': 'django.core.cache.backends.dummy.DummyCache'}}


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
