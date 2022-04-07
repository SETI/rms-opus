# metadata/urls.py
from django.urls import re_path

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
    re_path(r'^api/meta/result_count.(?P<fmt>json|html|csv)$', api_get_result_count),
    re_path(r'^__api/meta/result_count.json$', api_get_result_count_internal),

    re_path(r'^api/meta/mults/(?P<slug>[-\w]+).(?P<fmt>json|html|csv)$', api_get_mult_counts),
    re_path(r'^__api/meta/mults/(?P<slug>[-\w]+).json$', api_get_mult_counts_internal),

    re_path(r'^api/meta/range/endpoints/(?P<slug>[-\w]+).(?P<fmt>json|html|csv)$', api_get_range_endpoints),
    re_path(r'^__api/meta/range/endpoints/(?P<slug>[-\w]+).json$', api_get_range_endpoints_internal),

    re_path(r'^api/fields/(?P<slug>\w+).(?P<fmt>json|csv)$', api_get_fields),
    re_path(r'^api/fields.(?P<fmt>json|csv)$', api_get_fields),
]
