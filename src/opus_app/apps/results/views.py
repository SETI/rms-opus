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

"""The API handlers that report on a search's results or on a single observation.

The endpoints return observation data, metadata, preview images, file lists,
categories, and product types; each handler's docstring gives the formats it can
produce. The ones that page through the observations a search matched share
`get_search_results_chunk`, which runs the query and hands back one chunk of rows
for the handler to render.
"""

from __future__ import annotations

import json
import logging
import os
import time
from typing import TYPE_CHECKING, Any, Literal

from django.apps import apps
from django.conf import settings
from django.core.cache import cache
from django.db import DatabaseError, connection
from django.http import Http404, HttpResponseServerError
from django.shortcuts import render
from django.views.decorators.cache import never_cache

from opus_app.apps.metadata.views import get_cart_count, get_result_count_helper
from opus_app.apps.paraminfo.models import ParamInfo
from opus_app.apps.search.models import Partables, TableNames
from opus_app.apps.search.views import (
    add_mult_table_joins,
    add_obs_table_joins,
    create_order_by_terms,
    get_param_info_by_slug,
    get_user_query_table,
    parse_order_slug,
    search_cache_join_condition,
    url_to_search_params,
)
from opus_app.apps.tools import sql_builder
from opus_app.apps.tools.app_utils import (
    Http400Error,
    api_view,
    cols_to_slug_list,
    convert_ring_obs_id_to_opus_id,
    csv_response,
    download_filename,
    get_mult_name,
    get_reqno,
    get_session_id,
    http400_bad_limit,
    http400_bad_offset,
    http400_bad_or_missing_reqno,
    http400_bad_pageno,
    http400_bad_startobs,
    http400_missing_opus_id,
    http400_search_params_invalid,
    http400_unknown_category,
    http400_unknown_slug,
    http404_no_request,
    http404_unknown_format,
    http404_unknown_opus_id,
    http404_unknown_ring_obs_id,
    http500_database_error,
    http500_internal_error,
    http500_search_cache_failed,
    json_response,
)
from opus_app.apps.tools.db_utils import (
    lookup_pretty_value_for_mult,
    lookup_pretty_value_for_mult_list,
    query_table_for_opus_id,
)
from opus_app.apps.tools.file_utils import get_pds_preview_images, get_pds_products
from opus_support import format_unit_value, parse_form_type

if TYPE_CHECKING:
    from collections.abc import Collection

    from django.http import HttpRequest, HttpResponse

    #: What `get_search_results_chunk` returns: the page number, the starting
    #: observation number, the limit, the rows, the sort order, the auxiliary
    #: dictionary, and the error. Every other value is None when the error is set,
    #: and the error is None when the read succeeded.
    SearchResultsChunk = tuple[int | None, int | None, int | None,
                               list[list[Any]] | None, str | None,
                               dict[str, Any] | None, tuple[int, str] | None]

log = logging.getLogger(__name__)


################################################################################
#
# API INTERFACES
#
################################################################################

@never_cache
@api_view
def api_get_data_and_images(request: HttpRequest, *, api_code: int) -> HttpResponse:
    """Return a page of data and images for a given search.

    This is a PRIVATE API.

    Get data and images for observations based on search criteria, columns,
    and sort order. Data is returned in chunks given a starting observation
    and a limit of how many to return. We also support "pages" for specifying
    the starting observation for backwards compatibility. A "page" is 100
    observations long.

    ::

        Format: __api/dataimages.json
        Arguments: limit=<N>
                   page=<N>  OR  startobs=<N> (1-based)
                   order=<column>[,<column>...]
                   reqno=<N>
                   Normal search and selected-column arguments

    Returns JSON.

    Returned JSON::

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
    if not request or request.GET is None or request.META is None:
        raise Http404(http404_no_request('/__api/dataimages.json'))

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
        return get_search_results_chunk_error_handler(error)

    # A read that reported no error filled in every other value it returned.
    assert page is not None
    assert aux is not None

    preview_jsons = [json.loads(x[-1]) for x in page]
    opus_ids = aux['opus_ids']
    image_list = get_pds_preview_images(opus_ids, preview_jsons,
                                        ['thumb', 'small', 'med', 'full'])

    if not image_list and len(opus_ids) > 0: # pragma: no cover - bad import or data
        log.error('api_get_data_and_images: No image found for: %r',
                  str(opus_ids[:50]))

    new_image_list = []
    for image in image_list:
        new_image: dict[str, dict[str, Any]] = {}
        for _key, _val in image.items():
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
    if labels is None or labels_no_units is None: # pragma: no cover -
        # Bad slugs will have already been caught in get_search_results_chunk
        raise Http400Error(http400_unknown_slug(None, request))

    order_slugs = cols_to_slug_list(order)
    order_slugs_pure = [x[1:] if x[0] == '-' else x for x in order_slugs]
    order_labels = labels_for_slugs(order_slugs_pure, units=False)
    if order_labels is None: # pragma: no cover -
        # Bad slugs will have already been caught in get_search_results_chunk
        raise Http400Error(http400_unknown_slug(None, request))

    order_list = []
    for _idx, (slug, label) in enumerate(zip(order_slugs, order_labels, strict=False)):
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

    count: int | None
    if request.GET.get('view', 'browse') == 'cart':
        cart_count, recycled_count = get_cart_count(session_id)
        count = cart_count + recycled_count
    else:
        count, _, err = get_result_count_helper(request, api_code)
        if err is not None: # pragma: no cover - database error
            return err

    reqno = get_reqno(request)
    if reqno is None:
        log.error('api_get_data_and_images: Missing or badly formatted reqno')
        raise Http400Error(http400_bad_or_missing_reqno(request))

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

    return json_response(data)


@never_cache
@api_view
def api_get_data(request: HttpRequest, fmt: str, *, api_code: int) -> HttpResponse:
    """Return a page of data for a given search.

    This is a PUBLIC API.

    Get data for observations based on search criteria, columns, and sort order.
    Data is returned in chunks given a starting observation and a limit of how
    many to return. We also support "pages" for specifying the starting
    observation for backwards compatibility. A "page" is 100 observations long.
    "page" is not documented in the API Guide.

    ::

        Format: api/data.(?P<fmt>json|html|csv)
                __api/data.(?P<fmt>csv)
        Arguments: limit=<N>
                   page=<N>  OR  startobs=<N> (1-based)
                   order=<column>[,<column>...]
                   Normal search and selected-column arguments

    Can return JSON, HTML, or CSV.

    Returned JSON::

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

    Returned CSV::

        OPUS ID,Instrument Name,Planet,Intended Target Name,Observation Start Time,Observation Duration (secs)
        vg-iss-2-s-c4360001,Voyager ISS,Saturn,Titan,1981-08-12T14:55:10.080,1.9200

    Returned HTML::

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
    if not request or request.GET is None or request.META is None:
        raise Http404(http404_no_request(f'/api/data.{fmt}'))

    session_id = get_session_id(request)

    cols = request.GET.get('cols', settings.DEFAULT_COLUMNS)

    labels = labels_for_slugs(cols_to_slug_list(cols))
    if labels is None:
        raise Http400Error(http400_unknown_slug(None, request))

    (page_no, start_obs, limit,
     page, order, _aux, error) = get_search_results_chunk(request,
                                                         cols=cols,
                                                         return_opusids=True,
                                                         api_code=api_code)
    if error is not None:
        return get_search_results_chunk_error_handler(error)

    # A read that reported no error filled in every other value it returned.
    assert page is not None

    result_count: int | None
    if request.GET.get('view', 'browse') == 'cart':
        # This part of the API isn't documented for the public but is used in
        # our tests
        cart_count, recycled_count = get_cart_count(session_id)
        result_count = cart_count + recycled_count
    else:
        result_count, _, err = get_result_count_helper(request, api_code)
        if err is not None: # pragma: no cover - database error
            return err

    data: dict[str, Any] = {}
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
        csv_data: list[list[Any]] = []
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
        log.error('api_get_data: Unknown format "%r"', fmt)
        raise Http404(http404_unknown_format(fmt, request))

    return ret


@never_cache
@api_view
def api_get_metadata(request: HttpRequest, opus_id: str, fmt: str, *,
                     api_code: int) -> HttpResponse:
    r"""Return all metadata, sorted by category, for this opus_id.

    This is a PUBLIC API.

    ::

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
    return get_metadata(request, opus_id, fmt, False, api_code)


@api_view
def api_get_metadata_internal(request: HttpRequest, opus_id: str, fmt: str, *,
                              api_code: int) -> HttpResponse:
    r"""Return all metadata, sorted by category, for this opus_id.

    This is a PRIVATE API.

    ::

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
    return get_metadata(request, opus_id, fmt, True, api_code)

def get_metadata(request: HttpRequest, opus_id: str, fmt: str, internal: bool,
                 api_code: int) -> HttpResponse:
    """Return everything OPUS knows about one observation.

    This is what the public and the internal metadata handlers both call.

    Parameters:
        request: The request being served. `?cols=` limits the result to particular
            columns and `?cats=` limits it to particular categories; when both are
            given `?cols=` is used and `?cats=` is ignored.
        opus_id: The observation to describe. An old-format ringobsid is converted
            to an OPUS ID first.
        fmt: The format to return: `'json'`, `'html'`, or `'csv'`.
        internal: Return the HTML the Details tab needs rather than the HTML the
            public endpoint returns. It affects the `'html'` format only.
        api_code: The API call number, for the search helpers' logging.

    Returns:
        An `HttpResponse` holding the metadata in the requested format, or a
        response with status 500 when a category's data model cannot be found.

    Raises:
        Http400Error: If a slug or a category the caller named does not exist, or
            the request itself is malformed.
        Http404: If the OPUS ID names no observation, or the format is unknown.
    """
    if not request or request.GET is None or request.META is None:
        # This could technically be the wrong string for the error message,
        # but since this can never actually happen outside of testing we
        # don't care.
        raise Http404(http404_no_request(f'/api/metadata/{opus_id}.{fmt}'))

    if not opus_id: # pragma: no cover - configuration error
        raise Http400Error(http400_missing_opus_id(request))

    # Backwards compatibility
    orig_opus_id = opus_id
    # The conversion returns None for a ringobsid that names no observation, and
    # the next line turns that into an HTTP 404, so opus_id is a string everywhere
    # the rest of this function reads it.
    opus_id = convert_ring_obs_id_to_opus_id(opus_id)  # type: ignore[assignment]
    if not opus_id:
        raise Http404(http404_unknown_ring_obs_id(orig_opus_id, request))

    cols: str | Literal[False] = request.GET.get('cols', False)
    if cols or cols == '':
        # False is neither truthy nor equal to '', so the test above is passed
        # only by a string.
        assert not isinstance(cols, bool)
        ret = _get_metadata_by_slugs(request, opus_id, cols,
                                     fmt,
                                     internal,
                                     api_code)
        if ret is None: # pragma: no cover -
            # _get_metadata_by_slugs can't return None
            raise Http400Error(http400_unknown_slug(None, request))
        # Only fmt 'raw_data' returns the values themselves, and fmt here is the
        # format named in the URL.
        assert not isinstance(ret, list)
        return ret

    # Make sure it's a valid OPUS ID
    try:
        results = query_table_for_opus_id('obs_general', opus_id)
    except LookupError: # pragma: no cover - configuration error
        log.exception('get_metadata: Could not find data model for obs_general')
        return HttpResponseServerError(http500_internal_error(request))
    if len(results) == 0:
        log.error('get_metadata: Error searching for opus_id "%r"',
                  opus_id)
        raise Http404(http404_unknown_opus_id(opus_id, request))

    cats: str | Literal[False] = request.GET.get('cats', False)
    url_cols = request.GET.get('url_cols', False)

    # Holds data struct to be returned
    data: dict[str, dict[str | None, Any]] = {}
    # Holds all the param info objects keyed by table label
    data_all_info: dict[str, dict[str | None, ParamInfo]] = {}

    all_tables: Collection[TableNames]
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
            log.error('get_metadata: Unknown category name in "%r"',
                      cats)
            raise Http400Error(http400_unknown_category(request))

    # Now find all params and their values in each of these tables
    for table in all_tables:
        table_label = table.label
        table_name = table.table_name
        model_name = ''.join(table_name.title().split('_'))
        all_info: dict[str | None, ParamInfo] = {} # Holds all the param info objects

        # Make a list of all slugs and another of all param_names in this table
        param_info_list = list(ParamInfo.objects
                               .filter(category_name=table_name,
                                       display_results=1)
                               .order_by('disp_order'))
        if param_info_list:
            all_param_names: list[str] = []
            for param_info in param_info_list:
                if param_info.referred_slug is not None:
                    referred_slug = param_info.referred_slug
                    # A referred slug will never contain a unit specifier
                    # A referred_slug that names no field looks up as None and is
                    # dereferenced on the next line; that fault is recorded here
                    # rather than cast away by widening the declaration.
                    param_info = get_param_info_by_slug(referred_slug, 'col',  # type: ignore[assignment]
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
            except LookupError: # pragma: no cover - configuration error
                log.exception('get_metadata: Could not find data model for '
                              +'category %r', model_name)
                return HttpResponseServerError(http500_internal_error(request))

            result_rows = results.values(*all_param_names)
            if not result_rows:
                # This is normal - we're looking at ALL tables so many won't
                # have this OPUS_ID in them.
                continue
            result_vals = result_rows[0]
            ordered_results: dict[str | None, Any] = {}
            for param_info in param_info_list:
                if param_info.referred_slug is not None:
                    referred_slug = param_info.referred_slug
                    # A referred slug will never contain a unit specifier
                    # A referred_slug that names no field looks up as None and is
                    # dereferenced on the next line; that fault is recorded here
                    # rather than cast away by widening the declaration.
                    param_info = get_param_info_by_slug(referred_slug, 'col',  # type: ignore[assignment]
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
                        # 'raw_data' returns the values themselves, except when
                        # the search failed with a 500 and the response is
                        # returned instead; nothing here checks for that, so the
                        # response reaches the subscript below and raises. The
                        # fault is recorded rather than cast away.
                        result = r_data[0].get(param_info.referred_slug, None)  # type: ignore[index, union-attr]
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
        csv_data: list[list[Any]] = []
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
        log.error('get_metadata: Unknown format "%r"', fmt)
        raise Http404(http404_unknown_format(fmt, request))

    return ret


@never_cache
@api_view
def api_get_images_by_size(request: HttpRequest, size: str, fmt: str, *,
                           api_code: int) -> HttpResponse:
    """Return all images of a particular size for a given search.

    This is a PUBLIC API.

    ::

        Format: api/images/(?P<size>thumb|small|med|full).(?P<fmt>json|html|csv)
                __api/images/(?P<size>thumb|small|med|full).(?P<fmt>json)
        Arguments: limit=<N>
                   page=<N>  OR  startobs=<N> (1-based)
                   order=<column>[,<column>...]
                   Normal search arguments

    Can return JSON, HTML, or CSV.
    """
    return _api_get_images(request, fmt, api_code, size, True, None)

@never_cache
@api_view
def api_get_images(request: HttpRequest, fmt: str, *, api_code: int) -> HttpResponse:
    """Return all images of all sizes for a given search.

    This is a PUBLIC API.

    ::

        Format: api/images.(?P<fmt>json|csv)
        Arguments: limit=<N>
                   page=<N>  OR  startobs=<N> (1-based)
                   order=<column>[,<column>...]
                   Normal search arguments

    Can return JSON or CSV.
    """
    return _api_get_images(request, fmt, api_code, None, True, None)

@never_cache
@api_view
def api_get_image(request: HttpRequest, opus_id: str, size: str, fmt: str, *,
                  api_code: int) -> HttpResponse:
    r"""Return info about a preview image for the given opus_id and size.

    This is a PUBLIC API.

    ::

        Format: api/image/(?P<size>thumb|small|med|full)/(?P<opus_id>[-\w]+).
                (?P<fmt>json|html|csv)

    Can return JSON, HTML, or CSV.
    """
    if not request or request.GET is None or request.META is None:
        raise Http404(http404_no_request(f'/api/image/{size}/{opus_id}.{fmt}'))

    # QueryDict.copy() returns a mutable copy, which Django documents and this
    # handler relies on; the stubs describe request.GET as the immutable one the
    # request arrived with, so the copy and the first write into it are marked.
    request.GET = request.GET.copy()  # type: ignore[assignment]
    request.GET['opusid'] = opus_id  # type: ignore[misc]
    request.GET['qtype-opusid'] = 'matches'
    return _api_get_images(request, fmt, api_code, size, False, opus_id)

def _api_get_images(request: HttpRequest, fmt: str, api_code: int, size: str | None,
                    include_search: bool, opus_id: str | None) -> HttpResponse:
    """Return the preview images the search matched, at one size or at every size.

    This is what the three image handlers call.

    Parameters:
        request: The request being served, holding the search and paging arguments.
        fmt: The format to return: `'json'`, `'html'`, or `'csv'`.
        api_code: The API call number, for the search helpers' logging.
        size: The preview size to report on -- `'thumb'`, `'small'`, `'med'`, or
            `'full'` -- or None to report on every size. Naming a size also names
            that size's fields without their size prefix and adds the `path`, `img`
            and `<size>` fields to each image.
        include_search: Include the paging arguments and the result count in the
            JSON. It affects the `'json'` format only.
        opus_id: The observation the request named, used to name a CSV download.
            None names the download for the search instead.

    Returns:
        An `HttpResponse` holding the image list in the requested format.

    Raises:
        Http400Error: If the search or paging arguments are malformed.
        Http404: If the format is unknown, or the handler was called without a
            usable request.
    """
    if not request or request.GET is None or request.META is None:
        # This could technically be the wrong string for the error message,
        # but since this can never actually happen outside of testing we
        # don't care.
        raise Http404(http404_no_request(f'/api/images/{size}.{fmt}'))

    (page_no, start_obs, limit,
     page, order, aux, error) = get_search_results_chunk(
                                       request,
                                       cols='opusid,**previewimages',
                                       return_opusids=True,
                                       return_ringobsids=True,
                                       api_code=api_code)
    if error is not None:
        return get_search_results_chunk_error_handler(error)

    # A read that reported no error filled in every other value it returned.
    assert page is not None
    assert aux is not None

    preview_jsons = [json.loads(x[1]) for x in page]
    opus_ids = aux['opus_ids']
    if size is None:
        image_list = get_pds_preview_images(opus_ids, preview_jsons,
                                            ignore_missing=True)
    else:
        image_list = get_pds_preview_images(opus_ids, preview_jsons,
                                            sizes=[size])

    if not image_list:
        log.error('_api_get_images: No image found for: %r', str(opus_ids[:50]))

    # Backwards compatibility
    ring_obs_ids = aux['ring_obs_ids']
    ring_obs_id_dict: dict[str, str] = {}
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

    data: dict[str, Any] = {}
    if include_search:
        result_count, _, err = get_result_count_helper(request, api_code)
        if err is not None: # pragma: no cover - database error
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
        csv_data: list[list[Any]] = []
        columns = ['OPUS ID']
        if size is None:
            for img_size in settings.PREVIEW_SIZE_TO_PDS_TYPE:
                columns.append(img_size.title() + ' URL')
        else:
            columns.append('URL')
        for image in image_list:
            if size is None:
                row = [image['opus_id']]
                for img_size in settings.PREVIEW_SIZE_TO_PDS_TYPE:
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
        log.error('_api_get_images: Unknown format %r', fmt)
        raise Http404(http404_unknown_format(fmt, request))

    return ret


@never_cache
@api_view
def api_get_files(request: HttpRequest, opus_id: str | None = None, *,
                  api_code: int) -> HttpResponse:
    r"""Return all files for a given opus_id or search results.

    This is a PUBLIC API.

    ::

        Format: api/files/(?P<opus_id>[-\w]+).json
                api/files.json
        Arguments: types=<types>   Product types
                   limit=<N>
                   page=<N>  OR  startobs=<N> (1-based)
                   order=<column>[,<column>...]
                   Normal search arguments

    Only returns JSON.
    """
    if not request or request.GET is None or request.META is None:
        raise Http404(http404_no_request(f'/api/files/{opus_id}.json'))

    product_types = request.GET.get('types', 'all')

    opus_ids: list[str] = []
    if opus_id:
        # Backwards compatibility
        orig_opus_id = opus_id
        opus_id = convert_ring_obs_id_to_opus_id(opus_id)
        if not opus_id:
            raise Http404(http404_unknown_ring_obs_id(orig_opus_id, request))
        opus_ids = [opus_id]
    else:
        # No opus_id passed, get files from search results
        # Override cols because we don't care about anything except
        # opusid
        (page_no, start_obs, limit,
         _page, order, aux, error) = get_search_results_chunk(request,
                                                cols='',
                                                return_opusids=True,
                                                api_code=api_code)
        if error is not None:
            return get_search_results_chunk_error_handler(error)

        # A read that reported no error filled in every other value it returned.
        assert aux is not None

        opus_ids = aux['opus_ids']

    ret = get_pds_products(opus_ids,
                           loc_type='url',
                           product_types=product_types)

    versioned_ret: dict[str, dict[str, dict[str, Any]]] = {}
    current_ret: dict[str, dict[str, Any]] = {}
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

    data: dict[str, Any] = {}
    if opus_id is None:
        result_count, _, err = get_result_count_helper(request, api_code)
        if err is not None: # pragma: no cover - database error
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

    return json_response(data)


@never_cache
@api_view
def api_get_categories_for_opus_id(request: HttpRequest, opus_id: str) -> HttpResponse:
    r"""Return a JSON list of all categories (tables) this opus_id appears in.

    This is a PUBLIC API.

    ::

        Format: [__]api/categories/(?P<opus_id>[-\w]+).json
    """
    if not request or request.GET is None or request.META is None:
        raise Http404(http404_no_request(f'/api/categories/{opus_id}.json'))

    if not opus_id: # pragma: no cover - configuration error
        raise Http400Error(http400_missing_opus_id(request))

    # Backwards compatibility
    orig_opus_id = opus_id
    # The conversion returns None for a ringobsid that names no observation, and
    # the next line turns that into an HTTP 404, so opus_id is a string everywhere
    # the rest of this function reads it.
    opus_id = convert_ring_obs_id_to_opus_id(opus_id)  # type: ignore[assignment]
    if not opus_id:
        raise Http404(http404_unknown_ring_obs_id(orig_opus_id, request))

    all_categories: list[dict[str, Any]] = []
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
            log.exception('api_get_categories_for_opus_id: Unable to find '
                          +'table %r', table_name)
            continue
        opus_id_rows = results.values('opus_id')
        if opus_id_rows:
            cat = {'table_name': table_name, 'label': tbl['label']}
            all_categories.append(cat)

    return json_response(all_categories)


@never_cache
@api_view
def api_get_categories_for_search(request: HttpRequest, *, api_code: int) -> HttpResponse:
    """Return a JSON list of all categories (tables) triggered by this search.

    This is a PUBLIC API.

    ::

        Format: api/categories.json

        Arguments: Normal search arguments
    """
    if not request or request.GET is None or request.META is None:
        raise Http404(http404_no_request('/api/categories.json'))

    (selections, extras) = url_to_search_params(request.GET)
    if selections is None:
        log.error('api_get_categories_for_search: Could not find selections for'
                  +' request %r', str(request.GET))
        raise Http400Error(http400_search_params_invalid(request))

    # url_to_search_params returns both of these or neither.
    assert extras is not None

    if not selections:
        triggered_tables = settings.BASE_TABLES[:]  # Copy
    else:
        # get_triggered_tables returns None when the search's cache table cannot
        # be created, and nothing here checks for it: that None reaches the
        # membership test below and raises TypeError. The fault is recorded here
        # rather than cast away by widening the declaration.
        triggered_tables = get_triggered_tables(selections, extras,  # type: ignore[assignment]
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

    return json_response(list(labels))


@never_cache
@api_view
def api_get_product_types_for_opus_id(request: HttpRequest, opus_id: str) -> HttpResponse:
    r"""Return a JSON list of all product types available for this opus_id.

    This is a PUBLIC API.

    ::

        Format: api/product_types/(?P<opus_id>[-\w]+).json
    """
    if not request or request.GET is None or request.META is None:
        raise Http404(http404_no_request(f'/api/product_types/{opus_id}.json'))

    if not opus_id: # pragma: no cover - configuration error
        raise Http400Error(http400_missing_opus_id(request))

    # Backwards compatibility
    orig_opus_id = opus_id
    # The conversion returns None for a ringobsid that names no observation, and
    # the next line turns that into an HTTP 404, so opus_id is a string everywhere
    # the rest of this function reads it.
    opus_id = convert_ring_obs_id_to_opus_id(opus_id)  # type: ignore[assignment]
    if not opus_id:
        raise Http404(http404_unknown_ring_obs_id(orig_opus_id, request))

    cursor = connection.cursor()

    select, _from_source = _product_types_select()
    select.add_where(sql_builder.binary_op(
        sql_builder.column('opus_id', 'obs_files'), '=',
        sql_builder.value(opus_id)))

    sql, values = select.build()
    log.debug('get_product_types_for_opus_id SQL: %r %r', sql, values)
    cursor.execute(sql, values)

    results = cursor.fetchall()
    product_types = [{'category': x[0],
                      'product_type': x[1],
                      'description': x[2],
                      'version_number': x[3],
                      'version_name': x[4]} for x in results]

    return json_response(product_types)


@never_cache
@api_view
def api_get_product_types_for_search(request: HttpRequest, *, api_code: int) -> HttpResponse:
    """Return a JSON list of all product types available for this search.

    This is a PUBLIC API.

    ::

        Format: api/product_types.json

        Arguments: Normal search arguments
    """
    if not request or request.GET is None or request.META is None:
        raise Http404(http404_no_request('/api/product_types.json'))

    (selections, extras) = url_to_search_params(request.GET)
    if selections is None:
        log.error('api_get_product_types_for_search: Could not find selections '
                  +'for request %r', str(request.GET))
        raise Http400Error(http400_search_params_invalid(request))

    # url_to_search_params returns both of these or neither.
    assert extras is not None

    user_query_table = get_user_query_table(selections, extras, api_code)
    if not user_query_table: # pragma: no cover - internal or database failure
        log.error('api_get_product_types_for_search: get_user_query_table '
                  +'failed *** Selections %r *** Extras %r',
                  str(selections), str(extras))
        return HttpResponseServerError(http500_search_cache_failed(request))

    cache_key = (settings.CACHE_SERVER_PREFIX + settings.CACHE_KEY_PREFIX
                 + ':product_types:' + user_query_table)
    # This cache holds the responses this endpoint built earlier.
    cached_val: HttpResponse | None = cache.get(cache_key)
    if cached_val is not None:
        return cached_val

    cursor = connection.cursor()

    select, from_source = _product_types_select()
    if selections:
        from_source.add_join(
            'INNER', user_query_table,
            sql_builder.columns_equal(
                sql_builder.column('obs_general_id', 'obs_files'),
                sql_builder.column('id', user_query_table)))

    sql, values = select.build()
    log.debug('get_product_types_for_search SQL: %r %r', sql, values)
    cursor.execute(sql, values)

    results = cursor.fetchall()
    product_types = [{'category': x[0],
                      'product_type': x[1],
                      'description': x[2],
                      'version_number': x[3],
                      'version_name': x[4]} for x in results]
    ret = json_response(product_types)

    cache.set(cache_key, ret)

    return ret


################################################################################
#
# SUPPORT ROUTINES
#
################################################################################

def _results_column_select(column_names: list[str]) -> sql_builder.Select:
    """Return a Select over the requested "table.column" names, in order.

    The result rows are unpacked positionally by the caller, so the column order
    is the caller's `column_names` order and nothing may reorder it.

    Parameters:
        column_names: The columns to select, each written `<table>.<column>`.
    """
    select = sql_builder.Select()
    for qualified_name in column_names:
        table_name, _, column_name = qualified_name.partition('.')
        select.add_column(sql_builder.column(column_name, table_name))
    return select


def _product_types_select() -> tuple[sql_builder.Select, sql_builder.FromSource]:
    """Return the (Select, FromSource) shared by the two product_types endpoints.

    Both list the distinct product types found in obs_files, ordered so that the
    "Current" version of a product comes before its older versions; they differ
    only in how they narrow the rows down.
    """
    select = sql_builder.Select(distinct=True)
    for column_name in ('category', 'short_name', 'full_name', 'version_number',
                        'version_name', 'sort_order'):
        select.add_column(sql_builder.column(column_name, 'obs_files'))
    from_source = select.add_from('obs_files')
    select.add_order_by(sql_builder.column('sort_order', 'obs_files'))
    select.add_order_by(sql_builder.column('version_number', 'obs_files'),
                        descending=True)
    return select, from_source


def get_search_results_chunk_error_handler(error: tuple[int, str]) -> HttpResponse:
    """Turn a `get_search_results_chunk` error tuple into an error response.

    Parameters:
        error: The `(status, message)` pair the chunk reader returned. It is 400
            for a malformed request and 500 for a database or internal failure;
            it is never 404, because nothing the reader looks at comes from the
            URL path.

    Returns:
        An `HttpResponse` with status 500, for the 500 case.

    Raises:
        Http400Error: When the request itself was malformed.
    """
    if error[0] == 400:
        raise Http400Error(error[1])
    else: # pragma: no cover - 500 won't happen during testing
        assert error[0] == 500
        return HttpResponseServerError(error[1])

def get_search_results_chunk(request: HttpRequest,
                             use_cart: bool | None = None,
                             ignore_recycle_bin: bool = False,
                             cols: str | None = None,
                             prepend_cols: str | None = None,
                             append_cols: str | None = None,
                             limit: int | str | None = None,
                             opus_id: str | None = None,
                             start_obs: int | None = None,
                             return_opusids: bool = False,
                             return_ringobsids: bool = False,
                             return_cart_states: bool = False,
                             api_code: int | None = None) -> SearchResultsChunk:
    """Return a page of results.

    Parameters:
        request: The request being served. It supplies the search parameters, the
            sort order, and the columns when they are not overridden here.
        use_cart: Ignore the search parameters and use the observations stored in
            the cart table for this session instead. None reads the cart when the
            request asks for `view=cart`.
        ignore_recycle_bin: Ignore the cart entries that are in the recycle bin. It
            is consulted only when the cart is being read.
        cols: The columns to return, as a comma-separated list of slugs, in place of
            the ones in the request.
        prepend_cols: A string to prepend to the column list.
        append_cols: A string to append to the column list.
        limit: The maximum number of results to return. None uses the limit provided
            in the request, or the default if the request gives none. `'all'` asks
            for the largest page the search supports.
        opus_id: Ignore the search parameters and return the result for this single
            opusid instead.
        start_obs: Ignore the page or startobs field in the request and use this
            1-based observation number instead.
        return_opusids: Include `'opus_ids'` in the returned aux dict. This is a
            list of opus_ids 1:1 with the returned data.
        return_ringobsids: Include `'ring_obs_ids'` in the returned aux dict, the
            same way.
        return_cart_states: Include `'cart_states'` in the returned aux dict. This
            is a list 1:1 with the returned data holding, for each observation,
            False when it is not in this session's cart, `'recycle'` when it is in
            the recycle bin, and `'cart'` otherwise.
        api_code: The API call number, for the search helpers' logging.

    Returns:
        A tuple `(page_no, start_obs, limit, results, all_order, aux_dict, error)`.
        `page_no` is set when the page was asked for by page number and `start_obs`
        when it was asked for by observation number; the other one is None. `limit`
        is the maximum number of results that could be returned, `results` holds one
        list of column values per observation, `all_order` is the sort order that
        was used, including a trailing opus_id if necessary, and `aux_dict` holds
        whatever the `return_` arguments asked for. When something goes wrong all
        six of those are None and `error` is a `(response_code, string)` pair to be
        handed to `get_search_results_chunk_error_handler`; the code is 400 when the
        request itself was malformed and 500 on a database or internal failure.
        `error` is None when the page was read.
    """
    def error_return(s: int, e: str) -> SearchResultsChunk:
        """Return the all-None result tuple that carries an error.

        Parameters:
            s: The response code the error should produce.
            e: The message to show.

        Returns:
            The tuple `get_search_results_chunk` returns, with every value None but
            the error.
        """
        return (None, None, None, None, None, None, (s,e))

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
        except ValueError:
            log.error('get_search_results_chunk: Unable to parse limit %r',
                      limit)
            return error_return(400, http400_bad_limit(limit, request))
        if limit < 0 or limit > settings.SQL_MAX_LIMIT:
            log.error('get_search_results_chunk: Bad limit %r', str(limit))
            return error_return(400, http400_bad_limit(limit, request))

    if cols is None:
        cols = request.GET.get('cols', settings.DEFAULT_COLUMNS)

    if prepend_cols:
        cols = prepend_cols + ',' + cols
    if append_cols:
        cols = cols + ',' + append_cols

    form_type_formats: list[tuple[ParamInfo, str | None, str | None, str | None,
                                  str | None]] = []
    column_names: list[str] = []
    tables: set[str] = set()
    mult_tables: set[tuple[str, bool, str, str]] = set()
    for slug in cols_to_slug_list(cols):
        # First try the full name, which might include a trailing 1 or 2
        # Allow the caller to specify desired units for the retrieved metadata
        pi, desired_units = get_param_info_by_slug(slug, 'col',
                                                   allow_units_override=True)
        if not pi:
            log.error('get_search_results_chunk: Slug "%r" not found', slug)
            return error_return(400, http400_unknown_slug(slug, request))
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
    if return_ringobsids and 'obs_general.ring_obs_id' not in column_names: # pragma: no cover -
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
    if (return_opusids or not column_names) and 'obs_general.opus_id' not in column_names:
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
    page_no: int | None = None # Keep these for returning to the caller
    offset: int | None = None

    if start_obs is None:
        raw_start_obs: int | str | None = None
        raw_page_no: int | str | None = None
        if use_cart:
            raw_start_obs = request.GET.get('cart_startobs', None)
            if raw_start_obs is None:
                raw_page_no = request.GET.get('cart_page', 1)
        else:
            raw_start_obs = request.GET.get('startobs', None)
            if raw_start_obs is None:
                raw_page_no = request.GET.get('page', None)
        if raw_start_obs is None and raw_page_no is None:
            raw_start_obs = 1 # Default to using start_obs
        if raw_start_obs is not None:
            try:
                start_obs = int(raw_start_obs)
            except ValueError:
                log.error('get_search_results_chunk: Unable to parse '
                          +'startobs "%r"', raw_start_obs)
                return error_return(400, http400_bad_startobs(raw_start_obs, request))
            offset = start_obs-1
        else:
            # The two are never both absent: the default above sets the one.
            assert raw_page_no is not None
            try:
                page_no = int(raw_page_no)
            except ValueError:
                log.error('get_search_results_chunk: Unable to parse page_no "%r"',
                          raw_page_no)
                return error_return(400, http400_bad_pageno(raw_page_no, request))
            offset = (page_no-1)*page_size
    else:
        offset = start_obs-1

    if offset < 0 or offset > settings.SQL_MAX_LIMIT:
        log.error('get_search_results_chunk: Bad offset %r', str(offset))
        return error_return(400, http400_bad_offset(offset, request))

    temp_table_name: str | None = None
    drop_temp_table = False
    if not use_cart:
        # This is for a search query

        # Create the SQL query
        # There MUST be some way to do this in Django, but I just can't figure
        # it out. It's incredibly easy to do in raw SQL, so we just do that
        # instead. -RF
        selections: dict[str, Any] | None
        extras: dict[str, Any] | None
        if opus_id:
            selections = {'obs_general.opus_id': [opus_id]}
            extras = {'qtypes': {'obs_general.opus_id': ['matches']}}
        else:
            (selections, extras) = url_to_search_params(request.GET)
        if selections is None:
            log.error('get_search_results_chunk: Could not find selections for'
                      +' request %r', str(request.GET))
            return error_return(400, http400_search_params_invalid(request))

        # url_to_search_params returns both of these or neither.
        assert extras is not None

        user_query_table = get_user_query_table(selections, extras,
                                                api_code=api_code)
        if not user_query_table: # pragma: no cover -
            # internal or database failure
            log.error('get_search_results_chunk: get_user_query_table failed '
                      +'*** Selections %r *** Extras %r',
                      str(selections), str(extras))
            return error_return(500, http500_search_cache_failed(request))

        # First we create a temporary table that contains only those ids
        # in the limit window that we care about (if there's a limit window).
        # Then we use that temporary table (or the original cache table) to
        # extract data from all our data tables.
        drop_temp_table = True
        pid_sfx = str(os.getpid())
        time1 = time.time()
        time_sfx = (f'{time1:.6f}').replace('.', '_')
        temp_table_name = 'temp_'+user_query_table
        temp_table_name += '_'+pid_sfx+'_'+time_sfx
        temp_select = sql_builder.Select()
        temp_select.add_column(sql_builder.column('sort_order'))
        temp_select.add_column(sql_builder.column('id'))
        temp_select.add_from(user_query_table)
        temp_select.add_order_by(sql_builder.column('sort_order'))
        temp_select.limit(limit)
        temp_select.offset(offset)
        temp_sql, temp_params = sql_builder.create_table_as_select(
            temp_table_name, temp_select, temporary=True)
        # This SELECT has no WHERE, so it carries no parameters. Assert that
        # rather than discarding the list, so a condition added here later
        # cannot lose its values silently.
        assert not temp_params
        cursor = connection.cursor()
        try:
            cursor.execute(temp_sql)
        except DatabaseError: # pragma: no cover - database error
            log.exception('get_search_results_chunk: "%r" failed', temp_sql)
            return error_return(500, http500_database_error(request))
        log.debug('get_search_results_chunk SQL (%.2f secs): %r',
                  time.time()-time1, temp_sql)

        select = _results_column_select(column_names)
        from_source = select.add_from('obs_general')

        # All the column tables are LEFT JOINs because if the table doesn't
        # have an entry for a given opus_id, we still want the row to show up,
        # just full of NULLs.
        # Sorted so the generated SQL and its debug log are the same from one
        # process to the next: these are sets, and set iteration order depends on
        # PYTHONHASHSEED. The join order carries no meaning either way.
        add_obs_table_joins(from_source, sorted(tables))

        # Now JOIN in all the mult_ tables.
        for (_mult_table, is_multigroup, _table, _field_name) in mult_tables:
            # We can't have a MULTIGROUP here because those fields are simply
            # added as columns above to be mapped later
            assert not is_multigroup
        add_mult_table_joins(from_source, sorted(mult_tables))

        # But the cache table is an INNER JOIN because we only want opus_ids
        # that appear in the cache table to cause result rows
        from_source.add_join(
            'INNER', temp_table_name,
            sql_builder.columns_equal(
                sql_builder.column('id', 'obs_general'),
                sql_builder.column('id', temp_table_name)))

        # Maybe join in the cart table if we need cart_state
        if return_cart_states:
            from_source.add_join(
                'LEFT', 'cart',
                sql_builder.join_exprs(
                    [sql_builder.columns_equal(
                        sql_builder.column('id', 'obs_general'),
                        sql_builder.column('obs_general_id', 'cart')),
                     sql_builder.binary_op(sql_builder.column('session_id',
                                                              'cart'),
                                           '=',
                                           sql_builder.value(session_id))],
                    'AND'))

        select.add_order_by(sql_builder.column('sort_order', temp_table_name))
    else:
        # This is for a cart
        order_params, order_descending_params = parse_order_slug(all_order)
        # An unresolvable order slug is bad user input, not an internal failure.
        # Unchecked, the None reaches create_order_by_terms and trips its
        # `assert order_params`, so the caller sees an AssertionError.
        if order_params is None:
            log.error('get_search_results_chunk: Could not parse order %r',
                      all_order)
            return error_return(400, http400_unknown_slug(None, request))

        # parse_order_slug returns both of these or neither.
        assert order_descending_params is not None

        (order_terms, order_mult_tables,
         order_obs_tables) = create_order_by_terms(order_params,
                                                   order_descending_params)
        if order_terms is None: # pragma: no cover -
            # parse_order_slug resolves every slug through the same ParamInfo
            # lookup, so it fails first; this guard is here because the function
            # documents the return, not because a route reaches it.
            log.error('get_search_results_chunk: Could not build order terms '
                      +'for %r', all_order)
            return error_return(400, http400_unknown_slug(None, request))

        # create_order_by_terms returns all three of these or none of them.
        assert order_mult_tables is not None
        assert order_obs_tables is not None

        select = _results_column_select(column_names)
        from_source = select.add_from('obs_general')

        # All the column tables are LEFT JOINs because if the table doesn't
        # have an entry for a given opus_id, we still want the row to show up,
        # just full of NULLs.
        add_obs_table_joins(from_source, sorted(tables | order_obs_tables))

        # Now JOIN in all the mult_ tables.
        # If is_multigroup is True, this must have been from order_mult_tables.
        # This is OK, because a multigroup field will never show up in mult_tables
        # (see above), so this field will only be used for sorting.
        add_mult_table_joins(from_source,
                             sorted(mult_tables | order_mult_tables))

        # But the cart table is an INNER JOIN because we only want
        # opus_ids that appear in the cart table to cause result rows
        cart_conditions = [
            sql_builder.columns_equal(
                sql_builder.column('id', 'obs_general'),
                sql_builder.column('obs_general_id', 'cart')),
            sql_builder.binary_op(sql_builder.column('session_id', 'cart'), '=',
                                  sql_builder.value(session_id))]
        if ignore_recycle_bin:
            cart_conditions.append(
                sql_builder.binary_op(sql_builder.column('recycled', 'cart'),
                                      '=', sql_builder.value(0)))
        from_source.add_join('INNER', 'cart',
                             sql_builder.join_exprs(cart_conditions, 'AND'))

        # Note we don't need to add in a special cart JOIN here for
        # return_cart_states, because we're already joining in the
        # cart table.

        # Finally add in the sort order
        for order_column, descending in order_terms:
            select.add_order_by(order_column, descending=descending)
        select.limit(limit)
        select.offset(offset)

    sql, params = select.build()

    time1 = time.time()

    cursor = connection.cursor()
    try:
        cursor.execute(sql, params)
    except DatabaseError: # pragma: no cover - database error
        log.exception('get_search_results_chunk: "%r" + "%r" failed',
                      sql, params)
        return error_return(500, http500_database_error(request))
    results = []
    more = True
    while more:
        part_results = cursor.fetchall()
        results += part_results
        more = cursor.nextset()

    log.debug('get_search_results_chunk SQL (%.2f secs): %r',
              time.time()-time1, sql)

    if drop_temp_table:
        # drop_temp_table is set only where the temporary table was named.
        assert temp_table_name is not None
        sql = sql_builder.drop_table(temp_table_name)
        try:
            cursor.execute(sql)
        except DatabaseError: # pragma: no cover - database error
            log.exception('get_search_results_chunk: "%r" failed', sql)
            return error_return(500, http500_database_error(request))

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

        def _recycled_mapping(x: int | None) -> Literal[False, 'recycle', 'cart']:
            """Return the cart state a cart.recycled column value stands for.

            Parameters:
                x: The cart table's `recycled` value for the observation, or None
                    when the join found no cart row for it.

            Returns:
                False when the observation is not in the cart, `'recycle'` when it
                is in the recycle bin, and `'cart'` otherwise.
            """
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

    aux_dict: dict[str, Any] = {}
    if return_opusids:
        aux_dict['opus_ids'] = opus_ids
    if return_ringobsids:
        aux_dict['ring_obs_ids'] = ring_obs_ids
    if return_cart_states:
        aux_dict['cart_states'] = cart_states

    return (page_no, start_obs, limit, results, all_order, aux_dict, None)


def _get_metadata_by_slugs(request: HttpRequest, opus_id: str, cols: str, fmt: str,
                           internal: bool,
                           api_code: int) -> HttpResponse | list[dict[str, Any]]:
    """Return the values of the given columns for one observation.

    Parameters:
        request: The request being served. `?url_cols=` names the columns the
            internal HTML puts in the search links it draws.
        opus_id: The observation to describe.
        cols: The columns to return, as a comma-separated list of slugs. A slug may
            carry a `:unit` suffix naming the units its value is wanted in.
        fmt: `'json'`, `'html'`, or `'csv'` to return a response in that format, or
            `'raw_data'` to return the values themselves.
        internal: Return the HTML the Details tab needs rather than the HTML the
            public endpoint returns. It affects the `'html'` format only.
        api_code: The API call number, for the search helpers' logging.

    Returns:
        For `'raw_data'`, a list holding one `{slug: value}` dictionary per column,
        in the order the slugs were given. For every other format, an `HttpResponse`
        carrying the values. A search that failed with a database error returns that
        failure's response whatever the format is.

    Raises:
        Http400Error: If a slug the caller named does not exist.
        Http404: If the OPUS ID names no observation, or the format is unknown.
    """
    (_page_no, _start_obs, _limit,
     page, _order, _aux, error) = get_search_results_chunk(
                                                     request,
                                                     cols=cols,
                                                     opus_id=opus_id,
                                                     start_obs=1,
                                                     limit=1,
                                                     api_code=api_code)
    if error is not None:
        return get_search_results_chunk_error_handler(error)

    # A read that reported no error filled in every other value it returned.
    assert page is not None

    if len(page) != 1: # pragma: no cover - internal error
        log.error('_get_metadata_by_slugs: Error searching for opus_id "%r"',
                  opus_id)
        raise Http404(http404_unknown_opus_id(opus_id, request))

    slug_list = cols_to_slug_list(cols)
    labels = labels_for_slugs(slug_list)
    if labels is None: # pragma: no cover -
        # labels None should be impossible since it will be caught by
        # get_search_results_chunk
        raise Http400Error(http400_unknown_slug(None, request))

    if fmt == 'csv':
        csv_filename = download_filename(opus_id, 'metadata')
        return csv_response(csv_filename, page, labels)

    url_cols = request.GET.get('url_cols', False)

    # We're just screwing backwards compatibility here and always returning
    # the slug names instead of supporting the support database-internal names
    # that used to be supplied by the metadata API.

    data: list[dict[str, Any]] = []
    if fmt == 'json':
        for slug, result in zip(slug_list, page[0], strict=False):
            data.append({slug: result})
        return json_response(data)
    elif fmt == 'html':
        if internal:
            # This is only for the Details tab. We allow desired units to be given but
            # we ignore them because they were already processed earlier during
            # get_search_results_chunk.
            for slug, label, result in zip(slug_list, labels, page[0], strict=False):
                pi, _desired_units = get_param_info_by_slug(slug, 'col',
                                                           allow_units_override=True)
                data.append({label: (result, pi)})
            context = {'data': data,
                       'url_cols': url_cols}
            return render(request,
                          'results/detail_metadata_slugs_internal.html',
                          context)
        for label, result in zip(labels, page[0], strict=False):
            data.append({label: result})
        context = {'data': data,
                   'url_cols': url_cols}
        return render(request, 'results/detail_metadata_slugs.html',
                      context)
    elif fmt == 'raw_data':
        for slug, result in zip(slug_list, page[0], strict=False):
            data.append({slug: result})
        return data
    else: # pragma: no cover - error catchall
        log.error('_get_metadata_by_slugs: Unknown format "%r"', fmt)
        raise Http404(http404_unknown_format(fmt, request))


def get_triggered_tables(selections: dict[str, list[Any]], extras: dict[str, Any],
                         api_code: int | None = None) -> list[str] | None:
    """Return the tables triggered by the selections including the base tables.

    Parameters:
        selections: The search's selections, as `url_to_search_params` returns them.
        extras: The search's extras, as `url_to_search_params` returns them.
        api_code: The API call number, for the search helpers' logging.

    Returns:
        The names of the triggered tables, in the order they are displayed in, or
        the base tables sorted by name when there are no selections. It is None when
        the search's cache table could not be created.
    """
    if not selections:
        return sorted(settings.BASE_TABLES)

    user_query_table = get_user_query_table(selections, extras,
                                            api_code=api_code)
    if not user_query_table: # pragma: no cover - database error
        log.error('get_triggered_tables: get_user_query_table failed '
                  +'*** Selections %r *** Extras %r',
                  str(selections), str(extras))
        return None

    cache_key = (settings.CACHE_SERVER_PREFIX + settings.CACHE_KEY_PREFIX
                 + ':triggered_tables:' + user_query_table)
    # This cache holds the table lists this function built earlier.
    cached_val: list[str] | None = cache.get(cache_key)
    if cached_val is not None:
        return cached_val

    triggered_tables = settings.BASE_TABLES[:]

    # Now see if any more tables are triggered from query
    queries: dict[str, list[Any]] = {}
    for partable in Partables.objects.all():
        # We are joining the results of a user's query - the single column
        # table of ids - with the trigger_tab listed in the partable
        trigger_tab = partable.trigger_tab
        trigger_col = partable.trigger_col
        trigger_val = partable.trigger_val
        partable_name = partable.partable
        # The importer writes all four of these columns for every row it creates,
        # and the model declares them nullable only because the schema does.
        assert trigger_tab is not None
        assert trigger_col is not None
        assert trigger_val is not None
        assert partable_name is not None

        if partable_name in triggered_tables:
            continue  # Already triggered, no need to check

        if trigger_tab == 'obs_surface_geometry_name':
            # Surface geometry has multiple targets per observation
            # so we just want to know if our val is in the result
            # (not the only result)
            if ('obs_surface_geometry_name.target_name' in selections and
                    trigger_val.upper() ==
                    selections['obs_surface_geometry_name.target_name'][0].upper()):
                # If the selected surfacegeo target has no result, we
                # still want to have the related menu item displayed.
                triggered_tables.append(partable_name)
        else:
            if trigger_tab + trigger_col in queries:
                results = queries[trigger_tab + trigger_col]
            else:
                # We are joining the search's cache table, which has no model,
                # so this is raw SQL rather than an ORM query. The model is
                # still what resolves the trigger column's name, because a field
                # declared with db_column is not named by its column.
                #
                # Currently there are no triggers on anything except obs_general
                # and surface geometry (which is handled separately above), so
                # only the obs_general arm of the join condition is reachable
                # from here -- both arms of the equivalent branch used to be
                # marked "# pragma: no cover" for that reason.
                trigger_model = apps.get_model('search',
                                               ''.join(trigger_tab.title()
                                                       .split('_')))
                trigger_column = trigger_model._meta.get_field(trigger_col).column
                select = sql_builder.Select(distinct=True)
                select.add_column(sql_builder.column(trigger_column, trigger_tab))
                select.add_from(trigger_tab)
                select.add_from(user_query_table)
                select.add_where(search_cache_join_condition(trigger_tab,
                                                             user_query_table))
                sql, sql_params = select.build()
                log.debug('get_triggered_tables SQL: %r *** PARAMS %r',
                          sql, str(sql_params))
                cursor = connection.cursor()
                cursor.execute(sql, sql_params)
                results = [row[0] for row in cursor.fetchall()]
                queries.setdefault(trigger_tab + trigger_col, results)

            if len(results) == 1 and str(results[0]) == trigger_val:
                triggered_tables.append(partable_name)

    # Now hack in the proper ordering of tables
    final_table_list: list[str] = []
    for table in (TableNames.objects.filter(table_name__in=triggered_tables)
                  .values('table_name').order_by('disp_order')):
        final_table_list.append(table['table_name'])

    cache.set(cache_key, final_table_list)

    return final_table_list


def labels_for_slugs(slugs: list[str], units: bool = True) -> list[str] | None:
    """Return the label to display for each of the given column slugs.

    Parameters:
        slugs: The column slugs, each of which may carry a `:unit` suffix naming
            the units the label should report.
        units: Include the units in each label.

    Returns:
        The labels, one per slug and in the same order, or None if one of the slugs
        names no metadata field.
    """
    labels: list[str] = []

    for slug in slugs:
        pi, desired_units = get_param_info_by_slug(slug, 'col',
                                                   allow_units_override=True)
        if not pi:
            log.error('labels_for_slugs: Could not find param_info '
                      +'for %r', slug)
            return None

        # append units if pi_units has unit stored
        unit = None
        if units:
            unit = pi.get_units(override_unit=desired_units)
        label = pi.body_qualified_label_results()
        # A field whose label_results column is NULL has no results label, and
        # nothing here checks for that: the first line below raises on it and the
        # second puts a None among the labels. The fault is recorded rather than
        # cast away.
        if unit:
            labels.append(label + ' ' + unit)  # type: ignore[operator]
        else:
            labels.append(label)  # type: ignore[arg-type]

    return labels
