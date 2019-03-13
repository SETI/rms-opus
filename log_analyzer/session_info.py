import abc
import ipaddress
import re
import urllib.parse
from enum import auto, Flag
from typing import List, Dict, Optional, Match, Tuple, Pattern, Callable, Any

from markupsafe import Markup

import slug
from log_entry import LogEntry
from query_handler import QueryHandler, ColumnSlugInfo

SESSION_INFO = Tuple[List[str], Optional[str]]


class SessionInfoGenerator:
    """
    A generator class for creating a SessionInfo.
    """
    _slug_map: slug.ToInfoMap
    _default_column_slug_info: ColumnSlugInfo
    _ignored_ips: List[ipaddress.IPv4Network]
    _debug_show_all: bool

    DEFAULT_COLUMN_INFO = 'opusid,instrument,planet,target,time1,observationduration'.split(',')

    def __init__(self, slug_info: slug.ToInfoMap, ignored_ips: List[ipaddress.IPv4Network], debug_show_all: bool):
        """

        :param slug_info: Information about the slugs we expect to see in the URL
        :param ignored_ips: A list representing hosts that we want to ignore
        """
        self._slug_map = slug_info
        self._default_column_slug_info = QueryHandler.get_column_slug_info(self.DEFAULT_COLUMN_INFO, slug_info)
        self._ignored_ips = ignored_ips
        self._debug_show_all = debug_show_all

    def create(self, uses_html: bool = False) -> 'SessionInfo':
        """Create a new SessionInfo"""
        return SessionInfoImpl(
            self._slug_map, self._default_column_slug_info, self._ignored_ips, self._debug_show_all, uses_html)


class ActionFlags(Flag):
    # These should be in the order we want to see them in the output
    HAS_SEARCH = auto()
    FETCHED_GALLERY = auto()
    HAS_COLUMNS = auto()
    HAS_DOWNLOAD = auto()
    HAS_OBSOLETE_SLUG = auto()


class SessionInfo(metaclass=abc.ABCMeta):
    """
    A class that keeps track of information about the current user session and parses log entries based on information
    that it already knows about this session.

    This is an abstract class.  The user should only get instances of this class from the SessionInfoGenerator.
    """
    _session_search_slugs: Dict[str, slug.Info]
    _session_column_slugs: Dict[str, slug.Info]
    _action_flags: ActionFlags

    def __init__(self) -> None:
        self._session_search_slugs = dict()
        self._session_column_slugs = dict()
        self._action_flags = ActionFlags(0)

    @abc.abstractmethod
    def parse_log_entry(self, entry: LogEntry) -> SESSION_INFO:
        raise Exception()

    def add_search_slug(self, slug: str, slug_info: slug.Info) -> None:
        self._session_search_slugs[slug] = slug_info
        if slug_info.flags.is_obsolete():
            self._action_flags |= ActionFlags.HAS_OBSOLETE_SLUG

    def add_column_slug(self, slug: str, slug_info: slug.Info) -> None:
        self._session_column_slugs[slug] = slug_info
        if slug_info.flags.is_obsolete():
            self._action_flags |= ActionFlags.HAS_OBSOLETE_SLUG

    def changed_search_slugs(self) -> None:
        self._action_flags |= ActionFlags.HAS_SEARCH

    def changed_column_slugs(self) -> None:
        self._action_flags |= ActionFlags.HAS_COLUMNS

    def performed_download(self) -> None:
        self._action_flags |= ActionFlags.HAS_DOWNLOAD

    def fetched_gallery(self) -> None:
        self._action_flags |= ActionFlags.FETCHED_GALLERY

    @property
    def session_search_slugs(self) -> Dict[str, slug.Info]:
        return self._session_search_slugs

    @property
    def session_column_slugs(self) -> Dict[str, slug.Info]:
        return self._session_column_slugs

    @property
    def action_flags(self) -> ActionFlags:
        return self._action_flags

    @staticmethod
    def quote_and_join_list(string_list: List[str]) -> str:
        return ', '.join(f'"{string}"' for string in string_list)

    @staticmethod
    def safe_format(format_string: str, *args: Any) -> str:
        return Markup(format_string).format(*args)


class ForPattern:
    """
    A Decorator used by SessionInfo.
    A method is decorated with the regex of the URLs that it knows how to parse.
    """

    METHOD = Callable[[Any, Dict[str, str], Match[str]], SESSION_INFO]

    PATTERNS: List[Tuple[Pattern[str], METHOD]] = []

    def __init__(self, pattern: str):
        self.pattern = re.compile(pattern + '$')

    def __call__(self, fn: METHOD, *args: Any, **kwargs: Any) -> METHOD:
        # We leave the function unchanged, but we add the regular expression and the function to our list of
        # regexp/function pairs
        ForPattern.PATTERNS.append((self.pattern, fn))
        return fn


# noinspection PyUnusedLocal
class SessionInfoImpl(SessionInfo):
    _ignored_ips: List[ipaddress.IPv4Network]
    _previous_product_info_type: Optional[List[str]]
    _query_handler: QueryHandler
    _show_all: bool

    def __init__(self, slug_map: slug.ToInfoMap, default_column_slug_info: ColumnSlugInfo,
                 ignored_ips: List[ipaddress.IPv4Network], show_all: bool, uses_html: bool):
        """This initialization should only be called by SessionInfoGenerator above.
        """
        super(SessionInfoImpl, self).__init__()
        self._ignored_ips = ignored_ips
        self._query_handler = QueryHandler(self, slug_map, default_column_slug_info, uses_html)
        self._uses_html = uses_html
        self._show_all = show_all

        # The previous value of types when downloading a collection
        self._previous_product_info_type = None

    def parse_log_entry(self, entry: LogEntry) -> SESSION_INFO:
        """Parses a log record within the context of the current session."""

        # We ignore all sorts of log entries.
        if entry.method != 'GET' or entry.status != 200:
            return [], None
        if entry.agent and "bot" in entry.agent.lower():
            return [], None
        path = entry.url.path
        if not path.startswith('/opus/__'):
            return [], None
        if any(entry.host_ip in ipNetwork for ipNetwork in self._ignored_ips):
            return [], None

        # See if the path matches one of our patterns.
        path = path[5:]
        info: List[str]
        info, reference = [], None
        for (pattern, method) in ForPattern.PATTERNS:
            match = re.match(pattern, path)
            if match:
                # raw_query will match a key to a list of values for that key.  Opus only uses each key once
                # (values are separated by commas), so we convert the raw query to a more useful form.
                raw_query = urllib.parse.parse_qs(entry.url.query)
                query = {key: value[0]
                         for key, value in raw_query.items()
                         if isinstance(value, list) and len(value) == 1}
                info, reference = method(self, query, match)
                break
        if self._show_all and not info:
            if self._uses_html:
                info = [self.safe_format('<span class="show_all">{}</span>', path)]
            else:
                info = [f'[{path}]']
        return info, reference

    #
    # API
    #

    @ForPattern(r'/__api/(data)\.json')  # is this correct?
    @ForPattern(r'/__api/(data)\.html')  # is this correct?
    @ForPattern(r'/__api/(images)\.html')
    @ForPattern(r'/__api/(dataimages)\.json')
    @ForPattern(r'/__api/meta/(result_count)\.json')
    def _api_data(self, query: Dict[str, str], match: Match[str]) -> SESSION_INFO:
        return self._query_handler.handle_query(query, match.group(1))

    @ForPattern(r'/__api/image/med/(.*)\.json')
    def _view_metadata(self, query: Dict[str, str], match: Match[str]) -> SESSION_INFO:
        metadata = match.group(1)
        return [f'View Metadata: {metadata}'], self.__create_opus_url(metadata)

    @ForPattern(r'/__api/data\.csv')
    def _download_results_csv(self, query: Dict[str, str], match: Match[str]) -> SESSION_INFO:
        self.performed_download()
        return ["Download CSV of Search Results"], None

    @ForPattern(r'/__api/metadata_v2/(.*)\.csv')
    def _download_metadata_csv(self, query: Dict[str, str], match: Match[str]) -> SESSION_INFO:
        self.performed_download()
        opus_id = match.group(1)
        extra = 'Selected' if query.get('cols') else 'All'
        text = f'Download CSV of {extra} Metadata for OPUSID'
        if self._uses_html:
            return [self.safe_format('{}: {}', text, opus_id)], self.__create_opus_url(opus_id)
        else:
            return [f'{text}: { opus_id }'], None

    @ForPattern(r'/__api/download/(.*)\.zip')
    def _download_archive(self, query: Dict[str, str], match: Match[str]) -> SESSION_INFO:
        self.performed_download()
        opus_id = match.group(1)
        extra = 'URL' if query.get('urlonly') not in (None, "0") else 'Data'
        text = f'Download {extra} Archive for OPUSID'
        if self._uses_html:
            return [self.safe_format('{}: {}', text, opus_id)], self.__create_opus_url(opus_id)
        else:
            return [f'{text}: { opus_id }'], None

    #
    # Collections
    #

    @ForPattern(r'/__collections/view\.json')
    @ForPattern(r'/__cart/view\.json')
    def download_product_types(self, query: Dict[str, str], match: Match[str]) -> SESSION_INFO:
        return ['Download Product Types'], None

    @ForPattern(r'/__collections/view\.html')
    @ForPattern(r'/__cart/view\.html')
    def collections_view_cart(self, query: Dict[str, str], match: Match[str]) -> SESSION_INFO:
        return ['View Cart'], None

    @ForPattern(r'/__collections/data.csv')
    @ForPattern(r'/__cart/data.csv')
    def _download_cart_metadata_csv(self, query: Dict[str, str], match: Match[str]) -> SESSION_INFO:
        self.performed_download()
        return ["Download CSV of Selected Metadata for Cart"], None

    @ForPattern(r'/__collections/download.json')
    @ForPattern(r'/__cart/download.json')
    def _create_archive(self, query: Dict[str, str], match: Match[str]) -> SESSION_INFO:
        self.performed_download()
        has_url = query.get('urlonly') not in [None, '0']
        text = f'Download {"URL" if has_url else "Data"} Archive for Cart'
        return [text], None

    @ForPattern(r'/__collections/status\.json')
    @ForPattern(r'/__cart/status\.json')
    def _download_product_types(self, query: Dict[str, str], match: Match[str]) -> SESSION_INFO:
        if query.get('download') != '1':
            return [], None
        self.performed_download()
        ptypes_field = query.get('types', None)
        new_ptypes = ptypes_field.split(',') if ptypes_field else []
        old_ptypes = self._previous_product_info_type
        self._previous_product_info_type = new_ptypes

        if old_ptypes is None:
            joined_new_ptypes = self.quote_and_join_list(new_ptypes)
            plural = '' if len(new_ptypes) == 1 else 's'
            return [f'Download Product Type{plural}: {joined_new_ptypes}'], None

        result = []

        def show(verb: str, items: List[str]) -> None:
            if items:
                plural = 's' if len(items) > 1 else ''
                joined_items = self.quote_and_join_list(items)
                result.append(f'{verb.title()} Product Type{plural}: {joined_items}')

        show('add', [ptype for ptype in new_ptypes if ptype not in old_ptypes])
        show('remove', [ptype for ptype in old_ptypes if ptype not in new_ptypes])

        if not result:
            result.append('Product Types are unchanged')
        return result, None

    @ForPattern(r'/__collections/reset.html')
    @ForPattern(r'/__cart/reset.html')
    def _reset_cart(self, query: Dict[str, str], match: Match[str]) -> SESSION_INFO:
        return ['Empty Cart'], None

    @ForPattern(r'/__collections/(add|remove)\.json')
    @ForPattern(r'/__cart/(add|remove)\.json')
    def _change_cart(self, query: Dict[str, str], match: Match[str]) -> SESSION_INFO:
        opus_id = query.get('opusid') or query.get('opus_id')  # opusid is new name, opus_id is old
        selection = match.group(1).title()
        if self._uses_html and opus_id:
            return [self.safe_format('Cart {}: {}', selection.title(), opus_id)], self.__create_opus_url(opus_id)
        else:
            return [f'Cart {selection.title() + ":":<7} {opus_id or "???"}'], None

    @ForPattern(r'/__collections/(add|remove)range.json')
    @ForPattern(r'/__cart/(add|remove)range.json')
    def _add_range_to_cart(self, query: Dict[str, str], match: Match[str]) -> SESSION_INFO:
        selection = match.group(1).title()
        query_range = query.get('range', '???').replace(',', ', ')
        return [f'Cart {selection} Range: {query_range}'], None

    @ForPattern(r'/__collections/addall.json')
    @ForPattern(r'/__cart/addall.json')
    def _add_all_to_cart(self, query: Dict[str, str], match: Match[str]) -> SESSION_INFO:
        query_range = query.get('range', '???').replace(',', ', ')
        return [f'Cart Add All'], None

    #
    # FORMS
    #

    @ForPattern(r'/__forms/column_chooser\.html')
    def _column_chooser(self, query: Dict[str, str], match: Match[str]) -> SESSION_INFO:
        return ['Metadata Selector'], None

    #
    # INIT DETAIL
    #

    @ForPattern(r'/__initdetail/(.*)\.html')
    def _initialize_detail(self, query: Dict[str, str], match: Match[str]) -> SESSION_INFO:
        opus_id = match.group(1)
        if self._uses_html:
            return [self.safe_format('View Detail: {}', opus_id)], self.__create_opus_url(opus_id)
        else:
            return [f'View Detail: { opus_id }'], None

    #
    # HELP
    #

    @ForPattern(r'/__help/(\w+)\.html')
    def _get_help_information(self, query: Dict[str, str], match: Match[str]) -> SESSION_INFO:
        help_type = match.group(1)
        help_name = help_type.upper() if help_type == 'faq' else help_type.title()
        return [f'Read {help_name}'], None

    #
    # Various utilities
    #

    def __create_opus_url(self, opus_id: str) -> str:
        return self.safe_format('/opus/#/view=detail&amp;detail={0}', opus_id)
