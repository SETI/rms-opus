# downloads/urls.py
from django.conf.urls import url
from downloads.views import (
    api_create_download,
    api_get_download_info
)

# making downloads
urlpatterns = [
    url(r'^zip/(?P<opus_id>[-\w]+).(?P<fmt>[json]+)$', api_create_download),
    url(r'^collections/download/(?P<collection_name>[default]+).zip$', api_create_download),
    url(r'^collections/download/info/$', api_get_download_info),
]
