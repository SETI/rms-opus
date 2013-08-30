###############################################
#
#   search.views
#
################################################
from opus.search.models import *
from opus.paraminfo.models import *
from opus.metadata.views import *
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
from search.forms import *

# NOTE: forehead smack.

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

    cache_key = 'usersearchno:selections_hash:' + str(selections_hash) + ':qtypes_hash:' +  str(qtypes_hash) + ':units_hash:' + str(units_hash) + ':string_selects_hash:' + str(string_selects_hash)
    if (cache.get(cache_key)):
        return cache.get(cache_key)

    try:
        s = UserSearches.objects.get(selections_hash=selections_hash,qtypes_hash=qtypes_hash,units_hash=units_hash,string_selects_hash=string_selects_hash)
    except UserSearches.DoesNotExist:
        s = UserSearches(selections_hash=selections_hash, selections_json=selections_json, qtypes=qtypes_json,qtypes_hash=qtypes_hash,units=units_json,units_hash=units_hash, string_selects=string_selects_json,string_selects_hash=string_selects_hash )
        s.save()

    cache.set(cache_key,s.id,0)
    return s.id


def getQueryTable(mission,instrument):
    """
    which table to query when querying data
    driven by mission and instrument field in param_info (ParamInfo)
    if can query a smaller table do so.
    """
    if instrument:
        table = 'obs_' + mission + '_' + instrument
    elif mission:
        table = 'obs_' + mission
    else:
        table = 'observations'

    return table.lower()


def getUserQueryTable(selections,extras={}):

    """
    This is THE main data query place.  Performs a data search and creates
    a table of Ids that match the result rows.

    (the function urlToSearchParams take the user http request object and
    creates the data objects that are passed to this function)

    OPUS allows querying of different datasets in the same query, in what would normally break
    a simple relational ' AND ' type string of where clauses.
    (for example: no observation possesses both a voyager and a cassini filter)

    To accomplish this each parameter has a 'join_type' below, either 'aux' or 'base'
    whether or not the row in param_info has a value for instrument or mission fields decides this
    mission specific params have a mission_id in this field, instrument specific params have an instrument_id
    Base groups are common to all observations, aux groups are specific to a mission or an instrument
    all params with join type 'base' in a request are joined together with 'and' in a group,
    call it 'Base Group'

    (planet = Saturn and target = Pan)

    params with 'aux' join_type are "AND" joined *each in turn* with a copy of Base group,
    then each resulting set is joined together with 'OR' like:

    (planet = Saturn and target = Pan) and (COISS_filter = RED)
    or
    (planet = Saturn and target = Pan) and (VGISS_filter = BLUE)

    to explain this:
    say we want data from voyager and cassini ISS, defining a different filter for each,
    http request looks like this:

    ?planet=Saturn&target=Pan&vgissfilter=GRN&coissfilter=GREEN

    OPUS looks up the join_type for each param:

    planet        :: join_type = base
    target        :: join_type = base
    vgiss_filter  :: join_type = aux
    coiss_filter  :: join_type = aux

    with this information this function builds a where clause like so:

    (planet = saturn and target = pan and vgissfilter = GRN)
    OR
    (planet = saturn and target = pan and coissfilter = GREEN)

    aka:
    (base group ' AND ' aux1)  OR  (base group ' AND ' aux2) ...

    """
    # housekeeping
    if selections is False: return False

    if len(selections.keys()) < 1: return False

    if 'qtypes' in extras:
        all_qtypes = extras['qtypes']


    # table may already exist
    no     = setUserSearchNo(selections,extras)
    ptbl   = getUserSearchTableName(no)

    cache_key = 'cache_table:' + str(no)
    if (cache.get(cache_key)):
        return cache.get(cache_key)

    cursor = connection.cursor()
    cursor.execute("show tables like %s" , [ptbl])
    if cursor.rowcount: return ptbl # table already exists return that

    # we are buliding a big query piece by piece,
    # each pass adding more to the list of parameterized placeholders
    # these all get pasted together like humpty dumpty at the end, with an "AND"
    base_clauses    = [] # holds the parts of the where clause we will glue together with 'AND', base join types
    base_params     = [] # holds the values to insert into parameterized %s placeholders, base join types
    mission_clauses = {} # mission type clauses by param_name key
    mission_params  = {} # mission params by param_name key
    inst_clauses    = {} # instrument clauses by param_name key
    inst_params     = {} # instrument params by param_name key

    # helpers to keep track of stuff
    inst_missions   = {} # tracker, instrument key corresponds to mission value
    finished_ranges = [] # range params that have been handled already (avoids repeating range clauses for each side of range.. lame huh?)
    combined_mission_clauses = {} # combined base clauses by mission

    # related_tables = {'aux':{}, 'base':{}} fuck it they are always base
    related = {'clauses':[], 'tables':[], 'fields':[]}

    for param_name, value_list in selections.items():
        param_info = ParamInfo.objects.get(name=param_name)
        form_type = param_info.form_type
        special_query = param_info.special_query
        mission = param_info.mission
        instrument = param_info.instrument
        mission = param_info.mission
        param_name_no_num = stripNumericSuffix(param_name)
        # related_table_name = param_info.related_table_name
        # related_table_field_name = param_info.related_table_field_name

        related_table_name = None
        related_table_field_name = None # not fleshed out functionality

        # having a mission_id indicates this should be aux type
        # you can't have an instrument_id without a mission_id
        join_type = 'aux' if mission else 'base'

        # fetch any qtypes
        try:    qtypes = all_qtypes[param_name_no_num]
        except: qtypes = []

        # add any related table info to main query structure
        if related_table_name:
            # join in the related table to the query
            if related_table_name not in related['tables']:
                # this related table has not already joined the pack
                related['tables'].append(related_table_name)

        # this prevents range queries from getting through twice
        # if one range side has been processed can skip the 2nd
        if form_type in settings.RANGE_FIELDS:
            if param_name_no_num in finished_ranges:
                continue # this range has already been done, clause for both sides built, skip to next param in loop
            else: finished_ranges += [param_name_no_num]

        # get the where clause and params for this param/value :
        (clause,params) = buildWhereClause(param_name,value_list,{'form_type':form_type,'qtypes':qtypes,'special_query':special_query, 'selections':selections, 'related_table_name':related_table_name,'related_table_field_name':related_table_field_name})

        # if we have a clause for this param+value, append it to the big list
        if clause:

            if join_type == 'base':
                # these will be part of a flat join with the base where clause
                base_clauses.append(clause) # again this references base_clauses or aux_clauses
                base_params += params       # so can keep them in a flat list


            elif join_type  == 'aux':
                if instrument: # this is an instrument param
                    inst_missions[instrument] = mission # simple tracker for which instruments go with which missions
                # create Aux Clause groupings
                (inst_clauses,inst_params,mission_clauses,mission_params) = createAuxClauseGroups(clause,params,mission,instrument,inst_clauses,inst_params,mission_clauses,mission_params)
            (clause,params)  = [None,None] # unset holders

    # now we have all the clauses and params, arrange the aux clauses so that instruments are grouped with their missions:
    (aux_clauses,aux_params) = gatherAuxClauses(inst_clauses,inst_params,inst_missions,mission_clauses,mission_params)


    # now we have all the base_clauses and/or aux_clauses,  build the big query """
    (grand_unified_query,grand_param_list) = combineAllClauses(base_clauses,base_params,aux_clauses,aux_params,related)

    # now join all sets together with "UNION"
    where_clause = ' UNION '.join(grand_unified_query)

    query = "create table " + connection.ops.quote_name(ptbl) + ' ' + where_clause


    #### not handling related right now but they are partially implemented #####

    # print 'trying ' + query + ' , ' + str(grand_param_list) # shows in unit testing
    try: # now create our table
        cursor.execute(query, grand_param_list) # aaaaand secure

        # print 'query ok'
        cursor.execute("alter table " + connection.ops.quote_name(ptbl) + " add unique key(id)  ")
        # print 'execute ok'
        cache.set(cache_key,ptbl,0)
        return ptbl
    except:
        # import sys
        # print sys.exc_info()[1] + ': ' + print sys.exc_info()[1]
        return False


def createAuxClauseGroups(clause,params,mission,instrument,inst_clauses,inst_params,mission_clauses,mission_params):
    """ puts the clause and params into the proper grouping of aux-type clauses """
    if instrument:
        # this is an instrument param
        try:
            inst_clauses[instrument] += [clause]
            inst_params[instrument]  += [params]
        except KeyError:
            inst_clauses[instrument]  = [clause]
            inst_params[instrument]   = [params]
    else:
        # this is a mission param
        try:
            mission_clauses[mission] += [clause]
            mission_params[mission]  += [params]
        except KeyError:
            mission_clauses[mission]  = [clause]
            mission_params[mission]   = [params]

    return [inst_clauses,inst_params,mission_clauses,mission_params]


def gatherAuxClauses(inst_clauses,inst_params,inst_missions,mission_clauses,mission_params):

    """ creates a clause for each instrument group, join in any corresponding mission clauses """
    aux_clauses = {} # holds the parts of the where clause we will glue together with 'AND', base join types
    aux_params  = {} # holds the values to insert into parameterized %s placeholders, base join types

    combined_mission_clauses = {}
    combined_mission_params  = {}

    # combine mission clauses and params so that we have 1 combined clause and 1 set of params for each mission
    for mission in mission_clauses:
        combined_mission_clauses[mission] = ' and '.join(mission_clauses[mission])
        combined_mission_params[mission]  = [item for innerlist in mission_params[mission] for item in innerlist] # from [['this','that'],['this','that']] to ['this','that','this','that']
        if not inst_clauses:
            table = getQueryTable(mission,None);
            try:  # this just has to do with whether this is first time set or not:
                aux_clauses[table] += [combined_mission_clauses[mission]]
                aux_params[table]  += [combined_mission_params[mission]]
            except KeyError:
                aux_clauses[table]  = [combined_mission_clauses[mission]]
                aux_params[table]   = [combined_mission_params[mission]]

    for instrument,clauses in inst_clauses.items():
        this_mission = inst_missions[instrument]
        table = getQueryTable(this_mission,instrument);
        clause = ' and '.join(clauses)
        params = [item for innerlist in inst_params[instrument] for item in innerlist]
        try:  # if there is a mission clause corresponding to this instrument join it  in
            clause += " AND " + combined_mission_clauses[this_mission]
            # since we joined the clauses we must also join the params into the same list because we will call it by key later, must match clause key:
            params += combined_mission_params[this_mission]
        except KeyError: pass # no corresponding mission clauses
        try:
            aux_clauses[table] += [clause]
            aux_params[table]  += [params]
        except KeyError:
            aux_clauses[table]  = [clause]
            aux_params[table]   = [params]

    return [aux_clauses,aux_params]


# related = {'clauses':[], 'params':[], 'tables':[] }
def combineAllClauses(base_clauses,base_params,aux_clauses,aux_params, related):
    """ combine aux and base queries to make the one whole combined query and pram list """

    grand_unified_query = []
    grand_param_list    = []

    base_query = ''
    if len(base_clauses):
        base_query = ' and '.join(base_clauses)

    if len(related['clauses']):
        base_query += ' and '.join(related['clauses'])

    if not len(aux_clauses):
        # no funky aux clauses to deal with, just proceed normally
        query_lead = "select id from observations where ";
        grand_unified_query  = [query_lead + base_query]
        grand_param_list     = base_params
    else:
        # we have join_type = aux clauses: tie each aux clause together
        # with a copy of the entire base_query clause

        for table in aux_clauses:
            clauses = aux_clauses[table]

            i = 0
            for clause in clauses:
                big_clause = '(' + base_query + ' AND ' + clause + ')' if base_query else '(' + clause + ')'
                query      = '(select ' + table + '.id from ' + table + ' where ' + big_clause + ')'

                try:             grand_unified_query += [query]
                except KeyError: grand_unified_query  = [query]

                try:             grand_param_list += base_params   # add all base params
                except KeyError: grand_param_list  = base_params   # add all base params
                try:             grand_param_list += aux_params[table][i] # and then all aux param values for this param
                except KeyError: grand_param_list  = aux_params[table][i] # and then all aux param values for this param
                i+=1

    return [grand_unified_query,grand_param_list]


def buildWhereClause(param_name,value_list,more):

    """ builds an individual where clause for a given param/value list """

    # extracting passed dict 'more'
    form_type     = more['form_type']
    qtypes        = more['qtypes']
    special_query = more['special_query']
    selections    = more['selections']
    related_table_name = more['related_table_name']
    related_table_field_name = more['related_table_field_name']

    if related_table_name:
        # this should actually query a related table, so we CHANGE the param_name to that param! plus, I like UNICORNS
        param_name = related_table_name + "." + related_table_field_name

    # mult form type can be overriden by the user into a string type:
    if form_type in settings.MULT_FORM_TYPES:
        if qtypes in ['contains','ends','begins','excludes']:
            form_type = 'STRING'

    if form_type in settings.MULT_FORM_TYPES:
        if qtypes == 'range':  # user can override mult type queries with RANGE type
            (clause,params)  = simpleRangeQuery(param_name,value_list)
        else:
            (clause, params) = multQuery(param_name,value_list,qtypes)

    elif form_type == 'LONG':
        try:
            (clause,params) = longitudeQuery(selections,param_name)
        except KeyError:
            pass
            ############################## RETURN SOME ERROR TO THE FRONT END ?????????????????????? ##############

    elif form_type in ['TIME','RANGE']:
        try:
            (clause,params) = rangeQuery(selections,param_name,qtypes)
        except:
            invalid_times = findInvalidTimes(value_list)
            # print 'rangeQuery raised exception: ' + str(invalid_times)
            ############################## RETURN SOME ERROR TO THE FRONT END ?????????????????????? ##############

    elif form_type == 'STRING':
        if qtypes == 'range':  # user can override string type queries with RANGE type
            (clause,params)  = simpleRangeQuery(param_name,value_list)
        else:
            (clause, params) = stringQuery(param_name,value_list,qtypes)

    try:
        return [clause,params]
    except:
        raise Exception("no clause? no params? build where clause fails")


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
    return [' OR '.join(clauses), params]


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


def multQuery(param_name,value_list,qtypes):
    """ builds where clause for mult type queries """
    # this makes getMultName() below not choke, circular import issue? not sure.. but this fixes
    from metadata.views import getMultName

    mult_param = getMultName(param_name)
    model      = get_model('search',mult_param.title().replace('_',''))
    q_values   = model.objects.filter(label__in=value_list).values('id') # get the ids from the mult table that match these labels
    id_list    = [value for q in q_values for key,value in q.items()] # extracts the numeric ids obtained from the q_values query
    q          = connection.ops.quote_name(mult_param+'_id') + ' IN(' + ','.join(['%s' for v in value_list]) + ') ' # `mult_planet_id` IN (%s,%s...)
    return [q , id_list]


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

        # print 'hello ' + str(value_min) + ' ' + str(value_max) + ' ' + str(qtype) + ' ' + str(qtype[0])

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


def stringQuery(param_name,value_list, qtypes):
    """
    builds the where clause for a string type queries
    """
    str_q_list = [] # holds query clauses for this string search
    str_v_list = [] # holds parameterized values

    try:    str_qtypes[0] = qtypes[0]
    except: str_qtypes    = ['contains']       # default qtype, we don't force user to give us qtypes
    i=0  # each search param has a matching qtype in the qtypes list, keys match: ?note=Partial,SODIUM&qtypes-note=begins,contains'
    for value in value_list:
        try:
            qtype = qtypes[i]
        except:
            qtype = str_qtypes[0] # if user has only one value that's ok, use it for all params
        i+=1

        """ constructing clauses + hacking the parameterized values to add mysql wildcard chars """
        if    qtype  == 'contains': str_val = '%'+value+'%'
        elif  qtype  == 'ends':     str_val = '%'+value
        elif  qtype  == 'begins':   str_val = value+'%'
        elif  qtype  == 'matches':  str_val = value
        else: str_val  = '%'+value+'%'    # defaults to "contains"


        str_v_list.append(str_val)
        """
        elif qtype=='excludes':
            NOTE: this got very complicated when we start talkinga bout 'base' and 'aux' join types
                       so commenting it out for now, possible?
                       also removing the q_list & v_list param being passed to and returned from this function
                       as this was the only place that was needed
                       if this should be fixed know that it must alter the *entire* query string not just an OR clause.. right?
            # excludes are special, they get 'AND' joined in with the main query
            #    not OR joined in with the (string query)
            str_val = '%'+value+'%'
            q_list.append(connection.ops.quote_name(param_name) + " NOT LIKE %s ")
            v_list.append('%'+value+'%')
            continue
        """

        q = connection.ops.quote_name(param_name) + " LIKE %s "
        str_q_list.append(q)

    if str_q_list:         # could be empty if all we had was excludes
        q = "(" + ' OR '.join(str_q_list) + ")" # joined with ORs.. string in '%Jup%' OR string in '%Sat%' etc..
    else: q = ''

    return [q , str_v_list]




