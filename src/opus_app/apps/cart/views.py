################################################################################
#
# cart/views.py
#
# The (private) API interface for adding and removing items from the cart
# and creating download .zip and .csv files.
#
#    Format: __cart/view.json
#    Format: __cart/status.json
#    Format: __cart/data.csv
#    Format: __cart/(?P<action>add|remove|addrange|removerange|addall).json
#    Format: __cart/reset.json
#    Format: __cart/download.json
#    Format: [__]api/download/(?P<opus_id>[-\w]+).zip
#
################################################################################

import csv
import logging
import os
import tarfile
import time
import zipfile

from django.conf import settings
from django.db import DatabaseError, connection
from django.http import Http404, HttpResponse, HttpResponseServerError
from django.template.loader import get_template
from django.views.decorators.cache import never_cache

from opus_app.apps.cart.models import Cart
from opus_app.apps.metadata.views import get_cart_count, get_result_count_helper
from opus_app.apps.results.views import (
    get_search_results_chunk,
    get_search_results_chunk_error_handler,
    labels_for_slugs,
)
from opus_app.apps.search.models import ObsGeneral
from opus_app.apps.search.views import (
    add_mult_table_joins,
    add_obs_table_joins,
    create_order_by_terms,
    get_user_query_table,
    parse_order_slug,
    url_to_search_params,
)
from opus_app.apps.tools import sql_builder
from opus_app.apps.tools.app_utils import (
    HTTP400_BAD_DOWNLOAD,
    HTTP400_BAD_OR_MISSING_RANGE,
    HTTP400_BAD_OR_MISSING_REQNO,
    HTTP400_BAD_RECYCLEBIN,
    HTTP400_MISSING_OPUS_ID,
    HTTP400_SEARCH_PARAMS_INVALID,
    HTTP400_UNKNOWN_DOWNLOAD_FILE_FORMAT,
    HTTP400_UNKNOWN_SLUG,
    HTTP404_NO_REQUEST,
    HTTP500_DATABASE_ERROR,
    HTTP500_INTERNAL_ERROR,
    HTTP500_SEARCH_CACHE_FAILED,
    Http400Error,
    api_view,
    cols_to_slug_list,
    csv_response,
    download_filename,
    get_reqno,
    get_session_id,
    json_response,
)
from opus_app.apps.tools.dictionary import Definitions
from opus_app.apps.tools.file_size import nice_file_size
from opus_app.apps.tools.file_utils import get_pds_products

log = logging.getLogger(__name__)

#: The cart table's columns, in the order every write to it supplies them.
_CART_COLUMNS = ('session_id', 'obs_general_id', 'opus_id', 'recycled')


################################################################################
#
# API INTERFACES
#
################################################################################


@never_cache
@api_view
def api_view_cart(request):
    """Return the OPUS-specific left side of the "Selections" page as HTML.

    This includes the number of files selected, total size of files selected,
    and list of product types with their number. This returns information about
    ALL files and product types, ignoring any user choices. However, there is
    an optional types=<PRODUCT_TYPES> parameter which, if specified, causes
    product types not listed to return "0" for number of products and sizes.

    This is a PRIVATE API.

    Format: __cart/view.json
    Arguments: reqno=<reqno>
               Normal search arguments
    """
    if not request or request.GET is None or request.META is None:
        raise Http404(HTTP404_NO_REQUEST('/__cart/view.html'))

    session_id = get_session_id(request)

    reqno = get_reqno(request)
    if reqno is None:
        log.error('api_view_cart: Missing or badly formatted reqno')
        raise Http400Error(HTTP400_BAD_OR_MISSING_REQNO(request))

    get_not_selected_product_types_str = request.GET.get('unselected_types', '')
    not_selected_product_types = get_not_selected_product_types_str.split(',')

    product_types_str = request.GET.get('types', 'all')
    product_types = product_types_str.split(',')

    info = _get_download_info(product_types, session_id)
    count, recycled_count = get_cart_count(session_id)

    for _name, product_versions in info['product_cat_dict'].items():
        for _ver, types in product_versions.items():
            for prod_type in types:
                if (prod_type['slug_name'] in not_selected_product_types or
                    not prod_type['default_checked']):
                    prod_type['selected'] = ''
                else:
                    prod_type['selected'] = 'checked'

    info['count'] = count
    info['recycled_count'] = recycled_count
    info['format'] = settings.DOWNLOAD_FORMATS.keys()

    cart_template = get_template('cart/cart.html')
    html = cart_template.render(info)

    return json_response({'html': html,
                          'count': info['count'],
                          'recycled_count': info['recycled_count'],
                          'reqno': reqno})


@never_cache
@api_view
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
            'count':                      Total number of items in cart NOT in
                                              recycle bin
            'recycled_count':             Total number of items in cart IN
                                              recycle bin

        If download=1:
            'total_download_count':       Total number of unique files
            'total_download_size':        Total size of unique files (bytes)
            'total_download_size_pretty': Total size of unique files (pretty format)
            'product_cat_dict':           Dict of categories and info:
                {
                  <Product Type Category>:
                    {version_name:              Like "Current", "1" or "1.0"
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
                    }
                  , ...
                }


    """
    if not request or request.GET is None or request.META is None:
        raise Http404(HTTP404_NO_REQUEST('/__cart/status.json'))

    session_id = get_session_id(request)

    reqno = get_reqno(request)
    if reqno is None:
        log.error('api_cart_status: Missing or badly formatted reqno')
        raise Http400Error(HTTP400_BAD_OR_MISSING_REQNO(request))

    download_str = request.GET.get('download', 0)
    try:
        download = int(download_str)
    except ValueError:
        download = None
    if download != 0 and download != 1:
        log.error('api_cart_status: Badly formatted download %s', download_str)
        raise Http400Error(HTTP400_BAD_DOWNLOAD(download_str, request))

    if download:
        product_types_str = request.GET.get('types', 'all')
        product_types = product_types_str.split(',')
        info = _get_download_info(product_types, session_id)
    else:
        info = {}

    count, recycled_count = get_cart_count(session_id)

    info['count'] = count
    info['recycled_count'] = recycled_count
    info['reqno'] = reqno

    return json_response(info)


@never_cache
@api_view
def api_get_cart_csv(request, *, api_code):
    """Returns a CSV file of the current cart.

    The CSV file contains the columns specified in the request.

    This is a PRIVATE API.

    Format: __cart/data.csv
            Normal selected-column arguments
    """
    if not request or request.GET is None or request.META is None:
        raise Http404(HTTP404_NO_REQUEST('/__cart/data.csv'))

    column_labels, page, error = _csv_helper(request, None, api_code)
    if error is not None:
        return get_search_results_chunk_error_handler(error)

    if column_labels is None: # pragma: no cover -
        # This should never happen because the bad slugs are caught inside
        # _csv_helper
        raise Http400Error(HTTP400_UNKNOWN_SLUG(None, request))

    csv_filename = download_filename(None, 'cart')

    return csv_response(csv_filename, page, column_labels)


@never_cache
@api_view
def api_edit_cart(request, action, *, api_code, **kwargs):
    """Add or remove items from a cart.

    This is a PRIVATE API.

    Format: __cart/
            (?P<action>add|remove|addrange|removerange|addall).json
    Arguments: opusid=<ID>                  (add, remove)
               range=<OPUS_ID>,<OPUS_ID>    (addrange, removerange)
               recyclebin=0/1               (remove, removerange, addall)
               reqno=<N>
               [download=<N>]

    Returns the new number of items in the cart.
    If download=1, also returns all the data returned by
        /__cart/status.json

    State transitions:

    add/addrange (recyclebin option ignored):
        Not previously in cart                  Add to cart recycled=0
        Previously in cart recycled=0           No effect
        Previously in cart recycled=1           Set recycled=0
        Bad opus_id                             Error

    addall recyclebin=0 (this means to take "all" from browse results or cart
                         depending on "view=")
        Not previously in cart                  Add to cart recycled=0
        Previously in cart recycled=0           No effect
        Previously in cart recycled=1           Set recycled=0

    addall recyclebin=1 (this means to take "all" from browse results or
                         cart+recycle bin depending on "view=")
        Not previously in cart                  Add to cart recycled=0
        Previously in cart recycled=0           No effect
        Previously in cart recycled=1           Set recycled=0

    remove/removerange recyclebin=0
        Not in cart                             No effect
        In cart recycled=0                      Remove from cart
        In cart recycled=1                      Remove from cart
        Bad opus_id                             No effect

    remove/removerange recyclebin=1
        Not in cart                             No effect
        In cart recycled=0                      Set recycled=1
        In cart recycled=1                      No effect
        Bad opus_id                             Error

    For addrange/removerange/addall, if view=browse then the search parameters
    are used to determine the opus_ids to operate on. If view=cart then the
    entire cart is used (with the current sort order).

    For addall, view=browse and view=cart change the source of "all".
    For view=browse, ?recyclebin is ignored. For view=cart, recyclebin is
    used to decide if only observations in the cart, or observations in the
    cart+recycle bin, are used. This means that:
                addall.json?view=cart&recyclebin=1
    can be used to move everything from the recycle bin back into the main cart.
    """
    if not request or request.GET is None or request.META is None:
        raise Http404(HTTP404_NO_REQUEST(f'/__cart/{action}.json'))

    session_id = get_session_id(request)

    reqno = get_reqno(request)
    if reqno is None:
        log.error('api_edit_cart: Missing or badly formatted reqno: %s',
                  request.GET)
        raise Http400Error(HTTP400_BAD_OR_MISSING_REQNO(request))

    opus_id = None
    if action in ('add', 'remove'):
        opus_id = request.GET.get('opusid', None)
        if not opus_id: # Also catches empty string
            log.error('api_edit_cart: Missing opusid: %s',
                      request.GET)
            raise Http400Error(HTTP400_MISSING_OPUS_ID(request))
        opus_id = opus_id.split(',')

    recycle_bin = request.GET.get('recyclebin', 0)
    try:
        recycle_bin = int(recycle_bin)
    except (TypeError, ValueError):
        # %r (not %s) so CR/LF in recycle_bin -- still the raw request string
        # when int() raised -- cannot forge extra log lines (error_analyzer
        # parses these logs line-anchored).
        log.error('api_edit_cart: Bad value for recyclebin %r: %r', recycle_bin,
                  request.GET)
        raise Http400Error(HTTP400_BAD_RECYCLEBIN(recycle_bin,
                                                  request)) from None

    if action == 'add':
        err = _add_to_cart_table(opus_id, session_id)
    elif action == 'remove':
        err = _remove_from_cart_table(opus_id, session_id, recycle_bin)
    elif action in ('addrange', 'removerange'):
        err = _edit_cart_range(request, session_id, action, recycle_bin,
                               api_code)
    elif action == 'addall':
        err = _edit_cart_addall(request, session_id, recycle_bin, api_code)
    else: # pragma: no cover - error catchall
        log.error('api_edit_cart: Unknown action %s: %s', action,
                  request.GET)
        return HttpResponseServerError(HTTP500_INTERNAL_ERROR(request))

    if isinstance(err, HttpResponse): # pragma: no cover - database error
        return err

    download_str = request.GET.get('download', 0)
    try:
        download = int(download_str)
    except ValueError:
        download = None
    if download != 0 and download != 1:
        log.error('api_edit_cart: Badly formatted download %s', download_str)
        raise Http400Error(HTTP400_BAD_DOWNLOAD(download_str, request))
    if download:
        product_types_str = request.GET.get('types', 'all')
        product_types = product_types_str.split(',')
        info = _get_download_info(product_types, session_id)
    else:
        info = {}

    count, recycled_count = get_cart_count(session_id)

    info['error'] = err
    info['count'] = count
    info['recycled_count'] = recycled_count
    info['reqno'] = reqno

    return json_response(info)


@never_cache
@api_view
def api_reset_session(request):
    """Remove everything from the cart and reset the session.

    This is a PRIVATE API.

    Format: __cart/reset.json
    Arguments: reqno=<N>
               recyclebin=0/1
               [download=<N>]

    If recyclebin=1, then only remove items from the recycle bin and leave the
    normal cart alone.

    Returns dict containing:
        In all cases:
            'count':                    Total number of items in cart NOT in
                                            recycle bin
            'recycled_count':           Total number of items in cart IN
                                            recycle bin

        If download=1:
            'total_download_count':       Total number of unique files
            'total_download_size':        Total size of unique files (bytes)
            'total_download_size_pretty': Total size of unique files (pretty format)
            'product_cat_dict':           Dict of categories and info:
                {
                  <Product Type Category>:
                    {version_name:              Like "Current", "1" or "1.0"
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
                    }
                  , ...
                }


    """
    if not request or request.GET is None or request.META is None:
        raise Http404(HTTP404_NO_REQUEST('/__cart/reset.json'))

    session_id = get_session_id(request)

    reqno = get_reqno(request)
    if reqno is None:
        log.error('api_reset_session: Missing or badly formatted reqno')
        raise Http400Error(HTTP400_BAD_OR_MISSING_REQNO(request))

    recycle_str = request.GET.get('recyclebin', 0)
    try:
        recycle_bin = int(recycle_str)
    except ValueError:
        recycle_bin = None
    if recycle_bin not in (0, 1):
        log.error('api_reset_session: Badly formatted recyclebin %s',
                  recycle_str)
        raise Http400Error(HTTP400_BAD_RECYCLEBIN(recycle_str, request))

    download_str = request.GET.get('download', 0)
    try:
        download = int(download_str)
    except ValueError:
        download = None
    if download not in (0, 1):
        log.error('api_reset_session: Badly formatted download %s', download_str)
        raise Http400Error(HTTP400_BAD_DOWNLOAD(download_str, request))

    conditions = [sql_builder.binary_op(sql_builder.column('session_id', 'cart'),
                                        '=', sql_builder.value(session_id))]
    if recycle_bin:
        # Only empty the recycle bin, leaving the rest of the cart alone.
        conditions.append(
            sql_builder.binary_op(sql_builder.column('recycled', 'cart'), '=',
                                  sql_builder.value(1)))
    sql, values = sql_builder.delete_from(
        'cart', sql_builder.join_exprs(conditions, 'AND'))
    log.debug('api_reset_session SQL: %s %s', sql, values)
    cursor = connection.cursor()
    cursor.execute(sql, values)

    if download:
        product_types_str = request.GET.get('types', 'all')
        product_types = product_types_str.split(',')
        info = _get_download_info(product_types, session_id)
    else:
        info = {}

    count, recycled_count = get_cart_count(session_id)

    info['count'] = count
    info['recycled_count'] = recycled_count
    info['reqno'] = reqno

    return json_response(info)


@never_cache
@api_view
def api_create_download(request, opus_id=None, fmt=None, *, api_code):
    r"""Creates an archive file of all items in the cart or the given OPUS ID.

    This is a PRIVATE API.

    Format: __cart/download.json
        or: [__]api/download/(?P<opus_id>[-\w]+).(?P<fmt>zip|tar|tgz)
    Arguments: types=<PRODUCT_TYPES>
               urlonly=1 (optional) means to not include the actual data products
               hierarchical=1 (optional) means files in archive are stored with
               hierarchy tree
    """
    if not request or request.GET is None or request.META is None:
        if opus_id:
            raise Http404(HTTP404_NO_REQUEST(f'/api/download/{opus_id}.{fmt}'))
        raise Http404(HTTP404_NO_REQUEST('/__cart/download.json'))

    url_file_only = request.GET.get('urlonly', 0)

    session_id = get_session_id(request)

    download_current_only = False
    product_types = request.GET.get('types', 'all')
    if product_types is None or product_types == '':
        product_types = ['all']
        download_current_only = True
    else:
        product_types = product_types.lower().split(',')
    # By default, we want to download all files of the "Current" version if types
    # parameter is not specified.
    if opus_id:
        opus_ids = [opus_id]
        return_directly = True
    else:
        num_selections = (Cart.objects
                          .filter(session_id__exact=session_id)
                          .filter(recycled=0)
                          .count())
        if url_file_only:
            max_selections = settings.MAX_SELECTIONS_FOR_URL_DOWNLOAD
            if num_selections > max_selections:
                return json_response({'error':
                      'You are attempting to download more than the maximum '
                    +f'permitted number ({max_selections}) of observations in '
                    + 'a URL archive. Please reduce the number of '
                    + 'observations you are trying to download.'})
        else:
            max_selections = settings.MAX_SELECTIONS_FOR_DATA_DOWNLOAD
            if num_selections > max_selections:
                return json_response({'error':
                      'You are attempting to download more than the maximum '
                    +f'permitted number ({max_selections}) of observations in '
                    + 'a data archive. Please either reduce the number of '
                    + 'observations you are trying to download or download a '
                    + 'URL archive instead and then retrieve the data products '
                    + 'using "wget".'})
        res = (Cart.objects
               .filter(session_id__exact=session_id)
               .filter(recycled=0)
               .values_list('opus_id'))
        opus_ids = [x[0] for x in res]
        return_directly = False

    if not opus_ids:
        return json_response({'error': 'No observations selected'})

    # Fetch the full file info of the files we'll be zipping up
    # We want the raw objects so we can get the file metadata as well as the
    # abspath
    files = get_pds_products(opus_ids, loc_type='raw',
                             product_types=product_types)

    file_type = 'url' if url_file_only else 'data'

    if not fmt:
        fmt = request.GET.get('fmt', 'zip')
    # A format given in the URL path is constrained by the route's own pattern, so
    # the only value that can fail here is the one from the query string.
    if fmt not in settings.DOWNLOAD_FORMATS:
        log.error('api_create_download: Unknown download format "%s"', fmt)
        raise Http400Error(HTTP400_UNKNOWN_DOWNLOAD_FILE_FORMAT(fmt, request))

    archive_root = download_filename(opus_id, file_type)
    archive_base_file_name = archive_root + f'.{fmt}'
    archive_file_name = settings.TAR_FILE_PATH + archive_base_file_name
    manifest_file_name = settings.MANIFEST_FILE_PATH+f'manifest_{archive_root}.csv'
    csv_file_name = settings.TAR_FILE_PATH + f'csv_{archive_root}.txt'
    url_file_name = settings.TAR_FILE_PATH + f'url_{archive_root}.txt'

    _create_csv_file(request, csv_file_name, opus_id, api_code=api_code)

    # Don't create download if the resultant archive file would be too big
    if not url_file_only:
        info = _get_download_info(product_types, session_id)
        download_size = info['total_download_size']
        if download_size > settings.MAX_DOWNLOAD_SIZE:
            return json_response({'error':
                 'Sorry, this download would require '
                 +f'{download_size:,}'
                 +' bytes but the maximum allowed is '
                 +f'{settings.MAX_DOWNLOAD_SIZE:,}'
                 +' bytes. Please either reduce the number of '
                 +'observations you are trying to download, reduce the number '
                 +'of data products for each observation, or download a URL '
                 +'archive instead and then retrieve the data products using '
                 +'"wget".'})

        # Don't keep creating downloads after user has reached their size limit
        # for this session
        cum_download_size = request.session.get('cum_download_size', 0)
        cum_download_size += download_size
        if cum_download_size > settings.MAX_CUM_DOWNLOAD_SIZE:
            return json_response({'error':
                 'Sorry, maximum cumulative download size ('
                 +f'{settings.MAX_CUM_DOWNLOAD_SIZE:,}'
                 +' bytes) reached for this session'})
        request.session['cum_download_size'] = int(cum_download_size)

    mime_type = settings.DOWNLOAD_FORMATS[fmt][0]
    write_mode = settings.DOWNLOAD_FORMATS[fmt][1]
    # Add each file to the new archive file and create a manifest too
    if return_directly:
        response = HttpResponse(content_type=mime_type)
        if fmt == 'zip':
            archive_file = zipfile.ZipFile(response, mode=write_mode)
        else:
            archive_file = tarfile.open(mode=write_mode, fileobj=response)  # noqa: SIM115
    else:
        if fmt == 'zip':
            archive_file = zipfile.ZipFile(archive_file_name, mode=write_mode)
        else:
            archive_file = tarfile.open(name=archive_file_name, mode=write_mode)  # noqa: SIM115

    # The archive, manifest, and URL handles are written incrementally across the
    # rest of this function and closed explicitly below, so a context manager does
    # not fit without restructuring the whole download-assembly block.
    manifest_fp = open(manifest_file_name, 'w')  # noqa: SIM115
    manifest_fp.write('OPUS ID,Product Category,Product Type,'
                      +'Product Type Abbrev,'
                      +'Version,File Path,Checksum,Size\n')
    url_fp = open(url_file_name, 'w')  # noqa: SIM115

    errors = []
    # Store the files' logical paths added to the zip file.
    added = []

    # Loop through files first to create a dictionary keyed by basenames. Each
    # key has a list of paths pointing to itself. If there are multiple paths
    # for a key, then it means these paths are not duplicated and need to be
    # stored with hierarchy tree in the zip file.
    hierarchical_struct = int(request.GET.get('hierarchical', 0))
    files_info = {}
    for f_opus_id in files:
        for version_name in files[f_opus_id]:
            if download_current_only and version_name != 'Current':
                continue
            files_version = files[f_opus_id][version_name]
            for product_type in files_version:
                for file_data in files_version[product_type]:
                    path = file_data['path']
                    pretty_name = path.split('/')[-1]
                    pds_version = file_data['pds_version']
                    if pds_version == 3:
                        logical_path = path[
                            path.index(settings.PDS3_HOLDINGS_DIR)+
                            len(settings.PDS3_HOLDINGS_DIR):]
                    else:
                        logical_path = path[
                            path.index(settings.PDS4_HOLDINGS_DIR)+
                            len(settings.PDS4_HOLDINGS_DIR):]
                    if pretty_name not in files_info:
                        files_info[pretty_name] = [logical_path]
                    elif logical_path not in files_info[pretty_name]:
                        files_info[pretty_name].append(logical_path)

    for f_opus_id in files:
        for version_name in files[f_opus_id]:
            if download_current_only and version_name != 'Current':
                continue
            files_version = files[f_opus_id][version_name]
            for product_type in files_version:
                for file_data in files_version[product_type]:
                    path = file_data['path']
                    url = file_data['url']
                    category = file_data['category']
                    product_type = file_data['full_name']
                    product_abbrev = file_data['short_name']
                    version_name = file_data['version_name']
                    checksum = file_data['checksum']
                    size = file_data['size']
                    pretty_name = path.split('/')[-1]
                    pds_version = file_data['pds_version']
                    if pds_version == 3:
                        logical_path = path[
                            path.index(settings.PDS3_HOLDINGS_DIR)+
                            len(settings.PDS3_HOLDINGS_DIR):]
                    else:
                        logical_path = path[
                            path.index(settings.PDS4_HOLDINGS_DIR)+
                            len(settings.PDS4_HOLDINGS_DIR):]
                    mdigest = (f'{f_opus_id},{category},{product_type},'
                              +f'{product_abbrev},{version_name},{logical_path},'
                              +f'{checksum},{size}')
                    manifest_fp.write(mdigest+'\n')

                    if logical_path not in added:
                        url_fp.write(url+'\n')
                        filename = os.path.basename(path)
                        # If hierarchical_struct is 1 or there are multiple paths
                        # for the same file basename, we store files with hierarchy
                        # tree in the zip file.
                        if hierarchical_struct or len(files_info[pretty_name]) > 1:
                            filename = logical_path
                        if not url_file_only:
                            try:
                                if fmt == 'zip':
                                    archive_file.write(path, arcname=filename)
                                else:
                                    archive_file.add(path, arcname=filename)
                            except Exception: # pragma: no cover - internal error
                                log.exception(
                                    'api_create_download threw exception for '
                                    +'opus_id %s, product_type %s, file %s, '
                                    +'pretty_name %s',
                                    f_opus_id, product_type, path, pretty_name)
                                errors.append('Error adding: ' + pretty_name)
                        added.append(logical_path)

    # Write errors to manifest file
    if errors: # pragma: no cover - internal error
        manifest_fp.write('Errors:\n')
        for e in errors:
            manifest_fp.write(e+'\n')

    # Add manifests and checksum files to tarball and close everything up
    manifest_fp.close()
    url_fp.close()
    if fmt == 'zip':
        archive_file.write(manifest_file_name, arcname='manifest.csv')
        archive_file.write(csv_file_name, arcname='data.csv')
        archive_file.write(url_file_name, arcname='urls.txt')
    else:
        archive_file.add(manifest_file_name, arcname='manifest.csv')
        archive_file.add(csv_file_name, arcname='data.csv')
        archive_file.add(url_file_name, arcname='urls.txt')
    archive_file.close()

    os.remove(csv_file_name)
    os.remove(url_file_name)

    if return_directly:
        response['Content-Disposition'] = ('attachment; filename='
                                           + archive_base_file_name)
        ret = response
    else:
        archive_url = settings.TAR_FILE_URL_PATH + archive_base_file_name
        ret = json_response({'filename': archive_url})

    return ret


################################################################################
#
# Support routines - get information
#
################################################################################

def _get_download_info(product_types, session_id):
    """Return information about the current cart useful for download.

    The resulting totals are limited to the given product_types.
    ['all'] means include all product types that are checked by default in the
    database.
    Product types for items in the recycle bin are returned with values of 0.

    Returns dict containing:
        'total_download_count':       Total number of unique files
        'total_download_size':        Total size of unique files (bytes)
        'total_download_size_pretty': Total size of unique files (pretty format)
        'product_cat_dict':           Dict of categories and info:
            {
              <Product Type Category>:
                {version_name:              Like "Current", "1" or "1.0"
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
                }
              , ...
            }
    """
    cursor = connection.cursor()

    def cart_join_condition():
        """Return the condition tying obs_files rows to their cart entries."""
        return sql_builder.columns_equal(
            sql_builder.column('obs_general_id', 'cart'),
            sql_builder.column('obs_general_id', 'obs_files'))

    def in_this_cart():
        """Return the condition restricting the cart to this session."""
        return sql_builder.binary_op(sql_builder.column('session_id', 'cart'),
                                     '=', sql_builder.value(session_id))

    def not_recycled():
        """Return the condition excluding the recycle bin."""
        return sql_builder.binary_op(sql_builder.column('recycled', 'cart'),
                                     '=', sql_builder.value(0))

    # Retrieve the distinct list of product types for all observations,
    # including the ones in the recycle bin.  This is used to allow the items
    # in the cart to be added/removed from the recycle bin and update the
    # download data panel without redrawing the cart page on every edit.
    select = sql_builder.Select(distinct=True)
    for column_name, alias in (('category', 'cat'), ('sort_order', 'sort'),
                               ('short_name', 'short'), ('full_name', 'full'),
                               ('default_checked', 'checked'),
                               ('version_name', 'ver'),
                               ('version_number', 'ver_num')):
        select.add_column(sql_builder.column(column_name, 'obs_files'),
                          alias=alias)
    select.add_from('obs_files').add_join('INNER', 'cart',
                                          cart_join_condition())
    select.add_where(in_this_cart())
    # Put "Current" version on top of others
    select.add_order_by(sql_builder.column('sort'))
    select.add_order_by(sql_builder.column('ver_num'), descending=True)

    sql, values = select.build()
    log.debug('_get_download_info SQL DISTINCT product_type list: %s %s', sql, values)
    cursor.execute(sql, values)

    results = cursor.fetchall()

    product_cats = []
    product_cat_dict = {}
    product_dict_by_short_name_ver = {}

    for res in results:
        (category, _sort_order, short_name, full_name, default_checked, ver, _ver_num) = res

        pretty_name = category
        if category == 'metadata':
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
            product_cat_dict[pretty_name] = {}
            product_cat_dict[pretty_name][ver] = cur_product_list
        else:
            if ver in product_cat_dict[pretty_name]:
                cur_product_list = product_cat_dict[pretty_name][ver]
            else:
                cur_product_list = []
                product_cat_dict[pretty_name][ver] = cur_product_list
        try:
            entry = Definitions.objects.get(context__name='OPUS_PRODUCT_TYPE',
                                            term=short_name)
            tooltip = entry.definition
        except Definitions.DoesNotExist: # pragma: no cover - import error
            log.error('No tooltip definition for OPUS_PRODUCT_TYPE "%s"',
                      short_name)
            tooltip = None
        product_dict_entry = {
            'slug_name': short_name,
            'tooltip': tooltip,
            'product_type': full_name,
            'product_count': 0,
            'download_count': 0,
            'download_size': 0,
            'download_size_pretty': 0,
            'default_checked': default_checked,
            'product_type_with_version': f'{short_name}@{ver}'
        }
        cur_product_list.append(product_dict_entry)
        short_name_ver = short_name + '@' + ver.lower()
        product_dict_by_short_name_ver[short_name_ver] = product_dict_entry


# SELECT obs_files.category,
#        obs_files.sort_order,
#        obs_files.short_name,
#        obs_files.version_name,
#        obs_files.full_name,
#        obs_files.default_checked,
#        count(distinct obs_files.opus_id) as product_count,
#        count(distinct obs_files.logical_path) as download_count,
#        t2.download_size as downloadsize
# FROM obs_files,
#
#      (SELECT t1.short_name, t1.version_name, sum(t1.size) as download_size
#              FROM (SELECT DISTINCT obs_files.short_name, obs_files.version_name,
#                                    obs_files.logical_path, obs_files.size
#                           FROM obs_files
#                           WHERE opus_id IN ('co-iss-n1460960653', 'co-iss-n1460960868')
#                   ) as t1
#              GROUP BY t1.short_name, t1.version_name
#      ) as t2
# WHERE obs_files.short_name=t2.short_name
#   AND obs_files.version_name=t2.version_name
#   AND obs_files.opus_id in ('co-iss-n1460960653', 'co-iss-n1460960868')
# GROUP BY obs_files.category, obs_files.sort_order, obs_files.short_name,
#          obs_files.version_name, obs_files.full_name, obs_files.default_checked
# ORDER BY sort_order;
    # Nested SELECT #2: the distinct files in the cart, so that a file shared by
    # two observations is only counted and sized once.
    distinct_files = sql_builder.Select(distinct=True)
    for column_name in ('short_name', 'version_name', 'logical_path', 'size'):
        distinct_files.add_column(sql_builder.column(column_name, 'obs_files'))
    distinct_files.add_from('obs_files').add_join('INNER', 'cart',
                                                  cart_join_condition())
    distinct_files.add_where(in_this_cart())
    distinct_files.add_where(not_recycled())

    # Nested SELECT #1: the total size of those files per product type.
    sizes_by_product = sql_builder.Select()
    sizes_by_product.add_column(sql_builder.column('short_name', 't1'))
    sizes_by_product.add_column(sql_builder.column('version_name', 't1'))
    sizes_by_product.add_column(sql_builder.sum_of(sql_builder.column('size',
                                                                      't1')),
                                alias='download_size')
    sizes_by_product.add_from(sql_builder.Subquery(distinct_files, 't1'))
    sizes_by_product.add_group_by(sql_builder.column('short_name', 't1'))
    sizes_by_product.add_group_by(sql_builder.column('version_name', 't1'))

    select = sql_builder.Select()

    # For a given short_name, the category, sort_order, and full_name are
    # always the same. Thus we can group by all four and it's the same as
    # grouping by just short_name. We need them all here to return to the user.
    for column_name, alias in (('category', 'cat'), ('sort_order', 'sort'),
                               ('short_name', 'short'), ('version_name', 'ver'),
                               ('full_name', 'full'),
                               ('default_checked', 'checked')):
        select.add_column(sql_builder.column(column_name, 'obs_files'),
                          alias=alias)

    # download_size is the total sizes of all distinct filenames
    # Note there is only one download_size per short_name, so when we add
    # download_size to the GROUP BY later, we aren't actually aggregating
    # anything.
    select.add_column(sql_builder.column('download_size', 't2'),
                      alias='download_size')

    # download_count is the number of distinct filenames
    select.add_column(
        sql_builder.count_distinct(sql_builder.column('logical_path',
                                                      'obs_files')),
        alias='download_count')

    # product_count is the number of distinct OPUS_IDs in each group
    select.add_column(
        sql_builder.count_distinct(sql_builder.column('obs_general_id',
                                                      'obs_files')),
        alias='product_count')

    # The per-product-type totals are cross-joined with the cart's files and
    # matched up in the WHERE clause below, which is what pairs each row with
    # its own product type's total size.
    select.add_from(sql_builder.Subquery(sizes_by_product, 't2'))
    select.add_from('obs_files').add_join('INNER', 'cart', cart_join_condition())
    select.add_where(in_this_cart())
    select.add_where(not_recycled())
    select.add_where(sql_builder.columns_equal(
        sql_builder.column('short_name', 'obs_files'),
        sql_builder.column('short_name', 't2')))
    select.add_where(sql_builder.columns_equal(
        sql_builder.column('version_name', 'obs_files'),
        sql_builder.column('version_name', 't2')))

    for alias in ('cat', 'sort', 'short', 'ver', 'full', 'checked'):
        select.add_group_by(sql_builder.column(alias))
    select.add_order_by(sql_builder.column('sort'))

    sql, values = select.build()
    log.debug('_get_download_info SQL: %s %s', sql, values)
    cursor.execute(sql, values)

    results = cursor.fetchall()

    total_download_size = 0
    total_download_count = 0

    for res in results:
        (category, _sort_order, short_name, version_name, full_name,
         checked, download_size, download_count, product_count) = res
        short_name_ver = short_name + '@' + version_name.lower()
        download_size = int(download_size)
        download_count = int(download_count)
        product_count = int(product_count)

        # Check if the files info of a product type should be added up to total download
        # info
        is_adding_up_to_total = False
        for p in product_types:
            if '@' in p:
                prod_type, _, p_version = p.partition('@')
                if p_version.lower() == 'current':
                    p_version = 'current'
                if short_name == prod_type and version_name.lower() == p_version:
                    is_adding_up_to_total = True
                    break
            elif short_name == p:
                is_adding_up_to_total = True
                break
        if (product_types == ['all'] and checked) or is_adding_up_to_total:
            total_download_size += download_size
            total_download_count += download_count

        product_dict_by_short_name_ver[short_name_ver]['product_count'] = product_count
        product_dict_by_short_name_ver[short_name_ver]['download_count'] = download_count
        product_dict_by_short_name_ver[short_name_ver]['download_size'] = download_size
        product_dict_by_short_name_ver[short_name_ver]['download_size_pretty'] = nice_file_size(download_size)

    ret = {
        'total_download_count': total_download_count,
        'total_download_size': total_download_size,
        'total_download_size_pretty':  nice_file_size(total_download_size),
        'product_cat_dict': product_cat_dict
    }

    return ret


################################################################################
#
# Support routines - add or remove items from cart
#
################################################################################

def _add_to_cart_table(opus_id_list, session_id):
    """Add OPUS_IDs to the cart table.

    Note that we don't care here if the caller set recyclebin=0 or 1 because
    we always do the same operation - put or replace the item in the cart
    with recycled=0.
    """
    cursor = connection.cursor()
    if not isinstance(opus_id_list, (list, tuple)): # pragma: no cover -
        # We currently never pass in a list
        opus_id_list = [opus_id_list]
    general_res = (ObsGeneral.objects.filter(opus_id__in=opus_id_list)
                   .values_list('opus_id', 'id'))
    if len(general_res) != len(opus_id_list):
        # There are a few things this misses - empty opus_ids and duplicate
        # opus_ids will return this same error. But it doesn't seem worth
        # trying to catch those for an internal API.
        return ('Internal Error: One or more OPUS_IDs not found; '
                +'nothing added to cart')

    num_cart_and_recycle = (Cart.objects
                            .filter(session_id__exact=session_id)
                            .count())

    # Subtract out the number of observations already in the cart, whether in
    # the recycle bin or not, since these won't count towards the total.
    incart_count = (Cart.objects
                    .filter(session_id__exact=session_id)
                    .filter(opus_id__in=opus_id_list)
                    .count())

    if (num_cart_and_recycle+len(general_res)-incart_count >
        settings.MAX_SELECTIONS_ALLOWED):
        if len(general_res) == 1:
            return (f'Your request to add OPUS ID {opus_id_list[0]} to the '
                    +'cart failed - there are already too many observations '
                    +'in the cart and recycle bin. The maximum allowed is '
                    +f'{settings.MAX_SELECTIONS_ALLOWED:,d}.')
        else:
            return ('Your request to add multiple OPUS IDs to the cart failed '
                    +'- there are already too many observations in the cart '
                    +'and recycle bin. The maximum allowed is '
                    +f'{settings.MAX_SELECTIONS_ALLOWED:,d}.')

    # We use REPLACE INTO to avoid problems with duplicate entries or
    # race conditions that would be caused by deleting first and then adding.
    # Note that REPLACE INTO only works because we have a constraint on the
    # cart table that makes the (session_id,obs_general_id) fields into a unique
    # key.
    # If the observation is already in the cart but in the recycle bin, this
    # will override that entry and set the recycled field to 0.
    values = [(session_id, obs_id, opus_id, 0) for opus_id, obs_id in general_res]
    sql = sql_builder.replace_into_values('cart', _CART_COLUMNS)
    log.debug('_add_to_cart_table SQL: %s %s', sql, values)
    cursor.executemany(sql, values)

    return False

def _remove_from_cart_table(opus_id_list, session_id, recycle_bin):
    """Remove OPUS_IDs from the cart table.

    If recycle_bin is True, then remove moves an observation into the
    recycle bin, even if it was already there. If recycle_bin is False,
    then remove deletes the entry completely.
    """
    cursor = connection.cursor()
    if not isinstance(opus_id_list, (list, tuple)): # pragma: no cover -
        # We currently never pass in a list
        opus_id_list = [opus_id_list]
    if recycle_bin:
        # If the recycle_bin flag is set, then this updates the existing entries
        # in the cart table to set recycled=1.
        res = (Cart.objects
               .filter(session_id__exact=session_id)
               .filter(opus_id__in=opus_id_list)
               .values_list('opus_id', 'obs_general_id'))
        if len(res) != len(opus_id_list):
            return ('Internal Error: One or more OPUS_IDs not found; '
                    +'nothing removed from cart')
        values = [(session_id, obs_general_id, opus_id, 1)
                  for opus_id, obs_general_id in res]
        sql = sql_builder.replace_into_values('cart', _CART_COLUMNS)
        log.debug('_remove_from_cart_table SQL: %s %s', sql, values)
        cursor.executemany(sql, values)
    else:
        # Otherwise we remove the entries completely.
        sql, values = sql_builder.delete_from(
            'cart',
            sql_builder.join_exprs(
                [sql_builder.binary_op(sql_builder.column('session_id', 'cart'),
                                       '=', sql_builder.value(session_id)),
                 sql_builder.in_sequence(sql_builder.column('opus_id', 'cart'),
                                         list(opus_id_list))], 'AND'))
        log.debug('_remove_from_cart_table SQL: %s %s', sql, values)
        cursor.execute(sql, values)
    return False

def _edit_cart_range(request, session_id, action, recycle_bin, api_code):
    "Add or remove a range of opus_ids based on the current sort order."
    id_range = request.GET.get('range', False)
    if not id_range:
        log.error('_edit_cart_range: No range given: %s', request.GET)
        raise Http400Error(HTTP400_BAD_OR_MISSING_RANGE(request))

    ids = id_range.split(',')
    if len(ids) != 2 or not ids[0] or not ids[1]:
        log.error('_edit_cart_range: Bad range format: %s', request.GET)
        raise Http400Error(HTTP400_BAD_OR_MISSING_RANGE(request))

    temp_table_name = None

    if request.GET.get('view', 'browse') == 'cart':
        # This is for the cart page - we don't have any pre-done sort order
        # so we have to do it ourselves here
        all_order = request.GET.get('order', settings.DEFAULT_SORT_ORDER)
        order_params, order_descending_params = parse_order_slug(all_order)
        # An unresolvable order slug is bad user input, not an internal failure:
        # unchecked, the None propagates into create_order_by_terms and comes
        # back out as a TypeError.
        if order_params is None:
            log.error('_edit_cart_range: Could not parse order "%s"', all_order)
            raise Http400Error(HTTP400_UNKNOWN_SLUG(None, request))
        (order_terms, order_mult_tables,
         order_obs_tables) = create_order_by_terms(order_params,
                                                   order_descending_params)
        if order_terms is None: # pragma: no cover -
            # parse_order_slug resolves every slug through the same ParamInfo
            # lookup, so it fails first; this guard is here because the function
            # documents the return, not because a route reaches it.
            log.error('_edit_cart_range: Could not build order terms for "%s"',
                      all_order)
            raise Http400Error(HTTP400_UNKNOWN_SLUG(None, request))

        cursor = connection.cursor()

        # First we create a temporary table that contains the ids of
        # observations in the cart, appropriately sorted, with a unique
        # incrementing sort_id. This is just like a user_query_table, but
        # short-lived, and we use it in the same way.
        pid_sfx = str(os.getpid())
        time1 = time.time()
        time_sfx = (f'{time1:.6f}').replace('.', '_')
        temp_table_name = 'temp_'+session_id+'_'+pid_sfx+'_'+time_sfx
        temp_select = sql_builder.Select()
        temp_select.add_column(sql_builder.column('id', 'obs_general'))
        temp_from = temp_select.add_from('obs_general')
        # Now JOIN all the obs_ tables together
        add_obs_table_joins(temp_from, sorted(order_obs_tables))
        # And JOIN all the mult_ tables together
        add_mult_table_joins(temp_from, sorted(order_mult_tables))
        temp_from.add_join(
            'INNER', 'cart',
            sql_builder.join_exprs(
                [sql_builder.columns_equal(
                    sql_builder.column('id', 'obs_general'),
                    sql_builder.column('obs_general_id', 'cart')),
                 sql_builder.binary_op(sql_builder.column('session_id', 'cart'),
                                       '=', sql_builder.value(session_id))],
                'AND'))
        for order_column, descending in order_terms:
            temp_select.add_order_by(order_column, descending=descending)
        temp_sql, params = sql_builder.create_table_as_select(
            temp_table_name, temp_select,
            column_defs=sql_builder.CACHE_TABLE_COLUMN_DEFS, temporary=True)
        try:
            cursor.execute(temp_sql, params)
        except DatabaseError: # pragma: no cover - database error
            log.exception('_edit_cart_range: "%s" "%s" failed', temp_sql, params)
            return HttpResponseServerError(HTTP500_DATABASE_ERROR(request))
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
            raise Http400Error(HTTP400_SEARCH_PARAMS_INVALID(request))

        user_query_table = get_user_query_table(selections, extras,
                                                api_code=api_code)
        if not user_query_table: # pragma: no cover - database error
            log.error('_edit_cart_range: get_user_query_table failed '
                      +'*** Selections %s *** Extras %s',
                      str(selections), str(extras))
            return HttpResponseServerError(HTTP500_SEARCH_CACHE_FAILED(request))

    cursor = connection.cursor()

    def cache_table_join_condition():
        return sql_builder.columns_equal(
            sql_builder.column('id', user_query_table),
            sql_builder.column('id', 'obs_general'))

    sort_orders = []
    for opus_id in ids:
        sort_order_select = sql_builder.Select()
        sort_order_select.add_column(sql_builder.column('sort_order'))
        # INNER JOIN because we only want rows that exist in the
        # user_query_table
        sort_order_select.add_from('obs_general').add_join(
            'INNER', user_query_table, cache_table_join_condition())
        sort_order_select.add_where(sql_builder.binary_op(
            sql_builder.column('opus_id', 'obs_general'), '=',
            sql_builder.value(opus_id)))
        sql, values = sort_order_select.build()
        log.debug('_edit_cart_range SQL: %s %s', sql, values)
        cursor.execute(sql, values)
        results = cursor.fetchall()
        if len(results) == 0:
            log.error('_edit_cart_range: No OPUS ID "%s" in obs_general',
                      opus_id)
            if request.GET.get('view', 'browse') == 'cart':
                return (f'An OPUS ID was given to {action} that was not found '
                        +'in the cart')
            else:
                return (f'An OPUS ID was given to {action} that was not found '
                        +'using the supplied search criteria')
        sort_orders.append(results[0][0])

    sort_order_column = sql_builder.column('sort_order', user_query_table)
    range_condition = sql_builder.join_exprs(
        [sql_builder.binary_op(sort_order_column, '>=',
                               sql_builder.value(min(sort_orders))),
         sql_builder.binary_op(sort_order_column, '<=',
                               sql_builder.value(max(sort_orders)))], 'AND')

    def range_from_source(restrict_to_cart):
        """Return the FROM clause selecting the observations in the range."""
        from_source = sql_builder.FromSource('obs_general')
        # INNER JOIN because we only want rows that exist in the
        # user_query_table
        from_source.add_join('INNER', user_query_table,
                             cache_table_join_condition())
        if restrict_to_cart:
            # Restrict to observations already in this session's cart
            from_source.add_join(
                'INNER', 'cart',
                sql_builder.join_exprs(
                    [sql_builder.binary_op(
                        sql_builder.column('session_id', 'cart'), '=',
                        sql_builder.value(session_id)),
                     sql_builder.columns_equal(
                         sql_builder.column('obs_general_id', 'cart'),
                         sql_builder.column('id', 'obs_general'))], 'AND'))
        return from_source

    if action == 'addrange' or (action == 'removerange' and recycle_bin):
        num_cart_and_recycle = (Cart.objects
                                .filter(session_id__exact=session_id)
                                .count())

        # removerange with recyclebin=1 only flips the recycled flag on rows that
        # are already in the cart, so its statements are restricted to those.
        restrict_to_cart = (action == 'removerange')

        if not recycle_bin:
            # We don't want to check the maximum when moving items to or from
            # the recycle bin because they go towards the same maximum either
            # way. So we should be left here with just:
            #       action == 'addrange' and not recycle_bin
            assert action == 'addrange'
            assert not recycle_bin

            # Count the number of observations we're going to add
            count_select = sql_builder.Select()
            count_select.add_column(sql_builder.count_star())
            count_select.add_from_source(range_from_source(restrict_to_cart))
            count_select.add_where(range_condition)
            sql, count_params = count_select.build()
            try:
                cursor.execute(sql, count_params)
                num_new = cursor.fetchone()[0]
            except DatabaseError: # pragma: no cover - database error
                log.exception('_edit_cart_range: SQL query failed for request '
                              +'%s: SQL "%s"', request.GET, sql)
                return HttpResponseServerError(HTTP500_DATABASE_ERROR(request))

            # Subtract the number of observations that are already in the cart.
            # We are on the addrange path here (asserted above), so the FROM
            # clause is not already restricted to the cart and this adds that
            # restriction on top of it.
            dup_select = sql_builder.Select()
            dup_select.add_column(sql_builder.count_star())
            dup_select.add_from_source(range_from_source(restrict_to_cart=True))
            dup_select.add_where(range_condition)
            sql, dup_params = dup_select.build()
            try:
                cursor.execute(sql, dup_params)
                num_old = cursor.fetchone()[0]
            except DatabaseError: # pragma: no cover - database error
                log.exception('_edit_cart_range: SQL query failed for request '
                              +'%s: SQL "%s"', request.GET, sql)
                return HttpResponseServerError(HTTP500_DATABASE_ERROR(request))

            num_wanted = num_new-num_old
            if (num_cart_and_recycle+num_wanted >
                settings.MAX_SELECTIONS_ALLOWED):
                return (f'Your request to add {num_wanted:,d} observations ('
                        +f'OPUS IDs {ids[0]} to {ids[1]}) '
                        +'to the cart failed. The resulting cart and recycle '
                        +'bin would have more than the maximum '
                        +f'({settings.MAX_SELECTIONS_ALLOWED:,d}) '
                        +'allowed. None of the observations were added.')

        # We always set recycled to "0" on addrange. If an observation is
        # already in the cart, it won't be changed. If it's in the recycle bin,
        # then it will have recycled set to 0. The recycle_bin parameter is
        # ignored.
        #
        # removerange with recyclebin=1 just means to set the recycled flag. In
        # that case the FROM clause is restricted to items already in the cart.
        recycled = 0 if action == 'addrange' else 1
        edit_select = sql_builder.Select()
        edit_select.add_column(sql_builder.value(session_id))
        edit_select.add_column(sql_builder.column('id', 'obs_general'))
        edit_select.add_column(sql_builder.column('opus_id', 'obs_general'))
        edit_select.add_column(sql_builder.value(recycled))
        edit_select.add_from_source(range_from_source(restrict_to_cart))
        edit_select.add_where(range_condition)
        sql, sql_params = sql_builder.replace_into_select('cart', _CART_COLUMNS,
                                                          edit_select)

    elif action == 'removerange': # recycle_bin == 0
        delete_from_source = sql_builder.FromSource('cart')
        delete_from_source.add_join(
            'INNER', user_query_table,
            sql_builder.columns_equal(
                sql_builder.column('id', user_query_table),
                sql_builder.column('obs_general_id', 'cart')))
        # The join above matches on obs_general_id alone, and the cart table
        # holds every session's rows, so the session has to be named here as
        # well or this deletes the observations in the range from every other
        # user's cart too. The user_query_table does not supply the restriction:
        # with view=browse it is the shared search cache table, and even with
        # view=cart, where it is a temporary table holding only this session's
        # cart, it only narrows which observations are in range -- another
        # session's row for one of those same observations still joins.
        delete_condition = sql_builder.join_exprs(
            [sql_builder.binary_op(sql_builder.column('session_id', 'cart'),
                                   '=', sql_builder.value(session_id)),
             range_condition], 'AND')
        sql, sql_params = sql_builder.delete_joined('cart', delete_from_source,
                                                    delete_condition)
    else: # pragma: no cover - error catchall
        log.error('_edit_cart_range: Unknown action %s: %s', action,
                  request.GET)
        return HttpResponseServerError(HTTP500_INTERNAL_ERROR(request))

    log.debug('_edit_cart_range SQL: %s %s', sql, sql_params)
    cursor.execute(sql, sql_params)

    if temp_table_name:
        sql = sql_builder.drop_table(temp_table_name)
        try:
            cursor.execute(sql)
        except DatabaseError: # pragma: no cover - database error
            log.exception('_edit_cart_range: "%s" failed', sql)
            return HttpResponseServerError(HTTP500_DATABASE_ERROR(request))

    return False


def _edit_cart_addall(request, session_id, recycle_bin, api_code):
    "Add all results from a search into the cart table."
    cursor = connection.cursor()
    view = request.GET.get('view', 'browse')
    if view == 'browse':
        # We ignore recycle_bin here because it doesn't mean anything
        count, user_query_table, err = get_result_count_helper(request, api_code)
        if err is not None: # pragma: no cover - database errors
            return err

        num_cart_and_recycle = (Cart.objects
                                .filter(session_id__exact=session_id)
                                .count())

        # Subtract off the number of observations already in the cart or
        # recycle bin because adding them back won't change the count.
        dup_select = sql_builder.Select()
        dup_select.add_column(sql_builder.count_star())
        # INNER JOIN because we only want rows that exist in the
        # user_query_table
        dup_select.add_from('cart').add_join(
            'INNER', user_query_table,
            sql_builder.columns_equal(
                sql_builder.column('id', user_query_table),
                sql_builder.column('obs_general_id', 'cart')))
        dup_select.add_where(sql_builder.binary_op(
            sql_builder.column('session_id', 'cart'), '=',
            sql_builder.value(session_id)))
        sql, values = dup_select.build()
        try:
            cursor.execute(sql, values)
            num_dup = cursor.fetchone()[0]
        except DatabaseError: # pragma: no cover - database error
            log.exception('_edit_cart_addall: SQL query failed for request %s: '
                          +'SQL "%s"', request.GET, sql)
            return HttpResponseServerError(HTTP500_DATABASE_ERROR(request))

        if num_cart_and_recycle+count-num_dup > settings.MAX_SELECTIONS_ALLOWED:
            return (f'Your request to add all {count:,d} observations '
                    +'to the cart failed. The resulting cart and recycle bin '
                    +'would have more than the maximum '
                    +f'({settings.MAX_SELECTIONS_ALLOWED:,d}) '
                    +'allowed. None of the observations were added.')

        addall_select = sql_builder.Select()
        addall_select.add_column(sql_builder.value(session_id))
        addall_select.add_column(sql_builder.column('id', 'obs_general'))
        addall_select.add_column(sql_builder.column('opus_id', 'obs_general'))
        # Always set recycled=0
        addall_select.add_column(sql_builder.value(0))
        # INNER JOIN because we only want rows that exist in the
        # user_query_table
        addall_select.add_from('obs_general').add_join(
            'INNER', user_query_table,
            sql_builder.columns_equal(
                sql_builder.column('id', user_query_table),
                sql_builder.column('id', 'obs_general')))
        sql, values = sql_builder.replace_into_select('cart', _CART_COLUMNS,
                                                      addall_select)

        log.debug('_edit_cart_addall SQL: %s %s', sql, values)
        cursor.execute(sql, values)

    elif view == 'cart':
        # Here recycle_bin determines whether or not we ignore the recycled
        # column. Admittedly view=cart&recyclebin=0 is silly, but we still
        # allow it and just don't do anything.
        if recycle_bin:
            sql, values = sql_builder.update(
                'cart', [('recycled', 0)],
                sql_builder.binary_op(sql_builder.column('session_id', 'cart'),
                                      '=', sql_builder.value(session_id)))
            log.debug('_edit_cart_addall SQL: %s %s', sql, values)
            cursor.execute(sql, values)

    else: # pragma: no cover - error catchall
        log.error('_edit_cart_addall: Bad view %s', view)

    return False


################################################################################
#
# Support routines - Downloads
#
################################################################################


def _csv_helper(request, opus_id, api_code=None):
    "Create the data for a CSV file containing the cart data."
    slugs = request.GET.get('cols', settings.DEFAULT_COLUMNS)
    (_page_no, _start_obs, _limit,
     page, _order, _aux, error) = get_search_results_chunk(
                                                     request,
                                                     use_cart=(opus_id is None),
                                                     ignore_recycle_bin=True,
                                                     limit='all',
                                                     opus_id=opus_id,
                                                     api_code=api_code)

    slug_list = cols_to_slug_list(slugs)

    return labels_for_slugs(slug_list), page, error


def _create_csv_file(request, csv_file_name, opus_id, api_code=None):
    "Create a CSV file containing the cart data."
    column_labels, page, error = _csv_helper(request, opus_id, api_code)
    if error is not None:
        return get_search_results_chunk_error_handler(error)

    if column_labels is None: # pragma: no cover -
        # This should never happen because the bad slugs are caught inside
        # _csv_helper
        raise Http400Error(HTTP400_UNKNOWN_SLUG(None, request))

    with open(csv_file_name, 'a') as csv_file:
        wr = csv.writer(csv_file)
        wr.writerow(column_labels)
        wr.writerows(page)
