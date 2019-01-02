from __future__ import print_function

import json
import re
from enum import Enum, auto
from typing import Optional, Dict, Any, NamedTuple, cast

import requests


class SlugFamily(NamedTuple):
    base_slug: str  # Is this needed?
    label: str
    min: str
    max: str


class SlugFamilyType(Enum):
    NONE = auto()
    MIN = auto()
    MAX = auto()
    QTYPE = auto()


class SlugInfo(NamedTuple):
    slug: str
    label: str
    extra_info: Optional[str] = None
    family_type: SlugFamilyType = SlugFamilyType.NONE
    family: Optional[SlugFamily] = None


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

        original_slug = slug
        slug = slug.lower()
        search_map = self._search_map
        if slug in search_map:
            return search_map[slug]

        if slug in self._slug_to_label:
            result = search_map[slug] = self._known_label(slug, None)
            return result

        if slug in self._old_slug_to_new_slug:
            new_slug = self._old_slug_to_new_slug[slug]
            result = search_map[slug] = self._known_label(new_slug, self.OBSOLETE_SLUG_INFO)
            return result

        if slug[-1] in '12':
            result = self.get_info_for_search_slug(slug[:-1], False)
            if result:
                slug_root = slug[:-1]
                family = SlugFamily(base_slug=result.slug, label=result.label, min='min', max='max')
                extra_info = result.extra_info
                search_map[slug_root + '1'] = SlugInfo(
                    slug=result.slug + '1', label=result.label + ' (Min)',
                    extra_info=extra_info, family=family, family_type=SlugFamilyType.MIN)
                search_map[slug_root + '2'] = SlugInfo(
                    slug=result.slug + '2', label=result.label + ' (Max)',
                    extra_info=extra_info, family=family, family_type=SlugFamilyType.MAX)
            return search_map[slug]

        if slug.startswith('qtype-'):
            result = self.get_info_for_search_slug(slug[6:] + '1', False)
            if result:
                assert result.family
                assert result.slug.endswith('1')
                sub_result = search_map[slug] = SlugInfo(
                    slug='qtype-' + result.slug[:-1], label=result.family.label + self.QTYPE_SUFFIX,
                    extra_info=result.extra_info, family=result.family, family_type=SlugFamilyType.QTYPE)
                return sub_result
            result = self.get_info_for_search_slug(slug[6:], False)
            if result:
                family = SlugFamily(base_slug=result.slug, label=result.label, min='min', max='max')
                sub_result = search_map[slug] = SlugInfo(
                    slug='qtype-' + result.slug, label=result.label + self.QTYPE_SUFFIX,
                    extra_info=result.extra_info, family=family, family_type=SlugFamilyType.QTYPE)
                return sub_result

        if create:
            result = search_map[slug] = SlugInfo(slug=slug, label=original_slug, extra_info=self.UNKNOWN_SLUG_INFO)
            return result

        return None

    def _known_label(self, slug: str, extra_info: Optional[str]) -> SlugInfo:
        label = self._slug_to_label[slug]
        family, family_type = None, SlugFamilyType.NONE
        if slug[-1] in '12':
            if label.endswith(' (Min)') or label.endswith(' (Max)'):
                family = SlugFamily(base_slug=slug[:-1], label=label[:-6], min='min', max='max')
            else:
                base_label = re.sub(r'(.*) (Start|Stop) (.*)', r'\1 \3', label)
                family = SlugFamily(base_slug=slug[-1], label=base_label, min='start', max='stop')
            family_type = SlugFamilyType.MIN if slug[-1] == '1' else SlugFamilyType.MAX
        return SlugInfo(slug=slug, label=label, extra_info=extra_info, family=family, family_type=family_type)

    def get_info_for_column_slug(self, slug: str, create: bool = True) -> Optional[SlugInfo]:
        """Returns information about a slug that appears in a cols= part of a query

        :param slug: A slug that represents a column name
        :param create: Used only internally.  Indicates whether to create a slug if this slug is completely unknown
        """
        original_slug = slug
        slug = slug.lower()
        column_map = self._column_map

        if slug in column_map:
            return column_map[slug]

        if slug in self._slug_to_label:
            result = column_map[slug] = SlugInfo(slug, self._slug_to_label[slug])
            return result

        if slug in self._old_slug_to_new_slug:
            new_slug = self._old_slug_to_new_slug[slug]
            new_slug_info = cast(SlugInfo, self.get_info_for_column_slug(new_slug, True))
            result = column_map[slug] = new_slug_info._replace(extra_info=self.OBSOLETE_SLUG_INFO)
            return result

        if slug[-1] in '12':
            temp = self.get_info_for_column_slug(slug[:-1], False)
            if temp:
                result = column_map[slug] = SlugInfo(temp.slug, temp.label, f'removed {slug[-1]} from end')
                return result

        if create:
            result = column_map[slug] = SlugInfo(slug, original_slug, self.UNKNOWN_SLUG_INFO)
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
