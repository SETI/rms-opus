"""The web scenarios: what ``scenarios/web.toml`` says, turned into request sequences.

A **scenario** is a named sequence of requests issued one after another with one cookie
jar, as a browser issues them. Most scenarios are written in ``web.toml`` by kind and
the search they act on, and expanded here into their requests:

``search``
    The search's result count, which is what builds a search.
``pages``
    The first, tenth and last page of the search's results through ``api/data.json``,
    preceded by an untimed result count so the pages measure paging and not the build.
``resort``
    The first page sorted by ``web.toml``'s re-sort order, preceded by an untimed first
    page in the default order, so the timed request re-sorts a search already built.
``fanout``
    What a user-interface load asks for: the result count, the mult counts of the
    default widgets, the range endpoints, and the menu (which carries the triggered
    tables).
``widget``
    One widget's HTML.
``categories``
    The categories of one observation.
``autocomplete``
    Autocomplete for a prefix of each length named, preceded by an untimed result count
    for the empty search so the search the autocomplete names is built first.
``files``
    The files of one observation, and the first page of a search's files.
``previews``
    The first and tenth page of a search through the results gallery and the public
    images API, one observation's detail page, and its medium image.
``concurrency``
    Many users at once, each with its own session; see `benchmarks.bench_web`.

A request's URL is relative to the server's root. ``{search}`` in a template stands
for a search's query string. The scenarios that name one observation (``categories``,
``files``, ``previews``) take the scale's from ``web.toml``'s ``[observations]``, because
no observation is in the data of every scale.
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

from benchmarks.results import SCENARIOS_DIR

if TYPE_CHECKING:
    from collections.abc import Mapping

WEB_TOML = SCENARIOS_DIR / 'web.toml'

#: The page size every paged request asks for.
PAGE_LIMIT = 100

#: The scenario kinds named for, and built on, one of the named searches.
SEARCH_KINDS = ('search', 'pages', 'resort', 'fanout', 'files', 'previews')

#: The scenario kinds that ask about the scale's observation.
OBSERVATION_KINDS = ('categories', 'files', 'previews')

#: The states a run resets to before a scenario, each of which may warm the landing page.
COLD_STATES = ('db-cold', 'app-cold')


class ScenarioError(Exception):
    """Raised when ``web.toml`` is inconsistent."""


@dataclass(frozen=True)
class WebServerSettings:
    """How the harness starts the servers a web run measures.

    Attributes:
        port: gunicorn's port on 127.0.0.1.
        workers: gunicorn worker processes.
        threads: Threads per worker, and connections each worker accepts.
        memcached_port: The owned memcached's port on 127.0.0.1.
        memcached_mb: The owned memcached's item memory.
    """

    port: int
    workers: int
    threads: int
    memcached_port: int
    memcached_mb: int

    @property
    def memcached_location(self) -> str:
        """The owned memcached as the application's ``cache_location`` names it."""
        return f'127.0.0.1:{self.memcached_port}'


@dataclass(frozen=True)
class Request:
    """One request of a scenario.

    Attributes:
        name: Its name within the scenario, which names its latency metric.
        url: Its URL, relative to the server's root, with every placeholder filled.
        timed: False for a request that only prepares the timed ones.
    """

    name: str
    url: str
    timed: bool = True


@dataclass(frozen=True)
class Scenario:
    """A named sequence of requests.

    Attributes:
        name: The scenario's name, ``<kind>.<subject>``.
        kind: Its kind.
        requests: Its requests in order. A ``pages`` scenario's last-page request is
            completed by `benchmarks.bench_web` once the result count is known.
        last_page_of: For a ``pages`` scenario, the search whose result count gives the
            last page; otherwise None.
    """

    name: str
    kind: str
    requests: tuple[Request, ...]
    last_page_of: str | None = None


@dataclass(frozen=True)
class Concurrency:
    """The concurrency scenario.

    Attributes:
        users: How many simulated users act at once.
        shared: The search every user asks for at the same moment.
        distinct: A search template with ``{i}`` for the user's number, so each user's
            search is new.
        fanout: The fan-out each user issues for its search, as URL templates.
    """

    users: int
    shared: str
    distinct: str
    fanout: tuple[Request, ...]


@dataclass(frozen=True)
class WebConfig:
    """Everything ``web.toml`` says.

    Attributes:
        path: The file.
        server: How the servers are started.
        runs: Web runs per side in a floor session, by scale.
        searches: The named searches, as query strings.
        scenarios: The sequential scenarios, in the order a pass runs them.
        concurrency: The concurrency scenario, run after them.
        warm: The cold states whose resets end with the side's ``warm_search``.
    """

    path: Path
    server: WebServerSettings
    runs: Mapping[str, int]
    searches: Mapping[str, str]
    scenarios: tuple[Scenario, ...] = ()
    concurrency: Concurrency | None = None
    warm: frozenset[str] = frozenset()


def _join(path: str, query: str) -> str:
    """Join a path and a query string, leaving out an empty query.

    Parameters:
        path: The URL path, possibly with a query already.
        query: Query parameters to add.

    Returns:
        The URL.
    """
    if query == '':
        return path
    return f'{path}&{query}' if '?' in path else f'{path}?{query}'


def _fanout_requests(raw: Mapping[str, Any], search: str) -> tuple[Request, ...]:
    """Expand the fan-out for one search.

    Parameters:
        raw: ``web.toml``'s ``[fanout]`` table.
        search: The search's query string.

    Returns:
        The result count, each mult count, each range endpoints request, and the menu.
    """
    requests = [
        Request('result_count', _join(_join('__api/meta/result_count.json', search), 'reqno=1'))
    ]
    for slug in raw['mult_widgets']:
        url = _join(_join(f'__api/meta/mults/{slug}.json', search), 'reqno=1')
        requests.append(Request(f'mults_{slug}', url))
    for slug in raw['range_slugs']:
        url = _join(_join(f'__api/meta/range/endpoints/{slug}.json', search), 'reqno=1')
        requests.append(Request(f'endpoints_{slug}', url))
    requests.append(Request('menu', _join(_join('__menu.json', search), 'reqno=1')))
    return tuple(requests)


def _expand(
    raw: Mapping[str, Any], entry: Mapping[str, Any], searches: Mapping[str, str], opus_id: str
) -> Scenario:
    """Expand one ``[[scenarios]]`` entry into its requests.

    Parameters:
        raw: The whole file.
        entry: The entry.
        searches: The named searches.
        opus_id: The scale's observation.

    Returns:
        The scenario.

    Raises:
        ScenarioError: If the entry names an unknown kind or search, lacks the search its
            kind needs, or needs an observation the scale does not name.
    """
    kind = entry['kind']
    requests: tuple[Request, ...]
    search_name = entry.get('search')
    if search_name is not None and search_name not in searches:
        raise ScenarioError(f'scenario {entry} names the unknown search {search_name!r}')
    if search_name is None and kind in SEARCH_KINDS:
        raise ScenarioError(f'scenario {entry} names no search')
    if opus_id == '' and kind in OBSERVATION_KINDS:
        raise ScenarioError(f"scenario {entry} needs this scale's [observations] entry")
    search = searches[search_name] if search_name is not None else ''
    limit = f'limit={PAGE_LIMIT}'
    if kind == 'search':
        url = _join(_join('__api/meta/result_count.json', search), 'reqno=1')
        return Scenario(f'search.{search_name}', kind, (Request('result_count', url),))
    if kind == 'pages':
        data = _join('api/data.json', search)
        requests = (
            Request(
                'build',
                _join(_join('__api/meta/result_count.json', search), 'reqno=1'),
                timed=False,
            ),
            Request('page_1', _join(data, f'page=1&{limit}')),
            Request('page_10', _join(data, f'page=10&{limit}')),
            Request('page_last', _join(data, f'page={{last}}&{limit}')),
        )
        return Scenario(f'pages.{search_name}', kind, requests, last_page_of=search_name)
    if kind == 'resort':
        data = _join('api/data.json', search)
        order = raw['resort']['order']
        requests = (
            Request('default_order', _join(data, f'page=1&{limit}'), timed=False),
            Request('resorted', _join(data, f'order={order}&page=1&{limit}')),
        )
        return Scenario(f'resort.{search_name}', kind, requests)
    if kind == 'fanout':
        return Scenario(f'fanout.{search_name}', kind, _fanout_requests(raw['fanout'], search))
    if kind == 'widget':
        slug = entry['slug']
        return Scenario(f'widget.{slug}', kind, (Request('widget', f'__widget/{slug}.html'),))
    if kind == 'categories':
        return Scenario(
            'categories', kind, (Request('categories', f'api/categories/{opus_id}.json'),)
        )
    if kind == 'autocomplete':
        slug = entry['slug']
        requests_list = [Request('build', '__api/meta/result_count.json?reqno=1', timed=False)]
        for prefix in entry['prefixes']:
            url = f'__api/stringsearchchoices/{slug}.json?{slug}={prefix}&reqno=1'
            requests_list.append(Request(f'prefix_{len(prefix)}', url))
        return Scenario(f'autocomplete.{slug}', kind, tuple(requests_list))
    if kind == 'files':
        requests = (
            Request('one_observation', f'api/files/{opus_id}.json'),
            Request('search_page_1', _join(_join('api/files.json', search), f'page=1&{limit}')),
        )
        return Scenario(f'files.{search_name}', kind, requests)
    if kind == 'previews':
        gallery = _join('__api/dataimages.json', search)
        images = _join('api/images.json', search)
        requests = (
            Request('gallery_page_1', _join(gallery, f'page=1&{limit}&reqno=1')),
            Request('gallery_page_10', _join(gallery, f'page=10&{limit}&reqno=1')),
            Request('images_page_1', _join(images, f'page=1&{limit}')),
            Request('images_page_10', _join(images, f'page=10&{limit}')),
            Request('detail', f'__initdetail/{opus_id}.html'),
            Request('image_med', f'api/image/med/{opus_id}.json'),
        )
        return Scenario(f'previews.{search_name}', kind, requests)
    raise ScenarioError(f'scenario {entry} has the unknown kind {kind!r}')


def load_web_config(path: Path = WEB_TOML, *, scale: str = 'test') -> WebConfig:
    """Read ``web.toml``.

    Parameters:
        path: The file.
        scale: The scale whose observation the scenarios that name one use.

    Returns:
        Its server settings, run counts, searches and expanded scenarios.

    Raises:
        ScenarioError: If two scenarios share a name, an entry is malformed, or
            ``[warm]`` names a state that is not a cold one or gives one no boolean.
    """
    with path.open('rb') as stream:
        raw = tomllib.load(stream)
    warm_flags = raw.get('warm', {})
    unknown = sorted(set(warm_flags) - set(COLD_STATES))
    if len(unknown) > 0:
        raise ScenarioError(f'{path}: [warm] names {unknown}, not one of {list(COLD_STATES)}')
    if not all(isinstance(flag, bool) for flag in warm_flags.values()):
        raise ScenarioError(f'{path}: [warm] takes true or false for each state')
    server = raw['server']
    searches = {str(name): str(value) for name, value in raw['searches'].items()}
    opus_id = str(raw.get('observations', {}).get(scale, ''))
    scenarios = tuple(_expand(raw, entry, searches, opus_id) for entry in raw.get('scenarios', ()))
    names = [scenario.name for scenario in scenarios]
    duplicates = sorted({name for name in names if names.count(name) > 1})
    if len(duplicates) > 0:
        raise ScenarioError(f'{path}: scenario names used twice: {duplicates}')
    for scenario in scenarios:
        # A request's name is its metric's, so two of one name would overwrite each other.
        requests = [request.name for request in scenario.requests]
        if len(set(requests)) != len(requests):
            raise ScenarioError(f'{path}: {scenario.name} names two requests alike: {requests}')
    concurrency = None
    if 'concurrency' in raw:
        entry = raw['concurrency']
        concurrency = Concurrency(
            users=int(entry['users']),
            shared=searches[entry['shared']],
            distinct=str(entry['distinct']),
            fanout=_fanout_requests(raw['fanout'], '{search}'),
        )
    return WebConfig(
        path=path,
        server=WebServerSettings(
            port=int(server['port']),
            workers=int(server['workers']),
            threads=int(server['threads']),
            memcached_port=int(server['memcached_port']),
            memcached_mb=int(server['memcached_mb']),
        ),
        runs={str(scale): int(count) for scale, count in raw['runs'].items()},
        searches=searches,
        scenarios=scenarios,
        concurrency=concurrency,
        warm=frozenset(state for state, flag in warm_flags.items() if flag),
    )
