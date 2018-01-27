################################################
#
#   user_collections.views
#
################################################ import settings
import settings
import json
from django.http import HttpResponse, Http404
from django.template import RequestContext
from tools.app_utils import *
from results.views import *
from downloads.views import *
from metrics.views import update_metrics
from django.views.decorators.cache import never_cache
from django.db import connection, DatabaseError
from django.shortcuts import render

import logging
log = logging.getLogger(__name__)

def get_all_in_collection(request):
    if not request.session.get('has_session'):
        return []
    else:
        cursor = connection.cursor()
        session_id = request.session.session_key
        coll_table_name = get_collection_table(session_id)
        sql = 'select ring_obs_id from ' + connection.ops.quote_name(coll_table_name)
        cursor.execute(sql)
        ring_obs_ids = [n[0] for n in cursor.fetchall()]
        return ring_obs_ids


def get_collection_table(session_id):
    """
    returns collection table name and if one doesn't exist create a new one
    """
    if not session_id:
        return False

    cursor = connection.cursor()
    coll_table_name = 'colls_' + session_id
    try:
        sql = 'select ring_obs_id from ' + connection.ops.quote_name(coll_table_name) + ' limit 1'
        cursor.execute(sql)
    except DatabaseError:
        sql = 'create table ' + connection.ops.quote_name(coll_table_name) + ' like user_collections_template';
        cursor.execute(sql)

    return coll_table_name

def bulk_add_to_collection(ring_obs_id_list, session_id):
    cursor = connection.cursor()
    if type(ring_obs_id_list).__name__ == 'str':
        ring_obs_id_list = [ring_obs_id_list]
    coll_table_name = get_collection_table(session_id)
    placeholders = ['(%s)' for i in range(len(ring_obs_id_list))]
    values_str = ','.join(placeholders)
    sql = 'replace into ' + connection.ops.quote_name(coll_table_name) + ' (ring_obs_id) values %s' % values_str
    cursor.execute(sql, tuple(ring_obs_id_list))

def add_to_collection(ring_obs_id, session_id):
    cursor = connection.cursor()
    coll_table_name = get_collection_table(session_id)
    # first remove
    remove_from_collection(ring_obs_id, session_id)
    sql = 'replace into ' + connection.ops.quote_name(coll_table_name) + ' (ring_obs_id) values (%s)'
    cursor.execute(sql, (ring_obs_id,))

def remove_from_collection(ring_obs_id, session_id):
    cursor = connection.cursor()
    coll_table_name = get_collection_table(session_id)
    sql = 'delete from ' + connection.ops.quote_name(coll_table_name) + ' where ring_obs_id = %s'
    cursor.execute(sql, (ring_obs_id,))

def get_collection_in_page(page, session_id):
    """ returns obs_general_ids in page that are also in user collection
        this is for views in results where you have to display the gallery
        and indicate which thumbnails are in cart """
    if not session_id:
        return

    cursor = connection.cursor()
    coll_table_name = get_collection_table(session_id)
    collection_in_page = []
    for p in page:
        ring_obs_id = p[0]
        sql = 'select ring_obs_id from ' + connection.ops.quote_name(coll_table_name) + ' where ring_obs_id = %s'
        cursor.execute(sql, (ring_obs_id,))
        row = cursor.fetchone()
        if row is not None:
            collection_in_page.append(ring_obs_id)
    return collection_in_page

def get_collection_count(session_id):
    cursor = connection.cursor()
    coll_table_name = get_collection_table(session_id)
    sql = 'select count(*) from ' + connection.ops.quote_name(coll_table_name)
    cursor.execute(sql)
    c = cursor.fetchone()[0]
    return c

def edit_collection(request, **kwargs):
    update_metrics(request)
    """
    edits a single ring_obs_id in a user collection (user "selections")
    # edits?
    """
    if not request.session.get('has_session'):
        request.session['has_session'] = True

    session_id = request.session.session_key

    checkArgs = check_collection_args(request, **kwargs)
    if type(checkArgs).__name__ == 'list' and checkArgs:
        (action, ring_obs_id, request_no, expected_request_no) = checkArgs
    else:
        return HttpResponse(json.dumps({"err":checkArgs}))

    # just add this request to the queue, every request gets queued
    add_to_queue(request, request_no, action, ring_obs_id)

    """
    # todo
    turning this off for now, we will get the queue of whatever request_no is passed
    to us, without checking against what is expected_request_no
    by turning this off we are at risk of ajax race conditions
    but it's breaking something and no time for it right now
    Issue is here:
    https://bitbucket.org/ringsnode/opus2/issue/75/collections-downloads-majorly-broken
    # todo:
    # now look for the next expected request in the queue
    if get_queued(request, expected_request_no):
        # found the next expected request in the queue
        (request,action,ring_obs_id) = get_queued(request, expected_request_no)
    else:
        # the expected request has not yet arrived, do nothing
        return HttpResponse(json.dumps({"err":"waiting"}))
    """
    # instead of the above we are doing this:
    (action, ring_obs_id) = get_queued(request, request_no)

    # redux: these will be not so simple sadly, they will insert or delete from
    # the colleciton table..
    if action == 'add':
        add_to_collection(ring_obs_id, session_id)

    elif (action == 'remove'):
        remove_from_collection(ring_obs_id, session_id)

    elif (action == 'addall'):
        collection_count = edit_collection_addall(request, **kwargs)

    elif (action in ['addrange','removerange']):
        collection_count = edit_collection_range(request, **kwargs)

    remove_from_queue(request, request_no)

    """
    try:
        json = {"msg":"yay!","count":len(collection), "collection": ', '.join(collection)}
    except:
        json = collection
    """
    collection_count = get_collection_count(session_id)

    json_data = {"err":False, "count":collection_count, "request_no":request_no}

    return HttpResponse(json.dumps(json_data))

def edit_collection_addall(request, **kwargs):
    """
    add the entire result set to the collection cart

    This may be turned off. The way to turn this off is:

    - comment out html link in apps/ui/templates/browse_headers.html
    - add these lines below:

            # turn off this functionality
            log.debug("edit_collection_addall is currently turned off. see apps/user_collections.edit_collection_addall")
            return  # this thing is turned off for now


    The reason is it needs more testing, but this branch makes a big
    efficiency improvements to the way downloads are handled, and fixes
    some things, so I wanted to merge it into master

    Things that needs further exploration:
    This functionality provides no checks on how large a cart can be.
    There needs to be some limit.
    It doesn't hide the menu link when the result count is too high.
    And what happens when it bumps against the MAX_CUM_DOWNLOAD_SIZE.
    The functionality is there but these are questions!

    To bring this functionality back for testing do the folloing:
        - uncomment the "add all to cart" link in apps/ui/templates/browse_headers.html
        - comment out the 2 lines below in this function

    """
    # turn off this functionality
    log.error("edit_collection_addall is currently unavailable. see user_collections.edit_collection_addall()")
    return  # this thing is turned off for now

    update_metrics(request)
    session_id = request.session.session_key
    colls_table_name = get_collection_table(session_id)

    (selections,extras) = urlToSearchParams(request.GET)
    query_table_name = getUserQueryTable(selections,extras)

    cursor = connection.cursor()
    coll_table_name = get_collection_table(session_id)
    sql = "replace into " + connection.ops.quote_name(coll_table_name) + \
          " (id, ring_obs_id) select o.id, o.ring_obs_id from obs_general o, " + connection.ops.quote_name(query_table_name) + \
          " s where o.id = s.id"
    cursor.execute(sql)
    return get_collection_count(session_id)


def edit_collection_range(request, **kwargs):
    update_metrics(request)
    """
    the request will come in not as a single ring_obs_id
    but as min and max ring_obs_ids + a range in a search query

    """
    if not request.session.get('has_session'):
        request.session['has_session'] = True

    session_id = request.session.session_key
    colls_table_name = get_collection_table(session_id)
    (action, ring_obs_id, request_no, expected_request_no) = check_collection_args(request, **kwargs)

    id_range = request.GET.get('addrange',False)
    if not id_range:
        return False; # "invalid ringobsid pair"

    (min_id, max_id) = id_range.split(',')
    (selections,extras) = urlToSearchParams(request.GET)

    from results.views import *
    data = getData(request,"raw")
    selected_range = []
    in_range = False  # loop has reached the range selected

    column_slugs = request.GET.get('cols',settings.DEFAULT_COLUMNS)

    ring_obs_id_key = column_slugs.split(',').index('ringobsid')

    # return HttpResponse(json.dumps(data['page']));
    for row in data['page']:

        ring_obs_id = row[ring_obs_id_key]

        if ring_obs_id == min_id:
            in_range = True;

        if in_range:
            selected_range.append(ring_obs_id)

        if in_range & (ring_obs_id == max_id):

            # this is the last one, update the collection
            if action == 'addrange':
                bulk_add_to_collection([rid for rid in selected_range], session_id)

    if not selected_range:
        log.error("edit_collection_range failed to find range " + id_range)
        log.error(selections)

    return get_collection_count(session_id)


@never_cache
def view_collection(request, collection_name, template="collections.html"):
    """ the collection tab http endpoint!
        returns render(request, template,locals())
        template="collections.html"
        the information it returns about product types and files does not
        relect user filters such as  product types and preview images
        it returns all product types and all preview images in order to draw the page
        the highlighting of user selected preview and product type selections are handled client side
    """
    update_metrics(request)

    # nav stuff - page | limit | columns | offset
    page_no = int(request.GET.get('page',1))
    limit = int(request.GET.get('limit',100))
    column_slugs = request.GET.get('cols',settings.DEFAULT_COLUMNS)
    previews_str = request.GET.get('previews', None)

    previews = []
    if previews_str:
        previews = previews_str.split(',')

    from results.views import *  # circulosity

    column_slugs = column_slugs.split(',')
    columns = []
    for slug in column_slugs:
        columns += [ParamInfo.objects.get(slug=slug).param_name()]
    offset = (page_no-1)*limit

    # collection
    if not request.session.get('has_session'):
        request.session['has_session'] = True
    session_id = request.session.session_key
    colls_table_name = get_collection_table(session_id)

    # images and join with the collections table
    where   = "images.ring_obs_id = " + connection.ops.quote_name(colls_table_name) + ".ring_obs_id"
    images = Image.objects
    images = images.extra(where=[where], tables=[colls_table_name])

    image_types = settings.IMAGE_TYPES
    image_count = len(images)  # todo: huh.

    # all product types
    all_product_types = Files.objects.all().values('product_type').distinct()
    # product files
    # for this we want the list of all possible product types relevant for this dataset
    # todo: this is really inefficient, another place that large carts are going to be unhappy
    product_counts = dict([(i,0) for i in [p['product_type'] for p in all_product_types]]) # a dict with product_type names as keys
                                                                                           # and all values set to zero
                                                                                           # for holding a count of each product type
    # get count of each product type
    where = "files.ring_obs_id = " + connection.ops.quote_name(colls_table_name) + ".ring_obs_id"
    product_counts_query = Files.objects.extra(where=[where], tables=[colls_table_name]).values("product_type").annotate(Count("product_type"))
    product_counts_nonzero = {i['product_type']: i['product_type__count'] for i in product_counts_query}
    # update a product_count array with the non-zero counts
    for product_type, pcount in product_counts_nonzero.items():
        product_counts[product_type] = pcount

    # download_info, count and total size before zip
    from downloads.views import get_download_info
    product_types = [ptype for ptype, count in product_counts.items()]
    download_size, download_count =  get_download_info(product_types, previews, colls_table_name)
    download_size = nice_file_size(download_size)  # pretty display it

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

    # set up the where clause to join with the rest of the tables
    where = "obs_general.ring_obs_id = " + connection.ops.quote_name(colls_table_name) + ".ring_obs_id"
    triggered_tables.append(colls_table_name)

    # bring in the  triggered_tables
    results = ObsGeneral.objects.extra(where=[where], tables=triggered_tables)
    results = results.values(*column_values)[offset:offset+limit]

    page_ids = [o['ring_obs_id'] for o in results]

    return render(request, template,locals())


@never_cache
def collection_status(request, collection_name='default'):
    """
    #todo this method needs tests
    """
    update_metrics(request)

    expected_request_no = 1
    if not request.session.get('has_session'):
        count = 0
    else:
        session_id = request.session.session_key
        count = get_collection_count(session_id)

    try:
        expected_request_no =  request.session['expected_request_no']
    except KeyError:
        pass  # leave xpected_request_no = 1

    return HttpResponse(json.dumps({"count":count, "expected_request_no": expected_request_no }))


def check_collection_args(request,**kwargs):
    """
    # this just checks that we have all we need to process an edit_collection
    # and if we don't it returns the error msg as string
    checkArgs = check_collection_args(request, **kwargs)
    if type(checkArgs) == 'string':
        return HttpResponse(checkArgs)
    else:
        (action, ring_obs_id, request_no, expected_request_no) = check_collection_args(request, **kwargs)
    """

    # collection and action are part of the url conf so you won't get in without one
    try:
        action = kwargs['action']
    except KeyError:
        msg = 'Page not found'
        return msg

    ring_obs_id = request.GET.get('ringobsid', False)
    request_no = request.GET.get('request', False)
    addrange = request.GET.get('addrange',False)

    if not ring_obs_id and action != 'addall':
        try:
            ring_obs_id = kwargs['ring_obs_id']
        except KeyError:
            if addrange:
                ring_obs_id = addrange
            else:
                msg = "No Observations specified"
                return msg

    if not request_no:
        try:
            request_no = kwargs['request_no']
        except KeyError:
            msg = 'no request number received'
            return msg

    request_no = int(request_no)

    expected_request_no = 1
    if request.session.get('expected_request_no'):
        expected_request_no =  request.session['expected_request_no']

    return [action, ring_obs_id, request_no, expected_request_no]


def is_odd(num):
        return num & 1 and True or False

@never_cache
def reset_sess(request):
    """ this is hit when user clicks 'empty collection' """
    request.session.flush()
    request.session['has_session'] = True
    return HttpResponse("session reset")


def add_to_queue(request, request_no, action, ring_obs_id):
    # just adding one request to the queue if its not already there

    queue = {}
    queue = request.session.get("queue", {})
    if request_no not in queue:
        queue[request_no] = [action, ring_obs_id]

    request.session["queue"] = queue
    return True


def remove_from_queue(request, request_no):
    """ delete from queue, does not return item
        for when a queued request is finished being processed """
    if request_no in request.session["queue"]:
        del request.session["queue"][request_no]
    return True


def get_queued(request, request_no):
    """ get the next request in queue
        if get_queued(request, expected_request_no):
        (collection_name,action,ring_obs_id) = get_queued(request, expected_request_no)
    """
    queue = request.session.get("queue", {})
    try:
        return queue[request_no]
    except KeyError:
        return False


# avoiding a circular dependency, even James Bennett does this okayyyy! http://is.gd/TGblFO
# well ok I moved to the end of module because it's needed in 2 methods here o_0
from search.views import *
from results.views import *
from downloads.views import *
