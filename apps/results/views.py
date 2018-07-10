################################################
#
#   results.views
#
#    gallery and details pages
#       page numbers, pictures, details, triggered tables, etc
#
################################################
import settings
import json
import csv
from django.template import loader, Context
from django.http import Http404
from django.shortcuts import render
from collections import OrderedDict as SortedDict
from django.db import connection, DatabaseError
from django.apps import apps
from django.core.exceptions import FieldError
from search.views import *
from search.models import *
from paraminfo.models import *
from metadata.views import *
from metrics.views import update_metrics
from django.views.decorators.cache import never_cache
from user_collections.models import Collections

from tools.app_utils import *
from tools.file_utils import *
from tools.db_utils import *

import logging
log = logging.getLogger(__name__)


def api_get_data(request, fmt):
    """Return a page of data for a given search and page_no.

    Can return JSON, HTML, or RAW.

    Returned JSON is of the format:
        data = {
                'page_no': page_no,
                'limit':   limit,
                'page':    page,         # tabular page data
                'count':   len(page),
                'labels':  labels
                }
    """
    update_metrics(request)
    api_code = enter_api_call('api_get_data', request)

    ret = get_data(request, fmt)

    exit_api_call(api_code, ret)
    return ret


def api_get_files(request, opus_id=None, fmt='raw'):
    update_metrics(request)
    api_code = enter_api_call('api_get_files', request)

    product_types = request.GET.get('types', 'all')
    loc_type = request.GET.get('loc_type', 'url')

    if request and request.GET and not opus_id:
        # no opus_id passed, get files from search results
        # XXX NEED TO LOOK AT THIS AGAIN ###
        (selections, extras) = urlToSearchParams(request.GET)
        page = api_get_data(request,'raw')['page']
        if not len(page):
            exit_api_call(api_code, False)
            return False
        opus_id = [p[0] for p in page]

    ret = get_pds_products(opus_id=opus_id, fmt=fmt,
                           loc_type=loc_type,
                           product_types=product_types)
    exit_api_call(api_code, ret)
    return ret


def api_get_image(request, opus_id, size='med', fmt='raw'):
    """Return info about a preview image for the given opus_id and size.

    Valid sizes are: thumb, small, med, full

    return HttpResponse(img + "<br>" + opus_id + ' ' + size )
    """
    update_metrics(request)
    api_code = enter_api_call('api_get_image', request)

    image_list = get_pds_preview_images(opus_id, size)
    if len(image_list) != 1:
        log.error('api_get_image: Could not find preview for opus_id "%s" size "%s"',
                  str(opus_id), str(size))
        image_list = []
    image_list[0]['url'] = image_list[0][size+'_url']
    data = {'data': image_list}
    ret = responseFormats(data, fmt, size=size,
                          template='image_list.html')
    exit_api_call(api_code, ret)
    return ret

def api_get_all_categories(request, opus_id):
    """Return a JSON list of all cateories (tables) this opus_id appears in."""
    update_metrics(request)
    api_code = enter_api_call('api_get_all_categories', request)

    all_categories = []
    table_info = TableNames.objects.all().values('table_name', 'label').order_by('disp_order')

    for tbl in table_info:
        table_name = tbl['table_name']
        if table_name == 'obs_surface_geometry':
            # obs_surface_geometry is not a data table
            # it's only used to select targets, not to hold data, so remove it
            continue

        try:
            results = query_table_for_opus_id(table_name, opus_id)
        except LookupError:
            log.error("Didn't find table %s", table_name)
            continue
        results = results.values('opus_id')
        if results:
            cat = {'table_name': table_name, 'label': tbl['label']}
            all_categories.append(cat)

    ret = HttpResponse(json.dumps(all_categories),
                     content_type="application/json")
    exit_api_call(api_code, ret)
    return ret


def api_get_metadata(request, opus_id, fmt):
    """Return all metadata, sorted by category, for this opus_id.

    The argument "cols" can be used to limit results to particular columns.
    This is a list of slugs separated by commas. Note that the return will
    be indexed by field name, but by slug name.

    The argument "cats" can be used to limit results to particular categories.

    TODO: XXX
        make it return cols by slug as field name if cols are slugs (no underscores)
        if cols does has underscores make it return field names as column name
        (this is a fix for backward compatablility )

        and om make 'field' an alias for 'cols' plz omg what is 'cols' even

        if cat is passed returns all in the named category(s) and ignores cols

        you will have to add a column to table_names "slug" to get a
        url-worthy representation of the category name

    """
    update_metrics(request)
    api_code = enter_api_call('api_get_metadata', request)

    if not opus_id: raise Http404

    slugs = None
    try:
        slugs = request.GET.get('cols', False)
    except AttributeError:
        pass  # No request was sent
    if slugs:
        ret = _get_metadata_by_slugs(request, opus_id, slugs.split(','),
                                     fmt)
        exit_api_call(api_code, ret)
        return ret

    try:
        cats = request.GET.get('cats', False)
    except AttributeError:
        cats = False  # No request was sent

    data = SortedDict()     # holds data struct to be returned
    all_info = SortedDict() # holds all the param info objects

    # find all the tables (categories) this observation belongs to,
    if not cats:
        all_tables = TableNames.objects.filter(display='Y').order_by('disp_order')
    else:
        # restrict table to those found in cats
        all_tables = TableNames.objects.filter(table_name__in=cats.split(','), display='Y').order_by('disp_order')

    # now find all params and their values in each of these tables:
    for table in all_tables:
        table_label = table.label
        table_name = table.table_name
        model_name = ''.join(table_name.title().split('_'))

        # make a list of all slugs and another of all param_names in this table
        all_slugs = [param.slug for param in ParamInfo.objects.filter(category_name=table_name, display_results=1).order_by('disp_order')]
        all_param_names = [param.name for param in ParamInfo.objects.filter(category_name=table_name, display_results=1).order_by('disp_order')]

        for k, slug in enumerate(all_slugs):
            param_info = ParamInfo.objects.get(slug=slug)
            name = param_info.name
            all_info[name] = param_info

        if all_param_names:
            try:
                try:
                    results = query_table_for_opus_id(table_name, opus_id)
                except LookupError:
                    log.error("Could not find data model for category %s", model_name)
                    break
                results = results.values(*all_param_names)[0]

                # results is an ordinary dict so here to make sure we have the correct ordering:
                ordered_results = SortedDict({})
                for param in all_param_names:
                    ordered_results[param] = results[param]

                data[table_label] = ordered_results

            except IndexError:
                # this is pretty normal, it will check every table for a ring obs id
                # a lot of observations do not appear in a lot of tables..
                # for example something on jupiter won't appear in a saturn table..
                # log.error('IndexError: no results found for {0} in table {1}'.format(opus_id, table_name) )
                pass  # no results found in this table, move along
            except AttributeError:
                log.error('AttributeError: No results found for opus_id %s in table %s', opus_id, table_name)
                pass  # no results found in this table, move along
            except FieldError:
                log.error('FieldError: No results found for opus_id %s in table %s', opus_id, table_name)
                pass  # no results found in this table, move along

    if fmt == 'html':
        # hack because we want to display labels instead of param names
        # on our html Detail page
        ret = render(request, 'detail_metadata.html',locals())
    if fmt == 'json':
        ret = HttpResponse(json.dumps(data), content_type="application/json")
    if fmt == 'raw':
        ret = data, all_info  # includes definitions for opus interface

    exit_api_call(api_code, ret)
    return ret


def get_data(request, fmt):
    """Return a page of data for a given search and page_no.

    Can return JSON, HTML, or RAW.

    Returned JSON is of the format:
        data = {
                'page_no': page_no,
                'limit':   limit,
                'page':    page,         # tabular page data
                'count':   len(page),
                'labels':  labels
                }
    """
    session_id = get_session_id(request)

    (page_no, limit, page, opus_ids, order) = get_page(request)

    checkboxes = request.is_ajax()

    slugs = request.GET.get('cols', settings.DEFAULT_COLUMNS)
    if not slugs:
        slugs = settings.DEFAULT_COLUMNS

    is_column_chooser = request.GET.get('col_chooser', False)

    labels = []
    id_index = None

    for slug_no, slug in enumerate(slugs.split(',')):
        if slug == 'opusid':
            id_index = slug_no
        try:
            labels += [ParamInfo.objects.get(slug=slug).label_results]
        except ParamInfo.DoesNotExist:
            # this slug doesn't match anything in param_info, nix it
            if '1' in slug:
                # single column range slugs will not have the index, but
                # will come in with it because of how ui is designed, so
                # look for the slug without the index
                temp_slug = slug[:-1]
                try:
                    labels += [ParamInfo.objects.get(slug=temp_slug).label_results]
                except ParamInfo.DoesNotExist:
                    log.error('Could not find param_info for %s', slug)
                    continue

    if is_column_chooser:
        labels.insert(0, "add")   # adds a column for checkbox add-to-collections

    collection = ''
    if request.is_ajax():
        # find the members of user collection in this page
        # for pre-filling checkboxes
        collection = get_collection_in_page(opus_ids, session_id)

    data = {'page_no': page_no,
            'limit':   limit,
            'page':    page,
            'count':   len(page),
            'labels':  labels
           }

    if fmt == 'raw':
        ret = data
    ret = responseFormats(data, fmt, template='data.html', id_index=id_index,
                          labels=labels, checkboxes=checkboxes,
                          collection=collection, order=order)
    return ret

def get_page(request, colls=None, colls_page=None, page=None):
    """Return a page of results."""
    # get some stuff from the url or fall back to defaults
    session_id = get_session_id(request)

    if not colls:
        collection_page = request.GET.get('colls', False)
    else:
        collection_page = colls

    limit = int(request.GET.get('limit', settings.DEFAULT_PAGE_LIMIT))
    slugs = request.GET.get('cols', settings.DEFAULT_COLUMNS)

    column_names = []  # Format: obs_pds.product_id
    tables = set()
    for slug in slugs.split(','):
        try:
            # First try the full name, which might include a trailing 1 or 2
            column = ParamInfo.objects.get(slug=slug).param_name()
        except ParamInfo.DoesNotExist:
            # Then try the name with the number "1" stripped because that's how
            # the UI sends it when there is only a single column
            column = ParamInfo.objects.get(slug=slug.strip('1')).param_name()
        except ParamInfo.DoesNotExist:
            log.error('get_page: Slug "%s" not found', slug)
            continue
        table = column.split('.')[0]
        if column.endswith('.opus_id'):
            # opus_id can be displayed from anywhere, but for consistency force
            # it to come from obs_general, since that's the master list.
            # This isn't needed for correctness, just cleanliness.
            table = 'obs_general'
            column = 'obs_general.opus_id'
        tables.add(table)
        column_names.append(column)

    added_extra_columns = 0
    tables.add('obs_general') # We must have obs_general since it owns the ids
    if 'obs_general.opus_id' not in column_names:
        column_names.append('obs_general.opus_id')
        added_extra_columns += 1 # So we know to strip it off later

    # Figure out the sort order
    order = None
    if collection_page:
        order = request.GET.get('colls_order', settings.DEFAULT_SORT_ORDER)
    if not order:
        order = request.GET.get('order', settings.DEFAULT_SORT_ORDER)
    order_param = None
    if order:
        descending = order[0] == '-'
        order = order.strip('-')
        try:
            order_param = ParamInfo.objects.get(slug=order).param_name()
        except ParamInfo.DoesNotExist:
            log.error('_get_pad: Unable to resolve order slug "%s"', order)
        else:
            table = order_param.split('.')[0]
            if order_param not in column_names:
                tables.add(table)
                column_names.append(order_param)
                added_extra_columns += 1 # So we know to strip it off later

    # Figure out what page we're asking for
    if collection_page:
        if colls_page:
            page_no = colls_page
        else:
            page_no = request.GET.get('colls_page', 1)
    else:
        if page:
            page_no = page
        else:
            page_no = request.GET.get('page', 1)
    if page_no != 'all':
        try:
            page_no = int(page_no)
        except:
            log.error('get_page: Unable to parse page "%s"',
                      str(page_no))
            page_no = 1

    if not collection_page:
        # This is for a search query

        # Create the SQL query
        # There MUST be some way to do this in Django, but I just can't figure
        # it out. It's incredibly easy to do in raw SQL, so we just do that
        # instead. -RF
        (selections, extras) = urlToSearchParams(request.GET)
        user_query_table = getUserQueryTable(selections, extras)

        sql = 'SELECT '
        sql += ','.join(column_names)
        sql += ' FROM obs_general'

        # All the column tables are LEFT JOINs because if the table doesn't
        # have an entry for a given opus_id, we still want the row to show up,
        # just full of NULLs.
        for table in tables:
            if table == 'obs_general':
                continue
            sql += ' LEFT JOIN '+connection.ops.quote_name(table)
            sql += ' ON obs_general.id='+connection.ops.quote_name(table)
            sql += '.obs_general_id'

        # But the cache table is a RIGHT JOIN because we only want opus_ids that
        # appear in the cache table to cause result rows
        sql += ' INNER JOIN '+connection.ops.quote_name(user_query_table)
        sql += ' ON obs_general.id='+connection.ops.quote_name(user_query_table)
        sql += '.id'
    else:
        # this is for a collection
        sql = 'SELECT '
        sql += ','.join(column_names)
        sql += ' FROM obs_general'

        # All the column tables are LEFT JOINs because if the table doesn't
        # have an entry for a given opus_id, we still want the row to show up,
        # just full of NULLs.
        for table in tables:
            if table == 'obs_general':
                continue
            sql += ' LEFT JOIN '+connection.ops.quote_name(table)
            sql += ' ON obs_general.id='+connection.ops.quote_name(table)
            sql += '.obs_general_id'

        # But the cache table is a RIGHT JOIN because we only want opus_ids that
        # appear in the cache table to cause result rows
        sql += ' INNER JOIN collections'
        sql += ' ON obs_general.id=collections.obs_general_id AND '
        sql += 'collections.session_id="'+session_id+'"'

    # Add in the ordering
    if order_param:
        sql += ' ORDER BY '+order_param
        if descending:
            sql += ' DESC'

    """
    the limit is pretty much always 100, the user cannot change it in the interface
    but as an aide to finding the right chunk of a result set to search for
    for the 'add range' click functinality, the front end may send a large limit, like say
    page_no = 42 and limit = 400
    that means start the page at 42 and go 4 pages, and somewhere in there is our range
    this is how 'add range' works accross multiple pages
    so the way of computing starting offset here should always use the base_limit of 100
    using the passed limit will result in the wrong offset because of way offset is computed here
    this may be an awful hack.
    """
    if page_no != 'all':
        base_limit = 100  # explainer of sorts is above
        offset = (page_no-1)*base_limit
        sql += ' LIMIT '+str(limit)
        sql += ' OFFSET '+str(offset)

    print 'get_page SQL', sql
    cursor = connection.cursor()
    cursor.execute(sql)
    results = cursor.fetchall()

    # Return a simple list of opus_ids
    opus_id_index = column_names.index('obs_general.opus_id')
    opus_ids = [o[opus_id_index] for o in results]

    # Strip off the opus_id if the user didn't actually ask for it initially
    if added_extra_columns:
        results = [o[:-added_extra_columns] for o in results]

    # There might be real None entries, which means the join returned null
    # data. Replace these so they look prettier.
    results = [[x if x is not None else 'N/A' for x in r] for r in results]

    return (page_no, limit, results, opus_ids, order)


def _get_metadata_by_slugs(request, opus_id, slugs, fmt):
    """
    returns results for specified slugs
    """
    params_by_table = {}  # params by table_name
    data = []
    all_info = {}

    for slug in slugs:
        param_info = get_param_info_by_slug(slug)
        if not param_info:
            log.error(
        "get_metadata_by_slugs: Could not find param_info entry for slug %s",
        str(slug))
            continue  # todo this should raise end user error
        table_name = param_info.category_name
        params_by_table.setdefault(table_name, []).append(param_info.param_name().split('.')[1])
        all_info[slug] = param_info  # to get things like dictionary entries for interface

    if slugs and not all_info:
        # none of the slugs were valid slugs
        # can't ignore them and return all metadata because can lead to infinite recursion here
        raise Http404

    for table_name, param_list in params_by_table.items():
        try:
            results = query_table_for_opus_id(table_name, opus_id)
        except LookupError:
            continue
        results = results.values(*param_list)

        if not results:
            # this opus_id doesn't exist in this table, log this..
            log.error('Could not find opus_id %s in table %s', opus_id, table_name)
        else:
            for param,value in results[0].items():
                data.append({param: value})

    if fmt == 'html':
        return render(request, 'detail_metadata_slugs.html',locals())
    if fmt == 'json':
        return HttpResponse(json.dumps(data), content_type="application/json")
    if fmt == 'raw':
        return data, all_info  # includes definitions for opus interface





def category_list_http_endpoint(request):
    """ returns a list of triggered categories (table_names) and labels
        as json response
        for use as part of public http api """
    if request and request.GET:
        try:
            (selections,extras) = urlToSearchParams(request.GET)
        except TypeError:
            selections = None
    else:
        selections = None

    if not selections:
        triggered_tables = settings.BASE_TABLES[:]  # makes a copy of settings.BASE_TABLES
    else:
        triggered_tables = get_triggered_tables(selections, extras)

    # the main geometry table, obs_surface_geometry, is not table that holds results data
    # it is only there for selecting targets, which then trigger the other geometry tables.
    # so in the context of returning list of categories it gets removed..
    try:
        triggered_tables.remove('obs_surface_geometry')
    except ValueError:
        pass  # it wasn't in there so no worries

    labels = TableNames.objects.filter(table_name__in=triggered_tables).values('table_name','label').order_by('disp_order')

    return HttpResponse(json.dumps([ob for ob in labels]), content_type="application/json")


def get_triggered_tables(selections, extras=None):
    """
    this looks at user request and returns triggered tables as list
    always returns the settings.BASE_TABLES
    """
    if not bool(selections):
        return sorted(settings.BASE_TABLES)

    # look for cache:
    cache_no = getUserQueryTable(selections,extras)
    cache_key = 'triggered_tables_' + str(cache_no)
    if (cache.get(cache_key)):
        return sorted(cache.get(cache_key))

    # first add the base tables
    triggered_tables = settings.BASE_TABLES[:]  # makes a copy of settings.BASE_TABLES

    # this is a hack to do something special for the usability of the Surface Geometry section
    # surface geometry is always triggered and showing by default,
    # but for some instruments there is actually no data there.
    # if one of those instruments is constrained directly - that is,
    # one of these instruments is selected in the Instrument Name widget
    # remove the geometry tab from the triggered tables

    # instruments with no surface geo metadata:
    # partables
    fields_to_check = ['obs_general.instrument_id','obs_general.inst_host_id','obs_general.mission_id']
    no_metadata = ['Hubble','CIRS','Galileo']
    for field in fields_to_check:
        if field not in selections:
            continue
        for inst in selections[field]:
            for search_string in no_metadata:
                if search_string in inst:
                    try:
                        triggered_tables.remove('obs_surface_geometry')
                    except Exception as e:
                        log.error("get_triggered_tables threw: %s", str(e))
                        log.error(".. Selections: %s", str(selections))
                        log.error(".. Field: %s", str(field))
                        log.error(".. Inst: %s", str(inst))


    # now see if any more tables are triggered from query
    query_result_table = getUserQueryTable(selections,extras)
    queries = {}  # keep track of queries
    for partable in Partables.objects.all():
        # we are joining the results of a user's query - the single column table of ids
        # with the trigger_tab listed in the partable,
        trigger_tab = partable.trigger_tab
        trigger_col = partable.trigger_col
        trigger_val = partable.trigger_val
        partable = partable.partable


        if partable in triggered_tables:
            continue  # already triggered, no need to check

        # get query
        # did we already do this query?

        if trigger_tab + trigger_col in queries:
            results = queries[trigger_tab + trigger_col]
        else:
            trigger_model = apps.get_model('search', ''.join(trigger_tab.title().split('_')))
            results = trigger_model.objects
            if query_result_table:
                if trigger_tab == 'obs_general':
                    where   = trigger_tab + ".id = " + query_result_table + ".id"
                else:
                    where   = trigger_tab + ".obs_general_id = " + query_result_table + ".id"
                results = results.extra(where=[where], tables=[query_result_table])
            results = results.distinct().values(trigger_col)
            queries.setdefault(trigger_tab + trigger_col, results)

        if (len(results) == 1) and (unicode(results[0][trigger_col]) == trigger_val):
            # we has a triggered table
            triggered_tables.append(partable)

        # surface geometry have multiple targets per observation
        # so we just want to know if our val is in the result (not the only result)
        if 'obs_surface_geometry.target_name' in selections:
            if trigger_tab == 'obs_surface_geometry' and trigger_val.upper() == selections['obs_surface_geometry.target_name'][0].upper():
                if trigger_val.upper() in [r['target_name'].upper() for r in results]:
                    triggered_tables.append(partable)


    # now hack in the proper ordering of tables
    final_table_list = []
    for table in TableNames.objects.filter(table_name__in=triggered_tables).values('table_name').order_by('disp_order'):
        final_table_list.append(table['table_name'])

    cache.set(cache_key, final_table_list)

    return sorted(final_table_list)


# this should return an image for every row..

@never_cache
def api_get_images(request, fmt):
    """
    this returns rows from images table that correspond to request
    some rows will not have images, this function doesn't return 'image_not_found' information
    if a row doesn't have an image you get nothing. you lose. good day sir. #fixme #todo

    """
    update_metrics(request)
    api_code = enter_api_call('api_get_images', request)

    session_id = get_session_id(request)

    alt_size = request.GET.get('alt_size', '')
    columns = request.GET.get('cols', settings.DEFAULT_COLUMNS)

    try:
        [page_no, limit, page, opus_ids, order] = get_page(request)
    except TypeError:  # get_page returns False
        log.error("404 error")
        raise Http404('could not find page')

    # XXX This is horrid and needs to be fixed
    image_list = get_pds_preview_images(opus_ids,
                                        ['thumb', 'small', 'med', 'full'])

    if not image_list:
        log.error('get_images: No image found for: %s', str(opus_ids[:50]))

    collection_opus_ids = get_all_in_collection(request)
    for image in image_list:
        image['in_collection'] = image['opus_id'] in collection_opus_ids

    ret = responseFormats({'data': image_list}, fmt,
                          alt_size=alt_size, columns_str=columns.split(','),
                          template='gallery.html', order=order)
    exit_api_call(api_code, ret)
    return ret


def get_base_path_previews(opus_id):
    # find the proper volume_id to pass to the Files table before asking for file_path
    # (sometimes the Files table has extra entries for an observation with funky paths)
    try:
        volume_id = ObsGeneral.objects.filter(opus_id=opus_id)[0].volume_id
    except IndexError:
        return

    file_path = Files.objects.filter(opus_id=opus_id, volume_id=volume_id)[0].base_path

    base_path = '/'.join(file_path.split('/')[-2:])

    return base_path


def file_name_cleanup(base_file):
    base_file = base_file.replace('.','/')
    base_file = base_file.replace(':','/')
    base_file = base_file.replace('[','/')
    base_file = base_file.replace(']','/')
    base_file = base_file.replace('.','/')
    base_file = base_file.replace('//','/')
    base_file = base_file.replace('///','/')
    return base_file




def ____OLD_BROKENget_page(request, colls=None, colls_page=None, page=None):
    """Return a page of results."""
    update_metrics(request)

    # get some stuff from the url or fall back to defaults
    session_id = get_session_id(request)

    if not colls:
        collection_page = request.GET.get('colls', False)
    else:
        collection_page = colls

    limit = int(request.GET.get('limit', settings.DEFAULT_PAGE_LIMIT))
    slugs = request.GET.get('cols', settings.DEFAULT_COLUMNS)

    column_values = set()
    column_values_ordered = []
    tables = set()
    for slug in slugs.split(','):
        try:
            # First try the full name
            column = [ParamInfo.objects.get(slug=slug).param_name()]
        except ParamInfo.DoesNotExist:
            # Then try the name with the number "1" stripped because that's how
            # the UI sends it
            column = [ParamInfo.objects.get(slug=slug.strip('1')).param_name()]
        except ParamInfo.DoesNotExist:
            continue
        column = ''.join(column)
        table = column.split('.')[0]
        field = column.split('.')[1]
        if table != 'obs_general' and field != 'opus_id':  #this is already added by django apparently so don't add twice
            tables.add(table)
            column_values.add(table+'__'+field)
            column_values_ordered.append(table+'__'+field)
        else:
            column_values.add(field)
            column_values_ordered.append(field)

    column_values = list(column_values)

    if not collection_page:
        # this is for a search query

        order = request.GET.get('order', 'time1')
        # figure out column order in table
        if order:
            try:
                descending = '-' if order[0] == '-' else None
                order_slug = order.strip('-')  # strip off any minus sign to look up param name
                order = ParamInfo.objects.get(slug=order_slug).param_name()
                if descending:
                    order = '-' + order
            except DoesNotExist:
                order = False

        # figure out page we are asking for
        if not page:
            page_no = request.GET.get('page', 1)
            if page_no != 'all':
                try:
                    page_no = int(page_no)
                except:
                    page_no = 1
        else:
            page_no = page

        # ok now that we have everything from the url get stuff from db
        (selections, extras) = urlToSearchParams(request.GET)
        user_query_table = getUserQueryTable(selections, extras)

        # figure out what tables do we need to join in and build query
        where = " AND ".join(["obs_general.id = " + connection.ops.quote_name(table) + ".obs_general_id " for table in tables])
        #special case for cache_NO table; perhaps TODO rename field from id to obs_general_id in cache tables
        where += " AND obs_general.id = " + connection.ops.quote_name(user_query_table) + ".id"
        tables.add(user_query_table)
        results = ObsGeneral.objects.extra(where=[where], tables=tables)

    else:
        # this is for a collection

        # find the ordering
        order = request.GET.get('colls_order', False)
        if not order:
            # get regular order if collections doesn't have a special order
            order = request.GET.get('order',False)

        if order:
            try:
                order_param = order.strip('-')  # strip off any minus sign to look up param name
                descending = order[0] if (order[0] == '-') else None
                order = ParamInfo.objects.get(slug=order_param).name
                if descending:
                    order = '-' + order
            except DoesNotExist:
                order = False

        if not colls_page:
            page_no = request.GET.get('colls_page',1)
            if page_no != 'all':
                page_no = int(page_no)
        else:
            page_no = colls_page

        # join in the collections table
        #### FIX ME this went away!
        colls_table_name = get_collection_table(session_id)
        triggered_tables.append(colls_table_name)
        where   = "obs_general.opus_id = " + connection.ops.quote_name(colls_table_name) + ".opus_id"
        results = ObsGeneral.objects.extra(where=[where], tables=triggered_tables)

    # now we have results object (either search or collections)
    if order:
        results = results.order_by(order)

    """
    the limit is pretty much always 100, the user cannot change it in the interface
    but as an aide to finding the right chunk of a result set to search for
    for the 'add range' click functinality, the front end may send a large limit, like say
    page_no = 42 and limit = 400
    that means start the page at 42 and go 4 pages, and somewhere in there is our range
    this is how 'add range' works accross multiple pages
    so the way of computing starting offset here should always use the base_limit of 100
    using the passed limit will result inthe wront offset because of way offset is computed here
    this may be an aweful hack.
    """
    return None
    if page_no != 'all':
        base_limit = 100  # explainer of sorts is above
        offset = (page_no-1)*base_limit # we don't use Django's pagination because of that count(*) that it does.
        results = results[offset:offset+int(limit)].values_list(*column_values_ordered)
    else:
        results = results.values_list(*column_values_ordered)

    # return a simple list of opus_ids
    opus_id_index = column_values.index('opus_id')
    opus_ids = [o[opus_id_index] for o in results]

    if not opus_ids:
        return False

    return (page_no, limit, list(results), opus_ids, order)


def get_all_in_collection(request):
    "Return a list of all OPUS IDs in the collection."
    session_id = get_session_id(request)
    res = (Collections.objects.filter(session_id__exact=session_id)
           .values_list('opus_id'))
    opus_ids = [x[0] for x in res]
    return opus_ids

def get_collection_in_page(opus_id_list, session_id):
    """ returns obs_general_ids in page that are also in user collection
        this is for views in results where you have to display the gallery
        and indicate which thumbnails are in cart """
    if not session_id:
        return

    cursor = connection.cursor()
    collection_in_page = []
    sql = 'SELECT DISTINCT opus_id FROM '+connection.ops.quote_name('collections')
    sql += ' WHERE session_id=%s'
    cursor.execute(sql, session_id)
    rows = cursor.fetchall()
    coll_ids = [r[0] for r in rows]
    ret = [opus_id for opus_id in opus_id_list if opus_id in coll_ids]
    return ret
