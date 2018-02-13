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
from tools.app_utils import responseFormats, stripNumericSuffix
import settings


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
    except:
        selections = {}

    param_info = search.views.get_param_info_by_slug(slug)

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
                    mult = mult_id  # fall back to id if there is no label

                mults[mult] = row[mult_name + '__count']
            except: pass # a none object may be found in the data but if it doesn't have a table row we don't handle it

        cache.set(cache_key,mults)

    multdata = { 'field':slug,'mults':mults }

    if (request.is_ajax()):
        reqno = request.GET.get('reqno','')
        multdata['reqno'] = reqno

    return responseFormats(multdata,fmt,template='mults.html')


# todo: why is this camel case?
def getRangeEndpoints(request,slug,fmt='json'):
    """
    fetch range widget hinting data for widget defined by slug
    based on current search defined in request

    this is the valid range endpoints that appear in
    range widgets (green numbers)

    returns a dictionary like:

        { min: 63.592, max: 88.637, nulls: 2365}

    """
    # if this param is in selections we want to remove it,
    # want results for param as they would be without itself constrained
    #    extras['qtypes']['']
    update_metrics(request)

    param_info = search.views.get_param_info_by_slug(slug)
    param_name = param_info.param_name()
    form_type = param_info.form_type
    table_name = param_info.category_name

    # "param" is the field name, the param_name with the table_name stripped
    param1 = stripNumericSuffix(param_name.split('.')[1]) + '1'
    param2 = stripNumericSuffix(param_name.split('.')[1]) + '2'
    param_no_num = stripNumericSuffix(param1)
    table_model = apps.get_model('search', table_name.title().replace('_',''))

    if form_type == 'RANGE' and '1' not in param_info.slug and '2' not in param_info.slug:
        param1 = param2 = param_no_num  # single column range query

    try:
        (selections,extras) = search.views.urlToSearchParams(request.GET)
        user_table = search.views.getUserQueryTable(selections,extras)
        has_selections = True
    except TypeError:
        selections = {}
        has_selections = False
        user_table = False

    # remove this param from the user's query if it is constrained
    # this keeps the green hinting numbers from reacting
    # to changes to its own field
    param_name_no_num = stripNumericSuffix(param_name)
    to_remove = [param_name_no_num, param_name_no_num + '1', param_name_no_num + '2']
    for p in to_remove:
        if p in selections:
            del selections[p]
    if not bool(selections):
        has_selections = False
        user_table = False

    # cached already?
    cache_key  = "rangeep" + param_no_num
    if user_table:
        cache_key += str(search.views.setUserSearchNo(selections,extras))

    if cache.get(cache_key) is not None:
        range_endpoints = cache.get(cache_key)
        return responseFormats(range_endpoints,fmt,template='mults.html')

    # no cache found, calculating..
    try:
        results    = table_model.objects # this is a count(*), group_by query
    except AttributeError, e:
        log.error("getRangeEndpoints threw: %s", str(e))
        log.error("Could not find table model for table_name: %s", table_name)
        raise Http404("Does Not Exist")

    if table_name == 'obs_general':
        where = "%s.id = %s.id" % (table_name, user_table)
    else:
        where = "%s.obs_general_id = %s.id" % (table_name, user_table)

    if has_selections:
        # has selections, tie query to user_table
        range_endpoints = results.extra(where = [where], tables = [user_table]).aggregate(min=Min(param1), max=Max(param2))

        # get count of nulls
        where = where + " and " + param1 + " is null and " + param2 + " is null "
        range_endpoints['nulls'] = results.extra(where=[where],tables=[user_table]).count()

    else:
        # no user query table, just hit the whole table

        range_endpoints  = results.all().aggregate(min = Min(param1),max = Max(param2))

        # count of nulls
        where = param1 + " is null and " + param2 + " is null "
        range_endpoints['nulls'] = results.all().extra(where=[where]).count()

    # convert time_sec to human readable
    if form_type == "TIME":
        range_endpoints['min'] = ObsGeneral.objects.filter(**{param1:range_endpoints['min']})[0].time1
        range_endpoints['max'] = ObsGeneral.objects.filter(**{param2:range_endpoints['max']})[0].time2
        pass  # ObsGeneral.objects.filter(param1=)

    else:
        # form type is not TIME..
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
