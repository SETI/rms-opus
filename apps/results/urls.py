# results/urls.py
from django.conf.urls import url
from results.views import (
    getData,
    getImages,
    getImage,
    getFilesAPI,
    get_metadata,
    get_collection_csv,
    get_all_categories,
    category_list_http_endpoint,
)
# results - getting data
urlpatterns = [
    url(r'^api/data.(json|zip|html|csv)$', getData),
    url(r'^api/images/(thumb|small|med|full).(json|zip|html|csv)$',getImages),
    url(r'^api/image/(?P<size>[thumb|small|med|full]+)/(?P<opus_id>[0-9a-zA-Z\-_]+).(?P<fmt>[json|zip|html|csv]+)$', getImage),
    url(r'^api/files/(?P<opus_id>[0-9a-zA-Z\-_]+).(?P<fmt>[json|zip|html|csv]+)$',getFilesAPI),
    url(r'^api/files.(?P<fmt>[json|zip|html|csv]+)$', getFilesAPI),
    url(r'^api/metadata/(?P<opus_id>[0-9a-zA-Z\-_]+).(?P<fmt>[json|html]+)$', get_metadata),
    url(r'^api/categories.json$', category_list_http_endpoint),
    url(r'^api/categories/(?P<opus_id>[0-9a-zA-Z\-_]+).json$', get_all_categories),
    url(r'^collections/data.csv$',get_collection_csv),
]
