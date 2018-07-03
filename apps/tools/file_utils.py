################################################################################
# file_utils.py
################################################################################

from collections import OrderedDict

from django.http import HttpResponse
import json

import pdsfile
import tools.app_utils as app_utils
from settings import PRODUCT_HTTP_PATH, PREVIEW_SIZE_TO_PDS_TYPE, PDS_DATA_DIR

import logging
log = logging.getLogger(__name__)

def get_base_path(opus_id):
    """Return the base path of the images for opus_id."""

def get__details(opus_id, size='thumb'):
    """Return the url, size of the requested image."""
    # size = 'small', 'med', 'full', 'thumb'
    #pdsf = pdsfile.PdsFile.from_opus_id(opus_id)
    return 'VGISS_6101/DATA/C32500XX/C3250013_thumb.jpg', 1300

def get_pds_products(opus_id=None, fmt='raw', loc_type='url',
                     product_types=['all']):
    """Return a list of all PDS products for a given opus_id(s).

    The returned list is sorted by opus_id and can be in raw, html, or json.
    The latter are used by the "files" API.

    opus_id can be a string or a list.

    product_types can be a simple string, a comma-separated string, or a list.
        'all' means return all product types.

    loc_type is 'url' to return full URLs or 'path' to return paths available on
        the local disk.

    """
    if (not isinstance(product_types, list) and
        not isinstance(product_types, tuple)):
        product_types = product_types.split(',')

    if opus_id:
        if (not isinstance(opus_id, list) and
            not isinstance(opus_id, tuple)):
            opus_ids = [opus_id]
        else:
            opus_ids = opus_id
    else:
        opus_ids = []

    # you can ask this function for url paths or disk paths
    if loc_type == 'url':
        path = PRODUCT_HTTP_PATH
    elif loc_type == 'path':
        path = PDS_DATA_DIR

    results = OrderedDict() # Dict of opus_ids

    for opus_id in opus_ids:
        results[opus_id] = OrderedDict() # Dict of product types
        pdsf = pdsfile.PdsFile.from_opus_id(opus_id)
        products = pdsf.opus_products()

        # Keep a running list of all products by type
        for opus_type in sorted(products.keys()):
            list_of_sublists = products[opus_type]
            if product_types != ['all'] and opus_type not in product_types:
                continue
            flat_list = app_utils.iter_flatten(list_of_sublists)
            res_list = []
            for file in flat_list:
                if loc_type == 'path':
                    res_list.append(file.abspath)
                elif loc_type == 'url':
                    res_list.append(PRODUCT_HTTP_PATH + file.url)
                else:
                    log.error('get_pds_products: Unknown loc_type %s', str(loc_type))
                    return None
            results[opus_id][opus_type] = res_list

    if fmt == 'raw':
        return results

    if fmt == 'json':
        return HttpResponse(json.dumps({'data': results}),
                                       content_type='application/json')

    if fmt == 'html':
        return render('list.html', results)

def get_obs_preview_images(opus_id_list, size):
    """Given a list of opus_ids, return a list of image info for thumbnails."""

    opus_type = PREVIEW_SIZE_TO_PDS_TYPE[size]

    if (not isinstance(opus_id_list, list) and
        not isinstance(opus_id_list, tuple)):
        opus_id_list = [opus_id_list]

    thumb_list = []
    for opus_id in opus_id_list:
        thumb = {'opus_id': opus_id,
                 'size': size}

        pdsf = pdsfile.PdsFile.from_opus_id(opus_id)
        viewset = pdsf.viewset
        for viewable in viewset.viewables:
            if viewable.pdsf.opus_type == opus_type:
                thumb['url'] = PRODUCT_HTTP_PATH + viewable.url
                thumb['alt_text'] = viewable.alt
                thumb_list.append(thumb)
                break
        else:
            log.error('No preview image size "%s" found for opus_id "%s"',
                      size, opus_id)

    return thumb_list
