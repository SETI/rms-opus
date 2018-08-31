################################################################################
#
# ui/views.py
#
################################################################################

import hashlib
import json
import julian
import logging
from operator import __or__ as OR
import sys

from pyparsing import ParseException

import settings

from django.apps import apps
from django.conf import settings
from django.core.cache import cache
from django.db import connection, DatabaseError
from django.db.models import Q
from django.db.models.sql.datastructures import EmptyResultSet

from paraminfo.models import ParamInfo
from search.models import *
from tools.app_utils import *
from tools.db_utils import *

import opus_support

log = logging.getLogger(__name__)


def url_to_search_params(request_get):
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
    search_params = request_get.items()
    if 'order' not in [x[0] for x in search_params]:
        # If there's no order slug, then force one
        search_params.append(('order', settings.DEFAULT_SORT_ORDER))
    for search_param in search_params:
        slug = search_param[0]
        if slug == 'order':
            if search_param[1]:
                all_order = search_param[1]
            else:
                all_order = settings.DEFAULT_SORT_ORDER
            if settings.FINAL_SORT_ORDER not in all_order.split(','):
                if all_order:
                    all_order += ','
                all_order += settings.FINAL_SORT_ORDER
            orders = all_order.split(',')
            for order in orders:
                descending = order[0] == '-'
                order = order.strip('-')
                param_info = get_param_info_by_slug(order, from_ui=True)
                if not param_info:
                    log.error('url_to_search_params: Unable to resolve order '
                              +'slug "%s"', order)
                    return None, None
                order_params.append(param_info.param_name())
                order_descending_params.append(descending)
            extras['order'] = (order_params, order_descending_params)
            continue
        if slug in settings.SLUGS_NOT_IN_DB:
            continue
        slug_no_num = strip_numeric_suffix(slug)
        values = search_param[1].strip(',').split(',')

        if not values:
            # If nothing is specified, just ignore the slug
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

        param_name = param_info.param_name()
        (form_type, form_type_func,
         form_type_format) = parse_form_type(param_info.form_type)

        param_name_no_num = strip_numeric_suffix(param_name)

        if qtype:
            if param_name_no_num in qtypes:
                log.error('url_to_search_params: Duplicate slug for '
                          +'qtype "%s": %s', param_name_no_num, request_get)
                return None, None
            qtypes[param_name_no_num] = values
            continue

        if form_type in settings.MULT_FORM_TYPES:
            # Mult form types can be sorted and uniquified to save duplicate
            # queries being built.
            # No other form types can be sorted since their ordering
            # corresponds to qtype ordering.
            if param_name in selections:
                log.error('url_to_search_params: Duplicate slug for '
                          +'"%s": %s', param_name, request_get)
                return None, None
            selections[param_name] = sorted(set(values))
        elif form_type == 'RANGE':
            # For RANGE queries, convert the strings into the internal
            # representations if necessary
            if form_type_func is None:
                func = float
            else:
                if form_type_func in opus_support.RANGE_FUNCTIONS:
                    func = (opus_support
                            .RANGE_FUNCTIONS[form_type_func][1])
                else:
                    log.error('url_to_search_params: Unknown RANGE '
                              +'function "%s"', form_type_func)
                    return None, None
            if param_name == param_name_no_num:
                # This is a single column range query
                ext = slug[-1]
                if param_name+ext in selections:
                    log.error('url_to_search_params: Duplicate slug '
                              +'for "%s": %s', param_name+ext,
                              request_get)
                    return None, None
                try:
                    selections[param_name + ext] = map(func, values)
                except ValueError,e:
                    log.error('url_to_search_params: Function "%s" '
                              +'threw ValueError(%s) for %s',
                              func, e, values)
            else:
                # Normal 2-column range query
                if param_name in selections:
                    log.error('url_to_search_params: Duplicate slug '
                              +'for "%s": %s', param_name,
                              request_get)
                    return None, None
                try:
                    selections[param_name] = map(func, values)
                except ValueError,e:
                    log.error('url_to_search_params: Function "%s" '
                              +'threw ValueError(%s) for %s',
                              func, e, values)
        else:
            # For non-RANGE queries, we just put the values here raw
            if param_name in selections:
                log.error('url_to_search_params: Duplicate slug '
                          +'for "%s": %s', param_name,
                          request_get)
                return None, None
            selections[param_name] = values

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
    cache_table_num = set_user_search_number(selections, extras)
    if cache_table_num is None:
        log.error('get_user_query_table: Failed to create cache table '+
                  '*** Selections %s *** Extras %s',
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
    except DatabaseError,e:
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
    sql, params = _construct_query_string(selections, extras)
    if sql is None:
        log.error('get_user_query_table: _construct_query_string failed'
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
    except DatabaseError,e:
        if e.args[0] == MYSQL_TABLE_ALREADY_EXISTS:
            log.error('get_user_query_table: Table "%s" originally didn\'t '+
                      'exist, but now it does!', cache_table_name)
            return cache_table_name
        log.error('get_user_query_table: "%s" with params "%s" failed with '
                  +'%s', create_sql, str(tuple(params)), str(e))
        return None
    log.debug('API %s (%.3f) get_user_query_table: %s *** PARAMS %s',
              str(api_code), time.time()-time1, create_sql, str(params))

    # alter_sql = ('ALTER TABLE '
    #              + connection.ops.quote_name(cache_table_name)
    #              + ' ADD UNIQUE KEY(id)')
    # try:
    #     cursor.execute(alter_sql)
    # except DatabaseError,e:
    #     log.error('get_user_query_table: "%s" with params "%s" failed with %s',
    #               alter_sql, str(tuple(params)), str(e))
    #     return None

    cache.set(cache_key, cache_table_name)
    return cache_table_name


def set_user_search_number(selections, extras):
    """Creates a new row in the user_searches table for each search request.

    This table lists query params+values plus any extra info needed to
    run a data search query.
    This method looks in user_searches table for current selections.
    If none exist, creates it.
    """
    if selections is None or extras is None:
        return None

    qtypes_json = qtypes_hash = None
    if 'qtypes' in extras:
        if len(extras['qtypes']):
            qtypes_json = str(json.dumps(sort_dictionary(extras['qtypes'])))
            qtypes_hash = hashlib.md5(qtypes_json).hexdigest()

    units_json = units_hash = None
    if 'units' in extras:
        units_json = str(json.dumps(sort_dictionary(extras['units'])))
        units_hash = hashlib.md5(units_json).hexdigest()

    order_json = order_hash = None
    if 'order' in extras:
        order_json = str(json.dumps(extras['order']))
        order_hash = hashlib.md5(order_json).hexdigest()

    selections_json = str(json.dumps(sort_dictionary(selections)))
    selections_hash = hashlib.md5(selections_json).hexdigest()

    cache_key = ('usersearchno:selections_hash:' + str(selections_hash)
                 +':qtypes_hash:' + str(qtypes_hash)
                 +':units_hash:' + str(units_hash)
                 +':order_hash:' + str(order_hash))
    cached_val = cache.get(cache_key)
    if cached_val is not None:
        return cached_val

    try:
        s = UserSearches.objects.get(selections_hash=selections_hash,
                                     qtypes_hash=qtypes_hash,
                                     units_hash=units_hash,
                                     order_hash=order_hash)
    except UserSearches.MultipleObjectsReturned:
        s = UserSearches.objects.filter(selections_hash=selections_hash,
                                        qtypes_hash=qtypes_hash,
                                        units_hash=units_hash,
                                        order_hash=order_hash)
        s = s[0]
        log.error('set_user_search_number: Multiple entries in user_searches '
                  +' for *** Selections %s *** Qtypes %s *** Units %s '
                  +' *** Order %s',
                  str(selections_json),
                  str(qtypes_json),
                  str(units_json),
                  str(order_json))
    except UserSearches.DoesNotExist:
        s = UserSearches(selections_json=selections_json,
                         selections_hash=selections_hash,
                         qtypes_json=qtypes_json,
                         qtypes_hash=qtypes_hash,
                         units_json=units_json,
                         units_hash=units_hash,
                         order_json=order_json,
                         order_hash=order_hash)
        s.save()

    cache.set(cache_key, s.id)
    return s.id


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

def _construct_query_string(selections, extras):
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

    for param_name, value_list in selections.items():
        # Lookup info about this param_name
        param_name_no_num = strip_numeric_suffix(param_name)
        param_info = _get_param_info_by_qualified_name(param_name)
        cat_name = param_info.category_name
        quoted_cat_name = connection.ops.quote_name(cat_name)
        name = param_info.name
        if not param_info:
            log.error('_construct_query_string: No param_info for "%s"'
                      +' *** Selections %s *** Extras *** %s', param_name,
                      str(selections), str(extras))
            return None, None

        if param_name_no_num in all_qtypes:
            qtypes = all_qtypes[param_name_no_num]
        else:
            qtypes = []

        (form_type, form_type_func,
         form_type_format) = parse_form_type(param_info.form_type)

        if form_type in settings.MULT_FORM_TYPES:
            # This is where we convert from the "pretty" name the user selected
            # to the internal name stored in the database and mapped to the
            # mult table.
            mult_name = get_mult_name(param_name)
            model_name = mult_name.title().replace('_','')
            model = apps.get_model('search', model_name)
            mult_values = [x['pk'] for x in
                           list(model.objects.filter(  Q(label__in=value_list)
                                                     | Q(value__in=value_list))
                                             .values('pk'))]
            clause = quoted_cat_name+'.'+connection.ops.quote_name(mult_name)
            clause += ' IN ('
            clause += ','.join(['%s']*len(mult_values))
            clause += ')'
            clauses.append(clause)
            clause_params += mult_values
            obs_tables.add(cat_name)

        elif form_type in settings.RANGE_FIELDS:
            # This prevents range queries from getting through twice.
            # If one range side has been processed we can skip the 2nd, because
            # it gets done when the first is.
            if param_name_no_num in finished_ranges:
                continue

            finished_ranges.append(param_name_no_num)

            clause = None
            params = None

            # Longitude queries
            if form_type == 'LONG':
                # This parameter requires a longitudinal query.
                # Both sides of range must be defined by user for this to work.
                if (selections[param_name_no_num + '1'] and
                    selections[param_name_no_num + '2']):
                    clause, params = _get_longitude_query(selections,
                                                          param_name, qtypes)
                else:
                    return None, None
            else:
                # Get the range query object and append it to the query
                clause, params = _get_range_query(selections, param_name,
                                                         qtypes)

            if clause is None:
                return None, None
            clauses.append(clause)
            clause_params += params
            obs_tables.add(cat_name)

        elif form_type == 'STRING':
            clause, params = _get_string_query(selections, param_name,
                                                      value_list, qtypes)
            if clause is None:
                return None, None
            clauses.append(clause)
            clause_params += params
            obs_tables.add(cat_name)

        else:
            log.error('_construct_query_string: Unknown field type "%s" for '
                      +'param "%s"', form_type, param_name)

    # Make the ordering SQL
    order_sql = ''
    if 'order' in extras:
        order_table_names = set()
        order_params, descending_params = extras['order']
        if order_params:
            order_str_list = []
            for i in range(len(order_params)):
                order = order_params[i]
                pi = _get_param_info_by_qualified_name(order)
                if not pi:
                    log.error('_construct_query_string: Unable to resolve order'
                              +' slug "%s"', order)
                    return None, None
                (form_type, form_type_func,
                 form_type_format) = parse_form_type(pi.form_type)
                if form_type in settings.MULT_FIELDS:
                    mult_table = get_mult_name(pi.param_name())
                    order_param = mult_table + '.label'
                else:
                    order_param = pi.param_name()
                table = order_param.split('.')[0]
                obs_tables.add(table)
                if descending_params[i]:
                    order += ' DESC'
                else:
                    order += ' ASC'
                order_str_list.append(order)
            order_sql = ' ORDER BY ' + ','.join(order_str_list)


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

    # Add in the WHERE clauses
    if clauses:
        sql += ' WHERE '
        sql += ' AND '.join(['('+c+')' for c in clauses])

    # Add in the ORDER BY clause
    sql += order_sql

    # log.debug('SEARCH SQL: %s *** PARAMS %s', sql, str(clause_params))
    return sql, clause_params


def _get_string_query(selections, param_name, values, qtypes):
    """Builds query for strings.

    The following q-types are supported:
        contains
        begins
        ends
        matches
        excludes
    """
    param_info = _get_param_info_by_qualified_name(param_name)
    if not param_info:
        return None, None

    (form_type, form_type_func,
     form_type_format) = parse_form_type(param_info.form_type)
    table_name = param_info.category_name

    cat_name = param_info.category_name
    quoted_cat_name = connection.ops.quote_name(cat_name)
    name = param_info.name
    quoted_param_name = (quoted_cat_name+'.'
                         +connection.ops.quote_name(name))

    if len(values) > 1:
        log.error('_get_string_query: More than one value specified for '
                  +'"%s" - "%s" '
                  +'*** Selections %s *** Qtypes %s ***',
                  param_name, str(values),
                  str(selections), str(qtypes))
        return None, None

    if len(qtypes) == 0:
        qtypes = ['contains']

    if len(qtypes) != 1:
        log.error('_get_string_query: Not one value specified for qtype '
                  +'for "%s"'
                  +'*** Selections %s *** Qtypes %s ***',
                  param_name, str(selections), str(qtypes))
        return None, None

    qtype = qtypes[0]
    value = values[0]

    clause = ''
    params = []

    if qtype == 'contains':
        clause = quoted_param_name + ' LIKE %s'
        params.append('%'+value+'%')
    elif qtype == 'begins':
        clause = quoted_param_name + ' LIKE %s'
        params.append(value+'%')
    elif qtype == 'ends':
        clause = quoted_param_name + ' LIKE %s'
        params.append('%'+value)
    elif qtype == 'matches':
        clause = quoted_param_name + ' = %s'
        params.append(value)
    elif qtype == 'excludes':
        clause = quoted_param_name + ' NOT LIKE %s'
        params.append('%'+value+'%')
    else:
        log.error('_get_string_query: Unknown qtype "%s" '
                  +'for "%s"'
                  +'*** Selections %s *** Qtypes %s ***',
                  qtype, param_name, str(selections), str(qtypes))

    return clause, params

def _get_range_query(selections, param_name, qtypes):
    """Builds query for numeric ranges.

    This can either be a single column range (one table column holds the value)
    or a normal dual-column range (2 table columns hold min and max values).

    The following q-types are supported:
        any
        all
        only
    """
    param_info = _get_param_info_by_qualified_name(param_name)
    if not param_info:
        return None, None

    (form_type, form_type_func,
     form_type_format) = parse_form_type(param_info.form_type)
    table_name = param_info.category_name
    name = param_info.name

    param_name_no_num = strip_numeric_suffix(param_name)
    param_name_min = param_name_no_num + '1'
    param_name_max = param_name_no_num + '2'

    values_min = selections.get(param_name_min, [])
    values_max = selections.get(param_name_max, [])

    if len(values_min) > 1 or len(values_max) > 1:
        log.error('_get_range_query: More than one value specified for '
                  +'"%s" - MIN %s MAX %s '
                  +'*** Selections %s *** Qtypes %s ***',
                  param_name, str(values_min), str(values_max),
                  str(selections), str(qtypes))
        return None, None

    # But, for constructing the query, if this is a single column range,
    # the param_names are both the same
    cat_name = param_info.category_name
    quoted_cat_name = connection.ops.quote_name(cat_name)
    name_no_num = strip_numeric_suffix(param_info.name)
    name_min = name_no_num + '1'
    name_max = name_no_num + '2'

    if _is_single_column_range(param_name):
        param_name_min = param_name_max = param_name_no_num
        name_min = name_max = name_no_num

    quoted_param_name_min = (quoted_cat_name+'.'
                             +connection.ops.quote_name(name_min))
    quoted_param_name_max = (quoted_cat_name+'.'
                             +connection.ops.quote_name(name_max))

    if len(qtypes) == 0:
        qtypes = ['any']

    if len(qtypes) != 1:
        log.error('_get_range_query: Not one value specified for qtype '
                  +'for "%s"'
                  +'*** Selections %s *** Qtypes %s ***',
                  param_name, str(selections), str(qtypes))
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
            clause += quoted_param_name_min + ' <= %s'
            params.append(value_min)
        if value_max is not None:
            if clause:
                clause += ' AND '
            clause += quoted_param_name_max + ' >= %s'
            params.append(value_max)

    elif qtype == 'only':
        # param_name_min >= value_min AND param_name_max <= value_max
        if value_min is not None:
            clause += quoted_param_name_min + ' >= %s'
            params.append(value_min)
        if value_max is not None:
            if clause:
                clause += ' AND '
            clause += quoted_param_name_max + ' <= %s'
            params.append(value_max)

    elif qtype == 'any' or qtype == '':
        # param_name_min <= value_max AND param_name_max >= value_min
        if value_min is not None:
            clause += quoted_param_name_max + ' >= %s'
            params.append(value_min)
        if value_max is not None:
            if clause:
                clause += ' AND '
            clause += quoted_param_name_min + ' <= %s'
            params.append(value_max)

    else:
        log.error('_get_range_query: Unknown qtype "%s" '
                  +'for "%s"'
                  +'*** Selections %s *** Qtypes %s ***',
                  qtype, param_name, str(selections), str(qtypes))

    return clause, params

def _get_longitude_query(selections, param_name, qtypes):
    """Builds query for longitude ranges.

    Both sides of the range must be specified.

    The following q-types are supported:
        any
        all
        only
    """

    param_info = _get_param_info_by_qualified_name(param_name)
    if not param_info:
        return None, None

    (form_type, form_type_func,
     form_type_format) = parse_form_type(param_info.form_type)
    table_name = param_info.category_name
    name = param_info.name

    param_name_no_num = strip_numeric_suffix(param_name)
    param_name_min = param_name_no_num + '1'
    param_name_max = param_name_no_num + '2'

    values_min = selections.get(param_name_min, [])
    values_max = selections.get(param_name_max, [])

    if len(values_min) != 1 or len(values_max) != 1:
        log.error('_get_longitude_query: Must have one value for each '
                  +'"%s" - MIN %s MAX %s '
                  +'*** Selections %s *** Qtypes %s ***',
                  param_name, str(values_min), str(values_max),
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

    if _is_single_column_range(param_name):
        param_name_min = param_name_max = param_name_no_num
        name_min = name_max = name_no_num

    quoted_param_name_min = (quoted_cat_name+'.'
                             +connection.ops.quote_name(name_min))
    quoted_param_name_max = (quoted_cat_name+'.'
                             +connection.ops.quote_name(name_max))

    if len(qtypes) == 0:
        qtypes = ['any']

    if len(qtypes) != 1:
        log.error('_get_longitude_query: Not one value specified for qtype '
                  +'for "%s"'
                  +'*** Selections %s *** Qtypes %s ***',
                  param_name, str(selections), str(qtypes))
        return None, None

    # If we want to support more than one set of range fields, loop here
    # XXX Need to add parameter validation here
    value_min = float(values_min[0])
    value_max = float(values_max[0])
    qtype = qtypes[0]

    # Find the midpoint and dx of the user's range
    if value_max >= value_min:
        longit = (value_min + value_max)/2.
    else:
        longit = (value_min + value_max + 360.)/2.
    longit = longit % 360.
    d_long = (longit - value_min) % 360.
    sep_sql = 'ABS(MOD(%s - ' + param_name_no_num + ' + 540., 360.) - 180.)'
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
        log.error('_get_longitude_query: Unknown qtype "%s" '
                  +'for "%s"'
                  +'*** Selections %s *** Qtypes %s ***',
                  qtype, param_name, str(selections), str(qtypes))

    return clause, params

def convertTimes(value_list):
    """ other conversion scripts are 'seconds_to_time','seconds_to_et' """
    converted = []
    for time in value_list:
        try:
            (day, sec, timetype) = julian.day_sec_type_from_string(time)
            time_sec = julian.tai_from_day(day) + sec
            converted += [time_sec]
        except ParseException:
            log.error("Could not convert time: %s", time)
            converted += [None]
    return converted


def get_user_search_table_name(num):
    """ pass cache_no, returns user search table name"""
    return 'cache_' + str(num);


################################################################################
#
# INTERNAL SUPPORT ROUTINES
#
################################################################################

def _get_param_info_by_qualified_name(param_name):
    "Given a qualified name cat.name return the ParamInfo"
    cat_name = param_name.split('.')[0]
    name = param_name.split('.')[1]

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


def _is_single_column_range(param_name):
    "Given a qualified name cat.name return True if it's a single-column range"
    cat_name = param_name.split('.')[0]
    name = param_name.split('.')[1]

    try:
        param_info = ParamInfo.objects.get(category_name=cat_name, name=name)
        return False
    except ParamInfo.DoesNotExist:
        # Single column range queries will not have the numeric suffix
        name_no_num = strip_numeric_suffix(name)
        try:
            temp = ParamInfo.objects.get(category_name=cat_name,
                                         name=name_no_num)
            return True
        except ParamInfo.DoesNotExist:
            return False
