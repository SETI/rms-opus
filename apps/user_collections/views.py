################################################
#
#   user_collections.views
#   django adds/removes opus_ids from the current collection
#   note to self: add time added to collectionTable for timeout
#
################################################ import settings
import settings
import json
from django.http import HttpResponse, Http404
from django.template import RequestContext
from django.views.decorators.cache import never_cache
from django.db import connection, DatabaseError
from django.shortcuts import render
from hurry.filesize import size as nice_file_size

from tools.app_utils import *
from user_collections.models import *
from paraminfo.models import ParamInfo
from search.models import ObsGeneral
from metrics.views import update_metrics

from tools.pdsfilestubs import *
import pdsfile

import logging
log = logging.getLogger(__name__)

#################
def get_args(request,**kwargs):
    """
    # Parse out the args from the slug.
        (action, opus_id, request_no, expected_request_no)

    """

    # collection and action are part of the url conf so you won't get in without one
    try:
        action = kwargs['action']
    except KeyError:
        msg = 'Page not found'
        return msg

    opus_id = request.GET.get('opus_id', False)
    request_no = request.GET.get('request', False)
    addrange = request.GET.get('addrange',False)

    if not opus_id and action != 'addall':
        try:
            opus_id = kwargs['opus_id']
        except KeyError:
            if addrange:
                opus_id = addrange
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

    return [action, opus_id, request_no, expected_request_no]

def get_product_types(opus_id_list):
    """Return the list of all product types associated with the opus_id_list."""
    product_types = {}
    if isinstance(opus_id_list,type(basestring)):
        opus_id_list = [opus_id_list]

    for opus_id in opus_id_list:
        pdsf = pdsfile.PdsFile.from_opus_id(opus_id)
        products = pdsf.opus_products()

        # Keep a running list of all products by type
        for (opus_type, list_of_sublists) in products.items():
            #flatten list_of_sublists FIRST
            flat_list = iter_flatten(list_of_sublists)
            product_types.setdefault(opus_type, []).extend(flat_list)
            #grab abs path at same time; make sure that types are distinct

    return product_types

def get_product_counts(product_types):
    # get count of each product type
    size = 0;
    count = 0;
    no_products = {}
    for product, sublist in product_types.iteritems():
        no_products[product] = len(sublist)
        for pdsf in sublist:
            abspath = pdsf.abspath
            size += pdsf.size_bytes
            count +=1

    # download_info, count and total size before zip
    size = nice_file_size(size)  # pretty display it

    return size, count, no_products


def get_collection_count(session_id):
    cursor = connection.cursor()
    sql = 'select count(*) from `collection_table` where session_id = %s'
    cursor.execute(sql, (session_id,))
    c = cursor.fetchone()[0]
    return c

def get_all_in_collection(request):
    """ returns list of opus_ids """
    # note this needs to move to downloads
    if not request.session.get('has_session'):
        return []
    else:
        session_id = request.session.session_key
        opus_ids = CollectionTable.objects.filter(session_id__in=session_id)
        return opus_ids

def get_collection_csv(request, fmt=None):
    """
        creates csv based on user query and selection columns
        defaults to response object
        or as first line and all data tuple object for fmt=raw
    """
    slugs = request.GET.get('cols')
    from results.views import getPage
    all_data = getPage(request, colls=True, colls_page='all')

    if fmt == 'raw':
        return slugs.split(","), all_data[2]
    else:
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="data.csv"'
        wr = csv.writer(response)
        wr.writerow(slugs.split(","))
        wr.writerows(all_data[2])
        return response

def add(opus_id_list, session_id):
    cursor = connection.cursor()
    if isinstance(opus_id_list, str):
        opus_id_list = [opus_id_list]
    values = [(session_id, opus_id) for opus_id in opus_id_list]
    sql = 'replace into `collection_table`' + ' (session_id, opus_id) values (%s, %s)'
    cursor.executemany(sql, values)

def remove(opus_id, session_id):
    cursor = connection.cursor()
    sql = 'delete from `collection_table`' + ' where opus_id = %s'
    cursor.execute(sql, (opus_id,))

def edit_collection_range(request, session_id):
    """
    the request will come in not as a single opus_id
    but as min and max opus_ids + a range in a search query

    there are two ways to refer to an obersrvation:
    opus_id - up to 80 char string, unique for any observations
            every obs table has a column for the opus_id <so you can join tables together>
    obs_general - `id` - integer (unique id) created during import process that is associated w/one opus_id
        joins on all other tables to obs_general_id - this is much faster <making opus_id redundant in other tables>

    """
    id_range = request.GET.get('addrange',False)
    if not id_range:
        return False; # "invalid opus_id pair"

    (min_id, max_id) = id_range.split(',')

    from results.views import *
    data = get_data(request,"raw")

    selected_range = []
    in_range = False  # loop has reached the range selected

    column_slugs = request.GET.get('cols',settings.DEFAULT_COLUMNS)

    opus_id_key = column_slugs.split(',').index('opus_id')

    # return HttpResponse(json.dumps(data['page']));
    for row in data['page']:

        opus_id = row[opus_id_key]

        if opus_id == min_id:
            in_range = True;

        if in_range:
            selected_range.append(opus_id)

        if in_range and (opus_id == max_id):

            # this is the last one, update the collection
            if action == 'addrange':
                add([rid for rid in selected_range], session_id)

    if not selected_range:
        log.error("edit_collection_range failed to find range " + id_range)

    return True


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

    (selections,extras) = urlToSearchParams(request.GET)
    query_table_name = getUserQueryTable(selections,extras)

    cursor = connection.cursor()
    coll_table_name = get_collection_table(session_id)
    sql = "replace into " + connection.ops.quote_name(coll_table_name) + \
          " (id, opus_id) select o.id, o.opus_id from obs_general o, " + connection.ops.quote_name(query_table_name) + \
          " s where o.id = s.id"
    cursor.execute(sql)
    return get_collection_count(session_id)


def get_collection_in_page(page, session_id):
    """ returns obs_general_ids in page that are also in user collection
        this is for views in results where you have to display the gallery
        and indicate which thumbnails are in cart """
    if not session_id:
        return

    cursor = connection.cursor()
    collection_in_page = []
    for p in page:
        opus_id = p[0]
        sql = 'select DISTINCT opus_id from `collection_table` where session_id = %s'
        cursor.execute(sql, (session_id,))
        row = cursor.fetchone()
        if row is not None:
            collection_in_page.append(opus_id)
    return collection_in_page

############################
def edit_collection(request, **kwargs):
    update_metrics(request)

    if not request.session.get('has_session'):
        request.session['has_session'] = True

    session_id = request.session.session_key

    args = get_args(request, **kwargs)
    if isinstance(args, list):
        (action, opus_id, request_no, expected_request_no) = args
    else:
        return HttpResponse(json.dumps({"err":args}))

    if action == 'add':
        add(opus_id, session_id)

    elif (action == 'remove'):
        remove(opus_id, session_id)

    elif (action in ['addrange','removerange']):
        edit_collection_range(request, session_id)

    elif (action == 'addall'):
        edit_collection_addall(request, **kwargs)

    collection_count = get_collection_count(session_id)

    json_data = {"count":collection_count, "request_no":request_no,}
    return HttpResponse(json.dumps(json_data))

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

    column_slugs = column_slugs.split(',')
    columns = []
    for slug in column_slugs:
        columns += [ParamInfo.objects.get(slug=slug).param_name()]
    offset = (page_no-1)*limit

    # collection
    if not request.session.get('has_session'):
        request.session['has_session'] = True
    if not request.session.session_key:
        request.session.save()
    session_id = request.session.session_key

    opus_ids = CollectionTable.objects.filter(session_id__in=session_id)
    opus_id_list = list(opus_ids)

    # all product types
    all_product_types = get_product_types(opus_id_list)
    download_size, download_count, product_counts = get_product_counts(all_product_types)

    # the image_links should come from the pdsf for each sublist, right now it's stubbed out
    image_links = get_image_links(all_product_types)

    # images and join with the collections table
    image_types = settings.IMAGE_TYPES
    image_count = len(image_links)

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
    where = "obs_general.opus_id = collection_table.opus_id"
    triggered_tables.append('collection_table')

    # bring in the  triggered_tables
    results = ObsGeneral.objects.extra(where=[where], tables=triggered_tables)
    results = results.values(*column_values)[offset:offset+limit]

    context = {
        "download_count": download_count,
        "download_size": download_size,
        "product_counts": product_counts,
        "image_types": image_types,
        "image_count": image_count,
    }

    return render(request, template, context)


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

@never_cache
def reset_session(request):
    """ this is hit when user clicks 'empty collection' """
    request.session.flush()
    request.session['has_session'] = True
    return HttpResponse("session reset")


def add_to_queue(request, request_no, action, opus_id):
    # just adding one request to the queue if its not already there

    queue = {}
    queue = request.session.get("queue", {})
    if request_no not in queue:
        queue[request_no] = [action, opus_id]

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
        (collection_name,action,opus_id) = get_queued(request, expected_request_no)
    """
    queue = request.session.get("queue", {})
    try:
        return queue[request_no]
    except KeyError:
        return False
