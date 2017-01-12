from guide.models import *
from django.shortcuts import render
from django.http import HttpResponse,Http404
from metrics.views import update_metrics

def guide(request):
    update_metrics(request)

    base_url = 'http://' +request.META['HTTP_HOST'] + '/opus/'
    groups = Group.objects.all()
    resources = Resource.objects.filter(display=True).select_related().order_by('disp_order')

    return render(request, 'guide.html', locals())


# def update(request)
