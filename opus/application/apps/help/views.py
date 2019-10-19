################################################################################
#
# help/views.py
#
################################################################################

import base64
from io import BytesIO
import logging
import os
import qrcode

import oyaml as yaml # Cool package that preserves key order

from django.http import Http404, HttpResponse, HttpRequest
from django.shortcuts import render
from django.views.decorators.cache import never_cache

from metadata.views import get_fields_info
from search.views import ObsGeneral, MultObsGeneralInstrumentId
from tools.app_utils import *

import settings

log = logging.getLogger(__name__)


################################################################################
#
# API INTERFACES
#
################################################################################

@never_cache
def api_about(request):
    """Renders the about page.

    This is a PRIVATE API.

    Format: __help/about.html
    """
    api_code = enter_api_call('api_about', request)

    if not request or request.GET is None:
        ret = Http404(settings.HTTP404_NO_REQUEST)
        exit_api_call(api_code, ret)
        raise ret

    git_id = get_git_version(True, True)
    database_schema = settings.DB_SCHEMA_NAME
    database_host = settings.DB_HOST_NAME
    context = {
        'git_id': git_id,
        'database_schema': database_schema,
        'database_host': database_host
    }

    ret = render(request, 'help/about.html', context)
    exit_api_call(api_code, ret)
    return ret

@never_cache
def api_volumes(request):
    """Renders the volumes page.

    This is a PRIVATE API.

    Format: __help/volumes.html
    """
    api_code = enter_api_call('api_volumes', request)

    if not request or request.GET is None:
        ret = Http404(settings.HTTP404_NO_REQUEST)
        exit_api_call(api_code, ret)
        raise ret

    data = {}
    all_volumes = OrderedDict()
    for d in (ObsGeneral.objects.values('instrument_id','volume_id')
              .order_by('instrument_id','volume_id').distinct()):
        instrument_name = (MultObsGeneralInstrumentId.objects.values('label')
                           .filter(value=d['instrument_id']))
        all_volumes.setdefault(instrument_name[0]['label'],
                               []).append(d['volume_id'])
    for k,v in all_volumes.items():
        all_volumes[k] = ', '.join(all_volumes[k])
    data = {'all_volumes': all_volumes}

    ret = render(request, 'help/volumes.html', data)
    exit_api_call(api_code, ret)
    return ret

@never_cache
def api_faq(request):
    """Renders the faq page.

    This is a PRIVATE API.

    Format: __help/faq.html
    """
    api_code = enter_api_call('api_faq', request)

    if not request or request.GET is None:
        ret = Http404(settings.HTTP404_NO_REQUEST)
        exit_api_call(api_code, ret)
        raise ret

    path = os.path.dirname(os.path.abspath(__file__))
    faq_content_file = 'faq.yaml'
    with open(os.path.join(path, faq_content_file), 'r') as stream:
        text = stream.read()
        try:
            faq = yaml.load(text, Loader=yaml.FullLoader)

        except yaml.YAMLError as exc: # pragma: no cover
            log.error('api_faq error: %s', str(exc))
            exit_api_call(api_code, None)
            raise Http404

    ret = render(request, 'help/faq.html',
                 {'faq': faq})

    exit_api_call(api_code, ret)
    return ret

@never_cache
def api_tutorial(request):
    """Renders the tutorial page.

    This is a PRIVATE API.

    Format: __help/tutorial.html
    """
    api_code = enter_api_call('api_tutorial', request)

    if not request or request.GET is None:
        ret = Http404(settings.HTTP404_NO_REQUEST)
        exit_api_call(api_code, ret)
        raise ret

    ret = render(request, 'help/tutorial.html')
    exit_api_call(api_code, ret)
    return ret

@never_cache
def api_gettingstarted(request):
    """Renders the getting started page.

    This is a PRIVATE API.

    Format: __help/gettingstarted.html
    """
    api_code = enter_api_call('api_gettingstarted', request)

    if not request or request.GET is None:
        ret = Http404(settings.HTTP404_NO_REQUEST)
        exit_api_call(api_code, ret)
        raise ret

    ret = render(request, 'help/gettingstarted.html')
    exit_api_call(api_code, ret)
    return ret

@never_cache
def api_splash(request):
    """Renders the splash page.

    This is a PRIVATE API.

    Format: __help/splash.html
    """
    api_code = enter_api_call('api_splash', request)

    if not request or request.GET is None:
        ret = Http404(settings.HTTP404_NO_REQUEST)
        exit_api_call(api_code, ret)
        raise ret

    ret = render(request, 'help/splash.html')
    exit_api_call(api_code, ret)
    return ret

@never_cache
def api_citing_opus(request):
    """Renders the citing opus page.

    This is a PRIVATE API.

    Format: __help/citing.html
    """
    api_code = enter_api_call('api_citing_opus', request)

    if not request or request.GET is None:
        ret = Http404(settings.HTTP404_NO_REQUEST)
        exit_api_call(api_code, ret)
        raise ret

    opus_search_url = request.GET.get('searchurl', None)
    opus_state_url = request.GET.get('stateurl', None)

    qr = qrcode.QRCode(
        box_size=5,
        border=4,
    )
    qr.add_data(settings.PUBLIC_OPUS_URL)
    qr.make(fit=True)
    basic_opus_qr = qr.make_image(fill_color='black', back_color='white')
    buffered = BytesIO()
    basic_opus_qr.save(buffered, format='PNG')
    basic_opus_qr_str = str(base64.b64encode(buffered.getvalue()))[2:-1]

    opus_search_qr_str = None
    if opus_search_url is not None:
        qr = qrcode.QRCode(
            box_size=5,
            border=4,
        )
        qr.add_data(opus_search_url)
        qr.make(fit=True)
        opus_search_qr = qr.make_image(fill_color='black', back_color='white')
        buffered = BytesIO()
        opus_search_qr.save(buffered, format='PNG')
        opus_search_qr_str = str(base64.b64encode(buffered.getvalue()))[2:-1]

    opus_state_qr_str = None
    if opus_state_url is not None:
        qr = qrcode.QRCode(
            box_size=5,
            border=4,
        )
        qr.add_data(opus_state_url)
        qr.make(fit=True)
        opus_state_qr = qr.make_image(fill_color='black', back_color='white')
        buffered = BytesIO()
        opus_state_qr.save(buffered, format='PNG')
        opus_state_qr_str = str(base64.b64encode(buffered.getvalue()))[2:-1]

    context = {'basic_opus_url': settings.PUBLIC_OPUS_URL,
               'basic_opus_qr': basic_opus_qr_str,
               'opus_search_url': opus_search_url,
               'opus_search_qr': opus_search_qr_str,
               'opus_state_url': opus_state_url,
               'opus_state_qr': opus_state_qr_str}
    ret = render(request, 'help/citing.html', context)
    exit_api_call(api_code, ret)
    return ret

def api_guide(request):
    """Renders the API guide at opus/api.

    Format: api/
        or: api/guide.html

    To edit guide content edit the examples.yaml
    """
    api_code = enter_api_call('api_guide', request)

    if not request or request.GET is None:
        ret = Http404(settings.HTTP404_NO_REQUEST)
        exit_api_call(api_code, ret)
        raise ret

    uri = HttpRequest.build_absolute_uri(request)
    prefix = '/'.join(uri.split('/')[:3])

    path = os.path.dirname(os.path.abspath(__file__))
    guide_content_file = 'examples.yaml'
    with open(os.path.join(path, guide_content_file), 'r') as stream:
        text = stream.read()
        text = text.replace('<HOST>', prefix)
        try:
            guide = yaml.load(text, Loader=yaml.FullLoader)

        except yaml.YAMLError as exc: # pragma: no cover
            log.error('api_guide error: %s', str(exc))
            exit_api_call(api_code, None)
            raise Http404

    slugs = get_fields_info('raw', collapse=True)

    ret = render(request, 'help/guide.html',
                 {'guide': guide, 'slugs': slugs})
    exit_api_call(api_code, ret)
    return ret
