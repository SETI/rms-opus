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
    url(r'^api/meta/result_count.url(?P<fmt>[json|zip|html|csv]+)$', getResultCount),
    url(r'^api/meta/mults/url(?P<slug>[-\sa-zA-Z]+).url(?P<fmt>[json|zip|html|csv]+)$', getValidMults),
    url(r'^api/meta/range/endpoints/url(?P<slug>[-\sa-zA-Z0-9]+).url(?P<fmt>[json|zip|html|csv]+)$', getRangeEndpoints),
    url(r'^api/fields/url(?P<field>\w+).url(?P<fmt>[json|zip|html|csv]+)$', getFields),
    url(r'^api/fields.url(?P<fmt>[json|zip|html|csv]+)$', getFields),
]
