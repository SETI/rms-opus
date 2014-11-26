###############################################
#
#   metadata.views
#
################################################
import json
from django.core.cache import cache
from django.http import Http404
from django.http import HttpResponse
from django.db.models import Avg, Max, Min, Count, get_model
from django.db import connection
from paraminfo.models import ParamInfo

from search.models import *

# from paraminfo.models import *
from tools.app_utils import responseFormats, stripNumericSuffix
import settings


import logging
log = logging.getLogger(__name__)

def getMultName(param_name):

    """ mult foreign key tables are named like so """
    return "mult_" + '_'.join(param_name.split('.'))

def getUserSearchTableName(no):
    """ a bit of text manipulation, user search tables are stored like so: """
    return 'cache_' + str(no);


def getResultCount(request,fmt='json'):

    """
    result count for a search

    """

    if request.GET is None:
        return HttpResponse(json.dumps({'result_count':'0'}),  mimetype='application/json')

    try:
        (selections,extras) = urlToSearchParams(request.GET)
    except TypeError:
        log.error("could not find selections for request")
        log.error(request.GET)
        raise Http404

    reqno = request.GET.get('reqno','')

    if selections is False:
        count = 'not found'
        return HttpResponse(json.dumps({'result_count':count}),  mimetype='application/json')


    table = getUserQueryTable(selections,extras)

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

        cache.set(cache_key,count,0)

    data = {'result_count':count}

    if (request.is_ajax()):
        data['reqno'] = request.GET['reqno']

    return responseFormats({'data':[data]},fmt,template='result_count.html')


def getValidMults(request,slug,fmt='json'):
    """
    returns list of valid mult ids or labels for field in GET param "field"
    based on current search defined in request
    field_format = 'ids' or 'labels' depending on how you want your data back
    (OPUS UI will use ids but they aren't very readable for everyone else)
    """
    try:
        (selections,extras) = urlToSearchParams(request.GET)
    except:
        selections = {}

    param_info = ParamInfo.objects.get(slug=slug)
    table_name = param_info.category_name
    param_name = param_info.param_name()

    # if this param is in selections we want to remove it,
    # want mults for a param as they would be without itself
    if param_name in selections:
        del selections[param_name]

    has_selections = True
    if len(selections.keys()) < 1: has_selections = False

    cache_key  = "mults" + param_name + str(setUserSearchNo(selections))

    if (cache.get(cache_key) is not None):

        mults = cache.get(cache_key)

    else:

        mult_name  = getMultName(param_name) # the name of the field to query
        mult_model = get_model('search',mult_name.title().replace('_',''))
        table_model = get_model('search', table_name.title().replace('_',''))

        mults = {}  # info to return
        results    = table_model.objects.values(mult_name).annotate(Count(mult_name))  # this is a count(*), group_by query!

        if has_selections:
            # selections are constrained so join in the user_table
            user_table = getUserQueryTable(selections,extras)
            if table_name == 'obs_general':
                where   = table_name + ".id = " + user_table + ".id"
            else:
                where   = table_name + ".obs_general_id = " + user_table + ".id"
            results = results.extra(where=[where],tables=[user_table])

        for row in results:
            mult_id = row[mult_name]
            try:
                try:    mult = mult_model.objects.get(id=mult_id).label
                except: mult = mult_id  # fall back to id if there is no label

                mults[mult] = row[mult_name + '__count']
            except: pass # a none object may be found in the data but if it doesn't have a table row we don't handle it

        cache.set(cache_key,mults,0)

    multdata = { 'field':slug,'mults':mults }

    if (request.is_ajax()):
        reqno = request.GET.get('reqno','')
        multdata['reqno']= reqno

    return responseFormats(multdata,fmt,template='mults.html')


# todo: why is this camel case?
def getRangeEndpoints(request,slug,fmt='json'):
    """
    returns valid range endpoints for field given selections and extras
    """
    # if this param is in selections we want to remove it,
    # want results for param as they would be without itself constrained

    #    extras['qtypes']['']

    param_info = ParamInfo.objects.get(slug=slug)

    param_name = param_info.param_name()
    form_type = param_info.form_type
    table_name = param_info.category_name
    param_name1 = stripNumericSuffix(param_name.split('.')[1]) + '1'
    param_name2 = stripNumericSuffix(param_name.split('.')[1]) + '2'
    param_name_no_num = stripNumericSuffix(param_name1)
    table_model = get_model('search', table_name.title().replace('_',''))

    try:
        (selections,extras) = urlToSearchParams(request.GET)
        user_table = getUserQueryTable(selections,extras)
        has_selections = True

    except TypeError:
        has_selections = False
        user_table = False

    # we remove this param from the user's query if it's there, because
    # otherwise it will just return it's own values
    if param_name1 in selections:
        del selections[param_name1]
    if param_name2 in selections:
        del selections[param_name2]

    # cached already?
    cache_key  = "rangeep" + param_name_no_num
    if user_table: cache_key += str(setUserSearchNo(selections,extras))

    if cache.get(cache_key) is not None:
        range_endpoints = cache.get(cache_key)
        return responseFormats(range_endpoints,fmt,template='mults.html')

    results    = table_model.objects # this is a count(*), group_by query!
    if table_name == 'obs_general':
        where = table_name + ".id = " + user_table + ".id"
    else:
        where = table_name + ".obs_general_id = " + user_table + ".id"

    if has_selections:
        # has selections, tie query to user_table
        range_endpoints = results.extra(where = [where], tables = [user_table]).aggregate(min = Min(param_name1), max = Max(param_name1))

        # get count of nulls
        where = where + " and " + param_name1 + " is null and " + param_name2 + " is null "
        range_endpoints['nulls'] = results.extra(where=[where],tables=[user_table]).count()

    else:
        # no user query table, just hit the whole table

        range_endpoints  = results.all().aggregate(min = Min(param_name1),max = Max(param_name2))

        # count of nulls
        where = param_name1 + " is null and " + param_name2 + " is null "
        range_endpoints['nulls'] = results.all().extra(where=[where]).count()

    # convert time_sec to human readable
    if form_type == "TIME":
        range_endpoints['min'] = ObsGeneral.objects.filter(**{param_name1:range_endpoints['min']})[0].time1
        range_endpoints['max'] = ObsGeneral.objects.filter(**{param_name1:range_endpoints['max']})[0].time1
        pass  # ObsGeneral.objects.filter(param_name1=)
    else:
        if abs(range_endpoints['min']) > 999000:
            range_endpoints['min'] = format(1.0*range_endpoints['min'],'.3');
        if abs(range_endpoints['max']) > 999000:
            range_endpoints['max'] = format(1.0*range_endpoints['max'],'.3');

    cache.set(cache_key,range_endpoints,0)

    return responseFormats(range_endpoints,fmt,template='mults.html')


def getFields(request,**kwargs):
    field=category=False
    fmt = kwargs['fmt']
    if 'field' in kwargs:
        field = kwargs['field']
    if 'category' in kwargs:
        category = kwargs['category']

    cache_key = 'getFields:field:' + field + ':category:' + category
    if (cache.get(cache_key)):
        fields = cache.get(cache_key)
    else:
        if field:
            fields = ParamInfo.objects.filter(slug=field)
        elif category:
            fields = ParamInfo.objects.filter(category_name=field)
        else:
            fields = ParamInfo.objects.all()
        cache.set(cache_key,fields,0)

    return responseFormats(fields,fmt,template='detail.html')


def getCats(request, **kwargs):

    field=category=False
    fmt = kwargs['fmt']
    if 'category' in kwargs:
        category = ' '.join(kwargs['category'].split('_'));

    cache_key='getCats:field:' + field + ':cat:' + category
    if (cache.get(cache_key)):
        fields = cache.get(cache_key)
    else:
        if category:
            fields = Category.objects.filter(name=category)
        else:
            fields = Category.objects.all()
        cache.set(cache_key,fields,0)

    return responseFormats(fields,fmt,template='detail.html')

from search.views import urlToSearchParams, setUserSearchNo, getUserQueryTable

