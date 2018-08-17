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
            lists and represent the users selections
        The 2nd dict is any extras being passed by user, like qtypes that
            define what types of queries will be performed for each
            param-value set in the first dict, or sort order

    NOTE: pass request_get = request.GET to this func please
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
        if slug == 'order' and search_param[1]:
            if 'order' in qtypes:
                log.error('url_to_search_params: Duplicate slug for '
                          +'"order": %s', request_get)
                return None, None
            all_order = search_param[1]
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
        else:
            if search_param[1]:
                if form_type == 'RANGE':
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


def get_user_query_table(selections, extras):
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
    try:
        desc_sql = 'DESC ' + connection.ops.quote_name(cache_table_name)
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

    # sql_order = _construct_sort_string(selections, extras)
    sql_order = ''

    # With this we can create a table that contains the single column
    create_sql = ('CREATE TABLE '
                  + connection.ops.quote_name(cache_table_name)
                  + ' ' + sql + ' ' + sql_order)
    log.debug('get_user_query_table: %s', create_sql)
    try:
        cursor.execute(create_sql, tuple(params))
    except DatabaseError,e:
        if e.args[0] == MYSQL_TABLE_ALREADY_EXISTS:
            log.error('get_user_query_table: Table "%s" originally didn\'t '+
                      'exist, but now it does!', cache_table_name)
            return cache_table_name
        log.error('get_user_query_table: "%s" with params "%s" failed with '
                  +'%s', create_sql, str(tuple(params)), str(e))
        return None
    # XXXXXXXXXX THIS APPEARS TO SORT THE ID FIELD!!! XXXXXXXXX
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

    This table (model) lists query params+values plus any extra info needed to
    run a data search query.
    This method looks in user_searches table for current selections.
    If none exist, creates it.
    """
    if selections is None or extras is None:
        return None

    qtypes_json = qtypes_hash = None
    if 'qtypes' in extras:
        # 'any' and 'contains' are the default qtypes, so lets not set that in
        # the cache.
        # We need to make a copy of the key list because it's going to change
        # out from under us
        for k in list(extras['qtypes'].keys())[:]:
            qlist = extras['qtypes'][k]
            extras['qtypes'][k] = [x for x in qlist
                                         if x != 'any' and x != 'contains']
            if len(extras['qtypes'][k]) == 0:
                del extras['qtypes'][k]
        if len(extras['qtypes']):
            qtypes_json = str(json.dumps(sort_dictionary(extras['qtypes'])))
            qtypes_hash = hashlib.md5(qtypes_json).hexdigest()

    units_json = units_hash = None
    if 'units' in extras:
        units_json = str(json.dumps(sort_dictionary(extras['units'])))
        units_hash = hashlib.md5(units_json).hexdigest()

    order_json = order_hash = None
    if 'order' in extras:
        default_sort_order = get_param_info_by_slug(settings.DEFAULT_SORT_ORDER)
        if (len(extras['order'][0]) >= 1 and
            (extras['order'][0][0] != default_sort_order.param_name() or
             extras['order'][1][0] != False)):
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
                  +' for *** Selections %s *** Qtypes %s *** Units %s '+
                  +' *** Order %s',
                  str(selections_json,
                  str(qtypes_json),
                  str(units_json),
                  str(order_json)))
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


def _construct_query_string(selections, extras):
    """Given a set selections,extras generate the appropriate SQL SELECT"""
    all_qtypes = extras['qtypes'] if 'qtypes' in extras else []
    long_queries = []    # Special longitudinal queries are pure sql
    q_objects = []       # For building up the query object
    finished_ranges = [] # Ranges are done for both sides at once so track
                         # which are finished to avoid duplicates

    for param_name, value_list in selections.items():
        # Lookup info about this param_name
        param_name_no_num = strip_numeric_suffix(param_name)
        param_info = _get_param_info_by_qualified_name(param_name)
        cat_name = param_info.category_name
        name = param_info.name
        # Django model names in query strings are in all lower case
        # not title case!
        cat_model_name = ''.join(cat_name.lower().split('_'))
        if not param_info:
            log.error('_construct_query_string: No param_info for "%s"'
                      +' *** Selections %s *** Extras *** %s', param_name,
                      str(selections), str(extras))
            return None, None

        special_query = param_info.special_query

        # define any qtypes for this param_name from query
        if param_name_no_num in all_qtypes:
            qtypes = all_qtypes[param_name_no_num]
        else:
            qtypes = []

        # now build the q_objects to run the query, by form_type:

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
            if cat_name != 'obs_general':
                q_objects.append(
                    Q(**{"%s__%s__in" % (cat_model_name, mult_name):
                         mult_values }))
            else:
                q_objects.append(
                    Q(**{"%s__in" % mult_name: mult_values }))

        elif form_type in settings.RANGE_FIELDS:
            # This prevents range queries from getting through twice.
            # If one range side has been processed we can skip the 2nd, because
            # it gets done when the first is.
            if param_name_no_num in finished_ranges:
                continue

            finished_ranges.append(param_name_no_num)

            # Longitude queries
            if special_query == 'long':
                # This parameter requires a longitudinal query.
                # These are crazy sql and can't use Django's model interface,
                # so after converting the rest of the query params from Django
                # model statements to SQL these are tacked on at the end.
                # Both sides of range must be defined by user for this to work.
                if (selections[param_name_no_num + '1'] and
                    selections[param_name_no_num + '2']):
                    lq, lq_params = _get_longitude_query(selections, param_name)
                    long_queries.append((lq, lq_params))
                else:
                    return None, None
            else:
                # Get the range query object and append it to the query
                q_obj = _get_range_query_object(selections, param_name, qtypes)
                q_objects.append(q_obj)

        elif form_type == 'STRING':
            q_obj = _get_string_query_object(param_name, value_list, qtypes)
            q_objects.append(q_obj)

        else:
            log.error('_construct_query_string: Unknown field type "%s" for '
                      +'param "%s"', form_type, param_name)

    # Construct our query. We'll be breaking into raw sql, but for that
    # we'll be using the SQL Django generates through its model interface.
    try:
        sql, params = (ObsGeneral.objects.filter(*q_objects).values('pk')
                                 .query.sql_with_params())
    except EmptyResultSet:
        return None, None

    # Append any longitudinal queries to the query string
    if long_queries:
        params = list(params)

        if 'where' in sql.lower():
            sql += ' AND obs_general.id IN '
        else:
            sql += ' WHERE obs_general.id IN '

        sql += (' AND obs_general.id IN '
                .join([" (%s) " % long_query[0]
                           for long_query in long_queries]))
        for long_q in long_queries:
            params += list(long_query[1])

        params = tuple(params)

    # Add in the ordering
    if 'order' in extras:
        order_params, descending_params = extras['order']
        if order_params:
            order_str_list = []
            for i in range(len(order_params)):
                s = order_params[i]
                if descending_params[i]:
                    s += ' DESC'
                else:
                    s += ' ASC'
                order_str_list.append(s)
            sql += ' ORDER BY ' + ','.join(order_str_list)

    log.debug('SEARCH SQL: %s *** PARAMS %s', sql, str(params))
    return sql, params


def _get_string_query_object(param_name, value_list, qtypes):

    cat_name, param = param_name.split('.')
    model_name = cat_name.lower().replace('_','')

    if param == 'opus_id':
        # Special case, because opus_id is always a foreign key field, which
        # is just an integer in Django. So we have to look through the foreign
        # key into the destination table (always obs_general) to get the
        # actual string.
        param_model_name = 'opus_id'
    elif model_name == 'obsgeneral':
        param_model_name = param
    else:
        param_model_name = model_name + '__' + param

    if len(value_list) > 1:
        log.error('string_query_object: value_list for param %s contains >1 item %s qtypes %s', param_name, str(value_list), str(qtypes))

    # This can apparently handle multiple string values, but it's not really implemented fully
    # Maybe it should return a list of q_exp?
    for val_no,value in enumerate(value_list):
        qtype = qtypes[val_no] if len(qtypes) > val_no else 'contains'
        if qtype == 'contains':
            q_exp = Q(**{"%s__icontains" % param_model_name: value })
        elif qtype == 'begins':
            q_exp = Q(**{"%s__startswith" % param_model_name: value })
        elif qtype == 'ends':
            q_exp = Q(**{"%s__endswith" % param_model_name: value })
        elif qtype == 'matches':
            q_exp = Q(**{"%s" % param_model_name: value })
        elif qtype == 'excludes':
            q_exp = ~Q(**{"%s__icontains" % param_model_name: value })
        else:
            log.error('string_query_object: Unknown qtype %s for param_name %s', qtype, param_name)

    return q_exp

def _get_range_query_object(selections, param_name, qtypes):
    """
    builds query for numeric ranges where 2 data columns represent min and max values
    oh and also single column ranges

    # just some text for searching this file
    any all only
    any / all / only
    any/all/only

    """
    # grab some info about this param
    param_info = _get_param_info_by_qualified_name(param_name)
    if not param_info:
        return False

    (form_type, form_type_func,
     form_type_format) = parse_form_type(param_info.form_type)
    table_name = param_info.category_name

    # we will define both sides of the query, so define those param names
    param_name_no_num = strip_numeric_suffix(param_name)
    param_name_min = param_name_no_num + '1'
    param_name_max = param_name_no_num + '2'

    # grab min and max values from query selections object
    values_min = selections[param_name_min] if param_name_min in selections else []
    values_max = selections[param_name_max] if param_name_max in selections else []

    # but, for constructing the query,
    # if this is a single column range, the param_names are both the same
    if _is_single_column_range(param_name):
        param_name_min = param_name_max = param_name_no_num

    # to follow related models, we need the lowercase model name, not the param name
    # UNLESS this param is in the obs_General table, then must leave out the model name!
    if table_name == 'obs_general':
        param_model_name_min = param_name_min.split('.')[1]
        param_model_name_max = param_name_max.split('.')[1]
    else:
        param_model_name_min = table_name.lower().replace('_','') + '__' + param_name_min.split('.')[1]
        param_model_name_max = table_name.lower().replace('_','') + '__' + param_name_max.split('.')[1]

    # we need to know how many times to go through this loop
    count = max(len(values_min), len(values_max))  # sometimes you can have queries
                                                   # that define multiple ranges for same widget
                                                   # (not currently implemented in UI)

    if count < len(qtypes):
        log.error('Passed qtypes is shorter in length than longest range values list, defaulting to "any"')
        log.error('.. values_min: %s', str(values_min))
        log.error('.. values_max: %s', str(values_max))
        log.error('.. qtypes: %s', str(qtypes))

    # XXX This is really awful. What happens if there are a different number
    # of qtypes and values?

    # now collect the query expressions
    all_query_expressions = []  # these will be joined by OR
    i=0
    while i < count:

        # define some things
        value_min, value_max = None, None
        try:
            value_min = values_min[i]
        except IndexError:
            pass

        try:
            value_max = values_max[i]
        except IndexError:
            pass

        try:
            qtype = qtypes[i]
        except IndexError:
            qtype = ['any']

        # reverse value_min and value_max if value_min < value_max
        if value_min is not None and value_max is not None:
            (value_min,value_max) = sorted([value_min,value_max])

        # we should end up with 2 query expressions
        q_exp, q_exp1, q_exp2 = None, None, None  # q_exp will hold the concat
                                                  # of q_exp1 and q_exp2

        if qtype == 'all':

            if value_min is not None:
                # param_name_min <= value_min
                q_exp1 = Q(**{"%s__lte" % param_model_name_min: value_min })

            if value_max is not None:
                # param_name_max >= value_max
                q_exp2 = Q(**{"%s__gte" % param_model_name_max: value_max })

        elif qtype == 'only':

            if value_min is not None:
                # param_name_min >= value_min
                q_exp1 = Q(**{"%s__gte" % param_model_name_min: value_min })

            if value_max is not None:
                # param_name_max <= value_max
                q_exp2 = Q(**{"%s__lte" % param_model_name_max: value_max })

        else: # defaults to qtype = any
            if value_max is not None:
                # param_name_min <= value_max
                q_exp1 = Q(**{"%s__lte" % param_model_name_min: value_max })

            if value_min is not None:
                # param_name_max >= value_min
                q_exp2 = Q(**{"%s__gte" % param_model_name_max: value_min })

        # put the query expressions together as "&" queries
        if q_exp1 and q_exp2:
            q_exp = q_exp1 & q_exp2
        elif q_exp1:
            q_exp = q_exp1
        elif q_exp2:
            q_exp = q_exp2

        all_query_expressions.append(q_exp)
        i+=1


    # now we have all query expressions, join them with 'OR'
    return reduce(OR, all_query_expressions)


def _get_longitude_query(selections,param_name):
    # raises 'KeyError' or IndexError if min or max value is blank
    # or ranges are lopsided, all ranges for LONG query must have both sides
    # defined returns string sql

    clauses = []  # we may have a number of clauses to piece together
    params  = []  # we are building a sql string

    cat_name = param_name.split('.')[0]
    name = param_name.split('.')[1]
    name_no_num = strip_numeric_suffix(name)
    param_name_no_num = strip_numeric_suffix(param_name)
    param_name_min = param_name_no_num + '1'
    param_name_max = param_name_no_num + '2'
    col_d_long = cat_name + '.d_' + name_no_num

    values_min = selections[param_name_min]
    values_max = selections[param_name_max]

    if len(values_min) != len(values_max):
        raise KeyError

    count = len(values_max)
    i=0
    while i < count:

        value_min = values_min[i]
        value_max = values_max[i]

        # find the midpoint and dx of the user's range
        if (value_max >= value_min):
            longit = (value_min + value_max)/2.
            d_long = longit - value_min
        else:
            longit = (value_min + value_max + 360.)/2.
            d_long = longit - value_min

        if (longit >= 360): longit = longit - 360.

        if d_long:
            clauses += ["(abs(abs(mod(%s - " + param_name_no_num + " + 180., 360.)) - 180.) <= %s + " + col_d_long + ")"];
            params  += [longit,d_long]

        i+=1

    clause = ' OR '.join(clauses)

    table_name = param_name_no_num.split('.')[0]

    key_field = 'obs_general_id' if cat_name != 'obs_general' else 'obs_general.id'

    query = "select " + key_field + " from " + table_name + " where " + clause

    return query, tuple(params)


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
