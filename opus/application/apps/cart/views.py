################################################################################
#
# results/views.py
#
# The (private) API interface for adding and removing items from the cart
# and creating download .zip and .csv files.
#
#    Format: __cart/view.html
#    Format: __cart/status.json
#    Format: __cart/data.csv
#    Format: __cart/(?P<action>add|remove|addrange|removerange|addall).json
#    Format: __cart/reset.json
#    Format: __cart/download.json
#    Format: [__]api/download/(?P<opus_id>[-\w]+).zip
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

from django.db import connection, DatabaseError
from django.http import (HttpResponse,
                         HttpResponseNotFound,
                         HttpResponseServerError,
                         Http404)
from django.shortcuts import render
from django.views.decorators.cache import never_cache

from hurry.filesize import size as nice_file_size

from dictionary.models import Definitions
from metadata.views import get_result_count_helper
from results.views import (get_search_results_chunk,
                           labels_for_slugs)
from search.models import ObsGeneral
from search.views import (url_to_search_params,
                          get_user_query_table,
                          parse_order_slug,
                          create_order_by_sql)
from cart.models import Cart
from tools.app_utils import *
from tools.file_utils import *

log = logging.getLogger(__name__)


################################################################################
#
# API INTERFACES
#
################################################################################


@never_cache
def api_view_cart(request):
    """Return the OPUS-specific left side of the "Selections" page as HTML.

    This includes the number of files selected, total size of files selected,
    and list of product types with their number. This returns information about
    ALL files and product types, ignoring any user choices. However, there is
    an optional types=<PRODUCT_TYPES> parameter which, if specified, causes
    product types not listed to return "0" for number of products and sizes.

    This is a PRIVATE API.

    Format: __cart/view.html
    """
    api_code = enter_api_call('api_view_cart', request)

    if not request or request.GET is None:
        ret = Http404(settings.HTTP404_NO_REQUEST)
        exit_api_call(api_code, ret)
        raise ret

    session_id = get_session_id(request)

    product_types = ['all']

    info = _get_download_info(product_types, session_id)

    template = 'cart/cart.html'
    ret = render(request, template, info)

    exit_api_call(api_code, ret)
    return ret


@never_cache
def api_cart_status(request):
    """Return the number of items in a cart.

    It is used to update the "Selections <N>" tab in the OPUS UI.

    This is a PRIVATE API.

    Format: __cart/status.json
    Arguments: reqno=<N>
               [types=<list of types>]
               [download=<N>]

    Returns a JSON dict containing:
        In all cases:
            'count':                      Total number of items in cart

        If download=1:
            'total_download_count':       Total number of unique files
            'total_download_size':        Total size of unique files (bytes)
            'total_download_size_pretty': Total size of unique files (pretty format)
            'product_cat_list':           List of categories and info:
                [
                 [<Product Type Category>,
                  [{'slug_name':            Like "browse-thumb"
                    'product_type':         Like "Browse Image (thumbnail)"
                    'product_count':        Number of opus_ids in this category
                    'download_count':       Number of unique files in this category
                    'download_size':        Size of unique files in this category
                                                (bytes)
                    'download_size_pretty': Size of unique files in this category
                                                (pretty format)
                   }
                  ], ...
                 ], ...
                ]


    """
    api_code = enter_api_call('api_cart_status', request)

    if not request or request.GET is None:
        ret = Http404(settings.HTTP404_NO_REQUEST)
        exit_api_call(api_code, ret)
        raise ret

    session_id = get_session_id(request)

    reqno = get_reqno(request)
    if reqno is None:
        log.error('api_cart_status: Missing or badly formatted reqno')
        ret = Http404(settings.HTTP404_MISSING_REQNO)
        exit_api_call(api_code, ret)
        raise ret

    download = request.GET.get('download', 0)
    try:
        download = int(download)
    except:
        pass
    if download:
        product_types_str = request.GET.get('types', 'all')
        product_types = product_types_str.split(',')
        info = _get_download_info(product_types, session_id)
    else:
        info = {}

    count = _get_cart_count(session_id)

    info['count'] = count
    info['reqno'] = reqno
    ret = json_response(info)
    exit_api_call(api_code, ret)
    return ret


@never_cache
def api_get_cart_csv(request):
    """Returns a CSV file of the current cart.

    The CSV file contains the columns specified in the request.

    This is a PRIVATE API.

    Format: __cart/data.csv
            Normal selected-column arguments
    """
    api_code = enter_api_call('api_get_cart_csv', request)

    if not request or request.GET is None:
        ret = Http404(settings.HTTP404_NO_REQUEST)
        exit_api_call(api_code, ret)
        raise ret

    column_labels, page = _csv_helper(request, None, api_code)
    if column_labels is None:
        ret = Http404(settings.HTTP404_UNKNOWN_SLUG)
        exit_api_call(api_code, ret)
        raise ret

    ret = csv_response('data', page, column_labels)

    exit_api_call(api_code, ret)
    return ret


@never_cache
def api_edit_cart(request, action, **kwargs):
    """Add or remove items from a cart.

    This is a PRIVATE API.

    Format: __cart/
            (?P<action>add|remove|addrange|removerange|addall).json
    Arguments: opusid=<ID>                  (add, remove)
               range=<OPUS_ID>,<OPUS_ID>    (addrange, removerange)
               reqno=<N>
               [download=<N>]

    Returns the new number of items in the cart.
    If download=1, also returns all the data returned by
        /__cart/status.json
    """
    api_code = enter_api_call('api_edit_cart', request)

    if not request or request.GET is None:
        ret = Http404(settings.HTTP404_NO_REQUEST)
        exit_api_call(api_code, ret)
        raise ret

    session_id = get_session_id(request)

    reqno = get_reqno(request)
    if reqno is None:
        log.error('api_edit_cart: Missing or badly formatted reqno: %s',
                  request.GET)
        ret = Http404(settings.HTTP404_MISSING_REQNO)
        exit_api_call(api_code, ret)
        raise ret

    opus_id = None
    if action in ('add', 'remove'):
        opus_id = request.GET.get('opusid', None)
        if not opus_id: # Also catches empty string
            log.error('api_edit_cart: Missing opusid: %s',
                      request.GET)
            ret = Http404(settings.HTTP404_MISSING_OPUS_ID)
            exit_api_call(api_code, ret)
            raise ret

    if action == 'add':
        err = _add_to_cart_table(opus_id, session_id, api_code)
    elif action == 'remove':
        err = _remove_from_cart_table(opus_id, session_id, api_code)
    elif action in ('addrange', 'removerange'):
        err = _edit_cart_range(request, session_id, action, api_code)
    elif action == 'addall':
        err = _edit_cart_addall(request, session_id, api_code)
    else: # pragma: no cover
        log.error('api_edit_cart: Unknown action %s: %s', action,
                  request.GET)
        ret = HttpResponseServerError(settings.HTTP500_INTERNAL_ERROR)
        exit_api_call(api_code, ret)
        return ret

    if isinstance(err, HttpResponse):
        exit_api_call(api_code, err)
        return err

    download = request.GET.get('download', 0)
    try:
        download = int(download)
    except:
        pass
    if download:
        product_types_str = request.GET.get('types', 'all')
        product_types = product_types_str.split(',')
        info = _get_download_info(product_types, session_id)
    else:
        info = {}

    cart_count = _get_cart_count(session_id)
    info['error'] = err
    info['count'] = cart_count
    info['reqno'] = reqno

    ret = json_response(info)
    exit_api_call(api_code, ret)
    return ret


@never_cache
def api_reset_session(request):
    """Remove everything from the cart and reset the session.

    This is a PRIVATE API.

    Format: __cart/reset.json
    """
    api_code = enter_api_call('api_reset_session', request)

    if not request or request.GET is None:
        ret = Http404(settings.HTTP404_NO_REQUEST)
        exit_api_call(api_code, ret)
        raise ret

    session_id = get_session_id(request)

    sql = 'DELETE FROM '+connection.ops.quote_name('cart')
    sql += ' WHERE session_id=%s'
    values = [session_id]
    log.debug('api_reset_session SQL: %s %s', sql, values)
    cursor = connection.cursor()
    cursor.execute(sql, values)

    request.session.flush()
    session_id = get_session_id(request) # Creates a new session id
    ret = json_response('session reset')
    exit_api_call(api_code, ret)
    return ret


@never_cache
def api_create_download(request, opus_id=None):
    """Creates a zip file of all items in the cart or the given OPUS ID.

    This is a PRIVATE API.

    Format: __cart/download.json
        or: [__]api/download/(?P<opus_id>[-\w]+).zip
    Arguments: types=<PRODUCT_TYPES>
               urlonly=1 (optional) means to not zip the actual data products
    """
    api_code = enter_api_call('api_create_download', request)

    if not request or request.GET is None:
        ret = Http404(settings.HTTP404_NO_REQUEST)
        exit_api_call(api_code, ret)
        raise ret

    url_file_only = request.GET.get('urlonly', 0)

    session_id = get_session_id(request)

    product_types = request.GET.get('types', 'all')
    if product_types is None or product_types == '':
        product_types = []
    else:
        product_types = product_types.split(',')

    if opus_id:
        opus_ids = [opus_id]
        return_directly = True
    else:
        num_selections = (Cart.objects
                          .filter(session_id__exact=session_id)
                          .count())
        if url_file_only:
            max_selections = settings.MAX_SELECTIONS_FOR_URL_DOWNLOAD
        else:
            max_selections = settings.MAX_SELECTIONS_FOR_DATA_DOWNLOAD
        if num_selections > max_selections:
            ret = json_response({'error':
                                 f'Too many selections ({max_selections} max)'})
            exit_api_call(api_code, ret)
            return ret
        res = (Cart.objects.filter(session_id__exact=session_id)
               .values_list('opus_id'))
        opus_ids = [x[0] for x in res]
        return_directly = False

    if not opus_ids:
        if return_directly:
            raise Http404('No OPUSID specified')
        else:
            ret = json_response({'error': 'No observations selected'})
            exit_api_call(api_code, ret)
            return ret

    # Fetch the full file info of the files we'll be zipping up
    # We want the PdsFile objects so we can get the checksum as well as the
    # abspath
    files = get_pds_products(opus_ids, loc_type='raw',
                             product_types=product_types)

    if not files:
        ret = json_response({'error': 'No files found'})
        exit_api_call(api_code, ret)
        return ret

    zip_base_file_name = _zip_filename(opus_id, url_file_only)
    zip_root = zip_base_file_name.split('.')[0]
    zip_file_name = settings.TAR_FILE_PATH + zip_base_file_name
    chksum_file_name = settings.TAR_FILE_PATH + f'checksum_{zip_root}.txt'
    manifest_file_name = settings.TAR_FILE_PATH + f'manifest_{zip_root}.txt'
    csv_file_name = settings.TAR_FILE_PATH + f'csv_{zip_root}.txt'
    url_file_name = settings.TAR_FILE_PATH + f'url_{zip_root}.txt'

    _create_csv_file(request, csv_file_name, opus_id, api_code=api_code)

    # Don't create download if the resultant zip file would be too big
    if not url_file_only:
        info = _get_download_info(product_types, session_id)
        download_size = info['total_download_size']
        if download_size > settings.MAX_DOWNLOAD_SIZE:
            ret = json_response({'error':
                                 'Sorry, this download would require '
                                 +'{:,}'.format(download_size)
                                 +' bytes but the maximum allowed is '
                                 +'{:,}'.format(settings.MAX_DOWNLOAD_SIZE)
                                 +' bytes'})
            exit_api_call(api_code, ret)
            return ret

        # Don't keep creating downloads after user has reached their size limit
        # for this session
        cum_download_size = request.session.get('cum_download_size', 0)
        cum_download_size += download_size
        if cum_download_size > settings.MAX_CUM_DOWNLOAD_SIZE:
            ret = json_response({'error':
                                 'Sorry, maximum cumulative download size ('
                                 +'{:,}'.format(settings.MAX_CUM_DOWNLOAD_SIZE)
                                 +' bytes) reached for this session'})
            exit_api_call(api_code, ret)
            return ret
        request.session['cum_download_size'] = int(cum_download_size)

    # Add each file to the new zip file and create a manifest too
    if return_directly:
        response = HttpResponse(content_type='application/zip')
        zip_file = zipfile.ZipFile(response, mode='w')
    else:
        zip_file = zipfile.ZipFile(zip_file_name, mode='w')
    chksum_fp = open(chksum_file_name, 'w')
    manifest_fp = open(manifest_file_name, 'w')
    url_fp = open(url_file_name, 'w')

    errors = []
    added = []
    for f_opus_id in files:
        if 'Current' not in files[f_opus_id]:
            continue
        files_version = files[f_opus_id]['Current']
        for product_type in files_version:
            for file_data in files_version[product_type]:
                path = file_data['path']
                url = file_data['url']
                checksum = file_data['checksum']
                pretty_name = path.split('/')[-1]
                digest = f'{pretty_name}:{checksum}'
                mdigest = f'{f_opus_id}:{pretty_name}'

                if pretty_name not in added:
                    chksum_fp.write(digest+'\n')
                    manifest_fp.write(mdigest+'\n')
                    url_fp.write(url+'\n')
                    filename = os.path.basename(path)
                    if not url_file_only:
                        try:
                            zip_file.write(path, arcname=filename)
                        except Exception as e:
                            log.error(
            'api_create_download threw exception for opus_id %s, product_type %s, '
            +'file %s, pretty_name %s: %s',
            f_opus_id, product_type, path, pretty_name, str(e))
                            errors.append('Error adding: ' + pretty_name)
                    added.append(pretty_name)

    # Write errors to manifest file
    if errors:
        manifest_fp.write('Errors:\n')
        for e in errors:
            manifest_fp.write(e+'\n')

    # Add manifests and checksum files to tarball and close everything up
    manifest_fp.close()
    chksum_fp.close()
    url_fp.close()
    zip_file.write(chksum_file_name, arcname='checksum.txt')
    zip_file.write(manifest_file_name, arcname='manifest.txt')
    zip_file.write(csv_file_name, arcname='data.csv')
    zip_file.write(url_file_name, arcname='urls.txt')
    zip_file.close()

    os.remove(chksum_file_name)
    os.remove(manifest_file_name)
    os.remove(csv_file_name)
    os.remove(url_file_name)

    if not added:
        log.error('No files found for download cart %s', manifest_file_name)
        ret = json_response({'error': 'No files found'})
        exit_api_call(api_code, ret)
        return ret

    if return_directly:
        response['Content-Disposition'] = f'attachment; filename={zip_base_file_name}'
        ret = response
    else:
        zip_url = settings.TAR_FILE_URL_PATH + zip_base_file_name
        ret = json_response({'filename': zip_url})

    exit_api_call(api_code, '<Encoded zip file>')
    return ret


################################################################################
#
# Support routines - get information
#
################################################################################

def _get_download_info(product_types, session_id):
    """Return information about the current cart useful for download.

    The resulting totals are limited to the given product_types.
    ['all'] means return all product_types.

    Returns dict containing:
        'total_download_count':       Total number of unique files
        'total_download_size':        Total size of unique files (bytes)
        'total_download_size_pretty': Total size of unique files (pretty format)
        'product_cat_list':           List of categories and info:
            [
             [<Product Type Category>,
              [{'slug_name':            Like "browse-thumb"
                'product_type':         Like "Browse Image (thumbnail)"
                'tooltip':              User-friendly tooltip, if any
                'product_count':        Number of opus_ids in this category
                'download_count':       Number of unique files in this category
                'download_size':        Size of unique files in this category
                                            (bytes)
                'download_size_pretty': Size of unique files in this category
                                            (pretty format)
               }
              ], ...
             ], ...
            ]
    """
    cursor = connection.cursor()
    q = connection.ops.quote_name

    values = []
    sql = 'SELECT '

# The prototype query:
# SELECT obs_files.short_name,
#        count(distinct obs_files.opus_id) as product_count,
#        count(distinct obs_files.logical_path) as download_count,
#        t2.download_size as downloadsize
# FROM obs_files,
#
#      (SELECT t1.short_name, sum(t1.size) as download_size
#              FROM (SELECT DISTINCT obs_files.short_name, obs_files.logical_path, obs_files.size
#                           FROM obs_files
#                           WHERE opus_id IN ('co-iss-n1460960653', 'co-iss-n1460960868')
#                   ) as t1
#              GROUP BY t1.short_name
#      ) as t2
# WHERE obs_files.short_name=t2.short_name
#   AND obs_files.opus_id in ('co-iss-n1460960653', 'co-iss-n1460960868')
# GROUP BY obs_files.category, obs_files.sort_order, obs_files.short_name, t2.download_size
# ORDER BY sort_order;


    # For a given short_name, the category, sort_order, and full_name are
    # always the same. Thus we can group by all four and it's the same as
    # grouping by just short_name. We need them all here to return to the user.
    sql += q('obs_files')+'.'+q('category')+' AS '+q('cat')+', '
    sql += q('obs_files')+'.'+q('sort_order')+' AS '+q('sort')+', '
    sql += q('obs_files')+'.'+q('short_name')+' AS '+q('short')+', '
    sql += q('obs_files')+'.'+q('full_name')+' AS '+q('full')+', '

    # download_size is the total sizes of all distinct filenames
    # Note there is only one download_size per short_name, so when we add
    # download_size to the GROUP BY later, we aren't actually aggregating
    # anything.
    sql += q('t2')+'.'+q('download_size')+' AS '+q('download_size')+', '

    # download_count is the number of distinct filenames
    sql += 'COUNT(DISTINCT '+q('obs_files')+'.'+q('logical_path')+') AS '
    sql += q('download_count')+', '

    # product_count is the number of distinct OPUS_IDs in each group
    sql += 'COUNT(DISTINCT '+q('obs_files')+'.'+q('obs_general_id')+') AS '
    sql += q('product_count')+' '

    sql += 'FROM '

    # Nested SELECT #1
    sql += '(SELECT '+q('t1')+'.'+q('short_name')+', '
    sql += 'SUM('+q('t1')+'.'+q('size')+') AS '+q('download_size')+' '
    sql += 'FROM '

    # Nested SELECT #2
    sql += '(SELECT DISTINCT '+q('obs_files')+'.'+q('short_name')+', '
    sql += q('obs_files')+'.'+q('logical_path')+', '
    sql += q('obs_files')+'.'+q('size')+' '
    sql += 'FROM '+q('obs_files')+' '
    sql += 'INNER JOIN '+q('cart')+' ON '
    sql += q('cart')+'.'+q('obs_general_id')+'='
    sql += q('obs_files')+'.'+q('obs_general_id')+' '
    sql += 'WHERE '+q('cart')+'.'+q('session_id')+'=%s '
    values.append(session_id)
    sql += 'AND '+q('obs_files')+'.'+q('version_number')+' >= 900000'
    sql += ') AS '+q('t1')+' '
    # End of nested SELECT #2

    # Back to nested SELECT #1
    sql += 'GROUP BY '+q('t1')+'.'+q('short_name')
    sql += ') AS '+q('t2')+', '
    # End of nested SELECT #1

    sql += q('obs_files')+' '
    sql += 'INNER JOIN '+q('cart')+' ON '
    sql += q('cart')+'.'+q('obs_general_id')+'='
    sql += q('obs_files')+'.'+q('obs_general_id')+' '
    sql += 'WHERE '+q('cart')+'.'+q('session_id')+'=%s '
    values.append(session_id)
    sql += 'AND '+q('obs_files')+'.'+q('short_name')+'='
    sql += q('t2')+'.'+q('short_name')+' '
    sql += 'AND '+q('obs_files')+'.'+q('version_number')+' >= 900000 '

    sql += 'GROUP BY '+q('cat')+', '+q('sort')+', '
    sql += q('short')+', '+q('full')+' '
    sql += 'ORDER BY '+q('sort')

    log.debug('_get_download_info SQL: %s %s', sql, values)
    cursor.execute(sql, values)

    results = cursor.fetchall()

    total_download_size = 0
    total_download_count = 0
    product_cats = []
    product_cat_list = []

    for res in results:
        (category, sort_order, short_name, full_name,
         download_size, download_count, product_count) = res
        download_size = int(download_size)
        download_count = int(download_count)
        product_count = int(product_count)
        if product_types == ['all'] or short_name in product_types:
            total_download_size += download_size
            total_download_count += download_count
        pretty_name = category
        category_name = category
        if category == 'standard':
            pretty_name = 'Standard Data Products'
        elif category == 'metadata':
            pretty_name = 'Metadata Products'
        elif category == 'browse':
            pretty_name = 'Browse Products'
        elif category == 'diagram':
            pretty_name = 'Diagram Products'
        else:
            pretty_name = category + '-Specific Products'
            category_name = 'specific'
        key = (category, pretty_name)
        if key not in product_cats:
            product_cats.append(key)
            cur_product_list = []
            product_cat_list.append((pretty_name, cur_product_list, category_name))
        try:
            entry = Definitions.objects.get(context__name='OPUS_PRODUCT_TYPE',
                                            term=short_name)
            tooltip = entry.definition
        except Definitions.DoesNotExist:
            log.error('No tooltip definition for OPUS_PRODUCT_TYPE "%s"',
                      short_name)
            tooltip = None
        product_dict_entry = {
            'slug_name': short_name,
            'tooltip': tooltip,
            'product_type': full_name,
            'product_count': product_count,
            'download_count': download_count,
            'download_size': download_size,
            'download_size_pretty': nice_file_size(download_size)
        }
        cur_product_list.append(product_dict_entry)

    ret = {
        'total_download_count': total_download_count,
        'total_download_size': total_download_size,
        'total_download_size_pretty':  nice_file_size(total_download_size),
        'product_cat_list': product_cat_list
    }

    return ret


def _get_cart_count(session_id):
    "Return the number of items in the current cart."
    count = Cart.objects.filter(session_id__exact=session_id).count()
    return count


################################################################################
#
# Support routines - add or remove items from cart
#
################################################################################

def _add_to_cart_table(opus_id, session_id, api_code):
    "Add OPUS_IDs to the cart table."
    cursor = connection.cursor()
    res = (ObsGeneral.objects.filter(opus_id__exact=opus_id)
           .values_list('opus_id', 'id'))
    if len(res) != 1:
        return (f'Internal Error: OPUS ID {opus_id} not found; nothing added '
                +'to cart')

    # Note that this doesn't handle the case where some or all of the opus_ids
    # are already in the cart. It's difficult to handle this well, would slow
    # down the API, and should never happen when using the UI anyway.
    num_selections = _get_cart_count(session_id)
    if num_selections >= settings.MAX_SELECTIONS_ALLOWED:
        return (f'Your request to add OPUS ID {opus_id} to the cart failed '
                +f'- there are already too many observations there. The '
                +f'maximum allowed is {settings.MAX_SELECTIONS_ALLOWED:,d}.')

    # We use REPLACE INTO to avoid problems with duplicate entries or
    # race conditions that would be caused by deleting first and then adding.
    # Note that REPLACE INTO only works because we have a constraint on the
    # cart table that makes the fields into a unique key.
    values = [(session_id, id, opus_id) for opus_id, id in res]
    q = connection.ops.quote_name
    sql = 'REPLACE INTO '+q('cart')+' ('+q('session_id')+','
    sql += q('obs_general_id')+','+q('opus_id')+')'
    sql += ' VALUES (%s, %s, %s)'
    log.debug('_add_to_cart_table SQL: %s %s', sql, values)
    cursor.executemany(sql, values)

    return False

def _remove_from_cart_table(opus_id_list, session_id, api_code):
    "Remove OPUS_IDs from the cart table."
    cursor = connection.cursor()
    if not isinstance(opus_id_list, (list, tuple)):
        opus_id_list = [opus_id_list]
    values = [(session_id, opus_id) for opus_id in opus_id_list]
    sql = 'DELETE FROM '+connection.ops.quote_name('cart')
    sql += ' WHERE session_id=%s AND opus_id=%s'
    log.debug('_remove_from_cart_table SQL: %s %s', sql, values)
    cursor.executemany(sql, values)

    return False

def _edit_cart_range(request, session_id, action, api_code):
    "Add or remove a range of opus_ids based on the current sort order."
    id_range = request.GET.get('range', False)
    if not id_range:
        log.error('_edit_cart_range: No range given: %s', request.GET)
        ret = Http404(settings.HTTP404_BAD_OR_MISSING_RANGE)
        exit_api_call(api_code, ret)
        raise ret

    ids = id_range.split(',')
    if len(ids) != 2 or not ids[0] or not ids[1]:
        log.error('_edit_cart_range: Bad range format: %s', request.GET)
        ret = Http404(settings.HTTP404_BAD_OR_MISSING_RANGE)
        exit_api_call(api_code, ret)
        raise ret

    q = connection.ops.quote_name

    temp_table_name = None

    if request.GET.get('view', 'browse') == 'cart':
        # addrange for cart is not implemented because we don't have any
        # way to figure out what the UI thinks is in this range.
        if action == 'addrange':
            return ('Internal Error: addrange is not implemented for '+
                    'view=cart')
        # This is for the cart page - we don't have any pre-done sort order
        # so we have to do it ourselves here
        all_order = request.GET.get('order', settings.DEFAULT_SORT_ORDER)
        if not all_order:
            all_order = settings.DEFAULT_SORT_ORDER
        order_params, order_descending_params = parse_order_slug(all_order)
        (order_sql, order_mult_tables,
         order_obs_tables) = create_order_by_sql(order_params,
                                                 order_descending_params)

        cursor = connection.cursor()

        # First we create a temporary table that contains the ids of
        # observations in the cart, appropriately sorted, with a unique
        # incrementing sort_id. This is just like a user_query_table, but
        # short-lived, and we use it in the same way.
        pid_sfx = str(os.getpid())
        time1 = time.time()
        time_sfx = ('%.6f' % time1).replace('.', '_')
        params = []
        temp_table_name = 'temp_'+session_id+'_'+pid_sfx+'_'+time_sfx
        temp_sql = 'CREATE TEMPORARY TABLE '+q(temp_table_name)
        temp_sql += '(sort_order INT NOT NULL AUTO_INCREMENT, '
        temp_sql += 'PRIMARY KEY(sort_order), id INT UNSIGNED, '
        temp_sql += 'UNIQUE KEY(id)) SELECT '
        temp_sql += q('obs_general')+'.'+q('id')
        # Now JOIN all the obs_ tables together
        temp_sql += ' FROM '+q('obs_general')
        for table in sorted(order_obs_tables):
            if table == 'obs_general':
                continue
            temp_sql += ' LEFT JOIN '+q(table)+' ON '+q('obs_general')+'.'+q('id')
            temp_sql += '='+q(table)+'.'+q('obs_general_id')
        # And JOIN all the mult_ tables together
        for mult_table, category in sorted(order_mult_tables):
            temp_sql += ' LEFT JOIN '+q(mult_table)+' ON '+q(category)+'.'
            temp_sql += q(mult_table)+'='+q(mult_table)+'.'+q('id')
        temp_sql += ' INNER JOIN '+q('cart')
        temp_sql += ' ON '+q('obs_general')+'.'+q('id')+'='
        temp_sql += q('cart')+'.'+q('obs_general_id')
        temp_sql += ' AND '
        temp_sql += q('cart')+'.'+q('session_id')+'=%s'
        params.append(session_id)
        temp_sql += order_sql
        try:
            cursor.execute(temp_sql, params)
        except DatabaseError as e:
            log.error('_edit_cart_range: "%s" "%s" returned %s',
                      temp_sql, params, str(e))
            ret = HttpResponseServerError(settings.HTTP500_SEARCH_FAILED)
            return ret
        log.debug('_edit_cart_range SQL (%.2f secs): %s %s',
                  time.time()-time1, temp_sql, params)

        user_query_table = temp_table_name
    else:
        # This is for the browse page - everything is based on the
        # user_query_table

        # Find the index in the cache table for the min and max opus_ids

        (selections, extras) = url_to_search_params(request.GET)
        if selections is None:
            log.error('_edit_cart_range: Could not find selections for'
                      +' request %s', request.GET)
            ret = Http404(settings.HTTP404_SEARCH_PARAMS_INVALID)
            exit_api_call(api_code, ret)
            raise ret

        user_query_table = get_user_query_table(selections, extras,
                                                api_code=api_code)
        if not user_query_table:
            log.error('_edit_cart_range: get_user_query_table failed '
                      +'*** Selections %s *** Extras %s',
                      str(selections), str(extras))
            ret = HttpResponseServerError(settings.HTTP500_SEARCH_FAILED)
            return ret

    cursor = connection.cursor()

    sort_orders = []
    for opus_id in ids:
        sql = 'SELECT '+q('sort_order')+' FROM '+q('obs_general')
        # INNER JOIN because we only want rows that exist in the
        # user_query_table
        sql += ' INNER JOIN '+q(user_query_table)+' ON '
        sql += q(user_query_table)+'.'+q('id')+'='
        sql += q('obs_general')+'.'+q('id')
        sql += ' WHERE '+q('obs_general')+'.'+q('opus_id')+'=%s'
        values = [opus_id]
        log.debug('_edit_cart_range SQL: %s %s', sql, values)
        cursor.execute(sql, values)
        results = cursor.fetchall()
        if len(results) == 0:
            log.error('_edit_cart_range: No OPUS ID "%s" in obs_general',
                      opus_id)
            return (f'An OPUS ID was given to {action} that was not found '
                    +'using the supplied search criteria')
        sort_orders.append(results[0][0])

    sql_where  = ' WHERE '
    sql_where += q(user_query_table)+'.'+q('sort_order')
    sql_where += ' >= '+str(min(sort_orders))+' AND '
    sql_where += q(user_query_table)+'.'+q('sort_order')
    sql_where += ' <= '+str(max(sort_orders))

    if action == 'addrange':
        # Note that this doesn't handle the case where some or all of the
        # observations in the range are already in the cart. It's difficult to
        # handle this well and would slow down the API, so we're just going to
        # ignore it for now even though it's possible a user would run into
        # it when adding a range that already contains observations that are in
        # the cart.
        num_selections = _get_cart_count(session_id)

        sql_from = ' FROM '+q('obs_general')
        # INNER JOIN because we only want rows that exist in the
        # user_query_table
        sql_from += ' INNER JOIN '+q(user_query_table)+' ON '
        sql_from += q(user_query_table)+'.'+q('id')+'='
        sql_from += q('obs_general')+'.'+q('id')

        sql = 'SELECT COUNT(*)'+sql_from+sql_where
        cursor.execute(sql)
        try:
            num_new = cursor.fetchone()[0]
        except DatabaseError as e: # pragma: no cover
            log.error('_edit_cart_range: SQL query failed for request %s: '
                      +' SQL "%s" ERR "%s"', request.GET, sql, e)
            ret = HttpResponseServerError(settings.HTTP500_SQL_FAILED)
            return ret

        if num_selections+num_new > settings.MAX_SELECTIONS_ALLOWED:
            return (f'Your request to add {num_new:,d} observations ('
                    +f'OPUS IDs {ids[0]} to {ids[1]}) '
                    +f'to the cart failed. The resulting cart would have more '
                    +f'than the maximum '
                    +f'({settings.MAX_SELECTIONS_ALLOWED:,d}) '
                    +f'allowed. None of the observations were added.')

        values = [session_id]
        sql = 'REPLACE INTO '+q('cart')+' ('
        sql += q('session_id')+','+q('obs_general_id')+','+q('opus_id')+')'
        sql += ' SELECT %s,'
        sql += q('obs_general')+'.'+q('id')+','
        sql += q('obs_general')+'.'+q('opus_id')
        sql += sql_from

    elif action == 'removerange':
        values = []
        sql = 'DELETE '
        sql += q('cart')+' FROM '+q('cart')+' INNER JOIN '
        sql += q(user_query_table)+' ON '
        sql += q(user_query_table)+'.'+q('id')+'='
        sql += q('cart')+'.'+q('obs_general_id')
    else:
        log.error('_edit_cart_range: Unknown action %s: %s', action,
                  request.GET)
        ret = HttpResponseServerError(settings.HTTP500_INTERNAL_ERROR)
        return ret

    sql += sql_where

    log.debug('_edit_cart_range SQL: %s %s', sql, values)
    cursor.execute(sql, values)

    if temp_table_name:
        sql = 'DROP TABLE '+q(temp_table_name)
        try:
            cursor.execute(sql)
        except DatabaseError as e:
            log.error('_edit_cart_range: "%s" returned %s',
                      sql, str(e))
            ret = HttpResponseServerError(settings.HTTP500_INTERNAL_ERROR)
            return ret

    return False


def _edit_cart_addall(request, session_id, api_code):
    "Add all results from a search into the cart table."
    view = request.GET.get('view', 'browse')
    if view != 'browse':
        # addall for cart is not implemented because it doesn't make sense.
        return ('Internal Error: addall is not implemented for '+
                f'view={view}')

    count, user_query_table, err = get_result_count_helper(request, api_code)
    if err is not None:
        return err

    # Note that this doesn't handle the case where some or all of the
    # observations in the current search results are already in the cart. It's
    # difficult to handle this well and would slow down the API, so we're just
    # going to ignore it for now even though it's possible a user would run into
    # it when adding all from a search that already contains observations that
    # are in the cart.
    num_selections = _get_cart_count(session_id)
    if num_selections+count > settings.MAX_SELECTIONS_ALLOWED:
        return (f'Your request to add all {count:,d} observations '
                +f'to the cart failed. The resulting cart would have more '
                +f'than the maximum ({settings.MAX_SELECTIONS_ALLOWED:,d}) '
                +f'allowed. None of the observations were added.')

    cursor = connection.cursor()

    values = [session_id]
    q = connection.ops.quote_name
    sql = 'REPLACE INTO '+q('cart')+' ('
    sql += q('session_id')+','+q('obs_general_id')+','+q('opus_id')+')'
    sql += ' SELECT %s,'
    sql += q('obs_general')+'.'+q('id')+','+q('obs_general')+'.'+q('opus_id')
    sql += ' FROM '+q('obs_general')
    # INNER JOIN because we only want rows that exist in the
    # user_query_table
    sql += ' INNER JOIN '+q(user_query_table)+' ON '
    sql += q(user_query_table)+'.'+q('id')+'='+q('obs_general')+'.'+q('id')

    log.debug('_edit_cart_addall SQL: %s %s', sql, values)
    cursor.execute(sql, values)

    return False


################################################################################
#
# Support routines - Downloads
#
################################################################################


def _zip_filename(opus_id, url_file_only):
    "Create a unique .zip filename for a user's cart."
    random_ascii = random.choice(string.ascii_letters).lower()
    timestamp = "T".join(str(datetime.datetime.now()).split(' '))
    # Windows doesn't like ':' in filenames
    timestamp = timestamp.replace(':', '-')
    data_url = 'url' if url_file_only else 'data'
    if opus_id:
        return f'pdsrms-{data_url}-{random_ascii}-{timestamp}_{opus_id}.zip'
    return f'pdsrms-{data_url}-{random_ascii}-{timestamp}.zip'


def _csv_helper(request, opus_id, api_code=None):
    "Create the data for a CSV file containing the cart data."
    slugs = request.GET.get('cols', settings.DEFAULT_COLUMNS)
    (page_no, start_obs, limit, page, order, aux) = get_search_results_chunk(
                                                     request,
                                                     use_cart=(opus_id is None),
                                                     limit='all',
                                                     opus_id=opus_id,
                                                     api_code=api_code)

    slug_list = cols_to_slug_list(slugs)

    return labels_for_slugs(slug_list), page


def _create_csv_file(request, csv_file_name, opus_id, api_code=None):
    "Create a CSV file containing the cart data."
    column_labels, page = _csv_helper(request, opus_id, api_code)
    if column_labels is None:
        ret = Http404(settings.HTTP404_UNKNOWN_SLUG)
        exit_api_call(api_code, ret)
        raise ret

    with open(csv_file_name, 'a') as csv_file:
        wr = csv.writer(csv_file)
        wr.writerow(column_labels)
        wr.writerows(page)
