import logging
import os

import oyaml as yaml # Cool package that preserves key order

from django.shortcuts import render
from django.http import Http404, HttpResponse

from metadata.views import get_fields_info
from tools.app_utils import *

log = logging.getLogger(__name__)


################################################################################
#
# API INTERFACES
#
################################################################################

def api_guide(request):
    """Renders the API guide at opus/api

    Format: api/
        or: api/guide.html

    To edit guide content edit the examples.yaml
    """
    api_code = enter_api_call('api_guide', request)

    path = os.path.dirname(os.path.abspath(__file__))
    guide_content_file = 'examples.yaml'
    with open(os.path.join(path, guide_content_file), 'r') as stream:
        try:
            guide = yaml.load(stream)

        except yaml.YAMLError as exc:
            log.error('api_guide error: %s', str(exc))
            exit_api_call(api_code, None)
            raise Http404

    slugs = get_fields_info('raw', collapse=True)

    ret = render(request, 'guide/guide.html',
                 {'guide': guide, 'slugs': slugs})
    exit_api_call(api_code, ret)
    return ret
