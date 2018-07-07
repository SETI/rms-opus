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

def get_download_info(product_types, session_id):
    """
        returns total_size, file_count in bytes
        product_types list
    """
    opus_ids = Collections.objects.filter(session_id__exact=session_id).values_list('opus_id')
    opus_id_list = [x[0] for x in opus_ids]

    products_by_type = get_pds_products_by_type(opus_id_list,
                                                product_types=product_types)
    (download_size, download_count,
     product_counts) = get_product_counts(products_by_type)
    download_size = nice_file_size(download_size)

    ret = {
        "download_count": download_count,
        "download_size": download_size,
        "product_counts": product_counts
    }

    return ret


def api_get_download_info(request):
    """
    this serves get_download_info as an api endpoint
    but takes a request object as input
    and inspects the request for product type / preview image filters
    """
    update_metrics(request)
    api_code = enter_api_call('api_get_download_info', request)

    session_id = request.session.session_key

    product_types = []
    product_types_str = request.GET.get('types', None)
    if product_types_str:
        product_types = product_types_str.split(',')

    # since we are assuming this is coming from user interaction
    # if no filters exist then none of this product type is wanted
    if product_types == ['none']:
        product_types = []

    # now get the files and download size / count for this cart
    ret = get_download_info(product_types, session_id)

    ret = HttpResponse(json.dumps(ret), content_type='application/json')
    exit_api_call(api_code, ret)
    return ret


@never_cache
def api_create_download(request, session_id=None, opus_ids=None, fmt=None):
    """
    feeds request to getFiles and zips up all files it finds into zip file
    and adds a manifest file and md5 checksums

    """
    update_metrics(request)
    api_code = enter_api_call('api_create_download', request)

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
    size, download_count = get_download_info(product_types, previews, session_id)

    # don't keep creating downloads after user has reached their size limit
    cum_download_size = request.session.get('cum_download_size', 0)
    if cum_download_size > settings.MAX_CUM_DOWNLOAD_SIZE:
        # user is trying to download > MAX_CUM_DOWNLOAD_SIZE
        ret = HttpResponse("Sorry, Max cumulative download size reached " + str(cum_download_size) + ' > ' + str(settings.MAX_CUM_DOWNLOAD_SIZE))
        exit_api_call(api_code, ret)
        return ret
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
        ret = HttpResponse(json.dumps(zip_url), content_type='application/json')
    else:
        ret = HttpResponse(zip_url)

    exit_api_call(api_code, ret)
    return ret
