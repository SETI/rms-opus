
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
#    Format: __zip/(?P<opus_id>[-\w]+).zip
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
from search.views import (get_param_info_by_slug,
                          url_to_search_params,
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
def api_view_collection(request, fmt):
    """Return the OPUS-specific left side of the "Selections" page as HTML.

    This includes the number of files selected, total size of files selected,
    and list of product types with their number. This returns information about
    ALL files and product types, ignoring any user choices. However, there is
    an optional types=<PRODUCT_TYPES> parameter which, if specified, causes
    product types not listed to return "0" for number of products and sizes.

    This is a PRIVATE API.

    Format: __collections/view.(html|json)
    Arguments: types=<PRODUCT_TYPES>

    For HTML format, returns the left side of the Selections page.

    For JSON format, returns a dict containing:
        'total_download_count':       Total number of unique files
        'total_download_size':        Total size of unique files (bytes)
        'total_download_size_pretty': Total size of unique files (pretty format)
        'product_cat_list':           List of categories and info:
            [
             ['<Product Type Category>',
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
    api_code = enter_api_call('api_view_collection', request)

    session_id = get_session_id(request)

    product_types_str = request.GET.get('types', 'all')
    product_types = product_types_str.split(',')

    info = _get_download_info(product_types, session_id)

    if fmt == 'json':
        ret = json_response(info)
    else:
        assert fmt == 'html'
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
    """
    api_code = enter_api_call('api_collection_status', request)

    session_id = get_session_id(request)

    count = _get_collection_count(session_id)

    reqno = request.GET.get('reqno', None)
    try:
        reqno = int(reqno)
    except:
        pass

    ret = json_response({'count': count,
                         'reqno': reqno})
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
               [reqno=<N>]
               [download=<N>]

    Returns the new number of items in the collection.
    If download=1, also returns all the data returns by
        /__collections/status.json
    """
    api_code = enter_api_call('api_edit_collection', request)

    session_id = get_session_id(request)

    try:
        action = kwargs['action']
    except KeyError:
        exit_api_call(api_code, None)
        raise Http404

    reqno = request.GET.get('reqno', None)
    try:
        reqno = int(reqno)
    except:
        pass

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

    collection_count = _get_collection_count(session_id)
    json_data = {'err': err,
                 'count': collection_count,
                 'reqno': reqno}

    download = request.GET.get('download', False)
    try:
        download = int(download)
    except:
        pass
    # Minor performance check - if we don't need a total download size, don't
    # bother
    # Only the selection tab is interested in updating that count at this time.
    if download:
        product_types_str = request.GET.get('types', 'all')
        product_types = product_types_str.split(',')
        info = _get_download_info(product_types, session_id)
        json_data.update(info)

    ret = json_response(json_data)
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
        or: __zip/(?P<opus_id>[-\w]+).zip
    Arguments: types=<PRODUCT_TYPES>
    """
    api_code = enter_api_call('api_create_download', request)

    session_id = get_session_id(request)

    if opus_id:
        product_types = ['all']
        opus_ids = [opus_id]
        return_directly = True
    else:
        product_types = request.GET.get('types', 'none')
        product_types = product_types.split(',')
        opus_ids = get_all_in_collection(request)
        return_directly = False

    if not opus_ids:
        if return_directly:
            raise Http404("No OPUSID specified")
        else:
            raise Http404("No observations selected")

    zip_base_file_name = _zip_filename()
    zip_root = zip_base_file_name.split('.')[0]
    zip_file_name = settings.TAR_FILE_PATH + zip_base_file_name
    chksum_file_name = settings.TAR_FILE_PATH + f'checksum_{zip_root}.txt'
    manifest_file_name = settings.TAR_FILE_PATH + f'manifest_{zip_root}.txt'
    csv_file_name = settings.TAR_FILE_PATH + f'csv_{zip_root}.txt'

    _create_csv_file(request, csv_file_name, api_code=api_code)

    # Fetch the full file info of the files we'll be zipping up
    # We want the PdsFile objects so we can get the checksum as well as the
    # abspath
    files = get_pds_products(opus_ids, None, loc_type='raw',
                             product_types=product_types)

    if not files:
        raise Http404("No files found")

    info = _get_download_info(product_types, session_id)
    download_size = info['total_download_size']
    # Don't create download if the resultant zip file would be too big
    if download_size > settings.MAX_DOWNLOAD_SIZE:
        ret = HttpResponse('Sorry, this download would require '
                           +'{:,}'.format(download_size)
                           +' bytes but the maximum allowed is '
                           +'{:,}'.format(settings.MAX_DOWNLOAD_SIZE)
                           +' bytes')
        exit_api_call(api_code, ret)
        return ret

    # Don't keep creating downloads after user has reached their size limit
    # for this session
    cum_download_size = request.session.get('cum_download_size', 0)
    cum_download_size += download_size
    if cum_download_size > settings.MAX_CUM_DOWNLOAD_SIZE:
        ret = HttpResponse('Sorry, maximum cumulative download size ('
                           +'{:,}'.format(settings.MAX_CUM_DOWNLOAD_SIZE)
                           +' bytes) reached for this session')
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

    errors = []
    added = []
    for opus_id in files:
        if 'Current' not in files[opus_id]:
            continue
        files_version = files[opus_id]['Current']
        for product_type in files_version:
            for pdsf in files_version[product_type]:
                f = pdsf.abspath
                pretty_name = f.split('/')[-1]
                digest = f'{pretty_name}:{pdsf.checksum}'
                mdigest = f'{opus_id}:{pretty_name}'

                if pretty_name not in added:
                    chksum_fp.write(digest+'\n')
                    manifest_fp.write(mdigest+'\n')
                    filename = os.path.basename(f)
                    try:
                        zip_file.write(f, arcname=filename)
                        added.append(pretty_name)
                    except Exception as e:
                        log.error(
        'api_create_download threw exception for opus_id %s, product_type %s, '
        +'file %s, pretty_name %s: %s',
        opus_id, product_type, f, pretty_name, str(e))
                        errors.append('Error adding: ' + pretty_name)

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

    if not added:
        log.error('No files found for download cart %s', manifest_file_name)
        raise Http404('No files found')

    if return_directly:
        response['Content-Disposition'] = f'attachment; filename={zip_base_file_name}'
        ret = response
    else:
        zip_url = settings.TAR_FILE_URL_PATH + zip_base_file_name
        ret = json_response(zip_url)

    exit_api_call(api_code, '<Encoded zip file>')
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

    Returns dict containing:
        'total_download_count':       Total number of unique files
        'total_download_size':        Total size of unique files (bytes)
        'total_download_size_pretty': Total size of unique files (pretty format)
        'product_cat_list':           List of categories and info:
            [
             ['<Product Type Category>',
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
    opus_ids = (Collections.objects.filter(session_id__exact=session_id)
                .values_list('opus_id'))
    opus_id_list = [x[0] for x in opus_ids]

    (total_download_size, total_download_count,
     product_counts) = get_product_counts(opus_id_list,
                                          product_types=product_types)

    product_cats = []
    product_cat_list = []
    for (product_type, product_count,
         download_count, download_size) in product_counts:
        # product_type format is:
        #   ('Cassini ISS', 0, 'coiss-raw', 'Raw image')
        #   ('browse', 40, 'browse-full', 'Browse Image (full-size)')
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
            cur_product_list = []
            product_cat_list.append((pretty_name, cur_product_list))
        product_dict_entry = {
            'slug_name': product_type[2],
            'product_type': product_type[3],
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
    sql = 'REPLACE INTO '+connection.ops.quote_name('collections')
    sql += ' ('
    sql += connection.ops.quote_name('session_id')+','
    sql += connection.ops.quote_name('obs_general_id')+','
    sql += connection.ops.quote_name('opus_id')+')'
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
    for opus_id in ids:
        sql = 'SELECT '
        sql += connection.ops.quote_name('sort_order')
        sql += ' FROM '
        sql += connection.ops.quote_name('obs_general')
        # INNER JOIN because we only want rows that exist in the
        # user_query_table
        sql += ' INNER JOIN '
        sql += connection.ops.quote_name(user_query_table)
        sql += ' ON '
        sql += connection.ops.quote_name(user_query_table)+'.'
        sql += connection.ops.quote_name('id')+'='
        sql += connection.ops.quote_name('obs_general')+'.'
        sql += connection.ops.quote_name('id')
        sql += ' WHERE '
        sql += connection.ops.quote_name('obs_general')+'.'
        sql += connection.ops.quote_name('opus_id')+'=%s'
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
        sql = 'REPLACE INTO '+connection.ops.quote_name('collections')
        sql += ' ('
        sql += connection.ops.quote_name('session_id')+','
        sql += connection.ops.quote_name('obs_general_id')+','
        sql += connection.ops.quote_name('opus_id')+')'
        sql += ' SELECT %s,'
        sql += connection.ops.quote_name('obs_general')+'.'
        sql += connection.ops.quote_name('id')+','
        sql += connection.ops.quote_name('obs_general')+'.'
        sql += connection.ops.quote_name('opus_id')
        sql += ' FROM '
        sql += connection.ops.quote_name('obs_general')
        # INNER JOIN because we only want rows that exist in the
        # user_query_table
        sql += ' INNER JOIN '
        sql += connection.ops.quote_name(user_query_table)
        sql += ' ON '
        sql += connection.ops.quote_name(user_query_table)+'.'
        sql += connection.ops.quote_name('id')+'='
        sql += connection.ops.quote_name('obs_general')+'.'
        sql += connection.ops.quote_name('id')

    elif action == 'removerange':
        values = []
        sql = 'DELETE '
        sql += connection.ops.quote_name('collections')
        sql += ' FROM '+connection.ops.quote_name('collections')
        sql += ' INNER JOIN '
        sql += connection.ops.quote_name(user_query_table)
        sql += ' ON '
        sql += connection.ops.quote_name(user_query_table)+'.'
        sql += connection.ops.quote_name('id')+'='
        sql += connection.ops.quote_name('collections')+'.'
        sql += connection.ops.quote_name('obs_general_id')
    else:
        assert False

    sql += ' WHERE '
    sql += connection.ops.quote_name(user_query_table)+'.'
    sql += connection.ops.quote_name('sort_order')
    sql += ' >= '+str(min(sort_orders))+' AND '
    sql += connection.ops.quote_name(user_query_table)+'.'
    sql += connection.ops.quote_name('sort_order')
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
    sql = 'REPLACE INTO '+connection.ops.quote_name('collections')
    sql += ' ('
    sql += connection.ops.quote_name('session_id')+','
    sql += connection.ops.quote_name('obs_general_id')+','
    sql += connection.ops.quote_name('opus_id')+')'
    sql += ' SELECT %s,'
    sql += connection.ops.quote_name('obs_general')+'.'
    sql += connection.ops.quote_name('id')+','
    sql += connection.ops.quote_name('obs_general')+'.'
    sql += connection.ops.quote_name('opus_id')
    sql += ' FROM '
    sql += connection.ops.quote_name('obs_general')
    # INNER JOIN because we only want rows that exist in the
    # user_query_table
    sql += ' INNER JOIN '
    sql += connection.ops.quote_name(user_query_table)
    sql += ' ON '
    sql += connection.ops.quote_name(user_query_table)+'.'
    sql += connection.ops.quote_name('id')+'='
    sql += connection.ops.quote_name('obs_general')+'.'
    sql += connection.ops.quote_name('id')

    log.debug('_edit_collection_addall SQL: %s %s', sql, values)
    cursor.execute(sql, values)

    return False


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


def _csv_helper(request, api_code=None):
    "Create the data for a CSV file containing the collection data."
    slugs = request.GET.get('cols', settings.DEFAULT_COLUMNS)
    (page_no, start_obs, limit, page, order, aux) = get_search_results_chunk(
                                                     request,
                                                     use_collections=True,
                                                     limit='all',
                                                     api_code=api_code)

    slug_list = slugs.split(',')
    column_labels = []
    for slug in slug_list:
        pi = get_param_info_by_slug(slug)
        if pi is None:
            log.error('_create_csv_file: Unknown slug "%s"', slug)
            return HttpResponseNotFound('Unknown slug')
        else:
            # append units if pi_units has unit stored
            unit = pi.get_units()
            label = pi.body_qualified_label_results()
            if unit:
                column_labels.append(label + ' ' + unit)
            else:
                column_labels.append(label)

    return column_labels, page


def _create_csv_file(request, csv_file_name, api_code=None):
    "Create a CSV file containing the collection data."
    column_labels, page = _csv_helper(request, api_code)

    with open(csv_file_name, 'a') as csv_file:
        wr = csv.writer(csv_file)
        wr.writerow(column_labels)
        wr.writerows(page)
