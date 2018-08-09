# metadata/urls.py
from django.conf.urls import url
from metadata.views import (
    api_get_result_count,
    api_get_mult_counts,
    api_get_range_endpoints,
    api_get_fields,
)
# metadata - getting information about a data
urlpatterns = [
    url(r'^api/meta/result_count.(?P<fmt>[json|zip|html|csv]+)$', api_get_result_count),
    url(r'^__api/meta/result_count.(?P<fmt>[json|zip|html|csv]+)$', api_get_result_count),
    url(r'^api/meta/mults/(?P<slug>[-\w]+).(?P<fmt>[json|zip|html|csv]+)$', api_get_mult_counts),
    url(r'^__api/meta/mults/(?P<slug>[-\w]+).(?P<fmt>[json|zip|html|csv]+)$', api_get_mult_counts),
    url(r'^api/meta/range/endpoints/(?P<slug>[-\w]+).(?P<fmt>[json|zip|html|csv]+)$', api_get_range_endpoints),
    url(r'^__api/meta/range/endpoints/(?P<slug>[-\w]+).(?P<fmt>[json|zip|html|csv]+)$', api_get_range_endpoints),
    url(r'^api/fields/(?P<field>\w+).(?P<fmt>[json|zip|html|csv]+)$', api_get_fields),
    url(r'^__api/fields/(?P<field>\w+).(?P<fmt>[json|zip|html|csv]+)$', api_get_fields),
    url(r'^api/fields.(?P<fmt>[json|zip|html|csv]+)$', api_get_fields),
    url(r'^__api/fields.(?P<fmt>[json|zip|html|csv]+)$', api_get_fields),
]
