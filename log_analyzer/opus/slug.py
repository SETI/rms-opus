from __future__ import print_function

import json
import re
from enum import Enum, auto, Flag
from typing import Optional, Dict, Any, NamedTuple, cast

import requests

SEARCH_LABEL = 'full_search_label'
COLUMN_LABEL = 'full_label'


class Family(NamedTuple):
    label: str  # The long name for this slug
    min: str  # 'min' or 'start'.  Empty string if this is a singleton
    max: str  # 'max' or 'stop'.  Empty string if this is a singleton

    def is_singleton(self) -> bool:
        return self.min == ''


class FamilyType(Enum):
    MIN = auto()
    MAX = auto()
    QTYPE = auto()
    SINGLETON = auto()
    COLUMN = auto()
    UNIT = auto()


class Flags(Flag):
    NONE = 0
    UNKNOWN_SLUG = auto()  # slug not in our database
    REMOVED_1_FROM_END = auto()  # slug ending in 1 not in our database, but removing 1 works
    REMOVED_2_FROM_END = auto()  # slug ending in 2 not in our database, but removing 2 works
    OBSOLETE_SLUG = auto()  # slug in the list of obsolete slugs

    def pretty_print(self) -> str:
        """Print a set of flags in a slightly more human readable format"""
        temp = str(self).replace('Flags.', '').replace('_', ' ')
        return ', '.join(x.lower() for x in temp.split('|'))

    def is_obsolete(self) -> bool:
        return bool(self & Flags.OBSOLETE_SLUG)


class Info(NamedTuple):
    """
    Information about a slug.  Note that we can't let the Info for an obsolete slug and its replacement be
    identical, since they are used as keys in a dictionary.
    """
    canonical_name: str  # The slug name.  Included so obsolete slugs will be different than their updated version
    label: str  # The verbose label for this slug
    flags: Flags
    family_type: FamilyType
    family: Family
    subgroup: int = 0


class ToInfoMap:
    _slug_to_search_label: Dict[str, str]
    _slug_to_column_label: Dict[str, str]
    _old_slug_to_new_slug: Dict[str, str]
    _search_map: Dict[str, Optional[Info]] = {}
    _column_map: Dict[str, Optional[Info]] = {}

    QTYPE_SUFFIX = ' (QT)'
    UNIT_SUFFIX = ' (UNIT)'
    UNKNOWN_SLUG_INFO = 'unknown slug'
    OBSOLETE_SLUG_INFO = 'obsolete slug'

    # Slugs that should be ignored when see them as either a column name or as a search term.
    SLUGS_NOT_IN_DB = {'browse', 'order', 'page', 'startobs',
                       'cart_browse', 'cart_order', 'cart_page', 'cart_startobs',
                       'colls_browse', 'colls_order', 'colls_page',
                       'colls_startobs',
                       'cols', 'col_chooser', 'detail', 'download',
                       'expanded_cats',
                       'gallery_data_viewer', 'ignorelog', 'limit', 'loc_type',
                       'range', 'recyclebin', 'reqno', 'request',
                       'types', 'url_cols', 'units', 'unselected_types', 'view',
                       'widgets', 'widgets2',
                       '__sessionid',

                       # Not mentioned by Rob French, but ignored anyway.
                       'timesampling', 'wavelengthsampling', 'colls',
                       }

    def __init__(self, url_prefix: str):
        """Initializes the slug info by reading the JSON describing it either from a URL or from a file to which
        it has been copied.
        """

        # Read the json
        raw_json = self.__read_json(url_prefix)
        json_data: Dict[str, Any] = raw_json['data']

        slug_to_search_label = {}
        slug_to_column_label = {}
        for slug_info in json_data.values():
            slug_name = slug_info['slug'].lower()
            slug_search_value = slug_info.get(SEARCH_LABEL, None)
            slug_column_value = slug_info.get(COLUMN_LABEL, None)
            if slug_search_value:
                slug_to_search_label[slug_name] = slug_search_value
            if slug_column_value:
                slug_to_column_label[slug_name] = slug_column_value
        self._slug_to_search_label = slug_to_search_label
        self._slug_to_column_label = slug_to_column_label

        # Fill in all the normal slugs

        self._old_slug_to_new_slug = {
            old_slug_info.lower(): slug_info['slug'].lower()
            for slug_info in json_data.values()
            for old_slug_info in [slug_info.get('old_slug')] if old_slug_info
        }

        for slug in self.SLUGS_NOT_IN_DB:
            self._column_map[slug] = None
            self._search_map[slug] = None

    def get_family_info_for_widget(self, widget: str) -> Optional[Family]:
        widget = widget.lower()
        result = self._search_map.get(widget)
        if not result:
            result = self._search_map.get(widget + "1")
        if not result:
            result = self._search_map.get(widget + "2")

        if result:
            return result.family
        else:
            return None

    def get_info_for_search_slug(self, slug: str, value: str) -> Optional[Info]:
        return self._get_info_for_search_slug(slug, True, value)

    def _get_info_for_search_slug(self, original_slug: str, create: bool = True, value: str = '') -> Optional[Info]:
        base_result: Optional[Info]
        slug = original_slug.lower()
        search_map = self._search_map

        if slug in search_map:
            # value may be None, so we can't just check the value of search_map.get(slug)
            return search_map[slug]

        match = re.fullmatch(r'(.*)_(\d{2,})$', slug)
        if match:
            base_result = self._get_info_for_search_slug(match.group(1), create, value)
            result = search_map[slug] = base_result._replace(subgroup=int(match.group(2))) if base_result else None
            return result

        label = self._slug_to_search_label.get(slug)
        if label:
            result = search_map[slug] = self._known_label(slug, label, Flags.NONE)
            return result

        current_slug = self._old_slug_to_new_slug.get(slug)
        if current_slug:
            label = self._slug_to_search_label[current_slug]
            result = search_map[slug] = self._known_label(current_slug, label, Flags.OBSOLETE_SLUG)
            return result

        if slug[-1] in '12':
            slug_root = slug[:-1]
            base_result = cast(Info, self._get_info_for_search_slug(slug_root, True))
            family = Family(label=base_result.label, min='min', max='max')
            for suffix, family_type in (('1', FamilyType.MIN), ('2', FamilyType.MAX)):
                search_map[f'{slug_root}{suffix}'] = Info(
                    canonical_name=f'{base_result.canonical_name}{suffix}',
                    label=f'{base_result.label} ({family_type.name.title()})',
                    flags=base_result.flags,
                    family=family, family_type=family_type)
            result = search_map[slug]
            return result

        if slug.startswith('qtype-'):
            # Look to see if the slug with the qtype- removed, but 1 or 2 added does exist
            is_numeric = value in ('any', 'all', 'only')
            if is_numeric:
                base_result = next((self._get_info_for_search_slug(slug[6:] + i, False) for i in '12'), None)
                if base_result:
                    assert base_result.family
                    assert base_result.canonical_name[-1] in '12'
                    result = search_map[slug] = Info(
                        canonical_name='qtype-' + base_result.canonical_name[:-1],
                        label=base_result.family.label + self.QTYPE_SUFFIX,
                        flags=base_result.flags,
                        family=base_result.family, family_type=FamilyType.QTYPE)
                    return result
            # Okay.  We have a qtype- slug.  Create whatever kind of slug we can without the qtype- and guess.
            base_result = cast(Info, self._get_info_for_search_slug(slug[6:], True))
            if is_numeric:
                family = Family(label=base_result.label, min='min', max='max')
            else:
                family = Family(label=base_result.label, min='', max='')
            result = search_map[slug] = Info(
                canonical_name='qtype-' + base_result.canonical_name,
                label=base_result.label + self.QTYPE_SUFFIX,
                flags=base_result.flags,
                family=family, family_type=FamilyType.QTYPE)
            return result

        if slug.startswith('unit-'):
            for suffix in ('1', '2', ''):
                base_result = self._get_info_for_search_slug(slug[5:] + suffix, False, value)
                if base_result:
                    stripped_name = base_result.canonical_name[:-len(suffix)] if suffix else base_result.canonical_name
                    result = search_map[slug] = Info(
                        canonical_name='qtype-' + stripped_name,
                        label=base_result.family.label + self.UNIT_SUFFIX,
                        flags=base_result.flags,
                        family=base_result.family, family_type=FamilyType.UNIT)
                    return result
            return None

        if create:
            result = search_map[slug] = self._known_label(slug, original_slug, Flags.UNKNOWN_SLUG)
            return result

        return None

    def _known_label(self, slug: str, label: str, flag: Flags) -> Info:
        if slug[-1] in '12':
            if label.endswith(' (Min)') or label.endswith(' (Max)'):
                family = Family(label=label[:-6], min='min', max='max')
            else:
                base_label = re.sub(r'(.*) (Start|Stop) (.*)', r'\1 \3', label)
                if base_label != label:
                    family = Family(label=base_label, min='start', max='stop')
                else:
                    family = Family(label=label, min='min', max='max')
            family_type = FamilyType.MIN if slug[-1] == '1' else FamilyType.MAX
        else:
            family_type = FamilyType.SINGLETON
            family = Family(label=label, min='', max='')
        return Info(canonical_name=slug, label=label, flags=flag, family=family, family_type=family_type)

    def get_info_for_column_slug(self, slug: str, create: bool = True) -> Optional[Info]:
        """Returns information about a slug that appears in a cols= part of a query

        :param slug: A slug that represents a column name
        :param create: Used only internally.  Indicates whether to create a slug if this slug is completely unknown
        """
        original_slug = slug
        slug = slug.lower()
        column_map = self._column_map

        def create_slug(canonical_name: str, label: str, flags: Flags) -> Info:
            family = Family(label, '', '')
            return Info(canonical_name, label, flags, FamilyType.COLUMN, family)

        if slug in column_map:
            return column_map[slug]

        if slug in self._slug_to_column_label:
            label = self._slug_to_column_label[slug]
            result = column_map[slug] = create_slug(slug, label, Flags.NONE)
            return result

        if slug in self._old_slug_to_new_slug:
            new_slug = self._old_slug_to_new_slug[slug]
            new_slug_info = cast(Info, self.get_info_for_column_slug(new_slug, True))
            result = column_map[slug] = new_slug_info._replace(flags=(Flags.OBSOLETE_SLUG | new_slug_info.flags))
            return result

        if slug[-1] in '12':
            base_slug = self.get_info_for_column_slug(slug[:-1], False)
            if base_slug:
                column_map[slug[:-1] + '1'] = base_slug._replace(flags=(Flags.REMOVED_1_FROM_END | base_slug.flags))
                column_map[slug[:-1] + '2'] = base_slug._replace(flags=(Flags.REMOVED_2_FROM_END | base_slug.flags))
                return column_map[slug]

        if create:
            result = column_map[slug] = create_slug(slug, original_slug, Flags.UNKNOWN_SLUG)
            return result

        column_map[slug] = None
        return None

    DEFAULT_FIELDS_SUFFIX = '/opus/api/fields.json'

    @staticmethod
    def __read_json(url_prefix: str) -> Dict[str, Any]:
        if url_prefix.endswith('/'):
            url_prefix = url_prefix[:-1]
        url = url_prefix + ToInfoMap.DEFAULT_FIELDS_SUFFIX

        if url.startswith('file://'):
            with open(url[7:], "r") as file:
                text = file.read()
        else:
            response = requests.get(url)
            response.raise_for_status()
            text = response.text
        info = json.loads(text)

        # This is a known bug in the JSON.  We correct it before writing it out.
        data = info['data']
        new_data = {}
        for cat, slug_info in data.items():
            new_data.update(slug_info)
        info['data'] = new_data
        assert new_data['ringobsid']
        del new_data['ringobsid']
        new_data['opusid']['old_slug'] = 'ringobsid'
        return cast(Dict[str, Any], info)
