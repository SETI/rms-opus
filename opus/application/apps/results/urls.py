# results/urls.py
from django.conf.urls import url
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
    api_get_image,
    api_get_categories_for_opus_id,
    api_get_categories_for_search,
)

urlpatterns = [
    url(r'^__api/dataimages.json$', api_get_data_and_images),
    url(r'^api/data.(?P<fmt>json|html|csv)$', api_get_data),
    url(r'^api/metadata/(?P<opus_id>[-\w]+).(?P<fmt>json|html|csv)$', api_get_metadata),
    url(r'^api/metadata_v2/(?P<opus_id>[-\w]+).(?P<fmt>json|html|csv)$', api_get_metadata_v2),
    url(r'^__api/metadata_v2/(?P<opus_id>[-\w]+).(?P<fmt>json|html|csv)$', api_get_metadata_v2_internal),
    url(r'^api/images/(?P<size>thumb|small|med|full).(?P<fmt>json|zip|html|csv)$', api_get_images_by_size),
    url(r'^api/images.(?P<fmt>json|zip|html|csv)$', api_get_images),
    url(r'^api/image/(?P<size>thumb|small|med|full)/(?P<opus_id>[-\w]+).(?P<fmt>json|zip|html|csv)$', api_get_image),
    url(r'^api/files/(?P<opus_id>[-\w]+).json$', api_get_files),
    url(r'^api/files.json$', api_get_files),
    url(r'^api/categories/(?P<opus_id>[-\w]+).json$', api_get_categories_for_opus_id),
    url(r'^__api/categories/(?P<opus_id>[-\w]+).json$', api_get_categories_for_opus_id),
    url(r'^api/categories.json$', api_get_categories_for_search),
]
