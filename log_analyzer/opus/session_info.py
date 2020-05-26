import re
import urllib.parse
from typing import Dict, Set, Tuple, List, Optional, Sequence, Match

from abstract_configuration import AbstractSessionInfo, PatternRegistry, SESSION_INFO
from log_entry import LogEntry
from opus import slug
from .configuration_flags import IconFlags, InfoFlags
from .query_handler import QueryHandler, MetadataSlugInfo
from .slug import Info, FamilyType


class SessionInfo(AbstractSessionInfo):
    """
    A class that keeps track of information about the current user session and parses log entries based on information
    that it already knows about this session.

    This is an abstract class.  The user should only get instances of this class from the Configuration.
    """
    _session_search_slugs: Dict[str, slug.Info]
    _session_metadata_slugs: Dict[str, slug.Info]
    _session_sort_slugs_list: Set[Tuple[slug.Info, ...]]
    _help_files: Set[str]
    _downloads: List[Tuple[str, int]]
    _product_types: List[str]
    _product_types_count: int
    _widgets: Set[slug.Family]
    _icon_flags: IconFlags
    _info_flags: InfoFlags
    _previous_product_info_type: Optional[List[str]]
    _query_handler: QueryHandler
    _show_all: bool
    _sessionless_downloads: List[Tuple[str, LogEntry]]

    pattern_registry = PatternRegistry()

    def __init__(self, slug_map: slug.ToInfoMap, default_column_slug_info: MetadataSlugInfo,
                 show_all: bool, uses_html: bool, sessionless_downloads: List[Tuple[str, LogEntry]]):
        self._session_search_slugs = dict()
        self._session_metadata_slugs = dict()
        self._session_sort_slugs_list = set()
        self._help_files = set()
        self._downloads = []
        self._product_types = []
        self._product_types_count = 0
        self._widgets = set()
        self._icon_flags = IconFlags(0)
        self._info_flags = InfoFlags(InfoFlags.DID_NOT_PERFORM_SEARCH)
        self._query_handler = QueryHandler(self, slug_map, default_column_slug_info, uses_html)
        self._uses_html = uses_html
        self._show_all = show_all
        self._sessionless_downloads = sessionless_downloads

        # The previous value of types when downloading a collection
        self._previous_product_info_type = None

        # Debugging information.  Maybe delete me

    def add_search_slug(self, slug_name: str, slug_info: slug.Info) -> None:
        self._session_search_slugs[slug_name] = slug_info
        if slug_info.flags.is_obsolete():
            self._icon_flags |= IconFlags.HAS_OBSOLETE_SLUG
            self._info_flags |= InfoFlags.HAS_OBSOLETE_SLUG

    def add_metadata_slug(self, slug: str, slug_info: slug.Info) -> None:
        self._session_metadata_slugs[slug] = slug_info
        if slug_info.flags.is_obsolete():
            self._icon_flags |= IconFlags.HAS_OBSOLETE_SLUG
            self._info_flags |= InfoFlags.HAS_OBSOLETE_SLUG

    def add_sort_slugs_list(self, slugs_list: Sequence[slug.Info]) -> None:
        self._session_sort_slugs_list.add(tuple(slugs_list))

    def changed_search_slugs(self) -> None:
        self._icon_flags |= IconFlags.HAS_SEARCH
        self._info_flags |= InfoFlags.PERFORMED_SEARCH
        self._info_flags &= ~InfoFlags.DID_NOT_PERFORM_SEARCH

    def changed_metadata_slugs(self) -> None:
        self._icon_flags |= IconFlags.HAS_METADATA
        self._info_flags |= InfoFlags.CHANGED_SELECTED_METADATA

    def performed_download(self) -> None:
        self._icon_flags |= IconFlags.HAS_DOWNLOAD

    def fetched_gallery(self) -> None:
        self._icon_flags |= IconFlags.FETCHED_GALLERY

    def update_info_flags(self, flags: InfoFlags) -> None:
        self._info_flags |= flags

    def register_download(self, filename: str, size: Optional[int]) -> None:
        self._downloads.append((filename, size or 0))

    def register_product_types(self, product_types: Sequence[str]) -> None:
        self._product_types.extend(product_types)
        self._product_types_count += 1

    def register_sessionless_download(self, path: str, entry: LogEntry) -> None:
        match = re.fullmatch(r"/downloads/([^/]+)", path)
        if match:
            self._sessionless_downloads.append((match.group(1), entry))

    def register_widget(self, family: slug.Family) -> None:
        self._widgets.add(family)

    def get_slug_info(self) -> Sequence[List[Tuple[str, bool]]]:
        def fixit(info: Dict[str, Info]) -> List[Tuple[str, bool]]:
            return [(slug, info[slug].flags.is_obsolete())
                    for slug in sorted(info, key=str.lower)
                    # Rob doesn't want to see slugs that start with 'qtype-' in the list.
                    if not slug.startswith('qtype-')
                    if not slug.startswith('unit-')]

        # Make a copy of session_search_slugs, and change any subgroup slugs to the base value.  If we overwrite
        # an existing value, that's fine.
        session_search_slugs = self._session_search_slugs.copy()
        for slug in self._session_search_slugs.keys():
            match = re.fullmatch(r'(.*)_\d{2,}', slug)
            if match:
                session_search_slugs[match.group(1)] = session_search_slugs.pop(slug)

        search_slug_list = fixit(session_search_slugs)
        column_slug_list = fixit(self._session_metadata_slugs)
        return search_slug_list, column_slug_list

    def get_search_names(self) -> List[str]:
        return list({value.family.label for value in self._session_search_slugs.values()
                     if value.family_type != FamilyType.QTYPE
                     if value.family_type != FamilyType.UNIT})

    def get_metadata_names(self) -> List[str]:
        return list({value.family.label for value in self._session_metadata_slugs.values()})

    def get_sort_list_names(self) -> List[Tuple[str, ...]]:
        return [tuple(value.family.label for value in sort_list)
                for sort_list in self._session_sort_slugs_list]

    def get_icon_flags(self) -> IconFlags:
        return self._icon_flags

    def get_info_flags(self) -> InfoFlags:
        return self._info_flags

    def get_help_files(self) -> Set[str]:
        return self._help_files

    def get_product_types(self) -> List[str]:
        return self._product_types

    def get_product_types_count(self) -> int:
        return self._product_types_count

    def get_downloads(self) -> List[Tuple[str, int]]:
        return self._downloads

    def get_unmatched_widgets(self) -> Set[slug.Family]:
        widgets = self._widgets
        used = {x.family for x in self._session_search_slugs.values()}
        return widgets - used

    def parse_log_entry(self, entry: LogEntry) -> SESSION_INFO:
        """Parses a log record within the context of the current session."""
        # We ignore all sorts of log entries.
        if entry.method != 'GET' or entry.status != 200:
            return [], None
        if entry.agent and ("bot" in entry.agent.lower() or "spider" in entry.agent.lower()):
            return [], None

        path = entry.url.path

        if path.startswith('/opus/__'):
            pass
        elif path.startswith('/downloads/'):
            self.register_sessionless_download(path, entry)
            return [], None
        else:
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
            info, reference = method(self, entry, query, match)
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

    @pattern_registry.register(r'/__api/(data)\.html')
    @pattern_registry.register(r'/__api/(images)\.html')
    @pattern_registry.register(r'/__api/(dataimages)\.json')
    @pattern_registry.register(r'/__api/meta/(result_count)\.json')
    def __api_data(self, log_entry: LogEntry, query: Dict[str, str], match: Match[str]) -> SESSION_INFO:
        return self._query_handler.handle_query(log_entry, query, match.group(1))

    @pattern_registry.register(r'/__api/data\.json')
    def __api_data_old(self, log_entry: LogEntry, query: Dict[str, str], _match: Match[str]) -> SESSION_INFO:
        # data.json was the old name for dataimages.json.  Treat it like dataimages, rather than like data.html.
        return self._query_handler.handle_query(log_entry, query, "dataimages")

    #
    # CREATE WIDGET
    #

    @pattern_registry.register(r'/__widget/(.*).html')
    @pattern_registry.register(r'/__forms/widget/(.*).html')
    def __initialize_widget(self, log_entry: LogEntry, query: Dict[str, str], match: Match[str]) -> SESSION_INFO:
        return self._query_handler.create_widget(log_entry, query, match.group(1))

    @pattern_registry.register(r'/__api/image/med/(.*)\.json')
    @pattern_registry.register(r'/__viewmetadatamodal/(.*)\.json')
    def __view_metadata(self,  _log_entry: LogEntry, _query: Dict[str, str], match: Match[str]) -> SESSION_INFO:
        self.update_info_flags(InfoFlags.VIEWED_SLIDE_SHOW)
        metadata = match.group(1)
        return [f'View Metadata: {metadata}'], self.__create_opus_url(metadata)

    @pattern_registry.register(r'/__api/data\.csv')
    def __download_results_csv(self, _log_entry: LogEntry, _query: Dict[str, str], _match: Match[str]) -> SESSION_INFO:
        self.performed_download()
        self.update_info_flags(InfoFlags.DOWNLOADED_CSV_FILE_FOR_ALL_RESULTS)
        return ["Download CSV of Search Results"], None

    @pattern_registry.register(r'/__api/metadata_v2/(.*)\.csv')
    def __download_metadata_csv(self, log_entry: LogEntry, query: Dict[str, str], match: Match[str]) -> SESSION_INFO:
        self.performed_download()
        self.update_info_flags(InfoFlags.DOWNLOADED_CSV_FILE_FOR_ONE_OBSERVATION)
        opus_id = match.group(1)
        self.register_download(opus_id + '.csv', log_entry.size)
        extra = 'Selected' if query.get('cols') else 'All'
        text = f'Download CSV of {extra} Metadata for OPUSID'
        if self._uses_html:
            return [self.safe_format('{}: {}', text, opus_id)], self.__create_opus_url(opus_id)
        else:
            return [f'{text}: { opus_id }'], None

    @pattern_registry.register(r'/__api/download/(.*)\.zip')
    def __download_archive(self, log_entry: LogEntry, query: Dict[str, str], match: Match[str]) -> SESSION_INFO:
        self.performed_download()
        opus_id = match.group(1)
        self.register_download(opus_id + '.zip', log_entry.size)
        url_only = query.get('urlonly') not in (None, "0")
        text = f'Download {"URL" if url_only else "Data"} Archive for OPUSID'
        self.update_info_flags(InfoFlags.DOWNLOADED_ZIP_URL_FILE_FOR_ONE_OBSERVATION if url_only else
                               InfoFlags.DOWNLOADED_ZIP_FILE_FOR_ONE_OBSERVATION)
        if self._uses_html:
            return [self.safe_format('{}: {}', text, opus_id)], self.__create_opus_url(opus_id)
        else:
            return [f'{text}: { opus_id }'], None

    #
    # Collections
    #

    @pattern_registry.register(r'/__collections/view\.html')
    @pattern_registry.register(r'/__cart/view\.html')
    def __collections_view_cart(self, _log_entry: LogEntry, _query: Dict[str, str], _match: Match[str]) -> SESSION_INFO:
        return ['View Cart'], None

    @pattern_registry.register(r'/__collections/data\.csv')
    @pattern_registry.register(r'/__cart/data\.csv')
    def __download_cart_metadata_csv(self, _: LogEntry, _query: Dict[str, str], _match: Match[str]) -> SESSION_INFO:
        self.performed_download()
        self.update_info_flags(InfoFlags.DOWNLOADED_CSV_FILE_FOR_CART)
        return ["Download CSV of Selected Metadata for Cart"], None

    @pattern_registry.register(r'/__collections/download\.(json|zip)')
    @pattern_registry.register(r'/__collections/download/default\.zip')
    @pattern_registry.register(r'/__cart/download\.json')
    def __create_archive(self, _log_entry: LogEntry, query: Dict[str, str], _match: Match[str]) -> SESSION_INFO:
        self.performed_download()
        url_only = query.get('urlonly') not in [None, '0']
        self.update_info_flags(InfoFlags.DOWNLOADED_ZIP_URL_FILE_FOR_CART if url_only else
                               InfoFlags.DOWNLOADED_ZIP_ARCHIVE_FILE_FOR_CART)
        ptypes_field = query.get('types', None)
        ptypes = ptypes_field.split(',') if ptypes_field else []
        self.register_product_types(ptypes)
        joined_ptypes = self.quote_and_join_list(sorted(ptypes))
        text = f'Download {"URL" if url_only else "Data"} Archive for Cart: {joined_ptypes}'
        return [text], None

    # Note that the __collections/ and the __cart/ are different.
    @pattern_registry.register(r'/__collections/(view)\.json')
    @pattern_registry.register(r'/__collections/default/(view)\.json')
    @pattern_registry.register(r'/__cart/(status)\.json')
    def __download_product_types(self, _log_entry: LogEntry, query: Dict[str, str], match: Match[str]) -> SESSION_INFO:
        if match.group(1) == 'status' and query.get('download') != '1':
            # The __cart/status version requires &download=1
            return [], None
        self.performed_download()
        ptypes_field = query.get('types', None)
        new_ptypes = ptypes_field.split(',') if ptypes_field else []
        self.register_product_types(new_ptypes)
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
    def __reset_cart(self, _log_entry: LogEntry, _query: Dict[str, str], _match: Match[str]) -> SESSION_INFO:
        return ['Empty Cart'], None

    @pattern_registry.register(r'/__collections/(add|remove)\.json')
    @pattern_registry.register(r'/__collections/default/(add|remove)\.json')
    @pattern_registry.register(r'/__cart/(add|remove)\.json')
    def __add_remove_cart(self, _log_entry: LogEntry, query: Dict[str, str], match: Match[str]) -> SESSION_INFO:
        opus_id = query.get('opusid') or query.get('opus_id')  # opusid is new name, opus_id is old
        selection = match.group(1).title()
        if self._uses_html and opus_id:
            return [self.safe_format('Cart {}: {}', selection.title(), opus_id)], self.__create_opus_url(opus_id)
        else:
            return [f'Cart {selection.title() + ":":<7} {opus_id or "???"}'], None

    @pattern_registry.register(r'/__collections/(add|remove)range\.json')
    @pattern_registry.register(r'/__collections/default/(add|remove)range\.json')
    @pattern_registry.register(r'/__cart/(add|remove)range\.json')
    def __add_remove_range_to_cart(self, _log: LogEntry, query: Dict[str, str], match: Match[str]) -> SESSION_INFO:
        selection = match.group(1).title()
        query_range = query.get('range', '???').replace(',', ', ')
        return [f'Cart {selection} Range: {query_range}'], None

    @pattern_registry.register(r'/__collections/addall\.json')
    @pattern_registry.register(r'/__collections/default/addall\.json')
    @pattern_registry.register(r'/__cart/addall\.json')
    def __add_all_to_cart(self, _log_entry: LogEntry, query: Dict[str, str], _match: Match[str]) -> SESSION_INFO:
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
    def __column_chooser(self, _log_entry: LogEntry, _query: Dict[str, str], _match: Match[str]) -> SESSION_INFO:
        self.update_info_flags(InfoFlags.VIEWED_SELECT_METADATA)
        return ['Metadata Selector'], None

    #
    # INIT DETAIL
    #

    @pattern_registry.register(r'/__initdetail/(.*)\.html')
    def __initialize_detail(self, _log_entry: LogEntry, _query: Dict[str, str], match: Match[str]) -> SESSION_INFO:
        self.update_info_flags(InfoFlags.VIEWED_DETAIL_TAB)
        opus_id = match.group(1)
        if self._uses_html:
            return [self.safe_format('View Detail: {}', opus_id)], self.__create_opus_url(opus_id)
        else:
            return [f'View Detail: { opus_id }'], None

    #
    # HELP
    #

    @pattern_registry.register(r'/__help/(\w+)\.(html|pdf)')
    def __read_help_information(self, _log_entry: LogEntry, _query: Dict[str, str], match: Match[str]) -> SESSION_INFO:
        help_type, file_type = match.group(1, 2)
        help_name = help_type.upper() if help_type == 'faq' else help_type
        if help_name != 'splash':
            flag = InfoFlags.VIEWED_HELP_FILE if file_type == 'html' else InfoFlags.VIEWED_HELP_FILE_AS_PDF
            self.update_info_flags(flag)
        self._help_files.add(help_name + '.' + file_type)
        if self._uses_html:
            return [self.safe_format('Help <samp>{}</samp>', help_name)], None
        else:
            return [f'Help {help_name}'], None

    #
    # Various utilities
    #

    def __create_opus_url(self, opus_id: str) -> str:
        return self.safe_format('/opus/#/view=detail&amp;detail={0}', opus_id)
