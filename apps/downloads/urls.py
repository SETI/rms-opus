# downloads/urls.py
from django.conf.urls import url
from downloads.views import create_download, get_download_info_API

# making downloads
urlpatterns = [
    url(r'^zip/(?P<ring_obs_id>[0-9a-zA-Z\-_]+).(?P<fmt>[json]+)$', create_download),
    url(r'^collections/download/(?P<collection_name>[default]+).zip$', create_download),
    url(r'^collections/download/info/$', get_download_info_API),
]
