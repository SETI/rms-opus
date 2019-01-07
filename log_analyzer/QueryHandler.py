import operator
from collections import defaultdict
from enum import Enum, auto
from functools import reduce
from typing import Dict, Tuple, List, Optional, cast, ClassVar, Any

import SessionInfo
import Slug

SearchSlugInfo = Dict[Slug.Family, List[Tuple[Slug.Info, str]]]
ColumnSlugInfo = Dict[Slug.Family, Slug.Info]

class State(Enum):
    RESET = auto()
    SEARCHING = auto()
    FETCHING = auto()


class QueryHandler:
    DEFAULT_SORT_ORDER = 'time1'

    _slug_map: Slug.ToInfoMap
    _default_column_slug_info: ColumnSlugInfo

    _all_search_slugs: ClassVar[Dict[str, Slug.Info]] = {}
    _all_column_slugs: ClassVar[Dict[str, Slug.Info]] = {}

    _is_reset: bool

    _previous_search_slug_info: SearchSlugInfo   # map from family to List[(Slug.Info, Value)]
    _previous_column_slug_info: ColumnSlugInfo   # map from raw slug to Slug.Info
    _previous_page: str                          # previous page
    _previous_sort_order: str                    # sort order
    _previous_state: State

    def __init__(self, slug_map: Slug.ToInfoMap, default_column_slug_info: ColumnSlugInfo):
        self._slug_map = slug_map
        self._default_column_slug_info = default_column_slug_info
        self.reset()

    @property
    @classmethod
    def all_search_slugs(cls) -> Dict[str, Slug.Info]:
        return cls._all_search_slugs

    @property
    @classmethod
    def all_column_slugs(cls) -> Dict[str, Slug.Info]:
        return cls._all_column_slugs

    def reset(self) -> None:
        self._previous_query_type = None
        self._previous_search_slug_info = {}
        self._previous_column_slug_info = self._default_column_slug_info
        self._previous_sort_order = self.DEFAULT_SORT_ORDER
        self._previous_page = ''
        self._previous_state = State.RESET

    def handle_query(self, query: Dict[str, str], query_type: str) -> List[str]:
        assert query_type in ['data', 'images', 'result_count']

        result: List[str] = []

        uses_columns = query_type == 'data'
        uses_pages = query_type != 'result_count'
        uses_sort = uses_pages   # For now the same, but this may change in the future

        current_state = State.SEARCHING if query_type == 'result_count' else State.FETCHING

        previous_state = self._previous_state
        if current_state != previous_state:
            if previous_state == State.RESET:
                result.append('Begin New Search')
            if (previous_state, current_state) == (State.FETCHING, State.SEARCHING):
                result.append('Refining Previous Search')

        search_slug_info: Dict[Slug.Family, List[Tuple[Slug.Info, str]]] = defaultdict(list)
        for slug, value in query.items():
            slug_info = self._slug_map.get_info_for_search_slug(slug)
            if slug_info:
                family = slug_info.family
                search_slug_info[family].append((slug_info, value))
                self._all_search_slugs[slug] = slug_info

        if uses_columns:
            columns_query = query.get('cols')
            if columns_query:
                column_slug_info = self.get_column_slug_info(columns_query.split(','), self._slug_map, record=True)
            else:
                column_slug_info = self._default_column_slug_info
        else:
            column_slug_info = {}

        sort_order = query.get('order', self.DEFAULT_SORT_ORDER)
        page = query.get('page', '')

        self.__get_search_info(self._previous_search_slug_info, search_slug_info, result)
        self._previous_search_slug_info = search_slug_info

        if uses_columns:
            self.__get_column_info(self._previous_column_slug_info, column_slug_info, result)
            self._previous_column_slug_info = column_slug_info
        if uses_sort:
            self.__get_sort_order_info(self._previous_sort_order, sort_order, result)
            self._previous_sort_order = sort_order

        if uses_pages:
            assert current_state == State.FETCHING
            if current_state != previous_state:
                viewed = 'Table' if query.get('browse') == 'data' else 'Gallery'
                result.append(f'View {viewed}: Page {page or "???"}')
            else:
                 self.__get_page_info(self._previous_page, page, result)
            self._previous_page = page

        self._previous_state = current_state
        return result

    def __get_search_info(self, old_info: SearchSlugInfo, new_info: SearchSlugInfo, result: List[str]) -> None:
        all_search_families = set(old_info.keys()).union(new_info.keys())

        def parse_family(pairs: List[Tuple[Slug.Info, str]]) -> Tuple[
                  Optional[str], Optional[str], Optional[str], Slug.Flags]:
            mapping = {slug_info.family_type: value for slug_info, value in pairs}  # family_type to value
            return (
                mapping.get(Slug.FamilyType.MIN), mapping.get(Slug.FamilyType.MAX), mapping.get(Slug.FamilyType.QTYPE),
                reduce(operator.or_, (slug_info.flags for (slug_info, _) in pairs))
            )

        def pprint(value: Optional[str]) -> str:
            if value is None:
                return '~'
            return '"' + value + '"'

        if not new_info:
            if old_info:
                result.append('Reset Search')
            return

        removed_searches: List[str] = []
        added_searches: List[str] = []
        changed_searches: List[str] = []
        for family in sorted(all_search_families):
            if family not in new_info:
                removed_searches.append(f'Remove Search: "{family.label}"')
            elif family not in old_info:
                if family.is_singleton():
                    assert len(new_info[family]) == 1
                    slug_info, value = new_info[family][0]
                    assert family.label == slug_info.label
                    postscript = f' **{slug_info.flags.pretty_print()}**' if slug_info.flags else ''
                    added_searches.append(f'Add Search:    "{family.label}" = "{value}"{postscript}')
                else:
                    new_min, new_max, new_qtype, flags = parse_family(new_info[family])
                    new_value = (f'({family.min.upper()}:{pprint(new_min)},'
                                 f' {family.max.upper()}:{pprint(new_max)}, '
                                 f'QTYPE:{pprint(new_qtype)})')
                    postscript = f' **{flags.pretty_print()}**' if flags else ''
                    added_searches.append(f'Add Search:    "{family.label}" = {new_value}{postscript}')
            else:
                if family.is_singleton():
                    assert len(old_info[family]) == 1
                    assert len(new_info[family]) == 1
                    old_slug_info, old_value = old_info[family][0]
                    new_slug_info, new_value = new_info[family][0]
                    self.__slug_value_change(new_slug_info.label, old_value, new_value, changed_searches)
                else:
                    old_min, old_max, old_qtype, _ = parse_family(old_info[family])
                    new_min, new_max, new_qtype, _ = parse_family(new_info[family])
                    if (old_min, old_max, old_qtype) != (new_min, new_max, new_qtype):
                        min_name = family.min if old_min == new_min else family.min.upper()
                        max_name = family.max if old_max == new_max else family.max.upper()
                        qtype_name = 'qtype' if old_qtype == new_qtype else 'QTYPE'
                        new_value = (f'({min_name}:{pprint(new_min)},' 
                                     f' {max_name}:{pprint(new_max)},' 
                                     f' {qtype_name}:{pprint(new_qtype)})')
                        changed_searches.append(f'Change Search: "{family.label}" = {new_value}')

        result.extend(removed_searches)
        result.extend(added_searches)
        result.extend(changed_searches)

    def __get_column_info(self, old_info: ColumnSlugInfo, new_info: ColumnSlugInfo, result: List[str]) -> None:
        old_column_families = set(old_info.keys())
        new_column_families = set(new_info.keys())
        if new_column_families == old_column_families:
            return
        if new_column_families == set(self._default_column_slug_info.keys()):
            result.append('Reset Columns')
            return
        all_column_families = old_column_families.union(new_column_families)
        added_columns, removed_columns = [], []
        for family in sorted(all_column_families):
            old_slug_info = old_info.get(family)
            new_slug_info = new_info.get(family)
            if old_slug_info and not new_slug_info:
                removed_columns.append(f'Remove Column: "{old_slug_info.label}"')
            elif new_slug_info and not old_slug_info:
                postscript = f' **{new_slug_info.flags.pretty_print()}**' if new_slug_info.flags else ''
                added_columns.append(f'Add Column:    "{new_slug_info.label}{postscript}"')
        result.extend(removed_columns)
        result.extend(added_columns)

    def __get_page_info(self, old_page: Optional[str], new_page: Optional[str], result: List[str]) -> None:
        if old_page != new_page and old_page and new_page:
            result.append(f'Change Page: {old_page} -> {new_page}')

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
            joined_old_value_set = SessionInfo.quote_and_join_list(sorted(old_value_set))
            joined_new_value_set = SessionInfo.quote_and_join_list(sorted(new_value_set))
            result.append(f'Change Search: "{name}" = {joined_old_value_set} -> {joined_new_value_set}')

    @classmethod
    def get_column_slug_info(cls, slugs: List[str], slug_map: Slug.ToInfoMap, record:bool = False) -> ColumnSlugInfo:
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
                if record:
                    cls._all_column_slugs[slug] = slug_info
        return result


