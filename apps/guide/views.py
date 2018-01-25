import yaml, os
from django.shortcuts import render
from django.http import HttpResponse,Http404
from metrics.views import update_metrics

def guide(request):
    path = os.path.dirname(os.path.abspath(__file__))
    with open(path + "/examples.yaml", 'r') as stream:
        try:
            guide = yaml.load(stream)
            return render(request, 'guide.html', locals())

        except yaml.YAMLError as exc:
            print(exc)
