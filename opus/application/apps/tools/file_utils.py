################################################################################
#
# tools/file_utils.py
#
################################################################################

from collections import OrderedDict
import json

from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse

from search.models import *
import tools.app_utils as app_utils

import settings

import pdsfile
import pdsviewable

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
    for pdsf in pdsfiles:
        if pdsf.abspath not in abspaths:
            abspaths.append(pdsf.abspath)
            ret.append(pdsf)
    return ret

def pds_products_sort_func(x):
    pref = None
    if x[0] == 'standard':
        pref = 1
    elif x[0] == 'metadata':
        pref = 2
    elif x[0] == 'browse':
        pref = 3
    elif x[0] == 'diagram':
        pref = 4
    if pref:
        return (str(pref), x[1])
    return x[0:2]

def get_pds_products_by_type(opus_id_list, product_types=['all']):
    """Return product types and their associated PdsFile objects for opus_ids.

        opus_id_list can be a string or a list.

        The returned dict is indexed by product_type and for each entry
        contains the combined information for all opus_ids. product_type
        is in the format (category, sort_order, slug, pretty_name) and is
        sorted in the order 'standard', 'metadata', 'browse', 'diagram', other.
    """
    if opus_id_list:
        if not isinstance(opus_id_list, (list, tuple)):
            opus_id_list = [opus_id_list]
    else:
        opus_id_list = []

    try:
        res = (ObsGeneral.objects.filter(opus_id__in=opus_id_list)
               .values('primary_file_spec'))
    except ObjectDoesNotExist:
        log.error('get_pds_products_by_type: Failed to find opus_ids "%s" '
                  +'in obs_general', str(opus_id_list))
        return None
    file_specs = [x['primary_file_spec'] for x in res]

    if len(opus_id_list) != len(file_specs):
        log.error('get_pds_products_by_type: Failed to find some opus_ids "%s" '
                  +'in obs_general', str(opus_id_list))
        return None

    products_by_type = {}

    for idx in range(len(opus_id_list)):
        opus_id = opus_id_list[idx]
        file_spec = file_specs[idx]
        try:
            pdsf = pdsfile.PdsFile.from_filespec(file_spec)
        except ValueError:
            log.error('get_pds_products_by_type: Failed to convert file_spec '
                      +'"%s"', file_spec)
            continue
        products = pdsf.opus_products()

        # Keep a running list of all products by type
        for (product_type, list_of_sublists) in products.items():
            if product_types == ['all'] or product_type in product_types:
                flat_list = _pdsfile_iter_flatten(list_of_sublists)
                products_by_type.setdefault(product_type, []).extend(flat_list)

    ret = OrderedDict()
    for product_type in sorted(products_by_type, key=pds_products_sort_func):
        ret[product_type] = products_by_type[product_type]

    return ret


def get_product_counts(products_by_type):
    size = 0
    count = 0
    num_products = OrderedDict()
    for product_type, products in products_by_type.items():
        num_products[product_type] = len(products)
        for pdsf in products:
            size += pdsf.size_bytes
            count += 1

    return size, count, num_products


def get_pds_products(opus_id_list=None, file_specs=None,
                     fmt='raw', loc_type='url',
                     product_types=['all']):
    """Return a list of all PDS products for a given opus_id(s).

    The returned dict is indexed by opus_id and can be in raw, html, or json.
    The latter are used by the "files" API. The dict is in the same order as
    the original opus_id_list.

    For each opus_id in the returned dict, there is a dict indexed by
    product_type in the format (category, sort_order, slug, pretty_name). The
    dict is sorted in the order 'standard', 'metadata', 'browse', 'diagram',
    other.

    opus_id_list can be a string or a list.

    file_specs can be None, a string, or a list. If a string or list,
        must correspond 1-to-1 with the entries in opus_list and give the
        primary_file_spec entry. If None, we will look them up for you.

    product_types can be a simple string, a comma-separated string, or a list.
        'all' means return all product types. product_types are slug names like
        'browse-medium'.

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

    if file_specs:
        if not isinstance(file_specs, (list, tuple)):
            file_specs = [file_specs]
    else:
        try:
            res = (ObsGeneral.objects.filter(opus_id__in=opus_id_list)
                   .values('primary_file_spec'))
        except ObjectDoesNotExist:
            log.error('get_pds_products: Failed to find opus_ids "%s" '
                      +'in obs_general', str(opus_id_list))
            return None
        file_specs = [x['primary_file_spec'] for x in res]

    # you can ask this function for url paths or disk paths
    if loc_type == 'url':
        path = settings.PRODUCT_HTTP_PATH
    elif loc_type == 'path':
        path = settings.PDS_DATA_DIR

    results = OrderedDict() # Dict of opus_ids

    for idx in range(len(opus_id_list)):
        opus_id = opus_id_list[idx]
        results[opus_id] = OrderedDict() # Dict of product types
        file_spec = file_specs[idx]
        try:
            pdsf = pdsfile.PdsFile.from_filespec(file_spec)
        except ValueError:
            log.error('get_pds_products: Failed to convert file_spec "%s"',
                      file_spec)
            continue
        products = pdsf.opus_products()
        # Keep a running list of all products by type
        for product_type in sorted(products, key=pds_products_sort_func):
            # product_type is in the format
            # (category, sort_order, slug, pretty_name)
            list_of_sublists = products[product_type]
            if (product_types != ['all'] and
                product_type[2] not in product_types):
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

    return app_utils.response_formats({'data': results}, fmt,
                                     template='results/list.html')
    # if fmt == 'json':
    #     return HttpResponse(json.dumps({'data': results}),
    #                                    content_type='application/json')
    #
    # if fmt == 'html':
    #     return render('list.html', results)


def get_pds_preview_images(opus_id_list, preview_jsons, sizes):
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

    if not isinstance(sizes, (list, tuple)):
        sizes = [sizes]

    if preview_jsons:
        if not isinstance(preview_jsons, (list, tuple)):
            preview_jsons = [preview_jsons]

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
                preview_json_str = (ObsGeneral.objects.get(opus_id=opus_id)
                                    .preview_images)
                preview_json = json.loads(preview_json_str)
            except ObjectDoesNotExist:
                log.error('get_pds_preview_images: Failed to find opus_ids "%s" '
                          +'in obs_general', opus_id)
        viewset = None
        if preview_json:
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
                else:
                    log.error('Unknown image size "%s"', size)
            if not preview_json or not viewset:
                log.error('No preview image size "%s" found for '
                          +'opus_id "%s"', size, opus_id)
                url = settings.THUMBNAIL_NOT_FOUND
                alt_text = 'Not found'
                byte_size = 0
                width = 0
                height = 0
            else:
                url = settings.PRODUCT_HTTP_PATH + viewable.url
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
