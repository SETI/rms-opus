# ui/urls.py
from django.urls import re_path
from django.contrib import admin

from ui.views import (
    api_notifications,
    api_get_menu,
    api_get_widget,
    api_get_metadata_selector,
    api_init_detail_page,
    api_normalize_url,
    api_dummy
)

urlpatterns = [
    re_path(r'^admin/', admin.site.urls),
    re_path(r'^__notifications.json$', api_notifications),
    re_path(r'^__menu.json$', api_get_menu),
    re_path(r'^__metadata_selector.json$', api_get_metadata_selector),
    re_path(r'^__widget/(?P<slug>[-\w]+).html$', api_get_widget),
    re_path(r'^__initdetail/(?P<opus_id>[-\w]+).html$', api_init_detail_page),
    re_path(r'^__normalizeurl.json$', api_normalize_url),
    re_path(r'^__dummy.json$', api_dummy),
    re_path(r'^__fake/__viewmetadatamodal/(?P<opus_id>[-\w]+).json$', api_dummy),
    re_path(r'^__fake/__selectmetadatamodal.json$', api_dummy)
]
