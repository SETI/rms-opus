###############################################
#
#   metadata.views
#
################################################
import json
from django.core.cache import cache
from django.http import Http404
from django.http import HttpResponse
from django.db.models import Avg, Max, Min, Count
from django.apps import apps
from django.db import connection
from paraminfo.models import ParamInfo
import search.views
from metrics.views import update_metrics

from search.models import *

# from paraminfo.models import *
from tools.app_utils import responseFormats, strip_numeric_suffix
import settings

import opus_support

import logging
log = logging.getLogger(__name__)

def getMultName(param_name):
    """ pass param_name, returns mult widget foreign key table name
        the tables themselves are in the search/models.py """
    return "mult_" + '_'.join(param_name.split('.'))

def getUserSearchTableName(no):
    """ pass cache_no, returns user search table name"""
    return 'cache_' + str(no);

def getResultCount(request,fmt='json'):
    """ pass request and response format,
        returns result count for a search """
    update_metrics(request)

    if request.GET is None:
        return HttpResponse(json.dumps({'result_count':'0'}),  content_type='application/json')

    try:
        (selections,extras) = search.views.urlToSearchParams(request.GET)
    except TypeError:
        log.error("Could not find selections for request %s", str(request.GET))
        raise Http404

    reqno = request.GET.get('reqno','')

    if selections is False:
        count = 'not found'
        return HttpResponse(json.dumps({'result_count':count}),  content_type='application/json')


    table = search.views.getUserQueryTable(selections,extras)

    if table is False:
        count = 0;
    else:
        cache_key    = "resultcount:" + table
        if (cache.get(cache_key)):
            count = cache.get(cache_key)
        else:
            cursor = connection.cursor()
            cursor.execute("select count(*) from " + connection.ops.quote_name(table))
            try:
                count = cursor.fetchone()
                count = count[0]
            except:
                count = 0

            # set this result in cache
            cache.set(cache_key,count)


    data = {'result_count':count}

    if (request.is_ajax()):
        data['reqno'] = request.GET['reqno']

    return responseFormats({'data':[data]},fmt,template='result_count.html')


def getValidMults(request,slug,fmt='json'):
    """
    fetch mult widget hinting data for widget defined by slug
    based on current search defined in request

    this is the widget hinting numbers that appear next to each
    possible checkbox value in a mult/group widget (green numbers)

    pass request, slug, and response format
    returns valid mults for a given field (slug) like so:

        { 'field':slug,'mults':mults }

    """
    update_metrics(request)
    try:
        (selections,extras) = search.views.urlToSearchParams(request.GET)
    except Exception,e:
        log.error('Failed to get selections for slug %s, URL %s', str(slug), request.GET)
        log.error('.. %s', str(e))
        selections = {}

    param_info = search.views.get_param_info_by_slug(slug)
    if not param_info:
        log.error("getValidMults: Could not find param_info entry for slug %s",
                  str(slug))
        log.error(".. Selections: %s", str(selections))
        log.error(".. Extras: %s", str(extras))
        raise Http404

    table_name = param_info.category_name
    param_name = param_info.param_name()

    # if this param is in selections we want to remove it,
    # want mults for a param as they would be without itself
    if param_name in selections:
        del selections[param_name]

    has_selections = False
    if bool(selections):
        has_selections = True

    cache_key  = "mults" + param_name + str(search.views.setUserSearchNo(selections))

    if (cache.get(cache_key) is not None):

        mults = cache.get(cache_key)

    else:

        mult_name  = getMultName(param_name)  # the name of the field to query

        try:
            mult_model = apps.get_model('search',mult_name.title().replace('_',''))
        except LookupError:
            log.error('Could not get_model for %s', mult_name.title().replace('_',''))
            raise Http404

        try:
            table_model = apps.get_model('search', table_name.title().replace('_',''))
        except LookupError:
            log.error('Could not get_model for %s', table_name.title().replace('_',''))
            raise Http404

        mults = {}  # info to return
        results    = table_model.objects.values(mult_name).annotate(Count(mult_name))  # this is a count(*), group_by query!

        user_table = search.views.getUserQueryTable(selections,extras)

        if has_selections and not user_table:
            # selections are constrained so join in the user_table
            log.error('getValidMults has_selections = true but no user_table found:')
            log.error(".. Selections: %s", str(selections))
            log.error(".. Extras: %s", str(extras))
            raise Http404

        if table_name == 'obs_general':
            where   = table_name + ".id = " + user_table + ".id"
        else:
            where   = table_name + ".obs_general_id = " + user_table + ".id"
        results = results.extra(where=[where],tables=[user_table])

        for row in results:
            mult_id = row[mult_name]

            try:
                try:
                    mult = mult_model.objects.get(id=mult_id).label
                except:
                    log.error('Could not find mult label for id %s mult_model %s', str(mult_id), str(mult_model))
                    log.error('.. URL: %s', request.GET)
                    log.error('.. Slug: %s', slug)
                    log.error('.. Selections: %s', str(selections))
                    log.error('.. Extras: %s', str(extras))
                    log.error('.. Query: %s', str(where))
                    log.error('.. Row: %s', str(row))
                    mult = mult_id  # fall back to id if there is no label

                mults[mult] = row[mult_name + '__count']
            except: pass # a none object may be found in the data but if it doesn't have a table row we don't handle it

        cache.set(cache_key,mults)

    multdata = { 'field':slug,'mults':mults }

    if (request.is_ajax()):
        reqno = request.GET.get('reqno','')
        multdata['reqno'] = reqno

    return responseFormats(multdata,fmt,template='mults.html')


def get_range_endpoints(request, slug, fmt='json'):
    """Compute and return range widget endpoints (min, max, nulls) for the
    widget defined by [slug] based on current search defined in request.

    This is the valid range endpoints that appear in range widgets
    (green numbers).

    Returns a dictionary like:

        { min: 63.592, max: 88.637, nulls: 2365}

    Note that min and max can be strings, not just real numbers. This happens,
    for example, with spacecraft clock counts, and may also happen with
    floating point values when we want to force a particular display format
    (such as full-length numbers instead of exponential notation).
    """
    update_metrics(request)

    param_info = search.views.get_param_info_by_slug(slug)
    if not param_info:
        log.error('get_range_endpoints: Could not find param_info entry for '+
                  'slug %s', str(slug))
        raise Http404

    param_name = param_info.name # Just name
    full_param_name = param_info.param_name() # category.name
    form_type = param_info.form_type
    form_type_ext = None
    if form_type.find(':') != -1:
        form_type, form_type_ext = form_type.split(':')
    table_name = param_info.category_name
    table_model = apps.get_model('search', table_name.title().replace('_',''))

    param_no_num = strip_numeric_suffix(param_name)
    param1 = param_no_num + '1'
    param2 = param_no_num + '2'

    if form_type == 'RANGE' and param_info.slug[-1] not in '12':
        param1 = param2 = param_no_num  # single column range query

    # XXX What can cause this TypeError? The enclosed functions should be more
    # careful about what they do.
    try:
        (selections, extras) = search.views.urlToSearchParams(request.GET)
    except TypeError:
        selections = {}
        user_table = False

    # Remove this param from the user's query if it is constrained.
    # This keeps the green hinting numbers from reacting to changes to its
    # own field.
    param_name_no_num = strip_numeric_suffix(full_param_name)
    for to_remove in [param_name_no_num,
                      param_name_no_num + '1',
                      param_name_no_num + '2']:
        if to_remove in selections:
            del selections[to_remove]
    if selections:
        user_table = search.views.getUserQueryTable(selections, extras)
    else:
        user_table = False

    # Is this result already cached?
    cache_key  = "rangeep" + param_name_no_num
    if user_table:
        cache_key += str(search.views.setUserSearchNo(selections, extras))

    if cache.get(cache_key) is not None:
        range_endpoints = cache.get(cache_key)
        return responseFormats(range_endpoints, fmt, template='mults.html')

    # We didn't find a cache entry, so calculate the endpoints
    try:
        results = table_model.objects # this is a count(*), group_by query
    except AttributeError, e:
        log.error('get_range_endpoints threw: %s', str(e))
        log.error('Could not find table model for table_name: %s', table_name)
        raise Http404('Does Not Exist')

    if selections:
        # There are selections, so tie the query to user_table
        if table_name == 'obs_general':
            where = '%s.id = %s.id' % (table_name, user_table)
        else:
            where = '%s.obs_general_id = %s.id' % (table_name, user_table)

        range_endpoints = (results.extra(where=[where], tables=[user_table]).
                           aggregate(min=Min(param1), max=Max(param2)))

        # Count of nulls
        where = where+' and '+param1+' is null and '+param2+' is null'
        range_endpoints['nulls'] = results.extra(where=[where],
                                                 tables=[user_table]).count()

    else:
        # There are no selections, so hit the whole table
        range_endpoints = results.all().aggregate(min = Min(param1),
                                                  max = Max(param2))

        # Count of nulls
        where = param1+' is null and '+param2+' is null '
        range_endpoints['nulls'] = results.all().extra(where=[where]).count()

    # convert time_sec to human readable
    # XXX THIS IS A HORRIBLE HACK. FIX THIS!
    # ALSO FIX this whole thing where it looks up time1 or time2 separately from
    # time_sec1 or time_sec2 because it has trouble with floating point imprecision
    # and sometimes doesn't find the associated time1/time2 field!
    if form_type == 'TIME':
        if slug.startswith('ert'):
            range_endpoints['min'] = ObsMissionCassini.objects.filter(**{param1:range_endpoints['min']})[0].ert1
            range_endpoints['max'] = ObsMissionCassini.objects.filter(**{param2:range_endpoints['max']})[0].ert2
        else:
            if range_endpoints['min'] is not None:
                range_endpoints['min'] = ObsGeneral.objects.filter(**{param1:range_endpoints['min']})[0].time1
            if range_endpoints['max'] is not None:
                range_endpoints['max'] = ObsGeneral.objects.filter(**{param2:range_endpoints['max']})[0].time2

    else:
        # form type is not TIME..
        if form_type_ext is not None:
            # We need to run some arbitrary function to convert from float to
            # some kind of string. This happens for spacecraft clock count
            # fields, among others.
            if form_type_ext in settings.RANGE_FUNCTIONS:
                func = settings.RANGE_FUNCTIONS[form_type_ext][0]
                if range_endpoints['min'] is not None:
                    range_endpoints['min'] = func(range_endpoints['min'])
                if range_endpoints['max'] is not None:
                    range_endpoints['max'] = func(range_endpoints['max'])
            else:
                log.error('Unknown RANGE function "%s"', form_type_ext)
        try:
            if abs(range_endpoints['min']) > 999000:
                range_endpoints['min'] = format(1.0*range_endpoints['min'],'.3');
        except TypeError:
            pass

        try:
            if abs(range_endpoints['max']) > 999000:
                range_endpoints['max'] = format(1.0*range_endpoints['max'],'.3');
        except TypeError:
            pass

    # save this in cache
    cache.set(cache_key,range_endpoints)

    return responseFormats(range_endpoints,fmt,template='mults.html')


def getFields(request,**kwargs):
    """
        this is helper method for people using the public API
        it's a list of all slugs in the database and helpful info
        about each one like label, dict/more_info links:

            surfacegeometryJUPITERsolarhourangle: {
                more_info: {
                    def: false,
                    more_info: false
                },
                label: "Solar Hour Angle"
            }

        if 'field' is in kwargs, it will return this for just that field (#todo this broken?)
        otherwise returns full list of fields in db, as seen here:
        https://tools.pds-rings.seti.org/opus/api/fields.json

    """
    field = category = ''
    fmt = kwargs['fmt']
    if 'field' in kwargs:
        field = kwargs['field']
    if 'category' in kwargs:
        category = kwargs['category']

    cache_key = 'getFields:field:' + field + ':category:' + category
    if cache.get(cache_key):
        fields = cache.get(cache_key)
    else:
        if field:
            fields = ParamInfo.objects.filter(slug=field)
        elif category:
            fields = ParamInfo.objects.filter(category_name=field)
        else:
            fields = ParamInfo.objects.all()

    # build return objects
    return_obj = {}
    for f in fields:
        return_obj[f.slug] = {
            'label': f.label,
            'more_info': f.get_dictionary_info(),
            }

    if not cache.get(cache_key):
        cache.set(cache_key,return_obj)

    return HttpResponse(json.dumps(return_obj), content_type='application/json')
