################################################################################
#
# help/views.py
#
# The API interface for retrieving help documents:
#
#    Format: __help/about.(?P<fmt>html|pdf)
#    Format: __help/bundles.(?P<fmt>html|pdf)
#    Format: __help/faq.(?P<fmt>html|pdf)
#    Format: __help/gettingstarted.(?P<fmt>html|pdf)
#    Format: __help/splash.html
#    Format: apiguide.(?P<fmt>pdf)
#    Format: __help/apiguide.(?P<fmt>html|pdf)
#    Format: __help/citing.(?P<fmt>html|pdf)
#
################################################################################

import base64
import datetime
import logging
import os
import platform
import re
from io import BytesIO

import mistune
import pdfkit
import qrcode
import yaml
from django.conf import settings
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import render
from django.template.loader import get_template
from django.views.decorators.cache import never_cache

from opus_app.apps.metadata.views import get_fields_info
from opus_app.apps.search.models import MultObsGeneralInstrumentId, ObsGeneral
from opus_app.apps.tools.app_utils import (
    api_view,
    get_git_version,
    http404_no_request,
)

log = logging.getLogger(__name__)


################################################################################
#
# API INTERFACES
#
################################################################################

@never_cache
@api_view
def api_about(request, fmt):
    """Renders the about page.

    This is a PRIVATE API.

    Format: __help/about.(?P<fmt>html|pdf)
    """
    if not request or request.GET is None or request.META is None:
        raise Http404(http404_no_request(f'/__help/about.{fmt}'))

    git_id = get_git_version()
    database_schema = settings.DB_SCHEMA_NAME
    database_host = settings.DB_HOST_NAME
    hostname = platform.node()
    context = {
        'git_id': git_id,
        'database_schema': database_schema,
        'database_host': database_host,
        'hostname': hostname
    }

    return _render_html_or_pdf(request, 'help/about.html', fmt, 'about',
                               'About OPUS', context)


@never_cache
@api_view
def api_bundles(request, fmt):
    """Renders the bundles page.

    This is a PRIVATE API.

    Format: __help/bundles.(?P<fmt>html|pdf)
    """
    if not request or request.GET is None or request.META is None:
        raise Http404(http404_no_request(f'/__help/bundles.{fmt}'))

    all_bundles = {}
    for d in (ObsGeneral.objects.values('instrument_id','bundle_id')
              .order_by('instrument_id','bundle_id').distinct()):
        instrument_name = (MultObsGeneralInstrumentId.objects.values('label')
                           .filter(id=d['instrument_id']))
        all_bundles.setdefault(instrument_name[0]['label'],
                               []).append(d['bundle_id'])
    for k,_v in all_bundles.items():
        all_bundles[k] = ', '.join(all_bundles[k])

    context = {'all_bundles': all_bundles}
    return _render_html_or_pdf(
                    request, 'help/bundles.html', fmt, 'bundles',
                    'Bundles/Volumes Available for Searching with OPUS', context)


@never_cache
@api_view
def api_faq(request, fmt):
    """Renders the faq page.

    This is a PRIVATE API.

    Format: __help/faq.(?P<fmt>html|pdf)
    """
    if not request or request.GET is None or request.META is None:
        raise Http404(http404_no_request(f'/__help/faq.{fmt}'))

    path = os.path.dirname(os.path.abspath(__file__))
    faq_content_file = 'faq.yaml'
    with open(os.path.join(path, faq_content_file)) as stream:
        text = stream.read()
        try:
            # FullLoader (not the unsafe default) over apps/help/faq.yaml, which
            # ships inside this package. No request data reaches this parser.
            faq = yaml.load(text, Loader=yaml.FullLoader)  # nosec B506
        except yaml.YAMLError as exc: # pragma: no cover -
            # This can only happen if there is a problem with the YAML in the
            # FAQ.YAML file
            log.exception('api_faq: Unable to parse %s', faq_content_file)
            raise Http404 from exc

    context = {'faq': faq,
               'allow_collapse': fmt == 'html'}
    return _render_html_or_pdf(
                    request, 'help/faq.html', fmt, 'faq',
                    'Frequently Asked Questions (FAQ) About OPUS', context)


@never_cache
@api_view
def api_gettingstarted(request, fmt):
    """Renders the getting started page.

    This is a PRIVATE API.

    Format: __help/gettingstarted.(?P<fmt>html|pdf)
    """
    if not request or request.GET is None or request.META is None:
        raise Http404(http404_no_request(f'/__help/gettingstarted.{fmt}'))

    return _render_html_or_pdf(request, 'help/gettingstarted.html', fmt,
                               'getting_started',
                               'Getting Started with OPUS')


@never_cache
@api_view
def api_splash(request):
    """Renders the splash page.

    This is a PRIVATE API.

    Format: __help/splash.html
    """
    if not request or request.GET is None or request.META is None:
        raise Http404(http404_no_request('/__help/splash.html'))

    return render(request, 'help/splash.html')


@never_cache
@api_view
def api_citing_opus(request, fmt):
    """Renders the citing opus page.

    This is a PRIVATE API.

    Format: __help/citing.(?P<fmt>html|pdf)
    """
    if not request or request.GET is None or request.META is None:
        raise Http404(http404_no_request(f'/__help/citing.{fmt}'))

    opus_search_url = request.GET.get('searchurl', None)
    opus_state_url = request.GET.get('stateurl', None)

    def url_to_png_string(url):
        qr = qrcode.QRCode(box_size=5, border=4)
        qr.add_data(url)
        qr.make(fit=True)
        url_qr = qr.make_image(fill_color='black', back_color='white')
        buffered = BytesIO()
        url_qr.save(buffered, format='PNG')
        url_qr_string = base64.b64encode(buffered.getvalue()).decode('ascii', 'strict')
        return url_qr_string

    basic_opus_qr_str = url_to_png_string(settings.PUBLIC_OPUS_URL)

    opus_search_qr_str = None
    if opus_search_url is not None:
        opus_search_qr_str = url_to_png_string(opus_search_url)

    opus_state_qr_str = None
    if opus_state_url is not None:
        opus_state_qr_str = url_to_png_string(opus_state_url)

    context = {'basic_opus_url': settings.PUBLIC_OPUS_URL,
               'basic_opus_qr': basic_opus_qr_str,
               'opus_search_url': opus_search_url,
               'opus_search_qr': opus_search_qr_str,
               'opus_state_url': opus_state_url,
               'opus_state_qr': opus_state_qr_str}
    return _render_html_or_pdf(request, 'help/citing.html', fmt, 'citing',
                               'How to Cite OPUS',
                               context)


@never_cache
@api_view
def api_api_guide(request, fmt):
    """Renders the API guide.

    Format: __help/apiguide.(?P<fmt>html|pdf)

    To edit guide content edit api_guide.md
    """
    if not request or request.GET is None or request.META is None:
        raise Http404(http404_no_request(f'/__help/apiguide.{fmt}'))

    uri = HttpRequest.build_absolute_uri(request)
    prefix = '/'.join(uri.split('/')[:3])
    git_id = get_git_version()
    current_date = datetime.datetime.today().strftime('%d-%B-%Y')

    path = os.path.dirname(os.path.abspath(__file__))
    guide_content_file = 'api_guide.md'
    with open(os.path.join(path, guide_content_file)) as stream:
        text = stream.read()
        text = text.replace('%HOST%', prefix)
        text = text.replace('%DATE%', current_date)
        text = text.replace('%VERSION%', git_id)
        text = re.sub(
            r'%EXTLINK%(.*)%ENDEXTLINK%',
            r'<a target="_blank" href="\1"><span class="op-api-guide-code">'
            +r'<code>\1</code></span></a>',
            text)
        text = re.sub(r'%CODE%\n', r'<div class="op-api-guide-code-block '
                      +r'op-api-guide-code"><pre><code>',
                      text)
        text = re.sub(r'%ENDCODE%', r'</code></pre></div>', text)
        guide = mistune.html(text)
        guide = guide.replace('%ADDCLASS%', '<div class="')
        guide = guide.replace('%ENDADDCLASS%', '">')
        guide = guide.replace('%ENDCLASS%', '</div>')
        guide = guide.replace('<table>',
                 '<table class="table table-sm table-striped table-hover '
                +'op-table-indent op-table-nonfluid">')
        guide = guide.replace('<thead>', '<thead class="thead-dark">')
        guide = guide.replace('<td>', '<td class="op-table-padding">')

    fields_dict = get_fields_info('raw', request, collapse=True)
    fields = []
    for _cat, cat_data in fields_dict.items():
        for _field_name, field in cat_data.items():
            field['pretty_units'] = None
            available_units = field['available_units']
            if available_units:
                field['pretty_units'] = ', '.join(available_units)
            fields.append(field)

    template_name = 'help/apiguide.html'
    if fmt == 'pdf':  # pragma: no cover
        template_name = 'help/apiguide_print.html'

    context = {'guide': guide,
               'fields': fields}
    return _render_html_or_pdf(request, template_name, fmt, 'api_guide',
                               None, context)


def _render_html_or_pdf(request, template, fmt, filename, title, context=None):
    """Render a template as HTML or PDF."""
    if fmt == 'html':  # pragma: no cover
        ret = render(request, template, context)
    else:  # pragma: no cover
        # Since we can't render PDF on Windows or Mac, we have to avoid using
        # this section for code coverage.
        header_template = get_template('ui/header.html')
        header_context = {'STATIC_URL': settings.OPUS_STATIC_ROOT+'/',
                          'allow_fallback': False,
                          'include_print_style': True}
        header = header_template.render(header_context)
        body_template = get_template(template)
        body = body_template.render(context)
        html = header + '<body>'
        if title is not None:
            html += '<h1>' + title + '</h1>'
        html += body + '</body>'
        options = {
            'page-size':        'Letter',
            'encoding':         'UTF-8',
            'margin-top':       '1in',
            'margin-bottom':    '1in', # Footer eats into this
            'margin-left':      '1in',
            'margin-right':     '1in',
            'footer-center':    'Page [page] of [topage]',
            'footer-spacing':   '5', # in mm
            'outline':          None, # Turn on PDF bookmarks
            'print-media-type': None, # Turn on @media print
            'quiet':            None, # Turn off console messages
        }
        pdf = pdfkit.from_string(html, False, options)
        # pdf = re.sub(b'file:///tmp/wktemp.*#', b'/#', pdf)

        ret = HttpResponse(pdf, content_type='application/pdf')
        filename = 'opus_'+filename+'.pdf'
        ret['Content-Disposition'] = f'attachment; filename="{filename}"'
        ret['Content-Transfer-Encoding'] = 'binary'
    return ret
