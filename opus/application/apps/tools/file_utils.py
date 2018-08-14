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


def _iter_flatten(iterable):
  it = iter(iterable)
  for e in it:
    if isinstance(e, (list, tuple)):
      for f in _iter_flatten(e):
        yield f
    else:
      yield e

def _pdsfile_iter_flatten(iterable):
    "Flatten list and remove duplicate PdsFile objects"
    pdsfiles = _iter_flatten(iterable)
    abspaths = []
    ret = []
    for pdsfile in pdsfiles:
        if pdsfile.abspath not in abspaths:
            abspaths.append(pdsfile.abspath)
            ret.append(pdsfile)
    return ret

def get_pds_products_by_type(opus_id_list, product_types=['all']):
    """Return product types and their associated PdsFile objects for opus_ids.

        opus_id_list can be a string or a list.
    """
    if opus_id_list:
        if not isinstance(opus_id_list, (list, tuple)):
            opus_id_list = [opus_id_list]
    else:
        opus_id_list = []

    products_by_type = {}

    for opus_id in opus_id_list:
        try:
            pdsf = pdsfile.PdsFile.from_opus_id(opus_id)
        except ValueError:
            log.error('Failed to convert opus_id "%s"', opus_id)
            continue
        products = pdsf.opus_products()

        # Keep a running list of all products by type
        for (product_type, list_of_sublists) in products.items():
            if product_types == ['all'] or product_type in product_types:
                flat_list = _pdsfile_iter_flatten(list_of_sublists)
                products_by_type.setdefault(product_type, []).extend(flat_list)

    ret = OrderedDict()
    for product_type in sorted(products_by_type):
        ret[product_type] = products_by_type[product_type]

    return ret


def get_product_counts(products_by_type):
    size = 0
    count = 0
    num_products = OrderedDict()
    for product_type, products in products_by_type.iteritems():
        num_products[product_type] = len(products)
        for pdsf in products:
            size += pdsf.size_bytes
            count += 1

    return size, count, num_products


def get_pds_products(opus_id_list=None, fmt='raw', loc_type='url',
                     product_types=['all']):
    """Return a list of all PDS products for a given opus_id(s).

    The returned list is sorted by opus_id and can be in raw, html, or json.
    The latter are used by the "files" API.

    opus_id_list can be a string or a list.

    product_types can be a simple string, a comma-separated string, or a list.
        'all' means return all product types.

    loc_type is 'url' to return full URLs or 'path' to return paths available on
        the local disk. It can also be 'raw' to return the actual PdsFile
        object.

    """
    if not isinstance(product_types, (list, tuple)):
        product_types = product_types.split(',')

    if opus_id_list:
        if not isinstance(opus_id_list, (list, tuple)):
            opus_id_list = [opus_id_list]
    else:
        opus_id_list = []

    # you can ask this function for url paths or disk paths
    if loc_type == 'url':
        path = settings.PRODUCT_HTTP_PATH
    elif loc_type == 'path':
        path = settings.PDS_DATA_DIR

    results = OrderedDict() # Dict of opus_ids

    for opus_id in opus_id_list:
        results[opus_id] = OrderedDict() # Dict of product types
        try:
            pdsf = pdsfile.PdsFile.from_opus_id(opus_id)
        except ValueError:
            log.error('Failed to convert opus_id "%s"', opus_id)
            continue
        products = pdsf.opus_products()

        # Keep a running list of all products by type
        for product_type in sorted(products.keys()):
            list_of_sublists = products[product_type]
            if product_types != ['all'] and product_type not in product_types:
                continue
            flat_list = _pdsfile_iter_flatten(list_of_sublists)
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
            results[opus_id][product_type] = res_list

    if fmt == 'raw':
        return results

    return app_utils.responseFormats({'data': results}, fmt,
                                     template='results/list.html')
    # if fmt == 'json':
    #     return HttpResponse(json.dumps({'data': results}),
    #                                    content_type='application/json')
    #
    # if fmt == 'html':
    #     return render('list.html', results)


def get_pds_preview_images(opus_id_list, sizes):
    """Given a list of opus_ids, return a list of image info for a size.

        opus_id_list can be a string or a list.
    """
    if opus_id_list:
        if not isinstance(opus_id_list, (list, tuple)):
            opus_id_list = [opus_id_list]
    else:
        opus_id_list = []

    if not isinstance(sizes, (list, tuple)):
        sizes = [sizes]

    product_types = []
    for size in sizes:
        product_types.append(settings.PREVIEW_SIZE_TO_PDS_TYPE[size])

    image_list = []
    for opus_id in opus_id_list:
        data = OrderedDict({'opus_id':  opus_id})
        products = get_pds_products(opus_id, 'raw', 'raw',
                                    product_types=product_types)[opus_id]
        for size, product_type in zip(sizes, product_types):
            if (product_type not in products or
                len(products[product_type]) != 1):
                log.error('No preview image size "%s" found for opus_id "%s"',
                          size, opus_id)
                url = settings.THUMBNAIL_NOT_FOUND
                alt_text = 'Not found'
                byte_size = 0
                width = 0
                height = 0
            else:
                product = products[product_type][0]
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
