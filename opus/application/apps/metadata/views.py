################################################################################
#
# metadata/views.py
#
# The API interface for retrieving metadata (data about searches and the actual
# database):
#
#    Format: api/meta/result_count.(?P<fmt>json|html|csv)
#            __api/meta/result_count.json
#    Format: api/meta/mults/(?P<slug>[-\w]+).(?P<fmt>json|html|csv)
#            __api/meta/mults/(?P<slug>[-\w]+).json
#    Format: api/meta/range/endpoints/(?P<slug>[-\w]+).(?P<fmt>json|html|csv)
#            __api/meta/range/endpoints/(?P<slug>[-\w]+).json
#    Format: api/fields/(?P<slug>\w+).(?P<fmt>json|csv)
#        or: api/fields.(?P<fmt>json|csv)
#
################################################################################

from collections import OrderedDict
import json
import logging

import settings

from django.apps import apps
from django.db import connection
from django.core.cache import cache
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Max, Min, Count
from django.http import Http404, HttpResponse, HttpResponseServerError
from django.shortcuts import render_to_response
from django.views.decorators.cache import never_cache

from paraminfo.models import ParamInfo
from search.models import *
from search.views import (get_param_info_by_slug,
                          get_user_query_table,
                          set_user_search_number,
                          url_to_search_params)
from tools.app_utils import *

import opus_support

log = logging.getLogger(__name__)


################################################################################
#
# API INTERFACES
#
################################################################################

@never_cache
def api_get_result_count(request, fmt, internal=False):
    """Return the result count for a given search.

    You can specify a sort order as well as search arguments because the result
    of the search (including the sort order) is cached for future use.

    This is a PUBLIC API.

    Format: api/meta/result_count.(?P<fmt>json|html|csv)
            __api/meta/result_count.json
    Arguments: Normal search arguments
               reqno=<N> (Required for internal, ignored for external)

    Can return JSON, HTML, or CSV (external) or JSON (internal)

    Returned JSON:
        {"data": [{"result_count": 47}]}
      or
        {"data": [{"result_count": 47, "reqno": 1}]}

    Returned HTML:
        <body>
            <dl>
		        <dt>result_count</dt><dd>47</dd>
            </dl>
        </body>

    Returned CSV:
        result count,47
    """
    api_code = enter_api_call('api_get_result_count', request)

    if not request or request.GET is None:
        ret = Http404(settings.HTTP404_NO_REQUEST)
        exit_api_call(api_code, ret)
        raise ret

    count, _, err = get_result_count_helper(request, api_code)
    if err is not None: # pragma: no cover
        exit_api_call(api_code, err)
        return err

    data = {'result_count': count}
    if internal:
        reqno = get_reqno(request)
        if reqno is None:
            log.error('api_get_result_count: Missing or badly formatted reqno')
            ret = Http404(settings.HTTP404_MISSING_REQNO)
            exit_api_call(api_code, ret)
            raise ret
        data['reqno'] = reqno

    if fmt == 'json':
        ret = json_response({'data': [data]})
    elif fmt == 'html':
        ret = render_to_response('metadata/result_count.html', {'data': data})
    elif fmt == 'csv':
        ret = csv_response('result_count', [['result count', count]])
    else: # pragma: no cover
        log.error('api_get_result_count: Unknown format "%s"', fmt)
        ret = Http404(settings.HTTP404_UNKNOWN_FORMAT)
        exit_api_call(api_code, ret)
        raise ret

    exit_api_call(api_code, ret)
    return ret

def api_get_result_count_internal(request):
    return api_get_result_count(request, 'json', internal=True)


@never_cache
def api_get_mult_counts(request, slug, fmt, internal=False):
    """Return the mults for a given slug along with result counts.

    This is a PUBLIC API.

    Format: api/meta/mults/(?P<slug>[-\w]+).(?P<fmt>json|html|csv)
            __api/meta/mults/(?P<slug>[-\w]+).json
    Arguments: Normal search arguments
               reqno=<N> (Required for internal, ignored for external)

    Can return JSON, HTML, or CSV (external) or JSON (internal)

    Returned JSON:
        {'field': slug, 'mults': mults}
      or:
        {'field': slug, 'mults': mults, 'reqno': reqno}

        mult is a list of entries pairing mult name and result count.

    Returned HTML:
        <body>
        	<dl>
        	    <dt>Atlas</dt><dd>2</dd>
        	    <dt>Daphnis</dt><dd>4</dd>
        	</dl>
        </body>

    Returned CSV:
        name1,name2,name3
        number1,number2,number3
    """
    api_code = enter_api_call('api_get_mult_counts', request)

    if not request or request.GET is None:
        ret = Http404(settings.HTTP404_NO_REQUEST)
        exit_api_call(api_code, ret)
        raise ret

    (selections, extras) = url_to_search_params(request.GET)
    if selections is None:
        log.error('api_get_mult_counts: Failed to get selections for slug %s, '
                  +'URL %s', str(slug), request.GET)
        ret = Http404(settings.HTTP404_SEARCH_PARAMS_INVALID)
        exit_api_call(api_code, ret)
        raise ret

    param_info = get_param_info_by_slug(slug, 'col')
    if not param_info:
        log.error('api_get_mult_counts: Could not find param_info entry for '
                  +'slug %s *** Selections %s *** Extras %s', str(slug),
                  str(selections), str(extras))
        ret = Http404(settings.HTTP404_UNKNOWN_SLUG)
        exit_api_call(api_code, ret)
        raise ret

    table_name = param_info.category_name
    param_qualified_name = param_info.param_qualified_name()

    # If this param is in selections already we want to remove it
    # We want mults for a param as they would be without itself
    if param_qualified_name in selections:
        del selections[param_qualified_name]

    cache_num, cache_new_flag = set_user_search_number(selections, extras)
    if cache_num is None: # pragma: no cover
        log.error('api_get_mult_counts: Failed to create user_selections entry'
                  +' for *** Selections %s *** Extras %s',
                  str(selections), str(extras))
        ret = HttpResponseServerError(settings.HTTP500_DATABASE_ERROR)
        exit_api_call(api_code, ret)
        return ret

    # Note we don't actually care here if the cache table even exists, because
    # if it's in the cache, it must exist, and if it's not in the cache, it
    # will be created if necessary by get_user_query_table below.
    cache_key = (settings.CACHE_SERVER_PREFIX + settings.CACHE_KEY_PREFIX
                 + ':mults_' + param_qualified_name
                 + ':' + str(cache_num))

    cached_val = cache.get(cache_key)
    if cached_val is not None:
        mults = cached_val
    else:
        mult_name = get_mult_name(param_qualified_name)
        try:
            mult_model = apps.get_model('search',
                                        mult_name.title().replace('_',''))
        except LookupError: # pragma: no cover
            log.error('api_get_mult_counts: Could not get_model for %s',
                      mult_name.title().replace('_',''))
            ret = HttpResponseServerError(settings.HTTP500_INTERNAL_ERROR)
            exit_api_call(api_code, ret)
            return ret

        try:
            table_model = apps.get_model('search',
                                         table_name.title().replace('_',''))
        except LookupError: # pragma: no cover
            log.error('api_get_mult_counts: Could not get_model for %s',
                      table_name.title().replace('_',''))
            ret = HttpResponseServerError(settings.HTTP500_INTERNAL_ERROR)
            exit_api_call(api_code, ret)
            return ret

        results = (table_model.objects.values(mult_name)
                   .annotate(Count(mult_name)))

        user_table = get_user_query_table(selections, extras, api_code=api_code)

        if selections and not user_table: # pragma: no cover
            log.error('api_get_mult_counts: has selections but no user_table '
                      +'found *** Selections %s *** Extras %s',
                      str(selections), str(extras))
            ret = HttpResponseServerError(settings.HTTP500_SEARCH_FAILED)
            exit_api_call(api_code, ret)
            return ret

        if selections:
            # selections are constrained so join in the user_table
            if table_name == 'obs_general':
                where = [connection.ops.quote_name(table_name) + '.id='
                         + connection.ops.quote_name(user_table) + '.id']
            else:
                where = [connection.ops.quote_name(table_name)
                         + '.obs_general_id='
                         + connection.ops.quote_name(user_table) + '.id']
            results = results.extra(where=where, tables=[user_table])

        mult_result_list = []
        for row in results:
            mult_id = row[mult_name]
            try:
                mult = mult_model.objects.get(id=mult_id)
                mult_disp_order = mult.disp_order
                mult_label = mult.label
            except ObjectDoesNotExist: # pragma: no cover
                log.error('api_get_mult_counts: Could not find mult entry for '
                          +'mult_model %s id %s', str(mult_model), str(mult_id))
                ret = HttpResponseServerError(settings.HTTP500_INTERNAL_ERROR)
                exit_api_call(api_code, ret)
                return ret

            mult_result_list.append((mult_disp_order,
                                     (mult_label,
                                      row[mult_name + '__count'])))
        mult_result_list.sort()

        mults = OrderedDict()  # info to return
        for _, mult_info in mult_result_list:
            mults[mult_info[0]] = mult_info[1]

        cache.set(cache_key, mults)

    data = {'field': slug,
            'mults': mults}
    if internal:
        reqno = get_reqno(request)
        if reqno is None:
            log.error('api_get_mult_counts: Missing or badly formatted reqno')
            ret = Http404(settings.HTTP404_MISSING_REQNO)
            exit_api_call(api_code, ret)
            raise ret
        data['reqno'] = reqno

    if fmt == 'json':
        ret = json_response(data)
    elif fmt == 'html':
        ret = render_to_response('metadata/mults.html', data)
    elif fmt == 'csv':
        ret = csv_response(slug, [list(mults.values())],
                           column_names=list(mults.keys()))
    else:
        log.error('api_get_mult_counts: Unknown format "%s"', fmt)
        ret = Http404(settings.HTTP404_UNKNOWN_FORMAT)
        exit_api_call(api_code, ret)
        raise ret

    exit_api_call(api_code, ret)
    return ret

def api_get_mult_counts_internal(request, slug):
    return api_get_mult_counts(request, slug, 'json', internal=True)


@never_cache
def api_get_range_endpoints(request, slug, fmt, internal=False):
    """Compute and return range widget endpoints (min, max, nulls)

    This is a PUBLIC API.

    Compute and return range widget endpoints (min, max, nulls) for the
    widget defined by [slug] based on current search defined in request.

    Format: api/meta/range/endpoints/(?P<slug>[-\w]+).(?P<fmt>json|html|csv)
            __api/meta/range/endpoints/(?P<slug>[-\w]+).json
    Arguments: Normal search arguments
               reqno=<N> (Required for internal, ignored for external)

    Can return JSON, HTML, or CSV (external) or JSON (internal)

    Returned JSON:
        {"min": 63.592, "max": 88.637, "nulls": 2365}
      or
        {"min": 63.592, "max": 88.637, "nulls": 2365, "reqno": 123}

        Note that min and max can be strings, not just real numbers. This
        happens, for example, with spacecraft clock counts, and may also happen
        with floating point values when we want to force a particular display
        format (such as full-length numbers instead of exponential notation).

        {"min": "0.0000", "max": "50000.0000", "nulls": 11}

    Returned HTML:
        <body>
            <dl>
                <dt>min</dt><dd>0.0000</dd>
                <dt>max</dt><dd>50000.0000</dd>
                <dt>nulls</dt><dd>11</dd>
            </dl>
        </body>

    Returned CSV:
        min,max,nulls
        0.0000,50000.0000,11
    """
    api_code = enter_api_call('api_get_range_endpoints', request)

    if not request or request.GET is None:
        ret = Http404(settings.HTTP404_NO_REQUEST)
        exit_api_call(api_code, ret)
        raise ret

    param_info = get_param_info_by_slug(slug, 'widget')
    if not param_info:
        log.error('get_range_endpoints: Could not find param_info entry for '+
                  'slug %s', str(slug))
        ret = Http404(settings.HTTP404_UNKNOWN_SLUG)
        exit_api_call(api_code, ret)
        raise ret

    param_name = param_info.name # Just name
    param_qualified_name = param_info.param_qualified_name() # category.name
    (form_type, form_type_func,
     form_type_format) = parse_form_type(param_info.form_type)
    table_name = param_info.category_name
    try:
        table_model = apps.get_model('search',
                                     table_name.title().replace('_',''))
    except LookupError: # pragma: no cover
        log.error('api_get_range_endpoints: Could not get_model for %s',
                  table_name.title().replace('_',''))
        ret = HttpResponseServerError(settings.HTTP500_INTERNAL_ERROR)
        exit_api_call(api_code, ret)
        return ret

    param_no_num = strip_numeric_suffix(param_name)
    param1 = param_no_num + '1'
    param2 = param_no_num + '2'

    if (form_type in settings.RANGE_FORM_TYPES and
        param_info.slug[-1] not in '12'):
        param1 = param2 = param_no_num  # single column range query

    (selections, extras) = url_to_search_params(request.GET)
    if selections is None:
        log.error('api_get_range_endpoints: Could not find selections for '
                  +'request %s', str(request.GET))
        ret = Http404(settings.HTTP404_SEARCH_PARAMS_INVALID)
        exit_api_call(api_code, ret)
        raise ret

    # Remove this param from the user's query if it is constrained.
    # This keeps the green hinting numbers from reacting to changes to its
    # own field.
    qualified_param_name_no_num = strip_numeric_suffix(param_qualified_name)
    for to_remove in [qualified_param_name_no_num,
                      qualified_param_name_no_num + '1',
                      qualified_param_name_no_num + '2']:
        if to_remove in selections:
            del selections[to_remove]
    if selections:
        user_table = get_user_query_table(selections, extras, api_code=api_code)
        if user_table is None: # pragma: no cover
            log.error('api_get_range_endpoints: Count not retrieve query table'
                      +' for *** Selections %s *** Extras %s',
                      str(selections), str(extras))
            ret = HttpResponseServerError(settings.HTTP500_SEARCH_FAILED)
            exit_api_call(api_code, ret)
            return ret
    else:
        user_table = None

    # Is this result already cached?
    cache_key = (settings.CACHE_SERVER_PREFIX + settings.CACHE_KEY_PREFIX
                 + ':rangeep:' + qualified_param_name_no_num)
    if user_table:
        cache_num, cache_new_flag = set_user_search_number(selections, extras)
        if cache_num is None: # pragma: no cover
            log.error('api_get_range_endpoints: Failed to create cache table '
                      +'for *** Selections %s *** Extras %s',
                      str(selections), str(extras))
            exit_api_call(api_code, Http404)
            raise Http404
        # We're guaranteed the table actually exists here, since
        # get_user_query_table has already returned for the same search.
        cache_key += ':' + str(cache_num)

    range_endpoints = cache.get(cache_key)
    if range_endpoints is None:
        # We didn't find a cache entry, so calculate the endpoints
        results = table_model.objects

        if selections:
            # There are selections, so tie the query to user_table
            if table_name == 'obs_general':
                where = (connection.ops.quote_name(table_name)+'.id='
                         +connection.ops.quote_name(user_table)+'.id')
            else:
                where = (connection.ops.quote_name(table_name)
                         +'.'+connection.ops.quote_name('obs_general_id')+'='
                         +connection.ops.quote_name(user_table)+'.id')
            range_endpoints = (results.extra(where=[where],
                               tables=[user_table]).
                               aggregate(min=Min(param1), max=Max(param2)))
            where += ' AND ' + param1 + ' IS NULL AND ' + param2 + ' IS NULL'
            range_endpoints['nulls'] = (results.extra(where=[where],
                                                      tables=[user_table])
                                               .count())
        else:
            # There are no selections, so hit the whole table
            range_endpoints = results.all().aggregate(min=Min(param1),
                                                      max=Max(param2))
            where = param1 + ' IS NULL AND ' + param2 + ' IS NULL'
            range_endpoints['nulls'] = (results.all().extra(where=[where])
                                                     .count())

        range_endpoints['min'] = format_metadata_number_or_func(
                                                range_endpoints['min'],
                                                form_type_func,
                                                form_type_format)
        range_endpoints['max'] = format_metadata_number_or_func(
                                                range_endpoints['max'],
                                                form_type_func,
                                                form_type_format)

        cache.set(cache_key, range_endpoints)

    if internal:
        reqno = get_reqno(request)
        if reqno is None:
            log.error(
                'api_get_range_endpoints: Missing or badly formatted reqno')
            ret = Http404(settings.HTTP404_MISSING_REQNO)
            exit_api_call(api_code, ret)
            raise ret
        range_endpoints['reqno'] = reqno

    if fmt == 'json':
        ret = json_response(range_endpoints)
    elif fmt == 'html':
        ret = render_to_response('metadata/endpoints.html',
                                 {'data': range_endpoints})
    elif fmt == 'csv':
        ret = csv_response(slug, [[range_endpoints['min'],
                                   range_endpoints['max'],
                                   range_endpoints['nulls']]],
                           ['min', 'max', 'nulls'])
    else:
        log.error('api_get_range_endpoints: Unknown format "%s"', fmt)
        ret = Http404(settings.HTTP404_UNKNOWN_FORMAT)
        exit_api_call(api_code, ret)
        raise ret

    exit_api_call(api_code, ret)
    return ret

def api_get_range_endpoints_internal(request, slug):
    return api_get_range_endpoints(request, slug, 'json', internal=True)


@never_cache
def api_get_fields(request, fmt='json', slug=None):
    """Return information about fields in the database (slugs).

    This is a PUBLIC API.

    This is helper method for people using the public API.
    It's provides a list of all slugs in the database and helpful info
    about each one like label, dict/more_info links, etc.

    Format: api/fields/(?P<slug>\w+).(?P<fmt>json|html|csv)
        or: api/fields.(?P<fmt>json|html|csv)
    Arguments: [collapse=1]  Collapse surface geo slugs into one

    Can return JSON or CSV.

    Returned JSON:
        {"time1":
            {"label": "Observation Start Time",
             "search_label": "Observation Time",
             "full_label": "Observation Start Time",
             "full_search_label": "Observation Time [General]",
             "category": "General Constraints",
             "slug": "time1",
             "old_slug": "timesec1"}
        }

    Returned CSV:
        Slug,Category,Search Label,Results Label,Full Search Label,Full Results Label,Old Slug
        time1,General Constraints,Observation Time,Observation Start Time,Observation Time [General],Observation Start Time,timesec1

    If collapse=1, then all surface geometry is collapsed into a single
    <TARGET> version based on the Saturn prototype.
    """
    api_code = enter_api_call('api_get_fields', request)

    if not request or request.GET is None:
        ret = Http404(settings.HTTP404_NO_REQUEST)
        exit_api_call(api_code, ret)
        raise ret

    collapse = request.GET.get('collapse', '0')
    try:
        collapse = int(collapse) != 0
    except ValueError:
        ret = Http404()
        exit_api_call(api_code, ret)
        raise ret

    ret = get_fields_info(fmt, slug, collapse=collapse)

    exit_api_call(api_code, ret)
    return ret


################################################################################
#
# SUPPORT ROUTINES
#
################################################################################

# This routine is public because it's called by _edit_cart_addall
# in cart/views.py
def get_result_count_helper(request, api_code):
    (selections, extras) = url_to_search_params(request.GET)
    if selections is None:
        log.error('get_result_count_helper: Could not find selections for '
                  +'request %s', str(request.GET))
        ret = Http404(settings.HTTP404_SEARCH_PARAMS_INVALID)
        exit_api_call(api_code, ret)
        raise ret

    table = get_user_query_table(selections, extras, api_code=api_code)

    if not table: # pragma: no cover
        log.error('get_result_count_helper: Could not find/create query table '
                  +'for request %s', str(request.GET))
        ret = HttpResponseServerError(settings.HTTP500_SEARCH_FAILED)
        return None, None, ret

    cache_key = (settings.CACHE_SERVER_PREFIX + settings.CACHE_KEY_PREFIX
                 + ':resultcount:' + table)
    count = cache.get(cache_key)
    if count is None:
        cursor = connection.cursor()
        sql = 'SELECT COUNT(*) FROM ' + connection.ops.quote_name(table)
        cursor.execute(sql)
        try:
            count = cursor.fetchone()[0]
        except DatabaseError as e: # pragma: no cover
            log.error('get_result_count_helper: SQL query failed for request '
                      +'%s: SQL "%s" ERR "%s"',
                      str(request.GET), sql, str(e))
            ret = HttpResponseServerError(settings.HTTP500_SQL_FAILED)
            return None, None, ret

        cache.set(cache_key, count)

    return count, table, None


# This routine is public because it's called by the API guide in guide/views.py
def get_fields_info(fmt, slug=None, collapse=False):
    "Helper routine for api_get_fields."
    cache_key = (settings.CACHE_SERVER_PREFIX + settings.CACHE_KEY_PREFIX
                 + ':getFields:field:' + str(slug) + ':' + str(collapse))
    return_obj = cache.get(cache_key)
    if return_obj is None:
        if slug:
            fields = ParamInfo.objects.filter(slug=slug)
        else:
            fields = ParamInfo.objects.all()
        fields.order_by('category_name', 'slug')
        # We cheat with the HTML return because we want to collapse all the
        # surface geometry down to a single target version to save screen
        # space. This is a horrible hack, but for right now we just assume
        # there will always be surface geometry data for Saturn.
        return_obj = {}
        for f in fields:
            if not f.slug:
                continue
            if (collapse and
                f.slug.startswith('SURFACEGEO') and
                not f.slug.startswith('SURFACEGEOsaturn')):
                continue
            if f.slug.startswith('**'):
                # Internal use only
                continue
            entry = OrderedDict()
            table_name = TableNames.objects.get(table_name=f.category_name)
            entry['table_order'] = table_name.disp_order
            entry['disp_order'] = f.disp_order
            entry['label'] = f.label_results
            entry['search_label'] = f.label
            entry['full_label'] = f.body_qualified_label_results()
            entry['full_search_label'] = f.body_qualified_label()
            collapsed_slug = f.slug
            if collapse:
                entry['category'] = table_name.label.replace('Saturn',
                                                             '<TARGET>')
                collapsed_slug = entry['slug'] = f.slug.replace('saturn',
                                                                '<TARGET>')
            else:
                entry['category'] = table_name.label
                entry['slug'] = f.slug
            if f.old_slug and collapse:
                entry['old_slug'] = f.old_slug.replace('saturn', '<TARGET>')
            else:
                entry['old_slug'] = f.old_slug
            return_obj[collapsed_slug] = entry

        return_obj = OrderedDict(sorted(return_obj.items(),
                                        key=lambda x: (x[1]['table_order'],
                                                       x[1]['disp_order'])))
        # Hide internal sort order info from the end user
        for key, val in return_obj.items():
            del val['table_order']
            del val['disp_order']

        cache.set(cache_key, return_obj)

    if fmt == 'raw':
        ret = return_obj
    elif fmt == 'json':
        ret = json_response({'data': return_obj})
    elif fmt == 'csv':
        labels = ['Slug', 'Category',
                  'Search Label', 'Results Label',
                  'Full Search Label', 'Full Results Label',
                  'Old Slug'
                 ]
        rows = [(v['slug'], v['category'],
                 v['search_label'], v['label'],
                 v['full_search_label'],
                 v['full_label'],
                 v['old_slug']) for k,v in return_obj.items()]
        ret = csv_response('fields', rows, labels)
    else:
        log.error('get_fields_info: Unknown format "%s"', fmt)
        ret = Http404(settings.HTTP404_UNKNOWN_FORMAT)
        exit_api_call(api_code, ret)
        raise ret

    return ret
