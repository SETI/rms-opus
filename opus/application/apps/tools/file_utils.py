################################################################################
#
# tools/file_utils.py
#
# This file contains utilities that interact with the obs_files table.
#
################################################################################

from collections import OrderedDict

from django.core.exceptions import ObjectDoesNotExist
from django.db import connection

from search.models import ObsGeneral

import settings

import pdsviewable

import logging
log = logging.getLogger(__name__)


def get_pds_products(opus_id_list,
                     loc_type='url',
                     product_types=['all']):
    """Return all PDS products for a given opus_id(s) organized by version.

    The returned dict is indexed by opus_id and is in the same order as the
    original opus_id_list.

    For each opus_id in the returned dict, there is a dict indexed by
    version that contains another dict. For each version in this dict, there
    is an entry per product_type in the format
        (category, sort_order, slug, pretty_name).
    The dict is sorted as defined in in obs_files.

    opus_id_list can be a string or a list.

    WARNING: The returned OrderedDict() is not currently guaranteed to be in the same
             order as opus_id_list. Instead it is in a sorted order.

    product_types can be a simple string, a comma-separated string, or a list.
        'all' means return all product types. product_types are slug names like
        'browse-medium'.

    loc_type is 'url' to return full URLs or 'path' to return paths available on
        the local disk. It can also be 'raw' to return a dictionary containing
        the URL, path, and checksum.
    """
    assert loc_type in ('path', 'url', 'raw'), loc_type
    if opus_id_list is None: # pragma: no cover
        return {}

    if not isinstance(product_types, (list, tuple)):
        product_types = product_types.lower().split(',')

    if not isinstance(opus_id_list, (list, tuple)):
        opus_id_list = [opus_id_list]

    if len(opus_id_list) == 0 or len(product_types) == 0: # pragma: no cover
        return {}

    results = OrderedDict() # Dict of opus_ids

    cursor = connection.cursor()
    q = connection.ops.quote_name

    values = []
    sql = 'SELECT '
    sql += q('obs_files')+'.'+q('opus_id')+', '
    sql += q('obs_files')+'.'+q('version_name')+', '
    sql += q('obs_files')+'.'+q('category')+', '
    sql += q('obs_files')+'.'+q('sort_order')+', '
    sql += q('obs_files')+'.'+q('short_name')+', '
    sql += q('obs_files')+'.'+q('full_name')+', '
    sql += q('obs_files')+'.'+q('size')+', '
    sql += q('obs_files')+'.'+q('default_checked')
    if loc_type == 'path' or loc_type == 'raw':
        sql += ', '+q('obs_files')+'.'+q('logical_path')
    if loc_type == 'url' or loc_type == 'raw':
        sql += ', '+q('obs_files')+'.'+q('url')
    if loc_type == 'raw':
        sql += ', '+q('obs_files')+'.'+q('checksum')

    sql += ' FROM '+q('obs_files')
    sql += ' WHERE '
    if product_types != ['all']:
        sql += '('
        # Because we didn't store @version in the database, when multiple versions (or
        # product types) are passed in, we need to query the database by both short name
        # and version name for each product type in the product_types list. The query
        # condition will be something like:
        # (obs_files.short_name='coiss_calib' AND obs_files.version_name='Current') OR
        # (obs_files.short_name='coiss_calib' AND obs_files.version_name='1') OR
        # (obs_files.short_name='coiss_raw' AND obs_files.version_name='Current') OR
        # ...
        for i, p in enumerate(product_types):
            # Check and see if the product type has a version specified (look for '@')
            if '@' in p:
                prod_type, _, version = p.partition('@')
                if version.lower() == 'current':
                    version = 'Current'
                sql += '('+q('obs_files')+'.'+q('short_name')+'=%s'
                values.append(prod_type)
                if version.lower() != 'all':
                    sql +=' AND '+q('obs_files')+'.'+q('version_name')+'=%s)'
                    values.append(version)
                else:
                    sql += ')'
            else:
                # When there is no modifier "@" in types, we will display "Current"
                # version of the files. This will match the behavior of api/download
                sql += '('+q('obs_files')+'.'+q('short_name')+'=%s AND '
                values.append(p)
                sql += q('obs_files')+'.'+q('version_name')+'="Current")'
            sql += ' OR ' if i != len(product_types)-1 else ') AND '
    sql += q('obs_files')+'.'+q('opus_id')+' IN %s'
    values.append(opus_id_list)
    sql += ' ORDER BY '
    sql += q('obs_files')+'.'+q('opus_id')+', '
    sql += q('obs_files')+'.'+q('version_number')+' DESC, '
    sql += q('obs_files')+'.'+q('sort_order')+', '
    sql += q('obs_files')+'.'+q('product_order')+', '
    sql += q('obs_files')+'.'+q('id') # Keep individual files in original order

    log.debug('get_pds_products SQL: %s %s', sql, values)
    cursor.execute(sql, values)

    # We do this here so if there aren't any products, there's still an empty
    # dictionary returned
    for opus_id in opus_id_list:
        results[opus_id] = OrderedDict() # Dict of versions

    for row in cursor:
        path = None
        url = None
        if loc_type == 'path':
            (opus_id, version_name, category, sort_order, short_name,
             full_name, size, default_checked, path) = row
        elif loc_type == 'url':
            (opus_id, version_name, category, sort_order, short_name,
             full_name, size, default_checked, url) = row
        else:
            (opus_id, version_name, category, sort_order, short_name,
             full_name, size, default_checked, path, url, checksum) = row

        # sort_order is the format CASISSxxx where xxx is the original numeric
        # sort order
        sort_order = int(sort_order[6:])
        if version_name not in results[opus_id]:
            results[opus_id][version_name] = OrderedDict()
        product_type = (category, sort_order, short_name, full_name)
        if product_type not in results[opus_id][version_name]:
            results[opus_id][version_name][product_type] = []

        if path:
            path = settings.PDS_DATA_DIR.rstrip('/') + '/' + path
        if url:
            url = settings.PRODUCT_HTTP_PATH.rstrip('/') + '/' + url

        if loc_type == 'path':
            res = path
        elif loc_type == 'url':
            res = url
        else:
            res = {'path': path,
                   'url': url,
                   'checksum': checksum,
                   'category': category,
                   'version_name': version_name,
                   'full_name': full_name,
                   'short_name': short_name,
                   'size': size}
        if res not in results[opus_id][version_name][product_type]:
            results[opus_id][version_name][product_type].append(res)

    return results


def get_pds_preview_images(opus_id_list, preview_jsons, sizes=None,
                           ignore_missing=False):
    """Given a list of opus_ids, return a list of image info for a size.

        opus_id_list can be a string or a list.

        preview_jsons can be None, a string, or a list. If a string or list,
        must correspond 1-to-1 with the entries in opus_list and give the
        obs_general.preview_images entry. If None, we will look them up for you.
    """
    if opus_id_list:
        if not isinstance(opus_id_list, (list, tuple)):
            opus_id_list = [opus_id_list]
    else:
        opus_id_list = []

    if sizes is None:
        sizes = settings.PREVIEW_SIZE_TO_PDS_TYPE.keys()
    elif not isinstance(sizes, (list, tuple)):
        sizes = [sizes]

    product_types = []
    for size in sizes:
        product_types += settings.PREVIEW_SIZE_TO_PDS_TYPE[size]

    image_list = []
    for idx in range(len(opus_id_list)):
        opus_id = opus_id_list[idx]
        preview_json = None
        if preview_jsons:
            preview_json = preview_jsons[idx]
        else:
            try:
                preview_json = ObsGeneral.objects.get(opus_id=opus_id).preview_images
            except ObjectDoesNotExist: # pragma: no cover
                log.error('get_pds_preview_images: Failed to find opus_id "%s" '
                          +'in obs_general', opus_id)
        viewset = None
        if preview_json: # pragma: no cover
            viewset = pdsviewable.PdsViewSet.from_dict(preview_json)
        data = OrderedDict({'opus_id':  opus_id})
        for size in sizes:
            viewable = None
            if viewset:
                if size == 'thumb':
                    viewable = viewset.thumbnail
                elif size == 'small':
                    viewable = viewset.small
                elif size == 'med':
                    viewable = viewset.medium
                elif size == 'full':
                    viewable = viewset.full_size
                else: # pragma: no cover
                    log.error('Unknown image size "%s"', size)
            if not preview_json or not viewset: # pragma: no cover
                # log.error('No preview image size "%s" found for '
                #           +'opus_id "%s"', size, opus_id)
                if ignore_missing: # pragma: no cover
                    continue
                url = settings.THUMBNAIL_NOT_FOUND
                alt_text = 'Not found'
                byte_size = 0
                width = 0
                height = 0
            else:
                url = settings.PRODUCT_HTTP_PATH.strip('/') + viewable.url
                alt_text = viewable.alt
                byte_size = viewable.bytes
                width = viewable.width
                height = viewable.height
            data[size+'_url'] = url
            data[size+'_alt_text'] = alt_text
            data[size+'_size_bytes'] = byte_size
            data[size+'_width'] = width
            data[size+'_height'] = height
        image_list.append(data)

    return image_list

def get_displayed_browse_products(opus_id, version_name='Current'):
    """Given an opus_id, return a list of browse product URLs to display in the
       detail tab. The function will return a list of tuples, and each tuple will
       be (medium browse url, full browse url).
    """
    browse_products = get_pds_products(opus_id,
                                       product_types=settings.DISPLAYED_BROWSE_PRODUCTS)

    selected_browse_products = browse_products[opus_id].get(version_name, [])
    # When there is no preview image, we return settings.THUMBNAIL_NOT_FOUND
    if len(selected_browse_products) == 0: # pragma: no cover
        return [(settings.THUMBNAIL_NOT_FOUND, settings.THUMBNAIL_NOT_FOUND)]
    res = []
    # One opus id could have multiple previews, for example:
    # co-rss-occ-2008-039-rev058c-x43-i
    # co-uvis-occ-2005-232-alpsco-i
    # Get paired medium and full browse urls in res (medium url, full url)
    disp_prod_dict = {}
    for p in selected_browse_products:
        for browse_url in selected_browse_products[p]:
            if '_med.' in browse_url:
                basename, _, _ = browse_url.partition('_med.')
                if basename in disp_prod_dict:
                    res.append((browse_url, disp_prod_dict[basename]))
                    continue
            else: # '_full.' in browse_url
                basename, _, _ = browse_url.partition('_full.')
                if basename in disp_prod_dict:
                    res.append((disp_prod_dict[basename], browse_url))
                    continue
            disp_prod_dict[basename] = browse_url

    return res
