from __future__ import print_function

import json
import re
from typing import Optional, Tuple, Dict, Any

import requests


class SlugInfo(object):
    _slug_map: Dict[str, Tuple[str, Optional[str]]]
    _additional_slugs_for_searches: Dict[str, Tuple[str, Optional[str]]]
    _additional_slugs_for_columns: Dict[str, Tuple[str, Optional[str]]]

    # Slugs that should be ignored when see them as either a column name or as a search term.
    SLUGS_NOT_IN_DB = {'browse', 'col_chooser', 'colls_browse', 'cols', 'detail',
                       'gallery_data_viewer', 'limit', 'loc_type', 'order', 'page',
                       'range', 'reqno', 'request', 'types', 'view', 'widgets', 'widgets2',
                       # Not mentioned by Rob French, but ignored anyway.
                       'timesampling', 'wavelengthsampling', 'colls',
                       }

    QT_SUFFIX = "(QT)"

    DEFAULT_FIELDS_SUFFIX = '/opus/api/fields.json'

    def __init__(self, url_prefix: str):
        """Initializes the slug info by reading the JSON describing it either from a URL or from a file to which
        it has been copied.

        :param url_prefix: The prefix of the url from which to read the JSON description.
        """

        # Read the json
        if url_prefix.endswith('/'):
            url_prefix = url_prefix[:-1]
        url = url_prefix + self.DEFAULT_FIELDS_SUFFIX
        raw_json = self.__read_json(url)
        json_data: Dict[str, Any] = raw_json['data']

        slug_map: Dict[str, Tuple[str, Optional[str]]] = {}

        # Fill in all the normal slugs
        for slug_info in json_data.values():
            label = slug_info['label']
            slug = slug_info['slug'].lower()
            slug_map[slug] = (label, None)
        # Only allow an old_slug if it doesn't have the same value as one already existing.
        for slug_info in json_data.values():
            label = slug_info['label']
            slug = slug_info.get('old_slug')
            if slug and slug.lower() not in slug_info:
                slug_map[slug.lower()] = (label, 'obsolete slug')
        self._slug_map = slug_map
        self._additional_slugs_for_searches = {}
        self._additional_slugs_for_columns = {}

    def get_info_for_column_slug(self, slug: str) -> Optional[Tuple[str, Optional[str]]]:
        """Returns information about a slug that appears in a cols= part of a query

        :param String slug: A slug that represents a column name
        :return Tuple(String, String):
        """
        slug = slug.lower()
        if slug in self._slug_map:
            return self._slug_map[slug]
        if slug in self._additional_slugs_for_columns:
            return self._additional_slugs_for_columns[slug]
        if slug in self.SLUGS_NOT_IN_DB:
            return None

        if slug[-1] in '12' and slug[:-1] in self._slug_map:
            # Rob says this shouldn't be happening, but it is.  A search slug is accidentally being used as a column.
            # Just silently do the right thing, but mark it as a mistake.  When we see either a '1' or a '2' that
            # shouldn't be at the end of a slug, just silently add both.
            base_info, _ = self._slug_map[slug[:-1]]
            for ch in '12':
                self._additional_slugs_for_columns[slug[:-1] + ch] = base_info, f'removed {ch} from end'
        else:
            # We don't know what to do with this.  Just mark it as itself.
            self._additional_slugs_for_columns[slug] = slug, 'unknown slug'
        return self._additional_slugs_for_columns[slug]

    def get_info_for_search_slug(self, slug: str) -> Optional[Tuple[str, Optional[str]]]:
        """
        Returns information about a slug that appears as part of a search term in a query
        """
        slug = slug.lower()
        if slug in self._slug_map:
            return self._slug_map[slug]
        if slug in self._additional_slugs_for_searches:
            return self._additional_slugs_for_searches[slug]
        if slug in self.SLUGS_NOT_IN_DB:
            return None

        if slug[-1] in '12' and slug[:-1] in self._slug_map:
            # Sometimes, the search term can have a min and max, even though the column can't.
            base_info, extra_info = self._slug_map[slug[:-1]]
            self._additional_slugs_for_searches[slug[:-1] + '1'] = base_info + ' (Min)', extra_info
            self._additional_slugs_for_searches[slug[:-1] + '2'] = base_info + ' (Max)', extra_info
        elif slug.startswith('qtype-') and slug[6:] in self._slug_map:
            # qtype-foo where foo is a known slug
            base_info, extra_info = self._slug_map[slug[6:]]
            self._additional_slugs_for_searches[slug] = base_info + self.QT_SUFFIX, extra_info
        elif slug.startswith('qtype-') and slug[6:] + '1' in self._slug_map:
            # qtype-foo where foo1 is a known slug
            base_info, extra_info = self._slug_map[slug[6:] + '1']
            # We try to make a reasonable name by either deleting '(Min)'  or by deleting ' Start '
            if base_info.endswith(' (Min)'):
                base_info = base_info[:-6]
            else:
                base_info = re.sub(r'(.*) Start (.*)', r'\1 \2', base_info)
            self._additional_slugs_for_searches[slug] = base_info + self.QT_SUFFIX, extra_info
        else:
            # No idea.  Let's just flag it.
            self._additional_slugs_for_searches[slug] = slug, 'unknown slug'
        return self._additional_slugs_for_searches[slug]

    @staticmethod
    def __read_json(url: str) -> Dict[str, Any]:
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
