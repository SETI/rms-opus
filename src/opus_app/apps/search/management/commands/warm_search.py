"""``opus_manage warm_search``: ask the site for the common searches once, so they are ready.

Every visitor's first search is the empty one, in the default sort, and most next choose
one value of a general constraint: a planet, a mission, an instrument. This command asks
the running site's API for what those searches show, over HTTP and several requests at
a time, so that the first visitor after a deploy finds each search's results built in
``search_results``, its answers cached, the rows they read in the database's buffer pool,
and the web server's workers past their first request:

* for the empty search, its result count; its first page, through the public
  ``api/data.json`` and the results gallery's ``__api/dataimages.json``; the fan-out of
  the default widgets (``settings.DEFAULT_WIDGETS``): the range endpoints of those that
  are ranges, and the menu, which carries the triggered tables; and the mult counts of
  every mult field ``api/fields.json`` lists, so that opening any mult widget is a cache
  hit;
* for one search per value of each field of `COMMON_SEARCH_FIELDS`, the same count, first
  page, default widgets' fan-out and menu, and the searched field's own counts. The
  values are those the empty search's mult counts for the field name, so every one is a
  value some observation holds.

The fields and the values come from the API, so the command reads nothing itself. The
empty search's count is asked for first, alone, since every other request of the empty
search needs its results; then the rest run concurrently, each common search's requests
in order, so that its count builds its results before its pages read them.
"""

from __future__ import annotations

import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import TYPE_CHECKING, Any
from urllib.parse import urlencode, urljoin

import requests
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

if TYPE_CHECKING:
    from argparse import ArgumentParser
    from collections.abc import Sequence
    from concurrent.futures import Future


#: The fields for each of whose values one search is warmed, the general constraints a
#: visitor most often searches on alone. ``target`` is not among them, since its values run
#: to every body observed, most of which few visitors search for.
COMMON_SEARCH_FIELDS = (
    'planet',
    'targetclass',
    'mission',
    'insthost',
    'instrument',
    'observationtype',
    'quantity',
)

#: How many requests are in flight at once unless ``--parallel`` says otherwise.
DEFAULT_PARALLEL = 8

#: How long one request may take. A search's first request builds its results, which
#: for a search matching most of the archive takes far longer than a page view.
REQUEST_TIMEOUT_SECONDS = 600.0

#: The ``type`` ``api/fields.json`` gives a mult field.
MULT_TYPE = 'multiple'

#: The prefix of the ``type`` ``api/fields.json`` gives a range field.
RANGE_TYPE_PREFIX = 'range_'


def default_site_url() -> str:
    """Return the site's API root: the public URL, under the path the web server serves at.

    Returns:
        ``settings.PUBLIC_OPUS_URL`` joined with ``settings.BASE_PATH``, ending in a slash.
    """
    return urljoin(settings.PUBLIC_OPUS_URL, f'{settings.BASE_PATH}/')


def api_fields(content: bytes) -> list[tuple[str, str]]:
    """Return every field an ``api/fields.json`` answer describes, with its type.

    Parameters:
        content: The body of the answer.

    Returns:
        Each field's slug and ``type``, in the answer's order, which is the categories'
        table order and each category's display order. A field the answer lists in more
        than one category, as a linked field, appears once, where it first does.
    """
    categories: dict[str, dict[str, dict[str, Any]]] = json.loads(content)['data']
    types: dict[str, str] = {}
    for category in categories.values():
        for entry in category.values():
            types.setdefault(str(entry['field_id']), str(entry['type']))
    return list(types.items())


def _search_requests(
    query: str, range_slugs: Sequence[str], mult_slugs: Sequence[str]
) -> list[str]:
    """Return one search's requests, in the order they are issued.

    Parameters:
        query: The search's query string, empty for the empty search.
        range_slugs: The range widgets whose endpoints are asked for.
        mult_slugs: The mult widgets whose counts are asked for.

    Returns:
        The URLs relative to the site's API root: the result count, the first page twice,
        the range endpoints, the menu, then the mult counts.
    """
    search = f'{query}&' if query else ''
    requests = [
        f'__api/meta/result_count.json?{search}reqno=1',
        f'api/data.json?{search}page=1&limit={settings.DEFAULT_PAGE_LIMIT}',
        f'__api/dataimages.json?{search}page=1&limit={settings.DEFAULT_PAGE_LIMIT}&reqno=1',
    ]
    requests.extend(
        f'__api/meta/range/endpoints/{slug}.json?{search}reqno=1' for slug in range_slugs
    )
    requests.append(f'__menu.json?{search}reqno=1')
    requests.extend(f'__api/meta/mults/{slug}.json?{search}reqno=1' for slug in mult_slugs)
    return requests


def _default_widgets_of(
    types: dict[str, str], default_widgets: Sequence[str]
) -> tuple[list[str], list[str]]:
    """Return the default widgets that are ranges, and those that are mults."""
    ranges = [slug for slug in default_widgets if types.get(slug, '').startswith(RANGE_TYPE_PREFIX)]
    mults = [slug for slug in default_widgets if types.get(slug) == MULT_TYPE]
    return ranges, mults


def warm_requests(fields: Sequence[tuple[str, str]], default_widgets: Sequence[str]) -> list[str]:
    """Return the requests that warm the landing page, in the order they are issued.

    Parameters:
        fields: Every field's slug and type (`api_fields`).
        default_widgets: The slugs of the widgets the landing page opens.

    Returns:
        The URLs relative to the site's API root, in this order -- the result count, the
        first page twice, the range endpoints of each default widget that is a range,
        the menu, then every mult field's counts, default widgets first.
    """
    ranges, mults = _default_widgets_of(dict(fields), default_widgets)
    for slug, kind in fields:
        if kind == MULT_TYPE and slug not in mults:
            mults.append(slug)
    return _search_requests('', ranges, mults)


def value_search_requests(
    slug: str, value: str, fields: Sequence[tuple[str, str]], default_widgets: Sequence[str]
) -> list[str]:
    """Return the requests a search for one value of one field makes, in order.

    Parameters:
        slug: The searched field.
        value: The value searched for, as the field's mult counts name it.
        fields: Every field's slug and type (`api_fields`).
        default_widgets: The slugs of the widgets the landing page opens.

    Returns:
        The URLs relative to the site's API root, in this order -- the search's result
        count, its first page twice, the range endpoints of each default widget that is
        a range, the menu, then the counts of each default widget that is a mult and of
        the searched field.
    """
    ranges, mults = _default_widgets_of(dict(fields), default_widgets)
    if slug not in mults:
        mults.append(slug)
    return _search_requests(urlencode({slug: value}), ranges, mults)


def counted_values(content: bytes) -> list[str]:
    """Return the values a mult counts answer names, in its order.

    Parameters:
        content: The body of a ``__api/meta/mults`` answer.

    Returns:
        Each value with a count, as the answer's ``mults`` names it.
    """
    mults: dict[str, int] = json.loads(content)['mults']
    return [value for value, count in mults.items() if count]


def fetch(session: requests.Session, url: str) -> tuple[int, bytes]:
    """Ask for one URL.

    Parameters:
        session: The session every request shares, which carries the site's cookie.
        url: The absolute URL.

    Returns:
        The answer's status and body.

    Raises:
        requests.RequestException: If no answer came.
    """
    response = session.get(url, timeout=REQUEST_TIMEOUT_SECONDS)
    return response.status_code, response.content


#: The outcome of one request, as its URL relative to the API root, its status or the
#: reason no answer came, the seconds it took, and its body.
Outcome = tuple[str, int | str, float, bytes]


def _issue_in_order(session: requests.Session, site: str, urls: Sequence[str]) -> list[Outcome]:
    """Ask for each URL in turn, after the one before it has answered."""
    outcomes: list[Outcome] = []
    for url in urls:
        started = time.perf_counter()
        status: int | str
        try:
            status, content = fetch(session, site + url)
        except requests.RequestException as error:
            status, content = f'no answer: {error}', b''
        outcomes.append((url, status, time.perf_counter() - started, content))
    return outcomes


class Command(BaseCommand):
    """Ask the site for the common searches once, building their results and caching them."""

    help = (
        "Ask the site's API for the landing page (the empty search's count, first page, "
        'default widgets and every mult count) and for one search per value of each '
        'common field, several requests at a time, so that their results are built and '
        'cached.'
    )

    def add_arguments(self, parser: ArgumentParser) -> None:
        """Add ``--url`` and ``--parallel``.

        Parameters:
            parser: The command's argument parser.
        """
        parser.add_argument(
            '--url',
            help='the API root to warm, such as http://localhost/opus/ (default: the '
            'configured public_url joined with the base path the web server serves at)',
        )
        parser.add_argument(
            '--parallel',
            type=int,
            default=DEFAULT_PARALLEL,
            help=f'how many requests are in flight at once (default {DEFAULT_PARALLEL})',
        )

    def handle(self, *args: Any, **options: Any) -> None:
        """Ask for the empty search's count, then everything else concurrently.

        Parameters:
            *args: Unused.
            **options: ``url`` and ``parallel``.

        Raises:
            CommandError: If ``--parallel`` is not positive, ``api/fields.json`` does
                not answer, or a request did not answer 200.
        """
        parallel: int = options['parallel']
        if parallel < 1:
            raise CommandError(f'--parallel must be at least 1, not {parallel}')
        site: str = options['url'] or default_site_url()
        if not site.endswith('/'):
            site += '/'
        session = requests.Session()
        started = time.perf_counter()
        issued = 0
        failed: list[str] = []

        def report(outcomes: list[Outcome]) -> None:
            nonlocal issued
            for url, status, seconds, _content in outcomes:
                self.stdout.write(f'{status} {seconds:8.3f} s  {url}')
                issued += 1
                if status != 200:
                    failed.append(f'{url} ({status})')

        (fields_answer,) = _issue_in_order(session, site, ['api/fields.json'])
        report([fields_answer])
        if fields_answer[1] != 200:
            raise CommandError(f'{site}api/fields.json answered {fields_answer[1]}')
        fields = api_fields(fields_answer[3])
        types = dict(fields)
        default_widgets = [slug for slug in settings.DEFAULT_WIDGETS.split(',') if slug]
        landing = warm_requests(fields, default_widgets)
        report(_issue_in_order(session, site, landing[:1]))

        counted = {f'__api/meta/mults/{slug}.json?reqno=1': slug for slug in COMMON_SEARCH_FIELDS}
        values: dict[str, list[str]] = {}
        with ThreadPoolExecutor(max_workers=parallel) as pool:
            pending: list[Future[list[Outcome]]] = [
                pool.submit(_issue_in_order, session, site, [url]) for url in landing[1:]
            ]
            for future in as_completed(pending):
                outcomes = future.result()
                report(outcomes)
                for url, status, _seconds, content in outcomes:
                    if url in counted and status == 200:
                        values[counted[url]] = counted_values(content)
            searches = [
                value_search_requests(slug, value, fields, default_widgets)
                for slug in COMMON_SEARCH_FIELDS
                if types.get(slug) == MULT_TYPE
                for value in values.get(slug, [])
            ]
            for future in as_completed(
                [pool.submit(_issue_in_order, session, site, urls) for urls in searches]
            ):
                report(future.result())
        self.stdout.write(
            f'Warmed {issued - len(failed)} of {issued} requests, for the empty search and '
            f'{len(searches)} common searches, in {time.perf_counter() - started:.3f} s'
        )
        if failed:
            raise CommandError(f'{len(failed)} requests failed: {", ".join(failed)}')
