import collections
import textwrap
import urllib.parse
from enum import auto, Flag
from typing import List, Dict, Optional, Match, Any, Iterable, Tuple, TextIO, cast

from abstract_configuration import SESSION_INFO, AbstractSessionInfo, AbstractConfiguration, PatternRegistry
from log_entry import LogEntry
from log_parser import Session
from opus import slug
from opus.query_handler import QueryHandler, ColumnSlugInfo
from opus.slug import Info


class ActionFlags(Flag):
    # These should be in the order we want to see them in the output
    HAS_SEARCH = auto()
    FETCHED_GALLERY = auto()
    HAS_COLUMNS = auto()
    HAS_DOWNLOAD = auto()
    HAS_OBSOLETE_SLUG = auto()


class Configuration(AbstractConfiguration):
    """
    A generator class for creating a SessionInfo.
    """
    _slug_map: slug.ToInfoMap
    _default_column_slug_info: ColumnSlugInfo
    _api_host_url: str
    _debug_show_all: bool

    DEFAULT_COLUMN_INFO = 'opusid,instrument,planet,target,time1,observationduration'.split(',')

    def __init__(self, *, api_host_url: str, debug_show_all: bool, **_: Any):
        self._slug_map = slug.ToInfoMap(api_host_url)
        self._default_column_slug_info = QueryHandler.get_column_slug_info(self.DEFAULT_COLUMN_INFO, self._slug_map)
        self._api_host_url = api_host_url
        self._debug_show_all = debug_show_all

    def create_session_info(self, uses_html: bool = False) -> 'SessionInfo':
        """Create a new SessionInfo"""
        return SessionInfo(self._slug_map, self._default_column_slug_info, self._debug_show_all, uses_html)

    def additional_template_info(self) -> Dict[str, Any]:
        # noinspection PyTypeChecker
        action_flag_list = list(ActionFlags)
        return {
            'api_host_url': self._api_host_url,
            'action_flags_list': action_flag_list,
        }

    def show_summary(self, sessions: List[Session], output: TextIO) -> None:
        all_info: Dict[str, Dict[str, bool]] = collections.defaultdict(dict)
        for session in sessions:
            session_info = cast(SessionInfo, session.session_info)
            for info_type, slug_and_flags in session_info.get_slug_info():
                for slug, is_obsolete in slug_and_flags:
                    all_info[info_type][slug] = is_obsolete

        def show_info(info_type: str) -> None:
            result = ', '.join(
                # Use ~ as a non-breaking space for textwrap.  We replace it with a space, below
                (slug + '~[OBSOLETE]') if all_info[slug] else slug
                for slug in sorted(all_info[info_type], key=str.lower))
            wrapped = textwrap.fill(result, 100,
                                    initial_indent=f'{info_type.title()} slugs: ', subsequent_indent='    ')
            print(wrapped.replace('~', ' '), file=output)

        show_info('search')
        print('', file=output)
        show_info('column')


class SessionInfo(AbstractSessionInfo):
    """
    A class that keeps track of information about the current user session and parses log entries based on information
    that it already knows about this session.

    This is an abstract class.  The user should only get instances of this class from the Configuration.
    """
    _session_search_slugs: Dict[str, slug.Info]
    _session_column_slugs: Dict[str, slug.Info]
    _action_flags: ActionFlags
    _previous_product_info_type: Optional[List[str]]
    _query_handler: QueryHandler
    _show_all: bool

    pattern_registry = PatternRegistry()

    def __init__(self, slug_map: slug.ToInfoMap, default_column_slug_info: ColumnSlugInfo,
                 show_all: bool, uses_html: bool):
        self._session_search_slugs = dict()
        self._session_column_slugs = dict()
        self._action_flags = ActionFlags(0)
        self._query_handler = QueryHandler(self, slug_map, default_column_slug_info, uses_html)
        self._uses_html = uses_html
        self._show_all = show_all

        # The previous value of types when downloading a collection
        self._previous_product_info_type = None

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

    def get_slug_info(self) -> Iterable[Tuple[str, List[Tuple[str, bool]]]]:
        def fixit(info: Dict[str, Info]) -> List[Tuple[str, bool]]:
            return [(slug, info[slug].flags.is_obsolete())
                    for slug in sorted(info, key=str.lower)
                    # Rob doesn't want to see slugs that start with 'qtype-' in the list.
                    if not slug.startswith('qtype-')]

        search_slug_list = fixit(self._session_search_slugs)
        column_slug_list = fixit(self._session_column_slugs)
        return ('search', search_slug_list), ('column', column_slug_list)

    def get_session_flags(self) -> ActionFlags:
        return self._action_flags

    def parse_log_entry(self, entry: LogEntry) -> SESSION_INFO:
        """Parses a log record within the context of the current session."""

        # We ignore all sorts of log entries.
        if entry.method != 'GET' or entry.status != 200:
            return [], None
        if entry.agent and ("bot" in entry.agent.lower() or "spider" in entry.agent.lower()):
            return [], None
        path = entry.url.path
        if not path.startswith('/opus/__'):
            return [], None

        raw_query = urllib.parse.parse_qs(entry.url.query)
        # raw_query will match a key to a list of values for that key.  Opus only uses each key once
        # (values are separated by commas), so we convert the raw query to a more useful form.
        query = {key: value[0]
                 for key, value in raw_query.items()
                 if isinstance(value, list) and len(value) == 1}
        # ignorelog is a marker to ignore this entry
        if 'ignorelog' in query:
            return [], None

        # See if the path matches one of our patterns.
        path = path[5:]  # remove '/opus'
        if path.startswith('/__fake/__'):
            path = path[7:]  # remove '/__fake
        method_and_match = self.pattern_registry.find_matching_pattern(path)
        if method_and_match:
            method, match = method_and_match
            info, reference = method(self, query, match)
        else:
            info, reference = [], None
        if self._show_all and not info:
            if self._uses_html:
                info = [self.safe_format('<span class="show_all">{}</span>', path)]
            else:
                info = [f'[{path}]']
        return info, reference

    #
    # API
    #

    @pattern_registry.register(r'/__api/(data)\.json')
    @pattern_registry.register(r'/__api/(data)\.html')
    @pattern_registry.register(r'/__api/(images)\.html')
    @pattern_registry.register(r'/__api/(dataimages)\.json')
    @pattern_registry.register(r'/__api/meta/(result_count)\.json')
    def __api_data(self, query: Dict[str, str], match: Match[str]) -> SESSION_INFO:
        return self._query_handler.handle_query(query, match.group(1))

    @pattern_registry.register(r'/__api/image/med/(.*)\.json')
    @pattern_registry.register(r'/__viewmetadatamodal/(.*)\.json')
    def __view_metadata(self, _: Dict[str, str], match: Match[str]) -> SESSION_INFO:
        metadata = match.group(1)
        return [f'View Metadata: {metadata}'], self.__create_opus_url(metadata)

    @pattern_registry.register(r'/__api/data\.csv')
    def __download_results_csv(self, _query: Dict[str, str], _match: Match[str]) -> SESSION_INFO:
        self.performed_download()
        return ["Download CSV of Search Results"], None

    @pattern_registry.register(r'/__api/metadata_v2/(.*)\.csv')
    def __download_metadata_csv(self, query: Dict[str, str], match: Match[str]) -> SESSION_INFO:
        self.performed_download()
        opus_id = match.group(1)
        extra = 'Selected' if query.get('cols') else 'All'
        text = f'Download CSV of {extra} Metadata for OPUSID'
        if self._uses_html:
            return [self.safe_format('{}: {}', text, opus_id)], self.__create_opus_url(opus_id)
        else:
            return [f'{text}: { opus_id }'], None

    @pattern_registry.register(r'/__api/download/(.*)\.zip')
    def __download_archive(self, query: Dict[str, str], match: Match[str]) -> SESSION_INFO:
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

    @pattern_registry.register(r'/__collections/view\.html')
    @pattern_registry.register(r'/__cart/view\.html')
    def __collections_view_cart(self, _query: Dict[str, str], _match: Match[str]) -> SESSION_INFO:
        return ['View Cart'], None

    @pattern_registry.register(r'/__collections/data\.csv')
    @pattern_registry.register(r'/__cart/data\.csv')
    def __download_cart_metadata_csv(self, _query: Dict[str, str], _match: Match[str]) -> SESSION_INFO:
        self.performed_download()
        return ["Download CSV of Selected Metadata for Cart"], None

    @pattern_registry.register(r'/__collections/download\.(json|zip)')
    @pattern_registry.register(r'/__collections/download/default\.zip')
    @pattern_registry.register(r'/__cart/download\.json')
    def __create_archive(self, query: Dict[str, str], _match: Match[str]) -> SESSION_INFO:
        self.performed_download()
        has_url = query.get('urlonly') not in [None, '0']
        ptypes_field = query.get('types', None)
        ptypes = ptypes_field.split(',') if ptypes_field else []
        joined_ptypes = self.quote_and_join_list(sorted(ptypes))
        text = f'Download {"URL" if has_url else "Data"} Archive for Cart: {joined_ptypes}'
        return [text], None

    # Note that the __collections/ and the __cart/ are different.
    @pattern_registry.register(r'/__collections/(view)\.json')
    @pattern_registry.register(r'/__collections/default/(view)\.json')
    @pattern_registry.register(r'/__cart/(status)\.json')
    def __download_product_types(self, query: Dict[str, str], match: Match[str]) -> SESSION_INFO:
        if match.group(1) == 'status' and query.get('download') != '1':
            # The __cart/status version requires &download=1
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

    @pattern_registry.register(r'/__collections/reset\.(html|json)')
    @pattern_registry.register(r'/__collections/default/reset\.(html|json)')
    @pattern_registry.register(r'/__cart/reset\.(html|json)')
    def __reset_cart(self, _query: Dict[str, str], _match: Match[str]) -> SESSION_INFO:
        return ['Empty Cart'], None

    @pattern_registry.register(r'/__collections/(add|remove)\.json')
    @pattern_registry.register(r'/__collections/default/(add|remove)\.json')
    @pattern_registry.register(r'/__cart/(add|remove)\.json')
    def __add_remove_cart(self, query: Dict[str, str], match: Match[str]) -> SESSION_INFO:
        opus_id = query.get('opusid') or query.get('opus_id')  # opusid is new name, opus_id is old
        selection = match.group(1).title()
        if self._uses_html and opus_id:
            return [self.safe_format('Cart {}: {}', selection.title(), opus_id)], self.__create_opus_url(opus_id)
        else:
            return [f'Cart {selection.title() + ":":<7} {opus_id or "???"}'], None

    @pattern_registry.register(r'/__collections/(add|remove)range\.json')
    @pattern_registry.register(r'/__collections/default/(add|remove)range\.json')
    @pattern_registry.register(r'/__cart/(add|remove)range\.json')
    def __add_remove_range_to_cart(self, query: Dict[str, str], match: Match[str]) -> SESSION_INFO:
        selection = match.group(1).title()
        query_range = query.get('range', '???').replace(',', ', ')
        return [f'Cart {selection} Range: {query_range}'], None

    @pattern_registry.register(r'/__collections/addall\.json')
    @pattern_registry.register(r'/__collections/default/addall\.json')
    @pattern_registry.register(r'/__cart/addall\.json')
    def __add_all_to_cart(self, query: Dict[str, str], _match: Match[str]) -> SESSION_INFO:
        query_range = query.get('range', None)
        if query_range:
            query_range = query_range.replace(',', ', ')
            return [f'Cart Add {query_range}'], None
        else:
            return [f'Cart Add All'], None

    #
    # FORMS
    #

    @pattern_registry.register(r'/__forms/column_chooser\.html')
    @pattern_registry.register(r'/__selectmetadatamodal\.json')
    def __column_chooser(self, _query: Dict[str, str], _match: Match[str]) -> SESSION_INFO:
        return ['Metadata Selector'], None

    #
    # INIT DETAIL
    #

    @pattern_registry.register(r'/__initdetail/(.*)\.html')
    def __initialize_detail(self, _query: Dict[str, str], match: Match[str]) -> SESSION_INFO:
        opus_id = match.group(1)
        if self._uses_html:
            return [self.safe_format('View Detail: {}', opus_id)], self.__create_opus_url(opus_id)
        else:
            return [f'View Detail: { opus_id }'], None

    #
    # HELP
    #

    @pattern_registry.register(r'/__help/(\w+)\.html')
    def __read_help_information(self, _query: Dict[str, str], match: Match[str]) -> SESSION_INFO:
        help_type = match.group(1)
        help_name = help_type.upper() if help_type == 'faq' else help_type.title()
        return [f'Help {help_name}'], None

    #
    # Various utilities
    #

    def __create_opus_url(self, opus_id: str) -> str:
        return self.safe_format('/opus/#/view=detail&amp;detail={0}', opus_id)
