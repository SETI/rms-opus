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
#    Format: __help/citing.(?P<fmt>html|pdf)
#
################################################################################

"""The OPUS help pages, from the About page to the API guide.

Every page but the splash page is rendered by `_render_html_or_pdf`, which returns
it either as HTML or as a PDF built from the template it is given, according to the
format named in the URL. One page takes its text from a file that ships inside this
package: the FAQ, from `faq.yaml`.

The API guide is not here. It is published as documentation, and the ``apiguide.pdf``
entry point redirects to it; `opus_app.settings.API_GUIDE_URL` is where the URL lives.
"""

from __future__ import annotations

import base64
import logging
import os
import platform
from io import BytesIO
from typing import Any

import pdfkit
import qrcode
import yaml
from django.conf import settings
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import render
from django.template.loader import get_template
from django.views.decorators.cache import never_cache

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
def api_about(request: HttpRequest, fmt: str) -> HttpResponse:
    """Render the About page.

    This is a PRIVATE API.

    ::

        Format: __help/about.(?P<fmt>html|pdf)

    The page is given the OPUS version, the schema and host name of the database
    being served, and the name of the machine serving it.

    Parameters:
        request: The request being served.
        fmt: `html` for the page itself, `pdf` for a PDF download.

    Returns:
        The About page in the requested format.

    Raises:
        Http404: If there is no request, or it has no GET or META.
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
        'hostname': hostname,
    }

    return _render_html_or_pdf(request, 'help/about.html', fmt, 'about', 'About OPUS', context)


@never_cache
@api_view
def api_bundles(request: HttpRequest, fmt: str) -> HttpResponse:
    """Render the Bundles page.

    This is a PRIVATE API.

    ::

        Format: __help/bundles.(?P<fmt>html|pdf)

    The page lists the bundles that hold observations in the database, grouped under
    the name of the instrument each was taken with.

    Parameters:
        request: The request being served.
        fmt: `html` for the page itself, `pdf` for a PDF download.

    Returns:
        The Bundles page in the requested format.

    Raises:
        Http404: If there is no request, or it has no GET or META.
    """
    if not request or request.GET is None or request.META is None:
        raise Http404(http404_no_request(f'/__help/bundles.{fmt}'))

    all_bundles: dict[str, list[str]] = {}
    for d in (
        ObsGeneral.objects.values('instrument_id', 'bundle_id')
        .order_by('instrument_id', 'bundle_id')
        .distinct()
    ):
        instrument_name = MultObsGeneralInstrumentId.objects.values('label').filter(
            id=d['instrument_id']
        )
        all_bundles.setdefault(instrument_name[0]['label'], []).append(d['bundle_id'])
    joined_bundles: dict[str, str] = {}
    for k, _v in all_bundles.items():
        joined_bundles[k] = ', '.join(all_bundles[k])

    context = {'all_bundles': joined_bundles}
    return _render_html_or_pdf(
        request,
        'help/bundles.html',
        fmt,
        'bundles',
        'Bundles/Volumes Available for Searching with OPUS',
        context,
    )


@never_cache
@api_view
def api_faq(request: HttpRequest, fmt: str) -> HttpResponse:
    """Render the FAQ page.

    This is a PRIVATE API.

    ::

        Format: __help/faq.(?P<fmt>html|pdf)

    The questions and answers are read from `faq.yaml`, which ships inside this
    package. The HTML page offers them collapsed; the PDF does not.

    Parameters:
        request: The request being served.
        fmt: `html` for the page itself, `pdf` for a PDF download.

    Returns:
        The FAQ page in the requested format.

    Raises:
        Http404: If there is no request, or it has no GET or META, or `faq.yaml`
            cannot be parsed.
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
        except yaml.YAMLError as exc:  # pragma: no cover -
            # This can only happen if there is a problem with the YAML in the
            # FAQ.YAML file
            log.exception('api_faq: Unable to parse %r', faq_content_file)
            raise Http404 from exc

    context = {'faq': faq, 'allow_collapse': fmt == 'html'}
    return _render_html_or_pdf(
        request, 'help/faq.html', fmt, 'faq', 'Frequently Asked Questions (FAQ) About OPUS', context
    )


@never_cache
@api_view
def api_gettingstarted(request: HttpRequest, fmt: str) -> HttpResponse:
    """Render the Getting Started page.

    This is a PRIVATE API.

    ::

        Format: __help/gettingstarted.(?P<fmt>html|pdf)

    Parameters:
        request: The request being served.
        fmt: `html` for the page itself, `pdf` for a PDF download.

    Returns:
        The Getting Started page in the requested format.

    Raises:
        Http404: If there is no request, or it has no GET or META.
    """
    if not request or request.GET is None or request.META is None:
        raise Http404(http404_no_request(f'/__help/gettingstarted.{fmt}'))

    return _render_html_or_pdf(
        request, 'help/gettingstarted.html', fmt, 'getting_started', 'Getting Started with OPUS'
    )


@never_cache
@api_view
def api_splash(request: HttpRequest) -> HttpResponse:
    """Render the splash page.

    This is a PRIVATE API.

    ::

        Format: __help/splash.html

    Parameters:
        request: The request being served.

    Returns:
        The splash page as HTML.

    Raises:
        Http404: If there is no request, or it has no GET or META.
    """
    if not request or request.GET is None or request.META is None:
        raise Http404(http404_no_request('/__help/splash.html'))

    return render(request, 'help/splash.html')


@never_cache
@api_view
def api_citing_opus(request: HttpRequest, fmt: str) -> HttpResponse:
    """Render the page explaining how to cite OPUS.

    This is a PRIVATE API.

    ::

        Format: __help/citing.(?P<fmt>html|pdf)
        Arguments: searchurl=<URL> (Optional, a search to be cited)
                   stateurl=<URL>  (Optional, a page state to be cited)

    The page carries a QR code for the public OPUS URL, plus one for each URL given
    as an argument.

    Parameters:
        request: The request being served.
        fmt: `html` for the page itself, `pdf` for a PDF download.

    Returns:
        The citation page in the requested format.

    Raises:
        Http404: If there is no request, or it has no GET or META.
    """
    if not request or request.GET is None or request.META is None:
        raise Http404(http404_no_request(f'/__help/citing.{fmt}'))

    opus_search_url = request.GET.get('searchurl', None)
    opus_state_url = request.GET.get('stateurl', None)

    def url_to_png_string(url: str) -> str:
        """Render a URL as a QR code.

        Parameters:
            url: The URL to encode in the QR code.

        Returns:
            A PNG image of the QR code, base64-encoded as ASCII text.
        """
        qr = qrcode.QRCode(box_size=5, border=4)
        qr.add_data(url)
        qr.make(fit=True)
        url_qr = qr.make_image(fill_color='black', back_color='white')
        buffered = BytesIO()
        # The stubs declare make_image() as returning the pure-Python
        # PyPNGImage, whose save() takes no `format`. With Pillow installed --
        # it is a declared dependency -- qrcode returns a PilImage instead,
        # whose save() forwards **kwargs to PIL. Measured: the class here is
        # qrcode.image.pil.PilImage and this call produces a PNG.
        url_qr.save(buffered, format='PNG')  # type: ignore[call-arg]
        url_qr_string = base64.b64encode(buffered.getvalue()).decode('ascii', 'strict')
        return url_qr_string

    basic_opus_qr_str = url_to_png_string(settings.PUBLIC_OPUS_URL)

    opus_search_qr_str = None
    if opus_search_url is not None:
        opus_search_qr_str = url_to_png_string(opus_search_url)

    opus_state_qr_str = None
    if opus_state_url is not None:
        opus_state_qr_str = url_to_png_string(opus_state_url)

    context = {
        'basic_opus_url': settings.PUBLIC_OPUS_URL,
        'basic_opus_qr': basic_opus_qr_str,
        'opus_search_url': opus_search_url,
        'opus_search_qr': opus_search_qr_str,
        'opus_state_url': opus_state_url,
        'opus_state_qr': opus_state_qr_str,
    }
    return _render_html_or_pdf(
        request, 'help/citing.html', fmt, 'citing', 'How to Cite OPUS', context
    )


def _render_html_or_pdf(
    request: HttpRequest,
    template: str,
    fmt: str,
    filename: str,
    title: str | None,
    context: dict[str, Any] | None = None,
) -> HttpResponse:
    """Render a template as HTML or PDF.

    Parameters:
        request: The request being served.
        template: The name of the template to render.
        fmt: `html` to return the rendered page; anything else returns a PDF.
        filename: The word naming the page in the PDF's download name.
        title: A heading to place above the body of the PDF, or None to omit it.
        context: The context to render the template with.

    Returns:
        The rendered page, or the PDF as an attachment named `opus_<filename>.pdf`.
    """
    if fmt == 'html':  # pragma: no cover
        ret = render(request, template, context)
    else:  # pragma: no cover
        # Since we can't render PDF on Windows or Mac, we have to avoid using
        # this section for code coverage.
        header_template = get_template('ui/header.html')
        header_context = {
            'STATIC_URL': settings.OPUS_STATIC_ROOT + '/',
            'allow_fallback': False,
            'include_print_style': True,
        }
        header = header_template.render(header_context)
        body_template = get_template(template)
        body = body_template.render(context)
        html = header + '<body>'
        if title is not None:
            html += '<h1>' + title + '</h1>'
        html += body + '</body>'
        options = {
            'page-size': 'Letter',
            'encoding': 'UTF-8',
            'margin-top': '1in',
            'margin-bottom': '1in',  # Footer eats into this
            'margin-left': '1in',
            'margin-right': '1in',
            'footer-center': 'Page [page] of [topage]',
            'footer-spacing': '5',  # in mm
            'outline': None,  # Turn on PDF bookmarks
            'print-media-type': None,  # Turn on @media print
            'quiet': None,  # Turn off console messages
        }
        pdf = pdfkit.from_string(html, False, options)
        # pdf = re.sub(b'file:///tmp/wktemp.*#', b'/#', pdf)

        ret = HttpResponse(pdf, content_type='application/pdf')
        filename = 'opus_' + filename + '.pdf'
        ret['Content-Disposition'] = f'attachment; filename="{filename}"'
        ret['Content-Transfer-Encoding'] = 'binary'
    return ret
