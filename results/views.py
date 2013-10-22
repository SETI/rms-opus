################################################
#
#   results.views
#
################################################
import settings
from search.views import *
from search.models import *
from results.models import *
from paraminfo.models import *
from metadata.views import *
from user_collections.views import *
from django.http import Http404
from django.shortcuts import render_to_response
from tools.app_utils import *
from django.utils.datastructures import SortedDict

import logging
log = logging.getLogger(__name__)

def getData(request,fmt):
    """
    a page of results for a given search
    """
    [page_no, limit,page, page_ids, order] = getPage(request)
    table_headers = request.GET.get('table_headers',False)
    if (table_headers=='False'): table_headers = False
    checkboxes = True if (request.is_ajax()) else False

    column_slugs = request.GET.get('cols',settings.DEFAULT_COLUMNS)
    column_slugs = verifyColumns(column_slugs.split(','))

    labels = []
    if table_headers:
        for slug in column_slugs:
            labels += [ParamInfo.objects.get(slug=slug).label_results]
        labels = ("add," + labels) if (request.is_ajax()) else labels


    from user_collections.views import *

    collection = in_collections(request)

    data = {'page_no':page_no, 'limit':limit, 'page':page, 'count':len(page)}

    return responseFormats(data,fmt,template='data.html', labels=labels,table_headers=table_headers,checkboxes=checkboxes, collection=collection, order=order)

def getDetail(request,ring_obs_id='',fmt='json'):
    """
    results for a single observation
    all the data, in categories and groups

    """
    if not ring_obs_id: return

    data = SortedDict({})
    # mission and instrument values for this ring_obs_id
    try:
        mission = Files.objects.filter(ring_obs_id=ring_obs_id)[:1][0].mission
        instrument = Files.objects.filter(ring_obs_id=ring_obs_id)[:1][0].instrument_id
    except Files.DoesNotExist:
        raise Http404

    results = Observations.objects.filter(ring_obs_id=ring_obs_id)

    flat_data = SortedDict({}) # this is to build a csv
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
                if param.mission:
                    if param.mission != mission:
                        continue
                if param.instrument:
                    if param.instrument != instrument:
                        continue

                param_name = param.name.strip()
                data[group_name][cat_name][param.slug.strip()] = results.values(param_name)[0][param_name]
                flat_data[param.slug.strip()] = results.values(param_name)[0][param_name]

            if not len(data[group_name][cat_name]):
                del data[group_name][cat_name] # clean up empties
        if not len(data[group_name]):
            del data[group_name] # clean up empties

    if fmt == 'csv':
        # return HttpResponse(','.join(column_values))
        return responseFormats({'data':[flat_data]},fmt,template='detail.html')

    return responseFormats({'data':data},fmt,template='detail.html')


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
    the gets the metadata
    get some stuff from the url or fall back to defaults
    """
    collection_page = (request.GET.get('colls',False))
    limit = request.GET.get('limit',100)
    limit = int(limit)
    column_slugs = request.GET.get('cols',settings.DEFAULT_COLUMNS)
    column_slugs = verifyColumns(column_slugs.split(','))
    columns = []
    for slug in column_slugs:
        try:
            columns += [ParamInfo.objects.get(slug=slug).name]
        except ParamInfo.DoesNotExist:
            pass

    if not collection_page:
        order = request.GET.get('order',False)
        if order:
            try:
                order_param = order.strip('-')  # strip off any minus sign to look up param name
                descending = order[0] if (order[0] == '-') else None
                order = ParamInfo.objects.get(slug=order_param).name
                if descending:
                    order = '-' + order
            except DoesNotExist:
                order = False


        page_no = request.GET.get('page',1)
        page_no = int(page_no)
        (selections,extras) = urlToSearchParams(request.GET)
        table = getUserQueryTable(selections,extras)

        # join it with Observations table where all results are found
        where   = "observations.id = " + connection.ops.quote_name(table) + ".id"
        results = Observations.objects.extra(where=[where], tables=[table])
        if order:
            results = results.order_by(order)
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
        results = Observations.objects.filter(ring_obs_id__in=collection)
        if order:
            results = results.order_by(order)

    offset = (page_no-1)*limit # we don't use Django's pagination because of that count(*) that it does.
    results = results.values(*columns)[offset:offset+limit]

    page_ids = [o['ring_obs_id'] for o in results]


    # fix ordering of columns to match that defined by url
    page = []
    for row in results:
        new_row = []
        for col in columns:
            new_row.append(row[col])
        page += [new_row]

    return [page_no, limit, page, page_ids, order]





# finishe me!
def verifyColumns(slugs):
    """
    columns is a list of column names

    THIS IS IMPLEMENTED BUT NOT FLESHED OUT

    check columns against param_info table and return valid column names as fetched from that table
    returns empty list when all columns are requested

    receives and returns slugs
    """

    # FINISH ME:
    if slugs == 'all': return slugs

    if 'ringobsid' not in slugs:
         slugs.insert(0,'ringobsid')
    return slugs;

# avoiding a circular dependency, even James Bennett does this! http://is.gd/TGblFO
# well ok I moved to the end of module because it's needed in 2 methods here :0
