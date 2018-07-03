from os.path import getsize
import random
import string
import datetime
import hashlib
import zipfile
import json
import csv
from urlparse import urlparse
from django.http import HttpResponse, Http404
from django.db import connection
from django.db.models import Sum
from results.views import *
from tools.app_utils import *
from user_collections.views import *
from hurry.filesize import size as nice_file_size
from metrics.views import update_metrics
from django.views.decorators.cache import never_cache
import settings
import logging

log = logging.getLogger(__name__)

def create_csv_file(request, csv_file_name):
    """ for the given request and file name,
        writes a csv file on disk!
    """
    from user_collections.views import get_collection_csv
    slug_list, all_data = get_collection_csv(request, fmt="raw")
    csv_file = open(csv_file_name,'a')
    wr = csv.writer(csv_file)
    wr.writerow(slug_list)
    wr.writerows(all_data)


def create_zip_filename(opus_id=None):
    """ create a unique filename for a user's cart
    """
    if not opus_id:
        random_ascii = random.choice(string.ascii_letters).lower()
        timestamp = "T".join(str(datetime.datetime.now()).split(' '))
        return 'pdsrings-data-' + random_ascii + '-' + timestamp + '.zip'
    else:
        return 'pdsrings-data-' + opus_id + '.zip'

def md5(filename):
    """ accepts full path file name and returns its md5
    """
    d = hashlib.md5()
    try:
        d.update(open(filename).read())
    except Exception,e:
        return False
    else:
        return d.hexdigest()

def get_file_path(filename):
    """
    takes an url or full system path for images and returns path alone
    stripping domain and/or images_base_path + xxx directory
    """
    if 'http' in filename:
        parsed_uri = urlparse(filename)
        f = '/' + parsed_uri.path[1:]
        f = '/'.join(f.split('/')[3:])  # split the xxx dir, remove the leading /
    else:
        filename = ('/' + filename) if filename[0] != '/' else filename  # make sure starts with /
        # split local img path from path
        f = filename.replace(settings.FILE_PATH, '/')
        f = f.replace(settings.IMAGE_PATH, '/')
        f = f.replace(settings.DERIVED_PATH, '/')
        f = '/'.join(f.split('/')[2:])  # split the xxx dir, remove the leading /

    return f

def get_download_info(product_types, previews, colls_table_name):
    """
        returns total_size, file_count in bytes
        product_types list, previews bool, and colls_table_name string
        return
    """
    if previews == 'none' or previews == '' or previews == []:
        previews = None  # :-(

    if product_types and type(product_types).__name__ == 'str':
        product_types = [product_types]

    file_paths = []  # the files we need to check
    file_count = 0  # count of each file in files
    total_size = 0

    # find the total size of all the pds products in product_types
    total_size_products = 0
    file_count_products = 0
    if product_types:
        where   = "file_sizes.opus_id = " + connection.ops.quote_name(colls_table_name) + ".opus_id"
        file_sizes = FileSizes.objects.filter(PRODUCT_TYPE__in=product_types)
        total_size_info = file_sizes.extra(where=[where], tables=[colls_table_name])
        total_size_products = total_size_info.values('size').aggregate(Sum('size'))['size__sum']
        file_count_products = total_size_info.count()
        if not total_size_products:
            total_size_products = 0

    # now find total size of browse images on disc
    total_size_images = 0
    file_count_images = 0
    if previews:
        previews = [p.lower() for p in previews]
        images = Image.objects
        where   = "images.opus_id = " + connection.ops.quote_name(colls_table_name) + ".opus_id"

        for sz in previews:
            total_size_info = images.extra(where=[where], tables=[colls_table_name]).values('size_' + sz)
            total_size_images += total_size_info.aggregate(Sum('size_' + sz))['size_' + sz + '__sum']
            file_count_images += total_size_info.count()
            if not total_size_images:
                total_size_images = 0

    total_size = total_size_products + total_size_images
    file_count = file_count_products + file_count_images
    return total_size, file_count  # bytes

def get_download_info_API(request):
    """
    this serves get_download_info as an api endpoint
    but takes a request object as input
    and inspects the request for product type / preview image filters
    """
    update_metrics(request)

    from user_collections.views import get_collection_table  # circulosity
    session_id = request.session.session_key
    colls_table_name = get_collection_table(session_id)

    product_types = []
    product_types_str = request.GET.get('types', None)
    if product_types_str:
        product_types = product_types_str.split(',')

    previews = []
    previews_str = request.GET.get('previews', None)
    if previews_str:
        previews = previews_str.split(',')

    # since we are assuming this is coming from user interaction
    # if no filters exist then none of this product type is wanted
    if product_types == ['none'] and previews == ['none']:
        # ie this happens when all product types are unchecked in the interface
        return HttpResponse(json.dumps({'size':'0', 'count':'0'}), content_type='application/json')

    if previews == ['all']:
        previews = [i[0] for i in settings.image_sizes]

    # now get the files and download size / count for this cart
    urls = []
    from results.views import *
    download_size, count = get_download_info(product_types, previews, colls_table_name)

    # make pretty size string
    download_size = nice_file_size(download_size)

    return HttpResponse(json.dumps({'size':download_size, 'count':count}), content_type='application/json')


@never_cache
def create_download(request, collection_name=None, opus_ids=None, fmt=None):
    """
    feeds request to getFiles and zips up all files it finds into zip file
    and adds a manifest file and md5 checksums

    """
    update_metrics(request)

    from user_collections.views import get_collection_table, get_all_in_collection  # circulosity
    session_id = request.session.session_key
    colls_table_name = get_collection_table(session_id)

    fmt = request.GET.get('fmt', "raw")
    product_types = request.GET.get('types', 'none')
    product_types = product_types.split(',')

    previews = request.GET.get('previews', None)
    if previews:
        previews = previews.split(',')

    if not opus_ids:
        opus_ids = []
        from user_collections.views import get_collection_table
        opus_ids = get_all_in_collection(request)

    if type(opus_ids) is unicode or type(opus_ids).__name__ == 'str':
        opus_ids = [opus_id]

    if not opus_ids:
        raise Http404

    # create some file names
    zip_file_name = create_zip_filename();
    chksum_file_name = settings.TAR_FILE_PATH + "checksum_" + zip_file_name.split(".")[0] + ".txt"
    manifest_file_name = settings.TAR_FILE_PATH + "manifest_" + zip_file_name.split(".")[0] + ".txt"
    csv_file_name = settings.TAR_FILE_PATH + "csv_" + zip_file_name.split(".")[0] + ".txt"

    create_csv_file(request, csv_file_name)

    # fetch the full file paths we'll be zipping up
    import results
    files = db_utils.get_pds_products(opus_ids,fmt="raw", loc_type="path", product_types=product_types, previews=previews)

    if not files:
        log.error("No files found from results.views.get_files in downloads.create_download")
        log.error(".. First 5 opus_ids: %s", str(opus_ids[:5]))
        log.error(".. First 5 PRODUCT TYPES: %s", str(product_types[:5]))
        log.error(".. First 5 PREVIEWS: %s", str(previews[:5]))
        raise Http404

    # zip each file into tarball and create a manifest too
    zip_file = zipfile.ZipFile(settings.TAR_FILE_PATH + zip_file_name, mode='w')
    chksum = open(chksum_file_name,"w")
    manifest = open(manifest_file_name,"w")
    size, download_count = get_download_info(product_types, previews, colls_table_name)

    # don't keep creating downloads after user has reached their size limit
    cum_download_size = request.session.get('cum_download_size', 0)
    if cum_download_size > settings.MAX_CUM_DOWNLOAD_SIZE:
        # user is trying to download > MAX_CUM_DOWNLOAD_SIZE
        return HttpResponse("Sorry, Max cumulative download size reached " + str(cum_download_size) + ' > ' + str(settings.MAX_CUM_DOWNLOAD_SIZE))
    else:
        cum_download_size = cum_download_size + size
        request.session['cum_download_size'] = int(cum_download_size)

    errors = []
    added = []
    for opus_id in files:
        for product_type in files[opus_id]:
            for f in files[opus_id][product_type]:

                if 'FMT' in f or 'fmt' in f:
                    pretty_name = '/'.join(f.split("/")[-3:]).upper()
                    digest = "%s:%s" % (pretty_name, md5(f))
                    mdigest = "%s:%s" % (opus_id, pretty_name)
                else:
                    pretty_name = f.split("/")[-1]
                    if product_type != 'preview_image':
                        pretty_name = pretty_name.upper()

                    digest = "%s:%s" % (pretty_name, md5(f))
                    mdigest = "%s:%s" % (opus_id, pretty_name)

                if pretty_name not in added:

                    chksum.write(digest+"\n")
                    manifest.write(mdigest+"\n")
                    try:
                        zip_file.write(f, arcname=f.split("/")[-1]) # arcname = fielname only, not full path
                        added.append(pretty_name)

                    except Exception,e:
                        log.error('create_download threw exception for opus_id %s, product_type %s, file %s, pretty_name %s',
                                  opus_id, product_type, f, pretty_name)
                        log.error('.. %s', str(e))
                        errors.append("Could not find: " + pretty_name)
                    # "could not find " + name

    # write errors to manifest file
    if errors:
        manifest.write("errors:"+"\n")
        for e in errors:
            manifest.write(e+"\n")

    # add manifests and checksum files to tarball and close everything up
    manifest.close()
    chksum.close()
    zip_file.write(chksum_file_name, arcname="checksum.txt")
    zip_file.write(manifest_file_name, arcname="manifest.txt")
    zip_file.write(csv_file_name, arcname="data.csv")
    zip_file.close()

    zip_url = settings.TAR_FILE_URI_PATH + zip_file_name

    if not added:
        log.error('No files found for download cart %s', manifest_file_name)
        raise Http404

    if fmt == 'json':
        return HttpResponse(json.dumps(zip_url), content_type='application/json')

    return HttpResponse(zip_url)
