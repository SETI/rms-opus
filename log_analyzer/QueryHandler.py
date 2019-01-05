import operator
from collections import defaultdict
from functools import reduce
from typing import Dict, Tuple, List, Optional, cast, ClassVar, Any

import SessionInfo
import Slug

SEARCH_SLUG_INFO = Dict[Slug.Family, List[Tuple[Slug.Info, str]]]
COLUMN_SLUG_INFO = Dict[str, Slug.Info]


class QueryHandler:
    _slug_map: Any
    _default_column_slug_info: COLUMN_SLUG_INFO

    _all_search_slugs: ClassVar[Dict[str, Slug.Info]] = {}
    _all_column_slugs: ClassVar[Dict[str, Slug.Info]] = {}

    _is_reset: bool

    _previous_query_type: Optional[str]
    _previous_search_slug_info: SEARCH_SLUG_INFO   # map from family to List[(Slug.Info, Value)]
    _previous_column_slug_info: COLUMN_SLUG_INFO   # map from raw slug to Slug.Info
    _previous_page: Optional[str]  # previous page

    def __init__(self, slug_map: Slug.ToInfoMap, default_column_slug_info: COLUMN_SLUG_INFO):
        self._slug_map = slug_map
        self._default_column_slug_info = default_column_slug_info
        self.reset()

    @property
    @staticmethod
    def all_search_slugs() -> ClassVar[Dict[str, Slug.Info]]:
        return QueryHandler._all_search_slugs

    @property
    @staticmethod
    def all_column_slugs() -> ClassVar[Dict[str, Slug.Info]]:
        return QueryHandler._all_column_slugs

    def reset(self) -> None:
        self._is_reset = True
        self._previous_query_type = None
        self._previous_search_slug_info = {}
        self._previous_column_slug_info = self._default_column_slug_info
        self._previous_page = None

    def handle_query(self, query: Dict[str, str], query_type: str) -> List[str]:
        assert query_type in ['data', 'images', 'result_count']

        search_slug_info: Dict[Slug.Family, List[Tuple[Slug.Info, str]]] = defaultdict(list)
        for slug, value in query.items():
            slug_info = self._slug_map.get_info_for_search_slug(slug)
            if slug_info:
                family = cast(Slug.Family, slug_info.family)  # It can't be None for search slugs
                search_slug_info[family].append((slug_info, value))
                self._all_search_slugs[slug] = slug_info

        if query_type == 'data':
            columns_query = query.get('cols')
            if columns_query:
                column_slug_info = self.get_column_slug_info(columns_query.split(','), self._slug_map)
            else:
                column_slug_info = self._default_column_slug_info
            self._all_column_slugs.update(column_slug_info)
            page = query.get('page', None)

        else:
            column_slug_info = {}
            page = None

        result: List[str] = []

        if self._is_reset:
            viewed = 'Table' if query.get('browse') == 'data' else 'Gallery'
            result.append (f'View {viewed}')

        if query_type != self._previous_query_type:
            info = query_type.replace('_', ' ').title()
            result.append(f'Fetching {info}')
        self.__get_search_info(self._previous_search_slug_info, search_slug_info, result)
        if query_type == 'data':
            self.__get_column_info(self._previous_column_slug_info, column_slug_info, result)
            self.__get_page_info(self._previous_page, page, result)

        self._previous_query_type = query_type
        self._previous_search_slug_info = search_slug_info
        if query_type == 'data':
            self._previous_column_slug_info = column_slug_info
            self._previous_page = page
        self._is_reset = False


        return result

    def __get_search_info(self, old_info: SEARCH_SLUG_INFO, new_info: SEARCH_SLUG_INFO, result: List[str]) -> None:
        all_search_families = set(old_info.keys()).union(new_info.keys())

        def parse_family(pairs: List[Tuple[Slug.Info, str]]) -> Tuple[
                  Optional[str], Optional[str], Optional[str], Slug.Flags]:
            mapping = {slug_info.family_type: value for slug_info, value in pairs}  # family_type to value
            return (
                mapping.get(Slug.FamilyType.MIN), mapping.get(Slug.FamilyType.MAX), mapping.get(Slug.FamilyType.QTYPE),
                reduce(operator.or_, (slug_info.flags for (slug_info, _) in pairs))
            )

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
                    new_value = (f'({family.min.upper()}:"{new_min}", {family.max.upper()}:"{new_max}", '
                                 f'QTYPE:"{new_qtype}")')
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
                        new_value = f'({min_name}:"{new_min}", {max_name}:"{new_max}", {qtype_name}:"{new_qtype}")'
                        changed_searches.append(f'Change Search: "{family.label}" = {new_value}')

        result.extend(removed_searches)
        result.extend(added_searches)
        result.extend(changed_searches)

    def __get_column_info(self, old_info: COLUMN_SLUG_INFO, new_info: COLUMN_SLUG_INFO, result: List[str]) -> None:
        old_columns = set(old_info.keys())
        new_columns = set(new_info.keys())
        if new_columns == old_columns:
            return
        if new_columns == set(self._default_column_slug_info.keys()):
            result.append('Reset Columns')
            return
        all_columns = old_columns.union(new_columns)
        added_columns, removed_columns = [], []
        for column in sorted(all_columns):
            if column in new_columns and column not in old_columns:
                slug_info = new_info[column]
                postscript = f' **{slug_info.flags.pretty_print()}**' if slug_info.flags else ''
                added_columns.append(f'Add Column: "{slug_info.label}{postscript}"')
            elif column in old_columns and column not in new_info:
                slug_info = old_info[column]
                removed_columns.append(f'Remove Column: "{slug_info.label}"')
        result.extend(removed_columns)
        result.extend(added_columns)

    def __get_page_info(self, old_page: Optional[str], new_page: Optional[str], result: List[str]) -> None:
        if old_page != new_page and new_page is not None:
            result.append(f'Get Page: {new_page}')

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
            joined_old_value_set = SessionInfo.SessionInfo.quote_and_join_list(sorted(old_value_set))
            joined_new_value_set = SessionInfo.SessionInfo.quote_and_join_list(sorted(new_value_set))
            result.append(f'Change Search: "{name}" = {joined_old_value_set} -> {joined_new_value_set}')

    @staticmethod
    def get_column_slug_info(slugs: List[str], slug_map: Slug.ToInfoMap) -> Dict[str, Slug.Info]:
        """
        This returns a map from the slugs that appear in the list of strings to the Info for that slug,
        provided that the info exists.
        """
        return {
            slug: slug_info
            for slug in slugs
            for slug_info in [slug_map.get_info_for_column_slug(slug)]
            if slug_info is not None
        }



