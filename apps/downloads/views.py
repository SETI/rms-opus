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
    from results.views import get_csv
    slug_list, all_data = get_csv(request, fmt="raw")
    csv_file = open(csv_file_name,'a')
    wr = csv.writer(csv_file)
    wr.writerow(slug_list)
    wr.writerows(all_data)


def create_zip_filename(ring_obs_id=None):
    """ create a unique filename for a user's cart
    """
    if not ring_obs_id:
        random_ascii = random.choice(string.ascii_letters).lower()
        timestamp = "T".join(str(datetime.datetime.now()).split(' '))
        return 'pdsrings-data-' + random_ascii + '-' + timestamp + '.zip'
    else:
        return 'pdsrings-data-' + ring_obs_id + '.zip'

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
    takes an url or pull system path for images and returns path alone
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

def get_download_info(files):
    """
    calculate the sum download size of every file found in files.
    returns a tuple of ints: (<total size in bytes>, <total file count>)
    accepts only structure like that returnd by getfiles:
    files = {
        '<ring_obs_id>': {
            '<product_type'>: [<file_name1>, <file_name2>]
        }
    }
    product type can be a valid PDS product type or 'preview_image' (todo: marry these 2)
    """
    file_paths = []  # the files we need to check
    file_count = 0  # count of each file in files
    total_size = 0

    all_product_types = []
    for ring_obs_id in files:
        for product_type in files[ring_obs_id]:
            for f in files[ring_obs_id][product_type]:

                all_product_types.append(product_type)

                if product_type != 'preview_image':
                    # this is a pds file not a browse product
                    # collect the urls.. we will process these at the end
                    file_paths += [f for f in files[ring_obs_id][product_type]] # list of all urls

                elif product_type == 'preview_image':
                    # the file size of each preview images on disc is checked here
                    # todo: OMG WHY WHAT
                    # todo: get the file sizes into database instead = process like pds files and remove this whole section!

                    from results.views import get_base_path_previews
                    try:
                        size = getsize(f)
                        total_size += size
                        file_count = file_count + 1
                    except OSError:
                        log.error('could not find file: ' + f)

    all_product_types = list(set(all_product_types))  # make unique
    # now we have all pds file_names, put all file names in a list and get their count
    if file_paths:

        file_names = list(set([ get_file_path(u) for u in file_paths]))
        file_count += len(file_names)

        # query database for the sum of all file_names size fields
        file_sizes = FileSizes.objects.filter(name__in=file_names, PRODUCT_TYPE__in=all_product_types).values('name','size','volume_id').distinct()
        total_size += sum([f['size'] for f in file_sizes])  # todo: this is here b/c django was not happy mixing aggregate+distinct

    return total_size, file_count  # bytes

def get_download_info_API(request):
    """
    this serves get_download_info as an api endpoint
    but takes a request object as input
    and inspects the request for product type / preview image filters
    """
    update_metrics(request)

    session_id = request.session.session_key

    product_types = request.GET.get('types', 'none')
    product_types = product_types.split(',')

    previews = request.GET.get('previews', 'none')
    previews = previews.split(',')

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
    files = getFiles(collection=True, session_id=session_id, fmt="raw", loc_type="url", product_types=product_types, previews=previews)
    download_size, count = get_download_info(files)

    # make pretty size string
    download_size = nice_file_size(download_size)

    return HttpResponse(json.dumps({'size':download_size, 'count':count}), content_type='application/json')


@never_cache
def create_download(request, collection_name=None, ring_obs_ids=None, fmt=None):
    """
    feeds request to getFiles and zips up all files it finds into zip file
    and adds a manifest file and md5 checksums

    """
    update_metrics(request)

    fmt = request.GET.get('fmt', "raw")
    product_types = request.GET.get('types', 'none')
    product_types = product_types.split(',')

    previews = request.GET.get('previews', 'none')
    previews = previews.split(',')

    if not ring_obs_ids:
        ring_obs_ids = []
        from user_collections.views import *
        ring_obs_ids = get_all_in_collection(request)

    if type(ring_obs_ids) is unicode or type(ring_obs_ids).__name__ == 'str':
        ring_obs_ids = [ring_obs_id]

    if not ring_obs_ids:
        raise Http404

    # create some file names
    zip_file_name = create_zip_filename();
    chksum_file_name = settings.TAR_FILE_PATH + "checksum_" + zip_file_name.split(".")[0] + ".txt"
    manifest_file_name = settings.TAR_FILE_PATH + "manifest_" + zip_file_name.split(".")[0] + ".txt"
    csv_file_name = settings.TAR_FILE_PATH + "csv_" + zip_file_name.split(".")[0] + ".txt"

    create_csv_file(request, csv_file_name)

    # fetch the full file paths we'll be zipping up
    import results
    files = results.views.getFiles(ring_obs_ids,fmt="raw", loc_type="path", product_types=product_types, previews=previews)

    if not files:
        log.error("no files found from results.views.getFiles in downloads.create_download")
        raise Http404

    # zip each file into tarball and create a manifest too
    zip_file = zipfile.ZipFile(settings.TAR_FILE_PATH + zip_file_name, mode='w')
    chksum = open(chksum_file_name,"w")
    manifest = open(manifest_file_name,"w")
    size, download_count = get_download_info(files)

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
    for ring_obs_id in files:
        for product_type in files[ring_obs_id]:
            for f in files[ring_obs_id][product_type]:

                if 'FMT' in f or 'fmt' in f:
                    pretty_name = '/'.join(f.split("/")[-3:]).upper()
                    digest = "%s:%s" % (pretty_name, md5(f))
                    mdigest = "%s:%s" % (ring_obs_id, pretty_name)
                else:
                    pretty_name = f.split("/")[-1]
                    if product_type != 'preview_image':
                        pretty_name = pretty_name.upper()

                    digest = "%s:%s" % (pretty_name, md5(f))
                    mdigest = "%s:%s" % (ring_obs_id, pretty_name)

                if pretty_name not in added:

                    chksum.write(digest+"\n")
                    manifest.write(mdigest+"\n")
                    try:
                        zip_file.write(f, arcname=f.split("/")[-1]) # arcname = fielname only, not full path
                        added.append(pretty_name)

                    except Exception,e:
                        log.error(e);
                        errors.append("could not find: " + pretty_name)
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
        log.error('no files found for download cart ' + manifest_file_name);
        raise Http404

    if fmt == 'json':
        return HttpResponse(json.dumps(zip_url), content_type='application/json')

    return HttpResponse(zip_url)
