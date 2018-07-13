# results/urls.py
from django.conf.urls import url
from results.views import (
    api_get_data,
    api_get_images,
    api_get_image,
    api_get_files,
    api_get_metadata,
    api_get_all_categories,
    category_list_http_endpoint,
)
# results - getting data
urlpatterns = [
    url(r'^api/data.(json|zip|html|csv)$', api_get_data),
    url(r'^api/images.(json|zip|html|csv)$', api_get_images),
    url(r'^api/image/(?P<size>[thumb|small|med|full]+)/(?P<opus_id>[-\w]+).(?P<fmt>[json|zip|html|csv]+)$', api_get_image),
    url(r'^api/files/(?P<opus_id>[-\w]+).(?P<fmt>[json|zip|html|csv]+)$', api_get_files),
    url(r'^api/files.(?P<fmt>[json|zip|html|csv]+)$', api_get_files),
    url(r'^api/metadata/(?P<opus_id>[-\w]+).(?P<fmt>[json|html]+)$', api_get_metadata),
    url(r'^api/categories.json$', category_list_http_endpoint),
    url(r'^api/categories/(?P<opus_id>[-\w]+).json$', api_get_all_categories)
]
