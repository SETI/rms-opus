###############################################
#
#   UI.views
#
################################################
# computer
import settings

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
        menu = getMenuLabels('')
        context['default_columns'] = settings.DEFAULT_COLUMNS
        context['menu'] = menu['menu']
        return context

def get_browse_headers(request,template='browse_headers.html'):
    return render_to_response(template,locals(), context_instance=RequestContext(request))




def get_table_headers(request,template='table_headers.html'):
    slugs = request.GET.get('cols', settings.DEFAULT_COLUMNS)
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

    """ such a hack, need to get menu sometimes without rendering,
        ie from another view.. so this is for column chooser
        couldn't get template include/block.super to heed GET vars """
    return getMenuLabels(request)

def getMenuLabels(request):
    """
    the categories in the menu on the search form
    category_name is really div_title
    todo: change name of  field 'category_name' in param_info table to 'div_title'
    """

    if request and request.GET:
        (selections,extras) = urlToSearchParams(request.GET)
    else:
        selections = None

    if not selections:
        triggered_tables = settings.BASE_TABLES
    else:
        triggered_tables = get_triggered_tables(selections, extras)

    params = ParamInfo.objects.filter(display='Y', category_name__in=triggered_tables)
    divs = TableName.objects.filter(display='Y', table_name__in=triggered_tables)

    # build a struct that relates sub_headings to div_titles
    sub_headings = {}
    for p in params:
        sub_headings.setdefault(p.category_name, []).append(p.sub_heading)
    for s in sub_headings:
        sub_headings[s] = list(set(sub_headings[s]))
        if sub_headings[s] == [None]:
            sub_headings[s] = None

    # build a nice data struct form the mu&*!#$@!ing template
    menu_data = {}
    for d in divs:
        menu_data.setdefault(d.table_name, {})

        if d.table_name in sub_headings and sub_headings[d.table_name]:
            # this div is divided into sub headings
            menu_data[d.table_name]['has_sub_heading'] = True
            # menu_data[d.table_name]['data'] = {'hello':[5,4,3,2,1],'goodbye':[1,2,3,4,5]} # todo
            menu_data[d.table_name].setdefault('data', {})
            for sub_head in sub_headings[d.table_name]:
                menu_data[d.table_name]['data'][sub_head] = ParamInfo.objects.filter(display='Y', category_name = d.table_name, sub_heading = sub_head)

        else:
            # this div has not sub headings
            menu_data[d.table_name]['has_sub_heading'] = False
            for p in ParamInfo.objects.filter(display='Y', category_name=d.table_name):
                menu_data[d.table_name].setdefault('data', []).append(p)

    # div_labels = {d.table_name:d.label for d in TableName.objects.filter(display='Y', table_name__in=triggered_tables)}

    return {'menu': {'data': menu_data, 'divs': divs}}


def getWidget(request, **kwargs):



    """ search form widget as string, http response"""
    slug = kwargs['slug']
    fmt = kwargs['fmt']
    form = ''

    param_info  = ParamInfo.objects.get(slug=slug)

    form_type = param_info.form_type
    param_name = param_info.param_name()

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
                             '<span class = "mult_group_label"><span class = "closed_triangle">&nbsp;</span>' + \
                             str(glabel) + '</span>' + \
                             '<ul class = "mult_group" id = "mult_group_' + str(glabel) + '">' +  \
                             SearchForm(form_vals, auto_id = '%s_' + str(gvalue), grouping=gvalue).as_ul() + \
                             '</ul>';

        except FieldError:
            # this model does not have grouping
            form = SearchForm(form_vals, auto_id=auto_id).as_ul()

    else:  # all other form types
        if param_name in selections:
            form_vals = {slug:selections[param_name]}
        form = SearchForm(form_vals, auto_id=auto_id).as_ul()

    param_info  = ParamInfo.objects.get(slug=slug)
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


def getDetailPage(request, **kwargs):
    template="detail.html"
    slugs = request.GET.get('cols',False)
    ring_obs_id = kwargs['ring_obs_id']

    img = get_object_or_404(Image, ring_obs_id=ring_obs_id)
    base_vol_path = Files.objects.filter(ring_obs_id=ring_obs_id)[0].base_path.split('/')[-2:-1][0] + '/' # base_path in the db
    path = settings.IMAGE_HTTP_PATH + base_vol_path
    # get the data for this obs
    data = getDetail(request,ring_obs_id=ring_obs_id,fmt='raw')



    #files = getFiles(ring_obs_id=ring_obs_id,fmt='raw')['data'][ring_obs_id]
    files = getFiles(ring_obs_id,fmt='raw')[ring_obs_id]
    file_list = {}
    for product_type in files:
        if product_type not in file_list:
            file_list[product_type] = []
        for f in files[product_type]:
            ext = f.split('.').pop()
            file_list[product_type].append({'ext':ext,'link':f})

    return render_to_response(template,locals(), context_instance=RequestContext(request))

# I can't explain, other than it's named badly
def getDetailQuick(request, **kwargs):
    template="detail_quick.html"
    slugs = request.GET.get('cols',False)
    ring_obs_id = kwargs['ring_obs_id']

    param_info  = ParamInfo.objects

    data = {}
    if slugs:
        fields = []
        slugs = slugs.split(',')
        for slug in slugs:
            fields += [param_info.get(slug=slug)]
    else:
        fields = param_info.objects.filter(display_results='Y')

    for field in fields:
        try:
            data[str(field.name)] = str(Observations.objects.filter(ring_obs_id=ring_obs_id).values(str(field.name))[0][field.name])
        except:pass
    return render_to_response(template,locals(), context_instance=RequestContext(request))


def getColumnLabels(slugs):
    labels = {}
    for slug in slugs:
        labels[slug] = ParamInfo.objects.get(slug=slug).label_results
    return labels


def getColumnChooser(request, **kwargs):
    slugs = request.GET.get('cols', settings.DEFAULT_COLUMNS).split(',')
    slugs = filter(None, slugs) # sometimes 'cols' is in url but is blank, fails above
    if not slugs:
        slugs = settings.DEFAULT_COLUMNS.split(',')
    labels = getColumnLabels(slugs)
    namespace = 'column_chooser_input'
    menu = getMenuLabels(request)['menu']
    return render_to_response("choose_columns.html",locals(), context_instance=RequestContext(request))





