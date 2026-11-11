"""``opus_manage warm_search``: answer the landing page's requests once, so the cache holds them.

Every visitor's first search is the empty one, in the default sort, and what the landing
page asks for about it -- the result count, the first page, the default widgets' fan-out,
and a mult widget's counts when one is opened -- is cached in memcached until the next
import. This command issues those requests itself, through Django's test client, so
that the first visitor after a deploy finds them cached and the rows they read in the
database's buffer pool:

* the empty search's result count;
* its first page, through the public ``api/data.json`` and the results gallery's
  ``__api/dataimages.json``;
* the fan-out of the default widgets (``settings.DEFAULT_WIDGETS``): the range endpoints
  of those that are ranges, and the menu, which carries the triggered tables;
* the empty search's mult counts for every searchable mult field in ``param_info``, so
  that opening any mult widget is a cache hit.

The requests go through the whole application, so the cache keys are the application's
own; the command computes none. It warms memcached and the database, not the worker
processes: each worker still loads its own per-process caches on its first request.

It requires memcached. Under Django's local-memory fallback the entries would live in
this process alone, which exits when the command does, so the command refuses.
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.test import Client

from opus_app.apps.paraminfo.models import ParamInfo
from opus_support.units import parse_form_type

if TYPE_CHECKING:
    from collections.abc import Sequence

#: The part of a cache backend's class path that marks Django's local-memory fallback.
LOCMEM_MARKER = 'locmem'

#: The ``param_info.display`` value of a field the search menu offers as a widget.
SEARCHABLE = 1


def warm_host(allowed_hosts: Sequence[str]) -> str:
    """Return the host the test client names, so that ``ALLOWED_HOSTS`` admits it.

    Parameters:
        allowed_hosts: ``settings.ALLOWED_HOSTS``.

    Returns:
        The first entry that is not the wildcard ``*``, or ``localhost`` when every
        entry is.
    """
    for host in allowed_hosts:
        if host != '*':
            return host
    return 'localhost'


def searchable_fields() -> list[tuple[str, str]]:
    """Return every field the search menu offers, with its form type.

    Returns:
        Each searchable ``param_info`` row's slug and its form type without its format
        or unit, in the menu's order.
    """
    rows = (
        ParamInfo.objects.filter(display=SEARCHABLE, slug__isnull=False, form_type__isnull=False)
        .order_by('disp_order')
        .values_list('slug', 'form_type')
    )
    return [(str(slug), str(parse_form_type(form_type)[0])) for slug, form_type in rows]


def warm_requests(fields: Sequence[tuple[str, str]], default_widgets: Sequence[str]) -> list[str]:
    """Return the requests that warm the landing page, in the order they are issued.

    Parameters:
        fields: Every searchable field's slug and form type (`searchable_fields`).
        default_widgets: The slugs of the widgets the landing page opens.

    Returns:
        The URLs relative to the site's root, in this order -- the result count, the
        first page twice, the range endpoints of each default widget that is a range,
        the menu, then every mult field's counts, default widgets first.
    """
    form_types = dict(fields)
    requests = [
        '__api/meta/result_count.json?reqno=1',
        f'api/data.json?page=1&limit={settings.DEFAULT_PAGE_LIMIT}',
        f'__api/dataimages.json?page=1&limit={settings.DEFAULT_PAGE_LIMIT}&reqno=1',
    ]
    requests.extend(
        f'__api/meta/range/endpoints/{slug}.json?reqno=1'
        for slug in default_widgets
        if form_types.get(slug) in settings.RANGE_FORM_TYPES
    )
    requests.append('__menu.json?reqno=1')
    mults = [slug for slug in default_widgets if form_types.get(slug) in settings.MULT_FORM_TYPES]
    mults.extend(
        slug
        for slug, form_type in fields
        if form_type in settings.MULT_FORM_TYPES and slug not in mults
    )
    requests.extend(f'__api/meta/mults/{slug}.json?reqno=1' for slug in mults)
    return requests


class Command(BaseCommand):
    """Answer the landing page's requests once, filling memcached and the buffer pool."""

    help = (
        "Issue the landing page's requests (the empty search's count, first page, default "
        'widgets and every mult count) through the application, so the cache holds them. '
        'Requires memcached.'
    )

    def handle(self, *args: Any, **options: Any) -> None:
        """Issue every request of `warm_requests` and report how long each took.

        Parameters:
            *args: Unused.
            **options: Unused.

        Raises:
            CommandError: If the cache is Django's local-memory fallback, or a request
                did not answer 200.
        """
        backend = str(settings.CACHES['default']['BACKEND'])
        if LOCMEM_MARKER in backend.lower():
            raise CommandError(
                f'the cache is {backend}, the local-memory fallback, which this process '
                'alone would hold: warm_search needs memcached running and pymemcache '
                'installed'
            )
        default_widgets = [slug for slug in settings.DEFAULT_WIDGETS.split(',') if slug]
        requests = warm_requests(searchable_fields(), default_widgets)
        host = warm_host(settings.ALLOWED_HOSTS)
        client = Client(HTTP_HOST=host, raise_request_exception=False)
        started = time.perf_counter()
        failed = []
        for url in requests:
            request_started = time.perf_counter()
            response = client.get(f'/{url}')
            seconds = time.perf_counter() - request_started
            self.stdout.write(f'{response.status_code} {seconds:8.3f} s  {url}')
            if response.status_code != 200:
                failed.append(f'{url} ({response.status_code})')
        self.stdout.write(
            f'Warmed {len(requests) - len(failed)} of {len(requests)} requests in '
            f'{time.perf_counter() - started:.3f} s'
        )
        if failed:
            raise CommandError(f'{len(failed)} requests failed: {", ".join(failed)}')
