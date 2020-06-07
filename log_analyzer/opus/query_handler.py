import operator
import urllib
import urllib.parse
from collections import defaultdict
from enum import Enum, auto
from functools import reduce
from typing import Dict, Tuple, List, Optional, Any, cast, NamedTuple, Sequence

from markupsafe import Markup

from log_entry import LogEntry
from opus import slug as slug
from opus.configuration_flags import Action
from opus.slug import FamilyType, Info


class SearchClause(NamedTuple):
    single_value: Optional[str]
    min_value: Optional[str]
    max_value: Optional[str]
    qtype: Optional[str]
    unit: Optional[str]
    flags: slug.Flags

    @staticmethod
    def from_slug_list(pairs: List[Tuple[slug.Info, str]]) -> 'SearchClause':
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
        return self.qtype is None and self.unit is None


SearchSlugInfo = Dict[slug.Family, Dict[int, SearchClause]]
MetadataSlugInfo = Dict[slug.Family, slug.Info]


class State(Enum):
    RESET = auto()
    SEARCHING = auto()
    FETCHING = auto()


class QueryHandler:
    DEFAULT_SORT_ORDER = 'time1,opusid'
    _session_info: Any  # can't handle circular imports.  :-(
    _slug_map: slug.ToInfoMap
    _default_metadata_slug_info: MetadataSlugInfo
    _uses_html: bool

    _previous_search_slug_info: SearchSlugInfo  # map from family to List[(Slug.Info, Value)]
    _previous_metadata_slug_info: Optional[MetadataSlugInfo]  # map from raw slug to Slug.Info
    _previous_pages: List[str]  # previous page.  Two entries for browse and cart
    _previous_startobss: List[str]  # previous start observation.  Two entries for browse and cart
    _previous_sort_order: str  # sort order
    _previous_state: State

    def __init__(self, session_info: Any, slug_map: slug.ToInfoMap, default_metadata_slug_info: MetadataSlugInfo,
                 uses_html: bool):
        self._session_info = session_info
        self._slug_map = slug_map
        self._default_metadata_slug_info = default_metadata_slug_info
        self._uses_html = uses_html
        self.__reset()

    def __reset(self) -> None:
        self._previous_search_slug_info = {}
        self._previous_metadata_slug_info = None  # handled specially by get_metadata_slug_info
        self._previous_sort_order = self.DEFAULT_SORT_ORDER
        self._previous_pages = ['', '']
        self._previous_startobss = ['', '']
        self._previous_browses = ['', '']
        self._previous_state = State.RESET

    def create_widget(self, _entry: LogEntry, _query: Dict[str, str], widget: str) -> Tuple[List[str], Optional[str]]:
        family_info = self._slug_map.get_family_info_for_widget(widget)
        if family_info:
            self._session_info.register_widget(family_info)
            return [f'Create Widget "{family_info.label}"'], None
        else:
            return [], None

    def handle_query(self, _entry: LogEntry, query: Dict[str, str], query_type: str) -> Tuple[List[str], Optional[str]]:
        assert query_type in ['data', 'images', 'result_count', 'dataimages']

        result: List[str] = []

        if query_type == 'result_count':
            uses_metadata, uses_pages, uses_sort, current_state = False, False, False, State.SEARCHING
        elif query_type == 'data' or query_type == 'dataimages':
            uses_metadata, uses_pages, uses_sort, current_state = True, True, True, State.FETCHING
        else:  # images
            uses_metadata, uses_pages, uses_sort, current_state = False, True, True, State.FETCHING

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

        tentative_flag: Optional[Action] = None
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
            tentative_flag = {
                ("Browse", "Table"): Action.VIEWED_BROWSE_TAB_AS_TABLE,
                ("Browse", "Gallery"): Action.VIEWED_BROWSE_TAB_AS_GALLERY,
                ("Cart", "Table"): Action.VIEWED_CART_TAB_AS_TABLE,
                ("Cart", "Gallery"): Action.VIEWED_CART_TAB_AS_GALLERY,
            }[browse_or_cart, viewed]

            if current_state != previous_state or current_browse != previous_browse:
                result.append(f'View {browse_or_cart} {viewed}: {page_type} {info}')
            elif info:
                what = f'{browse_or_cart} {viewed} {page_type}'
                limit = query.get('limit', '???')
                result.append(f'Fetch {what.title()} {info} Limit {limit}')

            previous_info[is_browsing] = info
            self._previous_browses[is_browsing] = current_browse

        self._previous_state = current_state

        url: Optional[str] = None
        if result and self._uses_html:
            query.pop('reqno', None)  # Remove if there, but okay if not
            url = self.safe_format('/opus/#/{}', urllib.parse.urlencode(query, False))

        if result and query_type != 'result_count':
            self._session_info.fetched_gallery()

        if result and query_type == 'dataimages' and tentative_flag:
            self._session_info.register_info_flags(tentative_flag)

        return result, url

    def __handle_search_info(self, old_info: SearchSlugInfo, new_info: SearchSlugInfo, result: List[str]) -> None:
        """Handles info for the contents of search slugs"""
        if not new_info:
            if old_info:
                result.append('Reset Search')
            return

        all_search_families = set(old_info.keys()).union(new_info.keys())

        result_length = len(result)
        for family in sorted(all_search_families):
            family_result_length = len(result)
            if family not in new_info:
                result.append(f'Remove Search: "{family.label}"')
            else:
                self.__handle_search_info_for_family(family, old_info, new_info, result)
            if family_result_length != len(result):
                self._session_info.register_search_slug(family)
        if result_length != len(result):
            self._session_info.changed_search_slugs()

    def __handle_search_info_for_family(self, family: slug.Family, old_info: SearchSlugInfo, new_info: SearchSlugInfo,
                                        result: List[str]) -> None:
        is_add = family not in old_info

        def pull_data(info: SearchSlugInfo) -> List[SearchClause]:
            return [info[family][subgroup] for subgroup in sorted(info[family].keys())]

        old_data = [] if is_add else pull_data(old_info)
        new_data = pull_data(new_info)

        fields_info: Sequence[Tuple[str, str]]
        if family.is_singleton():
            fields_info = (('value', 'single_value'), ('qtype', 'qtype'), ('unit', 'unit'))
        else:
            fields_info = ((family.min, 'min_value'), (family.max, 'max_value'), ('qtype', 'qtype'), ('unit', 'unit'))

        if len(old_data) == len(new_data):
            for i, old, new in ((i, old, new) for i, (old, new) in enumerate(zip(old_data, new_data)) if old != new):
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

    def __show_search_change_add(self, family: slug.Family, fields_info: Sequence[Tuple[str, str]],
                                 new_data: List[SearchClause], index: int,
                                 result: List[str], *,
                                 action: str = 'Add Search') -> None:
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
                joined_info = Markup(', ').join(
                    self.safe_format('<mark><ins>{}:{}</ins></mark>', name, self.__format_search_value(value), )
                    for (name, value) in fields)
                result.append(self.safe_format('{}: "{}" = ({}){}', action, label, joined_info, postscript))
            else:
                joined_info = ", ".join(
                    f'{name.upper()}:{self.__format_search_value(value)}' for (name, value) in fields)
                result.append(f'{action}:{space} "{label}" = ({joined_info}){postscript}')

    def __show_search_change_remove(self, family: slug.Family, fields_info: Sequence[Tuple[str, str]],
                                    old_data: List[SearchClause], new_data: List[SearchClause],
                                    index: int,
                                    result: List[str]) -> None:
        length = len(old_data)
        label = family.label if length == 1 else f'{family.label} #{index + 1}'
        result.append(f'Remove Search Term: "{label}"')
        for i in range(len(new_data)):
            self.__show_search_change_add(family, fields_info, new_data, i, result, action="- Current Search Term")

    def __show_unexpected_change(self, family: slug.Family, fields_info: Sequence[Tuple[str, str]],
                                 new_data: List[SearchClause],
                                 result: List[str]) -> None:
        result.append(f'Complex Change for Search Term: "{family.label}"')
        for i in range(len(new_data)):
            self.__show_search_change_add(family, fields_info, new_data, i, result, action="- Current Search Term")

    def __show_search_change_delta(self, family: slug.Family, fields_info: Sequence[Tuple[str, str]],
                                   old_list: List[SearchClause], new_list: List[SearchClause], index: int,
                                   result: List[str]) -> None:
        old_values, new_values = old_list[index], new_list[index]
        label = family.label if index == 0 and len(old_list) == 1 else f"{family.label} #{index + 1}"

        if family.is_singleton() and old_values.is_value_only() and new_values.is_value_only():
            self.__slug_value_change(label, old_values.single_value or '', new_values.single_value or '', result)
        else:
            fields = [(name, getattr(old_values, attr), getattr(new_values, attr))
                      for name, attr in fields_info]
            if self._uses_html:
                def maybe_mark(tag: str, old: Optional[str], new: Optional[str]) -> str:
                    fmt = '{}:{}' if old == new else '<mark>{}:{}</mark>'
                    return self.safe_format(fmt, tag, self.__format_search_value(new))

                joined_info = Markup(', ').join(maybe_mark(tag, old, new) for (tag, old, new) in fields)
                result.append(self.safe_format('Change Search: "{}": ({})', label, joined_info))
            else:
                def maybe_mark(tag: str, old: Optional[str], new: Optional[str]) -> str:
                    return f'{tag if old == new else tag.upper()}:{self.__format_search_value(new)}'

                joined_info = ', '.join(maybe_mark(tag, old, new) for (tag, old, new) in fields)
                result.append(f'Change Search: "{label}" = ({joined_info})')

    def __get_metadata_info(self, old_info: Optional[MetadataSlugInfo], new_info: MetadataSlugInfo,
                            result: List[str]) -> None:

        new_metadata_families = set(new_info.keys())
        old_metadata_families = set(new_info.keys()) if old_info is not None else set()

        if old_info is None:
            if new_metadata_families == set(self._default_metadata_slug_info.keys()):
                return
            metadata_labels = [new_info[family].label for family in sorted(new_metadata_families)]
            quoted_metadata_labels = self._session_info.quote_and_join_list(sorted(metadata_labels))
            for family in new_metadata_families:
                self._session_info.register_metadata_slug(family)
            result.append(f'Starting with Selected Metadata: {quoted_metadata_labels}')
            return

        if new_metadata_families == old_metadata_families:
            return
        if new_metadata_families == set(self._default_metadata_slug_info.keys()):
            result.append('Reset Selected Metadata')
            return
        all_metadata_families = old_metadata_families.union(new_metadata_families)
        added_metadata: List[str] = []
        removed_metadata: List[str] = []
        for family in sorted(all_metadata_families):
            old_length = len(removed_metadata) + len(added_metadata)
            old_slug_info = old_info.get(family)
            new_slug_info = new_info.get(family)
            if old_slug_info and not new_slug_info:
                removed_metadata.append(f'Remove Selected Metadata: "{old_slug_info.label}"')
            elif new_slug_info and not old_slug_info:
                postscript = self.__get_postscript(new_slug_info.flags)
                if not self._uses_html:
                    added_metadata.append(f'Add Selected Metadata:    "{new_slug_info.label}"{postscript}')
                else:
                    added_metadata.append(
                        self.safe_format('Add Selected Metadata: "{}"{}', new_slug_info.label, postscript))
            if old_length != len(removed_metadata) + len(added_metadata):
                self._session_info.register_metadata_slug(family)
                self._session_info.changed_metadata_slugs()

        result.extend(removed_metadata)
        result.extend(added_metadata)

    def __get_sort_order_info(self, old_sort_order: str, new_sort_order: str, result: List[str]) -> None:
        if old_sort_order != new_sort_order:
            sort_list: List[Info] = []
            columns = new_sort_order.split(',')
            result.append(f'Change Sort Order:')
            for column in columns:
                if column.startswith('-'):
                    order = 'Descending'
                    column = column[1:]
                else:
                    order = 'Ascending'
                slug_info: Optional[Info] = self._slug_map.get_info_for_column_slug(column)
                assert slug_info
                sort_list.append(slug_info)
                result.append(f'        "{slug_info.label}" ({order})')

            self._session_info.register_sort_slugs_changed(sort_list)
            self._session_info.register_info_flags(Action.CHANGED_SORT_ORDER)

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
            result.append(self.safe_format('Change Search: "{}" = {}', name, joined_values))
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

    def __get_search_slug_info(self, query: Dict[str, str]) -> SearchSlugInfo:
        family_group_mapping: Dict[Tuple[slug.Family, int], List[Tuple[slug.Info, str]]] = defaultdict(list)

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
    def get_metadata_slug_info(slugs: List[str], slug_map: slug.ToInfoMap,
                               session_info: Optional[Any] = None) -> MetadataSlugInfo:
        """
        This returns a map from the slugs that appear in the list of strings to the Info for that slug,
        provided that the info exists.
        """
        result: MetadataSlugInfo = {}
        for slug in slugs:
            slug_info = slug_map.get_info_for_column_slug(slug)
            if slug_info:
                assert slug_info.family
                result[slug_info.family] = slug_info
                if session_info:
                    session_info.add_metadata_slug(slug, slug_info)

        return result

    def __format_search_value(self, value: Optional[str]) -> str:
        if self._uses_html:
            if value is None:
                return Markup('&ndash;')
            else:
                return self.safe_format('"<samp>{}</samp>"', value)
        else:
            return '~' if value is None else '"' + value + '"'

    def __get_postscript(self, flags: slug.Flags) -> str:
        if not flags:
            return ''
        elif self._uses_html:
            return self.safe_format(' <span class="text-danger">({})</span>', flags.pretty_print())
        else:
            return f' **{flags.pretty_print()}**'

    def safe_format(self, format_string: str, *args: Any) -> str:
        return cast(str, self._session_info.safe_format(format_string, *args))

