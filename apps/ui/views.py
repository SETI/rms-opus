###############################################
#
#   UI.views
#
################################################
# computer
import settings
from collections import OrderedDict

# django things
from django.template import RequestContext
from django.shortcuts import render_to_response, get_object_or_404
from django.db.models import get_model
from django.http import HttpResponse
from django.core.exceptions import FieldError

# lib things
from annoying.decorators import render_to

# opus things
from search.models import *
from search.views import *
from search.forms import SearchForm
from metadata.views import *
from paraminfo.models import *
from results.views import *
from django.views.generic import TemplateView
from metrics.views import update_metrics

# guide only
import json
from pprint import pprint

import logging
log = logging.getLogger(__name__)


from django.views.generic import TemplateView

class main_site(TemplateView):
    template_name = "base.html"

    def get_context_data(self, **kwargs):
        context = super(main_site, self).get_context_data(**kwargs)
        menu = getMenuLabels('', 'search')
        context['default_columns'] = settings.DEFAULT_COLUMNS
        context['menu'] = menu['menu']
        return context

def about(request, template = 'about.html'):
    all_volumes = OrderedDict()
    for d in ObsGeneral.objects.values('instrument_id','volume_id').order_by('instrument_id','volume_id').distinct():
        all_volumes.setdefault(d['instrument_id'], []).append(d['volume_id'])

    return render_to_response(template,locals(), context_instance=RequestContext(request))


def get_browse_headers(request,template='browse_headers.html'):
    update_metrics(request)
    return render_to_response(template,locals(), context_instance=RequestContext(request))


def get_table_headers(request,template='table_headers.html'):
    update_metrics(request)
    slugs = request.GET.get('cols', settings.DEFAULT_COLUMNS)
    order = request.GET.get('order', None)
    if order:
        sort_icon = 'fa-sort-desc' if order[0] == '-' else 'fa-sort-asc'
        order = order[1:] if order[0] == '-' else order

    if not slugs: slugs = settings.DEFAULT_COLUMNS
    slugs = slugs.split(',')
    columns = []

    # if this is an ajax call it means it's from our app, so append the
    # checkbox column for adding to selections
    if (request.is_ajax()):
        columns.append(["collection","Collect"])

    param_info  = ParamInfo.objects
    for slug in slugs:
        if slug and slug != 'ring_obs_id':
            try:
                columns.append([slug, param_info.get(slug=slug).label_results])
            except ParamInfo.DoesNotExist:
                pass
    return render_to_response(template,locals(), context_instance=RequestContext(request))


@render_to('menu.html')
def getMenu(request):
    """ hack, need to get menu sometimes without rendering,
        ie from another view.. so this is for column chooser
        couldn't get template include/block.super to heed GET vars """
    update_metrics(request)
    return getMenuLabels(request,'search')

def normalize_single_colun_range_slug(param_info):
    # hack for single column range queries:
    # want the slug to be 'slug1' in menu not just 'slug'
    # param_info is param_info object for a single slug
    if param_info.form_type == 'RANGE' and '1' not in param_info.slug and '2' not in param_info.slug:
        param_info.slug = param_info.slug + '1'
        return param_info.slug
    else:
        return param_info.slug


def getMenuLabels(request, labels_view):
    """
    the categories in the menu on the search form
    category_name is really div_title

    labels_view speaks to whether we fetch the label for 'label' or 'label_results'
    from the param_info model

    todo: change name of  field 'category_name' in param_info table to 'div_title'
    """

    labels_view = 'results' if labels_view == 'results' else 'search'

    if request and request.GET:
        try:
            (selections,extras) = urlToSearchParams(request.GET)
        except TypeError:
            selections = None
    else:
        selections = None

    if not selections:
        triggered_tables = settings.BASE_TABLES
    else:
        triggered_tables = get_triggered_tables(selections, extras)

    divs = TableName.objects.filter(display='Y', table_name__in=triggered_tables)

    if labels_view == 'search':
        params = ParamInfo.objects.filter(display=1, category_name__in=triggered_tables)
    else:
        params = ParamInfo.objects.filter(display_results=1, category_name__in=triggered_tables)

    # build a struct that relates sub_headings to div_titles
    sub_headings = {}
    for p in params:
        sub_headings.setdefault(p.category_name, []).append(p.sub_heading)
    for s in sub_headings:
        sub_headings[s] = list(set(sub_headings[s]))
        if sub_headings[s] == [None]:
            sub_headings[s] = None

    # build a nice data struct for the mu&*!#$@!ing template
    menu_data = {}
    for d in divs:
        menu_data.setdefault(d.table_name, {})

        if d.table_name in sub_headings and sub_headings[d.table_name]:
            # this div is divided into sub headings
            menu_data[d.table_name]['has_sub_heading'] = True

            menu_data[d.table_name].setdefault('data', {})
            for sub_head in sub_headings[d.table_name]:

                if labels_view == 'search':
                    menu_data[d.table_name]['data'][sub_head] = ParamInfo.objects.filter(display=1, category_name = d.table_name, sub_heading = sub_head)
                else:  # lables for results or search view
                    menu_data[d.table_name]['data'][sub_head] = ParamInfo.objects.filter(display_results=1, category_name = d.table_name, sub_heading = sub_head)

                for p in menu_data[d.table_name]['data'][sub_head]:
                    p.slug = normalize_single_colun_range_slug(p)

        else:
            # this div has no sub headings
            menu_data[d.table_name]['has_sub_heading'] = False

            if labels_view == 'search':
                for p in ParamInfo.objects.filter(display=1, category_name=d.table_name):
                    menu_data[d.table_name].setdefault('data', []).append(p)
            else:
                for p in ParamInfo.objects.filter(display_results=1, category_name=d.table_name):

                    menu_data[d.table_name].setdefault('data', []).append(p)

    # div_labels = {d.table_name:d.label for d in TableName.objects.filter(display='Y', table_name__in=triggered_tables)}
    return {'menu': {'data': menu_data, 'divs': divs}}


def getWidget(request, **kwargs):

    """ search form widget as string, http response"""
    update_metrics(request)

    slug = kwargs['slug']
    fmt = kwargs['fmt']
    form = ''

    param_info = get_param_info_by_slug(slug)

    form_type = param_info.form_type
    param_name = param_info.param_name()

    dictionary = param_info.get_dictionary_info()

    form_vals = {slug:None}
    auto_id = True
    selections = {}

    if (request.GET):
        try:
            (selections,extras) = urlToSearchParams(request.GET)
        except TypeError: pass

    addlink = request.GET.get('addlink',True) # suppresses the add_str link
    remove_str = '<a class = "remove_input" href = "">-</a>'
    add_str = '<a class = "add_input" href = "">add</a> '

    if form_type in settings.RANGE_FIELDS:
        auto_id = False

        slug_no_num = stripNumericSuffix(slug)
        param_name_no_num = stripNumericSuffix(param_name)

        slug1 = slug_no_num+'1'
        slug2 = slug_no_num+'2'
        param1 = param_name_no_num+'1'
        param2 = param_name_no_num+'2'

        form_vals = { slug1:None, slug2:None }

        try: len1 = len(selections[param1])
        except: len1 = 0

        try: len2 = len(selections[param2])
        except: len2 = 0

        lngth = len1 if len1 > len2 else len2

        if not lngth: # param is not constrained
            form = str(SearchForm(form_vals, auto_id=auto_id).as_ul());
            if addlink == 'false':
                form = '<ul>' + form + '<li>'+remove_str+'</li></ul>' # remove input is last list item in form
            else:
                form = '<span>'+add_str+'</span><ul>' + form + '</ul>'  # add input link comes before form

        else: # param is constrained
            key=0
            while key<lngth:
                try:
                  form_vals[slug1] = selections[param1][key]
                except IndexError:
                    form_vals[slug1] = None
                try:
                  form_vals[slug2] = selections[param2][key]
                except IndexError:
                    form_vals[slug2] = None

                qtypes = request.GET.get('qtype-' + slug, False)
                if qtypes:
                    try:
                        form_vals['qtype-'+slug] = qtypes.split(',')[key]
                    except KeyError:
                        form_vals['qtype-'+slug] = False
                form = form + str(SearchForm(form_vals, auto_id=auto_id).as_ul())
                if key > 0:
                    form = '<ul>' + form + '<li>'+remove_str+'</li></ul>' # remove input is last list item in form
                else:
                    form = '<span>'+add_str+'</span><ul>' + form + '</ul>'  # add input link comes before form
                if lngth > 1:
                    form = form + '</span><div style = "clear: both;"></div></section><section><span class="widget_form">'
                key = key+1


    elif form_type == 'STRING':
        auto_id = False
        if param_name in selections:
            key = 0
            for value in selections[param_name]:
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
        if param_name in selections:
            form_vals = {slug:selections[param_name]}

        # determine if this mult param has a grouping field (see doc/group_widgets.md for howto on grouping fields)
        mult_param = getMultName(param_name)
        model      = get_model('search',mult_param.title().replace('_',''))

        try:
            grouping = model.objects.distinct().values('grouping')
            grouping_table = 'grouping_' + param_name.split('.')[1]
            grouping_model = get_model('metadata',grouping_table.title().replace('_',''))
            for group_info in grouping_model.objects.order_by('disp_order'):
                gvalue = group_info.value
                glabel = group_info.label if group_info.label else 'Other'
                if glabel == 'NULL': glabel = 'Other'
                if model.objects.filter(grouping=gvalue)[0:1]:
                    form +=  "\n\n" + \
                             '<div class = "mult_group_label_container" id = "mult_group_' + str(glabel) + '">' + \
                             '<span class = "indicator fa fa-plus"></span>' + \
                             '<span class = "mult_group_label">' + str(glabel) + '</span></div>' + \
                             '<ul class = "mult_group">' +  \
                             SearchForm(form_vals, auto_id = '%s_' + str(gvalue), grouping=gvalue).as_ul() + \
                             '</ul>';

        except FieldError:
            # this model does not have grouping
            form = SearchForm(form_vals, auto_id=auto_id).as_ul()

    else:  # all other form types
        if param_name in selections:
            form_vals = {slug:selections[param_name]}
        form = SearchForm(form_vals, auto_id=auto_id).as_ul()

    param_info = get_param_info_by_slug(slug)

    label = param_info.label

    if fmt == 'raw':
        return str(form)
    else:

        template = "widget.html"
        return render_to_response(template,locals(), context_instance=RequestContext(request))
    # return responseFormats(form, fmt)



"""
move this to metadata or results ??
def detailPage(request,ring_obs_id, template='detail.html'):
    ring_obs_id = ('/').join(ring_obs_id.split('-'))
    path = settings.IMAGE_HTTP_PATH
    img_med = path + getImage(ring_obs_id, "med")
    img_full = path + getImage(ring_obs_id, "full")
    data = getDetail(request,ring_obs_id=ring_obs_id)
    return render_to_response(template,locals(), context_instance=RequestContext(request))
"""



def getQuickPage(request,template='demo.html'):
    widgets = {}
    images = Image.objects.all()[0:100]

    for param in ParamInfo.objects.filter(rank=1):
        # widgets[param.label] = str(getWidget(request,param.slug))
        widgets[param.label] = getWidget(request,param=param,slug=param.slug,fmt='raw')
    return render_to_response(template,locals(), context_instance=RequestContext(request))


def init_detail_page(request, **kwargs):
    """
    this loads the initial parts of the detail tab on first loads
    these are the things that are fast to compute while other parts of the page
    are handled with ajax calls because they are slower

    the detail page calls other views via ajax:
    results.get_metadata_by_slugs
    results.get_metadata

    """
    update_metrics(request)

    template="detail.html"
    slugs = request.GET.get('cols',False)
    ring_obs_id = kwargs['ring_obs_id']

    # get the preview image and some general info
    img = get_object_or_404(Image, ring_obs_id=ring_obs_id)
    base_vol_path = get_base_path_previews(ring_obs_id)
    path = settings.IMAGE_HTTP_PATH + base_vol_path
    instrument_id = ObsGeneral.objects.filter(ring_obs_id=ring_obs_id).values('instrument_id')[0]['instrument_id']

    # get the preview guide url
    preview_guide_url = ''
    if instrument_id == 'COCIRS':
        preview_guide_url = 'http://pds-rings.seti.org/cassini/cirs/COCIRS_previews.txt'
    if instrument_id == 'COUVIS':
        preview_guide_url = 'http://pds-rings.seti.org/cassini/uvis/UVIS_previews.txt'
    if instrument_id == 'COVIMS':
        preview_guide_url = 'http://pds-rings.seti.org/cassini/vims/COVIMS_previews.txt'

    # get the list of files for this observation
    files = getFiles(ring_obs_id,fmt='raw')[ring_obs_id]
    file_list = {}
    for product_type in files:
        if product_type not in file_list:
            file_list[product_type] = []
        for f in files[product_type]:
            ext = f.split('.').pop()
            file_list[product_type].append({'ext':ext,'link':f})

    return render_to_response(template,locals(), context_instance=RequestContext(request))

def getColumnInfo(slugs):
    info = {}
    for slug in slugs:
        info[slug] = param_info = get_param_info_by_slug(slug)
    return info


def getColumnChooser(request, **kwargs):
    update_metrics(request)

    slugs = request.GET.get('cols', settings.DEFAULT_COLUMNS).split(',')

    slugs = filter(None, slugs) # sometimes 'cols' is in url but is blank, fails above
    if not slugs:
        slugs = settings.DEFAULT_COLUMNS.split(',')
    info = getColumnInfo(slugs)
    namespace = 'column_chooser_input'
    menu = getMenuLabels(request, 'results')['menu']

    return render_to_response("choose_columns.html",locals(), context_instance=RequestContext(request))





