import abc
import ipaddress
import re
import urllib.parse
from typing import List, Dict, Optional, Match, Tuple, Pattern, Any

from LogEntry import LogEntry
from SlugInfo import SlugInfo


class ForPattern:
    """
    A Decorator used by SessionInfo.
    A method is decorated with the regex of the URLs that it knows how to parse.
    """
    PATTERNS: List[Tuple[Pattern, Any]] = []

    def __init__(self, pattern: str):
        self.pattern = re.compile(pattern + '$')

    def __call__(self, fn, *args, **kwargs):
        # We leave the function unchanged, but we add the regular expression and the function to our list of
        # regexp/function pairs
        ForPattern.PATTERNS.append((self.pattern, fn))
        return fn


class SessionInfo(metaclass=abc.ABCMeta):
    """
    A class that keeps track of information about the current user session and parses log entries based on information
    that it already knows about this session.

    This is an abstract class.  The user should only get instances of this class from the SessionInfoGenerator.
    """

    @abc.abstractmethod
    def parse_log_entry(self, entry: LogEntry) -> Optional[List[str]]:
        raise Exception()


class SessionInfoGenerator:
    """
    A generator class for creating a SessionInfo.
    """
    _slug_info: SlugInfo
    _default_column_list: Dict[str, Optional[str]]
    _ignored_ips: List[ipaddress.IPv4Network]

    DEFAULT_COLUMN_INFO = 'opusid,instrument,planet,target,time1,observationduration'.split(',')

    def __init__(self, slug_info: SlugInfo, ignored_ips: List[ipaddress.IPv4Network]):
        """

        :param slug_info: Information about the slugs we expect to see in the URL
        :param ignored_ips: A list representing hosts that we want to ignore
        """
        self._slug_info = slug_info
        self._default_column_list = {
            info: extra_info
            for slug in self.DEFAULT_COLUMN_INFO
            for info, extra_info in [self._slug_info.get_info_for_search_slug(slug) or (None, None)]
            if info is not None
        }

        self._ignored_ips = ignored_ips

    def create(self) -> SessionInfo:
        """Create a new SessionInfo"""
        return _SessionInfoImpl(self._slug_info, self._default_column_list, self._ignored_ips)


# noinspection PyUnusedLocal
class _SessionInfoImpl(SessionInfo):
    _slug_info: SlugInfo
    _default_column_info: Dict[str, Optional[str]]
    _ignored_ips: List[ipaddress.IPv4Network]
    _previous_product_info_type: Optional[List[str]]
    _previous_api_query: Optional[Dict[str, str]]

    def __init__(self, slug_info: SlugInfo, default_column_info: Dict[str, Optional[str]],
                 ignored_ips: List[ipaddress.IPv4Network]):
        """This initialization should only be called by SessionInfoGenerator above."""
        self._slug_info = slug_info
        self._default_column_info = default_column_info
        self._ignored_ips = ignored_ips

        # The previous value of types when downloading a collection
        self._previous_product_info_type = None

        # The previous query when using /__api/
        self._previous_api_query = None

    def parse_log_entry(self, entry: LogEntry) -> Optional[List[str]]:
        """Parses a log record within the context of the current session."""

        # We ignore all sorts of log entries.
        if entry.method != 'GET' or entry.status != 200:
            return None
        if entry.agent and "bot" in entry.agent.lower():
            return None
        path = entry.url.path
        if not path.startswith('/opus/__'):
            return None
        if any(entry.host_ip in ipNetwork for ipNetwork in self._ignored_ips):
            return None

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
                return method(self, entry=entry, query=query, match=match)
        return None

    #
    # API
    #

    @ForPattern(r'/__api/data\.(.*)')
    @ForPattern(r'/__api/images\.(.*)')
    def _api_data(self, entry: LogEntry, query: Dict[str, str], match: Match) -> Optional[List[str]]:
        cols = query.get('cols', None)
        if cols and cols.lower() not in ('0', 'false'):
            return self.__handle_query(query)
        page = query.get('page', '???')
        if query.get('browse', None) == 'data':
            return [f'View Table: Page {page}']
        else:
            return [f'View Gallery: Page {page}']

    @ForPattern('/__api/image/med/(.*).json')
    def _view_metadata(self, entry: LogEntry, query: Dict[str, str], match: Match) -> List[str]:
        metadata = match.group(1)
        return [f'View Metadata: {metadata}']

    @ForPattern('/__api/meta/result_count.json')
    def _get_info(self, entry: LogEntry, query: Dict[str, str], match: Match) -> Optional[List[str]]:
        return self.__handle_query(query)

    #
    # Collections
    #

    @ForPattern(r'/__collections/reset.html')
    def _reset_selections(self, entry: LogEntry, query: Dict[str, str], match: Match) -> List[str]:
        return ['Reset Selections']

    @ForPattern(r'/__collections(/default)?/(add|remove).json')
    def _change_selections(self, entry: LogEntry, query: Dict[str, str], match: Match) -> List[str]:
        opus_id = query.get('opus_id', '???')
        selection = match.group(2).title()
        return [f'Selections {selection}: {opus_id}']

    @ForPattern(r'/__collections(/default)?/view.json')
    def collections_view(self, entry: LogEntry, query: Dict[str, str], match: Match) -> List[str]:
        return ['View Selections']

    @ForPattern(r'/__collections/default/addrange.json')
    def _add_range_selections(self, entry: LogEntry, query: Dict[str, str], match: Match) -> List[str]:
        query_range = query.get('range', '???').replace(',', ', ')
        return [f'Selections Add Range: {query_range}']

    @ForPattern(r'/__collections(/download)?/default.zip')
    def _create_zip_file(self, entry: LogEntry, query: Dict[str, str], match: Match) -> List[str]:
        types = query.get('types', None)
        if types is None:
            output = '???'
        else:
            output = self.__quote_and_join_list(types.split(','))
        return [f'Create Zip File: {output}']

    @ForPattern(r'/__collections/download/info')
    def _download_product_types(self, entry: LogEntry, query: Dict[str, str], match: Match) -> List[str]:
        ptypes_field = query.get('types', None)
        new_ptypes = ptypes_field.split(',') if ptypes_field else []
        old_ptypes = self._previous_product_info_type
        self._previous_product_info_type = new_ptypes

        if old_ptypes is None:
            joined_new_ptypes = ', '.join(new_ptypes)
            return [f'Download Product Types: {joined_new_ptypes}']

        result = []

        def show(verb: str, items: List[str]) -> None:
            if items:
                plural = 's' if len(items) > 1 else ''
                joined_items = self.__quote_and_join_list(items)
                result.append(f'{verb.title()} Product Type{plural}: {joined_items}')

        show('add', [ptype for ptype in new_ptypes if ptype not in old_ptypes])
        show('remove', [ptype for ptype in old_ptypes if ptype not in new_ptypes])

        if not result:
            result.append('Product Types are unchanged')
        return result

    #
    # FORMS
    #

    @ForPattern(r'/__forms/column_chooser.html')
    def _column_chooser(self, entry: LogEntry, query: Dict[str, str], match: Match) -> List[str]:
        return ['Column Chooser']

    #
    # INIT DETAIL
    #

    @ForPattern(r'/__initdetail/(.*).html')
    def _initialize_detail(self, entry: LogEntry, query: Dict[str, str], match: Match) -> List[str]:
        return [f'View Detail: {match.group(1)}']

    def __handle_query(self, new_query: Dict[str, str]) -> Optional[List[str]]:
        result: List[str] = []
        old_query = self._previous_api_query
        self._previous_api_query = new_query

        self.__get_query_info_search_slugs(old_query, new_query, result)
        self.__get_query_info_column_names(old_query, new_query, result)
        self.__get_query_info_page_number(old_query, new_query, result)
        return result or None  # convert empty result to None

    QTYPE_SLUG_SUFFIX_LENGTH = len(SlugInfo.QT_SUFFIX)

    def __get_query_info_search_slugs(self, old_query: Optional[Dict[str, str]], new_query: Dict[str, str],
                                      result: List[str]):
        def get_info_for_query_slugs(query):
            return {slug: (info, extra_info, value)
                    for slug, value in query.items()
                    for info, extra_info in [self._slug_info.get_info_for_search_slug(slug) or (None, None)]
                    if info is not None
                    }

        if old_query is not None:
            old_search_slug_info = get_info_for_query_slugs(old_query)
        else:
            result.append('Empty Search')
            old_search_slug_info = {}
        new_search_slug_info = get_info_for_query_slugs(new_query)
        all_search_slugs = set(old_search_slug_info.keys()).union(new_search_slug_info.keys())
        for slug in sorted(all_search_slugs):
            is_normal_slug = not slug.startswith('qtype-')
            if slug in new_search_slug_info and slug not in old_search_slug_info:
                search, extra_info, value = new_search_slug_info[slug]
                postscript = f' **{extra_info}**' if extra_info else ''
                if is_normal_slug:
                    result.append(f'Add Search: "{search}" = "{value}"{postscript}')
                else:
                    search = search[:-self.QTYPE_SLUG_SUFFIX_LENGTH]
                    result.append(f'Change qtype for "{search:}" = default -> "{value}"{postscript}')
            elif slug in old_search_slug_info and slug not in new_search_slug_info:
                search, extra_info, value = old_search_slug_info[slug]
                if is_normal_slug:
                    result.append(f'Remove Search: "{search}"')
                else:
                    base_slug = slug[6:]  # remove initial 'qtype-'
                    if base_slug in new_search_slug_info:
                        search = search[:-self.QTYPE_SLUG_SUFFIX_LENGTH]
                        result.append(f'Change qtype for "{search}" = "{value}" -> default')
            else:
                _, _, old_value = old_search_slug_info[slug]
                search, extra_info, new_value = new_search_slug_info[slug]
                if is_normal_slug:
                    if is_normal_slug:
                        self.__slug_value_change(search, old_value, new_value, result)
                    else:
                        search = search[:-self.QTYPE_SLUG_SUFFIX_LENGTH]
                        result.append(f'Change qtype for "{search}" = "{old_value}" -> "{new_value}"')

    def __get_query_info_column_names(self, old_query: Optional[Dict[str, str]], new_query: Dict[str, str],
                                      result: List[str]):
        def get_info_for_column_slugs(query):
            columns_query = query.get('cols', None) if query else None
            if columns_query:
                columns = columns_query.split(',')
                return {info: extra_info
                        for slug in columns
                        for info, extra_info in [self._slug_info.get_info_for_search_slug(slug) or (None, None)]
                        if info is not None
                        }
            else:
                return self._default_column_info

        old_column_info = get_info_for_column_slugs(old_query)
        new_column_info = get_info_for_column_slugs(new_query)
        old_columns = set(old_column_info.keys())
        new_columns = set(new_column_info.keys())
        if new_columns == old_columns:
            return
        if new_columns == set(self._default_column_info.keys()):
            result.append('Reset Columns')
            return
        all_columns = old_columns.union(new_columns)
        for column in sorted(all_columns):
            if column in new_columns and column not in old_columns:
                extra_info = new_column_info[column]
                postscript = f' **{extra_info}**' if extra_info else ''
                result.append(f'Add Column: "{column}{postscript}"')
            elif column in old_columns and column not in new_column_info:
                result.append(f'Remove Column: "{column}"')

    def __get_query_info_page_number(self, old_query: Optional[Dict[str, str]], new_query: Dict[str, str],
                                     result: List[str]):
        if old_query and 'page' in old_query and 'page' in new_query and old_query['page'] != new_query['page']:
            result.append(f'Change Page: {old_query["page"]} -> {new_query["page"]}')

    def __slug_value_change(self, name: str, old_value: str, new_value: str, result: List[str]) -> None:
        old_value_set = set(old_value.split(','))
        new_value_set = set(new_value.split(','))
        if old_value_set.intersection(new_value_set):
            change_list: List[str] = []
            for value in sorted(old_value_set.union(new_value_set)):
                if value in new_value_set and value not in old_value_set:
                    change_list.append(f'+"{value}"')
                elif value in old_value_set and value not in new_value_set:
                    change_list.append(f'-"{value}"')
            if change_list:
                joined_change_list = ', '.join(change_list)
                result.append(f'Change Search: "{name}" = {joined_change_list}')
        else:
            joined_old_value_set = self.__quote_and_join_list(sorted(old_value_set))
            joined_new_value_set = self.__quote_and_join_list(sorted(new_value_set))
            result.append(f'Change Search: "{name}" = {joined_old_value_set} -> {joined_new_value_set}')

    @staticmethod
    def __quote_and_join_list(string_list: List[str]) -> str:
        return ', '.join(f'"{string}"' for string in string_list)
