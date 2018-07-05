################################################################################
# file_utils.py
################################################################################

from collections import OrderedDict

from django.http import HttpResponse
import json

import pdsfile
import tools.app_utils as app_utils
import settings

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
        the local disk. It can also be 'raw' to return the actual PdsFile
        object.

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
        path = settings.PRODUCT_HTTP_PATH
    elif loc_type == 'path':
        path = settings.PDS_DATA_DIR

    results = OrderedDict() # Dict of opus_ids

    for opus_id in opus_ids:
        results[opus_id] = OrderedDict() # Dict of product types
        try:
            pdsf = pdsfile.PdsFile.from_opus_id(opus_id)
        except ValueError:
            log.error('Failed to convert opus_id "%s"', opus_id)
            continue
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
                    res_list.append(settings.PRODUCT_HTTP_PATH + file.url)
                elif loc_type == 'raw':
                    res_list.append(file)
                else:
                    log.error('get_pds_products: Unknown loc_type %s',
                              str(loc_type))
                    return None
            results[opus_id][opus_type] = res_list

    if fmt == 'raw':
        return results

    if fmt == 'json':
        return HttpResponse(json.dumps({'data': results}),
                                       content_type='application/json')

    if fmt == 'html':
        return render('list.html', results)

def get_obs_preview_images(opus_id_list, sizes):
    """Given a list of opus_ids, return a list of image info for a size."""

    if (not isinstance(opus_id_list, list) and
        not isinstance(opus_id_list, tuple)):
        opus_id_list = [opus_id_list]

    if (not isinstance(sizes, list) and
        not isinstance(sizes, tuple)):
        sizes = [sizes]

    opus_types = []
    for size in sizes:
        opus_types.append(settings.PREVIEW_SIZE_TO_PDS_TYPE[size])

    image_list = []
    for opus_id in opus_id_list:
        data = OrderedDict({'opus_id':  opus_id})
        products = get_pds_products(opus_id, 'raw', 'raw',
                                    product_types=opus_types)[opus_id]
        for size, opus_type in zip(sizes, opus_types):
            if (opus_type not in products or
                len(products[opus_type]) != 1):
                log.error('No preview image size "%s" found for opus_id "%s"',
                          size, opus_id)
                url = settings.THUMBNAIL_NOT_FOUND
                alt_text = 'Not found'
                byte_size = 0
                width = 0
                height = 0
            else:
                product = products[opus_type][0]
                url = settings.PRODUCT_HTTP_PATH + product.url
                alt_text = product.alt
                byte_size = product.size_bytes
                width = product.width
                height = product.height
            data[size+'_url'] = url
            data[size+'_alt_text'] = alt_text
            data[size+'_size_bytes'] = byte_size
            data[size+'_width'] = width
            data[size+'_height'] = height
        image_list.append(data)

    return image_list

    #
    #     pdsf = pdsfile.PdsFile.from_opus_id(opus_id)
    #     viewset = pdsf.viewset
    #     print viewset
    #     print viewset.viewables
    #     for viewable in viewset.viewables:
    #         print viewable.pdsf.opus_type, opus_type
    #         if viewable.pdsf.opus_type == opus_type:
    #             thumb['url'] = PRODUCT_HTTP_PATH + viewable.url
    #             thumb['alt_text'] = viewable.alt
    #             thumb_list.append(thumb)
    #             break
    #     else:
    #         log.error('No preview image size "%s" found for opus_id "%s"',
    #                   size, opus_id)

    return thumb_list
