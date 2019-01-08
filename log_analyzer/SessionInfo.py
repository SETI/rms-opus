import abc
import ipaddress
import re
import urllib.parse
from typing import List, Dict, Optional, Match, Tuple, Pattern, Callable, Any

import Slug
from LogEntry import LogEntry
from QueryHandler import QueryHandler, ColumnSlugInfo


class SessionInfoGenerator:
    """
    A generator class for creating a SessionInfo.
    """
    _slug_map: Slug.ToInfoMap
    _default_column_slug_info: ColumnSlugInfo
    _ignored_ips: List[ipaddress.IPv4Network]

    DEFAULT_COLUMN_INFO = 'opusid,instrument,planet,target,time1,observationduration'.split(',')

    def __init__(self, slug_info: Slug.ToInfoMap, ignored_ips: List[ipaddress.IPv4Network]):
        """

        :param slug_info: Information about the slugs we expect to see in the URL
        :param ignored_ips: A list representing hosts that we want to ignore
        """
        self._slug_map = slug_info
        self._default_column_slug_info = QueryHandler.get_column_slug_info(self.DEFAULT_COLUMN_INFO, slug_info)
        self._ignored_ips = ignored_ips

    def create(self, uses_html: bool = False) -> 'SessionInfo':
        """Create a new SessionInfo"""
        return _SessionInfoImpl(self._slug_map, self._default_column_slug_info, self._ignored_ips, uses_html)


class SessionInfo(metaclass=abc.ABCMeta):
    """
    A class that keeps track of information about the current user session and parses log entries based on information
    that it already knows about this session.

    This is an abstract class.  The user should only get instances of this class from the SessionInfoGenerator.
    """

    @abc.abstractmethod
    def parse_log_entry(self, entry: LogEntry) -> List[str]:
        raise Exception()

    @classmethod
    @abc.abstractmethod
    def all_search_slugs(cls) -> Dict[str, Slug.Info]:
        raise Exception()

    @classmethod
    @abc.abstractmethod
    def all_column_slugs(cls) -> Dict[str, Slug.Info]:
        raise Exception()


class ForPattern:
    """
    A Decorator used by SessionInfo.
    A method is decorated with the regex of the URLs that it knows how to parse.
    """
    METHOD = Callable[[Any, Dict[str, str], Match[str]], List[str]]

    PATTERNS: List[Tuple[Pattern[str], METHOD]] = []

    def __init__(self, pattern: str):
        self.pattern = re.compile(pattern + '$')

    def __call__(self, fn: METHOD, *args: Any, **kwargs: Any) -> METHOD:
        # We leave the function unchanged, but we add the regular expression and the function to our list of
        # regexp/function pairs
        ForPattern.PATTERNS.append((self.pattern, fn))
        return fn


def quote_and_join_list(string_list: List[str]) -> str:
    return ', '.join(f'"{string}"' for string in string_list)


# noinspection PyUnusedLocal
class _SessionInfoImpl(SessionInfo):
    _ignored_ips: List[ipaddress.IPv4Network]
    _previous_product_info_type: Optional[List[str]]
    _query_handler: QueryHandler
    _uses_html: bool

    def __init__(self, slug_map: Slug.ToInfoMap, default_column_slug_info: ColumnSlugInfo,
                 ignored_ips: List[ipaddress.IPv4Network], uses_html: bool):
        """This initialization should only be called by SessionInfoGenerator above."""
        self._ignored_ips = ignored_ips
        self._uses_html = uses_html
        self._query_handler = QueryHandler(slug_map, default_column_slug_info, uses_html)

        # The previous value of types when downloading a collection
        self._previous_product_info_type = None

    def parse_log_entry(self, entry: LogEntry) -> List[str]:
        """Parses a log record within the context of the current session."""

        # We ignore all sorts of log entries.
        if entry.method != 'GET' or entry.status != 200:
            return []
        if entry.agent and "bot" in entry.agent.lower():
            return []
        path = entry.url.path
        if not path.startswith('/opus/__'):
            return []
        if any(entry.host_ip in ipNetwork for ipNetwork in self._ignored_ips):
            return []

        # See if the path matches one of our patterns.
        path = path[5:]
        for (pattern, method) in ForPattern.PATTERNS:
            match = re.match(pattern, path)
            if match:
                # raw_query will match a key to a list of values for that key.  Opus only uses each key once
                # (values are separated by commas), so we convert the raw query to a more useful form.
                raw_query = urllib.parse.parse_qs(entry.url.query)
                query = {key: value[0]
                         for key, value in raw_query.items()
                         if isinstance(value, list) and len(value) == 1}
                return method(self, query, match)
        return []

    @classmethod
    def all_search_slugs(cls) -> Dict[str, Slug.Info]:
        return QueryHandler._all_search_slugs

    @classmethod
    def all_column_slugs(cls) -> Dict[str, Slug.Info]:
        return QueryHandler._all_column_slugs

    #
    # API
    #

    @ForPattern(r'/__api/(data)\.(.*)')
    @ForPattern(r'/__api/(images)\.(.*)')
    @ForPattern(r'/__api/meta/(result_count).json')
    def _api_data(self, query: Dict[str, str], match: Match[str]) -> List[str]:
        assert match.group(1) in ['data', 'images', 'result_count']
        return self._query_handler.handle_query(query, match.group(1))

    @ForPattern('/__api/image/med/(.*).json')
    def _view_metadata(self, query: Dict[str, str], match: Match[str]) -> List[str]:
        metadata = match.group(1)
        return [f'View Metadata: {metadata}']

    @ForPattern(r'/__api/data.csv')
    def _download_results_csv(self, query: Dict[str, str], match: Match[str]) -> List[str]:
        return ["Download Results CSV"]

    #
    # Collections
    #

    @ForPattern(r'/__collections/reset.html')
    def _reset_selections(self, query: Dict[str, str], match: Match[str]) -> List[str]:
        return ['Reset Selections']

    @ForPattern(r'/__collections(/default)?/(add|remove)\.json')
    def _change_selections(self, query: Dict[str, str], match: Match[str]) -> List[str]:
        opus_id = query.get('opus_id', '???')
        selection = match.group(2).title()
        return [f'Selections {selection.title() + ":":<7} {opus_id}']

    @ForPattern(r'/__collections(/default)?/view(|\.json)')
    def collections_view(self, query: Dict[str, str], match: Match[str]) -> List[str]:
        self._query_handler.reset()
        return ['View Selections']

    @ForPattern(r'/__collections/default/addrange.json')
    def _add_range_selections(self, query: Dict[str, str], match: Match[str]) -> List[str]:
        query_range = query.get('range', '???').replace(',', ', ')
        return [f'Selections Add Range: {query_range}']

    @ForPattern(r'/__collections(/default)?/download.zip')
    @ForPattern(r'/__collections/download/default.zip')
    def _create_zip_file(self, query: Dict[str, str], match: Match[str]) -> List[str]:
        self._query_handler.reset();
        types = query.get('types')
        if types is None:
            output = '???'
        else:
            output = quote_and_join_list(types.split(','))
        return [f'Create Zip File: {output}']

    @ForPattern(r'/__collections/download/info(|\.json)')
    def _download_product_types(self, query: Dict[str, str], match: Match[str]) -> List[str]:
        ptypes_field = query.get('types', None)
        new_ptypes = ptypes_field.split(',') if ptypes_field else []
        old_ptypes = self._previous_product_info_type
        self._previous_product_info_type = new_ptypes

        if old_ptypes is None:
            joined_new_ptypes = ', '.join(new_ptypes)
            plural = '' if len(new_ptypes) == 1 else 's'
            return [f'Download Product Type{plural}: {joined_new_ptypes}']

        result = []

        def show(verb: str, items: List[str]) -> None:
            if items:
                plural = 's' if len(items) > 1 else ''
                joined_items = quote_and_join_list(items)
                result.append(f'{verb.title()} Product Type{plural}: {joined_items}')

        show('add', [ptype for ptype in new_ptypes if ptype not in old_ptypes])
        show('remove', [ptype for ptype in old_ptypes if ptype not in new_ptypes])

        if not result:
            result.append('Product Types are unchanged')
        return result

    @ForPattern(r'/__collections/data.csv')
    def _download_selections_csv(self, query: Dict[str, str], match: Match[str]) -> List[str]:
        return ["Download Selections CSV"]


    #
    # FORMS
    #

    @ForPattern(r'/__forms/column_chooser.html')
    def _column_chooser(self, query: Dict[str, str], match: Match[str]) -> List[str]:
        return ['Column Chooser']

    #
    # INIT DETAIL
    #

    @ForPattern(r'/__initdetail/(.*).html')
    def _initialize_detail(self, query: Dict[str, str], match: Match[str]) -> List[str]:
        return [f'View Detail: {match.group(1)}']

