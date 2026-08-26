"""Turning OPUS log entries into the lines of a session's report.

The generic log parser groups Apache log entries into sessions and hands each entry
of a session to `SessionInfo.parse_log_entry`. This module recognizes the OPUS URLs
among them -- searches, metadata selection, cart edits, downloads, help pages -- and
returns the report lines for that entry together with an OPUS URL the report can link
the entry to. Along the way it accumulates the per-session tallies the report's
statistics are built from.

A request is dispatched by matching its path against `SessionInfo.pattern_registry`.
The query-string bookkeeping for searches, metadata columns and sort order is
delegated to `QueryHandler`.

Usage is tallied against log markers. A marker is either the id of a log entry or a
(log entry id, line number) pair naming one of the report lines that entry produced,
so a tally can point at either a whole request or a single line of it.
"""
import collections
import re
import urllib.parse
from collections.abc import Iterable, Iterator, Mapping, Sequence
from re import Match

from opus_log_analyzer.abstract_configuration import (
    SESSION_INFO,
    AbstractSessionInfo,
    LogId,
    PatternRegistry,
)
from opus_log_analyzer.log_entry import LogEntry
from opus_log_analyzer.opus import slug
from opus_log_analyzer.opus.configuration_flags import Action, IconFlags
from opus_log_analyzer.opus.query_handler import MetadataSlugInfo, QueryHandler
from opus_log_analyzer.opus.slug import Info

LogMarker = LogId | tuple[LogId, int]


class SessionInfo(AbstractSessionInfo):
    """
    A class that keeps track of information about the current user session and parses log entries based on information
    that it already knows about this session.

    The class is concrete: it declares no abstract methods, and
    `Configuration.create_session_info` instantiates it. Obtain instances from
    the Configuration rather than constructing them directly.
    """
    _session_search_slugs: dict[str, slug.Info]
    _session_metadata_slugs: dict[str, slug.Info]
    _icon_flags: IconFlags
    _previous_product_info_type: set[str] | None
    _query_handler: QueryHandler
    _show_all: bool
    _current_id: LogId

    _search_slugs_usage: dict[str, set[LogMarker]]
    _metadata_slugs_usage: dict[str, set[LogMarker]]
    _session_sort_slugs_usage: dict[tuple[slug.Info, ...], set[LogMarker]]
    _help_files_usage: dict[str, set[LogMarker]]
    _product_types_usage: dict[str, set[LogMarker]]
    _product_types_count: int
    _widgets_usage: dict[str, set[LogMarker]]
    _info_flags_usage: dict[Action, set[LogMarker]]
    _sessioned_downloads_usage: dict[str, tuple[list[int], set[LogMarker]]]
    _sessionless_downloads_usage: list[tuple[str, LogEntry]]

    pattern_registry = PatternRegistry()

    def __init__(self, slug_map: slug.ToInfoMap, default_column_slug_info: MetadataSlugInfo,
                 show_all: bool, uses_html: bool, sessionless_downloads: list[tuple[str, LogEntry]]):
        """Create the state for one user session.

        Parameters:
            slug_map: The slug database used to interpret search and metadata slug
                names.
            default_column_slug_info: The metadata columns a query is taken to use when
                it names none of its own.
            show_all: When true, a log entry whose URL produced no report line still
                produces one naming the path.
            uses_html: When true, report lines are HTML and carry links; when false they
                are plain text.
            sessionless_downloads: The list, shared with the configuration and with the
                other sessions it creates, that `register_sessionless_download` appends
                to.
        """
        self._session_search_slugs = {}
        self._session_metadata_slugs = {}
        self._session_sort_slugs_usage = collections.defaultdict(set)
        self._help_files_usage = collections.defaultdict(set)
        self._sessioned_downloads_usage = collections.defaultdict(lambda: ([0], set()))
        self._sessionless_downloads_usage = sessionless_downloads
        self._product_types_usage = collections.defaultdict(set)
        self._product_types_count = 0
        self._widgets_usage = collections.defaultdict(set)
        self._icon_flags = IconFlags(0)
        self._info_flags_usage = collections.defaultdict(set)
        self._search_slugs_usage = collections.defaultdict(set)
        self._metadata_slugs_usage = collections.defaultdict(set)

        self._query_handler = QueryHandler(self, slug_map, default_column_slug_info, uses_html)
        self._uses_html = uses_html
        self._show_all = show_all

        # The previous value of types when downloading a collection
        self._previous_product_info_type = None
        self._current_id = LogId(-1)

        # Debugging information.  Maybe delete me

    def add_search_slug(self, slug_name: str, slug_info: slug.Info) -> None:
        """Note that a search slug appeared in this session's queries.

        The slug is remembered under its own name, so a later use of the same name
        replaces the earlier one. `get_slug_info` reports what was remembered here. A
        slug whose info is marked obsolete also raises the session's obsolete-slug icon
        and registers `Action.HAS_OBSOLETE_SLUG`.

        Parameters:
            slug_name: The slug as it appeared as a query-string key.
            slug_info: What the slug map knows about it.
        """
        self._session_search_slugs[slug_name] = slug_info
        if slug_info.flags.is_obsolete():
            self._icon_flags |= IconFlags.HAS_OBSOLETE_SLUG
            self.register_info_flags(Action.HAS_OBSOLETE_SLUG)

    def add_metadata_slug(self, slug: str, slug_info: slug.Info) -> None:
        """Note that a metadata slug appeared among a query's selected columns.

        The slug is remembered under its own name, so a later use of the same name
        replaces the earlier one. `get_slug_info` reports what was remembered here. A
        slug whose info is marked obsolete also raises the session's obsolete-slug icon
        and registers `Action.HAS_OBSOLETE_SLUG`.

        Parameters:
            slug: The slug as it appeared in the query's list of columns.
            slug_info: What the slug map knows about it.
        """
        self._session_metadata_slugs[slug] = slug_info
        if slug_info.flags.is_obsolete():
            self._icon_flags |= IconFlags.HAS_OBSOLETE_SLUG
            self.register_info_flags(Action.HAS_OBSOLETE_SLUG)

    def changed_search_slugs(self, *, line_number: int) -> None:
        """Note that a report line describes a change to the session's search.

        Raises the session's search icon and registers `Action.PERFORMED_SEARCH` against
        the named line.

        Parameters:
            line_number: The index of the line, among the report lines the log entry
                being parsed produces.
        """
        self._icon_flags |= IconFlags.HAS_SEARCH
        self.register_info_flags(Action.PERFORMED_SEARCH, line_number=line_number)

    def changed_metadata_slugs(self, *, line_number: int) -> None:
        """Note that a report line describes a change to the selected metadata.

        Raises the session's metadata icon and registers
        `Action.CHANGED_SELECTED_METADATA` against the named line.

        Parameters:
            line_number: The index of the line, among the report lines the log entry
                being parsed produces.
        """
        self._icon_flags |= IconFlags.HAS_METADATA
        self.register_info_flags(Action.CHANGED_SELECTED_METADATA, line_number=line_number)

    def performed_download(self) -> None:
        """Raise the session's download icon."""
        self._icon_flags |= IconFlags.HAS_DOWNLOAD

    def fetched_gallery(self) -> None:
        """Raise the session's gallery icon."""
        self._icon_flags |= IconFlags.FETCHED_GALLERY

    def get_slug_info(self) -> Sequence[list[tuple[str, bool]]]:
        """The search slugs and the metadata slugs this session used.

        A search slug whose name ends in an underscore followed by two or more digits is
        reported under the name with that suffix removed, which can collapse several
        such slugs onto one reported name.

        Returns:
            A pair of lists, the search slugs first and the metadata slugs second. Each
            list holds (slug name, is obsolete) pairs sorted case-insensitively by name,
            leaving out names that start with `qtype-` or `unit-`.
        """
        def fixit(info: dict[str, Info]) -> list[tuple[str, bool]]:
            """The reported (name, is obsolete) pairs for one map of slug name to info.

            The pairs are sorted case-insensitively by name, and names starting with
            `qtype-` or `unit-` are left out.
            """
            return [(slug, info[slug].flags.is_obsolete())
                    for slug in sorted(info, key=str.lower)
                    # Rob doesn't want to see slugs that start with 'qtype-' in the list.
                    if not slug.startswith('qtype-')
                    if not slug.startswith('unit-')]

        # Make a copy of session_search_slugs, and change any subgroup slugs to the base value.  If we overwrite
        # an existing value, that's fine.
        session_search_slugs = self._session_search_slugs.copy()
        for slug_name in self._session_search_slugs:
            match = re.fullmatch(r'(.*)_\d{2,}', slug_name)
            if match:
                session_search_slugs[match.group(1)] = session_search_slugs.pop(slug_name)

        search_slug_list = fixit(session_search_slugs)
        column_slug_list = fixit(self._session_metadata_slugs)
        return search_slug_list, column_slug_list

    def get_icon_flags(self) -> IconFlags:
        """The summary icons raised for this session so far."""
        return self._icon_flags

    #
    # Mark events that we eventually want to summarize
    #

    def register_info_flags(self, flags: Action, *, line_number: int | None = None) -> None:
        """Record that this session performed an action.

        The action is recorded against the log entry being parsed, or against one of
        that entry's report lines when `line_number` is given. A `line_number` of 0 is
        treated as though it were absent, and records the entry as a whole.

        Parameters:
            flags: The action to record.
            line_number: The index of the report line the action belongs to, among the
                lines the log entry being parsed produces.
        """
        marker: LogMarker = (self._current_id, line_number) if line_number else self._current_id
        self._info_flags_usage[flags].add(marker)

    def register_search_slug(self, family: slug.Family, *, line_number: int) -> None:
        """Record that a report line searched on a slug family.

        The use is tallied under the family's label, which is the name
        `get_search_names_usage` reports.

        Parameters:
            family: The slug family the line searched on.
            line_number: The index of the line, among the report lines the log entry
                being parsed produces.
        """
        self._search_slugs_usage[family.label].add((self._current_id, line_number))

    def register_metadata_slug(self, family: slug.Family, *, line_number: int) -> None:
        """Record that a report line selected or deselected a metadata slug family.

        The use is tallied under the family's label, which is the name
        `get_metadata_names_usage` reports.

        Parameters:
            family: The slug family the line is about.
            line_number: The index of the line, among the report lines the log entry
                being parsed produces.
        """
        self._metadata_slugs_usage[family.label].add((self._current_id, line_number))

    def register_sessioned_download(self, filename: str, entry: LogEntry) -> None:
        """Record a file downloaded by a request belonging to this session.

        Downloads of the same name accumulate: the entry's size is added to the running
        total for that name and the log entry being parsed joins the set of entries that
        fetched it. An entry with no recorded size contributes zero bytes.

        Parameters:
            filename: The name the download is tallied under.
            entry: The log entry for the request, read for its size.
        """
        (size, log_ids) = self._sessioned_downloads_usage[filename]
        size[0] += entry.size or 0
        log_ids.add(self._current_id)

    def register_sessionless_download(self, path: str, entry: LogEntry) -> None:
        """Record a download requested directly rather than from within a session.

        The record goes onto the list shared with the configuration rather than onto
        this session's own tallies. A path that is not `/downloads/` followed by a single
        name is ignored, so a file named inside a subdirectory is not recorded.

        Parameters:
            path: The request path.
            entry: The log entry for the request.
        """
        match = re.fullmatch(r"/downloads/([^/]+)", path)
        if match:
            self._sessionless_downloads_usage.append((match.group(1), entry))

    def register_product_types(self, product_types: Iterable[str]) -> None:
        """Record the product types a request named.

        Each name is tallied against the log entry being parsed, and the session's count
        of product-type requests goes up by one whether or not any name was given.

        Parameters:
            product_types: The product type names to record.
        """
        for product in product_types:
            self._product_types_usage[product].add(self._current_id)
        self._product_types_count += 1

    def register_widget(self, family: slug.Family) -> None:
        """Record that this session created a search widget.

        The use is tallied against the log entry being parsed, under the family's label.

        Parameters:
            family: The slug family the widget was created for.
        """
        self._widgets_usage[family.label].add(self._current_id)

    def register_help_file(self, file_name: str) -> None:
        """Record that this session read a help file.

        The use is tallied against the log entry being parsed.

        Parameters:
            file_name: The help file's name, including its extension.
        """
        self._help_files_usage[file_name].add(self._current_id)

    def register_sort_slugs_changed(self, slugs_list: Sequence[slug.Info], *, line_number: int) -> None:
        """Record the sort order a report line changed the session to.

        The whole ordered list is the key, so the same slugs in a different order are a
        different sort order.

        Parameters:
            slugs_list: The slugs being sorted on, in order.
            line_number: The index of the line, among the report lines the log entry
                being parsed produces.
        """
        self._session_sort_slugs_usage[tuple(slugs_list)].add((self._current_id, line_number))

    #
    # The following are used by the summary pages.
    #

    def get_search_names_usage(self) -> Mapping[str, set[LogMarker]]:
        """Which report lines of this session searched on which slug family.

        Returns:
            A mapping from a family's label to the markers registered for it by
            `register_search_slug`.
        """
        return self._search_slugs_usage

    def get_metadata_names_usage(self) -> Iterator[tuple[str, set[LogMarker]]]:
        """Which parts of this session used which metadata slug family.

        A family that also had a widget created for it has the widget's markers folded
        in, so selecting a family and creating its widget are reported under one name.

        Yields:
            A family's label and the markers registered for it.
        """
        for name, log_ids in self._metadata_slugs_usage.items():
            if name in self._widgets_usage:
                log_ids = log_ids.union(self._widgets_usage[name])
            yield name, log_ids

    def get_unmatched_widgets_usage(self) -> Iterator[tuple[str, set[LogMarker]]]:
        """Which widgets this session created for families it never used as metadata.

        Yields:
            A family's label and the markers that created its widget, for each family
            with no metadata use registered.
        """
        for widget, ids in self._widgets_usage.items():
            if widget not in self._metadata_slugs_usage:
                yield widget, ids

    def get_sort_list_names_usage(self) -> Iterator[tuple[tuple[str, ...], set[LogMarker]]]:
        """Which report lines of this session set which sort order.

        Yields:
            A tuple of family labels, in sort order, and the markers that set it. The
            same tuple of labels can be yielded more than once, since sort orders are
            kept apart by their slugs rather than by their labels.
        """
        for sort_list, ids in self._session_sort_slugs_usage.items():
            names = tuple(value.family.label for value in sort_list)
            yield names, ids

    def get_info_flags_usage(self) -> Mapping[Action, set[LogMarker]]:
        """The actions this session performed, each mapped to its markers."""
        return self._info_flags_usage

    def get_help_files_usage(self) -> Mapping[str, set[LogMarker]]:
        """The help files this session read, each mapped to the entries that read it."""
        return self._help_files_usage

    def get_product_types_usage(self) -> Mapping[str, set[LogMarker]]:
        """The product types this session named, each mapped to the entries naming it."""
        return self._product_types_usage

    def get_product_types_usage_count(self) -> int:
        """How many of this session's requests named product types.

        A request that named an empty list of types still counts.
        """
        return self._product_types_count

    def get_sessioned_downloads_usage(self) -> Mapping[str, tuple[list[int], set[LogMarker]]]:
        """The files this session downloaded.

        Returns:
            A mapping from a file's name to a pair: a one-element list holding the total
            number of bytes tallied for that name, and the log entries that fetched it.
        """
        return self._sessioned_downloads_usage

    def parse_log_entry(self, entry: LogEntry, log_id: LogId) -> SESSION_INFO:
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
            try:
                self._current_id = log_id
                info, reference = method(self, entry, query, match)
            finally:
                self._current_id = LogId(-1)

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
    @pattern_registry.register(r'/__api/(dataimages)\.json')
    @pattern_registry.register(r'/__api/meta/(result_count)\.json')
    def __api_data(self, log_entry: LogEntry, query: dict[str, str], match: Match[str]) -> SESSION_INFO:
        """Report a request for search results, for their images, or for their count.

        The captured name -- `data`, `dataimages` or `result_count` -- says which of the
        three was asked for, and `QueryHandler` turns the query string into the report
        lines.
        """
        return self._query_handler.handle_query(log_entry, query, match.group(1))

    @pattern_registry.register(r'/__api/data\.json')
    def __api_data_old(self, log_entry: LogEntry, query: dict[str, str], _match: Match[str]) -> SESSION_INFO:
        """Report a request for `data.json`, an alternate spelling of `dataimages.json`.

        The request is reported the way `dataimages.json` is, not the way `data.html`
        is.
        """
        # data.json was the old name for dataimages.json.  Treat it like dataimages, rather than like data.html.
        return self._query_handler.handle_query(log_entry, query, "dataimages")

    #
    # CREATE WIDGET
    #

    @pattern_registry.register(r'/__widget/(.*).html')
    @pattern_registry.register(r'/__forms/widget/(.*).html')
    def __initialize_widget(self, log_entry: LogEntry, query: dict[str, str], match: Match[str]) -> SESSION_INFO:
        """Report the creation of a search widget.

        The widget's name is the captured part of the path. A name the slug map does not
        recognize produces no report line.
        """
        return self._query_handler.create_widget(log_entry, query, match.group(1))

    @pattern_registry.register(r'/__api/image/med/(.*)\.json')
    @pattern_registry.register(r'/__viewmetadatamodal/(.*)\.json')
    def __view_metadata(self,  _log_entry: LogEntry, _query: dict[str, str], match: Match[str]) -> SESSION_INFO:
        """Report one observation's metadata being viewed.

        Registers `Action.VIEWED_SLIDE_SHOW` and links the line to the observation's
        detail view.
        """
        self.register_info_flags(Action.VIEWED_SLIDE_SHOW)
        metadata = match.group(1)
        return [f'View Metadata: {metadata}'], self.__create_opus_url(metadata)

    @pattern_registry.register(r'/__api/data\.csv')
    def __download_results_csv(self, _log_entry: LogEntry, _query: dict[str, str], _match: Match[str]) -> SESSION_INFO:
        """Report a CSV of the whole search result being downloaded.

        Raises the session's download icon and registers
        `Action.DOWNLOADED_CSV_FILE_FOR_ALL_RESULTS`.
        """
        self.performed_download()
        self.register_info_flags(Action.DOWNLOADED_CSV_FILE_FOR_ALL_RESULTS)
        return ["Download CSV of Search Results"], None

    @pattern_registry.register(r'/__api/metadata_v2/(.*)\.csv')
    def __download_metadata_csv(self, log_entry: LogEntry, query: dict[str, str], match: Match[str]) -> SESSION_INFO:
        """Report a CSV of one observation's metadata being downloaded.

        Raises the session's download icon, registers
        `Action.DOWNLOADED_CSV_FILE_FOR_ONE_OBSERVATION`, and tallies the download under
        the OPUS id with a `.csv` extension. The line says "Selected" when the request
        named columns of its own and "All" when it did not.
        """
        self.performed_download()
        self.register_info_flags(Action.DOWNLOADED_CSV_FILE_FOR_ONE_OBSERVATION)
        opus_id = match.group(1)
        self.register_sessioned_download(opus_id + '.csv', log_entry)
        extra = 'Selected' if query.get('cols') else 'All'
        text = f'Download CSV of {extra} Metadata for OPUSID'
        if self._uses_html:
            return [self.safe_format('{}: {}', text, opus_id)], self.__create_opus_url(opus_id)
        else:
            return [f'{text}: { opus_id }'], None

    @pattern_registry.register(r'/__api/download/(.*)\.zip')
    def __download_archive(self, log_entry: LogEntry, query: dict[str, str], match: Match[str]) -> SESSION_INFO:
        """Report a data or URL archive for one observation being downloaded.

        Raises the session's download icon and tallies the download under the OPUS id
        with a `.zip` extension. A request whose `urlonly` is present and not "0" is a
        URL archive and registers
        `Action.DOWNLOADED_ZIP_URL_FILE_FOR_ONE_OBSERVATION`; otherwise it is a data
        archive and registers `Action.DOWNLOADED_ZIP_FILE_FOR_ONE_OBSERVATION`.
        """
        self.performed_download()
        opus_id = match.group(1)
        self.register_sessioned_download(opus_id + '.zip', log_entry)
        url_only = query.get('urlonly') not in (None, "0")
        text = f'Download {"URL" if url_only else "Data"} Archive for OPUSID'
        self.register_info_flags(Action.DOWNLOADED_ZIP_URL_FILE_FOR_ONE_OBSERVATION if url_only else
                                 Action.DOWNLOADED_ZIP_FILE_FOR_ONE_OBSERVATION)
        if self._uses_html:
            return [self.safe_format('{}: {}', text, opus_id)], self.__create_opus_url(opus_id)
        else:
            return [f'{text}: { opus_id }'], None

    #
    # Collections
    #

    @pattern_registry.register(r'/__collections/view\.html')
    @pattern_registry.register(r'/__cart/view\.html')
    def __collections_view_cart(self, _log_entry: LogEntry, _query: dict[str, str], _match: Match[str]) -> SESSION_INFO:
        """Report the cart being viewed."""
        return ['View Cart'], None

    @pattern_registry.register(r'/__collections/data\.csv')
    @pattern_registry.register(r'/__cart/data\.csv')
    def __download_cart_metadata_csv(self, _: LogEntry, _query: dict[str, str], _match: Match[str]) -> SESSION_INFO:
        """Report a CSV of the cart's selected metadata being downloaded.

        Raises the session's download icon and registers
        `Action.DOWNLOADED_CSV_FILE_FOR_CART`.
        """
        self.performed_download()
        self.register_info_flags(Action.DOWNLOADED_CSV_FILE_FOR_CART)
        return ["Download CSV of Selected Metadata for Cart"], None

    @pattern_registry.register(r'/__collections/download\.(json|zip)')
    @pattern_registry.register(r'/__collections/download/default\.zip')
    @pattern_registry.register(r'/__cart/download\.json')
    def __create_archive(self, _log_entry: LogEntry, query: dict[str, str], _match: Match[str]) -> SESSION_INFO:
        """Report a data or URL archive for the whole cart being downloaded.

        Raises the session's download icon and records the product types the request
        named, with hyphens in their names turned into underscores. A request whose
        `urlonly` is present and not "0" is a URL archive and registers
        `Action.DOWNLOADED_ZIP_URL_FILE_FOR_CART`; otherwise it is a data archive and
        registers `Action.DOWNLOADED_ZIP_ARCHIVE_FILE_FOR_CART`. The line lists the
        product types in sorted order.
        """
        self.performed_download()
        url_only = query.get('urlonly') not in [None, '0']
        self.register_info_flags(Action.DOWNLOADED_ZIP_URL_FILE_FOR_CART if url_only else
                                 Action.DOWNLOADED_ZIP_ARCHIVE_FILE_FOR_CART)
        ptypes_field = query.get('types')
        ptypes = [x.replace('-', '_') for x in (ptypes_field.split(',') if ptypes_field else [])]
        self.register_product_types(ptypes)
        joined_ptypes = self.quote_and_join_list(sorted(ptypes))
        text = f'Download {"URL" if url_only else "Data"} Archive for Cart: {joined_ptypes}'
        return [text], None

    # Note that the __collections/ and the __cart/ are different.
    @pattern_registry.register(r'/__collections/(view)\.json')
    @pattern_registry.register(r'/__collections/default/(view)\.json')
    @pattern_registry.register(r'/__cart/(status)\.json')
    def __download_product_types(self, _log_entry: LogEntry, query: dict[str, str], match: Match[str]) -> SESSION_INFO:
        """Report the product types selected for a cart download.

        The report is a difference against the types this session last selected: the
        first such request reports the types it set, and later ones report the types
        added and the types removed. When that leaves nothing to say, the line reports
        that the product types are unchanged. Names have hyphens turned into
        underscores.

        The `/__cart/status.json` spelling reports nothing, and changes nothing, unless
        the request also carries `download=1`.
        """
        if match.group(1) == 'status' and query.get('download') != '1':
            # The __cart/status version requires &download=1
            return [], None
        ptypes_field = query.get('types')
        new_ptypes = {x.replace('-', '_') for x in (ptypes_field.split(',') if ptypes_field else [])}

        old_ptypes = self._previous_product_info_type
        self._previous_product_info_type = new_ptypes

        result = []

        def show(verb: str, items: set[str]) -> None:
            """Add a line naming a set of product types, unless the set is empty.

            Parameters:
                verb: What happened to the types; it appears title-cased in the line.
                items: The product types, which the line lists in sorted order.
            """
            if items:
                plural = 's' if len(items) > 1 else ''
                joined_items = self.quote_and_join_list(sorted(items))
                result.append(f'{verb.title()} Product Type{plural}: {joined_items}')

        if old_ptypes is None:
            show('set', new_ptypes)
        else:
            show('add', new_ptypes - old_ptypes)
            show('remove', old_ptypes - new_ptypes)

        if not result:
            result.append('Product Types are unchanged')
        return result, None

    @pattern_registry.register(r'/__collections/reset\.(html|json)')
    @pattern_registry.register(r'/__collections/default/reset\.(html|json)')
    @pattern_registry.register(r'/__cart/reset\.(html|json)')
    def __reset_cart(self, _log_entry: LogEntry, _query: dict[str, str], _match: Match[str]) -> SESSION_INFO:
        """Report the cart being emptied."""
        return ['Empty Cart'], None

    @pattern_registry.register(r'/__collections/(add|remove)\.json')
    @pattern_registry.register(r'/__collections/default/(add|remove)\.json')
    @pattern_registry.register(r'/__cart/(add|remove)\.json')
    def __add_remove_cart(self, _log_entry: LogEntry, query: dict[str, str], match: Match[str]) -> SESSION_INFO:
        """Report one observation being added to or removed from the cart.

        The observation is taken from the request's `opusid`, or from `opus_id` when
        `opusid` is absent. A request naming neither reports "???" in place of the id.
        """
        opus_id = query.get('opusid') or query.get('opus_id')  # opusid is new name, opus_id is old
        selection = match.group(1).title()
        if self._uses_html and opus_id:
            return [self.safe_format('Cart {}: {}', selection.title(), opus_id)], self.__create_opus_url(opus_id)
        else:
            return [f'Cart {selection.title() + ":":<7} {opus_id or "???"}'], None

    @pattern_registry.register(r'/__collections/(add|remove)range\.json')
    @pattern_registry.register(r'/__collections/default/(add|remove)range\.json')
    @pattern_registry.register(r'/__cart/(add|remove)range\.json')
    def __add_remove_range_to_cart(self, _log: LogEntry, query: dict[str, str], match: Match[str]) -> SESSION_INFO:
        """Report a range of observations being added to or removed from the cart.

        The range comes from the request's `range`; a request without one reports "???"
        in its place.
        """
        selection = match.group(1).title()
        query_range = query.get('range', '???').replace(',', ', ')
        return [f'Cart {selection} Range: {query_range}'], None

    @pattern_registry.register(r'/__collections/addall\.json')
    @pattern_registry.register(r'/__collections/default/addall\.json')
    @pattern_registry.register(r'/__cart/addall\.json')
    def __add_all_to_cart(self, _log_entry: LogEntry, query: dict[str, str], _match: Match[str]) -> SESSION_INFO:
        """Report observations being added to the cart in bulk.

        A request carrying a `range` reports that range; one without reports that
        everything was added.
        """
        query_range = query.get('range')
        if query_range:
            query_range = query_range.replace(',', ', ')
            return [f'Cart Add {query_range}'], None
        else:
            return ['Cart Add All'], None

    #
    # FORMS
    #

    @pattern_registry.register(r'/__forms/column_chooser\.html')
    @pattern_registry.register(r'/__selectmetadatamodal\.json')
    def __column_chooser(self, _log_entry: LogEntry, _query: dict[str, str], _match: Match[str]) -> SESSION_INFO:
        """Report the metadata selector being opened.

        Registers `Action.VIEWED_SELECT_METADATA`.
        """
        self.register_info_flags(Action.VIEWED_SELECT_METADATA)
        return ['Metadata Selector'], None

    #
    # INIT DETAIL
    #

    @pattern_registry.register(r'/__initdetail/(.*)\.html')
    def __initialize_detail(self, _log_entry: LogEntry, _query: dict[str, str], match: Match[str]) -> SESSION_INFO:
        """Report one observation's detail tab being opened.

        Registers `Action.VIEWED_DETAIL_TAB`. When the report is HTML, the line links to
        the observation's detail view.
        """
        self.register_info_flags(Action.VIEWED_DETAIL_TAB)
        opus_id = match.group(1)
        if self._uses_html:
            return [self.safe_format('View Detail: {}', opus_id)], self.__create_opus_url(opus_id)
        else:
            return [f'View Detail: { opus_id }'], None

    #
    # HELP
    #

    @pattern_registry.register(r'/__help/(\w+)\.(html|pdf)')
    def __read_help_information(self, _log_entry: LogEntry, _query: dict[str, str], match: Match[str]) -> SESSION_INFO:
        """Report a help page being read as HTML or as PDF.

        The file is tallied under its name and extension, with `faq` reported as `FAQ`.
        Reading `splash` registers no action; any other name registers
        `Action.VIEWED_HELP_FILE` for HTML or `Action.VIEWED_HELP_FILE_AS_PDF` for PDF.
        """
        help_type, file_type = match.group(1, 2)
        help_name = help_type.upper() if help_type == 'faq' else help_type
        if help_name != 'splash':
            flag = Action.VIEWED_HELP_FILE if file_type == 'html' else Action.VIEWED_HELP_FILE_AS_PDF
            self.register_info_flags(flag)
        self.register_help_file(help_name + '.' + file_type)
        if self._uses_html:
            return [self.safe_format('Help {} <samp>{}</samp>', file_type.upper(), help_name)], None
        else:
            return [f'Help {file_type.upper()} {help_name}'], None

    #
    # Various utilities
    #

    def __create_opus_url(self, opus_id: str) -> str:
        """Build the link the report uses for one observation.

        Parameters:
            opus_id: The observation's OPUS id.

        Returns:
            The URL of the observation's detail view, with the id escaped for HTML.
        """
        return self.safe_format('/opus/#/view=detail&amp;detail={0}', opus_id)
