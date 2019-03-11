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
from django.utils.html import escape
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
        context['default_widgets'] = settings.DEFAULT_WIDGETS
        context['default_sort_order'] = settings.DEFAULT_SORT_ORDER
        context['menu'] = menu['menu']
        if settings.OPUS_FILE_VERSION == '':
            settings.OPUS_FILE_VERSION = get_latest_git_commit_id()
        context['OPUS_FILE_VERSION'] = settings.OPUS_FILE_VERSION
        return context

@never_cache
def api_last_blog_update(request):
    """Return the date of the last blog update.

    This is a PRIVATE API.

    Format: __lastblogupdate.json

    JSON return:
        {'lastupdate': '2019-01-31'}
      or if none available:
        {'lastupdate': None}
    """
    api_code = enter_api_call('api_last_blog_update', request)

    if not request or request.GET is None:
        ret = Http404(settings.HTTP404_NO_REQUEST)
        exit_api_call(api_code, ret)
        raise ret

    lastupdate = None
    try:
        with open(settings.OPUS_LAST_BLOG_UPDATE_FILE, 'r') as fp:
            lastupdate = fp.read().strip()
    except:
        try:
            log.error('api_last_blog_update: Failed to read file "%s"',
                      settings.OPUS_LAST_BLOG_UPDATE_FILE)
        except:
            log.error('api_last_blog_update: Failed to read file UNKNOWN')

    ret = json_response({'lastupdate': lastupdate})

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
    slugs = cols_to_slug_list(slugs)
    columns = []

    columns.append(['collection', 'Selected'])

    template = 'table_headers.html'
    param_info = ParamInfo.objects

    for slug in slugs:
        if slug and slug != 'opus_id':
            pi = get_param_info_by_slug(slug, 'col')
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

    This is a hack to provide the widget names to the metadata selector.

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

    param_info = get_param_info_by_slug(slug, 'widget')
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
        (selections, extras) = url_to_search_params(request.GET,
                                                    allow_errors=True)
        if selections is None: # XXX Really should throw an error of some kind
            selections = {}
            extras = {}

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

        else: # param is constrained
            if form_type_func is None:
                if form_type_format == 'd':
                    func = int
                else:
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
                except (IndexError, KeyError, ValueError, TypeError) as e:
                    form_vals[slug1] = None
                try:
                    form_vals[slug2] = func(selections[param2][key])
                except (IndexError, KeyError, ValueError, TypeError) as e:
                    form_vals[slug2] = None

                qtypes = request.GET.get('qtype-' + slug, False)
                if qtypes:
                    try:
                        form_vals['qtype-'+slug] = qtypes.split(',')[key]
                    except KeyError:
                        form_vals['qtype-'+slug] = False
                form = form + str(SearchForm(form_vals, auto_id=auto_id).as_ul())

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
                key = key+1
        else:
            form = str(SearchForm(form_vals, auto_id=auto_id).as_ul());

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


def api_get_metadata_selector(request):
    """Create the metadata selector list.

    This is a PRIVATE API.

    Format: __forms/metadata_selector.html
    Arguments: None
    """
    api_code = enter_api_call('api_get_metadata_selector', request)

    slugs = request.GET.get('cols', settings.DEFAULT_COLUMNS)
    slugs = cols_to_slug_list(slugs)

    slugs = filter(None, slugs)
    if not slugs:
        slugs = cols_to_slug_list(settings.DEFAULT_COLUMNS)
    all_slugs_info = OrderedDict()
    for slug in slugs:
        all_slugs_info[slug] = get_param_info_by_slug(slug, 'col')
    menu = _get_menu_labels(request, 'results')['menu']

    context = {
        "all_slugs_info": all_slugs_info,
        "menu": menu
    }
    ret = render(request, "select_metadata.html", context)

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
    products = get_pds_products(opus_id)[opus_id]
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
        'instrument_id': instrument_id
    }
    ret = render(request, 'detail.html', context)
    exit_api_call(api_code, ret)
    return ret


@never_cache
def api_normalize_url(request):
    """Given a top-level OPUS URL, normalize it to modern format and return.

    This is a PRIVATE API.

    Format: __normalizeurl.json?<slugs>

    JSON return:
        {'new_url': '...'}
        {'message': None or 'MSG'}
    """
    api_code = enter_api_call('api_normalize_url', request)

    if not request or request.GET is None:
        ret = Http404(settings.HTTP404_NO_REQUEST)
        exit_api_call(api_code, ret)
        raise ret

    old_slugs = dict(list(request.GET.items())) # Make it mutable
    msg_list = []
    new_url_suffix_list = []
    new_url_search_list = []
    old_ui_slug_flag = False

    #
    # Handle search slugs including qtypes
    #

    required_widgets_list = []

    handled_slugs = []
    for slug in old_slugs:
        if slug in settings.SLUGS_NOT_IN_DB:
            continue
        if slug in handled_slugs:
            continue
        if slug.startswith('qtype-'):
            continue
        handled_slugs.append(slug)
        pi = get_param_info_by_slug(slug, 'search')
        if not pi:
            msg = ('Search term "' + escape(slug) + '" is unknown; '
                   +'it has been ignored.')
            msg_list.append(msg)
            continue
        if not pi.display:
            msg = ('Search field "' + pi.body_qualified_label_results()
                   + '" is not searchable; it has been removed.')
            msg_list.append(msg)
            continue
        (form_type, form_type_func,
         form_type_format) = parse_form_type(pi.form_type)

        is_range = form_type in settings.RANGE_FORM_TYPES
        is_string = not is_range and form_type not in settings.MULT_FORM_TYPES

        search1 = None
        search1_val = ''
        search2 = None
        search2_val = ''
        qtype_slug = None
        qtype_val = None
        pi1 = None
        pi2 = None
        if pi.slug[-1] == '1':
            pi1 = pi
            search1 = pi.slug
            search1_val = old_slugs[slug]
            # We found a '1', look for a '2'
            slug2 = slug[:-1]+'2'
            if slug2 in old_slugs:
                handled_slugs.append(slug2)
                pi2 = get_param_info_by_slug(slug2, 'search')
                if not pi2:
                    msg = ('Search term "' + escape(slug2) + '" is '
                           +'unknown; it has been ignored.')
                    msg_list.append(msg)
                else:
                    search2 = pi2.slug
                    search2_val = old_slugs[slug2]
            else:
                search2 = pi.slug[:-1]+'2'
        elif pi.slug[-1] == '2':
            pi2 = pi
            search2 = pi.slug
            search2_val = old_slugs[slug]
            # We found a '2', look for a '1'
            slug1 = slug[:-1]+'1'
            if slug1 in old_slugs:
                handled_slugs.append(slug1)
                pi1 = get_param_info_by_slug(slug1, 'search')
                if not pi1:
                    msg = ('Search term "' + escape(slug1) + '" is '
                           +'unknown; it has been ignored.')
                    msg_list.append(msg)
                else:
                    search1 = pi1.slug
                    search1_val = old_slugs[slug1]
            else:
                search1 = pi.slug[:-1]+'1'
        else:
            # Not numeric
            pi1 = pi
            search1 = pi.slug
            search1_val = old_slugs[slug]
        valid_qtypes = None
        if is_range and not is_single_column_range(pi.param_qualified_name()):
            valid_qtypes = ('any','all','only')
            qtype_default = 'any'
        if is_string:
            valid_qtypes = ('contains', 'begins', 'ends', 'matches', 'excludes')
            qtype_default = 'contains'
        if valid_qtypes:
            # Only look for a qtype field if there's a reason to have one
            old_qtype_slug = 'qtype-' + strip_numeric_suffix(slug)
            if old_qtype_slug in old_slugs:
                handled_slugs.append(old_qtype_slug)
                piq = get_param_info_by_slug(old_qtype_slug, 'qtype')
                if not piq:
                    msg = ('Search field "' + escape(old_qtype_slug) +
                           '" is unknown; it has been ignored.')
                    msg_list.append(msg)
                else:
                    if old_slugs[old_qtype_val] not in valid_qtypes:
                        msg = ('Search field "'
                               + escape(old_slugs[old_qtype_val])
                               + '" is unknown; it has been ignored.')
                        msg_list.append(msg)
                    else:
                        qtype_slug = 'qtype-' + strip_numeric_suffix(piq.slug)
                        qtype_val = old_slugs[old_qtype_slug]
            else:
                # Force a default qtype
                qtype_slug = 'qtype-' + strip_numeric_suffix(pi.slug)
                qtype_val = qtype_default

        # Now normalize all the values
        temp_dict = {}
        if search1:
            temp_dict[search1] = search1_val
        if search2:
            temp_dict[search2] = search2_val
        if qtype_slug:
            temp_dict[qtype_slug] = qtype_val
        (selections, extras) = url_to_search_params(temp_dict,
                                                    allow_errors=True,
                                                    return_slugs=True,
                                                    pretty_results=True)
        if selections is None:
            # Even after all that effort, something still failed miserably
            msg = ('Search query for "'+escape(old_slug)+'" failed for '
                   +'internal reasons - ignoring')
            msg_list.append(msg)
            continue

        if search1_val:
            if not selections[search1]:
                msg = ('Search query for "'
                       + pi1.body_qualified_label_results()
                       + '" minimum had an illegal '
                       'value; it has been ignored.')
                msg_list.append(msg)
                search1 = None
            else:
                search1_val = selections[search1]
        if search2_val:
            if not selections[search2]:
                msg = ('Search query for "'
                       + pi2.body_qualified_label_results()
                       + '" maximum had an illegal '
                       'value; it has been ignored.')
                msg_list.append(msg)
                search2 = None
            else:
                search2_val = selections[search2]

        if search1:
            new_url_search_list.append((search1, search1_val))
        if search2:
            new_url_search_list.append((search2, search2_val))
        if qtype_slug:
            new_url_search_list.append((qtype_slug, qtype_val))

        # Make sure that if we have values to search, that the search widget
        # is also enabled.
        required_widgets_list.append(search1)

    #
    # Deal with all the slugs we know about that AREN'T search terms.
    #

    ### COLS
    cols_list = []
    if 'cols' in old_slugs:
        cols = old_slugs['cols']
    else:
        msg = 'The "cols" field is missing; it has been set to the default.'
        msg_list.append(msg)
        cols = settings.DEFAULT_COLUMNS
    if (cols ==
        'ringobsid,planet,target,phase1,phase2,time1,time2'):
        msg = ('Your URL uses the old defaults for selected metadata; '
               +'they have been replaced with the new defaults.')
        msg_list.append(msg)
        cols = settings.DEFAULT_COLUMNS
    for col in cols.split(','):
        if col == 'ringobsid':
            col = 'opusid'
        pi = get_param_info_by_slug(col, 'col')
        if not pi:
            msg = ('Selected metadata field "' + escape(col)
                   + '" is unknown; it has been removed.')
            msg_list.append(msg)
            continue
        if pi.slug in cols_list:
            msg = ('Selected metadata field "'
                   + pi.body_qualified_label_results()
                   +'" is duplicated in the list of selected metadata; '
                   +'only one copy is being used.')
            msg_list.append(msg)
            continue
        cols_list.append(pi.slug)
        if col != pi.slug:
            old_ui_slug_flag = True
    new_url_suffix_list.append(('cols', ','.join(cols_list)))

    ### WIDGETS
    widgets_list = []
    if 'widgets' in old_slugs:
        widgets = old_slugs['widgets']
    else:
        msg = 'The "widgets" field is missing; it has been set to the default.'
        msg_list.append(msg)
        widgets = settings.DEFAULT_WIDGETS
    if widgets == 'planet,target' and widgets != settings.DEFAULT_WIDGETS:
        msg = ('Your URL uses the old defaults for search fields; '
               +'they have been replaced with the new defaults.')
        msg_list.append(msg)
        widgets = settings.DEFAULT_WIDGETS
    for widget in widgets.split(','):
        pi = get_param_info_by_slug(widget, 'widget')
        if not pi:
            msg = ('Search field "' + escape(widget) + '" is unknown; it '
                   +'has been removed.')
            msg_list.append(msg)
            continue
        if not pi.display:
            msg = ('Search field "' + escape(widget) + '" is not '
                   +'searchable; it has been removed.')
            msg_list.append(msg)
            continue
        widget_name = pi.slug
        if pi.slug[-1] != '1':
            (form_type, form_type_func,
             form_type_format) = parse_form_type(pi.form_type)
            if form_type in settings.RANGE_FORM_TYPES:
                widget_name = pi.slug + '1'
        if widget_name in widgets_list:
            msg = ('Search field "' + pi.body_qualified_label_results()
                   +'" is duplicated in the list of search fields; '
                   +'only one copy is being used.')
            msg_list.append(msg)
            continue
        widgets_list.append(widget_name)
        if widget != pi.slug:
            old_ui_slug_flag = True
    for widget in required_widgets_list:
        if widget not in widgets_list:
            pi = get_param_info_by_slug(widget, 'widget')
            msg = ('Search field "' + pi.body_qualified_label_results()
                   +'" has search parameters but is not listed as a displayed '
                   +'search field; it has been added to the displayed search '
                   +'field list.')
            msg_list.append(msg)
            widgets_list.append(widget)
    new_url_suffix_list.append(('widgets', ','.join(widgets_list)))

    ### ORDER
    order_list = []
    if 'order' in old_slugs:
        orders = old_slugs['order']
    else:
        msg = 'The "order" field is missing; it has been set to the default.'
        msg_list.append(msg)
        orders = settings.DEFAULT_SORT_ORDER
    for order in orders.split(','):
        desc = False
        if order[0] == '-':
            desc = True
            order = order[1:]
        pi = get_param_info_by_slug(order, 'col')
        if not pi:
            msg = ('Sort order metadata field "' + escape(order)
                   +'" is unknown; it has been removed.')
            msg_list.append(msg)
            continue
        if desc:
            order_list.append('-'+pi.slug)
        else:
            order_list.append(pi.slug)
        if order != pi.slug:
            old_ui_slug_flag = True
    if len(order_list) == 0:
        msg = 'The "order" field is empty; it has been set to the default.'
        msg_list.append(msg)
        order_list = settings.DEFAULT_SORT_ORDER.split(',')
    new_url_suffix_list.append(('order', ','.join(order_list)))

    ### VIEW
    view_val = None
    if 'view' in old_slugs:
        if old_slugs['view'] not in ('search', 'gallery', 'data',
                                     'collection', 'cart', 'detail'):
            msg = ('The value for "view" was not one of '
                   +' "search", "gallery", "data", "collection", "cart", or '
                   +'"detail"); it has been set to "gallery".')
            msg_list.append(msg)
            view_val = 'gallery'
        else:
            view_val = old_slugs['browse']
            # if view_val == 'collection':
            #     old_ui_slug_flag = True
            #     view_val = 'cart'
        del old_slugs['view']
    if view_val is None:
        msg = 'The "view" field is missing; it has been set to the default.'
        msg_list.append(msg)
        view_val = 'gallery'
    new_url_suffix_list.append(('view', view_val))

    ### BROWSE
    browse_val = None
    if 'browse' in old_slugs:
        if old_slugs['browse'] not in ('gallery', 'data'):
            msg = ('The value for "browse" was not either "gallery" or "data"; '
                   +'it has been set to "gallery".')
            msg_list.append(msg)
        else:
            browse_val = old_slugs['browse']
        del old_slugs['browse']
    if browse_val is None:
        msg = 'The "browse" field is missing; it has been set to the default.'
        msg_list.append(msg)
        browse_val = 'gallery'
    new_url_suffix_list.append(('browse', browse_val))

    ### PAGE and STARTOBS
    startobs_val = None
    if 'page' in old_slugs:
        old_ui_slug_flag = True
        page_no = 1
        try:
            page_no = int(old_slugs['page'])
        except TypeError:
            msg = ('The value for the "page" term was not a valid '
                   +'integer; it has been set to 1.')
            msg_list.append(msg)
            page_no = 1
        else:
            if page_no < 1 or page_no > 20000:
                page_no = 1
                msg = ('The value for the "page" term was not between '
                       +'1 and 20000; it has been set to 1.')
                msg_list.append(msg)
                page_no = 1
        del old_slugs['page']
        startobs_val = (page_no-1)*100+1
    if 'startobs' in old_slugs:
        try:
            startobs_val = int(old_slugs['startobs'])
        except TypeError:
            msg = ('The value for the "startobs" term was not a valid '
                   +'integer; it has been set to 1.')
            msg_list.append(msg)
            startobs_val = 1
        else:
            if startobs_val < 1 or startobs_val > 10000000:
                msg = ('The value for the "startobs" term was not between '
                       +'1 and 10000000; it has been set to 1.')
                msg_list.append(msg)
                startobs_val = 1
        del old_slugs['startobs']
    if not startobs_val:
        msg = ('The "startobs" or "page" fields are missing; they have been '
               +'set to the default.')
        msg_list.append(msg)
        startobs_val = 1
    new_url_suffix_list.append(('startobs', startobs_val))

    ### COLLS_BROWSE
    colls_browse_val = None
    if 'colls_browse' in old_slugs:
        if old_slugs['colls_browse'] not in ('gallery', 'data'):
            msg = ('The value for "colls_browse" was not either "gallery" or '
                   +'"data"; it has been set to "gallery".')
            msg_list.append(msg)
        else:
            colls_browse_val = old_slugs['colls_browse']
        del old_slugs['colls_browse']
    if colls_browse_val is None:
        colls_browse_val = 'gallery'
    new_url_suffix_list.append(('colls_browse', colls_browse_val))

    ### DETAIL
    detail_val = None
    if 'detail' in old_slugs:
        opus_id = convert_ring_obs_id_to_opus_id(old_slugs['detail'])
        if opus_id != old_slugs['detail']:
            msg = ('You appear to be using an obsolete RINGOBS_ID ('
                   +old_slugs['detail']+') instead of the equivalent new '
                   +' OPUS_ID ('+opus_id+'); it has been converted for you.')
            msg_list.append(msg)
        try:
            obs_general = ObsGeneral.objects.get(opus_id=opus_id)
        except ObjectDoesNotExist:
            msg = ('The OPUS_ID or RINGOBS_ID specified for the "detail" tab '
                   +'was not found in the current database; '
                   +'it has been ignored.')
            msg_list.append(msg)
        else:
            detail_val = opus_id
    if detail_val is None:
        detail_val = ''
    new_url_suffix_list.append(('detail', detail_val))

    #
    # Anything left in the slug list that we would ignore for searching is
    # just something that shouldn't be there anymore.
    #

    for slug_to_ignore in settings.SLUGS_NOT_IN_DB:
        if slug_to_ignore in old_slugs:
            old_ui_slug_flag = True
            del old_slugs[slug_to_ignore]

    # Now let's see if we forgot anything
    handled_slugs = []
    for slug in old_slugs:
        if slug in handled_slugs:
            continue
        if not slug.startswith('qtype-'):
            log.error('api_normalize_url: Failed to handle slug "'+slug+'"')
            continue
        handled_slugs.append(slug)
        # If there's a qtype left behind, then it's either dead, or related to
        # a widget that is active but has no search input.

        old_qtype_slug = slug.split('-')[1]
        pi = get_param_info_by_slug(old_qtype_slug, 'qtype')
        if not pi:
            msg = ('Search query field "' + escape(old_qtype_slug) +
                   '" is unknown; it has been ignored.')
            msg_list.append(msg)
            continue
        qtype_slug = 'qtype-' + pi.slug
        if (qtype_slug not in widgets_list and
            qtype_slug+'1' not in widgets_list):
            # Dead qtype
            msg = ('Search query type "' + pi.body_qualified_label_results()
                   +'" refers to a search field that is not being used; '
                   +'it has been ignored.')
            msg_list.append(msg)
            continue
        valid_qtypes = None
        (form_type, form_type_func,
         form_type_format) = parse_form_type(pi.form_type)
        is_range = form_type in settings.RANGE_FORM_TYPES
        is_string = not is_range and form_type not in settings.MULT_FORM_TYPES
        if is_range and not is_single_column_range(pi.param_qualified_name()):
            valid_qtypes = ('any','all','only')
            qtype_default = 'any'
        if is_string:
            valid_qtypes = ('contains', 'begins', 'ends', 'matches', 'excludes')
            qtype_default = 'contains'
        if valid_qtypes:
            if old_slugs[slug] not in valid_qtypes:
                msg = ('Search field "'
                       + escape(old_slugs[old_qtype_val])
                       + '" has an unknown query type; it has been ignored.')
                msg_list.append(msg)
                continue
            qtype_val = old_slugs[slug]
        else:
            # Force a default qtype
            qtype_val = qtype_default
        new_url_search_list.append((qtype_slug, qtype_val))

    new_url_list = []
    for slug, val in new_url_search_list:
        new_url_list.append(slug + '=' + str(val))
    for slug, val in new_url_suffix_list:
        new_url_list.append(slug + '=' + str(val))

    final_msg = ''
    if old_ui_slug_flag:
        msg = ('<p>Your URL is from a previous version of OPUS. It has been '
               +'adjusted to conform to the current version.</p><br>')
        final_msg = msg + final_msg
    if msg_list:
        final_msg += '<p>We found the following issues with your bookmarked '
        final_msg += 'URL:</p><br><ul>'
        for msg in msg_list:
            final_msg += '<li>'+msg+'</li>'
        final_msg += '</ul><br>'
    if final_msg:
        msg = ('<p>We strongly recommend that you replace your old bookmark '
               +'with the updated URL in your browser so that you will not see '
               +'this message in the future.</p>')
        final_msg += msg

    ret = json_response({'new_url': '&'.join(new_url_list),
                         'msg': final_msg})

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
        (selections, extras) = url_to_search_params(request.GET,
                                                    allow_errors=True)
    else:
        selections = None

    if not selections:
        triggered_tables = settings.BASE_TABLES[:]  # makes a copy of settings.BASE_TABLES
    else:
        triggered_tables = get_triggered_tables(selections, extras) # Needs api_code

    if labels_view == 'results':
        if 'obs_surface_geometry' in triggered_tables:
            triggered_tables.remove('obs_surface_geometry')

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

                menu_data[d.table_name]['data'][sub_head] = all_param_info

        else:
            # this div has no sub headings
            menu_data[d.table_name]['has_sub_heading'] = False
            for p in ParamInfo.objects.filter(**{filter:1, "category_name":d.table_name}):
                menu_data[d.table_name].setdefault('data', []).append(p)

    return {'menu': {'data': menu_data, 'divs': divs}}
