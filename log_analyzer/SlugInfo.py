from __future__ import print_function

import json
import re
from enum import Enum, auto, Flag
from typing import Optional, Dict, Any, NamedTuple, cast

import requests


class SlugFamily(NamedTuple):
    base_slug: str  # Is this needed?
    label: str
    min: str
    max: str

    def is_singleton(self):
        return self.min == ''


class SlugFamilyType(Enum):
    MIN = auto()
    MAX = auto()
    QTYPE = auto()
    SINGLETON = auto()
    COLUMN = auto()


class SlugFlags(Flag):
    NONE = 0
    UNKNOWN_SLUG = auto()
    REMOVED_1_FROM_END = auto()
    REMOVED_2_FROM_END = auto()
    OBSOLETE_SLUG = auto()

    def pretty_print(self):
        """Print a set of flags in a slightly more human readable format"""
        temp = str(self).replace('SlugFlags.', '').replace('_', ' ')
        return ', '.join(x.lower() for x in temp.split('|'))


class SlugInfo(NamedTuple):
    slug: str
    label: str
    flags: SlugFlags
    family_type: SlugFamilyType
    family: Optional[SlugFamily]


class SlugMap:
    _slug_to_label: Dict[str, str]
    _old_slug_to_new_slug: Dict[str, str]
    _search_map: Dict[str, Optional[SlugInfo]]
    _column_map: Dict[str, Optional[SlugInfo]]

    QTYPE_SUFFIX = ' (QT)'
    UNKNOWN_SLUG_INFO = 'unknown slug'
    OBSOLETE_SLUG_INFO = 'obsolete slug'

    # Slugs that should be ignored when see them as either a column name or as a search term.
    SLUGS_NOT_IN_DB = {'browse', 'col_chooser', 'colls_browse', 'cols', 'detail',
                       'gallery_data_viewer', 'limit', 'loc_type', 'order', 'page',
                       'range', 'reqno', 'request', 'types', 'view', 'widgets', 'widgets2',
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

        # Fill in all the normal slugs
        self._slug_to_label = {
            slug_info['slug'].lower(): slug_info['label'] for slug_info in json_data.values()
        }

        self._old_slug_to_new_slug = {
            old_slug_info.lower(): slug_info['slug'].lower()
            for slug_info in json_data.values()
            for old_slug_info in [slug_info.get('old_slug')]
            if old_slug_info
        }
        self._column_map = {}
        self._search_map = {}

        for slug in self.SLUGS_NOT_IN_DB:
            self._column_map[slug] = None
            self._search_map[slug] = None

    def get_info_for_search_slug(self, slug: str, create=True) -> Optional[SlugInfo]:
        """
        Returns information about a slug that appears as part of a search term in a query
        """

        result: Optional[SlugInfo]
        base_result: Optional[SlugInfo]

        original_slug = slug
        slug = slug.lower()
        search_map = self._search_map

        if slug in search_map:
            # value may be None, so we can't just check the value of search_map.get(slug)
            result = search_map[slug]
            return result

        label = self._slug_to_label.get(slug)
        if label:
            result = search_map[slug] = self._known_label(slug, label, SlugFlags.NONE)
            return result

        new_slug = self._old_slug_to_new_slug.get(slug)
        if new_slug:
            label = self._slug_to_label[new_slug]
            result = search_map[slug] = self._known_label(new_slug, label, SlugFlags.OBSOLETE_SLUG)
            return result

        if slug[-1] in '12':
            slug_root = slug[:-1]
            base_result = cast(SlugInfo, self.get_info_for_search_slug(slug_root, True))
            family = SlugFamily(base_slug=base_result.slug, label=base_result.label, min='min', max='max')
            for value, family_type in ((1, SlugFamilyType.MIN), (2, SlugFamilyType.MAX)):
                search_map[f'{slug_root}{value}'] = SlugInfo(
                    slug=f'{base_result.slug}{value}',
                    label=f'{base_result.label} ({family_type.name.title()})',
                    flags=base_result.flags,
                    family=family, family_type=family_type)
            result = search_map[slug]
            return result

        if slug.startswith('qtype-'):
            # Look to see if the slug with the qtype- removed, but 1 or 2 added does exist
            base_result = next((self.get_info_for_search_slug(slug[6:] + i, False) for i in '12'), None)
            if base_result:
                assert base_result.family
                assert base_result.slug[-1] in '12'
                result = search_map[slug] = SlugInfo(
                    slug='qtype-' + base_result.slug[:-1],
                    label=base_result.family.label + self.QTYPE_SUFFIX,
                    flags=base_result.flags,
                    family=base_result.family, family_type=SlugFamilyType.QTYPE)
                return result
            # Okay.  We have a qtype- slug.  Create whatever kind of slug we can without the qtype- and guess.
            base_result = cast(SlugInfo, self.get_info_for_search_slug(slug[6:], True))
            family = SlugFamily(base_slug=base_result.slug, label=base_result.label, min='min', max='max')
            result = search_map[slug] = SlugInfo(
                slug='qtype-' + base_result.slug,
                label=base_result.label + self.QTYPE_SUFFIX,
                flags=base_result.flags,
                family=family, family_type=SlugFamilyType.QTYPE)
            return result

        if create:
            result = search_map[slug] = self._known_label(slug, original_slug, SlugFlags.UNKNOWN_SLUG)
            return result

        return None

    def _known_label(self, slug: str, label: str, flag: SlugFlags) -> SlugInfo:
        if slug[-1] in '12':
            if label.endswith(' (Min)') or label.endswith(' (Max)'):
                family = SlugFamily(base_slug=slug[:-1], label=label[:-6], min='min', max='max')
            else:
                base_label = re.sub(r'(.*) (Start|Stop) (.*)', r'\1 \3', label)
                family = SlugFamily(base_slug=slug[:-1], label=base_label, min='start', max='stop')
            family_type = SlugFamilyType.MIN if slug[-1] == '1' else SlugFamilyType.MAX
        else:
            family_type = SlugFamilyType.SINGLETON
            family = SlugFamily(base_slug=slug, label=label, min='', max='')
        return SlugInfo(slug=slug, label=label, flags=flag, family=family, family_type=family_type)

    def get_info_for_column_slug(self, slug: str, create: bool = True) -> Optional[SlugInfo]:
        """Returns information about a slug that appears in a cols= part of a query

        :param slug: A slug that represents a column name
        :param create: Used only internally.  Indicates whether to create a slug if this slug is completely unknown
        """
        original_slug = slug
        slug = slug.lower()
        column_map = self._column_map

        def create_slug(create_slug: str, label: str, flags: SlugFlags) -> SlugInfo:
            return SlugInfo(create_slug, label, flags, SlugFamilyType.COLUMN, None)

        if slug in column_map:
            return column_map[slug]

        if slug in self._slug_to_label:
            result = column_map[slug] = create_slug(slug, self._slug_to_label[slug], SlugFlags.NONE)
            return result

        if slug in self._old_slug_to_new_slug:
            new_slug = self._old_slug_to_new_slug[slug]
            new_slug_info = cast(SlugInfo, self.get_info_for_column_slug(new_slug, True))
            result = column_map[slug] = new_slug_info._replace(flags=(SlugFlags.OBSOLETE_SLUG | new_slug_info.flags))
            return result

        if slug[-1] in '12':
            temp = self.get_info_for_column_slug(slug[:-1], False)
            flag = {'1': SlugFlags.REMOVED_1_FROM_END, '2': SlugFlags.REMOVED_2_FROM_END}[slug[-1]]
            if temp:
                result = column_map[slug] = create_slug(temp.slug, temp.label, temp.flags or flag)
                return result

        if create:
            result = column_map[slug] = create_slug(slug, original_slug, SlugFlags.UNKNOWN_SLUG)
            return result

        column_map[slug] = None
        return None

    DEFAULT_FIELDS_SUFFIX = '/opus/api/fields.json'

    @staticmethod
    def __read_json(url_prefix: str) -> Dict[str, Any]:
        if url_prefix.endswith('/'):
            url_prefix = url_prefix[:-1]
        url = url_prefix + SlugMap.DEFAULT_FIELDS_SUFFIX

        if url.startswith('file://'):
            with open(url[7:], "r") as file:
                text = file.read()
        else:
            response = requests.get(url)
            text = response.text
        info = json.loads(text)

        # This is a known bug in the JSON.  We correct it before writing it out.
        data = info['data']
        assert data['ringobsid']
        del data['ringobsid']
        data['opusid']['old_slug'] = 'ringobsid'
        return info
