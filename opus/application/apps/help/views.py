################################################################################
#
# help/views.py
#
################################################################################

import logging
import os

import oyaml as yaml # Cool package that preserves key order

from django.shortcuts import render
from django.http import Http404, HttpResponse, HttpRequest

from metadata.views import get_fields_info
from tools.app_utils import *

log = logging.getLogger(__name__)


################################################################################
#
# API INTERFACES
#
################################################################################

def api_about(request):
    """Renders the about page.

    This is a PRIVATE API.

    Format: __help/about.html
    """
    api_code = enter_api_call('api_about', request)

    ret = render(request, 'help/about.html')
    exit_api_call(api_code, ret)
    return ret

def api_datasets(request):
    """Renders the datasets page.

    This is a PRIVATE API.

    Format: __help/datasets.html
    """
    api_code = enter_api_call('api_datasets', request)

    data = {}
    all_volumes = OrderedDict()
    for d in (ObsGeneral.objects.values('instrument_id','volume_id')
              .order_by('instrument_id','volume_id').distinct()):
        all_volumes.setdefault(d['instrument_id'],
                               []).append(d['volume_id'])
    for k,v in all_volumes.items():
        all_volumes[k] = ', '.join(all_volumes[k])
    data = {'all_volumes': all_volumes}

    ret = render(request, 'help/datasets.html', data)
    exit_api_call(api_code, ret)
    return ret

def api_faq(request):
    """Renders the faq page.

    This is a PRIVATE API.

    Format: __help/faq.html
    """
    api_code = enter_api_call('api_faq', request)

    path = os.path.dirname(os.path.abspath(__file__))
    faq_content_file = 'faq.yaml'
    with open(os.path.join(path, faq_content_file), 'r') as stream:
        text = stream.read()
        try:
            faq = yaml.load(text)

        except yaml.YAMLError as exc:
            log.error('api_faq error: %s', str(exc))
            exit_api_call(api_code, None)
            raise Http404

    print(faq)
    ret = render(request, 'help/faq.html',
                 {'faq': faq})

    exit_api_call(api_code, ret)
    return ret

def api_tutorial(request):
    """Renders the tutorial page.

    This is a PRIVATE API.

    Format: __help/tutorial.html
    """
    api_code = enter_api_call('api_tutorial', request)

    ret = render(request, 'help/tutorial.html')
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
            guide = yaml.load(text)

        except yaml.YAMLError as exc:
            log.error('api_guide error: %s', str(exc))
            exit_api_call(api_code, None)
            raise Http404

    slugs = get_fields_info('raw', collapse=True)

    ret = render(request, 'help/guide.html',
                 {'guide': guide, 'slugs': slugs})
    exit_api_call(api_code, ret)
    return ret
