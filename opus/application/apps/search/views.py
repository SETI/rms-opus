################################################################################
#
# search/views.py
#
# The API interface for doing things related to searches plus major internal
# support routines for searching:
#
#    Format: __api/normalizeinput.json
#
################################################################################

import hashlib
import json
import logging
import math
import sys

import settings

from django.apps import apps
from django.conf import settings
from django.core.cache import cache
from django.db import connection, DatabaseError
from django.db.models import Q
from django.db.models.sql.datastructures import EmptyResultSet
from django.db.utils import IntegrityError
from django.http import Http404, HttpResponse

from paraminfo.models import ParamInfo
from search.models import *
from tools.app_utils import *
from tools.db_utils import *

import opus_support

log = logging.getLogger(__name__)


################################################################################
#
# API INTERFACES
#
################################################################################

def api_normalize_input(request):
    """Validate and normalize slug values.

    This is a PRIVATE API.

    For each searchable slug, check its value to see if it can be parsed.
    If it can be, return a normalized value by parsing it and then un-parsing
    it. If it can't be, return false.

    Format: __api/normalizeinput.json
    Arguments: Normal search arguments

    Returned JSON is of the format:
        {"slug1": "normalizedval1", "slug2": "normalizedval2"}
    """
    api_code = enter_api_call('api_normalize_input', request)

    if not request or request.GET is None:
        ret = Http404('No request')
        exit_api_call(api_code, ret)
        raise ret

    (selections, extras) = url_to_search_params(request.GET,
                                                allow_errors=True,
                                                return_slugs=True,
                                                pretty_results=True)
    if selections is None:
        log.error('api_normalize_input: Could not find selections for'
                  +' request %s', str(request.GET))
        ret = Http404('Parsing of selections failed')
        exit_api_call(api_code, ret)
        raise ret

    ret = json_response(selections)
    exit_api_call(api_code, ret)
    return ret


def api_string_search_choices(request, slug):
    """Return valid choices for a string search given other search criteria.

    This is a PRIVATE API.

    Return all valid choices for a given string search slug given the partial
    search value entered for that slug, its q-type, and the remainder of the
    normal search parameters.

    Format: __api/stringsearchchoices/<slug>.json
    Arguments: limit=<N>
               Normal search arguments

    Returned JSON is of the format:
        {"choices": ["choice1", "choice2"]}

    The portion of each choice selected by the partial search is highlighted
    with <b>...</b>.
    """
    api_code = enter_api_call('api_string_search_choices', request)

    if not request or request.GET is None:
        ret = Http404('No request')
        exit_api_call(api_code, ret)
        raise ret

    param_info = get_param_info_by_slug(slug)
    if not param_info:
        log.error('api_string_search_choices: unknown slug "%s"',
                  slug)
        ret = Http404('Unknown slug')
        exit_api_call(api_code, ret)
        raise ret

    param_qualified_name = param_info.param_qualified_name()
    param_category = param_info.category_name
    param_name = param_info.name

    (selections, extras) = url_to_search_params(request.GET)
    if selections is None:
        log.error('api_string_search_choices: Could not find selections for'
                  +' request %s', str(request.GET))
        ret = Http404('Parsing of selections failed')
        exit_api_call(api_code, ret)
        raise ret

    partial_query = ''
    query_qtype = 'contains'
    if param_qualified_name in selections:
        partial_query = selections[param_qualified_name][0]
        del selections[param_qualified_name]
    if 'qtypes' in extras:
        qtypes = extras['qtypes']
        if param_qualified_name in qtypes:
            query_qtype = qtypes[param_qualified_name]
            del qtypes[param_qualified_name]

    user_query_table = get_user_query_table(selections, extras,
                                            api_code=api_code)
    if not user_query_table:
        log.error('api_string_search_choices: get_user_query_table failed '
                  +'*** Selections %s *** Extras %s',
                  str(selections), str(extras))
        ret = Http404('Bad search')
        exit_api_call(api_code, ret)
        raise ret

    limit = request.GET.get('limit', settings.DEFAULT_STRINGCHOICE_LIMIT)
    try:
        limit = int(limit)
    except ValueError:
        log.error('api_string_search_choices: Bad limit for'
                  +' request %s', str(request.GET))
        ret = Http404('Bad limit')
        exit_api_call(api_code, ret)
        raise ret

    if limit < 1 or limit > 1000000000000:
        log.error('api_string_search_choices: Bad limit for'
                  +' request %s', str(request.GET))
        ret = Http404('Bad limit')
        exit_api_call(api_code, ret)
        raise ret

    quoted_table_name = connection.ops.quote_name(param_category)
    quoted_param_qualified_name = (quoted_table_name + '.'
                                   +connection.ops.quote_name(param_name))

    # Check the size of the cache table to see if we can afford to do a
    # search retricted by the cache table contents. The JOIN of the cache
    # table can be slow if it has too many entries and gives a bad user
    # experience.
    sql = 'SELECT COUNT(*) FROM '+connection.ops.quote_name(user_query_table)

    cursor = connection.cursor()
    cursor.execute(sql)
    results = cursor.fetchall()
    if len(results) != 1 or len(results[0]) != 1:
        log.error('api_string_search_choices: SQL failure: %s', sql)
        ret = Http404('Bad SQL')
        exit_api_call(api_code, ret)
        raise ret

    final_results = None

    do_simple_search = False
    count = int(results[0][0])
    if count >= settings.STRINGCHOICE_FULL_SEARCH_COUNT_THRESHOLD:
        do_simple_search = True

    if not do_simple_search:
        max_time = settings.STRINGCHOICE_FULL_SEARCH_TIME_THRESHOLD
        sql = f'SELECT /*+ MAX_EXECUTION_TIME({max_time}) */'
        sql += ' DISTINCT ' + quoted_param_qualified_name
        sql += ' FROM '+quoted_table_name
        # The cache table is an INNER JOIN because we only want opus_ids
        # that appear in the cache table to cause result rows
        sql += ' INNER JOIN '+connection.ops.quote_name(user_query_table)
        sql += ' ON '+quoted_table_name+'.'
        if param_category == 'obs_general':
            sql += connection.ops.quote_name('id')+'='
        else:
            sql += connection.ops.quote_name('obs_general_id')+'='
        sql += connection.ops.quote_name(user_query_table)+'.'
        sql += connection.ops.quote_name('id')

        sql_params = []
        if partial_query:
            sql += ' WHERE '
            sql += quoted_param_qualified_name + ' LIKE %s'
            sql_params.append('%'+partial_query+'%')

        sql += ' ORDER BY '+quoted_param_qualified_name
        sql += ' LIMIT '+str(limit)

        try:
            cursor.execute(sql, tuple(sql_params))
        except DatabaseError as e:
            if e.args[0] != MYSQL_EXECUTION_TIME_EXCEEDED:
                log.error('api_string_search_choices: "%s" returned %s',
                          sql, str(e))
                ret = Http404('Bad SQL')
                exit_api_call(api_code, ret)
                raise ret
            do_simple_search = True

    if do_simple_search:
        # Same thing but no cache table join
        # This will give more results than we really want, but will be much
        # faster
        max_time = settings.STRINGCHOICE_FULL_SEARCH_TIME_THRESHOLD2
        sql = f'SELECT /*+ MAX_EXECUTION_TIME({max_time}) */'
        sql += ' DISTINCT ' + quoted_param_qualified_name
        sql += ' FROM '+quoted_table_name

        sql_params = []
        if partial_query:
            sql += ' WHERE '
            sql += quoted_param_qualified_name + ' LIKE %s'
            sql_params.append('%'+partial_query+'%')

        sql += ' ORDER BY '+quoted_param_qualified_name
        sql += ' LIMIT '+str(limit)

        try:
            cursor.execute(sql, tuple(sql_params))
        except DatabaseError as e:
            if e.args[0] != MYSQL_EXECUTION_TIME_EXCEEDED:
                log.error('api_string_search_choices: "%s" returned %s',
                          sql, str(e))
                ret = Http404('Bad SQL')
                exit_api_call(api_code, ret)
                raise ret
            final_results = []

    if final_results is None:
        final_results = []
        more = True
        while more:
            part_results = cursor.fetchall()
            final_results += part_results
            more = cursor.nextset()

        final_results = [x[0] for x in final_results]
        if partial_query:
            final_results = [x.replace(partial_query,
                                       '<b>'+partial_query+'</b>')
                             for x in final_results]

    ret = json_response({'choices': final_results,
                         'full_search': do_simple_search})
    exit_api_call(api_code, ret)
    return ret


################################################################################
#
# MAJOR INTERNAL ROUTINES
#
################################################################################

def url_to_search_params(request_get, allow_errors=False, return_slugs=False,
                         pretty_results=False):
    """Convert a URL to a set of selections and extras.

    This is the MAIN routine for taking a URL and parsing it for searching.

    OPUS lets users put nice readable things in the URL, like "planet=Jupiter"
    rather than "planet_id=3".

    This function takes the URL params and translates them into a list that
    contains 2 dictionaries:
        The first dict is the user selections: keys of the dictionary are
            param_names of data columns in the data table; values are always
            lists and represent the user's selections.
        The 2nd dict is any extras being passed by user, like qtypes that
            define what types of queries will be performed for each
            param-value set in the first dict, or sort order.

    NOTE: Pass request_get = request.GET to this func please
    (This func doesn't return an http response so unit tests freak if you
     pass it an HTTP request)

    If allow_errors is True, then even if a value can't be parsed, the rest
    of the slugs are processed and the bad slug is just marked with None.

    If return_slugs is True, the indexes into selections are slug names, not
    qualified names (table.column).

    If pretty_results is True, the resulting values are unparsed back into
    strings based on the ParamInfo format.

    Example command line usage:

    from search.views import *
    from django.http import QueryDict
    q = QueryDict("planet=Saturn&volumeid=COISS_2&
                   qtype-volumeid=begins&
                   order=time1,-RINGGEOringcenterdistance")
    (selections,extras) = url_to_search_params(q)
    selections
        {u'obs_general.planet_id': [u'Saturn'],
         u'obs_pds.volume_id': [u'COISS_2']}
    extras
        {'order':
            ([u'obs_general.time1', u'obs_ring_geometry.ring_center_distance'],
             [False, True]),
         'qtypes':
            {u'obs_pds.volume_id': [u'begins']}}
    """
    selections = {}
    extras = {}
    qtypes = {}
    order_params = []
    order_descending_params = []

    # Note that request_get.items() automatically gets rid of duplicate entries
    # because it returns a dict! But we check for them below anyway just for
    # good measure.
    search_params = list(request_get.items())
    if 'order' not in [x[0] for x in search_params]:
        # If there's no order slug, then force one
        search_params.append(('order', settings.DEFAULT_SORT_ORDER))
    for search_param in search_params:
        slug = search_param[0]
        if slug == 'order':
            all_order = search_param[1]
            order_params, order_descending_params = parse_order_slug(all_order)
            if order_params is None:
                return None, None
            extras['order'] = (order_params, order_descending_params)
            continue
        if slug in settings.SLUGS_NOT_IN_DB:
            continue
        slug_no_num = strip_numeric_suffix(slug)
        values = search_param[1].strip(',').split(',')
        values = [x.strip() for x in values]
        value_not_split = search_param[1].strip()
        values_not_split = [value_not_split]

        # If nothing is specified, just ignore the slug
        if not values:
            if pretty_results and return_slugs:
                selections[slug] = ""
            continue

        has_value = False
        for value in values:
            if value:
                has_value = True
                break
        if not has_value:
            if pretty_results and return_slugs:
                selections[slug] = ""
            continue

        qtype = False  # assume this is not a qtype statement
        if slug.startswith('qtype-'): # like qtype-time=ZZZ
            qtype = True  # this is a statement of query type!
            slug = slug.split('-')[1]
            slug_no_num = strip_numeric_suffix(slug)
            if slug_no_num != slug:
                log.error('url_to_search_params: qtype slug has '+
                          'numeric suffix "%s"', slug)
                return None, None

        param_info = get_param_info_by_slug(slug)
        if not param_info:
            log.error('url_to_search_params: unknown slug "%s"',
                      slug)
            return None, None

        param_qualified_name = param_info.param_qualified_name()
        (form_type, form_type_func,
         form_type_format) = parse_form_type(param_info.form_type)

        param_qualified_name_no_num = strip_numeric_suffix(param_qualified_name)

        if qtype:
            if param_qualified_name_no_num in qtypes:
                log.error('url_to_search_params: Duplicate slug for '
                          +'qtype "%s": %s', param_qualified_name_no_num,
                          request_get)
                return None, None
            qtypes[param_qualified_name_no_num] = values
            continue

        if form_type in settings.MULT_FORM_TYPES:
            # Mult form types can be sorted and uniquified to save duplicate
            # queries being built.
            # No other form types can be sorted since their ordering
            # corresponds to qtype ordering.
            if param_qualified_name in selections:
                log.error('url_to_search_params: Duplicate slug for '
                          +'"%s": %s', param_qualified_name, request_get)
                return None, None
            new_val = sorted(set(values))
            if pretty_results:
                new_val = ','.join(new_val)
            if return_slugs:
                selections[slug] = new_val
            else:
                selections[param_qualified_name] = new_val
        elif form_type in settings.RANGE_FORM_TYPES:
            # For RANGE queries, convert the strings into the internal
            # representations if necessary
            if form_type_func is None:
                func = float
                if form_type_format and form_type_format[-1] == 'd':
                    func = int
                values_to_use = _clean_numeric_field(values_not_split)
            else:
                if form_type_func in opus_support.RANGE_FUNCTIONS:
                    func = (opus_support
                            .RANGE_FUNCTIONS[form_type_func][1])
                    values_to_use = values_not_split
                else:
                    log.error('url_to_search_params: Unknown RANGE '
                              +'function "%s"', form_type_func)
                    return None, None
            if param_qualified_name == param_qualified_name_no_num:
                # This is a single column range query
                ext = slug[-1]
                new_param_qualified_name = param_qualified_name+ext
            else:
                new_param_qualified_name = param_qualified_name
            if new_param_qualified_name in selections:
                log.error('url_to_search_params: Duplicate slug '
                          +'for "%s": %s', param_qualified_name+ext,
                          request_get)
                return None, None
            try:
                new_val = list(map(func, values_to_use))
                if func == float or func == int:
                    if not all(map(math.isfinite, new_val)):
                        raise ValueError
                if pretty_results:
                    new_val = format_metadata_number_or_func(
                                        new_val[0], form_type_func, form_type_format)
                if return_slugs:
                    selections[slug] = new_val
                else:
                    selections[new_param_qualified_name] = new_val
            except ValueError as e:
                if allow_errors:
                    if return_slugs:
                        selections[slug] = None
                    else:
                        selections[new_param_qualified_name] = None
                else:
                    log.error('url_to_search_params: Function "%s" slug "%s" '
                              +'threw ValueError(%s) for %s',
                              func, slug, e, values_to_use)
                    return None, None
        else:
            # For non-RANGE queries, we just put the values here raw
            if param_qualified_name in selections:
                log.error('url_to_search_params: Duplicate slug '
                          +'for "%s": %s', param_qualified_name,
                          request_get)
                return None, None
            if return_slugs:
                selections[slug] = values_not_split
            else:
                selections[param_qualified_name] = values_not_split

    extras['qtypes'] = qtypes

    # log.debug('url_to_search_params: GET %s *** Selections %s *** Extras %s',
    #           request_get, str(selections), str(extras))

    return selections, extras


def get_user_query_table(selections, extras, api_code=None):
    """Perform a data search and create a table of matching IDs.

    This is THE main data query place. Performs a data search and creates
    a table of IDs (obs_general_id) that match the result rows, possibly
    sorted.

    Note: The function url_to_search_params takes the user HTTP request object
          and creates the data objects that are passed to this function.
    """
    cursor = connection.cursor()

    if selections is None or extras is None:
        # This should never happen...
        return None

    # Create a cache key
    cache_table_num, cache_new_flag = set_user_search_number(selections, extras)
    if cache_table_num is None:
        log.error('get_user_query_table: Failed to make entry in user_searches'+
                  ' *** Selections %s *** Extras %s',
                  str(selections), str(extras))
        return None
    cache_table_name = get_user_search_table_name(cache_table_num)

    # Is this key set in the cache?
    cache_key = 'cache_table:' + str(cache_table_num)

    cached_val = cache.get(cache_key)
    if cached_val:
        return cached_val

    # Is this key set in the database?
    desc_sql = 'DESC ' + connection.ops.quote_name(cache_table_name)
    try:
        cursor.execute(desc_sql)
    except DatabaseError as e:
        if e.args[0] != MYSQL_TABLE_NOT_EXISTS:
            log.error('get_user_query_table: "%s" returned %s',
                      desc_sql, str(e))
            return None
    else:
        # DESC was successful, so the database table exists
        cache.set(cache_key, cache_table_name)
        return cache_table_name

    # Cache table does not exist
    # We will make one by doing some data querying
    sql, params = construct_query_string(selections, extras)
    if sql is None:
        log.error('get_user_query_table: construct_query_string failed'
                  +' *** Selections %s *** Extras %s',
                  str(selections), str(extras))
        return None

    if not sql:
        log.error('get_user_query_table: Query string is empty'
                  +' *** Selections %s *** Extras %s',
                  str(selections), str(extras))
        return None

    # With this we can create a table that contains the single column
    create_sql = ('CREATE TABLE '
                  + connection.ops.quote_name(cache_table_name)
                  + '(sort_order INT NOT NULL AUTO_INCREMENT, '
                  + 'PRIMARY KEY(sort_order), id INT UNSIGNED, '
                  + 'UNIQUE KEY(id)) '
                  + sql)
    try:
        time1 = time.time()
        cursor.execute(create_sql, tuple(params))
    except DatabaseError as e:
        # So here's what happens.
        # Proc1: Call get_user_search_table_name and get a new, unique id
        # Proc2: Call get_user_search_table_name and get the same id as Proc1
        # Proc1: Do the long search query and try to create the cache table
        # Proc2: Also do the long search query and try to the create the cache
        #        table
        # Proc1: Gets done first, create table succeeds, and all is good
        # Proc2: Finishes the query, tries to create the table, and finds out
        #        someone rudely created it already.
        # This does not actually break anything. It's just inefficient because
        # we're running the same query twice at the same time, which might slow
        # things down.
        # The only obvious way to fix this is to check cache_new_flag and
        # if it's True we "own" the table and get to create it. If it's False
        # we know someone else owns the table, and we just sit here polling
        # until the table shows up or we get tired of waiting.
        # For the minor performance gain this doesn't seem important to fix
        # right now but perhaps in the future.
        if e.args[0] == MYSQL_TABLE_ALREADY_EXISTS:
            log.error('get_user_query_table: Table "%s" originally didn\'t '+
                      'exist, but now it does!', cache_table_name)
            cache.set(cache_key, cache_table_name)
            return cache_table_name
        log.error('get_user_query_table: "%s" with params "%s" failed with '
                  +'%s', create_sql, str(tuple(params)), str(e))
        return None
    log.debug('API %s (%.3f) get_user_query_table: %s *** PARAMS %s',
              str(api_code), time.time()-time1, create_sql, str(params))

    cache.set(cache_key, cache_table_name)
    return cache_table_name


def set_user_search_number(selections, extras):
    """Creates a new row in the user_searches table for each search request.

    This table lists query params+values plus any extra info needed to
    run a data search query.
    This method looks in user_searches table for current selections.
    If none exist, creates it.

    Returns the number of the cache table that should be used along with a flag
    indicating if this is a new entry in user_searches so the cache table
    shouldn't exist yet.
    """
    if selections is None or extras is None:
        return None, False

    selections_json = str(json.dumps(sort_dictionary(selections)))
    selections_hash = hashlib.md5(str.encode(selections_json)).hexdigest()

    qtypes_json = None
    qtypes_hash = 'NONE' # Needed for UNIQUE constraint to work
    if 'qtypes' in extras:
        if len(extras['qtypes']):
            qtypes_json = str(json.dumps(sort_dictionary(extras['qtypes'])))
            qtypes_hash = hashlib.md5(str.encode(qtypes_json)).hexdigest()

    units_json = None
    units_hash = 'NONE' # Needed for UNIQUE constraint to work
    if 'units' in extras:
        units_json = str(json.dumps(sort_dictionary(extras['units'])))
        units_hash = hashlib.md5(str.encode(units_json)).hexdigest()

    order_json = None
    order_hash = 'NONE' # Needed for UNIQUE constraint to work
    if 'order' in extras:
        order_json = str(json.dumps(extras['order']))
        order_hash = hashlib.md5(str.encode(order_json)).hexdigest()

    cache_key = ('usersearchno:selections_hash:' + str(selections_hash)
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
    except UserSearches.MultipleObjectsReturned:
        # This really shouldn't be possible
        s = UserSearches.objects.filter(selections_hash=selections_hash,
                                        qtypes_hash=qtypes_hash,
                                        units_hash=units_hash,
                                        order_hash=order_hash)
        s = s[0]
        log.error('set_user_search_number: Multiple entries in user_searches'
                  +' for *** Selections %s *** Qtypes %s *** Units %s '
                  +' *** Order %s',
                  str(selections_json),
                  str(qtypes_json),
                  str(units_json),
                  str(order_json))

    cache.set(cache_key, s.id)
    return s.id, new_entry


def get_param_info_by_slug(slug, from_ui=False):
    """Given a slug, look up the corresponding ParamInfo.

    If from_ui is True, we try stripping the trailing '1' off a slug
    as well, because single-value slugs come in with this gratuitous
    '1' on the end.
    """
    slug_no_num = strip_numeric_suffix(slug)

    # Try the current slug names first
    try:
        return ParamInfo.objects.get(slug=slug_no_num)
    except ParamInfo.DoesNotExist:
        pass

    try:
        return ParamInfo.objects.get(slug=slug)
    except ParamInfo.DoesNotExist:
        pass

    try:
        # qtypes for ranges come through as the param_name_no_num
        # which doesn't exist in param_info, so grab the param_info
        # for the lower side of the range
        return ParamInfo.objects.get(slug=slug + '1')
    except ParamInfo.DoesNotExist:
        pass

    if from_ui:
        try:
            return ParamInfo.objects.get(slug=slug.strip('1'))
        except ParamInfo.DoesNotExist:
            pass

    # Now try the same thing but with the old slug names
    try:
        return ParamInfo.objects.get(old_slug=slug_no_num)
    except ParamInfo.DoesNotExist:
        pass

    try:
        return ParamInfo.objects.get(old_slug=slug)
    except ParamInfo.DoesNotExist:
        pass

    try:
        return ParamInfo.objects.get(old_slug=slug + '1')
    except ParamInfo.DoesNotExist:
        pass

    if from_ui:
        try:
            return ParamInfo.objects.get(old_slug=slug.strip('1'))
        except ParamInfo.DoesNotExist:
            pass

    log.error('get_param_info_by_slug: Slug "%s" not found', slug)

    return None

################################################################################
#
# CREATE AN SQL QUERY
#
################################################################################

def construct_query_string(selections, extras):
    """Given a set selections,extras generate the appropriate SQL SELECT"""
    all_qtypes = extras['qtypes'] if 'qtypes' in extras else []
    finished_ranges = [] # Ranges are done for both sides at once so track
                         # which are finished to avoid duplicates

    clauses = []
    clause_params = []
    obs_tables = set()
    mult_tables = set()

    # We always have to have obs_general since it's the master keeper of IDs
    obs_tables.add('obs_general')

    cursor = connection.cursor()

    # We sort this so that testing results are predictable
    for param_qualified_name in sorted(selections.keys()):
        value_list = selections[param_qualified_name]
        # Lookup info about this param_qualified_name
        param_qualified_name_no_num = strip_numeric_suffix(param_qualified_name)
        param_info = _get_param_info_by_qualified_name(param_qualified_name)
        if not param_info:
            log.error('construct_query_string: No param_info for "%s"'
                      +' *** Selections %s *** Extras *** %s',
                      param_qualified_name,
                      str(selections), str(extras))
            return None, None
        cat_name = param_info.category_name
        quoted_cat_name = connection.ops.quote_name(cat_name)
        name = param_info.name

        if param_qualified_name_no_num in all_qtypes:
            qtypes = all_qtypes[param_qualified_name_no_num]
        else:
            qtypes = []

        (form_type, form_type_func,
         form_type_format) = parse_form_type(param_info.form_type)

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
                log.error('construct_query_string: Bad mult data for "%s", '
                          +'found %s'
                          +' *** Selections %s *** Extras *** %s',
                          param_qualified_name,
                          str(mult_values), str(selections), str(extras))
                return None, None
            if mult_values:
                clause = (quoted_cat_name+'.'
                          +connection.ops.quote_name(mult_name))
                clause += ' IN ('
                clause += ','.join(['%s']*len(mult_values))
                clause += ')'
                clauses.append(clause)
                clause_params += mult_values
                obs_tables.add(cat_name)

        elif form_type in settings.RANGE_FORM_TYPES:
            # This prevents range queries from getting through twice.
            # If one range side has been processed we can skip the 2nd, because
            # it gets done when the first is.
            if param_qualified_name_no_num in finished_ranges:
                continue

            finished_ranges.append(param_qualified_name_no_num)

            clause = None
            params = None

            # Longitude queries
            if form_type == 'LONG':
                # This parameter requires a longitudinal query.
                # Both sides of range must be defined by user for this to work.
                if (selections.get(param_qualified_name_no_num + '1', False) and
                    selections.get(param_qualified_name_no_num + '2', False)):
                    clause, params = get_longitude_query(selections,
                                                         param_qualified_name,
                                                         qtypes)
                else:
                    # XXX Need to report this to the user somehow
                    # Pretend this is a range query
                    clause, params = get_range_query(selections,
                                                     param_qualified_name,
                                                     qtypes)
            else:
                # Get the range query object and append it to the query
                clause, params = get_range_query(selections,
                                                 param_qualified_name,
                                                 qtypes)

            if clause is None:
                return None, None
            clauses.append(clause)
            clause_params += params
            obs_tables.add(cat_name)

        elif form_type == 'STRING':
            clause, params = get_string_query(selections, param_qualified_name,
                                              qtypes)
            if clause is None:
                return None, None
            clauses.append(clause)
            clause_params += params
            obs_tables.add(cat_name)

        else:
            log.error('construct_query_string: Unknown field type "%s" for '
                      +'param "%s"', form_type, param_qualified_name)

    # Make the ordering SQL
    order_sql = ''
    if 'order' in extras:
        order_params, descending_params = extras['order']

        (order_sql, order_mult_tables,
         order_obs_tables) = create_order_by_sql(order_params,
                                                 descending_params)
        if order_sql is None:
            return None, None
        mult_tables |= order_mult_tables
        obs_tables |= order_obs_tables

    sql = 'SELECT '
    sql += connection.ops.quote_name('obs_general')+'.'
    sql += connection.ops.quote_name('id')

    # Now JOIN all the obs_ tables together
    sql += ' FROM '+connection.ops.quote_name('obs_general')
    for table in sorted(obs_tables):
        if table == 'obs_general':
            continue
        sql += ' LEFT JOIN '+connection.ops.quote_name(table)
        sql += ' ON '+connection.ops.quote_name('obs_general')+'.'
        sql += connection.ops.quote_name('id')+'='
        sql += connection.ops.quote_name(table)+'.'
        sql += connection.ops.quote_name('obs_general_id')

    # And JOIN all the mult_ tables together
    for mult_table, category in sorted(mult_tables):
        sql += ' LEFT JOIN '+connection.ops.quote_name(mult_table)
        sql += ' ON '+connection.ops.quote_name(category)+'.'
        sql += connection.ops.quote_name(mult_table)+'='
        sql += connection.ops.quote_name(mult_table)+'.'
        sql += connection.ops.quote_name('id')

    # Add in the WHERE clauses
    if clauses:
        sql += ' WHERE '
        sql += ' AND '.join(['('+c+')' for c in clauses])

    # Add in the ORDER BY clause
    sql += order_sql

    # log.debug('SEARCH SQL: %s *** PARAMS %s', sql, str(clause_params))
    return sql, clause_params


def get_string_query(selections, param_qualified_name, qtypes):
    """Builds query for strings.

    The following q-types are supported:
        contains
        begins
        ends
        matches
        excludes
    """
    values = selections[param_qualified_name]

    param_info = _get_param_info_by_qualified_name(param_qualified_name)
    if not param_info:
        return None, None

    (form_type, form_type_func,
     form_type_format) = parse_form_type(param_info.form_type)
    table_name = param_info.category_name

    cat_name = param_info.category_name
    quoted_cat_name = connection.ops.quote_name(cat_name)
    name = param_info.name
    quoted_param_qualified_name = (quoted_cat_name+'.'
                                   +connection.ops.quote_name(name))

    if len(values) > 1:
        log.error('_get_string_query: More than one value specified for '
                  +'"%s" - "%s" '
                  +'*** Selections %s *** Qtypes %s ***',
                  param_qualified_name, str(values),
                  str(selections), str(qtypes))
        return None, None

    if len(qtypes) == 0:
        qtypes = ['contains']

    if len(qtypes) != 1:
        log.error('_get_string_query: Not one value specified for qtype '
                  +'for "%s"'
                  +'*** Selections %s *** Qtypes %s ***',
                  param_qualified_name, str(selections), str(qtypes))
        return None, None

    qtype = qtypes[0]
    value = values[0]

    clause = ''
    params = []

    if qtype == 'contains':
        clause = quoted_param_qualified_name + ' LIKE %s'
        params.append('%'+value+'%')
    elif qtype == 'begins':
        clause = quoted_param_qualified_name + ' LIKE %s'
        params.append(value+'%')
    elif qtype == 'ends':
        clause = quoted_param_qualified_name + ' LIKE %s'
        params.append('%'+value)
    elif qtype == 'matches':
        clause = quoted_param_qualified_name + ' = %s'
        params.append(value)
    elif qtype == 'excludes':
        clause = quoted_param_qualified_name + ' NOT LIKE %s'
        params.append('%'+value+'%')
    else:
        log.error('_get_string_query: Unknown qtype "%s" '
                  +'for "%s"'
                  +'*** Selections %s *** Qtypes %s ***',
                  qtype, param_qualified_name, str(selections), str(qtypes))

    return clause, params

def get_range_query(selections, param_qualified_name, qtypes):
    """Builds query for numeric ranges.

    This can either be a single column range (one table column holds the value)
    or a normal dual-column range (2 table columns hold min and max values).

    The following q-types are supported:
        any
        all
        only
    """
    param_info = _get_param_info_by_qualified_name(param_qualified_name)
    if not param_info:
        return None, None

    (form_type, form_type_func,
     form_type_format) = parse_form_type(param_info.form_type)
    table_name = param_info.category_name
    name = param_info.name

    param_qualified_name_no_num = strip_numeric_suffix(param_qualified_name)
    param_qualified_name_min = param_qualified_name_no_num + '1'
    param_qualified_name_max = param_qualified_name_no_num + '2'

    values_min = selections.get(param_qualified_name_min, [])
    values_max = selections.get(param_qualified_name_max, [])

    if len(values_min) > 1 or len(values_max) > 1:
        log.error('get_range_query: More than one value specified for '
                  +'"%s" - MIN %s MAX %s '
                  +'*** Selections %s *** Qtypes %s ***',
                  param_qualified_name, str(values_min), str(values_max),
                  str(selections), str(qtypes))
        return None, None

    # But, for constructing the query, if this is a single column range,
    # the param_names are both the same
    cat_name = param_info.category_name
    quoted_cat_name = connection.ops.quote_name(cat_name)
    name_no_num = strip_numeric_suffix(param_info.name)
    name_min = name_no_num + '1'
    name_max = name_no_num + '2'

    if is_single_column_range(param_qualified_name):
        param_qualified_name_min = param_qualified_name_no_num
        param_qualified_name_max = param_qualified_name_no_num
        name_min = name_max = name_no_num
        # qtypes are meaningless for single column ranges!
        qtypes = ['any']

    quoted_param_qualified_name_min = (quoted_cat_name+'.'
                                       +connection.ops.quote_name(name_min))
    quoted_param_qualified_name_max = (quoted_cat_name+'.'
                                       +connection.ops.quote_name(name_max))

    if len(qtypes) == 0:
        qtypes = ['any']

    if len(qtypes) != 1:
        log.error('get_range_query: Not one value specified for qtype '
                  +'for "%s"'
                  +'*** Selections %s *** Qtypes %s ***',
                  param_qualified_name, str(selections), str(qtypes))
        return None, None

    # If we want to support more than one set of range fields, loop here
    if len(values_min):
        value_min = values_min[0]
    else:
        value_min = None
    if len(values_max):
        value_max = values_max[0]
    else:
        value_max = None
    qtype = qtypes[0]

    clause = ''
    params = []

    if qtype == 'all':
        # param_name_min <= value_min AND param_name_max >= value_max
        if value_min is not None:
            clause += quoted_param_qualified_name_min + ' <= %s'
            params.append(value_min)
        if value_max is not None:
            if clause:
                clause += ' AND '
            clause += quoted_param_qualified_name_max + ' >= %s'
            params.append(value_max)

    elif qtype == 'only':
        # param_name_min >= value_min AND param_name_max <= value_max
        if value_min is not None:
            clause += quoted_param_qualified_name_min + ' >= %s'
            params.append(value_min)
        if value_max is not None:
            if clause:
                clause += ' AND '
            clause += quoted_param_qualified_name_max + ' <= %s'
            params.append(value_max)

    elif qtype == 'any' or qtype == '':
        # param_name_min <= value_max AND param_name_max >= value_min
        if value_min is not None:
            clause += quoted_param_qualified_name_max + ' >= %s'
            params.append(value_min)
        if value_max is not None:
            if clause:
                clause += ' AND '
            clause += quoted_param_qualified_name_min + ' <= %s'
            params.append(value_max)

    else:
        log.error('get_range_query: Unknown qtype "%s" '
                  +'for "%s"'
                  +'*** Selections %s *** Qtypes %s ***',
                  qtype, param_qualified_name, str(selections), str(qtypes))

    return clause, params

def get_longitude_query(selections, param_qualified_name, qtypes):
    """Builds query for longitude ranges.

    Both sides of the range must be specified.

    The following q-types are supported:
        any
        all
        only
    """

    param_info = _get_param_info_by_qualified_name(param_qualified_name)
    if not param_info:
        return None, None

    (form_type, form_type_func,
     form_type_format) = parse_form_type(param_info.form_type)
    table_name = param_info.category_name
    name = param_info.name

    param_qualified_name_no_num = strip_numeric_suffix(param_qualified_name)
    param_qualified_name_min = param_qualified_name_no_num + '1'
    param_qualified_name_max = param_qualified_name_no_num + '2'

    values_min = selections.get(param_qualified_name_min, [])
    values_max = selections.get(param_qualified_name_max, [])

    if len(values_min) != 1 or len(values_max) != 1:
        log.error('get_longitude_query: Must have one value for each '
                  +'"%s" - MIN %s MAX %s '
                  +'*** Selections %s *** Qtypes %s ***',
                  param_qualified_name, str(values_min), str(values_max),
                  str(selections), str(qtypes))
        return None, None

    # But, for constructing the query, if this is a single column range,
    # the param_names are both the same
    cat_name = param_info.category_name
    quoted_cat_name = connection.ops.quote_name(cat_name)
    name_no_num = strip_numeric_suffix(param_info.name)
    name_min = name_no_num + '1'
    name_max = name_no_num + '2'
    col_d_long = cat_name + '.d_' + name_no_num

    if len(qtypes) == 0:
        qtypes = ['any']

    if len(qtypes) != 1:
        log.error('get_longitude_query: Not one value specified for qtype '
                  +'for "%s"'
                  +'*** Selections %s *** Qtypes %s ***',
                  param_qualified_name, str(selections), str(qtypes))
        return None, None

    # If we want to support more than one set of range fields, loop here
    # XXX Need to add parameter validation here
    value_min = float(values_min[0])
    value_max = float(values_max[0])
    qtype = qtypes[0]

    if is_single_column_range(param_qualified_name):
        # A single column range doesn't have center and d_ fields
        clause = ''
        params = []
        quoted_param_qualified_name = (quoted_cat_name+'.'
                                       +connection.ops.quote_name(name_no_num))
        if value_max >= value_min:
            # Normal range MIN to MAX
            clause = '(' + quoted_param_qualified_name + ' >= %s AND '
            clause += quoted_param_qualified_name + ' <= %s)'
            params = [value_min, value_max]
        else:
            # Wraparound range MIN to 360, 0 to MAX
            clause = '(' + quoted_param_qualified_name + ' >= %s OR '
            clause += quoted_param_qualified_name + ' <= %s)'
            params = [value_min, value_max]
        return clause, params

    quoted_param_qualified_name_min = (quoted_cat_name+'.'
                                       +connection.ops.quote_name(name_min))
    quoted_param_qualified_name_max = (quoted_cat_name+'.'
                                       +connection.ops.quote_name(name_max))


    # Find the midpoint and dx of the user's range
    if value_max >= value_min:
        longit = (value_min + value_max)/2.
    else:
        longit = (value_min + value_max + 360.)/2.
    longit = longit % 360.
    d_long = (longit - value_min) % 360.
    sep_sql = 'ABS(MOD(%s - ' + param_qualified_name_no_num + ' + 540., 360.) - 180.)'
    sep_params = [longit]

    clause = ''
    params = []

    if qtype == 'any' or qtype == '':
        clause += sep_sql + ' <= %s + ' + col_d_long
        params += sep_params
        params.append(d_long)
    elif qtype == 'all':
        clause += sep_sql + ' <= ' + col_d_long + ' - %s'
        params += sep_params
        params.append(d_long)
    elif qtype == 'only':
        clause += sep_sql + ' <= %s - ' + col_d_long
        params += sep_params
        params.append(d_long)
    else:
        log.error('get_longitude_query: Unknown qtype "%s" '
                  +'for "%s"'
                  +'*** Selections %s *** Qtypes %s ***',
                  qtype, param_name, str(selections), str(qtypes))

    return clause, params

def get_user_search_table_name(num):
    """ pass cache_no, returns user search table name"""
    return 'cache_' + str(num);


################################################################################
#
# INTERNAL SUPPORT ROUTINES
#
################################################################################

def _get_param_info_by_qualified_name(param_qualified_name):
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


def is_single_column_range(param_qualified_name):
    "Given a qualified name cat.name return True if it's a single-column range"
    if param_qualified_name.find('.') == -1:
        return False

    cat_name = param_qualified_name.split('.')[0]
    name = param_qualified_name.split('.')[1]

    # Single column range queries will not have the numeric suffix
    name_no_num = strip_numeric_suffix(name)
    try:
        temp = ParamInfo.objects.get(category_name=cat_name,
                                     name=name_no_num)
        return True
    except ParamInfo.DoesNotExist:
        return False

    return False


def _clean_numeric_field(s):
    clean_func = lambda x: x.replace(' ', '').replace(',', '').replace('_','')
    if isinstance(s, (list, tuple)):
        return [clean_func(z) for z in s]

    return clean_func(s)


def parse_order_slug(all_order):
    "Given a list of slugs a,b,-c,d create the params and descending lists"
    order_params = []
    order_descending_params = []

    if not all_order:
        all_order = settings.DEFAULT_SORT_ORDER
    if (settings.FINAL_SORT_ORDER
        not in all_order.replace('-','').split(',')):
        if all_order:
            all_order += ','
        all_order += settings.FINAL_SORT_ORDER
    orders = all_order.split(',')
    for order in orders:
        descending = order[0] == '-'
        order = order.strip('-')
        param_info = get_param_info_by_slug(order, from_ui=True)
        if not param_info:
            log.error('parse_order_slug: Unable to resolve order '
                      +'slug "%s"', order)
            return None, None
        order_params.append(param_info.param_qualified_name())
        order_descending_params.append(descending)

    return order_params, order_descending_params

def create_order_by_sql(order_params, descending_params):
    "Given params and descending lists, make ORDER BY SQL"
    order_mult_tables = set()
    order_obs_tables = set()
    order_sql = ''
    if order_params:
        order_str_list = []
        for i in range(len(order_params)):
            order_slug = order_params[i]
            pi = _get_param_info_by_qualified_name(order_slug)
            if not pi:
                log.error('construct_query_string: Unable to resolve order'
                          +' slug "%s"', order_slug)
                return None, None, None
            (form_type, form_type_func,
             form_type_format) = parse_form_type(pi.form_type)
            order_param = pi.param_qualified_name()
            order_obs_tables.add(pi.category_name)
            if form_type in settings.MULT_FORM_TYPES:
                mult_table = get_mult_name(pi.param_qualified_name())
                order_param = mult_table + '.label'
                order_mult_tables.add((mult_table, pi.category_name))
            if descending_params[i]:
                order_param += ' DESC'
            else:
                order_param += ' ASC'
            order_str_list.append(order_param)
        order_sql = ' ORDER BY ' + ','.join(order_str_list)

    return order_sql, order_mult_tables, order_obs_tables
