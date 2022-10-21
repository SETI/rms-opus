################################################################################
#
# ui/views.py
#
# The (private) API interface for returning things for the main UI.
#
#    Format: __notifications.json
#    Format: __menu.json
#    Format: __metadata_selector.json
#    Format: __widget/(?P<slug>[-\w]+).html
#    Format: __initdetail/(?P<opus_id>[-\w]+).html
#    Format: __normalizeurl.json
#    Format: __dummy.json
#    Format: __fake/__viewmetadatamodal/(?P<opus_id>[-\w]+).json
#    Format: __fake/__selectmetadatamodal.json
#
################################################################################

import settings
import os

from django.apps import apps
from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404
from django.shortcuts import render
from django.template.loader import get_template
from django.utils.decorators import method_decorator
from django.utils.html import escape
from django.utils.text import slugify
from django.views.decorators.cache import never_cache
from django.views.generic import TemplateView

from cart.models import Cart
from dictionary.models import Definitions
from dictionary.views import get_def_for_tooltip
from paraminfo.models import ParamInfo
from results.views import get_triggered_tables
from search.forms import SearchForm
from search.models import ObsGeneral, TableNames
from search.views import (get_param_info_by_slug,
                          is_single_column_range,
                          url_to_search_params)
from tools.app_utils import (cols_to_slug_list,
                             convert_ring_obs_id_to_opus_id,
                             enter_api_call,
                             exit_api_call,
                             get_git_version,
                             get_mult_name,
                             get_reqno,
                             get_session_id,
                             json_response,
                             strip_numeric_suffix,
                             throw_random_http404_error,
                             HTTP404_BAD_OR_MISSING_REQNO,
                             HTTP404_NO_REQUEST)
from tools.db_utils import lookup_pretty_value_for_mult
from tools.file_utils import (get_displayed_browse_products,
                              get_pds_preview_images,
                              get_pds_products)

from opus_support import (display_search_unit,
                          display_unit_ever,
                          format_unit_value,
                          get_disp_default_and_avail_units,
                          get_default_unit,
                          get_unit_display_names,
                          get_valid_units,
                          parse_form_type)

import logging
log = logging.getLogger(__name__)

@method_decorator(never_cache, name='dispatch')
class main_site(TemplateView): # pragma: no cover - only accessed from browser
    template_name = "ui/base.html"

    def get_context_data(self, **kwargs):
        context = super(main_site, self).get_context_data(**kwargs)
        menu = _get_menu_labels(None, 'search')
        context['default_columns'] = settings.DEFAULT_COLUMNS
        context['default_widgets'] = settings.DEFAULT_WIDGETS
        context['default_sort_order'] = settings.DEFAULT_SORT_ORDER
        context['max_selections_allowed'] = settings.MAX_SELECTIONS_ALLOWED
        context['preview_guides'] = str(settings.PREVIEW_GUIDES).strip('"')
        context['menu'] = menu['menu']
        if settings.OPUS_FILE_VERSION == '':
            settings.OPUS_FILE_VERSION = get_git_version()
        context['VERSION_SUFFIX'] = '?version='+settings.OPUS_FILE_VERSION
        context['allow_fallback'] = True
        try:
            chat_key = settings.CHAT_KEY
        except:
            chat_key = None
        context['chat_key'] = chat_key
        return context

@never_cache
def api_notifications(request):
    """Return the HTML for any pending notifications and the date of the last
       blog update.

    This is a PRIVATE API.

    Format: __notifications.json

    JSON return:
        {'lastupdate': '2019-01-31',               (or if none available 'None')
         'notification': '<html code>',            (or if none available 'None')
         'notification_mdate': '<file mod str>'    (ie: 1614648616.5189033)
        }
    """
    api_code = enter_api_call('api_notifications', request)
    if not request or request.GET is None or request.META is None:
        ret = Http404(HTTP404_NO_REQUEST('/__notifications.json'))
        exit_api_call(api_code, ret)
        raise ret

    lastupdate = None
    try:
        with open(settings.OPUS_LAST_BLOG_UPDATE_FILE, 'r') as fp: # pragma: no cover -
            # There's no guarantee there will be a blog update file during the
            # unit tests
            lastupdate_val = fp.read().strip()
            if lastupdate_val:
                lastupdate = lastupdate_val
    except FileNotFoundError:
        log.error('api_notifications: Failed to read file "%s"',
                  settings.OPUS_LAST_BLOG_UPDATE_FILE)

    notification = None
    notification_modify = None
    try:
        with open(settings.OPUS_NOTIFICATION_FILE, 'r') as fp: # pragma: no cover -
            # There's no guarantee there will be a notification file during the
            # unit tests
            notification_val = fp.read().strip()
            if notification_val:
                notification = notification_val
            try:
                notification_modify = os.path.getmtime(settings.OPUS_NOTIFICATION_FILE)
            except OSError: # pragma: no cover - filesystem error
                log.error('api_notification: Failed to read the modify date of '
                          'file "%s"', settings.OPUS_NOTIFICATION_FILE)
    except FileNotFoundError:
        log.debug('api_notifications: Failed to read file "%s"',
                  settings.OPUS_NOTIFICATION_FILE)

    ret = json_response({'lastupdate': lastupdate,
                         'notification': notification,
                         'notification_mdate': notification_modify})

    exit_api_call(api_code, ret)
    return ret


def api_get_menu(request):
    """Return the left side menu of the search page.

    This is a PRIVATE API.

    Format: __menu.json
    Arguments: reqno=<reqno>
               Normal search arguments
    """
    api_code = enter_api_call('api_get_menu', request)

    reqno = get_reqno(request)
    if reqno is None or throw_random_http404_error():
        log.error('api_get_menu: Missing or badly formatted reqno')
        ret = Http404(HTTP404_BAD_OR_MISSING_REQNO('/__menu.json'))
        exit_api_call(api_code, ret)
        raise ret

    menu_context = _get_menu_labels(request, 'search')
    menu_context['which'] = 'search' # Used to create DOM IDs
    menu_template = get_template('ui/menu.html')
    html = menu_template.render(menu_context)
    ret = json_response({'html': html, 'reqno': reqno})

    exit_api_call(api_code, ret)
    return ret


@never_cache
def api_get_metadata_selector(request):
    """Create the metadata selector list.

    This is a PRIVATE API.

    Format: __metadata_selector.json
    Arguments: reqno=<reqno>
               Normal search arguments
    """
    api_code = enter_api_call('api_get_metadata_selector', request)

    col_slugs = request.GET.get('cols', settings.DEFAULT_COLUMNS)
    col_slugs = cols_to_slug_list(col_slugs)
    col_slugs = list(filter(None, col_slugs)) # Eliminate empty slugs
    if not col_slugs:
        col_slugs = cols_to_slug_list(settings.DEFAULT_COLUMNS)
    col_slugs_info = {}
    for col_slug in col_slugs:
        # If the desired_unit is None, the default unit will be displayed, else the
        # desired_unit is displayed.
        p, desired_unit = get_param_info_by_slug(col_slug, 'col',
                                                 allow_units_override=True)
        (p.disp_unit, p.default_unit,
         p.units) = get_disp_default_and_avail_units(p.form_type)

        if desired_unit is not None:
            p.disp_unit = p.units[desired_unit]

        if ':' in col_slug:
            col_slug, _, _ = col_slug.partition(':')
        col_slugs_info[col_slug] = p

    search_slugs_info = []
    search_slugs = request.GET.get('widgets', None)
    if search_slugs:
        search_slugs = cols_to_slug_list(search_slugs)
        search_slugs = filter(None, search_slugs) # Eliminate empty slugs
        for search_slug in search_slugs:
            pi = get_param_info_by_slug(search_slug, 'widget')
            if pi.display_results: # pragma: no cover -
                # We don't currently support any search slugs that aren't also
                # displayed
                search_slugs_info.append(pi)

    reqno = get_reqno(request)
    if reqno is None or throw_random_http404_error():
        log.error('api_get_menu: Missing or badly formatted reqno')
        ret = Http404(HTTP404_BAD_OR_MISSING_REQNO('/__metadata_selector.json'))
        exit_api_call(api_code, ret)
        raise ret

    menu_context = _get_menu_labels(request, 'selector', search_slugs_info)

    menu_context['all_slugs_info'] = col_slugs_info
    menu_context['which'] = 'selector'
    menu_template = get_template('ui/select_metadata.html')
    add_field_menu_template = get_template('ui/add_field.html')
    html = menu_template.render(menu_context)
    add_field_html = add_field_menu_template.render(menu_context)
    ret = json_response({'html': html, 'add_field_html': add_field_html, 'reqno': reqno})

    exit_api_call(api_code, ret)
    return ret


@never_cache
def api_get_widget(request, **kwargs):
    """Create a search widget and return its HTML.

    This is a PRIVATE API.

    Format: __widget/<slug>.html
    Arguments: slug=<slug>
               addlink=true|false XXX???
    """

    def _update_form_with_grouping(form, form_vals, glabel, gvalue):
        # Get each level of the directories, create proper mult group label
        # container based on the directory names
        dir_list = glabel.split('/')
        html = ''
        num_of_u_tags = len(dir_list)
        current_hierarchy = ''
        for idx, dir in enumerate(dir_list):
            current_hierarchy = dir if idx == 0 else (current_hierarchy + '_' + dir)
            # Check if the current hierarchy exists
            if current_hierarchy in form: # pragma: no cover - XXX
                # We don't currently have any multi-level categories so this will
                # never execute.
                # Remove </ul> to make sure the next level directory is wrapped
                # within the current existing category
                form = form[:-5]

                # If the current hierarchy exists, and it's at the lowest level,
                # we will render the input form
                if idx == len(dir_list) - 1:
                    html += (SearchForm(form_vals,
                                        auto_id='%s_' + str(dir),
                                        grouping=glabel).as_ul()
                            +'</ul>' * num_of_u_tags)
                    form += html
                    return form
                else:
                    continue

            # If it's a brand new category, we will create a new mult group container
            html += ("\n\n"
                     +'<div class="mult_group_label_container'
                     +' mult_group_' + str(current_hierarchy) + '">'
                     +'<span class="indicator fa fa-plus">'
                     +'</span>'
                     +'<span class="mult_group_label">'
                     +str(dir) + '</span>'
                     +'<span class="hints"></span></div>'
                     +'<ul class="mult_group"'
                     +' data-group=' + str(current_hierarchy) + '>')
            if idx == len(dir_list) - 1: # pragma: no cover - XXX
                # We don't currently have any multi-level categories so this will always
                # execute.
                html += (SearchForm(form_vals,
                                    auto_id='%s_' + str(dir),
                                    grouping=glabel).as_ul()
                        +'</ul>' * num_of_u_tags)
        form += html
        return form

    api_code = enter_api_call('api_get_widget', request, kwargs)

    slug = strip_numeric_suffix(kwargs['slug'])
    form = ''

    param_info = get_param_info_by_slug(slug, 'widget')
    if not param_info:
        log.error(
            'api_get_widget: Could not find param_info entry for slug %s',
            str(slug))
        exit_api_call(api_code, Http404)
        raise Http404

    (form_type, form_type_format,
     form_type_unit_id) = parse_form_type(param_info.form_type)
    param_qualified_name = param_info.param_qualified_name()

    tooltip = param_info.get_tooltip()
    form_vals = {slug: None}
    auto_id = True
    selections = {}
    extras = {}
    customized_input = False
    # Mult options that will be passed to the template for customized mult input
    # HTML.
    options = []
    # Dictionary keyed by group names, and the value will a list mult options
    # corresponding to each group.
    grouped_options = {}
    is_grouped_mult = False

    if request and request.GET is not None: # pragma: no cover - always should be True
        (selections, extras) = url_to_search_params(request.GET,
                                                    allow_errors=True,
                                                    allow_empty=True)
        if selections is None: # pragma: no cover -
            # Would only happen if the front end screws up badly.
            # XXX Really should throw an error of some kind
            selections = {}
            extras = {}

    # Sadly, url_to_search_params optimizes the use of OPUS ID
    # so that it's always searched from obs_general even though it looks
    # to the user like it's in obs_pds. So we have to account for that here
    # or we won't find it in selections.
    if 'obs_general.opus_id' in selections:
        selections['obs_pds.opus_id'] = selections['obs_general.opus_id']
    if 'obs_general.opus_id' in extras['qtypes']:
        extras['qtypes']['obs_pds.opus_id'] = extras['qtypes']['obs_general.opus_id']

    param_qualified_name_no_num = strip_numeric_suffix(param_qualified_name)

    initial_qtype = None
    qtypes = extras['qtypes']
    if param_qualified_name_no_num in qtypes:
        initial_qtype = qtypes[param_qualified_name_no_num][0]

    if form_type in settings.RANGE_FORM_TYPES:
        auto_id = False

        slug_no_num = strip_numeric_suffix(slug)

        slug1 = slug_no_num+'1'
        slug2 = slug_no_num+'2'
        param1 = param_qualified_name_no_num+'1'
        param2 = param_qualified_name_no_num+'2'

        form_vals = {slug1: None, slug2: None}

        # find length of longest list of selections for either param1 or param2,
        # tells us how many times to go through loop below
        try:
            len1 = len(selections[param1])
        except:
            len1 = 0
        try:
            len2 = len(selections[param2])
        except:
            len2 = 0
        length = len1 if len1 > len2 else len2

        if not length: # param is not constrained
            form = ('<ul class="op-search-inputs-set">'
                    +str(SearchForm(form_vals, auto_id=auto_id).as_ul())
                    +'</ul>')

        else: # param is constrained
            initial_unit = None
            units = extras['units']
            initial_unit = units[param_qualified_name_no_num][0]

            key = 0
            while key < length:
                try:
                    form_vals[slug1] = format_unit_value(
                                                selections[param1][key],
                                                form_type_format,
                                                form_type_unit_id,
                                                initial_unit,
                                                convert_from_default=False)
                except (IndexError, KeyError, ValueError, TypeError): # pragma: no cover -
                    # Will only happen if the front end screws up badly
                    form_vals[slug1] = None
                try:
                    form_vals[slug2] = format_unit_value(
                                                selections[param2][key],
                                                form_type_format,
                                                form_type_unit_id,
                                                initial_unit,
                                                convert_from_default=False)
                except (IndexError, KeyError, ValueError, TypeError): # pragma: no cover -
                    # Will only happen if the front end screws up badly
                    form_vals[slug2] = None

                extra_str = ''
                if key != 0:
                    extra_str = 'op-extra-search-inputs'

                form += ('<ul class="op-search-inputs-set '
                         +extra_str + '">'
                         +str(SearchForm(form_vals,
                                         auto_id=auto_id).as_ul())
                         +'</ul>')
                key += 1

    elif form_type == 'STRING':
        auto_id = False
        if param_qualified_name in selections:
            for key_num, value in enumerate(selections[param_qualified_name]):
                form_vals[slug] = value
                extra_str = ''
                if key_num != 0:
                    extra_str = 'op-extra-search-inputs'

                form += ('<ul class="op-search-inputs-set '
                         +extra_str + '">'
                         +str(SearchForm(form_vals,
                                         auto_id=auto_id).as_ul())
                         +'</ul>')
        else:
            form = ('<ul class="op-search-inputs-set">'
                    +str(SearchForm(form_vals, auto_id=auto_id).as_ul())
                    +'</ul>')

    else: # MULT form types
        assert form_type in settings.MULT_FORM_TYPES, form_type
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
                for choice in choices: # pragma: no cover - loop should never complete
                    if val.upper() == choice.upper():
                        val = choice
                        break
                new_values.append(val)
            form_vals = {slug: new_values}

        # For entries with "None" grouping value, we don't group them.
        # None grouping values will be displayed before grouping values
        if list(model.objects.filter(grouping=None)):
            form = SearchForm(form_vals, auto_id=auto_id, grouping=None).as_ul()
            count = 0
            for mult in (model.objects.filter(display='Y')
                                        .order_by('disp_order')):
                tp_id = mult.label
                # If there is any invalid characters for HTML class/id
                # we will replace invalid characters in the mult options
                # with '_'. This will make sure we don't assign invalid
                # characters to HTML class/id for customized tooltips.
                for ch in settings.INVALID_CLASS_CHAR:
                    if ch in tp_id:
                        tp_id = tp_id.replace(ch, '-')
                mult_tooltip = get_def_for_tooltip(mult.value, 'MULT_'+slug.upper())
                if mult_tooltip is not None: # pragma: no cover - XXX
                    # No mults currently have tooltips
                    customized_input = True
                options.append((count, mult.label, mult_tooltip, tp_id))
                count += 1

        # Group the entries with the same grouping values.
        # Different groups will be displayed based on group_disp_order
        grouping_entries = (model.objects
                            .order_by('group_disp_order')
                            .distinct()
                            .values('grouping'))
        for entry in grouping_entries:
            options_of_a_group = []
            glabel = entry['grouping']
            if glabel is not None and glabel != 'NULL':
                if model.objects.filter(grouping=glabel)[0:1]: # pragma: no cover -
                    # There should always be at least one item under the grouping
                    form = _update_form_with_grouping(form, form_vals,
                                                      glabel, glabel)
                    count = 0
                    for mult in (model.objects.filter(grouping=glabel,
                                                      display='Y')
                                                .order_by('disp_order')):
                        tp_id = mult.label
                        for ch in settings.INVALID_CLASS_CHAR:
                            if ch in tp_id:
                                tp_id = tp_id.replace(ch, '-')
                        mult_tooltip = get_def_for_tooltip(mult.value,
                                                           'MULT_'+slug.upper())
                        if mult_tooltip is not None:
                            customized_input = True
                        options_of_a_group.append((count, mult.label,
                                                   mult_tooltip, tp_id))
                        count += 1
                    grouped_options[(glabel,glabel)] = options_of_a_group

    # This is a really horrible hack. They removed the ability to set a default
    # dropdown choice in Django 2.x. See the Django template file
    #   .../django/forms/templates/django/forms/widgets/select.html
    # At this point, "form" contains the entire widget as an HTML <ul>.
    # Somewhere in that string is an element like:
    #   <option value="QQQ">QQQ</option>
    # we need to replace it with:
    #   <option value="QQQ" selected>QQQ</option>
    # where QQQ is the initial_qtype.
    if initial_qtype:
        form = form.replace(f'<option value="{initial_qtype}">',
                            f'<option value="{initial_qtype}" selected>')

    label = param_info.body_qualified_label()
    intro = param_info.intro
    (form_type, form_type_format,
     form_type_unit_id) = parse_form_type(param_info.form_type)
    units = get_unit_display_names(form_type_unit_id)
    valid_units = get_valid_units(form_type_unit_id)
    ranges = param_info.get_ranges_info()

    for cat in ranges:
        default_format = cat['format']
        for item in cat['ranges']:
            val1 = float(item['field1'])
            val2 = float(item['field2'])
            new_unit, new_val1, new_val2 = [], [], []
            for unit in valid_units:
                new_unit.append(unit)
                new_val1.append(format_unit_value(val1, default_format,
                                                  form_type_unit_id, unit))
                new_val2.append(format_unit_value(val2, default_format,
                                                  form_type_unit_id, unit))
            item['valid_units_info'] = zip(new_unit, new_val1, new_val2)

    # Get the current selections for customized widget inputs, need to pass into
    # template and check the selected checkboxes.
    try:
        current_selections = form_vals[slug]
    except KeyError:
        current_selections = []
    # If we don't want to display this group of units on the search tab, then
    # don't pass it to the template
    if not display_search_unit(form_type_unit_id):
        units = None
    template = "ui/widget.html"
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
        "ranges": ranges,
        "customized_input": customized_input,
        "grouped_options": grouped_options,
        "options": options,
        "is_grouped_mult": is_grouped_mult,
        "selections": current_selections,
    }

    ret = render(request, template, context)

    exit_api_call(api_code, ret)
    return ret


@never_cache
def api_init_detail_page(request, **kwargs):
    r"""Render the top part of the Details tab.

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

    opus_id = kwargs['opus_id']

    try:
        obs_general = ObsGeneral.objects.get(opus_id=opus_id)
    except ObjectDoesNotExist:
        # This OPUS ID isn't even in the database!
        exit_api_call(api_code, None)
        raise Http404
    instrument_id = lookup_pretty_value_for_mult(
        get_param_info_by_slug('instrumentid', 'col'),
        obs_general.instrument_id, False)
    filespec = obs_general.primary_filespec
    selection = filespec.split('/')[-1].split('.')[0]

    # See if this opus_id is in the cart
    in_cart = True
    try:
        session_id = get_session_id(request)
        Cart.objects.get(opus_id=opus_id, session_id=session_id, recycled=0)
    except ObjectDoesNotExist:
        in_cart = False

    cart = {}
    if in_cart:
        cart['action'] = 'remove'
        cart['title'] = 'Remove from cart'
        cart['icon_class'] = 'far fa-trash-alt'
    else:
        cart['action'] = 'add'
        cart['title'] = 'Add to cart'
        cart['icon_class'] = 'fas fa-cart-plus'

    # The medium image is what's displayed on the Detail page
    # XXX This should be replaced with a viewset query and pixel size
    preview_med_list = get_pds_preview_images(opus_id, None, 'med')
    if len(preview_med_list) != 1: # pragma: no cover - data error
        log.error('Failed to find single med size image for "%s"', opus_id)
        preview_med_url = ''
    else:
        preview_med_url = preview_med_list[0]['med_url']

    # The full-size image is provided in case the user clicks on the medium one
    preview_full_list = get_pds_preview_images(opus_id, None, 'full')
    if len(preview_full_list) != 1: # pragma: no cover - data error
        log.error('Failed to find single full size image for "%s"', opus_id)
        preview_full_url = ''
    else:
        preview_full_url = preview_full_list[0]['full_url']

    # Get the preview explanation link for UVIS, VIMS, etc.
    preview_guide_url = ''
    if instrument_id in settings.PREVIEW_GUIDES:
        preview_guide_url = settings.PREVIEW_GUIDES[instrument_id]

    # Get all preview/browse products (medium size)
    preview_urls = get_displayed_browse_products(opus_id)

    # On the details page, we display the list of available filenames after
    # each product type
    products = get_pds_products(opus_id)[opus_id]
    if not products: # pragma: no cover - data error
        products = {}
    new_products = {}
    for version in products:
        new_products[version] = {}
        for product_type in products[version]:
            file_list = products[version][product_type]
            product_info = {}
            # Create the URL to look up a particular OPUS_ID in a given
            # metadata summary file in ViewMaster
            if product_type[3].find('Index') != -1:
                tab_url = None
                for fn in file_list: # pragma: no cover -
                    # We always have a tab in our current data
                    if (fn.endswith('.tab') or
                        fn.endswith('.TAB')):
                        tab_url = fn
                        break
                if tab_url: # pragma: no cover -
                    # We always have a tab in our current data
                    tab_url = tab_url.replace('holdings', 'viewmaster')
                    tab_url += '/'+selection
                    tab_url = tab_url.replace(settings.PRODUCT_HTTP_PATH,
                                              settings.VIEWMASTER_ROOT_PATH)
                product_info['product_link'] = tab_url
            else:
                product_info['product_link'] = None
            file_list = file_list[:]
            for i in range(len(file_list)):
                fn = file_list[i].split('/')[-1]
                file_list[i] = {'filename': fn,
                                'link': file_list[i]}
            product_info['files'] = file_list
            try:
                entry = Definitions.objects.get(
                                    context__name='OPUS_PRODUCT_TYPE',
                                    term=product_type[2])
                product_info['tooltip'] = entry.definition
            except Definitions.DoesNotExist: # pragma: no cover - import error
                log.error('No tooltip definition for OPUS_PRODUCT_TYPE "%s"',
                          product_type[2])
                product_info['tooltip'] = None
            new_products[version][product_type[3]] = product_info

    context = {
        'preview_full_url': preview_full_url,
        'preview_med_url': preview_med_url,
        'preview_urls': preview_urls,
        'preview_guide_url': preview_guide_url,
        'products': new_products,
        'opus_id': opus_id,
        'instrument_id': instrument_id,
        'cart': cart
    }
    ret = render(request, 'ui/detail.html', context)
    exit_api_call(api_code, ret)
    return ret


@never_cache
def api_normalize_url(request):
    """Given a top-level OPUS URL, normalize it to modern format and return.

    This is a PRIVATE API.

    Format: __normalizeurl.json?<slugs>

    JSON return:
        {'new_url': '...',
         'new_slugs': [{'slug1': val}, {'slug2': val}],
         'message': None or 'MSG'}
    """
    def _escape_or_label_results(old_slug, pi):
        if pi.display_results:
            return pi.body_qualified_label_results()
        return escape(old_slug)

    def _escape_or_label(old_slug, pi):
        if pi.display_results: # pragma: no cover -
            # We don't currently support any display terms that aren't
            # also search terms
            return pi.body_qualified_label()
        return escape(old_slug) # pragma: no cover

    api_code = enter_api_call('api_normalize_url', request)

    if not request or request.GET is None or request.META is None:
        ret = Http404(HTTP404_NO_REQUEST('/__normalizeurl.json'))
        exit_api_call(api_code, ret)
        raise ret

    original_slugs = dict(list(request.GET.items())) # Make it mutable

    # When we are given a URL, this is the user just selecting something like
    # opus.pds-rings.seti.org/opus
    # We don't want to give error messages in that case, but instead use all
    # the defaults.
    url_was_empty = len(original_slugs) == 0

    msg_list = []
    new_url_suffix_list = []
    new_url_search_list = []
    old_ui_slug_flag = False

    #
    # Handle search slugs including qtypes and units
    #

    required_widgets_list = []

    handled_slugs = []
    search_slugs_by_clause = {}
    units_by_slug = {} # To enforce a single unit for all clauses of a slug

    # Sort to make tests deterministic and to group qtype and unit
    # with search slugs
    def _sort_func(key):
        clause_num_str = ''
        if '_' in key:
            clause_num_str = key[key.index('_'):]
            key = key[:key.index('_')]
        if key.startswith('qtype-'):
            key = key[6:]+'0' # Add 0 to sort before 1/2 suffixes
        elif key.startswith('unit-'):
            key = key[5:]+'0'
        key += clause_num_str
        return key

    for slug in sorted(original_slugs, key=_sort_func):
        if slug in settings.SLUGS_NOT_IN_DB:
            continue
        if slug in handled_slugs:
            continue
        handled_slugs.append(slug)

        # Strip off any clause number and save for later
        clause_num_str = ''
        orig_slug = slug
        if '_' in slug:
            clause_num_str = slug[slug.rindex('_'):]
            try:
                clause_num = int(clause_num_str[1:])
                if clause_num > 0:
                    slug = slug[:slug.rindex('_')]
                else:
                    raise ValueError
            except ValueError:
                # If clause_num is not a positive integer, leave the slug as is.
                # If the slug is unknown, it will be caught later as an unknown
                # slug.
                clause_num_str = ''

        is_qtype = False
        is_unit = False
        if slug.startswith('qtype-'):
            is_qtype = True
            slug = slug[6:]
            # This will return the '1' version
            pi = get_param_info_by_slug(slug, 'qtype')
        elif slug.startswith('unit-'):
            is_unit = True
            slug = slug[5:]
            # This will return the '1' version
            pi = get_param_info_by_slug(slug, 'qtype')
        else:
            pi = get_param_info_by_slug(slug, 'search')

        # Note 'slug' could be old or new version, but pi.slug is always new
        if not pi:
            msg = ('Search term "' + escape(orig_slug) + '" is unknown; '
                   +'it has been ignored.')
            msg_list.append(msg)
            continue
        # Search slugs might have numeric suffixes but single column ranges
        # don't so just ignore all the numbers.
        if (not is_qtype and not is_unit and
            strip_numeric_suffix(slug) != strip_numeric_suffix(pi.slug)):
            old_ui_slug_flag = True
        pi_searchable = pi
        if pi.slug[-1] == '2':
            # We have to look at the '1' version to see if it's searchable
            pi_searchable = get_param_info_by_slug(
                                    strip_numeric_suffix(pi.slug)+'1', 'search')
            if not pi_searchable: # pragma: no cover - we don't have non-searchable slugs
                log.error('api_normalize_url: Found slug "%s" but not "%s"',
                          pi.slug, strip_numeric_suffix(pi.slug)+'1')
                continue
        handled_slugs.append(pi.slug+clause_num_str)
        if pi.old_slug:
            handled_slugs.append(pi.old_slug+clause_num_str)
        if not pi_searchable.display and slug != 'ringobsid':
            # Special exception for ringobsid - we don't have it marked
            # searchable in param_info, but we want to allow it here
            msg = ('Search field "' + _escape_or_label_results(orig_slug, pi)
                   +'" is not searchable; it has been removed.')
            msg_list.append(msg)
            continue
        (form_type, form_type_format,
         form_type_unit_id) = parse_form_type(pi_searchable.form_type)

        is_range = form_type in settings.RANGE_FORM_TYPES
        is_mult = form_type in settings.MULT_FORM_TYPES
        is_string = not is_range and not is_mult

        if is_mult and clause_num_str:
            msg = ('Search field "' + _escape_or_label_results(orig_slug, pi)
                   +'" has a clause number but none is permitted; '
                   +'it has been removed.')
            msg_list.append(msg)
            continue

        search1 = None
        search1_val = None
        search2 = None
        search2_val = None
        qtype_slug = None
        qtype_val = None
        unit_slug = None
        unit_val = None
        pi1 = None
        pi2 = None
        if ((is_qtype or is_unit) and is_range) or slug[-1] == '1':
            # We found a '1', look for a '2' OR we found a qtype or unit,
            # so look for a '2' even if the '1' isn't there.
            # Do some trickery to allow an old1/new2 or old2/new1 combination
            # If a user was being really obnoxious they could mix old1/new1
            # as well, so handle that case too by throwing away one of them.
            # This is so unusual we don't bother to make a message for it.
            pi1 = pi
            if not is_qtype and not is_unit: # We found a real '1' slug
                search1 = strip_numeric_suffix(pi.slug)+'1'
                search1_val = original_slugs[slug+clause_num_str]
            slug2 = strip_numeric_suffix(pi.slug)+'2'
            if slug2+clause_num_str not in original_slugs and pi.old_slug:
                slug2 = strip_numeric_suffix(pi.old_slug)+'2'
            if slug2+clause_num_str in original_slugs:
                if pi.old_slug:
                    handled_slugs.append(
                        strip_numeric_suffix(pi.old_slug)+'2'+clause_num_str)
                handled_slugs.append(
                        strip_numeric_suffix(pi.slug)+'2'+clause_num_str)
                pi2 = get_param_info_by_slug(slug2, 'search')
                if not pi2: # pragma: no cover - import error
                    log.error('api_normalize_url: Search term "%s" was found '
                              +' but "%s" was not',
                              escape(slug), escape(slug2))
                else:
                    # Don't bother checking .display and .display_results
                    # here because this slug is governed by the '1' version.
                    search2 = strip_numeric_suffix(pi2.slug)+'2'
                    search2_val = original_slugs[slug2+clause_num_str]
            else:
                search2 = strip_numeric_suffix(pi.slug)+'2'
        if ((is_qtype or is_unit) and is_range) or slug[-1] == '2':
            # We found a '2', look for a '1' OR we found a qtype or unit,
            # so look for a '1' even if the '2' isn't there.
            # Do some trickery to allow an old1/new2 or old2/new1 combination
            # If a user was being really obnoxious they could mix old1/new1
            # as well, so handle that case too by throwing away one of them.
            # This is so unusual we don't bother to make a message for it.
            pi2 = pi
            if not is_qtype and not is_unit:
                search2 = strip_numeric_suffix(pi.slug)+'2'
                search2_val = original_slugs[slug+clause_num_str]
            slug1 = strip_numeric_suffix(pi.slug)+'1'
            if slug1+clause_num_str not in original_slugs and pi.old_slug:
                slug1 = strip_numeric_suffix(pi.old_slug)+'1'
            if slug1+clause_num_str in original_slugs:
                if pi.old_slug: # pragma: no cover -
                    # This always has to be true if we got this far. We can
                    # only be in this section if we had a '2' slug
                    # alphabetically earlier than a '1' slug, which means they
                    # must be a combination of old/new. But if they are a
                    # combination, then by definition there's an old_slug!
                    handled_slugs.append(
                        strip_numeric_suffix(pi.old_slug)+'1'+clause_num_str)
                handled_slugs.append(
                        strip_numeric_suffix(pi.slug)+'1'+clause_num_str)
                pi1 = get_param_info_by_slug(slug1, 'search')
                if not pi1: # pragma: no cover - import error
                    log.error('api_normalize_url: Search term "%s" was found '
                              +' but "%s" was not',
                              escape(slug), escape(slug1))
                else:
                    search1 = strip_numeric_suffix(pi1.slug)+'1'
                    search1_val = original_slugs[slug1+clause_num_str]
            else:
                search1 = strip_numeric_suffix(pi.slug)+'1'
        if (((is_qtype or is_unit) and not is_range) or
            (not is_qtype and not is_unit and
             slug[-1] != '1' and slug[-1] != '2')):
            # Not numeric
            pi1 = pi
            search1 = pi.slug
            if slug+clause_num_str in original_slugs:
                search1_val = original_slugs[slug+clause_num_str]
                # If we're searching for ringobsid, convert it to opusid and
                # also convert the parameter to the new opusid format
                if pi.slug == 'ringobsid':
                    search1 = 'opusid'
                    new_search1_val = convert_ring_obs_id_to_opus_id(
                                                search1_val,
                                                force_ring_obs_id_fmt=True)
                    if not new_search1_val:
                        msg = ('RING OBS ID "' + escape(search1_val)
                               +'" not found; the ringobsid search term has been '
                               +'removed.')
                        msg_list.append(msg)
                        continue
                    search1_val = new_search1_val

        ### Handle qtypes ###

        valid_qtypes = None
        qtype_default = None
        if is_range and not is_single_column_range(pi.param_qualified_name()):
            valid_qtypes = settings.RANGE_QTYPES
            qtype_default = valid_qtypes[0]
        if is_string:
            valid_qtypes = settings.STRING_QTYPES
            qtype_default = valid_qtypes[0]

        # Look for an associated qtype.
        # Same trick as above in case there is qtype-old and qtype-new.
        # Note if we were already looking at the qtype, this will just
        # find it again.
        qtype_slug = 'qtype-' + strip_numeric_suffix(pi.slug)
        old_qtype_slug = qtype_slug
        found_qtype = False
        if qtype_slug+clause_num_str in original_slugs:
            found_qtype = qtype_slug+clause_num_str
        elif pi.old_slug:
            old_qtype_slug = 'qtype-' + strip_numeric_suffix(pi.old_slug)
        if old_qtype_slug+clause_num_str in original_slugs:
            found_qtype = old_qtype_slug+clause_num_str
            if pi.old_slug:
                handled_slugs.append('qtype-'
                                     +strip_numeric_suffix(pi.old_slug)
                                     +clause_num_str)
            handled_slugs.append('qtype-'
                                 +strip_numeric_suffix(pi.slug)
                                 +clause_num_str)
            qtype_val = original_slugs[old_qtype_slug+clause_num_str]
            if valid_qtypes and qtype_val not in valid_qtypes:
                msg = ('Query type "'+escape(orig_slug)
                       +'" has an illegal value; '
                       +'it has been set to the default.')
                msg_list.append(msg)
                qtype_val = qtype_default
        elif qtype_default:
            # Force a default qtype
            qtype_val = qtype_default

        if not valid_qtypes:
            qtype_slug = None

        if found_qtype and not valid_qtypes:
            # We have a qtype for a field that doesn't allow qtypes!
            msg = ('Search term "'+escape(found_qtype)+'" is a query type for '
                   +'a field that does not allow query types; '
                   +'it has been ignored.')
            msg_list.append(msg)

        if qtype_slug == 'qtype-ringobsid':
            qtype_slug = 'qtype-opusid'

        ### Handle units ###

        (form_type, form_type_format,
         form_type_unit_id) = parse_form_type(pi.form_type)
        valid_units = get_valid_units(form_type_unit_id)
        # For our purpose, a unit_id that is never shown to the user (not
        # during search and not during results) is not actually a valid unit
        # and should never have a unit-X slug. This happens for things like
        # SCLK fields which just use the units infrastructure to convert
        # database fields to fancy strings.
        if not display_unit_ever(form_type_unit_id):
            valid_units = None
        unit_default = get_default_unit(form_type_unit_id)

        # It really only makes sense to look for a unit field if there's a
        # reason one would be present, but if the user gave us one anyway,
        # we need to handle it so we can then ignore it and give an error.
        # Same trick as above in case there is unit-old and unit-new.
        # Note if we were already looking at the unit, this will just
        # find it again.
        unit_slug = 'unit-' + strip_numeric_suffix(pi.slug)
        old_unit_slug = unit_slug
        found_unit = False
        if unit_slug+clause_num_str in original_slugs:
            found_unit = unit_slug+clause_num_str
        elif pi.old_slug:
            old_unit_slug = 'unit-' + strip_numeric_suffix(pi.old_slug)
        if old_unit_slug+clause_num_str in original_slugs:
            found_unit = old_unit_slug+clause_num_str
            if pi.old_slug:
                handled_slugs.append('unit-'
                                     +strip_numeric_suffix(pi.old_slug)
                                     +clause_num_str)
            handled_slugs.append('unit-'
                                 +strip_numeric_suffix(pi.slug)
                                 +clause_num_str)
            unit_val = original_slugs[old_unit_slug+clause_num_str]
            # Silently replace old units with new versions
            unit_val = unit_val.replace('/', '_')
            if unit_val == 'hourangle': # pragma: no cover -
                # backwards compatibility that we don't really care about
                unit_val = 'hours'
            if valid_units and unit_val not in valid_units:
                msg = ('Unit "'+escape(found_unit)
                       +'" has an illegal value; '
                       +'it has been set to the default.')
                msg_list.append(msg)
                unit_val = unit_default
        elif unit_default:
            # Force a default unit
            unit_val = unit_default

        if not valid_units:
            unit_slug = None

        if found_unit and not valid_units:
            # We have a unit for a field that doesn't allow units!
            msg = ('Search term "'+escape(found_unit)+'" is a unit for '
                   +'a field that does not allow units; '
                   +'it has been ignored.')
            msg_list.append(msg)

        if unit_slug in units_by_slug:
            if unit_val != units_by_slug[unit_slug]:
                if found_unit:
                    msg = ('Search term "'+escape(found_unit)+'" is a unit that'
                           +' is inconsistent with the units for previous'
                           +' instances of this search field; it has been'
                           +' ignored.')
                else:
                    msg = ('No unit specified for "'+escape(orig_slug)
                           +'" but units were specified for other instances '
                           +'of this search field; the previous units have '
                           +'been used.')
                msg_list.append(msg)
                unit_val = units_by_slug[unit_slug]
        elif unit_slug:
            units_by_slug[unit_slug] = unit_val

        # Now normalize all the values
        # Note that search1/2_val are strings
        temp_dict = {}
        if search1 and search1_val is not None:
            temp_dict[search1] = search1_val
        if search2 and search2_val is not None:
            temp_dict[search2] = search2_val
        if qtype_slug and qtype_val is not None:
            temp_dict[qtype_slug] = qtype_val
        if unit_slug and unit_val is not None:
            temp_dict[unit_slug] = unit_val
        (selections, extras) = url_to_search_params(temp_dict,
                                                    allow_errors=True,
                                                    return_slugs=True,
                                                    pretty_results=True)
        if selections is None: # pragma: no cover - can't happen
            # Even after all that effort, something still failed miserably
            msg = ('Search query for "'+escape(slug)+'" failed for '
                   +'internal reasons - ignoring')
            msg_list.append(msg)
            continue

        if search1_val is not None:
            if selections[search1] is None:
                if is_range:
                    msg = ('Search query for "'
                           +_escape_or_label(search1, pi1)
                           +'" minimum had an illegal value; '
                           +'it has been ignored.')
                else:
                    msg = ('Search query for "'
                           +_escape_or_label_results(search1, pi1)
                           +'" had an illegal value; it has been ignored.')
                msg_list.append(msg)
                search1 = None
            else:
                search1_val = selections[search1]
        if search2_val is not None:
            if selections[search2] is None:
                msg = ('Search query for "'
                       +_escape_or_label(search2, pi2)
                       +'" maximum had an illegal value; it has been ignored.')
                msg_list.append(msg)
                search2 = None
            else:
                search2_val = selections[search2]
                if isinstance(search2_val, (list, tuple)): # pragma: no cover -
                    # This should never happen, because lists are only returned
                    # for strings, and strings never have a '2' slug
                    search2_val = search2_val[0]

        # Store the search/qtype slugs and values for later use so we can
        # add them to the URL in numerical clause order once we know what
        # all the clause numbers actually are.
        slug_no_num = strip_numeric_suffix(pi.slug)
        if slug_no_num not in search_slugs_by_clause:
            search_slugs_by_clause[slug_no_num] = []
        search_slugs_by_clause[slug_no_num].append((clause_num_str,
                                                    search1, search1_val,
                                                    search2, search2_val,
                                                    qtype_slug, qtype_val,
                                                    unit_slug, unit_val))

        # Make sure that if we have values to search, that the search widget
        # is also enabled.
        if pi.slug == 'ringobsid':
            # Note we already convert the ringobsid search parameter above
            required_widgets_list.append('opusid')
        else:
            required_widgets_list.append(strip_numeric_suffix(pi.slug))

    # Sort all the clauses for each slug key in numerical order
    # If there are duplicate numbers, do it in syntactic order
    for search_slug, search_list in search_slugs_by_clause.items():
        search_list.sort(key=lambda x: (0 if x[0] == '' else int(x[0][1:]),
                                        x))

    for search_slug in sorted(search_slugs_by_clause.keys(),
                              key=str.lower):
        for idx, search_data in enumerate(search_slugs_by_clause[search_slug]):
            (clause_str,
             search1, search1_val,
             search2, search2_val,
             qtype, qtype_val,
             unit, unit_val) = search_data
            clause_num_str = ''
            if len(search_slugs_by_clause[search_slug]) != 1:
                clause_num_str = '_%02d' % (idx+1)
            if search1 and search1_val is not None:
                new_url_search_list.append([search1+clause_num_str,
                                            search1_val])
            if search2 and search2_val is not None:
                new_url_search_list.append([search2+clause_num_str,
                                            search2_val])
            if qtype: # Always include the qtype
                new_url_search_list.append([qtype+clause_num_str,
                                            qtype_val])
            if unit: # Always include the unit
                new_url_search_list.append([unit+clause_num_str,
                                            unit_val])

    #
    # Deal with all the slugs we know about that AREN'T search terms.
    #

    ### COLS
    cols_list = []
    if 'cols' in original_slugs:
        cols = original_slugs['cols']
    else:
        # msg = 'The "cols" field is missing; it has been set to the default.'
        # msg_list.append(msg)
        cols = settings.DEFAULT_COLUMNS
    if (cols ==
        'ringobsid,planet,target,phase1,phase2,time1,time2'):
        msg = ('Your URL uses the old defaults for selected metadata; '
               +'they have been replaced with the new defaults.')
        msg_list.append(msg)
        cols = settings.DEFAULT_COLUMNS
    if cols == '':
        msg = ('Your selected metadata list is empty; '
               +'it has been replaced with the defaults.')
        msg_list.append(msg)
        cols = settings.DEFAULT_COLUMNS
    for col in cols.split(','):
        if col == '':
            continue
        if col == 'ringobsid':
            col = 'opusid'
        pi, desired_units = get_param_info_by_slug(col, 'col', allow_units_override=True,
                                                   check_valid_units=False)
        # It used to be OK for single-column ranges to have a '1' at the end
        if not pi and col[-1] == '1':
            pi, desired_units = get_param_info_by_slug(strip_numeric_suffix(col), 'col',
                                                       allow_units_override=True,
                                                       check_valid_units=False)
        if not pi:
            msg = ('Selected metadata field "' + escape(col)
                   +'" is unknown; it has been removed.')
            msg_list.append(msg)
            continue
        if not pi.display_results:
            msg = ('Selected metadata field "' + escape(col)
                   +'" is not displayable; it has been removed.')
            msg_list.append(msg)
            continue
        if pi.slug in cols_list:
            msg = ('Selected metadata field "'
                   +pi.body_qualified_label_results()
                   +'" is duplicated in the list of selected metadata; '
                   +'only one copy is being used.')
            msg_list.append(msg)
            continue
        if desired_units is not None and not pi.is_valid_unit(desired_units):
            msg = ('Selected metadata field "'
                   +pi.body_qualified_label_results()
                   +'" has invalid units "' + escape(desired_units)
                   +'"; units have been removed.')
            msg_list.append(msg)
            desired_units = None
        if col.partition(':')[0] != pi.slug:
            old_ui_slug_flag = True
        cols_list.append(f'{pi.slug}:{desired_units}' if desired_units else pi.slug)
    if len(cols_list) == 0:
        msg = ('Your new selected metadata list is empty; '
               +'it has been replaced with the defaults.')
        msg_list.append(msg)
        new_cols = settings.DEFAULT_COLUMNS
    else:
        new_cols = ','.join(cols_list)
    new_url_suffix_list.append(('cols', new_cols))

    ### WIDGETS
    widgets_list = []
    if 'widgets' in original_slugs:
        widgets = original_slugs['widgets']
    else:
        widgets = ''
    if (widgets == 'planet,target' and
        widgets != settings.DEFAULT_WIDGETS): # pragma: no cover -
        # At least for now, these are the same, so this can't happen
        msg = ('Your URL uses the old defaults for search fields; '
               +'they have been replaced with the new defaults.')
        msg_list.append(msg)
        widgets = settings.DEFAULT_WIDGETS
    for widget in widgets.split(','):
        if widget == '':
            continue
        if widget == 'ringobsid':
            widget = 'opusid'
        pi = get_param_info_by_slug(widget, 'widget')
        if not pi and widget[-1] == '1':
            pi = get_param_info_by_slug(strip_numeric_suffix(widget), 'widget')
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
        widget_name = strip_numeric_suffix(pi.slug)
        if widget_name in widgets_list:
            msg = ('Search field "' + pi.body_qualified_label_results()
                   +'" is duplicated in the list of search fields; '
                   +'only one copy is being used.')
            msg_list.append(msg)
            continue
        widgets_list.append(widget_name)
        # Widget names never have numeric suffixes even for two-column ranges
        if widget != strip_numeric_suffix(pi.slug):
            old_ui_slug_flag = True
    for widget in required_widgets_list:
        if widget not in widgets_list:
            pi = get_param_info_by_slug(widget, 'widget')
            # msg = ('Search field "' + pi.body_qualified_label_results()
            #        +'" has search parameters but is not listed as a displayed '
            #        +'search field; it has been added to the displayed search '
            #        +'field list.')
            # msg_list.append(msg)
            widgets_list.append(widget)
    if 'widgets' not in original_slugs and len(widgets_list) == 0:
        new_url_suffix_list.append(('widgets', settings.DEFAULT_WIDGETS))
    else:
        new_url_suffix_list.append(('widgets', ','.join(widgets_list)))

    ### ORDER
    order_list = []
    order_slug_list = []
    if 'order' in original_slugs:
        orders = original_slugs['order']
    else:
        # msg = 'The "order" field is missing; it has been set to the default.'
        # msg_list.append(msg)
        orders = settings.DEFAULT_SORT_ORDER
    if orders == 'time1' and orders != settings.DEFAULT_SORT_ORDER:
        # msg = ('Your URL uses the old defaults for sort order; '
        #        +'they have been replaced with the new defaults.')
        # msg_list.append(msg)
        orders = settings.DEFAULT_SORT_ORDER

    order_split = orders.split(',')
    for order_num, order in enumerate(order_split):
        if order == '':
            continue
        if order == 'ringobsid':
            order = 'opusid'
        desc = False
        if order[0] == '-':
            desc = True
            order = order[1:]
        # Sort order slugs should never include units
        pi = get_param_info_by_slug(order, 'col', allow_units_override=False)
        # It used to be OK for single-column ranges to have a '1' at the end
        if not pi and order[-1] == '1':
            pi = get_param_info_by_slug(strip_numeric_suffix(order), 'widget')
        if not pi:
            msg = ('Sort order metadata field "' + escape(order)
                   +'" is unknown; it has been removed.')
            msg_list.append(msg)
            continue
        if pi.slug in order_slug_list:
            msg = ('Sort order metadata field "'
                   +pi.body_qualified_label_results()
                   +'" is duplicated in the list of sort orders; '
                   +'only one copy is being used.')
            msg_list.append(msg)
            continue
        if not pi.display_results:
            msg = ('Sort order metadata field "' + escape(order)
                   +'" is not displayable; it has been removed.')
            msg_list.append(msg)
            continue
        order_slug_list.append(pi.slug)
        if desc:
            order_list.append('-'+pi.slug)
        else:
            order_list.append(pi.slug)
        if order != pi.slug:
            old_ui_slug_flag = True
        if pi.slug == 'opusid':
            if order_num != len(order_split)-1:
                msg = 'Fields after "opusid" in the sort order have been removed.'
                msg_list.append(msg)
            break
    if len(order_list) == 0:
        msg = 'The "order" field is empty; it has been set to the default.'
        msg_list.append(msg)
        order_str = settings.DEFAULT_SORT_ORDER
    else:
        if 'opusid' not in order_list and '-opusid' not in order_list:
            order_list.append('opusid')
        order_str = ','.join(order_list)
    new_url_suffix_list.append(('order', order_str))

    ### VIEW
    view_val = None
    if 'view' in original_slugs:
        if original_slugs['view'] not in ('search', 'browse',
                                     'collection', 'cart', 'detail'):
            msg = ('The value for "view" was not one of '
                   +'"search", "browse", "collection", "cart", or '
                   +'"detail"; it has been set to "search".')
            msg_list.append(msg)
            view_val = 'search'
        else:
            view_val = original_slugs['view']
            if view_val == 'collection':
                old_ui_slug_flag = True
                view_val = 'cart'
        del original_slugs['view']
    if view_val is None:
        # msg = 'The "view" field is missing; it has been set to the default.'
        # msg_list.append(msg)
        view_val = 'search'
    new_url_suffix_list.append(('view', view_val))

    ### BROWSE and CART_BROWSE
    # Note: there used to be a colls_browse, but since we never supported the
    # table in the cart anyway, we're just going to ignore colls_browse as
    # a possibility here.
    for prefix in ('', 'cart_'):
        browse_val = None
        if prefix+'browse' in original_slugs:
            if original_slugs[prefix+'browse'] not in ('gallery', 'data'):
                msg = (f'The value for "{prefix}browse" was not either '
                       +'"gallery" or "data"; it has been set to "gallery".')
                msg_list.append(msg)
                browse_val = 'gallery'
            else:
                browse_val = original_slugs[prefix+'browse']
            del original_slugs[prefix+'browse']
        if browse_val is None:
            # msg = 'The "browse" field is missing; it has been set to the default.'
            # msg_list.append(msg)
            browse_val = 'gallery'
        new_url_suffix_list.append((prefix+'browse', browse_val))

    ### PAGE and STARTOBS (and CART_PAGE and CART_STARTOBS)
    for prefix in ('', 'cart_'):
        startobs_val = None
        if prefix+'page' in original_slugs:
            old_ui_slug_flag = True
            page_no = 1
            try:
                page_no = int(original_slugs[prefix+'page'])
            except ValueError:
                msg = (f'The value for the "{prefix}page" term was not a valid '
                       +'integer; it has been set to 1.')
                msg_list.append(msg)
                page_no = 1
            else:
                if page_no < 1 or page_no > 20000:
                    page_no = 1
                    msg = (f'The value for the "{prefix}page" term was not '
                           +'between 1 and 20000; it has been set to 1.')
                    msg_list.append(msg)
                    page_no = 1
            del original_slugs[prefix+'page']
            startobs_val = (page_no-1)*100+1
        if prefix+'startobs' in original_slugs:
            try:
                startobs_val = int(original_slugs[prefix+'startobs'])
            except ValueError:
                msg = (f'The value for the "{prefix}startobs" term was not a '
                       +'valid integer; it has been set to 1.')
                msg_list.append(msg)
                startobs_val = 1
            else:
                if startobs_val < 1 or startobs_val > 10000000:
                    msg = (f'The value for the "{prefix}startobs" term was not '
                           +'between 1 and 10000000; it has been set to 1.')
                    msg_list.append(msg)
                    startobs_val = 1
            del original_slugs[prefix+'startobs']
        if not startobs_val:
            # msg = (f'The "{prefix}startobs" or "{prefix}page" fields are '
            #        +f'missing; {prefix}startobs has been set to 1.')
            # msg_list.append(msg)
            startobs_val = 1
        new_url_suffix_list.append((prefix+'startobs', startobs_val))

    ### DETAIL
    detail_val = None
    if 'detail' in original_slugs and original_slugs['detail']:
        opus_id = convert_ring_obs_id_to_opus_id(original_slugs['detail'])
        if not opus_id:
            msg = ('You appear to be using an obsolete RINGOBS_ID ('
                   +escape(original_slugs['detail'])
                   +'), but it could not be converted '
                   +'to a new OPUS_ID. It has been ignored.')
            msg_list.append(msg)
        else:
            if opus_id != original_slugs['detail']:
                msg = ('You appear to be using an obsolete RINGOBS_ID ('
                       +escape(original_slugs['detail'])
                       +') instead of the equivalent new '
                       +'OPUS_ID ('+opus_id+'); it has been converted for you.')
                msg_list.append(msg)
            try:
                _ = ObsGeneral.objects.get(opus_id=opus_id)
            except ObjectDoesNotExist:
                msg = ('The OPUS_ID specified for the "detail" tab '
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
        if slug_to_ignore in original_slugs:
            del original_slugs[slug_to_ignore]

    # Now let's see if we forgot anything
    for slug in original_slugs:
        if slug in handled_slugs: # pragma: no cover - bug if False
            continue
        log.error('api_normalize_url: Failed to handle slug "'+
                  slug+'"') # pragma: no cover

    new_url_list = []
    new_url_dict_list = []
    for slug, val in new_url_search_list:
        new_url_list.append(slug + '=' + str(val))
        new_url_dict_list.append({slug: val})
    for slug, val in new_url_suffix_list:
        new_url_list.append(slug + '=' + str(val))
        new_url_dict_list.append({slug: val})

    final_msg = ''
    if old_ui_slug_flag:
        msg = ('<p>Your bookmarked URL is from a previous version of OPUS. '
               +'It has been adjusted to conform to the current version.</p>')
        final_msg = msg + final_msg
    if msg_list:
        final_msg += '<p>We found the following issues with your bookmarked '
        final_msg += 'URL:</p><ul>'
        for msg in msg_list:
            final_msg += '<li>'+msg+'</li>'
        final_msg += '</ul>'
    if final_msg:
        msg = ('<p>We strongly recommend that you replace your old bookmark '
               +'with the updated URL in your browser so that you will not see '
               +'this message in the future.</p>')
        final_msg += msg

    if url_was_empty or final_msg == '':
        final_msg = None

    ret = json_response({'new_url': '&'.join(new_url_list),
                         'new_slugs': new_url_dict_list,
                         'msg': final_msg})

    exit_api_call(api_code, ret)
    return ret


@never_cache
def api_dummy(request, *args, **kwargs):
    """This API does nothing and is used for network performance testing.

    This is a PRIVATE API.

    Format: __dummy.json

    JSON return:
        {}
    """
    api_code = enter_api_call('api_dummy', request)

    ret = json_response({})

    exit_api_call(api_code, ret)
    return ret


################################################################################
#
# SUPPORT ROUTINES
#
################################################################################

def _get_menu_labels(request, labels_view, search_slugs_info=None):
    "Return the categories in the search tab or metadata selector."
    labels_view = 'selector' if labels_view == 'selector' else 'search'
    if labels_view == 'search':
        filter_ = "display"
    else:
        filter_ = "display_results"

    if search_slugs_info:
        expanded_cats = ['search_fields']
    else:
        expanded_cats = ['obs_general']
    if request and request.GET: # pragma: no cover - will always be True
        (selections, extras) = url_to_search_params(request.GET,
                                                    allow_errors=True)
        # Remember which categories the user had previous expanded so that when we
        # regenerate the category list we can expand them again.
        get_expanded_cats = request.GET.get('expanded_cats')
        if get_expanded_cats == '':
            expanded_cats = []
        elif get_expanded_cats is not None:
            expanded_cats = get_expanded_cats.split(',')
    else: # pragma: no cover - see above
        selections = None

    if not selections:
        # Makes a copy of settings.BASE_TABLES
        triggered_tables = settings.BASE_TABLES[:]
    else:
        # XXX Needs api_code to report errors
        triggered_tables = get_triggered_tables(selections, extras)

    divs = (TableNames.objects.filter(display='Y',
                                      table_name__in=triggered_tables)
                               .order_by('disp_order'))
    params = (ParamInfo.objects.filter(**{filter_:1,
                                          "category_name__in":triggered_tables})
                               .order_by('disp_order'))

    # Build a struct that relates sub_headings to div_titles
    # Note this is a mess because params contains ALL the params for all the
    # sub-menus!
    # We have to be careful to maintain ordering of sub-headings because the
    # original disp_order is the only way we know what the display order of
    # the sub-headings is.
    sub_headings = {}
    for p in params:
        if p.sub_heading is None:
            continue
        sub_headings.setdefault(p.category_name, [])
        if p.sub_heading not in sub_headings[p.category_name]:
            sub_headings[p.category_name].append(p.sub_heading)

    menu_data = {}
    menu_data['labels_view'] = labels_view

    obs_surface_geometry_name_div = None
    for d in divs:
        if d.table_name == 'obs_surface_geometry_name':
            obs_surface_geometry_name_div = d

    for d in divs:
        table_name = d.table_name
        # We have to treat obs_surface_geometry_name and
        # obs_surface_geometry_name specially. They are two separate tables but
        # we want their fields to show up under the heading for
        # obs_surface_geometry.
        if d.table_name == 'obs_surface_geometry_name':
            table_name = 'obs_surface_geometry'
        if table_name in expanded_cats:
            d.collapsed = ''
            d.show = 'show'
        else:
            d.collapsed = 'collapsed'
            d.show = ''
        menu_data.setdefault(table_name, {})

        if labels_view == 'search':
            # Don't want these to show up in the metadata selector
            # XXX This really shouldn't be here!!
            menu_data[table_name]['menu_help'] = None
            if table_name == 'obs_surface_geometry':
                menu_data[table_name]['menu_help'] = "Surface geometry, when available, is provided for all bodies in the field of view. Use Surface Geometry Target Selector to reveal more options. Supported instruments: Cassini ISS, UVIS, and VIMS, New Horizons LORRI, and Voyager ISS."

            if table_name == 'obs_ring_geometry':
                menu_data[table_name]['menu_help'] = "Supported instruments: Cassini ISS, UVIS, and VIMS, New Horizons LORRI, and Voyager ISS."

            if table_name == 'obs_instrument_cocirs':
                menu_data[table_name]['menu_help'] = "Cassini CIRS data is only available through June 30, 2010"

        if d.table_name in sub_headings and sub_headings[d.table_name]:
            # this div is divided into sub headings
            menu_data[table_name]['has_sub_heading'] = True

            menu_data[table_name].setdefault('data', {})
            for sub_head in sub_headings[d.table_name]:
                if table_name+'-'+slugify(sub_head) in expanded_cats:
                    sub_head_tuple = (sub_head, '', 'show')
                else:
                    sub_head_tuple = (sub_head, 'collapsed', '')

                all_param_info = (ParamInfo.objects
                                  .filter(**{filter_:1,
                                             'category_name': d.table_name,
                                             'sub_heading': sub_head}))
                for p in all_param_info:
                    # If referred_slug exists, we will look up the param info
                    # based on the referred_slug.
                    if p.referred_slug is not None: # pragma: no cover -
                        # We don't have any referred slugs in sub-headings in the current
                        # design.
                        # A referred slug will never contain a unit specifier
                        p = get_param_info_by_slug(p.referred_slug, 'col',
                                                   allow_units_override=False)
                        p.label = p.body_qualified_label()
                        p.label_results = p.body_qualified_label_results(True)

                    if labels_view == 'search':
                        if p.slug[-1] == '2':
                            # We can just skip these because we never use them
                            # for search widgets
                            continue
                        if p.slug[-1] == '1': # pragma: no cover -
                            # We don't currently have any single-column ranges under
                            # subheadings so we will always get here.
                            # Strip the trailing 1 off all ranges
                            p.slug = strip_numeric_suffix(p.slug)
                    (p.disp_unit, p.default_unit,
                     p.units) = get_disp_default_and_avail_units(p.form_type)
                    menu_data[table_name]['data'].setdefault(sub_head_tuple,
                                                               []).append(p)
        else:
            # this div has no sub headings
            menu_data[table_name]['has_sub_heading'] = False
            for p in ParamInfo.objects.filter(**{filter_:1,
                                                'category_name': d.table_name}):

                # If referred_slug exists, we will put that referred_slug
                # under the current category.
                if p.referred_slug is not None:
                    referred_slug = p.referred_slug
                    # A referred slug will never contain a unit specifier
                    p = get_param_info_by_slug(referred_slug, 'col',
                                               allow_units_override=False)
                    p.label = p.body_qualified_label()
                    p.label_results = p.body_qualified_label_results(True)
                    # assign referred_slug used to determine if an icon should
                    # be appended at the end of a menu item.
                    p.referred_slug = referred_slug

                # On the search tab, we don't need the trailing 1 & 2 for
                # data-slug; in the Select Metadata modal we do.
                if labels_view == 'search':
                    if p.slug[-1] == '2': # pragma: no cover -
                        # These should already be marked as non-display and thus
                        # were filtered out by the filter_ function above.
                        continue
                    if p.slug[-1] == '1':
                        # Strip the trailing 1 off all ranges
                        p.slug = strip_numeric_suffix(p.slug)
                (p.disp_unit, p.default_unit,
                 p.units) = get_disp_default_and_avail_units(p.form_type)
                menu_data[table_name].setdefault('data', []).append(p)

    # If there are any search slugs, put those in first
    if labels_view == 'selector' and search_slugs_info:
        # Thanks to the way templates work, we can fake up a TableNames object
        # by using a standard dictionary.
        search_div = {'table_name': 'search_fields',
                      'label': 'Current Search Fields'}
        if 'search_fields' in expanded_cats:
            search_div['collapsed'] = ''
            search_div['show'] = 'show'
        else:
            search_div['collapsed'] = 'collapsed'
            search_div['show'] = ''
        divs = [search_div] + list(divs)
        menu_data.setdefault('search_fields', {})
        menu_data['search_fields']['has_sub_heading'] = False
        for p in search_slugs_info:
            (p.disp_unit, p.default_unit,
             p.units) = get_disp_default_and_avail_units(p.form_type)
            menu_data['search_fields'].setdefault('data', []).append(p)
            if p.slug[-1] == '1':
                # This is a numeric range field, so we want to add both
                # the min and max slugs to the list.
                # This is generated by a search field, not a metadata column, so there
                # will never be a units modifier here.
                p2 = get_param_info_by_slug(p.slug[:-1]+'2', 'col',
                                            allow_units_override=False)
                (p2.disp_unit, p2.default_unit,
                 p2.units) = get_disp_default_and_avail_units(p2.form_type)
                menu_data['search_fields'].setdefault('data', []).append(p2)

    new_div_list = []
    first_category = True
    for div in divs:
        if div == obs_surface_geometry_name_div:
            # Since we combined them above, we don't want to allow
            # obs_surface_geometry_name to continue to the UI
            continue
        new_div_list.append(div)
        if type(div) == dict:
            div['first_category'] = first_category
        else:
            div.first_category = first_category
        first_category = False

    return {'menu': {'data': menu_data, 'divs': new_div_list}}
