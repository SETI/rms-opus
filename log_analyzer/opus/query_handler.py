import operator
import urllib
import urllib.parse
from collections import defaultdict
from enum import Enum, auto
from functools import reduce
from typing import Dict, Tuple, List, Optional, Any, cast

from markupsafe import Markup

from opus import slug as slug

SearchSlugInfo = Dict[slug.Family, List[Tuple[slug.Info, str]]]
ColumnSlugInfo = Dict[slug.Family, slug.Info]


class State(Enum):
    RESET = auto()
    SEARCHING = auto()
    FETCHING = auto()


class QueryHandler:
    DEFAULT_SORT_ORDER = 'time1'
    _session_info: Any  # can't handle circular imports.  :-(
    _slug_map: slug.ToInfoMap
    _default_column_slug_info: ColumnSlugInfo
    _uses_html: bool

    _previous_search_slug_info: SearchSlugInfo  # map from family to List[(Slug.Info, Value)]
    _previous_column_slug_info: Optional[ColumnSlugInfo]  # map from raw slug to Slug.Info
    _previous_pages: List[str]  # previous page.  Two entries for browse and cart
    _previous_startobss: List[str]  # previous start observation.  Two entries for browse and cart
    _previous_sort_order: str  # sort order
    _previous_state: State

    def __init__(self, session_info: Any, slug_map: slug.ToInfoMap, default_column_slug_info: ColumnSlugInfo,
                 uses_html: bool):
        self._session_info = session_info
        self._slug_map = slug_map
        self._default_column_slug_info = default_column_slug_info
        self._uses_html = uses_html
        self.__reset()

    def __reset(self) -> None:
        self._previous_search_slug_info = {}
        self._previous_column_slug_info = None  # handled specially by get_column_slug_info
        self._previous_sort_order = self.DEFAULT_SORT_ORDER
        self._previous_pages = ['', '']
        self._previous_startobss = ['', '']
        self._previous_state = State.RESET

    def handle_query(self, query: Dict[str, str], query_type: str) -> Tuple[List[str], Optional[str]]:
        assert query_type in ['data', 'images', 'result_count', 'dataimages']

        result: List[str] = []

        if query_type == 'result_count':
            uses_columns, uses_pages, uses_sort, current_state = False, False, False, State.SEARCHING
        elif query_type == 'data' or query_type == 'dataimages':
            uses_columns, uses_pages, uses_sort, current_state = True, True, True, State.FETCHING
        else:  # images
            uses_columns, uses_pages, uses_sort, current_state = False, True, True, State.FETCHING

        previous_state = self._previous_state
        if current_state != previous_state:
            if previous_state == State.RESET:
                result.append('Begin New Search')
            if (previous_state, current_state) == (State.FETCHING, State.SEARCHING):
                result.append('Refining Previous Search')

        search_slug_info: SearchSlugInfo = defaultdict(list)
        for slug, value in query.items():
            slug_info = self._slug_map.get_info_for_search_slug(slug)
            if slug_info:
                family = slug_info.family
                search_slug_info[family].append((slug_info, value))
                self._session_info.add_search_slug(slug, slug_info)

        if uses_columns:
            columns_query = query.get('cols')
            if columns_query:
                column_slug_info = self.get_column_slug_info(columns_query.split(','),
                                                             self._slug_map, self._session_info)
            else:
                column_slug_info = self._default_column_slug_info
        else:
            column_slug_info = {}

        sort_order = query.get('order', self.DEFAULT_SORT_ORDER)
        page = query.get('page', '')
        startobs = query.get('startobs', '')

        self.__handle_search_info(self._previous_search_slug_info, search_slug_info, result)
        self._previous_search_slug_info = search_slug_info

        if uses_columns:
            self.__get_column_info(self._previous_column_slug_info, column_slug_info, result)
            self._previous_column_slug_info = column_slug_info

        if uses_sort:
            self.__get_sort_order_info(self._previous_sort_order, sort_order, result)
            self._previous_sort_order = sort_order

        if uses_pages:
            assert current_state == State.FETCHING
            if page:
                page_type, info, previous_info = 'Page', page, self._previous_pages
            elif startobs:
                page_type, info, previous_info = 'Starting observation', startobs, self._previous_startobss
            else:
                page_type, info, previous_info = 'Page', '???', ['???', '???']
            is_browsing = query.get('view') == 'browse'
            browse_or_cart = 'Browse' if is_browsing else 'Cart'
            if current_state != previous_state:
                viewed = 'Table' if query.get('browse') == 'data' else 'Gallery'
                result.append(f'View {viewed}: {browse_or_cart} {page_type} {info}')
            else:
                self.__get_page_info(f'{browse_or_cart} {page_type}', previous_info[is_browsing], info, result)
            previous_info[is_browsing] = info

        self._previous_state = current_state

        url: Optional[str] = None
        if result and self._uses_html:
            query.pop('reqno', None)  # Remove if there, but okay if not
            if query_type != 'result_count':
                query['view'] = 'browse'
                query['browse'] = 'gallery'
            url = self.safe_format('/opus/#/{}', urllib.parse.urlencode(query, False))

        if result and query_type != 'result_count':
            self._session_info.fetched_gallery()

        return result, url

    def __handle_search_info(self, old_info: SearchSlugInfo, new_info: SearchSlugInfo, result: List[str]) -> None:
        all_search_families = set(old_info.keys()).union(new_info.keys())

        if not new_info:
            if old_info:
                result.append('Reset Search')
            return

        removed_searches: List[str] = []
        added_searches: List[str] = []
        changed_searches: List[str] = []

        for family in sorted(all_search_families):
            if family not in new_info:
                self.__handle_search_remove(removed_searches, family)
            elif family not in old_info:
                self.__handle_search_add(added_searches, family, new_info)
            else:
                self.__handle_search_change(changed_searches, family, old_info, new_info)

        result.extend(removed_searches)
        result.extend(added_searches)
        result.extend(changed_searches)

    def __handle_search_remove(self, result: List[str], family: slug.Family) -> None:
        self._session_info.changed_search_slugs()
        result.append(f'Remove Search: "{family.label}"')

    def __handle_search_add(self, result: List[str], family: slug.Family, new_info: SearchSlugInfo) -> None:
        self._session_info.changed_search_slugs()
        if family.is_singleton():
            assert len(new_info[family]) == 1
            slug_info, value = new_info[family][0]
            assert family.label == slug_info.label
            postscript = self.__get_postscript(slug_info.flags)  # is html-aware
            if self._uses_html:
                result.append(self.safe_format('Add Search: "{}" = <mark><ins>{}</ins></mark>{}',
                                               family.label, self.__format_search_value(value), postscript))
            else:
                result.append(f'Add Search:    "{family.label}" = "{value}"{postscript}')
        else:
            new_min, new_max, new_qtype, flags = self.__parse_search_family(new_info[family])
            postscript = self.__get_postscript(flags)  # is html-aware
            if self._uses_html:
                def always_mark(which: str, value: Optional[str]) -> str:
                    return self.safe_format('<mark><ins>{}:{}</ins></mark>', which, self.__format_search_value(value))

                result.append(self.safe_format('Add Search: &quot;{}&quot; = ({}, {}, {}){}',
                                               family.label,
                                               always_mark(family.min, new_min),
                                               always_mark(family.max, new_max),
                                               always_mark('qtype', new_qtype),
                                               postscript))
            else:
                new_value = (f'({family.min.upper()}:{self.__format_search_value(new_min)},'
                             f' {family.max.upper()}:{self.__format_search_value(new_max)}, '
                             f'QTYPE:{self.__format_search_value(new_qtype)})')
                result.append(f'Add Search:    "{family.label}" = {new_value}{postscript}')

    def __handle_search_change(self, result: List[str], family: slug.Family, old_info: SearchSlugInfo,
                               new_info: SearchSlugInfo) -> None:
        if family.is_singleton():
            assert len(old_info[family]) == 1
            assert len(new_info[family]) == 1
            old_slug_info, old_value = old_info[family][0]
            new_slug_info, new_value = new_info[family][0]
            self.__slug_value_change(new_slug_info.label, old_value, new_value, result)
        else:
            old_min, old_max, old_qtype, _ = self.__parse_search_family(old_info[family])
            new_min, new_max, new_qtype, _ = self.__parse_search_family(new_info[family])
            if (old_min, old_max, old_qtype) == (new_min, new_max, new_qtype):
                pass
            elif self._uses_html:
                def maybe_mark(tag: str, old: Optional[str], new: Optional[str]) -> str:
                    fmt = '{}:{}' if old == new else '<mark>{}:{}</mark>'
                    return self.safe_format(fmt, tag, self.__format_search_value(new))

                result.append(
                    self.safe_format('Change Search: &quot;{}&quot;: ({}, {}, {})', family.label,
                                     maybe_mark(family.min, old_min, new_min),
                                     maybe_mark(family.max, old_max, new_max),
                                     maybe_mark('qtype', old_qtype, new_qtype)))
            else:
                min_name = family.min if old_min == new_min else family.min.upper()
                max_name = family.max if old_max == new_max else family.max.upper()
                qtype_name = 'qtype' if old_qtype == new_qtype else 'QTYPE'
                new_value = (f'({min_name}:{self.__format_search_value(new_min)},'
                             f' {max_name}:{self.__format_search_value(new_max)},'
                             f' {qtype_name}:{self.__format_search_value(new_qtype)})')
                result.append(f'Change Search: "{family.label}" = {new_value}')

    def __get_column_info(self, old_info: Optional[ColumnSlugInfo], new_info: ColumnSlugInfo,
                          result: List[str]) -> None:
        if old_info is None:
            new_column_families = set(new_info.keys())
            if new_column_families == set(self._default_column_slug_info.keys()):
                return
            column_labels = [new_info[family].label for family in sorted(new_column_families)]
            quoted_column_labels = self._session_info.quote_and_join_list(sorted(column_labels))
            result.append(f'Starting with Selected Metadata: {quoted_column_labels}')
            return

        old_column_families = set(old_info.keys())
        new_column_families = set(new_info.keys())
        if new_column_families == old_column_families:
            return
        if new_column_families == set(self._default_column_slug_info.keys()):
            result.append('Reset Selected Metadata')
            return
        self._session_info.changed_column_slugs()
        all_column_families = old_column_families.union(new_column_families)
        added_columns, removed_columns = [], []
        for family in sorted(all_column_families):
            old_slug_info = old_info.get(family)
            new_slug_info = new_info.get(family)
            if old_slug_info and not new_slug_info:
                removed_columns.append(f'Remove Selected Metadata: "{old_slug_info.label}"')
            elif new_slug_info and not old_slug_info:
                postscript = self.__get_postscript(new_slug_info.flags)
                if not self._uses_html:
                    added_columns.append(f'Add Selected Metadata:    "{new_slug_info.label}"{postscript}')
                else:
                    added_columns.append(
                        self.safe_format('Add Selected Metadata: "{}"{}', new_slug_info.label, postscript))

        result.extend(removed_columns)
        result.extend(added_columns)

    def __get_page_info(self, what: str, old_page: str, new_page: str, result: List[str]) -> None:
        if old_page != new_page and new_page:
            if old_page:
                if self._uses_html:
                    result.append(self.safe_format('Change {}: {} &rarr; {}', what.title(), old_page, new_page))
                else:
                    result.append(f'Change {what.title()}: {old_page} -> {new_page}')
            else:
                if self._uses_html:
                    result.append(self.safe_format('Go To {}: {}', what.title(), new_page))
                else:
                    result.append(f'Go To {what.title()}: {new_page}')

    def __get_sort_order_info(self, old_sort_order: str, new_sort_order: str, result: List[str]) -> None:
        if old_sort_order != new_sort_order:
            columns = new_sort_order.split(',')
            result.append(f'Change Sort Order:')
            for column in columns:
                if column.startswith('-'):
                    order = 'Descending'
                    column = column[1:]
                else:
                    order = 'Ascending'
                slug_info = self._slug_map.get_info_for_column_slug(column)
                assert slug_info
                result.append(f'        "{slug_info.label}" ({order})')

    def __slug_value_change(self, name: str, old_value: str, new_value: str, result: List[str]) -> None:
        old_value_set = set(old_value.split(','))
        new_value_set = set(new_value.split(','))
        if old_value_set == new_value_set:
            return
        if self._uses_html:
            marked_changes: List[str] = []
            for value in sorted(old_value_set.union(new_value_set)):
                formatted_value = self.__format_search_value(value)
                if value not in old_value_set:
                    marked_changes.append(self.safe_format('<mark><ins>{}</ins></mark>', formatted_value))
                elif value not in new_value_set:
                    marked_changes.append(self.safe_format('<mark><del>{}</del></mark>', formatted_value))
                else:
                    marked_changes.append(Markup(formatted_value))
            joined_values = Markup(',').join(marked_changes)
            result.append(self.safe_format('Change Search: &quot;{}&quot; = {}', name, joined_values))
        elif old_value_set.intersection(new_value_set):
            change_list: List[Tuple[str, str]] = []
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

    @staticmethod
    def get_column_slug_info(slugs: List[str], slug_map: slug.ToInfoMap,
                             session_info: Optional[Any] = None) -> ColumnSlugInfo:
        """
        This returns a map from the slugs that appear in the list of strings to the Info for that slug,
        provided that the info exists.
        """
        result: ColumnSlugInfo = {}
        for slug in slugs:
            slug_info = slug_map.get_info_for_column_slug(slug)
            if slug_info:
                assert slug_info.family
                result[slug_info.family] = slug_info
                if session_info:
                    session_info.add_column_slug(slug, slug_info)

        return result

    def __format_search_value(self, value: Optional[str]) -> str:
        if self._uses_html:
            if value is None:
                return Markup('&ndash;')
            else:
                return self.safe_format('&quot;<samp>{}</samp>&quot;', value)
        else:
            return '~' if value is None else '"' + value + '"'

    def __get_postscript(self, flags: slug.Flags) -> str:
        if not flags:
            return ''
        elif self._uses_html:
            return self.safe_format(' <span class="text-danger">({})</span>', flags.pretty_print())
        else:
            return f' **{flags.pretty_print()}**'

    def __parse_search_family(self, pairs: List[Tuple[slug.Info, str]]) -> \
            Tuple[Optional[str], Optional[str], Optional[str], slug.Flags]:
        mapping = {slug_info.family_type: value for slug_info, value in pairs}  # family_type to value
        return (
            mapping.get(slug.FamilyType.MIN), mapping.get(slug.FamilyType.MAX), mapping.get(slug.FamilyType.QTYPE),
            reduce(operator.or_, (slug_info.flags for (slug_info, _) in pairs))
        )

    def safe_format(self, format_string: str, *args: Any) -> str:
        return cast(str, self._session_info.safe_format(format_string, *args))

