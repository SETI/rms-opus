# user_collections/urls.py
from django.conf.urls import url
from user_collections.views import (
    api_view_collection,
    api_collection_status,
    api_get_collection_csv,
    api_edit_collection,
    api_reset_session,
    api_create_download
)

urlpatterns = [
    url(r'^__collections/view.(?P<fmt>html|json)$', api_view_collection),
    url(r'^__collections/status.json$', api_collection_status),
    url(r'^__collections/data.csv$', api_get_collection_csv),
    url(r'^__collections/(?P<action>[add|remove|addrange|removerange|addall]+).json$', api_edit_collection),
    url(r'^__collections/reset.json$', api_reset_session),
    url(r'^__collections/download.zip$', api_create_download),
    url(r'^__zip/(?P<opus_id>[-\w]+).json$', api_create_download),
]
