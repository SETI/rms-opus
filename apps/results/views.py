################################################
#
#   results.views
#
################################################
import settings
import json
from django.http import Http404
from django.shortcuts import render_to_response
from django.utils.datastructures import SortedDict
from django.db.models import get_model
from search.views import *
from search.models import *
from results.models import *
from paraminfo.models import *
from metadata.views import *
from user_collections.views import *
from tools.app_utils import *
from django.views.decorators.cache import never_cache

import logging
log = logging.getLogger(__name__)

def getData(request,fmt):
    """
    a page of results for a given search
    """
    [page_no, limit, page, page_ids, order] = getPage(request)

    checkboxes = True if (request.is_ajax()) else False

    slugs = request.GET.get('cols',settings.DEFAULT_COLUMNS)
    if not slugs: slugs = settings.DEFAULT_COLUMNS  # i dunno why this is necessary

    labels = []
    for slug in slugs.split(','):
        labels += [ParamInfo.objects.get(slug=slug).label_results]
    labels = labels.insert(0, "add") if (request.is_ajax()) else labels  # adds a column for checkbox add-to-collections


    from user_collections.views import *

    collection = get_collection(request, "default")

    data = {'page_no':page_no, 'limit':limit, 'page':page, 'count':len(page)}

    return responseFormats(data,fmt,template='data.html', labels=labels,checkboxes=checkboxes, collection=collection, order=order)

def getDetail(request,ring_obs_id,fmt):
    """
    results for a single observation
    all the data, in categories

    """
    if not fmt: fmt = 'json'
    if not ring_obs_id: return Http404


    if fmt == 'html':
        from ui.views import getDetailPage
        return getDetailPage(request, ring_obs_id=ring_obs_id, fmt=fmt)

    try:
        col_slugs = request.GET.get('cols', False)
    except AttributeError:
        col_slugs = ''
        pass  # no request, prolly me a the shell

    if col_slugs:
        col_slugs = col_slugs.split(',')

    data = SortedDict({})

    # find all the tables (categories) this observation belongs to,
    all_tables = TableName.objects.filter(display='Y')

    # now find all params and their values in each of these tables:
    for table in all_tables:
        label = table.label
        table_name = table.table_name
        model_name = ''.join(table_name.title().split('_'))
        table_model = get_model('search', model_name)

        if not col_slugs:
            all_params = [param.name for param in ParamInfo.objects.filter(category_name=table_name, display_results=1)]
        else:
            all_params = []
            for slug in col_slugs:
                param_name = ParamInfo.objects.get(slug=slug).param_name()

                if table_name == param_name.split('.')[0]:
                    all_params.append(param_name.split('.')[1])

        if all_params:
            try:
                results = table_model.objects.filter(ring_obs_id=ring_obs_id).values(*all_params)[0]
                data[label] = results
            except AttributeError: pass  # no results found in this table, move along
            except IndexError: pass  # no results found in this table, move along


    if fmt == 'json':
        return HttpResponse(json.dumps(data), content_type="application/json")
    if fmt == 'raw':
        return data


def get_triggered_tables(selections, extras = {}):
    """
    this looks at user request and returns triggered tables
    always returns the settings.BASE_TABLES
    """
    if not selections:
        return sorted(settings.BASE_TABLES)

    # look for cache:
    cache_no = getUserQueryTable(selections,extras)
    cache_key = 'triggered_tables_' + str(cache_no)
    if (cache.get(cache_key)):
        return sorted(cache.get(cache_key))

    # first add the base tables
    triggered_tables = [t for t in settings.BASE_TABLES]
    query_result_table = getUserQueryTable(selections,extras)

    # now see if any more tables are triggered from query
    queries = {}  # keep track of queries
    for partable in Partable.objects.all():
        # we are joining the results of a user's query - the single column table of ids
        # with the trigger_tab listed in the partable,
        trigger_tab = partable.trigger_tab
        trigger_col = partable.trigger_col
        trigger_val = partable.trigger_val
        partable = partable.partable


        if partable in triggered_tables:
            continue  # already triggered, no need to check

        # get query
        # did we already do this query?

        if trigger_tab + trigger_col in queries:
            results = queries[trigger_tab + trigger_col]
        else:
            trigger_model = get_model('search', ''.join(trigger_tab.title().split('_')))
            results = trigger_model.objects
            if query_result_table:
                if trigger_tab == 'obs_general':
                    where   = trigger_tab + ".id = " + query_result_table + ".id"
                else:
                    where   = trigger_tab + ".obs_general_id = " + query_result_table + ".id"
                results = results.extra(where=[where], tables=[query_result_table])
            results = results.distinct().values(trigger_col)
            queries.setdefault(trigger_tab + trigger_col, results)

        if (len(results) == 1) and (unicode(results[0][trigger_col]) == trigger_val):
            # we has a triggered table
            triggered_tables.append(partable)

        # surface geometry have multiple targets per observation
        # so we just want to know if our val is in the result (not the only result)
        if 'obs_surface_geometry.target_name' in selections:
            if trigger_tab == 'obs_surface_geometry' and trigger_val == selections['obs_surface_geometry.target_name'][0]:
                if trigger_val in [r['target_name'] for r in results]:
                    triggered_tables.append(partable)

    # now hack in the proper ordering of tables
    final_table_list = []
    for table in TableName.objects.filter(table_name__in=triggered_tables).values('table_name'):
        final_table_list.append(table['table_name'])

    cache.set(cache_key, final_table_list, 0)

    return sorted(final_table_list)


# this should return an image for every row..

@never_cache
def getImages(request,size,fmt):
    """
    this returns rows from images table that correspond to request
    some rows will not have images, this function doesn't return 'image_not_found' information
    if a row doesn't have an image you get nothing. you lose. good day sir. #fixme #todo

    """
    alt_size = request.GET.get('alt_size','')
    columns = request.GET.get('cols',settings.DEFAULT_COLUMNS)

    try:
        [page_no, limit, page, page_ids, order] = getPage(request)
    except TypeError:  # getPage returns False
        return Http404

    log.debug('got page of length ' + str(len(page_ids)))
    log.debug(page_ids)
    image_links = Image.objects.filter(ring_obs_id__in=page_ids)

    if not image_links:
        log.error('no image found for:')
        log.error(page_ids[:50])

    # print page_ids
    if alt_size:
        image_links = image_links.values('ring_obs_id',size,alt_size)
    else:
        image_links = image_links.values('ring_obs_id',size)

    # add the base_path to each image
    all_sizes = ['small','thumb','med','full']
    for k, im in enumerate(image_links):
        for s in all_sizes:
            if s in im:
                image_links[k][s] = get_base_path_previews(im['ring_obs_id']) + im[s]

    # to preserve the order of page_ids as lamely as possible :P
    ordered_image_links = []
    for ring_obs_id in page_ids:
        found = False
        for link in image_links:
            if ring_obs_id == link['ring_obs_id']:
                found = True
                ordered_image_links.append(link)
        if not found:
            # return the thumbnail not found link
            ordered_image_links.append({size:settings.THUMBNAIL_NOT_FOUND, 'ring_obs_id':ring_obs_id})

    image_links = ordered_image_links

    all_collections = get_collection(request, "default")

    # find which are in collections, mark unfound images 'not found'
    for image in image_links:
        image['img'] = image[size] if image[size] else 'not found'
        if all_collections:
            from user_collections.views import *
            if image['ring_obs_id'] in all_collections:
                image['in_collection'] = True

    path = settings.IMAGE_HTTP_PATH

    if (request.is_ajax()):
        template = 'gallery.html'
    else: template = 'image_list.html'

    # print image_links
    return responseFormats({'data':[i for i in image_links]},fmt, size=size, path=path, alt_size=alt_size, columns_str=columns.split(','), all_collections=all_collections, template=template, order=order)


def get_base_path_previews(ring_obs_id):
    # find the proper volume_id to pass to the Files table before asking for file_path
    # (sometimes the Files table has extra entries for an observation with funky paths)
    try:
        volume_id = ObsGeneral.objects.filter(ring_obs_id=ring_obs_id)[0].volume_id
    except IndexError:
        return

    file_path = Files.objects.filter(ring_obs_id=ring_obs_id, volume_id=volume_id)[0].base_path

    return '/'.join(file_path.split('/')[-2:])


def getImage(request,size='med', ring_obs_id='',fmt='mouse'):      # mouse?
    """
    size = thumb, small, med, full
    return ring_obs_id + ' ' + size

    return HttpResponse(img + "<br>" + ring_obs_id + ' ' + size +' '+ fmt)
    """
    img = Image.objects.filter(ring_obs_id=ring_obs_id).values(size)[0][size]
    path = settings.IMAGE_HTTP_PATH + get_base_path_previews(ring_obs_id)
    return responseFormats({'data':[{'img':img, 'path':path}]}, fmt, size=size, path=path, template='image_list.html')

def file_name_cleanup(base_file):
    base_file = base_file.replace('.','/')
    base_file = base_file.replace(':','/')
    base_file = base_file.replace('[','/')
    base_file = base_file.replace(']','/')
    base_file = base_file.replace('.','/')
    base_file = base_file.replace('//','/')
    base_file = base_file.replace('///','/')
    return base_file


# loc_type = path or url
def getFilesAPI(request,ring_obs_id='',fmt='raw', loc_type="url"):

    product_types = request.GET.get('types',[])
    images = request.GET.get('previews',[])

    if request and request.GET and not ring_obs_id:

        # no ring_obs_id passed, get files from search results
        (selections,extras) = urlToSearchParams(request.GET)
        page  = getData(request,'raw')['page']
        if not len(page):
            return False
        ring_obs_id = []
        for p in page:
            ring_obs_id.append(p[0])

    return getFiles(ring_obs_id, fmt=fmt, loc_type=loc_type, product_types=product_types, previews=images)



# loc_type = path or url
def getFiles(ring_obs_id, fmt=None, loc_type=None, product_types=None, previews=None):

    if not fmt:
        fmt = 'raw'
    if not loc_type:
        loc_type = 'url'
    if not product_types:
        product_types = []
    if not previews:
        previews = []

    if ring_obs_id:
        if type(ring_obs_id) is unicode or type(ring_obs_id).__name__ == 'str':
            ring_obs_ids = [ring_obs_id]
        else:
            ring_obs_ids = ring_obs_id
    else:
        log.error('404: no files found for ' + str(ring_obs_id))
        return False

    file_names = {}

    if loc_type == 'url':
        path = settings.FILE_HTTP_PATH
    else:
        path = settings.FILE_PATH

    for ring_obs_id in ring_obs_ids:

        file_names[ring_obs_id] = {}

        files_table_rows = Files.objects.filter(ring_obs_id=ring_obs_id)

        for f in files_table_rows:

            file_extensions = []
            try:
                volume_loc = ObsGeneral.objects.filter(ring_obs_id=ring_obs_id)[0].volume_id
            except IndexError:
                volume_loc = f.volume_id

            if f.instrument_id == "LORRI":
                volume_loc = f.volume_id

            if f.product_type not in file_names[ring_obs_id]:
                file_names[ring_obs_id][f.product_type] = []

            extra_files = []
            if f.extra_files:
                extra_files = f.extra_files.split(',')

            ext = ''.join(f.file_specification_name.split('.')[-1:])
            base_file = '.'.join(f.file_specification_name.split('.')[:-1])

            # // sometimes in GO the volume_id is appended already
            if base_file.find(f.volume_id + ":")>-1:
                base_file = ''.join(base_file.split(':')[1:len(base_file.split(':'))])

            # // strange punctuation in the base file name is really a directory division
            base_file = file_name_cleanup(base_file).strip('/')

            if f.label_type.upper() == 'DETACHED':
                file_extensions += ['LBL']

            if f.ascii_ext: file_extensions += [f.ascii_ext]
            if f.lsb_ext: file_extensions += [f.lsb_ext]
            if f.msb_ext: file_extensions += [f.msb_ext]
            if f.detached_label_ext: file_extensions += [f.detached_label_ext]

            # extras are never found in the derived directory, so get those first
            for extra in extra_files:
                file_names[ring_obs_id][f.product_type]  += [path + volume_loc + '/' + extra]

            # now adjust the path whether this is on the derived directory or not
            if (f.product_type) == 'CALIBRATED':
                if loc_type != 'url':
                    path = settings.DERIVED_PATH
                else:
                    path = settings.DERIVED_HTTP_PATH
            else:
                if loc_type == 'path':
                    path = settings.FILE_PATH
                else:
                    path = settings.FILE_HTTP_PATH

            path = path + f.base_path.split('/')[-1:1]  # base path like xxx

            for extension in file_extensions:
                file_names[ring_obs_id][f.product_type]  += [path + volume_loc + '/' + base_file + '.' + extension]
            # // add the original file
            file_names[ring_obs_id][f.product_type]  += [path + '/' + volume_loc + '/' + base_file + '.' + ext]

            file_names[ring_obs_id][f.product_type] = list(set(file_names[ring_obs_id][f.product_type])) #  makes unique
            file_names[ring_obs_id][f.product_type].sort()
            file_names[ring_obs_id][f.product_type].reverse()

    # add some preview images?
    if len(previews):
        for ring_obs_id in file_names:
            file_names[ring_obs_id]['preview_image'] = []
            for size in previews.split(','):
                url_info = getImage(False,size.lower(), ring_obs_id,'raw')
                url = url_info['data'][0]['img']
                base_path = url_info['data'][0]['path']
                if url:
                    if loc_type == 'path':
                        url = settings.IMAGE_PATH + get_base_path_previews(ring_obs_id) + url
                    else:
                        url = base_path + url

                    file_names[ring_obs_id]['preview_image'].append(url) # ugh! this is cuz it goes through that stoopit utils too

    if fmt == 'raw':
        return file_names

    if fmt == 'json':
        return HttpResponse(json.dumps({'data':file_names}), mimetype='application/json')

    if fmt == 'html':
        return render_to_response("list.html",locals())




def getPage(request):
    """
    the gets the metadata to build a page of results
    """
    # get some stuff from the url or fall back to defaults
    collection_page = (request.GET.get('colls',False))
    limit = request.GET.get('limit',100)
    limit = int(limit)
    slugs = request.GET.get('cols', settings.DEFAULT_COLUMNS)
    if not slugs:
        slugs = settings.DEFAULT_COLUMNS  # i dunno why the above doesn't suffice

    columns = []
    for slug in slugs.split(','):
        try:
            columns += [ParamInfo.objects.get(slug=slug).param_name()]
        except ParamInfo.DoesNotExist:
            pass

    triggered_tables = list(set([param_name.split('.')[0] for param_name in columns]))
    try:
        triggered_tables.remove('obs_general')  # we remove it because it is the primary
                                                # model so don't need to add it to extra tables
    except ValueError:
        pass  # obs_general isn't in there

    if not collection_page:
        # this is a data table page

        order = request.GET.get('order',False)

        # figure out column order in table
        if order:
            try:
                descending = '-' if order[0] == '-' else None
                order_slug = order.strip('-')  # strip off any minus sign to look up param name
                order = ParamInfo.objects.get(slug=order_slug).param_name()
                if descending:
                    order = '-' + order
            except DoesNotExist:
                order = False

        # figure out page we are asking for
        page_no = request.GET.get('page',1)
        page_no = int(page_no)

        # ok now that we have everything from the url get stuff from db
        (selections,extras) = urlToSearchParams(request.GET)
        user_query_table = getUserQueryTable(selections,extras)

        # figure out what tables do we need to join in and build query
        triggered_tables.append(user_query_table)
        where   = "obs_general.id = " + connection.ops.quote_name(user_query_table) + ".id"
        results = ObsGeneral.objects.extra(where=[where], tables=triggered_tables)

    else:
        # this is for a collection
        order = request.GET.get('colls_order', False)
        if order:
            try:
                order_param = order.strip('-')  # strip off any minus sign to look up param name
                descending = order[0] if (order[0] == '-') else None
                order = ParamInfo.objects.get(slug=order_param).name
                if descending:
                    order = '-' + order
            except DoesNotExist:
                order = False


        page_no = request.GET.get('colls_page',1)
        page_no = int(page_no)

        from user_collections.views import *  # circular import problem
        collection = get_collection(request)
        if not collection:
            raise Http404

        # figure out what tables do we need to join in and build query
        triggered_tables = list(set([t.split('.')[0] for t in columns]))
        try:
            triggered_tables.remove('obs_general')
        except ValueError:
            pass  # obs_general table wasn't in there for whatever reason

        # bring in the  triggered_tables
        results = ObsGeneral.objects.extra(tables=triggered_tables)

        # and do the filtering
        results = results.filter(ring_obs_id__in=collection)

    # now we have results object (either search or collections)
    if order:
        results = results.order_by(order)

    # this is the thing you pass to django model via values()
    # so we have the table names a bit to get what django wants:
    column_values = []
    for param_name in columns:
        table_name = param_name.split('.')[0]
        if table_name == 'obs_general':
            column_values.append(param_name.split('.')[1])
        else:
            column_values.append(param_name.split('.')[0].lower().replace('_','') + '__' + param_name.split('.')[1])


    """
    this may be an aweful hack.
    the limit is pretty much always 100, the user cannot change it in the interface
    but as an aide to finding the right chunk of a result set to search for
    in an 'add range' situation, the front end may send a large limit, like say
    page_no = 42 and limit = 400
    that means start the page at 42 and go 4 pages, and somewhere in there is our range
    so the way of computing starting offset here should always use the base_limit of 100
    using the passed limit will result inthe wront offset because of way offset is computed here
    """
    base_limit = 100  # see above
    offset = (page_no-1)*base_limit # we don't use Django's pagination because of that count(*) that it does.

    results = results.values_list(*column_values)[offset:offset+int(limit)]
    log.debug(str(results.query))

    # print results
    # this whole page_ids thing is just rediculous, the caller can get it from the result set
    # especially if we are saying that the id is always at index 0
    page_ids = [o[0] for o in results]

    if not len(page_ids):
        return False
    # print page_ids
    # print results.query
    # print list(results)

    return [page_no, limit, list(results), page_ids, order]



# avoiding a circular dependency, even James Bennett does this! http://is.gd/TGblFO
# well ok I moved to the end of module because it's needed in 2 methods here :0
