# results/urls.py
from django.urls import re_path
from results.views import (
    api_get_data_and_images,
    api_get_data,
    api_get_metadata,
    api_get_metadata_v2,
    api_get_metadata_v2_internal,
    api_get_images,
    api_get_images_by_size,
    api_get_image,
    api_get_files,
    api_get_categories_for_opus_id,
    api_get_categories_for_search,
    api_get_product_types_for_opus_id,
    api_get_product_types_for_search,
)
from ui.views import api_dummy

urlpatterns = [
    # The internal version of api/data and api/images that we don't advertise
    # so we don't have to maintain backwards compatibility.
    re_path(r'^__api/dataimages.json$', api_get_data_and_images),
    # Called when we don't actually need data but want a user action recorded
    # in the web log file.
    re_path(r'^__fake/__api/dataimages.json$', api_dummy),

    re_path(r'^api/data.(?P<fmt>json|html|csv)$', api_get_data),
    re_path(r'^__api/data.(?P<fmt>csv)$', api_get_data),

    # Backwards compatibility
    re_path(r'^api/metadata/(?P<opus_id>[-\w]+).(?P<fmt>json|html|csv)$', api_get_metadata),

    re_path(r'^api/metadata_v2/(?P<opus_id>[-\w]+).(?P<fmt>json|html|csv)$', api_get_metadata_v2),
    re_path(r'^__api/metadata_v2/(?P<opus_id>[-\w]+).(?P<fmt>json|html|csv)$', api_get_metadata_v2_internal),

    re_path(r'^api/images/(?P<size>thumb|small|med|full).(?P<fmt>json|html|csv)$', api_get_images_by_size),
    re_path(r'^api/images.(?P<fmt>json|csv)$', api_get_images),
    re_path(r'^api/image/(?P<size>thumb|small|med|full)/(?P<opus_id>[-\w]+).(?P<fmt>json|html|csv)$', api_get_image),
    re_path(r'^__api/image/(?P<size>thumb|small|med|full)/(?P<opus_id>[-\w]+).(?P<fmt>json)$', api_get_image),

    re_path(r'^api/files/(?P<opus_id>[-\w]+).json$', api_get_files),
    re_path(r'^api/files.json$', api_get_files),

    re_path(r'^api/categories/(?P<opus_id>[-\w]+).json$', api_get_categories_for_opus_id),
    re_path(r'^__api/categories/(?P<opus_id>[-\w]+).json$', api_get_categories_for_opus_id),
    re_path(r'^api/categories.json$', api_get_categories_for_search),

    re_path(r'^api/product_types/(?P<opus_id>[-\w]+).json$', api_get_product_types_for_opus_id),
    re_path(r'^api/product_types.json$', api_get_product_types_for_search),
]
