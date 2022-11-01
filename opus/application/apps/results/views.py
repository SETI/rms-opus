################################################################################
#
# results/views.py
#
# The API interface for retrieving results (actual data, actual metadata, or
# lists of images or files):
#
#    Format: __api/dataimages.json
#
#    Format: api/data.(?P<fmt>json|html|csv)
#    Format: __api/data.(?P<fmt>csv)
#
#    Format: [__]api/metadata/(?P<opus_id>[-\w]+).(?P<fmt>json|html|csv)
#    Format: api/metadata_v2/(?P<opus_id>[-\w]+).(?P<fmt>json|html|csv)
#
#    Format: api/images/(?P<size>thumb|small|med|full).(?P<fmt>json|html|csv)
#    Format: api/images.(json|html|csv)
#    Format: api/image/(?P<size>thumb|small|med|full)/(?P<opus_id>[-\w]+)
#                          .(?P<fmt>json|html|csv)
#
#    Format: api/files/(?P<opus_id>[-\w]+).json
#    Format: api/files.json
#
#    Format: [__]api/categories/(?P<opus_id>[-\w]+).json
#    Format: api/categories.json
#
#    Format: api/product_types/(?P<opus_id>[-\w]+).json
#    Format: api/product_types.json
#
################################################################################

import json
import logging
import os
import time

import settings

from django.apps import apps
from django.core.cache import cache
from django.db import connection, DatabaseError
from django.http import Http404, HttpResponseServerError
from django.shortcuts import render
from django.views.decorators.cache import never_cache

from metadata.views import (get_cart_count,
                            get_result_count_helper)
from paraminfo.models import ParamInfo
from search.models import Partables, TableNames
from search.views import (get_param_info_by_slug,
                          get_user_query_table,
                          url_to_search_params,
                          create_order_by_sql,
                          parse_order_slug)
from tools.app_utils import (cols_to_slug_list,
                             convert_ring_obs_id_to_opus_id,
                             csv_response,
                             download_filename,
                             enter_api_call,
                             exit_api_call,
                             get_mult_name,
                             get_reqno,
                             get_session_id,
                             json_response,
                             throw_random_http404_error,
                             throw_random_http500_error,
                             HTTP404_BAD_LIMIT,
                             HTTP404_BAD_OFFSET,
                             HTTP404_BAD_OR_MISSING_REQNO,
                             HTTP404_BAD_PAGENO,
                             HTTP404_BAD_STARTOBS,
                             HTTP404_MISSING_OPUS_ID,
                             HTTP404_NO_REQUEST,
                             HTTP404_SEARCH_PARAMS_INVALID,
                             HTTP404_UNKNOWN_CATEGORY,
                             HTTP404_UNKNOWN_FORMAT,
                             HTTP404_UNKNOWN_OPUS_ID,
                             HTTP404_UNKNOWN_RING_OBS_ID,
                             HTTP404_UNKNOWN_SLUG,
                             HTTP500_DATABASE_ERROR,
                             HTTP500_INTERNAL_ERROR,
                             HTTP500_SEARCH_CACHE_FAILED)
from tools.db_utils import (query_table_for_opus_id,
                            lookup_pretty_value_for_mult,
                            lookup_pretty_value_for_mult_list)
from tools.file_utils import get_pds_preview_images, get_pds_products

from opus_support import (format_unit_value,
                          parse_form_type)

log = logging.getLogger(__name__)


################################################################################
#
# API INTERFACES
#
################################################################################

@never_cache
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
               reqno=<N>
               Normal search and selected-column arguments

    Returns JSON.

    Returned JSON:

        {'page': [
            {'opus_id': OPUS_ID,
             'obs_num': <obsnum>,    (only if start_obs=<N> was given)
             'metadata': ['<col1>', '<col2>', '<col3>'],
             'images': {
                'full':
                'med':
             },
             'cart_state': False, 'cart', or 'recycle'
            },
            ...
         ],
         'page_no':             page_no, # If page=<N> given
         'start_obs':           start_obs, # If start_obs=<N> given
         'limit':               limit,
         'order':               comma-separate list of slugs,
         'order_list':          [entry, entry...]
                                entry is {'slug': slug_name,
                                        'label': pretty_name,
                                        'descending': True/False,
                                        'removeable': True/False},
         'count':                       len(page),
         'columns':             columns with units
                                (corresponds to <col1> etc. in 'metadata'),
         'columns_no_units':    columns without units,
         'total_obs_count':     for view=browse, result count as returned by
                                    api/meta/result_count.json
                                for view=cart, cart count + recycled count
                                    as returned by __cart/status.json
         'reqno':               reqno
        }
    """
    api_code = enter_api_call('api_get_data_and_images', request)

    if not request or request.GET is None or request.META is None:
        ret = Http404(HTTP404_NO_REQUEST('/__api/dataimages.json'))
        exit_api_call(api_code, ret)
        raise ret

    session_id = get_session_id(request)

    (page_no, start_obs, limit,
     page, order, aux, error) = get_search_results_chunk(
                                       request,
                                       prepend_cols='opusid',
                                       append_cols='**previewimages',
                                       return_opusids=True,
                                       return_cart_states=True,
                                       api_code=api_code)
    if error is not None:
        return get_search_results_chunk_error_handler(error, api_code)

    preview_jsons = [json.loads(x[-1]) for x in page]
    opus_ids = aux['opus_ids']
    image_list = get_pds_preview_images(opus_ids, preview_jsons,
                                        ['thumb', 'small', 'med', 'full'])

    if not image_list and len(opus_ids) > 0: # pragma: no cover - bad import or data
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

    cart_states = aux['cart_states']
    new_page = []
    for i in range(len(opus_ids)):
        new_entry = {
            'opusid': opus_ids[i],
            'metadata': page[i][1:-1],
            'images': new_image_list[i],
            'cart_state': cart_states[i]
        }
        if start_obs is not None:
            new_entry['obs_num'] = start_obs+i
        new_page.append(new_entry)

    cols = request.GET.get('cols', settings.DEFAULT_COLUMNS)

    labels = labels_for_slugs(cols_to_slug_list(cols))
    labels_no_units = labels_for_slugs(cols_to_slug_list(cols), units=False)
    if (labels is None or labels_no_units is None or
        throw_random_http404_error()): # pragma: no cover -
        # Bad slugs will have already been caught in get_search_results_chunk
        ret = Http404(HTTP404_UNKNOWN_SLUG(None, request))
        exit_api_call(api_code, ret)
        raise ret

    order_slugs = cols_to_slug_list(order)
    order_slugs_pure = [x[1:] if x[0] == '-' else x for x in order_slugs]
    order_labels = labels_for_slugs(order_slugs_pure, units=False)
    if order_labels is None or throw_random_http404_error(): # pragma: no cover -
        # Bad slugs will have already been caught in get_search_results_chunk
        ret = Http404(HTTP404_UNKNOWN_SLUG(None, request))
        exit_api_call(api_code, ret)
        raise ret

    order_list = []
    for idx, (slug, label) in enumerate(zip(order_slugs, order_labels)):
        removeable = not slug.endswith('opusid')
        desc = False
        if slug[0] == '-':
            slug = slug[1:]
            desc = True
        order_entry = {'slug': slug,
                       'label': label,
                       'descending': desc,
                       'removeable': removeable}
        order_list.append(order_entry)

    if request.GET.get('view', 'browse') == 'cart':
        cart_count, recycled_count = get_cart_count(session_id)
        count = cart_count + recycled_count
    else:
        count, _, err = get_result_count_helper(request, api_code)
        if err is not None: # pragma: no cover - database error
            exit_api_call(api_code, err)
            return err

    reqno = get_reqno(request)
    if reqno is None or throw_random_http404_error():
        log.error('api_get_data_and_images: Missing or badly formatted reqno')
        ret = Http404(HTTP404_BAD_OR_MISSING_REQNO(request))
        exit_api_call(api_code, ret)
        raise ret

    data = {'page':             new_page,
            'limit':            limit,
            'count':            len(image_list),
            'order':            order,
            'order_list':       order_list,
            'columns':          labels,
            'columns_no_units': labels_no_units,
            'total_obs_count':  count,
            'reqno':            reqno
            }

    if page_no is not None:
        data['page_no'] = page_no # Bakwards compatibility
    if start_obs is not None:
        data['start_obs'] = start_obs

    ret = json_response(data)
    exit_api_call(api_code, ret)
    return ret


@never_cache
def api_get_data(request, fmt):
    """Return a page of data for a given search.

    This is a PUBLIC API.

    Get data for observations based on search criteria, columns, and sort order.
    Data is returned in chunks given a starting observation and a limit of how
    many to return. We also support "pages" for specifying the starting
    observation for backwards compatibility. A "page" is 100 observations long.
    "page" is not documented in the API Guide.

    Format: api/data.(?P<fmt>json|html|csv)
            __api/data.(?P<fmt>csv)
    Arguments: limit=<N>
               page=<N>  OR  startobs=<N> (1-based)
               order=<column>[,<column>...]
               Normal search and selected-column arguments

    Can return JSON, HTML, or CSV.

    Returned JSON:
        {
            'page_no':             page_no, # If page=<N> given
            'start_obs':           start_obs, # If start_obs=<N> given
            'limit':               limit,
            'count':               len(page),
            'available':           result_count,
            'order':               sort order,
            'labels':              fully-qualified labels,
            'page':                tabular page data
        }

    Returned CSV:
        OPUS ID,Instrument Name,Planet,Intended Target Name,Observation Start Time,Observation Duration (secs)
        vg-iss-2-s-c4360001,Voyager ISS,Saturn,Titan,1981-08-12T14:55:10.080,1.9200

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
    """
    api_code = enter_api_call('api_get_data', request)

    if not request or request.GET is None or request.META is None:
        ret = Http404(HTTP404_NO_REQUEST(f'/api/data.{fmt}'))
        exit_api_call(api_code, ret)
        raise ret

    cols = request.GET.get('cols', settings.DEFAULT_COLUMNS)

    labels = labels_for_slugs(cols_to_slug_list(cols))
    if labels is None or throw_random_http404_error():
        ret = Http404(HTTP404_UNKNOWN_SLUG(None, request))
        exit_api_call(api_code, ret)
        raise ret

    (page_no, start_obs, limit,
     page, order, aux, error) = get_search_results_chunk(
                                                     request,
                                                     cols=cols,
                                                     return_opusids=True,
                                                     api_code=api_code)
    if error is not None:
        return get_search_results_chunk_error_handler(error, api_code)

    result_count, _, err = get_result_count_helper(request, api_code)
    if err is not None: # pragma: no cover - database error
        exit_api_call(api_code, err)
        return err

    data = {}
    if page_no is not None:
        data['page_no'] = page_no # Backwards compatibility
    if start_obs is not None:
        data['start_obs'] = start_obs

    data['limit'] = limit
    data['count'] = len(page)
    data['available'] = result_count
    data['order'] = order
    data['labels'] = labels
    data['columns'] = labels # Backwards compatibility
    data['page'] = page

    if fmt == 'csv':
        csv_data = []
        csv_data.append(labels)
        csv_data.extend(page)
        csv_filename = download_filename(None, 'data')
        ret = csv_response(csv_filename, csv_data)
    elif fmt == 'html':
        context = {'data': data}
        ret = render(request, 'results/data.html', context)
    elif fmt == 'json':
        ret = json_response(data)
    else: # pragma: no cover - error catchall
        log.error('api_get_data: Unknown format "%s"', fmt)
        ret = Http404(HTTP404_UNKNOWN_FORMAT(fmt, request))
        exit_api_call(api_code, ret)
        raise ret

    exit_api_call(api_code, ret)
    return ret


@never_cache
def api_get_metadata(request, opus_id, fmt):
    r"""Return all metadata, sorted by category, for this opus_id.

    This is a PUBLIC API.

    Format: api/metadata/(?P<opus_id>[-\w]+).(?P<fmt>json|html|csv)

    Arguments: cols=<columns>
                    Limit results to particular columns.
                    This is a list of slugs separated by commas.
                    If cols is supplied, cats is ignored.
               cats=<cats>
                    Limit results to particular categories. Categories can be
                    given as "pretty names" as displayed on the Details page,
                    or can be given as table names.

    Can return JSON, HTML, or CSV.

    JSON is indexed by pretty category name, then by column slug.

    HTML and CSV return fully qualified labels.
    """
    return get_metadata(request, opus_id, fmt, 'api_get_metadata', False)


def api_get_metadata_internal(request, opus_id, fmt):
    r"""Return all metadata, sorted by category, for this opus_id.

    This is a PRIVATE API.

    Format: __api/metadata/(?P<opus_id>[-\w]+).(?P<fmt>json|html|csv)

    Arguments: cols=<columns>
                    Limit results to particular columns.
                    This is a list of slugs separated by commas. Note that the
                    return will be indexed by slug name. If cols is supplied, cats is
                    ignored. The slugs in cols may contain optional desired return units
                    of the form "slug:unit". If no unit is specified, the default units
                    are used. If the cols= parameter is not included at all, then all
                    results are returned using their default units, if applicable.
               cats=<cats>
                    Limit results to particular categories. Categories can be
                    given as "pretty names" as displayed on the Details page,
                    or can be given as table names. All results are returned using their
                    default units, if applicable.
               url_cols=<cols>
                    If given, include these column names in the URLs for each
                    search icon for mults/strings in the internal HTML output.
                    This is used on the Detail tab.

    Can return JSON, HTML, or CSV.

    JSON is indexed by pretty category name, then by column slug.

    HTML and CSV return fully qualified labels.

    The only difference between __api/metadata and api_metadata is in the
    returned HTML. The __api version returns an internally-formatted HTML needed
    by the Details tab including things like tooltips. The api version returns
    an externally-formatted HTML that is acceptable to outside users without
    exposing internal details.
    """
    return get_metadata(request, opus_id, fmt, 'api_get_metadata_internal', True)

def get_metadata(request, opus_id, fmt, api_name, internal):
    api_code = enter_api_call(api_name, request)
    if not request or request.GET is None or request.META is None:
        # This could technically be the wrong string for the error message,
        # but since this can never actually happen outside of testing we
        # don't care.
        ret = Http404(HTTP404_NO_REQUEST(f'/api/metadata/{opus_id}.{fmt}'))
        exit_api_call(api_code, ret)
        raise ret

    if not opus_id: # pragma: no cover - configuration error
        ret = Http404(HTTP404_MISSING_OPUS_ID(request))
        exit_api_call(api_code, ret)
        raise ret

    # Backwards compatibility
    orig_opus_id = opus_id
    opus_id = convert_ring_obs_id_to_opus_id(opus_id)
    if not opus_id or throw_random_http404_error():
        ret = Http404(HTTP404_UNKNOWN_RING_OBS_ID(orig_opus_id, request))
        exit_api_call(api_code, ret)
        raise ret

    cols = request.GET.get('cols', False)
    if cols or cols == '':
        ret = _get_metadata_by_slugs(request, opus_id, cols,
                                     fmt,
                                     internal,
                                     api_code)
        if ret is None or throw_random_http404_error(): # pragma: no cover -
            # _get_metadata_by_slugs can't return None
            ret = Http404(HTTP404_UNKNOWN_SLUG(None, request))
            exit_api_call(api_code, ret)
            raise ret
        exit_api_call(api_code, ret)
        return ret

    # Make sure it's a valid OPUS ID
    try:
        results = query_table_for_opus_id('obs_general', opus_id)
        if throw_random_http500_error(): # pragma: no cover - internal debugging
            raise LookupError
    except LookupError: # pragma: no cover - configuration error
        log.error('api_get_metadata: Could not find data model for obs_general')
        ret = HttpResponseServerError(HTTP500_INTERNAL_ERROR(request))
        exit_api_call(api_code, ret)
        return ret
    if len(results) == 0 or throw_random_http404_error():
        log.error('get_metadata: Error searching for opus_id "%s"',
                  opus_id)
        ret = Http404(HTTP404_UNKNOWN_OPUS_ID(opus_id, request))
        exit_api_call(api_code, ret)
        raise ret

    cats = request.GET.get('cats', False)
    url_cols = request.GET.get('url_cols', False)

    # Holds data struct to be returned
    data = {}
    # Holds all the param info objects keyed by table label
    data_all_info = {}

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
        if len(all_tables) != len(cat_list) or throw_random_http404_error():
            log.error('get_metadata: Unknown category name in "%s"',
                      cats)
            ret = Http404(HTTP404_UNKNOWN_CATEGORY(request))
            exit_api_call(api_code, ret)
            raise ret

    # Now find all params and their values in each of these tables
    for table in all_tables:
        table_label = table.label
        table_name = table.table_name
        model_name = ''.join(table_name.title().split('_'))
        all_info = {} # Holds all the param info objects

        # Make a list of all slugs and another of all param_names in this table
        param_info_list = list(ParamInfo.objects
                               .filter(category_name=table_name,
                                       display_results=1)
                               .order_by('disp_order'))
        if param_info_list:
            all_param_names = []
            for param_info in param_info_list:
                if param_info.referred_slug is not None:
                    referred_slug = param_info.referred_slug
                    # A referred slug will never contain a unit specifier
                    param_info = get_param_info_by_slug(referred_slug, 'col',
                                                        allow_units_override=False)
                    param_info.label = param_info.body_qualified_label()
                    param_info.label_results = (
                                param_info.body_qualified_label_results(True))
                    param_info.referred_slug = referred_slug
                else:
                    all_param_names.append(param_info.name)
                all_info[param_info.slug] = param_info
            # Store all param info objects for current table
            data_all_info[table_label] = all_info

            try:
                results = query_table_for_opus_id(table_name, opus_id)
                if throw_random_http500_error(): # pragma: no cover - internal debugging
                    raise LookupError
            except LookupError: # pragma: no cover - configuration error
                log.error('api_get_metadata: Could not find data model for '
                          +'category %s', model_name)
                ret = HttpResponseServerError(HTTP500_INTERNAL_ERROR(request))
                exit_api_call(api_code, ret)
                return ret

            result_vals = results.values(*all_param_names)
            if not result_vals:
                # This is normal - we're looking at ALL tables so many won't
                # have this OPUS_ID in them.
                continue
            result_vals = result_vals[0]
            ordered_results = {}
            for param_info in param_info_list:
                if param_info.referred_slug is not None:
                    referred_slug = param_info.referred_slug
                    # A referred slug will never contain a unit specifier
                    param_info = get_param_info_by_slug(referred_slug, 'col',
                                                        allow_units_override=False)
                    param_info.label = param_info.body_qualified_label()
                    param_info.label_results = (
                                param_info.body_qualified_label_results(True))
                    # Assign referred_slug. This will be used to determine if
                    # the param info is from referred_slug, and we will use
                    # the slug to get the metadata result later.
                    param_info.referred_slug = referred_slug

                (form_type, form_type_format,
                 form_type_unit_id) = parse_form_type(param_info.form_type)

                if form_type in settings.MULT_FORM_TYPES:
                    mult_val = results.values(param_info.name)[0][param_info.name]
                    if form_type != 'MULTIGROUP':
                        # This handles the case of a single mult value where the
                        # value is the index into the associated mult table
                        result = lookup_pretty_value_for_mult(param_info,
                                                              mult_val,
                                                              cvt_null=(fmt!='json'))
                    else:
                        # This handles the case of a "multisel" mult value where the
                        # value is a JSON string containing a list of indexes into
                        # the associated mult table. We display these as
                        # str1,str2,str3
                        result = lookup_pretty_value_for_mult_list(param_info,
                                                                   mult_val,
                                                                   cvt_null=(fmt!='json'))

                else:
                    result = result_vals.get(param_info.name, None)
                    # If this is the param info from referred_slug, we will get
                    # the result data from _get_metadata_by_slugs.
                    if result is None and param_info.referred_slug:
                        r_data = _get_metadata_by_slugs(
                                                    request, opus_id,
                                                    param_info.referred_slug,
                                                    'raw_data',
                                                    internal,
                                                    api_code)
                        result = r_data[0].get(param_info.referred_slug, None)
                        if (result == 'N/A' and fmt == 'json' and
                            form_type != 'STRING'):
                            result = None
                    elif (result is None and fmt != 'json' and
                          form_type != 'STRING'):
                        result = 'N/A'
                    else:
                        # Result is returned in proper format in the default
                        # unit. In this section of the code there is no way for the
                        # caller to specify desired units, so all return values are
                        # given in their default units.
                        result = format_unit_value(result,
                                                   form_type_format,
                                                   form_type_unit_id,
                                                   None)

                if fmt == 'csv':
                    index = param_info.fully_qualified_label_results()
                else:
                    index = param_info.slug
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
        csv_filename = download_filename(opus_id, 'metadata')
        ret = csv_response(csv_filename, csv_data)
    elif fmt == 'html':
        context = {'data': data,
                   'data_all_info': data_all_info,
                   'url_cols': url_cols}
        if internal:
            ret = render(request, 'results/detail_metadata_internal.html',
                         context)
        else:
            ret = render(request, 'results/detail_metadata.html',
                         context)
    elif fmt == 'json':
        ret = json_response(data)
    else: # pragma: no cover - error catchall
        log.error('get_metadata: Unknown format "%s"', fmt)
        ret = Http404(HTTP404_UNKNOWN_FORMAT(fmt, request))
        exit_api_call(api_code, ret)
        raise ret

    exit_api_call(api_code, ret)
    return ret


@never_cache
def api_get_images_by_size(request, size, fmt):
    """Return all images of a particular size for a given search.

    This is a PUBLIC API.

    Format: api/images/(?P<size>thumb|small|med|full).(?P<fmt>json|html|csv)
            __api/images/(?P<size>thumb|small|med|full).(?P<fmt>json)
    Arguments: limit=<N>
               page=<N>  OR  startobs=<N> (1-based)
               order=<column>[,<column>...]
               Normal search arguments

    Can return JSON, HTML, or CSV.
    """
    api_code = enter_api_call('api_get_images_by_size', request)

    ret = _api_get_images(request, fmt, api_code, size, True, None)

    exit_api_call(api_code, ret)
    return ret

@never_cache
def api_get_images(request, fmt):
    """Return all images of all sizes for a given search.

    This is a PUBLIC API.

    Format: api/images.(?P<fmt>json|csv)
    Arguments: limit=<N>
               page=<N>  OR  startobs=<N> (1-based)
               order=<column>[,<column>...]
               Normal search arguments

    Can return JSON or CSV.
    """
    api_code = enter_api_call('api_get_images', request)

    ret = _api_get_images(request, fmt, api_code, None, True, None)

    exit_api_call(api_code, ret)
    return ret

@never_cache
def api_get_image(request, opus_id, size, fmt):
    r"""Return info about a preview image for the given opus_id and size.

    This is a PUBLIC API.

    Format: api/image/(?P<size>[thumb|small|med|full])/(?P<opus_id>[-\w]+).
            (?P<fmt>json|html|csv)

    Can return JSON, HTML, or CSV.
    """
    api_code = enter_api_call('api_get_image', request)

    if not request or request.GET is None or request.META is None:
        ret = Http404(HTTP404_NO_REQUEST(f'/api/image/{size}/{opus_id}.{fmt}'))
        exit_api_call(api_code, ret)
        raise ret

    request.GET = request.GET.copy()
    request.GET['opusid'] = opus_id
    request.GET['qtype-opusid'] = 'matches'
    ret = _api_get_images(request, fmt, api_code, size, False, opus_id)

    exit_api_call(api_code, ret)
    return ret

def _api_get_images(request, fmt, api_code, size, include_search, opus_id):
    if not request or request.GET is None or request.META is None:
        # This could technically be the wrong string for the error message,
        # but since this can never actually happen outside of testing we
        # don't care.
        ret = Http404(HTTP404_NO_REQUEST(f'/api/images/{size}.{fmt}'))
        exit_api_call(api_code, ret)
        raise ret

    (page_no, start_obs, limit,
     page, order, aux, error) = get_search_results_chunk(
                                       request,
                                       cols='opusid,**previewimages',
                                       return_opusids=True,
                                       return_ringobsids=True,
                                       api_code=api_code)
    if error is not None:
        return get_search_results_chunk_error_handler(error, api_code)

    preview_jsons = [json.loads(x[1]) for x in page]
    opus_ids = aux['opus_ids']
    if size is None:
        image_list = get_pds_preview_images(opus_ids, preview_jsons,
                                            ignore_missing=True)
    else:
        image_list = get_pds_preview_images(opus_ids, preview_jsons,
                                            sizes=[size])

    if not image_list:
        log.error('_api_get_images: No image found for: %s', str(opus_ids[:50]))

    # Backwards compatibility
    ring_obs_ids = aux['ring_obs_ids']
    ring_obs_id_dict = {}
    for i in range(len(opus_ids)):
        ring_obs_id_dict[opus_ids[i]] = ring_obs_ids[i]

    for image in image_list:
        if size is not None:
            if size+'_alt_text' in image: # pragma: no cover - always present
                image['alt_text'] = image[size+'_alt_text']
                del image[size+'_alt_text']
            if size+'_size_bytes' in image: # pragma: no cover - always present
                image['size_bytes'] = image[size+'_size_bytes']
                del image[size+'_size_bytes']
            if size+'_width' in image: # pragma: no cover - always present
                image['width'] = image[size+'_width']
                del image[size+'_width']
            if size+'_height' in image: # pragma: no cover - always present
                image['height'] = image[size+'_height']
                del image[size+'_height']
            if size+'_url' in image: # pragma: no cover - always present
                image['url'] = image[size+'_url']
                del image[size+'_url']

            # Backwards compatibility
            path = None
            img = None
            if 'url' in image: # pragma: no cover - always present
                url = image['url']
                if 'previews/' in url:
                    path, img = url.split('previews/')
                    path += 'previews/'
                elif 'browse/' in url:
                    path, img = url.split('browse/')
                    path += 'browse/'
            else: # pragma: no cover
                image['url'] = ''
            image['path'] = path
            image['img'] = img
            image[size] = img

        image['ring_obs_id'] = ring_obs_id_dict[image['opus_id']]

    data = {}
    if include_search:
        result_count, _, err = get_result_count_helper(request, api_code)
        if err is not None: # pragma: no cover - database error
            exit_api_call(api_code, err)
            return err

        if page_no is not None:
            data['page_no'] = page_no # Backwards compatibility
        if start_obs is not None:
            data['start_obs'] = start_obs
        data['limit'] = limit
        data['count'] = len(image_list)
        data['available'] = result_count
        data['order'] = order
    data['data'] = image_list

    if fmt == 'csv':
        csv_data = []
        columns = ['OPUS ID']
        if size is None:
            for img_size in settings.PREVIEW_SIZE_TO_PDS_TYPE.keys():
                columns.append(img_size.title() + ' URL')
        else:
            columns.append('URL')
        for image in image_list:
            if size is None:
                row = [image['opus_id']]
                for img_size in settings.PREVIEW_SIZE_TO_PDS_TYPE.keys():
                    if img_size+'_url' not in image: # pragma: no cover - always present
                        row.append('')
                    else:
                        row.append(image[img_size+'_url'])
                csv_data.append(row)
            else:
                csv_data.append([image['opus_id'], image['url']])
        csv_filename = download_filename(opus_id, 'images')
        ret = csv_response(csv_filename, csv_data, column_names=columns)
    elif fmt == 'html':
        context = {'data': image_list,
                   'size': size}
        ret = render(request, 'results/image_list.html', context)
    elif fmt == 'json':
        ret = json_response(data)
    else: # pragma: no cover - error catchall
        log.error('api_get_images_by_size: Unknown format "%s"', fmt)
        ret = Http404(HTTP404_UNKNOWN_FORMAT(fmt, request))
        exit_api_call(api_code, ret)
        raise ret

    return ret


@never_cache
def api_get_files(request, opus_id=None):
    r"""Return all files for a given opus_id or search results.

    This is a PUBLIC API.

    Format: api/files/(?P<opus_id>[-\w]+).json
            api/files.json
    Arguments: types=<types>   Product types
               limit=<N>
               page=<N>  OR  startobs=<N> (1-based)
               order=<column>[,<column>...]
               Normal search arguments

    Only returns JSON.
    """
    api_code = enter_api_call('api_get_files', request)

    if not request or request.GET is None or request.META is None:
        ret = Http404(HTTP404_NO_REQUEST(f'/api/files/{opus_id}.json'))
        exit_api_call(api_code, ret)
        raise ret

    product_types = request.GET.get('types', 'all')

    opus_ids = []
    if opus_id:
        # Backwards compatibility
        orig_opus_id = opus_id
        opus_id = convert_ring_obs_id_to_opus_id(opus_id)
        if not opus_id or throw_random_http404_error():
            ret = Http404(HTTP404_UNKNOWN_RING_OBS_ID(orig_opus_id, request))
            exit_api_call(api_code, ret)
            raise ret
        opus_ids = [opus_id]
    else:
        # No opus_id passed, get files from search results
        # Override cols because we don't care about anything except
        # opusid
        (page_no, start_obs, limit,
         page, order, aux, error) = get_search_results_chunk(request,
                                                cols='',
                                                return_opusids=True,
                                                api_code=api_code)
        if error is not None:
            return get_search_results_chunk_error_handler(error, api_code)

        opus_ids = aux['opus_ids']

    ret = get_pds_products(opus_ids,
                           loc_type='url',
                           product_types=product_types)

    versioned_ret = {}
    current_ret = {}
    for ret_opus_id in ret:
        versioned_ret[ret_opus_id] = {} # Versions
        current_ret[ret_opus_id] = {}
        for version in ret[ret_opus_id]:
            versioned_ret[ret_opus_id][version] = {}
            for product_type in ret[ret_opus_id][version]:
                versioned_ret[ret_opus_id][version][product_type[2]] = \
                    ret[ret_opus_id][version][product_type]
                if version == 'Current':
                    current_ret[ret_opus_id][product_type[2]] = \
                        ret[ret_opus_id][version][product_type]

    data = {}
    if opus_id is None:
        result_count, _, err = get_result_count_helper(request, api_code)
        if err is not None: # pragma: no cover - database error
            exit_api_call(api_code, err)
            return err

        if page_no is not None:
            data['page_no'] = page_no # Backwards compatibility
        if start_obs is not None:
            data['start_obs'] = start_obs
        data['limit'] = limit
        data['count'] = len(opus_ids)
        data['available'] = result_count
        data['order'] = order
    data['data'] = current_ret
    data['versions'] = versioned_ret

    ret = json_response(data)
    exit_api_call(api_code, ret)
    return ret


@never_cache
def api_get_categories_for_opus_id(request, opus_id):
    r"""Return a JSON list of all categories (tables) this opus_id appears in.

    This is a PUBLIC API.

    Format: [__]api/categories/(?P<opus_id>[-\w]+).json
    """
    api_code = enter_api_call('api_get_categories_for_opus_id', request)

    if not request or request.GET is None or request.META is None:
        ret = Http404(HTTP404_NO_REQUEST(f'/api/categories/{opus_id}.json'))
        exit_api_call(api_code, ret)
        raise ret

    if not opus_id: # pragma: no cover - configuration error
        ret = Http404(HTTP404_MISSING_OPUS_ID(request))
        exit_api_call(api_code, ret)
        raise ret

    # Backwards compatibility
    orig_opus_id = opus_id
    opus_id = convert_ring_obs_id_to_opus_id(opus_id)
    if not opus_id or throw_random_http404_error():
        ret = Http404(HTTP404_UNKNOWN_RING_OBS_ID(orig_opus_id, request))
        exit_api_call(api_code, ret)
        raise ret

    all_categories = []
    table_info = (TableNames.objects.all().values('table_name', 'label')
                  .order_by('disp_order'))

    for tbl in table_info:
        table_name = tbl['table_name']
        if table_name == 'obs_surface_geometry_name':
            # obs_surface_geometry_name is not a data table
            # It's only used to select targets, not to hold data, so remove it
            continue

        try:
            results = query_table_for_opus_id(table_name, opus_id)
        except LookupError: # pragma: no cover - configuration error
            log.error('api_get_categories_for_opus_id: Unable to find table '
                      +'%s', table_name)
            continue
        results = results.values('opus_id')
        if results:
            cat = {'table_name': table_name, 'label': tbl['label']}
            all_categories.append(cat)

    ret = json_response(all_categories)
    exit_api_call(api_code, ret)
    return ret


@never_cache
def api_get_categories_for_search(request):
    """Return a JSON list of all categories (tables) triggered by this search.

    This is a PUBLIC API.

    Format: api/categories.json

    Arguments: Normal search arguments
    """
    api_code = enter_api_call('api_get_categories_for_search', request)

    if not request or request.GET is None or request.META is None:
        ret = Http404(HTTP404_NO_REQUEST('/api/categories.json'))
        exit_api_call(api_code, ret)
        raise ret

    (selections, extras) = url_to_search_params(request.GET)
    if selections is None or throw_random_http404_error():
        log.error('api_get_categories_for_search: Could not find selections for'
                  +' request %s', str(request.GET))
        ret = Http404(HTTP404_SEARCH_PARAMS_INVALID(request))
        exit_api_call(api_code, ret)
        raise ret

    if not selections:
        triggered_tables = settings.BASE_TABLES[:]  # Copy
    else:
        triggered_tables = get_triggered_tables(selections, extras,
                                                api_code=api_code)

    # The main geometry table, obs_surface_geometry_name, is not a table that
    # holds results data. It is only there for selecting targets, which then
    # trigger the other geometry tables. So in the context of returning list of
    # categories it gets removed.
    if 'obs_surface_geometry_name' in triggered_tables: # pragma: no cover -
        # obs_surface_geometry_name should always be in the triggered list
        triggered_tables.remove('obs_surface_geometry_name')

    labels = (TableNames.objects.filter(table_name__in=triggered_tables)
              .values('table_name','label').order_by('disp_order'))

    ret = json_response([ob for ob in labels])
    exit_api_call(api_code, ret)
    return ret


@never_cache
def api_get_product_types_for_opus_id(request, opus_id):
    r"""Return a JSON list of all product types available for this opus_id.

    This is a PUBLIC API.

    Format: api/product_types/(?P<opus_id>[-\w]+).json
    """
    api_code = enter_api_call('api_get_product_types_for_opus_id', request)

    if not request or request.GET is None or request.META is None:
        ret = Http404(HTTP404_NO_REQUEST(f'/api/product_types/{opus_id}.json'))
        exit_api_call(api_code, ret)
        raise ret

    if not opus_id: # pragma: no cover - configuration error
        ret = Http404(HTTP404_MISSING_OPUS_ID(request))
        exit_api_call(api_code, ret)
        raise ret

    # Backwards compatibility
    orig_opus_id = opus_id
    opus_id = convert_ring_obs_id_to_opus_id(opus_id)
    if not opus_id or throw_random_http404_error():
        ret = Http404(HTTP404_UNKNOWN_RING_OBS_ID(orig_opus_id, request))
        exit_api_call(api_code, ret)
        raise ret

    cursor = connection.cursor()
    q = connection.ops.quote_name

    values = []
    sql = 'SELECT DISTINCT '
    sql += q('obs_files')+'.'+q('category')+', '
    sql += q('obs_files')+'.'+q('short_name')+', '
    sql += q('obs_files')+'.'+q('full_name')+', '
    sql += q('obs_files')+'.'+q('version_number')+', '
    sql += q('obs_files')+'.'+q('version_name')+', '
    sql += q('obs_files')+'.'+q('sort_order')
    sql += ' FROM '+q('obs_files')
    sql += ' WHERE '
    sql += q('obs_files')+'.'+q('opus_id')+' = %s'
    values.append(opus_id)
    sql += ' ORDER BY '
    sql += q('obs_files')+'.'+q('sort_order')+', '
    sql += q('obs_files')+'.'+q('version_number')+' DESC'

    log.debug('get_product_types_for_opus_id SQL: %s %s', sql, values)
    cursor.execute(sql, values)

    results = cursor.fetchall()
    product_types = [{'category': x[0],
                      'product_type': x[1],
                      'description': x[2],
                      'version_number': x[3],
                      'version_name': x[4]} for x in results]
    ret = json_response(product_types)

    exit_api_call(api_code, ret)
    return ret


@never_cache
def api_get_product_types_for_search(request):
    """Return a JSON list of all product types available for this search.

    This is a PUBLIC API.

    Format: api/product_types.json

    Arguments: Normal search arguments
    """
    api_code = enter_api_call('api_get_product_types_for_search', request)

    if not request or request.GET is None or request.META is None:
        ret = Http404(HTTP404_NO_REQUEST('/api/product_types.json'))
        exit_api_call(api_code, ret)
        raise ret

    (selections, extras) = url_to_search_params(request.GET)
    if selections is None or throw_random_http404_error():
        log.error('api_get_product_types_for_search: Could not find selections '
                  +'for request %s', str(request.GET))
        ret = Http404(HTTP404_SEARCH_PARAMS_INVALID(request))
        exit_api_call(api_code, ret)
        raise ret

    user_query_table = get_user_query_table(selections, extras, api_code)
    if (not user_query_table or
        throw_random_http500_error()): # pragma: no cover - internal debugging
        log.error('api_get_product_types_for_search: get_user_query_table '
                  +'failed *** Selections %s *** Extras %s',
                  str(selections), str(extras))
        ret = HttpResponseServerError(HTTP500_SEARCH_CACHE_FAILED(request))
        exit_api_call(api_code, ret)
        return ret

    cache_key = (settings.CACHE_SERVER_PREFIX + settings.CACHE_KEY_PREFIX
                 + ':product_types:' + user_query_table)
    cached_val = cache.get(cache_key)
    if cached_val is not None:
        exit_api_call(api_code, cached_val)
        return cached_val

    cursor = connection.cursor()
    q = connection.ops.quote_name

    values = []
    sql = 'SELECT DISTINCT '
    sql += q('obs_files')+'.'+q('category')+', '
    sql += q('obs_files')+'.'+q('short_name')+', '
    sql += q('obs_files')+'.'+q('full_name')+', '
    sql += q('obs_files')+'.'+q('version_number')+', '
    sql += q('obs_files')+'.'+q('version_name')+', '
    sql += q('obs_files')+'.'+q('sort_order')
    sql += ' FROM '+q('obs_files')
    if selections:
        sql += ' INNER JOIN '+q(user_query_table)
        sql += ' ON '+q('obs_files')+'.'+q('obs_general_id')+'='
        sql += q(user_query_table)+'.'+q('id')
    sql += ' ORDER BY '
    sql += q('obs_files')+'.'+q('sort_order')+', '
    sql += q('obs_files')+'.'+q('version_number')+' DESC'

    log.debug('get_product_types_for_search SQL: %s %s', sql, values)
    cursor.execute(sql, values)

    results = cursor.fetchall()
    product_types = [{'category': x[0],
                      'product_type': x[1],
                      'description': x[2],
                      'version_number': x[3],
                      'version_name': x[4]} for x in results]
    ret = json_response(product_types)

    cache.set(cache_key, ret)

    exit_api_call(api_code, ret)
    return ret


################################################################################
#
# SUPPORT ROUTINES
#
################################################################################

def get_search_results_chunk_error_handler(error, api_code):
    if error[0] == 404: # pragma: no cover - 500 won't happen during testing
        ret = Http404(error[1])
        exit_api_call(api_code, ret)
        raise ret
    else: # pragma: no cover
        assert(error[0] == 500)
        ret = HttpResponseServerError(error[1])
        exit_api_call(api_code, ret)
        return ret

def get_search_results_chunk(request, use_cart=None,
                             ignore_recycle_bin=False,
                             cols=None, prepend_cols=None, append_cols=None,
                             limit=None, opus_id=None,
                             start_obs=None,
                             return_opusids=False,
                             return_ringobsids=False,
                             return_cart_states=False,
                             api_code=None):
    """Return a page of results.

        request             Used to find the search and order parameters and
                            columns if not overridden.
        use_cart            Ignore the search parameters and instead use the
                            observations stored in the cart table for
                            this session.
        ignore_recycle_bin  If True, ignore entries in the recycle bin. Only
                            valid if use_cart is True.
        cols                If specified, overrides the columns in request.
        prepend_cols        A string to prepend to the column list.
        append_cols         A string to append to the column list.
        limit               The maximum number of results to return. If not
                            specified, use the limit provided in the request,
                            or the default if none given.
        opus_id             Ignore the search parameters and instead return
                            the result for a single opusid.
        start_obs           Ignore the page or startobs field in the request and
                            use this startobs instead.
        return_opusids      Include 'opus_ids' in the returned aux dict.
                            This is a list of opus_ids 1:1 with the returned
                            data.
        return_ringobsids   Include 'ring_obs_ids' in the returned aux dict.
        return_cart_states
                            Include 'cart_states' in the returned aux
                            dict. This is a list of True/False values 1:1
                            with the returned data indicating if the given
                            observation is in the current cart table for
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
        error               A tuple (response_code, string) if something went
                            wrong. If response_code is 404, then the caller
                            should raise an Http404 exception. If it is 500,
                            then the caller should return
                            HttpResponseServerError.
    """
    def error_return(s, e): return (None, None, None, None, None, None, (s,e))

    session_id = get_session_id(request)

    if use_cart is None:
        if request.GET.get('view', 'browse') == 'cart':
            use_cart = True
        else:
            use_cart = False

    if limit is None:
        limit = request.GET.get('limit', settings.DEFAULT_PAGE_LIMIT)
    if limit == 'all':
        limit = settings.SQL_MAX_LIMIT
    else:
        try:
            limit = int(limit)
            if throw_random_http404_error(): # pragma: no cover - internal testing
                raise ValueError
        except ValueError:
            log.error('get_search_results_chunk: Unable to parse limit %s',
                      limit)
            return error_return(404, HTTP404_BAD_LIMIT(limit, request))
        if (limit < 0 or limit > settings.SQL_MAX_LIMIT or
            throw_random_http404_error()):
            log.error('get_search_results_chunk: Bad limit %s', str(limit))
            return error_return(404, HTTP404_BAD_LIMIT(limit, request))

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
        # Allow the caller to specify desired units for the retrieved metadata
        pi, desired_units = get_param_info_by_slug(slug, 'col',
                                                   allow_units_override=True)
        if not pi or throw_random_http404_error():
            log.error('get_search_results_chunk: Slug "%s" not found', slug)
            return error_return(404, HTTP404_UNKNOWN_SLUG(slug, request))
        column = pi.param_qualified_name()
        table = pi.category_name
        if column.endswith('.opus_id'):
            # opus_id can be displayed from anywhere, but for consistency force
            # it to come from obs_general, since that's the master list.
            # This isn't needed for correctness, just cleanliness.
            table = 'obs_general'
            column = 'obs_general.opus_id'
        tables.add(table)
        (form_type, form_type_format,
         form_type_unit_id) = parse_form_type(pi.form_type)
        if form_type in settings.MULT_FORM_TYPES and form_type != 'MULTIGROUP':
            # For a mult field, we will have to join in the mult table
            # and put the mult column here
            mult_table = get_mult_name(pi.param_qualified_name())
            mult_tables.add((mult_table, False, table, pi.name))
            column_names.append(mult_table+'.label')
        else:
            # For a non-mult column or a MULTIGROUP mult. In the latter case we don't want
            # to return the .label because it's a JSON list of multiple IDs. So just
            # return that list so we can look up the pretty values later.
            column_names.append(column)
        form_type_formats.append((pi, form_type, form_type_format, form_type_unit_id,
                                  desired_units))

    added_extra_columns = 0
    tables.add('obs_general') # We must have obs_general since it owns the ids
    if return_ringobsids:
        if 'obs_general.ring_obs_id' not in column_names: # pragma: no cover -
            # this should not normally be a request field, but could be
            column_names.append('obs_general.ring_obs_id')
            added_extra_columns += 1 # So we know to strip it off later
    if return_cart_states:
        column_names.append('cart.opus_id')
        column_names.append('cart.recycled')
        added_extra_columns += 2 # So we know to strip it off later
    # This is kind of obscure, but if there are NO columns at this point,
    # go ahead and force opus_ids to be present because we can't actually
    # do a query on no columns, and we at least want to return a page
    # with the correct number of rows, even if they're all empty!
    if return_opusids or not column_names:
        if 'obs_general.opus_id' not in column_names:
            column_names.append('obs_general.opus_id')
            added_extra_columns += 1 # So we know to strip it off later

    # Figure out the sort order
    # Note: There is only a single sort order that is used for both the
    # browse tab and the cart tab.
    all_order = request.GET.get('order', settings.DEFAULT_SORT_ORDER)
    if not all_order:
        all_order = settings.DEFAULT_SORT_ORDER
    if (settings.FINAL_SORT_ORDER not in all_order.replace('-','').split(',')):
        all_order += ','+settings.FINAL_SORT_ORDER

    # Figure out what starting observation we're asking for

    page_size = 100 # Pages are hard-coded to be 100 observations long
    page_no = None # Keep these for returning to the caller
    offset = None

    if start_obs is None:
        if use_cart:
            start_obs = request.GET.get('cart_startobs', None)
            if start_obs is None:
                page_no = request.GET.get('cart_page', 1)
        else:
            start_obs = request.GET.get('startobs', None)
            if start_obs is None:
                page_no = request.GET.get('page', None)
        if start_obs is None and page_no is None:
            start_obs = 1 # Default to using start_obs
        if start_obs is not None:
            try:
                start_obs = int(start_obs)
                if throw_random_http404_error(): # pragma: no cover - internal debugging
                    raise ValueError
            except ValueError:
                log.error('get_search_results_chunk: Unable to parse '
                          +'startobs "%s"', start_obs)
                return error_return(404, HTTP404_BAD_STARTOBS(start_obs, request))
            offset = start_obs-1
        else:
            try:
                page_no = int(page_no)
                if throw_random_http404_error(): # pragma: no cover - internal debugging
                    raise ValueError
            except ValueError:
                log.error('get_search_results_chunk: Unable to parse page_no "%s"',
                          page_no)
                return error_return(404, HTTP404_BAD_PAGENO(page_no, request))
            offset = (page_no-1)*page_size
    else:
        offset = start_obs-1

    if (offset < 0 or offset > settings.SQL_MAX_LIMIT or
        throw_random_http404_error()):
        log.error('get_search_results_chunk: Bad offset %s', str(offset))
        return error_return(404, HTTP404_BAD_OFFSET(offset, request))

    q = connection.ops.quote_name

    temp_table_name = None
    drop_temp_table = False
    params = []
    if not use_cart:
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
        if selections is None or throw_random_http404_error():
            log.error('get_search_results_chunk: Could not find selections for'
                      +' request %s', str(request.GET))
            return error_return(404, HTTP404_SEARCH_PARAMS_INVALID(request))

        user_query_table = get_user_query_table(selections, extras,
                                                api_code=api_code)
        if not user_query_table or throw_random_http500_error(): # pragma: no cover -
            # internal or database failure
            log.error('get_search_results_chunk: get_user_query_table failed '
                      +'*** Selections %s *** Extras %s',
                      str(selections), str(extras))
            return error_return(500, HTTP500_SEARCH_CACHE_FAILED(request))

        # First we create a temporary table that contains only those ids
        # in the limit window that we care about (if there's a limit window).
        # Then we use that temporary table (or the original cache table) to
        # extract data from all our data tables.
        drop_temp_table = True
        pid_sfx = str(os.getpid())
        time1 = time.time()
        time_sfx = ('%.6f' % time1).replace('.', '_')
        temp_table_name = 'temp_'+user_query_table
        temp_table_name += '_'+pid_sfx+'_'+time_sfx
        temp_sql = 'CREATE TEMPORARY TABLE '
        temp_sql += q(temp_table_name)
        temp_sql += ' SELECT sort_order, id FROM '+q(user_query_table)
        temp_sql += ' ORDER BY sort_order'
        temp_sql += ' LIMIT '+str(limit)
        temp_sql += ' OFFSET '+str(offset)
        cursor = connection.cursor()
        try:
            cursor.execute(temp_sql)
            if throw_random_http500_error(): # pragma: no cover - internal debugging
                raise DatabaseError
        except DatabaseError as e: # pragma: no cover - database error
            log.error('get_search_results_chunk: "%s" returned %s',
                      temp_sql, str(e))
            return error_return(500, HTTP500_DATABASE_ERROR(request))
        log.debug('get_search_results_chunk SQL (%.2f secs): %s',
                  time.time()-time1, temp_sql)

        sql = 'SELECT '
        sql += ','.join([q(x.split('.')[0])+'.'+
                         q(x.split('.')[1])
                         for x in column_names])
        sql += ' FROM '+q('obs_general')

        # All the column tables are LEFT JOINs because if the table doesn't
        # have an entry for a given opus_id, we still want the row to show up,
        # just full of NULLs.
        for table in tables:
            if table == 'obs_general':
                continue
            sql += ' LEFT JOIN '+q(table)
            sql += ' ON '+q('obs_general')+'.'+q('id')+'='
            sql += q(table)+'.'+q('obs_general_id')

        # Now JOIN in all the mult_ tables.
        for (mult_table, is_multigroup, table, field_name) in mult_tables:
            # We can't have a MULTIGROUP here because those fields are simply
            # added as columns above to be mapped later
            assert not is_multigroup
            sql += ' LEFT JOIN '+q(mult_table)
            sql += ' ON '+q(table)+'.'+q(field_name)+'='
            sql += q(mult_table)+'.'+q('id')

        # But the cache table is an INNER JOIN because we only want opus_ids
        # that appear in the cache table to cause result rows
        sql += ' INNER JOIN '+q(temp_table_name)
        sql += ' ON '+q('obs_general')+'.'+q('id')+'='
        sql += q(temp_table_name)+'.'+q('id')

        # Maybe join in the cart table if we need cart_state
        if return_cart_states:
            sql += ' LEFT JOIN '+q('cart')
            sql += ' ON '+q('obs_general')+'.'+q('id')+'='
            sql += q('cart')+'.'+q('obs_general_id')
            sql += ' AND '
            sql += q('session_id')+'=%s'
            params.append(session_id)

        sql += ' ORDER BY '
        sql += q(temp_table_name)+'.sort_order'
    else:
        # This is for a cart
        order_params, order_descending_params = parse_order_slug(all_order)
        (order_sql, order_mult_tables,
         order_obs_tables) = create_order_by_sql(order_params,
                                                 order_descending_params)

        sql = 'SELECT '
        sql += ','.join([q(x.split('.')[0])+'.'+
                         q(x.split('.')[1])
                         for x in column_names])
        sql += ' FROM '+q('obs_general')

        # All the column tables are LEFT JOINs because if the table doesn't
        # have an entry for a given opus_id, we still want the row to show up,
        # just full of NULLs.
        for table in tables | order_obs_tables:
            if table == 'obs_general':
                continue
            sql += ' LEFT JOIN '+q(table)
            sql += ' ON '+q('obs_general')+'.'+q('id')+'='
            sql += q(table)+'.'+q('obs_general_id')

        # Now JOIN in all the mult_ tables.
        for (mult_table, is_multigroup, table, field_name) in (
                mult_tables | order_mult_tables):
            # If is_multigroup is True, this must have been from order_mult_tables.
            # This is OK, because a multigroup field will never show up in mult_tables
            # (see above), so this field will only be used for sorting.
            sql += ' LEFT JOIN '+q(mult_table)
            sql += ' ON '
            if is_multigroup:
                sql += 'JSON_EXTRACT('
            sql += q(table)+'.'+q(field_name)
            if is_multigroup:
                # For a MULTIGROUP field, we just sort on the first value
                sql += ', "$[0]")'
            sql += '='+q(mult_table)+'.'+q('id')

        # But the cart table is an INNER JOIN because we only want
        # opus_ids that appear in the cart table to cause result rows
        sql += ' INNER JOIN '+q('cart')
        sql += ' ON '+q('obs_general')+'.'+q('id')+'='
        sql += q('cart')+'.'+q('obs_general_id')
        sql += ' AND '
        sql += q('cart')+'.'+q('session_id')+'=%s'
        params.append(session_id)
        if ignore_recycle_bin:
            sql += ' AND '
            sql += q('cart')+'.'+q('recycled')+'=0'

        # Note we don't need to add in a special cart JOIN here for
        # return_cart_states, because we're already joining in the
        # cart table.

        # Finally add in the sort order
        sql += order_sql
        sql += ' LIMIT '+str(limit)
        sql += ' OFFSET '+str(offset)

    time1 = time.time()

    cursor = connection.cursor()
    try:
        cursor.execute(sql, params)
        if throw_random_http500_error(): # pragma: no cover - internal debugging
            raise DatabaseError
    except DatabaseError as e: # pragma: no cover - database error
        log.error('get_search_results_chunk: "%s" + "%s" returned %s',
                  sql, params, str(e))
        return error_return(500, HTTP500_DATABASE_ERROR(request))
    results = []
    more = True
    while more:
        part_results = cursor.fetchall()
        results += part_results
        more = cursor.nextset()

    log.debug('get_search_results_chunk SQL (%.2f secs): %s',
              time.time()-time1, sql)

    if drop_temp_table:
        sql = 'DROP TABLE '+q(temp_table_name)
        try:
            cursor.execute(sql)
            if throw_random_http500_error(): # pragma: no cover - internal debugging
                raise DatabaseError
        except DatabaseError as e: # pragma: no cover - database error
            log.error('get_search_results_chunk: "%s" returned %s',
                      sql, str(e))
            return error_return(500, HTTP500_DATABASE_ERROR(request))

    if return_opusids:
        # Return a simple list of opus_ids
        opus_id_index = column_names.index('obs_general.opus_id')
        opus_ids = [o[opus_id_index] for o in results]

    if return_ringobsids:
        # And for backwards compatibility, ring_obs_ids
        ring_obs_id_index = column_names.index('obs_general.ring_obs_id')
        ring_obs_ids = [o[ring_obs_id_index] for o in results]

    if return_cart_states:
        # For retrieving cart states
        coll_index = column_names.index('cart.recycled')

        def _recycled_mapping(x):
            if x is None:
                return False # Not in cart at all
            if x:
                return 'recycle'
            return 'cart'
        cart_states = [_recycled_mapping(o[coll_index]) for o in results]

    # Strip off the opus_id if the user didn't actually ask for it initially
    if added_extra_columns:
        results = [o[:-added_extra_columns] for o in results]

    # There might be real None entries, which means the join returned null
    # data. Replace these so they look prettier.
    results = [[x if x is not None else 'N/A' for x in r] for r in results]

    # If pi_form_type has format, we format the results
    # This is also where we make pretty lists for MULTIGROUPs
    for idx, (param_info, form_type, form_type_format,
              form_type_unit_id, desired_units) in enumerate(form_type_formats):
        for entry in results:
            if form_type == 'MULTIGROUP':
                # This handles the case of a "multisel" mult value where the
                # value is a JSON string containing a list of indexes into
                # the associated mult table. We display these as
                # str1,str2,str3
                result = lookup_pretty_value_for_mult_list(param_info,
                                                           json.loads(entry[idx]),
                                                           cvt_null=True)
                entry[idx] = result
            if entry[idx] != 'N/A':
                # Result is returned in proper format converted to
                # the given unit
                entry[idx] = format_unit_value(entry[idx],
                                               form_type_format,
                                               form_type_unit_id,
                                               desired_units)

    aux_dict = {}
    if return_opusids:
        aux_dict['opus_ids'] = opus_ids
    if return_ringobsids:
        aux_dict['ring_obs_ids'] = ring_obs_ids
    if return_cart_states:
        aux_dict['cart_states'] = cart_states

    return (page_no, start_obs, limit, results, all_order, aux_dict, None)


def _get_metadata_by_slugs(request, opus_id, cols, fmt, internal, api_code):
    "Returns results for specified slugs."
    (page_no, start_obs, limit,
     page, order, aux, error) = get_search_results_chunk(
                                                     request,
                                                     cols=cols,
                                                     opus_id=opus_id,
                                                     start_obs=1,
                                                     limit=1,
                                                     api_code=api_code)
    if error is not None:
        return get_search_results_chunk_error_handler(error, api_code)

    if len(page) != 1 or throw_random_http404_error(): # pragma: no cover -
        # internal debugging or internal error
        log.error('_get_metadata_by_slugs: Error searching for opus_id "%s"',
                  opus_id)
        ret = Http404(HTTP404_UNKNOWN_OPUS_ID(opus_id, request))
        exit_api_call(api_code, ret)
        raise ret

    slug_list = cols_to_slug_list(cols)
    labels = labels_for_slugs(slug_list)
    if labels is None or throw_random_http404_error(): # pragma: no cover -
        # internal debugging; labels None should be impossible since it will
        # be caught by get_search_results_chunk
        ret = Http404(HTTP404_UNKNOWN_SLUG(None, request))
        exit_api_call(api_code, ret)
        raise ret

    if fmt == 'csv':
        csv_filename = download_filename(opus_id, 'metadata')
        return csv_response(csv_filename, page, labels)

    url_cols = request.GET.get('url_cols', False)

    # We're just screwing backwards compatibility here and always returning
    # the slug names instead of supporting the support database-internal names
    # that used to be supplied by the metadata API.

    data = []
    if fmt == 'json':
        for slug, result in zip(slug_list, page[0]):
            data.append({slug: result})
        return json_response(data)
    elif fmt == 'html':
        if internal:
            # This is only for the Details tab. We allow desired units to be given but
            # we ignore them because they were already processed earlier during
            # get_search_results_chunk.
            for slug, label, result in zip(slug_list, labels, page[0]):
                pi, desired_units = get_param_info_by_slug(slug, 'col',
                                                           allow_units_override=True)
                data.append({label: (result, pi)})
            context = {'data': data,
                       'url_cols': url_cols}
            return render(request,
                          'results/detail_metadata_slugs_internal.html',
                          context)
        for label, result in zip(labels, page[0]):
            data.append({label: result})
        context = {'data': data,
                   'url_cols': url_cols}
        return render(request, 'results/detail_metadata_slugs.html',
                      context)
    elif fmt == 'raw_data':
        for slug, result in zip(slug_list, page[0]):
            data.append({slug: result})
        return data
    else: # pragma: no cover - error catchall
        log.error('_get_metadata_by_slugs: Unknown format "%s"', fmt)
        ret = Http404(HTTP404_UNKNOWN_FORMAT(fmt, request))
        exit_api_call(api_code, ret)
        raise ret


def get_triggered_tables(selections, extras, api_code=None):
    "Returns the tables triggered by the selections including the base tables."
    if not selections:
        return sorted(settings.BASE_TABLES)

    user_query_table = get_user_query_table(selections, extras,
                                            api_code=api_code)
    if not user_query_table: # pragma: no cover - database error
        log.error('get_triggered_tables: get_user_query_table failed '
                  +'*** Selections %s *** Extras %s',
                  str(selections), str(extras))
        return None

    cache_key = (settings.CACHE_SERVER_PREFIX + settings.CACHE_KEY_PREFIX
                 + ':triggered_tables:' + user_query_table)
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
        partable_name = partable.partable

        if partable_name in triggered_tables:
            continue  # Already triggered, no need to check

        if trigger_tab == 'obs_surface_geometry_name':
            # Surface geometry has multiple targets per observation
            # so we just want to know if our val is in the result
            # (not the only result)
            if 'obs_surface_geometry_name.target_name' in selections:
                if (trigger_val.upper() ==
                    selections['obs_surface_geometry_name.target_name'][0].upper()):
                    # If the selected surfacegeo target has no result, we
                    # still want to have the related menu item displayed.
                    triggered_tables.append(partable_name)
        else:
            if trigger_tab + trigger_col in queries:
                results = queries[trigger_tab + trigger_col]
            else:
                trigger_model = apps.get_model('search',
                                               ''.join(trigger_tab.title()
                                                       .split('_')))
                results = trigger_model.objects
                if trigger_tab == 'obs_general': # pragma: no cover -
                    # currently there are no triggers on anything except
                    # obs_general and surface geometry (which is handled
                    # separately above).
                    where = connection.ops.quote_name(trigger_tab) + '.id='
                    where += user_query_table + '.id'
                else: # pragma: no cover
                    where = connection.ops.quote_name(trigger_tab)
                    where += '.obs_general_id='
                    where += connection.ops.quote_name(user_query_table) + '.id'
                results = results.extra(where=[where], tables=[user_query_table])
                results = results.distinct().values(trigger_col)
                queries.setdefault(trigger_tab + trigger_col, results)

            if len(results) == 1 and str(results[0][trigger_col]) == trigger_val:
                triggered_tables.append(partable_name)

    # Now hack in the proper ordering of tables
    final_table_list = []
    for table in (TableNames.objects.filter(table_name__in=triggered_tables)
                  .values('table_name').order_by('disp_order')):
        final_table_list.append(table['table_name'])

    cache.set(cache_key, final_table_list)

    return final_table_list


def labels_for_slugs(slugs, units=True):
    labels = []

    for slug in slugs:
        pi, desired_units = get_param_info_by_slug(slug, 'col',
                                                   allow_units_override=True)
        if not pi:
            log.error('api_get_data_and_images: Could not find param_info '
                      +'for %s', slug)
            return None

        # append units if pi_units has unit stored
        unit = None
        if units:
            unit = pi.get_units(override_unit=desired_units)
        label = pi.body_qualified_label_results()
        if unit:
            labels.append(label + ' ' + unit)
        else:
            labels.append(label)

    return labels
