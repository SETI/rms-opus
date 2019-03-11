################################################################################
#
# results/views.py
#
# The (private) API interface for adding and removing items from the collection
# and creating download .zip and .csv files.
#
#    Format: __collections/view.(html|json)
#    Format: __collections/status.json
#    Format: __collections/data.csv
#    Format: __collections/(?P<action>add|remove|addrange|removerange|addall).json
#    Format: __collections/reset.html
#    Format: __collections/download.json
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

from django.db import connection
from django.http import HttpResponse, HttpResponseNotFound, Http404
from django.shortcuts import render
from django.views.decorators.cache import never_cache

from hurry.filesize import size as nice_file_size

from dictionary.models import Definitions
from results.views import (get_search_results_chunk,
                           labels_for_slugs)
from search.models import ObsGeneral
from search.views import (url_to_search_params,
                          get_user_query_table)
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
    ALL files and product types, ignoring any user choices. However, there is
    an optional types=<PRODUCT_TYPES> parameter which, if specified, causes
    product types not listed to return "0" for number of products and sizes.

    This is a PRIVATE API.

    Format: __collections/view.html

    For HTML format, returns the left side of the Selections page.
    """
    api_code = enter_api_call('api_view_collection', request)

    session_id = get_session_id(request)

    product_types = ['all']

    info = _get_download_info(product_types, session_id)

    template = 'user_collections/collections.html'
    ret = render(request, template, info)

    exit_api_call(api_code, ret)
    return ret


@never_cache
def api_collection_status(request):
    """Return the number of items in a collection.

    It is used to update the "Selections <N>" tab in the OPUS UI.

    This is a PRIVATE API.

    Format: __collections/status.json
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
    api_code = enter_api_call('api_collection_status', request)

    session_id = get_session_id(request)

    reqno = get_reqno(request)
    if reqno is None:
        log.error('api_collection_status: Missing or badly formatted reqno')
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

    count = _get_collection_count(session_id)

    info['count'] = count
    info['reqno'] = reqno
    ret = json_response(info)
    exit_api_call(api_code, ret)
    return ret


@never_cache
def api_get_collection_csv(request):
    """Returns a CSV file of the current collection.

    The CSV file contains the columns specified in the request.

    This is a PRIVATE API.

    Format: __collections/data.csv
            Normal selected-column arguments
    """
    api_code = enter_api_call('api_get_collection_csv', request)

    column_labels, page = _csv_helper(request, api_code)
    if column_labels is None:
        ret = Http404(settings.HTTP404_UNKNOWN_SLUG)
        exit_api_call(api_code, ret)
        raise ret

    ret = csv_response('data', page, column_labels)

    exit_api_call(api_code, ret)
    return ret


@never_cache
def api_edit_collection(request, **kwargs):
    """Add or remove items from a collection.

    This is a PRIVATE API.

    Format: __collections/
            (?P<action>add|remove|addrange|removerange|addall).json
    Arguments: opus_id=<ID>                 (add, remove)
               range=<OPUS_ID>,<OPUS_ID>    (addrange, removerange)
               reqno=<N>
               [download=<N>]

    Returns the new number of items in the collection.
    If download=1, also returns all the data returned by
        /__collections/status.json
    """
    api_code = enter_api_call('api_edit_collection', request)

    session_id = get_session_id(request)

    try:
        action = kwargs['action']
    except KeyError:
        exit_api_call(api_code, None)
        raise Http404

    reqno = get_reqno(request)
    if reqno is None:
        log.error('api_edit_collection: Missing or badly formatted reqno')
        ret = Http404(settings.HTTP404_MISSING_REQNO)
        exit_api_call(api_code, ret)
        raise ret

    err = False

    opus_id = None
    if action in ('add', 'remove'):
        opus_id = request.GET.get('opusid', None)
        if not opus_id: # Also catches empty string
            err = 'No opusid specified'

    if not err:
        if action == 'add':
            err = _add_to_collections_table(opus_id, session_id, api_code)
        elif action == 'remove':
            err = _remove_from_collections_table(opus_id, session_id, api_code)
        elif action in ('addrange', 'removerange'):
            err = _edit_collection_range(request, session_id, action, api_code)
        elif action == 'addall':
            err = _edit_collection_addall(request, session_id, api_code)
        else:
            assert False

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

    collection_count = _get_collection_count(session_id)
    info['error'] = err
    info['count'] = collection_count
    info['reqno'] = reqno

    ret = json_response(info)
    exit_api_call(api_code, ret)
    return ret


@never_cache
def api_reset_session(request):
    """Remove everything from the collection and reset the session.

    This is a PRIVATE API.

    Format: __collections/reset.json
    """
    api_code = enter_api_call('api_reset_session', request)

    session_id = get_session_id(request)

    sql = 'DELETE FROM '+connection.ops.quote_name('collections')
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
    """Creates a zip file of all items in the collection or the given OPUS ID.

    This is a PRIVATE API.

    Format: __collections/download.json
        or: [__]api/download/(?P<opus_id>[-\w]+).zip
    Arguments: types=<PRODUCT_TYPES>
               urlonly=1 (optional) means to not zip the actual data products
    """
    api_code = enter_api_call('api_create_download', request)

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
        num_selections = (Collections.objects
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
        res = (Collections.objects.filter(session_id__exact=session_id)
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

    _create_csv_file(request, csv_file_name, api_code=api_code)

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
    """Return information about the current collection useful for download.

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
    sql += 'INNER JOIN '+q('collections')+' ON '
    sql += q('collections')+'.'+q('obs_general_id')+'='
    sql += q('obs_files')+'.'+q('obs_general_id')+' '
    sql += 'WHERE '+q('collections')+'.'+q('session_id')+'=%s '
    values.append(session_id)
    sql += 'AND '+q('obs_files')+'.'+q('version_number')+' >= 900000'
    sql += ') AS '+q('t1')+' '
    # End of nested SELECT #2

    # Back to nested SELECT #1
    sql += 'GROUP BY '+q('t1')+'.'+q('short_name')
    sql += ') AS '+q('t2')+', '
    # End of nested SELECT #1

    sql += q('obs_files')+' '
    sql += 'INNER JOIN '+q('collections')+' ON '
    sql += q('collections')+'.'+q('obs_general_id')+'='
    sql += q('obs_files')+'.'+q('obs_general_id')+' '
    sql += 'WHERE '+q('collections')+'.'+q('session_id')+'=%s '
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
        key = (category, pretty_name)
        if key not in product_cats:
            product_cats.append(key)
            cur_product_list = []
            product_cat_list.append((pretty_name, cur_product_list))
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


def _get_collection_count(session_id):
    "Return the number of items in the current collection."
    count = Collections.objects.filter(session_id__exact=session_id).count()
    return count


################################################################################
#
# Support routines - add or remove items from collections
#
################################################################################

def _add_to_collections_table(opus_id_list, session_id, api_code):
    "Add OPUS_IDs to the collections table."
    cursor = connection.cursor()
    if not isinstance(opus_id_list, (list, tuple)):
        opus_id_list = [opus_id_list]
    res = (ObsGeneral.objects.filter(opus_id__in=opus_id_list)
           .values_list('opus_id', 'id'))
    if len(opus_id_list) != len(res):
        return 'opusid not found'

    # We use REPLACE INTO to avoid problems with duplicate entries or
    # race conditions that would be caused by deleting first and then adding.
    # Note that REPLACE INTO only works because we have a constraint on the
    # collections table that makes the fields into a unique key.
    values = [(session_id, id, opus_id) for opus_id, id in res]
    q = connection.ops.quote_name
    sql = 'REPLACE INTO '+q('collections')+' ('+q('session_id')+','
    sql += q('obs_general_id')+','+q('opus_id')+')'
    sql += ' VALUES (%s, %s, %s)'
    log.debug('_add_to_collections_table SQL: %s %s', sql, values)
    cursor.executemany(sql, values)

    return False

def _remove_from_collections_table(opus_id_list, session_id, api_code):
    "Remove OPUS_IDs from the collections table."
    cursor = connection.cursor()
    if not isinstance(opus_id_list, (list, tuple)):
        opus_id_list = [opus_id_list]
    values = [(session_id, opus_id) for opus_id in opus_id_list]
    sql = 'DELETE FROM '+connection.ops.quote_name('collections')
    sql += ' WHERE session_id=%s AND opus_id=%s'
    log.debug('_remove_from_collections_table SQL: %s %s', sql, values)
    cursor.executemany(sql, values)

    return False

def _edit_collection_range(request, session_id, action, api_code):
    "Add or remove a range of opus_ids based on the current sort order."
    id_range = request.GET.get('range', False)
    if not id_range:
        return 'no range given'

    ids = id_range.split(',')
    if len(ids) != 2:
        return 'bad range'

    if not ids[0] or not ids[1]:
        return 'bad range'

    # Find the index in the cache table for the min and max opus_ids

    (selections, extras) = url_to_search_params(request.GET)
    if selections is None:
        log.error('_edit_collection_range: Could not find selections for'
                  +' request %s', str(request.GET))
        return 'bad search'

    user_query_table = get_user_query_table(selections, extras,
                                            api_code=api_code)
    if not user_query_table:
        log.error('_edit_collection_range: get_user_query_table failed '
                  +'*** Selections %s *** Extras %s',
                  str(selections), str(extras))
        return 'search failed'

    cursor = connection.cursor()

    sort_orders = []
    q = connection.ops.quote_name
    for opus_id in ids:
        sql = 'SELECT '+q('sort_order')+' FROM '+q('obs_general')
        # INNER JOIN because we only want rows that exist in the
        # user_query_table
        sql += ' INNER JOIN '+q(user_query_table)+' ON '
        sql += q(user_query_table)+'.'+q('id')+'='
        sql += q('obs_general')+'.'+q('id')
        sql += ' WHERE '+q('obs_general')+'.'+q('opus_id')+'=%s'
        values = [opus_id]
        log.debug('_edit_collection_range SQL: %s %s', sql, values)
        cursor.execute(sql, values)
        results = cursor.fetchall()
        if len(results) == 0:
            log.error('_edit_collection_range: No OPUS ID "%s" in obs_general',
                      opus_id)
            return 'opusid not found'
        sort_orders.append(results[0][0])

    if action == 'addrange':
        values = [session_id]
        sql = 'REPLACE INTO '+q('collections')+' ('
        sql += q('session_id')+','+q('obs_general_id')+','+q('opus_id')+')'
        sql += ' SELECT %s,'
        sql += q('obs_general')+'.'+q('id')+','
        sql += q('obs_general')+'.'+q('opus_id')+' FROM '+q('obs_general')
        # INNER JOIN because we only want rows that exist in the
        # user_query_table
        sql += ' INNER JOIN '+q(user_query_table)+' ON '
        sql += q(user_query_table)+'.'+q('id')+'='+q('obs_general')+'.'+q('id')

    elif action == 'removerange':
        values = []
        sql = 'DELETE '
        sql += q('collections')+' FROM '+q('collections')+' INNER JOIN '
        sql += q(user_query_table)+' ON '
        sql += q(user_query_table)+'.'+q('id')+'='
        sql += q('collections')+'.'+q('obs_general_id')
    else:
        assert False

    sql += ' WHERE '
    sql += q(user_query_table)+'.'+q('sort_order')
    sql += ' >= '+str(min(sort_orders))+' AND '
    sql += q(user_query_table)+'.'+q('sort_order')
    sql += ' <= '+str(max(sort_orders))
    log.debug('_edit_collection_range SQL: %s %s', sql, values)
    cursor.execute(sql, values)

    return False


def _edit_collection_addall(request, session_id, api_code):
    "Add all results from a search into the collections table."
    # Find the index in the cache table for the min and max opus_ids
    (selections, extras) = url_to_search_params(request.GET)
    if selections is None:
        log.error('_edit_collection_addall: Could not find selections for'
                  +' request %s', str(request.GET))
        return 'bad search'

    user_query_table = get_user_query_table(selections, extras,
                                            api_code=api_code)
    if not user_query_table:
        log.error('_edit_collection_addall: get_user_query_table failed '
                  +'*** Selections %s *** Extras %s',
                  str(selections), str(extras))
        return 'search failed'

    cursor = connection.cursor()

    values = [session_id]
    q = connection.ops.quote_name
    sql = 'REPLACE INTO '+q('collections')+' ('
    sql += q('session_id')+','+q('obs_general_id')+','+q('opus_id')+')'
    sql += ' SELECT %s,'
    sql += q('obs_general')+'.'+q('id')+','+q('obs_general')+'.'+q('opus_id')
    sql += ' FROM '+q('obs_general')
    # INNER JOIN because we only want rows that exist in the
    # user_query_table
    sql += ' INNER JOIN '+q(user_query_table)+' ON '
    sql += q(user_query_table)+'.'+q('id')+'='+q('obs_general')+'.'+q('id')

    log.debug('_edit_collection_addall SQL: %s %s', sql, values)
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


def _csv_helper(request, api_code=None):
    "Create the data for a CSV file containing the collection data."
    slugs = request.GET.get('cols', settings.DEFAULT_COLUMNS)
    (page_no, start_obs, limit, page, order, aux) = get_search_results_chunk(
                                                     request,
                                                     use_collections=True,
                                                     limit='all',
                                                     api_code=api_code)

    slug_list = cols_to_slug_list(slugs)

    return labels_for_slugs(slug_list), page


def _create_csv_file(request, csv_file_name, api_code=None):
    "Create a CSV file containing the collection data."
    column_labels, page = _csv_helper(request, api_code)
    if column_labels is None:
        ret = Http404(settings.HTTP404_UNKNOWN_SLUG)
        exit_api_call(api_code, ret)
        raise ret

    with open(csv_file_name, 'a') as csv_file:
        wr = csv.writer(csv_file)
        wr.writerow(column_labels)
        wr.writerows(page)
