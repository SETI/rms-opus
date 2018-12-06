# user_collections/urls.py
from django.conf.urls import url
from user_collections.views import (
    api_view_collection,
    api_collection_status,
    api_get_collection_csv,
    api_edit_collection,
    api_reset_session,
    api_create_download,
    api_get_download_info
)

# user_collections - all your carts are belong to us
urlpatterns = [
    url(r'^__collections/view.html$', api_view_collection),
    url(r'^__collections/status.json$', api_collection_status),
    url(r'^__collections/data.csv$', api_get_collection_csv),
    url(r'^__collections/(?P<action>[add|remove|addrange|removerange|addall]+).json$', api_edit_collection),
    url(r'^__collections/reset.html$', api_reset_session),
    url(r'^__collections/download/info.json$', api_get_download_info),
    url(r'^__collections/download.zip$', api_create_download),
    url(r'^__zip/(?P<opus_id>[-\w]+).(?P<fmt>[json]+)$', api_create_download),
]
