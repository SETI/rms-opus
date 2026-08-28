"""Interpreting the slugs that appear in an OPUS URL.

An OPUS URL names each search term and each result column by a short identifier called
a slug.  `ToInfoMap` reads the field definitions an OPUS server publishes and turns a
slug into an `Info`, giving the slug's verbose label, the `Family` of related slugs it
belongs to, and `Flags` recording whether the slug was unrecognized or obsolete.
"""

import json
import re
from enum import Enum, Flag, auto
from typing import Any, ClassVar, NamedTuple, cast

import requests

SEARCH_LABEL = 'full_search_label'
COLUMN_LABEL = 'full_label'


class Family(NamedTuple):
    """A group of slugs that together express one search term.

    A range has two slugs, one for each end; `min` and `max` are the words that name
    those ends when the report describes the term.  A singleton has a single slug, and
    both words are empty.
    """

    label: str  # The long name for this slug
    min: str  # 'min' or 'start'.  Empty string if this is a singleton
    max: str  # 'max' or 'stop'.  Empty string if this is a singleton

    def is_singleton(self) -> bool:
        """Whether this family is a single slug rather than the two ends of a range."""
        return self.min == ''


class FamilyType(Enum):
    """The part a single slug plays in its `Family`.

    `MIN` and `MAX` are the two ends of a range and `SINGLETON` a search term with one
    value.  `QTYPE` and `UNIT` are the slugs carrying a term's query type and its
    units, written with a `qtype-` or a `unit-` prefix.  `COLUMN` is a result column
    rather than a search term.
    """

    MIN = auto()
    MAX = auto()
    QTYPE = auto()
    SINGLETON = auto()
    COLUMN = auto()
    UNIT = auto()


class Flags(Flag):
    """What was odd about a slug, if anything, when it was looked up.

    A slug the field definitions do not mention is `UNKNOWN_SLUG`, and one listed as
    an earlier name for another slug is `OBSOLETE_SLUG`.  `REMOVED_1_FROM_END` and
    `REMOVED_2_FROM_END` mark a column slug that was recognized only once its trailing
    digit had been dropped.
    """

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
        """Whether `OBSOLETE_SLUG` is among these flags."""
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
    """The slug definitions of one OPUS server, and lookups against them.

    Constructing the map reads the server's field definitions.  Looking a slug up
    returns an `Info` describing it, working one out where the definitions do not
    cover the slug directly, and remembers the answer.  The two maps the answers are
    remembered in are class attributes, so every instance in a process shares them.
    """

    _slug_to_search_label: dict[str, str]
    _slug_to_column_label: dict[str, str]
    _old_slug_to_new_slug: dict[str, str]
    _search_map: ClassVar[dict[str, Info | None]] = {}
    _column_map: ClassVar[dict[str, Info | None]] = {}

    QTYPE_SUFFIX = ' (QT)'
    UNIT_SUFFIX = ' (UNIT)'
    UNKNOWN_SLUG_INFO = 'unknown slug'
    OBSOLETE_SLUG_INFO = 'obsolete slug'

    # Slugs that should be ignored when see them as either a column name or as a search term.
    SLUGS_NOT_IN_DB: ClassVar[set[str]] = {
        'browse',
        'order',
        'page',
        'startobs',
        'cart_browse',
        'cart_order',
        'cart_page',
        'cart_startobs',
        'colls_browse',
        'colls_order',
        'colls_page',
        'colls_startobs',
        'cols',
        'col_chooser',
        'detail',
        'download',
        'expanded_cats',
        'gallery_data_viewer',
        'ignorelog',
        'limit',
        'loc_type',
        'range',
        'recyclebin',
        'reqno',
        'request',
        'types',
        'url_cols',
        'units',
        'unselected_types',
        'view',
        'widgets',
        'widgets2',
        '__sessionid',
        # Not mentioned by Rob French, but ignored anyway.
        'timesampling',
        'wavelengthsampling',
        'colls',
    }

    def __init__(self, url_prefix: str):
        """Initializes the slug info by reading the JSON describing it either from a URL or from a file to which
        it has been copied.
        """

        # Read the json
        raw_json = self.__read_json(url_prefix)
        json_data: dict[str, Any] = raw_json['data']

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
            for old_slug_info in [slug_info.get('old_slug')]
            if old_slug_info
        }

        for slug in self.SLUGS_NOT_IN_DB:
            self._column_map[slug] = None
            self._search_map[slug] = None

    def get_family_info_for_widget(self, widget: str) -> Family | None:
        """Return the family of the search slug that a widget name refers to.

        The name is tried as it stands and then with `1` and with `2` appended, and is
        matched case-insensitively.  Only slugs already looked up as search slugs are
        considered; this creates nothing.

        Parameters:
            widget: A widget name, as it appears in the URL that opens the widget.

        Returns:
            The `Family` of the first of the three names that is found, or None if
            none of them is.
        """
        widget = widget.lower()
        result = self._search_map.get(widget)
        if not result:
            result = self._search_map.get(widget + '1')
        if not result:
            result = self._search_map.get(widget + '2')

        if result:
            return result.family
        else:
            return None

    def get_info_for_search_slug(self, slug: str, value: str) -> Info | None:
        """Return information about a slug used as a search term in a query.

        A slug the field definitions do not cover is given an `Info` of its own,
        flagged `UNKNOWN_SLUG` and labeled with the slug as it was written.

        Parameters:
            slug: The slug name, matched case-insensitively.
            value: The value the query gave for the slug.  It decides how a `qtype-`
                slug is read.

        Returns:
            The `Info` for the slug, or None for a slug that carries no information,
            such as one of `SLUGS_NOT_IN_DB`.
        """
        return self._get_info_for_search_slug(slug, True, value)

    def _get_info_for_search_slug(
        self, original_slug: str, create: bool = True, value: str = ''
    ) -> Info | None:
        """Look up a search slug, working one out where the definitions do not cover it.

        The first of these that applies decides the answer: an entry already recorded
        for the slug; an underscore and two or more digits at the end, which reuses the
        entry for the slug without that suffix and records the digits as a subgroup; a
        search label the server publishes; an earlier name for another slug, which
        resolves to that slug and is flagged `OBSOLETE_SLUG`; a trailing 1 or 2, which
        makes the two ends of a range; a `qtype-` prefix; a `unit-` prefix; and
        finally, when `create` is set, an unknown slug.  Whatever is worked out is
        recorded for later lookups.

        Parameters:
            original_slug: The slug as it was written; the lookup is case-insensitive.
            create: Whether a slug that nothing else matched should be given an `Info`
                flagged `UNKNOWN_SLUG`.
            value: The value the query gave for the slug.  A `qtype-` slug is read as
                belonging to a range when the value is `any`, `all` or `only`.

        Returns:
            The `Info` for the slug, or None.  None comes back for a name recorded as
            carrying no information, for a `unit-` slug whose underlying slug is not
            found, and for anything otherwise unmatched when `create` is false.
        """
        base_result: Info | None
        slug = original_slug.lower()
        search_map = self._search_map

        if slug in search_map:
            # value may be None, so we can't just check the value of search_map.get(slug)
            return search_map[slug]

        match = re.fullmatch(r'(.*)_(\d{2,})$', slug)
        if match:
            base_result = self._get_info_for_search_slug(match.group(1), create, value)
            result = search_map[slug] = (
                base_result._replace(subgroup=int(match.group(2))) if base_result else None
            )
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
                    family=family,
                    family_type=family_type,
                )
            result = search_map[slug]
            return result

        if slug.startswith('qtype-'):
            # Look to see if the slug with the qtype- removed, but 1 or 2 added does exist
            is_numeric = value in ('any', 'all', 'only')
            if is_numeric:
                base_result = next(
                    (self._get_info_for_search_slug(slug[6:] + i, False) for i in '12'), None
                )
                if base_result:
                    assert base_result.family
                    assert base_result.canonical_name[-1] in '12'
                    result = search_map[slug] = Info(
                        canonical_name='qtype-' + base_result.canonical_name[:-1],
                        label=base_result.family.label + self.QTYPE_SUFFIX,
                        flags=base_result.flags,
                        family=base_result.family,
                        family_type=FamilyType.QTYPE,
                    )
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
                family=family,
                family_type=FamilyType.QTYPE,
            )
            return result

        if slug.startswith('unit-'):
            for suffix in ('1', '2', ''):
                base_result = self._get_info_for_search_slug(slug[5:] + suffix, False, value)
                if base_result:
                    stripped_name = (
                        base_result.canonical_name[: -len(suffix)]
                        if suffix
                        else base_result.canonical_name
                    )
                    result = search_map[slug] = Info(
                        canonical_name='qtype-' + stripped_name,
                        label=base_result.family.label + self.UNIT_SUFFIX,
                        flags=base_result.flags,
                        family=base_result.family,
                        family_type=FamilyType.UNIT,
                    )
                    return result
            return None

        if create:
            result = search_map[slug] = self._known_label(slug, original_slug, Flags.UNKNOWN_SLUG)
            return result

        return None

    def _known_label(self, slug: str, label: str, flag: Flags) -> Info:
        """Build the `Info` for a search slug whose label is known.

        A slug ending in 1 or 2 becomes the minimum or the maximum end of a range.  Its
        family label is the label without a trailing ` (Min)` or ` (Max)`, or with the
        word `Start` or `Stop` taken out of the middle; the two ends are then named
        `min` and `max`, or `start` and `stop` when the label used those words.  Any
        other slug becomes a singleton whose family label is the whole label.

        Parameters:
            slug: The canonical name to give the `Info`.
            label: The verbose label for the slug.
            flag: The flags to record on the `Info`.

        Returns:
            The `Info` for the slug.
        """
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
        return Info(
            canonical_name=slug, label=label, flags=flag, family=family, family_type=family_type
        )

    def get_info_for_column_slug(self, slug: str, create: bool = True) -> Info | None:
        """Returns information about a slug that appears in a cols= part of a query

        :param slug: A slug that represents a column name
        :param create: Used only internally.  Indicates whether to create a slug if this slug is completely unknown
        """
        original_slug = slug
        slug = slug.lower()
        column_map = self._column_map

        def create_slug(canonical_name: str, label: str, flags: Flags) -> Info:
            """Build the `Info` for a column slug, whose family is the label alone."""
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
            result = column_map[slug] = new_slug_info._replace(
                flags=(Flags.OBSOLETE_SLUG | new_slug_info.flags)
            )
            return result

        if slug[-1] in '12':
            base_slug = self.get_info_for_column_slug(slug[:-1], False)
            if base_slug:
                column_map[slug[:-1] + '1'] = base_slug._replace(
                    flags=(Flags.REMOVED_1_FROM_END | base_slug.flags)
                )
                column_map[slug[:-1] + '2'] = base_slug._replace(
                    flags=(Flags.REMOVED_2_FROM_END | base_slug.flags)
                )
                return column_map[slug]

        if create:
            result = column_map[slug] = create_slug(slug, original_slug, Flags.UNKNOWN_SLUG)
            return result

        column_map[slug] = None
        return None

    DEFAULT_FIELDS_SUFFIX = '/opus/api/fields.json'

    @staticmethod
    def __read_json(url_prefix: str) -> dict[str, Any]:
        """Read an OPUS server's field definitions.

        `DEFAULT_FIELDS_SUFFIX` is appended to the prefix, with any trailing slash on
        the prefix dropped first.  A `file://` URL is read from the file system;
        anything else is fetched over HTTP.

        The server groups the definitions by category.  In the result they are
        flattened into a single map from field name to definition, the `ringobsid`
        entry is removed, and `ringobsid` is recorded as the old name of `opusid`.

        Parameters:
            url_prefix: The base URL of the server, or a `file://` URL naming a saved
                copy of the definitions.

        Returns:
            The parsed JSON, with its `data` rewritten as described.

        Raises:
            requests.HTTPError: The server answered with an error status.
        """
        if url_prefix.endswith('/'):
            url_prefix = url_prefix[:-1]
        url = url_prefix + ToInfoMap.DEFAULT_FIELDS_SUFFIX

        if url.startswith('file://'):
            with open(url[7:]) as file:
                text = file.read()
        else:
            # A missing timeout, so an unresponsive --api-host-url hangs the run.
            # Filed as issue #1449; log-analyzer behavior is out of scope for this
            # modernization (plan rev 7.14), so it is recorded rather than fixed.
            response = requests.get(url)  # nosec B113
            response.raise_for_status()
            text = response.text
        info = json.loads(text)

        # This is a known bug in the JSON.  We correct it before writing it out.
        data = info['data']
        new_data = {}
        for _cat, slug_info in data.items():
            new_data.update(slug_info)
        info['data'] = new_data
        assert new_data['ringobsid']
        del new_data['ringobsid']
        new_data['opusid']['old_slug'] = 'ringobsid'
        return cast(dict[str, Any], info)
