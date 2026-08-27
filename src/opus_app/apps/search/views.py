################################################################################
#
# search/views.py
#
# The API interface for doing things related to searches plus major internal
# support routines for searching:
#
#    Format: __api/normalizeinput.json
#    Format: __api/stringsearchchoices/<slug>.json
#
################################################################################

"""The search API, and the routines that turn a search URL into SQL.

`url_to_search_params` parses a request's query string into the `(selections,
extras)` pair the rest of the search path works in, and `construct_query_string`
renders that pair as a SELECT through `opus_app.apps.tools.sql_builder`.
`get_user_query_table` runs the search and caches its results in a per-search
`cache_<n>` table that the results, metadata and cart views then join against.
"""

from __future__ import annotations

import copy
import hashlib
import json
import logging
import re
import time
from typing import TYPE_CHECKING, Any, Literal, overload

# This is used instead of "re" because it's closer to the ICU regex library
# used by MySQL.
import regex
from django.apps import apps
from django.conf import settings
from django.core.cache import cache
from django.db import DatabaseError, connection
from django.db.models import Q
from django.db.utils import IntegrityError
from django.http import Http404, HttpResponseServerError

from opus_app.apps.paraminfo.models import ParamInfo
from opus_app.apps.search.models import UserSearches
from opus_app.apps.tools import sql_builder
from opus_app.apps.tools.app_utils import (
    Http400Error,
    api_view,
    get_mult_name,
    get_reqno,
    http400_bad_limit,
    http400_bad_or_missing_reqno,
    http400_search_params_invalid,
    http400_unknown_slug,
    http404_no_request,
    http500_database_error,
    http500_search_cache_failed,
    json_response,
    sort_dictionary,
    strip_numeric_suffix,
)
from opus_app.apps.tools.db_utils import MYSQL_EXECUTION_TIME_EXCEEDED, MYSQL_TABLE_ALREADY_EXISTS

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping

    from django.http import HttpRequest, HttpResponse

from opus_support import (
    convert_from_default_unit,
    convert_to_default_unit,
    format_unit_value,
    get_default_unit,
    get_valid_units,
    parse_form_type,
    parse_unit_value,
)

log = logging.getLogger(__name__)


################################################################################
#
# API INTERFACES
#
################################################################################

@api_view
def api_normalize_input(request: HttpRequest) -> HttpResponse:
    """Validate and normalize slug values.

    This is a PRIVATE API.

    For each searchable slug, check its value to see if it can be parsed.
    If it can be, return a normalized value by parsing it and then un-parsing
    it. If it can't be, return false.

    ::

        Format: __api/normalizeinput.json
        Arguments: reqno=<N>
                   Normal search arguments

    Returned JSON is of the format:
        {"slug1": "normalizedval1", "slug2": "normalizedval2",
         "reqno": N}
    """
    if not request or request.GET is None or request.META is None:
        raise Http404(http404_no_request('/__api/normalizeinput.json'))
    (selections, _extras) = url_to_search_params(request.GET,
                                                allow_errors=True,
                                                return_slugs=True,
                                                pretty_results=True)
    if selections is None:
        log.error('api_normalize_input: Could not find selections for'
                  +' request %r', str(request.GET))
        raise Http400Error(http400_search_params_invalid(request))

    reqno = get_reqno(request)
    if reqno is None:
        log.error('api_normalize_input: Missing or badly formatted reqno')
        raise Http400Error(http400_bad_or_missing_reqno(request))
    selections['reqno'] = reqno

    return json_response(selections)


@api_view
def api_string_search_choices(request: HttpRequest, slug: str, *,
                              api_code: int) -> HttpResponse:
    """Return valid choices for a string search given other search criteria.

    This is a PRIVATE API.

    Return all valid choices for a given string search slug given the partial
    search value entered for that slug, its q-type, and the remainder of the
    normal search parameters.

    ::

        Format: __api/stringsearchchoices/<slug>.json
        Arguments: limit=<N>
                   reqno=<N>
                   Normal search arguments

    Returned JSON is of the format:
        {"choices": ["choice1", "choice2"],
         "full_search": true/false,
         "truncated_results": true/false,
         "reqno": N}

    The portion of each choice selected by the partial search is highlighted
    with <b>...</b>.

    full_search is true if the search was so large that it either exceeded the
    query timeout or the maximum count allowed, thus requiring the results
    to be on the entire database. full_search is false if the search was
    performed restricted to the user's other constraints.

    truncated_results is true if the the number of results exceeded the
    specified limit. Only the limit number will be returned.
    """
    if not request or request.GET is None or request.META is None:
        raise Http404(http404_no_request(
                                f'/__api/stringsearchchoices/{slug}.json'))

    reqno = get_reqno(request)
    if reqno is None:
        log.error('api_string_search_choices: Missing or badly formatted reqno')
        raise Http400Error(http400_bad_or_missing_reqno(request))

    param_info = get_param_info_by_slug(slug, 'search')
    if not param_info:
        log.error('api_string_search_choices: unknown slug "%r"',
                  slug)
        raise Http400Error(http400_unknown_slug(slug, request))

    param_qualified_name = param_info.param_qualified_name()
    param_category = param_info.category_name
    param_name = param_info.name

    # obs_general.opus_id is shown to the user in the obs_pds table
    # but searched from the obs_general table. Thus we have to switch the
    # table here to find the parameter and qtype below.
    if param_qualified_name == 'obs_pds.opus_id':
        param_qualified_name = 'obs_general.opus_id'
        param_category = 'obs_general'
        param_name = 'opus_id'

    # We'd really rather not have to use allow_regex_errors here,
    # but the front end will send us search strings with bad regex
    # in the current input field due to the way autocomplete is timed
    # relative to input validation. Note that we'll delete this bad
    # search term later and catch the bad regex below.
    (selections, extras) = url_to_search_params(request.GET,
                                                allow_regex_errors=True)
    if selections is None:
        log.error('api_string_search_choices: Could not find selections for'
                  +' request %r', str(request.GET))
        raise Http400Error(http400_search_params_invalid(request))
    # url_to_search_params returns both dictionaries or neither.
    assert extras is not None

    if param_qualified_name not in selections:
        selections[param_qualified_name] = ['']

    query_qtype_list = []
    query_qtype = 'contains'
    qtypes = extras['qtypes']
    if param_qualified_name in qtypes:
        query_qtype_list = qtypes[param_qualified_name]
        # We convert "matches" to "contains" because when someone is doing a
        # "match" search we still want to give string matches even when they've
        # only entered part of the string.
        if query_qtype_list == ['matches']:
            query_qtype_list = ['contains']
        query_qtype = query_qtype_list[0]
        del qtypes[param_qualified_name]

    # Must do this here before deleting the slug from selections below
    like_query, like_params = get_string_query(selections, param_qualified_name,
                                               query_qtype_list)
    if like_query is None:
        # This is usually caused by a bad regex
        result = {'choices': [],
                  'full_search': True,
                  'truncated_results': False}
        result['reqno'] = reqno
        return json_response(result)

    partial_query = selections[param_qualified_name][0]
    del selections[param_qualified_name]

    user_query_table = get_user_query_table(selections, extras,
                                            api_code=api_code)
    if not user_query_table: # pragma: no cover - internal or database failure
        log.error('api_string_search_choices: get_user_query_table failed '
                  +'*** Selections %r *** Extras %r',
                  str(selections), str(extras))
        return HttpResponseServerError(http500_search_cache_failed(request))

    limit = request.GET.get('limit', settings.DEFAULT_STRINGCHOICE_LIMIT)
    try:
        limit = int(limit)
    except ValueError as err:
        log.error('api_string_search_choices: Bad limit for'
                  +' request %r', str(request.GET))
        raise Http400Error(http400_bad_limit(limit, request)) from err

    if limit < 1 or limit > settings.SQL_MAX_LIMIT:
        log.error('api_string_search_choices: Bad limit for'
                  +' request %r', str(request.GET))
        raise Http400Error(http400_bad_limit(limit, request))

    # We do this because the user may have included characters that aren't
    # allowed in a cache key
    partial_query_hash = hashlib.md5(str.encode(partial_query),
                                     usedforsecurity=False).hexdigest()

    # Is this result already cached?
    cache_key = (settings.CACHE_SERVER_PREFIX + settings.CACHE_KEY_PREFIX
                 +':stringsearchchoices:'
                 +param_qualified_name + ':'
                 +partial_query_hash + ':'
                 +user_query_table + ':'
                 +query_qtype + ':'
                 +str(limit))
    cached_val = cache.get(cache_key)
    if cached_val is not None:
        cached_val['reqno'] = reqno
        return json_response(cached_val)

    param_column = sql_builder.column(param_name, param_category)

    # Check the size of the cache table to see if we can afford to do a
    # search retricted by the cache table contents. The JOIN of the cache
    # table can be slow if it has too many entries and gives a bad user
    # experience.
    sql = sql_builder.count_rows(user_query_table)

    cursor = connection.cursor()
    cursor.execute(sql)
    results = cursor.fetchall()
    if len(results) != 1 or len(results[0]) != 1: # pragma: no cover - database error
        log.error('api_string_search_choices: SQL failure: %r', sql)
        return HttpResponseServerError(http500_database_error(request))

    final_results: list[Any] | None = None
    truncated_results = False

    do_simple_search = False
    count = int(results[0][0])
    if count >= settings.STRINGCHOICE_FULL_SEARCH_COUNT_THRESHOLD:
        do_simple_search = True

    if not do_simple_search:
        max_time = settings.STRINGCHOICE_FULL_SEARCH_TIME_THRESHOLD
        select = sql_builder.Select(distinct=True, max_execution_time=max_time)
        select.add_column(param_column)
        # The cache table is an INNER JOIN because we only want opus_ids
        # that appear in the cache table to cause result rows. The join is on
        # obs_general_id in practice: there are currently no string fields in
        # obs_general, so param_category is never obs_general here.
        select.add_from(param_category).add_join(
            'INNER', user_query_table,
            search_cache_join_condition(param_category, user_query_table))

        if partial_query:
            # get_string_query returns both halves together or neither, and the
            # None case returned above.
            assert like_params is not None
            select.add_where(sql_builder.Expr(like_query, like_params))

        select.add_order_by(param_column)
        select.limit(limit+1)
        sql, sql_params = select.build()

        try:
            cursor.execute(sql, tuple(sql_params))
        except DatabaseError as e:
            if e.args[0] != MYSQL_EXECUTION_TIME_EXCEEDED: # pragma: no cover -
                # database error
                log.exception('api_string_search_choices: "%r" failed', sql)
                return HttpResponseServerError(http500_database_error(request))
            do_simple_search = True

    if do_simple_search:
        # Same thing but no cache table join
        # This will give more results than we really want, but will be much
        # faster
        max_time = settings.STRINGCHOICE_FULL_SEARCH_TIME_THRESHOLD2
        select = sql_builder.Select(distinct=True, max_execution_time=max_time)
        select.add_column(param_column)
        select.add_from(param_category)

        if partial_query:
            # get_string_query returns both halves together or neither, and the
            # None case returned above.
            assert like_params is not None
            select.add_where(sql_builder.Expr(like_query, like_params))

        select.add_order_by(param_column)
        select.limit(limit+1)
        sql, sql_params = select.build()

        try:
            cursor.execute(sql, tuple(sql_params))
        except DatabaseError as e: # pragma: no cover - database error
            if e.args[0] != MYSQL_EXECUTION_TIME_EXCEEDED: # pragma: no cover -
                # database error
                log.exception('api_string_search_choices: "%r" failed', sql)
                return HttpResponseServerError(http500_database_error(request))
            final_results = []

    if final_results is None: # pragma: no cover - can't trigger during testing
        # This is always true except when BOTH queries time out
        final_results = []
        more = True
        while more:
            part_results = cursor.fetchall()
            final_results += part_results
            more = cursor.nextset()

        final_results = [x[0] for x in final_results]
        if partial_query:
            esc_partial_query = partial_query
            if query_qtype != 'regex':
                # Note - there is no regex.escape function available
                esc_partial_query = re.escape(partial_query)
            try:
                # We have to catch all random exceptions here because the
                # compile may fail if the user gives a regex that is bad for
                # the regex library but wasn't caught by _valid_regex
                # because it wasn't bad for MySQL
                pattern = regex.compile(f'({esc_partial_query})',
                                        regex.IGNORECASE | regex.V1)
                final_results = [pattern.sub('<b>\\1</b>', x)
                                 for x in final_results]
            except Exception:
                # Match highlighting is cosmetic. A query that will not compile as a
                # regular expression leaves the text unhighlighted rather than failing
                # the search the user asked for.
                pass  # nosec B110

    if len(final_results) > limit:
        final_results = final_results[:limit]
        truncated_results = True

    result = {'choices': final_results,
              'full_search': do_simple_search,
              'truncated_results': truncated_results}
    cache.set(cache_key, result)
    result['reqno'] = reqno
    return json_response(result)


################################################################################
#
# MAJOR INTERNAL ROUTINES
#
################################################################################

def url_to_search_params(request_get: Mapping[str, str],
                         allow_errors: bool = False,
                         allow_regex_errors: bool = False,
                         return_slugs: bool = False,
                         pretty_results: bool = False,
                         allow_empty: bool = False
                         ) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    """Convert a URL to a set of selections and extras.

    This is the MAIN routine for taking a URL and parsing it for searching.

    OPUS lets users put nice readable things in the URL, like "planet=Jupiter"
    rather than "planet_id=3".

    This function takes the URL params and translates them into a list that
    contains 2 dictionaries::

        The first dict is the user selections: keys of the dictionary are
            param_names of data columns in the data table; values represent
            the user's selections.
        The 2nd dict is any extras being passed by user, like qtypes that
            define what types of queries will be performed for each
            param-value set in the first dict, units for numeric values,
            or sort order.

    **The shape of a selections value depends on the mode flags below**, which is
    why it is annotated as `Any` rather than pinned to one type. In the default
    mode a value is a list, one entry per search clause. Under `return_slugs` it
    is a single value per slug instead -- the empty string for a slug the caller
    sent empty -- and `qtypes` and `units` in the extras change shape with it, to
    one value per slug rather than a list per qualified name. Under
    `pretty_results` a mult value is the joined string rather than the list, and
    a numeric value is the text it formats to rather than the number.

    NOTE: Pass request_get = request.GET to this func please (This func doesn't
    return an http response so unit tests freak if you pass it an HTTP request)

    If allow_errors is True, then even if a value can't be parsed, the rest
    of the slugs are processed and the bad slug is just marked with None.

    If allow_regex_errors is True, then even if a regex is badly formatted,
    the rest of the slugs are processed and the bad slug is just marked with
    None.

    If return_slugs is True, the indexes into selections are slug names, not
    qualified names (table.column).

    If pretty_results is True, the resulting values are unparsed back into
    strings based on the ParamInfo format.

    If allow_empty is True, then search terms that have no values for either
    min or max are kept. This is used to create UI forms for search widgets.

    Example command line usage::

        from opus_app.apps.search.views import *
        from django.http import QueryDict
        q = QueryDict("planet=Saturn&bundleid=COISS_2&qtype-bundleid=begins&rightasc1=10&order=time1,-RINGGEOringcenterdistance")
        (selections,extras) = url_to_search_params(q)
        selections
            {'obs_general.planet_id': ['Saturn'],
             'obs_pds.bundle_id': ['COISS_2'],
             'obs_general.right_asc1': [10.0],
             'obs_general.right_asc2': [None]}
        extras
            {'order': (['obs_general.time1',
                        'obs_ring_geometry.ring_center_distance',
                        'obs_general.opus_id'],
                       [False, True, False]),
             'qtypes': {'obs_pds.bundle_id': ['begins'],
                        'obs_general.right_asc': ['any']},
             'units': {'obs_general.right_asc': ['degrees']}}
    """
    # selections is deliberately `Any`-valued: what a value holds is decided by
    # this function's mode flags, and the docstring above states the shape each
    # mode produces. qtypes and units are uniform and are typed exactly.
    selections: dict[str, Any] = {}
    extras: dict[str, Any] = {}
    qtypes: dict[str, Any] = {}
    units: dict[str, Any] = {}
    order_params: list[str] | None = []
    order_descending_params: list[bool] | None = []

    # Note that request_get.items() automatically gets rid of duplicate entries
    # because it returns a dict.
    search_params = list(request_get.items())
    used_slugs = []

    if 'order' not in [x[0] for x in search_params]:
        # If there's no order slug, then force one
        search_params.append(('order', settings.DEFAULT_SORT_ORDER))

    # Go through the search_params one at a time and use whatever slug we find
    # to look for the other ones we could be paired with.
    for slug, value in search_params:
        orig_slug = slug
        if slug in used_slugs:
            continue

        if slug == 'order':
            all_order = value
            order_params, order_descending_params = parse_order_slug(all_order)
            if order_params is None:
                return None, None
            extras['order'] = (order_params, order_descending_params)
            used_slugs.append(slug)
            continue

        if slug in settings.SLUGS_NOT_IN_DB:
            used_slugs.append(slug)
            continue

        # STRING and RANGE types can can have multiple clauses ORed together by
        # putting "_NNN" after the slug name.
        clause_num = 1
        clause_num_str = ''
        if '_' in slug:
            clause_num_str = slug[slug.rindex('_'):]
            try:
                clause_num = int(clause_num_str[1:])
                if clause_num > 0:
                    slug = slug[:slug.rindex('_')]
                else:
                    raise ValueError
            except ValueError:
                # If clause_num is not a positive integer, leave the slug as is.
                # If the slug is unknown, it will be caught later as an unknown
                # slug.
                clause_num = 1
                clause_num_str = ''

        # Find the master param_info
        param_info = None
        # The unit is the unit we want the field to be in
        is_unit = None
        # The sourceunit is used by normalizeurl to allow the conversion of
        # values from one unit to another. The original unit is available in
        # "sourceunit" and the desination unit is available in "unit".
        # sourceunit should not be used anywhere else.
        if slug.startswith('qtype-'): # like qtype-time=all
            slug = slug[6:]
            slug_no_num = strip_numeric_suffix(slug)
            if slug_no_num != slug:
                log.error('url_to_search_params: qtype slug has '+
                          'numeric suffix "%r"', orig_slug)
                return None, None
            param_info = get_param_info_by_slug(slug, 'qtype')
        elif slug.startswith('unit-'): # like unit-observationduration=msec
            is_unit = True
            slug = slug[5:]
            slug_no_num = strip_numeric_suffix(slug)
            if slug_no_num != slug:
                log.error('url_to_search_params: unit slug has '+
                          'numeric suffix "%r"', orig_slug)
                return None, None
            param_info = get_param_info_by_slug(slug, 'qtype')
        elif slug.startswith('sourceunit-'):
            slug = slug[11:]
            slug_no_num = strip_numeric_suffix(slug)
            if slug_no_num != slug:
                log.error('url_to_search_params: sourceunit slug has '+
                          'numeric suffix "%r"', orig_slug)
                return None, None
            param_info = get_param_info_by_slug(slug, 'qtype')
        else:
            param_info = get_param_info_by_slug(slug, 'search')
        if not param_info:
            log.error('url_to_search_params: unknown slug "%r"',
                      orig_slug)
            return None, None

        slug_no_num = strip_numeric_suffix(slug)

        param_qualified_name = param_info.param_qualified_name()
        if param_qualified_name == 'obs_pds.opus_id':
            # Force OPUS_ID to be searched from obs_general for efficiency
            # even though the user sees it in PDS Constraints.
            param_qualified_name = 'obs_general.opus_id'
        param_qualified_name_no_num = strip_numeric_suffix(param_qualified_name)
        (form_type, form_type_format,
         form_type_unit_id) = parse_form_type(param_info.form_type)
        valid_units = get_valid_units(form_type_unit_id)

        if param_info.slug: # pragma: no cover - currently always true
            # Kill off all the original slugs
            pi_slug_no_num = strip_numeric_suffix(param_info.slug)
            used_slugs.append(pi_slug_no_num+clause_num_str)
            used_slugs.append(pi_slug_no_num+'1'+clause_num_str)
            used_slugs.append(pi_slug_no_num+'2'+clause_num_str)
            used_slugs.append('qtype-'+pi_slug_no_num+clause_num_str)
            used_slugs.append('unit-'+pi_slug_no_num+clause_num_str)
            used_slugs.append('sourceunit-'+pi_slug_no_num+clause_num_str)
        if param_info.old_slug:
            # Kill off all the old slugs - this prevents cases where someone
            # uses the new slug and old slug names in the same query.
            pi_old_slug_no_num = strip_numeric_suffix(param_info.old_slug)
            used_slugs.append(pi_old_slug_no_num+clause_num_str)
            used_slugs.append(pi_old_slug_no_num+'1'+clause_num_str)
            used_slugs.append(pi_old_slug_no_num+'2'+clause_num_str)
            used_slugs.append('qtype-'+pi_old_slug_no_num+clause_num_str)
            used_slugs.append('unit-'+pi_old_slug_no_num+clause_num_str)
            used_slugs.append('sourceunit-'+pi_old_slug_no_num+clause_num_str)

        # Look for an associated qtype.
        # Use the original slug name here since we hope if someone says
        # XXX=5 then they also say qtype-XXX=all
        qtype_slug = 'qtype-'+slug_no_num+clause_num_str
        valid_qtypes: tuple[str, ...] | None = None
        if form_type not in settings.MULT_FORM_TYPES:
            valid_qtypes = settings.STRING_QTYPES
            if form_type in settings.RANGE_FORM_TYPES:
                valid_qtypes = settings.RANGE_QTYPES
        qtype_val = None
        if qtype_slug in request_get:
            qtype_val = request_get[qtype_slug].lower()
            if valid_qtypes is None or qtype_val not in valid_qtypes:
                if allow_errors: # pragma: no cover - protection against future bugs
                    # We never actually hit this because normalizeurl catches
                    # the bad qtype first
                    qtype_val = None
                else:
                    log.error('url_to_search_params: Bad qtype value for '
                              +'"%r": %r', qtype_slug, str(qtype_val))
                    return None, None
        else:
            if valid_qtypes is not None:
                qtype_val = valid_qtypes[0] # Default if not specified

        # Look for an associated unit.
        # Use the original slug name here since we hope if someone says
        # XXX=5 then they also say unit-XXX=msec
        unit_slug = 'unit-'+slug_no_num+clause_num_str
        unit_val = None
        if unit_slug in request_get:
            unit_val = request_get[unit_slug].lower()
            if valid_units is None or unit_val not in valid_units:
                if allow_errors: # pragma: no cover - protection against future bugs
                    # We never actually hit this because normalizeurl catches
                    # the bad unit first
                    unit_val = None
                else:
                    log.error('url_to_search_params: Bad unit value for '
                              +'"%r": %r', unit_slug, str(unit_val))
                    return None, None
        else:
            # Default if not specified
            unit_val = get_default_unit(form_type_unit_id)

        # Look for an associated sourceunit. Sourceunits are created by the UI
        # when the user changes the unit selection on a range widget, so this
        # URL has never passed through normalizeurl.
        # Use the original slug name here since we hope if someone says
        # XXX=5 then they also say sourceunit-XXX=msec
        sourceunit_slug = 'sourceunit-'+slug_no_num+clause_num_str
        # sourceunit_val will be the same as unit_val if sourceunit_slug doesn't
        # exist in the URL
        sourceunit_val = unit_val
        if sourceunit_slug in request_get:
            sourceunit_val = request_get[sourceunit_slug].lower()
            if (valid_units is None or
                sourceunit_val not in valid_units):
                log.error('url_to_search_params: Bad sourceunit value'
                          +' for "%r": %r', sourceunit_slug,
                          str(sourceunit_val))
                if allow_errors: # pragma: no cover -
                    # sourceunit can only show up when called from
                    # normalizeinput, in which case allow_errors is always
                    # True. Since this is an internal error in the UI,
                    # we don't want to throw any kind of error that would freeze
                    # the UI, so we just pretend the sourceunit value wasn't
                    # specified and hope someone looks at the error log.
                    sourceunit_val = None
                else: # pragma: no cover
                    return None, None

        if form_type in settings.MULT_FORM_TYPES:
            # MULT types have no qtype, units, or 1/2 split.
            # They also can't accept a clause number.
            if clause_num_str:
                log.error('url_to_search_params: Mult field "%r" has clause'
                          +' number where none permitted', orig_slug)
                return None, None
            # Presence of qtype or unit slug will be caught earalier

            # If nothing is specified, just ignore the slug.
            values = [x.strip() for x in value.split(',')]
            has_value = False
            for value in values:
                if value:
                    has_value = True
                    break
            if not has_value:
                if pretty_results and return_slugs: # pragma: no cover -
                    # These must be true in the current usage
                    selections[slug] = ""
                continue
            # Mult form types can be sorted and uniquified to save duplicate
            # queries being built.
            # No other form types can be sorted since their ordering
            # corresponds to qtype/unit ordering.
            new_val: list[str] | str | None = sorted(set(values))
            # Now check to see if the mult values are all valid
            mult_name = get_mult_name(param_qualified_name)
            model_name = mult_name.title().replace('_','')
            model = apps.get_model('search', model_name)
            mult_values = [x['pk'] for x in
                           list(model.objects.filter(  Q(label__in=new_val)
                                                     | Q(value__in=new_val))
                                             .values('pk'))]
            # Still the sorted list here: the join and the None replacement
            # below are the only things that change what this name holds.
            assert isinstance(new_val, list)
            if len(mult_values) != len(new_val):
                if allow_errors:
                    new_val = None
                else:
                    log.error('url_to_search_params: Bad mult data for "%r", '
                              +'wanted "%r" found "%r"',
                              param_qualified_name, str(new_val),
                              str(mult_values))
                    return None, None
            if pretty_results and new_val:
                new_val = ','.join(new_val)
            if return_slugs:
                selections[slug] = new_val
            else:
                selections[param_qualified_name] = new_val
            continue

        # This is either a RANGE or a STRING type.

        if form_type in settings.RANGE_FORM_TYPES:
            # For RANGE form types, there can be 1/2 slugs. Just ignore the slug
            # we're currently looking at and start over for simplicity.
            new_param_qualified_names = []
            new_values = []

            for suffix in ('1', '2'):
                new_slug = slug_no_num+suffix+clause_num_str
                new_param_qualified_name = param_qualified_name_no_num+suffix
                new_value: float | str | None = None
                if new_slug in request_get:
                    value = request_get[new_slug].strip()
                    if value:
                        try:
                            # Convert the strings into the internal
                            # representation if necessary. If there is a
                            # sourceunit slug, then we parse the value as
                            # sourceunit, convert it to default as
                            # sourceunit, and convert it back to unit to do the
                            # unit conversion.
                            new_value = parse_unit_value(value,
                                                         form_type_format,
                                                         form_type_unit_id,
                                                         sourceunit_val)
                            if sourceunit_val is not None:
                                default_val = (convert_to_default_unit(
                                                    new_value,
                                                    form_type_unit_id,
                                                    sourceunit_val))
                                new_value = (convert_from_default_unit(
                                                    default_val,
                                                    form_type_unit_id,
                                                    unit_val))

                            # Do a conversion of the given value to the default
                            # units. We do this so that if the conversion throws
                            # an error (like overflow), we mark this search
                            # term as invalid, since it will fail later in
                            # construct_query_string anyway. This allows
                            # normalizeinput to report it as bad immediately.
                            default_val = convert_to_default_unit(
                                                new_value,
                                                form_type_unit_id,
                                                unit_val)

                            if pretty_results:
                                # We keep the returned value in the original
                                # unit rather than converting it, but we have
                                # to specify the unit here so the number
                                # of digits after the decimal can be adjusted.
                                # The actual conversion to the default unit
                                # will happen when creating a query.
                                new_value = format_unit_value(
                                                    new_value, form_type_format,
                                                    form_type_unit_id,
                                                    unit_val,
                                                    convert_from_default=False)
                        except ValueError as e:
                            new_value = None
                            if not allow_errors:
                                log.error('url_to_search_params: Unit ID "%r" '
                                          +'slug "%r" source unit "%r" unit '
                                          +'"%r" threw ValueError(%r) for %r',
                                          form_type_unit_id, slug,
                                          sourceunit_val, unit_val,
                                          e, value)
                                return None, None
                    else:
                        new_value = None
                    if return_slugs:
                        # Always put values for present slugs in for
                        # return_slugs
                        if value == '':
                            selections[new_slug] = ''
                        else:
                            selections[new_slug] = new_value
                new_param_qualified_names.append(new_param_qualified_name)
                new_values.append(new_value)
            if return_slugs:
                if not is_single_column_range(param_qualified_name_no_num):
                    # Always include qtype no matter what
                    if param_qualified_name_no_num not in qtypes: # pragma: no cover -
                        # This should always be true because we only hit
                        # this once for each slug
                        qtypes[param_qualified_name_no_num] = []
                    qtypes[param_qualified_name_no_num].append(qtype_val)
                # Always include unit no matter what
                if param_qualified_name_no_num not in units: # pragma: no cover -
                    # This should always be true because we only hit
                    # this once for each slug
                    units[param_qualified_name_no_num] = []
                units[param_qualified_name_no_num].append(unit_val)
            elif (allow_empty or
                  new_values[0] is not None or
                  new_values[1] is not None): # pragma: no cover -
                # One of these must be true in current usage
                # If both values are None, then don't include this slug at all
                if new_param_qualified_names[0] not in selections:
                    selections[new_param_qualified_names[0]] = []

                if allow_empty and clause_num_str:
                    range_min_selection = selections[
                                                new_param_qualified_names[0]]
                    len_min = len(range_min_selection)
                    # Note: clause_num here will not be a very large
                    # number because allow_empty is only True when it's
                    # called from api_get_widget, and in that case,
                    # clause numbers have already been normalized.
                    if len_min < clause_num: # pragma: no cover -
                        # This will always be True because the normalized
                        # clause numbers will be in order, and thus it will
                        # always be necessary to add a new entry.
                        range_min_selection += [None] * (clause_num-len_min)
                    range_min_selection[clause_num-1] = new_values[0]
                else:
                    selections[new_param_qualified_names[0]].append(
                                                                new_values[0])

                if new_param_qualified_names[1] not in selections:
                    selections[new_param_qualified_names[1]] = []

                if allow_empty and clause_num_str:
                    range_max_selection = selections[
                                                new_param_qualified_names[1]]
                    len_max = len(range_max_selection)
                    if len_max < clause_num: # pragma: no cover -
                        # This will always be True because the normalized
                        # clause numbers will be in order, and thus it will
                        # always be necessary to add a new entry.
                        range_max_selection += [None] * (clause_num-len_max)
                    range_max_selection[clause_num-1] = new_values[1]
                else:
                    selections[new_param_qualified_names[1]].append(
                                                                new_values[1])

                if not is_single_column_range(param_qualified_name_no_num):
                    # There was at least one value added or allow_empty
                    # is set - include the qtype
                    if param_qualified_name_no_num not in qtypes:
                        qtypes[param_qualified_name_no_num] = []

                    if allow_empty and clause_num_str:
                        range_qtype = qtypes[param_qualified_name_no_num]
                        len_qtype = len(range_qtype)
                        if len_qtype < clause_num: # pragma: no cover -
                            # This will always be True because the normalized
                            # clause numbers will be in order, and thus it will
                            # always be necessary to add a new entry.
                            range_qtype += [None] * (clause_num-len_qtype)
                        range_qtype[clause_num-1] = qtype_val
                    else:
                        qtypes[param_qualified_name_no_num].append(
                                                               qtype_val)

                # There was at least one value added - include the unit
                if param_qualified_name_no_num not in units:
                    units[param_qualified_name_no_num] = []
                units[param_qualified_name_no_num].append(unit_val)
            continue

        # For STRING form types, there is only a single slug. Just ignore the
        # slug we're currently looking at and start over for simplicity.
        if is_unit or unit_val is not None: # pragma: no cover -
            # We shouldn't ever get here because string fields have no valid
            # units and this will be caught above
            log.error('url_to_search_params: String field "%r" has unit',
                      orig_slug)
            return None, None
        new_value = ''
        new_slug = slug_no_num+clause_num_str
        if new_slug in request_get:
            new_value = request_get[new_slug]
        if (new_value and qtype_val == 'regex' and not allow_regex_errors
                and not _valid_regex(new_value)):
            if not allow_errors:
                log.error('url_to_search_params: String "%r" '
                          +'slug "%r" is not a valid regex',
                          new_value, slug)
                return None, None
            new_value = None
        if return_slugs:
            selections[new_slug] = new_value
            qtypes[new_slug] = qtype_val
            units[new_slug] = unit_val
        elif (allow_empty or
              (new_value is not None and
               new_value != '')): # pragma: no cover -
            # This will always be True because the normalized
            # clause numbers will be in order, and thus it will
            # always be necessary to add a new entry.
            # If the value is None or '', then don't include this slug at all
            if new_value == '':
                new_value = None
            if param_qualified_name_no_num not in selections:
                selections[param_qualified_name_no_num] = []

            if allow_empty and clause_num_str:
                str_selection = selections[param_qualified_name_no_num]
                len_s = len(str_selection)
                if len_s < clause_num:
                    str_selection += [None] * (clause_num-len_s)
                str_selection[clause_num-1] = new_value
            else:
                selections[param_qualified_name_no_num].append(new_value)

            if param_qualified_name_no_num not in qtypes:
                qtypes[param_qualified_name_no_num] = []

            if allow_empty and clause_num_str:
                str_qtype = qtypes[param_qualified_name_no_num]
                len_qtype = len(str_qtype)
                if len_qtype < clause_num:
                    str_qtype += [None] * (clause_num-len_qtype)
                str_qtype[clause_num-1] = qtype_val
            else:
                qtypes[param_qualified_name_no_num].append(qtype_val)

    extras['qtypes'] = qtypes
    extras['units'] = units

    # log.debug('url_to_search_params: GET %r *** Selections %r *** Extras %r',
    #           request_get, str(selections), str(extras))

    return selections, extras


def get_user_query_table(selections: dict[str, Any], extras: dict[str, Any],
                         api_code: int | None = None) -> str | None:
    """Perform a data search and create a table of matching IDs.

    This is THE main data query place.

    - Look in the "user_searches" table to see if this search has already
      been requested before. If so, retrieve the cache table number. If not,
      create the entry in "user_searches", which assigns a cache table number.
    - See if the cache table name has been cached in memory. (This means that
      we are SURE the table actually exists and don't have to check again)

      - If so, return the cached table name.

    - Otherwise, try to perform the search and store the results in the
      cache_NNN table.

      - If the table already existed, or was in the process of being created
        by another process, this will throw an error (after possibly waiting for
        the lock to clear), which we ignore.

    - Store the cache table name in the memory cache and return it. (At this
      point we KNOW the table exists and has been fully populated)

    The cache_NNN table has two columns::

        1) sort_order: A unique, monotonically increasing id that gives the
           order of the results based on the sort order requested when the
           search was done.
        2) id: A unique is corresponding to the obs_general.id of the
           observation.

    Note: `url_to_search_params` takes the user HTTP request object and creates the
    data objects that are passed to this function.
    """
    cursor = connection.cursor()

    # Create a cache key
    cache_table_num, _cache_new_flag = set_user_search_number(selections, extras)
    if cache_table_num is None: # pragma: no cover - database error
        log.error('get_user_query_table: Failed to make entry in user_searches'+
                  ' *** Selections %r *** Extras %r',
                  str(selections), str(extras))
        return None
    cache_table_name = get_user_search_table_name(cache_table_num)

    # Is this key set in the cache?
    cache_key = (settings.CACHE_SERVER_PREFIX + settings.CACHE_KEY_PREFIX
                 + ':cache_table:' + str(cache_table_num))
    cached_val: str | None = cache.get(cache_key)
    if cached_val:
        return cached_val

    # Try to create the table using the selection criteria.
    # If the table already exists from earlier, this will throw a
    # MYSQL_TABLE_ALREADY_EXISTS exception and we can just return the table
    # name.
    # If the table is in the process of being created by another process,
    # the CREATE TABLE will hang due to the lock and eventually return
    # when the CREATE TABLE is finished, at which point it will throw
    # a MYSQL_TABLE_ALREADY_EXISTS exception and we can just return the table
    # name.
    sql, params = construct_query_string(selections, extras)
    if sql is None: # pragma: no cover - already caught by previous checks
        log.error('get_user_query_table: construct_query_string failed'
                  +' *** Selections %r *** Extras %r',
                  str(selections), str(extras))
        return None

    if not sql: # pragma: no cover - not possible
        log.error('get_user_query_table: Query string is empty'
                  +' *** Selections %r *** Extras %r',
                  str(selections), str(extras))
        return None

    # With this we can create a table that contains the single column
    create_sql = sql_builder.create_table_from_select_sql(
        cache_table_name, sql,
        column_defs=sql_builder.CACHE_TABLE_COLUMN_DEFS)
    # construct_query_string returns both halves together or neither, and the
    # caller checked the SQL half above.
    assert params is not None
    try:
        time1 = time.time()
        cursor.execute(create_sql, tuple(params))
    except DatabaseError as e: # pragma: no cover -
        # This can only happen when multiple processes are accessing the
        # database at the same time
        if e.args[0] == MYSQL_TABLE_ALREADY_EXISTS: # pragma: no cover - ditto
            cache.set(cache_key, cache_table_name)
            return cache_table_name
        log.exception('get_user_query_table: "%r" with params "%r" failed',
                      create_sql, str(tuple(params)))
        return None
    log.debug('API %r (%.3f) get_user_query_table: %r *** PARAMS %r',
              str(api_code), time.time()-time1, create_sql, str(params))

    cache.set(cache_key, cache_table_name)
    return cache_table_name


def set_user_search_number(selections: dict[str, Any], extras: dict[str, Any]
                           ) -> tuple[int, bool]:
    """Creates a new row in the user_searches table for each search request.

    This table lists query params+values plus any extra info needed to
    run a data search query.
    This method looks in user_searches table for current selections.
    If none exist, creates it.

    Returns the number of the cache table that should be used along with a flag
    indicating if this is a new entry in user_searches so the cache table
    shouldn't exist yet.
    """
    selections_json = str(json.dumps(sort_dictionary(selections)))
    selections_hash = hashlib.md5(str.encode(selections_json),
                                  usedforsecurity=False).hexdigest()

    qtypes_json = None
    qtypes_hash = 'NONE' # Needed for UNIQUE constraint to work
    if 'qtypes' in extras:
        qtypes = extras['qtypes']
        # Remove qtypes that aren't used for searching because they don't
        # do anything to make the search unique
        new_qtypes = {}
        for qtype, val in qtypes.items():
            qtype_no_num = strip_numeric_suffix(qtype)
            if (qtype_no_num in selections or
                qtype_no_num+'1' in selections or
                qtype_no_num+'2' in selections):
                new_qtypes[qtype] = val
        if len(new_qtypes):
            qtypes_json = str(json.dumps(sort_dictionary(new_qtypes)))
            qtypes_hash = hashlib.md5(str.encode(qtypes_json),
                                      usedforsecurity=False).hexdigest()

    units_json = None
    units_hash = 'NONE' # Needed for UNIQUE constraint to work
    if 'units' in extras:
        units = extras['units']
        # Remove units that aren't used for searching because they don't
        # do anything to make the search unique
        new_units = {}
        for unit, val in units.items():
            unit_no_num = strip_numeric_suffix(unit)
            if (unit_no_num in selections or
                unit_no_num+'1' in selections or
                unit_no_num+'2' in selections):
                new_units[unit] = val
        if len(new_units):
            units_json = str(json.dumps(sort_dictionary(new_units)))
            units_hash = hashlib.md5(str.encode(units_json),
                                     usedforsecurity=False).hexdigest()

    order_json = None
    order_hash = 'NONE' # Needed for UNIQUE constraint to work
    if 'order' in extras and extras['order'][0]:
        order_json = str(json.dumps(extras['order']))
        order_hash = hashlib.md5(str.encode(order_json),
                                 usedforsecurity=False).hexdigest()

    cache_key = (settings.CACHE_SERVER_PREFIX + settings.CACHE_KEY_PREFIX
                 +':usersearchno:selections_hash:' + str(selections_hash)
                 +':qtypes_hash:' + str(qtypes_hash)
                 +':units_hash:' + str(units_hash)
                 +':order_hash:' + str(order_hash))
    cached_val = cache.get(cache_key)
    if cached_val is not None:
        return cached_val, False

    # This operation has to be atomic because multiple threads may be trying
    # to lookup/create the same selections entry at the same time. Thus,
    # rather than looking it up, and then creating it if it doesn't exist
    # (which leaves a nice hole for two threads to try to create it
    # simultaneously), instead we go ahead and try to create it and let the
    # UNIQUE CONSTRAINT on the hash fields throw an error if it already exists.
    # That gives us an atomic write.
    new_entry = False
    s = UserSearches(selections_json=selections_json,
                     selections_hash=selections_hash,
                     qtypes_json=qtypes_json,
                     qtypes_hash=qtypes_hash,
                     units_json=units_json,
                     units_hash=units_hash,
                     order_json=order_json,
                     order_hash=order_hash)
    try:
        s.save()
        new_entry = True
    except IntegrityError:
        # This means it's already there and we tried to duplicate the constraint
        s = UserSearches.objects.get(selections_hash=selections_hash,
                                     qtypes_hash=qtypes_hash,
                                     units_hash=units_hash,
                                     order_hash=order_hash)
    except UserSearches.MultipleObjectsReturned: # pragma: no cover -
        # This would only happen if the database is corrupted
        duplicates = UserSearches.objects.filter(selections_hash=selections_hash,
                                        qtypes_hash=qtypes_hash,
                                        units_hash=units_hash,
                                        order_hash=order_hash)
        s = duplicates[0]
        log.exception('set_user_search_number: Multiple entries in user_searches'
                      +' for *** Selections %r *** Qtypes %r *** Units %r '
                      +' *** Order %r',
                      str(selections_json),
                      str(qtypes_json),
                      str(units_json),
                      str(order_json))

    cache.set(cache_key, s.id)
    return s.id, new_entry


# get_param_info_by_slug is called a LOT and turns out to take a significant
# fraction of the execution time since it has to do at least one, and probably
# multiple, database lookups each time it's called. Thus we cache the results.
# We don't use the functools @lru_cache decorator because we need to make
# each return a distinct copy of the ParamInfo, because multiple callers
# mutate the structure after its returned.
_PARAMINFO_CACHE: dict[Any, Any] = {}

@overload
def get_param_info_by_slug(slug: str, source: Literal['col'],
                           allow_units_override: Literal[True],
                           check_valid_units: bool = True
                           ) -> tuple[ParamInfo | None, str | None]: ...


@overload
def get_param_info_by_slug(slug: str, source: str,
                           allow_units_override: Literal[False] = False,
                           check_valid_units: bool = True) -> ParamInfo | None: ...


def get_param_info_by_slug(slug: str, source: str,
                           allow_units_override: bool = False,
                           check_valid_units: bool = True
                           ) -> ParamInfo | tuple[ParamInfo | None, str | None] | None:
    """Given a slug, look up the corresponding ParamInfo.

    If source == 'col', then this is a column name. We look at the
    slug name as given (current or old). If allow_units_override is True and
    a unit is specified with ":unit", we ignore it when searching for the ParamInfo.
    If check_valid_units is True, we verify that the specified unit is one that is
    permitted on this slug, and reset it to the default if it is a bad unit.
    If check_valid_units is False, we simply return the specified unit, if any, without
    checking. This is useful for normalizeurl.

    If source == 'widget', then this is a widget name. Widget names have a
    '1' on the end even if they are single-column ranges, so we just remove the
    '1' before searching if we don't find the original name.

    If source == 'qtype', then this is a qtype for a column. Qtypes don't have
    any numeric suffix, even if though the columns do, so we just add on a '1'
    if we don't find the original name. This also gets used for looking up
    'unit' slugs.

    If source == 'search', then this is a search term. Numeric search terms
    can always have a '1' or '2' suffix even for single-column ranges.

    The return value is the ParamInfo structure. In the case of source == 'col' and
    allow_units_override == True, the return is a tuple consisting of the ParamInfo
    and the requested unit string.
    """
    assert source in ('col', 'widget', 'qtype', 'search')

    # Qtypes are forbidden from having a numeric suffix`
    if source == 'qtype' and slug[-1] in ('1', '2'): # pragma: no cover -
        # always caught by caller
        log.error('get_param_info_by_slug: Qtype slug "%r" has unpermitted '+
                  'numeric suffix', slug)
        return None

    desired_units = None
    if source == 'col' and allow_units_override and ':' in slug:
        slug, _, desired_units = slug.partition(':')
        desired_units = desired_units.lower()

    pi = None
    key = (slug, source)
    if key in _PARAMINFO_CACHE:
        pi = _PARAMINFO_CACHE[key]
    else:
        # Current slug as given
        try:
            pi = ParamInfo.objects.get(slug=slug)
        except ParamInfo.DoesNotExist:
            pass

        if not pi:
            # Old slug as given
            try:
                pi = ParamInfo.objects.get(old_slug=slug)
            except ParamInfo.DoesNotExist:
                pass

    if pi:
        if source == 'col' and allow_units_override: # pragma: no cover -
            # always caught by caller
            if (check_valid_units and desired_units is not None and
                not pi.is_valid_unit(desired_units)):
                log.error('get_param_info_by_slug: Slug "%r" unit "%r" invalid -'
                          'using default', slug, desired_units)
                desired_units = None
            _PARAMINFO_CACHE[key] = pi
            return copy.copy(pi), desired_units

        if source == 'search':
            if slug[-1] in ('1', '2'):
                # Search slug has 1/2, param_info has 1/2 - all is good
                return pi
            # For a single-column range, the slug we were given MUST end
            # in a '1' or '2' - but for non-range types, it's OK to not
            # have the '1' or '2'. Note the non-single-column ranges were
            # already dealt with above.
            (form_type, _form_type_format,
             _form_type_unit_id) = parse_form_type(pi.form_type)
            if form_type in settings.RANGE_FORM_TYPES: # pragma: no cover -
                # We are missing the numeric suffix - import error
                return None

        _PARAMINFO_CACHE[key] = pi
        return copy.copy(pi)

    # For widgets, if this is a multi-column range, return the version with
    # the '1' suffix.
    if source == 'widget':
        try:
            pi = ParamInfo.objects.get(slug=slug+'1')
        except ParamInfo.DoesNotExist:
            pass
        if not pi:
            try:
                pi = ParamInfo.objects.get(old_slug=slug+'1')
            except ParamInfo.DoesNotExist:
                pass
        if pi:
            _PARAMINFO_CACHE[key] = pi
            return copy.copy(pi)

    # Q-types can never have a '1' or '2' suffix, but the database entries
    # might.
    if source == 'qtype' and slug[-1] not in ('1', '2'):
        try:
            pi = ParamInfo.objects.get(slug=slug+'1')
        except ParamInfo.DoesNotExist:
            pass
        if not pi:
            try:
                pi = ParamInfo.objects.get(old_slug=slug+'1')
            except ParamInfo.DoesNotExist:
                pass
        if pi:
            _PARAMINFO_CACHE[key] = pi
            return copy.copy(pi)

    # Searching on a single-column range is done with '1' or '2' suffixes
    # even though the database entry is just a single column without a numeric
    # suffix.
    if source == 'search' and (slug[-1] == '1' or slug[-1] == '2'):
        try:
            pi = ParamInfo.objects.get(slug=slug[:-1])
        except ParamInfo.DoesNotExist:
            pass
        if not pi:
            try:
                pi = ParamInfo.objects.get(old_slug=slug[:-1])
            except ParamInfo.DoesNotExist:
                pass
        if pi:
            (form_type, _form_type_format,
             _form_type_unit_id) = parse_form_type(pi.form_type)
            if form_type not in settings.RANGE_FORM_TYPES:
                # Whoops! It's not a range, but we have a numeric suffix.
                return None
            _PARAMINFO_CACHE[key] = pi
            return copy.copy(pi)

    _PARAMINFO_CACHE[key] = None

    log.error('get_param_info_by_slug: Slug "%r" source "%r" not found',
              slug, source)

    if source == 'col' and allow_units_override:
        return None, None

    return None

################################################################################
#
# CREATE AN SQL QUERY
#
################################################################################

def construct_query_string(selections: dict[str, Any], extras: dict[str, Any]
                           ) -> tuple[str | None, list[Any] | None]:
    """Given a set selections,extras generate the appropriate SQL SELECT"""
    all_qtypes = extras.get('qtypes', [])
    all_units = extras.get('units', [])
    finished_ranges = []    # Ranges are done for both sides at once so track
                            # which are finished to avoid duplicates

    clauses = []
    obs_tables = set()
    mult_tables = set()

    # We always have to have obs_general since it's the master keeper of IDs
    obs_tables.add('obs_general')

    # We sort this so that testing results are predictable
    for param_qualified_name in sorted(selections.keys()):
        value_list = selections[param_qualified_name]
        # Lookup info about this param_qualified_name
        param_qualified_name_no_num = strip_numeric_suffix(param_qualified_name)
        param_info = _get_param_info_by_qualified_name(param_qualified_name)
        if not param_info:
            log.error('construct_query_string: No param_info for "%r"'
                      +' *** Selections %r *** Extras *** %r',
                      param_qualified_name,
                      str(selections), str(extras))
            return None, None
        cat_name = param_info.category_name

        if param_qualified_name_no_num in all_qtypes:
            qtypes = all_qtypes[param_qualified_name_no_num]
        else:
            qtypes = []
        if param_qualified_name_no_num in all_units:
            units = all_units[param_qualified_name_no_num]
        else:
            units = []

        (form_type, _form_type_format,
         _form_type_unit_id) = parse_form_type(param_info.form_type)

        if form_type in settings.MULT_FORM_TYPES:
            # This is where we convert from the "pretty" name the user selected
            # to the internal name stored in the database and mapped to the
            # mult table.
            mult_name = get_mult_name(param_qualified_name)
            model_name = mult_name.title().replace('_','')
            model = apps.get_model('search', model_name)
            mult_values = [x['pk'] for x in
                           list(model.objects.filter(  Q(label__in=value_list)
                                                     | Q(value__in=value_list))
                                             .values('pk'))]
            if len(mult_values) != len(value_list):
                log.error('construct_query_string: Bad mult data for "%r", '
                          +'found %r'
                          +' *** Selections %r *** Extras *** %r',
                          param_qualified_name,
                          str(mult_values), str(selections), str(extras))
                return None, None
            if mult_values:
                mult_column = sql_builder.column(param_info.name, cat_name)
                mult_clause: sql_builder.Expr
                if form_type == 'GROUP':
                    # Single-valued mult. We can be efficient by seeing if the field
                    # contents is in the list of search values.
                    mult_clause = sql_builder.in_values(mult_column, mult_values)
                else:
                    # Multi-valued mult (multisel). We have to see if each search value
                    # is in the database field list, so we have to check them one by one.
                    mult_clause = sql_builder.join_exprs(
                        [sql_builder.json_contains(mult_column, str(mult_value))
                         for mult_value in mult_values], 'OR')
                clauses.append(mult_clause)
                obs_tables.add(cat_name)

        elif form_type in settings.RANGE_FORM_TYPES:
            # This prevents range queries from getting through twice.
            # If one range side has been processed we can skip the 2nd, because
            # it gets done when the first is.
            if param_qualified_name_no_num in finished_ranges:
                continue

            finished_ranges.append(param_qualified_name_no_num)

            # Longitude queries
            if form_type == 'LONG':
                # This parameter requires a longitudinal query.
                # Both sides of range must be defined by user for this to work.
                clause, params = get_longitude_query(selections,
                                                     param_qualified_name,
                                                     qtypes, units)
            else:
                # Get the range query object and append it to the query
                clause, params = get_range_query(selections,
                                                 param_qualified_name,
                                                 qtypes, units)

            if clause is None:
                return None, None
            # These builders return both halves together or neither.
            assert params is not None
            clauses.append(sql_builder.Expr(clause, params))
            obs_tables.add(cat_name)

        elif form_type == 'STRING':
            clause, params = get_string_query(selections, param_qualified_name,
                                              qtypes)
            if clause is None:
                return None, None
            # These builders return both halves together or neither.
            assert params is not None
            clauses.append(sql_builder.Expr(clause, params))
            obs_tables.add(cat_name)

        else: # pragma: no cover - error catchall
            log.error('construct_query_string: Unknown field type "%r" for '
                      +'param "%r"', form_type, param_qualified_name)
            return None, None

    # Make the ordering terms
    order_terms: list[tuple[Any, bool]] | None = []
    if 'order' in extras:
        order_params, descending_params = extras['order']

        (order_terms, order_mult_tables,
         order_obs_tables) = create_order_by_terms(order_params,
                                                   descending_params)
        if order_terms is None:
            return None, None
        # create_order_by_terms returns all three or none, and the check above
        # ruled out none.
        assert order_mult_tables is not None
        assert order_obs_tables is not None
        mult_tables |= order_mult_tables
        obs_tables |= order_obs_tables

    select = sql_builder.Select()
    select.add_column(sql_builder.column('id', 'obs_general'))
    from_source = select.add_from('obs_general')

    # Now JOIN all the obs_ tables together
    add_obs_table_joins(from_source, sorted(obs_tables))
    # And JOIN all the mult_ tables together
    add_mult_table_joins(from_source, sorted(mult_tables))

    # Add in the WHERE clauses
    if clauses:
        select.add_where(sql_builder.combine_exprs(clauses, 'AND'))

    # Add in the ORDER BY clause
    # order_terms starts as [] and is only replaced by a non-None list, since the
    # None case returned above.
    assert order_terms is not None
    for order_column, descending in order_terms:
        select.add_order_by(order_column, descending=descending)

    sql, clause_params = select.build()
    log.debug('SEARCH SQL: %r *** PARAMS %r', sql, str(clause_params))
    return sql, clause_params


def _valid_regex(r: str) -> bool:
    """Whether the database will accept a regular expression the caller typed.

    The only way to know is to ask the server, since OPUS searches run the
    expression through MySQL rather than through Python.

    Parameters:
        r: The regular expression, as the caller typed it.

    Returns:
        True if the server accepted it.
    """
    # Validate the regex syntax. The only way to do this with certainty
    # is to actually try it on the SQL server and see if it throws
    # an error. No need to log this, though, because it's just bad
    # user input, not a real internal error.
    cursor = connection.cursor()
    try:
        cursor.execute('SELECT REGEXP_LIKE("x", %s)', (r,))
    except DatabaseError:
        return False
    return True

def get_string_query(selections: dict[str, Any], param_qualified_name: str,
                     qtypes: list[str]
                     ) -> sql_builder.Expr | tuple[None, None]:
    """Builds query for strings.

    The following q-types are supported:
        contains
        begins
        ends
        matches
        excludes

    Returns an `sql_builder.Expr`, which is a `(sql, params)` pair, or the pair
    `(None, None)` if the query cannot be built.
    """
    if selections is None or param_qualified_name not in selections:
        return None, None
    values = selections[param_qualified_name]

    param_info = _get_param_info_by_qualified_name(param_qualified_name)
    # The three sibling clause builders (construct_query_string, get_range_query
    # and get_longitude_query) return (None, None) when the name resolves to no
    # ParamInfo; this one has never had that guard. It is unreachable from either
    # caller today -- construct_query_string resolves the same name and bails
    # first, and api_string_search_choices takes the name off an already-resolved
    # ParamInfo -- so the invariant is asserted rather than a fourth guard being
    # invented, which would be a behavior change on a path nothing reaches.
    assert param_info is not None

    cat_name = param_info.category_name
    name = param_info.name
    param_column = sql_builder.column(name, cat_name)

    if len(qtypes) == 0:
        qtypes = ['contains'] * len(values)

    if len(qtypes) != len(values):
        log.error('get_string_query: Inconsistent qtype/values lengths '
                  +'for "%r" '
                  +'*** Selections %r *** Qtypes %r ***',
                  param_qualified_name, str(selections), str(qtypes))
        return None, None

    clauses = []

    for idx in range(len(values)):
        value = values[idx]
        qtype = qtypes[idx]

        if qtype != 'regex':
            value = value.replace('\\', '\\\\')
            if qtype != 'matches':
                value = value.replace('%', '\\%')
                value = value.replace('_', '\\_')

        if qtype == 'contains':
            clause = sql_builder.binary_op(param_column, 'LIKE',
                                           sql_builder.value('%'+value+'%'))
        elif qtype == 'begins':
            clause = sql_builder.binary_op(param_column, 'LIKE',
                                           sql_builder.value(value+'%'))
        elif qtype == 'ends':
            clause = sql_builder.binary_op(param_column, 'LIKE',
                                           sql_builder.value('%'+value))
        elif qtype == 'matches':
            clause = sql_builder.binary_op(param_column, '=',
                                           sql_builder.value(value))
        elif qtype == 'excludes':
            clause = sql_builder.binary_op(param_column, 'NOT LIKE',
                                           sql_builder.value('%'+value+'%'))
        elif qtype == 'regex':
            if not _valid_regex(value):
                return None, None
            clause = sql_builder.binary_op(param_column, 'RLIKE',
                                           sql_builder.value(value))
        else: # pragma: no cover - protecting against future bugs
            log.error('get_string_query: Unknown qtype %r '
                      +'for "%r" '
                      +'*** Selections %r *** Qtypes %r ***',
                      qtype, param_qualified_name, str(selections), str(qtypes))
            return None, None
        clauses.append(clause)

    return sql_builder.combine_exprs(clauses, 'OR')

def get_range_query(selections: dict[str, Any], param_qualified_name: str,
                    qtypes: list[str] | None, units: list[str | None] | None
                    ) -> sql_builder.Expr | tuple[None, None]:
    """Builds query for numeric ranges.

    This can either be a single column range (one table column holds the value)
    or a normal dual-column range (2 table columns hold min and max values).

    The following q-types are supported:
        any
        all
        only
    """
    if selections is None:
        return None, None

    param_info = _get_param_info_by_qualified_name(param_qualified_name)
    if not param_info:
        return None, None

    (_form_type, _form_type_format,
     form_type_unit_id) = parse_form_type(param_info.form_type)

    param_qualified_name_no_num = strip_numeric_suffix(param_qualified_name)
    param_qualified_name_min = param_qualified_name_no_num + '1'
    param_qualified_name_max = param_qualified_name_no_num + '2'

    values_min = selections.get(param_qualified_name_min, [])
    values_max = selections.get(param_qualified_name_max, [])

    (_form_type, _form_type_format,
     form_type_unit_id) = parse_form_type(param_info.form_type)

    if qtypes is None or len(qtypes) == 0:
        qtypes = ['any'] * len(values_min)

    if units is None or len(units) == 0:
        default_unit = get_default_unit(form_type_unit_id)
        units = [default_unit] * len(values_min)

    # But, for constructing the query, if this is a single column range,
    # the param_names are both the same
    cat_name = param_info.category_name
    name_no_num = strip_numeric_suffix(param_info.name)
    name_min = name_no_num + '1'
    name_max = name_no_num + '2'

    if is_single_column_range(param_qualified_name):
        param_qualified_name_min = param_qualified_name_no_num
        param_qualified_name_max = param_qualified_name_no_num
        name_min = name_max = name_no_num
        for qtype in qtypes:
            if qtype != 'any':
                log.error('get_range_query: bad qtype "%r" '
                          +'for "%r" '
                          +'*** Selections %r *** Qtypes %r *** Units %r',
                          qtype, param_qualified_name,
                          str(selections), str(qtypes), str(units))
                return None, None
        # qtypes are meaningless for single column ranges!
        qtypes = ['any'] * len(values_min)

    column_min = sql_builder.column(name_min, cat_name)
    column_max = sql_builder.column(name_max, cat_name)

    if (len(qtypes) != len(values_min) or len(units) != len(values_min) or
        len(values_min) != len(values_max)):
        log.error('get_range_query: Inconsistent qtype/unit/min/max lengths '
                  +'for "%r" '
                  +'*** Selections %r *** Qtypes %r *** Units %r',
                  param_qualified_name, str(selections), str(qtypes),
                  str(units))
        return None, None

    clauses = []

    for idx in range(len(values_min)):
        unit = units[idx]
        try:
            value_min = convert_to_default_unit(values_min[idx],
                                                form_type_unit_id,
                                                unit)
            value_max = convert_to_default_unit(values_max[idx],
                                                form_type_unit_id,
                                                unit)
        except KeyError:
            log.error('get_range_query: Unknown unit "%r" for "%r" '
                      +'*** Selections %r *** Qtypes %r *** Units %r',
                      unit, param_qualified_name, str(selections), str(qtypes),
                      str(units))
            return None, None
        except ValueError:
            log.error('get_range_query: Unit "%r" on "%r" conversion failed '
                      +'*** Selections %r *** Qtypes %r *** Units %r',
                      unit, param_qualified_name, str(selections), str(qtypes),
                      str(units))
            return None, None

        qtype = qtypes[idx]

        # Each qtype pairs one side of the user's range with one column: which
        # column and which direction is all that distinguishes them.
        if qtype == 'all':
            # param_name_min <= value_min AND param_name_max >= value_max
            sides = ((column_min, '<=', value_min), (column_max, '>=', value_max))
        elif qtype == 'only':
            # param_name_min >= value_min AND param_name_max <= value_max
            sides = ((column_min, '>=', value_min), (column_max, '<=', value_max))
        elif qtype == 'any' or qtype == '':
            # param_name_min <= value_max AND param_name_max >= value_min
            sides = ((column_max, '>=', value_min), (column_min, '<=', value_max))
        else:
            log.error('get_range_query: Unknown qtype "%r" '
                      +'for "%r" '
                      +'*** Selections %r *** Qtypes %r *** Units %r',
                      qtype, param_qualified_name,
                      str(selections), str(qtypes), str(units))
            return None, None

        # A side the user left blank contributes nothing, and if both are blank
        # this entry contributes no clause at all.
        side_clauses = [sql_builder.binary_op(side_column, operator,
                                              sql_builder.value(side_value))
                        for side_column, operator, side_value in sides
                        if side_value is not None]
        if side_clauses:
            clauses.append(sql_builder.join_exprs(side_clauses, 'AND'))

    return sql_builder.combine_exprs(clauses, 'OR')

def get_longitude_query(selections: dict[str, Any], param_qualified_name: str,
                        qtypes: list[str] | None, units: list[str | None] | None
                        ) -> sql_builder.Expr | tuple[None, None]:
    """Builds query for longitude ranges.

    Both sides of the range must be specified.

    The following q-types are supported:
        any
        all
        only
    """
    if selections is None:
        return None, None

    param_info = _get_param_info_by_qualified_name(param_qualified_name)
    if not param_info:
        return None, None

    (_form_type, _form_type_format,
     form_type_unit_id) = parse_form_type(param_info.form_type)

    param_qualified_name_no_num = strip_numeric_suffix(param_qualified_name)
    param_qualified_name_min = param_qualified_name_no_num + '1'
    param_qualified_name_max = param_qualified_name_no_num + '2'

    values_min = selections.get(param_qualified_name_min, [])
    values_max = selections.get(param_qualified_name_max, [])

    # But, for constructing the query, if this is a single column range,
    # the param_names are both the same
    cat_name = param_info.category_name
    name_no_num = strip_numeric_suffix(param_info.name)
    # The half-width of the observation's own longitude range.
    column_d_long = sql_builder.column('d_' + name_no_num, cat_name)

    (_form_type, _form_type_format,
     form_type_unit_id) = parse_form_type(param_info.form_type)

    if qtypes is None or len(qtypes) == 0:
        qtypes = ['any'] * len(values_min)

    if units is None or len(units) == 0:
        default_unit = get_default_unit(form_type_unit_id)
        units = [default_unit] * len(values_min)

    if (len(qtypes) != len(values_min) or len(units) != len(values_min) or
        len(values_min) != len(values_max)):
        log.error('get_longitude_query: Inconsistent qtype/unit/min/max lengths '
                  +'for "%r" '
                  +'*** Selections %r *** Qtypes %r *** Units %r',
                  param_qualified_name, str(selections), str(qtypes),
                  str(units))
        return None, None

    clauses = []

    for idx in range(len(values_min)):
        unit = units[idx]
        try:
            value_min = convert_to_default_unit(values_min[idx],
                                                form_type_unit_id,
                                                unit)
            value_max = convert_to_default_unit(values_max[idx],
                                                form_type_unit_id,
                                                unit)
        except KeyError:
            log.error('get_longitude_query: Unknown unit "%r" for "%r" '
                      +'*** Selections %r *** Qtypes %r *** Units %r',
                      unit, param_qualified_name, str(selections), str(qtypes),
                      str(units))
            return None, None
        except ValueError:
            log.error('get_longitude_query: Unit "%r" on "%r" conversion '
                      +'failed '
                      +'*** Selections %r *** Qtypes %r *** Units %r',
                      unit, param_qualified_name, str(selections), str(qtypes),
                      str(units))
            return None, None

        qtype = qtypes[idx]

        if value_min is None and value_max is None:
            # Ignore if nothing to search on
            continue

        if value_min is None or value_max is None:
            # Pretend this is a range query - fake up a new selections and
            # qtypes containing only this one entry
            new_selections = {param_qualified_name_min: [value_min],
                              param_qualified_name_max: [value_max]}
            new_qtypes = [qtype]
            range_clause, range_params = get_range_query(new_selections,
                                                         param_qualified_name,
                                                         new_qtypes, None)
            if range_clause is None:
                return None, None
            # get_range_query returns both halves together or neither.
            assert range_params is not None
            clause = sql_builder.Expr(range_clause, range_params)

        elif is_single_column_range(param_qualified_name):
            # A single column range doesn't have center and d_ fields
            if qtype != 'any':
                log.error('get_longitude_query: Bad qtype "%r" for "%r" '
                          +'*** Selections %r *** Qtypes %r *** Units %r',
                          qtype, param_qualified_name,
                          str(selections), str(qtypes), str(units))
                return None, None
            param_column = sql_builder.column(name_no_num, cat_name)
            # Normal range MIN to MAX, or a wraparound range MIN to 360 plus
            # 0 to MAX, which is the same pair of comparisons under OR.
            operator = 'AND' if value_max >= value_min else 'OR'
            clause = sql_builder.join_exprs(
                [sql_builder.binary_op(param_column, '>=',
                                       sql_builder.value(value_min)),
                 sql_builder.binary_op(param_column, '<=',
                                       sql_builder.value(value_max))],
                operator)

        else:
            # Find the midpoint and dx of the user's range
            if value_max >= value_min:
                longit = (value_min + value_max)/2.
            else:
                longit = (value_min + value_max + 360.)/2.
            longit = longit % 360.
            d_long = (longit - value_min) % 360.
            separation = sql_builder.angular_separation(
                sql_builder.column(name_no_num, cat_name), longit)

            # The observation matches when the two ranges overlap ("any"),
            # when the observation's range covers the user's ("all"), or when
            # the user's covers the observation's ("only") - each is the same
            # comparison of the center separation against a sum or difference
            # of the two half-widths.
            if qtype == 'any' or qtype == '':
                bound = sql_builder.binary_op(sql_builder.value(d_long), '+',
                                              column_d_long)
            elif qtype == 'all':
                bound = sql_builder.binary_op(column_d_long, '-',
                                              sql_builder.value(d_long))
            elif qtype == 'only':
                bound = sql_builder.binary_op(sql_builder.value(d_long), '-',
                                              column_d_long)
            else:
                log.error('get_longitude_query: Unknown qtype "%r" '
                          +'for "%r"'
                          +'*** Selections %r *** Qtypes %r *** Units %r',
                          qtype, param_qualified_name,
                          str(selections), str(qtypes),  str(units))
                return None, None
            clause = sql_builder.binary_op(separation, '<=', bound)

        clauses.append(clause)

    return sql_builder.combine_exprs(clauses, 'OR')

def get_user_search_table_name(num: int | str) -> str:
    """ pass cache_no, returns user search table name"""
    return 'cache_' + str(num)


def add_obs_table_joins(from_source: sql_builder.FromSource,
                        obs_tables: Iterable[str]) -> None:
    """LEFT JOIN each ``obs_`` table onto ``obs_general``.

    The joins are LEFT because an observation that has no row in one of these
    tables must still appear in the result, with that table's columns NULL.

    Parameters:
        from_source: The `sql_builder.FromSource` for obs_general.
        obs_tables: The tables to join, in the order they should appear.
            obs_general itself is skipped: it is the source, not a join.
    """
    for table in obs_tables:
        if table == 'obs_general':
            continue
        from_source.add_join(
            'LEFT', table,
            sql_builder.columns_equal(
                sql_builder.column('id', 'obs_general'),
                sql_builder.column('obs_general_id', table)))


def add_mult_table_joins(from_source: sql_builder.FromSource,
                         mult_tables: Iterable[tuple[str, bool, str, str]]) -> None:
    """LEFT JOIN each ``mult_`` table onto the ``obs_`` column that holds its id.

    Parameters:
        from_source: The `sql_builder.FromSource` to hang the joins on.
        mult_tables: (mult_table, is_multigroup, category, field_name) tuples, in
            the order they should appear. A MULTIGROUP column holds a JSON list
            rather than a single id, so it joins on the list's first element.
    """
    for mult_table, is_multigroup, category, field_name in mult_tables:
        mult_column = sql_builder.column(field_name, category)
        if is_multigroup:
            # For a MULTIGROUP field, we just sort on the first value
            mult_column = sql_builder.json_extract_first(mult_column)
        from_source.add_join(
            'LEFT', mult_table,
            sql_builder.columns_equal(mult_column,
                                      sql_builder.column('id', mult_table)))


def search_cache_join_condition(table_name: str,
                                cache_table_name: str) -> sql_builder.Expr:
    """Return the condition that ties a table's rows to a search's results.

    A search cache table holds one row per matching observation, keyed by
    obs_general.id. obs_general therefore joins to it on its own primary key,
    while every other ``obs_`` table joins on the ``obs_general_id`` it carries.

    The cache table is created by raw DDL under a name computed at runtime and has
    no Django model, which is why the queries that need this condition cannot be
    written with the ORM.

    Parameters:
        table_name: The ``obs_`` table being tied to the search.
        cache_table_name: The cache table holding the search results.
    """
    if table_name == 'obs_general':
        own_column = sql_builder.column('id', table_name)
    else:
        own_column = sql_builder.column('obs_general_id', table_name)
    return sql_builder.columns_equal(own_column,
                                     sql_builder.column('id', cache_table_name))


################################################################################
#
# INTERNAL SUPPORT ROUTINES
#
################################################################################

def _get_param_info_by_qualified_name(param_qualified_name: str) -> ParamInfo | None:
    "Given a qualified name cat.name return the ParamInfo"
    if param_qualified_name.find('.') == -1:
        return None

    cat_name = param_qualified_name.split('.')[0]
    name = param_qualified_name.split('.')[1]

    try:
        return ParamInfo.objects.get(category_name=cat_name, name=name)
    except ParamInfo.DoesNotExist:
        # Single column range queries will not have the numeric suffix
        name_no_num = strip_numeric_suffix(name)
        try:
            return ParamInfo.objects.get(category_name=cat_name,
                                         name=name_no_num)
        except ParamInfo.DoesNotExist:
            return None


def is_single_column_range(param_qualified_name: str) -> bool:
    "Given a qualified name cat.name return True if it's a single-column range"
    cat_name = param_qualified_name.split('.')[0]
    name = param_qualified_name.split('.')[1]

    # Single column range queries will not have the numeric suffix
    name_no_num = strip_numeric_suffix(name)
    try:
        ParamInfo.objects.get(category_name=cat_name,
                              name=name_no_num)
    except ParamInfo.DoesNotExist:
        return False

    return True


def parse_order_slug(all_order: str | None
                     ) -> tuple[list[str] | None, list[bool] | None]:
    "Given a list of slugs a,b,-c,d create the params and descending lists"
    order_params = []
    order_descending_params = []

    if not all_order:
        all_order = settings.DEFAULT_SORT_ORDER
    if (settings.FINAL_SORT_ORDER
        not in all_order.replace('-','').split(',')):
        all_order += ',' + settings.FINAL_SORT_ORDER
    orders = all_order.split(',')
    for order in orders:
        descending = order[0] == '-'
        order = order.strip('-')
        param_info = get_param_info_by_slug(order, 'col', allow_units_override=False)
        if not param_info:
            log.error('parse_order_slug: Unable to resolve order '
                      +'slug "%r"', order)
            return None, None
        order_param = param_info.param_qualified_name()
        if order_param == 'obs_pds.opus_id':
            # Force opus_id to be from obs_general for efficiency
            order_param = 'obs_general.opus_id'
        order_params.append(order_param)
        order_descending_params.append(descending)

    return order_params, order_descending_params

def create_order_by_terms(order_params: list[str], descending_params: list[bool]
                          ) -> tuple[list[tuple[Any, bool]] | None,
                                     set[tuple[str, bool, str, str]] | None,
                                     set[str] | None]:
    """Given params and descending lists, make the ORDER BY terms.

    Returns a list of (expression, descending) pairs ready for
    `sql_builder.Select.add_order_by`, plus the ``mult_`` and ``obs_`` tables the terms
    require the caller to join in.
    """
    order_mult_tables = set()
    order_obs_tables = set()
    assert order_params # There should always be an ordering
    order_terms = []
    for i in range(len(order_params)):
        order_slug = order_params[i]
        pi = _get_param_info_by_qualified_name(order_slug)
        if not pi:
            log.error('create_order_by_terms: Unable to resolve order'
                      +' slug "%r"', order_slug)
            return None, None, None
        (form_type, _form_type_format,
         _form_type_unit_id) = parse_form_type(pi.form_type)
        order_column = sql_builder.column(pi.name, pi.category_name)
        order_obs_tables.add(pi.category_name)
        if form_type in settings.MULT_FORM_TYPES:
            # A mult field holds an id, so it sorts by the human-readable label
            # in its mult table rather than by the value stored in the row.
            mult_table = get_mult_name(pi.param_qualified_name())
            order_column = sql_builder.column('label', mult_table)
            is_multigroup = form_type == 'MULTIGROUP'
            order_mult_tables.add((mult_table, is_multigroup, pi.category_name,
                                   pi.name))
        order_terms.append((order_column, descending_params[i]))

    return order_terms, order_mult_tables, order_obs_tables
