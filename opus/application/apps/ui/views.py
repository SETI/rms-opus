################################################################################
#
# ui/views.py
#
################################################################################

from collections import OrderedDict

import settings

from annoying.decorators import render_to

from django.apps import apps
from django.core.exceptions import FieldError, ObjectDoesNotExist
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView

from dictionary.models import *
from metadata.views import *
from paraminfo.models import *
from results.views import *
from search.forms import SearchForm
from search.models import *
from search.views import *
from tools.app_utils import *
from tools.file_utils import *

import opus_support

import logging
log = logging.getLogger(__name__)

@method_decorator(never_cache, name='dispatch')
class main_site(TemplateView):
    template_name = "base.html"

    def get_context_data(self, **kwargs):
        context = super(main_site, self).get_context_data(**kwargs)
        menu = _get_menu_labels('', 'search')
        context['default_columns'] = settings.DEFAULT_COLUMNS
        context['menu'] = menu['menu']
        if settings.OPUS_FILE_VERSION == '':
            settings.OPUS_FILE_VERSION = get_latest_git_commit_id()
        context['OPUS_FILE_VERSION'] = settings.OPUS_FILE_VERSION
        return context

def api_about(request):
    """Return the about page.

    This is a PRIVATE API, but we don't use the initial __ because it's a
    visible link.

    Format: about.html
    """
    api_code = enter_api_call('api_about', request)
    template = 'about.html'
    all_volumes = OrderedDict()
    for d in (ObsGeneral.objects.values('instrument_id','volume_id')
              .order_by('instrument_id','volume_id').distinct()):
        all_volumes.setdefault(d['instrument_id'], []).append(d['volume_id'])

    ret = render(request, template, {'all_volumes': all_volumes})
    exit_api_call(api_code, ret)
    return ret


def api_get_browse_headers(request):
    """Return the menu bar for the gallery view.

    This is a PRIVATE API.

    Format: __browse_headers.html
    """
    api_code = enter_api_call('api_get_browse_headers', request)
    ret = render(request, 'browse_headers.html')
    exit_api_call(api_code, ret)
    return ret


def api_get_table_headers(request):
    """Return the headers for the table view.

    This is a PRIVATE API.

    Format: __table_headers.html
    Arguments: cols=<columns>
               order=<column>
    """
    api_code = enter_api_call('api_get_table_headers', request)

    slugs = request.GET.get('cols', settings.DEFAULT_COLUMNS)
    order = request.GET.get('order', None)
    if order:
        sort_icon = 'fa-sort-desc' if order[0] == '-' else 'fa-sort-asc'
        order = order.strip('-')
    else:
        sort_icon = ''

    if not slugs:
        slugs = settings.DEFAULT_COLUMNS
    slugs = slugs.split(',')
    columns = []

    # If this is an ajax call it means it's from our app, so append the
    # checkbox column for adding to selections
    if (request.is_ajax()):
        columns.append(['collection', 'Selected'])

    template = 'table_headers.html'
    param_info = ParamInfo.objects

    for slug in slugs:
        if slug and slug != 'opus_id':
            pi = get_param_info_by_slug(slug, from_ui=True)
            if not pi:
                log.error('get_table_headers: Unable to find slug "%s"', slug)
                continue

            # append units if pi_units has unit stored
            unit = pi.get_units()
            label = pi.body_qualified_label_results()
            if unit:
                columns.append([slug, label + ' ' + unit])
            else:
                columns.append([slug, label])

    ret = render(request, template,
                 {'columns':   columns,
                  'sort_icon': sort_icon,
                  'order':     order})

    exit_api_call(api_code, ret)
    return ret


@render_to('menu.html')
def api_get_menu(request):
    """Return the left side menu of the search page.

    This is a PRIVATE API.

    This is a hack to provide the widget names to the column chooser.

    Format: __menu.html
    """
    api_code = enter_api_call('api_get_menu', request)
    ret = _get_menu_labels(request, 'search')
    exit_api_call(api_code, ret)
    return ret


def api_get_widget(request, **kwargs):
    """Create a search widget and return its HTML.

    This is a PRIVATE API.

    Format: __forms/widget/<slug>.html
    Arguments: slug=<slug>
               addlink=true|false XXX???
    """
    api_code = enter_api_call('api_get_widget', request, kwargs)

    slug = kwargs['slug']
    fmt = 'html'
    form = ''

    param_info = get_param_info_by_slug(slug)
    if not param_info:
        log.error(
            'api_get_widget: Could not find param_info entry for slug %s',
            str(slug))
        exit_api_call(api_code, Http404)
        raise Http404

    (form_type, form_type_func,
     form_type_format) = parse_form_type(param_info.form_type)
    param_qualified_name = param_info.param_qualified_name()

    tooltip = param_info.get_tooltip()
    form_vals = {slug: None}
    auto_id = True
    selections = {}

    if request and request.GET:
        (selections, extras) = url_to_search_params(request.GET)

    addlink = request.GET.get('addlink', True) # suppresses the add_str link
    remove_str = '<a class="remove_input" href="">-</a>'
    add_str = '<a class="add_input" href="">add</a> '

    search_form = param_info.category_name

    if form_type in settings.RANGE_FORM_TYPES:
        auto_id = False

        slug_no_num = strip_numeric_suffix(slug)
        param_qualified_name_no_num = strip_numeric_suffix(param_qualified_name)

        slug1 = slug_no_num+'1'
        slug2 = slug_no_num+'2'
        param1 = param_qualified_name_no_num+'1'
        param2 = param_qualified_name_no_num+'2'

        form_vals = {slug1: None, slug2: None}

        # find length of longest list of selections for either param1 or param2,
        # tells us how many times to go through loop below
        try: len1 = len(selections[param1])
        except: len1 = 0
        try: len2 = len(selections[param2])
        except: len2 = 0
        length = len1 if len1 > len2 else len2

        if not length: # param is not constrained
            form = str(SearchForm(form_vals, auto_id=auto_id).as_ul());
            if addlink == 'false':
                # Remove input is last list item in form
                form = '<ul>' + form + '<li>'+remove_str+'</li></ul>'
            else:
                # Add input link comes before form
                form = '<span>'+add_str+'</span><ul>' + form + '</ul>'

        else: # param is constrained
            if form_type_func is None:
                func = float
            else:
                if form_type_func in opus_support.RANGE_FUNCTIONS:
                    func = opus_support.RANGE_FUNCTIONS[form_type_func][0]
                else:
                    log.error('Unknown RANGE function "%s"',
                              form_type_func)
                    func = float
            key = 0
            while key<length:
                try:
                  form_vals[slug1] = func(selections[param1][key])
                except (IndexError, KeyError, ValueError) as e:
                    form_vals[slug1] = None
                try:
                    form_vals[slug2] = func(selections[param2][key])
                except (IndexError, KeyError, ValueError) as e:
                    form_vals[slug2] = None

                qtypes = request.GET.get('qtype-' + slug, False)
                if qtypes:
                    try:
                        form_vals['qtype-'+slug] = qtypes.split(',')[key]
                    except KeyError:
                        form_vals['qtype-'+slug] = False
                form = form + str(SearchForm(form_vals, auto_id=auto_id).as_ul())

                if key > 0:
                    # remove input is last list item in form
                    form = '<ul>' + form + '<li>'+remove_str+'</li></ul>'
                else:
                    # add input link comes before form
                    form = '<span>'+add_str+'</span><ul>' + form + '</ul>'
                if length > 1:
                    form = form + '</span><div style = "clear: both;"></div></section><section><span class="widget_form">'
                key = key+1

    elif form_type == 'STRING':
        auto_id = False
        if param_qualified_name in selections:
            key = 0
            for value in selections[param_qualified_name]:
                form_vals[slug] = value
                qtypes = request.GET.get('qtype-' + slug, False)
                if qtypes:
                    try:
                        form_vals['qtype-'+slug] = qtypes.split(',')[key]
                    except KeyError:
                        form_vals['qtype-'+slug] = False
                form = form + str(SearchForm(form_vals, auto_id=auto_id).as_ul())
                if key > 0:
                    form = form + '<li>'+remove_str+'</li>'
                else:
                    form = form + '<li>'+add_str+'</li>'
                key = key+1
        else:
            form = str(SearchForm(form_vals, auto_id=auto_id).as_ul());
            if addlink == 'false':
                form = form + '<li>'+remove_str+'<li>'
            else:
                form = form + '<li>'+add_str+'<li>'

    # MULT form types
    elif form_type in settings.MULT_FORM_TYPES:
        values = None
        form_vals = {slug: None}
        if param_qualified_name in selections:
            values = selections[param_qualified_name]
        # determine if this mult param has a grouping field (see doc/group_widgets.md for howto on grouping fields)
        mult_param = get_mult_name(param_qualified_name)
        model = apps.get_model('search',mult_param.title().replace('_',''))

        if values is not None:
            # Make form choices case-insensitive
            choices = [mult.label for mult in model.objects.filter(display='Y')]
            new_values = []
            for val in values:
                for choice in choices:
                    if val.upper() == choice.upper():
                        val = choice
                        break
                new_values.append(val)
            form_vals = {slug: new_values}

        try:
            grouping = model.objects.distinct().values('grouping')
            grouping_table = 'grouping_' + param_qualified_name.split('.')[1]
            grouping_model = apps.get_model('metadata',grouping_table.title().replace('_',''))
            for group_info in grouping_model.objects.order_by('disp_order'):
                gvalue = group_info.value
                glabel = group_info.label if group_info.label else 'Other'
                if glabel == 'NULL': glabel = 'Other'
                if model.objects.filter(grouping=gvalue)[0:1]:
                    form +=  "\n\n" + \
                             '<div class = "mult_group_label_container mult_group_' + str(glabel) + '">' + \
                             '<span class = "indicator fa fa-plus"></span>' + \
                             '<span class = "mult_group_label">' + str(glabel) + '</span></div>' + \
                             '<ul class = "mult_group">' +  \
                             SearchForm(form_vals, auto_id = '%s_' + str(gvalue), grouping=gvalue).as_ul() + \
                             '</ul>';

        except FieldError:
            # this model does not have grouping
            form = SearchForm(form_vals, auto_id=auto_id).as_ul()

    else:  # all other form types
        if param_qualified_name in selections:
            form_vals = {slug:selections[param_qualified_name]}
        form = SearchForm(form_vals, auto_id=auto_id).as_ul()

    param_info = get_param_info_by_slug(slug)
    if not param_info:
        log.error(
            "api_get_widget: Could not find param_info entry for slug %s",
            str(slug))
        raise Http404

    label = param_info.body_qualified_label()
    intro = param_info.intro
    units = param_info.get_units()

    template = "widget.html"
    context = {
        "slug": slug,
        "label": label,
        "tooltip": tooltip,
        "intro": intro,
        "form": form,
        "form_type": form_type,
        "range_form_types": settings.RANGE_FORM_TYPES,
        "mult_form_types": settings.MULT_FORM_TYPES,
        "units": units,
    }
    ret = render(request, template, context)

    exit_api_call(api_code, ret)
    return ret


def api_get_column_chooser(request):
    """Create a search widget and return its HTML.

    This is a PRIVATE API.

    Format: __forms/column_chooser.html
    Arguments: cols=<columns>
    """
    api_code = enter_api_call('api_get_column_chooser', request)

    slugs = request.GET.get('cols', settings.DEFAULT_COLUMNS)
    slugs = slugs.split(',')

    slugs = filter(None, slugs)
    if not slugs:
        slugs = settings.DEFAULT_COLUMNS.split(',')
    all_slugs_info = _get_column_info(slugs)
    namespace = 'column_chooser_input'
    menu = _get_menu_labels(request, 'results')['menu']

    context = {
        "all_slugs_info": all_slugs_info,
        "namespace": namespace,
        "menu": menu
    }
    ret = render(request, "choose_columns.html", context)

    exit_api_call(api_code, ret)
    return ret


def api_init_detail_page(request, **kwargs):
    """Render the top part of the Details tab.

    This is a PRIVATE API.

    Format: __initdetail/(?P<opus_id>[-\w]+).html
    Arguments: cols=<columns>

    This returns the initial parts of the detail page. These are the things that
    are fast to compute while other parts of the page are handled with AJAX
    calls because they are slower.

    The detail page calls other views via AJAX:
        results.get_metadata()
    """
    api_code = enter_api_call('api_get_data', request, kwargs)

    slugs = request.GET.get('cols', False)

    opus_id = kwargs['opus_id']
    orig_opus_id = opus_id
    opus_id = convert_ring_obs_id_to_opus_id(opus_id)
    # We have to save the original opus_id in case it's a ring_obs_id, and then
    # pass it to the detail.html template below, because the JS detail.js has
    # no way of knowing that we mapped ring_obs_id -> opus_id and tries to
    # reference HTML tags based on what it thinks of as the right name (the
    # old ring_obs_id). Thus we go ahead and name the appropriate HTML tag using
    # the user-provided name, whatever format it's in.

    try:
        obs_general = ObsGeneral.objects.get(opus_id=opus_id)
    except ObjectDoesNotExist:
        # This OPUS ID isn't even in the database!
        exit_api_call(api_code, None)
        raise Http404
    instrument_id = obs_general.instrument_id

    # The medium image is what's displayed on the Detail page
    # XXX This should be replaced with a viewset query and pixel size
    preview_med_list = get_pds_preview_images(opus_id, None, 'med')
    if len(preview_med_list) != 1:
        log.error('Failed to find single med size image for "%s"', opus_id)
        preview_med_url = ''
    else:
        preview_med_url = preview_med_list[0]['med_url']

    # The full-size image is provided in case the user clicks on the medium one
    preview_full_list = get_pds_preview_images(opus_id, None, 'full')
    if len(preview_full_list) != 1:
        log.error('Failed to find single full size image for "%s"', opus_id)
        preview_full_url = ''
    else:
        preview_full_url = preview_full_list[0]['full_url']

    # Get the preview explanation link for UVIS, VIMS, etc.
    preview_guide_url = ''
    if instrument_id in settings.PREVIEW_GUIDES:
        preview_guide_url = settings.PREVIEW_GUIDES[instrument_id]

    # On the details page, we display the list of available filenames after
    # each product type
    products = get_pds_products(opus_id, None)[opus_id]
    if not products:
        products = {}
    new_products = OrderedDict()
    for version in products:
        new_products[version] = OrderedDict()
        for product_type in products[version]:
            file_list = products[version][product_type]
            product_info = {}
            # Create the URL to look up a particular OPUS_ID in a given
            # metadata summary file in ViewMaster
            if product_type[3].find('Index') != -1:
                tab_url = None
                for fn in file_list:
                    if (fn.endswith('.tab') or
                        fn.endswith('.TAB')):
                        tab_url = fn
                        break
                if tab_url:
                    tab_url = tab_url.replace('holdings', 'viewmaster')
                    tab_url += '/'+opus_id.split('-')[-1]
                product_info['product_link'] = tab_url
            else:
                product_info['product_link'] = None
            file_list = file_list[:]
            for i in range(len(file_list)):
                fn = file_list[i].split('/')[-1]
                file_list[i] = {'filename': fn,
                                'link': file_list[i]}
            product_info['files'] = file_list
            new_products[version][product_type[3]] = product_info

    context = {
        'preview_full_url': preview_full_url,
        'preview_med_url': preview_med_url,
        'preview_guide_url': preview_guide_url,
        'products': new_products,
        'opus_id': opus_id,
        'opus_or_ringobs_id': orig_opus_id,
        'instrument_id': instrument_id
    }
    ret = render(request, 'detail.html', context)
    exit_api_call(api_code, ret)
    return ret


################################################################################
#
# SUPPORT ROUTINES
#
################################################################################

def _get_menu_labels(request, labels_view):
    "Return the categories in the menu for the search form."
    labels_view = 'results' if labels_view == 'results' else 'search'
    if labels_view == 'search':
        filter = "display"
    else:
        filter = "display_results"

    if request and request.GET:
        (selections, extras) = url_to_search_params(request.GET)
    else:
        selections = None

    if not selections:
        triggered_tables = settings.BASE_TABLES[:]  # makes a copy of settings.BASE_TABLES
    else:
        triggered_tables = get_triggered_tables(selections, extras) # Needs api_code

    divs = (TableNames.objects.filter(display='Y',
                                      table_name__in=triggered_tables)
                               .order_by('disp_order'))
    params = (ParamInfo.objects.filter(**{filter:1,
                                          "category_name__in":triggered_tables})
                               .order_by('disp_order'))

    # Build a struct that relates sub_headings to div_titles
    # Note this is a mess because params contains ALL the params for all the
    # sub-menus!
    # We have to be careful to maintain ordering of sub-headings because the
    # original disp_order is the only way we know what the display order of
    # the sub-headings is. Hence the use of OrderedDict.
    sub_headings = OrderedDict()
    for p in params:
        if p.sub_heading is None:
            continue
        sub_headings.setdefault(p.category_name, [])
        if p.sub_heading not in sub_headings[p.category_name]:
            sub_headings[p.category_name].append(p.sub_heading)

    # build a nice data struct for the mu&*!#$@!ing template
    menu_data = {}
    menu_data['labels_view'] = labels_view
    for d in divs:
        menu_data.setdefault(d.table_name, OrderedDict())

        # XXX This really shouldn't be here!!
        menu_data[d.table_name]['menu_help'] = None
        if d.table_name == 'obs_surface_geometry':
            menu_data[d.table_name]['menu_help'] = "Surface geometry, when available, is provided for all bodies in the field of view. Select a target name to reveal more options. Supported instruments: Cassini ISS, UVIS, and VIMS, New Horizons LORRI, and Voyager ISS."

        if d.table_name == 'obs_ring_geometry':
            menu_data[d.table_name]['menu_help'] = "Supported instruments: Cassini ISS, UVIS, and VIMS, New Horizons LORRI, and Voyager ISS."

        if d.table_name == 'obs_instrument_cocirs':
            menu_data[d.table_name]['menu_help'] = "Cassini CIRS data is only available through June 30, 2010"

        if d.table_name in sub_headings and sub_headings[d.table_name]:
            # this div is divided into sub headings
            menu_data[d.table_name]['has_sub_heading'] = True

            menu_data[d.table_name].setdefault('data', OrderedDict())
            for sub_head in sub_headings[d.table_name]:
                all_param_info = ParamInfo.objects.filter(**{filter:1, "category_name":d.table_name, "sub_heading": sub_head})

                # before adding this to data structure, correct a problem with
                # the naming of single column range slugs for menus like this
                all_param_info = list(all_param_info)
                for k,param_info in enumerate(all_param_info):
                    param_info.slug = _adjust_slug_name_single_col_ranges(param_info)
                    all_param_info[k] = param_info

                menu_data[d.table_name]['data'][sub_head] = all_param_info

        else:
            # this div has no sub headings
            menu_data[d.table_name]['has_sub_heading'] = False
            for p in ParamInfo.objects.filter(**{filter:1, "category_name":d.table_name}):
                p.slug = _adjust_slug_name_single_col_ranges(p)
                menu_data[d.table_name].setdefault('data', []).append(p)

    return {'menu': {'data': menu_data, 'divs': divs}}


def _adjust_slug_name_single_col_ranges(param_info):
    slug = param_info.slug
    form_type = param_info.form_type
    if (form_type is not None and form_type.startswith('RANGE') and
        '1' not in slug and '2' not in slug):
        slug = slug + '1'
    return slug

def _get_column_info(slugs):
    info = OrderedDict()
    for slug in slugs:
        info[slug] = get_param_info_by_slug(slug)
    return info
