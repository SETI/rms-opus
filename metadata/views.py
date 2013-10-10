###############################################
#
#   metadata.views
#
################################################
from search.views import *
from paraminfo.models import *
from django.utils import simplejson
from django.http import HttpResponse
from django.db.models import Avg, Max, Min, Count
from tools.app_utils import *
import settings


import logging
log = logging.getLogger(__name__)

def getResultCount(request,fmt='json'):

    """
    result count for a search

    """

    if request.GET is None:
        return HttpResponse(simplejson.dumps({'result_count':'0'}),  mimetype='application/json')

    (selections,extras) = urlToSearchParams(request.GET)

    reqno = request.GET.get('reqno','')

    if selections is False:
        count = 'not found'
        return HttpResponse(simplejson.dumps({'result_count':count}),  mimetype='application/json')


    table = getUserQueryTable(selections,extras)

    log.debug('got ' + str(table))

    if table is False:
        #print 'getUserQueryTable says: no table'
        count = False;
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
                count = False

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
    except: return False

    qtypes     = extras['qtypes']
    param_info = ParamInfo.objects.get(slug=slug)
    param_name = param_info.name
    mission = param_info.mission
    instrument = param_info.instrument


    # if this param is in selections we want to remove it,
    # want mults for a param as they would be without itself
    if param_name in selections:
        del selections[param_name]

    # if the other members of selections are from different missions or instruments
    # they will nullify this query, so we remove them too
    if mission:
        for name,value in selections.items():
            if mission != ParamInfo.objects.get(name=name).mission:
                del selections[name]
    if instrument:
        for name,value in selections.items():
            if instrument != ParamInfo.objects.get(name=name).instrument:
                del selections[name]


    # if removing current param leaves no other selections we handle that
    has_selections = True
    if len(selections.keys()) < 1: has_selections = False

    cache_key  = "mults" + param_name + str(setUserSearchNo(selections))

    if (cache.get(cache_key) is not None):
        mults = cache.get(cache_key)
    else:

        mult_name  = getMultName(param_name) # the name of the field to query
        model      = get_model('search',mult_name.title().replace('_',''))


        mults = {}  # info to return
        results    = Observations.objects.values(mult_name).annotate(Count(mult_name))  # this is a count(*), group_by query!

        if has_selections:
            # selections are constrained so join in the user_table
            user_table = getUserQueryTable(selections,extras)
            where   = "observations.id = " + user_table + ".id"
            results = results.extra(where=[where],tables=[user_table])


        for row in results:
            mult_id = row[mult_name]
            try:
                try:    mult = model.objects.get(id=mult_id).label
                except: mult = mult_id  # fall back to id if there is no label

                mults[mult] = row[mult_name + '__count']
            except: pass # a none object may be found in the data but if it doesn't have a table row we don't handle it



    cache.set(cache_key,mults,0)
    multdata = { 'field':slug,'mults':mults }

    if (request.is_ajax()):
        reqno = request.GET.get('reqno','')
        multdata['reqno']= reqno

    return responseFormats(multdata,fmt,template='mults.html')



def getRangeEndpoints(request,slug,fmt):
    """
    returns valid range endpoints for field given selections and extras
    """
    # if this param is in selections we want to remove it,
    # want results for param as they would be without itself constrained

    #    extras['qtypes']['']

    param_name = str(ParamInfo.objects.get(slug=slug))
    param_name1 = stripNumericSuffix(param_name) + '1'
    param_name2 = stripNumericSuffix(param_name) + '2'
    param_name_no_num = stripNumericSuffix(param_name1)

    try:
        (selections,extras) = urlToSearchParams(request.GET)
        user_table = getUserQueryTable(selections,extras)

        # we remove this param from the user's query if it's there, because
        # otherwise it will just return it's own values
        if param_name1 in selections:
            del selections[param_name1]
        if param_name2 in selections:
            del selections[param_name2]

    except:
        user_table = False

    # cached already?
    cache_key  = "rangeep" + param_name_no_num
    if user_table: cache_key += str(setUserSearchNo(selections,extras))

    if cache.get(cache_key) is not None:
        range_endpoints = cache.get(cache_key)
        return responseFormats(range_endpoints,fmt,template='mults.html')


    if user_table:
        # get endpoints
        where = "observations.id = " + user_table + ".id"
        range_endpoints          = Observations.objects.extra(where = [where], tables = [user_table]).aggregate(min = Min(param_name1),max = Max(param_name1))

        # get count of nulls
        where = "observations.id = " + user_table + ".id and " + param_name1 + " is null and " + param_name2 + " is null "
        range_endpoints['nulls'] = Observations.objects.extra(where = [where], tables = [user_table]).count()
    else:
        # endpoints
        range_endpoints          = Observations.objects.all().aggregate(min = Min('ring_radius1'),max = Max('ring_radius2'))

        # count of nulls
        where = param_name1 + " is null and " + param_name2 + " is null "
        range_endpoints['nulls'] = Observations.objects.filter(ring_radius1__isnull=True).count()


    if abs(range_endpoints['min']) > 1000:
        range_endpoints['min'] = format(1.0*range_endpoints['min'],'.3');
    if abs(range_endpoints['max']) > 1000:
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


