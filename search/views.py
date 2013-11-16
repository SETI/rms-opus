###############################################
#
#   search.views
#
################################################
from search.models import *
from paraminfo.models import *
from operator import __or__ as OR
from django.shortcuts import render_to_response
from django.http import HttpResponse, Http404
from django.core import serializers
from django.utils import simplejson
from django.conf import settings
from django.db.models import Q, get_model
from django.db import connection, transaction
from django.core.cache import cache
import subprocess, operator, hashlib, os, re
from tools.app_utils import *
from tools.views import *

import logging
log = logging.getLogger(__name__)

def urlToSearchParams(request_get):
    """
    OPUS lets users put nice readable things in the URL, like "planet=Jupiter" rather than "planet_id=3"
    this function takes the url params and translates it into a list that contains 2 dictionaries
    the first dict is the user selections: keys of the dictionary are param_names of data columns in
    the data table values are always lists and represent the users selections
    the 2nd dict is any extras being passed by user, like qtypes that define what types of queries
    will be performed for each param-value set in the first dict

    NOTE: pass request_get = request.GET to this func please
    (this func doesn't return an http response so unit tests freak if you pass it an http request :)

    example command line usage:

    >>>> from search.views import *
    >>>> from django.http import QueryDict
    >>>> q = QueryDict("planet=Jupiter")
    >>>> (selections,extras) = urlToSearchParams(q)
    >>>> selections
    {'planet_id': [u'Jupiter']}
    >>>> extras
    {'qtypes': {}}

    """
    selections = {}
    qtypes     = {}

    for searchparam in request_get.items():
        try:
            slug              = searchparam[0]
            slug_no_num       = stripNumericSuffix(slug)
            param_info        = ParamInfo.objects.get(slug=slug)
            param_name        = param_info.name
            form_type         = param_info.form_type
            param_name_no_num = stripNumericSuffix(param_name)

            if form_type in settings.MULT_FORM_TYPES:
                # mult for types can be sorted to save duplicate queries being built
                selections[param_name] = sorted(searchparam[1].strip(',').split(','))
            else:
                # no other form types can be sorted since qtype depends on ordering
                selections[param_name] = searchparam[1].strip(',').split(',')
            try:
                # checking for passed extra query instructions for this param
                # we always want to check the param name without the numeric suffix for ranges:
                qtypes[param_name_no_num] = request_get.get('qtype-'+slug_no_num,False).strip(',').split(',')
            except: pass
        except: pass # the param passed doesn't exist or is a USER PREF AAAAAACK
    if len(selections.keys()) > 0:
        extras  = {}
        extras['qtypes'] = qtypes
        results = []
        results.append(selections)
        results.append(extras)
        return results

    else: return False


def setUserSearchNo(selections,extras={}):
    """
    creates a new row in user_searches table (class userSearches) for every search request
    [cleanup,optimize]
    this table (model) lists query params+values plus any extra info needed to run a data search query
    this method looks in user_searches table for current selections
    if none exist creates it, returns id key
    """
    qtypes_json = qtypes_hash = None
    if 'qtypes' in extras:
        # 'any' is the default qtype, so lets not set that in the cache, set 'any' = None
        for k,qlist in extras['qtypes'].items():
            extras['qtypes'][k] = [x if x != 'any' else None for x in qlist]
            if len(extras['qtypes'][k])==1 and extras['qtypes'][k][0]==None:
                extras['qtypes'].pop(k)
        if len(extras['qtypes']):
            qtypes_json = str(simplejson.dumps(sortDict(extras['qtypes'])))
            qtypes_hash = hashlib.md5(qtypes_json).hexdigest()


    units_json = units_hash = None
    if 'units' in extras:
        units_json = str(simplejson.dumps(sortDict(extras['units'])))
        units_hash = hashlib.md5(units_json).hexdigest()


    string_selects_json = string_selects_hash = None
    if 'string_selects' in extras:
        string_selects_json = str(simplejson.dumps(sortDict(extras['string_selects'])))
        string_selects_hash = hashlib.md5(string_selects_json).hexdigest()

    selections_json = str(simplejson.dumps(selections))
    selections_hash = hashlib.md5(selections_json).hexdigest()

    # do we already have this cached?
    cache_key = 'usersearchno:selections_hash:' + str(selections_hash) + ':qtypes_hash:' +  str(qtypes_hash) + ':units_hash:' + str(units_hash) + ':string_selects_hash:' + str(string_selects_hash)
    if (cache.get(cache_key)):
        return cache.get(cache_key)

    # no cache, let's keep going..

    try:
        s = UserSearches.objects.get(selections_hash=selections_hash,qtypes_hash=qtypes_hash,units_hash=units_hash,string_selects_hash=string_selects_hash)
    except UserSearches.DoesNotExist:
        s = UserSearches(selections_hash=selections_hash, selections_json=selections_json, qtypes=qtypes_json,qtypes_hash=qtypes_hash,units=units_json,units_hash=units_hash, string_selects=string_selects_json,string_selects_hash=string_selects_hash )
        s.save()

    cache.set(cache_key,s.id,0)
    return s.id


def getUserQueryTable(selections,extras={}):
    """
    This is THE main data query place.  Performs a data search and creates
    a table of Ids that match the result rows.

    (the function urlToSearchParams take the user http request object and
    creates the data objects that are passed to this function)

    """
    cursor = connection.cursor()

    # housekeeping
    if selections is False: return False
    if len(selections.keys()) < 1: return False
    if 'qtypes' in extras:
        all_qtypes = extras['qtypes']

    # check if this search table already exists:
    no     = setUserSearchNo(selections,extras)
    ptbl   = getUserSearchTableName(no)

    # see if memcache knows about it:
    cache_key = 'cache_table:' + str(no)
    if (cache.get(cache_key )):
        return cache.get(cache_key)

    # check if table exists in db
    try:
        cursor.execute("desc " + ptbl)
        return ptbl
    except DatabaseError:
        pass

    # cache table dose not exist, we will make one by runing the query
    long_querys = []  # special longitudinal queries are pure sql
    q_objects = [] # for building up the query object
    for param_name, value_list in selections.items():
        param_info = ParamInfo.objects.get(name=param_name)
        form_type = param_info.form_type
        special_query = param_info.special_query
        table_name = param_info.category_name

        param_name_no_num = stripNumericSuffix(param_name)

        # fetch any qtypes
        try:    qtypes = all_qtypes[param_name_no_num]
        except: qtypes = []

        # now build the q_objects to run the query, by form_type:

        # MULTs
        if form_type in settings.MULT_FORM_TYPES:
            mult_name = "mult_" + table_name + "_" + param_name
            model = get_model('search',mult_name.title().replace('_',''))
            mult_values = [x['pk'] for x in list(model.objects.filter(label__in=value_list).values('pk'))]
            q_objects.append(Q(**{"%s__in" % mult_name: mult_values }))


        # RANGE including LONG
        if form_type in settings.RANGE_FIELDS:
            if special_query == 'long':
                lq = longitudeQuery(selections,param_name)
                long_querys.append(lq)
                continue

            if param_name_no_num in finished_ranges:
                # this prevents range queries from getting through twice
                # if one range side has been processed can skip the 2nd
                continue # this range has already been done, clause for both sides built, skip to next param in loop
            else: finished_ranges += [param_name_no_num]

            q_obj = range_query_object(selections, param_name, qtypes)
            q_objects.append(q_obj)



    try: # now create our table

        # construct our query, we'll be using the sql django makes
        cursor = connection.cursor()
        q = str(ObsGeneral.objects.filter(*q_objects).values('pk').query)

        # append any longitudinal queries to the query string
        if long_querys:
            for q in long_querys:
                q += " and (%s) " % q

        # with this we can create a table that contains the single row
        cursor.execute("create table " + ptbl + " " + q)
        # add the key, note this should be spawned to a backend process:
        cursor.execute("alter table " + connection.ops.quote_name(ptbl) + " add unique key(id)  ")
        # print 'execute ok'
        cache.set(cache_key,ptbl,0)
        return ptbl

    except:
        log.debug('query execute failed')
        # import sys
        # print sys.exc_info()[1] + ': ' + print sys.exc_info()[1]
        return False


def range_query_object(selections, param_name, qtypes):
    """
    builds query for numeric ranges where 2 data columns represent min and max values
    """
    param_name_no_num = stripNumericSuffix(param_name)

    param_info    = ParamInfo.objects.get(name=param_name)
    form_type     = param_info.form_type
    special_query = param_info.special_query

    param_name_min = param_name_no_num + '1'
    param_name_max = param_name_no_num + '2'

    try:    values_min = selections[param_name_min]
    except: values_min = []
    try:    values_max = selections[param_name_max]
    except: values_max = []

    # if these are times convert values from time string to seconds
    if form_type == 'TIME':
        values_min = convertTimes(values_min,conversion_script='time_to_seconds')
        try:
            index = values_min.index(None)
            raise Exception("InvalidTimes")
        except: pass
        values_max = convertTimes(values_max,conversion_script='time_to_seconds')
        try:
            index = values_max.index(None)
            raise Exception("InvalidTimes")
        except: pass

    try:   qtype = qtypes[0]
    except IndexError: qtypes += ['any'] # defaults to any

    count = len(values_max) if len(values_max) > len(values_min) else len(values_min) # how many times to go thru this loop:
    i=0

    all_query_expressions = []  # these will be joined by OR
    while i < count:
        try:    qtype = qtypes[i]
        except: qtype = qtypes[0]

        try:    value_min = values_min[i]
        except: value_min = None
        try:    value_max = values_max[i]
        except: value_max = None

        if value_min is not None and value_max is not None:
            (value_min,value_max) = sorted([value_min,value_max]) # reverse value_min and value_max if value_min < value_max


        q_exp1, q_exp2 = None, None
        if qtype == 'all':

            if value_min:
                # param_name_min <= value_min
                q_exp1 = Q(**{"%s__lte" % param_name_min: value_min })

            if value_max:
                # param_name_max >= value_max
                q_exp2 = Q(**{"%s__gte" % param_name_max: value_max })

        elif qtype == 'only':

            if value_min:
                # param_name_min >= value_min
                q_exp1 = Q(**{"%s__gte" % param_name_min: value_min })

            if value_max:
                # param_name_max <= value_max
                q_exp2 = Q(**{"%s__lte" % param_name_max: value_max })

        else: # defaults to qtype = any

            if value_max:
                # param_name_min <= value_max
                q_exp1 = Q(**{"%s__lte" % param_name_min: value_max })

            if value_min:
                # param_name_max >= value_min
                q_exp2 = Q(**{"%s__gte" % param_name_max: value_min })


        q_exp = q_exp1 & q_exp2 if q_exp2 else q_exp1
        all_query_expressions.append(q_exp)
        i+=1

    # now we have all query expressions, join them with 'OR'
    return reduce(OR, all_query_expressions)


def longitudeQuery(selections,param_name):
    """ raises 'KeyError' if min or max value is blank """
    clauses = []
    params  = []

    param_name_no_num = stripNumericSuffix(param_name)
    param_name_min    = param_name_no_num + '1'
    param_name_max    = param_name_no_num + '2'
    col_d_long        = 'd_' + param_name_no_num

    try:
        values_min = selections[param_name_min]
        values_max = selections[param_name_max]
    except:
        raise Exception("LongitudeError")

    count = len(values_max) if len(values_max) > len(values_min) else len(values_min) # how many times to go thru this loop:
    i=0
    while i < count:

        value_min = values_min[i]
        value_max = values_max[i]


        # find the midpoint and dx of the user's range
        if (value_max >= value_min):
            longit = (value_min + value_max)/2.
            d_long = longit - value_min
        else:
            longit   = (value_min + value_max + 360.)/2.
            d_long = longit - value_min

        if (longit >= 360): longit = longit - 360.

        if d_long:
            clauses += ["(abs(abs(mod(%s - %s + 180., 360.)) - 180.) <= %s + %s)"];
            params  += [longit,param_name_no_num,d_long,col_d_long]

        i+=1

    # print 'clauses ' + str(clauses)
    # print 'params ' + str(params)
    return ' OR '.join(clauses), params


def convertTimes(value_list,conversion_script='time_to_seconds'):
    """ other conversion scripts are 'seconds_to_time','seconds_to_et' """
    converted = []
    for time in value_list:
        cache_key = 'convertedtime:'+time
        if (cache.get(cache_key)):
            converted += [cache.get(cache_key)]
        else:
            # django guru explains: http://stackoverflow.com/questions/768677/how-do-i-prevent-execution-of-arbitrary-commands-from-a-django-app-making-system
            t = subprocess.Popen([settings.C_PATH + conversion_script, time], shell=False, stdout=subprocess.PIPE)
            try:
                time = t.stdout.readlines()[0].rstrip() # triggers key error if no time is returned
                cache.set(cache_key,time,0)
                converted += [time]
            except IndexError:
                converted += [None]
    return converted


def findInvalidTimes(value_list):
    """
    this function tells you which times are invalid in the value_list
    we know that value_list contains None values before passing it to this
    """
    converted_value_list = convertTimes(value_list)
    try:
        index = converted_value_list.index(None) # invalid times were submitted
        invalids = []
        i = -1
        try:     # find which times were invalid
            while 1:
                i = converted_value_list.index(None, i+1)
                invalids += [value_list[i]]
        except ValueError: pass
        return invalids
    except ValueError: pass



def simpleRangeQuery(param_name,value_list):
    """
    this method builds simple range queries for fields whose default type are MULT or STRING
    """
    value_list = sorted(value_list)
    q          = param_name + " >= %s and " + param_name + " <= %s"
    id_list    = [value_list[0],value_list[1]]
    return [q , id_list]


# throws InvalidTimes exception if it can't convert all times given
# run findInvalidTimes if you get this exception to see the invalid times
def rangeQuery(selections,param_name,qtypes):
    """
    builds query for numeric ranges where 2 data columns represent min and max values
    """
    param_info    = ParamInfo.objects.get(name=param_name)
    form_type     = param_info.form_type
    special_query = param_info.special_query

    param_name_min = stripNumericSuffix(param_name) + '1'
    param_name_max = stripNumericSuffix(param_name) + '2'

    try:    values_min = selections[param_name_min]
    except: values_min = []
    try:    values_max = selections[param_name_max]
    except: values_max = []

    if form_type == 'TIME':
        values_min = convertTimes(values_min,conversion_script='time_to_seconds')
        try:
            index = values_min.index(None)
            raise Exception("InvalidTimes")
        except: pass
        values_max = convertTimes(values_max,conversion_script='time_to_seconds')
        try:
            index = values_max.index(None)
            raise Exception("InvalidTimes")
        except: pass

    clauses = [] # clauses to be joined
    values  = [] # parameterized values

    try:   qtype = qtypes[0]
    except IndexError: qtypes += ['any'] # defaults to any

    count = len(values_max) if len(values_max) > len(values_min) else len(values_min) # how many times to go thru this loop:
    i=0
    while i < count:

        clause_pair = [] # each side of same range is joined with ' AND ' and pairs are joined by ' OR '

        try:    qtype = qtypes[i]
        except: qtype = qtypes[0]

        try:    value_min = values_min[i]
        except: value_min = None
        try:    value_max = values_max[i]
        except: value_max = None


        if value_min is not None and value_max is not None:
            (value_min,value_max) = sorted([value_min,value_max]) # reverse value_min and value_max if value_min < value_max

        if qtype == 'all':
            if value_min:
                clause_pair +=  [param_name_min + ' <= %s']
                values.append(value_min)
            if value_max:
                clause_pair +=  [param_name_max + ' >= %s']
                values.append(value_max)
        elif qtype == 'only':
            if value_min:
                clause_pair +=  [param_name_min + ' >= %s']
                values.append(value_min)
            if value_max:
                clause_pair +=  [param_name_max + ' <= %s']
                values.append(value_max)
        else: # defaults to qtype = any
            if value_max:
                clause_pair +=  [param_name_min + ' <= %s']
                values.append(value_max)
            if value_min:
                clause_pair +=  [param_name_max + ' >= %s']
                values.append(value_min)

        clauses += ['(' + ' AND '.join(clause_pair) + ')']
        i+=1

    return [' OR '.join(clauses), values]



from metadata.views import *
from search.forms import *

