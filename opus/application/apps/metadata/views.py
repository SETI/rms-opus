################################################################################
#
# metadata/views.py
#
# The API interface for retrieving metadata (data about searches and the actual
# database):
#
#    Format: api/meta/result_count.(?P<fmt>json|html|csv)
#    Format: api/meta/mults/(?P<slug>[-\w]+).(?P<fmt>json|zip|html|csv)
#    Format: api/meta/range/endpoints/(?P<slug>[-\w]+)
#            .(?P<fmt>json|zip|html|csv)
#    Format: api/fields/(?P<slug>\w+).(?P<fmt>json|zip|html|csv)
#        or: api/fields.(?P<fmt>json|zip|html|csv)
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
from django.http import Http404, HttpResponse
from django.shortcuts import render_to_response

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

def api_get_result_count(request, fmt):
    """Return the result count for a given search.

    You can specify a sort order as well as search arguments because the result
    of the search (including the sort order) is cached for future use.

    This is a PUBLIC API.

    Format: [__]api/meta/result_count.(?P<fmt>json|html|csv)
    Arguments: Normal search arguments

    Can return JSON, HTML, or CSV.

    Returned JSON:
        data = {"data": [{"result_count": 47}]}

    Returned HTML:
        <dl>
		    <dt>result_count</dt><dd>47</dd>
		</dl>

    Returned CSV:
        result count,47
    """
    api_code = enter_api_call('api_get_data', request)

    if not request or request.GET is None:
        ret = Http404('No request')
        exit_api_call(api_code, ret)
        raise ret

    (selections, extras) = url_to_search_params(request.GET)
    if selections is None:
        log.error('api_get_result_count: Could not find selections for '
                  +'request %s', str(request.GET))
        ret = Http404('Parsing of search parameters failed')
        exit_api_call(api_code, ret)
        raise ret

    table = get_user_query_table(selections, extras, api_code=api_code)

    if not table: # pragma: no cover
        log.error('api_get_result_count: Could not find/create query table for '
                  +'request %s', str(request.GET))
        ret = Http404('Parsing of search parameters failed')
        exit_api_call(api_code, ret)
        raise ret

    cache_key = 'resultcount:' + table
    count = cache.get(cache_key)
    if count is None:
        cursor = connection.cursor()
        sql = ('SELECT COUNT(*) FROM ' + connection.ops.quote_name(table))
        cursor.execute(sql)
        try:
            count = cursor.fetchone()[0]
        except: # pragma: no cover
            log.error('api_get_result_count: SQL query failed for request %s',
                      str(request.GET))
            ret = Http404('SQL query failed')
            exit_api_call(api_code, ret)
            raise ret

        cache.set(cache_key, count)

    data = {'result_count': count}

    if (request.is_ajax()): # pragma: no cover
        data['reqno'] = request.GET['reqno']

    if fmt == 'json':
        ret = json_response({'data': [data]})
    elif fmt == 'html':
        ret = render_to_response('metadata/result_count.html', {'data': data})
    elif fmt == 'csv':
        ret = csv_response('result_count', [['result count', count]])
    else:
        log.error('api_get_result_count: Unknown format "%s"', fmt)
        raise Http404(f'Unknown format {fmt}')

    exit_api_call(api_code, ret)
    return ret


def api_get_mult_counts(request, slug, fmt='json'):
    """Return the mults for a given slug along with result counts.

    This is a PUBLIC API.

    Format: [__]api/meta/mults/(?P<slug>[-\w]+).(?P<fmt>json|zip|html|csv)
    Arguments: Normal search arguments

    Can return JSON, ZIP, HTML, or CSV.

    Returned JSON is of the format:
        { 'field': slug,
          'mults': mults }
    mult is a list of entries pairing mult name and result count.
    """
    api_code = enter_api_call('api_get_data', request)

    if not request or request.GET is None:
        ret = Http404('No request')
        exit_api_call(api_code, ret)
        raise ret

    (selections, extras) = url_to_search_params(request.GET)
    if selections is None:
        log.error('api_get_mult_counts: Failed to get selections for slug %s, '
                  +'URL %s', str(slug), request.GET)
        ret = Http404('Parsing of selections failed')
        exit_api_call(api_code, ret)
        raise ret

    param_info = get_param_info_by_slug(slug)
    if not param_info:
        log.error('api_get_mult_counts: Could not find param_info entry for '
                  +'slug %s *** Selections %s *** Extras %s', str(slug),
                  str(selections), str(extras))
        ret = Http404('Unknown slug')
        exit_api_call(api_code, ret)
        raise ret

    table_name = param_info.category_name
    param_qualified_name = param_info.param_qualified_name()

    # If this param is in selections already we want to remove it
    # We want mults for a param as they would be without itself
    if param_qualified_name in selections:
        del selections[param_qualified_name]

    has_selections = False
    if selections:
        has_selections = True

    cache_num, cache_new_flag = set_user_search_number(selections, extras)
    if cache_num is None:
        log.error('api_get_mult_counts: Failed to create user_selections entry'
                  +' for *** Selections %s *** Extras %s',
                  str(selections), str(extras))
        exit_api_call(api_code, Http404)
        raise Http404

    # Note we don't actually care here if the cache table even exists, because
    # if it's in the cache, it must exist, and if it's not in the cache, it
    # will be created if necessary by get_user_query_table below.
    cache_key = ('mults_' + param_qualified_name + '_' + str(cache_num))

    cached_val = cache.get(cache_key)
    if cached_val is not None:
        mults = cached_val
    else:
        mult_name = get_mult_name(param_qualified_name)
        try:
            mult_model = apps.get_model('search',
                                        mult_name.title().replace('_',''))
        except LookupError:
            log.error('api_get_mult_counts: Could not get_model for %s',
                      mult_name.title().replace('_',''))
            exit_api_call(api_code, Http404)
            raise Http404

        try:
            table_model = apps.get_model('search',
                                         table_name.title().replace('_',''))
        except LookupError:
            log.error('api_get_mult_counts: Could not get_model for %s',
                      table_name.title().replace('_',''))
            exit_api_call(api_code, Http404)
            raise Http404

        results = (table_model.objects.values(mult_name)
                   .annotate(Count(mult_name)))

        user_table = get_user_query_table(selections, extras, api_code=api_code)

        if selections and not user_table:
            log.error('api_get_mult_counts: has selections but no user_table '
                      +'found *** Selections %s *** Extras %s',
                      str(selections), str(extras))
            exit_api_call(api_code, Http404)
            raise Http404

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
            except ObjectDoesNotExist:
                log.error('api_get_mult_counts: Could not find mult entry for '
                          +'mult_model %s id %s', str(mult_model), str(mult_id))
                mult_label = str(mult_id)
                mult_disp_order = 0

            mult_result_list.append((mult_disp_order,
                                     (mult_label,
                                      row[mult_name + '__count'])))
        mult_result_list.sort()

        mults = OrderedDict()  # info to return
        for _, mult_info in mult_result_list:
            mults[mult_info[0]] = mult_info[1]

        cache.set(cache_key, mults)

    multdata = {'field': slug,
                'mults': mults }

    if (request.is_ajax()):
        reqno = request.GET.get('reqno', '')
        multdata['reqno'] = reqno

    ret = response_formats(multdata, fmt, template='metadata/mults.html')
    exit_api_call(api_code, ret)
    return ret


def api_get_range_endpoints(request, slug, fmt='json'):
    """Compute and return range widget endpoints (min, max, nulls)

    This is a PUBLIC API.

    Compute and return range widget endpoints (min, max, nulls) for the
    widget defined by [slug] based on current search defined in request.

    Format: [__]api/meta/range/endpoints/(?P<slug>[-\w]+)
            .(?P<fmt>json|zip|html|csv)
    Arguments: Normal search arguments

    Can return JSON, ZIP, HTML, or CSV.

    Returned JSON is of the format:
        { min: 63.592, max: 88.637, nulls: 2365}

    Note that min and max can be strings, not just real numbers. This happens,
    for example, with spacecraft clock counts, and may also happen with
    floating point values when we want to force a particular display format
    (such as full-length numbers instead of exponential notation).
    """
    api_code = enter_api_call('api_get_range_endpoints', request)

    if not request or request.GET is None:
        ret = Http404('No request')
        exit_api_call(api_code, ret)
        raise ret

    param_info = get_param_info_by_slug(slug, from_ui=True)
    if not param_info:
        log.error('get_range_endpoints: Could not find param_info entry for '+
                  'slug %s', str(slug))
        ret = Http404('Unknown slug')
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
    except LookupError:
        log.error('api_get_range_endpoints: Could not get_model for %s',
                  table_name.title().replace('_',''))
        exit_api_call(api_code, Http404)
        raise Http404

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
        ret = Http404('Parsing of selections failed')
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
        if user_table is None:
            log.error('api_get_range_endpoints: Count not retrieve query table'
                      +' for *** Selections %s *** Extras %s',
                      str(selections), str(extras))
            ret = Http404('Parsing of selections failed')
            exit_api_call(api_code, ret)
            raise ret
    else:
        user_table = None

    # Is this result already cached?
    cache_key = 'rangeep:' + qualified_param_name_no_num
    if user_table:
        cache_num, cache_new_flag = set_user_search_number(selections, extras)
        # We're guaranteed the table actually exists here
        if cache_num is None:
            log.error('api_get_range_endpoints: Failed to create cache table '
                      +'for *** Selections %s *** Extras %s',
                      str(selections), str(extras))
            exit_api_call(api_code, Http404)
            raise Http404
        cache_key += ':' + str(cache_num)

    cached_val = cache.get(cache_key)
    if cached_val is not None:
        ret = response_formats(cached_val, fmt, template='metadata/mults.html')
        exit_api_call(api_code, ret)
        return ret

    # We didn't find a cache entry, so calculate the endpoints
    results = table_model.objects

    if selections:
        # There are selections, so tie the query to user_table
        if table_name == 'obs_general':
            where = (connection.ops.quote_name(table_name) + '.id='
                     + connection.ops.quote_name(user_table) + '.id')
        else:
            where = (connection.ops.quote_name(table_name)
                     + '.obs_general_id='
                     + connection.ops.quote_name(user_table) + '.id')
        range_endpoints = (results.extra(where=[where], tables=[user_table]).
                           aggregate(min=Min(param1), max=Max(param2)))

        where += ' AND ' + param1 + ' IS NULL AND ' + param2 + ' IS NULL'
        range_endpoints['nulls'] = results.extra(where=[where],
                                                 tables=[user_table]).count()
    else:
        # There are no selections, so hit the whole table
        range_endpoints = results.all().aggregate(min=Min(param1),
                                                  max=Max(param2))
        where = param1 + ' IS NULL AND ' + param2 + ' IS NULL'
        range_endpoints['nulls'] = results.all().extra(where=[where]).count()

    range_endpoints['min'] = format_metadata_number_or_func(
                                            range_endpoints['min'],
                                            form_type_func,
                                            form_type_format)
    range_endpoints['max'] = format_metadata_number_or_func(
                                            range_endpoints['max'],
                                            form_type_func,
                                            form_type_format)

    cache.set(cache_key, range_endpoints)

    ret = response_formats(range_endpoints, fmt, template='metadata/mults.html')
    exit_api_call(api_code, ret)
    return ret


def api_get_fields(request, fmt='json', slug=None):
    """Return information about fields in the database (slugs).

    This is a PUBLIC API.

    This is helper method for people using the public API.
    It's provides a list of all slugs in the database and helpful info
    about each one like label, dict/more_info links, etc.

    Format: [__]api/fields/(?P<slug>\w+).(?P<fmt>json|zip|html|csv)
        or: [__]api/fields.(?P<fmt>json|zip|html|csv)

    Can return JSON, ZIP, HTML, or CSV.

    Returned JSON is of the format:
            surfacegeometryJUPITERsolarhourangle: {
                more_info: {
                    def: false,
                    more_info: false
                },
                label: "Solar Hour Angle"
            }
    """
    api_code = enter_api_call('api_get_fields', request)

    if not request or request.GET is None:
        ret = Http404('No request')
        exit_api_call(api_code, ret)
        raise ret

    collapse = request.GET.get('collapse', False)
    ret = get_fields_info(fmt, slug, collapse=collapse)

    exit_api_call(api_code, ret)
    return ret


################################################################################
#
# SUPPORT ROUTINES
#
################################################################################

# This routine is public because it's called by the API guide in guide/views.py
def get_fields_info(fmt, slug=None, category=None, collapse=False):
    "Helper routine for api_get_fields."
    cache_key = 'getFields:field:' + str(slug) + ':category:' + str(category)
    return_obj = cache.get(cache_key)
    if return_obj is None:
        if slug:
            fields = ParamInfo.objects.filter(slug=slug)
        elif category:
            fields = ParamInfo.objects.filter(category_name=category)
        else:
            fields = ParamInfo.objects.all()
        fields.order_by('category_name', 'slug')
        # We cheat with the HTML return because we want to collapse all the
        # surface geometry down to a single target version to save screen
        # space. This is a horrible hack, but for right now we just assume
        # there will always be surface geometry data for Saturn.
        return_obj = OrderedDict()
        for f in fields:
            if (collapse and
                f.slug.startswith('SURFACEGEO') and
                not f.slug.startswith('SURFACEGEOsaturn')):
                continue
            if f.slug.startswith('**'):
                # Internal use only
                continue
            entry = OrderedDict()
            table_name = TableNames.objects.get(table_name=f.category_name)
            entry['label'] = f.label_results
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

        cache.set(cache_key, return_obj)

    if fmt == 'raw':
        return return_obj

    return response_formats({'data': return_obj}, fmt=fmt,
                           template='metadata/fields.html')
