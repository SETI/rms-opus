
################################################################################
#
# results/views.py
#
# The (private) API interface for adding and removing items from the collection
# and creating download .zip and .csv files.
#
#    Format: __collections/view.html
#    Format: __collections/status.json
#    Format: __collections/data.csv
#    Format: __collections/(?P<action>[add|remove|addrange|removerange|addall]+).json
#    Format: __collections/reset.html
#    Format: __collections/download/info.json
#    Format: __collections/download.zip
#    Format: __zip/(?P<opus_id>[-\w]+).(?P<fmt>[json]+)
#
################################################################################

import csv
import datetime
import json
import logging
import os
import random
import string
import zipfile

import pdsfile

import settings

from django.db import connection
from django.http import HttpResponse, HttpResponseNotFound, Http404
from django.shortcuts import render
from django.views.decorators.cache import never_cache

from hurry.filesize import size as nice_file_size

from results.views import (get_data,
                           get_search_results_chunk,
                           get_all_in_collection)
from search.models import ObsGeneral
from search.views import get_param_info_by_slug
from user_collections.models import Collections
from tools.app_utils import *
from tools.file_utils import *

log = logging.getLogger(__name__)


################################################################################
#
# API INTERFACES
#
################################################################################


@never_cache
def api_view_collection(request):
    """Return the OPUS-specific left side of the "Selections" page as HTML.

    This includes the number of files selected, total size of files selected,
    and list of product types with their number. This returns information about
    ALL files and product types, ignoring any user choices. Choices are handled
    in the OPUS UI.

    This is a PRIVATE API.

    Format: __collections/view.html
    """
    api_code = enter_api_call('api_view_collection', request)

    session_id = get_session_id(request)

    (download_size, download_count,
     product_counts) = _get_download_info(['all'], session_id)

    product_cats = []
    for product_type in product_counts:
        name = product_type[0]
        pretty_name = name
        if name == 'standard':
            pretty_name = 'Standard Data Products'
        elif name == 'metadata':
            pretty_name = 'Metadata Products'
        elif name == 'browse':
            pretty_name = 'Browse Products'
        elif name == 'diagram':
            pretty_name = 'Diagram Products'
        else:
            pretty_name = name + '-Specific Products'
        key = (name, pretty_name)
        if key not in product_cats:
            product_cats.append(key)

    context = {
        'download_count': download_count,
        'download_size': download_size,
        'download_size_pretty':  nice_file_size(download_size),
        'product_counts': product_counts,
        'product_cats': product_cats
    }

    template='user_collections/collections.html'
    ret = render(request, template, context)

    exit_api_call(api_code, ret)
    return ret


@never_cache
def api_collection_status(request):
    """Return the number of items in a collection.

    It is used to update the "Selection <N>" tab in the OPUS UI.

    This is a PRIVATE API.

    Format: __collections/status.json
    """
    api_code = enter_api_call('api_collection_status', request)

    session_id = get_session_id(request)

    count = _get_collection_count(session_id)

    # XXX What is the point of expected_request_no?
    expected_request_no = request.session.get('expected_request_no', 1)

    ret = HttpResponse(json.dumps({'count': count,
                                   'expected_request_no': expected_request_no}))
    exit_api_call(api_code, ret)
    return ret


def api_get_collection_csv(request, fmt=None):
    """Returns a CSV file of the current collection.

    The CSV file contains the columns specified in the request.

    This is a PRIVATE API.

    Format: __collections/data.csv
            Normal selected-column arguments
    """
    api_code = enter_api_call('api_get_collection_csv', request)

    ret = _get_collection_csv(request, fmt, api_code=api_code)

    exit_api_call(api_code, ret)
    return ret


@never_cache
def api_edit_collection(request, **kwargs):
    """Add or remove items from a collection.

    This is a PRIVATE API.

    Format: __collections/
            (?P<action>[add|remove|addrange|removerange|addall]+).json
    Arguments: opus_id=<ID>
               request=<N>
               expected_request_no=<N>
               addrange=<OPUS_ID>,<OPUS_ID>
               removerange=<OPUS_ID>,<OPUS_ID>

    Returns the new number of items in the collection.
    """
    api_code = enter_api_call('api_edit_collection', request)

    session_id = get_session_id(request)

    try:
        action = kwargs['action']
    except KeyError:
        exit_api_call(api_code, None)
        raise Http404

    request_no = request.GET.get('request', None)

    if action in ['add', 'remove']:
        opus_id = request.GET.get('opus_id', None)
        if opus_id is None:
            json_data = {'err': 'No observations specified'}
            ret = HttpResponse(json.dumps(json_data))
            exit_api_call(api_code, ret)
            return ret

    if request_no is None: # XXX Is this needed?
        try:
            request_no = kwargs['request_no']
        except KeyError:
            json_data = {'err': 'No request number received'}
            ret = HttpResponse(json.dumps(json_data))
            exit_api_call(api_code, ret)
            return ret

    request_no = int(request_no)

    expected_request_no = request.session.get('expected_request_no', 1)

    if action == 'add':
        _add_to_collections_table(opus_id, session_id)

    elif action == 'remove':
        _remove_from_collections_table(opus_id, session_id)

    elif action in ['addrange', 'removerange']:
        # This returns a boolean indicating success which we ignore XXX
        _edit_collection_range(request, session_id, action)

    elif action == 'addall':
        _edit_collection_addall(request, **kwargs)

    collection_count = _get_collection_count(session_id)
    json_data = {'err': False,
                 'count': collection_count,
                 'request_no': request_no}

    download = request.GET.get('download', False)
    # Minor performance check - if we don't need a total download size, don't
    # bother
    # Only the selection tab is interested in updating that count at this time.
    if download:
        product_types_str = request.GET.get('types', 'all')
        product_types = product_types_str.split(',')
        (download_size, download_count,
         product_counts) = _get_download_info(product_types, session_id)
        json_data['download_count'] = download_count
        json_data['download_size'] = download_size
        json_data['download_size_pretty'] = nice_file_size(download_size)
        json_data['product_counts'] = {x[0][3]: x[1] for x in product_counts}

    ret = HttpResponse(json.dumps(json_data))
    exit_api_call(api_code, ret)
    return ret


@never_cache
def api_reset_session(request):
    """Remove everything from the collection and reset the session.

    This is a PRIVATE API.

    Format: __collections/reset.html
    """
    api_code = enter_api_call('api_reset_session', request)

    session_id = get_session_id(request)

    sql = 'DELETE FROM '+connection.ops.quote_name('collections')
    sql += ' WHERE session_id=%s'
    cursor = connection.cursor()
    cursor.execute(sql, [session_id])

    request.session.flush()
    session_id = get_session_id(request) # Creates a new session id
    ret = HttpResponse('session reset')
    exit_api_call(api_code, ret)
    return ret


@never_cache
def api_get_download_info(request):
    """Return count, size, and product_type info for selected product types.

    This is very similar to api_view_collection, except instead of returning
    the HTML for the entire left side of the Selections page, it just returns
    the updated sizes and counts. This is used by the OPUS UI when the user
    clicks to (de)select a product type.

    This is a PRIVATE API.

    Format: __collections/download/info.json
    Arguments: types=<PRODUCT_TYPES>
    """
    api_code = enter_api_call('api_get_download_info', request)

    session_id = get_session_id(request)

    product_types_str = request.GET.get('types', '')
    product_types = product_types_str.split(',')

    # Since we are assuming this is coming from user interaction
    # if no filters exist then none of this product type is wanted
    if product_types == ['none']:
        product_types = []

    (download_size, download_count,
     product_counts) = _get_download_info(product_types, session_id)

    context = {
        'download_count': download_count,
        'download_size':  download_size,
        'download_size_pretty': nice_file_size(download_size),
        'product_counts': {x[0][2]: x[1] for x in product_counts}
    }

    ret = HttpResponse(json.dumps(context), content_type='application/json')
    exit_api_call(api_code, ret)
    return ret


@never_cache
def api_create_download(request, opus_ids=None, fmt=None):
    """Creates a zip file of all items in the collection or the given OPUS ID.

    This is a PRIVATE API.

    Format: __collections/download.zip
        or: __zip/(?P<opus_id>[-\w]+).(?P<fmt>[json]+)
    Arguments: types=<PRODUCT_TYPES>
    """
    api_code = enter_api_call('api_create_download', request)

    session_id = get_session_id(request)

    fmt = request.GET.get('fmt', 'raw')
    product_types = request.GET.get('types', 'none')
    product_types = product_types.split(',')

    if not opus_ids:
        opus_ids = get_all_in_collection(request)

    if not isinstance(opus_ids, (list, tuple)):
        opus_ids = [opus_id]

    if not opus_ids:
        raise Http404

    zip_base_file_name = _zip_filename()
    zip_root = zip_base_file_name.split('.')[0]
    zip_file_name = settings.TAR_FILE_PATH + zip_base_file_name
    chksum_file_name = settings.TAR_FILE_PATH + f'checksum_{zip_root}.txt'
    manifest_file_name = settings.TAR_FILE_PATH + f'manifest_{zip_root}.txt'
    csv_file_name = settings.TAR_FILE_PATH + f'csv_{zip_root}.txt'

    _create_csv_file(request, csv_file_name, api_code=api_code)

    # fetch the full file paths we'll be zipping up
    files = get_pds_products(opus_ids, None, loc_type='path',
                             product_types=product_types)

    if not files:
        log.error("No files found in api_create_download")
        log.error(".. First 5 opus_ids: %s", str(opus_ids[:5]))
        log.error(".. First 5 PRODUCT TYPES: %s", str(product_types[:5]))
        raise Http404

    (download_size, download_count,
     product_counts) = _get_download_info(product_types, session_id)

    # don't create download if files are too big
    if download_size > settings.MAX_DOWNLOAD_SIZE:
        ret = HttpResponse("Sorry, maximum download size ("+str(settings.MAX_DOWNLOAD_SIZE)+" bytes) exceeded")
        exit_api_call(api_code, ret)
        return ret

    # don't keep creating downloads after user has reached their size limit
    cum_download_size = request.session.get('cum_download_size', 0)
    cum_download_size += download_size
    if cum_download_size > settings.MAX_CUM_DOWNLOAD_SIZE:
        ret = HttpResponse("Sorry, maximum cumulative download size reached for this session")
        exit_api_call(api_code, ret)
        return ret
    request.session['cum_download_size'] = int(cum_download_size)

    # zip each file into tarball and create a manifest too
    zip_file = zipfile.ZipFile(zip_file_name, mode='w')
    chksum_fp = open(chksum_file_name, 'w')
    manifest_fp = open(manifest_file_name, 'w')

    errors = []
    added = []
    for opus_id in files:
        if 'Current' not in files[opus_id]:
            continue
        files_version = files[opus_id]['Current']
        for product_type in files_version:
            for f in files_version[product_type]:
                pretty_name = f.split('/')[-1]
                digest = "%s:%s" % (pretty_name, md5(f))
                mdigest = "%s:%s" % (opus_id, pretty_name)

                if pretty_name not in added:
                    chksum_fp.write(digest+'\n')
                    manifest_fp.write(mdigest+'\n')
                    filename = os.path.basename(f)
                    try:
                        zip_file.write(f, arcname=filename)
                        added.append(pretty_name)
                    except Exception as e:
                        log.error('create_download threw exception for opus_id %s, product_type %s, file %s, pretty_name %s',
                                  opus_id, product_type, f, pretty_name)
                        log.error('.. %s', str(e))
                        errors.append('Could not find: ' + pretty_name)

    # Write errors to manifest file
    if errors:
        manifest_fp.write('Errors:\n')
        for e in errors:
            manifest_fp.write(e+'\n')

    # Add manifests and checksum files to tarball and close everything up
    manifest_fp.close()
    chksum_fp.close()
    zip_file.write(chksum_file_name, arcname='checksum.txt')
    zip_file.write(manifest_file_name, arcname='manifest.txt')
    zip_file.write(csv_file_name, arcname='data.csv')
    zip_file.close()

    os.remove(chksum_file_name)
    os.remove(manifest_file_name)
    os.remove(csv_file_name)

    zip_url = settings.TAR_FILE_URL_PATH + zip_base_file_name

    if not added:
        log.error('No files found for download cart %s', manifest_file_name)
        raise Http404('No files found')

    if fmt == 'json':
        ret = HttpResponse(json.dumps(zip_url), content_type='application/json')
    else:
        ret = HttpResponse(zip_url)

    exit_api_call(api_code, ret)
    return ret


################################################################################
#
# Support routines - get information
#
################################################################################

def _get_download_info(product_types, session_id):
    """Return information about the current collection useful for download.

    The result is limited to the given product_types. ['all'] means return all
    product_types.

    Returns:
        download_size       (bytes)
        download_count      (total number of files)
        product_counts      (indexed by product_type)
    """
    opus_ids = (Collections.objects.filter(session_id__exact=session_id)
                .values_list('opus_id'))
    opus_id_list = [x[0] for x in opus_ids]

    products_by_type = get_pds_products_by_type(opus_id_list,
                                                product_types=product_types)
    (download_size, download_count,
     product_counts) = get_product_counts(products_by_type)

    return download_size, download_count, product_counts


def _get_collection_count(session_id):
    "Return the number of items in the current collection."
    count = Collections.objects.filter(session_id__exact=session_id).count()
    return count


def _get_collection_csv(request, fmt=None, api_code=None):
    "Create and return a CSV file based on user column and selection."
    slugs = request.GET.get('cols', settings.DEFAULT_COLUMNS)
    (page_no, start_obs, limit, page, opus_ids, file_specs,
     ring_obs_ids, order) = get_search_results_chunk(request,
                                                     use_collections=True,
                                                     limit='all',
                                                     api_code=api_code)

    if fmt == 'raw':
        return slugs.split(','), page

    column_labels = []
    for slug in slugs.split(','):
        pi = get_param_info_by_slug(slug)
        if pi is None:
            log.error('_get_collection_csv: Unknown slug "%s"', slug)
            return HttpResponseNotFound('Unknown slug')
        else:
            # append units if pi_units has unit stored
            unit = pi.get_units()
            label = pi.body_qualified_label_results()
            if unit:
                column_labels.append(label + ' ' + unit)
            else:
                column_labels.append(label)

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="data.csv"'
    wr = csv.writer(response)
    wr.writerow(column_labels)
    wr.writerows(page)

    return response


################################################################################
#
# Support routines - add or remove items from collections
#
################################################################################

def _add_to_collections_table(opus_id_list, session_id):
    "Add OPUS_IDs to the collections table."
    cursor = connection.cursor()
    if not isinstance(opus_id_list, (list, tuple)):
        opus_id_list = [opus_id_list]
    res = (ObsGeneral.objects.filter(opus_id__in=opus_id_list)
           .values_list('opus_id', 'id'))
    values = [(session_id, id, opus_id) for opus_id, id in res]
    # Get rid of one that's already there - we can't use REPLACE INTO because
    # we don't have a single unique key to use
    for opus_id in opus_id_list:
        _remove_from_collections_table(opus_id, session_id)
    sql = 'INSERT INTO '+connection.ops.quote_name('collections')
    sql += ' (session_id, obs_general_id, opus_id) VALUES (%s, %s, %s)'
    cursor.executemany(sql, values)


def _remove_from_collections_table(opus_id_list, session_id):
    "Remove OPUS_IDs from the collections table."
    cursor = connection.cursor()
    if not isinstance(opus_id_list, (list, tuple)):
        opus_id_list = [opus_id_list]
    values = [(session_id, opus_id) for opus_id in opus_id_list]
    sql = 'DELETE FROM '+connection.ops.quote_name('collections')
    sql += ' WHERE session_id=%s AND opus_id=%s'
    cursor.executemany(sql, values)


def _edit_collection_range(request, session_id, action):
    "Add or remove a range of opus_ids based on the current sort order."
    id_range = request.GET.get('range', False)
    if not id_range:
        log.error('Got to _edit_collection_range but no range given')
        log.error('... %s', str(request.GET))
        return False

    ids = id_range.split(',')
    if len(ids) != 2:
        return False
    (min_id, max_id) = ids

    data = get_data(request, 'raw', cols='opusid')
    if data is None:
        return False

    selected_range = []
    in_range = False  # loop has reached the range selected

    opus_id_key = 0

    for row in data['page']:
        opus_id = row[opus_id_key]
        if opus_id == min_id:
            in_range = True
        if in_range:
            selected_range.append(opus_id)
        if in_range and opus_id == max_id:
            break

    if not selected_range:
        log.error('_edit_collection_range failed to find range: %s', id_range)
    elif action == 'addrange':
        _add_to_collections_table(selected_range, session_id)
    elif action == 'removerange':
        _remove_from_collections_table(selected_range, session_id)

    return True


def _edit_collection_addall(request, **kwargs):
    """XXX NOT IMPLEMENTED - FIX THIS
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
    log.error("edit_collection_addall is currently unavailable. see user_collections.edit_collection_addall()")
    return

    #XXX NOT YET UPDATED
    session_id = request.session.session_key

    (selections,extras) = urlToSearchParams(request.GET)
    query_table_name = getUserQueryTable(selections,extras)
    assert query_table_name # This can be FALSE - Beware! XXX
    cursor = connection.cursor()
    coll_table_name = get_collection_table(session_id)
    sql = "replace into " + connection.ops.quote_name(coll_table_name) + \
          " (id, opus_id) select o.id, o.opus_id from obs_general o, " + connection.ops.quote_name(query_table_name) + \
          " s where o.id = s.id"
    cursor.execute(sql)
    return _get_collection_count(session_id)


################################################################################
#
# Support routines - Downloads
#
################################################################################


def _zip_filename(opus_id=None):
    "Create a unique filename for a user's cart."
    random_ascii = random.choice(string.ascii_letters).lower()
    timestamp = "T".join(str(datetime.datetime.now()).split(' '))
    # Windows doesn't like ':' in filenames
    timestamp = timestamp.replace(':', '-')
    if opus_id:
        return f'pdsrms-data-{opus_id}-{random_ascii}-{timestamp}.zip'
    return f'pdsrms-data-{random_ascii}-{timestamp}.zip'


def _create_csv_file(request, csv_file_name, api_code=None):
    "Create a CSV file containing the collection data."
    slug_list, all_data = _get_collection_csv(request, fmt='raw',
                                              api_code=api_code)
    column_labels = []
    for slug in slug_list:
        pi = get_param_info_by_slug(slug)
        if pi is None:
            log.error('_get_collection_csv: Unknown slug "%s"', slug)
            return HttpResponseNotFound('Unknown slug')
        else:
            # append units if pi_units has unit stored
            unit = pi.get_units()
            label = pi.body_qualified_label_results()
            if unit:
                column_labels.append(label + ' ' + unit)
            else:
                column_labels.append(label)

    with open(csv_file_name, 'a') as csv_file:
        wr = csv.writer(csv_file)
        wr.writerow(column_labels)
        wr.writerows(all_data)


# XXX We need to get MD5 checksums from PdsFile instead of computing them here.
def md5(filename):
    """ accepts full path file name and returns its md5
    """
    import hashlib
    d = hashlib.md5()
    try:
        d.update(open(filename, 'rb').read())
    except Exception as e:
        log.error('Failed to compute MD5 for "%s": %s',
                  filename, str(e))
        return False
    else:
        return d.hexdigest()
