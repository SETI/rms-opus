###############################################
#
#   UI.views
#
################################################
from search.models import *
from search.views import *
from metadata.views import *
from paraminfo.models import *
from results.views import *
from django.template import RequestContext
from django.shortcuts import render_to_response
from django.http import HttpResponse
from django.core.exceptions import FieldError
import settings

# guide only
import json
from pprint import pprint

import logging
log = logging.getLogger(__name__)


def mainSite(request, template="main.html"):
    # main site needs a few things:
    menu = getMenuLabels()
    defaults = getDefaults() # i don't like this here.
    namespace = 'search'

    return render_to_response(template,locals(), context_instance=RequestContext(request))

def getDefaults():
    # js declares these in the main.html template
    # passed by the categoryLinks method below
    # declared in the template like: {{ defaults.DEFAULT_COLUMNS }}

    return {
        'DEFAULT_COLUMNS': settings.DEFAULT_COLUMNS,
    }

def getDataTable(request,template='table_headers.html'):
    slugs = request.GET.get('cols',settings.DEFAULT_COLUMNS)
    slugs = verifyColumns(slugs.split(','))

    columns = []
    if (request.is_ajax()):
        columns.append(["collection","Collect"])

    for slug in slugs:
        columns.append([slug, ParamInfo.objects.get(slug=slug).label_results])

    return render_to_response(template,locals(), context_instance=RequestContext(request))


def getMenuLabels():
    """
    the categories in the menu on the search form
    """
    groups = Group.objects.filter(display=True)
    cats = Category.objects.filter(display=True).distinct()
    params = ParamInfo.objects.filter(display=True)

    return {'groups':groups, 'cats':cats, 'params':params }


def getWidget(request, **kwargs):

    """ search form widget as string, http response"""
    slug = kwargs['slug']
    fmt = kwargs['fmt']
    form = ''

    form_type = ParamInfo.objects.get(slug=slug.split('_')[0]).form_type
    param_name = ParamInfo.objects.get(slug=slug.split('_')[0]).name

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
                    form = form + '</span><div style="clear: both;"></div></section><section><span class="widget_form">'
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
        log.debug(param_name)
        try:
            grouping = model.objects.distinct().values('grouping')

            log.debug(str(grouping))
            grouping_table = 'grouping_' + mult_param[5:len(mult_param)]
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

    label = ParamInfo.objects.get(slug=slug).label

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

def getResults(request,view='gallery'):

    [page_no,limit,page,page_ids] = getPage(request)

    if view == 'table':
        template = 'table'
        pass
    else:
        template = 'gallery'
        images = getImages(request,size,raw)

    return render_to_response(template,locals(), context_instance=RequestContext(request))



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
    img = Image.objects.get(ring_obs_id=ring_obs_id)
    base_vol_path = Files.objects.filter(ring_obs_id=ring_obs_id)[0].base_path.split('/')[-2:-1][0] + '/' # base_path in the db
    path = settings.IMAGE_HTTP_PATH + base_vol_path

    # get the data for this obs
    data = getDetail(request,ring_obs_id=ring_obs_id,fmt='raw')
    error_log('hi ' + ring_obs_id)

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

    data = {}
    if slugs:
        fields = []
        slugs = slugs.split(',')
        for slug in slugs:
            fields += [ParamInfo.objects.get(slug=slug)]
    else:
        fields = ParamInfo.objects.filter(display_results='Y')

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
    cols = request.GET.get('cols',settings.DEFAULT_COLUMNS)
    cols = verifyColumns(cols.split(','))
    labels = getColumnLabels(cols)
    menu = getMenuLabels()
    namespace = 'column_chooser_input'
    return render_to_response("choose_columns.html",locals(), context_instance=RequestContext(request))





