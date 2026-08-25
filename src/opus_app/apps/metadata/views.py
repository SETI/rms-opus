################################################################################
#
# metadata/views.py
#
# The API interface for retrieving metadata (data about searches and the actual
# database):
#
#    Format: api/meta/result_count.(?P<fmt>json|html|csv)
#            __api/meta/result_count.json
#
#    Format: api/meta/mults/(?P<slug>[-\w]+).(?P<fmt>json|html|csv)
#            __api/meta/mults/(?P<slug>[-\w]+).json
#
#    Format: api/meta/range/endpoints/(?P<slug>[-\w]+).(?P<fmt>json|html|csv)
#            __api/meta/range/endpoints/(?P<slug>[-\w]+).json
#
#    Format: api/fields/(?P<slug>\w+).(?P<fmt>json|csv)
#        or: api/fields.(?P<fmt>json|csv)
#
################################################################################

import logging

from django.apps import apps
from django.conf import settings
from django.core.cache import cache
from django.core.exceptions import ObjectDoesNotExist
from django.db import DatabaseError, connection
from django.db.models import Max, Min
from django.http import Http404, HttpResponseServerError
from django.shortcuts import render
from django.views.decorators.cache import never_cache

from opus_app.apps.cart.models import Cart
from opus_app.apps.paraminfo.models import ParamInfo
from opus_app.apps.search.models import TableNames
from opus_app.apps.search.views import (
    get_param_info_by_slug,
    get_user_query_table,
    search_cache_join_condition,
    set_user_search_number,
    url_to_search_params,
)
from opus_app.apps.tools import sql_builder
from opus_app.apps.tools.app_utils import (
    HTTP400_BAD_COLLAPSE,
    HTTP400_BAD_OR_MISSING_REQNO,
    HTTP400_SEARCH_PARAMS_INVALID,
    HTTP400_UNKNOWN_SLUG,
    HTTP400_UNKNOWN_UNITS,
    HTTP404_NO_REQUEST,
    HTTP404_UNKNOWN_FORMAT,
    HTTP500_DATABASE_ERROR,
    HTTP500_INTERNAL_ERROR,
    HTTP500_SEARCH_CACHE_FAILED,
    Http400Error,
    api_view,
    csv_response,
    get_mult_name,
    get_reqno,
    json_response,
    strip_numeric_suffix,
)
from opus_support import (
    format_unit_value,
    get_default_unit,
    get_valid_units,
    is_valid_unit,
    parse_form_type,
)

log = logging.getLogger(__name__)


################################################################################
#
# API INTERFACES
#
################################################################################

@never_cache
@api_view
def api_get_result_count(request, fmt, internal=False, *, api_code):
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
    if not request or request.GET is None or request.META is None:
        raise Http404(HTTP404_NO_REQUEST(f'/api/meta/result_count.{fmt}'))

    count, _, err = get_result_count_helper(request, api_code)
    if err is not None: # pragma: no cover - database error
        return err

    data = {'result_count': count}
    if internal:
        reqno = get_reqno(request)
        if reqno is None:
            log.error('api_get_result_count: Missing or badly formatted reqno')
            raise Http400Error(HTTP400_BAD_OR_MISSING_REQNO(
                                        '/__api/meta/result_count.json'))
        data['reqno'] = reqno

    if fmt == 'json':
        ret = json_response({'data': [data]})
    elif fmt == 'html':
        ret = render(request,
                     'metadata/result_count.html',
                     {'data': data})
    elif fmt == 'csv':
        ret = csv_response('result_count', [['result count', count]])
    else: # pragma: no cover - error catchall
        log.error('api_get_result_count: Unknown format "%s"', fmt)
        raise Http404(HTTP404_UNKNOWN_FORMAT(fmt, request))

    return ret

def api_get_result_count_internal(request):
    return api_get_result_count(request, 'json', internal=True)


@never_cache
@api_view
def api_get_mult_counts(request, slug, fmt, internal=False, *,
                        api_code):
    r"""Return the mults for a given slug along with result counts.

    This is a PUBLIC API.

    Format: api/meta/mults/(?P<slug>[-\w]+).(?P<fmt>json|html|csv)
            __api/meta/mults/(?P<slug>[-\w]+).json
    Arguments: Normal search arguments
               reqno=<N> (Required for internal, ignored for external)

    Can return JSON, HTML, or CSV (external) or JSON (internal)

    Returned JSON:
        {'field_id': slug, 'mults': mults}
      or:
        {'field_id': slug, 'mults': mults, 'reqno': reqno}

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
    if not request or request.GET is None or request.META is None:
        raise Http404(HTTP404_NO_REQUEST(f'/api/meta/mults/{slug}.{fmt}'))

    if fmt not in ('json', 'html', 'csv'):
        log.error('api_get_mult_counts: Unknown format "%s"', fmt)
        raise Http404(HTTP404_UNKNOWN_FORMAT(fmt, request))

    (selections, extras) = url_to_search_params(request.GET)
    if selections is None:
        log.error('api_get_mult_counts: Failed to get selections for slug %s, '
                  +'URL %s', str(slug), request.GET)
        raise Http400Error(HTTP400_SEARCH_PARAMS_INVALID(request))

    param_info = get_param_info_by_slug(slug, 'col', allow_units_override=False)
    if not param_info:
        log.error('api_get_mult_counts: Could not find param_info entry for '
                  +'slug %s *** Selections %s *** Extras %s', str(slug),
                  str(selections), str(extras))
        raise Http400Error(HTTP400_UNKNOWN_SLUG(slug, request))

    table_name = param_info.category_name
    param_qualified_name = param_info.param_qualified_name()

    # If this param is in selections already we want to remove it
    # We want mults for a param as they would be without itself
    if param_qualified_name in selections:
        del selections[param_qualified_name]

    cache_num, _cache_new_flag = set_user_search_number(selections, extras)
    if cache_num is None: # pragma: no cover - database error
        log.error('api_get_mult_counts: Failed to create user_selections entry'
                  +' for *** Selections %s *** Extras %s',
                  str(selections), str(extras))
        return HttpResponseServerError(HTTP500_DATABASE_ERROR(request))

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
        except LookupError: # pragma: no cover - configuration error
            log.exception('api_get_mult_counts: Could not get_model for %s',
                          mult_name.title().replace('_',''))
            return HttpResponseServerError(HTTP500_INTERNAL_ERROR(request))

        try:
            table_model = apps.get_model('search',
                                         table_name.title().replace('_',''))
        except LookupError: # pragma: no cover - configuration error
            log.exception('api_get_mult_counts: Could not get_model for %s',
                          table_name.title().replace('_',''))
            return HttpResponseServerError(HTTP500_INTERNAL_ERROR(request))

        cursor = connection.cursor()

        # The database column, not the model field name: the two differ for a
        # field declared with db_column.
        param_column = sql_builder.column(
            table_model._meta.get_field(param_info.name).column, table_name)

        select = sql_builder.Select()
        if param_info.form_type == 'MULTIGROUP':
            # This extracts the list of mult ids from the JSON list and creates a new
            # column with them that is then summarized by count.
            counted_column = sql_builder.column('_mult_val_', table_name)
            select.add_column(counted_column)
            select.add_column(sql_builder.count_star(),
                              alias=param_info.name+'__count')
            select.add_from(table_name).add_join(
                'INNER',
                sql_builder.JSONTable(source_column=param_column,
                                      value_column='_mult_val_',
                                      alias=table_name))
        else:
            counted_column = param_column
            select.add_column(counted_column)
            select.add_column(sql_builder.count_star(),
                              alias=param_info.name+'__count')
            select.add_from(table_name)

        user_table = get_user_query_table(selections, extras, api_code=api_code)

        if selections and not user_table: # pragma: no cover - database corruption
            log.error('api_get_mult_counts: has selections but no user_table '
                      +'found *** Selections %s *** Extras %s',
                      str(selections), str(extras))
            return HttpResponseServerError(HTTP500_SEARCH_CACHE_FAILED(request))

        if selections:
            # selections are constrained so join in the user_table
            select.add_from(user_table)
            select.add_where(search_cache_join_condition(table_name, user_table))

        select.add_group_by(counted_column)

        sql, values = select.build()
        log.debug('MULT COUNTS SQL: %s *** PARAMS %s', sql, str(values))

        cursor.execute(sql, values)
        results = cursor.fetchall()

        mult_result_list = []
        for row in results:
            mult_id = row[0]
            try:
                mult = mult_model.objects.get(id=mult_id)
                mult_disp_order = mult.disp_order
                mult_label = mult.label
            except ObjectDoesNotExist: # pragma: no cover - import error
                log.exception('api_get_mult_counts: Could not find mult entry '
                              +'for mult_model %s id %s', str(mult_model),
                              str(mult_id))
                return HttpResponseServerError(HTTP500_INTERNAL_ERROR(request))

            mult_result_list.append((mult_disp_order,
                                     (mult_label, row[1])))
        mult_result_list.sort()

        mults = {}  # info to return
        for _, mult_info in mult_result_list:
            mults[mult_info[0]] = mult_info[1]

        cache.set(cache_key, mults)

    data = {'field_id': slug,
            'mults': mults}
    if internal:
        reqno = get_reqno(request)
        if reqno is None:
            log.error('api_get_mult_counts: Missing or badly formatted reqno')
            raise Http400Error(HTTP400_BAD_OR_MISSING_REQNO(request))
        data['reqno'] = reqno

    if fmt == 'json':
        ret = json_response(data)
    elif fmt == 'html':
        ret = render(request, 'metadata/mults.html', data)
    else:
        assert fmt == 'csv'
        ret = csv_response(slug, [list(mults.values())],
                           column_names=list(mults.keys()))

    return ret

def api_get_mult_counts_internal(request, slug):
    return api_get_mult_counts(request, slug, 'json', internal=True)


@never_cache
@api_view
def api_get_range_endpoints(request, slug, fmt, internal=False, *,
                            api_code):
    r"""Compute and return range widget endpoints (min, max, nulls)

    This is a PUBLIC API.

    Compute and return range widget endpoints (min, max, nulls) for the
    widget defined by [slug] based on current search defined in request.

    Format: api/meta/range/endpoints/(?P<slug>[-\w]+).(?P<fmt>json|html|csv)
            __api/meta/range/endpoints/(?P<slug>[-\w]+).json
    Arguments: Normal search arguments
               units=<unit> (Optional, gives units to return in)
               reqno=<N>    (Required for internal, ignored for external)

    Can return JSON, HTML, or CSV (external) or JSON (internal)

    Returned JSON:
        {"min": 63.592, "max": 88.637, "nulls": 2365, units: "km"}
      or
        {"min": 63.592, "max": 88.637, "nulls": 2365, units: "km", "reqno": 123}

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
                <dt>units</dt><dd>km</dd>
            </dl>
        </body>

    Returned CSV:
        min,max,nulls,units
        0.0000,50000.0000,11,km
    """
    if not request or request.GET is None or request.META is None:
        raise Http404(HTTP404_NO_REQUEST(
                                    f'/api/meta/range/endpoints/{slug}.{fmt}'))

    if fmt not in ('json', 'html', 'csv'):
        log.error('api_get_range_endpoints: Unknown format "%s"', fmt)
        raise Http404(HTTP404_UNKNOWN_FORMAT(fmt, request))

    param_info = get_param_info_by_slug(slug, 'widget')
    if not param_info:
        log.error('api_get_range_endpoints: Could not find param_info entry '
                  +'for slug %r', slug)
        raise Http400Error(HTTP400_UNKNOWN_SLUG(slug, request))

    (form_type, form_type_format,
     form_type_unit_id) = parse_form_type(param_info.form_type)
    units = request.GET.get('units', get_default_unit(form_type_unit_id))
    if form_type_unit_id and not is_valid_unit(form_type_unit_id, units):
        log.error('api_get_range_endpoints: Bad units %r for '
                  +'slug %r', units, slug)
        raise Http400Error(HTTP400_UNKNOWN_UNITS(units, slug, request))

    param_name = param_info.name # Just name
    param_qualified_name = param_info.param_qualified_name() # category.name
    (form_type, form_type_format,
     form_type_unit_id) = parse_form_type(param_info.form_type)
    table_name = param_info.category_name
    try:
        table_model = apps.get_model('search',
                                     table_name.title().replace('_',''))
    except LookupError: # pragma: no cover - configuration error
        log.exception('api_get_range_endpoints: Could not get_model for %s',
                      table_name.title().replace('_',''))
        return HttpResponseServerError(HTTP500_INTERNAL_ERROR(request))

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
        raise Http400Error(HTTP400_SEARCH_PARAMS_INVALID(request))

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
        if user_table is None: # pragma: no cover - database corruption
            log.error('api_get_range_endpoints: Count not retrieve query table'
                      +' for *** Selections %s *** Extras %s',
                      str(selections), str(extras))
            return HttpResponseServerError(HTTP500_SEARCH_CACHE_FAILED(request))
    else:
        user_table = None

    # Is this result already cached?
    cache_key = (settings.CACHE_SERVER_PREFIX + settings.CACHE_KEY_PREFIX
                 + ':rangeep:' + qualified_param_name_no_num
                 + ':units:' + str(units))
    if user_table:
        cache_num, _cache_new_flag = set_user_search_number(selections, extras)
        if cache_num is None: # pragma: no cover - database error
            log.error('api_get_range_endpoints: Failed to create cache table '
                      +'for *** Selections %s *** Extras %s',
                      str(selections), str(extras))
            raise Http404
        # We're guaranteed the table actually exists here, since
        # get_user_query_table has already returned for the same search.
        cache_key += ':' + str(cache_num)

    range_endpoints = cache.get(cache_key)
    if range_endpoints is None:
        # We didn't find a cache entry, so calculate the endpoints
        if selections:
            # There are selections, so tie the query to user_table. The cache
            # table has no model, so this cross-join and its condition cannot be
            # expressed through the ORM and are built as raw SQL instead.
            cache_join = search_cache_join_condition(table_name, user_table)
            # The database column, not the model field name: the two differ for a
            # field declared with db_column, and the ORM path below names fields.
            min_column = sql_builder.column(
                table_model._meta.get_field(param1).column, table_name)
            max_column = sql_builder.column(
                table_model._meta.get_field(param2).column, table_name)

            endpoints_select = sql_builder.Select()
            endpoints_select.add_column(sql_builder.min_of(min_column))
            endpoints_select.add_column(sql_builder.max_of(max_column))
            endpoints_select.add_from(table_name)
            endpoints_select.add_from(user_table)
            endpoints_select.add_where(cache_join)

            nulls_select = sql_builder.Select()
            nulls_select.add_column(sql_builder.count_star())
            nulls_select.add_from(table_name)
            nulls_select.add_from(user_table)
            nulls_select.add_where(cache_join)
            nulls_select.add_where(sql_builder.is_null(min_column))
            nulls_select.add_where(sql_builder.is_null(max_column))

            cursor = connection.cursor()
            sql, params = endpoints_select.build()
            log.debug('RANGE ENDPOINTS SQL: %s *** PARAMS %s', sql, str(params))
            cursor.execute(sql, params)
            (endpoint_min, endpoint_max) = cursor.fetchone()
            range_endpoints = {'min': endpoint_min, 'max': endpoint_max}

            sql, params = nulls_select.build()
            log.debug('RANGE ENDPOINTS NULLS SQL: %s *** PARAMS %s', sql, str(params))
            cursor.execute(sql, params)
            range_endpoints['nulls'] = cursor.fetchone()[0]
        else:
            # There are no selections, so hit the whole table
            results = table_model.objects
            range_endpoints = results.all().aggregate(min=Min(param1),
                                                      max=Max(param2))
            # For a single-column range param1 and param2 are the same column, so
            # this is one condition rather than two.
            null_filter = {f'{param1}__isnull': True, f'{param2}__isnull': True}
            range_endpoints['nulls'] = results.all().filter(**null_filter).count()

        # The returned range endpoints are converted to the destination
        # unit
        range_endpoints['min'] = format_unit_value(
                                                range_endpoints['min'],
                                                form_type_format,
                                                form_type_unit_id,
                                                units)
        range_endpoints['max'] = format_unit_value(
                                                range_endpoints['max'],
                                                form_type_format,
                                                form_type_unit_id,
                                                units)

        cache.set(cache_key, range_endpoints)

    if internal:
        reqno = get_reqno(request)
        if reqno is None:
            log.error(
                'api_get_range_endpoints: Missing or badly formatted reqno')
            raise Http400Error(HTTP400_BAD_OR_MISSING_REQNO(request))
        range_endpoints['reqno'] = reqno

    range_endpoints['units'] = units

    if fmt == 'json':
        ret = json_response(range_endpoints)
    elif fmt == 'html':
        ret = render(request,
                     'metadata/endpoints.html',
                     {'data': range_endpoints})
    else:
        assert fmt == 'csv'
        ret = csv_response(slug, [[range_endpoints['min'],
                                   range_endpoints['max'],
                                   range_endpoints['nulls'],
                                   range_endpoints['units']]],
                           ['min', 'max', 'nulls', 'units'])

    return ret

def api_get_range_endpoints_internal(request, slug):
    return api_get_range_endpoints(request, slug, 'json', internal=True)


@never_cache
@api_view
def api_get_fields(request, fmt, slug=None):
    r"""Return information about fields in the database (slugs).

    This is a PUBLIC API.

    This is helper method for people using the public API.
    It's provides a list of all slugs in the database and helpful info
    about each one like label, dict/more_info links, etc.

    Format: api/fields/(?P<slug>\w+).(?P<fmt>json|csv)
        or: api/fields.(?P<fmt>json|csv)
    Arguments: [collapse=1]  Collapse surface geo slugs into one

    Can return JSON or CSV.

    Returned JSON:
      {
        "General Constraints": {
          "time1": {
            "field_id": "time1",
            "category": "General Constraints",
            "type": "range_time",
            "label": "Observation Start Time",
            "search_label": "Observation Time",
            "full_label": "Observation Start Time",
            "full_search_label": "Observation Time [General]",
            "default_units": null,
            "available_units": null,
            "old_slug": "timesec1",
            "slug": "time1",
            "linked": false
          }
        }
      }

    Returned CSV:
        Field ID,Category,Type,Search Label,Results Label,Full Search Label,Full Results Label,Default Units,Available Units,Old Field ID,Linked
        time1,General Constraints,range_time,Observation Time,Observation Start Time,Observation Time [General],Observation Start Time,,,timesec1,0

    If collapse=1, then all surface geometry is collapsed into a single
    <TARGET> version based on the Saturn prototype.
    """
    if not request or request.GET is None or request.META is None:
        raise Http404(HTTP404_NO_REQUEST(f'/api/fields/{slug}.{fmt}'))

    collapse = request.GET.get('collapse', '0')
    try:
        collapse = int(collapse) != 0
    except ValueError as err:
        # %r for the same reason api_edit_cart uses it on recyclebin: this is
        # still the raw request string when int() raised.
        log.error('api_get_fields: Bad value for collapse %r', collapse)
        raise Http400Error(HTTP400_BAD_COLLAPSE(collapse, request)) from err

    return get_fields_info(fmt, request, slug=slug, collapse=collapse)


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
        raise Http400Error(HTTP400_SEARCH_PARAMS_INVALID(request))

    table = get_user_query_table(selections, extras, api_code=api_code)

    if not table: # pragma: no cover - internal or database failure
        log.error('get_result_count_helper: Could not find/create query table '
                  +'for request %s', str(request.GET))
        ret = HttpResponseServerError(HTTP500_SEARCH_CACHE_FAILED(request))
        return None, None, ret

    cache_key = (settings.CACHE_SERVER_PREFIX + settings.CACHE_KEY_PREFIX
                 + ':resultcount:' + table)
    count = cache.get(cache_key)
    if count is None:
        cursor = connection.cursor()
        sql = sql_builder.count_rows(table)
        try:
            cursor.execute(sql)
            count = cursor.fetchone()[0]
        except DatabaseError: # pragma: no cover - database error
            log.exception('get_result_count_helper: SQL query failed for '
                          +'request %s: SQL "%s"', str(request.GET), sql)
            ret = HttpResponseServerError(HTTP500_DATABASE_ERROR(request))
            return None, None, ret

        cache.set(cache_key, count)

    return count, table, None

def get_cart_count(session_id):
    "Return the number of items in the current cart."
    count = (Cart.objects
             .filter(session_id__exact=session_id)
             .filter(recycled=0)
             .count())
    recycled_count = (Cart.objects
             .filter(session_id__exact=session_id)
             .filter(recycled=1)
             .count())
    return count, recycled_count

# This routine is public because it's called by the API guide in guide/views.py
def get_fields_info(fmt, request, slug=None, collapse=False):
    "Helper routine for api_get_fields."
    if slug:
        fields = ParamInfo.objects.filter(slug=slug)
    else:
        fields = ParamInfo.objects.all()
    fields.order_by('category_name', 'slug')
    return_obj = {}
    for f in fields:
        if not f.slug:
            # Include referred slug
            if f.referred_slug is not None:
                referred_slug = f.referred_slug
                category = f.category_name
                disp_order = f.disp_order
                # A referred slug will never contain a unit specifier
                f = get_param_info_by_slug(referred_slug, 'col',
                                           allow_units_override=False)
                f.label = f.body_qualified_label()
                f.label_results = f.body_qualified_label_results(True)
                f.referred_slug = referred_slug
                f.category_name = category
                f.disp_order = disp_order
            else: # pragma: no cover - protection against future bugs
                # There shouldn't be a case where BOTH the slug and
                # referred_slug are None, but just to be careful...
                continue
        # We cheat with the HTML return because we want to collapse all the
        # surface geometry down to a single target version to save screen
        # space. This is a horrible hack, but for right now we just assume
        # there will always be surface geometry data for Saturn.
        if (collapse and
            f.slug.startswith('SURFACEGEO') and
            not f.slug.startswith('SURFACEGEOsaturn')):
            continue
        if f.slug.startswith('**'):
            # Internal use only
            continue

        table_name = TableNames.objects.get(table_name=f.category_name)
        cat = table_name.label
        if collapse and cat.find('Surface Geometry Constraints') != -1:
            cat = cat.replace('Saturn', '<TARGET>')

        return_obj[cat] = return_obj.get(cat, {})

        entry = {}
        return_obj[cat]['table_order'] = table_name.disp_order
        entry['disp_order'] = f.disp_order
        collapsed_slug = f.slug
        if collapse:
            collapsed_slug = entry['field_id'] = f.slug.replace('saturn',
                                                                '<TARGET>')
            entry['category'] = table_name.label.replace('Saturn', '<TARGET>')
        else:
            entry['field_id'] = f.slug
            entry['category'] = table_name.label
        f_type = None
        (form_type, form_type_format,
         form_type_unit_id) = parse_form_type(f.form_type)
        if form_type in settings.RANGE_FORM_TYPES:
            if form_type == 'LONG':
                f_type = 'range_longitude'
            elif form_type_format is not None:
                if form_type_format[-1] == 'd':
                    f_type = 'range_integer'
                elif form_type_format[-1] == 'f':
                    f_type = 'range_float'
                else: # pragma: no cover - error catchall
                    log.warning('Unparseable form type '+str(f.form_type))
            elif form_type_unit_id == 'datetime':
                f_type = 'range_time'
            elif form_type_unit_id is not None:
                f_type = 'range_special'
            else: # pragma: no cover - error catchall
                f_type = 'Internal Error'
        elif form_type in settings.MULT_FORM_TYPES:
            f_type = 'multiple'
        elif form_type == 'STRING':
            f_type = 'string'
        else: # pragma: no cover - error catchall
            log.warning('Unparseable form type '+str(f.form_type))
        entry['type'] = f_type
        entry['label'] = f.label_results
        entry['search_label'] = f.label
        entry['full_label'] = f.body_qualified_label_results()
        entry['full_search_label'] = f.body_qualified_label()
        (form_type, form_type_format,
         form_type_unit_id) = parse_form_type(f.form_type)
        entry['default_units'] = get_default_unit(form_type_unit_id)
        entry['available_units'] = get_valid_units(form_type_unit_id)
        if f.old_slug and collapse: # Backwards compatibility
            entry['old_slug'] = f.old_slug.replace('saturn', '<TARGET>')
        else:
            entry['old_slug'] = f.old_slug
        entry['slug'] = entry['field_id'] # Backwards compatibility
        entry['linked'] = bool(f.referred_slug)
        return_obj[cat][collapsed_slug] = entry

    # Organize return_obj before returning
    # Sort categories by table_order
    return_obj = dict(sorted(return_obj.items(), key=lambda x: x[1]['table_order']))
    for cat, cat_data in return_obj.items():
        del cat_data['table_order']
        # Sort slugs of each category by disp_order
        cat_data = dict(sorted(cat_data.items(), key=lambda x: x[1]['disp_order']))
        return_obj[cat] = cat_data
        for _key, val in cat_data.items():
            del val['disp_order']

    if fmt == 'raw':
        ret = return_obj
    elif fmt == 'json':
        ret = json_response({'data': return_obj})
    elif fmt == 'csv':
        labels = ['Field ID', 'Category', 'Type',
                  'Search Label', 'Results Label',
                  'Full Search Label', 'Full Results Label',
                  'Default Units', 'Available Units', 'Old Field ID',
                  'Linked'
                  ]

        rows = []
        for _cat, cat_data in return_obj.items():
            for _k, v in cat_data.items():
                # In csv, we will store the linked field value as 0 or 1.
                linked = 1 if v['linked'] else 0
                row_data = [(v['field_id'], v['category'], v['type'],
                             v['search_label'], v['label'],
                             v['full_search_label'],
                             v['full_label'],
                             v['default_units'],
                             v['available_units'],
                             v['old_slug'], linked
                             )]
                rows += row_data
        ret = csv_response('fields', rows, labels)
    else: # pragma: no cover - error catchall
        log.error('get_fields_info: Unknown format "%s"', fmt)
        raise Http404(HTTP404_UNKNOWN_FORMAT(fmt, request))

    return ret
