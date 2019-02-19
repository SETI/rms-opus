################################################################################
#
# results/views.py
#
# The API interface for retrieving results (actual data, actual metadata, or
# lists of images or files):
#
#    Format: __api/dataimages.json
#    Format: [__]api/data.(json|zip|html|csv)
#    Format: [__]api/data/(?P<opus_id>[-\w]+).csv
#    Format: [__]api/metadata/(?P<opus_id>[-\w]+).(?P<fmt>json|html)
#    Format: [__]api/metadata_v2/(?P<opus_id>[-\w]+).(?P<fmt>json|html)
#    Format: [__]api/images/(?P<size>thumb|small|med|full).
#                           (?P<fmt>json|zip|html|csv)
#    Format: [__]api/images.(json|zip|html|csv)
#    Format: [__]api/image/(?P<size>thumb|small|med|full)/(?P<opus_id>[-\w]+)
#                          .(?P<fmt>json|zip|html|csv)
#    Format: [__]api/files/(?P<opus_id>[-\w]+).(?P<fmt>json|zip|html|csv)
#        or: api/files.(?P<fmt>json|zip|html|csv)
#    Format: [__]api/categories/(?P<opus_id>[-\w]+).json
#    Format: [__]api/categories.json
#
################################################################################

from collections import OrderedDict
import json
import logging
import os

import settings

from django.apps import apps
from django.core.cache import cache
from django.core.exceptions import FieldError
from django.db import connection, DatabaseError
from django.http import Http404
from django.shortcuts import render
from django.views.decorators.cache import never_cache

from paraminfo.models import *
from search.models import *
from search.views import (get_param_info_by_slug,
                          get_user_query_table,
                          url_to_search_params,
                          create_order_by_sql,
                          parse_order_slug)
from user_collections.models import Collections
from tools.app_utils import *
from tools.db_utils import *
from tools.file_utils import *

log = logging.getLogger(__name__)


################################################################################
#
# API INTERFACES
#
################################################################################

def api_get_data_and_images(request):
    """Return a page of data and images for a given search.

    This is a PRIVATE API.

    Get data and images for observations based on search criteria, columns,
    and sort order. Data is returned in chunks given a starting observation
    and a limit of how many to return. We also support "pages" for specifying
    the starting observation for backwards compatibility. A "page" is 100
    observations long.

    Format: __api/dataimages.json
    Arguments: limit=<N>
               page=<N>  OR  startobs=<N> (1-based)
               order=<column>[,<column>...]
               Normal search and selected-column arguments

    Returns JSON.

    Returned JSON:

        {'page': [
            {'opus_id': OPUS_ID,
             'metadata': ['<col1>', '<col2>', '<col3>'],
             'images': {
                'full':
                'med':
             },
             'in_collection': True/False
            },
            ...
         ],
         'page_no':         page_no,   OR   'start_obs': start_obs,
         'limit':           limit,
         'order':           comma-separate list of slugs,
         'order_list':      [entry, entry...]
                            entry is {'slug': slug_name,
                                      'label': pretty_name,
                                      'descending': True/False,
                                      'removeable': True/False},
         'count':           len(page),
         'columns':         columns (corresponds to <col1> etc. in 'metadata')
        }
    """
    api_code = enter_api_call('api_get_data_and_images', request)

    if not request or request.GET is None:
        ret = Http404(settings.HTTP404_NO_REQUEST)
        exit_api_call(api_code, ret)
        raise ret

    session_id = get_session_id(request)

    cols = request.GET.get('cols', settings.DEFAULT_COLUMNS)

    labels = labels_for_slugs(cols_to_slug_list(cols))
    if labels is None:
        ret = Http404(settings.HTTP404_UNKNOWN_SLUG)
        exit_api_call(api_code, ret)
        raise ret

    (page_no, start_obs, limit, page, order, aux) = get_search_results_chunk(
                                       request,
                                       prepend_cols='opusid',
                                       append_cols='**previewimages',
                                       return_opusids=True,
                                       return_collection_status=True,
                                       api_code=api_code)
    if page is None:
        ret = HttpResponseServerError(settings.HTTP500_SEARCH_FAILED)
        exit_api_call(api_code, ret)
        return ret

    preview_jsons = [json.loads(x[-1]) for x in page]
    opus_ids = aux['opus_ids']
    image_list = get_pds_preview_images(opus_ids, preview_jsons,
                                        ['thumb', 'small', 'med', 'full'])

    if not image_list:
        log.error('api_get_data_and_images: No image found for: %s',
                  str(opus_ids[:50]))

    new_image_list = []
    for image in image_list:
        new_image = {}
        for key, val in image.items():
            for size in ['thumb', 'small', 'med', 'full']:
                new_image[size] = {}
                for sfx in ['url', 'alt_text', 'size_bytes', 'width', 'height']:
                    new_image[size][sfx] = image.get(size+'_'+sfx, None)
        new_image_list.append(new_image)

    collection_status = aux['collection_status']
    new_page = []
    for i in range(len(opus_ids)):
        new_entry = {
            'opusid': opus_ids[i],
            'metadata': page[i][1:-1],
            'images': new_image_list[i],
            'in_collection': collection_status[i] is not None
        }
        new_page.append(new_entry)

    cols = request.GET.get('cols', settings.DEFAULT_COLUMNS)

    labels = labels_for_slugs(cols_to_slug_list(cols))
    order_slugs = cols_to_slug_list(order)
    order_slugs_pure = [x[1:] if x[0] == '-' else x for x in order_slugs]
    order_labels = labels_for_slugs(order_slugs_pure, units=False)

    order_list = []
    for idx, (slug, label) in enumerate(zip(order_slugs, order_labels)):
        removeable = idx != len(order_slugs)-1;
        desc = False
        if slug[0] == '-':
            slug = slug[1:]
            desc = True
        order_entry = {'slug': slug,
                       'label': label,
                       'descending': desc,
                       'removeable': removeable}
        order_list.append(order_entry)

    reqno = request.GET.get('reqno', None)
    try:
        reqno = int(reqno)
    except:
        reqno = None

    data = {'page':         new_page,
            'limit':        limit,
            'count':        len(image_list),
            'order':        order,
            'order_list':   order_list,
            'columns':      labels,
            'reqno':        reqno
           }

    if page_no is not None:
        data['page_no'] = page_no
    if start_obs is not None:
        data['start_obs'] = start_obs

    ret = json_response(data)
    exit_api_call(api_code, ret)
    return ret


def api_get_data(request, fmt):
    """Return a page of data for a given search.

    This is a PUBLIC API.

    Get data for observations based on search criteria, columns, and sort order.
    Data is returned in chunks given a starting observation and a limit of how
    many to return. We also support "pages" for specifying the starting
    observation for backwards compatibility. A "page" is 100 observations long.

    Format: [__]api/data.(json|html|csv)
    Arguments: limit=<N>
               page=<N>  OR  startobs=<N> (1-based)
               order=<column>[,<column>...]
               Normal search and selected-column arguments

    Can return JSON, HTML, or CSV.

    Returned JSON:
        {
            'page_no': page_no,   OR   'startobs': start_obs,
            'limit':   limit,
            'order':   order,
            'count':   len(page),
            'labels':  labels,
            'page':    page         # tabular page data
        }

    Returned HTML:
        <table>
            <tr>
                <th>OPUS ID</th>
                <th>Instrument Name</th>
                <th>Planet</th>
                <th>Intended Target Name</th>
                <th>Observation Start Time</th>
                <th>Observation Duration (secs)</th>
            </tr>
            <tr>
                <td>vg-iss-2-s-c4360001</td>
                <td>Voyager ISS</td>
                <td>Saturn</td>
                <td>Titan</td>
                <td>1981-08-12T14:55:10.080</td>
                <td>1.9200</td>
            </tr>
        </table>

    Returned CSV:
        OPUS ID,Instrument Name,Planet,Intended Target Name,Observation Start Time,Observation Duration (secs)
        vg-iss-2-s-c4360001,Voyager ISS,Saturn,Titan,1981-08-12T14:55:10.080,1.9200
    """
    api_code = enter_api_call('api_get_data', request)

    if not request or request.GET is None:
        ret = Http404(settings.HTTP404_NO_REQUEST)
        exit_api_call(api_code, ret)
        raise ret

    session_id = get_session_id(request)

    cols = request.GET.get('cols', settings.DEFAULT_COLUMNS)

    labels = labels_for_slugs(cols_to_slug_list(cols))
    if labels is None:
        ret = Http404(settings.HTTP404_UNKNOWN_SLUG)
        exit_api_call(api_code, ret)
        raise ret

    (page_no, start_obs, limit, page, order, aux) = get_search_results_chunk(
                                                     request,
                                                     cols=cols,
                                                     return_opusids=True,
                                                     api_code=api_code)

    if page is None:
        ret = HttpResponseServerError(settings.HTTP500_SEARCH_FAILED)
        exit_api_call(api_code, ret)
        return ret

    data = {'limit':    limit,
            'page':     page,
            'order':    order,
            'count':    len(page),
            'labels':   labels,
            'columns':  labels # Backwards compatibility with external apps
           }

    if page_no is not None:
        data['page_no'] = page_no
    if start_obs is not None:
        data['start_obs'] = start_obs

    if fmt == 'csv':
        csv_data = []
        csv_data.append(labels)
        csv_data.extend(page)
        ret = csv_response('data', csv_data)
    elif fmt == 'html':
        context = {'data': data}
        ret = render(request, 'results/data.html', context)
    elif fmt == 'json':
        ret = HttpResponse(json.dumps(data), content_type='application/json')
    else:
        log.error('api_get_data: Unknown format "%s"', fmt)
        ret = Http404(settings.HTTP404_UNKNOWN_FORMAT)
        exit_api_call(api_code, ret)
        raise ret

    exit_api_call(api_code, ret)
    return ret


def api_get_metadata(request, opus_id, fmt):
    """Return all metadata, sorted by category, for this opus_id.

    This is a PUBLIC API.

    Format: api/metadata/(?P<opus_id>[-\w]+).(?P<fmt>[json|html|csv]+

    Arguments: cols=<columns>
                    Limit results to particular columns.
                    This is a list of slugs separated by commas. Note that the
                    return will be indexed by field name, but by slug name.
                    If cols is supplied, cats is ignored.
               cats=<cats>
                    Limit results to particular categories. Categories can be
                    given as "pretty names" as displayed on the Details page,
                    or can be given as table names.

    Can return JSON, HTML, or CSV.

    JSON is indexed by pretty category name, then by field database name (EEK).

    HTML and CSV return fully qualified labels.
    """
    return get_metadata(request, opus_id, fmt,
                        'api_get_metadata', True, False)

def api_get_metadata_v2(request, opus_id, fmt):
    """Return all metadata, sorted by category, for this opus_id.

    This is a PUBLIC API.

    Format: api/metadata_v2/(?P<opus_id>[-\w]+).(?P<fmt>[json|html|csv]+

    Arguments: cols=<columns>
                    Limit results to particular columns.
                    This is a list of slugs separated by commas. Note that the
                    return will be indexed by field name, but by slug name.
                    If cols is supplied, cats is ignored.
               cats=<cats>
                    Limit results to particular categories. Categories can be
                    given as "pretty names" as displayed on the Details page,
                    or can be given as table names.

    Can return JSON, HTML, or CSV.

    JSON is indexed by pretty category name, then by field pretty name.

    HTML and CSV return fully qualified labels.
    """
    return get_metadata(request, opus_id, fmt,
                        'api_get_metadata_v2', False, False)

def api_get_metadata_v2_internal(request, opus_id, fmt):
    """Return all metadata, sorted by category, for this opus_id.

    This is a PRIVATE API.

    Format: __api/metadata_v2/(?P<opus_id>[-\w]+).(?P<fmt>[json|html|csv]+

    Arguments: cols=<columns>
                    Limit results to particular columns.
                    This is a list of slugs separated by commas. Note that the
                    return will be indexed by field name, but by slug name.
                    If cols is supplied, cats is ignored.
               cats=<cats>
                    Limit results to particular categories. Categories can be
                    given as "pretty names" as displayed on the Details page,
                    or can be given as table names.

    Can return JSON, HTML, or CSV.

    JSON is indexed by pretty category name, then by field pretty name.

    HTML and CSV return fully qualified labels.

    The only difference between __api/metadata_v2 and api_metadata_v2 is in the
    returned HTML. The __api version returns an internally-formatted HTML needed
    by the Details tab including things like tooltips. The api version returns
    an external-formatted HTML that is acceptable to outside users without
    exposing internal details.
    """
    return get_metadata(request, opus_id, fmt,
                        'api_get_metadata_v2_internal', False, True)

def get_metadata(request, opus_id, fmt, api_name, return_db_names, internal):
    api_code = enter_api_call(api_name, request)

    if not request or request.GET is None:
        ret = Http404(settings.HTTP404_NO_REQUEST)
        exit_api_call(api_code, ret)
        raise ret

    if not opus_id:
        ret = Http404('No OPUS ID')
        exit_api_call(api_code, ret)
        raise ret

    # Backwards compatibility
    opus_id = convert_ring_obs_id_to_opus_id(opus_id)

    cols = request.GET.get('cols', False)
    if cols or cols == '':
        ret = _get_metadata_by_slugs(request, opus_id, cols,
                                     fmt,
                                     return_db_names,
                                     internal,
                                     api_code)
        if ret is None:
            ret = Http404(settings.HTTP404_UNKNOWN_SLUG)
            exit_api_call(api_code, ret)
            raise ret
        exit_api_call(api_code, ret)
        return ret

    # Make sure it's a valid OPUS ID
    try:
        results = query_table_for_opus_id('obs_general', opus_id)
    except LookupError:
        log.error('api_get_metadata: Could not find data model for obs_general')
        ret = HttpResponseServerError(settings.HTTP500_INTERNAL_ERROR)
        exit_api_call(api_code, ret)
        return ret
    if len(results) == 0:
        log.error('get_metadata: Error searching for opus_id "%s"',
                  opus_id)
        ret = Http404(settings.HTTP404_UNKNOWN_OPUS_ID)
        exit_api_call(api_code, ret)
        raise ret

    cats = request.GET.get('cats', False)

    data = OrderedDict()     # Holds data struct to be returned
    all_info = OrderedDict() # Holds all the param info objects

    if cats == '':
        all_tables = []
    elif not cats:
        # Find all the tables (categories) this observation belongs to
        all_tables = (TableNames.objects.filter(display='Y')
                      .order_by('disp_order'))
    else:
        # Uniquify
        cat_list = list(set(cats.split(',')))
        # Restrict tables to those found in cats
        all_tables = ((TableNames.objects.filter(label__in=cat_list,
                                                 display='Y') |
                       TableNames.objects.filter(table_name__in=cat_list,
                                                 display='Y'))
                                         .order_by('disp_order'))
        if len(all_tables) != len(cat_list):
            log.error('get_metadata: Unknown category name in "%s"',
                      cats)
            ret = Http404(settings.HTTP404_UNKNOWN_CATEGORY)
            exit_api_call(api_code, ret)
            raise ret

    # Now find all params and their values in each of these tables
    for table in all_tables:
        table_label = table.label
        table_name = table.table_name
        model_name = ''.join(table_name.title().split('_'))

        # Make a list of all slugs and another of all param_names in this table
        param_info_list = list(ParamInfo.objects
                               .filter(category_name=table_name,
                                       display_results=1)
                               .order_by('disp_order'))
        if param_info_list:
            for param_info in param_info_list:
                if return_db_names:
                    all_info[param_info.name] = param_info
                else:
                    all_info[param_info.slug] = param_info

            try:
                results = query_table_for_opus_id(table_name, opus_id)
            except LookupError:
                log.error('api_get_metadata: Could not find data model for '
                          +'category %s', model_name)
                ret = HttpResponseServerError(settings.HTTP500_INTERNAL_ERROR)
                exit_api_call(api_code, ret)
                return ret

            all_param_names = [p.name for p in param_info_list]
            result_vals = results.values(*all_param_names)
            if not result_vals:
                # This is normal - we're looking at ALL tables so many won't
                # have this OPUS_ID in them.
                continue
            result_vals = result_vals[0]
            ordered_results = OrderedDict()
            for param_info in param_info_list:
                (form_type, form_type_func,
                 form_type_format) = parse_form_type(param_info.form_type)

                if (form_type in settings.MULT_FORM_TYPES and
                    not return_db_names):
                    mult_name = get_mult_name(param_info.param_qualified_name())
                    mult_val = results.values(mult_name)[0][mult_name]
                    result = lookup_pretty_value_for_mult(param_info, mult_val)
                else:
                    result = result_vals[param_info.name]
                    # Format result depending on its form_type_format
                    result = format_metadata_number_or_func(result,
                                                            form_type_func,
                                                            form_type_format)

                if fmt == 'csv':
                    index = param_info.fully_qualified_label_results()
                elif return_db_names:
                    index = param_info.name
                else:
                    index = param_info.slug
                if index:
                    ordered_results[index] = result

            data[table_label] = ordered_results

    if fmt == 'csv':
        csv_data = []
        for table_label in data:
            csv_data.append([table_label])
            row_title = []
            row_data = []
            for k,v in data[table_label].items():
                row_title.append(k)
                row_data.append(v)
            csv_data.append(row_title)
            csv_data.append(row_data)
        ret = csv_response(opus_id, csv_data)
    elif fmt == 'html':
        context = {'data': data,
                   'all_info': all_info}
        if internal:
            ret = render(request, 'results/detail_metadata_internal.html', context)
        else:
            ret = render(request, 'results/detail_metadata.html', context)
    elif fmt == 'json':
        ret = HttpResponse(json.dumps(data), content_type='application/json')
    else:
        log.error('get_metadata: Unknown format "%s"', fmt)
        ret = Http404(settings.HTTP404_UNKNOWN_FORMAT)
        exit_api_call(api_code, ret)
        raise ret

    exit_api_call(api_code, ret)
    return ret


@never_cache
def api_get_images_by_size(request, size, fmt):
    """Return all images of a particular size for a given search.

    This is a PUBLIC API.

    Format: [__]api/images/(?P<size>[thumb|small|med|full]+).
            (?P<fmt>[json|zip|html|csv]+)
    Arguments: limit=<N>
               page=<N>  OR  startobs=<N> (1-based)
               order=<column>[,<column>...]
               Normal search arguments

    Can return JSON, ZIP, HTML, or CSV.
    """
    api_code = enter_api_call('api_get_images_by_size', request)

    if not request or request.GET is None:
        ret = Http404(settings.HTTP404_NO_REQUEST)
        exit_api_call(api_code, ret)
        raise ret

    session_id = get_session_id(request)

    (page_no, start_obs, limit, page, order, aux) = get_search_results_chunk(
                                       request,
                                       cols='opusid,**previewimages',
                                       return_opusids=True,
                                       return_ringobsids=True,
                                       api_code=api_code)
    if page is None:
        ret = Http404('Could not find page')
        exit_api_call(api_code, ret)
        raise ret

    preview_jsons = [json.loads(x[1]) for x in page]
    opus_ids = aux['opus_ids']
    image_list = get_pds_preview_images(opus_ids, preview_jsons, [size])

    if not image_list:
        log.error('api_get_images_by_size: No image found for: %s',
                  str(opus_ids[:50]))

    # Backwards compatibility
    ring_obs_ids = aux['ring_obs_ids']
    ring_obs_id_dict = {}
    for i in range(len(opus_ids)):
        ring_obs_id_dict[opus_ids[i]] = ring_obs_ids[i]

    for image in image_list:
        image['ring_obs_id'] = ring_obs_id_dict[image['opus_id']]
        if size+'_alt_text' in image:
            del image[size+'_alt_text']
        if size+'_size_bytes' in image:
            del image[size+'_size_bytes']
        if size+'_width' in image:
            del image[size+'_width']
        if size+'_height' in image:
            del image[size+'_height']
        if size+'_url' in image:
            root_idx = image[size+'_url'].find('previews/')+9
            path = image[size+'_url'][:root_idx]
            url = image[size+'_url'][root_idx:]
            image['img'] = url
            image['path'] = path
            image[size] = url
            del image[size+'_url']

    data = {'data':  image_list,
            'limit': limit,
            'count': len(image_list)
           }
    if page_no is not None:
        data['page_no'] = page_no
    if start_obs is not None:
        data['start_obs'] = start_obs

    ret = response_formats(data, fmt,
                          template='results/gallery.html', order=order)
    exit_api_call(api_code, ret)
    return ret


@never_cache
def api_get_images(request, fmt):
    """Return all images of all sizes for a given search.

    This is a PUBLIC API.

    Format: [__]api/images.(json|zip|html|csv)
    Arguments: limit=<N>
               page=<N>  OR  startobs=<N> (1-based)
               order=<column>[,<column>...]
               Normal search arguments

    Can return JSON, ZIP, HTML, or CSV.
    """
    api_code = enter_api_call('api_get_images', request)

    if not request or request.GET is None:
        ret = Http404(settings.HTTP404_NO_REQUEST)
        exit_api_call(api_code, ret)
        raise ret

    session_id = get_session_id(request)

    (page_no, start_obs, limit, page, order, aux) = get_search_results_chunk(
                                       request,
                                       cols='opusid,**previewimages',
                                       return_opusids=True,
                                       return_ringobsids=True,
                                       return_collection_status=True,
                                       api_code=api_code)
    if page is None:
        ret = Http404('Could not find page')
        exit_api_call(api_code, ret)
        raise ret

    preview_jsons = [json.loads(x[1]) for x in page]
    opus_ids = aux['opus_ids']
    image_list = get_pds_preview_images(opus_ids, preview_jsons,
                                        ['thumb', 'small', 'med', 'full'])

    if not image_list:
        log.error('api_get_images: No image found for: %s',
                  str(opus_ids[:50]))

    # Backwards compatibility
    ring_obs_ids = aux['ring_obs_ids']
    ring_obs_id_dict = {}
    for i in range(len(opus_ids)):
        ring_obs_id_dict[opus_ids[i]] = ring_obs_ids[i]

    collection_status = aux['collection_status']
    for image, in_collection in zip(image_list, collection_status):
        image['in_collection'] = in_collection is not None
        image['ring_obs_id'] = ring_obs_id_dict[image['opus_id']]

    data = {'data':  image_list,
            'limit': limit,
            'count': len(image_list)
           }
    if page_no is not None:
        data['page_no'] = page_no
    if start_obs is not None:
        data['start_obs'] = start_obs
    ret = response_formats(data, fmt,
                          template='results/gallery.html', order=order)
    exit_api_call(api_code, ret)
    return ret


def api_get_image(request, opus_id, size='med', fmt='raw'):
    """Return info about a preview image for the given opus_id and size.

    This is a PUBLIC API.

    Format: [__]api/image/(?P<size>[thumb|small|med|full]+)/(?P<opus_id>[-\w]+)
            .(?P<fmt>[json|zip|html|csv]+)

    Can return JSON, ZIP, HTML, or CSV.

    The fields 'path' and 'img' are provided for backwards compatibility only.
    """
    api_code = enter_api_call('api_get_image', request)
    if not request or request.GET is None:
        ret = Http404(settings.HTTP404_NO_REQUEST)
        exit_api_call(api_code, ret)
        raise ret

    # Backwards compatibility
    opus_id = convert_ring_obs_id_to_opus_id(opus_id)

    image_list = get_pds_preview_images(opus_id, None, size)
    if len(image_list) != 1:
        log.error('api_get_image: Could not find preview for opus_id "%s" '
                  +'size "%s"', str(opus_id), str(size))
        ret = Http404('No preview image')
        exit_api_call(api_code, ret)
        raise ret

    image = image_list[0]
    path = None
    if size+'_url' in image:
        root_idx = image[size+'_url'].find('previews/')+9
        path = image[size+'_url'][:root_idx]
        url = image[size+'_url'][root_idx:]
        image['img'] = url
        image['path'] = path
        image['img'] = url
        image['url'] = image[size+'_url']
    data = {'path': path, 'data': image_list}
    ret = response_formats(data, fmt, size=size,
                          template='results/image_list.html')
    exit_api_call(api_code, ret)
    return ret


def api_get_files(request, opus_id=None):
    """Return all files for a given opus_id or search results.

    This is a PUBLIC API.

    Format: [__]api/files/(?P<opus_id>[-\w]+).json
        or: [__]api/files.json
    Arguments: types=<types>
                    Product types
               loc_type=['url', 'path']

    Only returns JSON.
    """
    api_code = enter_api_call('api_get_files', request)

    if not request or request.GET is None:
        ret = Http404(settings.HTTP404_NO_REQUEST)
        exit_api_call(api_code, ret)
        raise ret

    product_types = request.GET.get('types', 'all')
    loc_type = request.GET.get('loc_type', 'url')

    opus_ids = []
    data = {}
    if opus_id:
        # Backwards compatibility
        opus_id = convert_ring_obs_id_to_opus_id(opus_id)
        opus_ids = [opus_id]
    else:
        # No opus_id passed, get files from search results
        # Override cols because we don't care about anything except
        # opusid
        (page_no, start_obs, limit, page,
         order, aux) = get_search_results_chunk(request,
                                                cols='',
                                                return_opusids=True,
                                                api_code=api_code)
        opus_ids = aux['opus_ids']

    ret = get_pds_products(opus_ids,
                           loc_type=loc_type,
                           product_types=product_types)

    versioned_ret = OrderedDict()
    current_ret = OrderedDict()
    for opus_id in ret:
        versioned_ret[opus_id] = OrderedDict() # Versions
        current_ret[opus_id] = OrderedDict()
        for version in ret[opus_id]:
            versioned_ret[opus_id][version] = OrderedDict()
            for product_type in ret[opus_id][version]:
                versioned_ret[opus_id][version][product_type[2]] = \
                    ret[opus_id][version][product_type]
                if version == 'Current':
                    current_ret[opus_id][product_type[2]] = \
                        ret[opus_id][version][product_type]

    data['data'] = current_ret
    data['versions'] = versioned_ret

    ret = HttpResponse(json.dumps(data), content_type='application/json')
    exit_api_call(api_code, ret)
    return ret


def api_get_categories_for_opus_id(request, opus_id):
    """Return a JSON list of all cateories (tables) this opus_id appears in.

    This is a PUBLIC API.

    Format: [__]api/categories/(?P<opus_id>[-\w]+).json
    """
    api_code = enter_api_call('api_get_categories_for_opus_id', request)

    if not request or request.GET is None:
        ret = Http404(settings.HTTP404_NO_REQUEST)
        exit_api_call(api_code, ret)
        raise ret

    # Backwards compatibility
    opus_id = convert_ring_obs_id_to_opus_id(opus_id)

    all_categories = []
    table_info = (TableNames.objects.all().values('table_name', 'label')
                  .order_by('disp_order'))

    for tbl in table_info:
        table_name = tbl['table_name']
        if table_name == 'obs_surface_geometry':
            # obs_surface_geometry is not a data table
            # It's only used to select targets, not to hold data, so remove it
            continue

        try:
            results = query_table_for_opus_id(table_name, opus_id)
        except LookupError:
            log.error('api_get_categories_for_opus_id: Unable to find table '
                      +'%s', table_name)
            continue
        results = results.values('opus_id')
        if results:
            cat = {'table_name': table_name, 'label': tbl['label']}
            all_categories.append(cat)

    ret = HttpResponse(json.dumps(all_categories),
                       content_type="application/json")
    exit_api_call(api_code, ret)
    return ret


def api_get_categories_for_search(request):
    """Return a JSON list of all cateories (tables) triggered by this search.

    This is a PUBLIC API.

    Format: [__]api/categories.json

    Arguments: Normal search arguments
    """
    api_code = enter_api_call('api_get_categories_for_search', request)

    if not request or request.GET is None:
        ret = Http404(settings.HTTP404_NO_REQUEST)
        exit_api_call(api_code, ret)
        raise ret

    (selections, extras) = url_to_search_params(request.GET)
    if selections is None:
        log.error('api_get_categories_for_search: Could not find selections for'
                  +' request %s', str(request.GET))
        ret = Http404('Parsing of selections failed')
        exit_api_call(api_code, ret)
        raise ret

    if not selections:
        triggered_tables = settings.BASE_TABLES[:]  # Copy
    else:
        triggered_tables = get_triggered_tables(selections, extras,
                                                api_code=api_code)

    # The main geometry table, obs_surface_geometry, is not a table that holds
    # results data. It is only there for selecting targets, which then trigger
    # the other geometry tables. So in the context of returning list of
    # categories it gets removed.
    if 'obs_surface_geometry' in triggered_tables:
        triggered_tables.remove('obs_surface_geometry')

    labels = (TableNames.objects.filter(table_name__in=triggered_tables)
              .values('table_name','label').order_by('disp_order'))

    ret = HttpResponse(json.dumps([ob for ob in labels]),
                       content_type="application/json")
    exit_api_call(api_code, ret)
    return ret


################################################################################
#
# SUPPORT ROUTINES
#
################################################################################

def get_search_results_chunk(request, use_collections=None,
                             cols=None, prepend_cols=None, append_cols=None,
                             limit=None, opus_id=None,
                             return_opusids=False,
                             return_ringobsids=False,
                             return_filespecs=False,
                             return_collection_status=False,
                             api_code=None):
    """Return a page of results.

        request             Used to find the search and order parameters and
                            columns if not overridden.
        use_collections     Ignore the search parameters and instead use the
                            observations stored in the collections table for
                            this session.
        cols                If specified, overrides the columns in request.
        prepend_cols        A string to prepend to the column list.
        append_cols         A string to append to the column list.
        limit               The maximum number of results to return. If not
                            specified, use the limit provided in the request,
                            or the default if none given.
        opus_id             Ignore the search parameters and instead return
                            the result for a single opusid.
        return_opusids      Include 'opus_ids' in the returned aux dict.
                            This is a list of opus_ids 1:1 with the returned
                            data.
        return_ringobsids   Include 'ring_obs_ids' in the returned aux dict.
        return_filespecs    Include 'file_specs' in the returned aux dict.
                            This is a list of primary_file_specs 1:1 with the
                            returned data.
        return_collection_status
                            Include 'collection_status' in the returned aux
                            dict. This is a list of True/False values 1:1
                            with the returned data indicating if the given
                            observation is in the current collections table for
                            this session.

        Returns:

        (page_no, start_obs, limit, results, all_order, aux_dict)

        page_no             The starting page number, if page= was provided.
        start_obs           The starting observation number, if startobs=
                            was provided.
        limit               The maximum number of results that could be
                            returned.
        results             A list containing the columns for all returned
                            observations.
        all_order           The sort order that was used, including a trailing
                            opus_id if necessary.
        aux_dict            A dictionary that may contain keys as specified
                            above.
    """
    none_return = (None, None, None, None, None, {})

    session_id = get_session_id(request)

    if use_collections is None:
        if request.GET.get('view', 'browse') == 'collection':
            use_collections = True
        else:
            use_collections = False

    if limit is None:
        limit = request.GET.get('limit', settings.DEFAULT_PAGE_LIMIT)
        try:
            limit = int(limit)
        except ValueError:
            log.error('get_search_results_chunk: Unable to parse limit %s',
                      limit)
            return none_return

    if limit != 'all':
        if limit < 0 or limit > settings.SQL_MAX_LIMIT:
            log.error('get_search_results_chunk: Bad limit %s', str(limit))
            return none_return

    if cols is None:
        cols = request.GET.get('cols', settings.DEFAULT_COLUMNS)

    if prepend_cols:
        cols = prepend_cols + ',' + cols
    if append_cols:
        cols = cols + ',' + append_cols

    form_type_formats = []
    column_names = []
    tables = set()
    mult_tables = set()
    for slug in cols_to_slug_list(cols):
        # First try the full name, which might include a trailing 1 or 2
        pi = get_param_info_by_slug(slug, from_ui=True)
        if not pi:
            log.error('get_search_results_chunk: Slug "%s" not found', slug)
            return none_return
        column = pi.param_qualified_name()
        table = pi.category_name
        if column.endswith('.opus_id'):
            # opus_id can be displayed from anywhere, but for consistency force
            # it to come from obs_general, since that's the master list.
            # This isn't needed for correctness, just cleanliness.
            table = 'obs_general'
            column = 'obs_general.opus_id'
        tables.add(table)
        (form_type, form_type_func,
         form_type_format) = parse_form_type(pi.form_type)
        if form_type in settings.MULT_FORM_TYPES:
            # For a mult field, we will have to join in the mult table
            # and put the mult column here
            mult_table = get_mult_name(pi.param_qualified_name())
            mult_tables.add((mult_table, table))
            column_names.append(mult_table+'.label')
        else:
            column_names.append(column)
        form_type_formats.append((form_type_format, form_type_func))

    added_extra_columns = 0
    tables.add('obs_general') # We must have obs_general since it owns the ids
    if return_ringobsids:
        if 'obs_general.ring_obs_id' not in column_names:
            column_names.append('obs_general.ring_obs_id')
            added_extra_columns += 1 # So we know to strip it off later
    if return_filespecs:
        if 'obs_general.primary_file_spec' not in column_names:
            column_names.append('obs_general.primary_file_spec')
            added_extra_columns += 1 # So we know to strip it off later
    if return_collection_status:
        column_names.append('collections.opus_id')
        added_extra_columns += 1 # So we know to strip it off later
    # This is kind of obscure, but if there are NO columns at this point,
    # go ahead and force opus_ids to be present because we can't actually
    # do a query on no columns, and we at least want to return a page
    # with the correct number of rows, even if they're all empty!
    if return_opusids or not column_names:
        if 'obs_general.opus_id' not in column_names:
            column_names.append('obs_general.opus_id')
            added_extra_columns += 1 # So we know to strip it off later

    # XXX Something here should specify order for collections
    # colls_order is currently ignored!

    # Figure out the sort order
    all_order = request.GET.get('order', settings.DEFAULT_SORT_ORDER)
    if not all_order:
        all_order = settings.DEFAULT_SORT_ORDER
    if (settings.FINAL_SORT_ORDER
        not in all_order.replace('-','').split(',')):
        if all_order:
            all_order += ','
        all_order += settings.FINAL_SORT_ORDER

    # Figure out what starting observation we're asking for

    page_size = 100 # Pages are hard-coded to be 100 observations long
    page_no = None # Keep these for returning to the caller
    start_obs = None
    offset = None

    if use_collections:
        start_obs = request.GET.get('colls_startobs', None)
        if start_obs is None:
            page_no = request.GET.get('colls_page', 1)
    else:
        start_obs = request.GET.get('startobs', None)
        if start_obs is None:
            page_no = request.GET.get('page', None)
        if start_obs is None and page_no is None:
            start_obs = 1 # Default to using start_obs
    if start_obs is not None:
        try:
            start_obs = int(start_obs)
        except:
            log.error('get_search_results_chunk: Unable to parse startobs "%s"',
                      start_obs)
            return none_return
        offset = start_obs-1
    else:
        try:
            page_no = int(page_no)
        except:
            log.error('get_search_results_chunk: Unable to parse page_no "%s"',
                      page_no)
            return none_return
        offset = (page_no-1)*page_size

    if offset < 0 or offset > settings.SQL_MAX_LIMIT:
        log.error('get_search_results_chunk: Bad offset %s', str(offset))
        return none_return

    temp_table_name = None
    drop_temp_table = False
    params = []
    if not use_collections:
        # This is for a search query

        # Create the SQL query
        # There MUST be some way to do this in Django, but I just can't figure
        # it out. It's incredibly easy to do in raw SQL, so we just do that
        # instead. -RF
        if opus_id:
            selections = {'obs_general.opus_id': [opus_id]}
            extras = {'qtypes': {'obs_general.opus_id': ['matches']}}
        else:
            (selections, extras) = url_to_search_params(request.GET)
        if selections is None:
            log.error('get_search_results_chunk: Could not find selections for'
                      +' request %s', str(request.GET))
            return none_return

        user_query_table = get_user_query_table(selections, extras,
                                                api_code=api_code)
        if not user_query_table:
            log.error('get_search_results_chunk: get_user_query_table failed '
                      +'*** Selections %s *** Extras %s',
                      str(selections), str(extras))
            return none_return

        # First we create a temporary table that contains only those ids
        # in the limit window that we care about (if there's a limit window).
        # Then we use that temporary table (or the original cache table) to
        # extract data from all our data tables.
        temp_table_name = user_query_table

        if page_no != 'all':
            drop_temp_table = True
            pid_sfx = str(os.getpid())
            time1 = time.time()
            time_sfx = ('%.6f' % time1).replace('.', '_')
            temp_table_name = 'temp_'+user_query_table
            temp_table_name += '_'+pid_sfx+'_'+time_sfx
            temp_sql = 'CREATE TEMPORARY TABLE '
            temp_sql += connection.ops.quote_name(temp_table_name)
            temp_sql += ' SELECT sort_order, id FROM '
            temp_sql += connection.ops.quote_name(user_query_table)
            temp_sql += ' ORDER BY sort_order'
            if limit != 'all':
                temp_sql += ' LIMIT '+str(limit)
            temp_sql += ' OFFSET '+str(offset)
            cursor = connection.cursor()
            try:
                cursor.execute(temp_sql)
            except DatabaseError as e:
                log.error('get_search_results_chunk: "%s" returned %s',
                          temp_sql, str(e))
                return none_return
            log.debug('get_search_results_chunk SQL (%.2f secs): %s',
                      time.time()-time1, temp_sql)

        sql = 'SELECT '
        sql += ','.join([connection.ops.quote_name(x.split('.')[0])+'.'+
                         connection.ops.quote_name(x.split('.')[1])
                         for x in column_names])
        sql += ' FROM '+connection.ops.quote_name('obs_general')

        # All the column tables are LEFT JOINs because if the table doesn't
        # have an entry for a given opus_id, we still want the row to show up,
        # just full of NULLs.
        for table in tables:
            if table == 'obs_general':
                continue
            sql += ' LEFT JOIN '+connection.ops.quote_name(table)
            sql += ' ON '+connection.ops.quote_name('obs_general')+'.'
            sql += connection.ops.quote_name('id')+'='
            sql += connection.ops.quote_name(table)+'.'
            sql += connection.ops.quote_name('obs_general_id')

        # Now JOIN in all the mult_ tables.
        for (mult_table, table) in mult_tables:
            sql += ' LEFT JOIN '+connection.ops.quote_name(mult_table)
            sql += ' ON '+connection.ops.quote_name(table)+'.'
            sql += connection.ops.quote_name(mult_table)+'='
            sql += connection.ops.quote_name(mult_table)+'.'
            sql += connection.ops.quote_name('id')

        # But the cache table is an INNER JOIN because we only want opus_ids
        # that appear in the cache table to cause result rows
        sql += ' INNER JOIN '+connection.ops.quote_name(temp_table_name)
        sql += ' ON '+connection.ops.quote_name('obs_general')+'.'
        sql += connection.ops.quote_name('id')+'='
        sql += connection.ops.quote_name(temp_table_name)+'.'
        sql += connection.ops.quote_name('id')

        # Maybe join in the collections table if we need collections_status
        if return_collection_status:
            sql += ' LEFT JOIN '+connection.ops.quote_name('collections')
            sql += ' ON '+connection.ops.quote_name('obs_general')+'.'
            sql += connection.ops.quote_name('id')+'='
            sql += connection.ops.quote_name('collections')+'.'
            sql += connection.ops.quote_name('obs_general_id')
            sql += ' AND '
            sql += connection.ops.quote_name('session_id')+'=%s'
            params.append(session_id)

        sql += ' ORDER BY '
        sql += connection.ops.quote_name(temp_table_name)+'.sort_order'
    else:
        # This is for a collection
        order_params, order_descending_params = parse_order_slug(all_order)
        (order_sql, order_mult_tables,
         order_obs_tables) = create_order_by_sql(order_params,
                                                 order_descending_params)

        sql = 'SELECT '
        sql += ','.join([connection.ops.quote_name(x.split('.')[0])+'.'+
                         connection.ops.quote_name(x.split('.')[1])
                         for x in column_names])
        sql += ' FROM '+connection.ops.quote_name('obs_general')

        # All the column tables are LEFT JOINs because if the table doesn't
        # have an entry for a given opus_id, we still want the row to show up,
        # just full of NULLs.
        for table in tables | order_obs_tables:
            if table == 'obs_general':
                continue
            sql += ' LEFT JOIN '+connection.ops.quote_name(table)
            sql += ' ON '+connection.ops.quote_name('obs_general')+'.'
            sql += connection.ops.quote_name('id')+'='
            sql += connection.ops.quote_name(table)+'.'
            sql += connection.ops.quote_name('obs_general_id')

        # Now JOIN in all the mult_ tables.
        for (mult_table, table) in mult_tables | order_mult_tables:
            sql += ' LEFT JOIN '+connection.ops.quote_name(mult_table)
            sql += ' ON '+connection.ops.quote_name(table)+'.'
            sql += connection.ops.quote_name(mult_table)+'='
            sql += connection.ops.quote_name(mult_table)+'.'
            sql += connection.ops.quote_name('id')

        # But the collections table is an INNER JOIN because we only want
        # opus_ids that appear in the collections table to cause result rows
        sql += ' INNER JOIN '+connection.ops.quote_name('collections')
        sql += ' ON '+connection.ops.quote_name('obs_general')+'.'
        sql += connection.ops.quote_name('id')+'='
        sql += connection.ops.quote_name('collections')+'.'
        sql += connection.ops.quote_name('obs_general_id')
        sql += ' AND '
        sql += connection.ops.quote_name('collections')+'.'
        sql += connection.ops.quote_name('session_id')+'=%s'
        params.append(session_id)

        # Note we don't need to add in a special collections JOIN here for
        # return_collection_status, because we're already joining in the
        # collections table.

        # Finally add in the sort order
        sql += order_sql

    # if page_no != 'all':
    #     base_limit = 100  # explainer of sorts is above
    #     offset = (page_no-1)*base_limit
    #     sql += ' LIMIT '+str(limit)
    #     sql += ' OFFSET '+str(offset)

    time1 = time.time()

    cursor = connection.cursor()
    cursor.execute(sql, params)
    results = []
    more = True
    while more:
        part_results = cursor.fetchall()
        results += part_results
        more = cursor.nextset()

    log.debug('get_search_results_chunk SQL (%.2f secs): %s',
              time.time()-time1, sql)

    if drop_temp_table:
        sql = 'DROP TABLE '+connection.ops.quote_name(temp_table_name)
        try:
            cursor.execute(sql)
        except DatabaseError as e:
            log.error('get_search_results_chunk: "%s" returned %s',
                      sql, str(e))
            return none_return

    if return_opusids:
        # Return a simple list of opus_ids
        opus_id_index = column_names.index('obs_general.opus_id')
        opus_ids = [o[opus_id_index] for o in results]

    if return_ringobsids:
        # And for backwards compatibility, ring_obs_ids
        ring_obs_id_index = column_names.index('obs_general.ring_obs_id')
        ring_obs_ids = [o[ring_obs_id_index] for o in results]

    if return_filespecs:
        # For retrieving preview images, obs_general.primary_file_spec
        file_spec_index = column_names.index('obs_general.primary_file_spec')
        file_specs = [o[file_spec_index] for o in results]

    if return_collection_status:
        # For retrieving collection status
        coll_index = column_names.index('collections.opus_id')
        collection_status = [o[coll_index] for o in results]

    # Strip off the opus_id if the user didn't actually ask for it initially
    if added_extra_columns:
        results = [o[:-added_extra_columns] for o in results]

    # There might be real None entries, which means the join returned null
    # data. Replace these so they look prettier.
    results = [[x if x is not None else 'N/A' for x in r] for r in results]

    # If pi_form_type has format, we format the results
    for idx, (form_type_format, form_type_func) in enumerate(form_type_formats):
        for entry in results:
            if entry[idx] != 'N/A':
                entry[idx] = format_metadata_number_or_func(entry[idx],
                                                            form_type_func,
                                                            form_type_format)

    aux_dict = {}
    if return_opusids:
        aux_dict['opus_ids'] = opus_ids
    if return_ringobsids:
        aux_dict['ring_obs_ids'] = ring_obs_ids
    if return_filespecs:
        aux_dict['file_specs'] = file_specs
    if return_collection_status:
        aux_dict['collection_status'] = collection_status

    return (page_no, start_obs, limit, results, all_order, aux_dict)


def _get_metadata_by_slugs(request, opus_id, cols, fmt, use_param_names,
                           internal, api_code):
    "Returns results for specified slugs."
    (page_no, start_obs, limit, page, order, aux) = get_search_results_chunk(
                                                     request,
                                                     cols=cols,
                                                     opus_id=opus_id,
                                                     limit=1,
                                                     api_code=api_code)

    if page is None or len(page) != 1:
        log.error('_get_metadata_by_slugs: Error searching for opus_id "%s"',
                  opus_id)
        ret = Http404(settings.HTTP404_UNKNOWN_OPUS_ID)
        exit_api_call(api_code, ret)
        raise ret

    slug_list = cols_to_slug_list(cols)
    labels = labels_for_slugs(slug_list)

    if fmt == 'csv':
        return csv_response(opus_id, page, labels)

    # We're just screwing backwards compatibility here and always returning
    # the slug names instead of supporting the support database-internal names
    # that used to be supplied by the metadata API.

    data = []
    if fmt == 'json':
        for slug, result in zip(slug_list, page[0]):
            data.append({slug: result})
        return json_response(data)
    if fmt == 'html':
        if internal:
            for slug, label, result in zip(slug_list, labels, page[0]):
                pi = get_param_info_by_slug(slug)
                data.append({label: (result, pi)})
            return render(request,
                          'results/detail_metadata_slugs_internal.html',
                          {'data': data})
        for label, result in zip(labels, page[0]):
            data.append({label: result})
        return render(request, 'results/detail_metadata_slugs.html',
                      {'data': data})

    log.error('_get_metadata_by_slugs: Unknown format "%s"', fmt)
    ret = Http404(settings.HTTP404_UNKNOWN_FORMAT)
    exit_api_call(api_code, ret)
    raise ret


def get_triggered_tables(selections, extras, api_code=None):
    "Returns the tables triggered by the selections including the base tables."
    if not selections:
        return sorted(settings.BASE_TABLES)

    user_query_table = get_user_query_table(selections, extras,
                                            api_code=api_code)
    if not user_query_table:
        log.error('get_triggered_tables: get_user_query_table failed '
                  +'*** Selections %s *** Extras %s',
                  str(selections), str(extras))
        return None

    cache_key = None
    if user_query_table:
        cache_key = (settings.CACHE_KEY_PREFIX + ':triggered_tables:'
                     + user_query_table)
        cached_val = cache.get(cache_key)
        if cached_val is not None:
            return cached_val

    triggered_tables = settings.BASE_TABLES[:]

    # Now see if any more tables are triggered from query
    queries = {}
    for partable in Partables.objects.all():
        # We are joining the results of a user's query - the single column
        # table of ids - with the trigger_tab listed in the partable
        trigger_tab = partable.trigger_tab
        trigger_col = partable.trigger_col
        trigger_val = partable.trigger_val
        partable = partable.partable

        if partable in triggered_tables:
            continue  # Already triggered, no need to check

        if trigger_tab + trigger_col in queries:
            results = queries[trigger_tab + trigger_col]
        else:
            trigger_model = apps.get_model('search',
                                           ''.join(trigger_tab.title()
                                                   .split('_')))
            results = trigger_model.objects
            if selections:
                if trigger_tab == 'obs_general':
                    where = connection.ops.quote_name(trigger_tab) + '.id='
                    where += user_query_table + '.id'
                else:
                    where = connection.ops.quote_name(trigger_tab)
                    where += '.obs_general_id='
                    where += connection.ops.quote_name(user_query_table) + '.id'
                results = results.extra(where=[where], tables=[user_query_table])
            results = results.distinct().values(trigger_col)
            queries.setdefault(trigger_tab + trigger_col, results)

        if len(results) == 1 and results[0][trigger_col] == trigger_val:
            triggered_tables.append(partable)

        # Surface geometry has multiple targets per observation
        # so we just want to know if our val is in the result
        # (not the only result)
        if 'obs_surface_geometry.target_name' in selections:
            if (trigger_tab == 'obs_surface_geometry' and
                trigger_val.upper() ==
                selections['obs_surface_geometry.target_name'][0].upper()):
                if (trigger_val.upper() in
                    [r['target_name'].upper() for r in results]):
                    triggered_tables.append(partable)

    # Now hack in the proper ordering of tables
    final_table_list = []
    for table in (TableNames.objects.filter(table_name__in=triggered_tables)
                  .values('table_name').order_by('disp_order')):
        final_table_list.append(table['table_name'])

    if cache_key:
        cache.set(cache_key, final_table_list)

    return final_table_list


def get_collection_in_page(opus_id_list, session_id):
    """Returns obs_general_ids in page that are also in user collection.

    This is for views in results where you have to display the gallery
    and indicate which thumbnails are in cart.
    """
    if not session_id:
        return

    cursor = connection.cursor()
    collection_in_page = []
    sql = 'SELECT DISTINCT opus_id FROM '
    sql += connection.ops.quote_name('collections')
    sql += ' WHERE session_id=%s'
    cursor.execute(sql, [session_id])
    rows = []
    more = True
    while more:
        part_rows = cursor.fetchall()
        rows += part_rows
        more = cursor.nextset()
    coll_ids = [r[0] for r in rows]
    ret = [opus_id for opus_id in opus_id_list if opus_id in coll_ids]
    return ret


def labels_for_slugs(slugs, units=True):
    labels = []

    for slug in slugs:
        pi = get_param_info_by_slug(slug, from_ui=True)
        if not pi:
            log.error('api_get_data_and_images: Could not find param_info '
                      +'for %s', slug)
            return None

        # append units if pi_units has unit stored
        unit = None
        if units:
            unit = pi.get_units()
        label = pi.body_qualified_label_results()
        if unit:
            labels.append(label + ' ' + unit)
        else:
            labels.append(label)

    return labels
