# metadata/urls.py
from django.conf.urls import url
from metadata.views import (
    getResultCount,
    getValidMults,
    getRangeEndpoints,
    getFields,
)
# metadata - getting information about a data
urlpatterns = [
    url(r'^api/meta/result_count.(?P<fmt>[json|zip|html|csv]+)$', getResultCount),
    url(r'^api/meta/mults/(?P<slug>[-\w]+).(?P<fmt>[json|zip|html|csv]+)$', getValidMults),
    url(r'^api/meta/range/endpoints/(?P<slug>[-\w]+).(?P<fmt>[json|zip|html|csv]+)$', getRangeEndpoints),
    url(r'^api/fields/(?P<field>\w+).(?P<fmt>[json|zip|html|csv]+)$', getFields),
    url(r'^api/fields.(?P<fmt>[json|zip|html|csv]+)$', getFields),
]
