# results/urls.py
from django.conf.urls import url
from results.views import (
    get_data,
    get_images,
    get_image,
    get_files_API,
    api_get_metadata,
    get_collection_csv,
    api_get_all_categories,
    category_list_http_endpoint,
)
# results - getting data
urlpatterns = [
    url(r'^api/data.(json|zip|html|csv)$', get_data),
    url(r'^api/images/(thumb|small|med|full).(json|zip|html|csv)$',get_images),
    #url(r'^api/image/(?P<size>[thumb|small|med|full]+)/(?P<opus_id>[-\w]+).(?P<fmt>[json|zip|html|csv]+)$', get_image),
    url(r'^api/files/(?P<opus_id>[-\w]+).(?P<fmt>[json|zip|html|csv]+)$',get_files_API),
    url(r'^api/files.(?P<fmt>[json|zip|html|csv]+)$', get_files_API),
    url(r'^api/metadata/(?P<opus_id>[-\w]+).(?P<fmt>[json|html]+)$', api_get_metadata),
    url(r'^api/categories.json$', category_list_http_endpoint),
    url(r'^api/categories/(?P<opus_id>[-\w]+).json$', api_get_all_categories),
    url(r'^collections/data.csv$',get_collection_csv),
]
