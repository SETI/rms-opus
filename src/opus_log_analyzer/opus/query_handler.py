"""Turning an OPUS search URL into a description of what changed.

The OPUS front end re-sends its whole search in the query string of every API
call, so a session's requests are a series of snapshots rather than a series of
edits. `QueryHandler` keeps the previous snapshot and reports the difference:
which search terms were added, removed or altered, which metadata columns were
selected, how the sort order moved, and which page was fetched.

A search term is identified by a `Family` (the field) and a subgroup number (the
clause, for a field the user has more than one constraint on). Comparing the old
and new clause lists is what the `__show_search_change_*` methods render; where
the change does not fit one of the recognized shapes, the whole new term is
reported instead.
"""
from __future__ import annotations

import operator
import urllib
import urllib.parse
from collections import defaultdict
from collections.abc import Sequence
from enum import Enum, auto
from functools import reduce
from typing import Any, NamedTuple, cast

from markupsafe import Markup

from opus_log_analyzer.log_entry import LogEntry
from opus_log_analyzer.opus import slug as slug
from opus_log_analyzer.opus.configuration_flags import Action
from opus_log_analyzer.opus.slug import Family, FamilyType, Info


class SearchClause(NamedTuple):
    """One constraint on one field: its value or range, plus qtype and unit.

    A singleton field uses `single_value`; a range field uses `min_value` and
    `max_value`. `flags` carries what the slug map noticed about the slugs this
    clause was built from, such as an obsolete spelling.
    """

    single_value: str | None
    min_value: str | None
    max_value: str | None
    qtype: str | None
    unit: str | None
    flags: slug.Flags

    @staticmethod
    def from_slug_list(pairs: list[tuple[slug.Info, str]]) -> SearchClause:
        """Build a clause from the query-string slugs belonging to one term.

        Parameters:
            pairs: Each recognized slug and the value it carried. Two slugs of
                the same family type keep whichever comes later.

        Returns:
            The clause, with the union of the slugs' flags.

        Raises:
            TypeError: If `pairs` is empty, since the flags are reduced with no
                initial value.
        """
        mapping = {slug_info.family_type: value for slug_info, value in pairs}  # family_type to value
        return SearchClause(
            min_value=mapping.get(slug.FamilyType.MIN),
            max_value=mapping.get(slug.FamilyType.MAX),
            single_value=mapping.get(slug.FamilyType.SINGLETON),
            qtype=mapping.get(slug.FamilyType.QTYPE),
            unit=mapping.get(slug.FamilyType.UNIT),
            flags=reduce(operator.or_, (slug_info.flags for (slug_info, _) in pairs))
        )

    def is_value_only(self) -> bool:
        """Whether the clause constrains a value without a qtype or a unit."""
        return self.qtype is None and self.unit is None


SearchSlugInfo = dict[slug.Family, dict[int, SearchClause]]
MetadataSlugInfo = dict[slug.Family, slug.Info]


class State(Enum):
    """What the session was last seen doing: nothing yet, searching, or fetching."""

    RESET = auto()
    SEARCHING = auto()
    FETCHING = auto()


class QueryHandler:
    """Reports each search URL as the difference from the previous one.

    One instance belongs to one session, and it holds that session's previous
    snapshot. The report lines it produces are HTML or plain text according to
    the `uses_html` it was constructed with.
    """

    DEFAULT_SORT_ORDER = 'time1,opusid'
    _session_info: Any  # can't handle circular imports.  :-(
    _slug_map: slug.ToInfoMap
    _default_metadata_slug_info: MetadataSlugInfo
    _uses_html: bool

    _previous_search_slug_info: SearchSlugInfo  # map from family to List[(Slug.Info, Value)]
    _previous_metadata_slug_info: MetadataSlugInfo | None  # map from raw slug to Slug.Info
    _previous_pages: list[str]  # previous page.  Two entries for browse and cart
    _previous_startobss: list[str]  # previous start observation.  Two entries for browse and cart
    _previous_sort_order: str  # sort order
    _previous_state: State

    def __init__(self, session_info: Any, slug_map: slug.ToInfoMap, default_metadata_slug_info: MetadataSlugInfo,
                 uses_html: bool) -> None:
        """Parameters:
        session_info: The session these queries belong to, notified of each
            action and slug the handler recognizes. Typed loosely because
            `SessionInfo` imports this module.
        slug_map: Resolves a query-string slug to what it means.
        default_metadata_slug_info: The columns OPUS shows when the request
            names none.
        uses_html: Whether report lines are HTML rather than plain text.
        """
        self._session_info = session_info
        self._slug_map = slug_map
        self._default_metadata_slug_info = default_metadata_slug_info
        self._uses_html = uses_html
        self.__reset()

    def __reset(self) -> None:
        """Forget the previous snapshot, so the next query reports as a new search."""
        self._previous_search_slug_info = {}
        self._previous_metadata_slug_info = None  # handled specially by get_metadata_slug_info
        self._previous_sort_order = self.DEFAULT_SORT_ORDER
        self._previous_pages = ['', '']
        self._previous_startobss = ['', '']
        self._previous_browses = ['', '']
        self._previous_state = State.RESET

    def create_widget(self, _entry: LogEntry, _query: dict[str, str],
                      widget: str) -> tuple[list[str], str | None]:
        """Report the opening of a search widget.

        Parameters:
            _entry: The log entry, unused.
            _query: The query string, unused.
            widget: The widget's slug, as it appeared in the URL.

        Returns:
            A single report line naming the field, and None for the URL; or no
            lines at all if the slug map does not recognize the widget.
        """
        family_info = self._slug_map.get_family_info_for_widget(widget)
        if family_info:
            self._session_info.register_widget(family_info)
            return [f'Create Widget "{family_info.label}"'], None
        else:
            return [], None

    def handle_query(self, _entry: LogEntry, query: dict[str, str],
                     query_type: str) -> tuple[list[str], str | None]:
        """Report one search request as the difference from the previous one.

        The snapshot this query carries replaces the stored one, so the next
        call reports against this request.

        Parameters:
            _entry: The log entry, unused.
            query: The request's query string, one value per key.
            query_type: `result_count`, `data` or `dataimages`. A count request
                reports only the search terms; the other two also report
                metadata columns, sort order and paging.

        Returns:
            The report lines, and the OPUS URL that reproduces this search --
            the latter only in HTML mode and only when there was something to
            report, otherwise None.

        Raises:
            NotImplementedError: If `query_type` is none of the three.
        """
        result: list[str] = []

        if query_type == 'result_count':
            uses_metadata, uses_pages, uses_sort, current_state = False, False, False, State.SEARCHING
        elif query_type == 'data' or query_type == 'dataimages':
            uses_metadata, uses_pages, uses_sort, current_state = True, True, True, State.FETCHING
        else:
            raise NotImplementedError(query_type)

        previous_state = self._previous_state
        if current_state != previous_state:
            if previous_state == State.RESET:
                result.append('Begin New Search')
            if (previous_state, current_state) == (State.FETCHING, State.SEARCHING):
                result.append('Refining Previous Search')

        search_slug_info = self.__get_search_slug_info(query)

        if uses_metadata:
            metadata_query = query.get('cols')
            if metadata_query:
                metadata_slug_info = self.get_metadata_slug_info(metadata_query.split(','),
                                                                 self._slug_map, self._session_info)
            else:
                metadata_slug_info = self._default_metadata_slug_info
        else:
            metadata_slug_info = {}

        self.__handle_search_info(self._previous_search_slug_info, search_slug_info, result)
        self._previous_search_slug_info = search_slug_info

        if uses_metadata:
            self.__get_metadata_info(self._previous_metadata_slug_info, metadata_slug_info, result)
            self._previous_metadata_slug_info = metadata_slug_info

        if uses_sort:
            sort_order = query.get('order', self.DEFAULT_SORT_ORDER)
            self.__get_sort_order_info(self._previous_sort_order, sort_order, result)
            self._previous_sort_order = sort_order

        if uses_pages:
            assert current_state == State.FETCHING
            is_browsing = query.get('view') == 'browse'
            page = query.get('page', '')
            startobs = query.get('cart_startobs', ''), query.get('startobs', '')
            previous_browse = self._previous_browses[is_browsing]
            if is_browsing:
                current_browse = query.get('browse', '')
            else:
                current_browse = query.get('cart_browse') or query.get('colls_browse') or ''

            if startobs[is_browsing]:
                page_type, info, previous_info = 'Starting Observation', startobs[is_browsing], self._previous_startobss
            elif page:
                page_type, info, previous_info = 'Page', page, self._previous_pages
            else:
                page_type, info, previous_info = 'Page', '???', ['???', '???']
            browse_or_cart = 'Browse' if is_browsing else 'Cart'
            viewed = 'Table' if current_browse == 'data' else 'Gallery'

            if query_type == 'dataimages':
                action_flag = {
                    ("Browse", "Table"): Action.VIEWED_BROWSE_TAB_AS_TABLE,
                    ("Browse", "Gallery"): Action.VIEWED_BROWSE_TAB_AS_GALLERY,
                    ("Cart", "Table"): Action.VIEWED_CART_TAB_AS_TABLE,
                    ("Cart", "Gallery"): Action.VIEWED_CART_TAB_AS_GALLERY,
                }[browse_or_cart, viewed]
                # Attach the flag to the line we're about to add.
                self._session_info.register_info_flags(action_flag, line_number=len(result))

            if current_state != previous_state or current_browse != previous_browse:
                result.append(f'View {browse_or_cart} {viewed}: {page_type} {info}')
            elif info:
                what = f'{browse_or_cart} {viewed} {page_type}'
                limit = query.get('limit', '???')
                result.append(f'Fetch {what.title()} {info} Limit {limit}')

            previous_info[is_browsing] = info
            self._previous_browses[is_browsing] = current_browse

        self._previous_state = current_state

        url: str | None = None
        if result and self._uses_html:
            query.pop('reqno', None)  # Remove if there, but okay if not
            url = self.safe_format('/opus/#/{}', urllib.parse.urlencode(query, False))

        if result and query_type != 'result_count':
            self._session_info.fetched_gallery()

        return result, url

    def __handle_search_info(self, old_info: SearchSlugInfo, new_info: SearchSlugInfo, result: list[str]) -> None:
        """Handles info for the contents of search slugs"""
        if not new_info:
            if old_info:
                self._session_info.changed_search_slugs(line_number=len(result))
                result.append('Reset Search')
            return

        all_search_families = set(old_info.keys()).union(new_info.keys())

        for family in sorted(all_search_families):
            old_result_length = len(result)
            if family not in new_info:
                result.append(f'Remove Search: "{family.label}"')
            else:
                self.__handle_search_info_for_family(family, old_info, new_info, result)
            for line_number in range(old_result_length, len(result)):
                self._session_info.register_search_slug(family, line_number=line_number)
                self._session_info.changed_search_slugs(line_number=line_number)

    def __handle_search_info_for_family(self, family: slug.Family, old_info: SearchSlugInfo,
                                        new_info: SearchSlugInfo,
                                        result: list[str]) -> None:
        """Report how one field's constraints changed, in the most specific way that fits.

        The old and new clause lists are compared for four shapes, in order: the
        same number of clauses (each differing one is reported as an alteration),
        one clause appended, one clause removed from the middle, and anything
        else, which is reported as a complex change listing every current clause.

        Parameters:
            family: The field whose constraints changed.
            old_info: The previous snapshot.
            new_info: The current snapshot, which must contain `family`.
            result: The report lines, appended to.
        """
        is_add = family not in old_info

        def pull_data(info: SearchSlugInfo) -> list[SearchClause]:
            """Return this family's clauses from a snapshot, ordered by subgroup.

            Parameters:
                info: The snapshot to read.

            Returns:
                The clauses, in subgroup order.
            """
            return [info[family][subgroup] for subgroup in sorted(info[family].keys())]

        old_data = [] if is_add else pull_data(old_info)
        new_data = pull_data(new_info)

        fields_info: Sequence[tuple[str, str]]
        if family.is_singleton():
            fields_info = (('value', 'single_value'), ('qtype', 'qtype'), ('unit', 'unit'))
        else:
            fields_info = ((family.min, 'min_value'), (family.max, 'max_value'), ('qtype', 'qtype'), ('unit', 'unit'))

        if len(old_data) == len(new_data):
            for i, _old, _new in ((i, old, new) for i, (old, new) in enumerate(zip(old_data, new_data, strict=False)) if old != new):
                self.__show_search_change_delta(family, fields_info, old_data, new_data, i, result)
            return
        if len(old_data) == len(new_data) - 1 and old_data == new_data[0:-1]:
            self.__show_search_change_add(family, fields_info, new_data, len(new_data) - 1, result)
            return
        if len(old_data) == len(new_data) + 1:
            mismatch = next((i for i in range(len(new_data)) if old_data[i] != new_data[i]), len(new_data))
            if old_data[mismatch + 1:] == new_data[mismatch:]:
                self.__show_search_change_remove(family, fields_info, old_data, new_data, mismatch, result)
                return
        self.__show_unexpected_change(family, fields_info, new_data, result)

    def __show_search_change_add(self, family: slug.Family, fields_info: Sequence[tuple[str, str]],
                                 new_data: list[SearchClause], index: int,
                                 result: list[str], *,
                                 action: str = 'Add Search') -> None:
        """Report one whole clause, as an addition by default.

        Parameters:
            family: The field the clause constrains.
            fields_info: The clause attributes to show and the names to show
                them under, which differ between singleton and range fields.
            new_data: The current clause list.
            index: Which clause to report. The label carries a number only when
                the field has more than one.
            result: The report lines, appended to.
            action: The wording the line opens with, so the same rendering can
                serve "Add Search" and the "- Current Search Term" lines that
                follow a removal or a complex change.
        """
        search_family_values = new_data[index]
        postscript = self.__get_postscript(search_family_values.flags) if len(new_data) == 1 else ""
        label = family.label if len(new_data) == 1 else f'{family.label} #{index + 1}'
        space = ' ' * max(0, 13 - len(action))

        if family.is_singleton() and search_family_values.is_value_only():
            if self._uses_html:
                result.append(self.safe_format(
                    '{}: "{}" = <mark><ins>{}</ins></mark>{}',
                    action, label, self.__format_search_value(search_family_values.single_value), postscript))
            else:
                result.append(f'{action}:{space} "{label}" = "{search_family_values.single_value}"{postscript}')
        else:
            fields = [(name, getattr(search_family_values, attribute)) for name, attribute in fields_info]
            if self._uses_html:
                joined_info: str = Markup(', ').join(
                    self.safe_format('<mark><ins>{}:{}</ins></mark>', name, self.__format_search_value(value), )
                    for (name, value) in fields)
                result.append(self.safe_format('{}: "{}" = ({}){}', action, label, joined_info, postscript))
            else:
                joined_info = ", ".join(
                    f'{name.upper()}:{self.__format_search_value(value)}' for (name, value) in fields)
                result.append(f'{action}:{space} "{label}" = ({joined_info}){postscript}')

    def __show_search_change_remove(self, family: slug.Family, fields_info: Sequence[tuple[str, str]],
                                    old_data: list[SearchClause], new_data: list[SearchClause],
                                    index: int,
                                    result: list[str]) -> None:
        """Report that one clause was removed, then list the ones that remain.

        Parameters:
            family: The field the clause belonged to.
            fields_info: As for `__show_search_change_add`.
            old_data: The previous clause list.
            new_data: The current clause list.
            index: Which clause was removed, numbered within the old list.
            result: The report lines, appended to.
        """
        length = len(old_data)
        label = family.label if length == 1 else f'{family.label} #{index + 1}'
        result.append(f'Remove Search Term: "{label}"')
        for i in range(len(new_data)):
            self.__show_search_change_add(family, fields_info, new_data, i, result, action="- Current Search Term")

    def __show_unexpected_change(self, family: slug.Family, fields_info: Sequence[tuple[str, str]],
                                 new_data: list[SearchClause],
                                 result: list[str]) -> None:
        """Report a change that fits none of the recognized shapes.

        The change itself is not described; every current clause is listed
        instead, which is what makes the report readable when the front end
        rewrites a term wholesale.

        Parameters:
            family: The field that changed.
            fields_info: As for `__show_search_change_add`.
            new_data: The current clause list.
            result: The report lines, appended to.
        """
        result.append(f'Complex Change for Search Term: "{family.label}"')
        for i in range(len(new_data)):
            self.__show_search_change_add(family, fields_info, new_data, i, result, action="- Current Search Term")

    def __show_search_change_delta(self, family: slug.Family, fields_info: Sequence[tuple[str, str]],
                                   old_list: list[SearchClause], new_list: list[SearchClause], index: int,
                                   result: list[str]) -> None:
        """Report how one clause changed, field by field.

        A singleton field whose old and new clauses both carry a bare value is
        reported as a value change, which lists the individual values added and
        removed. Anything else is reported per attribute, upper-casing the name
        of each attribute that moved.

        Parameters:
            family: The field the clause constrains.
            fields_info: As for `__show_search_change_add`.
            old_list: The previous clause list.
            new_list: The current clause list.
            index: Which clause changed.
            result: The report lines, appended to.
        """
        old_values, new_values = old_list[index], new_list[index]
        label = family.label if index == 0 and len(old_list) == 1 else f"{family.label} #{index + 1}"

        if family.is_singleton() and old_values.is_value_only() and new_values.is_value_only():
            self.__slug_value_change(label, old_values.single_value or '', new_values.single_value or '', result)
        else:
            fields = [(name, getattr(old_values, attr), getattr(new_values, attr))
                      for name, attr in fields_info]
            if self._uses_html:
                def maybe_mark(tag: str, old: str | None, new: str | None) -> str:
                    """Render one changed attribute, marking it when it moved.

                    Parameters:
                        tag: The attribute's name, as the report shows it.
                        old: Its previous value.
                        new: Its current value.

                    Returns:
                        The rendered attribute, wrapped in a `mark` element when
                        the two values differ.
                    """
                    fmt = '{}:{}' if old == new else '<mark>{}:{}</mark>'
                    return self.safe_format(fmt, tag, self.__format_search_value(new))

                joined_info: str = Markup(', ').join(maybe_mark(tag, old, new) for (tag, old, new) in fields)
                result.append(self.safe_format('Change Search: "{}": ({})', label, joined_info))
            else:
                def maybe_mark(tag: str, old: str | None, new: str | None) -> str:
                    """Render one changed attribute, upper-casing it when it moved.

                    Parameters:
                        tag: The attribute's name, as the report shows it.
                        old: Its previous value.
                        new: Its current value.

                    Returns:
                        The rendered attribute, with the name upper-cased when
                        the two values differ.
                    """
                    return f'{tag if old == new else tag.upper()}:{self.__format_search_value(new)}'

                joined_info = ', '.join(maybe_mark(tag, old, new) for (tag, old, new) in fields)
                result.append(f'Change Search: "{label}" = ({joined_info})')

    def __get_metadata_info(self, old_info: MetadataSlugInfo | None, new_info: MetadataSlugInfo,
                            result: list[str]) -> None:
        """Report which metadata columns the user selected or removed.

        Nothing is reported when the set of columns is unchanged.

        Parameters:
            old_info: The previously selected columns, or None if the session
                has not selected any yet, in which case the comparison is
                against the OPUS defaults.
            new_info: The currently selected columns.
            result: The report lines, appended to.
        """
        new_metadata_families = set(new_info.keys())
        if old_info is None:
            old_metadata_families = set(self._default_metadata_slug_info.keys())
        else:
            old_metadata_families = set(old_info.keys())

        if new_metadata_families == old_metadata_families:
            return

        if old_info is None:
            metadata_labels = [new_info[family].label for family in sorted(new_metadata_families)]
            quoted_metadata_labels = self._session_info.quote_and_join_list(sorted(metadata_labels))
            for family in new_metadata_families:
                self._session_info.register_metadata_slug(family, line_number=len(result))
            self._session_info.changed_metadata_slugs(line_number=len(result))
            result.append(f'Starting with Selected Metadata: {quoted_metadata_labels}')
            return

        if new_metadata_families == set(self._default_metadata_slug_info.keys()):
            self._session_info.changed_metadata_slugs(line_number=len(result))
            result.append('Reset Selected Metadata')
            return

        all_metadata_families = old_metadata_families.union(new_metadata_families)
        added_metadata: list[tuple[Family, Info]] = []
        removed_metadata: list[tuple[Family, Info]] = []
        for family in sorted(all_metadata_families):
            old_slug_info = old_info.get(family)
            new_slug_info = new_info.get(family)
            if old_slug_info and not new_slug_info:
                removed_metadata.append((family, old_slug_info))
            elif new_slug_info and not old_slug_info:
                added_metadata.append((family, new_slug_info))

        for family, slug_info in removed_metadata:
            self._session_info.register_metadata_slug(family, line_number=len(result))
            self._session_info.changed_metadata_slugs(line_number=len(result))
            result.append(f'Remove Selected Metadata: "{slug_info.label}"')

        for family, slug_info in added_metadata:
            postscript = self.__get_postscript(slug_info.flags)
            self._session_info.register_metadata_slug(family, line_number=len(result))
            self._session_info.changed_metadata_slugs(line_number=len(result))
            if not self._uses_html:
                result.append(f'Add Selected Metadata:    "{slug_info.label}"{postscript}')
            else:
                result.append(
                    self.safe_format('Add Selected Metadata: "{}"{}', slug_info.label, postscript))

    def __get_sort_order_info(self, old_sort_order: str, new_sort_order: str,
                              result: list[str]) -> None:
        """Report a change of sort order, one line per column.

        Nothing is reported when the order is unchanged.

        Parameters:
            old_sort_order: The previous `order` value.
            new_sort_order: The current one, a comma-separated column list where
                a leading minus means descending.
            result: The report lines, appended to.

        Raises:
            AssertionError: If the slug map does not recognize a column named in
                the new sort order.
        """
        if old_sort_order != new_sort_order:
            start_result_length = len(result)
            sort_list: list[Info] = []
            columns = new_sort_order.split(',')
            result.append('Change Sort Order:')
            for column in columns:
                if column.startswith('-'):
                    order = 'Descending'
                    column = column[1:]
                else:
                    order = 'Ascending'
                slug_info: Info | None = self._slug_map.get_info_for_column_slug(column)
                assert slug_info
                sort_list.append(slug_info)
                result.append(f'        "{slug_info.label}" ({order})')
            for line_number in range(start_result_length, len(result)):
                self._session_info.register_sort_slugs_changed(sort_list, line_number=line_number)
                self._session_info.register_info_flags(Action.CHANGED_SORT_ORDER, line_number=line_number)

    def __slug_value_change(self, name: str, old_value: str, new_value: str,
                            result: list[str]) -> None:
        """Report which of a multi-valued term's values were added or removed.

        The values are treated as a set, so reordering alone reports nothing. In
        HTML mode additions and removals are marked up individually; in text
        mode the whole old and new lists are shown.

        Parameters:
            name: The label to report the term under.
            old_value: The previous comma-separated value list.
            new_value: The current one.
            result: The report lines, appended to.
        """
        old_value_set = set(old_value.split(','))
        new_value_set = set(new_value.split(','))
        if old_value_set == new_value_set:
            return
        if self._uses_html:
            marked_changes: list[str] = []
            for value in sorted(old_value_set.union(new_value_set)):
                formatted_value = self.__format_search_value(value)
                if value not in old_value_set:
                    marked_changes.append(self.safe_format('<mark><ins>{}</ins></mark>', formatted_value))
                elif value not in new_value_set:
                    marked_changes.append(self.safe_format('<mark><del>{}</del></mark>', formatted_value))
                else:
                    # formatted_value comes from this class's own safe_format helper above,
                    # which escaped it already; re-wrapping keeps it from being escaped twice.
                    marked_changes.append(Markup(formatted_value))  # nosec B704
            joined_values = Markup(',').join(marked_changes)
            result.append(self.safe_format('Change Search: "{}" = {}', name, joined_values))
        elif old_value_set.intersection(new_value_set):
            change_list: list[tuple[str, str]] = []
            for value in sorted(old_value_set.union(new_value_set)):
                if value not in old_value_set:
                    change_list.append(('+', self.__format_search_value(value)))
                elif value not in new_value_set:
                    change_list.append(('-', self.__format_search_value(value)))
            assert change_list
            joined_change_list = ', '.join(f'{a}{b}' for (a, b) in change_list)
            result.append(f'Change Search: "{name}" = {joined_change_list}')
        else:
            formatted_old_values = [self.__format_search_value(x) for x in sorted(old_value_set)]
            formatted_new_values = [self.__format_search_value(x) for x in sorted(new_value_set)]
            joined_old_values = ', '.join(formatted_old_values)
            joined_new_values = ', '.join(formatted_new_values)
            result.append(f'Change Search: "{name}" = {joined_old_values} -> {joined_new_values}')

    def __get_search_slug_info(self, query: dict[str, str]) -> SearchSlugInfo:
        """Read the search terms out of a query string.

        Every recognized slug is also registered with the session, including the
        ones dropped from the result below.

        Parameters:
            query: The request's query string, one value per key.

        Returns:
            The clauses, keyed by field and subgroup. A field/subgroup carrying
            nothing but a qtype and a unit is omitted, since it constrains
            nothing on its own.
        """
        family_group_mapping: dict[tuple[slug.Family, int], list[tuple[slug.Info, str]]] = defaultdict(list)

        for slug_name, value in query.items():
            slug_info = self._slug_map.get_info_for_search_slug(slug_name, value)
            if slug_info:
                family_group_mapping[slug_info.family, slug_info.subgroup].append((slug_info, value))
                self._session_info.add_search_slug(slug_name, slug_info)

        # Only keep the family/subgroup if there is something there besides QTYPE and UNIT
        result: SearchSlugInfo = defaultdict(dict)
        for (family, subgroup), slug_info_value_list in family_group_mapping.items():
            family_types = {slug_info.family_type for (slug_info, _) in slug_info_value_list}
            if family_types.difference((FamilyType.QTYPE, FamilyType.UNIT)):
                result[family][subgroup] = SearchClause.from_slug_list(slug_info_value_list)
        return result

    @staticmethod
    def get_metadata_slug_info(slugs: list[str], slug_map: slug.ToInfoMap,
                               session_info: Any | None = None) -> MetadataSlugInfo:
        """
        This returns a map from the slugs that appear in the list of strings to the Info for that slug,
        provided that the info exists.
        """
        result: MetadataSlugInfo = {}
        for slug_name in slugs:
            slug_info = slug_map.get_info_for_column_slug(slug_name)
            if slug_info:
                assert slug_info.family
                result[slug_info.family] = slug_info
                if session_info:
                    session_info.add_metadata_slug(slug_name, slug_info)

        return result

    def __format_search_value(self, value: str | None) -> str:
        """Render one search value for the report.

        Parameters:
            value: The value, or None for an absent half of a range.

        Returns:
            The rendered value: marked up and escaped in HTML mode, quoted in
            text mode, and a dash or a tilde where the value is None.
        """
        if self._uses_html:
            if value is None:
                return Markup('&ndash;')
            else:
                return self.safe_format('"<samp>{}</samp>"', value)
        else:
            return '~' if value is None else '"' + value + '"'

    def __get_postscript(self, flags: slug.Flags) -> str:
        """Render a clause's flags as the trailing note on its report line.

        Parameters:
            flags: What the slug map noticed about the term's slugs.

        Returns:
            The note, empty when there are no flags.
        """
        if not flags:
            return ''
        elif self._uses_html:
            return self.safe_format(' <span class="text-danger">({})</span>', flags.pretty_print())
        else:
            return f' **{flags.pretty_print()}**'

    def safe_format(self, format_string: str, *args: Any) -> str:
        """Format a literal template, escaping each argument as it is substituted.

        Parameters:
            format_string: The template, which callers pass as a literal.
            *args: The values to substitute, escaped unless they are already
                marked as HTML.

        Returns:
            The formatted text.
        """
        return cast(str, self._session_info.safe_format(format_string, *args))

