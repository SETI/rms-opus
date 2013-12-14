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

import logging
log = logging.getLogger(__name__)

def getData(request,fmt):
    """
    a page of results for a given search
    """
    [page_no, limit,page, page_ids, order] = getPage(request)

    checkboxes = True if (request.is_ajax()) else False

    slugs = request.GET.get('cols',settings.DEFAULT_COLUMNS)
    if not slugs: slugs = settings.DEFAULT_COLUMNS  # i dunno why this is necessary

    labels = []
    for slug in slugs.split(','):
        labels += [ParamInfo.objects.get(slug=slug).label_results]
    labels = labels.insert(0, "add") if (request.is_ajax()) else labels  # adds a column for checkbox add-to-collections


    from user_collections.views import *

    collection = in_collections(request)

    data = {'page_no':page_no, 'limit':limit, 'page':page, 'count':len(page)}

    return responseFormats(data,fmt,template='data.html', labels=labels,checkboxes=checkboxes, collection=collection, order=order)

def getDetail(request,ring_obs_id='',fmt='json'):
    """
    results for a single observation
    all the data, in categories

    """

    if not ring_obs_id: return Http404

    if fmt == 'html':
        from ui.views import getDetailPage
        return getDetailPage(request, ring_obs_id=ring_obs_id, fmt=fmt)

    data = SortedDict({})

    # find all the tables (categories) this observation belongs to,
    # start with base_tables:
    triggered_tables = [t for t in settings.BASE_TABLES]

    # grab mission and instrument tables
    # mission and instrument values for this ring_obs_id are in ObsGeneral model:
    try:
        mission = ObsGeneral.objects.get(ring_obs_id=ring_obs_id).mission_id
        instrument = ObsGeneral.objects.get(ring_obs_id=ring_obs_id).instrument_id
    except ObsGeneral.DoesNotExist:
        raise Http404
    # lookup the table name for this observation's mission and instrument
    # (misison tables are named a little trippy in TableName model / table_names table)
    triggered_tables.append(TableName.objects.get(table_name__startswith='obs_mission', mission_id=mission).table_name)
    triggered_tables.append('obs_instrument_' + instrument)


    # find any surface geo tables that contain this observation:
    # start by finding all surface targets for this ring_obs_id, then append the matching surface tables
    surface_geo_targets = ObsSurfaceGeometry.objects.filter(ring_obs_id=ring_obs_id).values('target_name')
    for target in surface_geo_targets:
        triggered_tables.append('obs_surface_geometry__' + target['target_name'])

    # now find all params and their values in each of these tables:
    for table_name in triggered_tables:
        table = TableName.objects.get(table_name=table_name)
        label = table.label
        table_name = table.table_name
        model_name = ''.join(table_name.title().split('_'))
        table_model = get_model('search', model_name)
        all_params = [param.name for param in ParamInfo.objects.filter(category_name=table_name, display_results=1)]
        results = table_model.objects.filter(ring_obs_id=ring_obs_id).values(*all_params)[0]

        data[label] = results


    if fmt == 'json':
        return HttpResponse(json.dumps(data), content_type="application/json")
    if fmt == 'raw':
        return data

    """
    THIS WILL BE REPLACED.
    leaving it for now because it is what the detail.html template expects
    results = ObsGeneral.objects.filter(ring_obs_id=ring_obs_id)
    for group in Group.objects.filter(display="Y"):
        group_name = group.name.strip()
        data[group_name] = SortedDict({})
        for cat in Category.objects.filter(display="Y", group = group) :
            cat_name = cat.name.strip()
            data[group_name][cat_name] = SortedDict({})
            for param in ParamInfo.objects.filter(display_results='Y', category = cat):
                # if mission or instrument is declared and do not match what is in files table
                # then do not return them as they are irrelevent to this observation
                # (for example: VGISS_camera is not relevant to a COISS image)
                if param.mission and param.mission != mission:
                    continue
                if param.instrument and param.instrument != instrument:
                    continue

                param_name = param.param_name()
                data[group_name][cat_name][param.slug.strip()] = results.values(param_name)[0][param_name]
                flat_data[param.slug.strip()] = results.values(param_name)[0][param_name]

            if not len(data[group_name][cat_name]):
                del data[group_name][cat_name] # clean up empties
        if not len(data[group_name]):
            del data[group_name] # clean up empties
    if fmt == 'csv':
        # return HttpResponse(','.join(column_values))
        return responseFormats({'data':[flat_data]},fmt,template='detail.html')

    return responseFormats({'data':detail},fmt,template='detail.html')
    """





def get_triggered_tables(selections, extras = {}):
    """
    this looks at user request and returns triggered tables
    always returns the settings.BASE_TABLES
    """
    # first add the base tables
    triggered_tables = [t for t in settings.BASE_TABLES]
    query_result_table = getUserQueryTable(selections,extras)

    # now see if any more tables are triggered from query
    for partable in Partable.objects.all():
        # we are joining the results of a user's query - the single column table of ids
        # with the trigger_tab listed in the partable,
        trigger_tab = partable.trigger_tab
        trigger_col = partable.trigger_col
        trigger_val = partable.trigger_val
        partable = partable.partable

        if partable in triggered_tables:
            continue  # already triggered, no need to check

        trigger_model = get_model('search', ''.join(trigger_tab.title().split('_')))
        results = trigger_model.objects
        if query_result_table:
            if trigger_tab == 'obs_general':
                where   = trigger_tab + ".id = " + query_result_table + ".id"
            else:
                where   = trigger_tab + ".obs_general_id = " + query_result_table + ".id"
            results = results.extra(where=[where], tables=[query_result_table])
        results = results.distinct().values(trigger_col)

        if len(results) == 1 and results[0][trigger_col] == trigger_val:
            # we has a triggered table
            triggered_tables.append(partable)

    # now hack in the proper ordering of tables
    final_table_list = []
    for table in TableName.objects.filter(table_name__in=triggered_tables).values('table_name'):
        final_table_list.append(table['table_name'])

    return final_table_list


# this should return an image for every row..
def getImages(request,size,fmt):
    """
    this returns rows from images table that correspond to request
    some rows will not have images, this function doesn't return 'image_not_found' information
    if a row doesn't have an image you get nothing. you lose. good day sir.

    """
    alt_size = request.GET.get('alt_size','')
    columns = request.GET.get('cols',settings.DEFAULT_COLUMNS)

    [page_no, limit, page, page_ids, order] = getPage(request)
    image_links   = Image.objects.filter(ring_obs_id__in=page_ids)

    if alt_size:
        image_links = image_links.values('ring_obs_id',size,alt_size);
    else:
        image_links = image_links.values('ring_obs_id',size);

    # to lamely preserve the order of page_ids
    ordered_image_links = []
    for ring_obs_id in page_ids:
        for link in image_links:
            if ring_obs_id == link['ring_obs_id']:
                ordered_image_links.append(link)
    image_links = ordered_image_links

    # find which are in collections, mark unfound images 'not found'
    for image in image_links:
        image['img'] = image[size] if image[size] else 'not found'
        from user_collections.views import *
        if image['ring_obs_id'] in in_collections(request):
            image['in_collection'] = True

    path = settings.IMAGE_HTTP_PATH

    if (request.is_ajax()):
        template = 'gallery.html'
    else: template = 'image_list.html'

    return responseFormats({'data':[i for i in image_links]},fmt, size=size, path=path, alt_size=alt_size, columns_str=columns.split(','), all_collections=in_collections(request), template=template, order=order)



def getImage(request,size='med', ring_obs_id='',fmt='mouse'):      # mouse?
    """
    size = thumb, small, med, full
    return ring_obs_id + ' ' + size

    return HttpResponse(img + "<br>" + ring_obs_id + ' ' + size +' '+ fmt)
    """
    img = Image.objects.filter(ring_obs_id=ring_obs_id).values(size)[0][size]
    path = settings.IMAGE_HTTP_PATH

    return responseFormats({'data':[{'img':img}]},fmt, size=size, path=path, template='image_list.html')

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

    return getFiles(ring_obs_id,fmt, loc_type, product_types,images)



# loc_type = path or url
def getFiles(ring_obs_id,fmt='raw', loc_type="url", product_types=[], previews=[]):
    if ring_obs_id:
        if type(ring_obs_id) is unicode:
            ring_obs_ids = [ring_obs_id]
        else:
            ring_obs_ids = ring_obs_id
    else: return HttpResponse('EPIC FAIL')

    file_names = {}

    if loc_type == 'url':
        path = settings.FILE_HTTP_PATH
    else:
        path = settings.FILE_PATH

    for ring_obs_id in ring_obs_ids:

        file_names[ring_obs_id] = {}

        files_table_rows = Files.objects.filter(ring_obs_id=ring_obs_id)

        for f in files_table_rows:

            # append new base paths
            path = path + f.base_path.split('/')[-2:-1][0] + '/'

            file_extensions = []
            # volume_loc = getAltVolumeLocs(volume_id)
            volume_loc = f.volume_id

            if f.product_type not in file_names[ring_obs_id]:
                file_names[ring_obs_id][f.product_type] = []

            extra_files = []
            if f.extra_files:
                extra_files = f.extra_files.split(',')

            file_name_split = f.file_specification_name.split('.')

            ext = file_name_split.pop()
            base_file = ''.join(file_name_split)

            #----- thought that was craycray? Now it gets craycray -----#

            # // sometimes in GO the volume_id is appended already
            if base_file.find(f.volume_id + ":")>-1:
                base_file_split = base_file.split(':')
                base_file = ''.join(base_file_split[1:len(base_file_split)])

            # // strange punctuation in the base file name is really a directory division
            base_file = file_name_cleanup(base_file)

            base_file = base_file.strip('/') # trim leading and trailing slashes

            if f.label_type.upper() == 'DETACHED':
                file_extensions += ['LBL']

            if f.ascii_ext: file_extensions += [f.ascii_ext]
            if f.lsb_ext: file_extensions += [f.lsb_ext]
            if f.msb_ext: file_extensions += [f.msb_ext]
            if f.detached_label_ext: file_extensions += [f.detached_label_ext]

            # extras are never found in the derived directory, so get those first
            for extra in extra_files:
                file_names[ring_obs_id][f.product_type]  += [path + volume_loc + '/' + extra]

            # now adjust the path whether this is on the derived directory or now
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


            base_vol_path = Files.objects.filter(ring_obs_id=ring_obs_id)[0].base_path.split('/')[-2:-1][0] + '/'  # base_path in db
            path = path + base_vol_path

            for extension in file_extensions:
                file_names[ring_obs_id][f.product_type]  += [path + volume_loc + '/' + base_file + '.' + extension]
            # // add the original file
            file_names[ring_obs_id][f.product_type]  += [path + volume_loc + '/' + base_file + '.' + ext]

            file_names[ring_obs_id][f.product_type] = list(set(file_names[ring_obs_id][f.product_type])) #  makes unique
            file_names[ring_obs_id][f.product_type].sort()
            file_names[ring_obs_id][f.product_type].reverse()

    # filter by product_type?
    if len(product_types):
        filtered_file_names = {}
        for ring_obs_id in file_names:
            for product_type in file_names[ring_obs_id]:
                if product_type in product_types:
                    filtered_file_names[ring_obs_id] = {product_type:file_names[ring_obs_id][product_type]}
        file_names = filtered_file_names

    # add some preview images?
    if len(previews):
        for ring_obs_id in file_names:
            file_names[ring_obs_id]['preview_image'] = []
            for size in previews.split(','):
                url_info = getImage(False,size.lower(), ring_obs_id,'raw')
                url = url_info['data'][0]['img']
                if url:
                    if loc_type == 'path':
                        url = settings.IMAGE_PATH + url
                    else:
                        url = settings.IMAGE_HTTP_PATH + url

                    file_names[ring_obs_id]['preview_image'].append(url) # ugh! this is cuz it goes through that stoopit utils too

    if fmt == 'raw':
        return file_names

    if fmt == 'json':
        return HttpResponse(simplejson.dumps({'data':file_names}), mimetype='application/json')

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
        triggered_tables.remove('obs_general')  # we remove it because it is the primary model so don't need to add it to extra tables
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

        # ok now that we have everything from the url et stuff from db
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

    offset = (page_no-1)*limit # we don't use Django's pagination because of that count(*) that it does.

    results = results.values_list(*column_values)[offset:offset+limit]
    page_ids = [o['ring_obs_id'] for o in results.values('ring_obs_id')[offset:offset+limit]]

    return [page_no, limit, list(results), page_ids, order]



# avoiding a circular dependency, even James Bennett does this! http://is.gd/TGblFO
# well ok I moved to the end of module because it's needed in 2 methods here :0
