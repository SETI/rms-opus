# metadata/urls.py
from django.conf.urls import url

from metadata.views import (
    api_get_result_count,
    api_get_result_count_internal,
    api_get_mult_counts,
    api_get_mult_counts_internal,
    api_get_range_endpoints,
    api_get_range_endpoints_internal,
    api_get_fields,
)

urlpatterns = [
    url(r'^api/meta/result_count.(?P<fmt>json|html|csv)$', api_get_result_count),
    url(r'^__api/meta/result_count.json$', api_get_result_count_internal),
    url(r'^api/meta/mults/(?P<slug>[-\w]+).(?P<fmt>json|html|csv)$', api_get_mult_counts),
    url(r'^__api/meta/mults/(?P<slug>[-\w]+).json$', api_get_mult_counts_internal),
    url(r'^api/meta/range/endpoints/(?P<slug>[-\w]+).(?P<fmt>json|html|csv)$', api_get_range_endpoints),
    url(r'^__api/meta/range/endpoints/(?P<slug>[-\w]+).json$', api_get_range_endpoints_internal),
    url(r'^api/fields/(?P<slug>\w+).(?P<fmt>json|html|csv)$', api_get_fields),
    url(r'^__api/fields/(?P<slug>\w+).(?P<fmt>json|html|csv)$', api_get_fields),
    url(r'^api/fields.(?P<fmt>json|html|csv)$', api_get_fields),
    url(r'^__api/fields.(?P<fmt>json|html|csv)$', api_get_fields),
]
