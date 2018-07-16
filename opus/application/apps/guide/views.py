import oyaml as yaml # Cool package that preserves key order
import os
from django.shortcuts import render
from django.http import HttpResponse,Http404
from metrics.views import update_metrics
from metadata.views import get_fields_info


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
    path = os.path.dirname(os.path.abspath(__file__))
    guide_content_file = 'examples.yaml'
    with open(path + "/{}".format(guide_content_file), 'r') as stream:
        try:
            guide = yaml.load(stream)

        except yaml.YAMLError as exc:
            print(exc)
            return

    slugs = get_fields_info('raw', collapse=True)

    print slugs
    return render(request, 'guide/guide.html',
                  {'guide': guide, 'slugs': slugs})
