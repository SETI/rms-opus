import settings
from django.http import HttpResponse
from django.utils import simplejson
from django.template import RequestContext
from tools.app_utils import *
from results.views import *
from downloads.views import *

import logging
log = logging.getLogger(__name__)

def sleepy():
    ''' ***************************************** remove me ***************************************** '''
    ''' ***************************************** xxxxxx xx ***************************************** '''
    import time
    time.sleep(2);


def in_collections(request):
    """
    returns flat list of ring_obs_ids as found in all user collections, for indication when displaying in browse
    """
    if not request.session.get("all_collections"):
        return []

    all_ids = []
    for collection_name in request.session.get("all_collections"):
        if request.session.get(collection_name):
            for ring_obs_id in request.session.get(collection_name):
                all_ids.append(ring_obs_id)

    return list(set(all_ids)) # makes unique



def set_collection(request,collection_name='default'):
    try:
        s = UserCollections.objects.get(selections_hash=selections_hash,qtypes_hash=qtypes_hash,units_hash=units_hash,string_selects_hash=string_selects_hash)
    except UserSearches.DoesNotExist:
        s = UserSearches(selections_hash=selections_hash, selections_json=selections_json, qtypes=qtypes_json,qtypes_hash=qtypes_hash,units=units_json,units_hash=units_hash, string_selects=string_selects_json,string_selects_hash=string_selects_hash )
        s.save()

def get_collection(request, collection_name='default'):
    """
    returns list of ring_obs_ids in the current session user's collection
    """
    collection_name = 'collection__' + collection_name;
    collection = [] # collection is a list of ring_obs_ids
    if request.session.get(collection_name):
        collection = request.session.get(collection_name)
        return collection
    return False






def view_collection(request, collection_name, template="collections.html"):
    # return getData(request,'html', True)
    session_key = request.session.session_key

    # nav stuff - page | limit | order | columns | offset
    page_no = int(request.GET.get('page',1))
    limit = int(request.GET.get('limit',100))
    order = int(request.GET.get('order',150))
    column_slugs = request.GET.get('cols',settings.DEFAULT_COLUMNS)

    from results.views import *  # circulosity

    column_slugs = column_slugs.split(',')
    columns = []
    for slug in column_slugs:
        columns += [ParamInfo.objects.get(slug=slug).param_name()]
    offset = (page_no-1)*limit

    # collection
    collection = get_collection(request, collection_name)
    files = getFiles(collection, "raw")
    product_types = Files.objects.all().values('product_type').distinct()

    # downlaod_info
    from downloads.views import *
    download = get_download_info(request,collection)

    download_size = download['size']
    download_count = download['count']

    # images
    images = Image.objects.filter(ring_obs_id__in=collection)
    image_types = dict([(i,0) for i in settings.IMAGE_TYPES])   # dict with image_types as keys and all values set to zero
    image_count = len(images)

    # product files
    product_counts = dict([(i,0) for i in [p['product_type'] for p in product_types]]) # a dictionary with product_Type names as keys and all values set to zero
    for ring_obs_id in files:
        for ptype in files[ring_obs_id]:
            product_counts[ptype] = product_counts[ptype] + 1

    # return HttpResponse(str(simplejson.dumps(product_types)))
    # return HttpResponse(files['data']['S_IMG_CO_ISS_1633303611_W'])

    # a page of results for the frontend
    """
    HOUSTON WE HAVE A PROBLEM
    """
    # ok now that we have everything from the url et stuff from db

    # this is the thing you pass to django model via values()
    # so we have the table names a bit to get what django wants:
    column_values = []
    for param_name in columns:
        table_name = param_name.split('.')[0]
        if table_name == 'obs_general':
            column_values.append(param_name.split('.')[1])
        else:
            column_values.append(param_name.split('.')[0].lower().replace('_','') + '__' + param_name.split('.')[1])

    # figure out what tables do we need to join in and build query
    triggered_tables = list(set([t.split('.')[0] for t in columns]))
    try:
        triggered_tables.remove('obs_general')
    except ValueError:
        pass  # obs_general table wasn't in there for whatever reason


    # bring in the  triggered_tables
    results = ObsGeneral.objects.extra(tables=triggered_tables)

    # and apply the filtering
    results = results.filter(ring_obs_id__in=collection).values(*column_values)[offset:offset+limit]

    page_ids = [o['ring_obs_id'] for o in results]
    return render_to_response(template,locals(), context_instance=RequestContext(request))





def collection_status(request, **kwargs):
    collection_name = 'collection__' + kwargs['collection']
    collection = []
    if request.session.get(collection_name):
        collection = request.session.get(collection_name)

    try:
        expected_request_no =  request.session['expected_request_no']
    except KeyError:
        expected_request_no = 1

    return HttpResponse(simplejson.dumps({"count":len(collection), "expected_request_no": expected_request_no }))



def check_collection_args(request,**kwargs):
    """
    # this just checks that we have all we need to process an edit_collection
    # and if we don't it returns the error msg as string
    checkArgs = check_collection_args(request, **kwargs)
    if type(checkArgs) == 'string':
        return HttpResponse(checkArgs)
    else:
        (action, collection_name, ring_obs_id, request_no, expected_request_no) = check_collection_args(request, **kwargs)
    """
    if request.is_ajax() == False:
        return HttpResponseNotFound('<h1>Page not found</h1>')

    # collection and action are part of the url conf so you won't get in without one
    try:
        action = kwargs['action']
        collection_name = 'collection__' + kwargs['collection']
    except KeyError:
        return HttpResponseNotFound('<h1>Page not found</h1>')

    ring_obs_id = request.GET.get('ringobsid', False)
    request_no = request.GET.get('request', False)
    addrange = request.GET.get('addrange',False)

    if not ring_obs_id:
        try:
            ring_obs_id = kwargs['ring_obs_id']
        except KeyError:
            if addrange:
                ring_obs_id = addrange
            else:
                return "No Observations specified"

    if not request_no:
        try:
            request_no = kwargs['request_no']
        except KeyError:
            return 'no request number received'

    request_no = int(request_no)

    expected_request_no = 1
    if request.session.get('expected_request_no'):
        expected_request_no =  request.session['expected_request_no']

    return [action, collection_name, ring_obs_id, request_no, expected_request_no]


def is_odd(num):
        return num & 1 and True or False

def reset_sess(request):
    try:
        del request.session['queue']
        request.session['expected_request_no'] = 1
    except KeyError:
        pass

    try:
        del request.session['collection__default']
        request.session['test'] = False
    except KeyError:
        pass

    return HttpResponse("session reset")


def edit_collection(request, **kwargs):
    """
    return reset_sess(request);
    """
    checkArgs = check_collection_args(request, **kwargs)

    if type(checkArgs).__name__ == 'list':
        (action, collection_name, ring_obs_id, request_no, expected_request_no) = checkArgs
    else:
        return HttpResponse(simplejson.dumps({"err":checkArgs}))

    # just add this request to the queue, every request gets queued
    add_to_queue(request, request_no, collection_name, action, ring_obs_id)


    # now look for the mext expected request in the queue
    if get_queued(request, expected_request_no):
        # found the next expected request in the queue
        (collection_name,action,ring_obs_id) = get_queued(request, expected_request_no)
    else:
        # the expected request has not yet arrived, do nothing
        return HttpResponse(simplejson.dumps({"err":"waiting"}))
        """
        # testing stuff:
        msg = "doing nothing: expected request not received yet! " + str(expected_request_no)
        q = request.session.get("queue") if request.session.get("queue") else ''
        return HttpResponse(simplejson.dumps({"msg":msg, "queue": q}))
        """

    collection = []
    if request.session.get(collection_name):
        collection = request.session.get(collection_name)


    all_collections = []
    if request.session.get("all_collections"):
        all_collections = request.session.get("all_collections")
    if collection_name not in all_collections:
        all_collections.append(collection_name)

    if action == 'add':
        if ring_obs_id in collection: # if it's already there, remove it and add it again, user may be futzing with order
            collection.remove(ring_obs_id)
        collection.append(ring_obs_id)
    elif (action == 'remove') & (ring_obs_id in collection):
        collection.remove(ring_obs_id)
    elif (action in ['addrange','removerange']):
        collection = edit_collection_range(request, **kwargs)
        # return collection
        if not collection:
            return HttpResponse("failfail<br>")

    next_request_no = expected_request_no + 1
    remove_from_queue(request, expected_request_no) # we are handling this one now

    request.session['expected_request_no'] = next_request_no
    request.session[collection_name] = collection
    request.session['all_collections'] = all_collections

    # so we did the next expected, is there another subsequent to that?
    if get_queued(request, next_request_no):
        (collection_name,action,ring_obs_id) = get_queued(request, next_request_no)
        next = {"collection":kwargs['collection'], "action":action, "ring_obs_id": ring_obs_id, "request_no":next_request_no}
        return edit_collection(request, **next)

    """
    try:
        json = {"msg":"yay!","count":len(collection), "collection": ', '.join(collection)}
    except:
        json = collection
    """
    json = {"err":False, "count":len(collection), "request_no":expected_request_no}
    return HttpResponse(simplejson.dumps(json))




def edit_collection_range(request, **kwargs):

    (action, collection_name, ring_obs_id, request_no, expected_request_no) = check_collection_args(request, **kwargs)

    collection = []
    if request.session.get(collection_name):
        collection = request.session.get(collection_name)

    id_range = request.GET.get('addrange',False)
    if not id_range:
        return False; # "invalid ringobsid pair"

    (min_id, max_id) = id_range.split(',')
    (selections,extras) = urlToSearchParams(request.GET)

    from results.views import *
    data = getData(request,"raw")
    selected_range = []
    in_range = False  # loop has reached the range selected

    # return HttpResponse(simplejson.dumps(data['page']));
    for row in data['page']:
        ring_obs_id = row[0]
        if ring_obs_id == min_id:
            in_range = True;
        if in_range:
            selected_range.append(ring_obs_id)
        if in_range & (ring_obs_id == max_id):
            # this is the last one, update the collection
            if action == 'addrange':
                for ring_obs_id in selected_range:
                    if ring_obs_id in collection:
                        collection.remove(ring_obs_id) # if it's already there, remove it and add it again, user may be futzing with order
                collection += selected_range
            if action == 'removerange':
                for ring_obs_id in selected_range:
                    collection.remove(ring_obs_id)

    if len(collection):
        return collection

    return False



def add_to_queue(request, request_no, collection_name, action, ring_obs_id):
    # just adding one request to the queue if its not already there
    queue = {}
    if request.session.get("queue"):
        queue = request.session.get("queue")
    if request_no not in queue:
        queue[request_no] = [collection_name, action, ring_obs_id]
    request.session["queue"] = queue
    return True


def remove_from_queue(request, request_no):
    queue = {}
    if not request.session.get("queue"):
        queue = request.session.get("queue")
    if request_no in queue:
        del queue[request_no]
        request.session["queue"] = queue
    return True


def get_queued(request, request_no):
    """
    if get_queued(request, expected_request_no):
        (collection_name,action,ring_obs_id) = get_queued(request, expected_request_no)
    """
    queue = {}
    if request.session.get("queue"):
        queue = request.session.get("queue")

    try:
        return queue[request_no]
    except KeyError:
        return False


# avoiding a circular dependency, even James Bennett does this! http://is.gd/TGblFO
# well ok I moved to the end of module because it's needed in 2 methods here :0
from search.views import *
from results.views import *
from downloads.views import *